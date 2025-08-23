// Central helper to build API base URL without hardcoding localhost
// Uses NEXT_PUBLIC_API_URL if provided at build; otherwise relative ('') so same origin
export function apiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL || '';
  // Remove trailing slash
  return raw.endsWith('/') ? raw.slice(0, -1) : raw;
}
