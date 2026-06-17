import time
import datetime
import config
import db
import whatsapp
import parser
import scraper
import scorer
import tailor
import pdf
import applier
import requests

def send_telegram_notification(message):
    if not config.TELEGRAM_BOT_TOKEN or "your_telegram" in config.TELEGRAM_BOT_TOKEN:
        print(f"Telegram Notification (Skipped): {message}")
        return
    
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Failed to send Telegram notification: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")

def run_agent():
    print(f"[{datetime.datetime.now()}] Starting Job Agent run...")
    
    try:
        # 1. Scrape WhatsApp
        messages = whatsapp.scrape_whatsapp()
        print(f"Found {len(messages)} new messages.")
    except Exception as e:
        print(f"Error in WhatsApp scraping: {e}")
        return

    if not messages:
        print("No new messages found. Ending run.")
        return

    # Check if master resume is still placeholder
    with open(config.MASTER_RESUME_PATH, "r") as f:
        master_resume = f.read()
    
    if "Paste your base resume here" in master_resume:
        print("WARNING: Master resume is empty/placeholder. Scoring and tailoring will be inaccurate.")

    for msg in messages:
        # 2. Parse Message
        try:
            jobs = parser.parse_message(msg['text'])
        except Exception as e:
            print(f"Error parsing message: {e}")
            continue

        for job in jobs:
            company = job.get('company')
            role = job.get('role')
            url = job.get('referral_url')
            
            if not company or not role:
                continue

            print(f"\n--- Processing: {role} at {company} ---")
            
            # 3. Scrape Full JD
            jd_text = scraper.scrape_jd(url, company, role)
            
            # 4. Score Job
            score, reason = scorer.score_job(jd_text, master_resume)
            print(f"Fit score: {score}")
            print(f"Reason: {reason}")
            
            if score < config.FIT_SCORE_THRESHOLD:
                print(f"Skipping {company} - score below threshold.")
                db.save_job({**job, "jd_text": jd_text, "fit_score": score, "status": "skipped"})
                continue
            
            # 5. Tailor Resume
            print(f"Tailoring resume for {company}...")
            tailored_data = tailor.tailor_resume(jd_text, master_resume)
            
            # 6. Generate PDF and Apply
            pdf_path = None
            if tailored_data:
                pdf_path = pdf.generate_pdf(tailored_data, company, role)
            
            if pdf_path:
                # 7. Apply
                personal_info = {
                    "full_name": os.getenv("FULL_NAME", "Your Full Name"),
                    "email": os.getenv("EMAIL", "your.email@example.com")
                }
                success, status_msg = applier.apply_to_job(url, pdf_path, personal_info)
                status = "applied" if success else "failed"
            else:
                print("Skipping application step as tailored PDF could not be generated.")
                status = "tailoring_failed"
                status_msg = "Could not generate tailored PDF (check API keys)"

            # 8. Log and Notify
            db.save_job({
                **job, 
                "jd_text": jd_text, 
                "fit_score": score, 
                "resume_path": pdf_path or "", 
                "status": status,
                "applied_at": datetime.datetime.now()
            })
            
            notification = f"Job Update:\nCompany: {company}\nRole: {role}\nScore: {score}\nStatus: {status_msg}"
            send_telegram_notification(notification)

def main():
    while True:
        try:
            run_agent()
        except Exception as e:
            print(f"Fatal error in main loop: {e}")
        
        print(f"Sleeping for {config.CHECK_INTERVAL} seconds...")
        time.sleep(config.CHECK_INTERVAL)

if __name__ == "__main__":
    main()
