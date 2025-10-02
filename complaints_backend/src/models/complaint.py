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
    
    # Relationships
    complaints_submitted = db.relationship('Complaint', foreign_keys='Complaint.trader_id', backref='trader', lazy=True)
    complaints_assigned = db.relationship('Complaint', foreign_keys='Complaint.assigned_to_committee_id', backref='assigned_committee_member', lazy=True)
    comments = db.relationship('ComplaintComment', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='recipient', lazy=True)
    
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
            'is_active': self.is_active
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
