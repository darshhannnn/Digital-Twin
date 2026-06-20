import sys
import db
import parser
import scraper
import scorer
import config

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def test_full_pipeline():
    db.init_db()
    test_message = "Walmart is hiring for Software Engineer Intern - 2026 Batch. Apply here: https://www.linkedin.com/posts/hemalathathiyagarajan1_walmart-hiring-freshersjobs-activity-744617222"
    print(f"Testing with message: {test_message}")
    
    jobs = parser.parse_message(test_message)
    print(f"Parsed jobs: {jobs}")
    
    if not jobs:
        print("No jobs parsed.")
        return

    job = jobs[0]
    company = job.get('company')
    role = job.get('role')
    url = job.get('referral_url')
    
    try:
        with open(config.MASTER_RESUME_PATH, "r", encoding="utf-8") as f:
            master_resume = f.read()
    except FileNotFoundError:
        print(f"ERROR: Master resume not found at {config.MASTER_RESUME_PATH}. Please create it.")
        return

    print(f"Scraping JD for {company}...")
    jd_text = scraper.scrape_jd(url, company, role)
    print(f"JD Snippet: {jd_text[:100]}...")
    
    print(f"Scoring job...")
    score, reason = scorer.score_job(jd_text, master_resume)
    print(f"Score: {score}, Reason: {reason}")

if __name__ == "__main__":
    test_full_pipeline()
