#!/usr/bin/env python
"""Generate Monday Morning CEO Briefing - Immediate."""

import os
import sys
import codecs
import json
from pathlib import Path
from datetime import datetime, timedelta
import re

from dashboard_manager import get_dashboard_manager

# Set UTF-8 encoding for Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv
load_dotenv()

# Configuration
VAULT_PATH = Path('E:/Hackathone/Gold Tier/AI_Employee_Vault')
BRIEFINGS_PATH = VAULT_PATH / 'Briefings'
DONE_PATH = VAULT_PATH / 'Done'
ACCOUNTING_PATH = VAULT_PATH / 'Accounting'
SOCIAL_PATH = VAULT_PATH / 'Social'
LOGS_PATH = VAULT_PATH / 'Logs'
BUSINESS_GOALS_PATH = VAULT_PATH / 'Business_Goals.md'
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'
PENDING_APPROVAL_ODOO_PATH = VAULT_PATH / 'Pending_Approval' / 'ODOO'

# Activity logs
FACEBOOK_LOG = LOGS_PATH / 'facebook_posts.json'
ODOO_LOG = LOGS_PATH / 'odoo_actions.json'
EMAIL_LOG = LOGS_PATH / 'sent_emails.json'
LINKEDIN_LOG = LOGS_PATH / 'linkedin_posts.json'
AUDIT_PATH = LOGS_PATH / 'audit'


