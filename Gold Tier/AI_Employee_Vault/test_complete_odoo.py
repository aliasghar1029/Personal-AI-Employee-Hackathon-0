#!/usr/bin/env python
"""Complete Odoo Integration Test - Gold Tier."""

import os
import sys
import codecs
import xmlrpc.client
from pathlib import Path
from datetime import datetime, timedelta

# Set UTF-8 encoding for Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv
load_dotenv()

# Configuration
VAULT_PATH = Path('E:/Hackathone/Gold Tier/AI_Employee_Vault')
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'
PENDING_APPROVAL_PATH = VAULT_PATH / 'Pending_Approval' / 'ODOO'

ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'ai_employee')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'masteraliasghar25@gmail.com')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'

# Test data
TEST_CUSTOMER_NAME = "Ali Khan"
TEST_CUSTOMER_EMAIL = "alikhan@test.com"
TEST_INVOICE_AMOUNT = 500.0
TEST_INVOICE_DESCRIPTION = "Professional Services - Gold Tier Test"


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def print_result(status, message):
    """Print a test result."""
    icon = "[OK]" if status else "[FAIL]"
    print(f"{icon} {message}")
    return status


class OdooIntegrationTest:
    """Complete Odoo integration test suite."""
    
    def __init__(self):
        self.common = None
        self.models = None
        self.uid = None
        self.partner_id = None
        self.invoice_id = None
        self.invoice_name = None
        self.approval_file = None
        self.test_results = []
    
    def run_test(self, step_name, test_func):
        """Run a single test step."""
        print_header(f"STEP: {step_name}")
        try:
            result = test_func()
            self.test_results.append((step_name, True, result))
            print_result(True, result)
            return True
        except Exception as e:
            self.test_results.append((step_name, False, str(e)))
            print_result(False, f"Error: {e}")
            return False
    
    def test_connect_odoo(self):
        """Step 1: Connect to Odoo."""
        print(f"Connecting to Odoo at {ODOO_URL}...")
        print(f"Database: {ODOO_DB}")
        print(f"Username: {ODOO_USERNAME}")
        
        # Connect to common endpoint
        self.common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        
        # Check server version
        version = self.common.version()
        print(f"Odoo Server Version: {version.get('server_version', 'Unknown')}")
        
        # Authenticate
        self.uid = self.common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not self.uid:
            raise Exception("Authentication failed - invalid credentials")
        
        # Connect to models endpoint
        self.models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        return f"Connected successfully! User ID: {self.uid}"
    
    def test_create_customer(self):
        """Step 2: Create new customer."""
        print(f"Creating customer: {TEST_CUSTOMER_NAME}")
        print(f"Email: {TEST_CUSTOMER_EMAIL}")
        
        # Check if customer already exists
        existing_ids = self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD,
            'res.partner', 'search', [[['email', '=', TEST_CUSTOMER_EMAIL]]]
        )
        
        if existing_ids:
            self.partner_id = existing_ids[0]
            return f"Customer already exists with ID: {self.partner_id}"
        
        # Create new customer
        partner_vals = {
            'name': TEST_CUSTOMER_NAME,
            'email': TEST_CUSTOMER_EMAIL,
        }
        
        self.partner_id = self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD,
            'res.partner', 'create', [partner_vals]
        )
        
        return f"Customer created successfully! ID: {self.partner_id}"
    
    def test_create_draft_invoice(self):
        """Step 3: Create draft invoice."""
        print(f"Creating draft invoice for: {TEST_CUSTOMER_NAME}")
        print(f"Amount: ${TEST_INVOICE_AMOUNT:.2f}")
        print(f"Description: {TEST_INVOICE_DESCRIPTION}")
        
        # Calculate due date (30 days)
        due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        invoice_date = datetime.now().strftime('%Y-%m-%d')
        
        # Create draft invoice
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id,
            'invoice_date': invoice_date,
            'invoice_date_due': due_date,
            'invoice_line_ids': [(0, 0, {
                'name': TEST_INVOICE_DESCRIPTION,
                'quantity': 1,
                'price_unit': TEST_INVOICE_AMOUNT,
            })],
            'state': 'draft'
        }
        
        self.invoice_id = self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD,
            'account.move', 'create', [invoice_vals]
        )
        
        # Get invoice details
        invoice_data = self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD,
            'account.move', 'read', [self.invoice_id],
            {'fields': ['name', 'state', 'amount_total', 'invoice_date']}
        )
        
        self.invoice_name = invoice_data[0].get('name', f'Invoice {self.invoice_id}')
        
        return f"Draft invoice created! ID: {self.invoice_id}, Name: {self.invoice_name}, Amount: ${TEST_INVOICE_AMOUNT:.2f}"
    
    def test_create_approval_request(self):
        """Step 4: Create approval request."""
        print(f"Creating approval request in: {PENDING_APPROVAL_PATH}")
        
        # Ensure directory exists
        PENDING_APPROVAL_PATH.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = "".join(c for c in TEST_CUSTOMER_NAME if c.isalnum() or c in ' -_')[:30]
        filename = f"ODOO_INVOICE_{timestamp}_{safe_name}.md"
        
        content = f"""---
type: odoo_approval
action_type: create_draft_invoice
partner_name: {TEST_CUSTOMER_NAME}
partner_email: {TEST_CUSTOMER_EMAIL}
amount: {TEST_INVOICE_AMOUNT:.2f}
description: {TEST_INVOICE_DESCRIPTION}
due_days: 30
invoice_id: {self.invoice_id}
invoice_name: {self.invoice_name}
created: {datetime.now().isoformat()}
status: pending
---

# Odoo Invoice Approval Request

## Action Required
Draft invoice has been created in Odoo and requires human approval.

## Invoice Details

| Field | Value |
|-------|-------|
| **Invoice ID** | {self.invoice_id} |
| **Invoice Name** | {self.invoice_name} |
| **Customer** | {TEST_CUSTOMER_NAME} |
| **Email** | {TEST_CUSTOMER_EMAIL} |
| **Amount** | ${TEST_INVOICE_AMOUNT:.2f} |
| **Description** | {TEST_INVOICE_DESCRIPTION} |
| **Due Date** | 30 days |
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
*Complete Integration Test*
"""
        
        filepath = PENDING_APPROVAL_PATH / filename
        filepath.write_text(content, encoding='utf-8')
        self.approval_file = filepath
        
        return f"Approval request saved: {filename}"
    
    def test_update_dashboard(self):
        """Step 5: Update Dashboard.md."""
        print(f"Updating Dashboard: {DASHBOARD_PATH}")
        
        if not DASHBOARD_PATH.exists():
            raise Exception("Dashboard.md not found")
        
        content = DASHBOARD_PATH.read_text(encoding='utf-8')
        
        # Count draft invoices from Odoo
        draft_invoices = self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD,
            'account.move', 'search', [[['move_type', '=', 'out_invoice'], ['state', '=', 'draft']]]
        )
        draft_count = len(draft_invoices) if draft_invoices else 0
        
        connection_status = "Connected ✅" if self.uid else "Disconnected ❌"
        
        odoo_section = f"""## Odoo Status
- Connection: {connection_status}
- URL: {ODOO_URL}
- Database: {ODOO_DB}
- Pending Invoices: {draft_count}
- Actions Today: 1
- DRY_RUN: {'Yes' if DRY_RUN else 'No'}
"""
        
        if '## Odoo Status' not in content:
            content += '\n' + odoo_section.strip() + '\n'
        else:
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
        
        DASHBOARD_PATH.write_text(content, encoding='utf-8')
        
        return f"Dashboard updated! Pending Invoices: {draft_count}"
    
    def print_summary(self):
        """Print complete test summary."""
        print_header("TEST SUMMARY")
        
        all_passed = True
        for i, (step_name, passed, message) in enumerate(self.test_results, 1):
            status = "PASS" if passed else "FAIL"
            icon = "✅" if passed else "❌"
            print(f"{i}. {icon} {step_name}: {status}")
            print(f"   {message}")
        
        print("\n" + "-"*70)
        passed_count = sum(1 for _, passed, _ in self.test_results if passed)
        total_count = len(self.test_results)
        
        if passed_count == total_count:
            print(f"\n🎉 ALL TESTS PASSED ({passed_count}/{total_count})")
            print("\nTest Results:")
            print(f"  - Customer: {TEST_CUSTOMER_NAME} (ID: {self.partner_id})")
            print(f"  - Invoice: {self.invoice_name} (ID: {self.invoice_id}, Amount: ${TEST_INVOICE_AMOUNT:.2f})")
            print(f"  - Approval File: {self.approval_file.name if self.approval_file else 'N/A'}")
            print(f"  - Dashboard: Updated with connection status and pending invoices")
        else:
            print(f"\n⚠️  SOME TESTS FAILED ({passed_count}/{total_count} passed)")
        
        print("\n" + "="*70)
        
        return all_passed


def main():
    """Main test runner."""
    print_header("ODOO INTEGRATION TEST - GOLD TIER")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Odoo URL: {ODOO_URL}")
    print(f"Database: {ODOO_DB}")
    print(f"DRY_RUN: {DRY_RUN}")
    
    test = OdooIntegrationTest()
    
    # Run all test steps
    test.run_test("Connect to Odoo", test.test_connect_odoo)
    test.run_test("Create Customer (Ali Khan)", test.test_create_customer)
    test.run_test("Create Draft Invoice ($500)", test.test_create_draft_invoice)
    test.run_test("Create Approval Request", test.test_create_approval_request)
    test.run_test("Update Dashboard.md", test.test_update_dashboard)
    
    # Print summary
    test.print_summary()
    
    # Return exit code
    all_passed = all(passed for _, passed, _ in test.test_results)
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
