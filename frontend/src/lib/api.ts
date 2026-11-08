/**
 * Unified API Client for Mathrix Quiz Application.
 *
 * Implements:
 * - Strict distinction between ApiError (HTTP status >= 400) and NetworkError (disconnect/timeout).
 * - Automatic retry policy: ONLY for GET or idempotent requests on NetworkError or 502/503/504.
 * - Non-idempotent mutations (POST/PUT) are NEVER retried automatically.
 * - Automatic Bearer token attachment via safeStorage.
 * - 401 session expiration handling with outbox preservation on exam pages.
 * - Server wake-up detection (> 3s delay) and /healthz recovery polling up to 90s.
 */

import { safeStorage } from './storage';
import { VI } from './i18n/vi';

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: unknown,
    public requestId?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message = 'Lỗi kết nối mạng') {
    super(message);
    this.name = 'NetworkError';
  }
}

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  timeoutMs?: number;
  idempotent?: boolean;
  maxRetries?: number;
  backoffDelays?: number[]; // e.g. [1000, 2000, 4000]
  skipAuth?: boolean;
}

export type ServerConnectionStatus = 'idle' | 'waking' | 'online' | 'unreachable';

type ServerStatusListener = (status: ServerConnectionStatus) => void;
type AuthExpiredListener = (returnTo: string) => void;

class ServerStateManager {
  private listeners = new Set<ServerStatusListener>();
  private currentStatus: ServerConnectionStatus = 'idle';

  public getStatus(): ServerConnectionStatus {
    return this.currentStatus;
  }

  public setStatus(status: ServerConnectionStatus): void {
    if (this.currentStatus !== status) {
      this.currentStatus = status;
      this.listeners.forEach((fn) => fn(status));
    }
  }

  public subscribe(fn: ServerStatusListener): () => void {
    this.listeners.add(fn);
    fn(this.currentStatus);
    return () => this.listeners.delete(fn);
  }
}

export const serverStateManager = new ServerStateManager();

// Global handler for 401 unauthorized
let onAuthExpired: AuthExpiredListener = (returnTo: string) => {
  safeStorage.removeToken();
  if (typeof window !== 'undefined') {
    const isExamTaking =
      window.location.pathname.includes('/take') || window.location.pathname.includes('/exam/');
    if (!isExamTaking) {
      window.location.href = `/login?returnTo=${encodeURIComponent(returnTo)}`;
    }
  }
};

export function setAuthExpiredHandler(handler: AuthExpiredListener): void {
  onAuthExpired = handler;
}

/**
 * Calculates exponential backoff with random jitter (±20%).
 */
export function calculateBackoff(baseMs: number): number {
  const jitterFactor = 0.8 + Math.random() * 0.4; // 0.8 to 1.2
  return Math.round(baseMs * jitterFactor);
}

/**
 * Checks whether an HTTP status is transient and eligible for retry.
 */
function isTransientServerError(status: number): boolean {
  return status === 502 || status === 503 || status === 504;
}

/**
 * Resolves the base URL for API requests.
 */
export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const envUrl = (import.meta as unknown as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL;
    return envUrl || '';
  }
  return '';
}

/**
 * Polls /healthz every intervalMs until success (200) or maxDurationMs expires.
 */
