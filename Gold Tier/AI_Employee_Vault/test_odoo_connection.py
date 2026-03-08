#!/usr/bin/env python
"""Test Odoo connection and create test customer + draft invoice."""

import os
import sys
import xmlrpc.client
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Odoo Configuration
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'ai_employee')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')

# Paths
VAULT_PATH = Path(os.getenv('VAULT_PATH', './AI_Employee_Vault'))
PENDING_APPROVAL_PATH = Path('E:/Hackathone/Gold Tier/AI_Employee_Vault/Pending_Approval/ODOO')

def test_odoo_connection():
    """Test connection to Odoo and create test customer + draft invoice."""
    
    # Set UTF-8 encoding for Windows console
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    print("="*60)
    print("ODOO CONNECTION TEST")
    print("="*60)
    print(f"URL: {ODOO_URL}")
    print(f"Database: {ODOO_DB}")
    print(f"Username: {ODOO_USERNAME}")
    print("="*60)
    
    try:
        # Common endpoint for authentication
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        
        # Check server version
        version = common.version()
        print(f"\n[OK] Odoo server version: {version}")
        
        # Authenticate
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            print("\n[ERROR] Odoo authentication failed!")
            return None
        
        print(f"[OK] Authentication successful! User ID: {uid}")
        
        # Models endpoint for operations
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # ===========================================
        # Create Test Customer
        # ===========================================
        print("\n" + "="*60)
        print("CREATING TEST CUSTOMER")
        print("="*60)
        
        partner_name = "Test Client"
        partner_email = "testclient@example.com"
        
        # Check if partner already exists
        existing_partner_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'search', [[['email', '=', partner_email]]]
        )
        
        if existing_partner_ids:
            print(f"[WARN] Partner already exists with ID: {existing_partner_ids[0]}")
            partner_id = existing_partner_ids[0]
        else:
            # Create new partner
            partner_vals = {
                'name': partner_name,
                'email': partner_email,
            }
            
            partner_id = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'res.partner', 'create', [partner_vals]
            )
            print(f"[OK] Created new customer '{partner_name}' with ID: {partner_id}")
        
        # ===========================================
        # Create Draft Invoice
        # ===========================================
        print("\n" + "="*60)
        print("CREATING DRAFT INVOICE")
        print("="*60)
        
        amount = 100.0
        description = "Test Invoice - Gold Tier Odoo Integration"
        due_days = 30
        due_date = (datetime.now() + timedelta(days=due_days)).strftime('%Y-%m-%d')
        
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_date': datetime.now().strftime('%Y-%m-%d'),
            'invoice_date_due': due_date,
            'invoice_line_ids': [(0, 0, {
                'name': description,
                'quantity': 1,
                'price_unit': amount,
            })],
            'state': 'draft'
        }
        
        invoice_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move', 'create', [invoice_vals]
        )
        
        print(f"[OK] Created draft invoice ID: {invoice_id}")
        
        # Get invoice details
        invoice_data = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move', 'read', [invoice_id],
            {'fields': ['name', 'state', 'amount_total', 'invoice_date']}
        )
        
        invoice_name = invoice_data[0].get('name', f'Invoice {invoice_id}')
        print(f"[OK] Invoice Name: {invoice_name}")
        print(f"[OK] State: {invoice_data[0].get('state')}")
        print(f"[OK] Amount: ${invoice_data[0].get('amount_total', amount):.2f}")
        
        # ===========================================
        # Create Approval Request
        # ===========================================
        print("\n" + "="*60)
        print("CREATING APPROVAL REQUEST")
        print("="*60)
        
        # Ensure directory exists
        PENDING_APPROVAL_PATH.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = "".join(c for c in partner_name if c.isalnum() or c in ' -_')[:30]
        filename = f"ODOO_INVOICE_{timestamp}_{safe_name}.md"
        
        content = f"""---
type: odoo_approval
action_type: create_draft_invoice
partner_name: {partner_name}
partner_email: {partner_email}
amount: {amount:.2f}
description: {description}
due_days: {due_days}
invoice_id: {invoice_id}
invoice_name: {invoice_name}
created: {datetime.now().isoformat()}
status: pending
---

# Odoo Invoice Approval Request

## Action Required
Draft invoice has been created in Odoo and requires human approval.

## Invoice Details

| Field | Value |
|-------|-------|
| **Invoice ID** | {invoice_id} |
| **Invoice Name** | {invoice_name} |
| **Customer** | {partner_name} |
| **Email** | {partner_email} |
| **Amount** | ${amount:.2f} |
| **Description** | {description} |
| **Due Date** | {due_days} days |
| **State** | Draft |

## To Approve
1. Review the invoice details above
2. Move this file to `/Approved/ODOO/` folder
3. The AI Employee will execute the action in Odoo

## To Reject
1. Move this file to `/Rejected/ODOO/` folder
2. Add a comment explaining the rejection

---
*Generated by Odoo MCP Server - Gold Tier*
*Test Connection Script*
"""
        
        filepath = PENDING_APPROVAL_PATH / filename
        filepath.write_text(content, encoding='utf-8')
        
        print(f"[OK] Approval request saved to: {filepath}")
        
        print("\n" + "="*60)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"Customer: {partner_name} (ID: {partner_id})")
        print(f"Invoice: {invoice_name} (ID: {invoice_id}, Amount: ${amount:.2f})")
        print(f"Approval Request: {filename}")
        print("="*60)
        
        return {
            'partner_id': partner_id,
            'invoice_id': invoice_id,
            'invoice_name': invoice_name,
            'approval_file': filepath
        }
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    result = test_odoo_connection()
    sys.exit(0 if result else 1)
