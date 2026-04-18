# Job Hunter Bot

A Python automation tool that searches for job listings, tailors your CV to each opportunity using AI, and generates professional PDF documents—all in one workflow.

## Overview

Job Hunter Bot streamlines the job application process by:
1. **Searching** job listings from multiple sources via the JSearch API
2. **Tailoring** your master CV to each job using Google Gemini AI
3. **Generating** professional PDF CVs ready for submission

Perfect for IT sales, account management, and other roles where customization matters.

---

## Features

- **Automated Job Search**: Query multiple job titles and fetch 171+ listings in seconds
- **AI-Powered CV Tailoring**: Uses Google Gemini to rewrite your CV, matching job descriptions and keywords
- **PDF Generation**: Converts tailored CVs to professional, ATS-friendly PDFs with formatting
- **Duplicate Detection**: Removes duplicate job listings automatically
- **Windows-Compatible**: Full UTF-8 and emoji support for Windows console

---

## Requirements

- **Python 3.10+**
- **Virtual Environment** (recommended)
- **API Keys**:
  - `RAPIDAPI_KEY` (for JSearch job listings)
  - `GEMINI_API_KEY` (for Google Gemini AI)

---

## Installation

### 1. Clone or Download the Project
```bash
cd job-hunter-bot
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install google-genai fpdf requests python-dotenv
```

## Running Tests

Run the unit tests with:
```bash
python -m unittest discover tests
```

### 4. Set Up Environment Variables
Copy the sample file and add your real API keys locally:
```bash
cp .env.example .env           # macOS/Linux
```
```powershell
Copy-Item .env.example .env    # Windows PowerShell
```

Then edit `.env`:
```env
RAPIDAPI_KEY=your_rapidapi_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**How to get API keys:**
- **RAPIDAPI_KEY**: Sign up at [RapidAPI](https://rapidapi.com), subscribe to [JSearch](https://rapidapi.com/letscrape-6bRBa3QQKCUaDXX8p/api/jsearch)
- **GEMINI_API_KEY**: Get free access at [Google AI Studio](https://aistudio.google.com/apikey)

---

## Privacy and Local Templates
This project keeps sensitive data local by design:
- `.env` is ignored by Git and should never be committed.
- `master_cv.txt` is also ignored by Git and should contain your private CV details locally only.
- Use `master_cv_template.txt` as a safe example if you want a non-sensitive starting point.

If you have already committed sensitive data, consider rewriting history with tools like `git filter-repo` or `git filter-branch`.
For example:
```bash
git filter-repo --path master_cv.txt --invert-paths
```
Or, for older Git versions:
```bash
git filter-branch --index-filter 'git rm --cached --ignore-unmatch master_cv.txt' -- --all
```

Be aware that rewriting history changes commit hashes and should be used carefully, especially on shared branches.

---

## Usage

### Step 1: Search for Jobs
```bash
python search_jobs.py
```
Searches for jobs matching your configured queries (IT Sales Manager, Account Manager, etc.) and saves results to `jobs_found.csv`.

**Output**: `jobs_found.csv` with 171 unique listings

### Step 2: Tailor Your CV
```bash
python tailor_cv.py --all --config tailor_config.json
```
This non-interactive CLI mode tailors your master CV for every job in `jobs_found.csv` and saves results to `tailored_cvs/`.

Other useful options:
```bash
python tailor_cv.py --top 5 --config tailor_config.json --workers 2 --log-level INFO
python tailor_cv.py --indices 0,2,4 --config tailor_config.json --workers 2 --log-level INFO
python tailor_cv.py --list --config tailor_config.json --log-level DEBUG
```

### Step 3: Generate PDFs
```bash
python generate_pdf.py --all
```
Converts all tailored CV `.txt` files into PDFs and saves them to `pdf_cvs/`.

Other useful options:
```bash
python generate_pdf.py --indices 0,1
python generate_pdf.py --pattern Cyber_Security
```

### Full Pipeline
```bash
python run_all.py --top 5
```
Searches for jobs, tailors the top 5 best-matching CVs, and generates PDFs automatically.

**Output**: `jobs_found.csv`, `tailored_cvs/`, and `pdf_cvs/`

### Local Dashboard
```bash
python dashboard.py
```
Open your browser at `http://127.0.0.1:5000` and use the dashboard to:
- choose query, country, location, employment type, and remote filtering
- view and select search results
- tailor selected jobs and generate PDFs
- review previously processed job history

