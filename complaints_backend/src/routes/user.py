from flask import Blueprint, jsonify, request
from src.database.db import db
from src.models.complaint import User, Role, AuditLog, Notification
from werkzeug.security import generate_password_hash
from src.routes.auth import token_required, role_required
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def get_users(current_user):
    """Admin-only endpoint to list all users"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def create_user(current_user):
    """Admin-only endpoint to create users with specific roles"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'الحقل {field} مطلوب'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'اسم المستخدم موجود مسبقاً'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'البريد الإلكتروني موجود مسبقاً'}), 400
        
        # SECURITY: Admin can specify role, but default to Trader if not provided
        role_id = None
        if 'role_name' in data:
            role = Role.query.filter_by(role_name=data['role_name']).first()
            if role:
                role_id = role.role_id
            else:
                return jsonify({'message': 'دور غير صالح'}), 400
        elif 'role_id' in data:
            role = Role.query.filter_by(role_id=data['role_id']).first()
            if role:
                role_id = role.role_id
            else:
                return jsonify({'message': 'دور غير صالح'}), 400
        else:
            # Default to Trader role if no role specified
            default_role = Role.query.filter_by(role_name='Trader').first()
            if not default_role:
                return jsonify({'message': 'خطأ في النظام: الدور الافتراضي غير مكوَّن'}), 500
            role_id = default_role.role_id
        
        # Hash password
        hashed_password = generate_password_hash(data['password'])
        
        # Create user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password,
            full_name=data['full_name'],
            phone_number=data.get('phone_number'),
            address=data.get('address'),
            role_id=role_id
        )
        
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في إنشاء المستخدم: {str(e)}'}), 500

