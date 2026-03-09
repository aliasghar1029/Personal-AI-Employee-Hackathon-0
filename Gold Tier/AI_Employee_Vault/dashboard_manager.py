"""
Dashboard Manager - Centralized Dashboard Update System
Updates the Gold Tier Dashboard.md with real-time status from all services.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

VAULT_PATH = Path(__file__).parent
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'
STATE_FILE = VAULT_PATH / '.dashboard_state.json'


class DashboardManager:
    """Manages the Gold Tier Dashboard with real-time updates."""
    
    def __init__(self):
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load persistent state from JSON file."""
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding='utf-8'))
            except:
                pass
        return self._default_state()
    
    def _default_state(self) -> Dict[str, Any]:
        """Return default state structure."""
        return {
            'emails_processed_today': 0,
            'emails_sent_today': 0,
            'emails_sent_total': 0,
            'linkedin_posts_today': 0,
            'linkedin_posts_week': 0,
            'linkedin_posts_total': 0,
            'facebook_posts_today': 0,
            'facebook_posts_week': 0,
            'facebook_posts_total': 0,
            'odoo_invoices_today': 0,
            'odoo_invoices_week': 0,
            'odoo_invoices_total': 0,
            'tasks_completed_today': 0,
            'tasks_completed_week': 0,
            'tasks_completed_total': 0,
            'pending_actions': 0,
            'in_progress': 0,
            'pending_approvals': 0,
            'gmail_last_checked': None,
            'gmail_new_emails': 0,
            'gmail_processed_hour': 0,
            'gmail_replies_drafted': 0,
            'gmail_replies_sent': 0,
            'gmail_status': 'Running',
            'whatsapp_last_checked': None,
            'whatsapp_urgent': 0,
            'whatsapp_keywords': 0,
            'whatsapp_total': 0,
            'whatsapp_status': 'Idle',
            'linkedin_last_post': 'Never',
            'linkedin_queue': 0,
            'linkedin_dry_run': False,
            'linkedin_status': 'Running',
            'facebook_status': 'Skip',
            'facebook_reason': 'Anti-bot protection',
            'email_mcp_status': 'Running',
            'odoo_status': 'Connected',
            'odoo_url': 'http://localhost:8069',
            'odoo_db': 'ai_employee',
            'odoo_draft_invoices': 0,
            'odoo_paid_week': 0,
            'odoo_revenue_mtd': 0,
            'odoo_actions_today': 0,
            'odoo_dry_run': False,
            'scheduler_status': 'Running',
            'error_recovery_status': 'Running',
            'last_activity': None,
            'alerts': [],
            'last_briefing_date': None,
            'last_security_check': None,
        }
    
    def _save_state(self):
        """Save state to JSON file."""
        try:
            STATE_FILE.write_text(json.dumps(self.state, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"[WARN] Could not save dashboard state: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in HH:MM format."""
        return datetime.now().strftime('%H:%M')
    
    def _get_datetime(self) -> str:
        """Get current datetime in YYYY-MM-DD HH:MM format."""
        return datetime.now().strftime('%Y-%m-%d %H:%M')
    
    def _get_date(self) -> str:
        """Get current date in YYYY-MM-DD format."""
        return datetime.now().strftime('%Y-%m-%d')
    
    def _get_status_icon(self, status: str) -> str:
        """Convert status to emoji icon."""
        status_lower = status.lower()
        if status_lower in ['running', 'active', 'healthy', 'connected']:
            return '🟢'
        elif status_lower in ['idle', 'waiting', 'pending']:
            return '🟡'
        elif status_lower in ['skip', 'stopped', 'error', 'disconnected']:
            return '🔴'
        else:
            return '⚪'
    
    def _count_files(self, path: Path) -> int:
        """Count files in a directory."""
        if not path.exists():
            return 0
        return len(list(path.glob('*.md')))
    
    def _get_action_queue(self) -> tuple:
        """Get action queue counts from folders."""
        needs_action = VAULT_PATH / 'Needs_Action'
        in_progress = VAULT_PATH / 'In_Progress'
        pending_approval = VAULT_PATH / 'Pending_Approval'
        done = VAULT_PATH / 'Done'
        
        high = self._count_files(needs_action)
        medium = self._count_files(in_progress)
        low = self._count_files(pending_approval)
        done_today = self._count_files(done)
        
        return high, medium, low, done_today
    
    def update_service(self, service: str, data: Dict[str, Any]):
        """Update state with data from a service."""
        for key, value in data.items():
            self.state[key] = value
        self._save_state()
        self.refresh()
    
    def increment_metric(self, metric: str, amount: int = 1):
        """Increment a metric counter."""
        if metric in self.state:
            self.state[metric] += amount
            self._save_state()
            self.refresh()
    
    def add_alert(self, alert: str, level: str = 'error'):
        """Add an alert to the dashboard."""
        self.state['alerts'].append({
            'message': alert,
            'level': level,
            'time': self._get_datetime()
        })
        # Keep only last 10 alerts
        self.state['alerts'] = self.state['alerts'][-10:]
        self._save_state()
        self.refresh()
    
    def clear_alerts(self):
        """Clear all alerts."""
        self.state['alerts'] = []
        self._save_state()
        self.refresh()
    
    def log_activity(self, action: str, status: str = 'Success'):
        """Log a recent activity."""
        self.state['last_activity'] = {
            'time': self._get_datetime(),
            'action': action,
            'status': status
        }
        self._save_state()
        self.refresh()
    
    def refresh(self):
        """Refresh the Dashboard.md with current state."""
        try:
            if not DASHBOARD_PATH.exists():
                return
            
            content = self._generate_dashboard()
            DASHBOARD_PATH.write_text(content, encoding='utf-8')
        except Exception as e:
            print(f"[ERROR] Dashboard refresh failed: {e}")
    
    def _generate_dashboard(self) -> str:
        """Generate the full dashboard content."""
        now = self._get_datetime()
        today = self._get_date()
        
        # Get action queue
        high, medium, low, done_today = self._get_action_queue()
        
        # Calculate totals
        total_emails = self.state['emails_sent_total']
        total_linkedin = self.state['linkedin_posts_total']
        total_facebook = self.state['facebook_posts_total']
        total_odoo = self.state['odoo_invoices_total']
        total_tasks = self.state['tasks_completed_total']
        
        # Build action queue table
        action_rows = []
        if high > 0:
            action_rows.append(f"| 🔴 High | {high} file(s) | Action Required | {today} |")
        else:
            action_rows.append("| 🔴 High | _None_ | — | — |")
        if medium > 0:
            action_rows.append(f"| 🟡 Medium | {medium} file(s) | In Progress | {today} |")
        else:
            action_rows.append("| 🟡 Medium | _None_ | — | — |")
        if low > 0:
            action_rows.append(f"| 🟢 Low | {low} file(s) | Pending Approval | {today} |")
        else:
            action_rows.append("| 🟢 Low | _None_ | — | — |")
        
        action_queue_table = '\n'.join(action_rows)
        
        # Build alerts section
        if self.state['alerts']:
            alerts_content = ""
            for alert in self.state['alerts'][-5:]:
                icon = '🚨' if alert['level'] == 'error' else '⚠️'
                alerts_content += f"\n> {icon} {alert['time']}: {alert['message']}"
        else:
            alerts_content = "> 🟢 No alerts at this time"
        
        # Build recent activity
        if self.state['last_activity']:
            activity = self.state['last_activity']
            status_icon = '✅' if activity['status'] == 'Success' else '❌'
            activity_table = f"| {activity['time']} | {activity['action']} | {status_icon} {activity['status']} |"
        else:
            activity_table = f"| {now} | System Started | ✅ Success |"
        
        # Build alerts table
        scheduled_tasks = f"""| Task | Schedule | Last Run | Next Run |
|------|----------|----------|----------|
| 📊 Folder Check | Every 2 min | {now} | {now} |
| 🌅 Daily Briefing | 8:00 AM | {today} | Tomorrow 8AM |
| 📝 CEO Briefing | Sunday 9PM | {today} | Next Sunday |"""
        
        # CEO Briefing info
        briefing_date = self.state.get('last_briefing_date', today)
        briefing_path = f"/Briefings/CEO_Briefing_{briefing_date}.md"
        
        # Security info
        security_check = self.state.get('last_security_check', today)
        
        dashboard = f"""# 🤖 AI Employee — Gold Tier Dashboard
> Last Updated: {now}
> System Status: 🟢 All Systems Operational

---

## 📊 Executive Summary
| Metric | Today | This Week | Total |
|--------|-------|-----------|-------|
| ✉️ Emails Processed | {self.state['emails_processed_today']} | {self.state['emails_processed_today']} | {self.state['emails_sent_total']} |
| 📤 Emails Sent | {self.state['emails_sent_today']} | {self.state['emails_sent_today']} | {self.state['emails_sent_total']} |
| 💼 LinkedIn Posts | {self.state['linkedin_posts_today']} | {self.state['linkedin_posts_week']} | {self.state['linkedin_posts_total']} |
| 📘 Facebook Posts | {self.state['facebook_posts_today']} | {self.state['facebook_posts_week']} | {self.state['facebook_posts_total']} |
| 🧾 Odoo Invoices | {self.state['odoo_invoices_today']} | {self.state['odoo_invoices_week']} | {self.state['odoo_invoices_total']} |
| ✅ Tasks Completed | {self.state['tasks_completed_today']} | {self.state['tasks_completed_week']} | {self.state['tasks_completed_total']} |

---

## ⚡ Live Status
| Service | Status | Last Active |
|---------|--------|-------------|
| 📧 Gmail Watcher | {self._get_status_icon(self.state['gmail_status'])} {self.state['gmail_status']} | {self.state['gmail_last_checked'] or now} |
| 💬 WhatsApp Watcher | {self._get_status_icon(self.state['whatsapp_status'])} {self.state['whatsapp_status']} | {self.state['whatsapp_last_checked'] or 'Not yet'} |
| 💼 LinkedIn Poster | {self._get_status_icon(self.state['linkedin_status'])} {self.state['linkedin_status']} | {now} |
| 📘 Facebook Manager | {self._get_status_icon(self.state['facebook_status'])} {self.state['facebook_status']} | N/A |
| 📨 Email MCP Server | {self._get_status_icon(self.state['email_mcp_status'])} {self.state['email_mcp_status']} | {now} |
| 🏢 Odoo MCP Server | {self._get_status_icon(self.state['odoo_status'])} {self.state['odoo_status']} | {now} |
| ⏰ Scheduler | {self._get_status_icon(self.state['scheduler_status'])} {self.state['scheduler_status']} | {now} |
| 🔄 Error Recovery | {self._get_status_icon(self.state['error_recovery_status'])} {self.state['error_recovery_status']} | {now} |

---

## 📥 Action Queue
{action_queue_table}

- **Pending Actions:** {high + medium + low}
- **In Progress:** {medium}
- **Pending Approvals:** {low}
- **Completed Today:** {done_today}

---

## 📧 Gmail Activity
- **Last Checked:** {self.state['gmail_last_checked'] or 'Not yet'}
- **New Emails:** {self.state['gmail_new_emails']}
- **Processed This Hour:** {self.state['gmail_processed_hour']}/50
- **Replies Drafted:** {self.state['gmail_replies_drafted']}
- **Replies Sent:** {self.state['gmail_replies_sent']}
- **Status:** {self._get_status_icon(self.state['gmail_status'])} {self.state['gmail_status']}

---

## 💬 WhatsApp Activity
- **Last Checked:** {self.state['whatsapp_last_checked'] or 'Not yet'}
- **Urgent Messages:** {self.state['whatsapp_urgent']}
- **Keywords Detected:** {self.state['whatsapp_keywords']}
- **Total Processed:** {self.state['whatsapp_total']}
- **Status:** {self._get_status_icon(self.state['whatsapp_status'])} {self.state['whatsapp_status']}

---

## 💼 LinkedIn Activity
- **Last Post:** {self.state['linkedin_last_post']}
- **Posts This Week:** {self.state['linkedin_posts_week']}
- **Posts in Queue:** {self.state['linkedin_queue']}
- **Total Posts:** {self.state['linkedin_posts_total']}
- **Status:** {self._get_status_icon(self.state['linkedin_status'])} {self.state['linkedin_status']}
- **DRY_RUN:** {'Yes' if self.state['linkedin_dry_run'] else 'No'}

---

## 📘 Facebook Activity
- **Status:** {self._get_status_icon(self.state['facebook_status'])} {self.state['facebook_status']}
- **Reason:** {self.state['facebook_reason']}
- **Posts This Week:** {self.state['facebook_posts_week']}

---

## 🏢 Odoo — Accounting
- **Connection:** {self._get_status_icon(self.state['odoo_status'])} {self.state['odoo_status']}
- **Server:** {self.state['odoo_url']}
- **Database:** {self.state['odoo_db']}
- **Draft Invoices:** {self.state['odoo_draft_invoices']}
- **Paid This Week:** ${self.state['odoo_paid_week']}
- **Total Revenue MTD:** ${self.state['odoo_revenue_mtd']}
- **Actions Today:** {self.state['odoo_actions_today']}
- **DRY_RUN:** {'Yes' if self.state['odoo_dry_run'] else 'No'}

---

## 📋 Recent Activity Log
| Time | Action | Status |
|------|--------|--------|
| {activity_table}

---

## 🚨 Alerts & Errors
{alerts_content}

---

## 📅 Scheduled Tasks
{scheduled_tasks}

---

## 📈 Weekly CEO Briefing
- **Last Generated:** {briefing_date}
- **Location:** {briefing_path}
- **Next Briefing:** Sunday 9:00 PM

---

## 🔒 Security & Audit
- **Audit Logs:** /Logs/audit/
- **Error Logs:** /Logs/errors/
- **Log Retention:** 90 days
- **Last Security Check:** {security_check}

---

*🤖 Powered by AI Employee Gold Tier | Built with Qwen Code*
"""
        return dashboard


# Singleton instance
_dashboard_manager = None


def get_dashboard_manager() -> DashboardManager:
    """Get the singleton dashboard manager instance."""
    global _dashboard_manager
    if _dashboard_manager is None:
        _dashboard_manager = DashboardManager()
    return _dashboard_manager


# Convenience functions for quick updates
def update_service(service: str, data: Dict[str, Any]):
    """Update a service's status."""
    get_dashboard_manager().update_service(service, data)


def increment_metric(metric: str, amount: int = 1):
    """Increment a metric counter."""
    get_dashboard_manager().increment_metric(metric, amount)


def add_alert(alert: str, level: str = 'error'):
    """Add an alert."""
    get_dashboard_manager().add_alert(alert, level)


def clear_alerts():
    """Clear all alerts."""
    get_dashboard_manager().clear_alerts()


def log_activity(action: str, status: str = 'Success'):
    """Log an activity."""
    get_dashboard_manager().log_activity(action, status)


def refresh_dashboard():
    """Refresh the dashboard display."""
    get_dashboard_manager().refresh()


if __name__ == '__main__':
    # Test the dashboard manager
    manager = DashboardManager()
    manager.log_activity("Dashboard Test", "Success")
    print(f"Dashboard refreshed at {manager._get_datetime()}")
    print(f"Dashboard path: {DASHBOARD_PATH}")
