"""
sources.py
----------
Multi-source job discovery beyond WhatsApp.
All sources return a list of job dicts in the same schema as parser.py:
  {company, role, batch, stipend, location, referral_url, source}
"""

import json
import re
import time
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import config


# ---------------------------------------------------------------------------
# HN "Who is hiring?" (monthly thread via Firebase API)
# ---------------------------------------------------------------------------

_HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
_HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

_ROLE_KEYWORDS = [
    "software engineer", "sde", "backend", "frontend", "full stack",
    "fullstack", "full-stack", "devops", "ml engineer", "data engineer",
    "platform engineer", "infrastructure", "site reliability", "sre",
    "python developer", "golang", "rust engineer",
]

_FRESHER_KEYWORDS = ["2026", "2025", "junior", "entry level", "new grad", "recent grad", "fresher", "intern"]


def _fetch_hn_hiring() -> list[dict]:
    """Fetch the latest 'Ask HN: Who is hiring?' thread and parse job posts."""
    jobs = []

    try:
        params = urllib.parse.urlencode({
            "query": '"Ask HN: Who is hiring?"',
            "tags": "ask_hn",
            "hitsPerPage": 1,
        })
        req = urllib.request.Request(
            f"{_HN_SEARCH_URL}?{params}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        hits = data.get("hits", [])
        if not hits:
            print("  No 'Who is hiring?' thread found.")
            return jobs

        thread_id = hits[0]["objectID"]
        thread_title = hits[0].get("title", "")
        print(f"  Thread: {thread_title}")

        req2 = urllib.request.Request(
            _HN_ITEM_URL.format(thread_id),
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req2, timeout=15) as resp:
            thread = json.loads(resp.read().decode())

        post_ids = thread.get("kids", [])
        print(f"  Total posts: {len(post_ids)}")

        # Fetch posts in batches of 20
        for i in range(0, min(len(post_ids), 100), 20):
            batch = post_ids[i:i + 20]
            for pid in batch:
                try:
                    req3 = urllib.request.Request(
                        _HN_ITEM_URL.format(pid),
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    with urllib.request.urlopen(req3, timeout=10) as resp:
                        comment = json.loads(resp.read().decode())

                    text = BeautifulSoup(comment.get("text", ""), "html.parser").get_text()
                    parsed = _parse_hn_post(text, comment.get("by", ""), pid)
                    if parsed:
                        jobs.append(parsed)
                except Exception:
                    continue
            time.sleep(0.5)

    except Exception as e:
        print(f"  HN Who's Hiring fetch failed: {e}")

    return jobs


def _parse_hn_post(text: str, author: str, post_id: int = 0) -> dict | None:
    """
    Parse a single HN job post. Format is typically:
      Company | Role | Location | Remote/Onsite | Full-time
    """
    text = text.strip()
    if not text:
        return None

    lines = text.split("\n")
    header = lines[0]

    # Split on pipe — typical format: Company | Role | Location | ...
    parts = [p.strip() for p in header.split("|")]
    if len(parts) < 2:
        return None

    company = parts[0]
    role = parts[1] if len(parts) > 1 else ""
    location = parts[2] if len(parts) > 2 else ""

    # Filter: only software/tech roles
    role_lower = role.lower()
    header_lower = header.lower()
    if not any(kw in role_lower for kw in _ROLE_KEYWORDS) and \
       not any(kw in header_lower for kw in _ROLE_KEYWORDS):
        return None

    # Build URL to the comment
    url = f"https://news.ycombinator.com/item?id={post_id}" if post_id else ""

    return {
        "company":      company,
        "role":         role,
        "batch":        config.TARGET_BATCH,
        "stipend":      None,
        "location":     location,
        "referral_url": url,
        "source":       "hn_hiring",
    }


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

    print("[Sources] Fetching HN Who's Hiring...")
    hn_jobs = _fetch_hn_hiring()
    print(f"  -> {len(hn_jobs)} matching jobs")
    all_jobs.extend(hn_jobs)

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
