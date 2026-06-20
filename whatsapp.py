import time
import hashlib
import config
import db
from playwright.sync_api import sync_playwright

def scrape_whatsapp():
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=config.CHROME_DATA_DIR,
                headless=False
            )
        except Exception as e:
            print(f"Error launching browser: {e}")
            return []

        page = browser.new_page()
        page.goto("https://web.whatsapp.com")
        
        print("Waiting for WhatsApp Web to load...")
        print("ACTION REQUIRED: If you see a QR code, please scan it with your WhatsApp app.")
        
        try:
            page.wait_for_selector('[data-testid="chat-list"]', timeout=60000)
            print("Login successful!")
        except Exception:
            print("Login timeout. Please ensure you have scanned the QR code.")
            time.sleep(10)
            if browser:
                browser.close()
            return []

        new_jobs_messages = []

        try:
            for channel_name in config.WHATSAPP_CHANNELS:
                print(f"Checking channel: {channel_name}")
                try:
                    print("Navigating to Channels/Updates tab...")
                    channels_tab = page.query_selector('[aria-label="Channels"]') or \
                                   page.query_selector('[aria-label="Updates"]') or \
                                   page.query_selector('[data-testid="newsletter-outline-draft"]') or \
                                   page.query_selector('[data-testid="newsletter-outline"]') or \
                                   page.query_selector('span[data-icon="newsletter-outline"]')

                    if channels_tab:
                        channels_tab.click()
                        time.sleep(2)

                    header = page.query_selector('[data-testid="conversation-info-header"]')
                    if header and channel_name.lower() in header.inner_text().lower():
                        print(f"Channel {channel_name} is already open.")
                    else:
                        print("Attempting to focus search bar via shortcut...")
                        page.keyboard.press("Control+Alt+/")
                        time.sleep(2)

                        print(f"Typing channel name: {channel_name}")
                        page.keyboard.type(channel_name)
                        time.sleep(2)

                        safe_name = channel_name.replace('"', '\\"')
                        result = page.query_selector(f'span[title="{safe_name}"]') or \
                                 page.query_selector(f'span:has-text("{safe_name}")')

                        if result:
                            print("Found channel in results, clicking...")
                            result.click()
                        else:
                            print("Channel not found in visible results, pressing Enter as fallback...")
                            page.keyboard.press("Enter")

                    time.sleep(3)
                    
                    page.mouse.wheel(0, -2000) 
                    time.sleep(2)

                    messages = page.query_selector_all('[data-testid="msg-container"]') or \
                               page.query_selector_all('div[role="row"]')

                    print(f"Detected {len(messages)} message containers.")

                    for msg in messages:
                        text_element = msg.query_selector('.copyable-text') or \
                                       msg.query_selector('span.selectable-text')

                        if text_element:
                            text = text_element.inner_text()

                            msg_id = msg.get_attribute("data-id")
                            if not msg_id:
                                msg_id = hashlib.md5(text.encode("utf-8")).hexdigest()

                            if db.is_message_seen(channel_name, msg_id):
                                continue

                            new_jobs_messages.append({
                                "channel": channel_name,
                                "id": msg_id,
                                "text": text
                            })
                            db.mark_message_seen(channel_name, msg_id)
                except Exception as e:
                    print(f"Error checking channel {channel_name}: {e}")
        finally:
            if browser:
                browser.close()

        return new_jobs_messages

if __name__ == "__main__":
    messages = scrape_whatsapp()
    for m in messages:
        print(f"New message from {m['channel']}: {m['text'][:100]}...")
