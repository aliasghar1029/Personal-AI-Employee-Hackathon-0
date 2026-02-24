# linkedin_poster.py
# Silver Tier: Reads post content from /Social/LinkedIn_Queue/ folder
# Automatically posts to LinkedIn using LinkedIn API with OAuth2
# Saves posting log in /Logs/
# Updates Dashboard.md after posting

import os
import time
import logging
import json
import hashlib
import base64
import webbrowser
import http.server
import socketserver
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv, set_key
from urllib.parse import urlencode, parse_qs, urlparse
import requests

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/linkedin_poster.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', '.'))
SOCIAL_PATH = VAULT_PATH / 'Social'
LINKEDIN_QUEUE = SOCIAL_PATH / 'LinkedIn_Queue'
LINKEDIN_DONE = SOCIAL_PATH / 'Done'
LOGS_PATH = Path('Logs')
POST_LOG = LOGS_PATH / 'linkedin_posts.json'
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'

# LinkedIn OAuth2 Configuration
LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID', '')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET', '')
LINKEDIN_ACCESS_TOKEN = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
LINKEDIN_REDIRECT_URI = 'http://localhost:8080/callback'
LINKEDIN_AUTH_URL = 'https://www.linkedin.com/oauth/v2/authorization'
LINKEDIN_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
LINKEDIN_API_BASE = 'https://api.linkedin.com/v2'

# LinkedIn Poster Settings
CHECK_INTERVAL = int(os.getenv('LINKEDIN_CHECK_INTERVAL', '60'))  # 1 minute
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'


class LinkedInAuthHandler:
    """Handle OAuth2 authentication with LinkedIn."""
    
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state = self._generate_state()
        self.auth_code = None
    
    def _generate_state(self):
        """Generate a random state parameter for CSRF protection."""
        return hashlib.sha256(os.urandom(32)).hexdigest()
    
    def get_authorization_url(self):
        """Generate the OAuth2 authorization URL."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope': 'openid profile w_member_social'
        }
        return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token."""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(LINKEDIN_TOKEN_URL, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data.get('access_token')
    
    def start_auth_flow(self):
        """Start the OAuth2 flow by opening browser."""
        auth_url = self.get_authorization_url()

        print("\n" + "="*60)
        print("LinkedIn OAuth2 Authorization Required")
        print("="*60)
        print("\nOpening LinkedIn login page in browser...")
        print("Please login and authorize the app")
        print(f"\nAuthorization URL: {auth_url}")

        # Open browser immediately
        webbrowser.open(auth_url)

        print("\nWaiting for authorization callback on http://localhost:8080/callback...")

        # Start local server to catch callback
        self.auth_code = self._wait_for_callback()

        if self.auth_code:
            access_token = self.exchange_code_for_token(self.auth_code)
            return access_token
        return None
    
    def _wait_for_callback(self, timeout=60):
        """Wait for OAuth2 callback from local server."""
        auth_code_container = {'code': None}
        
        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith('/callback'):
                    print(f"Callback received: {self.path}")
                    
                    if '?' in self.path:
                        parsed = urlparse(self.path)
                        params = parse_qs(parsed.query)
                        code = params.get('code', [None])[0]
                        
                        if code:
                            print("Authorization code received!")
                            print("Exchanging code for access token...")
                            auth_code_container['code'] = code
                            
                            self.send_response(200)
                            self.send_header('Content-type', 'text/html')
                            self.end_headers()
                            response_html = """
                            <html>
                                <body>
                                    <h1>LinkedIn Authorization Successful!</h1>
                                    <p>You can close this window and return to the application.</p>
                                    <script>setTimeout(() => window.close(), 3000);</script>
                                </body>
                            </html>
                            """
                            self.wfile.write(response_html.encode())
                        else:
                            print("No code parameter in callback")
                            self.send_response(400)
                            self.end_headers()
                            self.wfile.write(b'No code parameter')
                    else:
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b'OK')
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suppress logging
        
        # Start server
        with socketserver.TCPServer(('localhost', 8080), CallbackHandler) as httpd:
            httpd.state = self.state
            httpd.timeout = 5
            start_time = time.time()
            
            while auth_code_container['code'] is None:
                if time.time() - start_time > timeout:
                    logger.error("OAuth2 callback timeout")
                    return None
                httpd.handle_request()
        
        return auth_code_container['code']


