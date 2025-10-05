# دليل النشر باستخدام Docker

## المتطلبات الأساسية

- Docker 20.10 أو أحدث
- Docker Compose 2.0 أو أحدث

## بنية النظام

يتكون النظام من 4 خدمات رئيسية:

1. **db**: قاعدة بيانات PostgreSQL 15
2. **minio**: خادم تخزين الملفات MinIO
3. **api**: خادم Flask Backend (Port 8000)
4. **web**: خادم Nginx للـ Frontend (Port 5173)

## إعداد البيئة

### 1. متغيرات البيئة (اختياري)

يمكنك إنشاء ملف `.env` في المجلد الرئيسي:

```bash
SESSION_SECRET=your-very-secure-secret-key-here
DATABASE_URL=postgresql://complaints_user:complaints_password_2024@db:5432/complaints_db
```

### 2. بناء وتشغيل النظام

```bash
# بناء وتشغيل جميع الخدمات
docker-compose up --build -d

# عرض السجلات
docker-compose logs -f

# عرض سجلات خدمة معينة
docker-compose logs -f api
docker-compose logs -f web
```

### 3. تهيئة قاعدة البيانات

بعد تشغيل الخدمات، قم بتشغيل سكربتات التهيئة:

```bash
# تهيئة البيانات الأساسية (الأدوار، الفئات، الحالات)
docker-compose exec api python complaints_backend/src/init_data.py

# إنشاء المستخدم الإداري وطرق الدفع التجريبية
docker-compose exec api python seed_data.py
```

## بيانات الدخول الافتراضية

### حساب المسؤول (Admin)

```
البريد الإلكتروني: admin@example.com
كلمة المرور: ChangeMe123!
الدور: اللجنة العليا (Higher Committee)
```

⚠️ **مهم جداً**: يرجى تغيير كلمة المرور بعد أول تسجيل دخول!

### طرق الدفع التجريبية

تم إنشاء طريقتين للدفع لاختبار الواجهة:

1. **محفظة كاك بنك**
   - رقم الحساب: 777123456
   - صاحب الحساب: نظام الشكاوى الإلكتروني

2. **حساب بنك التضامن الإسلامي**
   - رقم الحساب: 1234567890
   - صاحب الحساب: اللجنة الاقتصادية العليا

## الوصول إلى الخدمات

| الخدمة | العنوان | الوصف |
|--------|---------|-------|
| Frontend | http://localhost:5173 | الواجهة الأمامية للنظام |
| Backend API | http://localhost:8000/api | واجهة API الخلفية |
| PostgreSQL | localhost:5432 | قاعدة البيانات |
| MinIO Console | http://localhost:9001 | لوحة تحكم MinIO |
| MinIO API | http://localhost:9000 | واجهة MinIO API |

### بيانات الدخول لـ MinIO Console

```
Username: minioadmin
Password: minioadmin123
```

## أوامر إدارة Docker

### إيقاف الخدمات

```bash
# إيقاف جميع الخدمات
docker-compose down

# إيقاف وحذف البيانات (الحذف الكامل)
docker-compose down -v
```

### إعادة تشغيل خدمة معينة

```bash
docker-compose restart api
docker-compose restart web
```

### بناء خدمة معينة

```bash
docker-compose build api
docker-compose build web
```

### عرض حالة الخدمات

```bash
docker-compose ps
```

### الوصول إلى shell داخل الحاوية

```bash
# الوصول إلى Backend
docker-compose exec api bash

# الوصول إلى قاعدة البيانات
docker-compose exec db psql -U complaints_user -d complaints_db
```

## استكشاف الأخطاء

### مشكلة: الخدمة لا تعمل

```bash
# فحص السجلات
docker-compose logs api
docker-compose logs web

# إعادة بناء الخدمة
docker-compose build --no-cache api
docker-compose up -d api
```

### مشكلة: خطأ في الاتصال بقاعدة البيانات

```bash
# التأكد من أن قاعدة البيانات تعمل
docker-compose ps db

# إعادة تشغيل قاعدة البيانات
docker-compose restart db
```

### مشكلة: Frontend لا يتصل بـ Backend

تأكد من أن:
1. خدمة API تعمل: `docker-compose ps api`
2. إعدادات CORS صحيحة في البيئة
3. Nginx proxy يعمل بشكل صحيح

### فحص الاتصال بقاعدة البيانات

```bash
docker-compose exec api python -c "
from src.database.db import db
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://complaints_user:complaints_password_2024@db:5432/complaints_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    from src.models.complaint import User
    print(f'Total users: {User.query.count()}')
"
```

## النشر في بيئة الإنتاج

### 1. تحديث المتغيرات البيئية

قم بإنشاء ملف `.env.production`:

```bash
SESSION_SECRET=very-strong-secret-key-for-production
DATABASE_URL=postgresql://prod_user:strong_password@prod_db:5432/prod_db
CORS_ORIGINS=https://yourdomain.com
```

### 2. استخدام ملف Docker Compose المخصص للإنتاج

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. إعدادات الأمان المهمة

- ✅ تغيير جميع كلمات المرور الافتراضية
- ✅ استخدام HTTPS مع شهادات SSL
- ✅ تفعيل firewall وحماية المنافذ
- ✅ عمل نسخ احتياطية دورية للبيانات
- ✅ مراقبة السجلات بانتظام

## النسخ الاحتياطي

### حفظ نسخة احتياطية من قاعدة البيانات

```bash
docker-compose exec db pg_dump -U complaints_user complaints_db > backup_$(date +%Y%m%d).sql
```

### استعادة من نسخة احتياطية

```bash
docker-compose exec -T db psql -U complaints_user complaints_db < backup_20241005.sql
```

### حفظ نسخة احتياطية من MinIO

```bash
docker-compose exec minio mc mirror /data /backup
```

## الصيانة

### تنظيف الصور والحاويات القديمة

```bash
docker system prune -a
docker volume prune
```

### تحديث النظام

```bash
# سحب التحديثات من Git
git pull

# إعادة بناء الحاويات
docker-compose build --no-cache

# إعادة تشغيل الخدمات
docker-compose up -d
```

## الدعم والمساعدة

في حالة مواجهة أي مشاكل:

1. راجع السجلات: `docker-compose logs -f`
2. تأكد من وجود المساحة الكافية: `df -h`
3. تأكد من أن المنافذ غير مستخدمة: `netstat -tulpn | grep -E '5173|8000|5432|9000'`
4. راجع ملف `DATABASE_SCHEMA.md` للتفاصيل الفنية

---

**ملاحظة**: هذا النظام تم تصميمه للعمل في بيئة إنتاج آمنة. يرجى اتباع أفضل ممارسات الأمان عند النشر.
