import csv
import json
import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from generate_pdf import generate_pdf_from_text
from search_jobs import (
    JOB_HISTORY_FILE,
    append_job_history,
    create_session,
    filter_new_jobs,
    load_job_history,
    save_to_csv,
    search_jobs,
)
from tailor_cv import load_config, load_master_cv, save_tailored_cv, tailor_cv

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-flask-key")
JOB_CACHE_PATH = "last_search.json"
MASTER_CV_PATH = "master_cv.txt"
TEMPLATE_CV_PATH = "master_cv_template.txt"
CONFIG_PATH = "tailor_config.json"

COUNTRY_OPTIONS = [
    ("gb", "United Kingdom"),
    ("us", "United States"),
    ("de", "Germany"),
    ("nl", "Netherlands"),
]
EMPLOYMENT_TYPES = ["Any", "Full-time", "Part-time", "Contract", "Internship", "Temporary"]


def save_last_search(jobs):
    with open(JOB_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)


def load_last_search():
    if not os.path.exists(JOB_CACHE_PATH):
        return []
    with open(JOB_CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_selected_jobs(jobs, country, location, employment_type, remote_only):
    def text(value):
        return (value or "").lower()

    if country:
        jobs = [job for job in jobs if text(job.get("job_country")) == country.lower()]
    if location:
        jobs = [
            job
            for job in jobs
            if location.lower() in text(job.get("job_city"))
            or location.lower() in text(job.get("employer_name"))
            or location.lower() in text(job.get("company"))
        ]
    if employment_type and employment_type != "Any":
        jobs = [job for job in jobs if employment_type.lower() in text(job.get("job_employment_type"))]
    if remote_only:
        jobs = [
            job
            for job in jobs
            if text(job.get("remote")) == "true"
            or "remote" in text(job.get("job_employment_type"))
        ]
    return jobs


def get_master_cv_path():
    return MASTER_CV_PATH if os.path.exists(MASTER_CV_PATH) else TEMPLATE_CV_PATH


@app.route("/")
def index():
    history_links = load_job_history(JOB_HISTORY_FILE)
    return render_template(
        "index.html",
        country_options=COUNTRY_OPTIONS,
        employment_types=EMPLOYMENT_TYPES,
        history_count=len(history_links),
    )


@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query", "IT Sales Manager")
    country = request.form.get("country", "gb")
    location = request.form.get("location", "")
    employment_type = request.form.get("employment_type", "Any")
    remote_only = request.form.get("remote_only") == "on"
    num_pages = int(request.form.get("num_pages", 2))

    session = create_session()
    history_links = load_job_history(JOB_HISTORY_FILE)
    raw_jobs = search_jobs(query, country, num_pages, remote_only, session, history_links)
    filtered_jobs = filter_selected_jobs(raw_jobs, country, location, employment_type, remote_only)

    if not filtered_jobs:
        flash("No new jobs found for the selected filters.", "warning")

    save_last_search(filtered_jobs)
    save_to_csv(filtered_jobs, filename="jobs_found.csv")

    return render_template(
        "results.html",
        jobs=filtered_jobs,
        query=query,
        country=country,
        location=location,
        employment_type=employment_type,
        remote_only=remote_only,
    )


@app.route("/tailor", methods=["POST"])
def tailor():
    selected_indices = request.form.getlist("selected_job")
    jobs = load_last_search()
    if not selected_indices:
        flash("Please select at least one job to tailor.", "danger")
        return redirect(url_for("index"))

    config = load_config(CONFIG_PATH)
    master_cv = load_master_cv(get_master_cv_path())
    selected_jobs = []
    tailored_results = []

    for index in selected_indices:
        try:
            job = jobs[int(index)]
        except (ValueError, IndexError):
            continue
        selected_jobs.append(job)
        tailored = tailor_cv(config, master_cv, job.get("job_title", "Unknown Role"), job.get("employer_name", "Unknown Company"), job.get("job_description", ""))
        text_path = save_tailored_cv(tailored, job.get("job_title", "job"), job.get("employer_name", "company"), "tailored_cvs")
        pdf_path = generate_pdf_from_text(text_path, "pdf_cvs")
        tailored_results.append(
            {
                "title": job.get("job_title", "Unknown Role"),
                "company": job.get("employer_name", "Unknown Company"),
                "text_path": text_path,
                "pdf_path": pdf_path,
                "pdf_name": os.path.basename(pdf_path),
            }
        )

    append_job_history(selected_jobs, JOB_HISTORY_FILE)
    flash(f"Tailored {len(tailored_results)} job(s) and generated PDFs.", "success")
    return render_template("tailor.html", tailored_results=tailored_results)


@app.route("/download/<path:filename>")
def download(filename):
    file_path = os.path.join("pdf_cvs", filename)
    if not os.path.exists(file_path):
        flash("PDF file not found.", "danger")
        return redirect(url_for("index"))
    return send_file(file_path, as_attachment=True)


@app.route("/history")
def history():
    if not os.path.exists(JOB_HISTORY_FILE):
        history_rows = []
    else:
        with open(JOB_HISTORY_FILE, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            history_rows = list(reader)
    return render_template("history.html", history=history_rows)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
