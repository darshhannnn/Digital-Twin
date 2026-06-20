import time
import urllib.parse
import urllib.request
import config
import db
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def scrape_jd(url: str, company: str, role: str, use_cache: bool = True) -> str:
    if not url:
        return search_google_for_jd(company, role)

    if use_cache:
        cached = db.get_cached_jd(url)
        if cached:
            print(f"  [Cache HIT] Using cached JD for {url[:60]}...")
            return cached

    body_text = None

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=config.CHROME_DATA_DIR,
                headless=True
            )
            page = browser.new_page()

            print(f"  Navigating to {url}")
            page.goto(url, wait_until="networkidle", timeout=30000)

            body_text = page.inner_text("body")

            if "linkedin.com" in url:
                if "/jobs/view/" in url:
                    jd_container = (
                        page.query_selector(".jobs-description") or
                        page.query_selector(".show-more-less-html__markup") or
                        page.query_selector("article")
                    )
                else:
                    jd_container = (
                        page.query_selector(".feed-shared-update-v2__description-wrapper") or
                        page.query_selector(".attributed-text-segment-list__content") or
                        page.query_selector(".main-content")
                    )
                if jd_container:
                    body_text = jd_container.inner_text()

            elif "internshala.com" in url:
                container = page.query_selector(".internship-details") or \
                            page.query_selector("#internship_meta")
                if container:
                    body_text = container.inner_text()

            if body_text and len(body_text) < 300:
                print("  Extracted text too short — may have hit an auth wall.")

        except Exception as e:
            print(f"  Error scraping {url}: {e}")
            body_text = None
        finally:
            if browser:
                browser.close()

    if body_text and len(body_text) > 100:
        if use_cache:
            db.cache_jd(url, body_text)
        return body_text

    return search_google_for_jd(company, role)


def search_google_for_jd(company: str, role: str) -> str:
    query = urllib.parse.quote_plus(f"{role} {company} intern 2026 job description")
    fallback_url = f"https://www.google.com/search?q={query}"
    print(f"  Fallback: Google search -> {fallback_url}")

    try:
        req = urllib.request.Request(fallback_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        snippets = soup.select(".VwiC3b")
        if snippets:
            return " ".join(s.get_text() for s in snippets[:5])
    except Exception as e:
        print(f"  Google fallback also failed: {e}")

    return f"Could not find JD for {role} at {company} automatically."


if __name__ == "__main__":
    url = "https://www.linkedin.com/jobs/view/placeholder"
    print(scrape_jd(url, "TestCo", "Software Engineer"))
