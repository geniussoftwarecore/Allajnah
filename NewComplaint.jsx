import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  FileText, 
  Upload, 
  X, 
  AlertCircle, 
  CheckCircle, 
  Loader2,
  Paperclip,
  Send
} from 'lucide-react';
import axios from 'axios';

const NewComplaint = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category_id: '',
    priority: 'Medium'
  });
  const [categories, setCategories] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/api/categories');
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const handleCategoryChange = (value) => {
    setFormData(prev => ({
      ...prev,
      category_id: value
    }));
    setError('');
  };

  const handlePriorityChange = (value) => {
    setFormData(prev => ({
      ...prev,
      priority: value
    }));
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif',
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];

    const validFiles = files.filter(file => {
      if (file.size > maxSize) {
        setError(`الملف ${file.name} كبير جداً. الحد الأقصى 10 ميجابايت.`);
        return false;
      }
      if (!allowedTypes.includes(file.type)) {
        setError(`نوع الملف ${file.name} غير مدعوم.`);
        return false;
      }
      return true;
    });

    if (validFiles.length > 0) {
      setAttachments(prev => [...prev, ...validFiles]);
      setError('');
    }
  };

  const removeAttachment = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const validateForm = () => {
    if (!formData.title.trim()) {
      setError('عنوان الشكوى مطلوب');
      return false;
    }
    if (!formData.description.trim()) {
      setError('وصف الشكوى مطلوب');
      return false;
    }
    if (!formData.category_id) {
      setError('تصنيف الشكوى مطلوب');
      return false;
    }
    if (formData.title.length < 10) {
      setError('عنوان الشكوى يجب أن يكون 10 أحرف على الأقل');
      return false;
    }
    if (formData.description.length < 20) {
      setError('وصف الشكوى يجب أن يكون 20 حرف على الأقل');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Submit complaint
      const complaintResponse = await axios.post('/api/complaints', formData);
      const complaintId = complaintResponse.data.complaint.complaint_id;

      // Upload attachments if any
      if (attachments.length > 0) {
        const formDataWithFiles = new FormData();
        attachments.forEach((file, index) => {
          formDataWithFiles.append(`file_${index}`, file);
        });
        formDataWithFiles.append('complaint_id', complaintId);

        // Note: This would require a file upload endpoint
        // await axios.post('/api/complaints/attachments', formDataWithFiles, {
        //   headers: { 'Content-Type': 'multipart/form-data' }
        // });
      }

      setSuccess('تم تقديم الشكوى بنجاح! سيتم مراجعتها من قبل اللجنة الفنية.');
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        category_id: '',
        priority: 'Medium'
      });
      setAttachments([]);

      // Redirect after 3 seconds
      setTimeout(() => {
        navigate('/complaints');
      }, 3000);

    } catch (error) {
      console.error('Failed to submit complaint:', error);
      setError(error.response?.data?.message || 'فشل في تقديم الشكوى. يرجى المحاولة مرة أخرى.');
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileType) => {
    if (fileType.startsWith('image/')) return '🖼️';
    if (fileType === 'application/pdf') return '📄';
    if (fileType.includes('word')) return '📝';
    return '📎';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            تقديم شكوى جديدة
          </h1>
          <p className="text-gray-600">
            املأ النموذج أدناه لتقديم شكواك. سيتم مراجعتها من قبل اللجنة الفنية المختصة.
          </p>
        </div>

        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-6 w-6" />
              نموذج الشكوى
            </CardTitle>
            <CardDescription>
              يرجى تقديم معلومات مفصلة ودقيقة لضمان معالجة سريعة وفعالة لشكواك
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Alerts */}
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert className="border-green-200 bg-green-50">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-800">
                    {success}
                  </AlertDescription>
                </Alert>
              )}

              {/* User Info Display */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">معلومات مقدم الشكوى</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-blue-700 font-medium">الاسم: </span>
                    <span className="text-blue-900">{user?.full_name}</span>
                  </div>
                  <div>
                    <span className="text-blue-700 font-medium">البريد الإلكتروني: </span>
                    <span className="text-blue-900">{user?.email}</span>
                  </div>
                  {user?.phone_number && (
                    <div>
                      <span className="text-blue-700 font-medium">رقم الهاتف: </span>
                      <span className="text-blue-900">{user.phone_number}</span>
                    </div>
                  )}
                  {user?.address && (
                    <div>
                      <span className="text-blue-700 font-medium">العنوان: </span>
                      <span className="text-blue-900">{user.address}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Complaint Title */}
              <div className="space-y-2">
                <Label htmlFor="title" className="text-sm font-medium text-gray-700">
                  عنوان الشكوى *
                </Label>
                <Input
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="اكتب عنواناً واضحاً ومختصراً للشكوى"
                  className="text-right"
                  disabled={loading}
                  maxLength={255}
                />
                <p className="text-xs text-gray-500">
                  {formData.title.length}/255 حرف
                </p>
              </div>

              {/* Category and Priority */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="category" className="text-sm font-medium text-gray-700">
                    تصنيف الشكوى *
                  </Label>
                  <Select value={formData.category_id} onValueChange={handleCategoryChange} disabled={loading}>
                    <SelectTrigger>
                      <SelectValue placeholder="اختر تصنيف الشكوى" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((category) => (
                        <SelectItem key={category.category_id} value={category.category_id.toString()}>
                          <div className="text-right">
                            <div className="font-medium">{category.category_name}</div>
                            {category.description && (
                              <div className="text-xs text-gray-500">{category.description}</div>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="priority" className="text-sm font-medium text-gray-700">
                    مستوى الأولوية
                  </Label>
                  <Select value={formData.priority} onValueChange={handlePriorityChange} disabled={loading}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Low">منخفضة</SelectItem>
                      <SelectItem value="Medium">متوسطة</SelectItem>
                      <SelectItem value="High">عالية</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label htmlFor="description" className="text-sm font-medium text-gray-700">
                  وصف تفصيلي للشكوى *
                </Label>
                <Textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="اشرح المشكلة بالتفصيل، متى حدثت، والخطوات التي اتخذتها لحلها..."
                  className="min-h-[150px] text-right"
                  disabled={loading}
                  maxLength={2000}
                />
                <p className="text-xs text-gray-500">
                  {formData.description.length}/2000 حرف
                </p>
              </div>

              {/* File Attachments */}
              <div className="space-y-4">
                <Label className="text-sm font-medium text-gray-700">
                  المرفقات (اختياري)
                </Label>
                
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                  <input
                    type="file"
                    multiple
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                    accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt"
                    disabled={loading}
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-600 mb-1">
                      اضغط لاختيار الملفات أو اسحبها هنا
                    </p>
                    <p className="text-xs text-gray-500">
                      الأنواع المدعومة: JPG, PNG, PDF, DOC, DOCX, TXT (حد أقصى 10 ميجابايت لكل ملف)
                    </p>
                  </label>
                </div>

                {/* Attached Files */}
                {attachments.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-700">الملفات المرفقة:</h4>
                    {attachments.map((file, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <span className="text-lg">{getFileIcon(file.type)}</span>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{file.name}</p>
                            <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                          </div>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeAttachment(index)}
                          disabled={loading}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <div className="flex justify-end pt-6">
                <Button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      جاري تقديم الشكوى...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      تقديم الشكوى
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Help Section */}
        <Card className="mt-6 bg-yellow-50 border-yellow-200">
          <CardContent className="p-4">
            <h3 className="font-medium text-yellow-800 mb-2">نصائح لتقديم شكوى فعالة:</h3>
            <ul className="text-sm text-yellow-700 space-y-1">
              <li>• كن واضحاً ومحدداً في وصف المشكلة</li>
              <li>• أرفق أي مستندات أو صور تدعم شكواك</li>
              <li>• اذكر التواريخ والأوقات المهمة</li>
              <li>• اشرح الخطوات التي اتخذتها لحل المشكلة</li>
              <li>• حدد النتيجة المرجوة من الشكوى</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default NewComplaint;
