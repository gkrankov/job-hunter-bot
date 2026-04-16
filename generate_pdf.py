import os
import re
import sys
import unicodedata
from fpdf import FPDF
from datetime import datetime

# Force UTF-8 console output on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class CVDocument(FPDF):
    """Custom PDF class for professional CV formatting"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        
    def header_section(self, name, contact_line):
        """Name and contact info at the top"""
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(33, 37, 41)
        self.cell(0, 12, name, ln=1, align="C")
        self.ln(2)
        
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, contact_line, ln=1, align="C")
        self.ln(2)
        
        # Divider line
        self.set_draw_color(52, 73, 94)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)
    
    def section_title(self, title):
        """Blue section headers"""
        self.ln(4)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(41, 128, 185)
        self.cell(0, 8, title.upper(), ln=1)
        
        # Thin underline
        self.set_draw_color(41, 128, 185)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)
    
    def job_header(self, job_title, company, dates):
        """Bold role title with company and dates"""
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(33, 37, 41)
        self.cell(140, 6, f"{job_title} | {company}")
        
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, dates, align="R", ln=1)
        self.ln(1)
    
    def body_text(self, text):
        """Normal paragraph text"""
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5, text)
        self.ln(1)
    
    def bullet_point(self, text):
        """Indented bullet point"""
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        self.cell(8)  # indent
        self.cell(4, 5, "-")  # simple ASCII bullet
        self.multi_cell(0, 5, text.strip("- ").strip())
        self.ln(1)


def parse_tailored_cv(text):
    """
    Parse the AI-generated tailored CV text into sections.
    Returns a dictionary of sections.
    """
    sections = {}
    current_section = "HEADER"
    current_content = []
    
    for line in text.split("\n"):
        stripped = line.strip()
        
        # Detect section headers (ALL CAPS lines or lines ending with :)
        if stripped and (
            stripped.isupper() or 
            stripped.endswith(":") and len(stripped.split()) <= 5 or
            stripped.startswith("##")
        ):
            # Save previous section
            if current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = stripped.strip("#:_ ").upper()
            current_content = []
        else:
            current_content.append(line)
    
    # Save last section
    if current_content:
        sections[current_section] = "\n".join(current_content)
    
    return sections


def generate_pdf_from_text(tailored_cv_path, output_folder="pdf_cvs"):
    """
    Takes a tailored CV .txt file and generates a professional PDF.
    """
    os.makedirs(output_folder, exist_ok=True)
    
    # Read the tailored CV
    with open(tailored_cv_path, "r", encoding="utf-8") as f:
        cv_text = f.read()
    
    # Normalize text to Latin-1 compatible ASCII-like characters for FPDF
    cv_text = unicodedata.normalize("NFKD", cv_text)
    cv_text = cv_text.encode("latin-1", "ignore").decode("latin-1")
    
    # Create PDF
    pdf = CVDocument()
    pdf.add_page()
    
    # ── Parse and render ──
    lines = cv_text.split("\n")
    
    # Try to extract name from first non-empty line
    name = "Gabor Krankovics"  # fallback
    contact_line = "Budapest, Hungary | +36709444432 | krankovics.gabor@gmail.com"
    
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            # First real line is likely the name
            if any(c.isalpha() for c in stripped):
                name = stripped.strip("#* ")
                break
    
    pdf.header_section(name, contact_line)
    
    # Process remaining lines
    for line in lines[1:]:  # skip name line
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
        
        # Contact info line — skip (already in header)
        if any(kw in stripped.lower() for kw in ["@gmail", "@email", "phone:", "location:", "linkedin"]):
            continue
        
        # Section headers: detect ALL CAPS, markdown ##, or known keywords
        section_keywords = [
            "PROFESSIONAL SUMMARY", "SUMMARY", "PROFILE",
            "CORE COMPETENCIES", "SKILLS", "KEY SKILLS",
            "PROFESSIONAL EXPERIENCE", "EXPERIENCE", "WORK EXPERIENCE",
            "EDUCATION", "CERTIFICATIONS", "CERTIFICATES",
            "LANGUAGES", "INTERESTS", "MISCELLANEOUS"
        ]
        
        clean = stripped.strip("#*: ").upper()
        if clean in section_keywords or (stripped.startswith("##") and len(stripped) < 50):
            pdf.section_title(clean)
            continue
        
        # Job headers: detect pattern like "Role | Company | Dates"
        if "|" in stripped and any(char.isdigit() for char in stripped):
            parts = [p.strip() for p in stripped.split("|")]
            if len(parts) >= 3:
                pdf.job_header(parts[0], parts[1], parts[2])
                continue
            elif len(parts) == 2:
                pdf.job_header(parts[0], parts[1], "")
                continue
        
        # Bullet points
        if stripped.startswith(("-", "•", "●", "*")) and len(stripped) > 3:
            pdf.bullet_point(stripped)
            continue
        
        # Regular text
        pdf.body_text(stripped)
    
    # Save PDF
    base_name = os.path.splitext(os.path.basename(tailored_cv_path))[0]
    pdf_filename = f"{base_name}.pdf"
    pdf_path = os.path.join(output_folder, pdf_filename)
    pdf.output(pdf_path)
    
    return pdf_path


def batch_convert():
    """
    Convert ALL tailored CVs in the tailored_cvs folder to PDFs.
    """
    input_folder = "tailored_cvs"
    output_folder = "pdf_cvs"
    
    if not os.path.exists(input_folder):
        print("No 'tailored_cvs' folder found.")
        print("   Run tailor_cv.py first to generate tailored CVs.")
        return
    
    txt_files = [f for f in os.listdir(input_folder) if f.endswith(".txt")]
    
    if not txt_files:
        print("No .txt files found in tailored_cvs/")
        print("   Run tailor_cv.py first.")
        return
    
    print("=" * 60)
    print("PDF Generator - Converting Tailored CVs")
    print("=" * 60)
    print(f"\n   Found {len(txt_files)} tailored CV(s)\n")
    
    # Show files and let user choose
    for i, f in enumerate(txt_files):
        print(f"  [{i}] {f}")
    
    print(f"\n  [A] Convert ALL")
    choice = input("\nEnter numbers separated by commas, or 'A' for all: ").strip()
    
    if choice.upper() == "A":
        selected = txt_files
    else:
        try:
            indices = [int(x.strip()) for x in choice.split(",")]
            selected = [txt_files[i] for i in indices]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return
    
    print(f"\nConverting {len(selected)} file(s)...\n")
    
    for filename in selected:
        filepath = os.path.join(input_folder, filename)
        try:
            pdf_path = generate_pdf_from_text(filepath, output_folder)
            print(f"  {filename}")
            print(f"     -> {pdf_path}")
        except Exception as e:
            print(f"  {filename} - Error: {e}")
    
    print(f"\n{'=' * 60}")
    print(f"Done! PDFs saved in '{output_folder}/'")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    batch_convert()
