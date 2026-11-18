/**
 * useOfflineOutbox - Offline Outbox Synchronization Hook (Step 5.6).
 *
 * Implements:
 * - Immediate local queuing with optimistic UI state (TC-5.6-01).
 * - Automatic background sequential flushing with exponential backoff on network recovery (TC-5.6-02).
 * - In-place re-authentication pause & resume on 401 (TC-5.6-04).
 * - Multi-tab storage sync without collisions (TC-5.6-05).
 * - Storage fallback monitoring (TC-5.6-06).
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { answerStore, OutboxItem } from '../lib/answerStore';
import { studentApi } from '../lib/studentApi';
import { ApiError } from '../lib/api';

export type QuestionSaveStatus = 'saved' | 'saving' | 'pending' | 'error';

interface UseOfflineOutboxOptions {
  attemptId: string | undefined;
  isSubmitted: boolean;
  onReAuthRequired: () => void;
  onAttemptClosed?: () => void;
}

export function useOfflineOutbox({
  attemptId,
  isSubmitted,
  onReAuthRequired,
  onAttemptClosed,
}: UseOfflineOutboxOptions) {
  const [outbox, setOutbox] = useState<OutboxItem[]>(() =>
    attemptId ? answerStore.getOutbox(attemptId) : []
  );
  const [isOnline, setIsOnline] = useState<boolean>(() =>
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [isStorageFallback, setIsStorageFallback] = useState<boolean>(() =>
    answerStore.isMemoryFallback()
  );
  const [saveStatusMap, setSaveStatusMap] = useState<Record<string, QuestionSaveStatus>>({});

  const isPausedForAuthRef = useRef<boolean>(false);
  const isSyncingRef = useRef<boolean>(false);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Subscribe to AnswerStore changes and cross-tab storage events
  useEffect(() => {
    if (!attemptId) return;

    const unsubscribe = answerStore.subscribe(attemptId, (items) => {
      setOutbox(items);

      // Reflect pending items in saveStatusMap
      setSaveStatusMap((prev) => {
        const next = { ...prev };
        items.forEach((it) => {
          if (next[it.questionId] !== 'saved') {
            next[it.questionId] = it.status === 'syncing' ? 'saving' : 'pending';
          }
        });
        return next;
      });
    });

    const unsubscribeFallback = answerStore.onStorageFallback((fallback) => {
      setIsStorageFallback(fallback);
    });

    return () => {
      unsubscribe();
      unsubscribeFallback();
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [attemptId]);

  // Flush pending outbox entries sequentially
  const flush = useCallback(async () => {
    if (!attemptId || isSubmitted || isSyncingRef.current || isPausedForAuthRef.current) {
      return;
    }

    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      setIsOnline(false);
      return;
    }

    const currentItems = answerStore.getOutbox(attemptId);
    if (currentItems.length === 0) {
      return;
    }

    isSyncingRef.current = true;
    setIsSyncing(true);

    try {
      for (const item of currentItems) {
        if (isPausedForAuthRef.current) break;

        setSaveStatusMap((prev) => ({ ...prev, [item.questionId]: 'saving' }));
        answerStore.updateStatus(attemptId, item.questionId, 'syncing');

        try {
          const res = await studentApi.saveAnswer(
            attemptId,
            item.questionId,
            item.value,
            item.client_seq
          );

          if (res.status === 'saved' || res.status === 'ignored') {
            answerStore.remove(attemptId, item.questionId, item.client_seq);
            setSaveStatusMap((prev) => ({ ...prev, [item.questionId]: 'saved' }));
          }
        } catch (err: unknown) {
          const is401 =
            (err instanceof ApiError && err.status === 401) ||
            (err instanceof Error && err.message.includes('401'));
          const is409 =
            (err instanceof ApiError && (err.status === 409 || err.code === 'attempt_closed')) ||
            (err instanceof Error &&
              (err.message.includes('409') || err.message.includes('attempt_closed')));

          if (is401) {
            isPausedForAuthRef.current = true;
            answerStore.updateStatus(attemptId, item.questionId, 'pending');
            setSaveStatusMap((prev) => ({ ...prev, [item.questionId]: 'pending' }));
            onReAuthRequired();
            break;
          }

          if (is409) {
            answerStore.clear(attemptId);
            onAttemptClosed?.();
            break;
          }

          // Network or server error: mark failed and schedule exponential backoff
          answerStore.updateStatus(attemptId, item.questionId, 'failed', true);
          setSaveStatusMap((prev) => ({ ...prev, [item.questionId]: 'pending' }));

          const backoffDelay = Math.min(1000 * Math.pow(2, item.retries + 1), 10000);
          if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
          retryTimeoutRef.current = setTimeout(() => {
            void flush();
          }, backoffDelay);

          break; // Stop further items until current retry succeeds
        }
      }
    } finally {
      isSyncingRef.current = false;
      setIsSyncing(false);
    }
  }, [attemptId, isSubmitted, onReAuthRequired, onAttemptClosed]);

  // Online / offline listeners
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      void flush();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial check and flush if pending items exist
    if (attemptId && answerStore.getPendingCount(attemptId) > 0) {
      void flush();
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [attemptId, flush]);

  // Optimistic answer save
  const saveAnswerOptimistic = useCallback(
    (questionId: string, value: Record<string, unknown>, client_seq: number) => {
      if (!attemptId || isSubmitted) return;

      answerStore.enqueue({
        attemptId,
        questionId,
        value,
        client_seq,
      });

      const onlineNow = typeof navigator !== 'undefined' ? navigator.onLine : true;
      setSaveStatusMap((prev) => ({
        ...prev,
        [questionId]: onlineNow ? 'saving' : 'pending',
      }));

      if (onlineNow && !isPausedForAuthRef.current) {
        if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
        void flush();
      }
    },
    [attemptId, isSubmitted, flush]
  );

  // Manual retry trigger (e.g. from offline banner button)
  const manualRetrySync = useCallback(() => {
    isPausedForAuthRef.current = false;
    if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
    void flush();
  }, [flush]);

  // Resume after re-authentication
  const resumeAfterAuth = useCallback(() => {
    isPausedForAuthRef.current = false;
    if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
    void flush();
  }, [flush]);

  return {
    outbox,
    outboxCount: outbox.length,
    isOnline,
    isSyncing,
    isStorageFallback,
    saveStatusMap,
    saveAnswerOptimistic,
    manualRetrySync,
    resumeAfterAuth,
    flush,
  };
}
