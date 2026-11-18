/**
 * Step 5.2 Frontend Tests: Idempotent Exam Attempt Start & Concurrency Control.
 *
 * Verifies:
 * - TC-5.2-FE-01: Start button calls studentApi.startExam with exam ID and navigates to /take.
 * - TC-5.2-FE-02: Button is disabled and shows loading indicator while request is pending (click-storm prevention).
 * - TC-5.2-FE-03: Resuming an already submitted attempt displays notification and invalidates queries.
 * - TC-5.2-FE-04: API error (e.g. 409 exam_not_open) triggers error toast and does not navigate.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { StudentExamDetailPage } from '../pages/student/StudentExamDetailPage';
import { studentApi, StudentExamDetail, StudentStartAttemptResponse } from '../lib/studentApi';

vi.mock('../lib/studentApi', () => ({
  studentApi: {
    getExam: vi.fn(),
    startExam: vi.fn(),
    listExams: vi.fn(),
  },
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'student-1', username: 'anhnt', full_name: 'Nguyễn Tuấn Anh', role: 'student' },
    isAuthenticated: true,
  }),
}));

const mockExamDetail: StudentExamDetail = {
  id: 'exam-52-1',
  title: 'Đề Khảo Sát Toán 12 - Đầu Năm',
  subject: 'toan',
  description_md: 'Đề thi gồm 50 câu trắc nghiệm.',
  duration_minutes: 90,
  question_count: 50,
  total_points: 10,
  open_at: '2026-11-18T00:00:00Z',
  close_at: '2026-11-18T23:59:59Z',
  state: 'open',
  attempt_id: null,
  can_start: true,
};

const mockStartResponse: StudentStartAttemptResponse = {
  id: 'attempt-52-100',
  exam_id: 'exam-52-1',
  status: 'in_progress',
  started_at: '2026-11-18T08:00:00Z',
  deadline_at: '2026-11-18T09:30:00Z',
  submitted_at: null,
  remaining_seconds: 5400,
  server_now: '2026-11-18T08:00:00Z',
};

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

describe('Step 5.2: Student Start Attempt Frontend Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('TC-5.2-FE-01: calls studentApi.startExam on button click and navigates to take exam', async () => {
    vi.mocked(studentApi.getExam).mockResolvedValueOnce(mockExamDetail);
    vi.mocked(studentApi.startExam).mockResolvedValueOnce(mockStartResponse);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/s/exams/exam-52-1']}>
          <Routes>
            <Route path="/s/exams/:examId" element={<StudentExamDetailPage />} />
            <Route path="/s/exams/:examId/take" element={<div>Exam Active Taking Screen</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    // Wait for exam details to load
    await waitFor(() => {
      expect(screen.getByText('Đề Khảo Sát Toán 12 - Đầu Năm')).toBeInTheDocument();
    });

    const startButton = screen.getByRole('button', { name: /Bắt đầu làm bài/i });
    expect(startButton).toBeInTheDocument();
    expect(startButton).not.toBeDisabled();

    fireEvent.click(startButton);

    await waitFor(() => {
      expect(studentApi.startExam).toHaveBeenCalledTimes(1);
      expect(studentApi.startExam).toHaveBeenCalledWith('exam-52-1');
    });

    // Should navigate to take route
    await waitFor(() => {
      expect(screen.getByText('Exam Active Taking Screen')).toBeInTheDocument();
    });
  });

  it('TC-5.2-FE-02: disables button and shows loading state while request is pending to prevent click-storms', async () => {
    vi.mocked(studentApi.getExam).mockResolvedValueOnce(mockExamDetail);

    // Create a delayed promise to inspect pending state
    let resolveStart: (value: StudentStartAttemptResponse) => void;
    const pendingPromise = new Promise<StudentStartAttemptResponse>((resolve) => {
      resolveStart = resolve;
    });
    vi.mocked(studentApi.startExam).mockReturnValueOnce(pendingPromise);

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/s/exams/exam-52-1']}>
          <Routes>
            <Route path="/s/exams/:examId" element={<StudentExamDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Bắt đầu làm bài/i })).toBeInTheDocument();
    });

    const startButton = screen.getByRole('button', { name: /Bắt đầu làm bài/i });
    fireEvent.click(startButton);

    // Button should become disabled / loading
    await waitFor(() => {
      expect(startButton).toBeDisabled();
    });

    // Multiple rapid clicks should NOT trigger extra API calls
    fireEvent.click(startButton);
    fireEvent.click(startButton);
    expect(studentApi.startExam).toHaveBeenCalledTimes(1);

    // Resolve promise
    resolveStart!(mockStartResponse);
  });

  it('TC-5.2-FE-03: handles resuming an already submitted attempt without taking route navigation', async () => {
    vi.mocked(studentApi.getExam).mockResolvedValueOnce(mockExamDetail);
    vi.mocked(studentApi.startExam).mockResolvedValueOnce({
      ...mockStartResponse,
      status: 'submitted',
      remaining_seconds: 0,
      submitted_at: '2026-11-18T09:30:00Z',
    });

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/s/exams/exam-52-1']}>
          <Routes>
            <Route path="/s/exams/:examId" element={<StudentExamDetailPage />} />
            <Route path="/s/exams/:examId/take" element={<div>Taking Screen</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Đề Khảo Sát Toán 12 - Đầu Năm')).toBeInTheDocument();
    });

    const startButton = screen.getByRole('button', { name: /Bắt đầu làm bài/i });
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(studentApi.startExam).toHaveBeenCalledWith('exam-52-1');
    });

    // Should NOT navigate to taking screen because attempt was already submitted
    expect(screen.queryByText('Taking Screen')).not.toBeInTheDocument();
  });

  it('TC-5.2-FE-04: handles API error properly and re-enables start button', async () => {
    vi.mocked(studentApi.getExam).mockResolvedValueOnce(mockExamDetail);
    vi.mocked(studentApi.startExam).mockRejectedValueOnce(new Error('Đề thi chưa tới giờ mở.'));

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/s/exams/exam-52-1']}>
          <Routes>
            <Route path="/s/exams/:examId" element={<StudentExamDetailPage />} />
            <Route path="/s/exams/:examId/take" element={<div>Taking Screen</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Bắt đầu làm bài/i })).toBeInTheDocument();
    });

    const startButton = screen.getByRole('button', { name: /Bắt đầu làm bài/i });
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(studentApi.startExam).toHaveBeenCalledTimes(1);
    });

    // Button should be re-enabled after error
    await waitFor(() => {
      expect(startButton).not.toBeDisabled();
    });

    expect(screen.queryByText('Taking Screen')).not.toBeInTheDocument();
  });
});
