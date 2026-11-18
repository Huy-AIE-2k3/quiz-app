/**
 * Monotonic Countdown Timer Hook (Step 5.5).
 *
 * Implements anti-tampering countdown clock using performance.now():
 * - Monotonic progression: immune to OS clock tampering (+/- 1 hour changes).
 * - Automatic re-synchronization on:
 *   - Tab re-entry (visibilitychange: visible)
 *   - Network reconnection (online)
 *   - Periodic background sync (default 30s)
 * - Immediate auto-submit trigger when remaining seconds reach 0.
 * - Offline fault tolerance: continues ticking uninterrupted if network is lost.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { studentApi, StudentAttemptStatusResponse } from '../lib/studentApi';

export interface UseMonotonicTimerOptions {
  attemptId?: string;
  initialRemainingSeconds: number;
  isSubmitted?: boolean;
  onTimeUp?: () => void;
  onStatusSync?: (status: StudentAttemptStatusResponse) => void;
  syncIntervalMs?: number;
}

export interface UseMonotonicTimerReturn {
  secondsRemaining: number;
  isExpired: boolean;
  syncNow: () => Promise<void>;
  formatTimer: (seconds?: number) => string;
}

export function formatTimeMMSS(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  const mins = Math.floor(s / 60);
  const secs = s % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export const useMonotonicTimer = ({
  attemptId,
  initialRemainingSeconds,
  isSubmitted = false,
  onTimeUp,
  onStatusSync,
  syncIntervalMs = 30000,
}: UseMonotonicTimerOptions): UseMonotonicTimerReturn => {
  const [secondsRemaining, setSecondsRemaining] = useState<number>(initialRemainingSeconds);

  // Monotonic reference anchors
  const startPerfRef = useRef<number>(performance.now());
  const anchorRemainingRef = useRef<number>(initialRemainingSeconds);
  const isSubmittedRef = useRef<boolean>(isSubmitted);
  isSubmittedRef.current = isSubmitted;

  const onTimeUpRef = useRef(onTimeUp);
  onTimeUpRef.current = onTimeUp;
  const onStatusSyncRef = useRef(onStatusSync);
  onStatusSyncRef.current = onStatusSync;

  const hasTriggeredTimeUpRef = useRef(false);

  // Update anchors when initialRemainingSeconds changes
  useEffect(() => {
    anchorRemainingRef.current = initialRemainingSeconds;
    startPerfRef.current = performance.now();
    setSecondsRemaining(initialRemainingSeconds);
    if (initialRemainingSeconds > 0) {
      hasTriggeredTimeUpRef.current = false;
    }
  }, [initialRemainingSeconds]);

  // Authoritative server clock sync
  const syncNow = useCallback(async () => {
    if (!attemptId || isSubmittedRef.current) return;

    try {
      const data = await studentApi.getAttemptStatus(attemptId);
      anchorRemainingRef.current = data.remaining_seconds;
      startPerfRef.current = performance.now();
      setSecondsRemaining(data.remaining_seconds);

      if (onStatusSyncRef.current) {
        onStatusSyncRef.current(data);
      }

      if (data.status === 'submitted' || data.remaining_seconds <= 0) {
        if (!hasTriggeredTimeUpRef.current && onTimeUpRef.current) {
          hasTriggeredTimeUpRef.current = true;
          onTimeUpRef.current();
        }
      }
    } catch {
      // Offline / network failure: monotonically tick without interrupting (TC-5.5-03)
    }
  }, [attemptId]);

  // Monotonic interval ticker
  useEffect(() => {
    if (isSubmitted) return;

    const timer = setInterval(() => {
      const elapsedSeconds = Math.floor((performance.now() - startPerfRef.current) / 1000);
      const remaining = Math.max(0, anchorRemainingRef.current - elapsedSeconds);
      setSecondsRemaining(remaining);

      if (remaining <= 0 && !hasTriggeredTimeUpRef.current) {
        hasTriggeredTimeUpRef.current = true;
        if (onTimeUpRef.current) {
          onTimeUpRef.current();
        }
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [isSubmitted]);

  // Auto-sync listeners
  useEffect(() => {
    if (!attemptId || isSubmitted) return;

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        void syncNow();
      }
    };

    const handleOnline = () => {
      void syncNow();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('online', handleOnline);

    let periodicTimer: NodeJS.Timeout | null = null;
    if (syncIntervalMs > 0) {
      periodicTimer = setInterval(() => {
        if (document.visibilityState === 'visible') {
          void syncNow();
        }
      }, syncIntervalMs);
    }

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('online', handleOnline);
      if (periodicTimer) clearInterval(periodicTimer);
    };
  }, [attemptId, isSubmitted, syncIntervalMs, syncNow]);

  return {
    secondsRemaining,
    isExpired: secondsRemaining <= 0,
    syncNow,
    formatTimer: (secs?: number) => formatTimeMMSS(secs !== undefined ? secs : secondsRemaining),
  };
};
