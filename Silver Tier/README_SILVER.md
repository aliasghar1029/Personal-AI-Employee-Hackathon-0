# Silver Tier AI Employee - Setup Guide

**Upgrade from Bronze Tier** - Adds Gmail, WhatsApp, LinkedIn, Email MCP, and Automated Scheduling

---

## Quick Start

### 1. Install Dependencies

```bash
# First, ensure Bronze Tier requirements are installed
pip install -r requirements.txt

# Then install Silver Tier additions
pip install -r requirements_silver.txt

# Install Playwright browsers (required for WhatsApp and LinkedIn)
playwright install
```

### 2. Configure Environment

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your API credentials
# See "API Setup" section below for details
```

### 3. Start the AI Employee

**Windows (One-Click Start):**
```batch
start_silver.bat
```

**Manual Start (Individual Services):**
```bash
# Start all watchers in separate terminals
python gmail_watcher.py      # Terminal 1
python whatsapp_watcher.py   # Terminal 2
python filesystem_watcher.py # Terminal 3
python scheduler.py          # Terminal 4

# Optional services
python linkedin_poster.py    # Terminal 5 (for LinkedIn auto-posting)
python email_mcp_server.py   # Terminal 6 (for email sending)
```

### 4. Open Dashboard in Obsidian

Open `AI_Employee_Vault/Dashboard.md` in Obsidian to monitor activity.

---

## API Setup

### Gmail API (Required for Gmail Watcher and Email MCP)

1. **Go to Google Cloud Console:** https://console.cloud.google.com/

2. **Create a New Project:**
   - Click "Select a project" → "New Project"
   - Name it "AI Employee" or similar

3. **Enable Gmail API:**
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Download the JSON file

5. **Save Credentials:**
   - Rename downloaded file to `credentials.json`
   - Place in `AI_Employee_Vault/` folder
   - **Never commit this file to version control!**

6. **First Run Authentication:**
   - Run `python gmail_watcher.py`
   - Browser will open for OAuth consent
   - Sign in with your Google account
   - Grant permissions
   - `token.json` will be created automatically

### LinkedIn API (Optional - for LinkedIn Auto-Posting)

1. **Go to LinkedIn Developers:** https://www.linkedin.com/developers/apps

2. **Create an App:**
   - Click "Create app"
   - Link to a LinkedIn Company Page (required)
   - Fill in app details

3. **Get Credentials:**
   - Go to "Auth" tab
   - Copy Client ID and Client Secret
   - Create OAuth 2.0 access token

4. **Configure .env:**
   ```bash
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_client_secret
   LINKEDIN_ACCESS_TOKEN=your_access_token
   ```

### WhatsApp Web (No API Required)

WhatsApp uses Playwright browser automation (no API setup needed).

**First Run Setup:**
1. Run `python whatsapp_watcher.py`
2. A browser window will open
3. Scan the QR code with your WhatsApp mobile app
4. Session will be saved in `whatsapp_session/` folder

**Note:** Be aware of WhatsApp's Terms of Service. Use at your own risk.

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
├── Logs/                  # Activity logs (auto-created)
├── Pending_Approval/      # Awaiting human approval
├── Approved/              # Human-approved actions
├── Rejected/              # Human-rejected actions
├── Sent/                  # Sent emails (auto-created)
├── Social/
│   ├── LinkedIn_Queue/    # Posts waiting to be published
│   └── LinkedIn_Posted/   # Published posts (auto-created)
├── Briefings/             # Daily and weekly briefings (auto-created)
├── Accounting/            # Bank transactions (for Gold Tier)
├── Dashboard.md           # Real-time status summary
├── Company_Handbook.md    # Rules of engagement
├── credentials.json       # Gmail OAuth credentials (DO NOT SHARE)
└── token.json             # Gmail auth token (auto-created, DO NOT SHARE)
```

---

## Configuration

### Environment Variables (.env)

Copy `.env.example` to `.env` and configure:

```bash
# Gmail Settings
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_CHECK_INTERVAL=120          # Check every 2 minutes
MAX_EMAILS_PER_HOUR=10            # Rate limit

# LinkedIn Settings
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_CHECK_INTERVAL=300       # Check every 5 minutes

# WhatsApp Settings
WHATSAPP_SESSION_PATH=./whatsapp_session
WHATSAPP_CHECK_INTERVAL=60        # Check every 60 seconds

# General Settings
VAULT_PATH=./AI_Employee_Vault
DRY_RUN=true                      # IMPORTANT: Keep true until ready!
PAYMENT_APPROVAL_THRESHOLD=500    # Flag payments over $500
SCHEDULER_CHECK_INTERVAL=120      # Check every 2 minutes
```

### Critical Settings

**DRY_RUN Mode:**
- `DRY_RUN=true` (default): Logs actions but doesn't send emails or posts
- `DRY_RUN=false`: Actually sends emails and LinkedIn posts
- **Always test with DRY_RUN=true first!**

