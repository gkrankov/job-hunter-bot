import argparse
import csv
import hashlib
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from validation import validate_rapidapi_key

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("RAPIDAPI_KEY")
DEFAULT_QUERIES = [
    "IT Sales Manager",
    "IT Account Manager",
    "Technical Account Manager",
    "IT Sales Executive",
    "SaaS Account Executive",
    "IT Support Manager"
]
COUNTRY_MAP = {
    "gb": "United Kingdom",
    "us": "United States",
    "de": "Germany",
    "nl": "Netherlands"
}

JOB_HISTORY_FILE = "job_history.csv"
LAST_SEARCH_FILE = "last_search.json"

logger = logging.getLogger(__name__)


def get_job_id(job: dict) -> str:
    link = job.get("job_apply_link", "").strip()
    if link:
        return link

    fallback = "|".join(
        [job.get("job_title", ""), job.get("employer_name", ""), job.get("job_city", ""), job.get("job_country", "")]
    )
    return hashlib.sha256(fallback.encode("utf-8")).hexdigest()


def load_job_history(filename: str = JOB_HISTORY_FILE) -> set:
    if not os.path.exists(filename):
        return set()

    links = set()
    with open(filename, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("job_id"):
                links.add(row["job_id"])
    return links


def append_job_history(jobs: list, filename: str = JOB_HISTORY_FILE) -> None:
    existing_links = load_job_history(filename)
    fieldnames = ["job_id", "job_title", "employer_name", "job_city", "job_country", "job_apply_link", "date_processed"]
    new_rows = []
    for job in jobs:
        job_id = get_job_id(job)
        if job_id in existing_links:
            continue
        new_rows.append({
            "job_id": job_id,
            "job_title": job.get("job_title", ""),
            "employer_name": job.get("employer_name", ""),
            "job_city": job.get("job_city", ""),
            "job_country": job.get("job_country", ""),
            "job_apply_link": job.get("job_apply_link", ""),
            "date_processed": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    if not new_rows:
        return

    write_header = not os.path.exists(filename)
    with open(filename, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for row in new_rows:
            writer.writerow(row)


def filter_new_jobs(jobs: list, history_links: set) -> list:
    return [job for job in jobs if get_job_id(job) not in history_links]


def configure_logging(level_name: str = "INFO"):
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_country_name(code: str) -> str:
    return COUNTRY_MAP.get(code.lower(), code)


def create_session() -> requests.Session:
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1,
        raise_on_status=False,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def search_jobs(query: str, country: str, num_pages: int, remote_only: bool, session: requests.Session, history_links: set | None = None):
    """Search for jobs using JSearch API with retries and rate-limit handling."""
    url = "https://jsearch.p.rapidapi.com/search"
    params = {
        "query": f"{query} in {get_country_name(country)}",
        "page": "1",
        "num_pages": str(num_pages),
        "date_posted": "week",
        "remote_jobs_only": str(remote_only).lower(),
    }
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    logger.debug("Requesting JSearch for query=%s country=%s pages=%s remote=%s", query, country, num_pages, remote_only)
    try:
        response = session.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 429:
            logger.warning("Rate limit hit for query '%s'; retrying after backoff", query)
            time.sleep(2)
            response = session.get(url, headers=headers, params=params, timeout=15)

        response.raise_for_status()
        jobs = response.json().get("data", [])
        if history_links is not None:
            jobs = filter_new_jobs(jobs, history_links)
        return jobs
    except requests.RequestException as exc:
        logger.warning("Failed to search '%s': %s", query, exc)
        return []


def save_to_csv(all_jobs, filename="jobs_found.csv"):
    """Save all jobs to a CSV file."""
    if not all_jobs:
        logger.warning("No jobs to save.")
        return

    fieldnames = [
        "date_found",
        "job_title",
        "company",
        "location",
        "employment_type",
        "apply_link",
        "description_snippet",
        "posted_date",
        "source"
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for job in all_jobs:
            description = job.get("job_description", "")
            snippet = description[:300].replace("\n", " ") if description else ""
            location_parts = [part for part in [job.get("job_city"), job.get("job_country")] if part]
            writer.writerow({
                "date_found": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "job_title": job.get("job_title", ""),
                "company": job.get("employer_name", ""),
                "location": ", ".join(location_parts),
                "employment_type": job.get("job_employment_type", ""),
                "apply_link": job.get("job_apply_link", ""),
                "description_snippet": snippet,
                "posted_date": job.get("job_posted_at_datetime_utc", "")[:10],
                "source": job.get("job_publisher", "")
            })

    logger.info("Saved %d jobs to %s", len(all_jobs), filename)


def parse_args():
    parser = argparse.ArgumentParser(description="Search for job listings using JSearch and save them to CSV.")
    parser.add_argument("--queries", nargs="+", default=DEFAULT_QUERIES, help="Job search queries to run.")
    parser.add_argument("--country", default="gb", help="Country code for the search location.")
    parser.add_argument("--num-pages", type=int, default=3, help="Number of pages to fetch per query.")
    parser.add_argument("--remote-only", action="store_true", help="Fetch only remote jobs.")
    parser.add_argument("--output", default="jobs_found.csv", help="CSV file path for search results.")
    parser.add_argument("--preview", type=int, default=5, help="Number of top jobs to preview after search.")
    parser.add_argument("--workers", type=int, default=3, help="Number of worker threads for parallel search.")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR).")
    return parser.parse_args()


def main():
    args = parse_args()
    configure_logging(args.log_level)
    logger.info("🔍 Job Hunter Bot — Starting Search...")
    
    # Validate API key before proceeding
    if not validate_rapidapi_key():
        logger.error("Cannot proceed without valid RapidAPI key.")
        sys.exit(1)

    all_jobs = []
    seen_links = set()
    session = create_session()

    with ThreadPoolExecutor(max_workers=min(args.workers, max(1, len(args.queries)))) as executor:
        future_to_query = {
            executor.submit(search_jobs, query, args.country, args.num_pages, args.remote_only, session): query
            for query in args.queries
        }
        with tqdm(total=len(args.queries), desc="Searching queries", unit="query") as pbar:
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    jobs = future.result()
                except Exception as exc:
                    logger.error("Unexpected error searching '%s': %s", query, exc)
                    jobs = []

                unique_count_before = len(all_jobs)
                for job in jobs:
                    link = job.get("job_apply_link", "")
                    if link and link not in seen_links:
                        seen_links.add(link)
                        all_jobs.append(job)
                logger.info("Query '%s' returned %d jobs (%d unique total)", query, len(jobs), len(all_jobs))
                pbar.update(1)

    logger.info("Total unique jobs found: %d", len(all_jobs))
    save_to_csv(all_jobs, filename=args.output)

    logger.info("Top Results Preview:")
    for job in all_jobs[: args.preview]:
        logger.info("📌 %s", job.get("job_title"))
        logger.info("   🏢 %s", job.get("employer_name"))
        logger.info("   📍 %s", job.get("job_city", "N/A"))
        logger.info("   🔗 %s", job.get("job_apply_link", "N/A")[:80])


if __name__ == "__main__":
    main()
