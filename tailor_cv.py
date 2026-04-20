import argparse
import csv
import json
import logging
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List

import google.genai as genai
from dotenv import load_dotenv
from tqdm import tqdm

from validation import validate_gemini_api_key, validate_master_cv

# Force UTF-8 console output on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger(__name__)


def configure_logging(level_name: str = "INFO"):
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# Load API keys
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-flash-latest"
CONFIG_PATH = "tailor_config.json"

CONTACT_BLOCK = """Gabor Krankov
gabor.krankov@email.com | +36 XX XXX XXXX
Budapest, Hungary
Languages: English (Fluent), German (Fluent), Hungarian (Native)
LinkedIn: https://www.linkedin.com/in/gkrankov/
"""

DEFAULT_PROMPT_TEMPLATE = """You are an expert CV writer tailoring a CV for a specific role.

ROLE: {job_title} at {company}
JOB DESCRIPTION: {job_description}

MASTER CV (the ONLY source of truth):
{master_cv}

ABSOLUTE RULES — violations make the output unusable:
1. NEVER invent metrics, percentages, dollar amounts, team sizes, or dates. Only use figures explicitly present in the master CV. If no metric exists for an achievement, describe it qualitatively.
   ❌ WRONG: "Managed a team of 50 engineers" (if master CV says nothing about team size)
   ✅ RIGHT: "Managed engineering teams" (qualitative description)
   ❌ WRONG: "Increased revenue by 30%" (if no percentage in master CV)
   ✅ RIGHT: "Increased revenue through strategic initiatives" (no invented numbers)
2. NEVER use placeholders like [Your Name], [Your Email], [Your City]. Contact details will be injected separately — omit the contact block entirely from your output.
3. NEVER alter job titles, company names, or employment dates. Copy them exactly.
4. Only list skills with demonstrable experience in the master CV. Do NOT include "learning", "basic", or "familiar with" qualifiers in Core Competencies.
5. Do NOT echo the job description or target summary back in the output.
6. Use consistent markdown: **bold** must open and close properly. No orphan `**` markers.

OUTPUT STRUCTURE (in this exact order):

## Professional Summary
[3-4 lines tailored to the target role, using keywords from the job description where truthful]

## Core Competencies
[8-10 bullets, mirroring the job description's language where accurate]

## Professional Experience
[Reorder roles by relevance to the target job. Reframe bullets using job-relevant language, but keep all facts intact.]

## Education & Certifications

---

## Cover Letter Draft
[Maximum 200 words, addressed "Dear Hiring Manager"]

## Cover Letter Talking Points
[3 bullets — each tied to a specific role or achievement]

## Match Score: X/10
[2-3 sentences: Strengths / Gaps / Framing strategy]
"""
DEFAULT_KEYWORDS = [
    "sales",
    "account",
    "cloud",
    "support",
    "incident",
    "service",
    "sla",
    "management",
    "cybersecurity",
    "firewall",
    "technical",
    "stakeholder",
    "azure",
    "linux",
    "jira",
    "crm",
    "saas",
    "operations",
    "vendor",
    "customer",
    "escalation",
]


def load_master_cv(path: str = "master_cv.txt") -> str:
    """Load the master CV from a file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_jobs_from_csv(filename: str = "jobs_found.csv") -> List[Dict[str, str]]:
    """Load jobs from a search results CSV file."""
    jobs = []
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(row)
    return jobs


def load_config(path: str = CONFIG_PATH) -> Dict[str, Any]:
    """Load the prompt and keyword configuration from JSON."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    config.setdefault("keywords", DEFAULT_KEYWORDS)
    config.setdefault("default_top", 3)
    config.setdefault("workers", 5)
    config.setdefault("prompt_template", DEFAULT_PROMPT_TEMPLATE)
    return config


def normalize_tokens(text: str) -> set:
    """Return a set of normalized lowercase tokens from the text."""
    return set(re.findall(r"\b[a-z]{3,}\b", text.lower()))


