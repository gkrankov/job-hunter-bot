#!/usr/bin/env python3
"""
Job Hunter Bot - Unified CLI

A single entry point for all job hunting operations:
  - Search for jobs
  - Tailor CVs
  - Generate PDFs
  - Run the full pipeline

Usage:
  python job_hunter.py search --queries "..." --country gb
  python job_hunter.py tailor --top 10
  python job_hunter.py generate-pdf --all
  python job_hunter.py run --pipeline all --top 5
"""

import argparse
import logging
import sys

from run_all import main as run_pipeline
from search_jobs import main as search_main
from tailor_cv import create_tailored_cvs, configure_logging as tailor_configure_logging
from tailor_cv import parse_args as tailor_parse_args
from generate_pdf import main as generate_pdf_main
from validation import validate_all_config

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO"):
    """Configure logging for all modules."""
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=getattr(logging, level.upper(), logging.INFO),
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_parser():
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="Job Hunter Bot - Automated job search and CV tailoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for jobs
  %(prog)s search --queries "IT Sales Manager" "Account Executive" --country gb

  # Tailor CVs for top 10 matches
  %(prog)s tailor --top 10

  # Generate PDFs for all tailored CVs
  %(prog)s generate-pdf --all

  # Run full pipeline: search -> tailor -> generate PDFs
  %(prog)s run --top 5

  # Validate configuration and API keys
  %(prog)s validate
        """,
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search subcommand
    search_parser = subparsers.add_parser("search", help="Search for jobs")
    search_parser.add_argument("--queries", nargs="+", help="Job search queries")
    search_parser.add_argument("--country", default="gb", help="Country code (gb, us, de, nl)")
    search_parser.add_argument("--num-pages", type=int, default=3, help="Number of pages per query")
    search_parser.add_argument("--remote-only", action="store_true", help="Fetch only remote jobs")
    search_parser.add_argument("--output", default="jobs_found.csv", help="CSV file path for results")
    search_parser.add_argument("--preview", type=int, default=5, help="Number of top jobs to preview")
    search_parser.add_argument("--workers", type=int, default=3, help="Number of worker threads")

    # Tailor subcommand
    tailor_parser = subparsers.add_parser("tailor", help="Tailor CVs for jobs")
    tailor_parser.add_argument("--jobs-csv", default="jobs_found.csv", help="CSV with job listings")
    tailor_parser.add_argument("--master-cv", default="master_cv.txt", help="Path to master CV")
    tailor_parser.add_argument("--output-dir", default="tailored_cvs", help="Output directory for CVs")
    tailor_parser.add_argument("--config", default="tailor_config.json", help="Config JSON file")
    tailor_parser.add_argument("--all", action="store_true", help="Tailor all jobs")
    tailor_parser.add_argument("--indices", help="Comma-separated indices (0,2,5)")
    tailor_parser.add_argument("--top", type=int, help="Top N jobs by match score")
    tailor_parser.add_argument("--list", action="store_true", help="List available jobs and exit")
    tailor_parser.add_argument("--workers", type=int, default=5, help="Number of concurrent workers")

    # Generate PDF subcommand
    generate_parser = subparsers.add_parser("generate-pdf", help="Generate PDFs from tailored CVs")
    generate_parser.add_argument("--all", action="store_true", help="Convert all tailored CVs")
    generate_parser.add_argument("--indices", help="Comma-separated indices (0,1,2)")
    generate_parser.add_argument("--pattern", help="Pattern to match filenames")
    generate_parser.add_argument("--output-dir", default="pdf_cvs", help="Output directory for PDFs")

    # Run (pipeline) subcommand
    run_parser = subparsers.add_parser("run", help="Run full pipeline: search -> tailor -> generate PDFs")
    run_parser.add_argument("--queries", nargs="+", help="Job search queries")
    run_parser.add_argument("--country", default="gb", help="Country code")
    run_parser.add_argument("--num-pages", type=int, default=3, help="Pages per query")
    run_parser.add_argument("--remote-only", action="store_true", help="Remote jobs only")
    run_parser.add_argument("--master-cv", default="master_cv.txt", help="Master CV file")
    run_parser.add_argument("--jobs-csv", default="jobs_found.csv", help="Jobs CSV file")
    run_parser.add_argument("--tailored-dir", default="tailored_cvs", help="Tailored CVs directory")
    run_parser.add_argument("--pdf-dir", default="pdf_cvs", help="PDF output directory")
    run_parser.add_argument("--config", default="tailor_config.json", help="Config JSON file")
    run_parser.add_argument("--all-jobs", action="store_true", help="Tailor all jobs")
    run_parser.add_argument("--top", type=int, default=5, help="Top N jobs")
    run_parser.add_argument("--workers", type=int, help="Number of workers")

    # Validate subcommand
    validate_parser = subparsers.add_parser("validate", help="Validate API keys and configuration")

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    setup_logging(args.log_level)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    logger.debug("Command: %s", args.command)

    try:
        if args.command == "search":
            # Convert args to search_main format
            sys.argv = ["search_jobs.py"]
            if args.queries:
                sys.argv.extend(["--queries"] + args.queries)
            if args.country != "gb":
                sys.argv.extend(["--country", args.country])
            if args.num_pages != 3:
                sys.argv.extend(["--num-pages", str(args.num_pages)])
            if args.remote_only:
                sys.argv.append("--remote-only")
            if args.output != "jobs_found.csv":
                sys.argv.extend(["--output", args.output])
            if args.preview != 5:
                sys.argv.extend(["--preview", str(args.preview)])
            if args.workers != 3:
                sys.argv.extend(["--workers", str(args.workers)])
            if args.log_level != "INFO":
                sys.argv.extend(["--log-level", args.log_level])
            search_main()

        elif args.command == "tailor":
            # Convert args to tailor format
            sys.argv = ["tailor_cv.py"]
            if args.jobs_csv != "jobs_found.csv":
                sys.argv.extend(["--jobs-csv", args.jobs_csv])
            if args.master_cv != "master_cv.txt":
                sys.argv.extend(["--master-cv", args.master_cv])
            if args.output_dir != "tailored_cvs":
                sys.argv.extend(["--output-dir", args.output_dir])
            if args.config != "tailor_config.json":
                sys.argv.extend(["--config", args.config])
            if args.all:
                sys.argv.append("--all")
            if args.indices:
                sys.argv.extend(["--indices", args.indices])
            if args.top:
                sys.argv.extend(["--top", str(args.top)])
            if args.list:
                sys.argv.append("--list")
            if args.workers != 5:
                sys.argv.extend(["--workers", str(args.workers)])
            if args.log_level != "INFO":
                sys.argv.extend(["--log-level", args.log_level])
            
            tailor_configure_logging(args.log_level)
            tailor_args = tailor_parse_args()
            create_tailored_cvs(
                master_cv_path=tailor_args.master_cv,
                jobs_csv=tailor_args.jobs_csv,
                output_dir=tailor_args.output_dir,
                all_jobs=tailor_args.all,
                indices=tailor_args.indices,
                top=tailor_args.top,
                list_jobs=tailor_args.list,
                config_path=tailor_args.config,
                workers=tailor_args.workers,
            )

        elif args.command == "generate-pdf":
            # Convert args to generate-pdf format
            sys.argv = ["generate_pdf.py"]
            if args.all:
                sys.argv.append("--all")
            if args.indices:
                sys.argv.extend(["--indices", args.indices])
            if args.pattern:
                sys.argv.extend(["--pattern", args.pattern])
            if args.output_dir != "pdf_cvs":
                sys.argv.extend(["--output-dir", args.output_dir])
            if args.log_level != "INFO":
                sys.argv.extend(["--log-level", args.log_level])
            generate_pdf_main()

        elif args.command == "run":
            # Run the full pipeline
            sys.argv = ["run_all.py"]
            if args.queries:
                sys.argv.extend(["--queries"] + args.queries)
            if args.country != "gb":
                sys.argv.extend(["--country", args.country])
            if args.num_pages != 3:
                sys.argv.extend(["--num-pages", str(args.num_pages)])
            if args.remote_only:
                sys.argv.append("--remote-only")
            if args.master_cv != "master_cv.txt":
                sys.argv.extend(["--master-cv", args.master_cv])
            if args.jobs_csv != "jobs_found.csv":
                sys.argv.extend(["--jobs-csv", args.jobs_csv])
            if args.tailored_dir != "tailored_cvs":
                sys.argv.extend(["--tailored-dir", args.tailored_dir])
            if args.pdf_dir != "pdf_cvs":
                sys.argv.extend(["--pdf-dir", args.pdf_dir])
            if args.config != "tailor_config.json":
                sys.argv.extend(["--config", args.config])
            if args.all_jobs:
                sys.argv.append("--all-jobs")
            if args.top != 5:
                sys.argv.extend(["--top", str(args.top)])
            if args.workers:
                sys.argv.extend(["--workers", str(args.workers)])
            if args.log_level != "INFO":
                sys.argv.extend(["--log-level", args.log_level])
            run_pipeline()

        elif args.command == "validate":
            logger.info("Running configuration validation...")
            if validate_all_config():
                logger.info("✅ All validations passed!")
                sys.exit(0)
            else:
                logger.error("❌ Validation failed. See errors above.")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