class LinkedInPoster:
    def __init__(self):
        self.posted_posts = set()
        self.access_token = LINKEDIN_ACCESS_TOKEN
        self.user_id = None
        self.posts_published = 0
        self._initialize()

    def _initialize(self):
        """Initialize poster and load posted history."""
        LINKEDIN_QUEUE.mkdir(parents=True, exist_ok=True)
        LINKEDIN_DONE.mkdir(parents=True, exist_ok=True)
        LOGS_PATH.mkdir(parents=True, exist_ok=True)
        self._load_posted_history()

        # Delete old token and re-authenticate
        logger.info("Deleting old access token for fresh authentication...")
        self._delete_access_token()
        self._authenticate()

    def _delete_access_token(self):
        """Delete old access token from .env file."""
        env_path = Path('.env')
        if not env_path.exists():
            env_path = Path('AI_Employee_Vault/.env')

        if env_path.exists():
            set_key(str(env_path), 'LINKEDIN_ACCESS_TOKEN', '')
            logger.info("Old access token deleted from .env file")

    def _authenticate(self):
        """Perform OAuth2 authentication with LinkedIn."""
        auth_handler = LinkedInAuthHandler(
            LINKEDIN_CLIENT_ID,
            LINKEDIN_CLIENT_SECRET,
            LINKEDIN_REDIRECT_URI
        )

        access_token = auth_handler.start_auth_flow()

        if access_token:
            self.access_token = access_token
            self._save_access_token(access_token)
            print("LinkedIn connected successfully!")
            logger.info("Access token saved successfully")
        else:
            logger.error("Failed to obtain access token")

    def _save_access_token(self, token):
        """Save access token to .env file."""
        env_path = Path('.env')
        if not env_path.exists():
            env_path = Path('AI_Employee_Vault/.env')
        
        if env_path.exists():
            set_key(str(env_path), 'LINKEDIN_ACCESS_TOKEN', token)
            logger.info("Access token saved to .env file")
        else:
            logger.warning(".env file not found, token not saved")

    def _load_posted_history(self):
        """Load previously posted post IDs."""
        if POST_LOG.exists():
            try:
                data = json.loads(POST_LOG.read_text(encoding='utf-8'))
                self.posted_posts = set(data.get('posted_ids', []))
                logger.info(f"Loaded {len(self.posted_posts)} posted post IDs")
            except:
                self.posted_posts = set()
        else:
            self.posted_posts = set()

    def _save_posted_post(self, post_id: str, post_data: dict):
        """Save a posted post record."""
        self.posted_posts.add(post_id)
        
        # Load existing data first
        existing_data = {'posts': []}
        if POST_LOG.exists():
            try:
                existing_data = json.loads(POST_LOG.read_text(encoding='utf-8'))
            except:
                existing_data = {'posts': []}
        
        data = {
            'posted_ids': list(self.posted_posts),
            'posts': existing_data.get('posts', []) + [post_data],
            'last_updated': datetime.now().isoformat()
        }
        POST_LOG.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def _parse_post_file(self, filepath: Path) -> dict:
        """Parse a markdown post file."""
        content = filepath.read_text(encoding='utf-8')

        post_data = {
            'content': '',
            'hashtags': [],
            'image': None,
            'scheduled_time': None,
            'filename': filepath.name
        }

        lines = content.split('\n')
        in_frontmatter = False
        frontmatter_end = 0

        for i, line in enumerate(lines):
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                    frontmatter_end = i
                else:
                    frontmatter_end = i + 1
                    break

            if in_frontmatter and i > 0:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if key == 'hashtags':
                        post_data['hashtags'] = [h.strip() for h in value.split(',')]
                    elif key == 'image':
                        post_data['image'] = value
                    elif key == 'scheduled_time':
                        post_data['scheduled_time'] = value

        post_data['content'] = '\n'.join(lines[frontmatter_end:]).strip()
        return post_data

    def _create_post_log(self, filename: str, status: str, error: str = None):
        """Create a log entry for the post attempt."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'status': status,
            'error': error
        }

        daily_log = LOGS_PATH / f'linkedin_{datetime.now().strftime("%Y%m%d")}.log'
        with open(daily_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')

    def _get_person_urn(self):
        """Get the person URN for the authenticated user using OpenID Connect userinfo endpoint."""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
        }

        response = requests.get(
            'https://api.linkedin.com/v2/userinfo',
            headers=headers
        )
        response.raise_for_status()

        profile_data = response.json()
        self.user_id = profile_data.get('sub')
        logger.info(f"User ID obtained from OpenID Connect: {self.user_id}")
        return self.user_id

    def post_to_linkedin(self, post_data: dict) -> bool:
        """Post content to LinkedIn using LinkedIn API."""
        file_moved = False
        
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would post: {post_data['filename']}")
            logger.info(f"[DRY_RUN] Content preview: {post_data['content'][:100]}...")
            self._create_post_log(post_data['filename'], 'dry_run_completed')
            return True

        try:
            # Get user ID from OpenID Connect
            user_id = self._get_person_urn()
            if not user_id:
                logger.error("Could not get user ID")
                self._create_post_log(post_data['filename'], 'failed', 'Could not get user ID')
                return False

            # Prepare post content
            post_content = post_data['content']
            if post_data['hashtags']:
                hashtag_text = ' ' + ' '.join(post_data['hashtags'])
                post_content += hashtag_text

            # Create post payload
            data = {
                "author": f"urn:li:person:{user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": post_content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            # Make API request
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'LinkedIn-Version': '202402',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            response = requests.post(
                'https://api.linkedin.com/v2/ugcPosts',
                headers=headers,
                json=data
            )
            
            # Handle 422 duplicate post error
            if response.status_code == 422:
                logger.warning(f"Duplicate post detected: {post_data['filename']}")
                self._create_post_log(post_data['filename'], 'duplicate', 'Post already exists')
                # Move file to Done folder even for duplicates
                self._move_file_to_done(post_data['filename'])
                file_moved = True
                return True
            
            response.raise_for_status()

            # Get post ID from response
            post_id = response.headers.get('X-RestLi-Id', f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

            # Log success
            post_record = {
                'id': post_id,
                'filename': post_data['filename'],
                'posted_at': datetime.now().isoformat(),
                'content_preview': post_data['content'][:200]
            }
            self._save_posted_post(post_record['id'], post_record)
            self._create_post_log(post_data['filename'], 'posted')

            logger.info(f"Successfully posted: {post_data['filename']}")

            # Increment posts published count
            self.posts_published += 1

            # Move file to Done folder
            self._move_file_to_done(post_data['filename'])
            file_moved = True

            # Update dashboard with new post count
            self._update_dashboard()

            # Print complete status
            print("\n" + "="*50)
            print("LINKEDIN POST STATUS")
            print("="*50)
            print(f"Posts published: {self.posts_published}")
            print(f"File moved to Done: {post_data['filename']}")
            print("Dashboard updated: Yes")
            print("="*50 + "\n")

            return True

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            self._create_post_log(post_data['filename'], 'failed', error_msg)
            return False
        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {e}")
            self._create_post_log(post_data['filename'], 'failed', str(e))
            return False

    def _move_file_to_done(self, filename: str):
        """Move post file from Queue to Done folder."""
        try:
            filepath = LINKEDIN_QUEUE / filename
            posted_path = LINKEDIN_DONE / filename
            
            if filepath.exists():
                # Create Done folder if it doesn't exist
                LINKEDIN_DONE.mkdir(parents=True, exist_ok=True)
                filepath.rename(posted_path)
                logger.info(f"File moved to Done: {filename}")
                print(f"Post file moved to /Done folder: {filename}")
            else:
                logger.warning(f"File not found in queue: {filename}")
        except Exception as e:
            logger.error(f"Error moving file to Done: {e}")

    def check_queue(self):
        """Check the LinkedIn queue for posts to publish."""
        try:
            post_files = list(LINKEDIN_QUEUE.glob('*.md'))

            if not post_files:
                logger.debug("No posts in queue")
                return

            logger.info(f"Found {len(post_files)} post(s) in queue")

            for post_file in post_files:
                if post_file.name in self.posted_posts:
                    logger.debug(f"Already posted: {post_file.name}")
                    continue

                post_data = self._parse_post_file(post_file)

                if post_data.get('scheduled_time'):
                    try:
                        scheduled = datetime.fromisoformat(post_data['scheduled_time'])
                        if scheduled > datetime.now():
                            logger.info(f"Post scheduled for later: {post_data['scheduled_time']}")
                            continue
                    except:
                        pass

                logger.info(f"Posting: {post_file.name}")
                success = self.post_to_linkedin(post_data)

                if success:
                    logger.info(f"Successfully posted: {post_file.name}")
                else:
                    logger.error(f"Failed to post: {post_file.name}")

        except Exception as e:
            logger.error(f"Error checking queue: {e}")

    def _update_dashboard(self):
        """Update the Dashboard.md with LinkedIn status."""
        try:
            if not DASHBOARD_PATH.exists():
                return

            content = DASHBOARD_PATH.read_text(encoding='utf-8')
            queue_count = len(list(LINKEDIN_QUEUE.glob('*.md')))
            
            # Read current posts published count from dashboard
            posts_published_count = 0
            if 'Posts Published:' in content:
                for line in content.split('\n'):
                    if 'Posts Published:' in line:
                        try:
                            posts_published_count = int(line.split(':')[1].strip())
                        except:
                            posts_published_count = 0
                        break
            
            # Add the newly published posts
            posts_published_count += self.posts_published
            
            this_week = len([p for p in self.posted_posts if 'post_' in p])

            linkedin_section = f"""## LinkedIn
