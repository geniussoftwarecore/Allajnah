# API Documentation - تطبيق الشكاوى الإلكتروني

## نظرة عامة

يوفر هذا التطبيق واجهات برمجة تطبيقات (APIs) شاملة لإدارة نظام الشكاوى الإلكتروني. جميع المسارات تبدأ بـ `/api` ويتطلب معظمها مصادقة عبر JWT Token.

## المصادقة (Authentication)

### تسجيل مستخدم جديد
```
POST /api/register
Content-Type: application/json

{
  "username": "trader1",
  "email": "trader1@example.com",
  "password": "password123",
  "full_name": "أحمد محمد",
  "phone_number": "777123456",
  "address": "صنعاء، اليمن",
  "role_name": "Trader"
}
```

**الاستجابة:**
```json
{
  "message": "User created successfully",
  "user": {
    "user_id": "uuid",
    "username": "trader1",
    "email": "trader1@example.com",
    "full_name": "أحمد محمد",
    "role_name": "Trader"
  }
}
```

### تسجيل الدخول
```
POST /api/login
Content-Type: application/json

{
  "username": "trader1",
  "password": "password123"
}
```

**الاستجابة:**
```json
{
  "message": "Login successful",
  "token": "jwt_token_here",
  "user": {
    "user_id": "uuid",
    "username": "trader1",
    "full_name": "أحمد محمد",
    "role_name": "Trader"
  }
}
```

### الحصول على الملف الشخصي
```
GET /api/profile
Authorization: Bearer jwt_token_here
```

### تحديث الملف الشخصي
```
PUT /api/profile
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
  "full_name": "أحمد محمد علي",
  "phone_number": "777654321",
  "address": "عدن، اليمن"
}
```

