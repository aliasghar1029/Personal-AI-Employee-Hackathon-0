# Gold Tier AI Employee - Complete Setup Guide

**Upgrade from Silver Tier** - Adds Facebook Integration, Odoo Accounting, CEO Briefings, and Error Recovery

---

## Overview

Gold Tier transforms your AI Employee into a complete business automation system with:

- **Facebook Integration** - Dual-method posting (API + Playwright fallback)
- **Odoo Accounting** - Self-hosted ERP integration via Docker
- **CEO Briefings** - Automated weekly business reports
- **Error Recovery** - Health monitoring and auto-recovery
- **Audit Logging** - Comprehensive action tracking

---

## Quick Start

### 1. Install Dependencies

```bash
# First, ensure Bronze and Silver Tier requirements are installed
pip install -r requirements.txt
pip install -r requirements_silver.txt

# Then install Gold Tier additions
pip install -r requirements_gold.txt

# Install Playwright browsers (required for Facebook automation)
playwright install
```

### 2. Install Docker Desktop (for Odoo)

Download and install Docker Desktop for Windows:
- https://www.docker.com/products/docker-desktop/

### 3. Start Odoo (Optional - for Accounting)

```bash
# Start Odoo with Docker Compose
docker-compose up -d

# Access Odoo at: http://localhost:8069
# First login: admin / admin
# Create database: ai_employee
# Install Accounting module
```

### 4. Configure Environment

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your API credentials
# See "API Setup" section below for details
```

### 5. Start the AI Employee

**Windows (One-Click Start):**
```batch
start_gold.bat
```

**Manual Start (Individual Services):**
```bash
# Start all watchers in separate terminals
python gmail_watcher.py      # Terminal 1
python whatsapp_watcher.py   # Terminal 2
python filesystem_watcher.py # Terminal 3
python facebook_manager.py   # Terminal 4 (Gold Tier)
python odoo_mcp_server.py    # Terminal 5 (Gold Tier)
python scheduler.py          # Terminal 6
python ceo_briefing.py       # Terminal 7 (Gold Tier)
python error_recovery.py     # Terminal 8 (Gold Tier)
```

### 6. Open Dashboard in Obsidian

Open `AI_Employee_Vault/Dashboard.md` in Obsidian to monitor activity.

---

## API Setup

### Facebook Graph API (Method A - Recommended)

1. **Go to Facebook Developers:** https://developers.facebook.com/

2. **Create a New App:**
   - Click "My Apps" → "Create App"
   - App Type: "Business"
   - Fill in app details

3. **Get App Credentials:**
   - Go to "Settings" → "Basic"
   - Copy App ID and App Secret

4. **Get Page Access Token:**
   - Go to "Graph API Explorer"
   - Select your app
   - Select permissions: `pages_manage_posts`, `pages_read_engagement`
   - Generate access token
   - Copy the Page Access Token

5. **Configure .env:**
   ```bash
   FACEBOOK_APP_ID=your_app_id_here
   FACEBOOK_APP_SECRET=your_app_secret_here
   FACEBOOK_PAGE_ID=your_page_id_here
   FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token_here
   ```

### Facebook Playwright (Method B - Fallback)

No API setup required. Uses browser automation.

**First Run Setup:**
1. Run `python facebook_playwright.py`
2. A browser window will open
3. Login to Facebook manually
4. Session will be saved in `facebook_session/` folder

**Configure .env:**
```bash
FACEBOOK_EMAIL=your_facebook_email
FACEBOOK_PASSWORD=your_facebook_password
FACEBOOK_SESSION_PATH=./facebook_session
```

### Odoo Configuration (Gold Tier)

1. **Start Odoo with Docker:**
   ```bash
   docker-compose up -d
   ```

2. **Access Odoo:**
   - Open browser: http://localhost:8069
   - Click "Create Database"
   - Master Password: `admin`
   - Database Name: `ai_employee`
   - Email: `admin@example.com`
   - Password: `admin` (change this!)

3. **Install Accounting Module:**
   - Go to Apps menu
   - Search "Accounting" or "Invoicing"
   - Click "Install"

4. **Configure .env:**
   ```bash
   ODOO_URL=http://localhost:8069
   ODOO_DB=ai_employee
   ODOO_USERNAME=admin
   ODOO_PASSWORD=your_password
   ```

---

## Configuration

### Environment Variables (.env)

Copy `.env.example` to `.env` and configure:

```bash
# ===========================================
# Facebook Settings (Gold Tier)
# ===========================================
# Method A - Graph API (Recommended)
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
FACEBOOK_PAGE_ID=your_page_id_here
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token_here

