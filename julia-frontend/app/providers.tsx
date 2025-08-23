'use client'

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { apiBase } from '../lib/runtimeApi'
import { NextUIProvider } from '@nextui-org/react'
import { ThemeProvider as NextThemesProvider } from 'next-themes'

interface User {
  id: string; email: string; name: string; picture: string; subscription_tier: string; role?: string;
}
interface AuthContextType {
  user: User | null; loading: boolean; error: string | null; role: string;
  login: (token: string, user: User) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  checkAuth: () => Promise<void>;
  isAuthenticated: boolean; subscriptionTier: string;
}
const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuthContext = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuthContext debe usarse dentro de AuthProvider')
  return ctx
}

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const checkAuth = useCallback(async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
      if (!token) { setUser(null); setLoading(false); return }
  const res = await fetch(`${apiBase()}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      if (res.ok) {
        const data = await res.json(); setUser(data.user); setError(null)
      } else { localStorage.removeItem('access_token'); setUser(null) }
    } catch (e) { setError('Error verificando autenticación'); setUser(null) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { checkAuth() }, [checkAuth])

  const login = useCallback(async (token: string, u: User) => {
    localStorage.setItem('access_token', token); setUser(u); setError(null); setLoading(false)
  }, [])

  const logout = useCallback(async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  if (token) { await fetch(`${apiBase()}/api/auth/logout`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } }) }
    } catch {}
    finally { localStorage.removeItem('access_token'); setUser(null) }
  }, [])

  const refreshToken = useCallback( async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
      if (!token) return
  const res = await fetch(`${apiBase()}/api/auth/refresh`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
      if (res.ok) { const data = await res.json(); localStorage.setItem('access_token', data.access_token); await checkAuth() }
      else { localStorage.removeItem('access_token'); setUser(null) }
    } catch {}
  }, [checkAuth])

  const value: AuthContextType = {
    user,
    loading,
    error,
    role: user?.role || 'student',
    login,
    logout,
    refreshToken,
    checkAuth,
    isAuthenticated: !!user,
    subscriptionTier: user?.subscription_tier || 'free'
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <NextUIProvider>
      <NextThemesProvider attribute="class" defaultTheme="light" themes={['light', 'dark', 'julia-light', 'julia-dark']}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </NextThemesProvider>
    </NextUIProvider>
  )
}

export default Providers
