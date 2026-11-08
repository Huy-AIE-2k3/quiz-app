import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi, StudentItem } from '../../lib/adminApi';
import { AdminLayout } from '../../components/admin/AdminLayout';
import { CsvImportWizard } from '../../components/admin/CsvImportWizard';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Table } from '../../components/ui/Table';
import { Checkbox } from '../../components/ui/Checkbox';
import { Input } from '../../components/ui/Input';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { ArrowLeft, Users, UserPlus, Upload, Trash2, Search } from 'lucide-react';

export const AdminClassDetailPage: React.FC = () => {
  const { classId } = useParams<{ classId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'members' | 'enroll' | 'csv'>('members');
  const [enrollSearch, setEnrollSearch] = useState('');
  const [selectedStudentIds, setSelectedStudentIds] = useState<Set<string>>(new Set());
  const [withdrawingStudent, setWithdrawingStudent] = useState<StudentItem | null>(null);

  // 1. Fetch Class Detail
  const { data: currentClass, isLoading: isClassLoading } = useQuery({
    queryKey: ['admin', 'classes', classId],
    queryFn: () => adminApi.getClass(classId!),
    enabled: !!classId,
  });

  // 2. Fetch Enrolled Students in this class
  const { data: membersData, isLoading: isMembersLoading } = useQuery({
    queryKey: ['admin', 'students', 'class', classId],
    queryFn: () => adminApi.listStudents({ class_id: classId, limit: 200 }),
    enabled: !!classId,
  });

  // 3. Fetch All Students for Enrollment Selection
  const { data: allStudentsData, isLoading: isAllStudentsLoading } = useQuery({
    queryKey: ['admin', 'students', 'enrollment_pool', enrollSearch],
    queryFn: () => adminApi.listStudents({ search: enrollSearch.trim() || undefined, limit: 200 }),
    enabled: activeTab === 'enroll',
  });

  // Sync selectedStudentIds with current members when switching to enroll tab
  const handleTabChange = (tab: 'members' | 'enroll' | 'csv') => {
    setActiveTab(tab);
    if (tab === 'enroll' && membersData) {
      setSelectedStudentIds(new Set(membersData.items.map((s) => s.id)));
    }
  };

  // Mutation: Set-based enrollment
  const enrollmentMutation = useMutation({
    mutationFn: (userIds: string[]) => adminApi.updateClassMembers(classId!, userIds),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'students', 'class', classId] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'classes', classId] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'classes'] });
      alert(`Cập nhật thành công: Đã thêm ${data.added} và rút ${data.removed} học sinh.`);
      setActiveTab('members');
    },
    onError: () => {
      alert('Không thể cập nhật danh sách ghi danh. Vui lòng thử lại.');
    },
  });

  // Handle withdrawing single student
  const handleWithdrawSingle = (student: StudentItem) => {
    if (!membersData) return;
    const remainingIds = membersData.items.filter((s) => s.id !== student.id).map((s) => s.id);
    enrollmentMutation.mutate(remainingIds);
    setWithdrawingStudent(null);
  };

  const members = membersData?.items || [];
  const allStudents = allStudentsData?.items || [];

  if (isClassLoading) {
    return (
      <AdminLayout>
        <div className="p-12 text-center text-xs text-text-muted">Đang tải thông tin lớp học...</div>
      </AdminLayout>
    );
  }

  if (!currentClass) {
    return (
      <AdminLayout>
        <div className="p-12 text-center text-xs text-status-wrong-text">
          Không tìm thấy thông tin lớp học.
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      {/* Back button and Class Header */}
      <div className="flex flex-col gap-4 mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/a/classes')}
          className="self-start flex items-center gap-1.5 text-text-secondary hover:text-text-primary"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Quay lại danh sách lớp</span>
        </Button>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-lg bg-surface border border-line-subtle">
          <div className="flex items-center gap-4">
            <span className="text-2xl font-bold font-mono text-brand px-3 py-1.5 rounded-md bg-brand/10 border border-brand/20">
              {currentClass.code}
            </span>
            <div>
              <h1 className="text-lg font-bold font-display text-text-primary">{currentClass.name}</h1>
              <div className="flex items-center gap-3 text-xs text-text-muted mt-1">
                <span>Năm học: {currentClass.academic_year}</span>
                <span>•</span>
                <span>
                  Môn học:{' '}
                  {currentClass.subject === 'toan'
                    ? 'Toán'
                    : currentClass.subject === 'tin'
                      ? 'Tin'
                      : 'Cả Toán & Tin'}
                </span>
                <span>•</span>
                <span className="font-mono text-brand font-semibold">{members.length} học sinh</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {currentClass.is_archived && (
              <Badge variant="danger" size="md">
                Đã lưu trữ
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-line-subtle mb-6 gap-2">
        <button
          onClick={() => handleTabChange('members')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === 'members'
              ? 'border-brand text-brand'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Danh sách học sinh ({members.length})</span>
        </button>

        <button
          onClick={() => handleTabChange('enroll')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === 'enroll'
              ? 'border-brand text-brand'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <UserPlus className="w-4 h-4" />
          <span>Ghi danh theo tập hợp</span>
        </button>

        <button
          onClick={() => handleTabChange('csv')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === 'csv'
              ? 'border-brand text-brand'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          <Upload className="w-4 h-4" />
          <span>Nhập CSV vào lớp</span>
        </button>
      </div>

      {/* ================= TAB 1: MEMBERS LIST ================= */}
      {activeTab === 'members' && (
        <Card className="overflow-hidden border border-line-subtle">
          {isMembersLoading ? (
            <div className="p-8 text-center text-xs text-text-muted">Đang tải danh sách học sinh...</div>
          ) : members.length === 0 ? (
            <div className="p-12 text-center flex flex-col items-center gap-3">
              <Users className="w-8 h-8 text-text-muted" />
              <span className="text-xs text-text-muted">Lớp học này chưa có học sinh nào.</span>
              <div className="flex items-center gap-2 mt-2">
                <Button variant="primary" size="sm" onClick={() => handleTabChange('enroll')}>
                  Ghi danh học sinh
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleTabChange('csv')}>
                  Nhập tệp CSV
                </Button>
              </div>
            </div>
          ) : (
            <Table>
              <thead>
                <tr>
                  <th>Tên đăng nhập</th>
                  <th>Họ và tên</th>
                  <th>Trạng thái</th>
                  <th>Ngày tạo</th>
                  <th className="text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {members.map((s) => (
                  <tr key={s.id}>
                    <td className="font-mono text-xs font-semibold text-text-primary">{s.username}</td>
                    <td className="text-xs font-medium">{s.full_name}</td>
                    <td>
                      {s.is_active ? (
                        <Badge variant="brand" size="sm">
                          Hoạt động
                        </Badge>
                      ) : (
                        <Badge variant="danger" size="sm">
                          Đã khóa
                        </Badge>
                      )}
                    </td>
                    <td className="font-mono text-xs text-text-muted">
                      {new Date(s.created_at).toLocaleDateString('vi-VN')}
                    </td>
                    <td className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setWithdrawingStudent(s)}
                        className="text-text-secondary hover:text-status-wrong-text p-1.5"
                        title="Rút học sinh khỏi lớp"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      )}

      {/* ================= TAB 2: SET-BASED ENROLLMENT ================= */}
      {activeTab === 'enroll' && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg bg-surface border border-line-subtle">
            <div className="relative max-w-sm w-full">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
              <Input
                value={enrollSearch}
                onChange={(e) => setEnrollSearch(e.target.value)}
                placeholder="Tìm học sinh để ghi danh..."
                className="pl-9 text-xs"
              />
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-text-secondary">
                Đã chọn: <strong className="font-mono text-brand">{selectedStudentIds.size}</strong> học sinh
              </span>
              <Button
                variant="primary"
                size="sm"
                onClick={() => enrollmentMutation.mutate(Array.from(selectedStudentIds))}
                disabled={enrollmentMutation.isPending}
                loading={enrollmentMutation.isPending}
              >
                Lưu danh sách ghi danh
              </Button>
            </div>
          </div>

          <Card className="overflow-hidden border border-line-subtle">
            {isAllStudentsLoading ? (
              <div className="p-8 text-center text-xs text-text-muted">Đang tải danh sách học sinh...</div>
            ) : allStudents.length === 0 ? (
              <div className="p-8 text-center text-xs text-text-muted">
                Không tìm thấy học sinh nào.
              </div>
            ) : (
              <Table>
                <thead>
                  <tr>
                    <th className="w-12 text-center">
                      <Checkbox
                        id="select-all-students"
                        checked={
                          allStudents.length > 0 &&
                          allStudents.every((s) => selectedStudentIds.has(s.id))
                        }
                        onChange={(e) => {
                          const next = new Set(selectedStudentIds);
                          if (e.target.checked) {
                            allStudents.forEach((s) => next.add(s.id));
                          } else {
                            allStudents.forEach((s) => next.delete(s.id));
                          }
                          setSelectedStudentIds(next);
                        }}
                      />
                    </th>
                    <th>Tên đăng nhập</th>
                    <th>Họ và tên</th>
                    <th>Lớp đang tham gia</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {allStudents.map((s) => {
                    const isSelected = selectedStudentIds.has(s.id);
                    return (
                      <tr
                        key={s.id}
                        className={isSelected ? 'bg-brand/5' : undefined}
                        onClick={() => {
                          const next = new Set(selectedStudentIds);
                          if (isSelected) next.delete(s.id);
                          else next.add(s.id);
                          setSelectedStudentIds(next);
                        }}
                      >
                        <td className="text-center" onClick={(e) => e.stopPropagation()}>
                          <Checkbox
                            id={`student-check-${s.id}`}
                            checked={isSelected}
                            onChange={(e) => {
                              const next = new Set(selectedStudentIds);
                              if (e.target.checked) next.add(s.id);
                              else next.delete(s.id);
                              setSelectedStudentIds(next);
                            }}
                          />
                        </td>
                        <td className="font-mono text-xs font-semibold text-text-primary">
                          {s.username}
                        </td>
                        <td className="text-xs font-medium">{s.full_name}</td>
                        <td className="text-xs text-text-secondary">
                          {s.classes.map((c) => c.code).join(', ') || '—'}
                        </td>
                        <td>
                          {isSelected ? (
                            <Badge variant="brand" size="sm">
                              ĐÃ CHỌN
                            </Badge>
                          ) : (
                            <Badge variant="neutral" size="sm">
                              CHƯA CHỌN
                            </Badge>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
            )}
          </Card>
        </div>
      )}

      {/* ================= TAB 3: CSV IMPORT WIZARD ================= */}
      {activeTab === 'csv' && (
        <Card className="p-6 border border-line-subtle">
          <CsvImportWizard
            defaultClassId={classId}
            onSuccess={() => {
              queryClient.invalidateQueries({ queryKey: ['admin', 'students', 'class', classId] });
              queryClient.invalidateQueries({ queryKey: ['admin', 'classes', classId] });
              setActiveTab('members');
            }}
          />
        </Card>
      )}

      {/* Confirmation Dialog: Withdraw Student */}
      {withdrawingStudent && (
        <ConfirmDialog
          isOpen={!!withdrawingStudent}
          onClose={() => setWithdrawingStudent(null)}
          onConfirm={() => handleWithdrawSingle(withdrawingStudent)}
          title={`Rút học sinh khỏi lớp: ${withdrawingStudent.username}`}
          description={`Bạn có chắc muốn rút "${withdrawingStudent.full_name}" khỏi lớp ${currentClass.code}? Lưu ý: Học sinh vẫn bảo lưu bài làm thi dở dang (nếu có).`}
          confirmText="Rút khỏi lớp"
          variant="danger"
          loading={enrollmentMutation.isPending}
        />
      )}
    </AdminLayout>
  );
};
