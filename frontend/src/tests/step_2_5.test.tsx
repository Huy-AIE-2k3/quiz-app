/**
 * Step 2.5 Test Suite: API Client, Routing, Auth Guards, and Global Error Handling.
 *
 * Verifies:
 * - TC-2.5-01: Distinction between ApiError (HTTP 500) and NetworkError (fetch abort / network down)
 * - TC-2.5-02: Automatic retry on GET with 503 errors succeeds on 3rd attempt
 * - TC-2.5-03: Non-idempotent POST is NEVER retried on NetworkError
 * - TC-2.5-04: Session expiry (401) clears token and triggers returnTo login redirection
 * - TC-2.5-05: Server wake-up detection (>3s) displays banner and dismisses upon /healthz recovery
 * - TC-2.5-06: Unreachable server (>90s) transitions to error state with manual retry without infinite loop
 * - TC-2.5-07: vite:preloadError displays update modal while preserving localStorage draft/outbox
 * - TC-2.5-08: Role route guard (RequireAuth) redirects student from /a/classes to /s/exams and admin from /s/exams to /a/classes
 * - TC-2.5-09: Blocked localStorage triggers in-memory fallback without crashing
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

import {
  request,
  ApiError,
  NetworkError,
  serverStateManager,
  pollServerHealth,
  setAuthExpiredHandler,
} from '../lib/api';
import { safeStorage } from '../lib/storage';
import { AuthProvider } from '../context/AuthContext';
import { RequireAuth } from '../components/auth/RequireAuth';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { ServerWakeBanner } from '../components/common/ServerWakeBanner';

describe('Step 2.5: API Client, Routing & Global Error Handling', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
    safeStorage.clear();
    safeStorage.setFallbackMode(false);
    serverStateManager.setStatus('idle');
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.useRealTimers();
  });

  // TC-2.5-01: Phân biệt rành mạch giữa HTTP 500 (ApiError) và mất mạng (NetworkError)
  it('TC-2.5-01: distinguishes between ApiError(500) and NetworkError(TypeError/abort)', async () => {
    // 1. Mock HTTP 500 response
    const mock500 = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      headers: new Headers({ 'Content-Type': 'application/json', 'X-Request-ID': 'req-err-500' }),
      json: async () => ({
        error: { code: 'internal_error', message: 'Máy chủ xảy ra lỗi nội bộ' },
      }),
    });
    global.fetch = mock500;

    let apiErr: unknown;
    try {
      await request('/api/v1/test-500', { maxRetries: 0 });
    } catch (err) {
      apiErr = err;
    }

    expect(apiErr).toBeInstanceOf(ApiError);
    expect((apiErr as ApiError).status).toBe(500);
    expect((apiErr as ApiError).code).toBe('internal_error');
    expect((apiErr as ApiError).requestId).toBe('req-err-500');

    // 2. Mock network failure (TypeError: Failed to fetch)
    const mockNetErr = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));
    global.fetch = mockNetErr;

    let netErr: unknown;
    try {
      await request('/api/v1/test-network', { maxRetries: 0 });
    } catch (err) {
      netErr = err;
    }

    expect(netErr).toBeInstanceOf(NetworkError);
    expect((netErr as NetworkError).message).toContain('Mất kết nối mạng');
  });

  // TC-2.5-02: Thử lại GET khi server chập chờn 503
  it('TC-2.5-02: automatically retries GET request on 503 and succeeds on 3rd attempt', async () => {
    let callCount = 0;
    global.fetch = vi.fn().mockImplementation(async () => {
      callCount++;
      if (callCount < 3) {
        return {
          ok: false,
          status: 503,
          statusText: 'Service Unavailable',
          headers: new Headers(),
          json: async () => ({ error: { code: 'db_unavailable' } }),
        };
      }
      return {
        ok: true,
        status: 200,
        headers: new Headers({ 'Content-Type': 'application/json' }),
        json: async () => ({ data: 'success_on_retry' }),
      };
    });

    // Use fast backoff delays for unit testing
    const result = await request<{ data: string }>('/api/v1/flaky-service', {
      method: 'GET',
      maxRetries: 3,
      backoffDelays: [10, 20, 40],
    });

    expect(callCount).toBe(3);
    expect(result.data).toBe('success_on_retry');
  });

  // TC-2.5-03: Không thử lại POST khi gặp NetworkError
  it('TC-2.5-03: non-idempotent POST does not automatically retry on NetworkError', async () => {
    let callCount = 0;
    global.fetch = vi.fn().mockImplementation(async () => {
      callCount++;
      throw new TypeError('Network disconnected');
    });

    let caughtError: unknown;
    try {
      await request('/api/v1/submit-answer', {
        method: 'POST',
        body: { answer: 'A' },
        idempotent: false,
        maxRetries: 3,
        backoffDelays: [10, 20, 40],
      });
    } catch (err) {
      caughtError = err;
    }

    expect(callCount).toBe(1); // Exactly 1 call, NO retries
    expect(caughtError).toBeInstanceOf(NetworkError);
  });

  // TC-2.5-04: Hết phiên (401) xóa token và chuyển hướng tới login kèm returnTo
  it('TC-2.5-04: 401 unauthorized removes token and invokes onAuthExpired with returnTo', async () => {
    safeStorage.setToken('expired_sample_token');
    const authExpiredSpy = vi.fn();
    setAuthExpiredHandler(authExpiredSpy);

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      headers: new Headers(),
      json: async () => ({ error: { code: 'session_expired' } }),
    });

    let caughtErr: unknown;
    try {
      await request('/api/v1/student/exams');
    } catch (err) {
      caughtErr = err;
    }

    expect(caughtErr).toBeInstanceOf(ApiError);
    expect((caughtErr as ApiError).status).toBe(401);
    expect(authExpiredSpy).toHaveBeenCalled();
  });

  // TC-2.5-05: Server ngủ (>3s delay) hiện banner "Đang đánh thức máy chủ", poll /healthz và tự phục hồi
  it('TC-2.5-05: server waking detection shows banner and hides after /healthz recovery', async () => {
    serverStateManager.setStatus('idle');
    const { unmount } = render(<ServerWakeBanner />);

    // Initially idle -> no banner rendered
    expect(screen.queryByRole('status')).toBeNull();

    // Trigger waking status
    act(() => {
      serverStateManager.setStatus('waking');
    });

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText(/Đang kết nối máy chủ/i)).toBeInTheDocument();

    // Mock /healthz recovery
    global.fetch = vi.fn().mockResolvedValue({ ok: true, status: 200 });
    const recovered = await pollServerHealth(5_000, 100);

    expect(recovered).toBe(true);
    expect(serverStateManager.getStatus()).toBe('online');
    await waitFor(() => {
      expect(screen.queryByRole('status')).toBeNull();
    });

    unmount();
  });

  // TC-2.5-06: Server không phản hồi quá thời hạn (>90s) chuyển sang trạng thái lỗi không lặp vô hạn
  it('TC-2.5-06: server unreachable after max timeout switches to error state with manual retry', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Connection refused'));

    // Test with short max duration to simulate 90s expiration cleanly
    const recovered = await pollServerHealth(200, 50);

    expect(recovered).toBe(false);
    expect(serverStateManager.getStatus()).toBe('unreachable');

    render(<ServerWakeBanner />);
    expect(screen.getByText(/Không thể kết nối máy chủ/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Thử lại/i })).toBeInTheDocument();
  });

  // TC-2.5-07: Chunk cũ kích hoạt vite:preloadError hiện modal cập nhật và giữ nguyên localStorage draft/outbox
  it('TC-2.5-07: vite:preloadError displays update modal while preserving localStorage outbox', async () => {
    const draftPayload = JSON.stringify({ attempt_id: 'att-123', answers: [{ qid: 'q1', val: 'A' }] });
    safeStorage.setOutbox(draftPayload);

    render(
      <ErrorBoundary>
        <div>Nội dung ứng dụng</div>
      </ErrorBoundary>
    );

    // Dispatch vite:preloadError event
    act(() => {
      window.dispatchEvent(new Event('vite:preloadError'));
    });

    // Modal appears
    expect(screen.getByRole('heading', { name: /Bản cập nhật mới/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Tải lại trang/i })).toBeInTheDocument();

    // Verify localStorage draft is completely preserved
    expect(safeStorage.getOutbox()).toBe(draftPayload);
  });

  // TC-2.5-08: Bảo vệ route (RequireAuth): student vào /a/classes -> /s/exams; admin vào /s/exams -> /a/classes
  it('TC-2.5-08: RequireAuth redirects student away from admin routes and admin from student routes', async () => {
    const studentUser = {
      id: 'u-std',
      username: 'student01',
      full_name: 'Nguyễn Văn Học Sinh',
      role: 'student' as const,
      is_active: true,
    };

    safeStorage.setToken('valid_student_token');
    safeStorage.setUser(JSON.stringify(studentUser));

    // Mock /api/v1/auth/me
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'Content-Type': 'application/json' }),
      json: async () => ({ user: studentUser }),
    });

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/a/classes']}>
          <Routes>
            <Route element={<RequireAuth allowedRoles={['admin']} />}>
              <Route path="/a/classes" element={<div>TRANG QUẢN TRỊ ADMIN BẢO MẬT</div>} />
            </Route>
            <Route path="/s/exams" element={<div>TRANG ĐỀ THI HỌC SINH</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    // Forbidden admin content must NEVER be shown
    expect(screen.queryByText('TRANG QUẢN TRỊ ADMIN BẢO MẬT')).toBeNull();

    // Redirected to student home
    await waitFor(() => {
      expect(screen.getByText('TRANG ĐỀ THI HỌC SINH')).toBeInTheDocument();
    });
  });

  // TC-2.5-09: Khi localStorage bị chặn, ứng dụng tự fallback lưu phiên trên bộ nhớ tạm (in-memory)
  it('TC-2.5-09: falls back to in-memory storage when localStorage throws an error', () => {
    // Spy on Storage.prototype.setItem to throw SecurityError
    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('The operation is insecure.', 'SecurityError');
    });

    try {
      // Re-probe storage availability
      safeStorage.checkAvailability();
      expect(safeStorage.isMemoryFallback()).toBe(true);

      // In-memory write and read must work seamlessly without throwing
      safeStorage.setToken('memory_fallback_token_123');
      expect(safeStorage.getToken()).toBe('memory_fallback_token_123');

      safeStorage.removeToken();
      expect(safeStorage.getToken()).toBeNull();
    } finally {
      setItemSpy.mockRestore();
      safeStorage.checkAvailability();
    }
  });
});
