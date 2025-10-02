import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DatePickerWithRange } from '@/components/ui/date-picker';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';
import { 
  FileText, 
  Download, 
  Filter, 
  Calendar,
  TrendingUp,
  Users,
  Clock,
  CheckCircle,
  AlertTriangle,
  BarChart3,
  PieChart as PieChartIcon
} from 'lucide-react';
import axios from 'axios';

const Reports = () => {
  const { user, isTechnicalCommittee, isHigherCommittee } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({ from: null, to: null });
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [categories, setCategories] = useState([]);
  const [statuses, setStatuses] = useState([]);

  // Chart colors
  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316'];

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch dashboard statistics
        const statsResponse = await axios.get('/api/dashboard/stats');
        setStats(statsResponse.data);

        // Fetch categories and statuses
        const [categoriesResponse, statusesResponse] = await Promise.all([
          axios.get('/api/categories'),
          axios.get('/api/statuses')
        ]);
        
        setCategories(categoriesResponse.data.categories);
        setStatuses(statusesResponse.data.statuses);
      } catch (error) {
        console.error('Failed to fetch reports data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const exportReport = (format) => {
    // This would typically generate and download a report
    console.log(`Exporting report in ${format} format`);
    // Implementation would depend on backend API
  };

  const formatChartData = (data, labelKey, valueKey) => {
    return data.map(item => ({
      name: item[labelKey],
      value: item[valueKey],
      count: item[valueKey]
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">جاري تحميل التقارير...</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
          <p className="text-gray-600">فشل في تحميل بيانات التقارير</p>
        </div>
      </div>
    );
  }

  const statusChartData = formatChartData(stats.status_distribution, 'status', 'count');
  const categoryChartData = formatChartData(stats.category_distribution, 'category', 'count');
  const priorityChartData = formatChartData(stats.priority_distribution, 'priority', 'count');

  // Sample time series data (would come from API in real implementation)
  const timeSeriesData = [
    { month: 'يناير', complaints: 45, resolved: 38 },
    { month: 'فبراير', complaints: 52, resolved: 45 },
    { month: 'مارس', complaints: 48, resolved: 42 },
    { month: 'أبريل', complaints: 61, resolved: 55 },
    { month: 'مايو', complaints: 55, resolved: 48 },
    { month: 'يونيو', complaints: 67, resolved: 58 }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                التقارير والإحصائيات
              </h1>
              <p className="text-gray-600">
                تحليل شامل لبيانات الشكاوى والأداء
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button onClick={() => exportReport('pdf')} className="bg-red-600 hover:bg-red-700">
                <Download className="w-4 h-4 mr-2" />
                تصدير PDF
              </Button>
              <Button onClick={() => exportReport('excel')} className="bg-green-600 hover:bg-green-700">
                <Download className="w-4 h-4 mr-2" />
                تصدير Excel
              </Button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              فلاتر التقارير
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  الفترة الزمنية
                </label>
                <Select defaultValue="last_month">
                  <SelectTrigger>
                    <SelectValue placeholder="اختر الفترة" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="last_week">الأسبوع الماضي</SelectItem>
                    <SelectItem value="last_month">الشهر الماضي</SelectItem>
                    <SelectItem value="last_quarter">الربع الماضي</SelectItem>
                    <SelectItem value="last_year">السنة الماضية</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  التصنيف
                </label>
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger>
                    <SelectValue placeholder="جميع التصنيفات" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">جميع التصنيفات</SelectItem>
                    {categories.map((category) => (
                      <SelectItem key={category.category_id} value={category.category_id.toString()}>
                        {category.category_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  الحالة
                </label>
                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                  <SelectTrigger>
                    <SelectValue placeholder="جميع الحالات" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">جميع الحالات</SelectItem>
                    {statuses.map((status) => (
                      <SelectItem key={status.status_id} value={status.status_id.toString()}>
                        {status.status_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-end">
                <Button className="w-full">
                  تطبيق الفلاتر
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm font-medium">إجمالي الشكاوى</p>
                  <p className="text-3xl font-bold">{stats.total_complaints}</p>
                  <p className="text-blue-100 text-xs">+12% من الشهر الماضي</p>
                </div>
                <FileText className="h-12 w-12 text-blue-200" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm font-medium">تم حلها</p>
                  <p className="text-3xl font-bold">
                    {stats.status_distribution.find(s => s.status === 'تم حلها')?.count || 0}
                  </p>
                  <p className="text-green-100 text-xs">معدل الحل: 78%</p>
                </div>
                <CheckCircle className="h-12 w-12 text-green-200" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-yellow-500 to-yellow-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-yellow-100 text-sm font-medium">قيد المعالجة</p>
                  <p className="text-3xl font-bold">
                    {stats.status_distribution.find(s => s.status === 'تحت المعالجة')?.count || 0}
                  </p>
                  <p className="text-yellow-100 text-xs">متوسط الوقت: 5 أيام</p>
                </div>
                <Clock className="h-12 w-12 text-yellow-200" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm font-medium">معدل الرضا</p>
                  <p className="text-3xl font-bold">4.2</p>
                  <p className="text-purple-100 text-xs">من أصل 5 نجوم</p>
                </div>
                <TrendingUp className="h-12 w-12 text-purple-200" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Status Distribution Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChartIcon className="h-5 w-5" />
                توزيع الشكاوى حسب الحالة
              </CardTitle>
              <CardDescription>
                نسبة الشكاوى في كل حالة
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statusChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Category Distribution Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                توزيع الشكاوى حسب التصنيف
              </CardTitle>
              <CardDescription>
                عدد الشكاوى في كل تصنيف
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={categoryChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Time Series Chart */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              اتجاه الشكاوى عبر الزمن
            </CardTitle>
            <CardDescription>
              مقارنة بين الشكاوى المقدمة والمحلولة شهرياً
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="complaints" 
                  stackId="1" 
                  stroke="#3B82F6" 
                  fill="#3B82F6" 
                  name="الشكاوى المقدمة"
                />
                <Area 
                  type="monotone" 
                  dataKey="resolved" 
                  stackId="2" 
                  stroke="#10B981" 
                  fill="#10B981" 
                  name="الشكاوى المحلولة"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Priority Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>توزيع الأولوية</CardTitle>
              <CardDescription>
                توزيع الشكاوى حسب مستوى الأولوية
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={priorityChartData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" />
                  <Tooltip />
                  <Bar dataKey="value" fill="#F59E0B" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Performance Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>مؤشرات الأداء</CardTitle>
              <CardDescription>
                مقاييس الأداء الرئيسية للنظام
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">متوسط وقت الاستجابة</span>
                <Badge variant="outline">2.3 أيام</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">معدل الحل في الوقت المحدد</span>
                <Badge className="bg-green-100 text-green-800">85%</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">معدل رضا العملاء</span>
                <Badge className="bg-blue-100 text-blue-800">4.2/5</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">الشكاوى المتكررة</span>
                <Badge className="bg-yellow-100 text-yellow-800">12%</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">كفاءة اللجنة الفنية</span>
                <Badge className="bg-purple-100 text-purple-800">92%</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Reports;
