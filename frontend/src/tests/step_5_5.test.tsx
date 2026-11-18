/**
 * Step 5.5 Frontend Tests: Client Monotonic Countdown & Anti-Tampering Mechanism.
 *
 * Verifies:
 * - TC-5.5-01: Altering OS clock (+1 hour) does NOT tamper with countdown time.
 * - TC-5.5-02: Tab visibilitychange (hiding and returning) triggers status re-sync.
 * - TC-5.5-03: Network outage does NOT halt countdown; timer continues via performance.now().
 * - TC-5.5-04: Timer expiration (0s) immediately triggers auto-submit and locks interface.
 * - TC-5.5-05: Teacher deadline extension updates remaining time seamlessly on status sync.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import { useMonotonicTimer, formatTimeMMSS } from '../hooks/useMonotonicTimer';
import { StudentExamTakePage } from '../pages/student/StudentExamTakePage';
import { studentApi, StudentAttemptDetail } from '../lib/studentApi';

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
    user: { id: 'student-1', username: 'anhnt', full_name: 'Nguyễn Tuấn Anh', role: 'student' },
    isAuthenticated: true,
  }),
}));

const mockAttempt: StudentAttemptDetail = {
  id: 'att-55-1',
  exam_id: 'exam-55-1',
  exam_title: 'Đề Khảo Sát Toán 12 - Bước 5.5',
  status: 'in_progress',
  started_at: '2026-11-18T08:00:00Z',
  deadline_at: '2026-11-18T08:10:00Z',
  submitted_at: null,
  remaining_seconds: 600, // 10 minutes
  server_now: '2026-11-18T08:00:00Z',
  questions: [
    {
      id: 'q-1',
      type: 'mcq',
      content_md: 'Câu 1?',
      points: '5.00',
      config: {
        options: [
          { id: 'opt_1', content_md: 'Đáp án A' },
          { id: 'opt_2', content_md: 'Đáp án B' },
        ],
      },
    },
  ],
  answers: {},
};

describe('Step 5.5: Client Monotonic Countdown & Anti-Tampering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('TC-5.5-01: altering OS clock does not distort countdown (monotonic performance.now())', () => {
    vi.useFakeTimers();

    let simulatedPerfNow = 1000;
    vi.spyOn(performance, 'now').mockImplementation(() => simulatedPerfNow);

    const { result } = renderHook(() =>
      useMonotonicTimer({
        initialRemainingSeconds: 600,
        syncIntervalMs: 0,
      })
    );

    expect(result.current.secondsRemaining).toBe(600);

    // Simulate 5 seconds passing in real elapsed time
    act(() => {
      simulatedPerfNow += 5000; // 5 seconds
      vi.advanceTimersByTime(5000);
    });
    expect(result.current.secondsRemaining).toBe(595);

    // Malicious student changes OS clock forward by 1 hour (3,600,000 ms)
    const originalDateNow = Date.now();
    vi.spyOn(Date, 'now').mockReturnValue(originalDateNow + 3600 * 1000);

    // Advance real time by only 2 seconds
    act(() => {
      simulatedPerfNow += 2000;
      vi.advanceTimersByTime(2000);
    });

    // Monotonic clock should only decrease by 2s (595 - 2 = 593), completely immune to Date.now()
    expect(result.current.secondsRemaining).toBe(593);
    expect(result.current.formatTimer()).toBe('09:53');

    vi.useRealTimers();
  });

  it('TC-5.5-02: tab visibilitychange (hiding and returning) re-synchronizes with server status', async () => {
    const onStatusSync = vi.fn();
    vi.mocked(studentApi.getAttemptStatus).mockResolvedValueOnce({
      id: 'att-55-1',
      status: 'in_progress',
      remaining_seconds: 300,
      server_now: '2026-11-18T08:05:00Z',
      deadline_at: '2026-11-18T08:10:00Z',
      submitted_at: null,
    });

    renderHook(() =>
      useMonotonicTimer({
        attemptId: 'att-55-1',
        initialRemainingSeconds: 600,
        onStatusSync,
        syncIntervalMs: 0,
      })
    );

    // Simulate tab becoming visible
    Object.defineProperty(document, 'visibilityState', {
      value: 'visible',
      configurable: true,
    });

    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });

    await waitFor(() => {
      expect(studentApi.getAttemptStatus).toHaveBeenCalledWith('att-55-1');
      expect(onStatusSync).toHaveBeenCalledWith(
        expect.objectContaining({ remaining_seconds: 300 })
      );
    });
  });

  it('TC-5.5-03: network outage does not freeze countdown; ticks uninterrupted', () => {
    vi.useFakeTimers();

    let simulatedPerfNow = 0;
    vi.spyOn(performance, 'now').mockImplementation(() => simulatedPerfNow);

    // Even if status sync throws network error
    vi.mocked(studentApi.getAttemptStatus).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() =>
      useMonotonicTimer({
        attemptId: 'att-55-1',
        initialRemainingSeconds: 100,
        syncIntervalMs: 10000,
      })
    );

    expect(result.current.secondsRemaining).toBe(100);

    // Advance 10 seconds while offline
    act(() => {
      simulatedPerfNow += 10000;
      vi.advanceTimersByTime(10000);
    });

    expect(result.current.secondsRemaining).toBe(90);

    vi.useRealTimers();
  });

  it('TC-5.5-04: timer reaching 0 triggers onTimeUp immediately', () => {
    vi.useFakeTimers();

    let simulatedPerfNow = 0;
    vi.spyOn(performance, 'now').mockImplementation(() => simulatedPerfNow);

    const onTimeUp = vi.fn();

    const { result } = renderHook(() =>
      useMonotonicTimer({
        initialRemainingSeconds: 3,
        onTimeUp,
        syncIntervalMs: 0,
      })
    );

    expect(result.current.secondsRemaining).toBe(3);
    expect(onTimeUp).not.toHaveBeenCalled();

    // Advance 3 seconds
    act(() => {
      simulatedPerfNow += 3000;
      vi.advanceTimersByTime(3000);
    });

    expect(result.current.secondsRemaining).toBe(0);
    expect(result.current.isExpired).toBe(true);
    expect(onTimeUp).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });

  it('TC-5.5-05: teacher deadline extension updates remaining time seamlessly', async () => {
    vi.mocked(studentApi.getAttempt).mockResolvedValueOnce(mockAttempt);
    // When status endpoint is polled, return extended deadline (+300s = 900s)
    vi.mocked(studentApi.getAttemptStatus).mockResolvedValueOnce({
      id: 'att-55-1',
      status: 'in_progress',
      remaining_seconds: 900,
      server_now: '2026-11-18T08:00:00Z',
      deadline_at: '2026-11-18T08:15:00Z',
      submitted_at: null,
    });

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/s/exams/exam-55-1/take',
            state: { attemptId: 'att-55-1' },
          },
        ]}
      >
        <Routes>
          <Route path="/s/exams/:examId/take" element={<StudentExamTakePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Đề Khảo Sát Toán 12 - Bước 5.5')).toBeInTheDocument();
    });

    // Trigger visibilitychange to fetch status
    Object.defineProperty(document, 'visibilityState', {
      value: 'visible',
      configurable: true,
    });

    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });

    await waitFor(() => {
      // 900 seconds = 15:00
      expect(screen.getByText('15:00')).toBeInTheDocument();
    });
  });

  it('TC-5.5-06: formatTimeMMSS helper formats edge cases correctly', () => {
    expect(formatTimeMMSS(0)).toBe('00:00');
    expect(formatTimeMMSS(5)).toBe('00:05');
    expect(formatTimeMMSS(65)).toBe('01:05');
    expect(formatTimeMMSS(3600)).toBe('60:00');
    expect(formatTimeMMSS(-10)).toBe('00:00');
  });
});
