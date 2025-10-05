import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';
import axios from 'axios';

const SubscriptionGate = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSubscriptionStatus();
  }, []);

  const checkSubscriptionStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/subscription/status', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setStatus(response.data);
      setLoading(false);
      
      if (response.data.has_active_subscription) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Error checking subscription:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">جاري التحميل...</p>
        </div>
      </div>
    );
  }

  if (status?.has_pending_payment) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 p-4" dir="rtl">
        <Card className="w-full max-w-lg">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center">
              <Clock className="w-8 h-8 text-yellow-600" />
            </div>
            <CardTitle className="text-2xl">بانتظار المراجعة</CardTitle>
            <CardDescription>طلبك قيد المراجعة. سنبلغك بالنتيجة قريبًا.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                تم استلام إثبات الدفع الخاص بك. سنبلغك بالنتيجة قريبًا.
              </AlertDescription>
            </Alert>
            
            <div className="bg-gray-50 p-4 rounded-lg space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">المبلغ المدفوع:</span>
                <span className="font-semibold">{status.pending_payment.amount} ريال</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">تاريخ الإرسال:</span>
                <span className="font-semibold">
                  {new Date(status.pending_payment.created_at).toLocaleDateString('ar-YE')}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">طريقة الدفع:</span>
                <span className="font-semibold">{status.pending_payment.method_name}</span>
              </div>
            </div>

            <Button 
              onClick={() => navigate('/')} 
              variant="outline" 
              className="w-full"
            >
              العودة للصفحة الرئيسية
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4" dir="rtl">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
            <CheckCircle className="w-10 h-10 text-blue-600" />
          </div>
          <CardTitle className="text-3xl mb-2">اشتراك سنوي لتفعيل حسابك</CardTitle>
          <CardDescription className="text-lg">
            يتطلب استخدام النظام اشتراكًا سنويًا. اضغط (اشترك الآن) للانتقال لخيارات الدفع.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-blue-900 mb-4">مميزات الاشتراك السنوي:</h3>
            <ul className="space-y-3">
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-blue-600 ml-2 mt-0.5 flex-shrink-0" />
                <span>تقديم شكاوى غير محدودة</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-blue-600 ml-2 mt-0.5 flex-shrink-0" />
                <span>متابعة حالة الشكاوى لحظياً</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-blue-600 ml-2 mt-0.5 flex-shrink-0" />
                <span>التواصل المباشر مع اللجان الفنية</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-blue-600 ml-2 mt-0.5 flex-shrink-0" />
                <span>الحصول على تقارير وإحصائيات</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-blue-600 ml-2 mt-0.5 flex-shrink-0" />
                <span>دعم فني متواصل</span>
              </li>
            </ul>
          </div>

          <div className="text-center">
            <Button 
              onClick={() => navigate('/payment')} 
              size="lg"
              className="w-full sm:w-auto px-12 text-lg"
            >
              اشترك الآن
            </Button>
          </div>

          <div className="text-center text-sm text-gray-500">
            <p>هل لديك حساب نشط؟ <button onClick={() => navigate('/')} className="text-blue-600 hover:underline">تسجيل الدخول</button></p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SubscriptionGate;
