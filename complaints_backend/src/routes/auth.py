from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from functools import wraps
from src.models.complaint import db, User, Role

auth_bp = Blueprint('auth', __name__)

def rate_limit(limit_string):
    """Decorator wrapper for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                limiter = current_app.limiter
                return limiter.limit(limit_string)(f)(*args, **kwargs)
            except AttributeError:
                return f(*args, **kwargs)
        return decorated_function
    return decorator

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer TOKEN
            except IndexError:
                return jsonify({'message': 'تنسيق رمز التوثيق غير صالح'}), 401
        
        if not token:
            return jsonify({'message': 'رمز التوثيق مفقود'}), 401
        
        try:
            from flask import current_app
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(user_id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'رمز التوثيق غير صالح'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'انتهت صلاحية رمز التوثيق'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'رمز التوثيق غير صالح'}), 401
        
        subscription_exempt_routes = [
            '/api/subscription/status',
            '/api/subscription/me',
            '/api/payment-methods',
            '/api/subscription-price',
            '/api/payment/submit',
            '/api/payment/receipt',
            '/api/payments',
            '/api/renewal/check'
        ]
        
        if current_user.role.role_name == 'Trader':
            if not any(request.path.startswith(route) for route in subscription_exempt_routes):
                from src.models.complaint import Subscription, Settings
                
                active_subscription = Subscription.query.filter_by(
                    user_id=current_user.user_id,
                    status='active'
                ).order_by(Subscription.end_date.desc()).first()
                
                if not active_subscription:
                    return jsonify({
                        'message': 'يجب تفعيل الاشتراك للوصول إلى هذه الميزة',
                        'requires_subscription': True
                    }), 403
                
                grace_period_setting = Settings.query.filter_by(key='grace_period_days').first()
                grace_period_days = int(grace_period_setting.value) if grace_period_setting else 7
                
                enable_grace_period = Settings.query.filter_by(key='enable_grace_period').first()
                grace_enabled = enable_grace_period.value.lower() == 'true' if enable_grace_period else True
                
                if active_subscription.end_date < datetime.utcnow():
                    if grace_enabled and active_subscription.grace_period_enabled:
                        grace_end = active_subscription.end_date + timedelta(days=grace_period_days)
                        if datetime.utcnow() > grace_end:
                            return jsonify({
                                'message': 'انتهت فترة السماح. يجب تجديد الاشتراك للوصول إلى هذه الميزة',
                                'requires_subscription': True,
                                'grace_period_expired': True
                            }), 403
                    else:
                        return jsonify({
                            'message': 'انتهى الاشتراك. يجب التجديد للوصول إلى هذه الميزة',
                            'requires_subscription': True
                        }), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if current_user.role.role_name not in required_roles:
                return jsonify({'message': 'صلاحيات غير كافية'}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator

def subscription_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role.role_name == 'Trader':
            from src.models.complaint import Subscription
            active_subscription = Subscription.query.filter_by(
                user_id=current_user.user_id,
                status='active'
            ).filter(Subscription.end_date > datetime.utcnow()).first()
            
            if not active_subscription:
                return jsonify({
                    'message': 'يجب تفعيل الاشتراك للوصول إلى هذه الميزة',
                    'requires_subscription': True
                }), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
@rate_limit("5 per hour")
def register():
    try:
        data = request.get_json()
        
        # Validate required fields (role_name removed - enforced by server)
        required_fields = ['username', 'email', 'password', 'full_name']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'message': f'الحقول التالية مطلوبة: {", ".join(missing_fields)}'
            }), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'اسم المستخدم موجود بالفعل'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'البريد الإلكتروني موجود بالفعل'}), 400
        
        # SECURITY: Always assign default "Trader" role to new registrations
        # Ignore any role data from client to prevent privilege escalation
        default_role = Role.query.filter_by(role_name='Trader').first()
        if not default_role:
            return jsonify({'message': 'خطأ في النظام: الدور الافتراضي غير مكوَّن'}), 500
        
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
            'message': 'تم إنشاء الحساب بنجاح',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في إنشاء المستخدم: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
@rate_limit("10 per minute")
def login():
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'message': 'اسم المستخدم وكلمة المرور مطلوبان'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            if not user.is_active:
                return jsonify({'message': 'الحساب غير نشط'}), 401
            
            # Check if 2FA is enabled
            if user.two_factor_enabled:
                # Return response requiring 2FA
                return jsonify({
                    'requires_2fa': True,
                    'message': 'يرجى إدخال رمز المصادقة الثنائية',
                    'username': user.username
                }), 200
            
            # No 2FA, proceed with login
            from flask import current_app
            token = jwt.encode({
                'user_id': user.user_id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'requires_2fa': False,
                'message': 'تم تسجيل الدخول بنجاح',
                'token': token,
                'user': user.to_dict()
            }), 200
        
        return jsonify({'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401
        
    except Exception as e:
        return jsonify({'message': f'خطأ أثناء تسجيل الدخول: {str(e)}'}), 500

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
                return jsonify({'message': 'البريد الإلكتروني مستخدم مسبقاً'}), 400
            current_user.email = data['email']
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'تم تحديث الملف الشخصي بنجاح',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تحديث الملف الشخصي: {str(e)}'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    try:
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'message': 'كلمة المرور الحالية والجديدة مطلوبتان'}), 400
        
        if not check_password_hash(current_user.password_hash, data['current_password']):
            return jsonify({'message': 'كلمة المرور الحالية غير صحيحة'}), 400
        
        current_user.password_hash = generate_password_hash(data['new_password'])
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'تم تغيير كلمة المرور بنجاح'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تغيير كلمة المرور: {str(e)}'}), 500

@auth_bp.route('/roles', methods=['GET'])
def get_roles():
    try:
        roles = Role.query.all()
        return jsonify({
            'roles': [role.to_dict() for role in roles]
        }), 200
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب الأدوار: {str(e)}'}), 500

# 2FA ENDPOINTS
@auth_bp.route('/2fa/enable', methods=['POST'])
@token_required
def enable_2fa(current_user):
    """Enable 2FA for the current user"""
    try:
        if current_user.two_factor_enabled:
            return jsonify({'message': 'المصادقة الثنائية مفعلة بالفعل'}), 400
        
        # Generate a new secret
        secret = pyotp.random_base32()
        current_user.two_factor_secret = secret
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=current_user.email,
            issuer_name='نظام الشكاوى الإلكتروني'
        )
        
        # Create QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        db.session.commit()
        
        return jsonify({
            'message': 'تم إنشاء مفتاح المصادقة الثنائية. يرجى مسح رمز QR باستخدام تطبيق المصادقة',
            'secret': secret,
            'qr_code': f'data:image/png;base64,{img_str}',
            'manual_entry': provisioning_uri
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تفعيل المصادقة الثنائية: {str(e)}'}), 500

@auth_bp.route('/2fa/verify', methods=['POST'])
@token_required
def verify_2fa_setup(current_user):
    """Verify 2FA setup with a code"""
    try:
        data = request.get_json()
        
        if 'code' not in data:
            return jsonify({'message': 'رمز التحقق مطلوب'}), 400
        
        if not current_user.two_factor_secret:
            return jsonify({'message': 'لم يتم إعداد المصادقة الثنائية'}), 400
        
        # Verify the code
        totp = pyotp.TOTP(current_user.two_factor_secret)
        if totp.verify(data['code']):
            current_user.two_factor_enabled = True
            db.session.commit()
            return jsonify({'message': 'تم تفعيل المصادقة الثنائية بنجاح'}), 200
        else:
            return jsonify({'message': 'رمز التحقق غير صحيح'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في التحقق: {str(e)}'}), 500

@auth_bp.route('/2fa/disable', methods=['POST'])
@token_required
def disable_2fa(current_user):
    """Disable 2FA for the current user"""
    try:
        data = request.get_json()
        
        if not current_user.two_factor_enabled:
            return jsonify({'message': 'المصادقة الثنائية غير مفعلة'}), 400
        
        # Verify password before disabling
        if 'password' not in data:
            return jsonify({'message': 'كلمة المرور مطلوبة لإيقاف المصادقة الثنائية'}), 400
        
        if not check_password_hash(current_user.password_hash, data['password']):
            return jsonify({'message': 'كلمة المرور غير صحيحة'}), 401
        
        current_user.two_factor_enabled = False
        current_user.two_factor_secret = None
        db.session.commit()
        
        return jsonify({'message': 'تم إيقاف المصادقة الثنائية بنجاح'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في إيقاف المصادقة الثنائية: {str(e)}'}), 500

@auth_bp.route('/2fa/validate', methods=['POST'])
@rate_limit("10 per minute")
def validate_2fa():
    """Validate 2FA code during login"""
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('code'):
            return jsonify({'message': 'اسم المستخدم ورمز التحقق مطلوبان'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.two_factor_enabled:
            return jsonify({'message': 'بيانات غير صحيحة'}), 401
        
        # Verify the 2FA code
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(data['code']):
            from flask import current_app
            token = jwt.encode({
                'user_id': user.user_id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'message': 'تم تسجيل الدخول بنجاح',
                'token': token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'message': 'رمز التحقق غير صحيح'}), 401
        
    except Exception as e:
        return jsonify({'message': f'خطأ في التحقق: {str(e)}'}), 500
