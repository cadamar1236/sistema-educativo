'use client';
import React, { useState } from 'react';
import { apiBase } from '../../lib/runtimeApi';
import { Button, Card } from '@nextui-org/react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const nextParam = searchParams?.get('next');

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