def estimate_match_score(master_cv: str, job_title: str, job_description: str, keywords: List[str]) -> int:
    """Estimate a job relevance score based on keyword overlap and title relevance."""
    master_terms = normalize_tokens(master_cv)
    job_terms = normalize_tokens(f"{job_title} {job_description}")
    if not job_terms:
        return 1

    overlap = master_terms & job_terms
    overlap_ratio = len(overlap) / len(job_terms)
    keyword_matches = sum(
        1 for kw in keywords if kw.lower() in master_cv.lower() and kw.lower() in job_description.lower()
    )
    title_keywords = normalize_tokens(job_title)
    title_match = len(title_keywords & master_terms)
    score = round(min(10, overlap_ratio * 7 + keyword_matches * 0.7 + min(title_match, 3) * 0.8))
    return max(score, 1)


def build_tailoring_prompt(
    config: Dict[str, Any],
    master_cv: str,
    job_title: str,
    company: str,
    job_description: str,
) -> str:
    """Build the Gemini prompt using the stored template."""
    template = config.get("prompt_template", DEFAULT_PROMPT_TEMPLATE)
    return template.format(
        job_title=job_title,
        company=company,
        job_description=job_description[:3000],
        master_cv=master_cv,
    )


def clean_output(text: str) -> str:
    # Remove any lingering placeholder brackets
    text = re.sub(r'\[Your[^\]]*\]', '', text)
    # Fix orphan ** markers (e.g. "Strategic Planning:**" -> "**Strategic Planning:**")
    text = re.sub(r'(?<!\*)(\w[\w ]+?):\*\*', r'**\1:**', text)
    # Collapse multiple spaces
    text = re.sub(r'  +', ' ', text)
    # Collapse 3+ blank lines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove any echoed "TARGET JOB SUMMARY" blocks if the AI slips up
    text = re.sub(r'TARGET JOB SUMMARY:.*?(?=\n## |\n# |\Z)', '', text, flags=re.DOTALL)

    # Fix broken bold patterns like **C**RM Strategy:** -> **CRM Strategy:**
    # Strategy: find lines with 3+ ** markers and collapse them
    def fix_broken_bold(line):
        # If a line has an odd number of ** markers, something's wrong
        count = line.count('**')
        if count >= 3:
            # Strip ALL ** then re-wrap the "label:" portion
            stripped = line.replace('**', '')
            # Match "Label: description" and bold the label
            m = re.match(r'^(\s*[-*]\s*)([^:]+):\s*(.*)$', stripped)
            if m:
                prefix, label, rest = m.groups()
                return f"{prefix}**{label.strip()}:** {rest}".rstrip()
        return line

    text = '\n'.join(fix_broken_bold(line) for line in text.split('\n'))

    # Final safety: collapse any remaining ****  (empty bold)
    text = re.sub(r'\*{4,}', '**', text)

    return text.strip()


def validate_metrics(tailored_output: str, master_cv: str) -> List[str]:
    """Extract numeric claims from tailored output and check against master CV."""
    warnings = []
    # Strip the Match Score section from tailored_output
    match_score_pattern = re.compile(r'## Match Score.*?(?=##|$)', re.DOTALL)
    tailored_output = match_score_pattern.sub('', tailored_output).strip()
    
    # Remove phone numbers (e.g. +36 XX XXX XXXX) to avoid extracting country codes as metrics
    tailored_output = re.sub(r'\+\d+\s+[\dX\s]+', '', tailored_output)
    master_cv = re.sub(r'\+\d+\s+[\dX\s]+', '', master_cv)
    
    # Regex to find numbers: $digits, digits%, digitsM, digitsK, digits.digits, digits
    # But exclude 4-digit years
    number_pattern = re.compile(r'\$?\d+(?:\.\d+)?(?:%|[MK])?')
    tailored_numbers = set(number_pattern.findall(tailored_output))
    master_numbers = set(number_pattern.findall(master_cv))
    
    # Exclude 4-digit years from tailored_numbers
    tailored_numbers = {n for n in tailored_numbers if not (len(n) == 4 and n.isdigit())}
    
    for num in tailored_numbers:
        if num not in master_numbers:
            warnings.append(f"Hallucinated metric: {num}")
    
    return warnings


def call_gemini_with_retries(prompt: str, max_retries: int = 5) -> str:
    """Send a Gemini request with retry/backoff and rate-limit handling."""
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug("Sending Gemini prompt (attempt %d)", attempt)
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=genai.types.GenerateContentConfig(temperature=0.2)
            )
            return response.text
        except Exception as exc:
            message = str(exc).lower()
            is_rate_limit = "429" in message or "rate limit" in message or "quota" in message
            is_transient = "timeout" in message or "502" in message or "503" in message or "504" in message
            if attempt >= max_retries or not (is_rate_limit or is_transient):
                logger.exception("Gemini request failed permanently on attempt %d", attempt)
                raise

            wait = 2 ** attempt + random.random()
            logger.warning(
                "Gemini request failed (%s). Retrying in %.1f seconds (attempt %d/%d)",
                exc,
                wait,
                attempt,
                max_retries,
            )
            time.sleep(wait)


