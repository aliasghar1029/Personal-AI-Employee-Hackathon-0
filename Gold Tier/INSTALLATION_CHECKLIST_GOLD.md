# Gold Tier Installation Checklist

Use this checklist to ensure all Gold Tier components are properly installed and configured.

---

## Pre-Installation (Complete First)

- [ ] Bronze Tier installed and working
- [ ] Silver Tier installed and working
- [ ] All Silver Tier services run without errors
- [ ] Dashboard.md updates correctly

---

## Step 1: Install Gold Tier Dependencies

- [ ] Run: `pip install -r requirements_gold.txt`
- [ ] Verify facebook-sdk installed: `pip show facebook-sdk`
- [ ] Verify Playwright installed: `playwright --version`
- [ ] Install Playwright browsers: `playwright install`

---

## Step 2: Install Docker Desktop (for Odoo)

- [ ] Download Docker Desktop for Windows
- [ ] Install Docker Desktop
- [ ] Start Docker Desktop
- [ ] Verify Docker running: `docker --version`
- [ ] Verify Docker Compose: `docker-compose --version`

---

## Step 3: Configure Environment Variables

- [ ] Copy `.env.example` to `.env`
- [ ] Configure Facebook API credentials (Method A):
  - [ ] FACEBOOK_APP_ID
  - [ ] FACEBOOK_APP_SECRET
  - [ ] FACEBOOK_PAGE_ID
  - [ ] FACEBOOK_PAGE_ACCESS_TOKEN
- [ ] Configure Facebook Playwright (Method B):
  - [ ] FACEBOOK_EMAIL
  - [ ] FACEBOOK_PASSWORD
- [ ] Configure Odoo credentials:
  - [ ] ODOO_URL=http://localhost:8069
  - [ ] ODOO_DB=ai_employee
  - [ ] ODOO_USERNAME=admin
  - [ ] ODOO_PASSWORD=admin
- [ ] Set DRY_RUN=true (for testing)

---

## Step 4: Start Odoo (Optional - for Accounting)

- [ ] Run: `docker-compose up -d`
- [ ] Verify Odoo running: `docker-compose ps`
- [ ] Open browser: http://localhost:8069
- [ ] Create database: ai_employee
- [ ] Login with admin/admin
- [ ] Install Accounting module
- [ ] Test Odoo connection

---

## Step 5: Create Required Folders

- [ ] AI_Employee_Vault/Social/Facebook_Queue/
- [ ] AI_Employee_Vault/Social/Facebook_Posted/
- [ ] AI_Employee_Vault/Logs/audit/
- [ ] AI_Employee_Vault/Logs/errors/
- [ ] AI_Employee_Vault/Pending_Approval/ODOO/
- [ ] AI_Employee_Vault/Approved/ODOO/
- [ ] AI_Employee_Vault/Rejected/ODOO/
- [ ] AI_Employee_Vault/Done/ODOO/
- [ ] facebook_session/

**Or run:** Folders are created automatically by start_gold.bat

---

## Step 6: Test Individual Services

### Facebook Manager
- [ ] Run: `python facebook_manager.py`
- [ ] Verify it starts without errors
- [ ] Check Facebook Status appears on Dashboard
- [ ] Create test post in Facebook_Queue
- [ ] Verify post is processed (in DRY_RUN mode)

### Odoo MCP Server
- [ ] Run: `python odoo_mcp_server.py`
- [ ] Verify connection to Odoo
- [ ] Check Odoo Status appears on Dashboard
- [ ] Test invoice creation (DRY_RUN mode)

### CEO Briefing Generator
- [ ] Run: `python ceo_briefing.py --generate-now`
- [ ] Verify briefing created in Briefings/
- [ ] Check briefing contains all sections
- [ ] Verify Dashboard updated

### Error Recovery System
- [ ] Run: `python error_recovery.py`
- [ ] Verify health checks run
- [ ] Check System Health section on Dashboard
- [ ] Verify error logging works

