#!/usr/bin/env python3
"""
Database initialization script for the complaints application.
This script populates the database with default roles, categories, and statuses.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.complaint import db, Role, ComplaintCategory, ComplaintStatus
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'asdf#FGSgvasgf$5$WGT')
    
    database_url = os.environ.get('DATABASE_URL', 
                                  f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def init_roles():
    """Initialize default user roles"""
    roles_data = [
        {
            'role_name': 'Trader',
            'description': 'التاجر - يمكنه تقديم الشكاوى ومتابعتها'
        },
        {
            'role_name': 'Technical Committee',
            'description': 'اللجنة الفنية - تستلم وتعالج الشكاوى'
        },
        {
            'role_name': 'Higher Committee',
            'description': 'اللجنة العليا - تراقب الأداء وتتخذ القرارات النهائية'
        }
    ]
    
    for role_data in roles_data:
        existing_role = Role.query.filter_by(role_name=role_data['role_name']).first()
        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)
            print(f"Added role: {role_data['role_name']}")
        else:
            print(f"Role already exists: {role_data['role_name']}")

def init_complaint_categories():
    """Initialize complaint categories based on the provided document"""
    categories_data = [
        {
            'category_name': 'مالية',
            'description': 'الشكاوى المتعلقة بالأمور المالية والضرائب والرسوم'
        },
        {
            'category_name': 'جمركية',
            'description': 'الشكاوى المتعلقة بالإجراءات الجمركية والتخليص'
        },
        {
            'category_name': 'خدمات',
            'description': 'الشكاوى المتعلقة بجودة الخدمات المقدمة'
        },
        {
            'category_name': 'تقنية',
            'description': 'الشكاوى المتعلقة بالأنظمة التقنية والمواصفات'
        },
        {
            'category_name': 'بيئية',
            'description': 'الشكاوى المتعلقة بالتصاريح البيئية والمتطلبات البيئية'
        },
        {
            'category_name': 'استثمارية',
            'description': 'الشكاوى المتعلقة بالاستثمار والمشاريع'
        },
        {
            'category_name': 'أخرى',
            'description': 'الشكاوى التي لا تندرج تحت التصنيفات الأخرى'
        }
    ]
    
    for category_data in categories_data:
        existing_category = ComplaintCategory.query.filter_by(category_name=category_data['category_name']).first()
        if not existing_category:
            category = ComplaintCategory(**category_data)
            db.session.add(category)
            print(f"Added category: {category_data['category_name']}")
        else:
            print(f"Category already exists: {category_data['category_name']}")

def init_complaint_statuses():
    """Initialize complaint statuses"""
    statuses_data = [
        {
            'status_name': 'جديدة',
            'description': 'شكوى جديدة لم يتم البدء في معالجتها'
        },
        {
            'status_name': 'تحت المعالجة',
            'description': 'شكوى قيد المعالجة من قبل اللجنة الفنية'
        },
        {
            'status_name': 'قيد المتابعة',
            'description': 'شكوى تحتاج متابعة مع جهات أخرى'
        },
        {
            'status_name': 'تم حلها',
            'description': 'شكوى تم حلها بنجاح'
        },
        {
            'status_name': 'مكتملة',
            'description': 'شكوى مكتملة ومغلقة'
        },
        {
            'status_name': 'مرفوضة',
            'description': 'شكوى مرفوضة لأسباب قانونية أو فنية'
        },
        {
            'status_name': 'تحفظ لعدم التجاوب',
            'description': 'شكوى محفوظة بسبب عدم تجاوب الجهة المعنية'
        },
        {
            'status_name': 'تحفظ لعدم توفير الأوليات',
            'description': 'شكوى محفوظة بسبب عدم توفير المستندات المطلوبة'
        },
        {
            'status_name': 'تحفظ لصحة الإجراءات',
            'description': 'شكوى محفوظة للتحقق من صحة الإجراءات'
        },
        {
            'status_name': 'رفع مذكرة بالرأي القانوني',
            'description': 'تم رفع مذكرة بالرأي القانوني للجنة الاقتصادية العليا'
        }
    ]
    
    for status_data in statuses_data:
        existing_status = ComplaintStatus.query.filter_by(status_name=status_data['status_name']).first()
        if not existing_status:
            status = ComplaintStatus(**status_data)
            db.session.add(status)
            print(f"Added status: {status_data['status_name']}")
        else:
            print(f"Status already exists: {status_data['status_name']}")

def main():
    """Main initialization function"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully")
        
        # Initialize data
        print("\nInitializing roles...")
        init_roles()
        
        print("\nInitializing complaint categories...")
        init_complaint_categories()
        
        print("\nInitializing complaint statuses...")
        init_complaint_statuses()
        
        # Commit all changes
        try:
            db.session.commit()
            print("\nDatabase initialization completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"\nError during database initialization: {str(e)}")
            return False
    
    return True

if __name__ == '__main__':
    success = main()
    if success:
        print("\n✅ Database initialization completed successfully!")
        print("\nNext steps:")
        print("1. Start the Flask application: python src/main.py")
        print("2. Create user accounts via the /api/register endpoint")
        print("3. Begin using the complaints system")
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)
