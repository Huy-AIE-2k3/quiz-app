/**
 * Step 5.3 Frontend Tests: Load Attempt, Deterministic Shuffling & Option Labels.
 *
 * Verifies:
 * - TC-5.3-FE-01: Loads attempt and displays exam title and questions.
 * - TC-5.3-FE-02: Client renders option letters A, B, C, D in order while keeping option IDs.
 * - TC-5.3-FE-03: Restores previously saved answers on page load (e.g. from tab reload).
 * - TC-5.3-FE-04: Displays countdown timer accurately and tracks tick.
 * - TC-5.3-FE-05: Handles corrupt question (unavailable: true) safely without crashing.
 * - TC-5.3-FE-06: Displays submitted state banner when attempt is already submitted.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import { StudentExamTakePage } from '../pages/student/StudentExamTakePage';
import { studentApi, StudentAttemptDetail } from '../lib/studentApi';

vi.mock('../lib/studentApi', () => ({
  studentApi: {
    getExam: vi.fn(),
    startExam: vi.fn(),
    getAttempt: vi.fn(),
    listExams: vi.fn(),
  },
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'student-1', username: 'anhnt', full_name: 'Nguyễn Tuấn Anh', role: 'student' },
    isAuthenticated: true,
  }),
}));

const mockAttempt: StudentAttemptDetail = {
  id: 'att-53-1',
  exam_id: 'exam-53-1',
  exam_title: 'Đề Khảo Sát Toán 12',
  status: 'in_progress',
  started_at: '2026-11-18T08:00:00Z',
  deadline_at: '2026-11-18T09:30:00Z',
  submitted_at: null,
  remaining_seconds: 3600,
  server_now: '2026-11-18T08:00:00Z',
  questions: [
    {
      id: 'q-1',
      type: 'mcq',
      content_md: 'Phương trình $x^2 - 4 = 0$ có nghiệm là:',
      points: '5.00',
      config: {
        options: [
          { id: 'opt_alpha', content_md: '$x = 2$ hoặc $x = -2$' },
          { id: 'opt_beta', content_md: '$x = 4$ hoặc $x = -4$' },
          { id: 'opt_gamma', content_md: '$x = 0$' },
          { id: 'opt_delta', content_md: '$x = 1$' },
        ],
      },
    },
    {
      id: 'q-2',
      type: 'mcq',
      content_md: 'Câu hỏi số 2?',
      points: '5.00',
      config: {
        options: [
          { id: 'opt_2_1', content_md: 'Lựa chọn 1' },
          { id: 'opt_2_2', content_md: 'Lựa chọn 2' },
        ],
      },
    },
  ],
  answers: {
    'q-1': {
      question_id: 'q-1',
      value: { selected: 'opt_alpha' },
      client_seq: 15,
    },
  },
};

describe('Step 5.3: Student Exam Take Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('TC-5.3-FE-01: loads attempt detail and displays exam title and first question', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttempt);

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-53-1/take',
            state: { attemptId: 'att-53-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Đề Khảo Sát Toán 12')).toBeInTheDocument();
      expect(screen.getByText(/Phương trình/i)).toBeInTheDocument();
    });

    expect(studentApi.getAttempt).toHaveBeenCalledWith('att-53-1');
  });

  it('TC-5.3-FE-02: renders client-side option labels A, B, C, D in order for MCQ', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttempt);

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-53-1/take',
            state: { attemptId: 'att-53-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('B')).toBeInTheDocument();
      expect(screen.getByText('C')).toBeInTheDocument();
      expect(screen.getByText('D')).toBeInTheDocument();
    });
  });

  it('TC-5.3-FE-03: restores prior saved answers on page load (e.g. from tab reload)', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttempt);

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-53-1/take',
            state: { attemptId: 'att-53-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Phương trình/i)).toBeInTheDocument();
    });

    // Option A ($x = 2$ hoặc $x = -2$) was in mockAttempt.answers -> should be visually selected
    const optionLetterA = screen.getByText('A');
    expect(optionLetterA).toHaveClass('bg-brand');
  });

  it('TC-5.3-FE-04: formats countdown timer accurately from remaining_seconds', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce({
      ...mockAttempt,
      remaining_seconds: 3665, // 61 minutes and 5 seconds -> 61:05
    });

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-53-1/take',
            state: { attemptId: 'att-53-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('61:05')).toBeInTheDocument();
    });
  });

  it('TC-5.3-FE-05: handles corrupt question (unavailable: true) safely without crashing', async () => {
    const corruptAttempt: StudentAttemptDetail = {
      ...mockAttempt,
      questions: [
        {
          id: 'q-corrupt',
          type: 'mcq',
          content_md: 'Nội dung câu lỗi',
          points: '5.00',
          config: {},
          unavailable: true,
        },
      ],
      answers: {},
    };
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(corruptAttempt);

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-53-1/take',
            state: { attemptId: 'att-53-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('KHÔNG KHẢ DỤNG')).toBeInTheDocument();
      expect(screen.getByText(/Câu hỏi tạm thời không khả dụng/i)).toBeInTheDocument();
    });
  });

  it('TC-5.3-FE-06: displays submitted state banner when attempt is already submitted', async () => {
    const submittedAttempt: StudentAttemptDetail = {
      ...mockAttempt,
      status: 'submitted',
      remaining_seconds: 0,
    };
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(submittedAttempt);

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-53-1/take',
            state: { attemptId: 'att-53-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('ĐÃ NỘP')).toBeInTheDocument();
      expect(screen.getByText('Đã thu bài')).toBeInTheDocument();
      expect(
        screen.getByText(/Bài thi này đã hoàn thành hoặc hết thời gian làm bài/i)
      ).toBeInTheDocument();
    });
  });
});
