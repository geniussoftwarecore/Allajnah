# مخطط قاعدة البيانات - نظام الشكاوى الإلكتروني
# Database Schema - Electronic Complaints System

تم التحديث: 4 أكتوبر 2025
Updated: October 4, 2025

---

## الجداول الرئيسية | Main Tables

### 1. users (المستخدمون)
جدول المستخدمين الرئيسي مع دعم المصادقة الثنائية

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | VARCHAR(36) | PRIMARY KEY | معرف فريد للمستخدم (UUID) |
| username | VARCHAR(255) | UNIQUE, NOT NULL | اسم المستخدم |
| email | VARCHAR(255) | UNIQUE, NOT NULL | البريد الإلكتروني |
| password_hash | VARCHAR(255) | NOT NULL | كلمة المرور المشفرة |
| full_name | VARCHAR(255) | NOT NULL | الاسم الكامل |
| phone_number | VARCHAR(50) | | رقم الهاتف |
| address | TEXT | | العنوان |
| role_id | INTEGER | FK → roles.role_id, NOT NULL | معرف الدور |
| is_active | BOOLEAN | DEFAULT TRUE | حالة تفعيل الحساب |
| two_factor_enabled | BOOLEAN | DEFAULT FALSE | تفعيل المصادقة الثنائية |
| two_factor_secret | VARCHAR(32) | | مفتاح المصادقة الثنائية |
| created_at | DATETIME | | تاريخ الإنشاء |
| updated_at | DATETIME | | تاريخ آخر تحديث |

**Indexes:**
- idx_users_role_id (role_id)
- idx_users_email (email)
- idx_users_username (username)

---

### 2. roles (الأدوار)
أدوار المستخدمين في النظام

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| role_id | INTEGER | PRIMARY KEY | معرف الدور |
| role_name | VARCHAR(50) | UNIQUE, NOT NULL | اسم الدور (Trader, Technical Committee, Higher Committee) |
| description | TEXT | | وصف الدور |

**الأدوار المتاحة:**
- Trader (تاجر)
- Technical Committee (اللجنة الفنية)
- Higher Committee (اللجنة العليا)

---

### 3. subscriptions (الاشتراكات)
اشتراكات المستخدمين السنوية مع دعم التجديد وفترة السماح

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| subscription_id | VARCHAR(36) | PRIMARY KEY | معرف الاشتراك (UUID) |
| user_id | VARCHAR(36) | FK → users.user_id, NOT NULL | معرف المستخدم |
| plan | VARCHAR(50) | DEFAULT 'annual' | خطة الاشتراك (سنوي) |
| start_date | DATETIME | NOT NULL | تاريخ بداية الاشتراك |
| end_date | DATETIME | NOT NULL | تاريخ نهاية الاشتراك |
| status | VARCHAR(20) | DEFAULT 'active' | الحالة (active, expired, canceled) |
| is_renewal | BOOLEAN | DEFAULT FALSE | هل هو تجديد |
| renewed_from | VARCHAR(36) | FK → subscriptions.subscription_id | معرف الاشتراك السابق (للتجديدات) |
| grace_period_enabled | BOOLEAN | DEFAULT TRUE | تفعيل فترة السماح |
| notified_14d | BOOLEAN | DEFAULT FALSE | تم الإشعار قبل 14 يوم |
| notified_7d | BOOLEAN | DEFAULT FALSE | تم الإشعار قبل 7 أيام |
| notified_3d | BOOLEAN | DEFAULT FALSE | تم الإشعار قبل 3 أيام |
| created_at | DATETIME | | تاريخ الإنشاء |
| updated_at | DATETIME | | تاريخ آخر تحديث |

**Indexes:**
- idx_subscriptions_user_id (user_id)
- idx_subscriptions_status (status)
- idx_subscriptions_end_date (end_date)

**Foreign Keys:**
- user_id → users.user_id
- renewed_from → subscriptions.subscription_id (self-reference for renewals)

---

