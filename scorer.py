import json
import ollama
import config

def score_job(jd_text, master_resume_text):
    if not jd_text or not master_resume_text:
        return 0, "Missing JD or Master Resume"
    
    client = ollama.Client(host=config.OLLAMA_BASE_URL)
    prompt = f"""
    Compare the following Job Description (JD) with the Master Resume.
    Score the fit from 0 to 100.
    
    JD:
    \"\"\"{jd_text[:2000]}\"\"\"
    
    Master Resume:
    \"\"\"{master_resume_text[:2000]}\"\"\"
    
    Respond ONLY with a JSON object: {{"score": 85, "reason": "Short explanation"}}
    """
    
    try:
        response = client.generate(
            model=config.OLLAMA_MODEL,
            prompt=prompt
        )
        
        raw_response = response.get('response', '').strip()
        if not raw_response:
            print("Ollama returned an empty response for scoring.")
            return 0, "Empty response"

        if "<think>" in raw_response:
            raw_response = raw_response.split("</think>")[-1].strip()

        if "```json" in raw_response:
            raw_response = raw_response.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_response:
            raw_response = raw_response.split("```")[1].split("```")[0].strip()

        result = json.loads(raw_response)
        return result.get('score', 0), result.get('reason', "No reason provided")
    except Exception as e:
        print(f"Error scoring job with Ollama: {e}")
        return 0, str(e)

if __name__ == "__main__":
    jd = "Seeking a Python developer with experience in Playwright and LLMs."
    resume = "I am a senior developer skilled in Python, web automation with Playwright, and AI integration."
    print(score_job(jd, resume))
