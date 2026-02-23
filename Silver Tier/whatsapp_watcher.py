# whatsapp_watcher.py
# Silver Tier: Monitors WhatsApp Web for urgent messages
# Uses Playwright for WhatsApp Web automation
# Saves detected messages as .md files in /Needs_Action/

import os
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/whatsapp_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './AI_Employee_Vault'))
NEEDS_ACTION = VAULT_PATH / 'Needs_Action'
LOGS_PATH = VAULT_PATH / 'Logs'
SESSION_PATH = Path(os.getenv('WHATSAPP_SESSION_PATH', './whatsapp_session'))
CHECK_INTERVAL = int(os.getenv('WHATSAPP_CHECK_INTERVAL', '60'))
PROCESSED_MESSAGES_FILE = LOGS_PATH / 'processed_whatsapp.json'

# Keywords to watch for (case-insensitive)
URGENT_KEYWORDS = [
    'urgent', 'asap', 'invoice', 'payment', 'help', 'price', 'pricing',
    'emergency', 'immediate', 'money', 'bank', 'transfer', 'deadline'
]

class WhatsAppWatcher:
    def __init__(self):
        self.processed_messages = set()
        self._initialize()
    
    def _initialize(self):
        """Initialize watcher and load processed messages."""
        LOGS_PATH.mkdir(parents=True, exist_ok=True)
        NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
        SESSION_PATH.mkdir(parents=True, exist_ok=True)
        self._load_processed_messages()
    
    def _load_processed_messages(self):
        """Load previously processed message IDs."""
        if PROCESSED_MESSAGES_FILE.exists():
            try:
                data = json.loads(PROCESSED_MESSAGES_FILE.read_text(encoding='utf-8'))
                self.processed_messages = set(data.get('processed_ids', []))
                logger.info(f"Loaded {len(self.processed_messages)} processed message IDs")
            except:
                self.processed_messages = set()
        else:
            self.processed_messages = set()
    
    def _save_processed_message(self, message_id: str):
        """Save a processed message ID."""
        self.processed_messages.add(message_id)
        data = {'processed_ids': list(self.processed_messages), 'last_updated': datetime.now().isoformat()}
        PROCESSED_MESSAGES_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def _contains_urgent_keyword(self, text: str) -> bool:
        """Check if message contains urgent keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in URGENT_KEYWORDS)
    
    def _create_action_file(self, chat_name: str, message_text: str, timestamp: str) -> Path:
        """Create a markdown action file for the WhatsApp message."""
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_chat = "".join(c for c in chat_name if c.isalnum() or c in ' -_')[:30]
        filename = f"WHATSAPP_{ts}_{safe_chat}.md"
        
        # Determine priority
        priority = 'normal'
        if self._contains_urgent_keyword(message_text):
            priority = 'high'
        
        content = f"""---
type: whatsapp
from: {chat_name}
received: {timestamp}
processed: {datetime.now().isoformat()}
priority: {priority}
status: pending
---

# WhatsApp Message

**From:** {chat_name}  
**Received:** {timestamp}  
**Priority:** {priority.upper()}

---

## Message Content

{message_text}

---

## Urgency Analysis

**Contains urgent keywords:** {'Yes' if self._contains_urgent_keyword(message_text) else 'No'}

"""
        
        if self._contains_urgent_keyword(message_text):
            found_keywords = [kw for kw in URGENT_KEYWORDS if kw in message_text.lower()]
            content += f"**Keywords found:** {', '.join(found_keywords)}\n\n"
        
        content += """
## Suggested Actions

- [ ] Read and understand the message
- [ ] Determine if immediate response is needed
- [ ] Draft response in /Pending_Approval/ if needed
- [ ] Take appropriate action based on message content
- [ ] Move to /Done when complete

## Notes

_Add any notes or context here_

