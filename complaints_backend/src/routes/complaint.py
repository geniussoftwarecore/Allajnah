from flask import Blueprint, request, jsonify
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from src.models.complaint import db, Complaint, ComplaintCategory, ComplaintStatus, ComplaintAttachment, ComplaintComment, Notification, User
from src.routes.auth import token_required, role_required, subscription_required

complaint_bp = Blueprint('complaint', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_notification(user_id, complaint_id, message, notification_type):
    """Helper function to create notifications"""
    try:
        notification = Notification(
            user_id=user_id,
            complaint_id=complaint_id,
            message=message,
            type=notification_type
        )
        db.session.add(notification)
        return True
    except Exception as e:
        print(f"Error creating notification: {str(e)}")
        return False

@complaint_bp.route('/complaints', methods=['POST'])
@token_required
@role_required(['Trader'])
@subscription_required
def create_complaint(current_user):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description', 'category_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400
        
        # Validate category exists
        category = ComplaintCategory.query.get(data['category_id'])
        if not category:
            return jsonify({'message': 'Invalid category'}), 400
        
        # Get default status (assuming 'جديدة' is the default)
        default_status = ComplaintStatus.query.filter_by(status_name='جديدة').first()
        if not default_status:
            return jsonify({'message': 'Default status not found'}), 500
        
        # Create new complaint
        new_complaint = Complaint(
            trader_id=current_user.user_id,
            title=data['title'],
            description=data['description'],
            category_id=data['category_id'],
            status_id=default_status.status_id,
            priority=data.get('priority', 'Medium')
        )
        
        db.session.add(new_complaint)
        db.session.flush()  # Get the complaint_id
        
        # Create notification for technical committee members
        technical_committee_members = User.query.join(User.role).filter_by(role_name='Technical Committee').all()
        for member in technical_committee_members:
            create_notification(
                member.user_id,
                new_complaint.complaint_id,
                f'شكوى جديدة تم تقديمها: {new_complaint.title}',
                'new_complaint'
            )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Complaint created successfully',
            'complaint': new_complaint.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating complaint: {str(e)}'}), 500

@complaint_bp.route('/complaints', methods=['GET'])
@token_required
@subscription_required
def get_complaints(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_id = request.args.get('status_id', type=int)
        category_id = request.args.get('category_id', type=int)
        priority = request.args.get('priority')
        search = request.args.get('search')
        
        # Build query based on user role
        query = Complaint.query
        
        if current_user.role.role_name == 'Trader':
            # Traders can only see their own complaints
            query = query.filter_by(trader_id=current_user.user_id)
        elif current_user.role.role_name == 'Technical Committee':
            # Technical committee can see all complaints or assigned ones
            assigned_only = request.args.get('assigned_only', 'false').lower() == 'true'
            if assigned_only:
                query = query.filter_by(assigned_to_committee_id=current_user.user_id)
        # Higher Committee can see all complaints (no additional filter)
        
        # Apply filters
        if status_id:
            query = query.filter_by(status_id=status_id)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if priority:
            query = query.filter_by(priority=priority)
        if search:
            query = query.filter(
                (Complaint.title.contains(search)) |
                (Complaint.description.contains(search))
            )
        
        # Order by submission date (newest first)
        query = query.order_by(Complaint.submitted_at.desc())
        
        # Paginate
        complaints = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'complaints': [complaint.to_dict() for complaint in complaints.items],
            'total': complaints.total,
            'pages': complaints.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching complaints: {str(e)}'}), 500

@complaint_bp.route('/complaints/<complaint_id>', methods=['GET'])
@token_required
def get_complaint(current_user, complaint_id):
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'message': 'Complaint not found'}), 404
        
        # Check permissions
        if (current_user.role.role_name == 'Trader' and 
            complaint.trader_id != current_user.user_id):
            return jsonify({'message': 'Access denied'}), 403
        
        # Get complaint details with comments and attachments
        complaint_data = complaint.to_dict()
        complaint_data['comments'] = [comment.to_dict() for comment in complaint.comments]
        complaint_data['attachments'] = [attachment.to_dict() for attachment in complaint.attachments]
        
        return jsonify({'complaint': complaint_data}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching complaint: {str(e)}'}), 500

@complaint_bp.route('/complaints/<complaint_id>/status', methods=['PUT'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def update_complaint_status(current_user, complaint_id):
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'message': 'Complaint not found'}), 404
        
        data = request.get_json()
        if 'status_id' not in data:
            return jsonify({'message': 'status_id is required'}), 400
        
        # Validate status exists
        status = ComplaintStatus.query.get(data['status_id'])
        if not status:
            return jsonify({'message': 'Invalid status'}), 400
        
        old_status = complaint.status.status_name
        complaint.status_id = data['status_id']
        complaint.last_updated_at = datetime.utcnow()
        
        # If status is closed, set closed_at
        if status.status_name in ['مكتملة', 'مرفوضة']:
            complaint.closed_at = datetime.utcnow()
            if 'resolution_details' in data:
                complaint.resolution_details = data['resolution_details']
        
        # Create notification for trader
        create_notification(
            complaint.trader_id,
            complaint.complaint_id,
            f'تم تحديث حالة شكواك من "{old_status}" إلى "{status.status_name}"',
            'status_update'
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Complaint status updated successfully',
            'complaint': complaint.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating complaint status: {str(e)}'}), 500

@complaint_bp.route('/complaints/<complaint_id>/assign', methods=['PUT'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def assign_complaint(current_user, complaint_id):
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'message': 'Complaint not found'}), 404
        
        data = request.get_json()
        if 'assigned_to_committee_id' not in data:
            return jsonify({'message': 'assigned_to_committee_id is required'}), 400
        
        # Validate committee member exists and has correct role
        committee_member = User.query.get(data['assigned_to_committee_id'])
        if not committee_member or committee_member.role.role_name != 'Technical Committee':
            return jsonify({'message': 'Invalid committee member'}), 400
        
        complaint.assigned_to_committee_id = data['assigned_to_committee_id']
        complaint.last_updated_at = datetime.utcnow()
        
        # Create notifications
        create_notification(
            committee_member.user_id,
            complaint.complaint_id,
            f'تم تعيين شكوى جديدة لك: {complaint.title}',
            'assignment'
        )
        
        create_notification(
            complaint.trader_id,
            complaint.complaint_id,
            f'تم تعيين شكواك لعضو اللجنة الفنية: {committee_member.full_name}',
            'assignment'
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Complaint assigned successfully',
            'complaint': complaint.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error assigning complaint: {str(e)}'}), 500

@complaint_bp.route('/complaints/<complaint_id>/comments', methods=['POST'])
@token_required
def add_comment(current_user, complaint_id):
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'message': 'Complaint not found'}), 404
        
        # Check permissions
        if (current_user.role.role_name == 'Trader' and 
            complaint.trader_id != current_user.user_id):
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        if 'comment_text' not in data:
            return jsonify({'message': 'comment_text is required'}), 400
        
        new_comment = ComplaintComment(
            complaint_id=complaint_id,
            user_id=current_user.user_id,
            comment_text=data['comment_text']
        )
        
        db.session.add(new_comment)
        
        # Create notification for relevant parties
        if current_user.role.role_name == 'Trader':
            # Notify assigned committee member and other committee members
            if complaint.assigned_to_committee_id:
                create_notification(
                    complaint.assigned_to_committee_id,
                    complaint.complaint_id,
                    f'تعليق جديد من التاجر على الشكوى: {complaint.title}',
                    'new_comment'
                )
        else:
            # Notify trader
            create_notification(
                complaint.trader_id,
                complaint.complaint_id,
                f'تعليق جديد من اللجنة على شكواك: {complaint.title}',
                'new_comment'
            )
        
        complaint.last_updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': new_comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error adding comment: {str(e)}'}), 500

