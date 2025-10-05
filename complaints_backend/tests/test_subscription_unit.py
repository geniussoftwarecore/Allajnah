"""
اختبارات الوحدات (Unit Tests) لنظام الاشتراكات
تتضمن:
- خدمات الاشتراك (create_or_extend)
- حساب تاريخ الانتهاء
- منطق التمديد
"""
import unittest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.db import db
from src.main import app
from src.models.complaint import User, Role, Subscription, Payment, PaymentMethod, Settings
from src.services.subscription_service import create_or_extend_subscription
from werkzeug.security import generate_password_hash


class TestSubscriptionService(unittest.TestCase):
    """اختبار خدمات الاشتراك"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    def setUp(self):
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            if not Role.query.filter_by(role_name='Trader').first():
                roles = [
                    Role(role_id=1, role_name='Trader', description='تاجر'),
                    Role(role_id=2, role_name='Technical Committee', description='لجنة فنية'),
                    Role(role_id=3, role_name='Higher Committee', description='لجنة عليا')
                ]
                for role in roles:
                    db.session.add(role)
                db.session.commit()
            
            if not User.query.filter_by(username='trader_test').first():
                trader_user = User(
                    username='trader_test',
                    email='trader@test.com',
                    password_hash=generate_password_hash('password123'),
                    full_name='تاجر تجريبي',
                    role_id=1
                )
                db.session.add(trader_user)
                db.session.commit()
            
            if not User.query.filter_by(username='admin_test').first():
                admin_user = User(
                    username='admin_test',
                    email='admin@test.com',
                    password_hash=generate_password_hash('admin123'),
                    full_name='مشرف تجريبي',
                    role_id=3
                )
                db.session.add(admin_user)
                db.session.commit()
            
            if not PaymentMethod.query.first():
                payment_method = PaymentMethod(
                    name='كاش يو',
                    account_number='777888999',
                    account_holder='النظام الإلكتروني'
                )
                db.session.add(payment_method)
                db.session.commit()
            
            if not Settings.query.filter_by(key='enable_grace_period').first():
                grace_setting = Settings(
                    key='enable_grace_period',
                    value='true',
                    description='تفعيل فترة السماح'
                )
                db.session.add(grace_setting)
                db.session.commit()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_create_first_subscription(self):
        """اختبار إنشاء اشتراك جديد لأول مرة"""
        with self.app.app_context():
            trader = User.query.filter_by(username='trader_test').first()
            admin = User.query.filter_by(username='admin_test').first()
            method = PaymentMethod.query.first()
            
            payment = Payment(
                user_id=trader.user_id,
                method_id=method.method_id,
                sender_name='تاجر تجريبي',
                sender_phone='777000111',
                amount=10000.0,
                currency='YER',
                payment_date=datetime.utcnow(),
                receipt_image_path='/uploads/receipt1.jpg',
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            result = create_or_extend_subscription(
                user_id=trader.user_id,
                payment_id=payment.payment_id,
                reviewed_by_id=admin.user_id
            )
            
            self.assertTrue(result['success'], f"Service returned error: {result.get('error', 'Unknown')}")
            self.assertFalse(result['is_renewal'])
            
            subscription = Subscription.query.filter_by(user_id=trader.user_id).first()
            self.assertIsNotNone(subscription)
            self.assertEqual(subscription.status, 'active')
            
            end_date = subscription.start_date + timedelta(days=365)
            self.assertEqual(subscription.end_date.date(), end_date.date())
    
    def test_extend_active_subscription(self):
        """اختبار تمديد اشتراك نشط (يبدأ التمديد من تاريخ الانتهاء)"""
        with self.app.app_context():
            trader = User.query.filter_by(username='trader_test').first()
            admin = User.query.filter_by(username='admin_test').first()
            method = PaymentMethod.query.first()
            
            existing_start = datetime.utcnow()
            existing_end = existing_start + timedelta(days=200)
            
            existing_subscription = Subscription(
                user_id=trader.user_id,
                start_date=existing_start,
                end_date=existing_end,
                status='active'
            )
            db.session.add(existing_subscription)
            db.session.commit()
            
            payment = Payment(
                user_id=trader.user_id,
                method_id=method.method_id,
                sender_name='تاجر تجريبي',
                sender_phone='777000111',
                amount=10000.0,
                currency='YER',
                payment_date=datetime.utcnow(),
                receipt_image_path='/uploads/receipt2.jpg',
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            result = create_or_extend_subscription(
                user_id=trader.user_id,
                payment_id=payment.payment_id,
                reviewed_by_id=admin.user_id
            )
            
            self.assertTrue(result['success'])
            self.assertTrue(result['is_renewal'])
            
            new_subscription = Subscription.query.filter_by(
                user_id=trader.user_id
            ).order_by(Subscription.created_at.desc()).first()
            
            self.assertEqual(new_subscription.start_date.date(), existing_end.date())
            
            expected_new_end = existing_end + timedelta(days=365)
            self.assertEqual(new_subscription.end_date.date(), expected_new_end.date())
    
    def test_renew_expired_subscription(self):
        """اختبار تجديد اشتراك منتهي (يبدأ من تاريخ الاعتماد)"""
        with self.app.app_context():
            trader = User.query.filter_by(username='trader_test').first()
            admin = User.query.filter_by(username='admin_test').first()
            method = PaymentMethod.query.first()
            
            expired_start = datetime.utcnow() - timedelta(days=400)
            expired_end = expired_start + timedelta(days=365)
            
            expired_subscription = Subscription(
                user_id=trader.user_id,
                start_date=expired_start,
                end_date=expired_end,
                status='expired'
            )
            db.session.add(expired_subscription)
            db.session.commit()
            
            payment = Payment(
                user_id=trader.user_id,
                method_id=method.method_id,
                sender_name='تاجر تجريبي',
                sender_phone='777000111',
                amount=10000.0,
                currency='YER',
                payment_date=datetime.utcnow(),
                receipt_image_path='/uploads/receipt3.jpg',
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            approval_time = datetime.utcnow()
            result = create_or_extend_subscription(
                user_id=trader.user_id,
                payment_id=payment.payment_id,
                reviewed_by_id=admin.user_id
            )
            
            self.assertTrue(result['success'])
            self.assertTrue(result['is_renewal'])
            
            new_subscription = Subscription.query.filter_by(
                user_id=trader.user_id,
                status='active'
            ).first()
            
            self.assertAlmostEqual(
                new_subscription.start_date.timestamp(),
                approval_time.timestamp(),
                delta=5
            )
    
    def test_payment_status_updated_on_approval(self):
        """اختبار تحديث حالة الدفع عند الاعتماد"""
        with self.app.app_context():
            trader = User.query.filter_by(username='trader_test').first()
            admin = User.query.filter_by(username='admin_test').first()
            method = PaymentMethod.query.first()
            
            payment = Payment(
                user_id=trader.user_id,
                method_id=method.method_id,
                sender_name='تاجر تجريبي',
                sender_phone='777000111',
                amount=10000.0,
                currency='YER',
                payment_date=datetime.utcnow(),
                receipt_image_path='/uploads/receipt4.jpg',
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            self.assertEqual(payment.status, 'pending')
            
            result = create_or_extend_subscription(
                user_id=trader.user_id,
                payment_id=payment.payment_id,
                reviewed_by_id=admin.user_id
            )
            
            self.assertTrue(result['success'])
            
            updated_payment = Payment.query.get(payment.payment_id)
            self.assertEqual(updated_payment.status, 'approved')
            self.assertEqual(updated_payment.reviewed_by_id, admin.user_id)
            self.assertIsNotNone(updated_payment.reviewed_at)
    
    def test_grace_period_setting_respected(self):
        """اختبار احترام إعداد فترة السماح"""
        with self.app.app_context():
            trader = User.query.filter_by(username='trader_test').first()
            admin = User.query.filter_by(username='admin_test').first()
            method = PaymentMethod.query.first()
            
            Settings.query.filter_by(key='enable_grace_period').update({'value': 'false'})
            db.session.commit()
            
            payment = Payment(
                user_id=trader.user_id,
                method_id=method.method_id,
                sender_name='تاجر تجريبي',
                sender_phone='777000111',
                amount=10000.0,
                currency='YER',
                payment_date=datetime.utcnow(),
                receipt_image_path='/uploads/receipt5.jpg',
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            result = create_or_extend_subscription(
                user_id=trader.user_id,
                payment_id=payment.payment_id,
                reviewed_by_id=admin.user_id
            )
            
            self.assertTrue(result['success'])
            
            subscription = Subscription.query.filter_by(user_id=trader.user_id).first()
            self.assertFalse(subscription.grace_period_enabled)
    
    def test_invalid_user_returns_error(self):
        """اختبار رفض معرف مستخدم غير موجود"""
        with self.app.app_context():
            admin = User.query.filter_by(username='admin_test').first()
            method = PaymentMethod.query.first()
            
            payment = Payment(
                user_id='invalid-user-id',
                method_id=method.method_id,
                sender_name='تاجر وهمي',
                sender_phone='000000000',
                amount=10000.0,
                currency='YER',
                payment_date=datetime.utcnow(),
                receipt_image_path='/uploads/invalid.jpg',
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            result = create_or_extend_subscription(
                user_id='invalid-user-id',
                payment_id=payment.payment_id,
                reviewed_by_id=admin.user_id
            )
            
            self.assertFalse(result['success'])
            self.assertIn('غير موجود', result['error'])


if __name__ == '__main__':
    unittest.main()
