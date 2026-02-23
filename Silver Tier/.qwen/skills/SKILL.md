# AI Employee Skill - Silver Tier

**Version:** 1.0.0  
**Tier:** Silver  
**Last Updated:** 2026-02-22

---

## Overview

This skill defines the capabilities of a **Silver Tier Personal AI Employee**. The AI Employee is a local-first, agent-driven autonomous assistant that manages personal and business affairs using Qwen Code as the reasoning engine and Obsidian as the management dashboard.

## Core Capabilities

### 1. Gmail Monitoring
- **Watcher:** `gmail_watcher.py`
- **Function:** Monitors Gmail for unread important emails
- **Action:** Saves emails as `.md` files in `/Needs_Action/`
- **Tracking:** Maintains processed email IDs to prevent duplicates
- **Rate Limiting:** Respects Gmail API rate limits (configurable)

### 2. WhatsApp Monitoring
- **Watcher:** `whatsapp_watcher.py`
- **Function:** Monitors WhatsApp Web for urgent messages
- **Keywords:** `urgent`, `asap`, `invoice`, `payment`, `help`, `price`, `pricing`, `emergency`, `immediate`, `money`, `bank`, `transfer`, `deadline`
- **Action:** Saves detected messages as `.md` files in `/Needs_Action/`
- **Technology:** Uses Playwright for WhatsApp Web automation

### 3. LinkedIn Auto-Posting
- **Poster:** `linkedin_poster.py`
- **Function:** Reads post content from `/Social/LinkedIn_Queue/`
- **Action:** Automatically posts to LinkedIn about business
- **Logging:** Saves posting log in `/Logs/`
- **Safety:** DRY_RUN mode by default (no real posts until enabled)

### 4. Email Sending (MCP Server)
- **Server:** `email_mcp_server.py`
- **Function:** Local MCP server that can SEND emails via Gmail
- **Approval:** Only sends after file is moved to `/Approved/` folder
- **Logging:** Logs every sent email to `/Logs/sent_emails.json`
- **Safety:** Never sends without approval; DRY_RUN mode available

### 5. Automated Scheduling
- **Scheduler:** `scheduler.py`
- **Functions:**
  - Every 2 minutes: Check `/Needs_Action/` and trigger Qwen
  - Every morning 8:00 AM: Generate daily briefing
  - Every Sunday 9:00 PM: Generate weekly summary
  - Auto-move completed tasks to `/Done/`
  - Auto-check `/Approved/` folder and trigger email sending

### 6. Human-in-the-Loop Approval
- **Automatic:** Scheduler watches `/Approved/` folder
- **Workflow:**
  - File in `/Approved/` → Trigger Email MCP
  - File in `/Rejected/` → Log rejection and notify in Dashboard
- **No Manual Prompting:** Fully automated workflow

### 7. Plan Creation
- **Trigger:** When new file arrives in `/Needs_Action/`
- **Action:** Scheduler triggers Qwen to create `PLAN_<taskname>_<date>.md`
- **Location:** Plans saved in `/Plans/` folder
- **Format:** Includes checkboxes for every step

---

## Folder Structure

```
AI_Employee_Vault/
├── Inbox/                  # Raw incoming items
├── Needs_Action/           # Items requiring action
├── In_Progress/           # Tasks being worked on now
├── Plans/                 # Created plans with checkboxes
├── Done/                  # Completed tasks
├── Logs/                  # Activity logs
├── Pending_Approval/      # Awaiting human approval
├── Approved/              # Human-approved actions
├── Rejected/              # Human-rejected actions
├── Sent/                  # Sent emails
├── Social/
│   └── LinkedIn_Queue/    # Posts waiting to be published
│   └── LinkedIn_Posted/   # Published posts
├── Briefings/             # Daily and weekly briefings
├── Accounting/            # Bank transactions (Gold Tier)
├── Dashboard.md           # Real-time status summary
├── Company_Handbook.md    # Rules of engagement
└── .qwen/
    └── skills/
        └── SKILL.md       # This file
```

---

## File Formats

### Email Action File
```markdown
---
type: email
from: sender@example.com
to: recipient@example.com
subject: Email Subject
received: 2026-02-22T10:30:00
priority: high
status: pending
email_id: gmail_id_here
---

# Email: Subject Line

**From:** sender@example.com  
**Received:** Date

---

## Content

Email body content here...

---

## Suggested Actions

- [ ] Read and understand the email
- [ ] Determine if reply is needed
- [ ] If reply needed, draft response in /Pending_Approval/
- [ ] Move to /Done when complete
```

