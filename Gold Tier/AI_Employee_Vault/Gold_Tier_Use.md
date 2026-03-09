# 🥇 Gold Tier — Complete Usage Guide
> AI Employee Gold Tier — Step by Step Usage
> **Last Updated:** 2026-03-09
> **Dashboard Version:** Advanced Gold Tier v2.0

---

## 📁 Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md                  ← Main screen (Advanced Dashboard) ⭐
├── Company_Handbook.md           ← AI rules
├── Business_Goals.md             ← Business targets
├── Gold_Tier_Use.md              ← This guide
│
├── Needs_Action/                 ← All incoming tasks
├── Plans/                        ← AI plans
├── Done/                         ← Completed tasks
├── Pending_Approval/
│   └── ODOO/                     ← Odoo approval requests
├── Approved/                     ← Approved actions
├── Rejected/                     ← Rejected actions
├── In_Progress/                  ← Currently being worked on
│
├── Social/
│   ├── LinkedIn_Queue/           ← LinkedIn posts
│   └── Facebook_Queue/           ← Facebook posts
├── Briefings/                    ← CEO briefings
├── Accounting/                   ← Transactions
└── Logs/
    ├── audit/                    ← All actions logged
    └── errors/                   ← Error logs

Scripts:
├── gmail_watcher.py              ← Gmail monitor
├── whatsapp_watcher.py           ← WhatsApp monitor
├── filesystem_watcher.py         ← File monitor
├── linkedin_poster.py            ← LinkedIn auto post
├── facebook_manager.py           ← Facebook manager
├── email_mcp_server.py           ← Email sender
├── odoo_mcp_server.py            ← Odoo integration
├── scheduler.py                  ← Auto scheduler
├── ceo_briefing.py               ← CEO briefing generator
├── error_recovery.py             ← Error recovery
├── audit_logger.py               ← Audit logging
├── dashboard_manager.py          ← Dashboard updates ⭐
└── start_gold.bat                ← One click start ⭐

