import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navigation from './components/Navigation';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import ComplaintsList from './components/ComplaintsList';
import NewComplaint from './components/NewComplaint';
import Reports from './components/Reports';
import UserManagement from './components/UserManagement';
import SubscriptionGate from './components/SubscriptionGate';
import PaymentPage from './components/PaymentPage';
import PaymentReview from './components/PaymentReview';
import PaymentSettings from './components/PaymentSettings';
import RenewalReminder from './components/RenewalReminder';
import './App.css';

// Axios will use Vite's proxy configuration for /api requests
import axios from 'axios';

function AppContent() {
  const { isAuthenticated, user } = useAuth();

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {isAuthenticated && <Navigation />}
        {isAuthenticated && user?.role_name === 'Trader' && <RenewalReminder />}
        
        <Routes>
          {/* Public Routes */}
          <Route 
            path="/login" 
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />
            } 
          />
          <Route 
            path="/register" 
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <Register />
            } 
          />
          
          {/* Subscription Routes */}
          <Route 
            path="/subscription-gate" 
            element={
              <ProtectedRoute>
                <SubscriptionGate />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/payment" 
            element={
              <ProtectedRoute>
                <PaymentPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Protected Routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          
          {/* Trader Routes */}
          <Route 
            path="/complaints/new" 
            element={
              <ProtectedRoute requiredRoles={['Trader']}>
                <NewComplaint />
              </ProtectedRoute>
            } 
          />
          
          {/* Committee Routes */}
          <Route 
            path="/reports" 
            element={
              <ProtectedRoute requiredRoles={['Technical Committee', 'Higher Committee']}>
                <Reports />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/users" 
            element={
              <ProtectedRoute requiredRoles={['Technical Committee', 'Higher Committee']}>
                <UserManagement />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/payments" 
            element={
              <ProtectedRoute requiredRoles={['Technical Committee', 'Higher Committee']}>
                <PaymentReview />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin/payment-settings" 
            element={
              <ProtectedRoute requiredRoles={['Technical Committee', 'Higher Committee']}>
                <PaymentSettings />
              </ProtectedRoute>
            } 
          />
          
          {/* General Protected Routes */}
          <Route 
            path="/complaints" 
            element={
              <ProtectedRoute>
                <ComplaintsList />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/profile" 
            element={
              <ProtectedRoute>
                <div className="p-6 text-center">
                  <h1 className="text-2xl font-bold">الملف الشخصي</h1>
                  <p className="text-gray-600 mt-2">هذه الصفحة قيد التطوير</p>
                </div>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/settings" 
            element={
              <ProtectedRoute>
                <div className="p-6 text-center">
                  <h1 className="text-2xl font-bold">الإعدادات</h1>
                  <p className="text-gray-600 mt-2">هذه الصفحة قيد التطوير</p>
                </div>
              </ProtectedRoute>
            } 
          />
          
          {/* Default Route */}
          <Route 
            path="/" 
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />
            } 
          />
          
          {/* 404 Route */}
          <Route 
            path="*" 
            element={
              <div className="min-h-screen flex items-center justify-center bg-gray-50" dir="rtl">
                <div className="text-center">
                  <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
                  <p className="text-gray-600 mb-6">الصفحة المطلوبة غير موجودة</p>
                  <button
                    onClick={() => window.history.back()}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    العودة للخلف
                  </button>
                </div>
              </div>
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
