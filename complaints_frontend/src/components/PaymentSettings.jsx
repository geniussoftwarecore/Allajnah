import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Switch } from './ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Plus, Edit, Trash2, Save } from 'lucide-react';
import axios from 'axios';

const PaymentSettings = () => {
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [subscriptionPrice, setSubscriptionPrice] = useState('');
  const [currency, setCurrency] = useState('YER');
  const [gracePeriodDays, setGracePeriodDays] = useState('7');
  const [enableGracePeriod, setEnableGracePeriod] = useState(true);
  const [loading, setLoading] = useState(true);
  const [showMethodDialog, setShowMethodDialog] = useState(false);
  const [editingMethod, setEditingMethod] = useState(null);
  const [methodForm, setMethodForm] = useState({
    name: '',
    account_number: '',
    account_holder: '',
    qr_image_path: '',
    notes: '',
    is_active: true,
    display_order: 0
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [methodsRes, settingsRes] = await Promise.all([
        axios.get('/api/admin/payment-methods', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get('/api/admin/settings', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setPaymentMethods(methodsRes.data.payment_methods);
      
      const priceSetting = settingsRes.data.settings.find(s => s.key === 'annual_subscription_price');
      if (priceSetting) {
        setSubscriptionPrice(priceSetting.value);
      }
      
      const currencySetting = settingsRes.data.settings.find(s => s.key === 'currency');
      if (currencySetting) {
        setCurrency(currencySetting.value);
      }
      
      const graceDaysSetting = settingsRes.data.settings.find(s => s.key === 'grace_period_days');
      if (graceDaysSetting) {
        setGracePeriodDays(graceDaysSetting.value);
      }
      
      const graceEnabledSetting = settingsRes.data.settings.find(s => s.key === 'enable_grace_period');
      if (graceEnabledSetting) {
        setEnableGracePeriod(graceEnabledSetting.value.toLowerCase() === 'true');
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const handleSaveMethod = async () => {
    try {
      const token = localStorage.getItem('token');
      
      if (editingMethod) {
        await axios.put(`/api/admin/payment-methods/${editingMethod.method_id}`, methodForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await axios.post('/api/admin/payment-methods', methodForm, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }

      setShowMethodDialog(false);
      setEditingMethod(null);
      setMethodForm({
        name: '',
        account_number: '',
        account_holder: '',
        qr_image_path: '',
        notes: '',
        is_active: true,
        display_order: 0
      });
      fetchData();
      alert('تم حفظ طريقة الدفع بنجاح');
    } catch (error) {
      console.error('Error saving payment method:', error);
      alert('حدث خطأ أثناء حفظ طريقة الدفع');
    }
  };

  const handleDeleteMethod = async (methodId) => {
    if (!confirm('هل أنت متأكد من حذف طريقة الدفع هذه؟')) return;

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`/api/admin/payment-methods/${methodId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchData();
      alert('تم حذف طريقة الدفع بنجاح');
    } catch (error) {
      console.error('Error deleting payment method:', error);
      alert('حدث خطأ أثناء حذف طريقة الدفع');
    }
  };

  const handleSaveSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.put('/api/admin/settings', 
        { 
          annual_subscription_price: subscriptionPrice,
          currency: currency,
          grace_period_days: gracePeriodDays,
          enable_grace_period: enableGracePeriod ? 'true' : 'false'
        },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      alert('تم حفظ الإعدادات بنجاح');
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('حدث خطأ أثناء حفظ الإعدادات');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-96">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>;
  }

  return (
    <div className="p-6" dir="rtl">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">إعدادات الاشتراك والدفع</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="methods">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="methods">طرق الدفع</TabsTrigger>
              <TabsTrigger value="settings">الإعدادات</TabsTrigger>
            </TabsList>

            <TabsContent value="methods" className="mt-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold">طرق الدفع المتاحة</h3>
                <Button onClick={() => {
                  setEditingMethod(null);
                  setMethodForm({
                    name: '',
                    account_number: '',
                    account_holder: '',
                    qr_image_path: '',
                    notes: '',
                    is_active: true,
                    display_order: 0
                  });
                  setShowMethodDialog(true);
                }}>
                  <Plus className="w-4 h-4 ml-1" />
                  إضافة طريقة دفع
                </Button>
              </div>

              {paymentMethods.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  لا توجد طرق دفع. قم بإضافة طريقة دفع جديدة.
                </div>
              ) : (
                <div className="space-y-4">
                  {paymentMethods.map(method => (
                    <Card key={method.method_id} className="border-2">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div className="space-y-2 flex-1">
                            <div className="flex items-center gap-3">
                              <h4 className="font-semibold text-lg">{method.name}</h4>
                              <span className={`text-sm px-2 py-1 rounded ${
                                method.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                              }`}>
                                {method.is_active ? 'نشط' : 'غير نشط'}
                              </span>
                            </div>
                            <div className="text-sm text-gray-600 space-y-1">
                              <p><span className="font-medium">رقم الحساب:</span> {method.account_number}</p>
                              <p><span className="font-medium">اسم المستلم:</span> {method.account_holder}</p>
                              {method.notes && <p><span className="font-medium">ملاحظات:</span> {method.notes}</p>}
                              <p><span className="font-medium">ترتيب العرض:</span> {method.display_order}</p>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setEditingMethod(method);
                                setMethodForm({
                                  name: method.name,
                                  account_number: method.account_number,
                                  account_holder: method.account_holder,
                                  qr_image_path: method.qr_image_path || '',
                                  notes: method.notes || '',
                                  is_active: method.is_active,
                                  display_order: method.display_order
                                });
                                setShowMethodDialog(true);
                              }}
                            >
                              <Edit className="w-4 h-4 ml-1" />
                              تعديل
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="text-red-600 border-red-200 hover:bg-red-50"
                              onClick={() => handleDeleteMethod(method.method_id)}
                            >
                              <Trash2 className="w-4 h-4 ml-1" />
                              حذف
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="settings" className="mt-6">
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">إعدادات الاشتراك</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div className="space-y-2">
                        <Label htmlFor="subscription_price">سعر الاشتراك السنوي</Label>
                        <Input
                          id="subscription_price"
                          type="number"
                          value={subscriptionPrice}
                          onChange={(e) => setSubscriptionPrice(e.target.value)}
                        />
                        <p className="text-sm text-gray-500">
                          سيتم عرض هذا السعر للمستخدمين عند الاشتراك
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="currency">العملة</Label>
                        <select
                          id="currency"
                          value={currency}
                          onChange={(e) => setCurrency(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        >
                          <option value="YER">ريال يمني (YER)</option>
                          <option value="USD">دولار أمريكي (USD)</option>
                          <option value="SAR">ريال سعودي (SAR)</option>
                        </select>
                        <p className="text-sm text-gray-500">
                          العملة المستخدمة في النظام
                        </p>
                      </div>

                      <div className="space-y-4 pt-4 border-t">
                        <h3 className="font-medium text-lg">إعدادات فترة السماح</h3>
                        
                        <div className="flex items-center justify-between">
                          <div className="space-y-1">
                            <Label htmlFor="enable_grace">تفعيل فترة السماح</Label>
                            <p className="text-sm text-gray-500">
                              السماح للمستخدمين بالوصول للنظام لفترة محدودة بعد انتهاء الاشتراك
                            </p>
                          </div>
                          <Switch
                            id="enable_grace"
                            checked={enableGracePeriod}
                            onCheckedChange={setEnableGracePeriod}
                          />
                        </div>

                        {enableGracePeriod && (
                          <div className="space-y-2">
                            <Label htmlFor="grace_days">عدد أيام فترة السماح</Label>
                            <Input
                              id="grace_days"
                              type="number"
                              min="1"
                              max="30"
                              value={gracePeriodDays}
                              onChange={(e) => setGracePeriodDays(e.target.value)}
                            />
                            <p className="text-sm text-gray-500">
                              عدد الأيام التي يمكن للمستخدم الوصول للنظام بعد انتهاء الاشتراك (1-30 يوم)
                            </p>
                          </div>
                        )}
                      </div>

                      <Button onClick={handleSaveSettings} className="w-full sm:w-auto">
                        <Save className="w-4 h-4 ml-1" />
                        حفظ الإعدادات
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Dialog open={showMethodDialog} onOpenChange={(open) => {
        setShowMethodDialog(open);
        if (!open) {
          setEditingMethod(null);
          setMethodForm({
            name: '',
            account_number: '',
            account_holder: '',
            qr_image_path: '',
            notes: '',
            is_active: true,
            display_order: 0
          });
        }
      }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingMethod ? 'تعديل طريقة الدفع' : 'إضافة طريقة دفع جديدة'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label htmlFor="name">اسم طريقة الدفع *</Label>
              <Input
                id="name"
                value={methodForm.name}
                onChange={(e) => setMethodForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="مثال: محفظة كاش"
              />
            </div>

            <div>
              <Label htmlFor="account_number">رقم الحساب / رقم المحفظة *</Label>
              <Input
                id="account_number"
                value={methodForm.account_number}
                onChange={(e) => setMethodForm(prev => ({ ...prev, account_number: e.target.value }))}
                placeholder="مثال: 777123456"
              />
            </div>

            <div>
              <Label htmlFor="account_holder">اسم صاحب الحساب *</Label>
              <Input
                id="account_holder"
                value={methodForm.account_holder}
                onChange={(e) => setMethodForm(prev => ({ ...prev, account_holder: e.target.value }))}
                placeholder="مثال: محمد أحمد"
              />
            </div>

            <div>
              <Label htmlFor="qr_image">رابط صورة QR (اختياري)</Label>
              <Input
                id="qr_image"
                value={methodForm.qr_image_path}
                onChange={(e) => setMethodForm(prev => ({ ...prev, qr_image_path: e.target.value }))}
                placeholder="مثال: qr_code.png"
              />
            </div>

            <div>
              <Label htmlFor="notes">ملاحظات (اختياري)</Label>
              <Textarea
                id="notes"
                value={methodForm.notes}
                onChange={(e) => setMethodForm(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="أي ملاحظات أو تعليمات إضافية للمستخدمين"
              />
            </div>

            <div>
              <Label htmlFor="display_order">ترتيب العرض</Label>
              <Input
                id="display_order"
                type="number"
                value={methodForm.display_order}
                onChange={(e) => setMethodForm(prev => ({ ...prev, display_order: parseInt(e.target.value) || 0 }))}
              />
            </div>

            <div className="flex items-center gap-2">
              <Switch
                id="is_active"
                checked={methodForm.is_active}
                onCheckedChange={(checked) => setMethodForm(prev => ({ ...prev, is_active: checked }))}
              />
              <Label htmlFor="is_active">طريقة دفع نشطة</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMethodDialog(false)}>
              إلغاء
            </Button>
            <Button onClick={handleSaveMethod}>
              {editingMethod ? 'تحديث' : 'إضافة'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PaymentSettings;