def tailor_cv(
    config: Dict[str, Any],
    master_cv: str,
    job_title: str,
    company: str,
    job_description: str,
) -> str:
    """Call Gemini to tailor the CV for a specific job."""
    prompt = build_tailoring_prompt(config, master_cv, job_title, company, job_description)
    response = call_gemini_with_retries(prompt)
    return clean_output(response)


def safe_filename(name: str) -> str:
    """Sanitize a string for use in filenames."""
    # Replace special chars with underscore
    safe = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Collapse multiple spaces
    safe = re.sub(r'\s+', ' ', safe)
    # Strip leading/trailing whitespace and dots
    safe = safe.strip(' .')
    # Cap at 100 chars
    if len(safe) > 100:
        safe = safe[:100]
    return safe


def save_tailored_cv(content: str, job_title: str, company: str, output_dir: str = "tailored_cvs") -> str:
    """Save the tailored CV to a timestamped file."""
    os.makedirs(output_dir, exist_ok=True)
    safe_title = safe_filename(job_title)
    safe_company = safe_filename(company)
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{timestamp}_{safe_company}_{safe_title}.txt"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def rank_jobs(jobs: List[Dict[str, str]], master_cv: str, keywords: List[str]) -> List[Dict[str, str]]:
    """Add an estimated match score to each job and return jobs sorted by score."""
    ranked = []
    for job in jobs:
        title = job.get("job_title", "")
        description = job.get("description_snippet", "")
        score = estimate_match_score(master_cv, title, description, keywords)
        job_copy = dict(job)
        job_copy["match_score"] = score
        ranked.append(job_copy)
    return sorted(ranked, key=lambda j: j["match_score"], reverse=True)


