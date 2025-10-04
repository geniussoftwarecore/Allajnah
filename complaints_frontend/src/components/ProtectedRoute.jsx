import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const ProtectedRoute = ({ children, requiredRoles = [] }) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [checkingSubscription, setCheckingSubscription] = useState(true);

  useEffect(() => {
    const checkSubscription = async () => {
      if (isAuthenticated && user?.role_name === 'Trader') {
        const subscriptionPages = ['/subscription-gate', '/payment'];
        if (subscriptionPages.includes(location.pathname)) {
          setCheckingSubscription(false);
          return;
        }

        try {
          const token = localStorage.getItem('token');
          const response = await axios.get('/api/subscription/status', {
            headers: { Authorization: `Bearer ${token}` }
          });
          setSubscriptionStatus(response.data);
        } catch (error) {
          console.error('Error checking subscription:', error);
        }
      }
      setCheckingSubscription(false);
    };

    if (!loading) {
      checkSubscription();
    }
  }, [isAuthenticated, user, loading, location.pathname]);

  // Show loading spinner while checking authentication
  if (loading || (isAuthenticated && user?.role_name === 'Trader' && checkingSubscription)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">جاري التحقق من الصلاحيات...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role-based access if required roles are specified
  if (requiredRoles.length > 0 && !requiredRoles.includes(user?.role_name)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50" dir="rtl">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            غير مصرح بالوصول
          </h2>
          <p className="text-gray-600 mb-6">
            ليس لديك الصلاحيات اللازمة للوصول إلى هذه الصفحة.
          </p>
          <button
            onClick={() => window.history.back()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            العودة للخلف
          </button>
        </div>
      </div>
    );
  }

  // Check subscription status for Traders
  const subscriptionPages = ['/subscription-gate', '/payment'];
  if (
    user?.role_name === 'Trader' && 
    !subscriptionPages.includes(location.pathname) && 
    subscriptionStatus && 
    !subscriptionStatus.has_active_subscription &&
    !subscriptionStatus.has_pending_payment
  ) {
    return <Navigate to="/subscription-gate" replace />;
  }

  return children;
};

export default ProtectedRoute;
