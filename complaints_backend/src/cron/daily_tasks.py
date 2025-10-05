#!/usr/bin/env python3
"""
وظيفة مجدولة (Scheduler/Cron) يومية:
- إرسال تذكيرات انتهاء (D-14, D-7, D-3) داخل التطبيق
- تغيير الاشتراكات المنتهية إلى expired

تشغيل يدوي:
    python complaints_backend/src/cron/daily_tasks.py

إعداد Cron (Linux/Mac):
    0 2 * * * cd /path/to/project && python complaints_backend/src/cron/daily_tasks.py

إعداد Task Scheduler (Windows):
    استخدم Task Scheduler لتشغيل هذا الملف يومياً
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.db import db
from src.services.scheduler import run_daily_tasks
from flask import Flask

def setup_app():
    """إعداد Flask app للتشغيل خارج السياق الرئيسي"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def main():
    """تشغيل المهام اليومية"""
    app = setup_app()
    
    with app.app_context():
        print("بدء تشغيل المهام اليومية...")
        results = run_daily_tasks()
        
        print("\n=== نتائج التنفيذ ===")
        
        # نتائج فحص الاشتراكات المنتهية
        expiry_result = results.get('expiry_check', {})
        if expiry_result.get('success'):
            print(f"✓ تم تحديث {expiry_result.get('expired_count', 0)} اشتراك منتهي")
        else:
            print(f"✗ خطأ في فحص الاشتراكات: {expiry_result.get('error', 'خطأ غير معروف')}")
        
        # نتائج إرسال التذكيرات
        reminder_result = results.get('renewal_reminders', {})
        if reminder_result.get('success'):
            print(f"✓ تم إرسال {reminder_result.get('reminders_sent', 0)} تذكير تجديد")
        else:
            print(f"✗ خطأ في إرسال التذكيرات: {reminder_result.get('error', 'خطأ غير معروف')}")
        
        print("\n=== اكتمل التنفيذ ===")

if __name__ == '__main__':
    main()
