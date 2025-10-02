import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  Users, 
  TrendingUp,
  Plus,
  Search,
  Filter,
  BarChart3
} from 'lucide-react';
import axios from 'axios';

const Dashboard = () => {
  const { user, isTrader, isTechnicalCommittee, isHigherCommittee } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentComplaints, setRecentComplaints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch dashboard statistics (for committee members)
        if (isTechnicalCommittee || isHigherCommittee) {
          const statsResponse = await axios.get('/api/dashboard/stats');
          setStats(statsResponse.data);
        }

        // Fetch recent complaints
        const complaintsResponse = await axios.get('/api/complaints?per_page=5');
        setRecentComplaints(complaintsResponse.data.complaints);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [isTechnicalCommittee, isHigherCommittee]);

  const getStatusColor = (status) => {
    const statusColors = {
      'جديدة': 'bg-blue-100 text-blue-800',
      'تحت المعالجة': 'bg-yellow-100 text-yellow-800',
      'قيد المتابعة': 'bg-orange-100 text-orange-800',
      'تم حلها': 'bg-green-100 text-green-800',
      'مكتملة': 'bg-green-100 text-green-800',
      'مرفوضة': 'bg-red-100 text-red-800'
    };
    return statusColors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority) => {
    const priorityColors = {
      'High': 'bg-red-100 text-red-800',
      'Medium': 'bg-yellow-100 text-yellow-800',
      'Low': 'bg-green-100 text-green-800'
    };
    return priorityColors[priority] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ar-SA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">جاري تحميل البيانات...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            مرحباً، {user?.full_name}
          </h1>
          <p className="text-gray-600">
            {isTrader && 'لوحة تحكم التاجر'}
            {isTechnicalCommittee && 'لوحة تحكم اللجنة الفنية'}
            {isHigherCommittee && 'لوحة تحكم اللجنة العليا'}
          </p>
        </div>

        {/* Statistics Cards (for Committee Members) */}
        {(isTechnicalCommittee || isHigherCommittee) && stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100 text-sm font-medium">إجمالي الشكاوى</p>
                    <p className="text-3xl font-bold">{stats.total_complaints}</p>
                  </div>
                  <FileText className="h-12 w-12 text-blue-200" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-100 text-sm font-medium">الشكاوى الحديثة</p>
                    <p className="text-3xl font-bold">{stats.recent_complaints}</p>
                    <p className="text-green-100 text-xs">آخر 30 يوم</p>
                  </div>
                  <TrendingUp className="h-12 w-12 text-green-200" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-yellow-500 to-yellow-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-yellow-100 text-sm font-medium">تحت المعالجة</p>
                    <p className="text-3xl font-bold">
                      {stats.status_distribution.find(s => s.status === 'تحت المعالجة')?.count || 0}
                    </p>
                  </div>
                  <Clock className="h-12 w-12 text-yellow-200" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-purple-100 text-sm font-medium">تم حلها</p>
                    <p className="text-3xl font-bold">
                      {stats.status_distribution.find(s => s.status === 'تم حلها')?.count || 0}
                    </p>
                  </div>
                  <CheckCircle className="h-12 w-12 text-purple-200" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                الشكاوى الحديثة
              </CardTitle>
              <CardDescription>
                آخر الشكاوى المقدمة في النظام
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentComplaints.length > 0 ? (
                  recentComplaints.map((complaint) => (
                    <div key={complaint.complaint_id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900 mb-1">
                          {complaint.title}
                        </h4>
                        <p className="text-sm text-gray-600 mb-2">
                          {complaint.description.substring(0, 100)}...
                        </p>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span>التاجر: {complaint.trader_name}</span>
                          <span>•</span>
                          <span>{formatDate(complaint.submitted_at)}</span>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <Badge className={getStatusColor(complaint.status_name)}>
                          {complaint.status_name}
                        </Badge>
                        <Badge className={getPriorityColor(complaint.priority)}>
                          {complaint.priority}
                        </Badge>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    لا توجد شكاوى حديثة
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                إجراءات سريعة
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {isTrader && (
                <Button className="w-full justify-start" variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  تقديم شكوى جديدة
                </Button>
              )}
              
              <Button className="w-full justify-start" variant="outline">
                <Search className="h-4 w-4 mr-2" />
                البحث في الشكاوى
              </Button>
              
              {(isTechnicalCommittee || isHigherCommittee) && (
                <>
                  <Button className="w-full justify-start" variant="outline">
                    <Filter className="h-4 w-4 mr-2" />
                    فلترة الشكاوى
                  </Button>
                  
                  <Button className="w-full justify-start" variant="outline">
                    <BarChart3 className="h-4 w-4 mr-2" />
                    عرض التقارير
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Status Distribution Chart (for Committee Members) */}
        {(isTechnicalCommittee || isHigherCommittee) && stats && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>توزيع الشكاوى حسب الحالة</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats.status_distribution.map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{item.status}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ 
                              width: `${(item.count / stats.total_complaints) * 100}%` 
                            }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600 w-8">{item.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>توزيع الشكاوى حسب التصنيف</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats.category_distribution.map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{item.category}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full" 
                            style={{ 
                              width: `${(item.count / stats.total_complaints) * 100}%` 
                            }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600 w-8">{item.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
