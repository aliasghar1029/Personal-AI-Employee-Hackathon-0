#!/usr/bin/env python
"""Simple Odoo connection test."""

import xmlrpc.client
import sys
import codecs

# Set UTF-8 encoding
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'ai_employee'

print("Testing Odoo connection...")
print(f"URL: {ODOO_URL}")
print(f"Database: {ODOO_DB}")

# Test 1: Check server version
try:
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    version = common.version()
    print(f"\nServer version: {version}")
except Exception as e:
    print(f"Error getting version: {e}")
    sys.exit(1)

# Test 2: Try different credentials
credentials = [
    ('admin', 'admin'),
    ('admin@aiemployee.com', 'admin'),
    ('odoo', 'odoo'),
    ('default', 'admin'),
    ('masteraliasghar25@gmail.com', 'admin'),
]

for username, password in credentials:
    try:
        print(f"\nTrying: {username} / {password}")
        uid = common.authenticate(ODOO_DB, username, password, {})
        if uid:
            print(f"SUCCESS! User ID: {uid}")
        else:
            print("FAILED - Invalid credentials")
    except Exception as e:
        print(f"ERROR: {e}")

# Test 3: List databases
try:
    print("\n\nListing databases...")
    db_list = common.list_dbs()
    print(f"Available databases: {db_list}")
except Exception as e:
    print(f"Error listing databases: {e}")