---

## Usage Guide

### Processing Incoming Emails

1. **Automatic:** Gmail Watcher runs continuously
2. **New emails** appear in `/Needs_Action/` as `.md` files
3. **Scheduler** processes every 2 minutes:
   - Creates plan in `/Plans/`
   - Moves to `/In_Progress/`
   - Triggers Qwen Code
4. **Review** the created plan
5. **Approve** any draft replies by moving to `/Approved/`

### Processing WhatsApp Messages

1. **Automatic:** WhatsApp Watcher runs continuously
2. **Urgent messages** (containing keywords) appear in `/Needs_Action/`
3. **Same workflow** as email processing

### Sending Emails

1. **AI creates** draft email in `/Pending_Approval/`
2. **Review** the draft
3. **To Approve:** Move file to `/Approved/`
4. **To Reject:** Move file to `/Rejected/`
5. **Email MCP Server** sends approved emails automatically

### LinkedIn Posting

1. **Create post** in `/Social/LinkedIn_Queue/`:
   ```markdown
   ---
   type: linkedin_post
   hashtags: #business, #ai, #automation
   ---
   
   Excited to share our latest AI project!
   
   #AI #Automation
   ```
2. **LinkedIn Poster** checks every 5 minutes
3. **Posts automatically** (if DRY_RUN=false)
4. **File moves** to `/Social/LinkedIn_Posted/`

### Daily Briefing

- **Automatic:** Generated every day at 8:00 AM
- **Location:** `/Briefings/Daily_Briefing_YYYY-MM-DD.md`
- **Includes:** Task overview, priorities, recent activity

### Weekly Summary

- **Automatic:** Generated every Sunday at 9:00 PM
- **Location:** `/Briefings/Weekly_Summary_YYYY-MM-DD.md`
- **Includes:** Week's completions, metrics, next week's focus

---

## Testing Checklist

Before going live (setting DRY_RUN=false):

- [ ] Gmail Watcher detects new emails
- [ ] WhatsApp Watcher detects urgent messages
- [ ] Scheduler creates plans in `/Plans/`
- [ ] Dashboard.md updates correctly
- [ ] Email drafts appear in `/Pending_Approval/`
- [ ] Moving file to `/Approved/` triggers sending (in DRY_RUN mode)
- [ ] LinkedIn posts are queued correctly
- [ ] Daily briefing generates at 8:00 AM
- [ ] All logs are being written to `/Logs/`

---

## Troubleshooting

### "Module not found" Errors

```bash
# Reinstall requirements
pip install -r requirements.txt
pip install -r requirements_silver.txt

# Install Playwright browsers
playwright install
```

### Gmail API Errors

1. **Check credentials.json exists** in `AI_Employee_Vault/`
2. **Verify Gmail API is enabled** in Google Cloud Console
3. **Delete token.json** and re-authenticate
4. **Check Logs/gmail_watcher.log** for details

### WhatsApp Watcher Not Working

1. **First run:** May need to scan QR code manually
2. **Check session folder** exists: `whatsapp_session/`
3. **Reinstall Playwright:**
   ```bash
   playwright install chromium
   ```

### LinkedIn Poster Not Working

1. **Log in manually first** to create session
2. **Check DRY_RUN setting** in `.env`
3. **Verify LinkedIn app** is approved by LinkedIn

### Scheduler Not Triggering Qwen

1. **Verify Qwen Code is installed:**
   ```bash
   qwen --version
   ```
2. **Check Logs/scheduler.log** for errors
3. **Ensure vault path** is correct in `.env`

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
   linkedin_session/
   ```

2. **Review all approvals** before moving to `/Approved/`

3. **Check logs regularly** in `/Logs/`

4. **Rotate API credentials** monthly

5. **Keep DRY_RUN=true** until fully tested

6. **Backup your vault** regularly

---

## Upgrade Path

### To Gold Tier
Add these features:
- Odoo accounting integration
- Facebook/Instagram integration  
- Twitter/X integration
- Weekly Business and Accounting Audit
- Ralph Wiggum loop for autonomous completion

### To Platinum Tier
Add these features:
- Cloud deployment for 24/7 operation
- Work-Zone Specialization (Cloud vs Local)
- Vault sync between Cloud and Local
- HTTPS, backups, health monitoring

---

## Support

For issues or questions:

1. **Check logs first:** `/Logs/` folder
2. **Review Dashboard.md** for status
3. **Check Company_Handbook.md** for rules
4. **Review SKILL.md** for capabilities

---

## Credits

Built for the **Personal AI Employee Hackathon 2026**

**Tier:** Silver  
**Version:** 1.0.0  
**Last Updated:** 2026-02-22

---

*Local-first, agent-driven, human-in-the-loop*
