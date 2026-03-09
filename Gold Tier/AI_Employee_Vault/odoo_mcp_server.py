# odoo_mcp_server.py
# Gold Tier: Odoo Accounting Integration via JSON-RPC
# Connects to Odoo via XML-RPC API
# Creates draft invoices, reads customers, checks payment status, creates expenses
# All actions are DRAFT only - require human approval
# Approval flow:
#   1. Create file in /Pending_Approval/ODOO_invoice.md
#   2. Human moves to /Approved/ODOO/
#   3. MCP executes action in Odoo
#   4. Log result to /Logs/audit/

import os
import time
import logging
import json
import xmlrpc.client
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

from dashboard_manager import get_dashboard_manager

# Import audit logger
from audit_logger import get_audit_logger

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/odoo_mcp.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './AI_Employee_Vault'))
PENDING_APPROVAL_PATH = VAULT_PATH / 'Pending_Approval' / 'ODOO'
APPROVED_PATH = VAULT_PATH / 'Approved' / 'ODOO'
REJECTED_PATH = VAULT_PATH / 'Rejected' / 'ODOO'
DONE_PATH = VAULT_PATH / 'Done' / 'ODOO'
LOGS_PATH = VAULT_PATH / 'Logs'
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'
ODOO_LOG = LOGS_PATH / 'odoo_actions.json'

# Odoo Configuration
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'ai_employee')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')
ODOO_CHECK_INTERVAL = int(os.getenv('ODOO_CHECK_INTERVAL', '60'))
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'


