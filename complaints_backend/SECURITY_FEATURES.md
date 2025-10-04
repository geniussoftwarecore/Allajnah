# الميزات الأمنية | Security Features

تم التحديث: 4 أكتوبر 2025

---

## 1. المصادقة والترخيص | Authentication & Authorization

### JWT Authentication ✅
- استخدام JSON Web Tokens للمصادقة
- مدة صلاحية Token: 24 ساعة
- خوارزمية التشفير: HS256
- مفتاح سري من متغيرات البيئة: `SESSION_SECRET`

### Role-Based Access Control (RBAC) ✅
الأدوار المتاحة:
- **Trader** (تاجر): الوصول الأساسي مع بوابة اشتراك
- **Technical Committee** (اللجنة الفنية): صلاحيات إدارية
- **Higher Committee** (اللجنة العليا): صلاحيات عليا

### الحماية بالأدوار
```python
@token_required
@role_required(['Technical Committee', 'Higher Committee'])
def admin_function(current_user):
    ...
```

### Two-Factor Authentication (2FA) ✅
- دعم TOTP (Time-based One-Time Password)
- توليد QR Code للإعداد
- مكتبة: `pyotp`

---

## 2. نظام الاشتراكات | Subscription System

### بوابة الاشتراك ✅
- **منع الوصول التلقائي**: جميع endpoints للتجار محمية
- **المسارات المستثناة** (غير محمية):
  - `/api/subscription/status`
  - `/api/payment-methods`
  - `/api/subscription-price`
  - `/api/payment/submit`
  - `/api/payment/receipt/*`

### فترة السماح (Grace Period) ✅
- مدة افتراضية: 7 أيام
- قابلة للتفعيل/التعطيل من الإعدادات
- إشعارات تلقائية: 14، 7، 3 أيام قبل الانتهاء

---

## 3. Rate Limiting ⚡

### الحدود المطبقة

#### endpoints المصادقة
- **التسجيل**: 5 طلبات في الساعة
  ```python
  @rate_limit("5 per hour")
  def register():
  ```

- **تسجيل الدخول**: 10 طلبات في الدقيقة
  ```python
  @rate_limit("10 per minute")
  def login():
  ```

- **التحقق الثنائي**: 10 طلبات في الدقيقة
  ```python
  @rate_limit("10 per minute")
  def validate_2fa():
  ```

#### endpoints الدفع
- **إرسال إثبات الدفع**: 3 طلبات في الساعة
  ```python
  @rate_limit("3 per hour")
  def submit_payment():
  ```

### الحد الافتراضي
- 200 طلب في اليوم
- 50 طلب في الساعة

### التخزين
- Development: `memory://`
- Production: يمكن استخدام Redis: `redis://localhost:6379`

---

## 4. أمان رفع الملفات | File Upload Security

### القيود والتحققات ✅

#### 1. حجم الملف
- الحد الأقصى: **5 ميجابايت**
- يطبق على مستوى Flask: `MAX_CONTENT_LENGTH`
- تحقق إضافي في كود التطبيق

#### 2. أنواع الملفات المسموحة
- **الامتدادات**: `png`, `jpg`, `jpeg` فقط
- **MIME Types المسموحة**:
  - `image/png`
  - `image/jpeg`
  - `image/jpg`

#### 3. فحص MIME Type
- استخدام `python-magic` للتحقق الفعلي من نوع الملف
- **لا يعتمد على الامتداد فقط**
- يكتشف المحاولات الخبيثة (مثل: ملف .exe معاد تسميته إلى .jpg)

```python
def validate_mime_type(file_path):
    mime = magic.Magic(mime=True)
    file_mime = mime.from_file(file_path)
    return file_mime in ALLOWED_MIME_TYPES
```

#### 4. أسماء ملفات عشوائية وآمنة
- توليد UUID عشوائي لكل ملف
- استخدام `secure_filename()` من Werkzeug
- منع Path Traversal attacks
- منع المحارف الخطرة: `../`, `\0`, newlines, etc.

```python
def generate_secure_filename(original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower()
    random_name = str(uuid.uuid4())
    return secure_filename(f"{random_name}.{ext}")
```

#### 5. التخزين الآمن
- المسار: `complaints_backend/src/uploads/receipts/`
- إنشاء تلقائي للمجلد إذا لم يكن موجوداً
- الوصول محمي بالمصادقة والترخيص

### عملية الرفع الكاملة
```python
success, result = validate_and_save_file(file, UPLOAD_FOLDER)
```

المراحل:
1. ✅ فحص وجود الملف
2. ✅ فحص الامتداد
3. ✅ فحص الحجم (≤5MB)
4. ✅ توليد اسم آمن
5. ✅ حفظ مؤقت
6. ✅ فحص MIME Type الفعلي
7. ✅ حذف الملف إذا فشل التحقق
8. ✅ إرجاع اسم الملف الآمن

---

## 5. التحقق من البيانات | Data Validation

### التحقق القوي من بيانات الدفع ✅

```python
def validate_payment_data(data):
    errors = []
    
    # الحقول المطلوبة
    required_fields = {
        'method_id': 'معرف طريقة الدفع',
        'sender_name': 'اسم المُرسل',
        'sender_phone': 'رقم الهاتف',
        'amount': 'المبلغ',
        'payment_date': 'تاريخ الدفع'
    }
    
    # التحقق من اسم المُرسل
    - الحد الأدنى: 3 أحرف
    - الحد الأقصى: 255 حرف
    
    # التحقق من رقم الهاتف
    - الحد الأدنى: 9 أرقام
    - الحد الأقصى: 15 رقم
    - أرقام فقط (مع دعم +)
    
    # التحقق من المبلغ
    - يجب أن يكون > 0
    - الحد الأقصى: 10,000,000
    
    # مرجع العملية
    - اختياري
    - الحد الأقصى: 255 حرف
```

