# facebook_playwright.py
# Gold Tier: Facebook Playwright Browser Automation
# Simple manual approach - no automatic URL waiting

import os
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Dict, Any

from playwright.sync_api import sync_playwright

# Import audit logger
from audit_logger import get_audit_logger

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/facebook_playwright.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VAULT_PATH = Path(r"E:\Hackathone\Gold Tier\AI_Employee_Vault")
SOCIAL_PATH = VAULT_PATH / 'Social'
FACEBOOK_QUEUE = SOCIAL_PATH / 'Facebook_Queue'
FACEBOOK_DONE = SOCIAL_PATH / 'Facebook_Posted'
LOGS_PATH = VAULT_PATH / 'Logs'
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'

# Facebook Credentials
FACEBOOK_EMAIL = os.getenv('FACEBOOK_EMAIL', '')
FACEBOOK_PASSWORD = os.getenv('FACEBOOK_PASSWORD', '')


class FacebookPlaywrightPoster:
    """Post to Facebook using Playwright browser automation."""

    def __init__(self):
        self.posts_published = 0
        self.audit_logger = get_audit_logger()
        self.browser = None
        self.page = None

    def _launch_browser(self):
        """Launch browser with headless=False, slow_mo=500."""
        try:
            playwright = sync_playwright().start()

            self.browser = playwright.chromium.launch(
                headless=False,
                slow_mo=500
            )

            self.page = self.browser.new_page()
            self.page.set_viewport_size({'width': 1280, 'height': 720})

            logger.info("Browser launched successfully")
            return True

        except Exception as e:
            logger.error(f"Error launching browser: {e}")
            self.audit_logger.log_failure(
                action_type='facebook_browser',
                actor='facebook_playwright',
                details='Failed to launch browser',
                error=str(e)
            )
            return False

    def login_to_facebook(self) -> bool:
        """Login to Facebook using credentials from .env"""
        try:
            # Navigate to Facebook
            logger.info("Navigating to https://www.facebook.com/")
            self.page.goto('https://www.facebook.com/')

            # Fill email
            logger.info("Filling email...")
            self.page.fill('input[name="email"]', FACEBOOK_EMAIL)

            # Fill password
            logger.info("Filling password...")
            self.page.fill('input[name="pass"]', FACEBOOK_PASSWORD)

            # Click login button
            logger.info("Clicking login button...")
            self.page.click('button[name="login"]')

            # Wait 3 seconds
            time.sleep(3)

            # Print manual action required message
            print("\n" + "="*50)
            print("MANUAL ACTION REQUIRED")
            print("="*50)
            print("Please complete any verification in browser")
            print("(CAPTCHA, Two-Factor, etc.)")
            print("When you see Facebook homepage, press Enter here")
            print("="*50)

            # Wait for user input
            input("Press Enter when Facebook homepage is loaded: ")

            # Take screenshot
            screenshot_path = VAULT_PATH / 'facebook_ready.png'
            self.page.screenshot(path=str(screenshot_path))
            logger.info(f"Screenshot saved to: {screenshot_path}")

            return True

        except Exception as e:
            logger.error(f"Error during login: {e}")
            print(f"ERROR: {e}")
            return False

    def post_to_facebook(self, post_data: Dict[str, Any]) -> bool:
        """Post content to Facebook."""
        try:
            message = post_data['message']

            # Click on "What's on your mind" area
            logger.info("Looking for post creation area...")

            textarea_selectors = [
                '[aria-label="What\'s on your mind?"]',
                '[data-testid="status-attachment-mentions-input"]',
                'div[role="textbox"]',
                '[aria-label*="mind"]',
                '[aria-label*="post"]',
                '[placeholder*="mind"]',
                'div[contenteditable="true"]'
            ]

            text_entered = False
            for selector in textarea_selectors:
                try:
                    textarea = self.page.locator(selector).first
                    if textarea.is_visible(timeout=5000):
                        logger.info(f"Found textarea using selector: {selector}")
                        textarea.click()
                        time.sleep(2)
                        textarea.fill(message)
                        time.sleep(1)
                        text_entered = True
                        logger.info("Post content entered successfully")
                        break
                except Exception as e:
                    logger.debug(f"Selector failed: {selector} - {e}")
                    continue

            if not text_entered:
                logger.error("Could not find textarea to enter post content")
                print("ERROR: Could not find textarea to enter post content")
                return False

            # Click Post button
            logger.info("Looking for Post button...")

            post_button_selectors = [
                '[aria-label="Post"]',
                'div[aria-label="Post"]',
                'button[type="submit"]',
                'button:has-text("Post")',
                'div[role="button"]:has-text("Post")'
            ]

            posted = False
            for selector in post_button_selectors:
                try:
                    post_button = self.page.locator(selector).first
                    if post_button.is_visible(timeout=5000) and post_button.is_enabled():
                        logger.info(f"Found Post button using selector: {selector}")
                        post_button.click()
                        time.sleep(3)
                        posted = True
                        logger.info("Post button clicked")
                        break
                except Exception as e:
                    logger.debug(f"Post button selector failed: {selector} - {e}")
                    continue

            if not posted:
                logger.warning("Could not find Post button")
                print("WARNING: Could not find Post button")
                return False

            # Generate post ID
            post_id = f"fb_pw_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Log success
            self._save_posted_post(post_id, post_data)

            self.audit_logger.log_success(
                action_type='facebook_post',
                actor='facebook_playwright',
                details=f"Posted to Facebook via Playwright: {post_data['filename']}",
                metadata={
                    'post_id': post_id,
                    'filename': post_data['filename'],
                    'method': 'playwright'
                }
            )

            logger.info(f"Successfully posted to Facebook: {post_data['filename']}")
            self.posts_published += 1

            # Move file to Done folder
            self._move_file_to_done(post_data['filename'])

            # Update dashboard
            self._update_dashboard()

            print("\n" + "="*50)
            print("FACEBOOK POST STATUS (Playwright)")
            print("="*50)
            print(f"Posts published: {self.posts_published}")
            print(f"Method: Playwright Browser Automation")
            print(f"Post ID: {post_id}")
            print(f"File moved to Done: {post_data['filename']}")
            print("="*50)

            return True

        except Exception as e:
            error_msg = f"Error posting to Facebook: {str(e)}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            self.audit_logger.log_failure(
                action_type='facebook_post',
                actor='facebook_playwright',
                details='Error during Facebook posting',
                error=error_msg,
                metadata={'filename': post_data['filename']}
            )
            return False

    def _save_posted_post(self, post_id: str, post_data: dict):
        """Save a posted post record."""
        POST_LOG = LOGS_PATH / 'facebook_posts.json'

        existing_data = {'posts': [], 'posted_ids': []}
        if POST_LOG.exists():
            try:
                existing_data = json.loads(POST_LOG.read_text(encoding='utf-8'))
            except:
                pass

        post_record = {
            'id': post_id,
            'filename': post_data['filename'],
            'posted_at': datetime.now().isoformat(),
            'content_preview': post_data['message'][:200],
            'method': 'playwright'
        }

        data = {
            'posted_ids': existing_data.get('posted_ids', []) + [post_id],
            'posts': existing_data.get('posts', []) + [post_record],
            'last_updated': datetime.now().isoformat()
        }
        POST_LOG.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def _move_file_to_done(self, filename: str):
        """Move post file from Queue to Done folder."""
        try:
            filepath = FACEBOOK_QUEUE / filename
            posted_path = FACEBOOK_DONE / filename

            if filepath.exists():
                FACEBOOK_DONE.mkdir(parents=True, exist_ok=True)
                filepath.rename(posted_path)
                logger.info(f"File moved to Done: {filename}")
            else:
                logger.warning(f"File not found in queue: {filename}")
        except Exception as e:
            logger.error(f"Error moving file to Done: {e}")

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

        if post_data['hashtags']:
            hashtag_text = ' ' + ' '.join(post_data['hashtags'])
            post_data['message'] += hashtag_text

        return post_data

    def _update_dashboard(self):
        """Update the Dashboard.md with Facebook status."""
        try:
            if not DASHBOARD_PATH.exists():
                return

            content = DASHBOARD_PATH.read_text(encoding='utf-8')
            queue_count = len(list(FACEBOOK_QUEUE.glob('*.md')))

            facebook_section = f"""## Facebook Status
- Last Checked: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Last Post: {self._get_last_post_time()}
- Posts in Queue: {queue_count}
- Method Used: Playwright
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
        POST_LOG = LOGS_PATH / 'facebook_posts.json'
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

    def check_queue(self):
        """Check the Facebook queue for posts to publish."""
        try:
            post_files = list(FACEBOOK_QUEUE.glob('*.md'))

            if not post_files:
                logger.debug("No posts in queue")
                return

            logger.info(f"Found {len(post_files)} post(s) in queue")

            for post_file in post_files:
                post_data = self._parse_post_file(post_file)
                logger.info(f"Posting via Playwright: {post_file.name}")
                success = self.post_to_facebook(post_data)

                if success:
                    logger.info(f"Successfully posted via Playwright: {post_file.name}")
                else:
                    logger.error(f"Failed to post via Playwright: {post_file.name}")
                    raise Exception(f"Playwright posting failed for {post_file.name}")

        except Exception as e:
            logger.error(f"Error checking queue: {e}")
            raise

    def close(self):
        """Close browser - intentionally does nothing to keep browser open."""
        pass

    def run(self):
        """Main run - keeps browser open until posting complete."""
        logger.info("Facebook Playwright Poster started")
        logger.info(f"Vault: {VAULT_PATH.resolve()}")
        logger.info(f"Queue: {FACEBOOK_QUEUE.resolve()}")

        try:
            # Launch browser
            if not self._launch_browser():
                return

            # Login to Facebook
            if not self.login_to_facebook():
                return

            # Check queue and post
            self.check_queue()

            # Keep browser open after posting
            print("\n" + "="*50)
            print("Posting complete!")
            print("Browser kept open - Close manually when done")
            print("="*50)

            # Wait to keep browser open
            while True:
                time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Stopped by user")
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            # NEVER close browser automatically
            pass


def main():
    """Entry point."""
    poster = None
    try:
        poster = FacebookPlaywrightPoster()
        poster.run()
    except KeyboardInterrupt:
        logger.info("Facebook Playwright Poster stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
