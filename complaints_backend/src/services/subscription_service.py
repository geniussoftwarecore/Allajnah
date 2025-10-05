from datetime import datetime, timedelta
from src.database.db import db
from src.models.complaint import User, Subscription, Payment, Settings, Notification

def create_or_extend_subscription(user_id, payment_id, reviewed_by_id):
    """
    خدمة توليد الاشتراك أو التمديد
    - إن كان لدى المستخدم اشتراك نشط، يبدأ التمديد من end_date الحالي
    - وإلا من تاريخ الاعتماد
    """
    try:
        user = User.query.get(user_id)
        payment = Payment.query.get(payment_id)
        
        if not user or not payment:
            return {'success': False, 'error': 'المستخدم أو الدفع غير موجود'}
        
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
        payment.reviewed_by_id = reviewed_by_id
        payment.reviewed_at = datetime.utcnow()
        
        notification = Notification(
            user_id=user.user_id,
            message='تم تفعيل اشتراكك بنجاح! استمتع بكامل مزايا النظام.',
            type='payment_approved'
        )
        
        db.session.add(new_subscription)
        db.session.add(notification)
        db.session.commit()
        
        return {
            'success': True,
            'subscription': new_subscription.to_dict(),
            'is_renewal': is_renewal
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}
