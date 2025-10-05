from flask import Blueprint, request, jsonify, current_app
from src.database.db import db
from src.models.complaint import User, Subscription, Payment, PaymentMethod, Settings, Notification
from src.routes.auth import token_required, role_required, rate_limit
from src.utils.security import validate_and_save_file, validate_payment_data
from datetime import datetime, timedelta
import os

subscription_bp = Blueprint('subscription', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'receipts')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@subscription_bp.route('/subscription/status', methods=['GET'])
@token_required
def get_subscription_status(current_user):
    try:
        active_subscription = Subscription.query.filter_by(
            user_id=current_user.user_id,
            status='active'
        ).filter(Subscription.end_date > datetime.utcnow()).first()
        
        pending_payment = Payment.query.filter_by(
            user_id=current_user.user_id,
            status='pending'
        ).first()
        
        return jsonify({
            'has_active_subscription': active_subscription is not None,
            'subscription': active_subscription.to_dict() if active_subscription else None,
            'has_pending_payment': pending_payment is not None,
            'pending_payment': pending_payment.to_dict() if pending_payment else None
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب حالة الاشتراك: {str(e)}'}), 500

@subscription_bp.route('/payment-methods', methods=['GET'])
def get_payment_methods():
    try:
        methods = PaymentMethod.query.filter_by(is_active=True).order_by(PaymentMethod.display_order).all()
        return jsonify({
            'payment_methods': [method.to_dict() for method in methods]
        }), 200
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب طرق الدفع: {str(e)}'}), 500

@subscription_bp.route('/subscription-price', methods=['GET'])
def get_subscription_price():
    try:
        price_setting = Settings.query.filter_by(key='annual_subscription_price').first()
        if not price_setting:
            price_setting = Settings(
                key='annual_subscription_price',
                value='50000',
                description='سعر الاشتراك السنوي بالريال اليمني'
            )
            db.session.add(price_setting)
            db.session.commit()
        
        return jsonify({
            'price': float(price_setting.value),
            'currency': 'YER'
        }), 200
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب سعر الاشتراك: {str(e)}'}), 500

@subscription_bp.route('/payment/submit', methods=['POST'])
@token_required
@rate_limit("3 per hour")
def submit_payment(current_user):
    try:
        if 'receipt_image' not in request.files:
            return jsonify({'message': 'صورة الإيصال مطلوبة'}), 400
        
        file = request.files['receipt_image']
        data = request.form.to_dict()
        
        validation_errors = validate_payment_data(data)
        if validation_errors:
            return jsonify({
                'message': 'بيانات غير صالحة',
                'errors': validation_errors
            }), 400
        
        method = PaymentMethod.query.get(data['method_id'])
        if not method or not method.is_active:
            return jsonify({'message': 'طريقة دفع غير صحيحة أو غير نشطة'}), 400
        
        success, result = validate_and_save_file(file, UPLOAD_FOLDER)
        if not success:
            return jsonify({'message': result.get('error', 'فشل في رفع الملف')}), 400
        
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
        admin_users = User.query.join(User.role).filter(User.role.has(role_name=admin_roles[0]) | User.role.has(role_name=admin_roles[1])).all()
        
        for admin in admin_users:
            notification = Notification(
                user_id=admin.user_id,
                message=f'طلب دفع جديد من {current_user.full_name} بمبلغ {data["amount"]} ريال',
                type='payment_submission'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'message': 'تم إرسال إثبات الدفع بنجاح. سيتم مراجعته قريباً',
            'payment': new_payment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في إرسال الدفع: {str(e)}'}), 500

@subscription_bp.route('/payment/receipt/<path:filename>', methods=['GET'])
@token_required
def get_receipt(current_user, filename):
    from flask import send_from_directory
    try:
        payment = Payment.query.filter_by(receipt_image_path=filename).first()
        
        if not payment:
            return jsonify({'message': 'الملف غير موجود'}), 404
        
        is_admin = current_user.role.role_name in ['Technical Committee', 'Higher Committee']
        is_owner = payment.user_id == current_user.user_id
        
        if not (is_admin or is_owner):
            return jsonify({'message': 'غير مصرح بالوصول'}), 403
        
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        return jsonify({'message': 'الملف غير موجود'}), 404

@subscription_bp.route('/admin/payments', methods=['GET'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def get_all_payments(current_user):
    try:
        status = request.args.get('status', 'pending')
        payments = Payment.query.filter_by(status=status).order_by(Payment.created_at.desc()).all()
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments]
        }), 200
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب المدفوعات: {str(e)}'}), 500

@subscription_bp.route('/admin/payment/<payment_id>/approve', methods=['POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def approve_payment(current_user, payment_id):
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'message': 'الدفع غير موجود'}), 404
        
        if payment.status != 'pending':
            return jsonify({'message': 'هذا الدفع تمت مراجعته بالفعل'}), 400
        
        user = User.query.get(payment.user_id)
        
        existing_subscription = Subscription.query.filter_by(
            user_id=user.user_id,
            status='active'
        ).order_by(Subscription.end_date.desc()).first()
        
        is_renewal = False
        if existing_subscription and existing_subscription.end_date > datetime.utcnow():
            start_date = existing_subscription.end_date
            is_renewal = True
        else:
            start_date = datetime.utcnow()
            if existing_subscription:
                is_renewal = True
        
        end_date = start_date + timedelta(days=365)
        
        grace_period_setting = Settings.query.filter_by(key='enable_grace_period').first()
        grace_enabled = grace_period_setting.value.lower() == 'true' if grace_period_setting else True
        
        new_subscription = Subscription(
            user_id=user.user_id,
            start_date=start_date,
            end_date=end_date,
            status='active',
            is_renewal=is_renewal,
            grace_period_enabled=grace_enabled
        )
        
        payment.status = 'approved'
        payment.reviewed_by_id = current_user.user_id
        payment.reviewed_at = datetime.utcnow()
        payment.review_notes = request.json.get('notes', '') if request.json else ''
        
        notification = Notification(
            user_id=user.user_id,
            message='تم تفعيل اشتراكك بنجاح! استمتع بكامل مزايا النظام.',
            type='payment_approved'
        )
        
        db.session.add(new_subscription)
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'تم اعتماد الدفع بنجاح',
            'subscription': new_subscription.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في اعتماد الدفع: {str(e)}'}), 500

@subscription_bp.route('/admin/payment/<payment_id>/reject', methods=['POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def reject_payment(current_user, payment_id):
    try:
        data = request.get_json()
        
        if not data.get('reason'):
            return jsonify({'message': 'سبب الرفض مطلوب'}), 400
        
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({'message': 'الدفع غير موجود'}), 404
        
        if payment.status != 'pending':
            return jsonify({'message': 'هذا الدفع تمت مراجعته بالفعل'}), 400
        
        payment.status = 'rejected'
        payment.reviewed_by_id = current_user.user_id
        payment.reviewed_at = datetime.utcnow()
        payment.review_notes = data['reason']
        
        notification = Notification(
            user_id=payment.user_id,
            message=f'تم رفض دفعتك. السبب: {data["reason"]}. يمكنك إعادة إرسال إثبات الدفع',
            type='payment_rejected'
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'تم رفض الدفع'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في رفض الدفع: {str(e)}'}), 500

@subscription_bp.route('/admin/payment-methods', methods=['GET'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def get_all_payment_methods(current_user):
    try:
        methods = PaymentMethod.query.order_by(PaymentMethod.display_order).all()
        return jsonify({
            'payment_methods': [method.to_dict() for method in methods]
        }), 200
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب طرق الدفع: {str(e)}'}), 500

@subscription_bp.route('/admin/payment-methods', methods=['POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def create_payment_method(current_user):
    try:
        data = request.get_json()
        
        required_fields = ['name', 'account_number', 'account_holder']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'{field} مطلوب'}), 400
        
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
        
        return jsonify({
            'message': 'تمت إضافة طريقة الدفع بنجاح',
            'method': new_method.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في إضافة طريقة الدفع: {str(e)}'}), 500

@subscription_bp.route('/admin/payment-methods/<method_id>', methods=['PUT'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def update_payment_method(current_user, method_id):
    try:
        method = PaymentMethod.query.get(method_id)
        if not method:
            return jsonify({'message': 'طريقة الدفع غير موجودة'}), 404
        
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
        
        return jsonify({
            'message': 'تم تحديث طريقة الدفع بنجاح',
            'method': method.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تحديث طريقة الدفع: {str(e)}'}), 500

@subscription_bp.route('/admin/payment-methods/<method_id>', methods=['DELETE'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def delete_payment_method(current_user, method_id):
    try:
        method = PaymentMethod.query.get(method_id)
        if not method:
            return jsonify({'message': 'طريقة الدفع غير موجودة'}), 404
        
        db.session.delete(method)
        db.session.commit()
        
        return jsonify({'message': 'تم حذف طريقة الدفع بنجاح'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في حذف طريقة الدفع: {str(e)}'}), 500

@subscription_bp.route('/admin/settings', methods=['GET'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def get_settings(current_user):
    try:
        settings = Settings.query.all()
        return jsonify({
            'settings': [setting.to_dict() for setting in settings]
        }), 200
    except Exception as e:
        return jsonify({'message': f'خطأ في جلب الإعدادات: {str(e)}'}), 500

@subscription_bp.route('/admin/settings', methods=['PUT'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def update_settings(current_user):
    try:
        data = request.get_json()
        
        for key, value in data.items():
            setting = Settings.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
                setting.updated_at = datetime.utcnow()
            else:
                new_setting = Settings(key=key, value=str(value))
                db.session.add(new_setting)
        
        db.session.commit()
        
        return jsonify({'message': 'تم تحديث الإعدادات بنجاح'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تحديث الإعدادات: {str(e)}'}), 500

@subscription_bp.route('/renewal/check', methods=['GET'])
@token_required
def check_renewal_status(current_user):
    try:
        if current_user.role.role_name != 'Trader':
            return jsonify({'message': 'هذه الخدمة متاحة للتجار فقط'}), 403
        
        active_subscription = Subscription.query.filter_by(
            user_id=current_user.user_id,
            status='active'
        ).order_by(Subscription.end_date.desc()).first()
        
        if not active_subscription:
            return jsonify({
                'needs_renewal': True,
                'status': 'no_subscription',
                'message': 'لا يوجد اشتراك نشط'
            }), 200
        
        days_remaining = (active_subscription.end_date - datetime.utcnow()).days
        
        grace_period_setting = Settings.query.filter_by(key='grace_period_days').first()
        grace_period_days = int(grace_period_setting.value) if grace_period_setting else 7
        
        enable_grace_period = Settings.query.filter_by(key='enable_grace_period').first()
        grace_enabled = enable_grace_period.value.lower() == 'true' if enable_grace_period else True
        
        in_grace_period = False
        grace_days_remaining = 0
        
        if active_subscription.end_date < datetime.utcnow():
            if grace_enabled and active_subscription.grace_period_enabled:
                grace_end = active_subscription.end_date + timedelta(days=grace_period_days)
                if datetime.utcnow() <= grace_end:
                    in_grace_period = True
                    grace_days_remaining = (grace_end - datetime.utcnow()).days
        
        return jsonify({
            'subscription': active_subscription.to_dict(),
            'days_remaining': max(0, days_remaining),
            'needs_renewal': days_remaining <= 14,
            'in_grace_period': in_grace_period,
            'grace_days_remaining': grace_days_remaining,
            'grace_period_days': grace_period_days,
            'grace_enabled': grace_enabled
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'خطأ في فحص حالة التجديد: {str(e)}'}), 500

@subscription_bp.route('/admin/check-renewals', methods=['POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def send_renewal_reminders(current_user):
    try:
        now = datetime.utcnow()
        reminders_sent = 0
        
        subscriptions = Subscription.query.filter_by(status='active').all()
        
        for subscription in subscriptions:
            days_remaining = (subscription.end_date - now).days
            
            if days_remaining == 14 and not subscription.notified_14d:
                notification = Notification(
                    user_id=subscription.user_id,
                    message=f'تنبيه: اشتراكك سينتهي بعد 14 يوماً في {subscription.end_date.strftime("%Y-%m-%d")}. يرجى التجديد قريباً.',
                    type='renewal_reminder_14d'
                )
                subscription.notified_14d = True
                db.session.add(notification)
                reminders_sent += 1
            
            elif days_remaining == 7 and not subscription.notified_7d:
                notification = Notification(
                    user_id=subscription.user_id,
                    message=f'تنبيه مهم: اشتراكك سينتهي بعد 7 أيام في {subscription.end_date.strftime("%Y-%m-%d")}. يرجى التجديد.',
                    type='renewal_reminder_7d'
                )
                subscription.notified_7d = True
                db.session.add(notification)
                reminders_sent += 1
            
            elif days_remaining == 3 and not subscription.notified_3d:
                notification = Notification(
                    user_id=subscription.user_id,
                    message=f'تنبيه عاجل: اشتراكك سينتهي بعد 3 أيام في {subscription.end_date.strftime("%Y-%m-%d")}. يرجى التجديد فوراً.',
                    type='renewal_reminder_3d'
                )
                subscription.notified_3d = True
                db.session.add(notification)
                reminders_sent += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'تم إرسال {reminders_sent} تذكير تجديد',
            'reminders_sent': reminders_sent
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في إرسال التذكيرات: {str(e)}'}), 500

@subscription_bp.route('/admin/init-settings', methods=['POST'])
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def initialize_settings(current_user):
    try:
        default_settings = [
            {'key': 'annual_subscription_price', 'value': '50000', 'description': 'سعر الاشتراك السنوي بالريال اليمني'},
            {'key': 'currency', 'value': 'YER', 'description': 'العملة المستخدمة'},
            {'key': 'grace_period_days', 'value': '7', 'description': 'عدد أيام فترة السماح بعد انتهاء الاشتراك'},
            {'key': 'enable_grace_period', 'value': 'true', 'description': 'تفعيل فترة السماح'},
        ]
        
        for setting_data in default_settings:
            existing = Settings.query.filter_by(key=setting_data['key']).first()
            if not existing:
                new_setting = Settings(**setting_data)
                db.session.add(new_setting)
        
        db.session.commit()
        
        return jsonify({'message': 'تم تهيئة الإعدادات الافتراضية بنجاح'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'خطأ في تهيئة الإعدادات: {str(e)}'}), 500
