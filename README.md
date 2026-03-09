# 🤖 Personal AI Employee — Complete Project Overview
> Hackathon 0: Building Autonomous FTEs in 2026
> **Developer: Ali Asghar**

---

## 🎯 Project Ka Maqsad

Yeh project ek **Digital FTE (Full-Time Employee)** banata hai jo:
- 24/7 kaam karta hai
- Emails automatically handle karta hai
- LinkedIn par posts karta hai
- Accounting manage karta hai
- Documents process karta hai
- Har action ke liye human approval leta hai

**Brain:** Qwen Code  
**Dashboard:** Obsidian  
**Storage:** Local folders (Obsidian Vault)

---

## 📁 Root Folder Structure

```
E:\Hackathone\
├── README.md                    ← Yeh file
├── Bronze Tier/                 ← Foundation
│   ├── AI_Employee_Vault/
│   └── Drop_Here/
├── Silver Tier/                 ← Smart Assistant  
│   ├── AI_Employee_Vault/
│   └── Drop_Here/
└── Gold Tier/                   ← Full Autonomous
    ├── AI_Employee_Vault/
    ├── Drop_Here/
    └── docker-compose.yml
```

---

# 🥉 BRONZE TIER

## Bronze mein Kya Bana?

### Files Banayi:
| File | Kaam |
|------|------|
| `Dashboard.md` | Main status screen Obsidian mein |
| `Company_Handbook.md` | AI ke liye rules aur guidelines |
| `filesystem_watcher.py` | `Drop_Here` folder monitor karta hai |
| `orchestrator.py` | Qwen ko manually trigger karta hai |
| `.qwen/skills/SKILL.md` | Qwen ko batata hai kaise kaam karna hai |

### Folders Banayi:
| Folder | Kaam |
|--------|------|
| `Needs_Action/` | Naye kaam yahan aate hain |
| `Plans/` | AI yahan plans banata hai |
| `Done/` | Complete kaam yahan jata hai |
| `Pending_Approval/` | AI yahan approval maangta hai |
| `Approved/` | Aap yahan approve karte ho |
| `Rejected/` | Aap yahan reject karte ho |
| `Inbox/` | General inbox |
| `Logs/` | Activity logs |
| `Drop_Here/` | Files yahan daalo — watcher detect karta hai |

## Bronze Kaise Kaam Karta Hai?

```
1. Drop_Here/ mein file daalo
        ↓
2. filesystem_watcher.py detect karta hai
        ↓
3. Needs_Action/ mein .md file banti hai
        ↓
4. Qwen padhta hai aur Plans/ mein plan banata hai
        ↓
5. Sensitive action ho toh Pending_Approval/ mein file banti hai
        ↓
6. Aap Approved/ ya Rejected/ mein move karte ho
        ↓
7. Kaam complete → Done/ mein move hota hai
```

## Bronze Start Karna:
```bash
cd "Bronze Tier\AI_Employee_Vault"
python filesystem_watcher.py
```

---

# 🥈 SILVER TIER

## Silver mein Bronze ke Upar Kya Add Hua?

### Nayi Files:
| File | Kaam |
|------|------|
| `gmail_watcher.py` | Har 2 min Gmail check karta hai |
| `linkedin_poster.py` | LinkedIn par auto post karta hai |
| `email_mcp_server.py` | Approved emails automatically bhejta hai |
| `whatsapp_watcher.py` | WhatsApp urgent messages monitor karta hai |
| `scheduler.py` | Sab kuch auto schedule karta hai |
| `start_silver.bat` | Ek click mein sab start |
| `requirements_silver.txt` | Extra Python packages |
| `README_SILVER.md` | Silver setup guide |

### Nayi Folders:
| Folder | Kaam |
|--------|------|
| `Social/LinkedIn_Queue/` | LinkedIn posts yahan rakho |
| `Briefings/` | Daily aur weekly briefings |
| `Accounting/` | Bank transactions |
| `In_Progress/` | Kaam chal raha hai |

### APIs Setup Kiye:
| API | Platform | Kaam |
|-----|----------|------|
| Gmail API | Google Cloud Console | Emails padhna aur bhejna |
| LinkedIn API | LinkedIn Developer | Posts karna |

## Silver Kaise Kaam Karta Hai?

