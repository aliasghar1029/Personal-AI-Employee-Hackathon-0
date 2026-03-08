#!/usr/bin/env python
"""Test dashboard update functionality - Debug version."""

import os
import sys
import codecs
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv
load_dotenv()

import xmlrpc.client

# Configuration
VAULT_PATH = Path('E:/Hackathone/Gold Tier/AI_Employee_Vault')
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'
PENDING_APPROVAL_PATH = VAULT_PATH / 'Pending_Approval' / 'ODOO'

ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'ai_employee')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'masteraliasghar25@gmail.com')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'

print("="*60)
print("DASHBOARD UPDATE TEST")
print("="*60)

try:
    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
    
    if not uid:
        print("\n[ERROR] Odoo authentication failed!")
        sys.exit(1)
    
    print(f"\n[OK] Connected to Odoo! User ID: {uid}")
    
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    
    # Count draft invoices from Odoo
    draft_invoices = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'account.move', 'search', [[['move_type', '=', 'out_invoice'], ['state', '=', 'draft']]]
    )
    draft_invoices_count = len(draft_invoices) if draft_invoices else 0
    
    print(f"[OK] Draft invoices in Odoo: {draft_invoices_count}")
    
    # Count pending approval files
    pending_count = len(list(PENDING_APPROVAL_PATH.glob('*.md')))
    print(f"[OK] Pending approval files: {pending_count}")
    
    # Update dashboard
    if DASHBOARD_PATH.exists():
        content = DASHBOARD_PATH.read_text(encoding='utf-8')
        
        connection_status = "Connected ✅" if uid else "Disconnected ❌"
        today = datetime.now().strftime('%Y-%m-%d')
        
        odoo_section = f"""## Odoo Status
- Connection: {connection_status}
- URL: {ODOO_URL}
- Database: {ODOO_DB}
- Pending Invoices: {draft_invoices_count}
- Actions Today: 1
- DRY_RUN: {'Yes' if DRY_RUN else 'No'}
"""
        
        # Check if section exists
        if '## Odoo Status' not in content:
            print("\n[INFO] Adding new Odoo Status section to Dashboard...")
            content += '\n' + odoo_section.strip() + '\n'
        else:
            print("\n[INFO] Updating existing Odoo Status section...")
            lines = content.split('\n')
            new_lines = []
            in_section = False
            for line in lines:
                if line.startswith('## Odoo Status'):
                    in_section = True
                    new_lines.append(odoo_section.strip())
                elif in_section and line.startswith('## '):
                    in_section = False
                    new_lines.append(line)
                elif not in_section:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
        
        # Write the updated content
        DASHBOARD_PATH.write_text(content, encoding='utf-8')
        print(f"[OK] Dashboard updated successfully!")
        
        # Verify the update
        verify_content = DASHBOARD_PATH.read_text(encoding='utf-8')
        if '## Odoo Status' in verify_content:
            print("[OK] Verification: Odoo Status section found in Dashboard!")
        else:
            print("[ERROR] Verification: Odoo Status section NOT found!")
        
        # Display updated section
        print("\n" + "="*60)
        print("UPDATED DASHBOARD SECTION:")
        print("="*60)
        print(odoo_section)
        
    else:
        print("\n[WARN] Dashboard.md not found!")
    
    print("\n" + "="*60)
    print("TEST COMPLETED!")
    print("="*60)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