Infrastructure:
└── docker-compose.yml            ← Odoo Docker
```

---

## 🚀 Step 1 — Daily Startup

### 1.1 Docker Desktop Kholo:
1. Start menu mein **Docker Desktop** kholo
2. Green icon dikhne tak wait karo ✅

### 1.2 Odoo Start Karo:
Command Prompt mein:
```bash
cd "E:\Hackathone\Gold Tier"
docker-compose up -d
```

Phir browser mein check karo:
```
http://localhost:8069
```

### 1.3 start_gold.bat Double Click Karo:
```bash
start_gold.bat
```

**Yeh windows khulti hain:**
| Window | Service | Status |
|--------|---------|--------|
| 📧 | Gmail Watcher | Checks Gmail every 2 min |
| 💬 | WhatsApp Watcher | Monitors WhatsApp messages |
| 📂 | File System Watcher | Watches file changes |
| 💼 | LinkedIn Poster | Auto posts to LinkedIn |
| 📘 | Facebook Manager | Manages Facebook posts |
| 📨 | Email MCP Server | Sends approved emails |
| 🏢 | Odoo MCP Server | Accounting integration |
| ⏰ | Scheduler | Auto-schedules tasks |
| 🔄 | Error Recovery | Auto-restart on failures |
| 📊 | CEO Briefing | Weekly briefing generator |

### 1.4 Obsidian Kholo:
`Dashboard.md` kholo — complete status dekho

**New Dashboard Sections:**
- 📊 **Executive Summary** — Today, Week, Total metrics
- ⚡ **Live Status** — All 8 services real-time status
- 📥 **Action Queue** — Priority-based task tracking
- 📧 **Gmail Activity** — Emails processed, replies sent
- 💬 **WhatsApp Activity** — Messages, keywords detected
- 💼 **LinkedIn Activity** — Posts queue, published count
- 📘 **Facebook Activity** — Status, posts this week
- 🏢 **Odoo Accounting** — Invoices, revenue, actions
- 📋 **Recent Activity Log** — Last action timestamp
- 🚨 **Alerts & Errors** — System warnings
- 📅 **Scheduled Tasks** — Next run times
- 📈 **Weekly CEO Briefing** — Last generated, next briefing
- 🔒 **Security & Audit** — Log locations, retention

---

## 📧 Step 2 — Gmail Use Karna

### Automatic Process:
- Har **2 minute** mein Gmail check hota hai
- Important emails `Needs_Action/` mein save hoti hain
- Dashboard automatically update hota hai:
  - **Last Checked** time
  - **New Emails** count
  - **Processed This Hour** (limit: 50/hour)

### Email Reply Process:

**Qwen ko prompt do:**
```
Read all files in /Needs_Action folder.
Draft professional replies for each email.
Create approval files in /Pending_Approval folder.
Update Dashboard.md.
```

### Approve/Reject Flow:
1. `Pending_Approval/` mein file dekho
2. Content review karo
3. **Approve:** `Approved/` mein move karo → email bhej dega ✅
4. **Reject:** `Rejected/` mein move karo → skip karega ✅

### Dashboard Metrics:
| Metric | Description |
|--------|-------------|
| Last Checked | Last Gmail check time |
| New Emails | Unread important emails found |
| Processed This Hour | Emails processed (max 50/hour) |
| Replies Drafted | Pending approval replies |
| Replies Sent | Approved emails sent today |

---

## 💼 Step 3 — LinkedIn Post Karna

### Process:
1. `Social/LinkedIn_Queue/` mein file banao:
   ```
   post_001.md
   ```

2. Content likho:
   ```markdown
   ---
   type: linkedin_post
   scheduled: 2026-03-09
   hashtags: AI, Business, Automation
   ---
   
   AI Employee Gold Tier complete!
   
   #AI #Business #Automation
   ```

3. **60 seconds** mein post ho jayegi! ✅

### Dashboard Updates:
| Metric | Updates When |
|--------|--------------|
| Last Post | After successful post |
| Posts This Week | Increments on post |
| Posts in Queue | Real-time queue count |
| Total Posts | Lifetime posts count |
| DRY_RUN | Yes/No (test mode) |

---

## 🏢 Step 4 — Odoo Accounting Use Karna

### Important URLs:
| URL | Purpose |
|-----|---------|
| http://localhost:8069 | Odoo main dashboard |
| http://localhost:8069/odoo/accounting | Accounting module |
| http://localhost:8069/odoo/accounting/customer-invoices | Customer invoices |
| http://localhost:8069/odoo/contacts | Customers list |
| http://localhost:8069/odoo/accounting/vendor-bills | Vendor bills |

### Invoice Banana (Qwen se):

**Qwen ko prompt do:**
```
Create a new invoice in Odoo for:
Customer: Ali Khan
Amount: $500
Description: Consulting Services January