### Gmail Flow:
```
Gmail mein naya email aata hai
        ↓
gmail_watcher.py detect karta hai (har 2 min)
        ↓
Needs_Action/ mein EMAIL_xxx.md banti hai
        ↓
Qwen professional reply draft karta hai
        ↓
Pending_Approval/ mein REPLY_EMAIL_xxx.md banti hai
        ↓
Aap Approved/ mein move karte ho
        ↓
email_mcp_server.py automatically email bhejta hai ✅
```

### LinkedIn Flow:
```
Social/LinkedIn_Queue/ mein post.md file rakho
        ↓
linkedin_poster.py detect karta hai (har 60 sec)
        ↓
LinkedIn par automatically post ho jati hai ✅
        ↓
File Done/ mein move hoti hai
        ↓
Dashboard.md update hota hai
```

### Scheduler Flow:
```
Har 2 minute → Needs_Action check
Subah 8 baje → Daily briefing generate
Har Sunday 9 PM → Weekly summary
```

## Silver Start Karna:
```bash
# Double click karo:
start_silver.bat
```

## Silver Important URLs:
| URL | Kaam |
|-----|------|
| gmail.com | Gmail check karna |
| linkedin.com | LinkedIn posts dekhna |
| console.cloud.google.com | Gmail API manage |
| developer.linkedin.com | LinkedIn API manage |

---

# 🥇 GOLD TIER

## Gold mein Silver ke Upar Kya Add Hua?

### Nayi Files:
| File | Kaam |
|------|------|
| `facebook_poster.py` | Facebook Graph API se post karta hai |
| `facebook_playwright.py` | Playwright se Facebook automate karta hai |
| `facebook_manager.py` | API ya Playwright — smart fallback |
| `odoo_mcp_server.py` | Odoo se connect karta hai — invoices banata hai |
| `ceo_briefing.py` | Har Sunday CEO briefing generate karta hai |
| `error_recovery.py` | Koi service crash ho toh auto restart |
| `audit_logger.py` | Har action ka 90 din ka record |
| `docker-compose.yml` | Odoo Docker setup |
| `start_gold.bat` | Ek click mein sab 10 services start |
| `requirements_gold.txt` | Gold tier packages |
| `README_GOLD.md` | Gold setup guide |

### Nayi Folders:
| Folder | Kaam |
|--------|------|
| `Social/Facebook_Queue/` | Facebook posts yahan rakho |
| `Pending_Approval/ODOO/` | Odoo invoices approval |
| `Logs/audit/` | Har action ka JSON log |
| `Logs/errors/` | Error logs |
| `facebook_session/` | Facebook browser session |

### Integrations:
| Service | Platform | Kaam |
|---------|----------|------|
| Odoo 18 | Docker (localhost:8069) | Accounting, invoices |
| Facebook | Playwright automation | Auto posts |
| CEO Briefing | Python scheduler | Weekly report |
| Audit Logger | JSON files | 90 day records |

## Gold Kaise Kaam Karta Hai?

### Odoo Invoice Flow:
```
Qwen ko prompt do: "Create invoice for Ali Khan $500"
        ↓
odoo_mcp_server.py Odoo se connect karta hai
        ↓
Pending_Approval/ODOO/ mein approval file banti hai
        ↓
Aap file Approved/ mein move karte ho
        ↓
Invoice Odoo mein automatically create hoti hai ✅
        ↓
Dashboard.md update hota hai
        ↓
Audit log mein record hota hai
```

### CEO Briefing Flow:
```
Har Sunday 9 PM scheduler trigger karta hai
        ↓
ceo_briefing.py chalti hai
        ↓
Business_Goals.md padhti hai
        ↓
Done/ folder se completed tasks count karta hai
        ↓
Accounting/ se revenue check karta hai
        ↓
Briefings/CEO_Briefing_YYYY-MM-DD.md generate hoti hai ✅
        ↓
Dashboard.md update hota hai
```

### Error Recovery Flow:
```
Koi service crash hoti hai
        ↓
error_recovery.py detect karta hai
        ↓
30 seconds baad auto restart karta hai ✅
        ↓
Logs/errors/ mein error record karta hai
```

## Gold Start Karna:
```bash
# Step 1: Docker start karo
cd "E:\Hackathone\Gold Tier"
docker-compose up -d

# Step 2: Odoo browser mein kholo
http://localhost:8069

# Step 3: Sab services start karo
# Double click:
start_gold.bat
```

