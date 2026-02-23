# gmail_watcher.py
# Monitors Gmail for unread important emails
# Saves them as .md files in /Needs_Action

import time
import logging
from pathlib import Path
from datetime import datetime

# For actual use: install google-auth, google-api-python-client
# pip install google-auth google-auth-oauthlib google-api-python-client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VAULT_PATH = Path("./AI_Employee_Vault")
NEEDS_ACTION = VAULT_PATH / "Needs_Action"
CHECK_INTERVAL = 120  # seconds
PROCESSED_IDS_FILE = VAULT_PATH / "Logs" / "processed_emails.txt"

def load_processed_ids():
    if PROCESSED_IDS_FILE.exists():
        return set(PROCESSED_IDS_FILE.read_text().splitlines())
    return set()

def save_processed_id(email_id: str):
    PROCESSED_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_IDS_FILE, "a") as f:
        f.write(email_id + "\n")

def create_action_file(email_id: str, sender: str, subject: str, snippet: str):
    content = f"""---
type: email
from: {sender}
subject: {subject}
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## Email Content
{snippet}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
"""
    filepath = NEEDS_ACTION / f"EMAIL_{email_id}.md"
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content)
    logger.info(f"Created action file: {filepath.name}")
    return filepath

def check_gmail(service, processed_ids):
    """Check Gmail for unread important emails."""
    results = service.users().messages().list(
        userId='me', q='is:unread is:important'
    ).execute()
    messages = results.get('messages', [])
    new_messages = [m for m in messages if m['id'] not in processed_ids]
    
    for msg_ref in new_messages:
        msg = service.users().messages().get(
            userId='me', id=msg_ref['id']
        ).execute()
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        create_action_file(
            email_id=msg_ref['id'],
            sender=headers.get('From', 'Unknown'),
            subject=headers.get('Subject', 'No Subject'),
            snippet=msg.get('snippet', '')
        )
        processed_ids.add(msg_ref['id'])
        save_processed_id(msg_ref['id'])

def main():
    # Setup Gmail API
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file('credentials.json')
    service = build('gmail', 'v1', credentials=creds)
    processed_ids = load_processed_ids()

    logger.info("Gmail Watcher started. Checking every 120 seconds...")
    while True:
        try:
            check_gmail(service, processed_ids)
        except Exception as e:
            logger.error(f"Error checking Gmail: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
