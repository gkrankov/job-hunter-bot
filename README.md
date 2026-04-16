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

### 4. Set Up Environment Variables
Create a `.env` file in the project root:
```env
RAPIDAPI_KEY=your_rapidapi_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**How to get API keys:**
- **RAPIDAPI_KEY**: Sign up at [RapidAPI](https://rapidapi.com), subscribe to [JSearch](https://rapidapi.com/letscrape-6bRBa3QQKCUaDXX8p/api/jsearch)
- **GEMINI_API_KEY**: Get free access at [Google AI Studio](https://aistudio.google.com/apikey)

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
python tailor_cv.py
```
Interactive selection of jobs. The tool uses Google Gemini to tailor your master CV to each opportunity, then saves results to `tailored_cvs/`.

**Example output**:
```
CV Tailoring Bot - Starting...

Loaded master CV (4848 characters)

Found 171 jobs in your CSV

Which jobs do you want to tailor your CV for?

  [0] Technical Sales Manager
  [1] Cyber Security Sales Exec
  [2] Technical Sales Manager (Scientific Industry)
  ...
  [A] Convert ALL

Enter job numbers separated by commas (e.g. 0,3,7): 1

Tailoring CV for 1 jobs...

  Tailoring for: Cyber Security Sales Exec at Unknown Company...
  Saved: tailored_cvs/20260416_Unknown_Company_Cyber_Security_Sales_Exec.txt
  Apply: https://uk.linkedin.com/jobs/view/...
```

### Step 3: Generate PDFs
```bash
python generate_pdf.py
```
Converts tailored CVs to professional PDF format. Interactive menu allows batch conversion.

**Output**: `pdf_cvs/` folder with PDF files ready for submission

---

## Project Structure

```
job-hunter-bot/
├── search_jobs.py           # Job search automation
├── tailor_cv.py             # AI-powered CV tailoring
├── generate_pdf.py          # PDF generation
├── master_cv.txt            # Your master CV template
├── jobs_found.csv           # Search results (auto-generated)
├── tailored_cvs/            # Tailored CVs (auto-generated)
├── pdf_cvs/                 # Generated PDFs (auto-generated)
├── .env                     # API keys (create manually)
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
