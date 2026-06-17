import time
import config
import db
from playwright.sync_api import sync_playwright

def scrape_whatsapp():
    db.init_db()
    with sync_playwright() as p:
        # Launch browser with persistent context to save session
        browser = p.chromium.launch_persistent_context(
            user_data_dir=config.CHROME_DATA_DIR,
            headless=False  # WhatsApp Web needs to be visible for QR/initial setup
        )
        page = browser.new_page()
        page.goto("https://web.whatsapp.com")
        
        print("Waiting for WhatsApp Web to load...")
        print("ACTION REQUIRED: If you see a QR code, please scan it with your WhatsApp app.")
        
        # Wait for the chat list or the search box to appear
        try:
            # chat-list is usually present after login
            page.wait_for_selector('[data-testid="chat-list"]', timeout=60000)
            print("Login successful!")
        except Exception:
            print("Login timeout. Please ensure you have scanned the QR code.")
            # Take a screenshot if possible? No, but let's at least wait a bit more.
            time.sleep(10)
            return []

        new_jobs_messages = []

        for channel_name in config.WHATSAPP_CHANNELS:
            print(f"Checking channel: {channel_name}")
            try:
                # 1. Try to click the "Channels/Updates" sidebar button first
                print("Navigating to Channels/Updates tab...")
                channels_tab = page.query_selector('[data-testid="newsletter-outline-draft"]') or \
                               page.query_selector('[data-testid="newsletter-outline"]') or \
                               page.query_selector('span[data-icon="newsletter-outline"]')
                
                if channels_tab:
                    channels_tab.click()
                    time.sleep(2)
                
                # 2. Check if the channel is already open
                header = page.query_selector('[data-testid="conversation-info-header"]')
                if header and channel_name.lower() in header.inner_text().lower():
                    print(f"Channel {channel_name} is already open.")
                else:
                    # 2. Try to search using keyboard shortcut (Ctrl + Alt + /)
                    print("Attempting to focus search bar via shortcut...")
                    page.keyboard.press("Control+Alt+/")
                    time.sleep(2)
                    
                    # 3. Blind type the channel name
                    print(f"Typing channel name: {channel_name}")
                    page.keyboard.type(channel_name)
                    time.sleep(2)
                    
                    # 4. Try to find the result in the list and click it
                    # This is more reliable than just pressing Enter
                    result = page.query_selector(f'span[title="{channel_name}"]') or \
                             page.query_selector(f'span:has-text("{channel_name}")')
                    
                    if result:
                        print("Found channel in results, clicking...")
                        result.click()
                    else:
                        print("Channel not found in visible results, pressing Enter as fallback...")
                        page.keyboard.press("Enter")
                
                # Wait for the channel to open and load messages
                time.sleep(3) 
                
                # 5. Extract messages
                # Try multiple selectors for messages as WhatsApp UI changes
                messages = page.query_selector_all('[data-testid="msg-container"]') or \
                           page.query_selector_all('div[role="row"]')
                
                print(f"Detected {len(messages)} message containers.")
                
                for msg in messages:
                    # Extract text - looking for common message text classes
                    text_element = msg.query_selector('.copyable-text') or \
                                   msg.query_selector('span.selectable-text')
                    
                    if text_element:
                        text = text_element.inner_text()
                        
                        # Use a hash of the text + timestamp/sender as a fallback ID if data-id is missing
                        msg_id = msg.get_attribute("data-id") or str(hash(text))
                        
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

        browser.close()
        return new_jobs_messages

if __name__ == "__main__":
    messages = scrape_whatsapp()
    for m in messages:
        print(f"New message from {m['channel']}: {m['text'][:100]}...")
