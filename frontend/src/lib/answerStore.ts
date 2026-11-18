/**
 * AnswerStore - Offline Outbox Local Storage Queue for Exam Answers.
 *
 * Implements:
 * - Persistent queuing in localStorage with SafeStorage memory fallback (TC-5.6-06).
 * - Monotonic client_seq serialization: higher client_seq replaces older pending items.
 * - Cross-tab synchronization via window 'storage' events (TC-5.6-05).
 * - Subscription mechanism for reactive UI updates and queue synchronization.
 */

import { safeStorage } from './storage';

export interface OutboxItem {
  attemptId: string;
  questionId: string;
  value: Record<string, unknown>;
  client_seq: number;
  timestamp: number;
  retries: number;
  status: 'pending' | 'syncing' | 'failed';
}

const OUTBOX_PREFIX = 'quiz_exam_outbox_';

export function getOutboxKey(attemptId: string): string {
  return `${OUTBOX_PREFIX}${attemptId}`;
}

type OutboxSubscriber = (items: OutboxItem[]) => void;
type FallbackSubscriber = (isFallback: boolean) => void;

class AnswerStore {
  private subscribers = new Map<string, Set<OutboxSubscriber>>();
  private fallbackSubscribers = new Set<FallbackSubscriber>();
  private memoryCache = new Map<string, OutboxItem[]>();

  constructor() {
    this.initStorageListener();
  }

  private initStorageListener() {
    if (typeof window === 'undefined') return;

    window.addEventListener('storage', (event: StorageEvent) => {
      if (!event.key || !event.key.startsWith(OUTBOX_PREFIX)) return;

      const attemptId = event.key.replace(OUTBOX_PREFIX, '');
      const items = this.getOutbox(attemptId);
      this.memoryCache.set(attemptId, items);
      this.notifySubscribers(attemptId, items);
    });
  }

  public getOutbox(attemptId: string): OutboxItem[] {
    if (!attemptId) return [];

    try {
      const raw = safeStorage.getItem(getOutboxKey(attemptId));
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        this.memoryCache.set(attemptId, parsed);
        return parsed;
      }
      return [];
    } catch {
      return this.memoryCache.get(attemptId) || [];
    }
  }

  public setOutbox(attemptId: string, items: OutboxItem[]): void {
    if (!attemptId) return;

    this.memoryCache.set(attemptId, items);

    try {
      safeStorage.setItem(getOutboxKey(attemptId), JSON.stringify(items));
      if (safeStorage.isMemoryFallback()) {
        this.notifyFallbackSubscribers(true);
      }
    } catch {
      safeStorage.setFallbackMode(true);
      this.notifyFallbackSubscribers(true);
    }

    this.notifySubscribers(attemptId, items);
  }

  public enqueue(entry: {
    attemptId: string;
    questionId: string;
    value: Record<string, unknown>;
    client_seq: number;
  }): OutboxItem {
    const { attemptId, questionId, value, client_seq } = entry;
    const currentQueue = this.getOutbox(attemptId);

    const existingIdx = currentQueue.findIndex((item) => item.questionId === questionId);
    let resolvedItem: OutboxItem;

    if (existingIdx !== -1) {
      const existing = currentQueue[existingIdx];
      // Only update if incoming client_seq is greater or equal
      if (client_seq >= existing.client_seq) {
        resolvedItem = {
          ...existing,
          value,
          client_seq,
          timestamp: Date.now(),
          retries: 0,
          status: 'pending',
        };
        currentQueue[existingIdx] = resolvedItem;
      } else {
        resolvedItem = existing;
      }
    } else {
      resolvedItem = {
        attemptId,
        questionId,
        value,
        client_seq,
        timestamp: Date.now(),
        retries: 0,
        status: 'pending',
      };
      currentQueue.push(resolvedItem);
    }

    this.setOutbox(attemptId, currentQueue);
    return resolvedItem;
  }

  public remove(attemptId: string, questionId: string, client_seq?: number): void {
    const currentQueue = this.getOutbox(attemptId);
    const updated = currentQueue.filter((item) => {
      if (item.questionId !== questionId) return true;
      if (client_seq !== undefined && item.client_seq > client_seq) {
        // Newer local answer exists, keep it
        return true;
      }
      return false;
    });

    this.setOutbox(attemptId, updated);
  }

  public updateStatus(
    attemptId: string,
    questionId: string,
    status: 'pending' | 'syncing' | 'failed',
    incrementRetries = false
  ): void {
    const currentQueue = this.getOutbox(attemptId);
    const item = currentQueue.find((q) => q.questionId === questionId);
    if (!item) return;

    item.status = status;
    if (incrementRetries) {
      item.retries += 1;
    }

    this.setOutbox(attemptId, currentQueue);
  }

  public clear(attemptId: string): void {
    this.memoryCache.delete(attemptId);
    try {
      safeStorage.removeItem(getOutboxKey(attemptId));
    } catch {
      // ignore
    }
    this.notifySubscribers(attemptId, []);
  }

  public getPendingCount(attemptId: string): number {
    return this.getOutbox(attemptId).length;
  }

  public isMemoryFallback(): boolean {
    return safeStorage.isMemoryFallback();
  }

  public subscribe(attemptId: string, listener: OutboxSubscriber): () => void {
    if (!this.subscribers.has(attemptId)) {
      this.subscribers.set(attemptId, new Set());
    }

    const set = this.subscribers.get(attemptId)!;
    set.add(listener);

    // Initial trigger
    listener(this.getOutbox(attemptId));

    return () => {
      set.delete(listener);
      if (set.size === 0) {
        this.subscribers.delete(attemptId);
      }
    };
  }

  public onStorageFallback(listener: FallbackSubscriber): () => void {
    this.fallbackSubscribers.add(listener);
    listener(this.isMemoryFallback());
    return () => {
      this.fallbackSubscribers.delete(listener);
    };
  }

  private notifySubscribers(attemptId: string, items: OutboxItem[]): void {
    const set = this.subscribers.get(attemptId);
    if (set) {
      set.forEach((fn) => {
        try {
          fn(items);
        } catch {
          // ignore error in subscriber
        }
      });
    }
  }

  private notifyFallbackSubscribers(isFallback: boolean): void {
    this.fallbackSubscribers.forEach((fn) => {
      try {
        fn(isFallback);
      } catch {
        // ignore
      }
    });
  }
}

export const answerStore = new AnswerStore();
