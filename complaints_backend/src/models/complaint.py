from datetime import datetime
import uuid
from src.database.db import db

class Role(db.Model):
    __tablename__ = 'roles'
    
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationship
    users = db.relationship('User', backref='role', lazy=True)
    
    def to_dict(self):
        return {
            'role_id': self.role_id,
            'role_name': self.role_name,
            'description': self.description
        }

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(50))
    address = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 2FA fields
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    
    # Relationships
    complaints_submitted = db.relationship('Complaint', foreign_keys='Complaint.trader_id', backref='trader', lazy=True)
    complaints_assigned = db.relationship('Complaint', foreign_keys='Complaint.assigned_to_committee_id', backref='assigned_committee_member', lazy=True)
    comments = db.relationship('ComplaintComment', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='recipient', lazy=True)
    audit_logs_performed = db.relationship('AuditLog', foreign_keys='AuditLog.performed_by_id', backref='performed_by', lazy=True)
    audit_logs_affected = db.relationship('AuditLog', foreign_keys='AuditLog.affected_user_id', backref='affected_user', lazy=True)
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone_number': self.phone_number,
            'address': self.address,
            'role_id': self.role_id,
            'role_name': self.role.role_name if self.role else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'two_factor_enabled': self.two_factor_enabled
        }

class ComplaintCategory(db.Model):
    __tablename__ = 'complaint_categories'
    
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationship
    complaints = db.relationship('Complaint', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'category_id': self.category_id,
            'category_name': self.category_name,
            'description': self.description
        }

class ComplaintStatus(db.Model):
    __tablename__ = 'complaint_statuses'
    
    status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationship
    complaints = db.relationship('Complaint', backref='status', lazy=True)
    
    def to_dict(self):
        return {
            'status_id': self.status_id,
            'status_name': self.status_name,
            'description': self.description
        }

class Complaint(db.Model):
    __tablename__ = 'complaints'
    
    complaint_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trader_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('complaint_categories.category_id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('complaint_statuses.status_id'), nullable=False)
    priority = db.Column(db.String(50), default='Medium')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to_committee_id = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    resolution_details = db.Column(db.Text)
    closed_at = db.Column(db.DateTime)
    
    # Relationships
    attachments = db.relationship('ComplaintAttachment', backref='complaint', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('ComplaintComment', backref='complaint', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='related_complaint', lazy=True)
    
    def to_dict(self):
        return {
            'complaint_id': self.complaint_id,
            'trader_id': self.trader_id,
            'trader_name': self.trader.full_name if self.trader else None,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.category_name if self.category else None,
            'status_id': self.status_id,
            'status_name': self.status.status_name if self.status else None,
            'priority': self.priority,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'last_updated_at': self.last_updated_at.isoformat() if self.last_updated_at else None,
            'assigned_to_committee_id': self.assigned_to_committee_id,
            'assigned_committee_member_name': self.assigned_committee_member.full_name if self.assigned_committee_member else None,
            'resolution_details': self.resolution_details,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'attachments_count': len(self.attachments),
            'comments_count': len(self.comments)
        }

class ComplaintAttachment(db.Model):
    __tablename__ = 'complaint_attachments'
    
    attachment_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = db.Column(db.String(36), db.ForeignKey('complaints.complaint_id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'attachment_id': self.attachment_id,
            'complaint_id': self.complaint_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }

class ComplaintComment(db.Model):
    __tablename__ = 'complaint_comments'
    
    comment_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = db.Column(db.String(36), db.ForeignKey('complaints.complaint_id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'comment_id': self.comment_id,
            'complaint_id': self.complaint_id,
            'user_id': self.user_id,
            'author_name': self.author.full_name if self.author else None,
            'author_role': self.author.role.role_name if self.author and self.author.role else None,
            'comment_text': self.comment_text,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    complaint_id = db.Column(db.String(36), db.ForeignKey('complaints.complaint_id'))
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'complaint_id': self.complaint_id,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    log_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_type = db.Column(db.String(100), nullable=False)  # e.g., 'role_change', 'user_created', 'user_deleted', 'status_change'
    performed_by_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    affected_user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'log_id': self.log_id,
            'action_type': self.action_type,
            'performed_by_id': self.performed_by_id,
            'performed_by_name': self.performed_by.full_name if self.performed_by else None,
            'affected_user_id': self.affected_user_id,
            'affected_user_name': self.affected_user.full_name if self.affected_user else None,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'description': self.description,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    subscription_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    plan = db.Column(db.String(50), default='annual')
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')
    is_renewal = db.Column(db.Boolean, default=False)
    renewed_from = db.Column(db.String(36), db.ForeignKey('subscriptions.subscription_id'), nullable=True)
    grace_period_enabled = db.Column(db.Boolean, default=True)
    notified_14d = db.Column(db.Boolean, default=False)
    notified_7d = db.Column(db.Boolean, default=False)
    notified_3d = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='subscriptions', lazy=True)
    previous_subscription = db.relationship('Subscription', remote_side=[subscription_id], backref='renewals', lazy=True)
    
    def to_dict(self):
        return {
            'subscription_id': self.subscription_id,
            'user_id': self.user_id,
            'plan': self.plan,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'is_renewal': self.is_renewal,
            'renewed_from': self.renewed_from,
            'grace_period_enabled': self.grace_period_enabled,
            'notified_14d': self.notified_14d,
            'notified_7d': self.notified_7d,
            'notified_3d': self.notified_3d,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    
    method_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    account_number = db.Column(db.String(255), nullable=False)
    account_holder = db.Column(db.String(255), nullable=False)
    qr_image_path = db.Column(db.String(500))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'method_id': self.method_id,
            'name': self.name,
            'account_number': self.account_number,
            'account_holder': self.account_holder,
            'qr_image_path': self.qr_image_path,
            'notes': self.notes,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    
    payment_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    method_id = db.Column(db.String(36), db.ForeignKey('payment_methods.method_id'), nullable=False)
    sender_name = db.Column(db.String(255), nullable=False)
    sender_phone = db.Column(db.String(50), nullable=False)
    transaction_reference = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='YER')
    payment_date = db.Column(db.DateTime, nullable=False)
    receipt_image_path = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='pending')
    reviewed_by_id = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    review_notes = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='payments')
    payment_method = db.relationship('PaymentMethod', backref='payments')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    
    def to_dict(self):
        return {
            'payment_id': self.payment_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'method_id': self.method_id,
            'method_name': self.payment_method.name if self.payment_method else None,
            'sender_name': self.sender_name,
            'sender_phone': self.sender_phone,
            'transaction_reference': self.transaction_reference,
            'amount': self.amount,
            'currency': self.currency,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'receipt_image_path': self.receipt_image_path,
            'status': self.status,
            'reviewed_by_id': self.reviewed_by_id,
            'reviewed_by_name': self.reviewed_by.full_name if self.reviewed_by else None,
            'review_notes': self.review_notes,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Settings(db.Model):
    __tablename__ = 'settings'
    
    setting_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'setting_id': self.setting_id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