---

## CLI Reference

Use these exact commands to run each script without interactive prompts.

### Search jobs
```bash
python search_jobs.py --queries "IT Sales Manager" "Technical Account Manager" --country gb --num-pages 3 --preview 5
```

### Tailor CVs
```bash
python tailor_cv.py --all --config tailor_config.json
```

Tailor the top 5 matched jobs:
```bash
python tailor_cv.py --top 5 --config tailor_config.json
```

Tailor specific job indices:
```bash
python tailor_cv.py --indices 0,2,4 --config tailor_config.json
```

List available jobs with estimated fit:
```bash
python tailor_cv.py --list --config tailor_config.json
```

### Generate PDFs
```bash
python generate_pdf.py --all
```

Convert specific tailored CV files:
```bash
python generate_pdf.py --indices 0,1
```

Convert files matching a keyword:
```bash
python generate_pdf.py --pattern Cyber_Security
```

### Run the whole pipeline
```bash
python run_all.py --top 5 --config tailor_config.json --workers 2 --log-level INFO
```

---

## Project Structure

```
job-hunter-bot/
├── search_jobs.py           # Job search automation
├── tailor_cv.py             # AI-powered CV tailoring
├── generate_pdf.py          # PDF generation
├── master_cv_template.txt   # Safe CV template example
├── master_cv.txt            # Your private master CV (local only, ignored by git)
├── dashboard.py             # Local Flask dashboard for search, selection, preview, and PDF download
├── jobs_found.csv           # Search results (auto-generated)
├── tailored_cvs/            # Tailored CVs (auto-generated)
├── pdf_cvs/                 # Generated PDFs (auto-generated)
├── tailor_config.json       # AI prompt and keyword scoring configuration
├── .env.example             # Example environment variables file
├── .env                     # API keys (create manually, ignored by git)
├── .gitignore               # Git configuration
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## File Descriptions

| File | Purpose |
|------|---------|
| `search_jobs.py` | Queries JSearch API for job listings across multiple roles/regions |
| `tailor_cv.py` | Uses Google Gemini to customize your CV for each job posting |
| `generate_pdf.py` | Converts tailored text CVs to professional PDF documents |
| `master_cv.txt` | Your complete work history; used as source for all tailored versions |
| `jobs_found.csv` | Database of job listings from the search (171+ rows) |
| `.env` | Sensitive configuration (API keys) — add to `.gitignore` |

---

## Configuration

### Customize Job Search

Edit `search_jobs.py`:
```python
SEARCH_QUERIES = [
    "IT Sales Manager",           # Add/remove job titles
    "IT Account Manager",
    "Your Job Title Here"
]
COUNTRY = "gb"                    # Change country code (gb, us, de, nl, etc.)
NUM_PAGES = "3"                   # Number of pages per query
REMOTE_ONLY = False               # Set True for remote-only jobs
```

### Customize CV Tailoring

Edit `tailor_config.json` to update the prompt template, keyword scoring, and default selection count.

Edit `tailor_cv.py`:
```python
MODEL_NAME = "gemini-flash-latest"  # Change Gemini model if needed
```

---

## How It Works

### 1. Job Search (`search_jobs.py`)
- Makes API calls to JSearch for each search query
- Fetches job title, company, location, description, apply link
- Removes duplicates based on apply link
- Exports to CSV with 171 unique listings

### 2. CV Tailoring (`tailor_cv.py`)
- Loads your master CV from `master_cv.txt`
- Reads job descriptions from `jobs_found.csv`
- Sends to Google Gemini with tailoring prompt
- Gemini rewrites CV to emphasize matching skills/keywords
- Saves as timestamped text files in `tailored_cvs/`
- Includes AI-generated "Match Score" and "Cover Letter Talking Points"

### 3. PDF Generation (`generate_pdf.py`)
- Reads tailored CVs from `tailored_cvs/`
- Formats with professional FPDF styling (blue headers, fonts, spacing)
- Normalizes Unicode for Latin-1 PDF compatibility
- Outputs PDF files to `pdf_cvs/` ready for submission

---

## Technologies Used

- **Python 3.14.4** — Core language
- **Google Gemini AI** — CV tailoring and optimization
- **google-genai 1.73.1** — Gemini API client
- **FPDF2** — PDF generation and formatting
- **RapidAPI / JSearch** — Job listing aggregation
- **python-dotenv** — Environment variable management

---

## Example Workflow

```bash
# 1. Search for jobs
python search_jobs.py
# Output: 171 jobs in jobs_found.csv

