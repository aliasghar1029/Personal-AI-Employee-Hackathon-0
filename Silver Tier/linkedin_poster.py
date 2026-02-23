# linkedin_poster.py
# Silver Tier: Reads post content from /Social/LinkedIn_Queue/ folder
# Automatically posts to LinkedIn about business
# Saves posting log in /Logs/
# Uses Playwright for LinkedIn automation

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
        logging.FileHandler('Logs/linkedin_poster.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './AI_Employee_Vault'))
SOCIAL_PATH = VAULT_PATH / 'Social'
LINKEDIN_QUEUE = SOCIAL_PATH / 'LinkedIn_Queue'
LINKEDIN_POSTED = SOCIAL_PATH / 'LinkedIn_Posted'
LOGS_PATH = VAULT_PATH / 'Logs'
POST_LOG = LOGS_PATH / 'linkedin_posts.json'
SESSION_PATH = Path(os.getenv('LINKEDIN_SESSION_PATH', './linkedin_session'))
CHECK_INTERVAL = int(os.getenv('LINKEDIN_CHECK_INTERVAL', '300'))  # 5 minutes
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

class LinkedInPoster:
    def __init__(self):
        self.posted_posts = set()
        self._initialize()
    
    def _initialize(self):
        """Initialize poster and load posted history."""
        LINKEDIN_QUEUE.mkdir(parents=True, exist_ok=True)
        LINKEDIN_POSTED.mkdir(parents=True, exist_ok=True)
        LOGS_PATH.mkdir(parents=True, exist_ok=True)
        SESSION_PATH.mkdir(parents=True, exist_ok=True)
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
        data = {
            'posted_ids': list(self.posted_posts),
            'posts': data.get('posts', []) + [post_data],
            'last_updated': datetime.now().isoformat()
        }
        POST_LOG.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def _parse_post_file(self, filepath: Path) -> dict:
        """Parse a markdown post file."""
        content = filepath.read_text(encoding='utf-8')
        
        # Extract frontmatter
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
        
        # Get post content (everything after frontmatter)
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
        
        # Append to daily log
        daily_log = LOGS_PATH / f'linkedin_{datetime.now().strftime("%Y%m%d")}.log'
        with open(daily_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def post_to_linkedin(self, post_data: dict) -> bool:
        """Post content to LinkedIn using Playwright."""
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would post: {post_data['filename']}")
            logger.info(f"[DRY_RUN] Content preview: {post_data['content'][:100]}...")
            self._create_post_log(post_data['filename'], 'dry_run_completed')
            return True
        
        try:
            with sync_playwright() as p:
                logger.info("Launching browser for LinkedIn...")
                
                browser = p.chromium.launch_persistent_context(
                    str(SESSION_PATH),
                    headless=True,
                    args=[
                        '--disable-gpu',
                        '--disable-dev-shm-usage',
                        '--disable-setuid-sandbox',
                        '--no-sandbox'
                    ]
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Navigate to LinkedIn
                logger.info("Navigating to LinkedIn...")
                page.goto('https://www.linkedin.com/feed/', timeout=60000)
                
                # Wait for page to load
                try:
                    page.wait_for_selector('[data-testid="update-editor"]', timeout=30000)
                    logger.info("LinkedIn feed loaded successfully")
                except PlaywrightTimeout:
                    logger.warning("LinkedIn not fully loaded or not logged in")
                    logger.info("Please log in to LinkedIn on your first run")
                    self._create_post_log(post_data['filename'], 'failed', 'Login required')
                    browser.close()
                    return False
                
                # Click on the "Start a post" box
                try:
                    start_post_btn = page.query_selector('[data-testid="update-editor"]')
                    if start_post_btn:
                        start_post_btn.click()
                        time.sleep(2)
                        
                        # Wait for post dialog
                        page.wait_for_selector('[role="dialog"]', timeout=10000)
                        time.sleep(1)
                        
                        # Find the textarea and type content
                        textarea = page.query_selector('[role="textbox"][contenteditable="true"]')
                        if textarea:
                            # Clear existing content
                            textarea.click()
                            page.keyboard.press('Control+A')
                            page.keyboard.press('Delete')
                            
                            # Type new content
                            page.keyboard.type(post_data['content'])
                            logger.info("Post content entered")
                            
                            # Add hashtags if present
                            if post_data['hashtags']:
                                for hashtag in post_data['hashtags']:
                                    page.keyboard.type(f' {hashtag}')
                            
                            time.sleep(1)
                            
                            # Click Post button
                            post_btn = page.query_selector('button:has-text("Post")')
                            if post_btn:
                                post_btn.click()
                                logger.info("Post button clicked")
                                
                                # Wait for confirmation
                                time.sleep(3)
                                
                                # Log success
                                post_record = {
                                    'id': f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                    'filename': post_data['filename'],
                                    'posted_at': datetime.now().isoformat(),
                                    'content_preview': post_data['content'][:200]
                                }
                                self._save_posted_post(post_record['id'], post_record)
                                self._create_post_log(post_data['filename'], 'posted')
                                
                                logger.info(f"Successfully posted: {post_data['filename']}")
                                
                                # Move file to posted folder
                                posted_path = LINKEDIN_POSTED / post_data['filename']
                                filepath = LINKEDIN_QUEUE / post_data['filename']
                                filepath.rename(posted_path)
                                
                                browser.close()
                                return True
                            else:
                                logger.error("Post button not found")
                                self._create_post_log(post_data['filename'], 'failed', 'Post button not found')
                        else:
                            logger.error("Textarea not found")
                            self._create_post_log(post_data['filename'], 'failed', 'Textarea not found')
                    else:
                        logger.error("Start post button not found")
                        self._create_post_log(post_data['filename'], 'failed', 'Start post button not found')
                        
                except Exception as e:
                    logger.error(f"Error during posting: {e}")
                    self._create_post_log(post_data['filename'], 'failed', str(e))
                
                browser.close()
                return False
                
        except Exception as e:
            logger.error(f"Error in post_to_linkedin: {e}")
            self._create_post_log(post_data['filename'], 'failed', str(e))
            return False
    
    def check_queue(self):
        """Check the LinkedIn queue for posts to publish."""
        try:
            # Get all markdown files in queue
            post_files = list(LINKEDIN_QUEUE.glob('*.md'))
            
            if not post_files:
                logger.debug("No posts in queue")
                return
            
            logger.info(f"Found {len(post_files)} post(s) in queue")
            
            for post_file in post_files:
                # Skip if already posted
                if post_file.name in self.posted_posts:
                    logger.debug(f"Already posted: {post_file.name}")
                    continue
                
                # Parse post file
                post_data = self._parse_post_file(post_file)
                
                # Check if scheduled for later
                if post_data.get('scheduled_time'):
                    try:
                        scheduled = datetime.fromisoformat(post_data['scheduled_time'])
                        if scheduled > datetime.now():
                            logger.info(f"Post scheduled for later: {post_data['scheduled_time']}")
                            continue
                    except:
                        pass
                
                # Post to LinkedIn
                logger.info(f"Posting: {post_file.name}")
                success = self.post_to_linkedin(post_data)
                
                if success:
                    logger.info(f"Successfully posted: {post_file.name}")
                else:
                    logger.error(f"Failed to post: {post_file.name}")
            
            # Update dashboard
            self._update_dashboard(len(post_files))
            
        except Exception as e:
            logger.error(f"Error checking queue: {e}")
    
    def _update_dashboard(self, queue_count: int):
        """Update the Dashboard.md with LinkedIn status."""
        dashboard_path = VAULT_PATH / 'Dashboard.md'
        
        try:
            if not dashboard_path.exists():
                return
            
            content = dashboard_path.read_text(encoding='utf-8')
            
            # Count posted this week
            this_week = len([p for p in self.posted_posts if 'post_' in p])
            
            # Add LinkedIn status section if not exists
            linkedin_section = f"""
## LinkedIn
- Last Checked: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Posts in Queue: {queue_count}
- Scheduled Posts: {queue_count}
- Posts This Week: {this_week}
- DRY_RUN: {'Yes' if DRY_RUN else 'No'}
"""
            
            if '## LinkedIn' not in content:
                content += '\n' + linkedin_section
            else:
                # Update existing section
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
            
            dashboard_path.write_text(content, encoding='utf-8')
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
