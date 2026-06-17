import json
import ollama
import config

def parse_message(text):
    client = ollama.Client(host=config.OLLAMA_BASE_URL)
    prompt = f"""
    Analyze the following WhatsApp message and extract job details.
    A message can contain multiple jobs. 
    Format the output as a JSON list of objects.
    Each object should have: company, role, batch, stipend, location, referral_url.
    If a field is missing, use null.
    
    Message:
    \"\"\"{text}\"\"\"
    
    Respond ONLY with the JSON list.
    """
    
    try:
        response = client.generate(
            model=config.OLLAMA_MODEL,
            prompt=prompt
        )
        
        raw_response = response.get('response', '').strip()
        if not raw_response:
            print("Ollama returned an empty response.")
            return []
            
        # Extract JSON from markdown if needed
        if "```json" in raw_response:
            raw_response = raw_response.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_response:
            raw_response = raw_response.split("```")[1].split("```")[0].strip()
            
        jobs = json.loads(raw_response)
        
        # Filter by batch
        filtered_jobs = []
        if isinstance(jobs, list):
            for job in jobs:
                batch = str(job.get('batch') or "")
                if config.TARGET_BATCH in batch:
                    filtered_jobs.append(job)
        
        return filtered_jobs
    except Exception as e:
        print(f"Error parsing message with Ollama: {e}")
        return []

if __name__ == "__main__":
    test_text = "1. Google is hiring SDE Intern for 2026 batch. Stipend: 1L. Link: https://google.com/careers\n2. Microsoft is hiring for 2025 batch. https://microsoft.com"
    print(f"Parsing test text: {test_text}")
    print(parse_message(test_text))