Create approval file in /Pending_Approval/ODOO/ folder.
Update Dashboard.md with Odoo status.
```

### Invoice Approve Karna:
1. `Pending_Approval/ODOO/` mein file dekho
2. Details check karo (customer, amount, description)
3. `Approved/ODOO/` mein move karo
4. Odoo MCP automatically invoice post karega ✅

### Odoo Browser mein Check Karo:
```
http://localhost:8069/odoo/accounting/customer-invoices
```
Invoice wahan dikhegi! ✅

### Dashboard Metrics:
| Metric | Description |
|--------|-------------|
| Connection | Odoo connection status |
| Server | Odoo URL (localhost:8069) |
| Database | Database name (ai_employee) |
| Draft Invoices | Pending draft invoices |
| Paid This Week | Revenue this week |
| Total Revenue MTD | Month-to-date revenue |
| Actions Today | Odoo actions executed |
| DRY_RUN | Test mode status |

---

## 📊 Step 5 — CEO Briefing

### Manually Generate Karo:
```bash
python AI_Employee_Vault/generate_ceo_briefing_now.py
```

### Automatically:
- Har **Sunday 9 PM** automatically generate hoti hai
- Location: `Briefings/CEO_Briefing_YYYY-MM-DD.md`

### Briefing Mein Kya Hota Hai:
- ✅ Revenue this week
- ✅ Completed tasks summary
- ✅ Gmail activity report
- ✅ LinkedIn posts published
- ✅ Odoo invoices status
- ✅ Proactive suggestions for next week

### Dashboard Updates:
| Metric | Updates When |
|--------|--------------|
| Last Generated | After briefing creation |
| Location | Briefing file path |
| Next Briefing | Next Sunday 9:00 PM |

---

## 📂 Step 6 — File Drop Karna

### Quick File Processing:
1. `Drop_Here/` mein file daalo
2. Automatically `Needs_Action/` mein aa jayegi
3. Qwen Code automatically process karega
4. Dashboard **Action Queue** update hoga

### Action Queue Priorities:
| Priority | Folder | Description |
|----------|--------|-------------|
| 🔴 High | `Needs_Action/` | Urgent tasks |
| 🟡 Medium | `In_Progress/` | Being worked on |
| 🟢 Low | `Pending_Approval/` | Awaiting approval |

---

## 🌅 Rozana Ka Schedule

| Waqt | Kaam | Dashboard Section |
|------|------|-------------------|
| Subah 9 AM | Docker Desktop kholo | ⚡ Live Status |
| Subah 9 AM | `docker-compose up -d` | 🏢 Odoo Connection |
| Subah 9 AM | `start_gold.bat` chalao | All services start |
| Subah 9 AM | `Dashboard.md` check karo | 📊 Executive Summary |
| Email aaye | `Needs_Action` dekho | 📧 Gmail Activity |
| Email reply | Qwen se reply banwao | 📥 Action Queue |
| LinkedIn | `LinkedIn_Queue` mein post | 💼 LinkedIn Activity |
| Invoice | Qwen se banwao → Approve | 🏢 Odoo Accounting |
| Sham 6 PM | `Briefings` check karo | 📈 CEO Briefing |
| Sunday 9 PM | CEO Briefing auto-generate | 📅 Scheduled Tasks |

---

## 🌐 Important URLs

| URL | Purpose |
|-----|---------|
| http://localhost:8069 | Odoo main dashboard |
| http://localhost:8069/odoo/accounting | Accounting module |
| http://localhost:8069/odoo/accounting/customer-invoices | Customer invoices |
| http://localhost:8069/odoo/contacts | Customers list |
| http://localhost:8069/odoo/accounting/vendor-bills | Vendor bills |
| https://gmail.com | Gmail check |
| https://linkedin.com | LinkedIn check |
| https://developers.google.com | Gmail API manage |
| https://developer.linkedin.com | LinkedIn API manage |

---

## ⚠️ Important Rules

### ✅ DO:
- ✅ Docker Desktop pehle kholo — phir bat file
- ✅ `docker-compose up -d` har din chalao
- ✅ `start_gold.bat` har din double click karo
- ✅ Terminals band mat karna (background mein chalte hain)
- ✅ `Pending_Approval` rozana check karo
- ✅ Odoo payments hamesha approve karo
- ✅ Dashboard.md regularly refresh karo (F5)
- ✅ `Gold_Tier_Use.md` refer karo for help

### ❌ DON'T:
- ❌ `.env` file share mat karo
- ❌ Odoo password share mat karo
- ❌ Docker band mat karo jab Odoo use ho raha ho
- ❌ `start_gold.bat` multiple times mat chalao
- ❌ Log files delete mat karo (90 days retention)

---

## 🔧 Troubleshooting

| Problem | Solution | Dashboard Indicator |
|---------|----------|---------------------|
| Odoo nahi khul raha | `docker-compose up -d` chalao | 🔴 Odoo Status |
| Gmail emails nahi aa rahe | Gmail mein "Important" mark karo | 🟡 Gmail Status |
| LinkedIn error | Token expire — `python linkedin_poster.py` chalao | 🔴 LinkedIn Status |
| Odoo invoice nahi bani | `python odoo_mcp_server.py` chalao | 🔴 Odoo Status |
| Dashboard update nahi | Scheduler window check karo | 🟡 Scheduler Status |
| Service crash ho | `error_recovery.py` auto restart karega | 🚨 Alerts section |
| CEO Briefing nahi bani | `python ceo_briefing.py` manually chalao | 📅 Scheduled Tasks |
| Facebook post fail | API token refresh karo | 🔴 Facebook Status |

### Error Recovery:
- **Auto-restart:** 30 seconds after crash
- **Error logging:** `/Logs/errors/` folder
- **Alert system:** Dashboard 🚨 section
- **Retry logic:** 5 retries before giving up

---

## 📊 Gold Tier Capabilities

| Feature | Status | Description |
|---------|--------|-------------|
| ✅ Gmail auto monitor | Active | Checks every 2 minutes |
| ✅ Email auto reply + approval | Active | Draft + approve flow |
| ✅ LinkedIn auto post | Active | Queue-based posting |
| ✅ Facebook auto post | Active | API + Playwright fallback |
| ✅ Odoo accounting | Active | Invoices, customers, payments |
| ✅ CEO Briefing | Active | Weekly auto-generate |
| ✅ Auto scheduler | Active | Task scheduling |
| ✅ Error recovery | Active | Auto-restart on failures |
| ✅ Audit logging | Active | 90 days record |
| ✅ Docker integration | Active | Odoo always running |
| ✅ Dashboard updates | Active | Real-time metrics |

---

## 🔄 Agar Sab Band Kar Diya — Dobara Start Karna:

### Complete Restart Process:

```bash
# Step 1: Docker Desktop kholo
# Wait for green icon ✅

