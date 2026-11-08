import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi, StudentItem, CreateStudentPayload } from '../../lib/adminApi';
import { AdminLayout } from '../../components/admin/AdminLayout';
import { CsvImportWizard } from '../../components/admin/CsvImportWizard';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Table } from '../../components/ui/Table';
import { Modal } from '../../components/ui/Modal';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import {
  UserPlus,
  Upload,
  Search,
  KeyRound,
  Lock,
  Unlock,
  AlertTriangle,
} from 'lucide-react';

export const AdminStudentsPage: React.FC = () => {
  const queryClient = useQueryClient();

  const [searchInput, setSearchInput] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedClassId, setSelectedClassId] = useState<string>('');
  const [selectedActiveStatus, setSelectedActiveStatus] = useState<string>('all');

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [resettingStudent, setResettingStudent] = useState<StudentItem | null>(null);
  const [togglingStudent, setTogglingStudent] = useState<StudentItem | null>(null);
  const [generatedPasswordModal, setGeneratedPasswordModal] = useState<{
    username: string;
    pwd: string;
  } | null>(null);

  // Form states for creating student
  const [newUsername, setNewUsername] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [createError, setCreateError] = useState<string | null>(null);

  // AbortController reference for TC-3.4-05
  const abortControllerRef = useRef<AbortController | null>(null);

  // TC-3.4-05: Debounce search input by 300ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Query classes for filter dropdown
  const { data: classesData } = useQuery({
    queryKey: ['admin', 'classes', 'dropdown'],
    queryFn: () => adminApi.listClasses({ limit: 100 }),
    staleTime: 60_000,
  });

  // Query students with AbortController for race-condition prevention
  const { data: studentsData, isLoading: isStudentsLoading } = useQuery({
    queryKey: ['admin', 'students', debouncedSearch, selectedClassId, selectedActiveStatus],
    queryFn: ({ signal }) => {
      // Abort previous in-flight request if exists
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      const combinedSignal = signal || abortControllerRef.current.signal;
      const isActiveParam =
        selectedActiveStatus === 'active' ? true : selectedActiveStatus === 'inactive' ? false : undefined;

      return adminApi.listStudents(
        {
          search: debouncedSearch.trim() || undefined,
          class_id: selectedClassId || undefined,
          is_active: isActiveParam,
          limit: 100,
        },
        combinedSignal
      );
    },
    staleTime: 30_000,
  });

  // Create Student Mutation
  const createMutation = useMutation({
    mutationFn: (payload: CreateStudentPayload) => adminApi.createStudent(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'students'] });
      setIsCreateOpen(false);
      setNewUsername('');
      setNewFullName('');
      setNewPassword('');
      setCreateError(null);
      if (data.generated_password) {
        setGeneratedPasswordModal({ username: data.username, pwd: data.generated_password });
      }
    },
    onError: (err: unknown) => {
      if (typeof err === 'object' && err !== null && 'message' in err) {
        setCreateError((err as { message: string }).message);
      } else {
        setCreateError('Lỗi tạo tài khoản học sinh.');
      }
    },
  });

  // Reset Password Mutation
  const resetPasswordMutation = useMutation({
    mutationFn: (studentId: string) => adminApi.resetStudentPassword(studentId),
    onSuccess: (data) => {
      setResettingStudent(null);
      if (data.generated_password) {
        setGeneratedPasswordModal({
          username: resettingStudent?.username || '',
          pwd: data.generated_password,
        });
      }
    },
    onError: () => {
      alert('Không thể đặt lại mật khẩu. Vui lòng thử lại.');
      setResettingStudent(null);
    },
  });

  // Toggle Active Status Mutation
  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      adminApi.updateStudent(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'students'] });
      setTogglingStudent(null);
    },
    onError: () => {
      alert('Không thể thay đổi trạng thái tài khoản. Vui lòng thử lại.');
      setTogglingStudent(null);
    },
  });

  const students = studentsData?.items || [];
  const classes = classesData?.items || [];

  return (
    <AdminLayout
      title="Quản lý Học sinh"
      action={
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsCsvModalOpen(true)}
            className="flex items-center gap-1.5"
          >
            <Upload className="w-4 h-4 text-brand" />
            <span>Nhập tệp CSV</span>
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsCreateOpen(true)}
            className="flex items-center gap-1.5"
          >
            <UserPlus className="w-4 h-4" />
            <span>Thêm học sinh</span>
          </Button>
        </div>
      }
    >
      {/* Filters & Search Toolbar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 mb-6">
        <div className="flex flex-col sm:flex-row items-center gap-3 flex-1">
          {/* TC-3.4-05: Realtime debounced search */}
          <div className="relative w-full sm:max-w-xs">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Tìm theo username hoặc họ tên..."
              className="pl-9 text-xs"
            />
          </div>

          <div className="w-full sm:max-w-xs">
            <Select
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              options={[
                { value: '', label: 'Tất cả các lớp' },
                ...classes.map((c) => ({
                  value: c.id,
                  label: `${c.code} — ${c.name}`,
                })),
              ]}
            />
          </div>

          <div className="w-full sm:w-44">
            <Select
              value={selectedActiveStatus}
              onChange={(e) => setSelectedActiveStatus(e.target.value)}
              options={[
                { value: 'all', label: 'Mọi trạng thái' },
                { value: 'active', label: 'Đang hoạt động' },
                { value: 'inactive', label: 'Đã bị khóa' },
              ]}
            />
          </div>
        </div>
      </div>

      {/* Students Table */}
      <Card className="overflow-hidden border border-line-subtle">
        {isStudentsLoading ? (
          <div className="p-8 text-center text-xs text-text-muted">Đang tải danh sách học sinh...</div>
        ) : students.length === 0 ? (
          <div className="p-8 text-center text-xs text-text-muted">
            Không tìm thấy học sinh nào phù hợp với bộ lọc.
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <th>Tên đăng nhập</th>
                <th>Họ và tên</th>
                <th>Lớp đang học</th>
                <th>Trạng thái</th>
                <th>Ngày tạo</th>
                <th className="text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {students.map((st) => (
                <tr key={st.id} className={!st.is_active ? 'opacity-60 bg-surface-raised/40' : undefined}>
                  <td className="font-mono text-xs font-bold text-text-primary">{st.username}</td>
                  <td className="text-xs font-medium">{st.full_name}</td>
                  <td className="text-xs">
                    {st.classes.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {st.classes.map((c) => (
                          <Badge key={c.id} variant="neutral" size="sm">
                            {c.code}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <span className="text-text-muted">—</span>
                    )}
                  </td>
                  <td>
                    {st.is_active ? (
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
                    {new Date(st.created_at).toLocaleDateString('vi-VN')}
                  </td>
                  <td className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setResettingStudent(st)}
                        className="text-text-secondary hover:text-brand p-1.5"
                        title="Đặt lại mật khẩu"
                      >
                        <KeyRound className="w-4 h-4" />
                      </Button>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setTogglingStudent(st)}
                        className={`p-1.5 ${
                          st.is_active
                            ? 'text-text-secondary hover:text-status-wrong-text'
                            : 'text-status-correct-text hover:text-text-primary'
                        }`}
                        title={st.is_active ? 'Khóa tài khoản' : 'Mở khóa tài khoản'}
                      >
                        {st.is_active ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      {/* Modal: Create Single Student */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Thêm Học Sinh Mới"
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
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                if (!newUsername.trim() || !newFullName.trim()) {
                  setCreateError('Vui lòng điền đủ Tên đăng nhập và Họ tên.');
                  return;
                }
                createMutation.mutate({
                  username: newUsername.trim().toLowerCase(),
                  full_name: newFullName.trim(),
                  password: newPassword.trim() || undefined,
                });
              }}
              disabled={createMutation.isPending}
              loading={createMutation.isPending}
            >
              Tạo tài khoản
            </Button>
          </div>
        }
      >
        <div className="flex flex-col gap-4 py-2">
          {createError && (
            <div className="p-3 rounded-md bg-status-wrong-bg border border-status-wrong-border text-status-wrong-text text-xs">
              {createError}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-text-primary mb-1">
              Tên đăng nhập <span className="text-status-wrong-text">*</span>
            </label>
            <Input
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              placeholder="Ví dụ: nam.td, nguyen_van_a"
              className="font-mono text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-primary mb-1">
              Họ và tên <span className="text-status-wrong-text">*</span>
            </label>
            <Input
              value={newFullName}
              onChange={(e) => setNewFullName(e.target.value)}
              placeholder="Ví dụ: Trần Đức Nam"
              className="text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-primary mb-1">
              Mật khẩu (Tùy chọn)
            </label>
            <Input
              type="text"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Để trống nếu muốn hệ thống tự sinh ngẫu nhiên an toàn"
              className="font-mono text-xs"
            />
            <span className="text-xs text-text-muted mt-1 block">
              Nếu để trống, hệ thống sẽ tự sinh mật khẩu 8 ký tự an toàn và hiển thị 1 lần sau khi tạo.
            </span>
          </div>
        </div>
      </Modal>

      {/* Modal: Batch CSV Import */}
      <Modal
        isOpen={isCsvModalOpen}
        onClose={() => setIsCsvModalOpen(false)}
        title="Nhập Học Sinh Hàng Loạt Bằng CSV"
        size="lg"
      >
        <CsvImportWizard
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['admin', 'students'] });
            setIsCsvModalOpen(false);
          }}
          onCancel={() => setIsCsvModalOpen(false)}
        />
      </Modal>

      {/* Modal: Display Generated Password Once */}
      {generatedPasswordModal && (
        <Modal
          isOpen={!!generatedPasswordModal}
          onClose={() => setGeneratedPasswordModal(null)}
          title="Mật Khẩu Khởi Tạo"
          size="sm"
          footer={
            <Button variant="primary" size="sm" onClick={() => setGeneratedPasswordModal(null)}>
              Đã lưu mật khẩu
            </Button>
          }
        >
          <div className="flex flex-col gap-3 py-2 text-xs">
            <div className="p-3 rounded-lg bg-surface border border-brand/30 flex items-center justify-between">
              <div>
                <span className="text-text-muted block">Tài khoản:</span>
                <span className="font-mono font-bold text-text-primary">
                  {generatedPasswordModal.username}
                </span>
              </div>
              <div className="text-right">
                <span className="text-text-muted block">Mật khẩu mới:</span>
                <span className="font-mono font-bold text-base text-brand">
                  {generatedPasswordModal.pwd}
                </span>
              </div>
            </div>

            <div className="p-2.5 rounded-md bg-status-wrong-bg/30 text-status-wrong-text flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>Mật khẩu chỉ hiển thị 1 lần duy nhất này. Vui lòng ghi lại ngay!</span>
            </div>
          </div>
        </Modal>
      )}

      {/* ConfirmDialog: Reset Password */}
      {resettingStudent && (
        <ConfirmDialog
          isOpen={!!resettingStudent}
          onClose={() => setResettingStudent(null)}
          onConfirm={() => resetPasswordMutation.mutate(resettingStudent.id)}
          title={`Đặt lại mật khẩu: ${resettingStudent.username}`}
          description={`Bạn có chắc muốn đặt lại mật khẩu cho học sinh "${resettingStudent.full_name}"? Mật khẩu mới sẽ được sinh ngẫu nhiên và toàn bộ phiên đăng nhập hiện có sẽ bị hủy.`}
          confirmText="Đặt lại mật khẩu"
          variant="brand"
          loading={resetPasswordMutation.isPending}
        />
      )}

      {/* ConfirmDialog: Lock / Unlock Student Account */}
      {togglingStudent && (
        <ConfirmDialog
          isOpen={!!togglingStudent}
          onClose={() => setTogglingStudent(null)}
          onConfirm={() =>
            toggleActiveMutation.mutate({
              id: togglingStudent.id,
              is_active: !togglingStudent.is_active,
            })
          }
          title={
            togglingStudent.is_active
              ? `Khóa tài khoản: ${togglingStudent.username}`
              : `Mở khóa tài khoản: ${togglingStudent.username}`
          }
          description={
            togglingStudent.is_active
              ? `Khóa tài khoản của "${togglingStudent.full_name}" sẽ lập tức đá phiên đăng nhập và không cho phép học sinh này tham gia thi hay nộp bài.`
              : `Mở khóa tài khoản sẽ cho phép học sinh "${togglingStudent.full_name}" đăng nhập và làm bài bình thường.`
          }
          confirmText={togglingStudent.is_active ? 'Khóa tài khoản' : 'Mở khóa'}
          variant={togglingStudent.is_active ? 'danger' : 'brand'}
          loading={toggleActiveMutation.isPending}
        />
      )}
    </AdminLayout>
  );
};