class OdooMCPServer:
    """Odoo MCP Server for accounting integration."""
    
    def __init__(self):
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.password = ODOO_PASSWORD
        self.uid = None
        self.common = None
        self.models = None
        self.audit_logger = get_audit_logger()
        self.actions_log = []
        self.dashboard = get_dashboard_manager()
        self._initialize()
    
    def _initialize(self):
        """Initialize Odoo connection and paths."""
        # Ensure directories exist
        for path in [PENDING_APPROVAL_PATH, APPROVED_PATH, REJECTED_PATH, DONE_PATH, LOGS_PATH]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Load action history
        self._load_action_history()
        
        # Connect to Odoo
        self._connect()
    
    def _load_action_history(self):
        """Load previously executed Odoo actions."""
        if ODOO_LOG.exists():
            try:
                data = json.loads(ODOO_LOG.read_text(encoding='utf-8'))
                self.actions_log = data.get('actions', [])
                logger.info(f"Loaded {len(self.actions_log)} Odoo action records")
            except:
                self.actions_log = []
        else:
            self.actions_log = []
    
    def _save_action(self, action_data: dict):
        """Save an executed Odoo action."""
        self.actions_log.append(action_data)
        
        data = {
            'actions': self.actions_log,
            'last_updated': datetime.now().isoformat()
        }
        ODOO_LOG.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def _connect(self) -> bool:
        """Connect to Odoo via XML-RPC."""
        try:
            # Common endpoint for authentication
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            
            # Check server version
            version = self.common.version()
            logger.info(f"Odoo server version: {version}")
            
            # Authenticate
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            
            if not self.uid:
                logger.error("Odoo authentication failed")
                self.audit_logger.log_failure(
                    action_type='odoo_connect',
                    actor='odoo_mcp',
                    details='Authentication failed',
                    error='Invalid credentials'
                )
                return False
            
            # Models endpoint for operations
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            
            logger.info(f"Connected to Odoo as user ID: {self.uid}")
            self.audit_logger.log_success(
                action_type='odoo_connect',
                actor='odoo_mcp',
                details=f'Connected to Odoo at {self.url}'
            )
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Odoo: {e}")
            self.audit_logger.log_failure(
                action_type='odoo_connect',
                actor='odoo_mcp',
                details=f'Connection failed: {str(e)}',
                error=str(e)
            )
            return False
    
    def _ensure_connection(self) -> bool:
        """Ensure Odoo connection is active."""
        if self.uid is None:
            return self._connect()
        
        try:
            # Test connection by checking user
            self.models.execute_kw(self.db, self.uid, self.password, 'res.users', 'check', [])
            return True
        except:
            logger.warning("Connection lost, reconnecting...")
            return self._connect()
    
    # ===========================================
    # Odoo Operations (All DRAFT by default)
    # ===========================================
    
    def create_draft_invoice(
        self,
        partner_name: str,
        partner_email: str,
        amount: float,
        description: str,
        due_days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Create a draft customer invoice in Odoo."""
        if not self._ensure_connection():
            return None
        
        try:
            # Find or create partner (customer)
            partner_id = self._find_or_create_partner(partner_name, partner_email)
            
            if not partner_id:
                logger.error("Could not create/find partner")
                return None
            
            # Calculate due date
            due_date = (datetime.now() + timedelta(days=due_days)).strftime('%Y-%m-%d')
            
            # Create draft invoice
            invoice_vals = {
                'move_type': 'out_invoice',  # Customer invoice
                'partner_id': partner_id,
                'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                'invoice_date_due': due_date,
                'invoice_line_ids': [(0, 0, {
                    'name': description,
                    'quantity': 1,
                    'price_unit': amount,
                })],
                'state': 'draft'  # Always create as draft
            }
            
            invoice_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'create', [invoice_vals]
            )
            
            logger.info(f"Created draft invoice ID: {invoice_id}")
            
            # Get invoice details
            invoice_data = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'read', [invoice_id],
                {'fields': ['name', 'state', 'amount_total', 'invoice_date']}
            )
            
            return {
                'id': invoice_id,
                'name': invoice_data[0].get('name', f'Invoice {invoice_id}'),
                'state': 'draft',
                'amount_total': amount,
                'partner': partner_name,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating draft invoice: {e}")
            return None
    
    def _find_or_create_partner(self, name: str, email: str) -> Optional[int]:
        """Find existing partner or create new one."""
        try:
            # Search for existing partner by email
            partner_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'search', [[['email', '=', email]]]
            )
            
            if partner_ids:
                logger.info(f"Found existing partner: {name}")
                return partner_ids[0]
            
            # Create new partner
            partner_vals = {
                'name': name,
                'email': email,
            }
            
            partner_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'create', [partner_vals]
            )
            
            logger.info(f"Created new partner ID: {partner_id}")
            return partner_id
            
        except Exception as e:
            logger.error(f"Error with partner operation: {e}")
            return None
    
    def get_customer_list(self) -> List[Dict[str, Any]]:
        """Get list of customers from Odoo."""
        if not self._ensure_connection():
            return []
        
        try:
            customer_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'search', [[['customer_rank', '>', 0]]]
            )
            
            customers = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.partner', 'read', [customer_ids],
                {'fields': ['name', 'email', 'phone', 'city', 'country_id']}
            )
            
            return customers
            
        except Exception as e:
            logger.error(f"Error getting customer list: {e}")
            return []
    
    def check_payment_status(self, invoice_ref: str = None) -> List[Dict[str, Any]]:
        """Check payment status of invoices."""
        if not self._ensure_connection():
            return []
        
        try:
            domain = []
            if invoice_ref:
                domain = [['name', '=', invoice_ref]]
            
            invoice_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'search', [domain]
            )
            
            invoices = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'read', [invoice_ids],
                {'fields': ['name', 'state', 'amount_total', 'amount_residual', 'invoice_date', 'invoice_date_due']}
            )
            
            # Add payment status
            for invoice in invoices:
                if invoice.get('amount_residual', 0) > 0:
                    invoice['payment_status'] = 'partial' if invoice.get('amount_residual', 0) < invoice.get('amount_total', 0) else 'unpaid'
                else:
                    invoice['payment_status'] = 'paid'
            
            return invoices
            
        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            return []
    
    def create_draft_expense(
        self,
        description: str,
        amount: float,
        category: str = 'General',
        date: str = None
    ) -> Optional[Dict[str, Any]]:
        """Create a draft expense in Odoo."""
        if not self._ensure_connection():
            return None
        
        try:
            expense_vals = {
                'name': description,
                'total_amount': amount,
                'description': description,
                'date': date or datetime.now().strftime('%Y-%m-%d'),
                'state': 'draft',  # Always create as draft
            }
            
            # Try to find expense category
            if category != 'General':
                category_ids = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'hr.expense.sheet', 'search', [[['name', 'ilike', category]]]
                )
            
            expense_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'hr.expense', 'create', [expense_vals]
            )
            
            logger.info(f"Created draft expense ID: {expense_id}")
            
            return {
                'id': expense_id,
                'description': description,
                'amount': amount,
                'state': 'draft',
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating draft expense: {e}")
            return None
    
    def confirm_invoice(self, invoice_id: int) -> bool:
        """Post/confirm a draft invoice (requires approval)."""
        if not self._ensure_connection():
            return False
        
        try:
            # Post the invoice (changes state from draft to posted)
            self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'action_post', [[invoice_id]]
            )
            
            logger.info(f"Confirmed invoice ID: {invoice_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error confirming invoice: {e}")
            return False
    
    # ===========================================
    # Approval File Processing
    # ===========================================
    
    def _parse_approval_file(self, filepath: Path) -> Dict[str, Any]:
        """Parse an Odoo approval file."""
        content = filepath.read_text(encoding='utf-8')
        
        approval_data = {
            'action_type': '',
            'invoice_id': None,
            'partner_name': '',
            'partner_email': '',
            'amount': 0.0,
            'description': '',
            'due_days': 30,
            'filename': filepath.name
        }
        
        # Extract frontmatter
        lines = content.split('\n')
        in_frontmatter = False
        
        for line in lines:
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
                continue
            
            if in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'action_type':
                    approval_data['action_type'] = value
                elif key == 'invoice_id':
                    approval_data['invoice_id'] = int(value) if value.isdigit() else None
                elif key == 'partner_name':
                    approval_data['partner_name'] = value
                elif key == 'partner_email':
                    approval_data['partner_email'] = value
                elif key == 'amount':
                    approval_data['amount'] = float(value)
                elif key == 'description':
                    approval_data['description'] = value
                elif key == 'due_days':
                    approval_data['due_days'] = int(value)
        
        return approval_data
    
    def process_approved_actions(self):
        """Process approved Odoo actions."""
        try:
            approved_files = list(APPROVED_PATH.glob('*.md'))
            
            if not approved_files:
                logger.debug("No approved Odoo actions")
                return
            
            logger.info(f"Found {len(approved_files)} approved Odoo action(s)")
            
            for filepath in approved_files:
                logger.info(f"Processing approved action: {filepath.name}")
                
                approval_data = self._parse_approval_file(filepath)
                
                if DRY_RUN:
                    logger.info(f"[DRY_RUN] Would execute: {approval_data['action_type']}")
                    self._move_to_done(filepath, 'dry_run')
                    continue
                
                success = False
                
                if approval_data['action_type'] == 'confirm_invoice':
                    if approval_data['invoice_id']:
                        success = self.confirm_invoice(approval_data['invoice_id'])
                
                if success:
                    logger.info(f"Successfully executed: {approval_data['action_type']}")
                    self._save_action({
                        'type': approval_data['action_type'],
                        'filename': filepath.name,
                        'executed_at': datetime.now().isoformat(),
                        'status': 'success'
                    })
                    self._move_to_done(filepath, 'success')
                else:
                    logger.error(f"Failed to execute: {approval_data['action_type']}")
                    self._move_to_rejected(filepath, 'Execution failed')
            
            self._update_dashboard()
            
        except Exception as e:
            logger.error(f"Error processing approved actions: {e}")
    
    def _move_to_done(self, filepath: Path, status: str):
        """Move approved file to Done folder."""
        try:
            done_path = DONE_PATH / filepath.name
            DONE_PATH.mkdir(parents=True, exist_ok=True)
            filepath.rename(done_path)
            logger.info(f"Moved to Done: {filepath.name}")
        except Exception as e:
            logger.error(f"Error moving file: {e}")
    
    def _move_to_rejected(self, filepath: Path, reason: str):
        """Move failed file to Rejected folder."""
        try:
            rejected_path = REJECTED_PATH / f"ERROR_{filepath.name}"
            REJECTED_PATH.mkdir(parents=True, exist_ok=True)
            
            content = filepath.read_text(encoding='utf-8')
            error_content = f"""---
original_file: {filepath.name}
error: {reason}
failed_at: {datetime.now().isoformat()}
status: failed
---

{content}
"""
            rejected_path.write_text(error_content, encoding='utf-8')
            filepath.unlink()
            logger.info(f"Moved to Rejected: {filepath.name}")
        except Exception as e:
            logger.error(f"Error moving file: {e}")
    
    # ===========================================
    # Create Approval Request
    # ===========================================
    
    def create_approval_request(
        self,
        action_type: str,
        partner_name: str,
        partner_email: str,
        amount: float,
        description: str,
        due_days: int = 30
    ) -> Path:
        """Create an approval request file for human review."""
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
created: {datetime.now().isoformat()}
status: pending
---

# Odoo Invoice Approval Request

## Action Required
Create and post a draft invoice in Odoo.

## Invoice Details

| Field | Value |
|-------|-------|
| **Customer** | {partner_name} |
| **Email** | {partner_email} |
| **Amount** | ${amount:.2f} |
| **Description** | {description} |
| **Due Date** | {due_days} days |

## To Approve
1. Review the invoice details above
2. Move this file to `/Approved/ODOO/` folder
3. The AI Employee will execute the action in Odoo

## To Reject
1. Move this file to `/Rejected/ODOO/` folder
2. Add a comment explaining the rejection

---
*Generated by Odoo MCP Server - Gold Tier*
"""
        
        filepath = PENDING_APPROVAL_PATH / filename
        filepath.write_text(content, encoding='utf-8')
        
        logger.info(f"Created approval request: {filename}")
        
        self.audit_logger.log_pending(
            action_type='odoo_invoice_approval',
            actor='odoo_mcp',
            details=f'Created approval request for invoice to {partner_name}',
            metadata={
                'partner': partner_name,
                'amount': amount,
                'filename': filename
            }
        )
        
        return filepath
    
    # ===========================================
    # Dashboard Updates
    # ===========================================

    def _update_dashboard(self):
        """Update Dashboard.md with Odoo status."""
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            # Count pending approvals
            pending_count = len(list(PENDING_APPROVAL_PATH.glob('*.md')))
            
            # Count actions today
            today = datetime.now().strftime('%Y-%m-%d')
            actions_today = len([a for a in self.actions_log if today in a.get('executed_at', '')])
            
            # Get connection status
            connection_status = "Connected" if self.uid else "Disconnected"
            
            # Count draft invoices from Odoo
            draft_invoices_count = 0
            if self._ensure_connection():
                try:
                    draft_invoices = self.models.execute_kw(
                        self.db, self.uid, self.password,
                        'account.move', 'search', [[['move_type', '=', 'out_invoice'], ['state', '=', 'draft']]]
                    )
                    draft_invoices_count = len(draft_invoices) if draft_invoices else 0
                except Exception:
                    draft_invoices_count = pending_count  # Fallback to file count

            self.dashboard.update_service('odoo', {
                'odoo_status': connection_status,
                'odoo_url': self.url,
                'odoo_db': self.db,
                'odoo_draft_invoices': draft_invoices_count,
                'odoo_actions_today': actions_today,
                'odoo_dry_run': DRY_RUN
            })
            logger.info("Dashboard updated")

        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def run(self):
        """Main run loop."""
        logger.info(f"Odoo MCP Server started. Checking every {ODOO_CHECK_INTERVAL} seconds...")
        logger.info(f"URL: {self.url}")
        logger.info(f"Database: {self.db}")
        logger.info(f"DRY_RUN: {DRY_RUN}")
        
        print("\n" + "="*50)
        print("ODOO MCP SERVER - GOLD TIER")
        print("="*50)
        print(f"URL: {self.url}")
        print(f"Database: {self.db}")
        print(f"Connection: {'Connected' if self.uid else 'Disconnected'}")
        print(f"DRY_RUN: {DRY_RUN}")
        print(f"Checking approved actions every {ODOO_CHECK_INTERVAL} seconds...")
        print("="*50 + "\n")
        
        while True:
            try:
                # Process approved actions
                self.process_approved_actions()
                
                # Update dashboard
                self._update_dashboard()
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            
            time.sleep(ODOO_CHECK_INTERVAL)


def main():
    """Entry point."""
    try:
        server = OdooMCPServer()
        server.run()
    except KeyboardInterrupt:
        logger.info("Odoo MCP Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