---
*Processed by WhatsApp Watcher - Silver Tier*
"""
        
        filepath = NEEDS_ACTION / filename
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"Created action file: {filename}")
        return filepath
    
    def check_whatsapp(self):
        """Check WhatsApp Web for new urgent messages."""
        try:
            with sync_playwright() as p:
                logger.info("Launching browser...")

                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    str(SESSION_PATH),
                    headless=False,
                    args=[
                        '--disable-gpu',
                        '--disable-dev-shm-usage',
                        '--disable-setuid-sandbox',
                        '--no-sandbox'
                    ]
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate to WhatsApp Web
                logger.info("Navigating to WhatsApp Web...")
                page.goto('https://web.whatsapp.com', timeout=60000)

                # Wait for chat list to load (indicates successful login)
                try:
                    page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
                    logger.info("WhatsApp Web loaded successfully")
                except PlaywrightTimeout:
                    logger.warning("WhatsApp Web not fully loaded or not logged in")
                    logger.info("Please scan QR code on your first run")
                    browser.close()
                    return

                # Give it a moment to load messages
                time.sleep(3)

                # Find all chat items with unread messages
                unread_chats = []
                try:
                    # Use correct selector for chat cells
                    chats = page.query_selector_all('[data-testid="cell-frame-container"]')
                    
                    if not chats:
                        print("No unread messages found")
                        logger.info("No unread messages found")
                        browser.close()
                        return

                    for chat in chats:
                        try:
                            # Check for unread badge
                            unread_badge = chat.query_selector('[data-testid="icon-unread-count"]')
                            if not unread_badge:
                                continue

                            # Get chat name
                            name_elem = chat.query_selector('[title]')
                            chat_name = name_elem.get_attribute('title') if name_elem else 'Unknown'

                            # Get message text
                            msg_elem = chat.query_selector('span[title]')
                            if msg_elem:
                                msg_text = msg_elem.inner_text()

                                # Generate unique ID
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                msg_id = f"{chat_name}:{msg_text[:50]}:{timestamp}"

                                if msg_id not in self.processed_messages:
                                    # Print to terminal
                                    print(f"New WhatsApp message detected from: {chat_name}")
                                    print(f"Message: {msg_text}")
                                    logger.info(f"New message from {chat_name}: {msg_text}")

                                    unread_chats.append({
                                        'name': chat_name,
                                        'text': msg_text,
                                        'id': msg_id
                                    })
                        except Exception as e:
                            logger.debug(f"Error processing chat: {e}")
                            continue

                except Exception as e:
                    logger.error(f"Error finding unread chats: {e}")
                    print("No unread messages found")

                if not unread_chats:
                    print("No unread messages found")

                logger.info(f"Found {len(unread_chats)} unread message(s)")

                # Create action files for unread messages
                for chat in unread_chats:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self._create_action_file(chat['name'], chat['text'], timestamp)
                    self._save_processed_message(chat['id'])

                browser.close()

                # Update dashboard
                self._update_dashboard(len(unread_chats))

        except Exception as e:
            logger.error(f"Error checking WhatsApp: {e}")
            print("No unread messages found")
    
    def _update_dashboard(self, new_messages_count: int):
        """Update the Dashboard.md with WhatsApp status."""
        dashboard_path = VAULT_PATH / 'Dashboard.md'
        
        try:
            if not dashboard_path.exists():
                return
            
            content = dashboard_path.read_text(encoding='utf-8')
            
            # Add WhatsApp status section if not exists
            whatsapp_section = f"""
## WhatsApp Status
- Last Checked: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Urgent Messages: {new_messages_count}
- Total Processed: {len(self.processed_messages)}
"""
            
            if '## WhatsApp Status' not in content:
                content += '\n' + whatsapp_section
            else:
                # Update existing section
                lines = content.split('\n')
                new_lines = []
                in_section = False
                for line in lines:
                    if line.startswith('## WhatsApp Status'):
                        in_section = True
                        new_lines.append(whatsapp_section.strip())
                    elif in_section and line.startswith('## '):
                        in_section = False
                        new_lines.append(line)
                    elif not in_section:
                        new_lines.append(line)
                content = '\n'.join(new_lines)
            
            dashboard_path.write_text(content, encoding='utf-8')
            logger.info("Dashboard updated")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def run(self):
        """Main run loop."""
        logger.info(f"WhatsApp Watcher started. Checking every {CHECK_INTERVAL} seconds...")
        logger.info(f"Vault: {VAULT_PATH.resolve()}")
        logger.info(f"Session: {SESSION_PATH.resolve()}")
        logger.info(f"Keywords: {', '.join(URGENT_KEYWORDS)}")
        
        while True:
            try:
                self.check_whatsapp()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            time.sleep(CHECK_INTERVAL)


def main():
    """Entry point."""
    try:
        watcher = WhatsAppWatcher()
        watcher.run()
    except KeyboardInterrupt:
        logger.info("WhatsApp Watcher stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
