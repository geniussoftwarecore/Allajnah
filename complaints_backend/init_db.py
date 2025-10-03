"""
Initialize database with default roles and data
"""
from src.database.db import db
from src.main import app
from src.models.complaint import Role, ComplaintCategory, ComplaintStatus

def init_database():
    """Initialize database with default data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add default roles if they don't exist
        if Role.query.count() == 0:
            print("Adding default roles...")
            roles = [
                Role(role_id=1, role_name='Trader', description='تاجر - يمكنه تقديم الشكاوى'),
                Role(role_id=2, role_name='Technical Committee', description='لجنة فنية - مراجعة الشكاوى فنياً'),
                Role(role_id=3, role_name='Higher Committee', description='لجنة عليا - إدارة النظام والمستخدمين')
            ]
            for role in roles:
                db.session.add(role)
            db.session.commit()
            print(f"✓ Added {len(roles)} roles")
        else:
            print(f"✓ Roles already exist ({Role.query.count()} roles)")
        
        # Add default complaint categories if they don't exist
        if ComplaintCategory.query.count() == 0:
            print("Adding default complaint categories...")
            categories = [
                ComplaintCategory(category_name='غش تجاري', description='شكاوى تتعلق بالغش التجاري'),
                ComplaintCategory(category_name='جودة المنتج', description='شكاوى تتعلق بجودة المنتجات'),
                ComplaintCategory(category_name='خدمة العملاء', description='شكاوى تتعلق بخدمة العملاء'),
                ComplaintCategory(category_name='تسعير', description='شكاوى تتعلق بالتسعير'),
                ComplaintCategory(category_name='أخرى', description='شكاوى أخرى')
            ]
            for category in categories:
                db.session.add(category)
            db.session.commit()
            print(f"✓ Added {len(categories)} complaint categories")
        else:
            print(f"✓ Complaint categories already exist ({ComplaintCategory.query.count()} categories)")
        
        # Add default complaint statuses if they don't exist
        if ComplaintStatus.query.count() == 0:
            print("Adding default complaint statuses...")
            statuses = [
                ComplaintStatus(status_name='مقدمة', description='شكوى مقدمة حديثاً'),
                ComplaintStatus(status_name='قيد المراجعة', description='جاري مراجعة الشكوى'),
                ComplaintStatus(status_name='محالة للجنة الفنية', description='تمت إحالة الشكوى للجنة الفنية'),
                ComplaintStatus(status_name='محالة للجنة العليا', description='تمت إحالة الشكوى للجنة العليا'),
                ComplaintStatus(status_name='مقبولة', description='تم قبول الشكوى'),
                ComplaintStatus(status_name='مرفوضة', description='تم رفض الشكوى'),
                ComplaintStatus(status_name='مغلقة', description='تم إغلاق الشكوى')
            ]
            for status in statuses:
                db.session.add(status)
            db.session.commit()
            print(f"✓ Added {len(statuses)} complaint statuses")
        else:
            print(f"✓ Complaint statuses already exist ({ComplaintStatus.query.count()} statuses)")
        
        print("\n✓ Database initialization complete!")

if __name__ == '__main__':
    init_database()
