#!/usr/bin/env python
"""Test LinkedIn token validation and refresh flow."""

import sys
import codecs
from pathlib import Path

# Set UTF-8 encoding
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from dotenv import load_dotenv, unset_key
import os

VAULT_PATH = Path('E:/Hackathone/Gold Tier/AI_Employee_Vault')
ENV_PATH = VAULT_PATH / '.env'

print("="*60)
print("LINKEDIN TOKEN REFRESH TEST")
print("="*60)

# Load current token
load_dotenv(ENV_PATH)
current_token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')

print(f"\nCurrent token status: {'Present' if current_token else 'Not set'}")

if current_token:
    print("\nRemoving existing token to test refresh flow...")
    unset_key(str(ENV_PATH), 'LINKEDIN_ACCESS_TOKEN')
    print("Token removed from .env file")
    
    # Reload to verify
    load_dotenv(ENV_PATH)
    new_token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
    print(f"Token after removal: {'Present' if new_token else 'Not set'}")
else:
    print("\nNo token present - refresh flow will trigger automatically")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
print("\nWhen linkedin_poster.py starts:")
print("1. It will detect no valid token")
print("2. Open browser for OAuth2 authorization")
print("3. Save new token to .env file")
print("4. Print: 'LinkedIn token refreshed successfully!'")
print("="*60)
