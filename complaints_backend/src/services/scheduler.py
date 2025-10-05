from datetime import datetime
from src.database.db import db
from src.models.complaint import Subscription, Notification

def check_and_expire_subscriptions():
    """
    وظيفة مجدولة لتغيير الاشتراكات المنتهية إلى expired
    يجب تشغيلها يومياً
    """
    try:
        now = datetime.utcnow()
        expired_count = 0
        
        active_subscriptions = Subscription.query.filter_by(status='active').all()
        
        for subscription in active_subscriptions:
            grace_period_days = 7
            if subscription.grace_period_enabled:
                expiry_with_grace = subscription.end_date
            else:
                expiry_with_grace = subscription.end_date
            
            if now > expiry_with_grace:
                subscription.status = 'expired'
                expired_count += 1
        
        db.session.commit()
        return {'expired_count': expired_count, 'success': True}
        
    except Exception as e:
        db.session.rollback()
        return {'error': str(e), 'success': False}

def send_renewal_reminders():
    """
    وظيفة مجدولة لإرسال تذكيرات انتهاء الاشتراك
    D-14, D-7, D-3
    يجب تشغيلها يومياً
    """
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
        return {'reminders_sent': reminders_sent, 'success': True}
        
    except Exception as e:
        db.session.rollback()
        return {'error': str(e), 'success': False}

def run_daily_tasks():
    """تشغيل جميع المهام اليومية"""
    results = {
        'expiry_check': check_and_expire_subscriptions(),
        'renewal_reminders': send_renewal_reminders()
    }
    return results
