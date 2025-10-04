"""
Migration Script: Add missing fields to existing tables
Created: 2025-10-04
Description: Adds missing columns and indexes to subscriptions, payments, and payment_methods tables
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy import text
from src.database.db import db
from src.main import app

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result]
    return column_name in columns

def run_migration():
    """Execute migration to add missing fields"""
    
    with app.app_context():
        try:
            print("Starting migration: Adding missing fields to tables...")
            
            # 1. Add missing fields to subscriptions table
            print("\n1. Checking subscriptions table...")
            
            if not column_exists('subscriptions', 'plan'):
                db.session.execute(text("""
                    ALTER TABLE subscriptions ADD COLUMN plan VARCHAR(50) DEFAULT 'annual'
                """))
                print("   ✓ Added 'plan' column to subscriptions")
            else:
                print("   - 'plan' column already exists")
            
            if not column_exists('subscriptions', 'renewed_from'):
                db.session.execute(text("""
                    ALTER TABLE subscriptions ADD COLUMN renewed_from VARCHAR(36)
                """))
                print("   ✓ Added 'renewed_from' column to subscriptions")
                print("   ℹ Note: Foreign key constraint for 'renewed_from' will be enforced at application level (SQLite limitation)")
            else:
                print("   - 'renewed_from' column already exists")
            
            # 2. Add missing currency field to payments table
            print("\n2. Checking payments table...")
            
            if not column_exists('payments', 'currency'):
                db.session.execute(text("""
                    ALTER TABLE payments ADD COLUMN currency VARCHAR(10) DEFAULT 'YER'
                """))
                print("   ✓ Added 'currency' column to payments")
            else:
                print("   - 'currency' column already exists")
            
            # 3. Create indexes for better performance
            print("\n3. Creating indexes...")
            
            indexes = [
                ("idx_users_role_id", "users", "role_id"),
                ("idx_users_email", "users", "email"),
                ("idx_users_username", "users", "username"),
                ("idx_complaints_trader_id", "complaints", "trader_id"),
                ("idx_complaints_status_id", "complaints", "status_id"),
                ("idx_complaints_category_id", "complaints", "category_id"),
                ("idx_complaints_assigned_to", "complaints", "assigned_to_committee_id"),
                ("idx_subscriptions_user_id", "subscriptions", "user_id"),
                ("idx_subscriptions_status", "subscriptions", "status"),
                ("idx_subscriptions_end_date", "subscriptions", "end_date"),
                ("idx_payments_user_id", "payments", "user_id"),
                ("idx_payments_status", "payments", "status"),
                ("idx_payments_reviewed_by_id", "payments", "reviewed_by_id"),
                ("idx_audit_logs_performed_by", "audit_logs", "performed_by_id"),
                ("idx_audit_logs_affected_user", "audit_logs", "affected_user_id"),
                ("idx_audit_logs_action_type", "audit_logs", "action_type"),
                ("idx_settings_key", "settings", "key"),
            ]
            
            for idx_name, table_name, column_name in indexes:
                try:
                    db.session.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name})
                    """))
                    print(f"   ✓ Created index: {idx_name}")
                except Exception as e:
                    print(f"   - Index {idx_name} may already exist or error: {e}")
            
            # 4. Commit all changes
            db.session.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    run_migration()