@user_bp.route('/users/<user_id>', methods=['GET'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def get_user(current_user, user_id):
    """Admin-only endpoint to get a specific user"""
    user = User.query.filter_by(user_id=user_id).first_or_404()
    return jsonify(user.to_dict())

@user_bp.route('/users/<user_id>', methods=['PUT'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def update_user(current_user, user_id):
    """Admin-only endpoint to update user details (not role - use /admin/users/<user_id>/role)"""
    user = User.query.filter_by(user_id=user_id).first_or_404()
    data = request.json
    
    # SECURITY: Do not allow role changes through this endpoint
    # Use the dedicated /admin/users/<user_id>/role endpoint instead
    if 'role_id' in data or 'role_name' in data:
        return jsonify({'message': 'استخدم endpoint تغيير الأدوار لتعديل دور المستخدم'}), 400
    
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.full_name = data.get('full_name', user.full_name)
    user.phone_number = data.get('phone_number', user.phone_number)
    user.address = data.get('address', user.address)
    user.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<user_id>', methods=['DELETE'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def delete_user(current_user, user_id):
    """Admin-only endpoint to delete a user"""
    # SECURITY: Prevent admins from deleting their own account
    if user_id == current_user.user_id:
        return jsonify({'message': 'لا يمكنك حذف حسابك الخاص'}), 403
    
    user = User.query.filter_by(user_id=user_id).first_or_404()
    db.session.delete(user)
    db.session.commit()
    return '', 204

# ADMIN-ONLY ENDPOINTS FOR ROLE MANAGEMENT
@user_bp.route('/admin/users', methods=['GET'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def get_all_users_admin(current_user):
    """Admin endpoint to get all users with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        role_filter = request.args.get('role')
        search = request.args.get('search', '')
        
        query = User.query
        
        # Filter by role if specified
        if role_filter:
            role = Role.query.filter_by(role_name=role_filter).first()
            if role:
                query = query.filter_by(role_id=role.role_id)
        
        # Search by username, email, or full_name
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (User.username.like(search_pattern)) |
                (User.email.like(search_pattern)) |
                (User.full_name.like(search_pattern))
            )
        
        # Paginate results
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب المستخدمين: {str(e)}'}), 500

@user_bp.route('/admin/users/<user_id>/role', methods=['PUT'])
@token_required
@role_required(['Higher Committee'])
def update_user_role(current_user, user_id):
    """Higher Committee ONLY endpoint to update a user's role - SECURITY CRITICAL"""
    try:
        data = request.get_json()
        
        if 'role_name' not in data:
            return jsonify({'message': 'اسم الدور مطلوب'}), 400
        
        # Find the user to update
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({'message': 'المستخدم غير موجود'}), 404
        
        # Prevent users from modifying their own role
        if user.user_id == current_user.user_id:
            return jsonify({'message': 'لا يمكنك تعديل دورك الخاص'}), 403
        
        # Get the new role
        new_role = Role.query.filter_by(role_name=data['role_name']).first()
        if not new_role:
            return jsonify({'message': 'دور غير صالح'}), 400
        
        # Update the user's role
        old_role_name = user.role.role_name
        user.role_id = new_role.role_id
        user.updated_at = datetime.utcnow()
        
        # Create audit log entry
        audit_log = AuditLog(
            action_type='role_change',
            performed_by_id=current_user.user_id,
            affected_user_id=user.user_id,
            old_value=old_role_name,
            new_value=new_role.role_name,
            description=f'تم تغيير دور المستخدم {user.full_name} من "{old_role_name}" إلى "{new_role.role_name}"',
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': f'تم تحديث دور المستخدم من "{old_role_name}" إلى "{new_role.role_name}" بنجاح',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تحديث دور المستخدم: {str(e)}'}), 500

@user_bp.route('/admin/users/<user_id>/toggle-status', methods=['PUT'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def toggle_user_status(current_user, user_id):
    """Admin endpoint to activate/deactivate a user account"""
    try:
        # Find the user
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({'message': 'المستخدم غير موجود'}), 404
        
        # Prevent users from deactivating their own account
        if user.user_id == current_user.user_id:
            return jsonify({'message': 'لا يمكنك تعديل حالة حسابك الخاص'}), 403
        
        # Toggle the is_active status
        old_status = 'نشط' if user.is_active else 'غير نشط'
        user.is_active = not user.is_active
        new_status = 'نشط' if user.is_active else 'غير نشط'
        user.updated_at = datetime.utcnow()
        
        # Create audit log
        audit_log = AuditLog(
            action_type='status_change',
            performed_by_id=current_user.user_id,
            affected_user_id=user.user_id,
            old_value=old_status,
            new_value=new_status,
            description=f'تم تغيير حالة حساب {user.full_name} من "{old_status}" إلى "{new_status}"',
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        return jsonify({
            'message': f'تم {new_status} حساب المستخدم بنجاح',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تحديث حالة المستخدم: {str(e)}'}), 500

# AUDIT LOG ENDPOINTS
@user_bp.route('/admin/audit-logs', methods=['GET'])
@token_required
@role_required(['Higher Committee'])
def get_audit_logs(current_user):
    """Higher Committee ONLY endpoint to view audit logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        action_type = request.args.get('action_type')
        affected_user_id = request.args.get('affected_user_id')
        
        query = AuditLog.query
        
        # Filter by action type if specified
        if action_type:
            query = query.filter_by(action_type=action_type)
        
        # Filter by affected user if specified
        if affected_user_id:
            query = query.filter_by(affected_user_id=affected_user_id)
        
        # Paginate results (newest first)
        pagination = query.order_by(AuditLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب سجل التدقيق: {str(e)}'}), 500

@user_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    """Get current user's notifications"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        query = Notification.query.filter_by(user_id=current_user.user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        pagination = query.order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        unread_count = Notification.query.filter_by(
            user_id=current_user.user_id,
            is_read=False
        ).count()
        
        return jsonify({
            'notifications': [notif.to_dict() for notif in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'unread_count': unread_count
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب الإشعارات: {str(e)}'}), 500

@user_bp.route('/notifications/<notification_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(current_user, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({'message': 'الإشعار غير موجود'}), 404
        
        if notification.user_id != current_user.user_id:
            return jsonify({'message': 'غير مصرح'}), 403
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({
            'message': 'تم تحديد الإشعار كمقروء',
            'notification': notification.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تحديث الإشعار: {str(e)}'}), 500

@user_bp.route('/notifications/mark-all-read', methods=['PUT'])
@token_required
def mark_all_notifications_read(current_user):
    """Mark all notifications as read"""
    try:
        Notification.query.filter_by(
            user_id=current_user.user_id,
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        
        return jsonify({'message': 'تم تحديد جميع الإشعارات كمقروءة'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تحديث الإشعارات: {str(e)}'}), 500
