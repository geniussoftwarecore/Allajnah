from flask import Blueprint, request, current_app
from src.database.db import db
from src.models.complaint import User, Subscription, Payment, PaymentMethod, Settings, Notification
from src.routes.auth import token_required, role_required, rate_limit
from src.utils.security import validate_and_save_file, validate_payment_data
from src.utils.response import success_response, error_response
from src.services.subscription_service import create_or_extend_subscription
from src.services.scheduler import run_daily_tasks, send_renewal_reminders, check_and_expire_subscriptions
from datetime import datetime
import os

subscription_v2_bp = Blueprint('subscription_v2', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'receipts')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===================== User Endpoints =====================

@subscription_v2_bp.route('/subscription/me', methods=['GET'])
@token_required
def get_my_subscription(current_user):
    """GET /api/subscription/me → حالة اشتراك المستخدم الحالي"""
    try:
        active_subscription = Subscription.query.filter_by(
            user_id=current_user.user_id,
            status='active'
        ).filter(Subscription.end_date > datetime.utcnow()).first()
        
        pending_payment = Payment.query.filter_by(
            user_id=current_user.user_id,
            status='pending'
        ).first()
        
        data = {
            'has_active_subscription': active_subscription is not None,
            'subscription': active_subscription.to_dict() if active_subscription else None,
            'has_pending_payment': pending_payment is not None,
            'pending_payment': pending_payment.to_dict() if pending_payment else None
        }
        
        return success_response(data=data)
        
    except Exception as e:
        return error_response(error=str(e), message='خطأ في جلب حالة الاشتراك', status_code=500)