def parse_job_selection(
    args: argparse.Namespace,
    jobs: List[Dict[str, str]],
    master_cv: str,
    config: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Select jobs using CLI options instead of interactive input."""
    ranked = rank_jobs(jobs, master_cv, config["keywords"])

    if args.list:
        return ranked

    if args.indices:
        indices = [int(x.strip()) for x in args.indices.split(",") if x.strip().isdigit()]
        return [ranked[i] for i in indices if 0 <= i < len(ranked)]

    if args.all:
        return ranked

    top_n = args.top if args.top is not None else config.get("default_top", 3)
    return ranked[:top_n]


def print_job_preview(jobs: List[Dict[str, str]], limit: int = 20) -> None:
    """Print a preview of jobs with their match score."""
    logger.info("Available jobs in CSV:")
    for idx, job in enumerate(jobs[:limit]):
        logger.info("  [%d] %s (%s)", idx, job.get('job_title', 'N/A'), job.get('company', 'N/A'))
        logger.info("      Score: %s", job.get('match_score', 'N/A'))
        logger.info("      Location: %s", job.get('location', 'N/A'))


def tailor_job(job: Dict[str, str], config: Dict[str, Any], master_cv: str, output_dir: str) -> str:
    title = job.get("job_title", "Unknown Role")
    company = job.get("company", "Unknown Company")
    description = job.get("description_snippet", "No description available")
    apply_link = job.get("apply_link", "N/A")
    score = job.get("match_score", estimate_match_score(master_cv, title, description, config["keywords"]))
    logger.info("Tailoring for: %s at %s (Score: %s)", title, company, score)
    tailored = tailor_cv(config, master_cv, title, company, description)
    final_cv = f"{CONTACT_BLOCK}\n\n{tailored}"
    path = save_tailored_cv(final_cv, title, company, output_dir)
    logger.info("Saved tailored CV: %s", path)
    logger.debug("Apply link: %s", apply_link)
    # Extract match score from final_cv
    match = re.search(r'Match Score: (\d+)/10', final_cv)
    if match:
        match_score = match.group(1)
        logger.info("✅ Tailored: %s — %s (Match: %s/10)", company, title, match_score)
    
    # Validate metrics
    warnings = validate_metrics(final_cv, master_cv)
    if warnings:
        for w in warnings:
            logger.warning(w)
        warnings_file = path.replace('.txt', '_warnings.txt')
        with open(warnings_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(warnings))
    
    return path


def create_tailored_cvs(
    master_cv_path: str,
    jobs_csv: str,
    output_dir: str,
    all_jobs: bool,
    indices: str,
    top: int,
    list_jobs: bool,
    config_path: str,
    workers: int,
) -> None:
    """Load jobs, select them, and generate tailored CVs."""
    config = load_config(config_path)
    master_cv = load_master_cv(master_cv_path)
    jobs = load_jobs_from_csv(jobs_csv)
    if not jobs:
        logger.warning("No jobs found in %s.", jobs_csv)
        return

    selected_jobs = parse_job_selection(
        argparse.Namespace(all=all_jobs, indices=indices, top=top, list=list_jobs),
        jobs,
        master_cv,
        config,
    )

    if list_jobs:
        print_job_preview(selected_jobs)
        return

    if not selected_jobs:
        logger.warning("No jobs selected. Use --all, --top, or --indices.")
        return

    logger.info("CV Tailoring Bot - Starting (%d jobs)", len(selected_jobs))
    logger.info("Loaded master CV (%d characters)", len(master_cv))

    config["workers"] = workers or config.get("workers", 2)
    max_workers = min(config["workers"], len(selected_jobs))
    successes = []
    failures = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_job = {
            executor.submit(tailor_job, job, config, master_cv, output_dir): job
            for job in selected_jobs
        }
        with tqdm(total=len(selected_jobs), desc="Tailoring CVs", unit="job") as pbar:
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                try:
                    path = future.result()
                    successes.append((job, path))
                except Exception as exc:
                    error_msg = str(exc)
                    failures.append((job, error_msg))
                    logger.error(
                        "Tailoring failed for %s at %s: %s",
                        job.get("job_title", "Unknown Role"),
                        job.get("company", "Unknown Company"),
                        error_msg,
                    )
                pbar.update(1)

    # Print summary
    logger.info("✅ Succeeded: %d", len(successes))
    logger.info("❌ Failed: %d", len(failures))
    if failures:
        for job, error in failures:
            logger.info("  - [%d] %s at %s: %s", 
                       selected_jobs.index(job), 
                       job.get("job_title", "Unknown Role"), 
                       job.get("company", "Unknown Company"), 
                       error)
        # Write to failures.log
        with open("failures.log", "w", encoding="utf-8") as f:
            for job, error in failures:
                f.write(f"[{selected_jobs.index(job)}] {job.get('job_title', 'Unknown Role')} at {job.get('company', 'Unknown Company')}: {error}\n")

    logger.info("Done! Check the tailored CVs in the output folder.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tailor your master CV for selected jobs using Gemini AI.")
    parser.add_argument("--jobs-csv", default="jobs_found.csv", help="Path to the CSV with job listings.")
    parser.add_argument("--master-cv", default="master_cv.txt", help="Path to your master CV text file.")
    parser.add_argument("--output-dir", default="tailored_cvs", help="Directory to save tailored CVs.")
    parser.add_argument("--config", default=CONFIG_PATH, help="Path to the tailoring config JSON file.")
    parser.add_argument("--all", action="store_true", help="Tailor CVs for all jobs in the CSV.")
    parser.add_argument("--indices", help="Comma-separated job indices to tailor, e.g. 0,2,5.")
    parser.add_argument("--top", type=int, help="Tailor the top N jobs by estimated fit.")
    parser.add_argument("--list", action="store_true", help="Print a ranked job preview and exit.")
    parser.add_argument("--workers", type=int, default=2, help="Number of concurrent GPT requests.")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR).")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    configure_logging(args.log_level)
    
    # Validate API key and master CV before proceeding
    if not validate_gemini_api_key():
        logger.error("Cannot proceed without valid Gemini API key.")
        sys.exit(1)
    
    if not validate_master_cv(args.master_cv):
        logger.error("Cannot proceed without valid master CV.")
        sys.exit(1)
    
    create_tailored_cvs(
        master_cv_path=args.master_cv,
        jobs_csv=args.jobs_csv,
        output_dir=args.output_dir,
        all_jobs=args.all,
        indices=args.indices,
        top=args.top,
        list_jobs=args.list,
        config_path=args.config,
        workers=args.workers,
    )
