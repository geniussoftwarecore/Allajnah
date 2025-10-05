# دليل الاختبارات - نظام الشكاوى الإلكتروني
# Testing Guide - Electronic Complaints System

## نظرة عامة | Overview

تم تطوير مجموعة اختبارات شاملة لنظام الاشتراكات والدفع تشمل:

A comprehensive test suite has been developed for the subscription and payment system including:

1. **اختبارات الوحدات (Unit Tests)** - `test_subscription_unit.py`
2. **اختبارات التكامل (Integration Tests)** - `test_subscription_integration.py`
3. **اختبارات شاملة E2E (E2E Tests)** - `test_subscription_e2e.py`
4. **اختبارات الأمان (Security Tests)** - `test_auth_security.py`
5. **مجموعة Postman** - `Complaints_System_Postman_Collection.json`

## المتطلبات | Requirements

```bash
pytest==7.0+
pytest-cov==4.0+
```

تم تثبيتها مسبقاً في المشروع | Already installed in the project.

## تشغيل الاختبارات | Running Tests

### 1. تشغيل جميع الاختبارات | Run All Tests

```bash
cd complaints_backend
chmod +x run_tests.sh
./run_tests.sh
```

أو باستخدام pytest مباشرة | Or using pytest directly:

```bash
cd complaints_backend
python -m pytest tests/ -v
```

### 2. تشغيل اختبارات محددة | Run Specific Tests

#### اختبارات الوحدات | Unit Tests
```bash
python -m pytest tests/test_subscription_unit.py -v
```

#### اختبارات التكامل | Integration Tests
```bash
python -m pytest tests/test_subscription_integration.py -v
```

#### اختبارات E2E | E2E Tests
```bash
python -m pytest tests/test_subscription_e2e.py -v
```

#### اختبارات الأمان | Security Tests
```bash
python -m pytest tests/test_auth_security.py -v
```

### 3. تقرير التغطية | Coverage Report

```bash
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
```

سيتم إنشاء تقرير HTML في مجلد `htmlcov/`
An HTML report will be generated in the `htmlcov/` folder.

## الاختبارات المتوفرة | Available Tests

### 1. اختبارات الوحدات (Unit Tests)

| الاختبار | الوصف | Description |
|---------|-------|-------------|
| `test_create_first_subscription` | إنشاء اشتراك جديد لأول مرة | Create first subscription |
| `test_extend_active_subscription` | تمديد اشتراك نشط | Extend active subscription |
| `test_renew_expired_subscription` | تجديد اشتراك منتهي | Renew expired subscription |
| `test_payment_status_updated_on_approval` | تحديث حالة الدفع عند الاعتماد | Update payment status on approval |
| `test_grace_period_setting_respected` | احترام إعداد فترة السماح | Respect grace period setting |
| `test_invalid_user_returns_error` | رفض معرف مستخدم غير موجود | Reject invalid user ID |

### 2. اختبارات التكامل (Integration Tests)

| الاختبار | الوصف | Description |
|---------|-------|-------------|
| `test_complete_subscription_flow` | المسار الكامل للدفع والتفعيل | Complete payment and activation flow |
| `test_payment_rejection_flow` | مسار رفض الدفع | Payment rejection flow |
| `test_multiple_payments_single_subscription` | دفعات متعددة وتمديد | Multiple payments and extension |

### 3. اختبارات E2E (E2E Tests)

| الاختبار | الوصف | Description |
|---------|-------|-------------|
| `test_new_trader_complete_journey` | رحلة التاجر الكاملة من التسجيل للتفعيل | Complete trader journey |
| `test_rejected_payment_scenario` | سيناريو الدفع المرفوض | Rejected payment scenario |
| `test_subscription_info_check` | التحقق من معلومات الاشتراك | Subscription info check |

### 4. اختبارات الأمان (Security Tests)

| الاختبار | الوصف | Description |
|---------|-------|-------------|
| `test_register_defaults_to_trader_role` | التسجيل يعطي دور تاجر فقط | Registration defaults to Trader |
| `test_protected_endpoint_requires_token` | الحماية تتطلب رمز توثيق | Protected endpoints require token |
| `test_role_based_access_control` | التحكم بالوصول حسب الدور | Role-based access control |
| `test_2fa_functionality` | وظائف التوثيق الثنائي | 2FA functionality |

## استخدام Postman Collection

### 1. استيراد المجموعة | Import Collection

