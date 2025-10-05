#!/usr/bin/env python3
"""
Seed script for creating initial admin user and payment methods.
This script should be run after the database is initialized.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'complaints_backend'))

from src.models.complaint import db, User, Role, PaymentMethod
from werkzeug.security import generate_password_hash
from flask import Flask
import uuid
from datetime import datetime

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    
    database_url = os.environ.get('DATABASE_URL', 
                                  f"sqlite:///{os.path.join(os.path.dirname(__file__), 'complaints_backend', 'src', 'database', 'app.db')}")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def seed_admin_user():
    """Create default admin user"""
    print("\n=== Creating Admin User ===")
    
    higher_committee_role = Role.query.filter_by(role_name='Higher Committee').first()
    if not higher_committee_role:
        print("❌ Error: 'Higher Committee' role not found. Please run init_data.py first.")
        return False
    
    existing_admin = User.query.filter_by(email='admin@example.com').first()
    if existing_admin:
        print("⚠️  Admin user already exists with email: admin@example.com")
        return True
    
    admin_user = User(
        user_id=str(uuid.uuid4()),
        username='admin',
        email='admin@example.com',
        password_hash=generate_password_hash('ChangeMe123!'),
        full_name='مسؤول النظام',
        phone_number='967700000000',
        address='صنعاء، اليمن',
        role_id=higher_committee_role.role_id,
        is_active=True,
        two_factor_enabled=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(admin_user)
    print(f"✅ Created admin user:")
    print(f"   Email: admin@example.com")
    print(f"   Password: ChangeMe123!")
    print(f"   Role: Higher Committee")
    
    return True

def seed_payment_methods():
    """Create two example payment methods for testing"""
    print("\n=== Creating Payment Methods ===")
    
    payment_methods = [
        {
            'method_id': str(uuid.uuid4()),
            'name': 'محفظة كاك بنك',
            'account_number': '777123456',
            'account_holder': 'نظام الشكاوى الإلكتروني',
            'notes': 'يرجى إرسال المبلغ إلى المحفظة وإرفاق إيصال الدفع',
            'is_active': True,
            'display_order': 1,
            'created_at': datetime.utcnow()
        },
        {
            'method_id': str(uuid.uuid4()),
            'name': 'حساب بنك التضامن الإسلامي',
            'account_number': '1234567890',
            'account_holder': 'اللجنة الاقتصادية العليا',
            'notes': 'التحويل البنكي: بنك التضامن الإسلامي - فرع الزبيري',
            'is_active': True,
            'display_order': 2,
            'created_at': datetime.utcnow()
        }
    ]
    
    for method_data in payment_methods:
        existing_method = PaymentMethod.query.filter_by(
            account_number=method_data['account_number']
        ).first()
        
        if existing_method:
            print(f"⚠️  Payment method already exists: {method_data['name']}")
            continue
        
        payment_method = PaymentMethod(**method_data)
        db.session.add(payment_method)
        print(f"✅ Created payment method: {method_data['name']}")
        print(f"   Account: {method_data['account_number']}")
        print(f"   Holder: {method_data['account_holder']}")
    
    return True

def main():
    """Main seeding function"""
    print("=" * 60)
    print("Database Seeding Script")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables verified/created")
            
            if not seed_admin_user():
                raise Exception("Failed to create admin user")
            
            if not seed_payment_methods():
                raise Exception("Failed to create payment methods")
            
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("✅ Database seeding completed successfully!")
            print("=" * 60)
            print("\nDefault Admin Credentials:")
            print("  📧 Email: admin@example.com")
            print("  🔑 Password: ChangeMe123!")
            print("\nPayment Methods:")
            print("  1. محفظة كاك بنك (777123456)")
            print("  2. حساب بنك التضامن الإسلامي (1234567890)")
            print("\n⚠️  IMPORTANT: Change the admin password after first login!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during seeding: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