### Audit Logger
- [ ] Run: `python audit_logger.py`
- [ ] Verify audit logs created in Logs/audit/
- [ ] Check log format is correct

---

## Step 7: Start All Gold Tier Services

- [ ] Run: `start_gold.bat`
- [ ] Verify all 10 services start:
  - [ ] Gmail Watcher
  - [ ] File System Watcher
  - [ ] WhatsApp Watcher
  - [ ] LinkedIn Poster
  - [ ] Facebook Manager
  - [ ] Email MCP Server
  - [ ] Odoo MCP Server
  - [ ] Scheduler
  - [ ] CEO Briefing Generator
  - [ ] Error Recovery System

---

## Step 8: Verify Dashboard Updates

- [ ] Open Dashboard.md in Obsidian
- [ ] Verify all sections present:
  - [ ] Status
  - [ ] Gmail Status
  - [ ] WhatsApp Status
  - [ ] LinkedIn
  - [ ] Email Status
  - [ ] **Facebook Status** (Gold Tier)
  - [ ] **Odoo Status** (Gold Tier)
  - [ ] **System Health** (Gold Tier)
  - [ ] **Latest Briefing** (Gold Tier)
  - [ ] Quick Links (updated)

---

## Step 9: Test End-to-End Workflow

### Facebook Posting
- [ ] Create post in Facebook_Queue
- [ ] Verify Facebook Manager picks it up
- [ ] Check post moves to Facebook_Posted
- [ ] Verify Dashboard updated
- [ ] Check audit log created

### Odoo Invoice (if Odoo installed)
- [ ] Create invoice approval request
- [ ] Move to Approved/ODOO/
- [ ] Verify Odoo MCP processes it
- [ ] Check invoice created in Odoo
- [ ] Verify audit log created

### CEO Briefing
- [ ] Wait for Sunday 9 PM or run manually
- [ ] Verify briefing generated
- [ ] Check all data included
- [ ] Verify suggestions provided

---

## Step 10: Production Readiness

- [ ] Review all DRY_RUN settings
- [ ] Test with DRY_RUN=false for one service at a time
- [ ] Verify actual Facebook posts work
- [ ] Verify actual Odoo invoices work
- [ ] Check all error handling
- [ ] Review security settings
- [ ] Backup vault
- [ ] Document any custom configurations

---

## Troubleshooting

### Facebook API Errors
- Check credentials in .env
- Verify Page permissions granted
- Test token in Graph API Explorer

### Odoo Connection Errors
- Verify Docker running: `docker-compose ps`
- Check Odoo logs: `docker-compose logs odoo`
- Test connection: http://localhost:8069

### Service Won't Start
- Check Python version: `python --version`
- Verify dependencies: `pip list`
- Check logs in Logs/ folder

### Dashboard Not Updating
- Verify Scheduler running
- Check file permissions
- Restart services

---

## Final Verification

- [ ] All Gold Tier files created
- [ ] All folders created
- [ ] All services start without errors
- [ ] Dashboard updates correctly
- [ ] Audit logging works
- [ ] Error recovery monitors services
- [ ] Facebook posting works (DRY_RUN then live)
- [ ] Odoo integration works (if installed)
- [ ] CEO briefings generate correctly
- [ ] Documentation reviewed

---

## Next Steps

After completing Gold Tier:

1. **Monitor for a week** - Ensure stability
2. **Gradually enable live mode** - One service at a time
3. **Review audit logs daily** - Catch issues early
4. **Customize workflows** - Adapt to your needs
5. **Consider Platinum Tier** - Cloud deployment

---

**Gold Tier Complete!** ✅

Your AI Employee now has:
- Facebook Integration (API + Playwright)
- Odoo Accounting (via Docker)
- Weekly CEO Briefings
- Error Recovery & Health Monitoring
- Comprehensive Audit Logging

---
*Gold Tier v1.0.0 - Personal AI Employee Hackathon 2026*
