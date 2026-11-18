/**
 * Step 5.4 Frontend Tests: Auto-saving Answers & Client-seq Serialization.
 *
 * Verifies:
 * - TC-5.4-FE-01: Selecting MCQ option increments client_seq and calls studentApi.saveAnswer.
 * - TC-5.4-FE-02: Displays auto-save status indicator (Đang lưu -> Đã lưu).
 * - TC-5.4-FE-03: Selecting True/False statement updates statements and calls saveAnswer.
 * - TC-5.4-FE-04: Typing and blurring Short Text / Number inputs triggers saveAnswer.
 * - TC-5.4-FE-05: Backend 409 attempt_closed error switches UI to submitted state.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import { StudentExamTakePage } from '../pages/student/StudentExamTakePage';
import { studentApi, StudentAttemptDetail } from '../lib/studentApi';

vi.mock('../lib/studentApi', () => ({
  studentApi: {
    getExam: vi.fn(),
    startExam: vi.fn(),
    getAttempt: vi.fn(),
    listExams: vi.fn(),
    saveAnswer: vi.fn(),
  },
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'student-1', username: 'anhnt', full_name: 'Nguyễn Tuấn Anh', role: 'student' },
    isAuthenticated: true,
  }),
}));

const mockAttempt: StudentAttemptDetail = {
  id: 'att-54-1',
  exam_id: 'exam-54-1',
  exam_title: 'Đề Kiểm Tra Toán & Tin 5.4',
  status: 'in_progress',
  started_at: '2026-11-18T08:00:00Z',
  deadline_at: '2026-11-18T09:30:00Z',
  submitted_at: null,
  remaining_seconds: 3600,
  server_now: '2026-11-18T08:00:00Z',
  questions: [
    {
      id: 'q-mcq-1',
      type: 'mcq',
      content_md: 'Câu 1: $1 + 1 = ?$',
      points: '2.50',
      config: {
        options: [
          { id: 'opt_1_a', content_md: '2' },
          { id: 'opt_1_b', content_md: '3' },
        ],
      },
    },
    {
      id: 'q-tf-2',
      type: 'tf',
      content_md: 'Câu 2: Mệnh đề sau đúng hay sai?',
      points: '2.50',
      config: {
        statements: [
          { id: 's1', content_md: 'Số 2 là số nguyên tố chẵn duy nhất' },
          { id: 's2', content_md: 'Số 1 là số nguyên tố' },
        ],
      },
    },
    {
      id: 'q-num-3',
      type: 'short_number',
      content_md: 'Câu 3: Điền nghiệm của phương trình $2x = 6$',
      points: '2.50',
      config: {},
    },
  ],
  answers: {
    'q-mcq-1': {
      question_id: 'q-mcq-1',
      value: { selected: 'opt_1_a' },
      client_seq: 2,
    },
  },
};

describe('Step 5.4: Student Exam Take Auto-Save Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('TC-5.4-FE-01: clicking MCQ option increments client_seq and invokes saveAnswer', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttempt);
    vi.mocked(studentApi.saveAnswer).mockResolvedValueOnce({
      question_id: 'q-mcq-1',
      client_seq: 3,
      status: 'saved',
      updated_at: '2026-11-18T08:05:00Z',
      value: { selected: 'opt_1_b' },
    });

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-54-1/take',
            state: { attemptId: 'att-54-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Đề Kiểm Tra Toán & Tin 5.4')).toBeInTheDocument();
    });

    // Initial answer is opt_1_a (client_seq = 2)
    // Click option B (opt_1_b)
    const optB = screen.getByTestId('option-opt_1_b');
    fireEvent.click(optB);

    await waitFor(() => {
      expect(studentApi.saveAnswer).toHaveBeenCalledWith(
        'att-54-1',
        'q-mcq-1',
        { selected: 'opt_1_b' },
        3 // nextSeq = 2 + 1 = 3
      );
    });
  });

  it('TC-5.4-FE-02: displays save status indicator ("Đã lưu")', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttempt);
    vi.mocked(studentApi.saveAnswer).mockResolvedValueOnce({
      question_id: 'q-mcq-1',
      client_seq: 3,
      status: 'saved',
      updated_at: '2026-11-18T08:05:00Z',
      value: { selected: 'opt_1_b' },
    });

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-54-1/take',
            state: { attemptId: 'att-54-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Đề Kiểm Tra Toán & Tin 5.4')).toBeInTheDocument();
    });

    const optB = screen.getByTestId('option-opt_1_b');
    fireEvent.click(optB);

    await waitFor(() => {
      expect(screen.getByText('Đã lưu')).toBeInTheDocument();
    });
  });

  it('TC-5.4-FE-03: selecting True/False updates statement map and calls saveAnswer', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttempt);
    vi.mocked(studentApi.saveAnswer).mockResolvedValueOnce({
      question_id: 'q-tf-2',
      client_seq: 1,
      status: 'saved',
      updated_at: '2026-11-18T08:06:00Z',
      value: { statements: { s1: true } },
    });

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-54-1/take',
            state: { attemptId: 'att-54-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Câu 1')).toBeInTheDocument();
    });

    // Navigate to Question 2 (TF)
    const nextBtn = screen.getByRole('button', { name: /Câu tiếp theo/i });
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(screen.getByText('Câu 2')).toBeInTheDocument();
    });

    // Click "Đúng" on statement 1
    const dungBtns = screen.getAllByRole('button', { name: 'Đúng' });
    fireEvent.click(dungBtns[0]);

    await waitFor(() => {
      expect(studentApi.saveAnswer).toHaveBeenCalledWith(
        'att-54-1',
        'q-tf-2',
        { statements: { s1: true } },
        1
      );
    });
  });

  it('TC-5.4-FE-04: entering Short Number calls saveAnswer on blur', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttempt);
    vi.mocked(studentApi.saveAnswer).mockResolvedValueOnce({
      question_id: 'q-num-3',
      client_seq: 1,
      status: 'saved',
      updated_at: '2026-11-18T08:07:00Z',
      value: { value: '3' },
    });

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-54-1/take',
            state: { attemptId: 'att-54-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Câu 1')).toBeInTheDocument();
    });

    // Navigate to Question 3
    const q3Btn = screen.getByRole('button', { name: '3' });
    fireEvent.click(q3Btn);

    await waitFor(() => {
      expect(screen.getByText('Câu 3')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/Nhập giá trị số/i);
    fireEvent.change(input, { target: { value: '3' } });
    fireEvent.blur(input);

    await waitFor(() => {
      expect(studentApi.saveAnswer).toHaveBeenCalledWith(
        'att-54-1',
        'q-num-3',
        { value: '3' },
        1
      );
    });
  });

  it('TC-5.4-FE-05: backend 409 attempt_closed marks attempt submitted and disables input', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttempt);
    vi.mocked(studentApi.saveAnswer).mockRejectedValueOnce(
      new Error('409 attempt_closed: Đã hết thời gian làm bài thi.')
    );

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-54-1/take',
            state: { attemptId: 'att-54-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Đề Kiểm Tra Toán & Tin 5.4')).toBeInTheDocument();
    });

    const optB = screen.getByTestId('option-opt_1_b');
    fireEvent.click(optB);

    await waitFor(() => {
      expect(screen.getByText('ĐÃ NỘP')).toBeInTheDocument();
      expect(screen.getByText(/Bài thi này đã hoàn thành hoặc hết thời gian làm bài/i)).toBeInTheDocument();
    });
  });
});
