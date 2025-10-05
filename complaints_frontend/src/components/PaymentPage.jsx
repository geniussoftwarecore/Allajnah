import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Alert, AlertDescription } from './ui/alert';
import { Wallet, Upload, ArrowRight, CheckCircle } from 'lucide-react';
import axios from 'axios';

const PaymentPage = () => {
  const navigate = useNavigate();
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [subscriptionPrice, setSubscriptionPrice] = useState(0);
  const [showProofForm, setShowProofForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    sender_name: '',
    sender_phone: '',
    transaction_reference: '',
    amount: '',
    payment_date: '',
    receipt_image: null
  });

  useEffect(() => {
    fetchPaymentData();
  }, []);

  const fetchPaymentData = async () => {
    try {
      const [methodsRes, priceRes] = await Promise.all([
        axios.get('/api/payment-methods'),
        axios.get('/api/subscription-price')
      ]);
      
      setPaymentMethods(methodsRes.data.payment_methods);
      setSubscriptionPrice(priceRes.data.price);
      setFormData(prev => ({ ...prev, amount: priceRes.data.price }));
      setLoading(false);
    } catch (error) {
      console.error('Error fetching payment data:', error);
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData(prev => ({ ...prev, receipt_image: file }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const token = localStorage.getItem('token');
      const submitData = new FormData();
      submitData.append('method_id', selectedMethod.method_id);
      submitData.append('sender_name', formData.sender_name);
      submitData.append('sender_phone', formData.sender_phone);
      submitData.append('transaction_reference', formData.transaction_reference);
      submitData.append('amount', formData.amount);
      submitData.append('payment_date', formData.payment_date);
      submitData.append('receipt_image', formData.receipt_image);

      await axios.post('/api/payment/submit', submitData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      navigate('/subscription-gate');
    } catch (error) {
      console.error('Error submitting payment:', error);
      alert('حدث خطأ أثناء إرسال إثبات الدفع. يرجى المحاولة مرة أخرى.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (showProofForm && selectedMethod) {
    return (
      <div className="min-h-screen bg-gray-50 p-4" dir="rtl">
        <div className="max-w-3xl mx-auto py-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">إثبات الدفع</CardTitle>
              <CardDescription>أدخل معلومات التحويل وارفع صورة الإيصال. سنراجع الطلب خلال وقت قصير.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-900">
                    طريقة الدفع المختارة: <strong>{selectedMethod.name}</strong>
                  </p>
                  <p className="text-sm text-blue-900 mt-1">
                    رقم الحساب: <strong>{selectedMethod.account_number}</strong>
                  </p>
                  <p className="text-sm text-blue-900 mt-1">
                    اسم المستلم: <strong>{selectedMethod.account_holder}</strong>
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="sender_name">اسم المُرسل *</Label>
                    <Input
                      id="sender_name"
                      value={formData.sender_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, sender_name: e.target.value }))}
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="sender_phone">رقم هاتف المُرسل *</Label>
                    <Input
                      id="sender_phone"
                      type="tel"
                      value={formData.sender_phone}
                      onChange={(e) => setFormData(prev => ({ ...prev, sender_phone: e.target.value }))}
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="transaction_reference">مرجع التحويل / آخر 4 أرقام</Label>
                    <Input
                      id="transaction_reference"
                      value={formData.transaction_reference}
                      onChange={(e) => setFormData(prev => ({ ...prev, transaction_reference: e.target.value }))}
                      placeholder="اختياري"
                    />
                  </div>

                  <div>
                    <Label htmlFor="amount">المبلغ (ريال يمني) *</Label>
                    <Input
                      id="amount"
                      type="number"
                      value={formData.amount}
                      onChange={(e) => setFormData(prev => ({ ...prev, amount: e.target.value }))}
                      required
                      readOnly
                    />
                  </div>

                  <div>
                    <Label htmlFor="payment_date">تاريخ ووقت التحويل *</Label>
                    <Input
                      id="payment_date"
                      type="datetime-local"
                      value={formData.payment_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, payment_date: e.target.value }))}
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="receipt_image">صورة الإيصال (لقطة شاشة) *</Label>
                    <Input
                      id="receipt_image"
                      type="file"
                      accept="image/*,.pdf"
                      onChange={handleFileChange}
                      required
                    />
                    <p className="text-sm text-gray-500 mt-1">صيغ مسموحة: JPG, PNG, PDF</p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowProofForm(false)}
                    className="flex-1"
                  >
                    رجوع
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting}
                    className="flex-1"
                  >
                    {submitting ? 'جاري الإرسال...' : 'إرسال إثبات الدفع'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4" dir="rtl">
      <div className="max-w-4xl mx-auto py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">إتمام الاشتراك السنوي</h1>
          <p className="text-gray-600">اختر طريقة الدفع المناسبة لك</p>
        </div>

        <Card className="mb-8">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-lg text-gray-700 mb-2">قيمة الاشتراك السنوي</p>
              <p className="text-4xl font-bold text-blue-600">{subscriptionPrice.toLocaleString('ar-YE')} ريال</p>
              <p className="text-gray-500 mt-1">صالح لمدة سنة كاملة</p>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">طرق الدفع المتاحة</h2>
          
          {paymentMethods.length === 0 ? (
            <Alert>
              <AlertDescription>
                لا توجد طرق دفع متاحة حالياً. يرجى التواصل مع الدعم الفني.
              </AlertDescription>
            </Alert>
          ) : (
            paymentMethods.map(method => (
              <Card 
                key={method.method_id}
                className={`cursor-pointer transition-all hover:shadow-lg ${
                  selectedMethod?.method_id === method.method_id ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => setSelectedMethod(method)}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Wallet className="w-6 h-6 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg mb-2">{method.name}</h3>
                        <div className="space-y-1 text-sm text-gray-600">
                          <p><span className="font-medium">رقم الحساب:</span> {method.account_number}</p>
                          <p><span className="font-medium">اسم المستلم:</span> {method.account_holder}</p>
                          {method.notes && <p className="text-gray-500 mt-2">{method.notes}</p>}
                        </div>
                        {method.qr_image_path && (
                          <div className="mt-3">
                            <img 
                              src={`/api/payment/receipt/${method.qr_image_path}`} 
                              alt="QR Code" 
                              className="w-32 h-32 border rounded"
                            />
                          </div>
                        )}
                      </div>
                    </div>
                    {selectedMethod?.method_id === method.method_id && (
                      <CheckCircle className="w-6 h-6 text-blue-600 flex-shrink-0" />
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {selectedMethod && (
          <div className="mt-8 flex gap-3">
            <Button
              variant="outline"
              onClick={() => navigate('/subscription-gate')}
              className="flex-1"
            >
              إلغاء
            </Button>
            <Button
              onClick={() => setShowProofForm(true)}
              className="flex-1"
            >
              أتممت التحويل/الدفع
              <ArrowRight className="mr-2 h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentPage;