### منع SQL Injection ✅
- استخدام SQLAlchemy ORM
- معاملات معلمة (Parameterized Queries)
- عدم تنفيذ SQL خام من مدخلات المستخدم

### منع XSS ✅
- تنظيف جميع المدخلات
- استخدام JSON responses
- Flask auto-escaping في templates (إن وجدت)

---

## 6. CORS Configuration

### إعدادات CORS المحسّنة ✅

```python
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
CORS(app, origins=cors_origins, supports_credentials=True)
```

**Production**:
```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**Development**:
```bash
CORS_ORIGINS=http://localhost:5000,http://localhost:3000
```

### الميزات
- ✅ Origins قابلة للتخصيص
- ✅ دعم Credentials
- ✅ فصل بين Development و Production

---

## 7. متغيرات البيئة | Environment Variables

### الملف: `.env.example` ✅

```bash
# المفاتيح السرية
SECRET_KEY=your-secret-key-here
SESSION_SECRET=your-session-secret-here

# رفع الملفات
MAX_FILE_SIZE_MB=5
UPLOAD_FOLDER=./src/uploads/receipts

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
RATELIMIT_DEFAULT=200 per day;50 per hour

# CORS
CORS_ORIGINS=http://localhost:5000,http://localhost:3000

# قاعدة البيانات
DATABASE_URL=sqlite:///./src/database/app.db
```

### الأمان في Production
⚠️ **مطلوب**:
1. تغيير `SECRET_KEY` و `SESSION_SECRET`
2. استخدام مفاتيح عشوائية قوية (32+ حرف)
3. عدم تضمين `.env` في Git
4. استخدام Redis للـ rate limiting
5. تحديد CORS origins بدقة

---

## 8. سجلات المراجعة | Audit Logs

### تسجيل العمليات الحساسة ✅

جدول `audit_logs` يسجل:
- تغيير الأدوار
- إنشاء/حذف المستخدمين
- الموافقة/رفض المدفوعات
- تفعيل/انتهاء الاشتراكات
- عنوان IP
- تفاصيل العملية

```python
audit_log = AuditLog(
    action_type='payment_approved',
    performed_by_id=admin.user_id,
    affected_user_id=user.user_id,
    old_value='pending',
    new_value='approved',
    description=f'تمت الموافقة على الدفع بمبلغ {amount} ريال',
    ip_address=request.remote_addr
)
```

---

## 9. حماية الملفات | File Access Protection

### الوصول إلى الإيصالات ✅

```python
@subscription_bp.route('/payment/receipt/<filename>', methods=['GET'])
@token_required
def get_receipt(current_user, filename):
    payment = Payment.query.filter_by(receipt_image_path=filename).first()
    
    is_admin = current_user.role.role_name in ['Technical Committee', 'Higher Committee']
    is_owner = payment.user_id == current_user.user_id
    
    if not (is_admin or is_owner):
        return jsonify({'message': 'غير مصرح بالوصول'}), 403
    
    return send_from_directory(UPLOAD_FOLDER, filename)
```

**القيود**:
- ✅ مصادقة مطلوبة
- ✅ فقط المالك أو الإداري
- ✅ التحقق من وجود الملف في قاعدة البيانات

---

## 10. Headers الأمنية | Security Headers

### التوصيات للإنتاج

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

---

## ✅ ملخص التحسينات المطبقة

### المصادقة والترخيص
- [x] JWT Authentication
- [x] Role-Based Access Control
- [x] Two-Factor Authentication
- [x] Subscription Gateway
- [x] Token Expiration

### Rate Limiting
- [x] Login endpoints
- [x] Registration
- [x] 2FA validation
- [x] Payment submission
- [x] Configurable limits

### رفع الملفات
- [x] Size limit (5MB)
- [x] Extension validation
- [x] MIME type checking
- [x] Secure random filenames
- [x] Path traversal prevention
- [x] File access authorization

### التحقق من البيانات
- [x] Payment data validation
- [x] Input sanitization
- [x] SQL injection prevention
- [x] XSS prevention

### الإعدادات
- [x] CORS configuration
- [x] Environment variables
- [x] Audit logging
- [x] Security headers (recommended)

---

## 🔐 قائمة التحقق للإنتاج

### قبل النشر
- [ ] تغيير جميع المفاتيح السرية
- [ ] تحديد CORS origins
- [ ] استخدام Redis للـ rate limiting
- [ ] تفعيل HTTPS
- [ ] تشغيل Gunicorn (وليس Flask dev server)
- [ ] فحص الأمان (penetration testing)
- [ ] مراجعة سجلات المراجعة
- [ ] نسخ احتياطي للقاعدة
- [ ] تحديد Security Headers
- [ ] فحص الثغرات (OWASP Top 10)

### المراقبة
- [ ] تتبع محاولات تسجيل الدخول الفاشلة
- [ ] مراقبة استهلاك Rate Limits
- [ ] تنبيهات للعمليات المشبوهة
- [ ] تحليل سجلات المراجعة

---

**تم التطوير بواسطة:** Replit Agent  
**التاريخ:** 4 أكتوبر 2025
