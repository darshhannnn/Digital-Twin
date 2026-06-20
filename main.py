"""
main.py
-------
Orchestrates the complete Digital Twin job-hunting pipeline:

  WhatsApp + Multi-Source -> Parse -> Deduplicate -> Scrape JD (cached)
  -> Score -> Skill Gap + Interview Prep + Salary Estimate
  -> Tailor Resume -> Cover Letter -> Generate PDFs -> Auto-Apply
  -> Save to DB -> Rich Notifications
"""

import sys
import signal
import time
import datetime
import os
import json

import config
import db
import whatsapp
import parser
import scraper
import scorer
import tailor
import cover_letter as cl_gen
import pdf
import applier
import notifier
import analyzer
import sources

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_shutdown_requested = False


def _handle_signal(signum, frame):
    global _shutdown_requested
    print("\nShutdown requested. Finishing current run...")
    _shutdown_requested = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_master_resume() -> str:
    try:
        with open(config.MASTER_RESUME_PATH, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[WARN] Master resume not found at {config.MASTER_RESUME_PATH}. "
              "Create it with your base resume text.")
        return ""


def _process_job(job: dict, master_resume: str):
    company = job.get('company') or ''
    role    = job.get('role') or ''
    url     = job.get('referral_url') or ''
    source  = job.get('source', 'whatsapp')

    if not company or not role:
        return None

    print(f"\n{'─'*55}")
    print(f"  {role}  @  {company}  [{source}]")
    print(f"{'─'*55}")

    if db.is_duplicate_job(url, company, role):
        print("  [SKIP] Already processed (duplicate).")
        return None

    print("  Scraping JD...")
    jd_text = scraper.scrape_jd(url, company, role, use_cache=True)

    print("  Scoring...")
    score, reason = scorer.score_job(jd_text, master_resume)
    print(f"  Fit score: {score}/100")

    if score < config.FIT_SCORE_THRESHOLD:
        print(f"  [SKIP] Score {score} below threshold {config.FIT_SCORE_THRESHOLD}.")
        job_id = db.save_job({
            **job, "jd_text": jd_text, "fit_score": score,
            "status": "skipped", "applied_at": datetime.datetime.now()
        })
        notifier.notify({**job, "fit_score": score, "status": "skipped"}, f"Skipped (score {score})")
        return job_id

    print("  Running AI analysis...")
    skill_gap_data     = analyzer.get_skill_gap(jd_text, master_resume)
    interview_prep_data = analyzer.get_interview_prep(jd_text, master_resume)
    salary_data        = analyzer.estimate_salary(jd_text, role, company)

    if skill_gap_data:
        missing = skill_gap_data.get('missing_skills', [])
        print(f"  Missing skills: {', '.join(missing[:4]) or 'none'}")
    if salary_data:
        print(f"  Salary estimate: {salary_data.get('monthly_range','?')}/mo")

    print("  Tailoring resume...")
    tailored_data = tailor.tailor_resume(jd_text, master_resume)

    pdf_path = None
    if tailored_data:
        pdf_path = pdf.generate_pdf(tailored_data, company, role)

    cl_path = None
    if tailored_data:
        print("  Generating cover letter...")
        cl_data = cl_gen.generate_cover_letter(jd_text, master_resume, company, role)
        if cl_data:
            cl_path = pdf.generate_cover_letter_pdf(cl_data, company, role)

    job_id = db.save_job({
        **job,
        "jd_text":          jd_text,
        "fit_score":        score,
        "resume_path":      pdf_path or "",
        "cover_letter_path":cl_path or "",
        "skill_gap":        json.dumps(skill_gap_data)      if skill_gap_data      else None,
        "interview_prep":   json.dumps(interview_prep_data) if interview_prep_data else None,
        "salary_estimate":  json.dumps(salary_data)         if salary_data         else None,
        "status":           "pending",
        "applied_at":       datetime.datetime.now(),
    })

    if pdf_path:
        full_name = os.getenv("FULL_NAME", "Your Full Name")
        email     = os.getenv("EMAIL",     "your.email@example.com")
        if not full_name.strip() or not email.strip():
            print("  [WARN] FULL_NAME or EMAIL not set in .env. Skipping application.")
            status     = "tailoring_failed"
            status_msg = "Missing FULL_NAME or EMAIL in .env"
        else:
            personal_info = {"full_name": full_name, "email": email}
            success, status_msg = applier.apply_to_job(url, pdf_path, personal_info)
            status = "applied" if success else "failed"
    else:
        print("  [WARN] No PDF — skipping application step.")
        status     = "tailoring_failed"
        status_msg = "Could not generate tailored PDF (check Ollama is running)"

    db.update_job_status(job_id, status, status_msg)

    notifier.notify({
        **job,
        "fit_score":       score,
        "status":          status,
        "skill_gap":       json.dumps(skill_gap_data)  if skill_gap_data  else None,
        "salary_estimate": json.dumps(salary_data)     if salary_data     else None,
    }, status_msg)

    print(f"  Done — status: {status}")
    return job_id


# ---------------------------------------------------------------------------
# Main agent run
# ---------------------------------------------------------------------------

def run_agent():
    print(f"\n{'='*55}")
    print(f"  JOB AGENT  —  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")

    db.init_db()
    master_resume = _load_master_resume()

    if "Paste your base resume" in master_resume or not master_resume.strip():
        print("[WARN] Master resume is placeholder/empty. Analysis will be inaccurate.")

    all_jobs: list[dict] = []

    try:
        print("\n[1/2] Scraping WhatsApp channels...")
        messages = whatsapp.scrape_whatsapp()
        print(f"      Found {len(messages)} new messages.")
        for msg in messages:
            try:
                parsed = parser.parse_message(msg['text'])
                for job in parsed:
                    job['source'] = 'whatsapp'
                all_jobs.extend(parsed)
            except Exception as e:
                print(f"      Parse error: {e}")
    except Exception as e:
        print(f"[WhatsApp] Error: {e}")

    try:
        print("\n[2/2] Discovering jobs from online sources...")
        discovered = sources.discover_jobs()
        filtered = [j for j in discovered
                    if config.TARGET_BATCH in str(j.get('batch') or j.get('role') or '')]
        print(f"      {len(filtered)} matching jobs (of {len(discovered)} found).")
        all_jobs.extend(filtered)
    except Exception as e:
        print(f"[Sources] Error: {e}")

    if not all_jobs:
        print("\nNo jobs to process this run.")
        return

    print(f"\nProcessing {len(all_jobs)} total jobs...\n")
    processed = 0
    for job in all_jobs:
        if _shutdown_requested:
            print("\nShutdown detected. Stopping early.")
            break
        try:
            result = _process_job(job, master_resume)
            if result:
                processed += 1
        except Exception as e:
            print(f"  [ERROR] Unexpected error processing job: {e}")

    print(f"\nRun complete. {processed}/{len(all_jobs)} jobs processed.")


# ---------------------------------------------------------------------------
# Scheduling loop
# ---------------------------------------------------------------------------

def main():
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    while not _shutdown_requested:
        try:
            run_agent()
        except Exception as e:
            print(f"Fatal error in main loop: {e}")

        if _shutdown_requested:
            break

        print(f"\nSleeping {config.CHECK_INTERVAL}s until next run...")
        for _ in range(config.CHECK_INTERVAL):
            if _shutdown_requested:
                break
            time.sleep(1)

    print("Agent shut down gracefully.")


if __name__ == "__main__":
    main()