@subscription_v2_bp.route('/payments', methods=['POST'])
@token_required
@rate_limit("3 per hour")
def create_payment(current_user):
    """POST /api/payments → إنشاء إثبات دفع"""
    try:
        if 'receipt_image' not in request.files:
            return error_response(error='صورة الإيصال مطلوبة', status_code=400)
        
        file = request.files['receipt_image']
        data = request.form.to_dict()
        
        validation_errors = validate_payment_data(data)
        if validation_errors:
            return error_response(
                error=validation_errors,
                message='بيانات غير صالحة',
                status_code=400
            )
        
        method = PaymentMethod.query.get(data['method_id'])
        if not method or not method.is_active:
            return error_response(error='طريقة دفع غير صحيحة أو غير نشطة', status_code=400)
        
        success, result = validate_and_save_file(file, UPLOAD_FOLDER)
        if not success:
            return error_response(error=result.get('error', 'فشل في رفع الملف'), status_code=400)
        
        filename = result['filename']
        
        new_payment = Payment(
            user_id=current_user.user_id,
            method_id=data['method_id'],
            sender_name=data['sender_name'],
            sender_phone=data['sender_phone'],
            transaction_reference=data.get('transaction_reference', ''),
            amount=float(data['amount']),
            payment_date=datetime.fromisoformat(data['payment_date'].replace('Z', '+00:00')),
            receipt_image_path=filename,
            status='pending'
        )
        
        db.session.add(new_payment)
        db.session.flush()
        
        admin_roles = ['Technical Committee', 'Higher Committee']
        admin_users = User.query.join(User.role).filter(
            User.role.has(role_name=admin_roles[0]) | User.role.has(role_name=admin_roles[1])
        ).all()
        
        for admin in admin_users:
            notification = Notification(
                user_id=admin.user_id,
                message=f'طلب دفع جديد من {current_user.full_name} بمبلغ {data["amount"]} ريال',
                type='payment_submission'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return success_response(
            data={'payment': new_payment.to_dict()},
            message='تم إرسال إثبات الدفع بنجاح. سيتم مراجعته قريباً',
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(error=str(e), message='خطأ في إرسال الدفع', status_code=500)

@subscription_v2_bp.route('/payment-methods', methods=['GET'])
def get_payment_methods():
    """GET /api/payment-methods → قائمة طرق الدفع النشطة"""
    try:
        methods = PaymentMethod.query.filter_by(is_active=True).order_by(PaymentMethod.display_order).all()
        return success_response(data={'payment_methods': [method.to_dict() for method in methods]})
    except Exception as e:
        return error_response(error=str(e), message='خطأ في جلب طرق الدفع', status_code=500)

# ===================== Admin Endpoints =====================

@subscription_v2_bp.route('/admin/payments', methods=['GET'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def get_all_payments(current_user):
    """GET /api/admin/payments?status=pending&..."""
    try:
        status = request.args.get('status', 'pending')
        payments = Payment.query.filter_by(status=status).order_by(Payment.created_at.desc()).all()
        
        return success_response(data={'payments': [payment.to_dict() for payment in payments]})
    except Exception as e:
        return error_response(error=str(e), message='خطأ في جلب المدفوعات', status_code=500)

@subscription_v2_bp.route('/admin/payments/<payment_id>/approve', methods=['POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def approve_payment(current_user, payment_id):
    """POST /api/admin/payments/{id}/approve → يعتمد ويفعّل/يمدّد الاشتراك سنة"""
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return error_response(error='الدفع غير موجود', status_code=404)
        
        if payment.status != 'pending':
            return error_response(error='هذا الدفع تمت مراجعته بالفعل', status_code=400)
        
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        result = create_or_extend_subscription(
            user_id=payment.user_id,
            payment_id=payment_id,
            reviewed_by_id=current_user.user_id
        )
        
        if not result['success']:
            return error_response(error=result['error'], message='خطأ في اعتماد الدفع', status_code=500)
        
        if notes:
            payment.review_notes = notes
            db.session.commit()
        
        return success_response(
            data={'subscription': result['subscription']},
            message='تم اعتماد الدفع بنجاح'
        )
        
    except Exception as e:
        db.session.rollback()
        return error_response(error=str(e), message='خطأ في اعتماد الدفع', status_code=500)

@subscription_v2_bp.route('/admin/payments/<payment_id>/reject', methods=['POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def reject_payment(current_user, payment_id):
    """POST /api/admin/payments/{id}/reject مع { "admin_note": "سبب الرفض" }"""
    try:
        data = request.get_json()
        
        if not data.get('admin_note'):
            return error_response(error='سبب الرفض (admin_note) مطلوب', status_code=400)
        
        payment = Payment.query.get(payment_id)
        if not payment:
            return error_response(error='الدفع غير موجود', status_code=404)
        
        if payment.status != 'pending':
            return error_response(error='هذا الدفع تمت مراجعته بالفعل', status_code=400)
        
        payment.status = 'rejected'
        payment.reviewed_by_id = current_user.user_id
        payment.reviewed_at = datetime.utcnow()
        payment.review_notes = data['admin_note']
        
        notification = Notification(
            user_id=payment.user_id,
            message=f'تم رفض دفعتك. السبب: {data["admin_note"]}. يمكنك إعادة إرسال إثبات الدفع',
            type='payment_rejected'
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return success_response(message='تم رفض الدفع')
        
    except Exception as e:
        db.session.rollback()
        return error_response(error=str(e), message='خطأ في رفض الدفع', status_code=500)

@subscription_v2_bp.route('/admin/settings/subscription', methods=['GET', 'POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def subscription_settings(current_user):
    """GET/POST /api/admin/settings/subscription (السعر/العملة/فترة السماح)"""
    
    if request.method == 'GET':
        try:
            price = Settings.query.filter_by(key='annual_subscription_price').first()
            currency = Settings.query.filter_by(key='currency').first()
            grace_period = Settings.query.filter_by(key='grace_period_days').first()
            grace_enabled = Settings.query.filter_by(key='enable_grace_period').first()
            
            data = {
                'annual_subscription_price': float(price.value) if price else 50000,
                'currency': currency.value if currency else 'YER',
                'grace_period_days': int(grace_period.value) if grace_period else 7,
                'enable_grace_period': grace_enabled.value.lower() == 'true' if grace_enabled else True
            }
            
            return success_response(data=data)
            
        except Exception as e:
            return error_response(error=str(e), message='خطأ في جلب إعدادات الاشتراك', status_code=500)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            settings_map = {
                'annual_subscription_price': 'annual_subscription_price',
                'currency': 'currency',
                'grace_period_days': 'grace_period_days',
                'enable_grace_period': 'enable_grace_period'
            }
            
            for key, db_key in settings_map.items():
                if key in data:
                    setting = Settings.query.filter_by(key=db_key).first()
                    if setting:
                        setting.value = str(data[key])
                        setting.updated_at = datetime.utcnow()
                    else:
                        new_setting = Settings(key=db_key, value=str(data[key]))
                        db.session.add(new_setting)
            
            db.session.commit()
            
            return success_response(message='تم تحديث إعدادات الاشتراك بنجاح')
            
        except Exception as e:
            db.session.rollback()
            return error_response(error=str(e), message='خطأ في تحديث الإعدادات', status_code=500)

@subscription_v2_bp.route('/admin/payment-methods', methods=['GET', 'POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def manage_payment_methods(current_user):
    """CRUD /api/admin/payment-methods"""
    
    if request.method == 'GET':
        try:
            methods = PaymentMethod.query.order_by(PaymentMethod.display_order).all()
            return success_response(data={'payment_methods': [method.to_dict() for method in methods]})
        except Exception as e:
            return error_response(error=str(e), message='خطأ في جلب طرق الدفع', status_code=500)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            required_fields = ['name', 'account_number', 'account_holder']
            for field in required_fields:
                if field not in data:
                    return error_response(error=f'{field} مطلوب', status_code=400)
            
            new_method = PaymentMethod(
                name=data['name'],
                account_number=data['account_number'],
                account_holder=data['account_holder'],
                qr_image_path=data.get('qr_image_path', ''),
                notes=data.get('notes', ''),
                is_active=data.get('is_active', True),
                display_order=data.get('display_order', 0)
            )
            
            db.session.add(new_method)
            db.session.commit()
            
            return success_response(
                data={'method': new_method.to_dict()},
                message='تم إضافة طريقة الدفع بنجاح',
                status_code=201
            )
            
        except Exception as e:
            db.session.rollback()
            return error_response(error=str(e), message='خطأ في إضافة طريقة الدفع', status_code=500)

@subscription_v2_bp.route('/admin/payment-methods/<method_id>', methods=['PUT', 'DELETE'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def update_delete_payment_method(current_user, method_id):
    """CRUD /api/admin/payment-methods/{id}"""
    
    if request.method == 'PUT':
        try:
            method = PaymentMethod.query.get(method_id)
            if not method:
                return error_response(error='طريقة الدفع غير موجودة', status_code=404)
            
            data = request.get_json()
            
            if 'name' in data:
                method.name = data['name']
            if 'account_number' in data:
                method.account_number = data['account_number']
            if 'account_holder' in data:
                method.account_holder = data['account_holder']
            if 'qr_image_path' in data:
                method.qr_image_path = data['qr_image_path']
            if 'notes' in data:
                method.notes = data['notes']
            if 'is_active' in data:
                method.is_active = data['is_active']
            if 'display_order' in data:
                method.display_order = data['display_order']
            
            db.session.commit()
            
            return success_response(
                data={'method': method.to_dict()},
                message='تم تحديث طريقة الدفع بنجاح'
            )
            
        except Exception as e:
            db.session.rollback()
            return error_response(error=str(e), message='خطأ في تحديث طريقة الدفع', status_code=500)
    
    elif request.method == 'DELETE':
        try:
            method = PaymentMethod.query.get(method_id)
            if not method:
                return error_response(error='طريقة الدفع غير موجودة', status_code=404)
            
            db.session.delete(method)
            db.session.commit()
            
            return success_response(message='تم حذف طريقة الدفع بنجاح')
            
        except Exception as e:
            db.session.rollback()
            return error_response(error=str(e), message='خطأ في حذف طريقة الدفع', status_code=500)

# ===================== Scheduler/Cron Endpoints =====================

@subscription_v2_bp.route('/admin/tasks/daily', methods=['POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def trigger_daily_tasks(current_user):
    """تشغيل المهام اليومية (للـ cron أو trigger يدوي)"""
    try:
        results = run_daily_tasks()
        return success_response(data=results, message='تم تشغيل المهام اليومية بنجاح')
    except Exception as e:
        return error_response(error=str(e), message='خطأ في تشغيل المهام اليومية', status_code=500)

# ===================== Webhook Endpoints (اختياري) =====================

@subscription_v2_bp.route('/webhooks/payment', methods=['POST'])
def payment_webhook():
    """POST /api/webhooks/payment - للبوابات الدفع المستقبلية (اختياري)"""
    try:
        data = request.get_json()
        
        # TODO: التحقق من صحة الـ webhook signature
        # TODO: معالجة بيانات الدفع من البوابة
        # TODO: تحديث حالة الدفع تلقائياً
        
        return success_response(message='Webhook received successfully')
        
    except Exception as e:
        return error_response(error=str(e), message='خطأ في معالجة الـ webhook', status_code=500)
