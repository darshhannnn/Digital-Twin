"""
sources.py
----------
Multi-source job discovery beyond WhatsApp.
All sources return a list of job dicts in the same schema as parser.py:
  {company, role, batch, stipend, location, referral_url, source}
"""

import time
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import config


# ---------------------------------------------------------------------------
# Internshala  (scrape search results)
# ---------------------------------------------------------------------------

def _fetch_internshala(role_keyword: str) -> list[dict]:
    jobs = []
    keyword = role_keyword.lower().replace(" ", "-")
    url = f"https://internshala.com/internships/{keyword}-internship/"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".individual_internship")[:15]
        for card in cards:
            title_el   = card.select_one("a.job-title-href")
            company_el = card.select_one(".company_name")
            if not title_el:
                continue
            role    = title_el.get_text(strip=True)
            company = company_el.get_text(strip=True) if company_el else "Unknown"
            href    = card.get("data-href", "") or title_el.get("href", "")
            full_url = f"https://internshala.com{href}" if href.startswith("/") else href
            jobs.append({
                "company":      company,
                "role":         role,
                "batch":        config.TARGET_BATCH,
                "stipend":      None,
                "location":     None,
                "referral_url": full_url,
                "source":       "internshala",
            })
    except Exception as e:
        print(f"  Internshala fetch failed for '{role_keyword}': {e}")
    return jobs


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def discover_jobs() -> list[dict]:
    all_jobs: list[dict] = []

    print("[Sources] Fetching Internshala...")
    for query in config.LINKEDIN_SEARCH_QUERIES:
        role_keyword = query.replace(config.TARGET_BATCH, "").strip()
        results = _fetch_internshala(role_keyword)
        print(f"  -> {len(results)} listings for '{role_keyword}'")
        all_jobs.extend(results)
        time.sleep(1)

    seen_urls: set[str] = set()
    deduped: list[dict] = []
    for job in all_jobs:
        url = (job.get("referral_url") or "").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(job)

    print(f"[Sources] Total unique jobs discovered: {len(deduped)}")
    return deduped
