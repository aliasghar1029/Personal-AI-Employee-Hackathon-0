# ceo_briefing.py
# Gold Tier: Weekly CEO Briefing Generator
# Runs every Sunday at 9:00 PM automatically
# Reads Business_Goals.md
# Checks /Done/ folder for completed tasks this week
# Reads /Accounting/ for transactions
# Checks /Logs/audit/ for actions taken
# Generates briefing in /Briefings/CEO_Briefing_YYYY-MM-DD.md

import os
import time
import logging
import json
import schedule
import re
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

from dashboard_manager import get_dashboard_manager

# Import audit logger
from audit_logger import get_audit_logger

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/ceo_briefing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===========================================
# Gold Tier Vault Configuration
# ===========================================
VAULT_PATH = Path('E:/Hackathone/Gold Tier/AI_Employee_Vault')
BRIEFINGS_PATH = VAULT_PATH / 'Briefings'
DONE_PATH = VAULT_PATH / 'Done'
ACCOUNTING_PATH = VAULT_PATH / 'Accounting'
SOCIAL_PATH = VAULT_PATH / 'Social'
LOGS_PATH = VAULT_PATH / 'Logs'
BUSINESS_GOALS_PATH = VAULT_PATH / 'Business_Goals.md'
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'
PENDING_APPROVAL_ODOO_PATH = VAULT_PATH / 'Pending_Approval' / 'ODOO'
APPROVED_ODOO_PATH = VAULT_PATH / 'Approved' / 'ODOO'

# Audit log paths
AUDIT_PATH = LOGS_PATH / 'audit'
FACEBOOK_LOG = LOGS_PATH / 'facebook_posts.json'
ODOO_LOG = LOGS_PATH / 'odoo_actions.json'
EMAIL_LOG = LOGS_PATH / 'sent_emails.json'
LINKEDIN_LOG = LOGS_PATH / 'linkedin_posts.json'


