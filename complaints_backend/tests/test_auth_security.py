"""
Security-focused tests for authentication and authorization
"""
import unittest
import json
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.db import db
from src.main import app
from src.models.complaint import User, Role, AuditLog


class TestAuthSecurity(unittest.TestCase):
    """Test authentication and security features"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test app once for all tests"""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    def setUp(self):
        """Set up test environment"""
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            # Create test roles if they don't exist
            if not Role.query.filter_by(role_name='Trader').first():
                roles = [
                    Role(role_id=1, role_name='Trader', description='تاجر'),
                    Role(role_id=2, role_name='Technical Committee', description='لجنة فنية'),
                    Role(role_id=3, role_name='Higher Committee', description='لجنة عليا')
                ]
                for role in roles:
                    db.session.add(role)
                db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_register_defaults_to_trader_role(self):
        """Test that registration always assigns Trader role"""
        response = self.client.post('/api/register', 
            json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123',
                'full_name': 'Test User'
            })
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['user']['role_name'], 'Trader')
    
    def test_register_ignores_custom_role(self):
        """Test that registration ignores any role data from client"""
        response = self.client.post('/api/register',
            json={
                'username': 'hacker',
                'email': 'hacker@example.com',
                'password': 'password123',
                'full_name': 'Hacker User',
                'role_name': 'Higher Committee',  # Should be ignored
                'role_id': 3  # Should be ignored
            })
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        # Despite sending Higher Committee role, should get Trader
        self.assertEqual(data['user']['role_name'], 'Trader')
    
    def test_register_validates_required_fields(self):
        """Test registration validates all required fields"""
        response = self.client.post('/api/register',
            json={
                'username': 'testuser',
                # Missing email, password, full_name
            })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('مطلوبة', data['message'])
    
    def test_register_rejects_duplicate_username(self):
        """Test registration rejects duplicate username"""
        # Create first user
        self.client.post('/api/register',
            json={
                'username': 'testuser',
                'email': 'test1@example.com',
                'password': 'password123',
                'full_name': 'Test User 1'
            })
        
        # Try to create second user with same username
        response = self.client.post('/api/register',
            json={
                'username': 'testuser',  # Duplicate
                'email': 'test2@example.com',
                'password': 'password123',
                'full_name': 'Test User 2'
            })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('موجود', data['message'])
    
    def test_login_with_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        response = self.client.post('/api/login',
            json={
                'username': 'nonexistent',
                'password': 'wrongpassword'
            })
        
        self.assertEqual(response.status_code, 401)
    
    def test_protected_endpoint_requires_token(self):
        """Test that protected endpoints require authentication token"""
        response = self.client.get('/api/profile')
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('رمز التوثيق مفقود', data['message'])
    
    def test_role_based_access_control(self):
        """Test that RBAC is enforced on admin endpoints"""
        # Create a trader user
        register_response = self.client.post('/api/register',
            json={
                'username': 'trader',
                'email': 'trader@example.com',
                'password': 'password123',
                'full_name': 'Trader User'
            })
        
        # Login to get token
        login_response = self.client.post('/api/login',
            json={
                'username': 'trader',
                'password': 'password123'
            })
        token = json.loads(login_response.data)['token']
        
        # Try to access admin endpoint
        response = self.client.get('/api/users',
            headers={'Authorization': f'Bearer {token}'})
        
        # Should be forbidden
        self.assertEqual(response.status_code, 403)


