# email_mcp_server.py
# Silver Tier: A local MCP server that can SEND emails via Gmail
# Only sends after file is moved to /Approved/ folder
# Logs every sent email to /Logs/
# Never sends without approval

import os
import time
import logging
import json
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/email_mcp.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './AI_Employee_Vault'))
APPROVED_PATH = VAULT_PATH / 'Approved'
REJECTED_PATH = VAULT_PATH / 'Rejected'
SENT_PATH = VAULT_PATH / 'Sent'
LOGS_PATH = VAULT_PATH / 'Logs'
CREDENTIALS_FILE = VAULT_PATH / 'credentials.json'
TOKEN_FILE = VAULT_PATH / 'token.json'
SENT_LOG = LOGS_PATH / 'sent_emails.json'
CHECK_INTERVAL = int(os.getenv('EMAIL_CHECK_INTERVAL', '30'))
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

class EmailMCPServer:
    def __init__(self):
        self.service = None
        self.sent_emails = []
        self._initialize()
    
    def _initialize(self):
        """Initialize email MCP server."""
        APPROVED_PATH.mkdir(parents=True, exist_ok=True)
        REJECTED_PATH.mkdir(parents=True, exist_ok=True)
        SENT_PATH.mkdir(parents=True, exist_ok=True)
        LOGS_PATH.mkdir(parents=True, exist_ok=True)
        
        self._load_sent_history()
        self._authenticate()
    
    def _load_sent_history(self):
        """Load previously sent emails log."""
        if SENT_LOG.exists():
            try:
                data = json.loads(SENT_LOG.read_text(encoding='utf-8'))
                self.sent_emails = data.get('sent_emails', [])
                logger.info(f"Loaded {len(self.sent_emails)} sent email records")
            except:
                self.sent_emails = []
        else:
            self.sent_emails = []
    
    def _save_sent_email(self, email_data: dict):
        """Save a sent email record."""
        self.sent_emails.append(email_data)
        data = {
            'sent_emails': self.sent_emails,
            'last_updated': datetime.now().isoformat()
        }
        SENT_LOG.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def _authenticate(self):
        """Authenticate with Gmail API for sending."""
        try:
            creds = None
            if TOKEN_FILE.exists():
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    from google.auth.transport.requests import Request
                    creds.refresh(Request())
                else:
                    if not CREDENTIALS_FILE.exists():
                        logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
                        logger.info("Please download credentials.json from Google Cloud Console")
                        logger.info("Enable Gmail API and create OAuth 2.0 credentials")
                        return False
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                TOKEN_FILE.write_text(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API authentication successful for sending")
            return True
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _parse_approval_file(self, filepath: Path) -> dict:
        """Parse an approval file for email sending."""
        content = filepath.read_text(encoding='utf-8')
        
        email_data = {
            'to': '',
            'cc': '',
            'bcc': '',
            'subject': '',
            'body': '',
            'filename': filepath.name,
            'approved_at': None
        }
        
        # Extract frontmatter
        lines = content.split('\n')
        in_frontmatter = False
        
        for i, line in enumerate(lines):
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
                continue
            
            if in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'to':
                    email_data['to'] = value
                elif key == 'cc':
                    email_data['cc'] = value
                elif key == 'bcc':
                    email_data['bcc'] = value
                elif key == 'subject':
                    email_data['subject'] = value
                elif key == 'approved_at':
                    email_data['approved_at'] = value
        
        # Get email body (everything after frontmatter)
        body_start = 0
        for i, line in enumerate(lines):
            if line.strip() == '---' and i > 0:
                body_start = i + 1
                break
        
        email_data['body'] = '\n'.join(lines[body_start:]).strip()
        
        # Remove any markdown headers from body
        body_lines = email_data['body'].split('\n')
        clean_body = []
        for line in body_lines:
            if not line.startswith('#'):
                clean_body.append(line)
        email_data['body'] = '\n'.join(clean_body).strip()
        
        return email_data
    
    def _create_message(self, email_data: dict) -> dict:
        """Create a Gmail API message."""
        message = MIMEMultipart()
        message['to'] = email_data['to']
        message['subject'] = email_data['subject']
        
        if email_data['cc']:
            message['cc'] = email_data['cc']
        
        message.attach(MIMEText(email_data['body'], 'plain', 'utf-8'))
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}
    
    def send_email(self, email_data: dict) -> bool:
        """Send an email via Gmail API."""
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would send email to: {email_data['to']}")
            logger.info(f"[DRY_RUN] Subject: {email_data['subject']}")
            logger.info(f"[DRY_RUN] Body preview: {email_data['body'][:100]}...")

            # Log as dry run
            email_record = {
                'id': f"dry_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'filename': email_data['filename'],
                'to': email_data['to'],
                'subject': email_data['subject'],
                'sent_at': datetime.now().isoformat(),
                'status': 'dry_run'
            }
            self._save_sent_email(email_record)

            # Move file to Done folder
            done_path = VAULT_PATH / 'Done' / email_data['filename']
            done_path.parent.mkdir(parents=True, exist_ok=True)
            filepath = APPROVED_PATH / email_data['filename']
            if filepath.exists():
                filepath.rename(done_path)

            self._update_dashboard('sent_dry_run')
            return True

        try:
            message = self._create_message(email_data)

            sent_message = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()

            logger.info(f"Email sent successfully: {sent_message['id']}")
            print("Email sent successfully!")

            # Log sent email
            email_record = {
                'id': sent_message['id'],
                'filename': email_data['filename'],
                'to': email_data['to'],
                'subject': email_data['subject'],
                'sent_at': datetime.now().isoformat(),
                'status': 'sent'
            }
            self._save_sent_email(email_record)

            # Move file to Done folder
            done_path = VAULT_PATH / 'Done' / email_data['filename']
            done_path.parent.mkdir(parents=True, exist_ok=True)
            filepath = APPROVED_PATH / email_data['filename']
            if filepath.exists():
                filepath.rename(done_path)

            self._update_dashboard('sent')
            return True

        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            self._handle_error(email_data, str(error))
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            self._handle_error(email_data, str(e))
            return False
    
    def _handle_error(self, email_data: dict, error: str):
        """Handle sending error - move to rejected."""
        error_path = REJECTED_PATH / f"ERROR_{email_data['filename']}"
        filepath = APPROVED_PATH / email_data['filename']
        
        if filepath.exists():
            content = filepath.read_text(encoding='utf-8')
            error_content = f"""---
original_file: {email_data['filename']}
error: {error}
failed_at: {datetime.now().isoformat()}
status: failed
---

{content}
"""
            error_path.write_text(error_content, encoding='utf-8')
            filepath.unlink()
    
    def check_approved_folder(self):
        """Check the Approved folder for emails to send."""
        try:
            # Get all markdown files in Approved
            approval_files = list(APPROVED_PATH.glob('*.md'))

            # Also check for email-specific files
            email_files = [f for f in approval_files if self._is_email_file(f)]

            if not email_files:
                logger.debug("No approval files to process")
                return

            logger.info(f"Found {len(email_files)} approval file(s) to process")

            for approval_file in email_files:
                logger.info(f"Processing: {approval_file.name}")

                # Parse the approval file
                email_data = self._parse_approval_file(approval_file)

                # If this is a reply and 'to' is 'Unknown' or placeholder, try to get from original email
                if email_data.get('to') in ['', 'Unknown', '[RECIPIENT_EMAIL_NEEDED]']:
                    original_email = self._find_original_email(approval_file)
                    if original_email and original_email.get('from'):
                        email_data['to'] = original_email['from']
                        logger.info(f"Auto-filled recipient from original email: {email_data['to']}")

                # Validate required fields
                if not email_data['to']:
                    print("Error: Invalid email address found in file")
                    logger.error(f"No 'to' field in {approval_file.name}")
                    continue

                # Validate email address contains @ symbol
                if '@' not in email_data['to']:
                    print("Error: Invalid email address found in file")
                    logger.error(f"Invalid email address '{email_data['to']}' in {approval_file.name}")
                    continue

                if not email_data['subject']:
                    logger.error(f"No 'subject' field in {approval_file.name}")
                    continue

                # Print the email address being sent to
                print(f"Sending email to: {email_data['to']}")
                logger.info(f"Sending email to: {email_data['to']}")

                # Send the email
                success = self.send_email(email_data)

                if success:
                    logger.info(f"Successfully processed: {approval_file.name}")
                else:
                    logger.error(f"Failed to process: {approval_file.name}")

            # Update dashboard
            self._update_dashboard()

        except Exception as e:
            logger.error(f"Error checking approved folder: {e}")
    
    def _is_email_file(self, filepath: Path) -> bool:
        """Check if a file is an email approval file."""
        content = filepath.read_text(encoding='utf-8').lower()
        return 'type: email' in content or 'to:' in content

    def _find_original_email(self, reply_file: Path) -> dict:
        """Find the original email in Needs_Action folder based on reply file."""
        content = reply_file.read_text(encoding='utf-8')
        
        # Extract original_email_id from reply file
        import re
        id_match = re.search(r'original_email_id:\s*(\S+)', content)
        if not id_match:
            return None
        
        original_id = id_match.group(1)
        
        # Search in Needs_Action folder for matching email
        needs_action_path = VAULT_PATH / 'Needs_Action'
        if not needs_action_path.exists():
            return None
        
        for email_file in needs_action_path.glob('*.md'):
            email_content = email_file.read_text(encoding='utf-8')
            if f'email_id: {original_id}' in email_content:
                # Parse the original email
                return self._parse_original_email(email_content)
        
        return None

    def _parse_original_email(self, content: str) -> dict:
        """Parse original email content to extract sender info."""
        email_data = {'from': '', 'to': '', 'subject': ''}
        
        lines = content.split('\n')
        in_frontmatter = False
        
        for line in lines:
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
                continue
            
            if in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'from':
                    email_data['from'] = value
                elif key == 'to':
                    email_data['to'] = value
                elif key == 'subject':
                    email_data['subject'] = value
        
        return email_data
    
    def _update_dashboard(self, action: str = None):
        """Update the Dashboard.md with email status."""
        dashboard_path = VAULT_PATH / 'Dashboard.md'
        
        try:
            if not dashboard_path.exists():
                return
            
            content = dashboard_path.read_text(encoding='utf-8')
            
            # Count emails sent today
            today = datetime.now().strftime('%Y-%m-%d')
            emails_today = len([e for e in self.sent_emails if today in e.get('sent_at', '')])
            
            # Add Email Status section if not exists
            email_section = f"""
## Email Status
- Last Checked: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Emails Sent Today: {emails_today}
- Total Emails Sent: {len(self.sent_emails)}
- DRY_RUN: {'Yes' if DRY_RUN else 'No'}
"""
            
            if '## Email Status' not in content:
                content += '\n' + email_section
            else:
                # Update existing section
                lines = content.split('\n')
                new_lines = []
                in_section = False
                for line in lines:
                    if line.startswith('## Email Status'):
                        in_section = True
                        new_lines.append(email_section.strip())
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
        logger.info(f"Email MCP Server started. Checking every {CHECK_INTERVAL} seconds...")
        logger.info(f"Vault: {VAULT_PATH.resolve()}")
        logger.info(f"Approved: {APPROVED_PATH.resolve()}")
        logger.info(f"DRY_RUN: {DRY_RUN}")
        
        while True:
            try:
                self.check_approved_folder()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            time.sleep(CHECK_INTERVAL)


def main():
    """Entry point."""
    try:
        server = EmailMCPServer()
        if server.service:
            server.run()
        else:
            logger.warning("Email MCP Server running without Gmail authentication")
            logger.info("Emails will be logged but not sent until credentials are configured")
            # Still run to process files in DRY_RUN mode
            server.run()
    except KeyboardInterrupt:
        logger.info("Email MCP Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
