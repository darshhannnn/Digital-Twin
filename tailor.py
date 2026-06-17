import json
import google.generativeai as genai
import config

def tailor_resume(jd_text, master_resume_text):
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_gemini_api_key_here":
        print("Gemini API Key not set. Skipping tailoring.")
        return None

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an expert career coach. Tailor the following Master Resume to match the Job Description (JD).
    Focus on keywords and impact. Rewrite experience bullets to highlight relevant skills.
    
    JD:
    \"\"\"{jd_text}\"\"\"
    
    Master Resume:
    \"\"\"{master_resume_text}\"\"\"
    
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
    
    try:
        response = model.generate_content(prompt)
        # Gemini sometimes wraps JSON in markdown blocks
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        tailored_data = json.loads(clean_response)
        return tailored_data
    except Exception as e:
        print(f"Error tailoring resume with Gemini: {e}")
        return None

if __name__ == "__main__":
    # Test with dummy data
    pass
