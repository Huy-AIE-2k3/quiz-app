/**
 * Step 5.6 Frontend Tests: Offline Outbox Queue & In-place Re-auth.
 *
 * Verifies:
 * - TC-5.6-01: Offline mode enqueues 5 answers into Outbox with banner count.
 * - TC-5.6-02: Online recovery automatically flushes outbox sequentially to server and marks 'Đã lưu'.
 * - TC-5.6-03: Refresh (F5) / reload while offline restores pending outbox answers.
 * - TC-5.6-04: 401 session expiration displays ReAuthModal; re-login resumes outbox flush.
 * - TC-5.6-05: Multi-tab outbox synchronization via storage event without conflicts.
 * - TC-5.6-06: localStorage quota/restriction falls back to RAM with warning banner.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import { StudentExamTakePage } from '../pages/student/StudentExamTakePage';
import { studentApi, StudentAttemptDetail } from '../lib/studentApi';
import { answerStore, getOutboxKey } from '../lib/answerStore';
import { safeStorage } from '../lib/storage';
import { ApiError } from '../lib/api';

vi.mock('../lib/studentApi', () => ({
  studentApi: {
    getExam: vi.fn(),
    startExam: vi.fn(),
    getAttempt: vi.fn(),
    listExams: vi.fn(),
    saveAnswer: vi.fn(),
    getAttemptStatus: vi.fn(),
  },
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 'student-56', username: 'student_56', full_name: 'Nguyễn Văn Minh', role: 'student' },
    isAuthenticated: true,
    login: vi.fn(),
  }),
}));

const mockAttemptDetail: StudentAttemptDetail = {
  id: 'att-56-1',
  exam_id: 'exam-56-1',
  exam_title: 'Kiểm Tra Giải Tích & Đại Số Tuyến Tính',
  status: 'in_progress',
  started_at: '2026-11-18T08:00:00Z',
  deadline_at: '2026-11-18T09:30:00Z',
  submitted_at: null,
  remaining_seconds: 3600,
  server_now: '2026-11-18T08:00:00Z',
  student_name: 'student_56',
  questions: [
    {
      id: 'q-mcq-1',
      type: 'mcq',
      content_md: 'Câu 1: Chọn khẳng định đúng.',
      points: '2.00',
      config: {
        options: [
          { id: 'opt_1_a', content_md: 'Đáp án A' },
          { id: 'opt_1_b', content_md: 'Đáp án B' },
        ],
      },
    },
    {
      id: 'q-mcq-2',
      type: 'mcq',
      content_md: 'Câu 2: Chọn khẳng định đúng.',
      points: '2.00',
      config: {
        options: [
          { id: 'opt_2_a', content_md: 'Đáp án A' },
          { id: 'opt_2_b', content_md: 'Đáp án B' },
        ],
      },
    },
    {
      id: 'q-mcq-3',
      type: 'mcq',
      content_md: 'Câu 3: Chọn khẳng định đúng.',
      points: '2.00',
      config: {
        options: [
          { id: 'opt_3_a', content_md: 'Đáp án A' },
          { id: 'opt_3_b', content_md: 'Đáp án B' },
        ],
      },
    },
    {
      id: 'q-mcq-4',
      type: 'mcq',
      content_md: 'Câu 4: Chọn khẳng định đúng.',
      points: '2.00',
      config: {
        options: [
          { id: 'opt_4_a', content_md: 'Đáp án A' },
          { id: 'opt_4_b', content_md: 'Đáp án B' },
        ],
      },
    },
    {
      id: 'q-mcq-5',
      type: 'mcq',
      content_md: 'Câu 5: Chọn khẳng định đúng.',
      points: '2.00',
      config: {
        options: [
          { id: 'opt_5_a', content_md: 'Đáp án A' },
          { id: 'opt_5_b', content_md: 'Đáp án B' },
        ],
      },
    },
  ],
  answers: {},
};

describe('Step 5.6: Offline Outbox Storage & Resilience', () => {
  const attemptId = 'att-56-1';

  beforeEach(() => {
    vi.clearAllMocks();
    answerStore.clear(attemptId);
    safeStorage.setFallbackMode(false);
  });

  afterEach(() => {
    answerStore.clear(attemptId);
    safeStorage.setFallbackMode(false);
  });

  it('TC-5.6-01: offline mode records 5 consecutive answers in outbox and displays offline banner', async () => {
    // 5 answers enqueued
    for (let i = 1; i <= 5; i++) {
      answerStore.enqueue({
        attemptId,
        questionId: `q-mcq-${i}`,
        value: { selected: `opt_${i}_a` },
        client_seq: 1,
      });
    }

    const queued = answerStore.getOutbox(attemptId);
    expect(queued).toHaveLength(5);
    expect(queued[0].questionId).toBe('q-mcq-1');
    expect(queued[4].questionId).toBe('q-mcq-5');

    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttemptDetail);

    // Mock navigator.onLine as false
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);

    render(
      <MemoryRouter initialEntries={[{ pathname: `/s/exams/exam-56-1/take`, state: { attemptId } }]}>
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/MẤT KẾT NỐI MẠNG/i)).toBeInTheDocument();
      expect(screen.getByText(/Outbox: 5 câu chờ gửi/i)).toBeInTheDocument();
    });
  });

  it('TC-5.6-02: network recovery automatically flushes outbox and marks answers as saved', async () => {
    // Put 2 items in outbox
    answerStore.enqueue({
      attemptId,
      questionId: 'q-mcq-1',
      value: { selected: 'opt_1_a' },
      client_seq: 1,
    });
    answerStore.enqueue({
      attemptId,
      questionId: 'q-mcq-2',
      value: { selected: 'opt_2_b' },
      client_seq: 1,
    });

    expect(answerStore.getPendingCount(attemptId)).toBe(2);

    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttemptDetail);
    vi.mocked(studentApi.saveAnswer).mockResolvedValue({
      question_id: 'q-mcq-1',
      client_seq: 1,
      status: 'saved',
      updated_at: '2026-11-18T08:10:00Z',
      value: {},
    });

    // Start online
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);

    render(
      <MemoryRouter initialEntries={[{ pathname: `/s/exams/exam-56-1/take`, state: { attemptId } }]}>
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Câu 1')).toBeInTheDocument();
    });

    // Trigger online event
    window.dispatchEvent(new Event('online'));

    await waitFor(() => {
      expect(studentApi.saveAnswer).toHaveBeenCalledWith('att-56-1', 'q-mcq-1', { selected: 'opt_1_a' }, 1);
      expect(studentApi.saveAnswer).toHaveBeenCalledWith('att-56-1', 'q-mcq-2', { selected: 'opt_2_b' }, 1);
    });

    await waitFor(() => {
      expect(answerStore.getPendingCount(attemptId)).toBe(0);
      expect(screen.getByText('Đã lưu')).toBeInTheDocument();
    });
  });

  it('TC-5.6-03: F5 or reload while offline restores pending outbox answers into attempt view', async () => {
    // Offline outbox pre-existing with answer for q-mcq-1
    answerStore.enqueue({
      attemptId,
      questionId: 'q-mcq-1',
      value: { selected: 'opt_1_b' },
      client_seq: 10,
    });

    // Server has empty answers
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce({
      ...mockAttemptDetail,
      answers: {},
    });

    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false);

    render(
      <MemoryRouter initialEntries={[{ pathname: `/s/exams/exam-56-1/take`, state: { attemptId } }]}>
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Câu 1')).toBeInTheDocument();
    });

    // Option B should be pre-selected from offline outbox
    const optB = screen.getByTestId('option-opt_1_b');
    expect(optB.className).toContain('bg-subtle-accent');

    // Outbox item is still preserved
    expect(answerStore.getPendingCount(attemptId)).toBe(1);
    expect(screen.getByText(/Chưa lưu \(ngoại tuyến\)/i)).toBeInTheDocument();
  });

  it('TC-5.6-04: 401 session expiration displays re-auth modal without redirecting, then resumes flush', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttemptDetail);

    // First saveAnswer returns 401
    vi.mocked(studentApi.saveAnswer).mockRejectedValueOnce(
      new ApiError(401, 'unauthorized', 'Phiên đăng nhập đã hết hạn.')
    );

    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true);

    render(
      <MemoryRouter initialEntries={[{ pathname: `/s/exams/exam-56-1/take`, state: { attemptId } }]}>
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Câu 1')).toBeInTheDocument();
    });

    // Select option A to trigger save
    const optA = screen.getByTestId('option-opt_1_a');
    fireEvent.click(optA);

    // ReAuthModal should pop up
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Phiên đăng nhập đã hết hạn/i })).toBeInTheDocument();
    });

    // Mock auth login success
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'Content-Type': 'application/json' }),
      json: async () => ({
        access_token: 'new_refreshed_token',
        token_type: 'bearer',
        user_id: 'student-56',
        username: 'student_56',
        role: 'student',
      }),
    });

    // Mock saveAnswer to succeed after login
    vi.mocked(studentApi.saveAnswer).mockResolvedValueOnce({
      question_id: 'q-mcq-1',
      client_seq: 1,
      status: 'saved',
      updated_at: '2026-11-18T08:15:00Z',
      value: { selected: 'opt_1_a' },
    });

    // Fill password in modal and submit
    const passwordInput = screen.getByTestId('reauth-password-input');
    fireEvent.change(passwordInput, { target: { value: 'SecretPassword123' } });

    const submitBtn = screen.getByRole('button', { name: /Xác nhận và tiếp tục làm bài/i });
    fireEvent.click(submitBtn);

    // Modal should close and outbox flushes
    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: /Phiên đăng nhập đã hết hạn/i })).toBeNull();
      expect(answerStore.getPendingCount(attemptId)).toBe(0);
    });
  });

  it('TC-5.6-05: cross-tab storage event synchronizes outbox without conflict', async () => {
    let receivedQueue: unknown[] = [];
    const unsubscribe = answerStore.subscribe(attemptId, (items) => {
      receivedQueue = items;
    });

    // Simulate another tab updating localStorage
    const otherTabItem = {
      attemptId,
      questionId: 'q-mcq-3',
      value: { selected: 'opt_3_b' },
      client_seq: 5,
      timestamp: Date.now(),
      retries: 0,
      status: 'pending' as const,
    };

    safeStorage.setItem(getOutboxKey(attemptId), JSON.stringify([otherTabItem]));

    // Dispatch StorageEvent
    const storageEvent = new StorageEvent('storage', {
      key: getOutboxKey(attemptId),
      newValue: JSON.stringify([otherTabItem]),
    });
    window.dispatchEvent(storageEvent);

    expect(receivedQueue).toHaveLength(1);
    expect((receivedQueue[0] as { questionId: string }).questionId).toBe('q-mcq-3');
    unsubscribe();
  });

  it('TC-5.6-06: localStorage failure falls back to RAM and displays storage warning banner', async () => {
    safeStorage.setFallbackMode(true);
    expect(answerStore.isMemoryFallback()).toBe(true);

    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttemptDetail);

    render(
      <MemoryRouter initialEntries={[{ pathname: `/s/exams/exam-56-1/take`, state: { attemptId } }]}>
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/Bộ nhớ trình duyệt bị hạn chế hoặc đã đầy/i)).toBeInTheDocument();
    });

    // Can still enqueue in RAM without throwing errors
    answerStore.enqueue({
      attemptId,
      questionId: 'q-mcq-1',
      value: { selected: 'opt_1_a' },
      client_seq: 1,
    });
    expect(answerStore.getPendingCount(attemptId)).toBe(1);
  });
});
