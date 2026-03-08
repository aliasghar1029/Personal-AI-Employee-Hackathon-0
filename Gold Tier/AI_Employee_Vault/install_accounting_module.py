#!/usr/bin/env python
"""Install Accounting module in Odoo."""

import xmlrpc.client
import sys
import codecs

# Set UTF-8 encoding
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'ai_employee'
ODOO_USERNAME = 'masteraliasghar25@gmail.com'
ODOO_PASSWORD = 'admin'

print("Installing Accounting module in Odoo...")
print(f"URL: {ODOO_URL}")
print(f"Database: {ODOO_DB}")

try:
    # Authenticate
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
    
    if not uid:
        print("[ERROR] Authentication failed!")
        sys.exit(1)
    
    print(f"[OK] Authentication successful! User ID: {uid}")
    
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    
    # Check if module exists
    module_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'ir.module.module', 'search', [[['name', '=', 'account']]]
    )
    
    if not module_ids:
        print("[ERROR] Accounting module not found!")
        sys.exit(1)
    
    # Get module info
    module_info = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'ir.module.module', 'read', [module_ids],
        {'fields': ['name', 'state', 'latest_version']}
    )
    
    print(f"Module info: {module_info}")
    
    if module_info[0].get('state') == 'installed':
        print("[OK] Accounting module is already installed!")
    else:
        # Install the module
        print("\nInstalling Accounting module...")
        result = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'ir.module.module', 'button_immediate_install', [module_ids]
        )
        print(f"[OK] Installation initiated: {result}")
        
        # Check state after installation
        module_info = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'ir.module.module', 'read', [module_ids],
            {'fields': ['name', 'state']}
        )
        print(f"Module state after installation: {module_info[0].get('state')}")
    
    print("\n[OK] Accounting module setup complete!")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
