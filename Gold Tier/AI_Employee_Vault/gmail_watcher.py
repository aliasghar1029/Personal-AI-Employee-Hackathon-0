# gmail_watcher.py
# Silver Tier: Monitors Gmail for unread important emails
# Saves them as .md files in /Needs_Action/
# Uses Google Gmail API with OAuth2

import os
import time
import logging
import base64
from pathlib import Path
from datetime import datetime
from email import message_from_bytes

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/gmail_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration - paths relative to script location (script is inside vault)
SCRIPT_DIR = Path(__file__).parent
VAULT_PATH = SCRIPT_DIR
NEEDS_ACTION = VAULT_PATH / 'Needs_Action'
LOGS_PATH = VAULT_PATH / 'Logs'
CREDENTIALS_FILE = SCRIPT_DIR / 'credentials.json'
TOKEN_FILE = SCRIPT_DIR / 'token.json'
PROCESSED_IDS_FILE = LOGS_PATH / 'processed_emails.txt'
CHECK_INTERVAL = int(os.getenv('GMAIL_CHECK_INTERVAL', '120'))
MAX_EMAILS_PER_HOUR = int(os.getenv('MAX_EMAILS_PER_HOUR', '50'))

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

class GmailWatcher:
    def __init__(self):
        self.service = None
        self.processed_ids = set()
        self.emails_this_hour = 0
        self.last_hour_reset = time.time()
        self._initialize()
    
    def _initialize(self):
        """Initialize Gmail API service and load processed IDs."""
        LOGS_PATH.mkdir(parents=True, exist_ok=True)
        NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
        
        self._load_processed_ids()
        self._authenticate()
    
    def _load_processed_ids(self):
        """Load previously processed email IDs."""
        if PROCESSED_IDS_FILE.exists():
            self.processed_ids = set(PROCESSED_IDS_FILE.read_text(encoding='utf-8').splitlines())
            logger.info(f"Loaded {len(self.processed_ids)} processed email IDs")
    
    def _save_processed_id(self, email_id: str):
        """Save a processed email ID."""
        self.processed_ids.add(email_id)
        with open(PROCESSED_IDS_FILE, 'a', encoding='utf-8') as f:
            f.write(email_id + '\n')
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        try:
            creds = None
            if TOKEN_FILE.exists():
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not CREDENTIALS_FILE.exists():
                        logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
                        logger.info("Please download credentials.json from Google Cloud Console")
                        return False
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                TOKEN_FILE.write_text(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API authentication successful")
            return True
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _reset_hourly_counter(self):
        """Reset hourly email counter if an hour has passed."""
        current_time = time.time()
        if current_time - self.last_hour_reset >= 3600:
            self.emails_this_hour = 0
            self.last_hour_reset = current_time
            logger.info("Reset hourly email counter")
    
    def _check_rate_limit(self) -> bool:
        """Check if we've hit the hourly rate limit."""
        self._reset_hourly_counter()
        return self.emails_this_hour < MAX_EMAILS_PER_HOUR
    
    def _decode_message(self, message: dict) -> dict:
        """Decode Gmail message parts."""
        try:
            msg_bytes = base64.urlsafe_b64decode(message['raw'])
            msg = message_from_bytes(msg_bytes)

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get("Content-Disposition"))
                    if ctype == "text/plain" and "attachment" not in cdispo:
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                            break
                        except:
                            pass
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                except:
                    body = msg.get_payload()

            headers = {h['name'].lower(): h['value'] for h in message['payload']['headers']}

            # Extract sender email address from 'from' header
            from_header = headers.get('from', 'Unknown')
            sender_email = self._extract_email_address(from_header)

            return {
                'from': sender_email,
                'from_full': from_header,
                'to': headers.get('to', ''),
                'subject': headers.get('subject', 'No Subject'),
                'date': headers.get('date', ''),
                'body': body,
                'snippet': message.get('snippet', '')
            }
        except Exception as e:
            logger.error(f"Error decoding message: {e}")
            return {
                'from': 'Unknown',
                'from_full': 'Unknown',
                'to': '',
                'subject': 'Error decoding',
                'date': '',
                'body': '',
                'snippet': message.get('snippet', '')
            }

    def _extract_email_address(self, from_string: str) -> str:
        """Extract email address from 'From' header string."""
        import re
        if not from_string or from_string == 'Unknown':
            return 'Unknown'
        
        # Try to find email in format: "Name <email@domain.com>" or just "email@domain.com"
        email_match = re.search(r'<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?', from_string)
        if email_match:
            return email_match.group(1)
        
        # If no email found, return the original string
        return from_string
    
    def _create_action_file(self, email_id: str, email_data: dict) -> Path:
        """Create a markdown action file for the email."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_subject = "".join(c for c in email_data['subject'] if c.isalnum() or c in ' -_')[:50]
        filename = f"EMAIL_{timestamp}_{safe_subject}.md"
        
        # Determine priority based on keywords
        priority = 'normal'
        urgent_keywords = ['urgent', 'asap', 'immediate', 'emergency', 'invoice', 'payment']
        subject_lower = email_data['subject'].lower()
        if any(kw in subject_lower for kw in urgent_keywords):
            priority = 'high'
        
        content = f"""---
