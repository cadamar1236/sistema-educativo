// Central helper to build API base URL without hardcoding localhost
// Always prefer NEXT_PUBLIC_API_URL if set; otherwise use current origin
export function apiBase(): string {
  // Primera prioridad: variable de entorno compilada en tiempo de build
  let envUrl = process.env.NEXT_PUBLIC_API_URL || '';
  if (envUrl) {
    envUrl = envUrl.replace(/\/$/, '');
    // Si no es localhost, usar directamente
    if (!/localhost|127\./i.test(envUrl)) {
      return envUrl;
    }
  }
  
  // Fallback para desarrollo o cuando no hay NEXT_PUBLIC_API_URL válida
  if (typeof window !== 'undefined') {
    return window.location.origin.replace(/\/$/, '');
  }
  
  // Durante build/SSR: usar relativo
  return '';
}

// Convenience to build API root (adds /api if not already)
export function apiRoot(): string {
  const base = apiBase();
  if (!base) return '/api';
  return /\/api$/i.test(base) ? base : `${base}/api`;
}
