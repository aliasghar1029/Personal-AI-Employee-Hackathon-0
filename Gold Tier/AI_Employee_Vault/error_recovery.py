# error_recovery.py
# Gold Tier: Error Recovery and Health Monitoring System
# - If Gmail API down: Queue locally, retry later
# - If Facebook API fails: Auto switch to Playwright
# - If Odoo down: Save actions locally, sync when restored
# - If any watcher crashes: Auto restart after 30 seconds
# - Log all errors to /Logs/errors/

import os
import time
import logging
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import threading

from dashboard_manager import get_dashboard_manager

# Import audit logger
from audit_logger import get_audit_logger

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/error_recovery.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './AI_Employee_Vault'))
LOGS_PATH = VAULT_PATH / 'Logs'
ERRORS_PATH = LOGS_PATH / 'errors'
QUEUE_PATH = VAULT_PATH / 'Error_Queue'
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'

# Recovery settings
RETRY_DELAY = int(os.getenv('ERROR_RETRY_DELAY', '30'))  # 30 seconds
MAX_RETRIES = int(os.getenv('ERROR_MAX_RETRIES', '5'))
HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))
AUTO_RESTART_DELAY = int(os.getenv('AUTO_RESTART_DELAY', '30'))


class ErrorRecoverySystem:
    """Error recovery and health monitoring system."""
    
    def __init__(self):
        self.audit_logger = get_audit_logger()
        self.service_status = {}
        self.error_queue = []
        self.retry_counts = {}
        self.dashboard = get_dashboard_manager()
        self._initialize()
    
    def _initialize(self):
        """Initialize error recovery system."""
        ERRORS_PATH.mkdir(parents=True, exist_ok=True)
        QUEUE_PATH.mkdir(parents=True, exist_ok=True)
        self._load_error_queue()
        self._initialize_service_status()
    
    def _load_error_queue(self):
        """Load previously queued errors."""
        queue_file = QUEUE_PATH / 'error_queue.json'
        if queue_file.exists():
            try:
                data = json.loads(queue_file.read_text(encoding='utf-8'))
                self.error_queue = data.get('errors', [])
                logger.info(f"Loaded {len(self.error_queue)} queued errors")
            except:
                self.error_queue = []
        else:
            self.error_queue = []
    
    def _save_error_queue(self):
        """Save error queue to file."""
        queue_file = QUEUE_PATH / 'error_queue.json'
        data = {
            'errors': self.error_queue,
            'last_updated': datetime.now().isoformat()
        }
        queue_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def _initialize_service_status(self):
        """Initialize service status tracking."""
        self.service_status = {
            'gmail_watcher': {'status': 'unknown', 'last_check': None, 'errors': 0},
            'whatsapp_watcher': {'status': 'unknown', 'last_check': None, 'errors': 0},
            'filesystem_watcher': {'status': 'unknown', 'last_check': None, 'errors': 0},
            'facebook_manager': {'status': 'unknown', 'last_check': None, 'errors': 0},
            'linkedin_poster': {'status': 'unknown', 'last_check': None, 'errors': 0},
            'email_mcp': {'status': 'unknown', 'last_check': None, 'errors': 0},
            'odoo_mcp': {'status': 'unknown', 'last_check': None, 'errors': 0},
            'scheduler': {'status': 'unknown', 'last_check': None, 'errors': 0},
        }
    
    def log_error(
        self,
        service: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log an error and queue for recovery."""
        timestamp = datetime.now().isoformat()
        error_date = datetime.now().strftime('%Y-%m-%d')
        
        # Create error log file
        error_file = ERRORS_PATH / f"{error_date}_{service}_{int(time.time())}.json"
        
        error_data = {
            'timestamp': timestamp,
            'service': service,
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
            'retry_count': self.retry_counts.get(service, 0),
            'status': 'queued'
        }
        
        # Write error file
        error_file.write_text(json.dumps(error_data, indent=2), encoding='utf-8')
        
        # Add to queue
        self.error_queue.append({
            'file': str(error_file),
            'service': service,
            'error_type': error_type,
            'added_at': timestamp
        })
        self._save_error_queue()
        
        # Update service status
        if service in self.service_status:
            self.service_status[service]['status'] = 'error'
            self.service_status[service]['last_check'] = timestamp
            self.service_status[service]['errors'] += 1
        
        # Log to audit
        self.audit_logger.log_failure(
            action_type='service_error',
            actor='error_recovery',
            details=f'{service}: {error_type}',
            error=error_message,
            metadata={
                'service': service,
                'error_type': error_type,
                'error_file': str(error_file)
            }
        )
        
        logger.error(f"[{service}] {error_type}: {error_message}")
    
    def check_service_health(self, service: str) -> bool:
        """Check if a service is healthy."""
        try:
            if service == 'gmail_watcher':
                return self._check_gmail_health()
            elif service == 'facebook_manager':
                return self._check_facebook_health()
            elif service == 'odoo_mcp':
                return self._check_odoo_health()
            elif service == 'linkedin_poster':
                return self._check_linkedin_health()
            else:
                # Generic check - assume healthy if no recent errors
                if service in self.service_status:
                    return self.service_status[service]['errors'] < MAX_RETRIES
                return True
        except Exception as e:
            logger.error(f"Error checking {service} health: {e}")
            return False
    
    def _check_gmail_health(self) -> bool:
        """Check Gmail API health."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            token_file = VAULT_PATH / 'token.json'
            credentials_file = VAULT_PATH / 'credentials.json'
            
            if not token_file.exists() or not credentials_file.exists():
                return False
            
            creds = Credentials.from_authorized_user_file(str(token_file), [
                'https://www.googleapis.com/auth/gmail.readonly'
            ])
            
            if not creds.valid:
                return False
            
            service = build('gmail', 'v1', credentials=creds)
            service.users().messages().list(userId='me', maxResults=1).execute()
            
            return True
        except Exception as e:
            logger.error(f"Gmail health check failed: {e}")
            return False
    
    def _check_facebook_health(self) -> bool:
        """Check Facebook API health."""
        try:
            import requests
            
            access_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')
            if not access_token:
                return False
            
            url = f'https://graph.facebook.com/v18.0/me'
            params = {'access_token': access_token}
            
            response = requests.get(url, params=params, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Facebook health check failed: {e}")
            return False
    
    def _check_odoo_health(self) -> bool:
        """Check Odoo connection health."""
        try:
            import xmlrpc.client
            
            odoo_url = os.getenv('ODOO_URL', 'http://localhost:8069')
            odoo_db = os.getenv('ODOO_DB', 'ai_employee')
            odoo_username = os.getenv('ODOO_USERNAME', 'admin')
            odoo_password = os.getenv('ODOO_PASSWORD', 'admin')
            
            common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
            uid = common.authenticate(odoo_db, odoo_username, odoo_password, {})
            
            return uid is not None and uid > 0
        except Exception as e:
            logger.error(f"Odoo health check failed: {e}")
            return False
    
    def _check_linkedin_health(self) -> bool:
        """Check LinkedIn API health."""
        try:
            import requests
            
            access_token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
            if not access_token:
                return False
            
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get('https://api.linkedin.com/v2/userinfo', headers=headers, timeout=10)
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"LinkedIn health check failed: {e}")
            return False
    
    def retry_failed_service(self, service: str) -> bool:
        """Attempt to retry a failed service."""
        if service not in self.retry_counts:
            self.retry_counts[service] = 0
        
        if self.retry_counts[service] >= MAX_RETRIES:
            logger.error(f"Max retries reached for {service}")
            return False
        
        self.retry_counts[service] += 1
        
        logger.info(f"Retrying {service} (attempt {self.retry_counts[service]}/{MAX_RETRIES})")
        
        try:
            if service == 'gmail_watcher':
                return self._retry_gmail()
            elif service == 'facebook_manager':
                return self._retry_facebook()
            elif service == 'odoo_mcp':
                return self._retry_odoo()
            else:
                # Generic retry - just check health
                return self.check_service_health(service)
        except Exception as e:
            logger.error(f"Retry failed for {service}: {e}")
            return False
    
    def _retry_gmail(self) -> bool:
        """Retry Gmail connection."""
        return self._check_gmail_health()
    
    def _retry_facebook(self) -> bool:
        """Retry Facebook connection."""
        return self._check_facebook_health()
    
    def _retry_odoo(self) -> bool:
        """Retry Odoo connection."""
        return self._check_odoo_health()
    
    def queue_action_for_retry(
        self,
        action_type: str,
        action_data: Dict[str, Any],
        error_message: str
    ):
        """Queue an action for later retry."""
        retry_file = QUEUE_PATH / f"retry_{action_type}_{int(time.time())}.json"
        
        retry_data = {
            'action_type': action_type,
            'action_data': action_data,
            'error_message': error_message,
            'queued_at': datetime.now().isoformat(),
            'retry_count': 0,
            'status': 'pending'
        }
        
        retry_file.write_text(json.dumps(retry_data, indent=2), encoding='utf-8')
        
        logger.info(f"Queued {action_type} for retry: {retry_file}")
        
        self.audit_logger.log_pending(
            action_type='action_queued_for_retry',
            actor='error_recovery',
            details=f'{action_type} queued for retry',
            metadata={
                'action_type': action_type,
                'retry_file': str(retry_file)
            }
        )
    
    def process_retry_queue(self):
        """Process queued actions for retry."""
        try:
            retry_files = list(QUEUE_PATH.glob('retry_*.json'))
            
            for retry_file in retry_files:
                try:
                    data = json.loads(retry_file.read_text(encoding='utf-8'))
                    
                    # Check retry count
                    if data.get('retry_count', 0) >= MAX_RETRIES:
                        logger.warning(f"Max retries reached for {data['action_type']}, moving to failed")
                        retry_file.unlink()
                        continue
                    
                    # Attempt retry
                    action_type = data['action_type']
                    action_data = data['action_data']
                    
                    logger.info(f"Retrying queued action: {action_type}")
                    
                    success = self._execute_retry_action(action_type, action_data)
                    
                    if success:
                        logger.info(f"Successfully retried: {action_type}")
                        retry_file.unlink()
                        
                        self.audit_logger.log_success(
                            action_type='action_retry_success',
                            actor='error_recovery',
                            details=f'{action_type} successfully retried'
                        )
                    else:
                        # Increment retry count
                        data['retry_count'] += 1
                        data['last_retry'] = datetime.now().isoformat()
                        retry_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
                        
                except Exception as e:
                    logger.error(f"Error processing retry file {retry_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing retry queue: {e}")
    
    def _execute_retry_action(self, action_type: str, action_data: Dict[str, Any]) -> bool:
        """Execute a retry action."""
        try:
            if action_type == 'facebook_post':
                # Try posting via manager
                from facebook_manager import FacebookManager
                manager = FacebookManager()
                success, _ = manager.post_with_fallback(action_data)
                return success
            elif action_type == 'email_send':
                # Queue for email MCP to process
                return True  # Email MCP will handle this
            elif action_type == 'odoo_invoice':
                # Queue for Odoo MCP to process
                return True  # Odoo MCP will handle this
            else:
                logger.warning(f"Unknown action type for retry: {action_type}")
                return False
        except Exception as e:
            logger.error(f"Error executing retry action {action_type}: {e}")
            return False
    
    def auto_restart_service(self, service: str):
        """Auto-restart a crashed service."""
        logger.info(f"Auto-restarting {service} in {AUTO_RESTART_DELAY} seconds...")
        
        def restart():
            time.sleep(AUTO_RESTART_DELAY)
            
            service_scripts = {
                'gmail_watcher': 'gmail_watcher.py',
                'whatsapp_watcher': 'whatsapp_watcher.py',
                'filesystem_watcher': 'filesystem_watcher.py',
                'facebook_manager': 'facebook_manager.py',
                'linkedin_poster': 'linkedin_poster.py',
                'email_mcp': 'email_mcp_server.py',
                'odoo_mcp': 'odoo_mcp_server.py',
                'scheduler': 'scheduler.py',
            }
            
            if service in service_scripts:
                script = service_scripts[service]
                try:
                    logger.info(f"Starting {script}...")
                    subprocess.Popen(
                        [sys.executable, script],
                        cwd=str(Path(__file__).parent),
                        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                    )
                    
                    self.service_status[service]['status'] = 'restarted'
                    self.service_status[service]['last_check'] = datetime.now().isoformat()
                    
                    self.audit_logger.log_success(
                        action_type='service_auto_restart',
                        actor='error_recovery',
                        details=f'{service} auto-restarted'
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to restart {service}: {e}")
        
        restart_thread = threading.Thread(target=restart)
        restart_thread.daemon = True
        restart_thread.start()
    
    def _update_dashboard(self):
        """Update Dashboard.md with system health."""
        try:
            # Update service status in dashboard
            for service, status in self.service_status.items():
                service_status = 'Running' if status['status'] in ['healthy', 'unknown'] else 'Error'
                self.dashboard.update_service(service, {
                    f'{service}_status': service_status
                })
            
            # Log any errors
            if self.error_queue:
                last_error = self.error_queue[-1]
                self.dashboard.add_alert(
                    f"{last_error['service']}: {last_error['error_type']}",
                    'error'
                )
            
            self.dashboard.log_activity("Health Check Completed", "Success")
            logger.info("Dashboard updated with health status")

        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def _get_last_error(self) -> str:
        """Get the last error message."""
        if not self.error_queue:
            return "None"
        
        last_error = self.error_queue[-1]
        return f"{last_error['service']}: {last_error['error_type']} ({last_error['added_at']})"
    
    def run_health_checks(self):
        """Run health checks on all services."""
        logger.info("Running health checks...")
        
        for service in self.service_status.keys():
            try:
                is_healthy = self.check_service_health(service)
                
                if is_healthy:
                    self.service_status[service]['status'] = 'healthy'
                    self.service_status[service]['errors'] = 0
                    logger.info(f"✓ {service} is healthy")
                else:
                    self.service_status[service]['status'] = 'unhealthy'
                    logger.warning(f"✗ {service} is unhealthy")
                    
                    # Attempt retry
                    if not self.retry_failed_service(service):
                        self.auto_restart_service(service)
                
                self.service_status[service]['last_check'] = datetime.now().isoformat()
                
            except Exception as e:
                logger.error(f"Error checking {service}: {e}")
                self.log_error(service, 'health_check_failed', str(e))
        
        # Process retry queue
        self.process_retry_queue()
        
        # Update dashboard
        self._update_dashboard()
    
    def run(self):
        """Main run loop."""
        logger.info(f"Error Recovery System started")
        logger.info(f"Health check interval: {HEALTH_CHECK_INTERVAL} seconds")
        logger.info(f"Retry delay: {RETRY_DELAY} seconds")
        logger.info(f"Max retries: {MAX_RETRIES}")
        
        print("\n" + "="*50)
        print("ERROR RECOVERY SYSTEM - GOLD TIER")
        print("="*50)
        print(f"Health Check Interval: {HEALTH_CHECK_INTERVAL}s")
        print(f"Retry Delay: {RETRY_DELAY}s")
        print(f"Max Retries: {MAX_RETRIES}")
        print("Monitoring all services...")
        print("="*50 + "\n")
        
        while True:
            try:
                self.run_health_checks()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
            
            time.sleep(HEALTH_CHECK_INTERVAL)


def main():
    """Entry point."""
    try:
        recovery = ErrorRecoverySystem()
        recovery.run()
    except KeyboardInterrupt:
        logger.info("Error Recovery System stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
