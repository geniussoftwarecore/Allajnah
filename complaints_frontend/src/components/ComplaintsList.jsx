import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Search, 
  Filter, 
  Eye, 
  Edit, 
  MessageSquare, 
  Paperclip,
  Calendar,
  User,
  Building,
  Clock,
  CheckCircle,
  AlertTriangle,
  FileText,
  Send,
  Download
} from 'lucide-react';
import axios from 'axios';

const ComplaintsList = () => {
  const { user, isTrader, isTechnicalCommittee, isHigherCommittee } = useAuth();
  const [complaints, setComplaints] = useState([]);
  const [categories, setCategories] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isCommentModalOpen, setIsCommentModalOpen] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [filters, setFilters] = useState({
    search: '',
    status_id: 'all',
    category_id: 'all',
    priority: 'all',
    assigned_only: false
  });
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0,
    pages: 0
  });

  useEffect(() => {
    fetchComplaints();
    fetchReferenceData();
  }, [filters, pagination.page]);

  const fetchComplaints = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        per_page: pagination.per_page.toString(),
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, value]) => value !== '' && value !== false && value !== 'all')
        )
      });

      const response = await axios.get(`/api/complaints?${params}`);
      setComplaints(response.data.complaints);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        pages: response.data.pages
      }));
    } catch (error) {
      console.error('Failed to fetch complaints:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReferenceData = async () => {
    try {
      const [categoriesResponse, statusesResponse] = await Promise.all([
        axios.get('/api/categories'),
        axios.get('/api/statuses')
      ]);
      setCategories(categoriesResponse.data.categories);
      setStatuses(statusesResponse.data.statuses);
    } catch (error) {
      console.error('Failed to fetch reference data:', error);
    }
  };

  const fetchComplaintDetails = async (complaintId) => {
    try {
      const response = await axios.get(`/api/complaints/${complaintId}`);
      setSelectedComplaint(response.data.complaint);
      setIsDetailModalOpen(true);
    } catch (error) {
      console.error('Failed to fetch complaint details:', error);
    }
  };

  const handleStatusUpdate = async (complaintId, statusId, resolutionDetails = '') => {
    try {
      await axios.put(`/api/complaints/${complaintId}/status`, {
        status_id: statusId,
        resolution_details: resolutionDetails
      });
      fetchComplaints();
      if (selectedComplaint && selectedComplaint.complaint_id === complaintId) {
        fetchComplaintDetails(complaintId);
      }
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim() || !selectedComplaint) return;

    try {
      await axios.post(`/api/complaints/${selectedComplaint.complaint_id}/comments`, {
        comment_text: newComment
      });
      setNewComment('');
      setIsCommentModalOpen(false);
      fetchComplaintDetails(selectedComplaint.complaint_id);
    } catch (error) {
      console.error('Failed to add comment:', error);
    }
  };

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
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      status_id: 'all',
      category_id: 'all',
      priority: 'all',
      assigned_only: false
    });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            إدارة الشكاوى
          </h1>
          <p className="text-gray-600">
            {isTrader && 'عرض وإدارة شكاواك'}
            {isTechnicalCommittee && 'معالجة ومتابعة الشكاوى'}
            {isHigherCommittee && 'مراقبة جميع الشكاوى واتخاذ القرارات'}
          </p>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              البحث والفلترة
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
              <div className="md:col-span-2">
                <Input
                  placeholder="البحث في العنوان أو الوصف..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  className="text-right"
                />
              </div>
              
              <Select value={filters.status_id} onValueChange={(value) => handleFilterChange('status_id', value)}>
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

              <Select value={filters.category_id} onValueChange={(value) => handleFilterChange('category_id', value)}>
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

              <Select value={filters.priority} onValueChange={(value) => handleFilterChange('priority', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="جميع الأولويات" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">جميع الأولويات</SelectItem>
                  <SelectItem value="High">عالية</SelectItem>
                  <SelectItem value="Medium">متوسطة</SelectItem>
                  <SelectItem value="Low">منخفضة</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              {isTechnicalCommittee && (
                <label className="flex items-center space-x-2 space-x-reverse">
                  <input
                    type="checkbox"
                    checked={filters.assigned_only}
                    onChange={(e) => handleFilterChange('assigned_only', e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700">الشكاوى المعينة لي فقط</span>
                </label>
              )}
              
              <Button variant="outline" onClick={resetFilters}>
                إعادة تعيين الفلاتر
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Complaints List */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>قائمة الشكاوى</CardTitle>
              <div className="text-sm text-gray-500">
                عرض {complaints.length} من أصل {pagination.total} شكوى
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">جاري تحميل الشكاوى...</p>
              </div>
            ) : complaints.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                لا توجد شكاوى تطابق معايير البحث
              </div>
            ) : (
              <div className="space-y-4">
                {complaints.map((complaint) => (
                  <div key={complaint.complaint_id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-gray-900">{complaint.title}</h3>
                          <Badge className={getStatusColor(complaint.status_name)}>
                            {complaint.status_name}
                          </Badge>
                          <Badge className={getPriorityColor(complaint.priority)}>
                            {complaint.priority}
                          </Badge>
                        </div>
                        
                        <p className="text-gray-600 mb-3 line-clamp-2">
                          {complaint.description}
                        </p>
                        
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <div className="flex items-center gap-1">
                            <User className="w-4 h-4" />
                            <span>{complaint.trader_name}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Building className="w-4 h-4" />
                            <span>{complaint.category_name}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            <span>{formatDate(complaint.submitted_at)}</span>
                          </div>
                          {complaint.attachments_count > 0 && (
                            <div className="flex items-center gap-1">
                              <Paperclip className="w-4 h-4" />
                              <span>{complaint.attachments_count} مرفق</span>
                            </div>
                          )}
                          {complaint.comments_count > 0 && (
                            <div className="flex items-center gap-1">
                              <MessageSquare className="w-4 h-4" />
                              <span>{complaint.comments_count} تعليق</span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => fetchComplaintDetails(complaint.complaint_id)}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          عرض
                        </Button>
                        
                        {(isTechnicalCommittee || isHigherCommittee) && (
                          <Select
                            value={complaint.status_id?.toString()}
                            onValueChange={(value) => handleStatusUpdate(complaint.complaint_id, parseInt(value))}
                          >
                            <SelectTrigger className="w-32">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {statuses.map((status) => (
                                <SelectItem key={status.status_id} value={status.status_id.toString()}>
                                  {status.status_name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="flex items-center justify-between mt-6">
                <div className="text-sm text-gray-500">
                  صفحة {pagination.page} من {pagination.pages}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pagination.page === 1}
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                  >
                    السابق
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pagination.page === pagination.pages}
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                  >
                    التالي
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Complaint Details Modal */}
        <Dialog open={isDetailModalOpen} onOpenChange={setIsDetailModalOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto" dir="rtl">
            {selectedComplaint && (
              <>
                <DialogHeader>
                  <DialogTitle className="text-right">{selectedComplaint.title}</DialogTitle>
                  <DialogDescription className="text-right">
                    تفاصيل الشكوى رقم: {selectedComplaint.complaint_id}
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-6">
                  {/* Basic Info */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700">التاجر</label>
                      <p className="text-gray-900">{selectedComplaint.trader_name}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">التصنيف</label>
                      <p className="text-gray-900">{selectedComplaint.category_name}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">الحالة</label>
                      <Badge className={getStatusColor(selectedComplaint.status_name)}>
                        {selectedComplaint.status_name}
                      </Badge>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-700">الأولوية</label>
                      <Badge className={getPriorityColor(selectedComplaint.priority)}>
                        {selectedComplaint.priority}
                      </Badge>
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <label className="text-sm font-medium text-gray-700 block mb-2">وصف الشكوى</label>
                    <p className="text-gray-900 bg-gray-50 p-3 rounded-lg">
                      {selectedComplaint.description}
                    </p>
                  </div>

                  {/* Attachments */}
                  {selectedComplaint.attachments && selectedComplaint.attachments.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-700 block mb-2">المرفقات</label>
                      <div className="space-y-2">
                        {selectedComplaint.attachments.map((attachment) => (
                          <div key={attachment.attachment_id} className="flex items-center justify-between p-2 border rounded">
                            <span className="text-sm">{attachment.file_name}</span>
                            <Button variant="outline" size="sm">
                              <Download className="w-4 h-4 mr-1" />
                              تحميل
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Comments */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <label className="text-sm font-medium text-gray-700">التعليقات</label>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsCommentModalOpen(true)}
                      >
                        <MessageSquare className="w-4 h-4 mr-1" />
                        إضافة تعليق
                      </Button>
                    </div>
                    
                    {selectedComplaint.comments && selectedComplaint.comments.length > 0 ? (
                      <div className="space-y-3 max-h-60 overflow-y-auto">
                        {selectedComplaint.comments.map((comment) => (
                          <div key={comment.comment_id} className="bg-gray-50 p-3 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium text-sm">{comment.author_name}</span>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="text-xs">
                                  {comment.author_role === 'Trader' ? 'تاجر' : 
                                   comment.author_role === 'Technical Committee' ? 'لجنة فنية' : 'لجنة عليا'}
                                </Badge>
                                <span className="text-xs text-gray-500">
                                  {formatDate(comment.created_at)}
                                </span>
                              </div>
                            </div>
                            <p className="text-gray-700 text-sm">{comment.comment_text}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">لا توجد تعليقات</p>
                    )}
                  </div>
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>

        {/* Add Comment Modal */}
        <Dialog open={isCommentModalOpen} onOpenChange={setIsCommentModalOpen}>
          <DialogContent dir="rtl">
            <DialogHeader>
              <DialogTitle className="text-right">إضافة تعليق</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <Textarea
                placeholder="اكتب تعليقك هنا..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                className="min-h-[100px] text-right"
              />
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setIsCommentModalOpen(false)}>
                  إلغاء
                </Button>
                <Button onClick={handleAddComment} disabled={!newComment.trim()}>
                  <Send className="w-4 h-4 mr-1" />
                  إرسال التعليق
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default ComplaintsList;