# Method B - Playwright (Fallback)
FACEBOOK_EMAIL=your_facebook_email
FACEBOOK_PASSWORD=your_facebook_password
FACEBOOK_SESSION_PATH=./facebook_session

# Facebook Manager Settings
FACEBOOK_CHECK_INTERVAL=60
FACEBOOK_API_FIRST=true

# ===========================================
# Odoo Settings (Gold Tier)
# ===========================================
ODOO_URL=http://localhost:8069
ODOO_DB=ai_employee
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password
ODOO_CHECK_INTERVAL=60

# ===========================================
# Gmail Settings (Silver Tier)
# ===========================================
GMAIL_CLIENT_ID=your_gmail_client_id_here
GMAIL_CLIENT_SECRET=your_gmail_client_secret_here
GMAIL_CHECK_INTERVAL=120

# ===========================================
# LinkedIn Settings (Silver Tier)
# ===========================================
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_CHECK_INTERVAL=60

# ===========================================
# WhatsApp Settings (Silver Tier)
# ===========================================
WHATSAPP_SESSION_PATH=./whatsapp_session
WHATSAPP_CHECK_INTERVAL=60

# ===========================================
# General Settings
# ===========================================
VAULT_PATH=./AI_Employee_Vault
DRY_RUN=true                      # IMPORTANT: Keep true until ready!
PAYMENT_APPROVAL_THRESHOLD=500

# ===========================================
# Error Recovery Settings (Gold Tier)
# ===========================================
ERROR_RETRY_DELAY=30
ERROR_MAX_RETRIES=5
HEALTH_CHECK_INTERVAL=60
AUTO_RESTART_DELAY=30
```

### Critical Settings

**DRY_RUN Mode:**
- `DRY_RUN=true` (default): Logs actions but doesn't post or send
- `DRY_RUN=false`: Actually posts to Facebook and sends emails
- **Always test with DRY_RUN=true first!**

---

## Gold Tier Features

### 1. Facebook Integration

**Two Methods with Smart Fallback:**

#### Method A - Graph API (`facebook_poster.py`)
- Official Facebook API
- More reliable and faster
- Requires API credentials
- Best for production use

#### Method B - Playwright (`facebook_playwright.py`)
- Browser automation
- No API setup required
- Works as fallback when API fails
- Good for testing

#### Smart Manager (`facebook_manager.py`)
- Tries API first
- Automatically falls back to Playwright
- Checks queue every 60 seconds
- Prints which method was used

**Usage:**
1. Create post in `/Social/Facebook_Queue/`:
   ```markdown
   ---
   type: facebook_post
   hashtags: #business, #ai, #automation
   ---

   Excited to announce our new AI Employee system!

   #AI #Automation #Business
   ```

2. Facebook Manager posts automatically
3. File moves to `/Social/Facebook_Posted/`

### 2. Odoo Accounting Integration

**Odoo MCP Server (`odoo_mcp_server.py`):**

- Creates draft invoices
- Reads customer list
- Checks payment status
- Creates draft expenses
- All actions require human approval

**Approval Workflow:**
1. AI creates approval request in `/Pending_Approval/ODOO/`
2. Human reviews and moves to `/Approved/ODOO/`
3. Odoo MCP executes the action
4. Result logged to `/Logs/audit/`

**Example Approval Request:**
```markdown
---
type: odoo_approval
action_type: create_draft_invoice
partner_name: Client ABC
partner_email: client@abc.com
amount: 1000.00
description: Consulting services
due_days: 30
---

# Odoo Invoice Approval Request

## Invoice Details
| Field | Value |
|-------|-------|
| Customer | Client ABC |
| Amount | $1,000.00 |
| Due Date | 30 days |

