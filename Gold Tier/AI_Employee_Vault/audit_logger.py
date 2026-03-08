# audit_logger.py
# Gold Tier: Comprehensive audit logging system
# Logs every action to /Logs/audit/YYYY-MM-DD.json
# Keeps logs for 90 days
# Provides weekly summary for briefings

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any

# Load environment variables
load_dotenv()

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', './AI_Employee_Vault'))
LOGS_PATH = VAULT_PATH / 'Logs'
AUDIT_PATH = LOGS_PATH / 'audit'
ERRORS_PATH = LOGS_PATH / 'errors'
RETENTION_DAYS = 90

# Ensure directories exist
AUDIT_PATH.mkdir(parents=True, exist_ok=True)
ERRORS_PATH.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_PATH / 'audit_logger.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AuditLogger:
    """Comprehensive audit logging for Gold Tier AI Employee."""
    
    def __init__(self):
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.audit_file = AUDIT_PATH / f"{self.current_date}.json"
        self._initialize_audit_file()
    
    def _initialize_audit_file(self):
        """Initialize or load today's audit file."""
        if self.audit_file.exists():
            try:
                data = json.loads(self.audit_file.read_text(encoding='utf-8'))
                self.entries = data.get('entries', [])
            except Exception as e:
                logger.warning(f"Error loading audit file: {e}")
                self.entries = []
        else:
            self.entries = []
    
    def _save_audit_file(self):
        """Save audit entries to file."""
        data = {
            'date': self.current_date,
            'created_at': datetime.now().isoformat(),
            'total_entries': len(self.entries),
            'entries': self.entries
        }
        self.audit_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def log(
        self,
        action_type: str,
        result: str,
        actor: str = 'qwen_ai',
        details: str = '',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log an audit entry.
        
        Args:
            action_type: Type of action (e.g., 'facebook_post', 'odoo_invoice', 'email_sent')
            result: Result of action ('success', 'failure', 'pending', 'dry_run')
            actor: Who/what performed the action (e.g., 'qwen_ai', 'facebook_manager', 'odoo_mcp')
            details: Human-readable description of the action
            metadata: Additional structured data about the action
        
        Returns:
            The created audit entry
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': actor,
            'result': result,
            'details': details,
            'metadata': metadata or {}
        }
        
        self.entries.append(entry)
        self._save_audit_file()
        
        logger.info(f"[AUDIT] {action_type} by {actor}: {result} - {details}")
        
        return entry
    
    def log_success(
        self,
        action_type: str,
        actor: str,
        details: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log a successful action."""
        return self.log(action_type, 'success', actor, details, metadata)
    
    def log_failure(
        self,
        action_type: str,
        actor: str,
        details: str,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log a failed action."""
        meta = metadata or {}
        if error:
            meta['error'] = error
        return self.log(action_type, 'failure', actor, details, meta)
    
    def log_pending(
        self,
        action_type: str,
        actor: str,
        details: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log a pending action awaiting approval."""
        return self.log(action_type, 'pending', actor, details, metadata)
    
    def log_dry_run(
        self,
        action_type: str,
        actor: str,
        details: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log a dry run action."""
        return self.log(action_type, 'dry_run', actor, details, metadata)
    
    def get_entries_for_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Get all audit entries for a specific date."""
        audit_file = AUDIT_PATH / f"{date_str}.json"
        if not audit_file.exists():
            return []
        
        try:
            data = json.loads(audit_file.read_text(encoding='utf-8'))
            return data.get('entries', [])
        except Exception as e:
            logger.error(f"Error reading audit file for {date_str}: {e}")
            return []
    
    def get_entries_for_period(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get all audit entries for a date range."""
        entries = []
        current = start_date
        
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            entries.extend(self.get_entries_for_date(date_str))
            current += timedelta(days=1)
        
        return entries
    
    def get_entries_by_type(
        self,
        action_type: str,
        date_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all entries of a specific action type."""
        if date_str:
            entries = self.get_entries_for_date(date_str)
        else:
            entries = self.entries
        
        return [e for e in entries if e.get('action_type') == action_type]
    
    def get_entries_by_actor(
        self,
        actor: str,
        date_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all entries by a specific actor."""
        if date_str:
            entries = self.get_entries_for_date(date_str)
        else:
            entries = self.entries
        
        return [e for e in entries if e.get('actor') == actor]
    
    def get_summary_for_date(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of audit entries for a date."""
        if date_str is None:
            entries = self.entries
        else:
            entries = self.get_entries_for_date(date_str)
        
        summary = {
            'total_actions': len(entries),
            'by_result': {},
            'by_type': {},
            'by_actor': {}
        }
        
        for entry in entries:
            result = entry.get('result', 'unknown')
            action_type = entry.get('action_type', 'unknown')
            actor = entry.get('actor', 'unknown')
            
            summary['by_result'][result] = summary['by_result'].get(result, 0) + 1
            summary['by_type'][action_type] = summary['by_type'].get(action_type, 0) + 1
            summary['by_actor'][actor] = summary['by_actor'].get(actor, 0) + 1
        
        return summary
    
    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get a summary of audit entries for the past 7 days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        entries = self.get_entries_for_period(start_date, end_date)
        
        summary = {
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'total_actions': len(entries),
            'by_result': {},
            'by_type': {},
            'by_actor': {},
            'daily_breakdown': {}
        }
        
        for entry in entries:
            result = entry.get('result', 'unknown')
            action_type = entry.get('action_type', 'unknown')
            actor = entry.get('actor', 'unknown')
            timestamp = entry.get('timestamp', '')[:10]  # YYYY-MM-DD
            
            summary['by_result'][result] = summary['by_result'].get(result, 0) + 1
            summary['by_type'][action_type] = summary['by_type'].get(action_type, 0) + 1
            summary['by_actor'][actor] = summary['by_actor'].get(actor, 0) + 1
            
            if timestamp not in summary['daily_breakdown']:
                summary['daily_breakdown'][timestamp] = 0
            summary['daily_breakdown'][timestamp] += 1
        
        return summary
    
    def cleanup_old_logs(self):
        """Remove audit logs older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        removed_count = 0
        
        for audit_file in AUDIT_PATH.glob('*.json'):
            try:
                # Extract date from filename
                date_str = audit_file.stem  # YYYY-MM-DD
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    audit_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed old audit log: {audit_file.name}")
            except Exception as e:
                logger.error(f"Error processing {audit_file.name}: {e}")
        
        if removed_count > 0:
            logger.info(f"Cleanup complete: removed {removed_count} old audit logs")
        
        return removed_count
    
    def export_audit_trail(
        self,
        output_path: Path,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Export audit trail to a file."""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        entries = self.get_entries_for_period(start_date, end_date)
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'total_entries': len(entries),
            'entries': entries
        }
        
        output_path.write_text(json.dumps(export_data, indent=2), encoding='utf-8')
        logger.info(f"Exported {len(entries)} audit entries to {output_path}")
        
        return len(entries)


# Global instance for easy import
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Convenience functions for direct use
def log_action(
    action_type: str,
    result: str,
    actor: str = 'qwen_ai',
    details: str = '',
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Log an audit action."""
    return get_audit_logger().log(action_type, result, actor, details, metadata)


def log_success(
    action_type: str,
    actor: str,
    details: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Log a successful action."""
    return get_audit_logger().log_success(action_type, actor, details, metadata)


def log_failure(
    action_type: str,
    actor: str,
    details: str,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Log a failed action."""
    return get_audit_logger().log_failure(action_type, actor, details, error, metadata)


def log_pending(
    action_type: str,
    actor: str,
    details: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Log a pending action."""
    return get_audit_logger().log_pending(action_type, actor, details, metadata)


def log_dry_run(
    action_type: str,
    actor: str,
    details: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Log a dry run action."""
    return get_audit_logger().log_dry_run(action_type, actor, details, metadata)


def get_weekly_summary() -> Dict[str, Any]:
    """Get weekly audit summary."""
    return get_audit_logger().get_weekly_summary()


def cleanup_old_logs() -> int:
    """Clean up old audit logs."""
    return get_audit_logger().cleanup_old_logs()


# Main entry point for testing
def main():
    """Test the audit logger."""
    logger = get_audit_logger()
    
    # Test logging various actions
    logger.log_success(
        action_type='system_startup',
        actor='audit_logger',
        details='Audit logger initialized successfully'
    )
    
    logger.log_success(
        action_type='facebook_post',
        actor='facebook_manager',
        details='Posted to Facebook Page via API',
        metadata={'post_id': 'test_123', 'method': 'api'}
    )
    
    logger.log_failure(
        action_type='odoo_invoice',
        actor='odoo_mcp',
        details='Failed to create draft invoice',
        error='Connection timeout'
    )
    
    logger.log_pending(
        action_type='email_approval',
        actor='email_mcp',
        details='Email awaiting human approval',
        metadata={'recipient': 'test@example.com'}
    )
    
    logger.log_dry_run(
        action_type='linkedin_post',
        actor='linkedin_poster',
        details='LinkedIn post simulated (DRY_RUN mode)'
    )
    
    # Print summary
    summary = logger.get_summary_for_date()
    print("\n=== Today's Audit Summary ===")
    print(f"Total Actions: {summary['total_actions']}")
    print(f"By Result: {summary['by_result']}")
    print(f"By Type: {summary['by_type']}")
    print(f"By Actor: {summary['by_actor']}")
    
    # Test cleanup
    removed = cleanup_old_logs()
    print(f"\nOld logs removed: {removed}")
    
    print("\nAudit logger test complete!")


if __name__ == '__main__':
    main()
