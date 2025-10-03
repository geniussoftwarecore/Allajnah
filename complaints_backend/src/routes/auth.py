from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from src.models.complaint import db, User, Role

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer TOKEN
            except IndexError:
                return jsonify({'message': 'Token format invalid'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            from flask import current_app
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(user_id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'Token is invalid'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if current_user.role.role_name not in required_roles:
                return jsonify({'message': 'Insufficient permissions'}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields (role_name removed - enforced by server)
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} is required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        # SECURITY: Always assign default "Trader" role to new registrations
        # Ignore any role data from client to prevent privilege escalation
        default_role = Role.query.filter_by(role_name='Trader').first()
        if not default_role:
            return jsonify({'message': 'System error: Default role not configured'}), 500
        
        # Create new user with default Trader role
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password,
            full_name=data['full_name'],
            phone_number=data.get('phone_number'),
            address=data.get('address'),
            role_id=default_role.role_id  # Always use default Trader role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            if not user.is_active:
                return jsonify({'message': 'Account is deactivated'}), 401
            
            from flask import current_app
            token = jwt.encode({
                'user_id': user.user_id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': user.to_dict()
            }), 200
        
        return jsonify({'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'message': f'Error during login: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    try:
        data = request.get_json()
        
        # Update allowed fields
        if 'full_name' in data:
            current_user.full_name = data['full_name']
        if 'phone_number' in data:
            current_user.phone_number = data['phone_number']
        if 'address' in data:
            current_user.address = data['address']
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.user_id != current_user.user_id:
                return jsonify({'message': 'Email already exists'}), 400
            current_user.email = data['email']
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating profile: {str(e)}'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    try:
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'message': 'Current password and new password are required'}), 400
        
        if not check_password_hash(current_user.password_hash, data['current_password']):
            return jsonify({'message': 'Current password is incorrect'}), 400
        
        current_user.password_hash = generate_password_hash(data['new_password'])
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error changing password: {str(e)}'}), 500

@auth_bp.route('/roles', methods=['GET'])
def get_roles():
    try:
        roles = Role.query.all()
        return jsonify({
            'roles': [role.to_dict() for role in roles]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching roles: {str(e)}'}), 500