## To Approve
Move this file to `/Approved/ODOO/` folder
```

### 3. Weekly CEO Briefing

**CEO Briefing Generator (`ceo_briefing.py`):**

- Runs every Sunday at 9:00 PM
- Reads `Business_Goals.md`
- Checks completed tasks
- Generates comprehensive briefing

**Briefing Includes:**
- Revenue summary
- Completed tasks
- Facebook/LinkedIn activity
- Odoo accounting summary
- Proactive suggestions

**Output:** `/Briefings/CEO_Briefing_YYYY-MM-DD.md`

**Manual Generation:**
```bash
python ceo_briefing.py --generate-now
```

### 4. Error Recovery System

**Error Recovery (`error_recovery.py`):**

- Health checks every 60 seconds
- Auto-retry failed services
- Auto-restart crashed watchers
- Queue actions for later retry
- Log all errors to `/Logs/errors/`

**Monitored Services:**
- Gmail Watcher
- WhatsApp Watcher
- Facebook Manager
- LinkedIn Poster
- Odoo MCP
- Scheduler

**Recovery Strategies:**
- Gmail API down → Queue locally, retry later
- Facebook API fails → Switch to Playwright
- Odoo down → Save actions locally, sync when restored
- Watcher crashes → Auto-restart after 30 seconds

### 5. Audit Logging

**Audit Logger (`audit_logger.py`):**

- Logs every action to `/Logs/audit/YYYY-MM-DD.json`
- 90-day retention
- Weekly summaries for briefings
- Export capability

**Log Entry Format:**
```json
{
  "timestamp": "2026-03-01T10:30:00Z",
  "action_type": "facebook_post",
  "actor": "facebook_manager",
  "result": "success",
  "details": "Posted to Facebook Page via API",
  "metadata": {
    "post_id": "12345",
    "method": "api"
  }
}
```

---

## Folder Structure

After setup, your vault should look like:

```
AI_Employee_Vault/
├── Inbox/                  # Raw incoming items
├── Needs_Action/           # Items requiring action
├── In_Progress/           # Tasks being worked on now
├── Plans/                 # Created plans with checkboxes
├── Done/                  # Completed tasks
│   └── ODOO/              # Completed Odoo actions (Gold Tier)
├── Logs/                  # Activity logs
│   ├── audit/             # Audit logs (Gold Tier)
│   └── errors/            # Error logs (Gold Tier)
├── Pending_Approval/      # Awaiting human approval
│   └── ODOO/              # Odoo approvals (Gold Tier)
├── Approved/              # Human-approved actions
│   └── ODOO/              # Approved Odoo actions (Gold Tier)
├── Rejected/              # Human-rejected actions
│   └── ODOO/              # Rejected Odoo actions (Gold Tier)
├── Sent/                  # Sent emails
├── Social/
│   ├── LinkedIn_Queue/    # LinkedIn posts waiting
│   ├── LinkedIn_Posted/   # LinkedIn posts published
│   ├── Facebook_Queue/    # Facebook posts waiting (Gold Tier)
│   └── Facebook_Posted/   # Facebook posts published (Gold Tier)
├── Briefings/             # Daily and weekly briefings
│   └── CEO_Briefing_*.md  # Weekly CEO briefings (Gold Tier)
├── Accounting/            # Bank transactions
│   └── Current_Month.md
├── Error_Queue/           # Queued actions for retry (Gold Tier)
├── Dashboard.md           # Real-time status summary
├── Business_Goals.md      # Q1 2026 objectives
├── Company_Handbook.md    # Rules of engagement
├── credentials.json       # Gmail OAuth credentials
└── token.json             # Gmail auth token
```

---

## Testing Checklist

Before going live (setting DRY_RUN=false):

### Facebook Integration
- [ ] Facebook API credentials configured
- [ ] Facebook Manager starts without errors
- [ ] Test post in DRY_RUN mode
- [ ] Verify file moves to Facebook_Posted
- [ ] Dashboard updates with Facebook status

### Odoo Integration
- [ ] Docker Odoo starts successfully
- [ ] Can access http://localhost:8069
- [ ] Accounting module installed
- [ ] Odoo MCP connects successfully
- [ ] Test invoice creation in DRY_RUN mode
- [ ] Approval workflow works

### CEO Briefing
- [ ] Business_Goals.md exists
- [ ] Manual briefing generation works
- [ ] Briefing includes all sections
- [ ] Dashboard updates with briefing info

### Error Recovery
- [ ] Health checks run every 60 seconds
- [ ] Service status shown on Dashboard
- [ ] Errors logged to /Logs/errors/
- [ ] Audit logs created in /Logs/audit/

---

## Troubleshooting

### Facebook API Errors

**"Invalid Access Token":**
1. Check token hasn't expired
2. Refresh token using `facebook_poster.py`
3. Verify Page permissions

**"Permissions Not Granted":**
1. Go to Facebook App Dashboard
2. Add `pages_manage_posts` permission
3. Add `pages_read_engagement` permission
4. Re-generate access token

### Facebook Playwright Errors

**"Browser won't open":**
```bash
# Reinstall Playwright
playwright install chromium
```

**"Login page not loading":**
1. Check internet connection
2. Try manual Facebook login in browser
3. Clear `facebook_session/` folder and restart

### Odoo Errors

**"Connection refused":**
```bash
# Check if Odoo is running
docker-compose ps

