import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Loader2, Users, Search, Shield, AlertCircle, CheckCircle } from 'lucide-react';

const UserManagement = () => {
  const { user, token } = useAuth();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [selectedUser, setSelectedUser] = useState(null);
  const [newRole, setNewRole] = useState('');
  const [showDialog, setShowDialog] = useState(false);
  const [pagination, setPagination] = useState({ current_page: 1, total: 0, pages: 0 });

  useEffect(() => {
    fetchRoles();
    fetchUsers();
  }, []);

  const fetchRoles = async () => {
    try {
      const response = await axios.get('/api/roles');
      setRoles(response.data.roles);
    } catch (err) {
      console.error('Failed to fetch roles:', err);
    }
  };

  const fetchUsers = async (page = 1, search = searchTerm, role = roleFilter) => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '20'
      });
      if (search) params.append('search', search);
      if (role && role !== 'all') params.append('role', role);

      const response = await axios.get(`/api/admin/users?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data.users);
      setPagination({
        current_page: response.data.current_page,
        total: response.data.total,
        pages: response.data.pages
      });
    } catch (err) {
      setError(err.response?.data?.message || 'فشل في جلب بيانات المستخدمين');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchUsers(1, searchTerm, roleFilter);
  };

  const handleRoleChange = async () => {
    if (!selectedUser || !newRole) return;

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const response = await axios.put(
        `/api/admin/users/${selectedUser.user_id}/role`,
        { role_name: newRole },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess(response.data.message);
      setShowDialog(false);
      fetchUsers(pagination.current_page, searchTerm, roleFilter);
    } catch (err) {
      setError(err.response?.data?.message || 'فشل في تحديث الدور');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (userId) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const response = await axios.put(
        `/api/admin/users/${userId}/toggle-status`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess(response.data.message);
      fetchUsers(pagination.current_page, searchTerm, roleFilter);
    } catch (err) {
      setError(err.response?.data?.message || 'فشل في تغيير حالة الحساب');
    } finally {
      setLoading(false);
    }
  };

  const openRoleDialog = (user) => {
    setSelectedUser(user);
    setNewRole(user.role_name);
    setShowDialog(true);
  };

  const getRoleColor = (roleName) => {
    switch (roleName) {
      case 'Higher Committee':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'Technical Committee':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'Trader':
        return 'bg-green-100 text-green-800 border-green-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getRoleDisplayName = (roleName) => {
    const roleMap = {
      'Trader': 'تاجر',
      'Technical Committee': 'عضو اللجنة الفنية',
      'Higher Committee': 'عضو اللجنة العليا'
    };
    return roleMap[roleName] || roleName;
  };

  if (!user || (user.role_name !== 'Technical Committee' && user.role_name !== 'Higher Committee')) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-100 p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <Shield className="mx-auto h-12 w-12 text-red-600 mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                غير مصرح
              </h2>
              <p className="text-gray-600">
                هذه الصفحة متاحة فقط لأعضاء اللجنة الفنية واللجنة العليا
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <CardTitle className="text-2xl font-bold text-gray-900">
                  إدارة المستخدمين
                </CardTitle>
                <CardDescription className="text-gray-600">
                  إدارة صلاحيات المستخدمين وحالاتهم
                </CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4 border-red-200 bg-red-50">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-red-800">{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="mb-4 border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">{success}</AlertDescription>
              </Alert>
            )}

            <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <Label htmlFor="search" className="text-sm font-medium text-gray-700 mb-2">
                  بحث
                </Label>
                <div className="flex gap-2">
                  <Input
                    id="search"
                    placeholder="بحث باسم المستخدم، البريد، أو الاسم الكامل"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="text-right"
                  />
                  <Button onClick={handleSearch} className="bg-blue-600 hover:bg-blue-700">
                    <Search className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <div>
                <Label htmlFor="roleFilter" className="text-sm font-medium text-gray-700 mb-2">
                  فلترة حسب الدور
                </Label>
                <Select value={roleFilter} onValueChange={(value) => {
                  setRoleFilter(value);
                  fetchUsers(1, searchTerm, value);
                }}>
                  <SelectTrigger className="text-right">
                    <SelectValue placeholder="جميع الأدوار" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">جميع الأدوار</SelectItem>
                    {roles.map((role) => (
                      <SelectItem key={role.role_id} value={role.role_name}>
                        {getRoleDisplayName(role.role_name)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {loading ? (
              <div className="flex justify-center items-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              </div>
            ) : (
              <>
                <div className="rounded-lg border border-gray-200 overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        <TableHead className="text-right font-semibold">اسم المستخدم</TableHead>
                        <TableHead className="text-right font-semibold">الاسم الكامل</TableHead>
                        <TableHead className="text-right font-semibold">البريد الإلكتروني</TableHead>
                        <TableHead className="text-right font-semibold">الدور</TableHead>
                        <TableHead className="text-right font-semibold">الحالة</TableHead>
                        <TableHead className="text-right font-semibold">الإجراءات</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {users.map((u) => (
                        <TableRow key={u.user_id} className="hover:bg-gray-50">
                          <TableCell className="font-medium">{u.username}</TableCell>
                          <TableCell>{u.full_name}</TableCell>
                          <TableCell className="text-sm text-gray-600">{u.email}</TableCell>
                          <TableCell>
                            <Badge className={`${getRoleColor(u.role_name)} border`}>
                              {getRoleDisplayName(u.role_name)}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className={u.is_active ? 'bg-green-100 text-green-800 border-green-300 border' : 'bg-red-100 text-red-800 border-red-300 border'}>
                              {u.is_active ? 'نشط' : 'معطل'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openRoleDialog(u)}
                                disabled={u.user_id === user.user_id}
                                className="text-sm"
                              >
                                تغيير الدور
                              </Button>
                              <Button
                                size="sm"
                                variant={u.is_active ? 'outline' : 'default'}
                                onClick={() => handleToggleStatus(u.user_id)}
                                disabled={u.user_id === user.user_id}
                                className="text-sm"
                              >
                                {u.is_active ? 'تعطيل' : 'تفعيل'}
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {pagination.pages > 1 && (
                  <div className="mt-4 flex justify-center gap-2">
                    <Button
                      variant="outline"
                      onClick={() => fetchUsers(pagination.current_page - 1)}
                      disabled={pagination.current_page === 1}
                    >
                      السابق
                    </Button>
                    <span className="flex items-center px-4 text-sm text-gray-600">
                      صفحة {pagination.current_page} من {pagination.pages}
                    </span>
                    <Button
                      variant="outline"
                      onClick={() => fetchUsers(pagination.current_page + 1)}
                      disabled={pagination.current_page === pagination.pages}
                    >
                      التالي
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>تغيير دور المستخدم</DialogTitle>
            <DialogDescription>
              تغيير دور {selectedUser?.full_name}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="newRole" className="text-sm font-medium text-gray-700 mb-2">
              الدور الجديد
            </Label>
            <Select value={newRole} onValueChange={setNewRole}>
              <SelectTrigger className="text-right">
                <SelectValue placeholder="اختر الدور" />
              </SelectTrigger>
              <SelectContent>
                {roles.map((role) => (
                  <SelectItem key={role.role_id} value={role.role_name}>
                    {getRoleDisplayName(role.role_name)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              إلغاء
            </Button>
            <Button onClick={handleRoleChange} disabled={loading} className="bg-blue-600 hover:bg-blue-700">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'حفظ'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserManagement;
