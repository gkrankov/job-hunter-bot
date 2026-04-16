import google.genai as genai
import os
import csv
import sys
from dotenv import load_dotenv
from datetime import datetime

# Force UTF-8 console output on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load API keys
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-flash-latest"

def load_master_cv():
    """Load your master CV from file"""
    with open("master_cv.txt", "r", encoding="utf-8") as f:
        return f.read()


def load_jobs_from_csv(filename="jobs_found.csv"):
    """Load jobs from your search results"""
    jobs = []
    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(row)
    return jobs


def tailor_cv(master_cv, job_title, company, job_description):
    """Use Gemini to tailor your CV for a specific job"""
    
    prompt = f"""
You are an expert CV writer and career coach specializing in IT sales 
and account management roles.

I'm applying for this job:

ROLE: {job_title}
COMPANY: {company}
JOB DESCRIPTION:
{job_description[:3000]}

Here is my master CV with all my experience:

{master_cv}

Please create a TAILORED CV that:

1. **Reorders** my experience to highlight what's most relevant to THIS role
2. **Rewrites** bullet points to mirror the language in the job description
3. **Emphasizes** matching skills and keywords from the job posting
4. **Adds a tailored professional summary** (3-4 lines) specific to this role
5. **Keeps it to 2 pages max** — remove less relevant details
6. **Does NOT fabricate** any experience — only reshape what I actually have
7. **Includes keywords** for ATS (Applicant Tracking Systems)

Format the output as a clean, professional CV in plain text.
At the end, add a section called "COVER LETTER TALKING POINTS" with 
3 bullet points I should mention in a cover letter.

Also add a section called "MATCH SCORE" rating how well I match 
this role from 1-10, with a brief explanation.
"""
    
    chat = client.chats.create(model=MODEL_NAME)
    response = chat.send_message(prompt)
    return response.text


def save_tailored_cv(content, job_title, company):
    """Save the tailored CV to a file"""
    os.makedirs("tailored_cvs", exist_ok=True)
    
    safe_title = "".join(c if c.isalnum() or c == " " else "_" for c in job_title)
    safe_company = "".join(c if c.isalnum() or c == " " else "_" for c in company)
    timestamp = datetime.now().strftime("%Y%m%d")
    
    filename = f"tailored_cvs/{timestamp}_{safe_company}_{safe_title}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    return filename


def main():
    print("CV Tailoring Bot - Starting...\n")
    
    master_cv = load_master_cv()
    print(f"Loaded master CV ({len(master_cv)} characters)\n")
    
    jobs = load_jobs_from_csv()
    print(f"Found {len(jobs)} jobs in your CSV\n")
    
    print("Which jobs do you want to tailor your CV for?\n")
    for i, job in enumerate(jobs[:20]):
        print(f"  [{i}] {job.get('job_title', 'N/A')}")
        print(f"      Company: {job.get('company', 'N/A')}")
        print()
    
    selections = input("Enter job numbers separated by commas (e.g. 0,3,7): ")
    selected_indices = [int(x.strip()) for x in selections.split(",") if x.strip().isdigit()]
    
    print(f"\nTailoring CV for {len(selected_indices)} jobs...\n")
    
    for idx in selected_indices:
        if idx < 0 or idx >= len(jobs):
            print(f"  Skipping invalid index: {idx}")
            continue
        job = jobs[idx]
        title = job.get("job_title", "Unknown Role")
        company = job.get("company", "Unknown Company")
        description = job.get("description_snippet", "No description available")
        apply_link = job.get("apply_link", "N/A")
        
        print(f"  Tailoring for: {title} at {company}...")
        tailored = tailor_cv(master_cv, title, company, description)
        filename = save_tailored_cv(tailored, title, company)
        
        print(f"  Saved: {filename}")
        print(f"  Apply: {apply_link}")
        print()
    
    print("=" * 60)
    print("Done! Check the 'tailored_cvs' folder for your CVs.")
    print("=" * 60)


if __name__ == "__main__":
    main()