# Step 2: Odoo restart
cd "E:\Hackathone\Gold Tier"
docker-compose up -d

# Step 3: Check Odoo
# Browser: http://localhost:8069

# Step 4: Start all services
start_gold.bat

# Step 5: Open Dashboard
# Obsidian: Dashboard.md
```

### Verify All Services:
Check Dashboard **⚡ Live Status** section:
- All services should show 🟢 Running
- Last Active times should be current
- No alerts in 🚨 Alerts section

---

## 📈 Dashboard Metrics Explained

### Executive Summary:
| Metric | Today | This Week | Total |
|--------|-------|-----------|-------|
| ✉️ Emails Processed | New emails today | This week count | Lifetime total |
| 📤 Emails Sent | Sent today | Sent this week | All time sent |
| 💼 LinkedIn Posts | Posts today | Posts this week | Total published |
| 📘 Facebook Posts | Posts today | Posts this week | Total published |
| 🧾 Odoo Invoices | Invoices today | Invoices this week | Total invoices |
| ✅ Tasks Completed | Done today | Done this week | Lifetime tasks |

### Live Status Icons:
- 🟢 **Running** — Service active and healthy
- 🟡 **Idle** — Service waiting for work
- 🔴 **Skip/Stopped** — Service disabled or error
- ⚪ **Unknown** — Status not determined

---

## 🎯 Quick Reference Commands

### Start Services:
```bash
start_gold.bat
```

### Stop All Services:
```bash
# Close all terminal windows
docker-compose down
```

### Check Logs:
```bash
# Gmail
type Logs\gmail_watcher.log

# LinkedIn
type Logs\linkedin_posts.log

# Odoo
type Logs\odoo_mcp.log

# Errors
type Logs\errors\*.log
```

### Manual Service Start:
```bash
python AI_Employee_Vault/gmail_watcher.py
python AI_Employee_Vault/linkedin_poster.py
python AI_Employee_Vault/odoo_mcp_server.py
python AI_Employee_Vault/scheduler.py
python AI_Employee_Vault/ceo_briefing.py
python AI_Employee_Vault/error_recovery.py
```

### Generate Briefing:
```bash
python AI_Employee_Vault/generate_ceo_briefing_now.py
```

---

## 📞 Support & Resources

### Documentation:
- `README_GOLD.md` — Gold Tier overview
- `INSTALLATION_CHECKLIST_GOLD.md` — Setup checklist
- `Company_Handbook.md` — AI rules and guidelines
- `Business_Goals.md` — Business objectives

### Log Locations:
- Audit Logs: `/Logs/audit/`
- Error Logs: `/Logs/errors/`
- Service Logs: `/Logs/*.log`

### Backup Important Files:
- `.env` — Environment variables (KEEP SECRET!)
- `credentials.json` — Gmail API credentials
- `token.json` — Gmail OAuth token
- `Business_Goals.md` — Your business targets

---

*🥇 Gold Tier — Autonomous AI Employee*
*Powered by Qwen Code | Built with ❤️ by Ali Asghar*