- Last Checked: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Posts in Queue: {queue_count}
- Scheduled Posts: {queue_count}
- Posts Published: {posts_published_count}
- Posts This Week: {this_week}
- DRY_RUN: {'Yes' if DRY_RUN else 'No'}
"""

            if '## LinkedIn' not in content:
                content += '\n' + linkedin_section.strip() + '\n'
            else:
                lines = content.split('\n')
                new_lines = []
                in_section = False
                for line in lines:
                    if line.startswith('## LinkedIn'):
                        in_section = True
                        new_lines.append(linkedin_section.strip())
                    elif in_section and line.startswith('## '):
                        in_section = False
                        new_lines.append(line)
                    elif not in_section:
                        new_lines.append(line)
                content = '\n'.join(new_lines)

            DASHBOARD_PATH.write_text(content, encoding='utf-8')
            logger.info("Dashboard updated")

        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    def run(self):
        """Main run loop."""
        logger.info(f"LinkedIn Poster started. Checking every {CHECK_INTERVAL} seconds...")
        logger.info(f"Vault: {VAULT_PATH.resolve()}")
        logger.info(f"Queue: {LINKEDIN_QUEUE.resolve()}")
        logger.info(f"DRY_RUN: {DRY_RUN}")

        while True:
            try:
                self.check_queue()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            time.sleep(CHECK_INTERVAL)


def main():
    """Entry point."""
    try:
        poster = LinkedInPoster()
        poster.run()
    except KeyboardInterrupt:
        logger.info("LinkedIn Poster stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