class TestRoleManagement(unittest.TestCase):
    """Test role management and audit logging"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test app once for all tests"""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    def setUp(self):
        """Set up test environment"""
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            # Create test roles if they don't exist
            if not Role.query.filter_by(role_name='Trader').first():
                roles = [
                    Role(role_id=1, role_name='Trader', description='تاجر'),
                    Role(role_id=2, role_name='Technical Committee', description='لجنة فنية'),
                    Role(role_id=3, role_name='Higher Committee', description='لجنة عليا')
                ]
                for role in roles:
                    db.session.add(role)
                db.session.commit()
            
            # Create a Higher Committee user for testing if doesn't exist
            from werkzeug.security import generate_password_hash
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    password_hash=generate_password_hash('admin123'),
                    full_name='Admin User',
                    role_id=3  # Higher Committee
                )
                db.session.add(admin_user)
                db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def get_admin_token(self):
        """Helper to get admin token"""
        response = self.client.post('/api/login',
            json={
                'username': 'admin',
                'password': 'admin123'
            })
        return json.loads(response.data)['token']
    
    def test_only_higher_committee_can_change_roles(self):
        """Test that only Higher Committee can change user roles"""
        admin_token = self.get_admin_token()
        
        # Create a regular trader user
        self.client.post('/api/register',
            json={
                'username': 'trader1',
                'email': 'trader1@example.com',
                'password': 'password123',
                'full_name': 'Trader One'
            })
        
        # Get the user ID
        with self.app.app_context():
            user = User.query.filter_by(username='trader1').first()
            user_id = user.user_id
        
        # Try to change role using admin token (Higher Committee)
        response = self.client.put(f'/api/admin/users/{user_id}/role',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'role_name': 'Technical Committee'})
        
        self.assertEqual(response.status_code, 200)
    
    def test_role_change_creates_audit_log(self):
        """Test that changing roles creates an audit log entry"""
        admin_token = self.get_admin_token()
        
        # Create a user
        self.client.post('/api/register',
            json={
                'username': 'trader2',
                'email': 'trader2@example.com',
                'password': 'password123',
                'full_name': 'Trader Two'
            })
        
        # Get the user ID
        with self.app.app_context():
            user = User.query.filter_by(username='trader2').first()
            user_id = user.user_id
        
        # Change role
        self.client.put(f'/api/admin/users/{user_id}/role',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'role_name': 'Technical Committee'})
        
        # Check audit log
        with self.app.app_context():
            audit_log = AuditLog.query.filter_by(
                action_type='role_change',
                affected_user_id=user_id
            ).first()
            
            self.assertIsNotNone(audit_log)
            self.assertEqual(audit_log.old_value, 'Trader')
            self.assertEqual(audit_log.new_value, 'Technical Committee')
    
    def test_cannot_change_own_role(self):
        """Test that users cannot change their own role"""
        admin_token = self.get_admin_token()
        
        # Get admin user ID
        with self.app.app_context():
            admin_user = User.query.filter_by(username='admin').first()
            admin_user_id = admin_user.user_id
        
        # Try to change own role
        response = self.client.put(f'/api/admin/users/{admin_user_id}/role',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'role_name': 'Trader'})
        
        self.assertEqual(response.status_code, 403)


class Test2FA(unittest.TestCase):
    """Test 2FA functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test app once for all tests"""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    def setUp(self):
        """Set up test environment"""
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            # Create test roles if doesn't exist
            if not Role.query.filter_by(role_name='Trader').first():
                role = Role(role_id=1, role_name='Trader', description='تاجر')
                db.session.add(role)
                db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_enable_2fa_generates_secret(self):
        """Test that enabling 2FA generates a secret and QR code"""
        # Register and login
        self.client.post('/api/register',
            json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123',
                'full_name': 'Test User'
            })
        
        login_response = self.client.post('/api/login',
            json={
                'username': 'testuser',
                'password': 'password123'
            })
        token = json.loads(login_response.data)['token']
        
        # Enable 2FA
        response = self.client.post('/api/2fa/enable',
            headers={'Authorization': f'Bearer {token}'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('secret', data)
        self.assertIn('qr_code', data)
        self.assertIn('data:image/png;base64,', data['qr_code'])
    
    def test_login_requires_2fa_when_enabled(self):
        """Test that login requires 2FA code when enabled"""
        # Register user
        self.client.post('/api/register',
            json={
                'username': 'testuser2',
                'email': 'test2@example.com',
                'password': 'password123',
                'full_name': 'Test User 2'
            })
        
        # Login to get token
        login_response = self.client.post('/api/login',
            json={
                'username': 'testuser2',
                'password': 'password123'
            })
        token = json.loads(login_response.data)['token']
        
        # Enable 2FA
        enable_response = self.client.post('/api/2fa/enable',
            headers={'Authorization': f'Bearer {token}'})
        secret = json.loads(enable_response.data)['secret']
        
        # Verify 2FA with a valid code
        import pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        self.client.post('/api/2fa/verify',
            headers={'Authorization': f'Bearer {token}'},
            json={'code': code})
        
        # Now try to login - should require 2FA
        login_response2 = self.client.post('/api/login',
            json={
                'username': 'testuser2',
                'password': 'password123'
            })
        
        data = json.loads(login_response2.data)
        self.assertTrue(data['requires_2fa'])


if __name__ == '__main__':
    unittest.main()
