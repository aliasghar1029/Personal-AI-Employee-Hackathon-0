# orchestrator.py
# Triggers Qwen Code to process the Needs_Action folder

import subprocess
import os
from pathlib import Path

VAULT_PATH = Path("./AI_Employee_Vault")
NEEDS_ACTION = VAULT_PATH / "Needs_Action"

def trigger_qwen():
    """Trigger Qwen Code to process pending action files."""
    pending_files = list(NEEDS_ACTION.glob("*.md"))
    
    if not pending_files:
        print("No pending actions.")
        return
    
    print(f"Found {len(pending_files)} pending action(s). Triggering Qwen Code...")
    
    prompt = f"""You are a Personal AI Employee. 
    
Read all files in the /Needs_Action folder of the AI_Employee_Vault.
For each file:
1. Create a Plan.md in /Plans with step-by-step checkboxes
2. If any action requires sending emails or payments, create an approval file in /Pending_Approval
3. Update Dashboard.md with the current status
4. Follow all rules in Company_Handbook.md

Start processing now."""
    
    # Run Qwen Code with the prompt
    os.chdir(VAULT_PATH)
    subprocess.run(["qwen", "-p", prompt], check=True)

if __name__ == "__main__":
    trigger_qwen()
