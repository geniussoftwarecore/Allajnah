"""
اختبارات التكامل (Integration Tests) لنظام الاشتراكات
مسار كامل: تسجيل → اشتراك غير مفعل → رفع إثبات → اعتماد المشرف → تفعيل الاشتراك → السماح للميزات
"""
import unittest
import json
import io
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.db import db
from src.main import app
from src.models.complaint import User, Role, PaymentMethod, Settings, Subscription, Payment


class TestPaymentFlowIntegration(unittest.TestCase):
    """اختبار المسار الكامل لعملية الدفع والاشتراك"""
    
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
            
            payment_method = PaymentMethod(
                name='كاش يو',
                account_number='777888999',
                account_holder='النظام الإلكتروني',
                is_active=True
            )
            db.session.add(payment_method)
            
            settings = [
                Settings(key='subscription_price', value='10000', description='سعر الاشتراك السنوي'),
                Settings(key='currency', value='YER', description='العملة'),
                Settings(key='enable_grace_period', value='true', description='تفعيل فترة السماح'),
                Settings(key='grace_period_days', value='7', description='عدد أيام السماح')
            ]
            for setting in settings:
                db.session.add(setting)
            
            db.session.commit()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_complete_subscription_flow(self):
        """
        اختبار المسار الكامل:
        1. تسجيل مستخدم جديد
        2. التحقق من عدم وجود اشتراك نشط
        3. رفع إثبات الدفع
        4. اعتماد الدفع من المشرف
        5. التحقق من تفعيل الاشتراك
        6. الوصول للميزات بنجاح
        """
        
        response = self.client.post('/api/register', json={
            'username': 'new_trader',
            'email': 'new_trader@test.com',
            'password': 'password123',
            'full_name': 'تاجر جديد'
        })
        self.assertEqual(response.status_code, 201)
        
        login_response = self.client.post('/api/login', json={
            'username': 'new_trader',
            'password': 'password123'
        })
        self.assertEqual(login_response.status_code, 200)
        trader_token = json.loads(login_response.data)['token']
        
        subscription_status = self.client.get('/api/subscription/status',
            headers={'Authorization': f'Bearer {trader_token}'})
        status_data = json.loads(subscription_status.data)
        self.assertFalse(status_data.get('has_active_subscription', True))
        
        with self.app.app_context():
            method = PaymentMethod.query.first()
            method_id = method.method_id
        
        payment_data = {
            'method_id': method_id,
            'sender_name': 'تاجر جديد',
            'sender_phone': '777123456',
            'transaction_reference': 'TRX123456',
            'amount': 10000,
            'currency': 'YER',
            'payment_date': datetime.utcnow().isoformat()
        }
        
        payment_response = self.client.post('/api/payment/submit',
            headers={'Authorization': f'Bearer {trader_token}'},
            data={
                **payment_data,
                'receipt': (io.BytesIO(b'fake image content'), 'receipt.jpg')
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(payment_response.status_code, 201)
        payment_id = json.loads(payment_response.data)['payment']['payment_id']
        
        blocked_response = self.client.get('/api/complaints',
            headers={'Authorization': f'Bearer {trader_token}'})
        self.assertEqual(blocked_response.status_code, 403)
        blocked_data = json.loads(blocked_response.data)
        self.assertIn('اشتراك', blocked_data['message'])
        
        from werkzeug.security import generate_password_hash
        with self.app.app_context():
            admin_user = User(
                username='admin_reviewer',
                email='admin@test.com',
                password_hash=generate_password_hash('admin123'),
                full_name='مشرف الاعتماد',
                role_id=3
            )
            db.session.add(admin_user)
            db.session.commit()
        
        admin_login = self.client.post('/api/login', json={
            'username': 'admin_reviewer',
            'password': 'admin123'
        })
        admin_token = json.loads(admin_login.data)['token']
        
        approve_response = self.client.put(f'/api/admin/payments/{payment_id}/approve',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'review_notes': 'تم الاعتماد بنجاح'}
        )
        self.assertEqual(approve_response.status_code, 200)
        
        with self.app.app_context():
            trader = User.query.filter_by(username='new_trader').first()
            active_subscription = Subscription.query.filter_by(
                user_id=trader.user_id,
                status='active'
            ).first()
            
            self.assertIsNotNone(active_subscription)
            self.assertEqual(active_subscription.status, 'active')
        
        allowed_response = self.client.get('/api/complaints',
            headers={'Authorization': f'Bearer {trader_token}'})
        self.assertEqual(allowed_response.status_code, 200)
    
    def test_payment_rejection_flow(self):
        """اختبار رفض الدفع وعدم تفعيل الاشتراك"""
        
        response = self.client.post('/api/register', json={
            'username': 'rejected_trader',
            'email': 'rejected@test.com',
            'password': 'password123',
            'full_name': 'تاجر مرفوض'
        })
        self.assertEqual(response.status_code, 201)
        
        login_response = self.client.post('/api/login', json={
            'username': 'rejected_trader',
            'password': 'password123'
        })
        trader_token = json.loads(login_response.data)['token']
        
        with self.app.app_context():
            method = PaymentMethod.query.first()
            method_id = method.method_id
        
        payment_response = self.client.post('/api/payment/submit',
            headers={'Authorization': f'Bearer {trader_token}'},
            data={
                'method_id': method_id,
                'sender_name': 'تاجر مرفوض',
                'sender_phone': '777999888',
                'amount': 5000,
                'currency': 'YER',
                'payment_date': datetime.utcnow().isoformat(),
                'receipt': (io.BytesIO(b'fake receipt'), 'receipt.jpg')
            },
            content_type='multipart/form-data'
        )
        payment_id = json.loads(payment_response.data)['payment']['payment_id']
        
        from werkzeug.security import generate_password_hash
        with self.app.app_context():
            admin_user = User(
                username='admin_rejector',
                email='admin2@test.com',
                password_hash=generate_password_hash('admin123'),
                full_name='مشرف الرفض',
                role_id=3
            )
            db.session.add(admin_user)
            db.session.commit()
        
        admin_login = self.client.post('/api/login', json={
            'username': 'admin_rejector',
            'password': 'admin123'
        })
        admin_token = json.loads(admin_login.data)['token']
        
        reject_response = self.client.put(f'/api/admin/payments/{payment_id}/reject',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'review_notes': 'المبلغ غير صحيح'}
        )
        self.assertEqual(reject_response.status_code, 200)
        
        with self.app.app_context():
            trader = User.query.filter_by(username='rejected_trader').first()
            subscription = Subscription.query.filter_by(user_id=trader.user_id).first()
            
            self.assertIsNone(subscription)
        
        blocked_response = self.client.get('/api/complaints',
            headers={'Authorization': f'Bearer {trader_token}'})
        self.assertEqual(blocked_response.status_code, 403)
    
    def test_multiple_payments_single_subscription(self):
        """اختبار أن دفعتين متتاليتين تنتج اشتراكين منفصلين (تمديد)"""
        
        response = self.client.post('/api/register', json={
            'username': 'extend_trader',
            'email': 'extend@test.com',
            'password': 'password123',
            'full_name': 'تاجر التمديد'
        })
        
        login_response = self.client.post('/api/login', json={
            'username': 'extend_trader',
            'password': 'password123'
        })
        trader_token = json.loads(login_response.data)['token']
        
        from werkzeug.security import generate_password_hash
        with self.app.app_context():
            admin_user = User(
                username='admin_extender',
                email='admin3@test.com',
                password_hash=generate_password_hash('admin123'),
                full_name='مشرف التمديد',
                role_id=3
            )
            db.session.add(admin_user)
            db.session.commit()
            method = PaymentMethod.query.first()
            method_id = method.method_id
        
        admin_login = self.client.post('/api/login', json={
            'username': 'admin_extender',
            'password': 'admin123'
        })
        admin_token = json.loads(admin_login.data)['token']
        
        payment1_response = self.client.post('/api/payment/submit',
            headers={'Authorization': f'Bearer {trader_token}'},
            data={
                'method_id': method_id,
                'sender_name': 'تاجر التمديد',
                'sender_phone': '777111222',
                'amount': 10000,
                'currency': 'YER',
                'payment_date': datetime.utcnow().isoformat(),
                'receipt': (io.BytesIO(b'receipt1'), 'receipt1.jpg')
            },
            content_type='multipart/form-data'
        )
        payment1_id = json.loads(payment1_response.data)['payment']['payment_id']
        
        self.client.put(f'/api/admin/payments/{payment1_id}/approve',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'review_notes': 'اعتماد الأول'}
        )
        
        payment2_response = self.client.post('/api/payment/submit',
            headers={'Authorization': f'Bearer {trader_token}'},
            data={
                'method_id': method_id,
                'sender_name': 'تاجر التمديد',
                'sender_phone': '777111222',
                'amount': 10000,
                'currency': 'YER',
                'payment_date': datetime.utcnow().isoformat(),
                'receipt': (io.BytesIO(b'receipt2'), 'receipt2.jpg')
            },
            content_type='multipart/form-data'
        )
        payment2_id = json.loads(payment2_response.data)['payment']['payment_id']
        
        self.client.put(f'/api/admin/payments/{payment2_id}/approve',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'review_notes': 'اعتماد الثاني'}
        )
        
        with self.app.app_context():
            trader = User.query.filter_by(username='extend_trader').first()
            subscriptions = Subscription.query.filter_by(
                user_id=trader.user_id
            ).order_by(Subscription.created_at).all()
            
            self.assertEqual(len(subscriptions), 2)
            self.assertTrue(subscriptions[1].is_renewal)
            self.assertEqual(
                subscriptions[1].start_date.date(),
                subscriptions[0].end_date.date()
            )


if __name__ == '__main__':
    unittest.main()
