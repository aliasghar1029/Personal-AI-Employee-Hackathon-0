# scheduler.py
# Silver Tier: Auto scheduler with human-in-the-loop
# Runs on Windows using schedule library
# - Every 2 minutes: Check /Needs_Action/ and trigger Qwen
# - Every morning 8:00 AM: Generate daily briefing in Dashboard.md
# - Every Sunday 9:00 PM: Generate weekly summary
# - Auto move completed tasks to /Done/
# - Auto check /Approved/ folder and trigger email sending

import os
import time
import logging
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

import schedule

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './AI_Employee_Vault'))
NEEDS_ACTION = VAULT_PATH / 'Needs_Action'
IN_PROGRESS = VAULT_PATH / 'In_Progress'
PLANS_PATH = VAULT_PATH / 'Plans'
DONE_PATH = VAULT_PATH / 'Done'
APPROVED_PATH = VAULT_PATH / 'Approved'
REJECTED_PATH = VAULT_PATH / 'Rejected'
LOGS_PATH = VAULT_PATH / 'Logs'
BRIEFINGS_PATH = VAULT_PATH / 'Briefings'
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'
HANDBOOK_PATH = VAULT_PATH / 'Company_Handbook.md'
SCHEDULER_STATE = LOGS_PATH / 'scheduler_state.json'
CHECK_INTERVAL = int(os.getenv('SCHEDULER_CHECK_INTERVAL', '120'))  # 2 minutes