@complaint_bp.route('/categories', methods=['GET'])
@token_required
def get_categories(current_user):
    try:
        categories = ComplaintCategory.query.all()
        return jsonify({
            'categories': [category.to_dict() for category in categories]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching categories: {str(e)}'}), 500

@complaint_bp.route('/statuses', methods=['GET'])
@token_required
def get_statuses(current_user):
    try:
        statuses = ComplaintStatus.query.all()
        return jsonify({
            'statuses': [status.to_dict() for status in statuses]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching statuses: {str(e)}'}), 500

@complaint_bp.route('/dashboard/stats', methods=['GET'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def get_dashboard_stats(current_user):
    try:
        # Basic statistics
        total_complaints = Complaint.query.count()
        
        # Status distribution
        status_stats = db.session.query(
            ComplaintStatus.status_name,
            db.func.count(Complaint.complaint_id).label('count')
        ).join(Complaint).group_by(ComplaintStatus.status_name).all()
        
        # Category distribution
        category_stats = db.session.query(
            ComplaintCategory.category_name,
            db.func.count(Complaint.complaint_id).label('count')
        ).join(Complaint).group_by(ComplaintCategory.category_name).all()
        
        # Priority distribution
        priority_stats = db.session.query(
            Complaint.priority,
            db.func.count(Complaint.complaint_id).label('count')
        ).group_by(Complaint.priority).all()
        
        # Recent complaints (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_complaints = Complaint.query.filter(
            Complaint.submitted_at >= thirty_days_ago
        ).count()
        
        return jsonify({
            'total_complaints': total_complaints,
            'recent_complaints': recent_complaints,
            'status_distribution': [{'status': s[0], 'count': s[1]} for s in status_stats],
            'category_distribution': [{'category': c[0], 'count': c[1]} for c in category_stats],
            'priority_distribution': [{'priority': p[0], 'count': p[1]} for p in priority_stats]
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching dashboard stats: {str(e)}'}), 500
