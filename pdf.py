import datetime
from fpdf import FPDF
import config

class ResumePDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def generate_pdf(tailored_data, company, role):
    if not tailored_data:
        return None
    
    pdf = ResumePDF()
    pdf.add_page()
    
    # Name
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, tailored_data.get('name', 'Your Name'), ln=True, align="C")
    
    # Contact
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 5, tailored_data.get('contact', ''), ln=True, align="C")
    pdf.ln(5)
    
    # Summary
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Professional Summary", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 5, tailored_data.get('summary', ''))
    pdf.ln(5)
    
    # Skills
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Skills", ln=True)
    pdf.set_font("helvetica", "", 10)
    skills = ", ".join(tailored_data.get('skills', []))
    pdf.multi_cell(0, 5, skills)
    pdf.ln(5)
    
    # Experience
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Experience", ln=True)
    for exp in tailored_data.get('experience', []):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(140, 5, f"{exp.get('role')} at {exp.get('company')}")
        pdf.set_font("helvetica", "I", 10)
        pdf.cell(0, 5, exp.get('duration', ''), ln=True, align="R")
        
        pdf.set_font("helvetica", "", 10)
        for bullet in exp.get('bullets', []):
            pdf.cell(5) # Indent
            pdf.multi_cell(0, 5, f"- {bullet}")
        pdf.ln(2)
    
    # Projects
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Projects", ln=True)
    for proj in tailored_data.get('projects', []):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 5, proj.get('name', ''), ln=True)
        
        pdf.set_font("helvetica", "", 10)
        for bullet in proj.get('bullets', []):
            pdf.cell(5) # Indent
            pdf.multi_cell(0, 5, f"- {bullet}")
        pdf.ln(2)
        
    # Education
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Education", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 5, tailored_data.get('education', ''))
    
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    safe_company = "".join(x for x in company if x.isalnum())
    safe_role = "".join(x for x in role if x.isalnum())
    filename = f"{safe_company}_{safe_role}_{date_str}.pdf"
    filepath = config.RESUMES_DIR / filename
    
    try:
        pdf.output(str(filepath))
        return str(filepath)
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

if __name__ == "__main__":
    # Test
    pass
