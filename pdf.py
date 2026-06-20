import datetime
from fpdf import FPDF
import config

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

class _BasePDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_heading(self, text: str):
        self.set_font("helvetica", "B", 12)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(2)

    def bullet(self, text: str, indent: float = 5):
        self.set_x(self.get_x() + indent)
        self.multi_cell(0, 5, f"•  {text}")


def _safe_filename(text: str) -> str:
    return "".join(x for x in text if x.isalnum() or x in "-_")


# ---------------------------------------------------------------------------
# Resume PDF
# ---------------------------------------------------------------------------

class ResumePDF(_BasePDF):
    pass


def generate_pdf(tailored_data: dict, company: str, role: str) -> str | None:
    if not tailored_data:
        return None

    pdf = ResumePDF()
    pdf.add_page()

    # --- Name ---
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 10, tailored_data.get('name', 'Your Name'),
             new_x="LMARGIN", new_y="NEXT", align="C")

    # --- Contact ---
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 5, tailored_data.get('contact', ''),
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # --- Summary ---
    pdf.section_heading("Professional Summary")
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 5, tailored_data.get('summary', ''))
    pdf.ln(4)

    # --- Skills ---
    pdf.section_heading("Skills")
    pdf.set_font("helvetica", "", 10)
    skills = ", ".join(tailored_data.get('skills', []))
    pdf.multi_cell(0, 5, skills)
    pdf.ln(4)

    # --- Experience ---
    pdf.section_heading("Experience")
    for exp in tailored_data.get('experience', []):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(140, 5, f"{exp.get('role')} at {exp.get('company')}")
        pdf.set_font("helvetica", "I", 10)
        pdf.cell(0, 5, exp.get('duration', ''),
                 new_x="LMARGIN", new_y="NEXT", align="R")
        pdf.set_font("helvetica", "", 10)
        for b in exp.get('bullets', []):
            pdf.bullet(b)
        pdf.ln(2)

    # --- Projects ---
    pdf.section_heading("Projects")
    for proj in tailored_data.get('projects', []):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 5, proj.get('name', ''), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 10)
        for b in proj.get('bullets', []):
            pdf.bullet(b)
        pdf.ln(2)

    # --- Education ---
    pdf.section_heading("Education")
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 5, tailored_data.get('education', ''))

    # --- Save ---
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{_safe_filename(company)}_{_safe_filename(role)}_{date_str}.pdf"
    filepath = config.RESUMES_DIR / filename

    try:
        pdf.output(str(filepath))
        print(f"  Resume saved: {filepath}")
        return str(filepath)
    except Exception as e:
        print(f"Error generating resume PDF: {e}")
        return None


# ---------------------------------------------------------------------------
# Cover Letter PDF
# ---------------------------------------------------------------------------

def generate_cover_letter_pdf(cl_data: dict, company: str, role: str) -> str | None:
    """
    Renders a cover_letter dict (from cover_letter.py) to a PDF file.
    Keys expected: applicant_name, applicant_contact, company, role, body_paragraphs
    """
    if not cl_data:
        return None

    pdf = _BasePDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # --- Header ---
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, cl_data.get('applicant_name', ''),
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 5, cl_data.get('applicant_contact', ''),
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    # --- Date ---
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 5, datetime.datetime.now().strftime("%B %d, %Y"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # --- Salutation ---
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 5, f"Hiring Team - {cl_data.get('company', company)}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(0, 5, f"Re: Application for {cl_data.get('role', role)}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # --- Body paragraphs ---
    pdf.set_font("helvetica", "", 10)
    for para in cl_data.get('body_paragraphs', []):
        pdf.multi_cell(0, 6, para)
        pdf.ln(4)

    # --- Sign-off ---
    pdf.ln(4)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 5, "Sincerely,", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 5, cl_data.get('applicant_name', ''), new_x="LMARGIN", new_y="NEXT")

    # --- Save ---
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"CL_{_safe_filename(company)}_{_safe_filename(role)}_{date_str}.pdf"
    filepath = config.COVER_LETTERS_DIR / filename

    try:
        pdf.output(str(filepath))
        print(f"  Cover letter saved: {filepath}")
        return str(filepath)
    except Exception as e:
        print(f"Error generating cover letter PDF: {e}")
        return None


if __name__ == "__main__":
    pass