### WhatsApp Message File
```markdown
---
type: whatsapp
from: Contact Name
received: 2026-02-22 10:30:00
processed: 2026-02-22T10:31:00
priority: high
status: pending
---

# WhatsApp Message

**From:** Contact Name  
**Received:** Timestamp  
**Priority:** HIGH

---

## Message Content

Message text here...

---

## Urgency Analysis

**Contains urgent keywords:** Yes
**Keywords found:** urgent, payment

## Suggested Actions

- [ ] Read and understand the message
- [ ] Determine if immediate response is needed
- [ ] Draft response if needed
- [ ] Move to /Done when complete
```

### Plan File
```markdown
---
type: plan
task: Task Name
created: 2026-02-22
estimated_time: 30 minutes
status: in_progress
---

# Plan: Task Name

## Objective

Clear description of what needs to be accomplished.

## Steps

- [ ] Step 1: First action
- [ ] Step 2: Second action
- [ ] Step 3: Third action
- [ ] Step 4: Final action

## Dependencies

- Any blockers or prerequisites

## Notes

_Add notes during execution_

---
*Created by Silver Tier AI Employee*
```

### Approval Request File
```markdown
---
type: approval_request
action: email
to: recipient@example.com
subject: Email Subject
created: 2026-02-22T10:30:00
expires: 2026-02-23T10:30:00
status: pending
---

# Approval Request: Send Email

**Action:** Send Email  
**To:** recipient@example.com  
**Subject:** Email Subject  
**Created:** Timestamp  
**Expires:** Timestamp (24 hours)

---

## Email Content

Email body to be sent...

---

## To Approve

Move this file to `/Approved/` folder.

## To Reject

Move this file to `/Rejected/` folder.

---
*AI Employee will not send without approval*
```

### LinkedIn Post File
```markdown
---
type: linkedin_post
hashtags: #business, #ai, #automation
scheduled_time: 2026-02-22T09:00:00
---

# Post Content

Excited to share our latest AI automation project! 

Our Personal AI Employee system is now handling:
- Email triage and responses
- WhatsApp message monitoring
- LinkedIn content publishing
- Task management and planning

All while maintaining human oversight and approval for sensitive actions.

#AI #Automation #Productivity #Innovation

---
*Scheduled for automatic posting*
```

---

## Company Rules (from Company_Handbook.md)

### Communication Rules
- Always be polite and professional in all messages
- Respond to client messages within 24 hours
- Flag any unusual requests for human review

### Financial Rules
- Auto-approve recurring payments under $50
- **Flag ALL payments over $500 for human approval**
- Never send money to new/unknown recipients without approval

### Email Rules
- Draft replies for known contacts, but require approval before sending
- Never reply to bulk/marketing emails automatically

### Social Media Rules
- Only post pre-approved content automatically
- All replies and DMs require human approval

### Privacy Rules
- Never share client data with third parties
- Keep all sensitive files local

---

## Workflow Examples

### Email Processing Workflow

1. **Gmail Watcher** detects new important unread email
2. Creates `.md` file in `/Needs_Action/`
3. **Scheduler** (every 2 min) moves file to `/In_Progress/`
4. **Scheduler** triggers Qwen Code to process
5. Qwen Code:
   - Reads email content
   - Creates `PLAN_<task>_<date>.md` in `/Plans/`
   - If reply needed, drafts in `/Pending_Approval/`
   - Updates `Dashboard.md`
6. Human reviews draft
7. Human moves to `/Approved/` to send OR `/Rejected/` to discard
8. **Email MCP Server** sends approved emails
9. File moved to `/Sent/` or `/Rejected/`
10. Original task moved to `/Done/`

### WhatsApp Processing Workflow

1. **WhatsApp Watcher** detects message with urgent keywords
2. Creates `.md` file in `/Needs_Action/`
3. **Scheduler** processes same as email workflow
4. Human responds via appropriate channel

### LinkedIn Posting Workflow

1. Human or AI creates post in `/Social/LinkedIn_Queue/`
2. **LinkedIn Poster** (every 5 min) checks queue
3. If post found and not DRY_RUN:
   - Logs in to LinkedIn via Playwright
   - Posts content with hashtags
   - Moves file to `/Social/LinkedIn_Posted/`
   - Logs in `/Logs/linkedin_posts.json`
4. Updates `Dashboard.md`

### Daily Briefing (8:00 AM)

1. **Scheduler** triggers at 8:00 AM
2. Generates daily briefing in `/Briefings/`
3. Includes:
   - Task overview (pending, in progress, done)
   - Emails sent today
   - Priorities for today
   - Recent activity
4. Updates `Dashboard.md`

### Weekly Summary (Sunday 9:00 PM)

