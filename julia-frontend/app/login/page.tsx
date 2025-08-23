'use client';
import React, { useState, useEffect } from 'react';
import { apiBase } from '../../lib/runtimeApi';
import { Button, Card } from '@nextui-org/react';
import { useRouter } from 'next/navigation';

// Forzar render estático compatible con output: 'export'
export const dynamic = 'force-static';

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Guardamos el parámetro next= de forma manual (solo en cliente) para no depender de useSearchParams (que marca la ruta como dinámica y rompe export)
  const [nextParam, setNextParam] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        const url = new URL(window.location.href);
        const val = url.searchParams.get('next');
        if (val && val.startsWith('/')) setNextParam(val);
      } catch {}
    }
  }, []);

  const startGoogle = async () => {
    try {
      setLoading(true);
      setError(null);
  // call backend to get Google auth URL
	const res = await fetch(`${apiBase()}/api/auth/google/login`);
      if (!res.ok) throw new Error('No se pudo iniciar autenticación');
      const data = await res.json();
      if (data.auth_url) {
        // Determine desired redirect (prioritize explicit next= param, else keep existing stored value, else dashboard)
        if (typeof window !== 'undefined') {
          const desired = nextParam && nextParam.startsWith('/') ? nextParam : (localStorage.getItem('auth_redirect') || '/dashboard');
          localStorage.setItem('auth_redirect', desired);
          if (data.redirect_uri_used) {
            sessionStorage.setItem('oauth_redirect_uri', data.redirect_uri_used);
          }
        }
        window.location.href = data.auth_url;
      } else {
        throw new Error('Respuesta inválida del servidor');
      }
    } catch (e: any) {
      setError(e.message || 'Error iniciando autenticación');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="p-8 w-full max-w-md space-y-4">
        <h1 className="text-2xl font-semibold text-center">Iniciar Sesión</h1>
        <p className="text-sm text-gray-500 text-center">Accede con tu cuenta de Google para continuar.</p>
        {error && <div className="text-sm text-red-500 text-center">{error}</div>}
        <Button color="primary" onPress={startGoogle} isLoading={loading} disabled={loading}>
          {loading ? 'Redirigiendo...' : 'Continuar con Google'}
        </Button>
      </Card>
    </div>
  );
}
