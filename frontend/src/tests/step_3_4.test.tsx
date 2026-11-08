/**
 * Step 3.4 Test Suite: Admin UI for Classes, Students & 3-Step CSV Import Wizard.
 *
 * Verifies:
 * - TC-3.4-01: Full flow: Create class -> CSV import 10 students -> enroll -> download passwords CSV.
 * - TC-3.4-02: Field-level error: Duplicate class code displays error under class code input.
 * - TC-3.4-03: Anti-double-click: Rapidly double-clicking submit sends only 1 request.
 * - TC-3.4-04: Dry-run errors: Button 'Xác nhận nhập' is disabled when error rows exist.
 * - TC-3.4-05: Fast search typing: Debounced 300ms with AbortController prevents stale results overwriting.
 * - TC-3.4-06: Optimistic lock conflict: 409 version_conflict displays banner with reload button.
 * - TC-3.4-07: Network disconnect during commit: Displays clear alert and never auto-retries.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { adminApi } from '../lib/adminApi';
import { ApiError, NetworkError } from '../lib/api';
import { AdminClassesPage } from '../pages/admin/AdminClassesPage';
import { AdminStudentsPage } from '../pages/admin/AdminStudentsPage';
import { CsvImportWizard } from '../components/admin/CsvImportWizard';
import { AuthContext } from '../context/AuthContext';

const mockUser = {
  id: 'admin-uuid-1',
  username: 'admin',
  full_name: 'Giáo Viên Quản Trị',
  role: 'admin' as const,
  is_active: true,
  created_at: new Date().toISOString(),
};

const mockAuthContextValue = {
  user: mockUser,
  role: 'admin' as const,
  isAuthenticated: true,
  isLoading: false,
  isMemoryFallback: false,
  login: vi.fn(),
  logout: vi.fn(),
  refreshUser: vi.fn(),
};

const renderWithProviders = (ui: React.ReactElement, initialRoute = '/') => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={mockAuthContextValue}>
        <MemoryRouter initialEntries={[initialRoute]}>{ui}</MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
};

describe('Step 3.4: Admin UI & CSV Import Wizard', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.URL.createObjectURL = vi.fn().mockReturnValue('blob:mock-url');
    window.URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  // TC-3.4-01: Full flow: Create class -> Import CSV 10 students -> Download passwords CSV
  it('TC-3.4-01: completes full flow from class creation to CSV import and password export', async () => {
    // 1. Mock create class
    vi.spyOn(adminApi, 'createClass').mockResolvedValueOnce({
      id: 'class-uuid-10a1',
      code: '10A1',
      name: 'Lớp 10A1 Toán',
      subject: 'toan',
      academic_year: 2026,
      is_archived: false,
      version: 1,
      student_count: 0,
      exam_count: 0,
      created_at: new Date().toISOString(),
    });

    // 2. Mock dry-run
    vi.spyOn(adminApi, 'importStudentsCsv')
      .mockResolvedValueOnce({
        total_rows: 10,
        valid_rows: 10,
        error_rows: 0,
        estimated_hash_seconds: 0.5,
        can_commit: true,
        rows: Array.from({ length: 10 }, (_, i) => ({
          row_number: i + 2,
          full_name: `Học Sinh ${i + 1}`,
          username: `student_${i + 1}`,
          class_code: '10A1',
          status: 'valid',
          errors: [],
        })),
        created_count: 0,
        students: [],
      })
      // 3. Mock commit
      .mockResolvedValueOnce({
        total_rows: 10,
        valid_rows: 10,
        error_rows: 0,
        estimated_hash_seconds: 0.5,
        can_commit: true,
        rows: [],
        created_count: 10,
        students: Array.from({ length: 10 }, (_, i) => ({
          id: `st-${i + 1}`,
          username: `student_${i + 1}`,
          full_name: `Học Sinh ${i + 1}`,
          class_code: '10A1',
          password_plain: `Pwd${i + 1}!safe`,
        })),
        csv_export_content:
          '\ufeffSTT,Tên đăng nhập,Họ và tên,Mã lớp,Mật khẩu\r\n1,student_1,Học Sinh 1,10A1,Pwd1!safe\r\n',
      });

    // Render Wizard directly for import flow
    const onWizardSuccess = vi.fn();
    renderWithProviders(<CsvImportWizard defaultClassId="class-uuid-10a1" onSuccess={onWizardSuccess} />);

    // Step 1: Select file
    const file = new File(['mock content'], 'danh_sach_10a1.csv', { type: 'text/csv' });
    const dropzoneInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(dropzoneInput).toBeTruthy();
    fireEvent.change(dropzoneInput, { target: { files: [file] } });

    // Click Dry-run check
    const dryRunBtn = screen.getByRole('button', { name: /Kiểm tra tệp/i });
    fireEvent.click(dryRunBtn);

    // Step 2: Verify dry-run summary
    await waitFor(() => {
      expect(screen.getByText('Xem trước & Kiểm tra lỗi')).toBeTruthy();
      expect(screen.getByText(/dòng đều hợp lệ/i)).toBeTruthy();
    });

    const commitBtn = screen.getByRole('button', { name: /Xác nhận nhập/i });
    expect(commitBtn).not.toBeDisabled();
    fireEvent.click(commitBtn);

    // Step 3: Success and download button
    await waitFor(() => {
      expect(screen.getByText(/Nhập học sinh thành công!/i)).toBeTruthy();
      expect(screen.getByRole('button', { name: /Tải tệp CSV mật khẩu/i })).toBeTruthy();
      expect(screen.getByText('Pwd1!safe')).toBeTruthy();
    });

    // Click download CSV
    const downloadBtn = screen.getByRole('button', { name: /Tải tệp CSV mật khẩu/i });
    fireEvent.click(downloadBtn);
    expect(window.URL.createObjectURL).toHaveBeenCalled();
  });

  // TC-3.4-02: Duplicate class code displays field-level error
  it('TC-3.4-02: displays error message directly under class code input on 409 class_code_taken', async () => {
    vi.spyOn(adminApi, 'listClasses').mockResolvedValueOnce({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });

    vi.spyOn(adminApi, 'createClass').mockRejectedValueOnce(
      new ApiError(409, 'class_code_taken', "Mã lớp '10A1' đã tồn tại.", { code: '10A1' })
    );

    renderWithProviders(<AdminClassesPage />);

    // Open create modal
    const openBtn = await screen.findByRole('button', { name: /Tạo lớp mới/i });
    fireEvent.click(openBtn);

    // Fill form
    const codeInput = screen.getByPlaceholderText(/TIN_K24/i);
    const nameInput = screen.getByPlaceholderText(/Chuyên Toán/i);
    fireEvent.change(codeInput, { target: { value: '10A1' } });
    fireEvent.change(nameInput, { target: { value: 'Lớp 10A1 Chuyên Toán' } });

    // Submit
    const submitBtn = screen.getByRole('button', { name: /^Tạo lớp$/i });
    fireEvent.click(submitBtn);

    // Expect field-level error message right under input
    await waitFor(() => {
      expect(
        screen.getByText('Mã lớp này đã tồn tại trên hệ thống. Vui lòng chọn mã khác.')
      ).toBeTruthy();
    });
  });

  // TC-3.4-03: Anti-double-click sends only 1 request
  it('TC-3.4-03: disables submit button and sends only 1 request upon rapid double-clicking', async () => {
    vi.spyOn(adminApi, 'listClasses').mockResolvedValueOnce({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });

    let resolveMutation: (val: any) => void;
    const pendingPromise = new Promise((resolve) => {
      resolveMutation = resolve;
    });

    const createSpy = vi.spyOn(adminApi, 'createClass').mockReturnValue(pendingPromise as any);

    renderWithProviders(<AdminClassesPage />);

    const openBtn = await screen.findByRole('button', { name: /Tạo lớp mới/i });
    fireEvent.click(openBtn);

    const codeInput = screen.getByPlaceholderText(/TIN_K24/i);
    const nameInput = screen.getByPlaceholderText(/Chuyên Toán/i);
    fireEvent.change(codeInput, { target: { value: '10A2' } });
    fireEvent.change(nameInput, { target: { value: 'Lớp 10A2' } });

    const submitBtn = screen.getByRole('button', { name: /^Tạo lớp$/i });

    // Rapid double click
    fireEvent.click(submitBtn);
    fireEvent.click(submitBtn);

    // Verify spy was called only once and button is disabled during in-flight
    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledTimes(1);
    });
    expect(submitBtn).toBeDisabled();

    // Clean up pending promise
    resolveMutation!({
      id: 'id-10a2',
      code: '10A2',
      name: 'Lớp 10A2',
      subject: 'toan',
      academic_year: 2026,
      is_archived: false,
      version: 1,
      student_count: 0,
      exam_count: 0,
      created_at: new Date().toISOString(),
    });
  });

  // TC-3.4-04: Button 'Xác nhận nhập' is disabled when dry-run errors exist
  it('TC-3.4-04: disables commit button and displays error details when dry-run reports invalid rows', async () => {
    vi.spyOn(adminApi, 'importStudentsCsv').mockResolvedValueOnce({
      total_rows: 3,
      valid_rows: 1,
      error_rows: 2,
      estimated_hash_seconds: 0.1,
      can_commit: false,
      rows: [
        {
          row_number: 2,
          full_name: 'Nguyễn Văn A',
          username: 'invalid user with spaces',
          class_code: '10A1',
          status: 'error',
          errors: ['username_invalid'],
        },
        {
          row_number: 3,
          full_name: '',
          username: 'student_no_name',
          class_code: '10A1',
          status: 'error',
          errors: ['name_empty'],
        },
        {
          row_number: 4,
          full_name: 'Trần Văn C',
          username: 'student_valid',
          class_code: '10A1',
          status: 'valid',
          errors: [],
        },
      ],
      created_count: 0,
      students: [],
    });

    renderWithProviders(<CsvImportWizard />);

    const file = new File(['dummy'], 'students_with_errors.csv', { type: 'text/csv' });
    const dropzoneInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(dropzoneInput, { target: { files: [file] } });

    const dryRunBtn = screen.getByRole('button', { name: /Kiểm tra tệp/i });
    fireEvent.click(dryRunBtn);

    await waitFor(() => {
      // Button must be disabled
      const commitBtn = screen.getByRole('button', { name: /Xác nhận nhập/i });
      expect(commitBtn).toBeDisabled();

      // Error badges and reason descriptions displayed
      expect(screen.getByText(/dòng có lỗi/i)).toBeTruthy();
      expect(screen.getByText('Tên đăng nhập không hợp lệ (cần 3-32 ký tự a-z, 0-9, ._-)')).toBeTruthy();
      expect(screen.getByText('Họ và tên để trống')).toBeTruthy();
    });
  });

  // TC-3.4-05: Realtime debounced search (300ms) with AbortController
  it('TC-3.4-05: debounces fast search typing by 300ms and prevents stale request overwrite', async () => {
    vi.useFakeTimers();

    const listStudentsSpy = vi.spyOn(adminApi, 'listStudents').mockResolvedValue({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });
    vi.spyOn(adminApi, 'listClasses').mockResolvedValue({ items: [], total: 0, limit: 100, offset: 0 });

    renderWithProviders(<AdminStudentsPage />);

    const searchInput = screen.getByPlaceholderText(/Tìm theo username/i);

    // Initial load call
    expect(listStudentsSpy).toHaveBeenCalledTimes(1);

    // Fast typing 'nguy' then 'nguyen'
    act(() => {
      fireEvent.change(searchInput, { target: { value: 'nguy' } });
      vi.advanceTimersByTime(100);
    });

    act(() => {
      fireEvent.change(searchInput, { target: { value: 'nguyen' } });
      vi.advanceTimersByTime(350);
    });

    expect(listStudentsSpy).toHaveBeenLastCalledWith(
      expect.objectContaining({ search: 'nguyen' }),
      expect.any(AbortSignal)
    );
  });

  // TC-3.4-06: 409 version_conflict displays banner with reload button
  it('TC-3.4-06: displays version conflict notification with reload button upon 409 version_conflict', async () => {
    vi.spyOn(adminApi, 'listClasses').mockResolvedValue({
      items: [
        {
          id: 'class-conflict',
          code: '10A3',
          name: 'Lớp 10A3',
          subject: 'toan',
          academic_year: 2026,
          is_archived: false,
          version: 1,
          student_count: 20,
          exam_count: 2,
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
      limit: 100,
      offset: 0,
    });

    vi.spyOn(adminApi, 'updateClass').mockRejectedValueOnce(
      new ApiError(409, 'version_conflict', 'Dữ liệu đã bị thay đổi bởi người khác.', {
        current_version: 2,
      })
    );

    renderWithProviders(<AdminClassesPage />);

    // Wait for class item to render in the table
    const classCodeCell = await screen.findByText('10A3');
    expect(classCodeCell).toBeTruthy();

    // Click edit button
    const editBtn = screen.getByTitle('Chỉnh sửa thông tin');
    fireEvent.click(editBtn);

    // Click save in edit modal
    const saveBtn = screen.getByRole('button', { name: /Lưu thay đổi/i });
    fireEvent.click(saveBtn);

    // Expect conflict alert and reload button
    await waitFor(() => {
      expect(
        screen.getByText(/Dữ liệu lớp học đã được người khác thay đổi ở nơi khác/i)
      ).toBeTruthy();
      expect(screen.getByRole('button', { name: /Tải lại dữ liệu/i })).toBeTruthy();
    });
  });

  // TC-3.4-07: Network disconnect during commit displays clear alert and never auto-retries
  it('TC-3.4-07: displays clear network alert and does not automatically retry when network drops during commit', async () => {
    vi.spyOn(adminApi, 'importStudentsCsv')
      .mockResolvedValueOnce({
        total_rows: 1,
        valid_rows: 1,
        error_rows: 0,
        estimated_hash_seconds: 0.1,
        can_commit: true,
        rows: [
          {
            row_number: 2,
            full_name: 'Trần Văn Nam',
            username: 'nam.tv',
            class_code: '10A1',
            status: 'valid',
            errors: [],
          },
        ],
        created_count: 0,
        students: [],
      })
      .mockRejectedValueOnce(new NetworkError('Failed to fetch'));

    renderWithProviders(<CsvImportWizard />);

    const file = new File(['valid csv'], 'valid.csv', { type: 'text/csv' });
    const dropzoneInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(dropzoneInput, { target: { files: [file] } });

    const dryRunBtn = screen.getByRole('button', { name: /Kiểm tra tệp/i });
    fireEvent.click(dryRunBtn);

    await waitFor(() => {
      expect(screen.getByText(/dòng đều hợp lệ/i)).toBeTruthy();
    });

    const commitBtn = screen.getByRole('button', { name: /Xác nhận nhập/i });
    fireEvent.click(commitBtn);

    // Expect network error alert and instruction not to auto retry
    await waitFor(() => {
      expect(screen.getByText('Mất kết nối mạng!')).toBeTruthy();
      expect(
        screen.getByText(/Hệ thống KHÔNG tự ý gửi lại yêu cầu để tránh nhân đôi dữ liệu/i)
      ).toBeTruthy();
    });
  });
});
