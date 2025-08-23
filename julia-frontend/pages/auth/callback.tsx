import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { Card, Spinner } from '@nextui-org/react';
import { useAuth } from '@/hooks/useAuth';
import { apiBase } from '../../lib/runtimeApi';

// Export estático: la página es puramente cliente y maneja query en runtime
export const dynamic = 'force-static';

export default function AuthCallback() {
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    handleCallback();
  }, [router.query]);

  const handleCallback = async () => {
  const { code, error: authError } = router.query;

    // Si no hay code y no hay token almacenado, reintentar flujo
    if (!code) {
      const existing = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      if (!existing) {
        // Forzar retorno al login preservando destino
        const stored = localStorage.getItem('auth_redirect') || '/dashboard';
        router.replace(`/login?next=${encodeURIComponent(stored)}`);
      }
      return;
    }

    if (authError) {
      setError('Error en la autenticación. Por favor, intenta nuevamente.');
      setTimeout(() => router.push('/login'), 3000);
      return;
    }

    if (code && typeof code === 'string') {
      try {
        // Enviar código al backend para obtener token
  const redirectOverride = typeof window !== 'undefined' ? sessionStorage.getItem('oauth_redirect_uri') : null;
  const url = new URL(`${apiBase()}/api/auth/google/callback`);
  url.searchParams.set('code', code as string);
  if (redirectOverride) url.searchParams.set('redirect_uri', redirectOverride);
  console.log('[OAuth] Calling backend callback', { url: url.toString(), redirectOverride });
  const response = await fetch(url.toString(), { method: 'GET' });

        if (response.ok) {
          const data = await response.json();
          
          // Guardar token y usuario
          await login(data.access_token, data.user);
          
          // Determinar destino final
          const stored = localStorage.getItem('auth_redirect');
          let redirectTo = stored;
          if (!redirectTo) {
            // Elegir dashboard según rol
            redirectTo = data.user?.role === 'teacher' ? '/dashboard/teacher' : '/dashboard';
          } else {
            // Si hay conflicto rol vs destino (ej: teacher y redirect genérico), ajustar
            if (data.user?.role === 'teacher' && redirectTo === '/dashboard') {
              redirectTo = '/dashboard/teacher';
            }
            if (data.user?.role !== 'teacher' && redirectTo === '/dashboard/teacher') {
              redirectTo = '/dashboard';
            }
          }
          localStorage.removeItem('auth_redirect');
          console.log('[OAuth] Redirecting to', redirectTo);
          router.push(redirectTo);
        } else {
          throw new Error('Error procesando autenticación');
        }
      } catch (error) {
        console.error('Error en callback:', error);
        setError('Error procesando la autenticación. Por favor, intenta nuevamente.');
        setTimeout(() => router.push('/login'), 3000);
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="p-8 max-w-md w-full">
        {error ? (
          <div className="text-center">
            <div className="text-red-500 mb-4">⚠️</div>
            <h2 className="text-xl font-semibold mb-2">Error de Autenticación</h2>
            <p className="text-gray-600">{error}</p>
            <p className="text-sm text-gray-500 mt-4">Redirigiendo...</p>
          </div>
        ) : (
          <div className="text-center">
            <Spinner size="lg" color="primary" />
            <h2 className="text-xl font-semibold mt-4 mb-2">Procesando autenticación</h2>
            <p className="text-gray-600">Por favor espera un momento...</p>
          </div>
        )}
      </Card>
    </div>
  );
}