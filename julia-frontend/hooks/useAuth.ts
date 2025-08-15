import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';

interface User {
  id: string;
  email: string;
  name: string;
  picture: string;
  subscription_tier: string;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null
  });
  const router = useRouter();

  // Verificar si hay token guardado al cargar
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        setAuthState({ user: null, loading: false, error: null });
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAuthState({
          user: data.user,
          loading: false,
          error: null
        });
      } else {
        // Token inválido o expirado
        localStorage.removeItem('access_token');
        setAuthState({ user: null, loading: false, error: null });
      }
    } catch (error) {
      console.error('Error verificando autenticación:', error);
      setAuthState({
        user: null,
        loading: false,
        error: 'Error verificando autenticación'
      });
    }
  };

  const login = useCallback(async (token: string, user: User) => {
    localStorage.setItem('access_token', token);
    setAuthState({
      user,
      loading: false,
      error: null
    });
  }, []);

  const logout = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (token) {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }
    } catch (error) {
      console.error('Error durante logout:', error);
    } finally {
      localStorage.removeItem('access_token');
      setAuthState({
        user: null,
        loading: false,
        error: null
      });
      router.push('/');
    }
  }, [router]);

  const refreshToken = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        throw new Error('No hay token para refrescar');
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        await checkAuth();
      } else {
        throw new Error('Error refrescando token');
      }
    } catch (error) {
      console.error('Error refrescando token:', error);
      logout();
    }
  }, [logout]);

  const requireAuth = useCallback((requiredTier?: string) => {
    if (!authState.user) {
      router.push('/login');
      return false;
    }

    if (requiredTier) {
      const tierLevels: Record<string, number> = {
        'free': 0,
        'basic': 1,
        'pro': 2,
        'enterprise': 3
      };

      const userLevel = tierLevels[authState.user.subscription_tier] || 0;
      const requiredLevel = tierLevels[requiredTier] || 0;

      if (userLevel < requiredLevel) {
        router.push('/subscription');
        return false;
      }
    }

    return true;
  }, [authState.user, router]);

  return {
    user: authState.user,
    loading: authState.loading,
    error: authState.error,
    login,
    logout,
    refreshToken,
    requireAuth,
    checkAuth,
    isAuthenticated: !!authState.user,
    subscriptionTier: authState.user?.subscription_tier || 'free'
  };
};