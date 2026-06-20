import tailor
import pdf
import os

MOCK_JD = """
Software Engineer Intern (2026 Batch)
We are looking for a Python developer with experience in:
- Playwright or Selenium
- Local LLMs (Ollama)
- Web scraping
- API development
"""

MOCK_RESUME = """
John Doe
Email: john.doe@example.com
Experience:
- Developed web scrapers using Playwright and Python.
- Integrated Ollama for automated text analysis.
- Built REST APIs with FastAPI.
Skills: Python, Playwright, SQL, Git.
"""

def test_full_flow():
    print("Testing Tailoring...")
    tailored_data = tailor.tailor_resume(MOCK_JD, MOCK_RESUME)
    if not tailored_data:
        print("FAILED: Tailoring returned None (check Ollama is running).")
        return

    print("Testing PDF Generation...")
    pdf_path = pdf.generate_pdf(tailored_data, "TestCorp", "Software Engineer")
    if not pdf_path or not os.path.exists(pdf_path):
        print("FAILED: PDF not generated.")
        return
    print(f"PDF generated at: {pdf_path}")

    print("Testing Applier (DRY RUN - skipped)")
    print("To test applier, call applier.apply_to_job() with a real URL.")

if __name__ == "__main__":
    test_full_flow()
