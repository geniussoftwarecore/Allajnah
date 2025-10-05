# Docker Quick Start Guide

## 🚀 البدء السريع

### 1. تشغيل النظام

```bash
# بناء وتشغيل جميع الخدمات
docker-compose up --build -d

# انتظر حوالي 30 ثانية للتأكد من تشغيل جميع الخدمات
docker-compose ps
```

### 2. تهيئة قاعدة البيانات

```bash
# تهيئة البيانات الأساسية
docker-compose exec api python complaints_backend/src/init_data.py

# إنشاء المستخدم الإداري وطرق الدفع
docker-compose exec api python seed_data.py
```

### 3. الوصول إلى النظام

افتح المتصفح على: **http://localhost:5173**

### 4. تسجيل الدخول

```
البريد الإلكتروني: admin@example.com
كلمة المرور: ChangeMe123!
```

---

## 📝 أوامر مفيدة

```bash
# عرض السجلات
docker-compose logs -f

# إيقاف الخدمات
docker-compose down

# إعادة التشغيل
docker-compose restart

# حذف البيانات والبدء من جديد
docker-compose down -v
docker-compose up --build -d
```

---

## 🔗 الخدمات المتاحة

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)
- **PostgreSQL**: localhost:5432

---

للمزيد من التفاصيل، راجع ملف `DOCKER_DEPLOYMENT.md`