### 4. payment_methods (طرق الدفع)
طرق الدفع المتاحة (محافظ إلكترونية وحسابات بنكية)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| method_id | VARCHAR(36) | PRIMARY KEY | معرف طريقة الدفع (UUID) |
| name | VARCHAR(255) | NOT NULL | اسم طريقة الدفع |
| account_number | VARCHAR(255) | NOT NULL | رقم الحساب |
| account_holder | VARCHAR(255) | NOT NULL | اسم صاحب الحساب |
| qr_image_path | VARCHAR(500) | | مسار صورة QR Code |
| notes | TEXT | | ملاحظات إضافية |
| is_active | BOOLEAN | DEFAULT TRUE | حالة التفعيل |
| display_order | INTEGER | DEFAULT 0 | ترتيب العرض |
| created_at | DATETIME | | تاريخ الإنشاء |

---

### 5. payments (المدفوعات)
سجل المدفوعات والاشتراكات مع مراجعة الإدارة

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| payment_id | VARCHAR(36) | PRIMARY KEY | معرف الدفع (UUID) |
| user_id | VARCHAR(36) | FK → users.user_id, NOT NULL | معرف المستخدم |
| method_id | VARCHAR(36) | FK → payment_methods.method_id, NOT NULL | معرف طريقة الدفع |
| sender_name | VARCHAR(255) | NOT NULL | اسم المُرسل |
| sender_phone | VARCHAR(50) | NOT NULL | رقم هاتف المُرسل |
| transaction_reference | VARCHAR(255) | | مرجع العملية |
| amount | FLOAT | NOT NULL | المبلغ |
| currency | VARCHAR(10) | DEFAULT 'YER' | العملة (YER, USD, SAR) |
| payment_date | DATETIME | NOT NULL | تاريخ الدفع |
| receipt_image_path | VARCHAR(500) | NOT NULL | مسار صورة الإيصال |
| status | VARCHAR(20) | DEFAULT 'pending' | الحالة (pending, approved, rejected) |
| reviewed_by_id | VARCHAR(36) | FK → users.user_id | معرف المراجع (إداري) |
| review_notes | TEXT | | ملاحظات المراجعة |
| reviewed_at | DATETIME | | تاريخ المراجعة |
| created_at | DATETIME | | تاريخ الإنشاء |

**Indexes:**
- idx_payments_user_id (user_id)
- idx_payments_status (status)
- idx_payments_reviewed_by_id (reviewed_by_id)

**Foreign Keys:**
- user_id → users.user_id
- method_id → payment_methods.method_id
- reviewed_by_id → users.user_id

---

### 6. complaints (الشكاوى)
شكاوى التجار مع التتبع والإدارة

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| complaint_id | VARCHAR(36) | PRIMARY KEY | معرف الشكوى (UUID) |
| trader_id | VARCHAR(36) | FK → users.user_id, NOT NULL | معرف التاجر |
| title | VARCHAR(255) | NOT NULL | عنوان الشكوى |
| description | TEXT | NOT NULL | وصف الشكوى |
| category_id | INTEGER | FK → complaint_categories.category_id, NOT NULL | معرف التصنيف |
| status_id | INTEGER | FK → complaint_statuses.status_id, NOT NULL | معرف الحالة |
| priority | VARCHAR(50) | DEFAULT 'Medium' | الأولوية |
| submitted_at | DATETIME | | تاريخ التقديم |
| last_updated_at | DATETIME | | تاريخ آخر تحديث |
| assigned_to_committee_id | VARCHAR(36) | FK → users.user_id | معرف عضو اللجنة المسؤول |
| resolution_details | TEXT | | تفاصيل الحل |
| closed_at | DATETIME | | تاريخ الإغلاق |

**Indexes:**
- idx_complaints_trader_id (trader_id)
- idx_complaints_status_id (status_id)
- idx_complaints_category_id (category_id)
- idx_complaints_assigned_to (assigned_to_committee_id)

**Foreign Keys:**
- trader_id → users.user_id
- category_id → complaint_categories.category_id
- status_id → complaint_statuses.status_id
- assigned_to_committee_id → users.user_id

---

### 7. complaint_categories (تصنيفات الشكاوى)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| category_id | INTEGER | PRIMARY KEY | معرف التصنيف |
| category_name | VARCHAR(100) | UNIQUE, NOT NULL | اسم التصنيف |
| description | TEXT | | الوصف |

