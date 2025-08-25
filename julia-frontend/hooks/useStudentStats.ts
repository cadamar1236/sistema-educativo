/**
 * Hook personalizado para gestionar estadísticas del estudiante
 * Proporciona datos actualizados y funciones para interactuar con el backend
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { statsService, DashboardStats, StudentStats } from '../lib/statsService';

interface UseStudentStatsOptions {
  studentId?: string; // si falta, el hook espera a que exista
  userEmail?: string; // email del usuario autenticado
  autoRefresh?: boolean;
  refreshInterval?: number; // en milisegundos
  onError?: (error: Error) => void;
}

interface UseStudentStatsReturn {
  // Estados
  dashboardStats: DashboardStats | null;
  studentStats: StudentStats | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  
  // Funciones
  refreshStats: (options?: { force?: boolean }) => Promise<void>;
  updateActivity: (activity: {
    type: 'lesson' | 'exercise' | 'quiz' | 'chat_session';
    subject?: string;
    duration_minutes?: number;
    points_earned?: number;
    success_rate?: number;
  }) => Promise<void>;
  clearError: () => void;
}

export function useStudentStats(options: UseStudentStatsOptions = {}): UseStudentStatsReturn {
  const {
    studentId,
    userEmail,
    autoRefresh = true,
    refreshInterval = 300000, // 5 minutos por defecto
    onError
  } = options;
  // Obtener usuario autenticado
  // Importa el hook de autenticación
  // Si ya está importado en el archivo, úsalo aquí
  let user: any = undefined;
  try {
    // Evita error si el hook no está disponible en contexto
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    user = require('@/hooks/useAuth').useAuth()?.user;
  } catch {}

  // Estados
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [studentStats, setStudentStats] = useState<StudentStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Función para limpiar errores
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Ref para evitar doble fetch inicial en StrictMode (montaje-desmontaje-montaje)
  const didInitialFetchRef = useRef(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const inFlightRef = useRef<Promise<void> | null>(null);

  // Función para cargar estadísticas del dashboard
  const refreshStats = useCallback(async (opts: { force?: boolean } = {}) => {
    if (!studentId) return;
    if (inFlightRef.current) return inFlightRef.current; // evita solapamiento
    if (didInitialFetchRef.current && !opts.force) return; // evita repetición inmediata
    const p = (async () => {
      try {
        setIsLoading(true);
        setError(null);
        const ds = await statsService.getDashboardStats(studentId);
        setDashboardStats(ds);
        setStudentStats(ds.student);
        setLastUpdated(new Date());
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar estadísticas';
        setError(errorMessage);
        if (onError) {
          onError(err instanceof Error ? err : new Error(errorMessage));
        }
      } finally {
        setIsLoading(false);
        didInitialFetchRef.current = true;
        inFlightRef.current = null;
      }
    })();
    inFlightRef.current = p;
    return p;
  }, [studentId, onError]);

  // Función para actualizar actividad del estudiante
  const updateActivity = useCallback(async (activity: {
    type: 'lesson' | 'exercise' | 'quiz' | 'chat_session';
    subject?: string;
    duration_minutes?: number;
    points_earned?: number;
    success_rate?: number;
  }) => {
    try {
      if (!studentId) return;
      // Incluye el email del usuario en la actividad
      const activityWithEmail = { ...activity, user_email: userEmail || studentId };
      await statsService.updateStudentActivity(studentId, activityWithEmail);
      await refreshStats({ force: true });
      console.log('✅ Actividad actualizada:', activityWithEmail);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error actualizando actividad';
      setError(errorMessage);
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMessage));
      }
      console.error('❌ Error actualizando actividad:', err);
    }
  }, [studentId, refreshStats, onError, userEmail]);

  // Efecto para carga inicial
  useEffect(() => {
    if (!studentId) return;
    // Primera carga forzada
    refreshStats({ force: true });
  }, [studentId, refreshStats]);

  // Efecto para actualización automática
  useEffect(() => {
    if (!autoRefresh || !studentId) return;
    // Evitar crear múltiples intervalos (StrictMode / remounts)
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    intervalRef.current = setInterval(() => {
      refreshStats();
    }, refreshInterval);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
    };
  }, [refreshStats, autoRefresh, refreshInterval, studentId]);

  return {
    dashboardStats,
    studentStats,
    isLoading,
    error,
    lastUpdated,
    refreshStats,
    updateActivity,
    clearError
  };
}

// Hook simplificado solo para estadísticas del estudiante
export function useStudentBasicStats(studentId?: string) {
  const [stats, setStats] = useState<StudentStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setIsLoading(true);
        if (!studentId) { setIsLoading(false); return; }
        const data = await statsService.getStudentStats(studentId);
        setStats(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error cargando estadísticas');
      } finally {
        setIsLoading(false);
      }
    };
    if (studentId) loadStats(); else setIsLoading(false);
  }, [studentId]);

  return { stats, isLoading, error };
}

// Hook para recomendaciones personalizadas
export function usePersonalizedRecommendations(studentId?: string) {
  const [recommendations, setRecommendations] = useState<DashboardStats['recommendations']>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshRecommendations = useCallback(async () => {
    try {
      setIsLoading(true);
      if (!studentId) { setIsLoading(false); return; }
      const data = await statsService.getPersonalizedRecommendations(studentId);
      setRecommendations(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando recomendaciones');
    } finally {
      setIsLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    if (studentId) refreshRecommendations(); else setIsLoading(false);
  }, [refreshRecommendations, studentId]);

  return { 
    recommendations, 
    isLoading, 
    error, 
    refreshRecommendations 
  };
}
