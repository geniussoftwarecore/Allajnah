import logging
from typing import Optional
from src.database.db import db
from src.models.complaint import AuditLog

class AuditLogger:
    
    def __init__(self):
        self.logger = logging.getLogger('complaints_system.audit')
    
    @staticmethod
    def log(
        action_type: str,
        performed_by_id: str,
        description: str,
        affected_user_id: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        ip_address: Optional[str] = None,
        commit: bool = True
    ):
        logger = logging.getLogger('complaints_system.audit')
        try:
            audit_entry = AuditLog()
            audit_entry.action_type = action_type
            audit_entry.performed_by_id = performed_by_id
            audit_entry.affected_user_id = affected_user_id
            audit_entry.old_value = old_value
            audit_entry.new_value = new_value
            audit_entry.description = description
            audit_entry.ip_address = ip_address
            
            db.session.add(audit_entry)
            if commit:
                db.session.commit()
            else:
                db.session.flush()
            
            logger.info(
                f"AUDIT: {action_type} by {performed_by_id} - {description}"
            )
            
            return True
        except Exception as e:
            logger.error(
                f"Failed to create audit log: {str(e)}"
            )
            db.session.rollback()
            return False
    
    @staticmethod
    def log_payment_approval(payment_id: str, reviewer_id: str, status: str, ip_address: Optional[str] = None):
        AuditLogger.log(
            action_type='payment_approval',
            performed_by_id=reviewer_id,
            description=f"Payment {payment_id} {status}",
            old_value='pending',
            new_value=status,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_user_role_change(user_id: str, admin_id: str, old_role: str, new_role: str, ip_address: Optional[str] = None):
        AuditLogger.log(
            action_type='role_change',
            performed_by_id=admin_id,
            affected_user_id=user_id,
            description=f"User role changed from {old_role} to {new_role}",
            old_value=old_role,
            new_value=new_role,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_user_status_change(user_id: str, admin_id: str, old_status: bool, new_status: bool, ip_address: Optional[str] = None):
        AuditLogger.log(
            action_type='status_change',
            performed_by_id=admin_id,
            affected_user_id=user_id,
            description=f"User status changed from {'active' if old_status else 'inactive'} to {'active' if new_status else 'inactive'}",
            old_value=str(old_status),
            new_value=str(new_status),
            ip_address=ip_address
        )
    
    @staticmethod
    def log_login(user_id: str, success: bool, ip_address: Optional[str] = None):
        AuditLogger.log(
            action_type='login_attempt',
            performed_by_id=user_id,
            description=f"Login {'successful' if success else 'failed'}",
            ip_address=ip_address
        )
    
    @staticmethod
    def log_settings_change(admin_id: str, setting_key: str, old_value: str, new_value: str, ip_address: Optional[str] = None):
        AuditLogger.log(
            action_type='settings_change',
            performed_by_id=admin_id,
            description=f"Setting {setting_key} changed",
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