1. **Scheduler** triggers Sunday 9:00 PM
2. Generates weekly summary in `/Briefings/`
3. Includes:
   - Tasks completed this week
   - Emails sent this week
   - Plans created
   - Next week's focus
4. Updates `Dashboard.md`

---

## Configuration

### Environment Variables (.env)

```bash
# Gmail API
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_CHECK_INTERVAL=120
MAX_EMAILS_PER_HOUR=10

# LinkedIn
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_CHECK_INTERVAL=300

# WhatsApp
WHATSAPP_SESSION_PATH=./whatsapp_session
WHATSAPP_CHECK_INTERVAL=60

# General
VAULT_PATH=./AI_Employee_Vault
DRY_RUN=true
PAYMENT_APPROVAL_THRESHOLD=500
SCHEDULER_CHECK_INTERVAL=120
```

### Important Settings

- **DRY_RUN=true**: Prevents actual email sending and LinkedIn posting
- **Set DRY_RUN=false** only when ready to go live
- **PAYMENT_APPROVAL_THRESHOLD=500**: Flags payments over $500

---

## Commands

### Start All Watchers (Windows)
```batch
start_silver.bat
```

### Start Individual Services
```bash
# Gmail Watcher
python gmail_watcher.py

# WhatsApp Watcher
python whatsapp_watcher.py

# File System Watcher
python filesystem_watcher.py

# Scheduler
python scheduler.py

# LinkedIn Poster
python linkedin_poster.py

# Email MCP Server
python email_mcp_server.py
```

### Install Dependencies
```bash
# Bronze Tier
pip install -r requirements.txt

# Silver Tier additions
pip install -r requirements_silver.txt

# Install Playwright browsers
playwright install
```

---

## Monitoring

### Dashboard.md

The central monitoring hub showing:
- Pending Actions count
- Plans in Progress count
- Pending Approvals count
- Completed Today count
- Emails Sent Today count
- LinkedIn Posts This Week count
- Gmail Status
- WhatsApp Status
- LinkedIn Status
- Email Status
- Recent Activity
- Alerts

### Logs

All activity is logged to `/Logs/`:
- `gmail_watcher.log` - Gmail monitoring
- `whatsapp_watcher.log` - WhatsApp monitoring
- `linkedin_poster.log` - LinkedIn posting
- `email_mcp.log` - Email sending
- `scheduler.log` - Scheduler activity
- `sent_emails.json` - Sent email records
- `linkedin_posts.json` - LinkedIn post records
- `scheduler_state.json` - Scheduler state

---

## Troubleshooting

### Gmail Watcher Not Working
1. Check `credentials.json` exists in `AI_Employee_Vault/`
2. Ensure Gmail API is enabled in Google Cloud Console
3. Delete `token.json` and re-authenticate
4. Check `Logs/gmail_watcher.log` for errors

### WhatsApp Watcher Not Working
1. First run: May need to scan QR code manually
2. Check `whatsapp_session/` folder exists
3. Ensure Playwright is installed: `playwright install`
4. Check `Logs/whatsapp_watcher.log` for errors

### LinkedIn Poster Not Working
1. Log in to LinkedIn manually first to create session
2. Check `linkedin_session/` folder exists
3. Ensure DRY_RUN=false for actual posting
4. Check `Logs/linkedin_poster.log` for errors

### Scheduler Not Triggering Qwen
1. Ensure Qwen Code is installed: `qwen --version`
2. Check `Logs/scheduler.log` for errors
3. Verify vault path is correct

### Emails Not Sending
1. Check `DRY_RUN` setting in `.env`
2. Verify Gmail credentials have send scope
3. Check file is in `/Approved/` not `/Pending_Approval/`
4. Check `Logs/email_mcp.log` for errors

---

## Security Notes

- **Never commit** `.env`, `credentials.json`, or `token.json`
- Keep your vault local and backed up
- Review all actions in `/Logs/` regularly
- Rotate API credentials monthly
- Use DRY_RUN mode until fully tested
- Always review approval files before moving to `/Approved/`

---

## Upgrade Path

### To Gold Tier
Add:
- Odoo accounting integration
- Facebook/Instagram integration
- Twitter/X integration
- Weekly Business and Accounting Audit
- Error recovery and graceful degradation
- Ralph Wiggum loop for autonomous multi-step completion

### To Platinum Tier
Add:
- Cloud deployment for 24/7 operation
- Work-Zone Specialization (Cloud vs Local)
- Vault sync between Cloud and Local
- HTTPS, backups, health monitoring

---

*Silver Tier AI Employee Skill - Built for the Personal AI Employee Hackathon 2026*
