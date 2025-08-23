import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { Card, Spinner } from '@nextui-org/react';
import { useAuth } from '@/hooks/useAuth';
import { apiBase } from '../../lib/runtimeApi';

export default function AuthCallback() {
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    handleCallback();
  }, [router.query]);

  const handleCallback = async () => {
    const { code, error: authError } = router.query;

    if (authError) {
      setError('Error en la autenticación. Por favor, intenta nuevamente.');
      setTimeout(() => router.push('/login'), 3000);
      return;
    }

    if (code && typeof code === 'string') {
      try {
        // Enviar código al backend para obtener token
        const response = await fetch(
          `${apiBase()}/api/auth/google/callback?code=${code}`,
          { method: 'GET' }
        );

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