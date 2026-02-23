# Personal AI Employee - Bronze Tier

A local-first, agent-driven Personal AI Employee system built with Qwen Code and Obsidian.

## Overview

This system acts as your digital Full-Time Equivalent (FTE), monitoring your communications and files, creating action plans, and managing tasks with human-in-the-loop approval for sensitive actions.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Gmail/File    │────▶│   Watcher Scripts │────▶│  Needs_Action/  │
│    Sources      │     │   (Python)        │     │   (Markdown)    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  External Actions│◀────│   Qwen Code      │◀────│  Company        │
│  (via MCP)       │     │   (Reasoning)    │     │  Handbook.md    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Folder Structure

```
AI_Employee_Vault/
├── Inbox/              # Raw incoming items
├── Needs_Action/       # Items requiring action (Watcher drops here)
├── Plans/              # Created plans with step-by-step checkboxes
├── Done/               # Completed tasks
├── Logs/               # Activity logs
├── Pending_Approval/   # Awaiting human approval
├── Approved/           # Human-approved actions
├── Rejected/           # Human-rejected actions
├── Dashboard.md        # Real-time status summary
├── Company_Handbook.md # Rules of engagement
└── .qwen/
    └── skills/
        └── ai-employee/
            └── SKILL.md # Agent skill definition
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Gmail API (Optional - for Gmail Watcher)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download as `credentials.json` and place in project root

### 3. Initialize the Vault

Open the `AI_Employee_Vault` folder in Obsidian to set it as your vault.

### 4. Start a Watcher

**Option A: Gmail Watcher** (requires Gmail API setup)
```bash
python gmail_watcher.py
```

**Option B: File System Watcher** (simpler, no API setup)
```bash
python filesystem_watcher.py
```

### 5. Trigger Qwen Code

When files appear in `Needs_Action/`, run:
```bash
python orchestrator.py
```

Or manually invoke Qwen Code in the vault directory.

## Usage

### File System Watcher Workflow

1. Start the watcher: `python filesystem_watcher.py`
2. Drop any file into the `Drop_Here/` folder
3. The watcher creates a `.md` action file in `Needs_Action/`
4. Run `python orchestrator.py` to trigger Qwen Code
5. Qwen Code creates a plan in `Plans/` and updates `Dashboard.md`
6. Review and approve actions in `Pending_Approval/` if needed
7. Move completed items to `Done/`

### Gmail Watcher Workflow

1. Ensure `credentials.json` is configured
2. Start the watcher: `python gmail_watcher.py`
3. New important unread emails are saved to `Needs_Action/`
4. Run orchestrator to process emails
5. Review and approve draft replies

## Approval Workflow

For sensitive actions (payments, emails, etc.):

1. Qwen Code creates an approval file in `Pending_Approval/`
2. Review the file contents
3. **To Approve**: Move file to `Approved/` folder
4. **To Reject**: Move file to `Rejected/` folder
5. Orchestrator executes approved actions

## Company Rules

See `Company_Handbook.md` for full rules:

- **Financial**: Flag all payments over $500 for approval
- **Email**: Draft replies for known contacts, require approval before sending
- **Privacy**: Never share client data with third parties
- **Communication**: Respond within 24 hours, always be professional

## Automation (Optional)

### Windows Task Scheduler

To run watchers continuously:

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "At startup")
4. Action: `python.exe` with argument `filesystem_watcher.py`
5. Set "Start in" to project directory

### Using PM2 (Cross-platform)

```bash
npm install -g pm2
pm2 start filesystem_watcher.py --interpreter python
pm2 save
pm2 startup
```

## Security Notes

- **Never commit** `.env`, `credentials.json`, or `token.json`
- Keep your vault local and backed up
- Review all actions in `Logs/` regularly
- Rotate API credentials monthly

## Troubleshooting

**Watcher not detecting files?**
- Ensure the watcher script is running
- Check file permissions on Drop_Here folder

**Qwen Code not responding?**
- Verify Qwen Code is installed and accessible
- Check that the vault path is correct

**Gmail API errors?**
- Verify `credentials.json` is valid
- Ensure Gmail API is enabled in Google Cloud Console

## Next Steps (Silver/Gold Tier)

- Add WhatsApp watcher using Playwright
- Integrate MCP servers for email sending
- Add scheduled CEO Briefings
- Implement Odoo accounting integration
- Deploy to cloud for 24/7 operation

## License

This project is for educational and personal use as part of the Personal AI Employee Hackathon 2026.
