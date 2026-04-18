import argparse
import logging
import os
import sys
import unicodedata
from fpdf import FPDF
from datetime import datetime

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
        self.cell(8)
        self.cell(4, 5, "-")
        self.multi_cell(0, 5, text.strip("-•* ").strip())
        self.ln(1)


def parse_tailored_cv(text):
    """Parse the AI-generated tailored CV text into named sections."""
    sections = {}
    current_section = "HEADER"
    current_content = []

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped and (
            stripped.isupper()
            or stripped.endswith(":") and len(stripped.split()) <= 5
            or stripped.startswith("##")
        ):
            if current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = stripped.strip("#:_ ").upper()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current_section] = "\n".join(current_content)
    return sections


def generate_pdf_from_text(tailored_cv_path, output_folder="pdf_cvs"):
    """Generate a professional PDF from a tailored CV text file."""
    os.makedirs(output_folder, exist_ok=True)

    with open(tailored_cv_path, "r", encoding="utf-8") as f:
        cv_text = f.read()

    cv_text = unicodedata.normalize("NFKD", cv_text)
    cv_text = cv_text.encode("latin-1", "ignore").decode("latin-1")

    pdf = CVDocument()
    pdf.add_page()

    lines = cv_text.split("\n")
    name = "Candidate Name"
    contact_line = "[Contact details removed]"
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            if any(c.isalpha() for c in stripped):
                name = stripped.strip("#* ")
                break

    pdf.header_section(name, contact_line)

    section_keywords = {
        "PROFESSIONAL SUMMARY", "SUMMARY", "PROFILE",
        "CORE COMPETENCIES", "SKILLS", "KEY SKILLS",
        "PROFESSIONAL EXPERIENCE", "EXPERIENCE", "WORK EXPERIENCE",
        "EDUCATION", "CERTIFICATIONS", "CERTIFICATES",
        "LANGUAGES", "INTERESTS", "MISCELLANEOUS",
        "COVER LETTER TALKING POINTS", "MATCH SCORE"
    }

    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if any(kw in stripped.lower() for kw in ["@gmail", "@email", "phone:", "location:", "linkedin"]):
            continue

        clean = stripped.strip("#*: ").upper()
        if clean in section_keywords or (stripped.startswith("##") and len(stripped) < 50):
            pdf.section_title(clean)
            continue

        if "|" in stripped and any(char.isdigit() for char in stripped):
            parts = [p.strip() for p in stripped.split("|")]
            if len(parts) >= 3:
                pdf.job_header(parts[0], parts[1], parts[2])
                continue
            elif len(parts) == 2:
                pdf.job_header(parts[0], parts[1], "")
                continue

        if stripped.startswith(("-", "•", "●", "*")) and len(stripped) > 3:
            pdf.bullet_point(stripped)
            continue

        pdf.body_text(stripped)

    base_name = os.path.splitext(os.path.basename(tailored_cv_path))[0]
    pdf_filename = f"{base_name}.pdf"
    pdf_path = os.path.join(output_folder, pdf_filename)
    pdf.output(pdf_path)
    return pdf_path


def get_text_files(input_dir):
    if not os.path.exists(input_dir):
        return []
    return sorted(f for f in os.listdir(input_dir) if f.endswith(".txt"))


def parse_args():
    parser = argparse.ArgumentParser(description="Convert tailored CV text files into PDFs.")
    parser.add_argument("--input-dir", default="tailored_cvs", help="Folder containing tailored CV .txt files.")
    parser.add_argument("--output-dir", default="pdf_cvs", help="Folder where PDFs will be saved.")
    parser.add_argument("--indices", help="Comma-separated file indices to convert, e.g. 0,2,4.")
    parser.add_argument("--pattern", help="Convert files matching this substring.")
    parser.add_argument("--all", action="store_true", help="Convert all tailored CV files.")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR).")
    return parser.parse_args()


def main():
    args = parse_args()
    configure_logging(args.log_level)
    txt_files = get_text_files(args.input_dir)
    if not txt_files:
        logger.warning("No .txt files found in '%s'.", args.input_dir)
        return

    if args.indices:
        indices = [int(x.strip()) for x in args.indices.split(",") if x.strip().isdigit()]
        selected = [txt_files[i] for i in indices if 0 <= i < len(txt_files)]
    elif args.pattern:
        selected = [f for f in txt_files if args.pattern.lower() in f.lower()]
    else:
        selected = txt_files if args.all or True else []

    if not selected:
        logger.warning("No files selected for conversion.")
        return

    logger.info("Converting %d file(s) from '%s' to '%s'...", len(selected), args.input_dir, args.output_dir)
    for filename in selected:
        input_path = os.path.join(args.input_dir, filename)
        try:
            pdf_path = generate_pdf_from_text(input_path, args.output_dir)
            logger.info("  %s -> %s", filename, pdf_path)
        except Exception as e:
            logger.error("  Failed: %s (%s)", filename, e)

    logger.info("Done! PDFs saved in '%s'", args.output_dir)


if __name__ == "__main__":
    main()
