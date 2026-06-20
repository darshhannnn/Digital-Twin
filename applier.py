import time
import config
from playwright.sync_api import sync_playwright

def detect_platform(page):
    url = page.url
    if "myworkdayjobs.com" in url:
        return "workday"
    if "greenhouse.io" in url:
        return "greenhouse"
    if "lever.co" in url:
        return "lever"
    return "custom"

def apply_to_job(url, pdf_path, personal_info):
    if not url:
        return False, "No URL provided"
    
    browser = None
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=config.CHROME_DATA_DIR,
                headless=True
            )
        except Exception as e:
            print(f"Error launching browser: {e}")
            return False, str(e)

        page = browser.new_page()
        result = (False, "Unknown error")

        try:
            print(f"Applying at {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)

            platform = detect_platform(page)
            print(f"Detected platform: {platform}")

            if platform == "lever":
                apply_btn = page.query_selector('a.postings-btn:has-text("Apply for this job")')
                if apply_btn: apply_btn.click()
                time.sleep(2)

                page.set_input_files('input[type="file"]', pdf_path)
                page.fill('input[name="name"]', personal_info.get('full_name', ''))
                page.fill('input[name="email"]', personal_info.get('email', ''))

            elif platform == "greenhouse":
                page.set_input_files('input[type="file"]', pdf_path)
                full_name = personal_info.get('full_name', '')
                name_parts = full_name.split()
                first_name = name_parts[0] if name_parts else ''
                last_name = name_parts[-1] if len(name_parts) > 1 else ''
                page.fill('#first_name', first_name)
                page.fill('#last_name', last_name)
                page.fill('#email', personal_info.get('email', ''))

            elif platform == "workday":
                apply_btn = page.query_selector('[data-automation-id="applyButton"]')
                if apply_btn:
                    apply_btn.click()
                    manual_btn = page.wait_for_selector('[data-automation-id="applyManually"]', timeout=5000)
                    if manual_btn: manual_btn.click()

                print("Workday detected. Manual intervention likely needed for multi-page flow.")
                return (False, "Workday requires manual multi-step navigation.")
            else:
                name_fields = page.query_selector_all('input[name*="name"], input[placeholder*="Name"]')
                for field in name_fields:
                    if field.is_visible():
                        field.fill(personal_info.get('full_name', ''))
                        break

                email_fields = page.query_selector_all('input[type="email"], input[name*="email"]')
                for field in email_fields:
                    if field.is_visible():
                        field.fill(personal_info.get('email', ''))
                        break

                resume_fields = page.query_selector_all('input[type="file"], input[name*="resume"]')
                for field in resume_fields:
                    if field.is_visible():
                        field.set_input_files(pdf_path)
                        break

            print("Form filling attempted. Please review and submit manually if needed.")

            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Apply")',
                'button:has-text("Submit Application")',
                '[data-automation-id="submit-button"]'
            ]
            
            for selector in submit_selectors:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible() and btn.is_enabled():
                        print(f"Submit button found ({selector}), clicking...")
                        btn.click()
                        time.sleep(5)
                        result = (True, f"Applied attempt on {platform}")
                        break
                except Exception:
                    continue

            time.sleep(5)

        except Exception as e:
            print(f"Error applying: {e}")
            result = (False, str(e))
        finally:
            if browser:
                browser.close()

        return result

if __name__ == "__main__":
    pass