# Restart Odoo
docker-compose down
docker-compose up -d
```

**"Authentication failed":**
1. Verify credentials in .env
2. Check database name matches
3. Reset Odoo admin password if needed

### CEO Briefing Errors

**"No data in briefing":**
1. Ensure tasks are moved to /Done/
2. Check Business_Goals.md exists
3. Verify audit logs are being created

### Error Recovery Errors

**"Service won't restart":**
1. Check logs for specific error
2. Verify Python dependencies installed
3. Restart manually: `python <service>.py`

---

## Docker Commands

### Odoo Management

```bash
# Start Odoo
docker-compose up -d

# Stop Odoo
docker-compose down

# View logs
docker-compose logs -f odoo
docker-compose logs -f db

# Restart Odoo
docker-compose restart

# Update Odoo
docker-compose pull
docker-compose up -d

# Backup database
docker-compose exec db pg_dump -U odoo postgres > backup.sql

# Restore database
docker-compose exec -T db psql -U odoo < backup.sql

# Remove all data (WARNING: destructive)
docker-compose down -v
```

---

## Security Best Practices

1. **Never commit sensitive files:**
   ```bash
   # Add to .gitignore
   .env
   credentials.json
   token.json
   *.log
   whatsapp_session/
   facebook_session/
   linkedin_session/
   ```

2. **Change default passwords:**
   - Odoo admin password (default: admin)
   - Database password (default: odoo)

3. **Review all approvals** before moving to `/Approved/`

4. **Check logs regularly** in `/Logs/`

5. **Rotate API credentials** monthly

6. **Keep DRY_RUN=true** until fully tested

7. **Backup your vault** regularly

8. **Secure Docker:**
   - Don't expose Odoo to public internet without HTTPS
   - Use strong database passwords
   - Regular backups

---

## Upgrade Path

### To Platinum Tier
Add these features:
- Cloud deployment for 24/7 operation
- Work-Zone Specialization (Cloud vs Local)
- Vault sync between Cloud and Local
- HTTPS, backups, health monitoring
- A2A (Agent-to-Agent) communication

---

## Support

For issues or questions:

1. **Check logs first:** `/Logs/` folder
2. **Review Dashboard.md** for status
3. **Check Company_Handbook.md** for rules
4. **Review error logs:** `/Logs/errors/`
5. **Check audit trail:** `/Logs/audit/`

---

## Credits

Built for the **Personal AI Employee Hackathon 2026**

**Tier:** Gold
**Version:** 1.0.0
**Last Updated:** 2026-03-05

---

## Changelog

### Gold Tier v1.0.0
- Facebook Integration (API + Playwright)
- Odoo Accounting via Docker
- Weekly CEO Briefings
- Error Recovery System
- Comprehensive Audit Logging
- Smart Fallback Manager
- One-click startup script

---

*Local-first, agent-driven, human-in-the-loop*
