/**
 * TanStack React Query Configuration.
 *
 * Enforces:
 * - 30-second standard staleTime for cached lists.
 * - Dynamic retry strategy (no retry on 4xx errors, maximum 3 retries for transient 5xx/network errors).
 * - Safe refetchOnWindowFocus (suppressed during active exams).
 */

import { QueryClient } from '@tanstack/react-query';
import { ApiError } from './api';

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000, // 30 seconds
        gcTime: 5 * 60_000, // 5 minutes
        retry: (failureCount, error) => {
          if (error instanceof ApiError) {
            // Never retry client errors (400, 401, 403, 404, 422, etc.)
            if (error.status >= 400 && error.status < 500) {
              return false;
            }
          }
          return failureCount < 3;
        },
        refetchOnWindowFocus: (query) => {
          // Disable refetch on window focus for exam attempts or queries marked with disableWindowFocus
          if (query.meta?.disableWindowFocus) {
            return false;
          }
          if (typeof window !== 'undefined' && window.location.pathname.includes('/take')) {
            return false;
          }
          return true;
        },
      },
      mutations: {
        retry: false, // Non-idempotent mutations must never retry automatically
      },
    },
  });
}

export const queryClient = createQueryClient();
