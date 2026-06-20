"""
analyzer.py
-----------
AI analysis suite powered by local Ollama.

Functions
---------
get_skill_gap(jd_text, resume_text)     -> dict  {missing_skills, learning_resources}
get_interview_prep(jd_text, resume)     -> dict  {questions: [{q, model_answer}]}
estimate_salary(jd_text, role, company) -> dict  {range, currency, reasoning}
"""

from llm import call_llm_json


def get_skill_gap(jd_text: str, resume_text: str) -> dict | None:
    prompt = f"""
Analyze how well the candidate's resume matches the Job Description.

JD:
\"\"\"{jd_text[:2500]}\"\"\"

Resume:
\"\"\"{resume_text[:2000]}\"\"\"

Respond ONLY with JSON:
{{
  "match_score_pct": <0-100>,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "learning_resources": [
    {{"skill": "skill3", "resource": "free course or doc link"}}
  ],
  "summary": "One sentence verdict"
}}
"""
    return call_llm_json(prompt, temperature=0.3)


def get_interview_prep(jd_text: str, resume_text: str) -> dict | None:
    prompt = f"""
You are a senior hiring manager. Generate the top 8 interview questions for this role,
along with concise model answers tailored to the candidate's background.

JD:
\"\"\"{jd_text[:2500]}\"\"\"

Candidate Resume:
\"\"\"{resume_text[:2000]}\"\"\"

Respond ONLY with JSON:
{{
  "questions": [
    {{
      "q": "Question text",
      "model_answer": "Model answer referencing candidate's experience"
    }}
  ]
}}
"""
    return call_llm_json(prompt, temperature=0.5)


def estimate_salary(jd_text: str, role: str, company: str) -> dict | None:
    prompt = f"""
Estimate the salary/stipend range for the following role based on the JD context,
company tier, and Indian job market norms for 2026 batch interns/freshers.

Company: {company}
Role: {role}

JD excerpt:
\"\"\"{jd_text[:1500]}\"\"\"

Respond ONLY with JSON:
{{
  "currency": "INR",
  "monthly_range": "X - Y",
  "annual_range": "X LPA - Y LPA",
  "reasoning": "Brief explanation"
}}
"""
    return call_llm_json(prompt, temperature=0.3)
