# facebook_manager.py
# Gold Tier: Smart Fallback Manager for Facebook Posting
# Tries API first, if fails uses Playwright
# Checks /Social/Facebook_Queue/ every 60 seconds
# Prints which method was used: "Posted via API" or "Posted via Playwright"
# Updates Dashboard.md with post count and last post time

import os
import time
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict, Any

# Import audit logger
from audit_logger import get_audit_logger

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/facebook_manager.log', encoding='utf-8'),
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

# Facebook API Configuration
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID', '')
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')

# Manager Settings
CHECK_INTERVAL = int(os.getenv('FACEBOOK_CHECK_INTERVAL', '60'))
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
API_FIRST = os.getenv('FACEBOOK_API_FIRST', 'true').lower() == 'true'


class FacebookManager:
    """Smart fallback manager for Facebook posting."""
    
    def __init__(self):
        self.api_poster = None
        self.playwright_poster = None
        self.audit_logger = get_audit_logger()
        self.posts_published = 0
        self._initialize()
    
    def _initialize(self):
        """Initialize managers."""
        FACEBOOK_QUEUE.mkdir(parents=True, exist_ok=True)
        FACEBOOK_DONE.mkdir(parents=True, exist_ok=True)
        LOGS_PATH.mkdir(parents=True, exist_ok=True)
        
        # Check if API is configured
        self.api_configured = bool(
            FACEBOOK_APP_ID and 
            FACEBOOK_APP_SECRET and 
            FACEBOOK_PAGE_ID and 
            FACEBOOK_PAGE_ACCESS_TOKEN
        )
        
        if self.api_configured:
            logger.info("Facebook API credentials configured")
        else:
            logger.warning("Facebook API credentials not fully configured")
            logger.info("Will use Playwright automation as primary method")
    
    def _get_api_poster(self):
        """Lazy load API poster."""
        if self.api_poster is None:
            try:
                from facebook_poster import FacebookAPIPoster
                self.api_poster = FacebookAPIPoster()
                logger.info("Facebook API Poster loaded")
            except Exception as e:
                logger.error(f"Error loading API poster: {e}")
                return None
        return self.api_poster
    
    def _get_playwright_poster(self):
        """Lazy load Playwright poster."""
        if self.playwright_poster is None:
            try:
                from facebook_playwright import FacebookPlaywrightPoster
                self.playwright_poster = FacebookPlaywrightPoster()
                logger.info("Facebook Playwright Poster loaded")
            except Exception as e:
                logger.error(f"Error loading Playwright poster: {e}")
                return None
        return self.playwright_poster
    
    def _parse_post_file(self, filepath: Path) -> Dict[str, Any]:
        """Parse a markdown post file."""
        content = filepath.read_text(encoding='utf-8')
        
        post_data = {
            'message': '',
            'hashtags': [],
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
        
        post_data['message'] = '\n'.join(lines[frontmatter_end:]).strip()
        
        # Add hashtags to message
        if post_data['hashtags']:
            hashtag_text = ' ' + ' '.join(post_data['hashtags'])
            post_data['message'] += hashtag_text
        
        return post_data
    
    def post_with_fallback(self, post_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Try to post using API first, fallback to Playwright if fails.
        
        Returns:
            Tuple of (success: bool, method_used: str)
        """
        method_used = "none"
        
        # If API is configured and we should try it first
        if self.api_configured and API_FIRST:
            logger.info("Attempting to post via API first...")
            
            try:
                api_poster = self._get_api_poster()
                if api_poster:
                    success = api_poster.post_to_facebook(post_data)
                    if success:
                        method_used = "api"
                        logger.info("✓ Posted via API")
                        print("Posted via API")
                        return True, method_used
                    else:
                        logger.warning("API post failed, falling back to Playwright...")
                else:
                    logger.warning("API poster not available")
            except Exception as e:
                logger.warning(f"API post failed with error: {e}")
                logger.info("Falling back to Playwright...")
        
        # Try Playwright
        logger.info("Attempting to post via Playwright...")
        
        try:
            playwright_poster = self._get_playwright_poster()
            if playwright_poster:
                success = playwright_poster.post_to_facebook(post_data)
                if success:
                    method_used = "playwright"
                    logger.info("✓ Posted via Playwright")
                    print("Posted via Playwright")
                    return True, method_used
                else:
                    logger.error("Playwright post failed")
            else:
                logger.error("Playwright poster not available")
        except Exception as e:
            logger.error(f"Playwright post failed with error: {e}")
        
        # Both methods failed
        logger.error(f"Failed to post {post_data['filename']} using both methods")
        
        self.audit_logger.log_failure(
            action_type='facebook_post',
            actor='facebook_manager',
            details=f"Failed to post using both API and Playwright: {post_data['filename']}",
            metadata={'filename': post_data['filename']}
        )
        
        return False, method_used
    
    def check_queue(self):
        """Check the Facebook queue for posts to publish."""
        try:
            post_files = list(FACEBOOK_QUEUE.glob('*.md'))
            
            if not post_files:
                logger.debug("No posts in queue")
                return
            
            logger.info(f"Found {len(post_files)} post(s) in queue")
            
            for post_file in post_files:
                # Check if already posted
                if self._is_posted(post_file.name):
                    logger.debug(f"Already posted: {post_file.name}")
                    continue
                
                post_data = self._parse_post_file(post_file)
                
                logger.info(f"Processing: {post_file.name}")
                print(f"\nProcessing: {post_file.name}")
                
                success, method = self.post_with_fallback(post_data)
                
                if success:
                    logger.info(f"Successfully posted via {method}: {post_file.name}")
                    self.posts_published += 1
                    self._mark_as_posted(post_file.name, method)
                    self._update_dashboard(method)
                else:
                    logger.error(f"Failed to post: {post_file.name}")
                    print(f"Failed to post: {post_file.name}")
                    
        except Exception as e:
            logger.error(f"Error checking queue: {e}")
    
    def _is_posted(self, filename: str) -> bool:
        """Check if a post has already been published."""
        if not POST_LOG.exists():
            return False
        
        try:
            data = json.loads(POST_LOG.read_text(encoding='utf-8'))
            posted_ids = data.get('posted_ids', [])
            
            # Check if filename is in posted IDs
            for post_id in posted_ids:
                if filename in post_id or post_id in filename:
                    return True
            
            return False
        except:
            return False
    
    def _mark_as_posted(self, filename: str, method: str):
        """Mark a post as published."""
        # This is handled by the individual posters
        pass
    
    def _update_dashboard(self, last_method: str = "unknown"):
        """Update the Dashboard.md with Facebook status."""
        try:
            if not DASHBOARD_PATH.exists():
                return
            
            content = DASHBOARD_PATH.read_text(encoding='utf-8')
            queue_count = len(list(FACEBOOK_QUEUE.glob('*.md')))
            
            # Count posts this week
            this_week = self._count_posts_this_week()
            last_post = self._get_last_post_time()
            
            facebook_section = f"""## Facebook Status
- Last Checked: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Last Post: {last_post}
- Posts This Week: {this_week}
- Posts in Queue: {queue_count}
- Method Used: {last_method.title()}
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
        logger.info(f"Facebook Manager started. Checking every {CHECK_INTERVAL} seconds...")
        logger.info(f"Vault: {VAULT_PATH.resolve()}")
        logger.info(f"Queue: {FACEBOOK_QUEUE.resolve()}")
        logger.info(f"DRY_RUN: {DRY_RUN}")
        logger.info(f"API Configured: {self.api_configured}")
        logger.info(f"Strategy: {'API First' if API_FIRST else 'Playwright First'}")
        
        print("\n" + "="*50)
        print("FACEBOOK MANAGER - GOLD TIER")
        print("="*50)
        print(f"API Configured: {self.api_configured}")
        print(f"DRY_RUN: {DRY_RUN}")
        print(f"Checking queue every {CHECK_INTERVAL} seconds...")
        print("="*50 + "\n")
        
        while True:
            try:
                self.check_queue()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            time.sleep(CHECK_INTERVAL)
    
    def cleanup(self):
        """Cleanup resources."""
        if self.playwright_poster:
            try:
                self.playwright_poster.close()
            except:
                pass


def main():
    """Entry point."""
    manager = None
    try:
        manager = FacebookManager()
        manager.run()
    except KeyboardInterrupt:
        logger.info("Facebook Manager stopped by user")
        print("\nFacebook Manager stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
    finally:
        if manager:
            manager.cleanup()


if __name__ == '__main__':
    main()
