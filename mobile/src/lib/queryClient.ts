import { QueryClient } from "@tanstack/react-query";

/**
 * Shared TanStack Query client with RESQ defaults.
 *
 * - `staleTime`: 60s — avoids refetching within the first minute
 * - `gcTime`: 5min — garbage-collect stale cache entries
 * - `retry`: 1 — one retry on failure
 * - `refetchOnWindowFocus`: false — mobile apps don't have "window focus"
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 5 * 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});
