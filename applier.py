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
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=config.CHROME_DATA_DIR,
            headless=False
        )
        page = browser.new_page()
        
        try:
            print(f"Applying at {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            platform = detect_platform(page)
            print(f"Detected platform: {platform}")
            
            if platform == "lever":
                # Lever usually has an 'Apply for this job' button first
                apply_btn = page.query_selector('a.postings-btn:has-text("Apply for this job")')
                if apply_btn: apply_btn.click()
                time.sleep(2)
                
                page.set_input_files('input[type="file"]', pdf_path)
                page.fill('input[name="name"]', personal_info.get('full_name', ''))
                page.fill('input[name="email"]', personal_info.get('email', ''))
                # Lever often auto-fills from resume, but let's be safe
                
            elif platform == "greenhouse":
                page.set_input_files('input[type="file"]', pdf_path)
                page.fill('#first_name', personal_info.get('full_name', '').split()[0])
                page.fill('#last_name', personal_info.get('full_name', '').split()[-1])
                page.fill('#email', personal_info.get('email', ''))
                
            elif platform == "workday":
                # Workday is notoriously difficult; usually requires 'Apply' click then 'Apply Manually'
                apply_btn = page.query_selector('[data-automation-id="applyButton"]')
                if apply_btn: 
                    apply_btn.click()
                    manual_btn = page.wait_for_selector('[data-automation-id="applyManually"]', timeout=5000)
                    if manual_btn: manual_btn.click()
                
                print("Workday detected. Manual intervention likely needed for multi-page flow.")
                return False, "Workday requires manual multi-step navigation."

            else:
                # Custom/Generic heuristic
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
            time.sleep(10) # Give time for user to see
            
            return True, f"Applied attempt on {platform}"
        except Exception as e:
            print(f"Error applying: {e}")
            return False, str(e)

if __name__ == "__main__":
    # Test
    pass
