/**
 * Safe local storage wrapper with in-memory fallback.
 *
 * Handles private browsing mode, restricted iframes, or quota exceeded errors
 * without crashing the application.
 */

const TOKEN_KEY = 'quiz_auth_token';
const USER_KEY = 'quiz_auth_user';
const OUTBOX_KEY = 'quiz_exam_outbox';

class SafeStorage {
  private memoryStore: Map<string, string> = new Map();
  private isFallback = false;

  constructor() {
    this.checkAvailability();
  }

  /**
   * Probes window.localStorage availability.
   * Falls back to memory if blocked or restricted.
   */
  public checkAvailability(): boolean {
    try {
      if (typeof window === 'undefined' || !window.localStorage) {
        this.isFallback = true;
        return false;
      }
      const testKey = '__storage_probe__';
      window.localStorage.setItem(testKey, testKey);
      window.localStorage.removeItem(testKey);
      this.isFallback = false;
      return true;
    } catch {
      this.isFallback = true;
      return false;
    }
  }

  /**
   * Returns true if localStorage is blocked and currently using in-memory fallback.
   */
  public isMemoryFallback(): boolean {
    return this.isFallback;
  }

  /**
   * Explicitly sets fallback mode (useful for testing or forced memory mode).
   */
  public setFallbackMode(enabled: boolean): void {
    this.isFallback = enabled;
  }

  public getItem(key: string): string | null {
    if (this.isFallback) {
      return this.memoryStore.get(key) ?? null;
    }
    try {
      return window.localStorage.getItem(key);
    } catch {
      this.isFallback = true;
      return this.memoryStore.get(key) ?? null;
    }
  }

  public setItem(key: string, value: string): void {
    if (this.isFallback) {
      this.memoryStore.set(key, value);
      return;
    }
    try {
      window.localStorage.setItem(key, value);
    } catch {
      this.isFallback = true;
      this.memoryStore.set(key, value);
    }
  }

  public removeItem(key: string): void {
    if (this.isFallback) {
      this.memoryStore.delete(key);
      return;
    }
    try {
      window.localStorage.removeItem(key);
    } catch {
      this.isFallback = true;
      this.memoryStore.delete(key);
    }
  }

  public clear(): void {
    this.memoryStore.clear();
    if (!this.isFallback) {
      try {
        window.localStorage.clear();
      } catch {
        this.isFallback = true;
      }
    }
  }

  // Token management helpers
  public getToken(): string | null {
    return this.getItem(TOKEN_KEY);
  }

  public setToken(token: string): void {
    this.setItem(TOKEN_KEY, token);
  }

  public removeToken(): void {
    this.removeItem(TOKEN_KEY);
  }

  // Outbox management helpers (for offline exam draft synchronization)
  public getOutbox(): string | null {
    return this.getItem(OUTBOX_KEY);
  }

  public setOutbox(data: string): void {
    this.setItem(OUTBOX_KEY, data);
  }

  public removeOutbox(): void {
    this.removeItem(OUTBOX_KEY);
  }

  // User cache helpers
  public getUser(): string | null {
    return this.getItem(USER_KEY);
  }

  public setUser(userData: string): void {
    this.setItem(USER_KEY, userData);
  }

  public removeUser(): void {
    this.removeItem(USER_KEY);
  }
}

export const safeStorage = new SafeStorage();
