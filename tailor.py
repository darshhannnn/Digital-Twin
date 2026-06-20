"""
tailor.py
---------
Resume tailoring powered by local Ollama.
"""

from llm import call_llm_json


def tailor_resume(jd_text, master_resume_text):
    prompt = f"""
You are an expert career coach. Tailor the following Master Resume to match the Job Description (JD).
Focus on keywords and impact. Rewrite experience bullets to highlight relevant skills.

JD:
\"\"\"{jd_text[:3000]}\"\"\"

Master Resume:
\"\"\"{master_resume_text[:2000]}\"\"\"

Respond ONLY with a JSON object containing the following structure:
{{
    "name": "Your Name",
    "contact": "Email, Phone, LinkedIn",
    "summary": "Tailored professional summary",
    "skills": ["Skill1", "Skill2"],
    "experience": [
        {{
            "company": "Company Name",
            "role": "Role Name",
            "duration": "Dates",
            "bullets": ["Bullet 1", "Bullet 2"]
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "bullets": ["Bullet 1", "Bullet 2"]
        }}
    ],
    "education": "Education details"
}}
"""
    return call_llm_json(prompt, temperature=0.2)
