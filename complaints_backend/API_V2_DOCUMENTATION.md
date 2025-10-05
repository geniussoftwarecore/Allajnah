# REST API v2 Documentation

## نمط الاستجابة الموحد

جميع الـ endpoints تستخدم نمط استجابة موحد:

### استجابة نجاح
```json
{
  "success": true,
  "data": { ... },
  "message": "رسالة اختيارية"
}
```

### استجابة خطأ
```json
{
  "success": false,
  "error": "وصف الخطأ",
  "data": null,
  "message": "رسالة اختيارية"
}
```

---

## User Endpoints

### GET /api/subscription/me
**الوصف:** حالة اشتراك المستخدم الحالي

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "has_active_subscription": true,
    "subscription": {
      "subscription_id": 1,
      "user_id": 5,
      "start_date": "2025-01-01T00:00:00",
      "end_date": "2026-01-01T00:00:00",
      "status": "active",
      "is_renewal": false,
      "grace_period_enabled": true
    },
    "has_pending_payment": false,
    "pending_payment": null
  }
}
```

---

### POST /api/payments
**الوصف:** إنشاء إثبات دفع

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
method_id: 1
sender_name: "Ahmed Ali"
sender_phone: "77XXXXXXX"
transaction_reference: "TX1234"  (اختياري)
amount: 50000
payment_date: "2025-10-05T09:30:00Z"
receipt_image: <file>
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "payment": {
      "payment_id": 10,
      "user_id": 5,
      "method_id": 1,
      "sender_name": "Ahmed Ali",
      "sender_phone": "77XXXXXXX",
      "transaction_reference": "TX1234",
      "amount": 50000,
      "payment_date": "2025-10-05T09:30:00",
      "receipt_image_path": "receipt_abc123.jpg",
      "status": "pending",
      "created_at": "2025-10-05T09:35:00"
    }
  },
  "message": "تم إرسال إثبات الدفع بنجاح. سيتم مراجعته قريباً"
}
```

---

### GET /api/payment-methods
**الوصف:** قائمة طرق الدفع النشطة

**Response (200):**
```json
{
  "success": true,
  "data": {
    "payment_methods": [
      {
        "method_id": 1,
        "name": "محفظة يمن موبايل",
        "account_number": "777123456",
        "account_holder": "شركة الشكاوى",
        "qr_image_path": "",
        "notes": "يرجى إدخال الرقم بدقة",
        "is_active": true,
        "display_order": 1
      }
    ]
  }
}
```

---

## Admin Endpoints

### GET /api/admin/payments
**الوصف:** جلب جميع المدفوعات مع فلترة حسب الحالة

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` (optional): pending | approved | rejected (default: pending)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "payments": [
      {
        "payment_id": 10,
        "user_id": 5,
        "user_name": "Ahmed Ali",
        "method_id": 1,
        "method_name": "محفظة يمن موبايل",
        "sender_name": "Ahmed",
        "sender_phone": "77XXXXXXX",
        "amount": 50000,
        "status": "pending",
        "created_at": "2025-10-05T09:35:00"
      }
    ]
  }
}
```

---

### POST /api/admin/payments/{id}/approve
**الوصف:** اعتماد الدفع وتفعيل/تمديد الاشتراك سنة

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body (Optional):**
```json
{
  "notes": "تم الاعتماد"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "subscription": {
      "subscription_id": 15,
      "user_id": 5,
      "start_date": "2025-10-05T00:00:00",
      "end_date": "2026-10-05T00:00:00",
      "status": "active",
      "is_renewal": false
    }
  },
  "message": "تم اعتماد الدفع بنجاح"
}
```

---

