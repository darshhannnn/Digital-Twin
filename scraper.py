import time
import config
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape_jd(url, company, role):
    if not url:
        return search_google_for_jd(company, role)
    
    with sync_playwright() as p:
        # Use persistent context to reuse LinkedIn session
        browser = p.chromium.launch_persistent_context(
            user_data_dir=config.CHROME_DATA_DIR,
            headless=True
        )
        page = browser.new_page()
        
        try:
            print(f"Navigating to {url}")
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Simple heuristic for JD extraction
            # Try to get text from common JD containers or just the whole body
            body_text = page.inner_text("body")
            
            # If it's a LinkedIn page, we might need more specific selectors
            if "linkedin.com" in url:
                jd_container = page.query_selector(".jobs-description") or \
                               page.query_selector(".show-more-less-html__markup") or \
                               page.query_selector("article") or \
                               page.query_selector(".main-content")
                if jd_container:
                    body_text = jd_container.inner_text()
                else:
                    # If LinkedIn post, try to get the post text specifically
                    post_text = page.query_selector(".feed-shared-update-v2__description-wrapper") or \
                                page.query_selector(".attributed-text-segment-list__content")
                    if post_text:
                        body_text = post_text.inner_text()
            
            # If the text is very short (e.g. language selection), it might have failed
            if len(body_text) < 300:
                print("Extracted text too short, might have hit a wall.")
                # Could try to wait or refresh, but fallback is better
            
            browser.close()
            return body_text
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            browser.close()
            return search_google_for_jd(company, role)

def search_google_for_jd(company, role):
    print(f"Searching Google for JD: {company} {role}")
    # This is a simplified fallback. A real one might use a search API or scrape Google results.
    # For now, let's just return a placeholder or attempt a basic search if url is missing.
    return f"Could not find JD for {role} at {company} automatically."

if __name__ == "__main__":
    url = "https://www.linkedin.com/jobs/view/placeholder"
    print(scrape_jd(url, "TestCo", "Software Engineer"))