1. افتح Postman | Open Postman
2. اضغط Import | Click Import
3. اختر الملف | Select file: `Complaints_System_Postman_Collection.json`

### 2. تكوين المتغيرات | Configure Variables

في Collection Variables:

```
base_url: http://localhost:8000/api
trader_token: (سيتم ملؤه تلقائياً | auto-filled)
admin_token: (سيتم ملؤه تلقائياً | auto-filled)
payment_id: (سيتم ملؤه تلقائياً | auto-filled)
method_id: (سيتم ملؤه تلقائياً | auto-filled)
```

### 3. تشغيل السيناريوهات | Run Scenarios

#### سيناريو 1: تسجيل وتفعيل اشتراك | Registration & Activation

1. ✅ Register New User (Trader)
2. ✅ Login as Trader
3. ✅ Check Subscription Status (غير مفعل | Not active)
4. ✅ Get Payment Methods
5. ✅ Get Subscription Price
6. ✅ Submit Payment (with Receipt)
7. ✅ Login as Admin
8. ✅ Get Pending Payments (Admin)
9. ✅ Approve Payment (Admin)
10. ✅ Check Subscription Status (مفعل | Active)
11. ✅ Access Complaints (مسموح | Allowed)

#### سيناريو 2: رفض الدفع | Payment Rejection

1. ✅ Register New User
2. ✅ Login as Trader
3. ✅ Submit Payment
4. ✅ Login as Admin
5. ✅ Reject Payment (Admin)
6. ✅ Get Notifications (إشعار بالرفض | Rejection notification)
7. ✅ Access Complaints (ممنوع | Blocked)

## تفاصيل التنفيذ | Implementation Details

### بنية قاعدة البيانات المستخدمة | Database Schema Used

- **Users**: المستخدمون (تجار، لجان) | Users (traders, committees)
- **Subscriptions**: الاشتراكات | Subscriptions
- **Payments**: الدفعات | Payments
- **PaymentMethods**: طرق الدفع | Payment methods
- **Settings**: الإعدادات | Settings
- **Notifications**: الإشعارات | Notifications

### الخدمات المختبرة | Tested Services

- `create_or_extend_subscription()` - خدمة التفعيل/التمديد | Activation/Extension service
- تحديث حالة الاشتراك | Subscription status update
- حساب تواريخ الانتهاء | End date calculation
- منطق التمديد | Extension logic

### نقاط النهاية المختبرة | Tested Endpoints

```
POST   /api/register
POST   /api/login
GET    /api/subscription/status
GET    /api/subscription-price
GET    /api/payment-methods
POST   /api/payment/submit
GET    /api/admin/payments
PUT    /api/admin/payments/{id}/approve
PUT    /api/admin/payments/{id}/reject
GET    /api/notifications
GET    /api/complaints (with subscription check)
```

## الملاحظات الهامة | Important Notes

1. **قاعدة بيانات الاختبار**: تستخدم SQLite في الذاكرة (`:memory:`)
   - Test database uses in-memory SQLite

2. **التنظيف التلقائي**: يتم مسح البيانات بعد كل اختبار
   - Automatic cleanup after each test

3. **الملفات الوهمية**: استخدام `io.BytesIO` لمحاكاة رفع الملفات
   - Mock files using `io.BytesIO` for upload simulation

4. **الرموز المميزة**: يتم إنشاؤها تلقائياً في كل اختبار
   - Tokens are auto-generated in each test

## التشخيص | Troubleshooting

### مشكلة: الاختبارات لا تعمل | Tests not running

```bash
# تأكد من تثبيت المتطلبات | Ensure requirements installed
pip install pytest pytest-cov

# تأكد من المسار الصحيح | Ensure correct path
cd complaints_backend
python -m pytest tests/ -v
```

### مشكلة: استيراد الوحدات | Import errors

```bash
# تحقق من PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### مشكلة: فشل الاتصال بقاعدة البيانات | Database connection failures

الاختبارات تستخدم قاعدة بيانات منفصلة في الذاكرة ولا تؤثر على البيانات الحقيقية.

Tests use a separate in-memory database and do not affect real data.

## المساهمة | Contributing

عند إضافة ميزات جديدة، يرجى:
When adding new features, please:

1. كتابة اختبارات الوحدات | Write unit tests
2. كتابة اختبارات التكامل | Write integration tests  
3. تحديث Postman Collection | Update Postman collection
4. تحديث هذا الملف | Update this README

---

**آخر تحديث**: 5 أكتوبر 2025  
**Last Updated**: October 5, 2025