---

### 8. complaint_statuses (حالات الشكاوى)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| status_id | INTEGER | PRIMARY KEY | معرف الحالة |
| status_name | VARCHAR(50) | UNIQUE, NOT NULL | اسم الحالة |
| description | TEXT | | الوصف |

---

### 9. complaint_attachments (مرفقات الشكاوى)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| attachment_id | VARCHAR(36) | PRIMARY KEY | معرف المرفق (UUID) |
| complaint_id | VARCHAR(36) | FK → complaints.complaint_id, NOT NULL | معرف الشكوى |
| file_name | VARCHAR(255) | NOT NULL | اسم الملف |
| file_path | VARCHAR(255) | NOT NULL | مسار الملف |
| file_type | VARCHAR(50) | | نوع الملف |
| uploaded_at | DATETIME | | تاريخ الرفع |

**Foreign Keys:**
- complaint_id → complaints.complaint_id (CASCADE DELETE)

---

### 10. complaint_comments (تعليقات الشكاوى)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| comment_id | VARCHAR(36) | PRIMARY KEY | معرف التعليق (UUID) |
| complaint_id | VARCHAR(36) | FK → complaints.complaint_id, NOT NULL | معرف الشكوى |
| user_id | VARCHAR(36) | FK → users.user_id, NOT NULL | معرف المستخدم |
| comment_text | TEXT | NOT NULL | نص التعليق |
| created_at | DATETIME | | تاريخ الإنشاء |

**Foreign Keys:**
- complaint_id → complaints.complaint_id (CASCADE DELETE)
- user_id → users.user_id

---

### 11. notifications (الإشعارات)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| notification_id | VARCHAR(36) | PRIMARY KEY | معرف الإشعار (UUID) |
| user_id | VARCHAR(36) | FK → users.user_id, NOT NULL | معرف المستخدم |
| complaint_id | VARCHAR(36) | FK → complaints.complaint_id | معرف الشكوى (اختياري) |
| message | TEXT | NOT NULL | نص الإشعار |
| type | VARCHAR(50) | | نوع الإشعار |
| is_read | BOOLEAN | DEFAULT FALSE | حالة القراءة |
| created_at | DATETIME | | تاريخ الإنشاء |

**Foreign Keys:**
- user_id → users.user_id
- complaint_id → complaints.complaint_id

---

### 12. settings (الإعدادات)
إعدادات النظام العامة (الأسعار، فترة السماح، إلخ)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| setting_id | VARCHAR(36) | PRIMARY KEY | معرف الإعداد (UUID) |
| key | VARCHAR(100) | UNIQUE, NOT NULL | مفتاح الإعداد |
| value | TEXT | NOT NULL | قيمة الإعداد (نص أو JSON) |
| description | TEXT | | وصف الإعداد |
| updated_at | DATETIME | | تاريخ آخر تحديث |

**Indexes:**
- idx_settings_key (key)

**الإعدادات المتوقعة:**
- `subscription_price`: سعر الاشتراك السنوي
- `currency`: العملة الافتراضية (YER, USD, SAR)
- `grace_period_days`: عدد أيام فترة السماح (افتراضي: 7)
- `enable_grace_period`: تفعيل فترة السماح (true/false)

---

### 13. audit_logs (سجلات المراجعة)
سجل شامل لجميع العمليات الحساسة في النظام

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| log_id | VARCHAR(36) | PRIMARY KEY | معرف السجل (UUID) |
| action_type | VARCHAR(100) | NOT NULL | نوع العملية |
| performed_by_id | VARCHAR(36) | FK → users.user_id, NOT NULL | منفذ العملية |
| affected_user_id | VARCHAR(36) | FK → users.user_id | المستخدم المتأثر |
| old_value | TEXT | | القيمة القديمة |
| new_value | TEXT | | القيمة الجديدة |
| description | TEXT | | وصف العملية |
| ip_address | VARCHAR(45) | | عنوان IP |
| created_at | DATETIME | | تاريخ العملية |

**Indexes:**
- idx_audit_logs_performed_by (performed_by_id)
- idx_audit_logs_affected_user (affected_user_id)
- idx_audit_logs_action_type (action_type)

