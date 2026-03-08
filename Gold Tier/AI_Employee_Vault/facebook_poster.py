# facebook_poster.py
# Gold Tier: Facebook Official Graph API Integration
# Posts to Facebook Page using Graph API
# Reads credentials from .env
# Reads posts from /Social/Facebook_Queue/ folder
# Moves posted files to /Done/
# Updates Dashboard.md
# Handles token refresh automatically
# Logs every action to /Logs/audit/

import os
import time
import logging
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv, set_key
from typing import Optional, Dict, Any

# Import audit logger
from audit_logger import get_audit_logger

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/facebook_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './AI_Employee_Vault'))
SOCIAL_PATH = VAULT_PATH / 'Social'
FACEBOOK_QUEUE = SOCIAL_PATH / 'Facebook_Queue'
FACEBOOK_DONE = SOCIAL_PATH / 'Facebook_Posted'
LOGS_PATH = VAULT_PATH / 'Logs'
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'
POST_LOG = LOGS_PATH / 'facebook_posts.json'

# Facebook Graph API Configuration
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID', '')
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')
FACEBOOK_API_VERSION = 'v18.0'
FACEBOOK_GRAPH_URL = f'https://graph.facebook.com/{FACEBOOK_API_VERSION}'

# Poster Settings
CHECK_INTERVAL = int(os.getenv('FACEBOOK_CHECK_INTERVAL', '60'))
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'


