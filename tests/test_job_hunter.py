import tempfile
import unittest
from pathlib import Path

from tailor_cv import build_tailoring_prompt, clean_output, load_jobs_from_csv, safe_filename, validate_metrics


class TestJobHunterBot(unittest.TestCase):
    def test_csv_parsing_loads_job_rows(self):
        sample_csv = """job_title,employer_name,job_city,job_country,job_apply_link,job_description,job_posted_at_datetime_utc,job_publisher,job_employment_type
IT Sales Manager,Acme Corp,London,UK,https://apply.example,Manage accounts.,2026-04-01,ExampleBoard,Full-time
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "jobs_found.csv"
            csv_path.write_text(sample_csv, encoding="utf-8")
            jobs = load_jobs_from_csv(str(csv_path))

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["job_title"], "IT Sales Manager")
            self.assertEqual(jobs[0]["employer_name"], "Acme Corp")
            self.assertEqual(jobs[0]["job_city"], "London")

    def test_prompt_generation_includes_target_summary(self):
        config = {
            "prompt_template": "ROLE: {job_title} at {company}\nJOB DESCRIPTION: {job_description}\nMASTER CV: {master_cv}",
            "keywords": [],
            "default_top": 3,
        }
        prompt = build_tailoring_prompt(
            config,
            "EXPERIENCE",
            "IT Sales Manager",
            "Acme Corp",
            "Drive revenue through customer success.",
        )

        self.assertIn("ROLE: IT Sales Manager at Acme Corp", prompt)
        self.assertIn("JOB DESCRIPTION: Drive revenue through customer success.", prompt)
        self.assertIn("MASTER CV: EXPERIENCE", prompt)

    def test_pdf_output_formatting_creates_pdf_file(self):
        sample_text = "John Doe\nProfessional Summary\nExperienced IT sales leader.\n"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "tailored_cv.txt"
            output_dir = Path(tmpdir) / "pdf_cvs"
            input_path.write_text(sample_text, encoding="utf-8")

            pdf_path = generate_pdf_from_text(str(input_path), str(output_dir))

            self.assertTrue(pdf_path.endswith(".pdf"))
            self.assertTrue(Path(pdf_path).exists())
            self.assertGreater(Path(pdf_path).stat().st_size, 0)

            pdf_bytes = Path(pdf_path).read_bytes()
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))


class TestCleanOutput(unittest.TestCase):
    def test_fixes_split_bold(self):
        dirty = "- **C**RM Strategy:** Built pipelines"
        cleaned = clean_output(dirty)
        self.assertEqual(cleaned, "- **CRM Strategy:** Built pipelines")


class TestValidateMetrics(unittest.TestCase):
    def test_validate_metrics_flags_hallucination(self):
        tailored = "Closed $100k deals"
        master = "Closed deals"
        warnings = validate_metrics(tailored, master)
        self.assertIn("$100", str(warnings))

    def test_validate_metrics_allows_real_numbers(self):
        master = "Increased by 20%"
        tailored = "Increased by 20%"
        warnings = validate_metrics(tailored, master)
        self.assertEqual(len(warnings), 0)

    def test_validate_metrics_ignores_years(self):
        master = "Started in 2020"
        tailored = "Worked from 2021 to 2022"
        warnings = validate_metrics(tailored, master)
        self.assertEqual(len(warnings), 0)


class TestValidateMetricsMatchScore(unittest.TestCase):
    def test_validate_metrics_ignores_match_score_section(self):
        master = "Increased by 20%"
        tailored = "## Professional Summary\nIncreased by 20%\n## Match Score\n8/10\n## Education"
        warnings = validate_metrics(tailored, master)
        self.assertEqual(len(warnings), 0)  # Should not flag 8 or 10


class TestSafeFilename(unittest.TestCase):
    def test_safe_filename_removes_special_chars(self):
        unsafe = 'Test<>:|?*File'
        safe = safe_filename(unsafe)
        # < > : | ? * = 6 chars, all replaced with _
        self.assertEqual(safe, 'Test______File')

    def test_safe_filename_caps_length(self):
        long_name = 'A' * 150
        safe = safe_filename(long_name)
        self.assertEqual(len(safe), 100)
        self.assertEqual(safe, 'A' * 100)

    def test_safe_filename_handles_empty_string(self):
        self.assertEqual(safe_filename(""), "")
        self.assertEqual(safe_filename("   "), "")

    def test_safe_filename_handles_only_dots(self):
        # Windows hates filenames ending in dots
        result = safe_filename("badname...")
        self.assertFalse(result.endswith("."))
        self.assertEqual(result, "badname")


if __name__ == "__main__":
    unittest.main()
