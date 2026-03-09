# 🥉 Bronze Tier — Complete Usage Guide
> AI Employee Bronze Tier — Step by Step Usage

---

## 📁 Folder Structure
```
AI_Employee_Vault/
├── Dashboard.md          ← Main screen — open this in Obsidian
├── Company_Handbook.md   ← AI rules
├── Needs_Action/         ← Incoming tasks land here
├── Plans/                ← AI creates plans here
├── Done/                 ← Completed tasks go here
├── Pending_Approval/     ← AI asks permission here
├── Approved/             ← You approve tasks here
├── Rejected/             ← You reject tasks here
├── Inbox/                ← General inbox
└── Logs/                 ← Activity logs

Drop_Here/                ← Drop files here to trigger AI
filesystem_watcher.py     ← Monitors Drop_Here folder
orchestrator.py           ← Triggers Qwen manually
```

---

## 🚀 Step 1 — Daily Startup

### Obsidian Kholo:
1. Obsidian open karo
2. `AI_Employee_Vault` folder open karo as vault
3. `Dashboard.md` kholo — yahi aapka main screen hai

### Watcher Start Karo:
Command Prompt mein:
```
cd AI_Employee_Vault
python filesystem_watcher.py
```
Terminal band mat karna! ✅

---

## 📂 Step 2 — File Drop Karna

Koi bhi document process karwana ho:
1. `Drop_Here` folder kholo
2. File andar daalo — jaise PDF, Word, ya text file
3. **Automatically** `Needs_Action` mein `.md` file ban jayegi
4. Terminal mein yeh dikhega:
```
New file detected: document.pdf
Action file created: FILE_document.md
```

---

## 🤖 Step 3 — Qwen se Process Karwao

Jab `Needs_Action` mein file aa jaye:

**Qwen ko yeh prompt do:**
```
Read all files in /Needs_Action folder.
For each file create a plan in /Plans folder.
Update Dashboard.md with current status.
```

Qwen yeh karega:
- ✅ File padhega
- ✅ Plan banayega `/Plans` mein
- ✅ Dashboard update karega

---

## ✅ Step 4 — Approval Dena

Agar Qwen koi sensitive kaam karna chahta hai:
1. `Pending_Approval` folder kholo Obsidian mein
2. File padhو — kya action lena hai likha hoga
3. **Approve:** File cut karo → `Approved` folder mein paste karo
4. **Reject:** File cut karo → `Rejected` folder mein paste karo

---

## 📋 Step 5 — Done Folder Check Karo

Kaam complete hone par:

**Qwen ko yeh prompt do:**
```
Move all completed tasks from /Needs_Action 
and /Plans to /Done folder.
Update Dashboard.md.
```

---

## 🌅 Rozana Ka Schedule

| Waqt | Kaam |
|------|------|
| Subah | Obsidian mein `Dashboard.md` kholo |
| Koi file aaye | `Drop_Here` mein daalo |
| Qwen chalao | Needs_Action process karwao |
| Approval | `Pending_Approval` check karo |
| Raat | `Done` folder mein completed tasks dekho |

---

## ⚠️ Important Rules

- ❌ Terminal band mat karna — watcher band ho jayega
- ✅ Har roz `Dashboard.md` check karo
- ✅ `Pending_Approval` rozana check karo
- ❌ `.env` file kabhi share mat karna
- ✅ `Drop_Here` mein sirf safe files daalo

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Watcher chal nahi raha | `python filesystem_watcher.py` dobara chalao |
| Needs_Action mein file nahi aayi | `Drop_Here` folder check karo |
| Dashboard update nahi hua | Qwen ko prompt do: "Update Dashboard.md" |
| Plans nahi bane | Qwen ko prompt do needs_action process karne ke liye |

---

## 📊 Bronze Tier Capabilities

✅ File drop karo → Automatically detect ho  
✅ Qwen plan banaye → Step by step instructions  
✅ Human approval → Sensitive actions ke liye  
✅ Done tracking → Completed tasks ka record  
✅ Local storage → Sab data aapke computer par  

❌ Automatic email monitoring — Silver mein  
❌ LinkedIn posting — Silver mein  
❌ Auto scheduling — Silver mein  
❌ Odoo accounting — Gold mein  

---

*🥉 Bronze Tier — Foundation of AI Employee*