class FacebookAPIPoster:
    """Post to Facebook using Official Graph API."""
    
    def __init__(self):
        self.posts_published = 0
        self.posted_posts = set()
        self.audit_logger = get_audit_logger()
        self._initialize()
    
    def _initialize(self):
        """Initialize poster and load posted history."""
        FACEBOOK_QUEUE.mkdir(parents=True, exist_ok=True)
        FACEBOOK_DONE.mkdir(parents=True, exist_ok=True)
        LOGS_PATH.mkdir(parents=True, exist_ok=True)
        self._load_posted_history()
    
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
    
    def _parse_post_file(self, filepath: Path) -> Dict[str, Any]:
        """Parse a markdown post file."""
        content = filepath.read_text(encoding='utf-8')
        
        post_data = {
            'message': '',
            'hashtags': [],
            'link': None,
            'picture': None,
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
                    elif key == 'link':
                        post_data['link'] = value
                    elif key == 'picture':
                        post_data['picture'] = value
        
        post_data['message'] = '\n'.join(lines[frontmatter_end:]).strip()
        
        # Add hashtags to message
        if post_data['hashtags']:
            hashtag_text = ' ' + ' '.join(post_data['hashtags'])
            post_data['message'] += hashtag_text
        
        return post_data
    
    def _refresh_access_token(self) -> Optional[str]:
        """Refresh the page access token if expired."""
        if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
            logger.warning("App credentials not configured for token refresh")
            return None
        
        try:
            # Exchange short-lived token for long-lived token
            url = f"{FACEBOOK_GRAPH_URL}/oauth/access_token"
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': FACEBOOK_APP_ID,
                'client_secret': FACEBOOK_APP_SECRET,
                'fb_exchange_token': FACEBOOK_PAGE_ACCESS_TOKEN
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            new_token = token_data.get('access_token')
            
            if new_token:
                # Save new token to .env
                env_path = Path('.env')
                if not env_path.exists():
                    env_path = Path('AI_Employee_Vault/.env')
                
                if env_path.exists():
                    set_key(str(env_path), 'FACEBOOK_PAGE_ACCESS_TOKEN', new_token)
                    logger.info("Access token refreshed and saved")
                    return new_token
            
            logger.warning("Failed to refresh access token")
            return None
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    def _validate_token(self) -> bool:
        """Validate the current access token."""
        try:
            url = f"{FACEBOOK_GRAPH_URL}/me"
            params = {
                'access_token': FACEBOOK_PAGE_ACCESS_TOKEN
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 401:
                logger.warning("Access token expired, attempting refresh")
                new_token = self._refresh_access_token()
                if new_token:
                    return True
                return False
            
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False
    
    def post_to_facebook(self, post_data: Dict[str, Any]) -> bool:
        """Post content to Facebook Page using Graph API."""
        if not FACEBOOK_PAGE_ACCESS_TOKEN:
            logger.error("Facebook Page Access Token not configured")
            self.audit_logger.log_failure(
                action_type='facebook_post',
                actor='facebook_api',
                details='Facebook Page Access Token not configured',
                error='Missing FACEBOOK_PAGE_ACCESS_TOKEN'
            )
            return False
        
        # Validate token
        if not self._validate_token():
            logger.error("Facebook access token invalid and could not be refreshed")
            self.audit_logger.log_failure(
                action_type='facebook_post',
                actor='facebook_api',
                details='Facebook access token invalid',
                error='Token validation failed'
            )
            return False
        
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would post to Facebook: {post_data['filename']}")
            logger.info(f"[DRY_RUN] Message preview: {post_data['message'][:100]}...")
            
            self.audit_logger.log_dry_run(
                action_type='facebook_post',
                actor='facebook_api',
                details=f"Would post to Facebook Page (DRY_RUN mode)",
                metadata={'filename': post_data['filename']}
            )
            
            self._move_file_to_done(post_data['filename'])
            self._update_dashboard()
            return True
        
        try:
            # Prepare post data
            post_url = f"{FACEBOOK_GRAPH_URL}/{FACEBOOK_PAGE_ID}/feed"
            
            payload = {
                'message': post_data['message'],
                'access_token': FACEBOOK_PAGE_ACCESS_TOKEN
            }
            
            if post_data.get('link'):
                payload['link'] = post_data['link']
            
            if post_data.get('picture'):
                payload['picture'] = post_data['picture']
            
            # Make API request
            response = requests.post(post_url, data=payload, timeout=60)
            
            if response.status_code != 200:
                error_data = response.json()
                error_msg = f"Facebook API Error: {error_data.get('error', {}).get('message', 'Unknown error')}"
                logger.error(error_msg)
                
                self.audit_logger.log_failure(
                    action_type='facebook_post',
                    actor='facebook_api',
                    details=f"Failed to post to Facebook: {post_data['filename']}",
                    error=error_msg,
                    metadata={'filename': post_data['filename']}
                )
                return False
            
            # Get post ID from response
            result = response.json()
            post_id = result.get('id', f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Log success
            post_record = {
                'id': post_id,
                'filename': post_data['filename'],
                'posted_at': datetime.now().isoformat(),
                'content_preview': post_data['message'][:200],
                'method': 'api'
            }
            self._save_posted_post(post_id, post_record)
            
            self.audit_logger.log_success(
                action_type='facebook_post',
                actor='facebook_api',
                details=f"Posted to Facebook Page via API: {post_data['filename']}",
                metadata={
                    'post_id': post_id,
                    'filename': post_data['filename'],
                    'method': 'api'
                }
            )
            
            logger.info(f"Successfully posted to Facebook: {post_data['filename']}")
            
            # Increment posts published count
            self.posts_published += 1
            
            # Move file to Done folder
            self._move_file_to_done(post_data['filename'])
            
            # Update dashboard
            self._update_dashboard()
            
            # Print complete status
            print("\n" + "="*50)
            print("FACEBOOK POST STATUS (API)")
            print("="*50)
            print(f"Posts published: {self.posts_published}")
            print(f"Method: Facebook Graph API")
            print(f"Post ID: {post_id}")
            print(f"File moved to Done: {post_data['filename']}")
            print("Dashboard updated: Yes")
            print("="*50 + "\n")
            
            return True
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            
            self.audit_logger.log_failure(
                action_type='facebook_post',
                actor='facebook_api',
                details=f"Network error posting to Facebook",
                error=error_msg,
                metadata={'filename': post_data['filename']}
            )
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            
            self.audit_logger.log_failure(
                action_type='facebook_post',
                actor='facebook_api',
                details=f"Unexpected error posting to Facebook",
                error=error_msg,
                metadata={'filename': post_data['filename']}
            )
            return False
    
    def _move_file_to_done(self, filename: str):
        """Move post file from Queue to Done folder."""
        try:
            filepath = FACEBOOK_QUEUE / filename
            posted_path = FACEBOOK_DONE / filename
            
            if filepath.exists():
                FACEBOOK_DONE.mkdir(parents=True, exist_ok=True)
                filepath.rename(posted_path)
                logger.info(f"File moved to Done: {filename}")
                print(f"Post file moved to /Done folder: {filename}")
            else:
                logger.warning(f"File not found in queue: {filename}")
        except Exception as e:
            logger.error(f"Error moving file to Done: {e}")
    
    def check_queue(self):
        """Check the Facebook queue for posts to publish."""
        try:
            post_files = list(FACEBOOK_QUEUE.glob('*.md'))
            
            if not post_files:
                logger.debug("No posts in queue")
                return
            
            logger.info(f"Found {len(post_files)} post(s) in queue")
            
            for post_file in post_files:
                if post_file.name in self.posted_posts:
                    logger.debug(f"Already posted: {post_file.name}")
                    continue
                
                post_data = self._parse_post_file(post_file)
                
                logger.info(f"Posting via API: {post_file.name}")
                success = self.post_to_facebook(post_data)
                
                if success:
                    logger.info(f"Successfully posted via API: {post_file.name}")
                else:
                    logger.error(f"Failed to post via API: {post_file.name}")
                    # Don't raise exception, let manager handle fallback
                    
        except Exception as e:
            logger.error(f"Error checking queue: {e}")
    
    def _update_dashboard(self):
        """Update the Dashboard.md with Facebook status."""
        try:
            if not DASHBOARD_PATH.exists():
                return
            
            content = DASHBOARD_PATH.read_text(encoding='utf-8')
            queue_count = len(list(FACEBOOK_QUEUE.glob('*.md')))
            
            # Count posts this week
            this_week = self._count_posts_this_week()
            
            facebook_section = f"""## Facebook Status
- Last Checked: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Last Post: {self._get_last_post_time()}
- Posts This Week: {this_week}
- Posts in Queue: {queue_count}
- Method Used: API
- Status: Active ✅
"""
            
            if '## Facebook Status' not in content:
                content += '\n' + facebook_section.strip() + '\n'
            else:
                lines = content.split('\n')
                new_lines = []
                in_section = False
                for line in lines:
                    if line.startswith('## Facebook Status'):
                        in_section = True
                        new_lines.append(facebook_section.strip())
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
    
    def _get_last_post_time(self) -> str:
        """Get the last post time."""
        if POST_LOG.exists():
            try:
                data = json.loads(POST_LOG.read_text(encoding='utf-8'))
                posts = data.get('posts', [])
                if posts:
                    last_post = posts[-1]
                    posted_at = last_post.get('posted_at', '')
                    if posted_at:
                        dt = datetime.fromisoformat(posted_at)
                        return dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        return "Not yet"
    
    def _count_posts_this_week(self) -> int:
        """Count Facebook posts this week."""
        if not POST_LOG.exists():
            return 0
        
        try:
            data = json.loads(POST_LOG.read_text(encoding='utf-8'))
            posts = data.get('posts', [])
            
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            
            count = 0
            for post in posts:
                posted_at = post.get('posted_at', '')
                if posted_at:
                    post_date = datetime.fromisoformat(posted_at).date()
                    if post_date >= week_start.date():
                        count += 1
            
            return count
        except:
            return 0
    
    def run(self):
        """Main run loop."""
        logger.info(f"Facebook API Poster started. Checking every {CHECK_INTERVAL} seconds...")
        logger.info(f"Vault: {VAULT_PATH.resolve()}")
        logger.info(f"Queue: {FACEBOOK_QUEUE.resolve()}")
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
        poster = FacebookAPIPoster()
        poster.run()
    except KeyboardInterrupt:
        logger.info("Facebook API Poster stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