**Foreign Keys:**
- performed_by_id → users.user_id
- affected_user_id → users.user_id

**أنواع العمليات المسجلة:**
- `role_change`: تغيير دور المستخدم
- `user_created`: إنشاء مستخدم جديد
- `user_deleted`: حذف مستخدم
- `status_change`: تغيير حالة الشكوى
- `payment_approved`: الموافقة على الدفع
- `payment_rejected`: رفض الدفع
- `subscription_activated`: تفعيل الاشتراك
- `subscription_expired`: انتهاء الاشتراك

---

## العلاقات الرئيسية | Key Relationships

### نظام المستخدمين والأدوار
- `users.role_id` → `roles.role_id` (Many-to-One)

### نظام الاشتراكات والدفع
- `subscriptions.user_id` → `users.user_id` (Many-to-One)
- `subscriptions.renewed_from` → `subscriptions.subscription_id` (Self-Reference للتجديدات)
- `payments.user_id` → `users.user_id` (Many-to-One)
- `payments.method_id` → `payment_methods.method_id` (Many-to-One)
- `payments.reviewed_by_id` → `users.user_id` (Many-to-One)

### نظام الشكاوى
- `complaints.trader_id` → `users.user_id` (Many-to-One)
- `complaints.assigned_to_committee_id` → `users.user_id` (Many-to-One)
- `complaints.category_id` → `complaint_categories.category_id` (Many-to-One)
- `complaints.status_id` → `complaint_statuses.status_id` (Many-to-One)
- `complaint_attachments.complaint_id` → `complaints.complaint_id` (Many-to-One, CASCADE DELETE)
- `complaint_comments.complaint_id` → `complaints.complaint_id` (Many-to-One, CASCADE DELETE)
- `complaint_comments.user_id` → `users.user_id` (Many-to-One)

### نظام الإشعارات والمراجعة
- `notifications.user_id` → `users.user_id` (Many-to-One)
- `notifications.complaint_id` → `complaints.complaint_id` (Many-to-One)
- `audit_logs.performed_by_id` → `users.user_id` (Many-to-One)
- `audit_logs.affected_user_id` → `users.user_id` (Many-to-One)

---

## ملاحظات التنفيذ | Implementation Notes

### قيود SQLite
- **Foreign Key Constraints**: SQLite لا يدعم إضافة قيود المفاتيح الأجنبية بعد إنشاء الجدول. يتم تطبيق قيد `renewed_from` على مستوى التطبيق.
- **Indexes**: تم إنشاء جميع الفهارس بنجاح لتحسين الأداء.

### سلامة البيانات
- جميع المفاتيح الرئيسية تستخدم UUID (VARCHAR(36)) لضمان الفرادة
- استخدام CASCADE DELETE على مرفقات وتعليقات الشكاوى لضمان النظافة عند الحذف
- جميع الحقول الهامة محددة بـ NOT NULL لمنع القيم الفارغة
- استخدام UNIQUE constraints على الحقول المهمة (email, username, role_name, etc.)

### الفهارس المُنشأة
تم إنشاء 17 فهرس لتحسين أداء الاستعلامات:
- فهارس المستخدمين (3)
- فهارس الشكاوى (4)
- فهارس الاشتراكات (3)
- فهارس المدفوعات (3)
- فهارس سجلات المراجعة (3)
- فهرس الإعدادات (1)

---

## تحديثات الترحيل | Migration Updates

**التاريخ: 4 أكتوبر 2025**

### الحقول المُضافة:
1. **subscriptions.plan** (VARCHAR(50), DEFAULT 'annual')
2. **subscriptions.renewed_from** (VARCHAR(36), FK to subscriptions.subscription_id)
3. **payments.currency** (VARCHAR(10), DEFAULT 'YER')

### الفهارس المُنشأة:
- تم إنشاء 17 فهرس لتحسين الأداء

### ملاحظات:
- جميع البيانات الموجودة محفوظة
- لا توجد عمليات حذف أو تعديل على البيانات الحالية
- التحديثات متوافقة مع الإصدار السابق (backward compatible)
