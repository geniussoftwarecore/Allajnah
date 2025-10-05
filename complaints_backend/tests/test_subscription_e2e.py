"""
اختبارات شاملة E2E بسيطة لسيناريوهات المستخدم الأساسية
تشمل سيناريوهات واقعية مع mocks لرفع الملفات
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
from src.models.complaint import User, Role, PaymentMethod, Settings
from werkzeug.security import generate_password_hash


class TestUserJourneyE2E(unittest.TestCase):
    """اختبارات شاملة لرحلة المستخدم الكاملة"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
    
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
            
            payment_methods = [
                PaymentMethod(
                    name='كاش يو',
                    account_number='777888999',
                    account_holder='نظام الشكاوى',
                    is_active=True,
                    display_order=1
                ),
                PaymentMethod(
                    name='يمن موبايل',
                    account_number='711223344',
                    account_holder='نظام الشكاوى',
                    is_active=True,
                    display_order=2
                )
            ]
            for method in payment_methods:
                db.session.add(method)
            
            settings = [
                Settings(key='subscription_price', value='10000', description='سعر الاشتراك'),
                Settings(key='currency', value='YER', description='العملة'),
                Settings(key='enable_grace_period', value='true', description='تفعيل السماح'),
                Settings(key='grace_period_days', value='7', description='أيام السماح')
            ]
            for setting in settings:
                db.session.add(setting)
            
            admin_user = User(
                username='committee_admin',
                email='admin@complaints.gov.ye',
                password_hash=generate_password_hash('admin@2025'),
                full_name='مسؤول اللجنة العليا',
                role_id=3
            )
            db.session.add(admin_user)
            
            db.session.commit()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_new_trader_complete_journey(self):
        """
        سيناريو: تاجر جديد يريد استخدام النظام
        1. يسجل حساب جديد
        2. يحاول الوصول للميزات (يُمنع)
        3. يشاهد طرق الدفع
        4. يرفع إثبات الدفع
        5. ينتظر اعتماد المشرف
        6. يحصل على إشعار بالتفعيل
        7. يصل للميزات بنجاح
        """
        
        register_response = self.client.post('/api/register', json={
            'username': 'ahmed_trader',
            'email': 'ahmed@tradingco.ye',
            'password': 'SecurePass123!',
            'full_name': 'أحمد محمد التاجر',
            'phone_number': '777123456',
            'address': 'صنعاء - شارع الزبيري'
        })
        
        self.assertEqual(register_response.status_code, 201)
        register_data = json.loads(register_response.data)
        self.assertEqual(register_data['user']['role_name'], 'Trader')
        
        login_response = self.client.post('/api/login', json={
            'username': 'ahmed_trader',
            'password': 'SecurePass123!'
        })
        
        self.assertEqual(login_response.status_code, 200)
        login_data = json.loads(login_response.data)
        self.assertIn('token', login_data)
        trader_token = login_data['token']
        
        complaints_response = self.client.get('/api/complaints',
            headers={'Authorization': f'Bearer {trader_token}'})
        
        self.assertEqual(complaints_response.status_code, 403)
        error_data = json.loads(complaints_response.data)
        self.assertIn('اشتراك', error_data['message'].lower())
        
        methods_response = self.client.get('/api/payment-methods',
            headers={'Authorization': f'Bearer {trader_token}'})
        
        self.assertEqual(methods_response.status_code, 200)
        methods_data = json.loads(methods_response.data)
        self.assertGreater(len(methods_data['payment_methods']), 0)
        selected_method_id = methods_data['payment_methods'][0]['method_id']
        
        price_response = self.client.get('/api/subscription-price',
            headers={'Authorization': f'Bearer {trader_token}'})
        
        price_data = json.loads(price_response.data)
        self.assertEqual(price_data['price'], 10000.0)
        self.assertEqual(price_data['currency'], 'YER')
        
        fake_receipt = io.BytesIO(b'\x89PNG\r\n\x1a\n...')
        fake_receipt.name = 'payment_receipt_ahmed.png'
        
        payment_submit = self.client.post('/api/payment/submit',
            headers={'Authorization': f'Bearer {trader_token}'},
            data={
                'method_id': selected_method_id,
                'sender_name': 'أحمد محمد التاجر',
                'sender_phone': '777123456',
                'transaction_reference': 'TRX-2025-001234',
                'amount': 10000,
                'currency': 'YER',
                'payment_date': datetime.utcnow().isoformat(),
                'receipt': (fake_receipt, 'receipt.png')
            },
            content_type='multipart/form-data'
        )
        
        self.assertEqual(payment_submit.status_code, 201)
        payment_data = json.loads(payment_submit.data)
        self.assertEqual(payment_data['payment']['status'], 'pending')
        payment_id = payment_data['payment']['payment_id']
        
        admin_login = self.client.post('/api/login', json={
            'username': 'committee_admin',
            'password': 'admin@2025'
        })
        admin_token = json.loads(admin_login.data)['token']
        
        pending_payments = self.client.get('/api/admin/payments?status=pending',
            headers={'Authorization': f'Bearer {admin_token}'})
        
        self.assertEqual(pending_payments.status_code, 200)
        pending_data = json.loads(pending_payments.data)
        self.assertGreater(len(pending_data['payments']), 0)
        
        approve_response = self.client.put(
            f'/api/admin/payments/{payment_id}/approve',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'review_notes': 'تم التحقق من الدفع والاعتماد'}
        )
        
        self.assertEqual(approve_response.status_code, 200)
        
        notifications_response = self.client.get('/api/notifications',
            headers={'Authorization': f'Bearer {trader_token}'})
        
        self.assertEqual(notifications_response.status_code, 200)
        notif_data = json.loads(notifications_response.data)
        self.assertGreater(len(notif_data['notifications']), 0)
        
        payment_approved = any(
            'تفعيل' in n['message'] or 'اعتماد' in n['message'] 
            for n in notif_data['notifications']
        )
        self.assertTrue(payment_approved)
        
        subscription_status = self.client.get('/api/subscription/status',
            headers={'Authorization': f'Bearer {trader_token}'})
        
        self.assertEqual(subscription_status.status_code, 200)
        sub_data = json.loads(subscription_status.data)
        self.assertTrue(sub_data['has_active_subscription'])
        self.assertEqual(sub_data['subscription']['status'], 'active')
        
        complaints_response_after = self.client.get('/api/complaints',
            headers={'Authorization': f'Bearer {trader_token}'})
        
        self.assertEqual(complaints_response_after.status_code, 200)
    
    def test_rejected_payment_scenario(self):
        """
        سيناريو: دفع مرفوض
        1. تاجر يرفع دفع غير صحيح
        2. المشرف يرفض الدفع
        3. التاجر يحصل على إشعار بالرفض
        4. لا يتم تفعيل الاشتراك
        """
        
        self.client.post('/api/register', json={
            'username': 'khalid_trader',
            'email': 'khalid@example.ye',
            'password': 'Pass123!',
            'full_name': 'خالد أحمد'
        })
        
        login_response = self.client.post('/api/login', json={
            'username': 'khalid_trader',
            'password': 'Pass123!'
        })
        trader_token = json.loads(login_response.data)['token']
        
        methods_response = self.client.get('/api/payment-methods',
            headers={'Authorization': f'Bearer {trader_token}'})
        method_id = json.loads(methods_response.data)['payment_methods'][0]['method_id']
        
        payment_submit = self.client.post('/api/payment/submit',
            headers={'Authorization': f'Bearer {trader_token}'},
            data={
                'method_id': method_id,
                'sender_name': 'خالد أحمد',
                'sender_phone': '711999888',
                'amount': 5000,
                'currency': 'YER',
                'payment_date': datetime.utcnow().isoformat(),
                'receipt': (io.BytesIO(b'fake'), 'receipt.jpg')
            },
            content_type='multipart/form-data'
        )
        payment_id = json.loads(payment_submit.data)['payment']['payment_id']
        
        admin_login = self.client.post('/api/login', json={
            'username': 'committee_admin',
            'password': 'admin@2025'
        })
        admin_token = json.loads(admin_login.data)['token']
        
        reject_response = self.client.put(
            f'/api/admin/payments/{payment_id}/reject',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'review_notes': 'المبلغ المدفوع غير كافٍ. المطلوب 10,000 ريال'}
        )
        
        self.assertEqual(reject_response.status_code, 200)
        
        notifications = self.client.get('/api/notifications',
            headers={'Authorization': f'Bearer {trader_token}'})
        notif_data = json.loads(notifications.data)
        
        rejection_found = any(
            'رفض' in n['message'] or 'غير كافٍ' in n.get('message', '')
            for n in notif_data['notifications']
        )
        self.assertTrue(rejection_found)
        
        subscription_status = self.client.get('/api/subscription/status',
            headers={'Authorization': f'Bearer {trader_token}'})
        sub_data = json.loads(subscription_status.data)
        self.assertFalse(sub_data['has_active_subscription'])
        
        blocked = self.client.get('/api/complaints',
            headers={'Authorization': f'Bearer {trader_token}'})
        self.assertEqual(blocked.status_code, 403)
    
    def test_subscription_info_check(self):
        """
        سيناريو: التحقق من معلومات الاشتراك
        """
        
        self.client.post('/api/register', json={
            'username': 'info_trader',
            'email': 'info@test.ye',
            'password': 'Pass123!',
            'full_name': 'مستخدم معلومات'
        })
        
        login = self.client.post('/api/login', json={
            'username': 'info_trader',
            'password': 'Pass123!'
        })
        token = json.loads(login.data)['token']
        
        price_check = self.client.get('/api/subscription-price',
            headers={'Authorization': f'Bearer {token}'})
        
        self.assertEqual(price_check.status_code, 200)
        price_data = json.loads(price_check.data)
        self.assertIn('price', price_data)
        self.assertIn('currency', price_data)
        
        methods_check = self.client.get('/api/payment-methods',
            headers={'Authorization': f'Bearer {token}'})
        
        self.assertEqual(methods_check.status_code, 200)
        methods = json.loads(methods_check.data)['payment_methods']
        self.assertGreater(len(methods), 0)
        
        for method in methods:
            self.assertIn('method_id', method)
            self.assertIn('name', method)
            self.assertIn('account_number', method)
            self.assertIn('account_holder', method)


if __name__ == '__main__':
    unittest.main()