export async function pollServerHealth(
  maxDurationMs = 90_000,
  intervalMs = 3_000,
  healthPath = '/healthz'
): Promise<boolean> {
  const startTime = Date.now();
  serverStateManager.setStatus('waking');

  while (Date.now() - startTime < maxDurationMs) {
    try {
      const res = await fetch(`${getApiBaseUrl()}${healthPath}`, { method: 'GET' });
      if (res.ok) {
        serverStateManager.setStatus('online');
        return true;
      }
    } catch {
      // Server still starting up, continue polling
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }

  serverStateManager.setStatus('unreachable');
  return false;
}

/**
 * Core HTTP request client.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = 'GET',
    body,
    headers = {},
    timeoutMs = 15_000,
    idempotent = false,
    maxRetries = 3,
    backoffDelays = [1000, 2000, 4000],
    skipAuth = false,
    ...restOptions
  } = options;

  const isGet = method.toUpperCase() === 'GET';
  const canRetry = isGet || idempotent;

  const url = path.startsWith('http') ? path : `${getApiBaseUrl()}${path}`;
  const normalizedHeaders = new Headers(headers);

  if (!skipAuth) {
    const token = safeStorage.getToken();
    if (token && !normalizedHeaders.has('Authorization')) {
      normalizedHeaders.set('Authorization', `Bearer ${token}`);
    }
  }

  if (body && !normalizedHeaders.has('Content-Type') && typeof body === 'object') {
    normalizedHeaders.set('Content-Type', 'application/json');
  }

  const serializedBody =
    body && typeof body === 'object' && !(body instanceof FormData)
      ? JSON.stringify(body)
      : (body as BodyInit | null | undefined);

  let attempt = 0;

  while (true) {
    attempt++;
    const controller = new AbortController();
    let isTimeout = false;

    const timeoutId = setTimeout(() => {
      isTimeout = true;
      controller.abort();
    }, timeoutMs);

    // Monitor for sleeping server (delay > 3s on initial attempt)
    const wakeTimer = setTimeout(() => {
      if (serverStateManager.getStatus() === 'idle') {
        serverStateManager.setStatus('waking');
      }
    }, 3_000);

    try {
      const response = await fetch(url, {
        method,
        headers: normalizedHeaders,
        body: serializedBody,
        signal: controller.signal,
        ...restOptions,
      });

      clearTimeout(timeoutId);
      clearTimeout(wakeTimer);

      if (serverStateManager.getStatus() === 'waking') {
        serverStateManager.setStatus('online');
      }

      // Check HTTP Status
      if (!response.ok) {
        const requestId = response.headers.get('X-Request-ID') || undefined;

        // Check for 401 Unauthorized (only when not skipping auth)
        if (!skipAuth && response.status === 401) {
          const currentPath =
            typeof window !== 'undefined'
              ? window.location.pathname + window.location.search
              : '/';
          onAuthExpired(currentPath);
          throw new ApiError(401, 'unauthorized', VI.auth.sessionExpired, undefined, requestId);
        }

        // Check for 429 Too Many Requests
        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After');
          const waitSec = retryAfter ? parseInt(retryAfter, 10) : 5;
          throw new ApiError(
            429,
            'rate_limited',
            `Thao tác quá nhanh. Vui lòng chờ ${waitSec} giây.`,
            { retryAfter: waitSec },
            requestId
          );
        }

        // Retry on 502/503/504 for GET / idempotent requests
        if (canRetry && isTransientServerError(response.status) && attempt <= maxRetries) {
          const delayBase = backoffDelays[attempt - 1] ?? 4000;
          await new Promise((r) => setTimeout(r, calculateBackoff(delayBase)));
          continue;
        }

        // Parse structured API error response
        let errorData: { error?: { code?: string; message?: string; detail?: unknown } } = {};
        try {
          errorData = await response.json();
        } catch {
          // Response body was not JSON
        }

        const code = errorData.error?.code || `http_${response.status}`;
        const message = errorData.error?.message || response.statusText || VI.common.error;
        const details = errorData.error?.detail;

        throw new ApiError(response.status, code, message, details, requestId);
      }

      // Success (2xx)
      if (response.status === 204) {
        return undefined as unknown as T;
      }

      const contentType = response.headers.get('Content-Type') || '';
      if (contentType.includes('application/json')) {
        return (await response.json()) as T;
      }
      return (await response.text()) as unknown as T;
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      clearTimeout(wakeTimer);

      if (err instanceof ApiError) {
        throw err;
      }

      const isNetworkOrTimeout =
        isTimeout ||
        err instanceof TypeError ||
        (err instanceof DOMException && err.name === 'AbortError');

      if (isNetworkOrTimeout) {
        // Can retry only if request is GET or explicitly marked idempotent
        if (canRetry && attempt <= maxRetries) {
          const delayBase = backoffDelays[attempt - 1] ?? 4000;
          await new Promise((r) => setTimeout(r, calculateBackoff(delayBase)));
          continue;
        }
        throw new NetworkError(isTimeout ? VI.network.timeout : VI.network.offline);
      }

      throw err;
    }
  }
}