### تغيير كلمة المرور
```
POST /api/change-password
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

### الحصول على الأدوار المتاحة
```
GET /api/roles
```

## إدارة الشكاوى (Complaints Management)

### إنشاء شكوى جديدة (للتجار فقط)
```
POST /api/complaints
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
  "title": "مشكلة في التخليص الجمركي",
  "description": "تأخير في إجراءات التخليص الجمركي للبضائع المستوردة",
  "category_id": 2,
  "priority": "High"
}
```

### الحصول على قائمة الشكاوى
```
GET /api/complaints?page=1&per_page=10&status_id=1&category_id=2&priority=High&search=تأخير
Authorization: Bearer jwt_token_here
```

**المعاملات الاختيارية:**
- `page`: رقم الصفحة (افتراضي: 1)
- `per_page`: عدد العناصر في الصفحة (افتراضي: 10)
- `status_id`: تصفية حسب الحالة
- `category_id`: تصفية حسب التصنيف
- `priority`: تصفية حسب الأولوية (Low, Medium, High)
- `search`: البحث في العنوان والوصف
- `assigned_only`: للجنة الفنية - عرض الشكاوى المعينة فقط (true/false)

**الاستجابة:**
```json
{
  "complaints": [
    {
      "complaint_id": "uuid",
      "title": "مشكلة في التخليص الجمركي",
      "description": "تأخير في إجراءات التخليص الجمركي",
      "category_name": "جمركية",
      "status_name": "جديدة",
      "priority": "High",
      "trader_name": "أحمد محمد",
      "submitted_at": "2024-01-01T10:00:00",
      "attachments_count": 2,
      "comments_count": 1
    }
  ],
  "total": 25,
  "pages": 3,
  "current_page": 1,
  "per_page": 10
}
```

### الحصول على تفاصيل شكوى محددة
```
GET /api/complaints/{complaint_id}
Authorization: Bearer jwt_token_here
```

**الاستجابة:**
```json
{
  "complaint": {
    "complaint_id": "uuid",
    "title": "مشكلة في التخليص الجمركي",
    "description": "تأخير في إجراءات التخليص الجمركي",
    "category_name": "جمركية",
    "status_name": "جديدة",
    "priority": "High",
    "trader_name": "أحمد محمد",
    "submitted_at": "2024-01-01T10:00:00",
    "comments": [
      {
        "comment_id": "uuid",
        "author_name": "سارة أحمد",
        "author_role": "Technical Committee",
        "comment_text": "تم استلام الشكوى وسيتم المتابعة",
        "created_at": "2024-01-01T11:00:00"
      }
    ],
    "attachments": [
      {
        "attachment_id": "uuid",
        "file_name": "invoice.pdf",
        "file_type": "application/pdf",
        "uploaded_at": "2024-01-01T10:05:00"
      }
    ]
  }
}
```

### تحديث حالة الشكوى (للجنة الفنية والعليا فقط)
```
PUT /api/complaints/{complaint_id}/status
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
  "status_id": 4,
  "resolution_details": "تم حل المشكلة بالتنسيق مع الجمارك"
}
```

### تعيين شكوى لعضو لجنة فنية (للجنة الفنية والعليا فقط)
```
PUT /api/complaints/{complaint_id}/assign
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
  "assigned_to_committee_id": "committee_member_uuid"
}
```

### إضافة تعليق على شكوى
```
POST /api/complaints/{complaint_id}/comments
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
  "comment_text": "تم التواصل مع الجهة المختصة وسيتم الرد خلال 48 ساعة"
}
```

## البيانات المرجعية (Reference Data)

### الحصول على تصنيفات الشكاوى
```
GET /api/categories
Authorization: Bearer jwt_token_here
```

**الاستجابة:**
```json
{
  "categories": [
    {
      "category_id": 1,
      "category_name": "مالية",
      "description": "الشكاوى المتعلقة بالأمور المالية والضرائب والرسوم"
    },
    {
      "category_id": 2,
      "category_name": "جمركية",
      "description": "الشكاوى المتعلقة بالإجراءات الجمركية والتخليص"
    }
  ]
}
```

### الحصول على حالات الشكاوى
```
GET /api/statuses
Authorization: Bearer jwt_token_here
```

**الاستجابة:**
```json
{
  "statuses": [
    {
      "status_id": 1,
      "status_name": "جديدة",
      "description": "شكوى جديدة لم يتم البدء في معالجتها"
    },
    {
      "status_id": 2,
      "status_name": "تحت المعالجة",
      "description": "شكوى قيد المعالجة من قبل اللجنة الفنية"
    }
  ]
}
```

## لوحة المتابعة (Dashboard)

### إحصائيات لوحة المتابعة (للجنة الفنية والعليا فقط)
```
GET /api/dashboard/stats
Authorization: Bearer jwt_token_here
```

**الاستجابة:**
```json
{
  "total_complaints": 150,
  "recent_complaints": 25,
  "status_distribution": [
    {"status": "جديدة", "count": 30},
    {"status": "تحت المعالجة", "count": 45},
    {"status": "تم حلها", "count": 60},
    {"status": "مكتملة", "count": 15}
  ],
  "category_distribution": [
    {"category": "جمركية", "count": 60},
    {"category": "مالية", "count": 40},
    {"category": "خدمات", "count": 30},
    {"category": "تقنية", "count": 20}
  ],
  "priority_distribution": [
    {"priority": "High", "count": 45},
    {"priority": "Medium", "count": 75},
    {"priority": "Low", "count": 30}
  ]
}
```

## رموز الاستجابة (Response Codes)

- `200 OK`: العملية نجحت
- `201 Created`: تم إنشاء المورد بنجاح
- `400 Bad Request`: خطأ في البيانات المرسلة
- `401 Unauthorized`: غير مصرح بالوصول (مطلوب تسجيل دخول)
- `403 Forbidden`: ممنوع (صلاحيات غير كافية)
- `404 Not Found`: المورد غير موجود
- `500 Internal Server Error`: خطأ في الخادم

## المصادقة والتفويض

### استخدام JWT Token
جميع المسارات المحمية تتطلب إرسال JWT Token في header:
```
Authorization: Bearer your_jwt_token_here
```

### الأدوار والصلاحيات

#### التاجر (Trader)
- إنشاء شكاوى جديدة
- عرض شكاواه فقط
- إضافة تعليقات على شكاواه
- تحديث ملفه الشخصي

#### اللجنة الفنية (Technical Committee)
- عرض جميع الشكاوى
- تحديث حالة الشكاوى
- تعيين الشكاوى لأعضاء اللجنة
- إضافة تعليقات على الشكاوى
- عرض إحصائيات لوحة المتابعة

#### اللجنة العليا (Higher Committee)
- جميع صلاحيات اللجنة الفنية
- عرض تقارير شاملة
- اتخاذ قرارات نهائية

## أمثلة على الاستخدام

### سيناريو كامل: تقديم شكوى ومتابعتها

1. **تسجيل تاجر جديد:**
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "email": "trader1@example.com",
    "password": "password123",
    "full_name": "أحمد محمد",
    "role_name": "Trader"
  }'
```

2. **تسجيل الدخول:**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "password": "password123"
  }'
```

3. **إنشاء شكوى:**
```bash
curl -X POST http://localhost:5000/api/complaints \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "تأخير في التخليص الجمركي",
    "description": "تأخير غير مبرر في إجراءات التخليص",
    "category_id": 2,
    "priority": "High"
  }'
```

4. **متابعة الشكوى:**
```bash
curl -X GET http://localhost:5000/api/complaints \
  -H "Authorization: Bearer YOUR_TOKEN"
```

هذا التوثيق يوفر دليلاً شاملاً لاستخدام واجهات برمجة التطبيقات في تطبيق الشكاوى الإلكتروني.
