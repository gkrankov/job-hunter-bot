import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from search_jobs import search_jobs, save_to_csv
from tailor_cv import load_config, load_master_cv, load_jobs_from_csv, tailor_cv, save_tailored_cv, rank_jobs, estimate_match_score
from generate_pdf import generate_pdf_from_text
from validation import validate_all_config

logger = logging.getLogger(__name__)

def configure_logging(level_name: str = "INFO"):
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Run the entire Job Hunter Bot pipeline end-to-end.")
    parser.add_argument("--queries", nargs="+", default=None, help="Job search queries to run.")
    parser.add_argument("--country", default="gb", help="Country code for the search location.")
    parser.add_argument("--num-pages", type=int, default=3, help="Number of pages to fetch per search query.")
    parser.add_argument("--remote-only", action="store_true", help="Fetch only remote jobs.")
    parser.add_argument("--jobs-csv", default="jobs_found.csv", help="Output CSV file for job search results.")
    parser.add_argument("--master-cv", default="master_cv.txt", help="Path to the master CV text file.")
    parser.add_argument("--tailored-dir", default="tailored_cvs", help="Directory to save tailored CVs.")
    parser.add_argument("--pdf-dir", default="pdf_cvs", help="Directory to save generated PDFs.")
    parser.add_argument("--config", default="tailor_config.json", help="Tailoring config JSON file for prompt templates and keywords.")
    parser.add_argument("--top", type=int, default=5, help="Tailor the top N jobs by estimated fit.")
    parser.add_argument("--all-jobs", action="store_true", help="Tailor and convert all jobs from the CSV.")
    parser.add_argument("--workers", type=int, default=None, help="Number of concurrent GPT tailoring workers.")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR).")
    return parser.parse_args()


def run_job_search(queries, country, num_pages, remote_only, output_csv):
    logger.info("🔍 Running job search...")
    all_jobs = []
    seen_links = set()

    for query in queries:
        jobs = search_jobs(query, country, num_pages, remote_only)
        for job in jobs:
            link = job.get("job_apply_link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                all_jobs.append(job)

    save_to_csv(all_jobs, filename=output_csv)
    logger.info("✅ Job search complete. %d unique jobs saved to %s.", len(all_jobs), output_csv)
    return all_jobs


def tailor_jobs_from_csv(jobs_csv, master_cv_path, tailored_dir, top, all_jobs, config_path, workers):
    config = load_config(config_path)
    if workers is not None:
        config["workers"] = workers

    master_cv = load_master_cv(master_cv_path)
    jobs = load_jobs_from_csv(jobs_csv)
    if not jobs:
        logger.warning("No jobs found in %s.", jobs_csv)
        return []

    if all_jobs:
        selected_jobs = jobs
    else:
        ranked = rank_jobs(jobs, master_cv, config["keywords"])
        selected_jobs = ranked[:top]

    logger.info("✍️  Tailoring %d jobs...", len(selected_jobs))
    tailored_files = []

    with ThreadPoolExecutor(max_workers=min(config.get("workers", 2), len(selected_jobs))) as executor:
        futures = []
        for job in selected_jobs:
            futures.append(executor.submit(_tailor_job_and_save, job, config, master_cv, tailored_dir))

        with tqdm(total=len(selected_jobs), desc="Tailoring CVs", unit="job") as pbar:
            for future in as_completed(futures):
                try:
                    path = future.result()
                    tailored_files.append(path)
                    logger.info("Saved tailored CV: %s", path)
                except Exception as exc:
                    logger.error("A tailoring task failed: %s", exc)
                pbar.update(1)

    logger.info("✅ Tailoring complete.\n")
    return tailored_files


def _tailor_job_and_save(job, config, master_cv, tailored_dir):
    title = job.get("job_title", "Unknown Role")
    company = job.get("company", "Unknown Company")
    description = job.get("description_snippet", "No description available")
    score = job.get("match_score") or estimate_match_score(master_cv, title, description, config["keywords"])
    logger.info("Tailoring for: %s at %s (Score: %s)", title, company, score)
    content = tailor_cv(config, master_cv, title, company, description)
    return save_tailored_cv(content, title, company, tailored_dir)


def convert_pdfs(tailored_files, output_dir):
    logger.info("📄 Generating PDFs...")
    for txt_path in tqdm(tailored_files, desc="Generating PDFs", unit="pdf"):
        pdf_path = generate_pdf_from_text(txt_path, output_dir)
        logger.info("  %s -> %s", txt_path, pdf_path)
    logger.info("✅ PDF generation complete.\n")


def main():
    args = parse_args()
    configure_logging(args.log_level)
    
    # Validate all configuration before running
    if not validate_all_config():
        logger.error("Configuration validation failed. Exiting.")
        sys.exit(1)
    
    queries = args.queries if args.queries else [
        "IT Sales Manager",
        "IT Account Manager",
        "Technical Account Manager",
        "IT Sales Executive",
        "SaaS Account Executive",
        "IT Support Manager"
    ]

    run_job_search(queries, args.country, args.num_pages, args.remote_only, args.jobs_csv)
    tailored_files = tailor_jobs_from_csv(
        args.jobs_csv,
        args.master_cv,
        args.tailored_dir,
        args.top,
        args.all_jobs,
        args.config,
        args.workers,
    )
    if tailored_files:
        convert_pdfs(tailored_files, args.pdf_dir)


if __name__ == "__main__":
    main()
