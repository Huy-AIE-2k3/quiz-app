import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { adminApi, ClassItem, CreateClassPayload, UpdateClassPayload } from '../../lib/adminApi';
import { ApiError } from '../../lib/api';
import { AdminLayout } from '../../components/admin/AdminLayout';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Badge } from '../../components/ui/Badge';
import { Table } from '../../components/ui/Table';
import { Modal } from '../../components/ui/Modal';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { Card } from '../../components/ui/Card';
import { Plus, Search, Eye, Trash2, Edit2, RefreshCw, AlertCircle } from 'lucide-react';

export const AdminClassesPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingClass, setEditingClass] = useState<ClassItem | null>(null);
  const [deletingClass, setDeletingClass] = useState<ClassItem | null>(null);
  const [versionConflictAlert, setVersionConflictAlert] = useState(false);

  // Form states for creating class
  const [newCode, setNewCode] = useState('');
  const [newName, setNewName] = useState('');
  const [newSubject, setNewSubject] = useState<'toan' | 'tin' | 'both'>('toan');
  const [newYear, setNewYear] = useState(new Date().getFullYear());
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Query classes
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['admin', 'classes', search],
    queryFn: () => adminApi.listClasses({ search: search.trim() || undefined, limit: 100 }),
    staleTime: 30_000,
  });

  // Create Mutation
  const createMutation = useMutation({
    mutationFn: (payload: CreateClassPayload) => adminApi.createClass(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'classes'] });
      setIsCreateOpen(false);
      resetCreateForm();
    },
    onError: (err: unknown) => {
      const apiErr = err as { code?: string; status?: number; details?: unknown };
      if (apiErr?.code === 'class_code_taken' || apiErr?.status === 409) {
        // TC-3.4-02: Display error right under the class code input
        setFieldErrors({ code: 'Mã lớp này đã tồn tại trên hệ thống. Vui lòng chọn mã khác.' });
        return;
      }
      if (apiErr?.details && typeof apiErr.details === 'object') {
        const detailErrors: Record<string, string> = {};
        Object.entries(apiErr.details as Record<string, string>).forEach(([k, v]) => {
          detailErrors[k] = String(v);
        });
        setFieldErrors(detailErrors);
        return;
      }
      setFieldErrors({ form: 'Có lỗi xảy ra khi tạo lớp. Vui lòng thử lại.' });
    },
  });

  // Update Mutation (Optimistic Lock)
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateClassPayload }) =>
      adminApi.updateClass(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'classes'] });
      setEditingClass(null);
      setVersionConflictAlert(false);
    },
    onError: (err: unknown) => {
      const apiErr = err as { code?: string; status?: number };
      if (apiErr?.code === 'version_conflict' || apiErr?.status === 409) {
        // TC-3.4-06: Display version conflict message with reload action
        setVersionConflictAlert(true);
      }
    },
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteClass(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'classes'] });
      setDeletingClass(null);
    },
    onError: (err: unknown) => {
      if (err instanceof ApiError && err.code === 'class_in_use') {
        alert('Lớp học này đã có đề thi, không thể xóa vĩnh viễn. Bạn có thể chọn Lưu trữ để ẩn lớp.');
      } else {
        alert('Không thể xóa lớp. Vui lòng thử lại.');
      }
      setDeletingClass(null);
    },
  });

  const resetCreateForm = () => {
    setNewCode('');
    setNewName('');
    setNewSubject('toan');
    setNewYear(new Date().getFullYear());
    setFieldErrors({});
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFieldErrors({});

    const normalizedCode = newCode.trim().toUpperCase();
    if (!normalizedCode) {
      setFieldErrors({ code: 'Mã lớp không được để trống.' });
      return;
    }
    if (!newName.trim()) {
      setFieldErrors({ name: 'Tên lớp không được để trống.' });
      return;
    }

    try {
      await createMutation.mutateAsync({
        code: normalizedCode,
        name: newName.trim(),
        subject: newSubject,
        academic_year: Number(newYear),
      });
    } catch {
      // Handled in onError of createMutation
    }
  };

  const classes = data?.items || [];

  return (
    <AdminLayout
      title="Quản lý Lớp học"
      action={
        <Button
          variant="primary"
          size="sm"
          onClick={() => {
            resetCreateForm();
            setIsCreateOpen(true);
          }}
          className="flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" />
          <span>Tạo lớp mới</span>
        </Button>
      }
    >
      {/* Version Conflict Alert (TC-3.4-06) */}
      {versionConflictAlert && (
        <div className="mb-6 p-4 rounded-lg bg-status-wrong-bg border border-status-wrong-border text-status-wrong-text flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span className="text-xs sm:text-sm font-medium">
              Dữ liệu lớp học đã được người khác thay đổi ở nơi khác. Vui lòng tải lại dữ liệu để lấy phiên bản mới nhất!
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              refetch();
              setVersionConflictAlert(false);
              setEditingClass(null);
            }}
            className="flex items-center gap-1.5 shrink-0"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Tải lại dữ liệu</span>
          </Button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-6">
        <div className="relative max-w-sm w-full">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo mã lớp hoặc tên lớp..."
            className="pl-9 text-xs"
          />
        </div>
      </div>

      {/* Classes Table */}
      <Card className="overflow-hidden border border-line-subtle">
        {isLoading ? (
          <div className="p-8 text-center text-xs text-text-muted">Đang tải danh sách lớp học...</div>
        ) : classes.length === 0 ? (
          <div className="p-8 text-center text-xs text-text-muted">
            Không tìm thấy lớp học nào phù hợp.
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <th>Mã lớp</th>
                <th>Tên lớp</th>
                <th>Môn học</th>
                <th>Năm học</th>
                <th>Học sinh</th>
                <th>Đề thi</th>
                <th>Trạng thái</th>
                <th className="text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {classes.map((cls) => (
                <tr key={cls.id} className={cls.is_archived ? 'opacity-60 bg-surface-raised/40' : undefined}>
                  <td className="font-mono text-xs font-bold text-brand">{cls.code}</td>
                  <td className="font-medium text-xs text-text-primary">{cls.name}</td>
                  <td>
                    <Badge variant={cls.subject === 'both' ? 'brand' : 'neutral'} size="sm">
                      {cls.subject === 'toan' ? 'Toán' : cls.subject === 'tin' ? 'Tin' : 'Toán + Tin'}
                    </Badge>
                  </td>
                  <td className="font-mono text-xs">{cls.academic_year}</td>
                  <td className="font-mono text-xs">{cls.student_count} HS</td>
                  <td className="font-mono text-xs">{cls.exam_count} đề</td>
                  <td>
                    {cls.is_archived ? (
                      <Badge variant="danger" size="sm">
                        Đã lưu trữ
                      </Badge>
                    ) : (
                      <Badge variant="brand" size="sm">
                        Hoạt động
                      </Badge>
                    )}
                  </td>
                  <td className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/a/classes/${cls.id}`)}
                        className="text-text-secondary hover:text-brand p-1.5"
                        title="Xem chi tiết & Ghi danh"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setEditingClass(cls)}
                        className="text-text-secondary hover:text-text-primary p-1.5"
                        title="Chỉnh sửa thông tin"
                      >
                        <Edit2 className="w-4 h-4" />
                      </Button>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeletingClass(cls)}
                        className="text-text-secondary hover:text-status-wrong-text p-1.5"
                        title="Xóa lớp học"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      {/* Modal: Create Class */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Tạo Lớp Học Mới"
        size="md"
        footer={
          <div className="flex items-center justify-end gap-2 w-full">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsCreateOpen(false)}
              disabled={createMutation.isPending}
            >
              Hủy
            </Button>
            {/* TC-3.4-03: Anti-double-click via isPending disabled */}
            <Button
              variant="primary"
              size="sm"
              onClick={handleCreateSubmit}
              disabled={createMutation.isPending}
              loading={createMutation.isPending}
            >
              Tạo lớp
            </Button>
          </div>
        }
      >
        <form onSubmit={handleCreateSubmit} className="flex flex-col gap-4 py-2">
          {fieldErrors.form && (
            <div className="p-3 rounded-md bg-status-wrong-bg border border-status-wrong-border text-status-wrong-text text-xs">
              {fieldErrors.form}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-text-primary mb-1">
              Mã lớp <span className="text-status-wrong-text">*</span>
            </label>
            <Input
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              placeholder="Ví dụ: 10A1, TIN_K24"
              className="font-mono uppercase text-xs"
              error={fieldErrors.code}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-primary mb-1">
              Tên lớp <span className="text-status-wrong-text">*</span>
            </label>
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Ví dụ: Lớp 10A1 Chuyên Toán"
              className="text-xs"
              error={fieldErrors.name}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Select
                label="Môn học"
                value={newSubject}
                onChange={(e) => setNewSubject(e.target.value as 'toan' | 'tin' | 'both')}
                options={[
                  { value: 'toan', label: 'Toán học' },
                  { value: 'tin', label: 'Tin học' },
                  { value: 'both', label: 'Cả Toán & Tin' },
                ]}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-primary mb-1">Năm học</label>
              <Input
                type="number"
                value={newYear}
                onChange={(e) => setNewYear(Number(e.target.value))}
                min={2020}
                max={2050}
                className="font-mono text-xs"
              />
            </div>
          </div>
        </form>
      </Modal>

      {/* Modal: Edit Class */}
      {editingClass && (
        <Modal
          isOpen={!!editingClass}
          onClose={() => setEditingClass(null)}
          title={`Chỉnh sửa lớp: ${editingClass.code}`}
          size="md"
          footer={
            <div className="flex items-center justify-end gap-2 w-full">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditingClass(null)}
                disabled={updateMutation.isPending}
              >
                Hủy
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  updateMutation.mutate({
                    id: editingClass.id,
                    payload: {
                      name: editingClass.name,
                      subject: editingClass.subject,
                      academic_year: editingClass.academic_year,
                      is_archived: editingClass.is_archived,
                      version: editingClass.version,
                    },
                  });
                }}
                disabled={updateMutation.isPending}
                loading={updateMutation.isPending}
              >
                Lưu thay đổi
              </Button>
            </div>
          }
        >
          <div className="flex flex-col gap-4 py-2">
            <div>
              <label className="block text-xs font-semibold text-text-primary mb-1">Mã lớp</label>
              <Input value={editingClass.code} disabled className="font-mono uppercase text-xs opacity-60" />
            </div>

            <div>
              <label className="block text-xs font-semibold text-text-primary mb-1">Tên lớp</label>
              <Input
                value={editingClass.name}
                onChange={(e) => setEditingClass({ ...editingClass, name: e.target.value })}
                className="text-xs"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Select
                  label="Môn học"
                  value={editingClass.subject}
                  onChange={(e) =>
                    setEditingClass({
                      ...editingClass,
                      subject: e.target.value as 'toan' | 'tin' | 'both',
                    })
                  }
                  options={[
                    { value: 'toan', label: 'Toán học' },
                    { value: 'tin', label: 'Tin học' },
                    { value: 'both', label: 'Cả Toán & Tin' },
                  ]}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-primary mb-1">Năm học</label>
                <Input
                  type="number"
                  value={editingClass.academic_year}
                  onChange={(e) =>
                    setEditingClass({ ...editingClass, academic_year: Number(e.target.value) })
                  }
                  className="font-mono text-xs"
                />
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Delete Confirmation Dialog */}
      {deletingClass && (
        <ConfirmDialog
          isOpen={!!deletingClass}
          onClose={() => setDeletingClass(null)}
          onConfirm={() => deleteMutation.mutate(deletingClass.id)}
          title={`Xác nhận xóa lớp: ${deletingClass.code}`}
          description={`Bạn có chắc chắn muốn xóa lớp "${deletingClass.name}"? Thao tác này không thể hoàn tác nếu lớp chưa có bài thi.`}
          confirmText="Xóa lớp"
          variant="danger"
          loading={deleteMutation.isPending}
        />
      )}
    </AdminLayout>
  );
};