def get_week_range(date):
    """Get Monday and Sunday of the week."""
    monday = date - timedelta(days=date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def read_business_goals():
    """Read business goals."""
    if not BUSINESS_GOALS_PATH.exists():
        return {'revenue_target': 10000, 'objectives': []}
    
    content = BUSINESS_GOALS_PATH.read_text(encoding='utf-8')
    goals = {'revenue_target': 10000, 'objectives': [], 'raw_content': content}
    
    # Extract revenue target
    revenue_match = re.search(r'Monthly goal:?\s*\$?(\d+)', content, re.IGNORECASE)
    if revenue_match:
        goals['revenue_target'] = float(revenue_match.group(1))
    
    # Extract objectives
    objectives_match = re.findall(r'^\d+\.\s*(.+)$', content, re.MULTILINE)
    goals['objectives'] = objectives_match
    
    return goals


def get_completed_tasks(week_start, week_end):
    """Get completed tasks from Done folder."""
    tasks = []
    if DONE_PATH.exists():
        for filepath in DONE_PATH.rglob('*.md'):
            try:
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if week_start.date() <= mtime.date() <= week_end.date():
                    tasks.append({
                        'name': filepath.stem,
                        'path': str(filepath.relative_to(VAULT_PATH)),
                        'completed_at': mtime.isoformat()
                    })
            except:
                continue
    tasks.sort(key=lambda x: x['completed_at'], reverse=True)
    return tasks


def get_facebook_activity(week_start, week_end):
    """Get Facebook activity."""
    activity = {'posts_count': 0, 'last_post': None}
    
    # Check Facebook_Posted folder
    facebook_posted = SOCIAL_PATH / 'Facebook_Posted'
    if facebook_posted.exists():
        for filepath in facebook_posted.glob('*.md'):
            try:
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if week_start.date() <= mtime.date() <= week_end.date():
                    activity['posts_count'] += 1
                    activity['last_post'] = mtime.isoformat()
            except:
                continue
    
    return activity


def get_linkedin_activity(week_start, week_end):
    """Get LinkedIn activity."""
    activity = {'posts_count': 0, 'last_post': None}
    
    # Check LinkedIn_Posted folder
    linkedin_posted = SOCIAL_PATH / 'LinkedIn_Posted'
    if linkedin_posted.exists():
        for filepath in linkedin_posted.glob('*.md'):
            try:
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if week_start.date() <= mtime.date() <= week_end.date():
                    activity['posts_count'] += 1
                    activity['last_post'] = mtime.isoformat()
            except:
                continue
    
    return activity


def get_odoo_summary(week_start, week_end):
    """Get Odoo summary from ODOO log and Pending_Approval folder."""
    summary = {
        'invoices_created': 0,
        'payments_received': 0,
        'total_revenue': 0.0,
        'invoice_details': []
    }
    
    # Check ODOO log
    if ODOO_LOG.exists():
        try:
            data = json.loads(ODOO_LOG.read_text(encoding='utf-8'))
            actions = data.get('actions', [])
            for action in actions:
                executed_at = action.get('executed_at', '')
                if executed_at:
                    action_date = datetime.fromisoformat(executed_at).date()
                    if week_start.date() <= action_date <= week_end.date():
                        if action.get('type') == 'create_draft_invoice':
                            summary['invoices_created'] += 1
        except:
            pass
    
    # Check Pending_Approval/ODOO folder for draft invoices (this week)
    if PENDING_APPROVAL_ODOO_PATH.exists():
        for filepath in PENDING_APPROVAL_ODOO_PATH.glob('*.md'):
            try:
                content = filepath.read_text(encoding='utf-8')
                # Extract amount from frontmatter
                amount_match = re.search(r'amount:\s*([\d.]+)', content)
                partner_match = re.search(r'partner_name:\s*(.+)', content)
                created_match = re.search(r'created:\s*(.+)', content)
                
                # Check if created this week
                if created_match:
                    try:
                        created_date = datetime.fromisoformat(created_match.group(1).strip()).date()
                        if week_start.date() <= created_date <= week_end.date():
                            if amount_match:
                                summary['invoices_created'] += 1
                                amount = float(amount_match.group(1))
                                summary['invoice_details'].append({
                                    'file': filepath.name,
                                    'partner': partner_match.group(1).strip() if partner_match else 'Unknown',
                                    'amount': amount
                                })
                    except:
                        # If can't parse date, still count it
                        if amount_match:
                            summary['invoices_created'] += 1
                            amount = float(amount_match.group(1))
                            summary['invoice_details'].append({
                                'file': filepath.name,
                                'partner': partner_match.group(1).strip() if partner_match else 'Unknown',
                                'amount': amount
                            })
            except:
                continue
    
    # Also check Approved/ODOO folder for invoices approved this week
    approved_odo_path = VAULT_PATH / 'Approved' / 'ODOO'
    if approved_odo_path.exists():
        for filepath in approved_odo_path.glob('*.md'):
            try:
                content = filepath.read_text(encoding='utf-8')
                amount_match = re.search(r'amount:\s*([\d.]+)', content)
                partner_match = re.search(r'partner_name:\s*(.+)', content)
                created_match = re.search(r'created:\s*(.+)', content)
                
                if created_match:
                    try:
                        created_date = datetime.fromisoformat(created_match.group(1).strip()).date()
                        if week_start.date() <= created_date <= week_end.date():
                            if amount_match and filepath.name not in [i['file'] for i in summary['invoice_details']]:
                                summary['invoices_created'] += 1
                                amount = float(amount_match.group(1))
                                summary['invoice_details'].append({
                                    'file': filepath.name,
                                    'partner': partner_match.group(1).strip() if partner_match else 'Unknown',
                                    'amount': amount
                                })
                    except:
                        pass
            except:
                continue
    
    # Read Current_Month.md for revenue
    current_month_file = ACCOUNTING_PATH / 'Current_Month.md'
    if current_month_file.exists():
        content = current_month_file.read_text(encoding='utf-8')
        revenue_match = re.search(r'\*\*Total Revenue\*\*\s*\|\s*\$?([\d,]+\.?\d*)', content)
        if revenue_match:
            summary['total_revenue'] = float(revenue_match.group(1).replace(',', ''))
    
    return summary


def get_email_activity(week_start, week_end):
    """Get email activity."""
    activity = {'emails_sent': 0}
    
    if EMAIL_LOG.exists():
        try:
            data = json.loads(EMAIL_LOG.read_text(encoding='utf-8'))
            emails = data.get('sent_emails', [])
            for email in emails:
                sent_at = email.get('sent_at', '')
                if sent_at:
                    email_date = datetime.fromisoformat(sent_at).date()
                    if week_start.date() <= email_date <= week_end.date():
                        activity['emails_sent'] += 1
        except:
            pass
    
    return activity


def get_audit_summary(week_start, week_end):
    """Get audit log summary."""
    summary = {'total_actions': 0, 'by_type': {}, 'by_result': {}}
    
    if AUDIT_PATH.exists():
        for audit_file in AUDIT_PATH.glob('*.json'):
            try:
                date_str = audit_file.stem
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
    
    return summary


def generate_suggestions(completed_tasks, facebook_activity, odoo_summary, business_goals):
    """Generate proactive suggestions."""
    suggestions = []
    
    # Facebook activity
    if facebook_activity['posts_count'] == 0:
        suggestions.append("📱 No Facebook posts this week. Consider scheduling content to maintain engagement.")
    elif facebook_activity['posts_count'] < 3:
        suggestions.append(f"📱 Only {facebook_activity['posts_count']} Facebook posts this week. Aim for 3-5 posts for better engagement.")
    
    # Revenue suggestion
    weekly_target = business_goals['revenue_target'] / 4
    if odoo_summary['total_revenue'] > 0:
        if odoo_summary['total_revenue'] < weekly_target * 0.5:
            suggestions.append(f"💰 Revenue (${odoo_summary['total_revenue']:.2f}) is below 50% of weekly target (${weekly_target:.2f}). Consider following up on pending invoices.")
    else:
        if odoo_summary['invoices_created'] > 0:
            suggestions.append(f"💰 {odoo_summary['invoices_created']} draft invoice(s) pending approval. Review and approve to accelerate revenue recognition.")
    
    # Task completion
    if len(completed_tasks) == 0:
        suggestions.append("✅ No tasks completed this week. Review pending items in Needs_Action folder.")
    elif len(completed_tasks) < 5:
        suggestions.append(f"✅ Only {len(completed_tasks)} tasks completed this week. Consider prioritizing high-impact tasks.")
    
    # Invoice suggestion
    if odoo_summary['invoices_created'] == 0:
        suggestions.append("📄 No invoices created this week. Review pending billing opportunities.")
    
    if not suggestions:
        suggestions.append("🎯 Great week! Continue maintaining momentum on business goals.")
    
    return suggestions


def update_dashboard(briefing_path):
    """Update Dashboard.md with briefing status."""
    try:
        dashboard = get_dashboard_manager()
        today = datetime.now().strftime('%Y-%m-%d')
        
        dashboard.state['last_briefing_date'] = today
        dashboard.log_activity(f"CEO Briefing Generated: {briefing_path.name}", "Success")
        dashboard.refresh()
        
    except Exception as e:
        print(f"[ERROR] Failed to update dashboard: {e}")


def generate_briefing():
    """Generate the CEO briefing."""
    now = datetime.now()
    week_start, week_end = get_week_range(now)
    
    print("="*70)
    print(" GENERATING MONDAY MORNING CEO BRIEFING")
    print("="*70)
    print(f"Period: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
    print()
    
    # Gather data
    print("Reading Business_Goals.md...")
    business_goals = read_business_goals()
    
    print("Reading /Done folder...")
    completed_tasks = get_completed_tasks(week_start, week_end)
    
    print("Reading /Accounting/Current_Month.md...")
    odoo_summary = get_odoo_summary(week_start, week_end)
    
    print("Reading /Logs/audit/ folder...")
    audit_summary = get_audit_summary(week_start, week_end)
    
    print("Reading Gmail activity...")
    email_activity = get_email_activity(week_start, week_end)
    
    print("Reading LinkedIn activity...")
    linkedin_activity = get_linkedin_activity(week_start, week_end)
    
    print("Reading Facebook activity...")
    facebook_activity = get_facebook_activity(week_start, week_end)
    
    # Generate suggestions
    print("Generating proactive suggestions...")
    suggestions = generate_suggestions(completed_tasks, facebook_activity, odoo_summary, business_goals)
    
    # Calculate metrics
    total_revenue = odoo_summary['total_revenue']
    weekly_target = business_goals['revenue_target'] / 4
    progress_pct = (total_revenue / weekly_target * 100) if weekly_target > 0 else 0
    
    # Create briefing
    briefing_date = now.strftime('%Y-%m-%d')
    briefing_filename = f"CEO_Briefing_{briefing_date}.md"
    briefing_path = BRIEFINGS_PATH / briefing_filename
    BRIEFINGS_PATH.mkdir(parents=True, exist_ok=True)
    
    print()
    print("="*70)
    print(" GENERATING BRIEFING DOCUMENT")
    print("="*70)
    
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

This week's business performance overview with key metrics, completed tasks, and actionable insights.

**Week At A Glance:**
- Tasks Completed: {len(completed_tasks)}
- Invoices Created: {odoo_summary['invoices_created']}
- Total Revenue: ${total_revenue:,.2f}
- Facebook Posts: {facebook_activity['posts_count']}
- LinkedIn Posts: {linkedin_activity['posts_count']}

---

## Revenue This Week

| Metric | Amount |
|--------|--------|
| **Total Revenue** | ${total_revenue:,.2f} |
| **Weekly Target** | ${weekly_target:,.2f} |
| **Progress** | {progress_pct:.1f}% |

"""

    # Revenue analysis
    if total_revenue >= weekly_target:
        content += "🎉 **Excellent!** Revenue target achieved or exceeded this week.\n\n"
    elif total_revenue >= weekly_target * 0.75:
        content += "📈 **Good progress.** Close to target, keep pushing!\n\n"
    elif total_revenue >= weekly_target * 0.5:
        content += "⚠️ **Below target.** Consider following up on pending invoices.\n\n"
    else:
        content += "🔴 **Significantly below target.** Immediate action recommended.\n\n"

    # Invoice details
    if odoo_summary['invoice_details']:
        content += "### Draft Invoices Pending Approval\n\n"
        content += "| Client | Amount | Status |\n"
        content += "|--------|--------|--------|\n"
        for inv in odoo_summary['invoice_details']:
            content += f"| {inv['partner']} | ${inv['amount']:.2f} | Draft |\n"
        content += "\n"

    content += f"""## Completed Tasks

**Total Completed:** {len(completed_tasks)}

"""

    if completed_tasks:
        content += "| Task | Completed Date |\n"
        content += "|------|----------------|\n"
        for task in completed_tasks[:15]:
            completed_date = datetime.fromisoformat(task['completed_at']).strftime('%Y-%m-%d')
            content += f"| {task['name']} | {completed_date} |\n"
        if len(completed_tasks) > 15:
            content += f"\n*...and {len(completed_tasks) - 15} more tasks*\n"
    else:
        content += "_No tasks completed this week._\n"

    content += f"""

## Facebook Activity

| Metric | Count |
|--------|-------|
| **Posts This Week** | {facebook_activity['posts_count']} |
| **Last Post** | {facebook_activity['last_post'] or 'None'} |

"""

    if facebook_activity['posts_count'] >= 3:
        content += "✅ Strong Facebook presence this week.\n\n"
    elif facebook_activity['posts_count'] > 0:
        content += "⚠️ Consider increasing Facebook posting frequency.\n\n"
    else:
        content += "🔴 No Facebook activity detected this week.\n\n"

    content += f"""## LinkedIn Activity

| Metric | Count |
|--------|-------|
| **Posts This Week** | {linkedin_activity['posts_count']} |
| **Last Post** | {linkedin_activity['last_post'] or 'None'} |

"""

    content += f"""## Odoo Accounting Summary

| Metric | Count |
|--------|-------|
| **Invoices Created** | {odoo_summary['invoices_created']} |
| **Payments Received** | {odoo_summary['payments_received']} |
| **Total Revenue** | ${odoo_summary['total_revenue']:,.2f} |

"""

    content += f"""## Gmail Activity

| Metric | Count |
|--------|-------|
| **Emails Sent** | {email_activity['emails_sent']} |

"""

    content += f"""## System Activity Summary

| Metric | Count |
|--------|-------|
| **Total Actions** | {audit_summary['total_actions']} |

"""

    if audit_summary['by_type']:
        content += "### Actions by Type\n\n"
        for action_type, count in sorted(audit_summary['by_type'].items(), key=lambda x: x[1], reverse=True)[:5]:
            content += f"- **{action_type}:** {count}\n"
    else:
        content += "_No activity recorded in audit logs._\n"

    content += f"""

## Proactive Suggestions

"""

    for i, suggestion in enumerate(suggestions, 1):
        content += f"{i}. {suggestion}\n\n"

    content += f"""
---

## Next Week's Focus Areas

- [ ] Review and follow up on pending invoices
- [ ] Schedule social media content for next week
- [ ] Process any pending items in Needs_Action folder
- [ ] Review and approve pending Odoo invoices

---

## Quick Links

- [Dashboard](../Dashboard.md) - Current system status
- [Pending Approvals](../Pending_Approval/) - Items awaiting approval
- [Business Goals](../Business_Goals.md) - Q1 2026 objectives
- [Briefings Archive](./) - All briefings

---

*Generated by Gold Tier AI Employee - CEO Briefing System*
"""

    # Write briefing
    briefing_path.write_text(content, encoding='utf-8')
    
    print(f"Briefing saved to: {briefing_path}")
    print()
    
    # Update dashboard
    print("Updating Dashboard.md...")
    update_dashboard(briefing_path)
    print("Dashboard updated!")
    
    print()
    print("="*70)
    print(" CEO BRIEFING GENERATED SUCCESSFULLY!")
    print("="*70)
    print(f"File: Briefings/{briefing_filename}")
    print(f"Period: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
    print(f"Tasks Completed: {len(completed_tasks)}")
    print(f"Invoices Created: {odoo_summary['invoices_created']}")
    print(f"Total Revenue: ${total_revenue:,.2f}")
    print("="*70)
    
    return briefing_path


if __name__ == '__main__':
    try:
        generate_briefing()
        print("\nCEO Briefing generated successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError generating briefing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