### POST /api/admin/payments/{id}/reject
**الوصف:** رفض الدفع مع سبب الرفض

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "admin_note": "صورة الإيصال غير واضحة"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {},
  "message": "تم رفض الدفع"
}
```

---

### GET /api/admin/settings/subscription
**الوصف:** جلب إعدادات الاشتراك (السعر/العملة/فترة السماح)

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "annual_subscription_price": 50000,
    "currency": "YER",
    "grace_period_days": 7,
    "enable_grace_period": true
  }
}
```

---

### POST /api/admin/settings/subscription
**الوصف:** تحديث إعدادات الاشتراك

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "annual_subscription_price": 60000,
  "currency": "YER",
  "grace_period_days": 10,
  "enable_grace_period": true
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {},
  "message": "تم تحديث إعدادات الاشتراك بنجاح"
}
```

---

### GET /api/admin/payment-methods
**الوصف:** جلب جميع طرق الدفع (نشطة وغير نشطة)

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "payment_methods": [ ... ]
  }
}
```

---

### POST /api/admin/payment-methods
**الوصف:** إضافة طريقة دفع جديدة

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "بنك التسليف",
  "account_number": "1234567890",
  "account_holder": "شركة الشكاوى",
  "qr_image_path": "",
  "notes": "ملاحظات إضافية",
  "is_active": true,
  "display_order": 2
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "method": { ... }
  },
  "message": "تم إضافة طريقة الدفع بنجاح"
}
```

---

### PUT /api/admin/payment-methods/{id}
**الوصف:** تحديث طريقة دفع

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "بنك التسليف المحدث",
  "is_active": false
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "method": { ... }
  },
  "message": "تم تحديث طريقة الدفع بنجاح"
}
```

---

### DELETE /api/admin/payment-methods/{id}
**الوصف:** حذف طريقة دفع

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {},
  "message": "تم حذف طريقة الدفع بنجاح"
}
```

---

## Scheduler/Cron Endpoints

### POST /api/admin/tasks/daily
**الوصف:** تشغيل المهام اليومية (للـ cron أو trigger يدوي)

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "expiry_check": {
      "success": true,
      "expired_count": 3
    },
    "renewal_reminders": {
      "success": true,
      "reminders_sent": 5
    }
  },
  "message": "تم تشغيل المهام اليومية بنجاح"
}
```

---

## Webhook Endpoints (اختياري)

### POST /api/webhooks/payment
**الوصف:** استقبال إشعارات من بوابات الدفع المستقبلية

**Request Body:**
```json
{
  "event": "payment.success",
  "payment_id": "ext_123456",
  "amount": 50000,
  "signature": "..."
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {},
  "message": "Webhook received successfully"
}
```

---

## خدمة توليد الاشتراك/التمديد

عند اعتماد الدفع (POST /api/admin/payments/{id}/approve)، يتم تنفيذ الخدمة التالية تلقائياً:

1. **إن كان لدى المستخدم اشتراك نشط:** يبدأ التمديد من `end_date` الحالي
2. **وإلا:** من تاريخ الاعتماد
3. **مدة الاشتراك:** 365 يوم
4. **إرسال إشعار للمستخدم:** "تم تفعيل اشتراكك بنجاح! استمتع بكامل مزايا النظام."

---

## Cron Job Setup

### Linux/Mac
أضف السطر التالي إلى crontab:
```bash
0 2 * * * cd /path/to/project && python complaints_backend/src/cron/daily_tasks.py
```

### Windows Task Scheduler
1. افتح Task Scheduler
2. Create Basic Task
3. اختر Daily trigger
4. اختر وقت التشغيل (مثلاً 2:00 صباحاً)
5. اختر "Start a program"
6. Program: `python.exe`
7. Arguments: `complaints_backend/src/cron/daily_tasks.py`
8. Start in: `/path/to/project`

---

## معايير الأمان

- جميع الـ endpoints تتطلب JWT token في Header
- Admin endpoints محمية بـ `@role_required` decorator
- Rate limiting على endpoints الحساسة (مثل POST /api/payments)
- التحقق من صلاحيات المستخدم قبل الوصول للموارد