## Gold Important URLs:
| URL | Kaam |
|-----|------|
| http://localhost:8069 | Odoo main dashboard |
| http://localhost:8069/odoo/accounting | Accounting module |
| http://localhost:8069/odoo/accounting/customer-invoices | Invoices list |
| http://localhost:8069/odoo/contacts | Customers list |
| gmail.com | Gmail check |
| linkedin.com | LinkedIn check |

## Gold Services (start_gold.bat se):
| Service | File | Kaam |
|---------|------|------|
| Gmail Watcher | gmail_watcher.py | Gmail monitor |
| WhatsApp Watcher | whatsapp_watcher.py | WhatsApp monitor |
| File Watcher | filesystem_watcher.py | Drop_Here monitor |
| LinkedIn Poster | linkedin_poster.py | LinkedIn auto post |
| Facebook Manager | facebook_manager.py | Facebook auto post |
| Email MCP | email_mcp_server.py | Email sender |
| Odoo MCP | odoo_mcp_server.py | Odoo integration |
| Scheduler | scheduler.py | Auto scheduler |
| CEO Briefing | ceo_briefing.py | Weekly report |
| Error Recovery | error_recovery.py | Auto restart |

---

# 📊 Teeno Tiers Ka Comparison

| Feature | 🥉 Bronze | 🥈 Silver | 🥇 Gold |
|---------|-----------|-----------|---------|
| File Processing | ✅ | ✅ | ✅ |
| Human Approval Flow | ✅ | ✅ | ✅ |
| Obsidian Dashboard | ✅ | ✅ | ✅ |
| Gmail Monitor | ❌ | ✅ | ✅ |
| Email Auto Reply | ❌ | ✅ | ✅ |
| LinkedIn Auto Post | ❌ | ✅ | ✅ |
| WhatsApp Monitor | ❌ | ✅ | ✅ |
| Auto Scheduler | ❌ | ✅ | ✅ |
| Daily Briefing | ❌ | ✅ | ✅ |
| Facebook Posts | ❌ | ❌ | ✅ |
| Odoo Accounting | ❌ | ❌ | ✅ |
| CEO Briefing | ❌ | ❌ | ✅ |
| Error Recovery | ❌ | ❌ | ✅ |
| Audit Logging | ❌ | ❌ | ✅ |
| Docker Support | ❌ | ❌ | ✅ |

---

# 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| 🧠 AI Brain | Qwen Code |
| 📊 Dashboard | Obsidian |
| 🐍 Backend | Python 3.13 |
| 👁️ Automation | Playwright |
| 🏢 Accounting | Odoo 18 Community |
| 🐳 Container | Docker Desktop |
| 📧 Email | Gmail API |
| 💼 LinkedIn | LinkedIn API |
| ⏰ Scheduler | Python schedule library |
| 🔌 Integration | Custom MCP Servers |

---

# 🔒 Security Rules

- ✅ `.env` file mein credentials — kabhi GitHub par nahi
- ✅ `.gitignore` mein: `.env`, `credentials.json`, `token.json`
- ✅ Sensitive actions hamesha approval se
- ✅ Odoo payments hamesha manual approve
- ✅ Audit logs 90 din tak
- ❌ Kabhi credentials share mat karo

---

# 🚀 Teeno Tiers Ka Rozana Use

## 🥉 Bronze Rozana:
```
1. python filesystem_watcher.py chalao
2. Obsidian mein Dashboard.md kholo
3. Drop_Here mein files daalo
4. Qwen ko prompt do process karne ke liye
5. Pending_Approval check karo
```

## 🥈 Silver Rozana:
```
1. start_silver.bat double click
2. Dashboard.md check karo
3. Emails aayengi automatically Needs_Action mein
4. Qwen se reply draft karwao
5. Approved/ mein move karo → email chali jayegi
6. LinkedIn_Queue mein post rakho → auto post
```

## 🥇 Gold Rozana:
```
1. Docker Desktop kholo
2. docker-compose up -d chalao
3. start_gold.bat double click
4. Dashboard.md check karo
5. Emails → Qwen reply → Approve
6. Invoices → Qwen banaye → Approve → Odoo mein
7. LinkedIn_Queue mein post → auto post
8. Sunday → CEO Briefing check karo
```

---

*🤖 Personal AI Employee Hackathon 0 — Built with Qwen Code*  
*👨‍💻 Developer: Ali Asghar | March 2026*
