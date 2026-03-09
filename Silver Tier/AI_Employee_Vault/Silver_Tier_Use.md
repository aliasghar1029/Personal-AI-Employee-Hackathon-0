# 🥈 Silver Tier — Complete Usage Guide
> AI Employee Silver Tier — Step by Step

---

## 📁 Folder Structure
```
AI_Employee_Vault/
├── Dashboard.md              ← Main screen
├── Company_Handbook.md       ← AI rules
├── Needs_Action/             ← All incoming tasks
├── Plans/                    ← AI plans
├── Done/                     ← Completed tasks
├── Pending_Approval/         ← Waiting for approval
├── Approved/                 ← Approved actions
├── Rejected/                 ← Rejected actions
├── In_Progress/              ← Currently being worked on
├── Social/
│   └── LinkedIn_Queue/       ← LinkedIn posts queue
├── Briefings/                ← Daily/weekly briefings
├── Accounting/               ← Bank transactions
└── Logs/                     ← Activity logs

gmail_watcher.py              ← Gmail monitor
whatsapp_watcher.py           ← WhatsApp monitor
filesystem_watcher.py         ← File monitor
linkedin_poster.py            ← LinkedIn auto post
email_mcp_server.py           ← Email sender
scheduler.py                  ← Auto scheduler
start_silver.bat              ← One click start ⭐
```

---

## 🚀 Step 1 — Daily Startup (Ek Click!)

### start_silver.bat Double Click Karo:
```
start_silver.bat
```

Yeh windows khulti hain:
- 📧 Gmail Watcher
- 💬 WhatsApp Watcher  
- 📂 File System Watcher
- 💼 LinkedIn Poster
- 📨 Email MCP Server
- ⏰ Scheduler

**Inhe band mat karna!** ✅

### Obsidian Kholo:
`Dashboard.md` kholo — status check karo

---

## 📧 Step 2 — Gmail Use Karna

### Automatic:
- Gmail Watcher har **2 minute** mein check karta hai
- Important email aaye toh automatically `Needs_Action` mein save hoti hai
- Terminal mein dikhega:
```
Found 1 new email(s) to process
Created action file: EMAIL_abc123.md
```

### Email Reply Karwana:
**Qwen ko prompt do:**
```
Read all files in /Needs_Action folder.
Draft professional replies for each email.
Create approval files in /Pending_Approval folder.
Update Dashboard.md.
```

### Email Approve Karna:
1. `Pending_Approval` folder mein file dekho
2. Reply pasand aaye → `Approved` folder mein move karo
3. Email MCP automatically bhej dega! ✅

---

## 💼 Step 3 — LinkedIn Post Karna

### Post Queue Mein Daalo:
1. `Social/LinkedIn_Queue/` folder mein file banao:
```
post_001.md
```
2. Andar yeh likho:
```
Aaj humne AI Employee complete kiya!
#AI #Technology #Business
```
3. **60 seconds** mein automatically post ho jayegi! ✅

### Terminal mein dikhega:
```
Found 1 post(s) in queue
Posting: post_001.md
LinkedIn post published successfully!
```

---

## 📂 Step 4 — File Drop Karna

1. `Drop_Here` folder mein file daalo
2. Automatically `Needs_Action` mein aa jayegi
3. Qwen ko prompt do process karne ke liye

---

## ✅ Step 5 — Approvals Manage Karna

### Check Karo:
`Pending_Approval` folder mein yeh types ki files aati hain:

| File Type | Matlab |
|-----------|--------|
| `REPLY_EMAIL_...md` | Email reply bhejni hai |
| `APPROVAL_...md` | Koi action karna hai |

### Process Karna:
- **Approve:** File → `Approved` folder mein move karo
- **Reject:** File → `Rejected` folder mein move karo

---

## ⏰ Step 6 — Scheduler Ka Kaam

Scheduler automatically yeh karta hai:

| Waqt | Kaam |
|------|------|
| Har 2 minute | `Needs_Action` check karta hai |
| Subah 8 baje | Daily briefing generate karta hai |
| Har Sunday 9 PM | Weekly summary banata hai |

---

## 🌅 Rozana Ka Schedule

| Waqt | Kaam |
|------|------|
| Subah | `start_silver.bat` double click |
| Obsidian kholo | `Dashboard.md` check karo |
| Gmail aaye | `Needs_Action` mein file dekho |
| Qwen ko prompt do | Reply draft karwao |
| Approve karo | `Pending_Approval` check karo |
| LinkedIn | `LinkedIn_Queue` mein post daalo |
| Sham | `Briefings` mein daily briefing dekho |

---

## 🌐 Important URLs

| URL | Kaam |
|-----|------|
| Gmail.com | Email check karna |
| linkedin.com | LinkedIn check karna |
| developers.google.com | Gmail API manage karna |
| developer.linkedin.com | LinkedIn API manage karna |

---

## ⚠️ Important Rules

- ✅ `start_silver.bat` har din chalao
- ✅ Terminals band mat karna
- ✅ `Pending_Approval` rozana check karo
- ✅ LinkedIn posts `LinkedIn_Queue` mein rakho
- ❌ `.env` file share mat karo
- ❌ `credentials.json` share mat karo
- ❌ `token.json` share mat karo

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Gmail emails nahi aa rahe | Gmail mein emails "Important" mark karo |
| LinkedIn post nahi ho rahi | Token expire — `python linkedin_poster.py` chalao |
| Email nahi gayi | `email_mcp_server.py` chal raha hai check karo |
| Dashboard update nahi | Scheduler chal raha hai check karo |
| Watcher band ho gaya | `start_silver.bat` dobara chalao |

---

## 📊 Silver Tier Capabilities

✅ Gmail auto monitor — emails automatically save hoti hain  
✅ Email auto reply — Qwen draft kare, aap approve karo  
✅ LinkedIn auto post — Queue mein rakho, post ho jayegi  
✅ File drop — Documents automatically process hote hain  
✅ Auto scheduler — Sab automatic check hota hai  
✅ Daily briefing — Har subah 8 baje  
✅ Weekly summary — Har Sunday  

❌ Odoo accounting — Gold mein  
❌ CEO Briefing — Gold mein  
❌ Facebook — Gold mein  

---

*🥈 Silver Tier — Intelligent AI Employee*