# 2. Tailor CVs for top 5 opportunities
python tailor_cv.py
# Select: 0,1,2,3,4
# Output: 5 tailored CVs in tailored_cvs/

# 3. Generate PDFs
python generate_pdf.py
# Select: A (all)
# Output: 5 PDF files in pdf_cvs/

# 4. Submit applications
# Upload PDFs from pdf_cvs/ to job sites
```

---

## Demo

### Example Non-Interactive Run
```bash
python run_all.py --top 5
```

This command runs the full pipeline:
- searches for jobs using the configured keywords
- saves results to `jobs_found.csv`
- tailors the top 5 jobs to your master CV
- generates professional PDFs in `pdf_cvs/`

### Output Preview
- `jobs_found.csv` — all collected listings
- `tailored_cvs/` — text CVs created by Gemini
- `pdf_cvs/` — final application-ready PDF resumes

---

## Troubleshooting

### API Key Errors
- Verify `.env` file exists in project root
- Check API keys are valid and have active subscriptions
- RAPIDAPI_KEY must have JSearch API enabled

### Job Search Timeout
- API may rate-limit after multiple queries
- Reduce `NUM_PAGES` or run at different time
- Check internet connection

### PDF Generation Errors
- Ensure `tailored_cvs/` contains `.txt` files
- Master CV must exist at `master_cv.txt`
- Check that filenames don't contain invalid characters

### Windows Console Issues
- UTF-8 reconfiguration is automatic (see `sys.stdout.reconfigure()`)
- If issues persist, run: `chcp 65001` in command prompt

---

## Performance Tips

- **Batch Processing**: Use `[A] Convert ALL` in `generate_pdf.py` for multiple PDFs
- **Selective Tailoring**: Only tailor top 10-15 jobs to minimize API costs
- **Cache Results**: Keep `jobs_found.csv`; re-run only when updating job pool
- **Parallel API Calls**: Current implementation is sequential; can be optimized with async

---

## Future Enhancements

- [ ] Async API calls for faster job searching
- [ ] Email integration to auto-send applications
- [ ] LinkedIn profile scraping
- [ ] ATS keyword scoring before submission
- [ ] Web UI dashboard for job tracking
- [ ] Interview preparation guides from job descriptions

---

## License

This project is open source and available under the MIT License.

---

## Author

**Gábor Krankovics**  
Budapest, Hungary  
[krankovics.gabor@gmail.com](mailto:krankovics.gabor@gmail.com)

---

## Support

For issues, questions, or contributions:
1. Check the Troubleshooting section above
2. Verify API keys and environment setup
3. Review script output for specific error messages
4. Consider opening an issue on GitHub (if applicable)

---

**Last Updated**: April 16, 2026  
**Version**: 1.0.0