class Scheduler:
    def __init__(self):
        self._initialize()
        self._load_state()
    
    def _initialize(self):
        """Initialize scheduler paths."""
        for path in [NEEDS_ACTION, IN_PROGRESS, PLANS_PATH, DONE_PATH, 
                     APPROVED_PATH, REJECTED_PATH, LOGS_PATH, BRIEFINGS_PATH]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _load_state(self):
        """Load scheduler state."""
        if SCHEDULER_STATE.exists():
            try:
                self.state = json.loads(SCHEDULER_STATE.read_text(encoding='utf-8'))
            except:
                self.state = {}
        else:
            self.state = {}
    
    def _save_state(self):
        """Save scheduler state."""
        SCHEDULER_STATE.write_text(json.dumps(self.state, indent=2), encoding='utf-8')
    
    def check_needs_action(self):
        """Check /Needs_Action/ folder and trigger Qwen to create plans."""
        try:
            pending_files = list(NEEDS_ACTION.glob('*.md'))
            
            if not pending_files:
                logger.debug("No pending actions")
                return
            
            logger.info(f"Found {len(pending_files)} pending action(s)")
            
            # Move files to In_Progress
            for filepath in pending_files:
                in_progress_path = IN_PROGRESS / filepath.name
                if not in_progress_path.exists():
                    filepath.rename(in_progress_path)
                    logger.info(f"Moved to In_Progress: {filepath.name}")
            
            # Trigger Qwen Code to process files
            self._trigger_qwen_processing()
            
            # Update dashboard
            self._update_dashboard()
            
        except Exception as e:
            logger.error(f"Error checking needs action: {e}")
    
    def _trigger_qwen_processing(self):
        """Trigger Qwen Code to process pending files."""
        try:
            prompt = """You are a Personal AI Employee (Silver Tier).

Read all files in the /In_Progress folder of the AI_Employee_Vault.

For each file:
1. Create a PLAN_<taskname>_<date>.md file in /Plans/ with step-by-step checkboxes
2. The Plan must include:
   - Clear objective
   - Step-by-step checklist with [ ] boxes
   - Estimated completion time
   - Any dependencies or blockers
3. If any action requires sending emails or payments, create an approval file in /Pending_Approval
4. Update Dashboard.md with the current status
5. Follow all rules in Company_Handbook.md

After creating plans, move the original files back to /Needs_Action/ for processing.

Start processing now."""
            
            # Change to vault directory
            original_dir = os.getcwd()
            os.chdir(VAULT_PATH)
            
            # Run Qwen Code with the prompt
            logger.info("Triggering Qwen Code for processing...")
            result = subprocess.run(
                ['qwen', '-p', prompt],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("Qwen Code processing completed")
            else:
                logger.warning(f"Qwen Code returned: {result.returncode}")
                logger.debug(f"Stderr: {result.stderr}")
            
            os.chdir(original_dir)
            
        except subprocess.TimeoutExpired:
            logger.error("Qwen Code processing timed out")
        except FileNotFoundError:
            logger.error("Qwen Code not found. Please ensure it's installed and in PATH")
        except Exception as e:
            logger.error(f"Error triggering Qwen: {e}")
    
    def check_approved_folder(self):
        """Check /Approved/ folder and trigger email sending."""
        try:
            approved_files = list(APPROVED_PATH.glob('*.md'))
            
            if not approved_files:
                logger.debug("No approved files")
                return
            
            logger.info(f"Found {len(approved_files)} approved file(s)")
            
            # The email_mcp_server.py handles actual sending
            # This just logs that files are ready
            for filepath in approved_files:
                logger.info(f"Approved file ready for processing: {filepath.name}")
            
            # Update dashboard
            self._update_dashboard()
            
        except Exception as e:
            logger.error(f"Error checking approved folder: {e}")
    
    def check_rejected_folder(self):
        """Check /Rejected/ folder and log rejections."""
        try:
            rejected_files = list(REJECTED_PATH.glob('*.md'))
            
            if not rejected_files:
                return
            
            logger.info(f"Found {len(rejected_files)} rejected file(s)")
            
            for filepath in rejected_files:
                logger.warning(f"Rejected file: {filepath.name}")
            
            # Update dashboard with alerts
            self._update_dashboard(rejected_count=len(rejected_files))
            
        except Exception as e:
            logger.error(f"Error checking rejected folder: {e}")
    
    def generate_daily_briefing(self):
        """Generate daily briefing at 8:00 AM."""
        try:
            logger.info("Generating daily briefing...")
            
            # Count tasks
            pending_count = len(list(NEEDS_ACTION.glob('*.md')))
            in_progress_count = len(list(IN_PROGRESS.glob('*.md')))
            plans_count = len(list(PLANS_PATH.glob('*.md')))
            done_today = self._count_done_today()
            
            # Count emails sent today
            emails_sent_today = self._count_emails_sent_today()
            
            # Create briefing file
            today = datetime.now()
            briefing_filename = f"Daily_Briefing_{today.strftime('%Y-%m-%d')}.md"
            briefing_path = BRIEFINGS_PATH / briefing_filename
            
            briefing_content = f"""---
type: daily_briefing
date: {today.strftime('%Y-%m-%d')}
generated: {datetime.now().isoformat()}
---

# Daily Briefing - {today.strftime('%A, %B %d, %Y')}

## Executive Summary

Good morning! Here's your business overview for today.

## Task Overview

| Status | Count |
|--------|-------|
| Pending Actions | {pending_count} |
| In Progress | {in_progress_count} |
| Plans Created | {plans_count} |
| Completed Today | {done_today} |

## Emails Sent Today

**Total:** {emails_sent_today}

## Priorities for Today

"""
            # Add priorities based on pending files
            pending_files = list(NEEDS_ACTION.glob('*.md'))
            if pending_files:
                briefing_content += "### Pending Items Requiring Attention\n\n"
                for f in pending_files[:5]:  # Top 5
                    briefing_content += f"- [ ] {f.stem}\n"
            else:
                briefing_content += "_No pending items requiring immediate attention._\n"
            
            briefing_content += f"""

## Recent Activity

"""
            # Add recent done items
            done_files = sorted(DONE_PATH.glob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
            if done_files:
                for f in done_files:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    briefing_content += f"- [x] {f.stem} - Completed {mtime.strftime('%Y-%m-%d %H:%M')}\n"
            else:
                briefing_content += "_No recent completions._\n"
            
            briefing_content += """

## Notes

_Add any additional notes or context here_

---
*Generated by Silver Tier Scheduler*
"""
            
            briefing_path.write_text(briefing_content, encoding='utf-8')
            logger.info(f"Daily briefing created: {briefing_filename}")
            
            # Update dashboard
            self._update_dashboard(briefing_generated=True)
            
        except Exception as e:
            logger.error(f"Error generating daily briefing: {e}")
    
    def generate_weekly_summary(self):
        """Generate weekly summary every Sunday at 9:00 PM."""
        try:
            logger.info("Generating weekly summary...")
            
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            
            # Count tasks completed this week
            done_this_week = 0
            for f in DONE_PATH.glob('*.md'):
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime >= week_start:
                    done_this_week += 1
            
            # Count emails sent this week
            emails_this_week = self._count_emails_this_week()
            
            # Create summary file
            summary_filename = f"Weekly_Summary_{week_start.strftime('%Y-%m-%d')}_to_{today.strftime('%Y-%m-%d')}.md"
            summary_path = BRIEFINGS_PATH / summary_filename
            
            summary_content = f"""---
type: weekly_summary
week_start: {week_start.strftime('%Y-%m-%d')}
week_end: {today.strftime('%Y-%m-%d')}
generated: {datetime.now().isoformat()}
---

# Weekly Summary

## Period: {week_start.strftime('%B %d')} - {today.strftime('%B %d, %Y')}

## Overview

This week's performance summary.

## Key Metrics

| Metric | Count |
|--------|-------|
| Tasks Completed | {done_this_week} |
| Emails Sent | {emails_this_week} |
| Plans Created | {len(list(PLANS_PATH.glob('*.md')))} |

## Completed Tasks This Week

"""
            # List completed tasks
            done_files = sorted(DONE_PATH.glob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True)
            if done_files:
                for f in done_files[:20]:  # Top 20
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime >= week_start:
                        summary_content += f"- [x] {f.stem}\n"
            else:
                summary_content += "_No tasks completed this week._\n"
            
            summary_content += f"""

## Next Week's Focus

_Add your focus and priorities for next week_

---
*Generated by Silver Tier Scheduler*
"""
            
            summary_path.write_text(summary_content, encoding='utf-8')
            logger.info(f"Weekly summary created: {summary_filename}")
            
            # Update dashboard
            self._update_dashboard(weekly_summary_generated=True)
            
        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}")
    
    def auto_archive_completed(self):
        """Auto-move completed tasks to /Done/ folder."""
        try:
            # Check In_Progress for files with completed plans
            in_progress_files = list(IN_PROGRESS.glob('*.md'))
            
            for filepath in in_progress_files:
                # Check if corresponding plan exists and is complete
                plan_name = f"{filepath.stem}.plan.md"
                plan_path = PLANS_PATH / plan_name
                
                if plan_path.exists():
                    plan_content = plan_path.read_text(encoding='utf-8')
                    
                    # Check if all checkboxes are marked
                    unchecked = plan_content.count('[ ]')
                    checked = plan_content.count('[x]')
                    
                    if unchecked == 0 and checked > 0:
                        # All tasks complete - move to Done
                        done_path = DONE_PATH / filepath.name
                        filepath.rename(done_path)
                        
                        # Also move the plan
                        plan_done_path = DONE_PATH / plan_name
                        plan_path.rename(plan_done_path)
                        
                        logger.info(f"Auto-archived: {filepath.name}")
            
            # Update dashboard
            self._update_dashboard()
            
        except Exception as e:
            logger.error(f"Error auto-archiving: {e}")
    
    def _count_done_today(self) -> int:
        """Count files moved to Done today."""
        today = datetime.now().date()
        count = 0
        for f in DONE_PATH.glob('*.md'):
            mtime = datetime.fromtimestamp(f.stat().st_mtime).date()
            if mtime == today:
                count += 1
        return count
    
    def _count_emails_sent_today(self) -> int:
        """Count emails sent today."""
        sent_log = LOGS_PATH / 'sent_emails.json'
        if not sent_log.exists():
            return 0
        
        try:
            data = json.loads(sent_log.read_text(encoding='utf-8'))
            today = datetime.now().strftime('%Y-%m-%d')
            return len([e for e in data.get('sent_emails', []) if today in e.get('sent_at', '')])
        except:
            return 0
    
    def _count_emails_this_week(self) -> int:
        """Count emails sent this week."""
        sent_log = LOGS_PATH / 'sent_emails.json'
        if not sent_log.exists():
            return 0
        
        try:
            data = json.loads(sent_log.read_text(encoding='utf-8'))
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            
            count = 0
            for email in data.get('sent_emails', []):
                sent_at = email.get('sent_at', '')
                if sent_at:
                    email_date = datetime.fromisoformat(sent_at).date()
                    if email_date >= week_start.date():
                        count += 1
            return count
        except:
            return 0
    
    def _update_dashboard(self, rejected_count: int = 0, 
                          briefing_generated: bool = False,
                          weekly_summary_generated: bool = False):
        """Update the Dashboard.md with current status."""
        try:
            if not DASHBOARD_PATH.exists():
                return
            
            content = DASHBOARD_PATH.read_text(encoding='utf-8')
            
            # Count various items
            pending_count = len(list(NEEDS_ACTION.glob('*.md'))) + len(list(IN_PROGRESS.glob('*.md')))
            plans_count = len(list(PLANS_PATH.glob('*.md')))
            pending_approvals = len(list(APPROVED_PATH.glob('*.md')))
            done_today = self._count_done_today()
            emails_today = self._count_emails_sent_today()
            
            # Count LinkedIn posts this week
            linkedin_posts = self._count_linkedin_posts_this_week()
            
            # Build status section
            status_section = f"""# AI Employee Dashboard
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Status
- Pending Actions: {pending_count}
- Plans in Progress: {plans_count}
- Pending Approvals: {pending_approvals}
- Completed Today: {done_today}
- Emails Sent Today: {emails_today}
- LinkedIn Posts This Week: {linkedin_posts}

## Recent Activity
"""
            # Add recent activity
            recent_activity = self._get_recent_activity()
            if recent_activity:
                status_section += recent_activity
            else:
                status_section += "_No activity yet_\n"
            
            status_section += "\n## Alerts\n"
            if rejected_count > 0:
                status_section += f"- ⚠️ {rejected_count} item(s) rejected - check /Rejected/ folder\n"
            elif briefing_generated:
                status_section += "- ✅ Daily briefing generated\n"
            elif weekly_summary_generated:
                status_section += "- ✅ Weekly summary generated\n"
            else:
                status_section += "_None_\n"
            
            # Preserve other sections (Gmail, WhatsApp, LinkedIn, Email status)
            # by extracting them from existing content
            for section in ['## Gmail Status', '## WhatsApp Status', '## LinkedIn', '## Email Status']:
                if section in content:
                    start = content.find(section)
                    # Find next section
                    rest = content[start:]
                    lines = rest.split('\n')
                    section_lines = [lines[0]]
                    for line in lines[1:]:
                        if line.startswith('## ') and line != section:
                            break
                        section_lines.append(line)
                    status_section += '\n' + '\n'.join(section_lines)
            
            DASHBOARD_PATH.write_text(status_section, encoding='utf-8')
            logger.info("Dashboard updated")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def _get_recent_activity(self) -> str:
        """Get recent activity for dashboard."""
        activity = []
        
        # Recent done items
        done_files = sorted(DONE_PATH.glob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
        for f in done_files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            activity.append(f"- **{mtime}:** {f.stem} → Completed")
        
        # Recent plans
        plan_files = sorted(PLANS_PATH.glob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True)[:2]
        for f in plan_files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            activity.append(f"- **{mtime}:** {f.stem} → Plan created")
        
        if activity:
            return '\n'.join(activity)
        return ""
    
    def _count_linkedin_posts_this_week(self) -> int:
        """Count LinkedIn posts this week."""
        linkedin_log = LOGS_PATH / 'linkedin_posts.json'
        if not linkedin_log.exists():
            return 0
        
        try:
            data = json.loads(linkedin_log.read_text(encoding='utf-8'))
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            
            count = 0
            for post in data.get('posts', []):
                posted_at = post.get('posted_at', '')
                if posted_at:
                    post_date = datetime.fromisoformat(posted_at).date()
                    if post_date >= week_start.date():
                        count += 1
            return count
        except:
            return 0
    
    def run_scheduled_jobs(self):
        """Run the schedule loop."""
        logger.info("Scheduler started")
        
        # Schedule jobs
        schedule.every(2).minutes.do(self.check_needs_action)
        schedule.every(2).minutes.do(self.check_approved_folder)
        schedule.every(2).minutes.do(self.check_rejected_folder)
        schedule.every(2).minutes.do(self.auto_archive_completed)
        schedule.every().day.at("08:00").do(self.generate_daily_briefing)
        schedule.every().sunday.at("21:00").do(self.generate_weekly_summary)
        
        logger.info("Scheduled jobs:")
        logger.info("  - Check folders: Every 2 minutes")
        logger.info("  - Daily briefing: 8:00 AM")
        logger.info("  - Weekly summary: Sunday 9:00 PM")
        
        # Initial run
        self.check_needs_action()
        self.check_approved_folder()
        self.check_rejected_folder()
        self._update_dashboard()
        
        # Run schedule loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in schedule loop: {e}")


def main():
    """Entry point."""
    try:
        scheduler = Scheduler()
        scheduler.run_scheduled_jobs()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
