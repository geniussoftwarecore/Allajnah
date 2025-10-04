import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { CheckCircle, XCircle, Eye, Clock } from 'lucide-react';
import axios from 'axios';

const PaymentReview = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [reviewAction, setReviewAction] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [activeTab, setActiveTab] = useState('pending');

  useEffect(() => {
    fetchPayments(activeTab);
  }, [activeTab]);

  const fetchPayments = async (status) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/admin/payments?status=${status}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPayments(response.data.payments);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching payments:', error);
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`/api/admin/payment/${selectedPayment.payment_id}/approve`, 
        { notes: reviewNotes },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      setSelectedPayment(null);
      setReviewAction(null);
      setReviewNotes('');
      fetchPayments(activeTab);
      alert('تم اعتماد الدفع بنجاح');
    } catch (error) {
      console.error('Error approving payment:', error);
      alert('حدث خطأ أثناء اعتماد الدفع');
    }
  };

  const handleReject = async () => {
    if (!reviewNotes.trim()) {
      alert('يرجى إدخال سبب الرفض');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(`/api/admin/payment/${selectedPayment.payment_id}/reject`, 
        { reason: reviewNotes },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      setSelectedPayment(null);
      setReviewAction(null);
      setReviewNotes('');
      fetchPayments(activeTab);
      alert('تم رفض الدفع');
    } catch (error) {
      console.error('Error rejecting payment:', error);
      alert('حدث خطأ أثناء رفض الدفع');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'pending':
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
          <Clock className="w-3 h-3 ml-1" />
          بانتظار المراجعة
        </Badge>;
      case 'approved':
        return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
          <CheckCircle className="w-3 h-3 ml-1" />
          معتمد
        </Badge>;
      case 'rejected':
        return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
          <XCircle className="w-3 h-3 ml-1" />
          مرفوض
        </Badge>;
      default:
        return null;
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
          <CardTitle className="text-2xl">مراجعة المدفوعات</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="pending">بانتظار المراجعة</TabsTrigger>
              <TabsTrigger value="approved">معتمدة</TabsTrigger>
              <TabsTrigger value="rejected">مرفوضة</TabsTrigger>
            </TabsList>

            <TabsContent value={activeTab} className="mt-6">
              {payments.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  لا توجد مدفوعات {activeTab === 'pending' ? 'بانتظار المراجعة' : activeTab === 'approved' ? 'معتمدة' : 'مرفوضة'}
                </div>
              ) : (
                <div className="space-y-4">
                  {payments.map(payment => (
                    <Card key={payment.payment_id} className="border-2">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div className="space-y-2 flex-1">
                            <div className="flex items-center gap-3">
                              <h3 className="font-semibold text-lg">{payment.user_name}</h3>
                              {getStatusBadge(payment.status)}
                            </div>
                            
                            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                              <div>
                                <span className="text-gray-600">المبلغ:</span>
                                <span className="font-medium mr-2">{payment.amount} ريال</span>
                              </div>
                              <div>
                                <span className="text-gray-600">طريقة الدفع:</span>
                                <span className="font-medium mr-2">{payment.method_name}</span>
                              </div>
                              <div>
                                <span className="text-gray-600">اسم المُرسل:</span>
                                <span className="font-medium mr-2">{payment.sender_name}</span>
                              </div>
                              <div>
                                <span className="text-gray-600">رقم الهاتف:</span>
                                <span className="font-medium mr-2">{payment.sender_phone}</span>
                              </div>
                              {payment.transaction_reference && (
                                <div>
                                  <span className="text-gray-600">مرجع التحويل:</span>
                                  <span className="font-medium mr-2">{payment.transaction_reference}</span>
                                </div>
                              )}
                              <div>
                                <span className="text-gray-600">تاريخ الدفع:</span>
                                <span className="font-medium mr-2">
                                  {new Date(payment.payment_date).toLocaleDateString('ar-YE')}
                                </span>
                              </div>
                            </div>

                            {payment.reviewed_by_name && (
                              <div className="mt-3 pt-3 border-t text-sm">
                                <div className="text-gray-600">
                                  تمت المراجعة بواسطة: <span className="font-medium">{payment.reviewed_by_name}</span>
                                  {payment.reviewed_at && (
                                    <span className="mr-2">
                                      في {new Date(payment.reviewed_at).toLocaleDateString('ar-YE')}
                                    </span>
                                  )}
                                </div>
                                {payment.review_notes && (
                                  <div className="mt-1">
                                    <span className="text-gray-600">ملاحظات:</span>
                                    <span className="mr-2">{payment.review_notes}</span>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>

                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedPayment(payment);
                                setReviewAction('view');
                              }}
                            >
                              <Eye className="w-4 h-4 ml-1" />
                              عرض الإيصال
                            </Button>
                            
                            {payment.status === 'pending' && (
                              <>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="text-green-600 border-green-200 hover:bg-green-50"
                                  onClick={() => {
                                    setSelectedPayment(payment);
                                    setReviewAction('approve');
                                  }}
                                >
                                  <CheckCircle className="w-4 h-4 ml-1" />
                                  اعتماد
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="text-red-600 border-red-200 hover:bg-red-50"
                                  onClick={() => {
                                    setSelectedPayment(payment);
                                    setReviewAction('reject');
                                  }}
                                >
                                  <XCircle className="w-4 h-4 ml-1" />
                                  رفض
                                </Button>
                              </>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Dialog open={reviewAction === 'view'} onOpenChange={() => {
        setReviewAction(null);
        setSelectedPayment(null);
      }}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>إيصال الدفع</DialogTitle>
          </DialogHeader>
          {selectedPayment && (
            <div className="mt-4">
              <img
                src={`/api/payment/receipt/${selectedPayment.receipt_image_path}`}
                alt="إيصال الدفع"
                className="w-full rounded-lg border"
              />
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={reviewAction === 'approve'} onOpenChange={() => {
        setReviewAction(null);
        setSelectedPayment(null);
        setReviewNotes('');
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>اعتماد الدفع</DialogTitle>
            <DialogDescription>
              هل أنت متأكد من اعتماد هذا الدفع؟ سيتم تفعيل اشتراك المستخدم لمدة سنة كاملة.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <Label htmlFor="approve_notes">ملاحظات (اختياري)</Label>
            <Textarea
              id="approve_notes"
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="أدخل أي ملاحظات..."
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setReviewAction(null);
              setSelectedPayment(null);
              setReviewNotes('');
            }}>
              إلغاء
            </Button>
            <Button onClick={handleApprove} className="bg-green-600 hover:bg-green-700">
              تأكيد الاعتماد
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={reviewAction === 'reject'} onOpenChange={() => {
        setReviewAction(null);
        setSelectedPayment(null);
        setReviewNotes('');
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>رفض الدفع</DialogTitle>
            <DialogDescription>
              يرجى إدخال سبب رفض الدفع. سيتم إرسال إشعار للمستخدم مع السبب.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <Label htmlFor="reject_reason">سبب الرفض *</Label>
            <Textarea
              id="reject_reason"
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="أدخل سبب الرفض..."
              required
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setReviewAction(null);
              setSelectedPayment(null);
              setReviewNotes('');
            }}>
              إلغاء
            </Button>
            <Button onClick={handleReject} className="bg-red-600 hover:bg-red-700">
              تأكيد الرفض
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PaymentReview;
