// Central helper to build API base URL - hardcoded for production
export function apiBase(): string {
  // Directly return the production API URL
  return 'https://educational-api.kindbeach-3a240fb9.eastus.azurecontainerapps.io';
}

// Convenience to build API root (adds /api if not already)
export function apiRoot(): string {
  const base = apiBase();
  if (!base) return '/api';
  return /\/api$/i.test(base) ? base : `${base}/api`;
}
