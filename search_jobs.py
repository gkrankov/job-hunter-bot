import requests
import csv
import os
from dotenv import load_dotenv
from datetime import datetime

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("RAPIDAPI_KEY")

# === CONFIGURE YOUR SEARCH HERE ===
SEARCH_QUERIES = [
    "IT Sales Manager",
    "IT Account Manager", 
    "Technical Account Manager",
    "IT Sales Executive",
    "SaaS Account Executive",
    "IT Support Manager"
]
COUNTRY = "gb"          # gb, us, de, nl, etc.
NUM_PAGES = "3"          # pages per query (save your free API calls)
REMOTE_ONLY = False      # set True if you want remote jobs only
# ===================================

def search_jobs(query):
    """Search for jobs using JSearch API"""
    url = "https://jsearch.p.rapidapi.com/search"
    
    params = {
        "query": f"{query} in United Kingdom",  # change location to yours
        "page": "1",
        "num_pages": NUM_PAGES,
        "date_posted": "week",          # today, 3days, week, month
        "remote_jobs_only": str(REMOTE_ONLY).lower(),
    }
    
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"  ❌ Error searching '{query}': {e}")
        return []

def save_to_csv(all_jobs, filename="jobs_found.csv"):
    """Save all jobs to a CSV file"""
    if not all_jobs:
        print("No jobs to save.")
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
    
    print(f"\n✅ Saved {len(all_jobs)} jobs to {filename}")

def main():
    print("🔍 Job Hunter Bot — Starting Search...\n")
    
    all_jobs = []
    seen_links = set()  # avoid duplicates
    
    for query in SEARCH_QUERIES:
        print(f"  Searching: '{query}'...")
        jobs = search_jobs(query)
        
        for job in jobs:
            link = job.get("job_apply_link", "")
            if link not in seen_links:
                seen_links.add(link)
                all_jobs.append(job)
        
        print(f"    Found {len(jobs)} results ({len(all_jobs)} unique total)")
    
    print(f"\n📊 Total unique jobs found: {len(all_jobs)}")
    
    # Save results
    save_to_csv(all_jobs)
    
    # Print top 5 to terminal
    print("\n🏆 Top 5 Results Preview:")
    print("-" * 60)
    for job in all_jobs[:5]:
        print(f"  📌 {job.get('job_title')}")
        print(f"     🏢 {job.get('employer_name')}")
        print(f"     📍 {job.get('job_city', 'N/A')}")
        print(f"     🔗 {job.get('job_apply_link', 'N/A')[:80]}")
        print()

if __name__ == "__main__":
    main()
