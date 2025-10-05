#!/bin/bash

echo "=========================================="
echo "تشغيل اختبارات نظام الشكاوى الإلكتروني"
echo "Running Complaints System Tests"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

echo "1️⃣  اختبارات الأمان والتوثيق (Authentication & Security Tests)..."
echo "-------------------------------------------"
python -m pytest tests/test_auth_security.py -v
echo ""

echo "2️⃣  اختبارات الوحدات - خدمات الاشتراك (Unit Tests - Subscription Services)..."
echo "-------------------------------------------"
python -m pytest tests/test_subscription_unit.py -v
echo ""

echo "3️⃣  اختبارات التكامل - مسار الدفع الكامل (Integration Tests - Payment Flow)..."
echo "-------------------------------------------"
python -m pytest tests/test_subscription_integration.py -v
echo ""

echo "4️⃣  اختبارات شاملة - سيناريوهات المستخدم (E2E Tests - User Journeys)..."
echo "-------------------------------------------"
python -m pytest tests/test_subscription_e2e.py -v
echo ""

echo "=========================================="
echo "✅ اكتملت جميع الاختبارات"
echo "All tests completed"
echo "=========================================="
echo ""

echo "📊 تقرير التغطية (Coverage Report):"
echo "-------------------------------------------"
python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
echo ""

echo "💡 تم إنشاء تقرير التغطية في: htmlcov/index.html"
echo "Coverage report generated at: htmlcov/index.html"
