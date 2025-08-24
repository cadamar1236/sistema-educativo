// Central helper to build API base URL without hardcoding localhost
// Prefers NEXT_PUBLIC_API_URL if it is not localhost; otherwise derives from window.location at runtime.
export function apiBase(): string {
  let envUrl = process.env.NEXT_PUBLIC_API_URL || '';
  if (envUrl) {
    envUrl = envUrl.replace(/\/$/, '');
  }
  const isLocalEnv = !envUrl || /localhost|127\./i.test(envUrl);
  if (isLocalEnv) {
    if (typeof window !== 'undefined') {
      // Use current origin in browser (production or preview environment)
      return window.location.origin.replace(/\/$/, '');
    }
    // During build or SSR fallback to empty so fetch('/api/...') same-origin
    return '';
  }
  return envUrl;
}

// Convenience to build API root (adds /api if not already)
export function apiRoot(): string {
  const base = apiBase();
  if (!base) return '/api';
  return /\/api$/i.test(base) ? base : `${base}/api`;
}