type: email
from: {email_data['from']}
to: {email_data['to']}
subject: {email_data['subject']}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
email_id: {email_id}
---

# Email: {email_data['subject']}

**From:** {email_data['from']}  
**Received:** {email_data['date']}  
**Priority:** {priority.upper()}

---

## Content

{email_data['body'] if email_data['body'] else email_data['snippet']}

---

## Suggested Actions

- [ ] Read and understand the email
- [ ] Determine if reply is needed
- [ ] If reply needed, draft response in /Pending_Approval/
- [ ] Forward to relevant party if needed
- [ ] Archive after processing

## Notes

_Add any notes or context here_

---
*Processed by Gmail Watcher - Silver Tier*
"""
        
        filepath = NEEDS_ACTION / filename
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"Created action file: {filename}")
        return filepath
    
    def check_gmail(self):
        """Check Gmail for new unread emails."""
        if not self.service:
            logger.warning("Gmail service not initialized")
            return

        if not self._check_rate_limit():
            logger.warning(f"Rate limit reached ({MAX_EMAILS_PER_HOUR} emails/hour)")
            return

        try:
            # Fetch all unread messages from last 1 hour
            logger.info("Checking Gmail for new emails...")
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread newer_than:1h',
                maxResults=10
            ).execute()

            messages = results.get('messages', [])
            new_messages = [m for m in messages if m['id'] not in self.processed_ids]

            logger.info(f"Checking Gmail... Found {len(new_messages)} new email(s)")

            if not new_messages:
                logger.info("No new emails")
                return

            logger.info(f"Found {len(new_messages)} new email(s) to process")
            
            for msg_ref in new_messages:
                if not self._check_rate_limit():
                    logger.warning("Rate limit reached during processing")
                    break
                
                # Get full message
                msg = self.service.users().messages().get(
                    userId='me',
                    id=msg_ref['id'],
                    format='raw'
                ).execute()
                
                email_data = self._decode_message(msg)
                self._create_action_file(msg_ref['id'], email_data)
                
                # Mark as processed (but don't mark as read in Gmail)
                self._save_processed_id(msg_ref['id'])
                self.emails_this_hour += 1
            
            # Update dashboard
            self._update_dashboard(len(new_messages))
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
        except Exception as e:
            logger.error(f"Error checking Gmail: {e}")
    
    def _update_dashboard(self, new_emails_count: int):
        """Update the Dashboard.md with Gmail status."""
        dashboard_path = VAULT_PATH / 'Dashboard.md'
        
        try:
            if not dashboard_path.exists():
                return
            
            content = dashboard_path.read_text(encoding='utf-8')
            
            # Add Gmail status section if not exists
            gmail_section = f"""
## Gmail Status
- Last Checked: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- New Emails: {new_emails_count}
- Processed This Hour: {self.emails_this_hour}/{MAX_EMAILS_PER_HOUR}
"""
            
            if '## Gmail Status' not in content:
                content += '\n' + gmail_section
            else:
                # Update existing section
                lines = content.split('\n')
                new_lines = []
                in_gmail_section = False
                for line in lines:
                    if line.startswith('## Gmail Status'):
                        in_gmail_section = True
                        new_lines.append(gmail_section.strip())
                    elif in_gmail_section and line.startswith('## '):
                        in_gmail_section = False
                        new_lines.append(line)
                    elif not in_gmail_section:
                        new_lines.append(line)
                content = '\n'.join(new_lines)
            
            dashboard_path.write_text(content, encoding='utf-8')
            logger.info("Dashboard updated")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def run(self):
        """Main run loop."""
        logger.info(f"Gmail Watcher started. Checking every {CHECK_INTERVAL} seconds...")
        logger.info(f"Vault: {VAULT_PATH.resolve()}")
        logger.info(f"Max emails per hour: {MAX_EMAILS_PER_HOUR}")
        
        while True:
            try:
                self.check_gmail()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            time.sleep(CHECK_INTERVAL)


def main():
    """Entry point."""
    try:
        watcher = GmailWatcher()
        if watcher.service:
            watcher.run()
        else:
            logger.error("Failed to initialize Gmail Watcher")
    except KeyboardInterrupt:
        logger.info("Gmail Watcher stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
