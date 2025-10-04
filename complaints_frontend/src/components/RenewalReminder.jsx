import { useState, useEffect } from 'react';
import { Alert, AlertDescription } from './ui/alert';
import { X, AlertTriangle, Info, Clock } from 'lucide-react';
import axios from 'axios';

const RenewalReminder = () => {
  const [renewalStatus, setRenewalStatus] = useState(null);
  const [visible, setVisible] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkRenewalStatus();
  }, []);

  const checkRenewalStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get('/api/renewal/check', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.needs_renewal || response.data.in_grace_period) {
        setRenewalStatus(response.data);
      }
    } catch (error) {
      console.error('Error checking renewal status:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !visible || !renewalStatus) return null;

  const { days_remaining, in_grace_period, grace_days_remaining, subscription } = renewalStatus;

  const getAlertVariant = () => {
    if (in_grace_period) return 'destructive';
    if (days_remaining <= 3) return 'destructive';
    if (days_remaining <= 7) return 'warning';
    return 'default';
  };

  const getIcon = () => {
    if (in_grace_period || days_remaining <= 3) return <AlertTriangle className="h-5 w-5" />;
    if (days_remaining <= 7) return <Clock className="h-5 w-5" />;
    return <Info className="h-5 w-5" />;
  };

  const getMessage = () => {
    if (in_grace_period) {
      return `فترة السماح: اشتراكك انتهى ولديك ${grace_days_remaining} يوم${grace_days_remaining === 1 ? '' : 'اً'} متبقية في فترة السماح. يرجى التجديد فوراً.`;
    }
    if (days_remaining === 0) {
      return 'اشتراكك ينتهي اليوم! يرجى التجديد للحفاظ على الوصول إلى النظام.';
    }
    if (days_remaining === 1) {
      return 'اشتراكك ينتهي غداً! يرجى التجديد في أقرب وقت.';
    }
    if (days_remaining <= 3) {
      return `تنبيه عاجل: اشتراكك سينتهي بعد ${days_remaining} أيام. يرجى التجديد فوراً.`;
    }
    if (days_remaining <= 7) {
      return `تنبيه مهم: اشتراكك سينتهي بعد ${days_remaining} أيام. يرجى التجديد قريباً.`;
    }
    return `تذكير: اشتراكك سينتهي بعد ${days_remaining} يوماً. يرجى التجديد قريباً.`;
  };

  return (
    <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-2xl px-4">
      <Alert variant={getAlertVariant()} className="relative shadow-lg">
        <div className="flex items-start gap-3">
          <div className="mt-0.5">{getIcon()}</div>
          <div className="flex-1">
            <AlertDescription className="text-base">
              {getMessage()}
              {subscription && (
                <div className="mt-2 text-sm opacity-90">
                  تاريخ الانتهاء: {new Date(subscription.end_date).toLocaleDateString('ar-EG')}
                </div>
              )}
              <a
                href="/payment"
                className="inline-block mt-3 px-4 py-2 bg-white text-gray-900 rounded-md hover:bg-gray-100 transition-colors font-medium"
              >
                تجديد الاشتراك الآن
              </a>
            </AlertDescription>
          </div>
          <button
            onClick={() => setVisible(false)}
            className="absolute top-2 left-2 p-1 rounded-md hover:bg-black/10 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </Alert>
    </div>
  );
};

export default RenewalReminder;
