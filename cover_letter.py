"""
cover_letter.py
---------------
Generates a tailored, professional cover letter for a given job using local Ollama.
Returns structured data that pdf.py can render to PDF.
"""

from llm import call_llm_json


def generate_cover_letter(jd_text: str, master_resume_text: str,
                           company: str, role: str) -> dict | None:
    safe_company = company.replace('"', '\\"')
    safe_role = role.replace('"', '\\"')

    prompt = f"""
You are an expert career coach writing a professional cover letter.
Using the Job Description and the candidate's Resume below, write a compelling,
concise cover letter (3-4 paragraphs, ~250 words).

Company: {safe_company}
Role: {safe_role}

Job Description:
\"\"\"{jd_text[:3000]}\"\"\"

Candidate Resume:
\"\"\"{master_resume_text[:2000]}\"\"\"

Respond ONLY with a JSON object:
{{
  "applicant_name": "Full Name from resume",
  "applicant_contact": "Email | Phone | LinkedIn",
  "company": "{safe_company}",
  "role": "{safe_role}",
  "body_paragraphs": [
    "Opening paragraph - hook and enthusiasm",
    "Skills match paragraph - 2-3 specific skills from JD",
    "Achievement paragraph - one concrete accomplishment",
    "Closing paragraph - call to action"
  ]
}}
"""
    return call_llm_json(prompt, temperature=0.4)
