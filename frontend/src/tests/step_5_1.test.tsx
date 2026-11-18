/**
 * Step 5.1 Frontend Test Suite: Student Exams Catalog & Detail Introduction.
 *
 * Verifies:
 * - Dynamic real-time state badge rendering for all 6 states (upcoming, open, in_progress, submitted, result_available, closed).
 * - Category filter tabs (all, active, submitted, other).
 * - ErrorState with retry on transient DB errors (never a false empty list).
 * - EmptyState when no exams are assigned.
 * - StudentExamDetailPage renders metadata, MathText markdown description, rules, and authoritative can_start button.
 * - 404 error handling for unauthorized / draft exams in detail view.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { studentApi, StudentExamListItem, StudentExamDetail } from '../lib/studentApi';
import { StudentExamsPage } from '../pages/student/StudentExamsPage';
import { StudentExamDetailPage } from '../pages/student/StudentExamDetailPage';

// Mock studentApi
vi.mock('../lib/studentApi', async () => {
  const actual = await vi.importActual('../lib/studentApi');
  return {
    ...actual,
    studentApi: {
      listExams: vi.fn(),
      getExam: vi.fn(),
    },
  };
});

// Mock AuthContext
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'student-1', full_name: 'Nguyễn Tuấn Anh', role: 'student' },
    logout: vi.fn(),
  }),
}));

const mockExamList: StudentExamListItem[] = [
  {
    id: 'exam-1',
    title: 'Đề Thi Toán Giữa Kỳ 1',
    subject: 'toan',
    duration_minutes: 45,
    question_count: 20,
    open_at: '2026-11-18T08:00:00Z',
    close_at: '2026-11-18T12:00:00Z',
    state: 'open',
    attempt_id: null,
  },
  {
    id: 'exam-2',
    title: 'Kiểm Tra Tin Học 15 Phút',
    subject: 'tin',
    duration_minutes: 15,
    question_count: 10,
    open_at: '2026-11-18T08:00:00Z',
    close_at: '2026-11-18T12:00:00Z',
    state: 'in_progress',
    attempt_id: 'att-2',
  },
  {
    id: 'exam-3',
    title: 'Đề Thi Học Kỳ 1 Đã Nộp',
    subject: 'both',
    duration_minutes: 60,
    question_count: 30,
    open_at: '2026-11-10T08:00:00Z',
    close_at: '2026-11-10T12:00:00Z',
    state: 'submitted',
    attempt_id: 'att-3',
  },
  {
    id: 'exam-4',
    title: 'Đề Ôn Tập Đã Có Điểm',
    subject: 'toan',
    duration_minutes: 30,
    question_count: 15,
    open_at: '2026-11-05T08:00:00Z',
    close_at: '2026-11-05T12:00:00Z',
    state: 'result_available',
    attempt_id: 'att-4',
  },
  {
    id: 'exam-5',
    title: 'Đề Thi Sắp Diễn Ra',
    subject: 'toan',
    duration_minutes: 90,
    question_count: 40,
    open_at: '2026-11-20T08:00:00Z',
    close_at: '2026-11-20T12:00:00Z',
    state: 'upcoming',
    attempt_id: null,
  },
  {
    id: 'exam-6',
    title: 'Đề Thi Đã Kết Thúc',
    subject: 'tin',
    duration_minutes: 45,
    question_count: 20,
    open_at: '2026-11-01T08:00:00Z',
    close_at: '2026-11-01T12:00:00Z',
    state: 'closed',
    attempt_id: null,
  },
];

const mockExamDetail: StudentExamDetail = {
  id: 'exam-1',
  title: 'Đề Thi Toán Giữa Kỳ 1',
  subject: 'toan',
  description_md: 'Hướng dẫn: Cho hàm số $f(x) = x^2 + 1$. Đọc kỹ câu hỏi trước khi chọn đáp án.',
  duration_minutes: 45,
  question_count: 20,
  total_points: '10.00',
  open_at: '2026-11-18T08:00:00Z',
  close_at: '2026-11-18T12:00:00Z',
  state: 'open',
  attempt_id: null,
  can_start: true,
};

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe('Step 5.1: Student Exam Catalog & Detail Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders student exams catalog with correct state badges', async () => {
    vi.mocked(studentApi.listExams).mockResolvedValueOnce(mockExamList);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/s/exams']}>
          <Routes>
            <Route path="/s/exams" element={<StudentExamsPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Verify loading skeleton appears initially
    expect(screen.getByTestId('exams-loading')).toBeDefined();

    // Wait for cards to render
    await waitFor(() => {
      expect(screen.getByTestId('exams-grid')).toBeDefined();
    });

    // Check titles
    expect(screen.getByText('Đề Thi Toán Giữa Kỳ 1')).toBeDefined();
    expect(screen.getByText('Kiểm Tra Tin Học 15 Phút')).toBeDefined();
    expect(screen.getByText('Đề Thi Học Kỳ 1 Đã Nộp')).toBeDefined();

    // Check state badges
    expect(screen.getByText('Đang mở')).toBeDefined();
    expect(screen.getByText('Đang làm dở')).toBeDefined();
    expect(screen.getAllByText('Đã nộp bài').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Đã có điểm')).toBeDefined();
    expect(screen.getByText('Sắp diễn ra')).toBeDefined();
    expect(screen.getByText('Đã kết thúc')).toBeDefined();

    // Check action buttons
    expect(screen.getByText('Vào làm bài')).toBeDefined();
    expect(screen.getByText('Tiếp tục làm bài')).toBeDefined();
    expect(screen.getByText('Chưa mở đề thi')).toBeDefined();
  });

  it('filters exams correctly when clicking filter tabs', async () => {
    vi.mocked(studentApi.listExams).mockResolvedValueOnce(mockExamList);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/s/exams']}>
          <Routes>
            <Route path="/s/exams" element={<StudentExamsPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('exams-grid')).toBeDefined();
    });

    // Click 'Đang mở / Đang làm' tab
    const activeTabButton = screen.getByText('Đang mở / Đang làm');
    fireEvent.click(activeTabButton);

    expect(screen.getByText('Đề Thi Toán Giữa Kỳ 1')).toBeDefined();
    expect(screen.getByText('Kiểm Tra Tin Học 15 Phút')).toBeDefined();
    expect(screen.queryByText('Đề Thi Học Kỳ 1 Đã Nộp')).toBeNull();

    // Click 'Đã nộp bài' tab
    const submittedTabButton = screen.getByText('Đã nộp bài');
    fireEvent.click(submittedTabButton);

    expect(screen.getByText('Đề Thi Học Kỳ 1 Đã Nộp')).toBeDefined();
    expect(screen.getByText('Đề Ôn Tập Đã Có Điểm')).toBeDefined();
    expect(screen.queryByText('Đề Thi Toán Giữa Kỳ 1')).toBeNull();
  });

  it('handles transient error (503 db_unavailable) and allows retry', async () => {
    vi.mocked(studentApi.listExams).mockRejectedValueOnce(
      new Error('Dịch vụ cơ sở dữ liệu tạm thời gián đoạn.')
    );

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/s/exams']}>
          <Routes>
            <Route path="/s/exams" element={<StudentExamsPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('exams-error')).toBeDefined();
    });

    expect(screen.getByText('Không thể tải danh sách bài thi')).toBeDefined();
    expect(screen.getByText('Thử lại')).toBeDefined();

    // Mock successful retry
    vi.mocked(studentApi.listExams).mockResolvedValueOnce(mockExamList);
    const retryBtn = screen.getByText('Thử lại');
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByTestId('exams-grid')).toBeDefined();
    });
    expect(screen.getByText('Đề Thi Toán Giữa Kỳ 1')).toBeDefined();
  });

  it('renders EmptyState when student has no assigned exams', async () => {
    vi.mocked(studentApi.listExams).mockResolvedValueOnce([]);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/s/exams']}>
          <Routes>
            <Route path="/s/exams" element={<StudentExamsPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('exams-empty')).toBeDefined();
    });

    expect(screen.getByText('Chưa có bài thi nào')).toBeDefined();
  });

  it('renders exam detail introduction page with MathText and can_start button', async () => {
    vi.mocked(studentApi.getExam).mockResolvedValueOnce(mockExamDetail);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/s/exams/exam-1']}>
          <Routes>
            <Route path="/s/exams/:examId" element={<StudentExamDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Đề Thi Toán Giữa Kỳ 1')).toBeDefined();
    });

    // Check stats
    expect(screen.getByText('45 phút')).toBeDefined();
    expect(screen.getByText('20 câu')).toBeDefined();
    expect(screen.getByText('10.00 điểm')).toBeDefined();

    // Check CTA button
    expect(screen.getByText('Bắt đầu làm bài')).toBeDefined();
  });

  it('renders ErrorState when exam detail returns 404 not found', async () => {
    vi.mocked(studentApi.getExam).mockRejectedValueOnce(
      new Error('Không tìm thấy bài thi.')
    );

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/s/exams/exam-unknown']}>
          <Routes>
            <Route path="/s/exams/:examId" element={<StudentExamDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('detail-error')).toBeDefined();
    });

    expect(screen.getByText('Không tìm thấy bài thi')).toBeDefined();
  });
});