class CEOBriefingGenerator:
    """Generate weekly CEO briefing reports."""

    def __init__(self):
        self.audit_logger = get_audit_logger()
        self.dashboard = get_dashboard_manager()
        self._initialize()

    def _initialize(self):
        """Initialize briefing generator."""
        for path in [BRIEFINGS_PATH, ACCOUNTING_PATH, DONE_PATH, AUDIT_PATH]:
            path.mkdir(parents=True, exist_ok=True)

    def _get_week_start(self, date: datetime) -> datetime:
        """Get the Monday of the week for a given date."""
        return date - timedelta(days=date.weekday())

    def _get_week_end(self, date: datetime) -> datetime:
        """Get the Sunday of the week for a given date."""
        return self._get_week_start(date) + timedelta(days=6)

    def _read_business_goals(self) -> Dict[str, Any]:
        """Read and parse Business_Goals.md."""
        if not BUSINESS_GOALS_PATH.exists():
            return {'revenue_target': 10000, 'objectives': [], 'metrics': {}}

        try:
            content = BUSINESS_GOALS_PATH.read_text(encoding='utf-8')
            goals = {
                'revenue_target': 10000,
                'objectives': [],
                'metrics': {},
                'raw_content': content
            }

            # Extract revenue target
            revenue_match = re.search(r'Monthly goal:?\s*\$?(\d+)', content, re.IGNORECASE)
            if revenue_match:
                goals['revenue_target'] = float(revenue_match.group(1))

            # Extract objectives
            objectives_match = re.findall(r'^\d+\.\s*(.+)$', content, re.MULTILINE)
            goals['objectives'] = objectives_match

            return goals

        except Exception as e:
            logger.error(f"Error reading business goals: {e}")
            return {'revenue_target': 10000, 'objectives': [], 'metrics': {}}

    def _count_completed_tasks(self, week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """Count and list completed tasks for the week from /Done folder."""
        completed_tasks = []

        try:
            if DONE_PATH.exists():
                for filepath in DONE_PATH.rglob('*.md'):
                    try:
                        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                        if week_start.date() <= mtime.date() <= week_end.date():
                            completed_tasks.append({
                                'name': filepath.stem,
                                'path': str(filepath.relative_to(VAULT_PATH)),
                                'completed_at': mtime.isoformat()
                            })
                    except:
                        continue

            completed_tasks.sort(key=lambda x: x['completed_at'], reverse=True)

        except Exception as e:
            logger.error(f"Error counting completed tasks: {e}")

        return completed_tasks

    def _get_gmail_activity(self, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """Get Gmail activity for the week."""
        activity = {'emails_processed': 0, 'replies_sent': 0}

        try:
            if EMAIL_LOG.exists():
                data = json.loads(EMAIL_LOG.read_text(encoding='utf-8'))
                emails = data.get('sent_emails', [])

                for email in emails:
                    sent_at = email.get('sent_at', '')
                    if sent_at:
                        email_date = datetime.fromisoformat(sent_at).date()
                        if week_start.date() <= email_date <= week_end.date():
                            activity['emails_processed'] += 1
                            if 'reply' in email.get('subject', '').lower() or 're:' in email.get('subject', '').lower():
                                activity['replies_sent'] += 1

        except Exception as e:
            logger.error(f"Error getting Gmail activity: {e}")

        return activity

    def _get_linkedin_activity(self, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """Get LinkedIn activity for the week."""
        activity = {'posts_published': 0, 'last_post': None}

        try:
            # Check LinkedIn log
            if LINKEDIN_LOG.exists():
                data = json.loads(LINKEDIN_LOG.read_text(encoding='utf-8'))
                posts = data.get('posts', [])

                for post in posts:
                    posted_at = post.get('posted_at', '')
                    if posted_at:
                        post_date = datetime.fromisoformat(posted_at).date()
                        if week_start.date() <= post_date <= week_end.date():
                            activity['posts_published'] += 1
                            activity['last_post'] = posted_at

            # Also check LinkedIn_Posted folder
            linkedin_posted = SOCIAL_PATH / 'LinkedIn_Posted'
            if linkedin_posted.exists():
                for filepath in linkedin_posted.glob('*.md'):
                    try:
                        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                        if week_start.date() <= mtime.date() <= week_end.date():
                            activity['posts_published'] += 1
                            activity['last_post'] = mtime.isoformat()
                    except:
                        continue

        except Exception as e:
            logger.error(f"Error getting LinkedIn activity: {e}")

        return activity

    def _get_odoo_activity(self, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """Get Odoo activity for the week from /Accounting/ and logs."""
        activity = {
            'invoices_created': 0,
            'total_amount': 0.0,
            'invoice_details': []
        }

        try:
            # Check ODOO log
            if ODOO_LOG.exists():
                data = json.loads(ODOO_LOG.read_text(encoding='utf-8'))
                actions = data.get('actions', [])

                for action in actions:
                    executed_at = action.get('executed_at', '')
                    if executed_at:
                        action_date = datetime.fromisoformat(executed_at).date()
                        if week_start.date() <= action_date <= week_end.date():
                            if action.get('type') == 'create_draft_invoice':
                                activity['invoices_created'] += 1

            # Check Pending_Approval/ODOO folder for draft invoices
            if PENDING_APPROVAL_ODOO_PATH.exists():
                for filepath in PENDING_APPROVAL_ODOO_PATH.glob('*.md'):
                    try:
                        content = filepath.read_text(encoding='utf-8')
                        amount_match = re.search(r'amount:\s*([\d.]+)', content)
                        partner_match = re.search(r'partner_name:\s*(.+)', content)
                        created_match = re.search(r'created:\s*(.+)', content)

                        if created_match and amount_match:
                            created_date = datetime.fromisoformat(created_match.group(1).strip()).date()
                            if week_start.date() <= created_date <= week_end.date():
                                activity['invoices_created'] += 1
                                amount = float(amount_match.group(1))
                                activity['total_amount'] += amount
                                activity['invoice_details'].append({
                                    'client': partner_match.group(1).strip() if partner_match else 'Unknown',
                                    'amount': amount
                                })
                    except:
                        continue

            # Check Approved/ODOO folder for invoices approved this week
            if APPROVED_ODOO_PATH.exists():
                for filepath in APPROVED_ODOO_PATH.glob('*.md'):
                    try:
                        content = filepath.read_text(encoding='utf-8')
                        amount_match = re.search(r'amount:\s*([\d.]+)', content)
                        partner_match = re.search(r'partner_name:\s*(.+)', content)
                        created_match = re.search(r'created:\s*(.+)', content)

                        if created_match and amount_match:
                            created_date = datetime.fromisoformat(created_match.group(1).strip()).date()
                            if week_start.date() <= created_date <= week_end.date():
                                if filepath.name not in [i.get('file', '') for i in activity['invoice_details']]:
                                    activity['invoices_created'] += 1
                                    amount = float(amount_match.group(1))
                                    activity['total_amount'] += amount
                                    activity['invoice_details'].append({
                                        'client': partner_match.group(1).strip() if partner_match else 'Unknown',
                                        'amount': amount
                                    })
                    except:
                        continue

            # Check /Accounting/ for transactions
            current_month_file = ACCOUNTING_PATH / 'Current_Month.md'
            if current_month_file.exists():
                content = current_month_file.read_text(encoding='utf-8')
                revenue_match = re.search(r'\*\*Total Revenue\*\*\s*\|\s*\$?([\d,]+\.?\d*)', content)
                if revenue_match:
                    activity['total_revenue'] = float(revenue_match.group(1).replace(',', ''))

        except Exception as e:
            logger.error(f"Error getting Odoo activity: {e}")

        return activity

    def _get_audit_summary(self, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """Get audit log summary from /Logs/audit/ for actions taken."""
        summary = {'total_actions': 0, 'by_type': {}, 'by_result': {}}

        try:
            if AUDIT_PATH.exists():
                for audit_file in AUDIT_PATH.glob('*.json'):
                    try:
                        date_str = audit_file.stem  # YYYY-MM-DD
                        file_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                        if week_start.date() <= file_date <= week_end.date():
                            data = json.loads(audit_file.read_text(encoding='utf-8'))
                            entries = data.get('entries', [])
                            summary['total_actions'] += len(entries)

                            for entry in entries:
                                action_type = entry.get('action_type', 'unknown')
                                result = entry.get('result', 'unknown')
                                summary['by_type'][action_type] = summary['by_type'].get(action_type, 0) + 1
                                summary['by_result'][result] = summary['by_result'].get(result, 0) + 1

                    except:
                        continue

        except Exception as e:
            logger.error(f"Error getting audit summary: {e}")

        return summary

    def _generate_suggestions(
        self,
        completed_tasks: List[Dict],
        gmail_activity: Dict,
        linkedin_activity: Dict,
        odoo_activity: Dict,
        business_goals: Dict
    ) -> List[str]:
        """Generate proactive suggestions based on activity."""
        suggestions = []

        # LinkedIn activity suggestion
        if linkedin_activity['posts_published'] == 0:
            suggestions.append("📱 No LinkedIn posts this week. Consider scheduling content to maintain professional presence.")
        elif linkedin_activity['posts_published'] < 3:
            suggestions.append(f"📱 Only {linkedin_activity['posts_published']} LinkedIn posts this week. Aim for 3-5 posts for better engagement.")

        # Gmail activity suggestion
        if gmail_activity['emails_processed'] == 0:
            suggestions.append("📧 No emails processed this week. Check inbox for pending messages.")

        # Revenue suggestion
        weekly_target = business_goals['revenue_target'] / 4
        if odoo_activity['total_amount'] > 0:
            if odoo_activity['total_amount'] < weekly_target * 0.5:
                suggestions.append(f"💰 Invoices (${odoo_activity['total_amount']:.2f}) below 50% of weekly target (${weekly_target:.2f}). Follow up on pending invoices.")
        else:
            suggestions.append("📄 No invoices created this week. Review pending billing opportunities.")

        # Task completion suggestion
        if len(completed_tasks) == 0:
            suggestions.append("✅ No tasks completed this week. Review pending items in Needs_Action folder.")
        elif len(completed_tasks) < 5:
            suggestions.append(f"✅ Only {len(completed_tasks)} tasks completed this week. Consider prioritizing high-impact tasks.")

        if not suggestions:
            suggestions.append("🎯 Great week! Continue maintaining momentum on business goals.")

        return suggestions

    def generate_briefing(self) -> Optional[Path]:
        """Generate the weekly CEO briefing."""
        try:
            now = datetime.now()
            week_start = self._get_week_start(now)
            week_end = self._get_week_end(now)

            logger.info(f"Generating CEO briefing for week: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")

            # Gather all data
            business_goals = self._read_business_goals()
            completed_tasks = self._count_completed_tasks(week_start, week_end)
            gmail_activity = self._get_gmail_activity(week_start, week_end)
            linkedin_activity = self._get_linkedin_activity(week_start, week_end)
            odoo_activity = self._get_odoo_activity(week_start, week_end)
            audit_summary = self._get_audit_summary(week_start, week_end)

            # Generate suggestions
            suggestions = self._generate_suggestions(
                completed_tasks,
                gmail_activity,
                linkedin_activity,
                odoo_activity,
                business_goals
            )

            # Create briefing content
            briefing_date = now.strftime('%Y-%m-%d')
            briefing_filename = f"CEO_Briefing_{briefing_date}.md"
            briefing_path = BRIEFINGS_PATH / briefing_filename

            # Build Executive Summary
            summary_lines = [
                f"Week of {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}.",
                f"Completed {len(completed_tasks)} tasks, created {odoo_activity['invoices_created']} invoices totaling ${odoo_activity['total_amount']:.2f}.",
                f"Processed {gmail_activity['emails_processed']} emails and published {linkedin_activity['posts_published']} LinkedIn posts."
            ]
            executive_summary = " ".join(summary_lines)

            # Build Completed Tasks section
            if completed_tasks:
                tasks_content = "| Task | Completed Date |\n|------|----------------|\n"
                for task in completed_tasks[:15]:
                    completed_date = datetime.fromisoformat(task['completed_at']).strftime('%Y-%m-%d')
                    tasks_content += f"| {task['name']} | {completed_date} |\n"
                if len(completed_tasks) > 15:
                    tasks_content += f"\n*...and {len(completed_tasks) - 15} more tasks*"
            else:
                tasks_content = "_No tasks completed this week._"

            # Build Proactive Suggestions section
            suggestions_content = ""
            for i, suggestion in enumerate(suggestions, 1):
                suggestions_content += f"{i}. {suggestion}\n\n"

            content = f"""---
type: ceo_briefing
period_start: {week_start.strftime('%Y-%m-%d')}
period_end: {week_end.strftime('%Y-%m-%d')}
generated: {now.isoformat()}
---

# Monday Morning CEO Briefing

**Generated:** {now.strftime('%A, %B %d, %Y at %I:%M %p')}

**Week:** {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}

---

## Executive Summary

{executive_summary}

---

## Completed Tasks This Week

**Total:** {len(completed_tasks)}

{tasks_content}

---

## Gmail Activity

| Metric | Count |
|--------|-------|
| Emails Processed | {gmail_activity['emails_processed']} |
| Replies Sent | {gmail_activity['replies_sent']} |

---

## LinkedIn Activity

| Metric | Count |
|--------|-------|
| Posts Published | {linkedin_activity['posts_published']} |
| Last Post | {linkedin_activity['last_post'] or 'None'} |

---

## Odoo Activity

| Metric | Count |
|--------|-------|
| Invoices Created | {odoo_activity['invoices_created']} |
| Total Amount | ${odoo_activity['total_amount']:.2f} |

"""

            if odoo_activity['invoice_details']:
                content += "### Invoice Details\n\n"
                content += "| Client | Amount |\n|--------|--------|\n"
                for inv in odoo_activity['invoice_details']:
                    content += f"| {inv['client']} | ${inv['amount']:.2f} |\n"
                content += "\n"

            content += f"""## Proactive Suggestions

{suggestions_content}
---

## Next Week's Focus Areas

- [ ] Review and follow up on pending invoices
- [ ] Schedule social media content for next week
- [ ] Process any pending items in Needs_Action folder
- [ ] Review and approve pending Odoo invoices

---

## Quick Links

- [Dashboard](Dashboard.md) - Current system status
- [Pending Approvals](Pending_Approval/) - Items awaiting approval
- [Business Goals](Business_Goals.md) - Q1 2026 objectives
- [Briefings Archive](Briefings/) - All briefings

---

*Generated by Gold Tier AI Employee - CEO Briefing System*
"""

            # Write briefing file
            briefing_path.write_text(content, encoding='utf-8')

            logger.info(f"CEO briefing generated: {briefing_filename}")

            # Log the briefing generation
            self.audit_logger.log_success(
                action_type='ceo_briefing_generated',
                actor='ceo_briefing',
                details=f'Weekly CEO briefing generated for {briefing_date}',
                metadata={
                    'briefing_path': str(briefing_path),
                    'week_start': week_start.strftime('%Y-%m-%d'),
                    'week_end': week_end.strftime('%Y-%m-%d'),
                    'tasks_completed': len(completed_tasks),
                    'invoices_created': odoo_activity['invoices_created'],
                    'total_amount': odoo_activity['total_amount']
                }
            )

            # Update dashboard
            self._update_dashboard(briefing_path)

            return briefing_path

        except Exception as e:
            logger.error(f"Error generating briefing: {e}")
            self.audit_logger.log_failure(
                action_type='ceo_briefing_generated',
                actor='ceo_briefing',
                details='Failed to generate CEO briefing',
                error=str(e)
            )
            return None

    def _update_dashboard(self, briefing_path: Path):
        """Update Dashboard.md with briefing status."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            self.dashboard.state['last_briefing_date'] = today
            self.dashboard.log_activity(f"CEO Briefing Generated: {briefing_path.name}", "Success")
            self.dashboard.refresh()
            
            logger.info("Dashboard updated with briefing info")

        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    def run_scheduled(self):
        """Run the scheduled briefing generator - every Sunday at 9:00 PM."""
        logger.info("CEO Briefing Generator started")
        logger.info("Scheduled for: Every Sunday at 9:00 PM")

        # Schedule the briefing generation
        schedule.every().sunday.at("21:00").do(self.generate_briefing)

        logger.info("Scheduled jobs:")
        logger.info("  - CEO Briefing: Every Sunday at 9:00 PM")

        # Generate initial briefing if it's Sunday
        if datetime.now().weekday() == 6:  # Sunday
            logger.info("Today is Sunday, generating briefing...")
            self.generate_briefing()

        # Run schedule loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error in schedule loop: {e}")


def main():
    """Entry point - can run manually or scheduled."""
    try:
        generator = CEOBriefingGenerator()

        # Check if running manually (generate immediately)
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == '--generate-now':
            logger.info("Generating briefing immediately...")
            briefing_path = generator.generate_briefing()
            if briefing_path:
                print("\nCEO Briefing generated!")
                print(f"File: {briefing_path}")
            else:
                print("\nFailed to generate CEO Briefing")
            return

        # Run scheduled mode
        generator.run_scheduled()

    except KeyboardInterrupt:
        logger.info("CEO Briefing Generator stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
