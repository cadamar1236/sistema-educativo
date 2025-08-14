/**
 * Hook personalizado para gestionar estadísticas del estudiante
 * Proporciona datos actualizados y funciones para interactuar con el backend
 */

import { useState, useEffect, useCallback } from 'react';
import { statsService, DashboardStats, StudentStats } from '../lib/statsService';

interface UseStudentStatsOptions {
  studentId?: string;
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
  refreshStats: () => Promise<void>;
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
    studentId = 'student_001',
    autoRefresh = true,
    refreshInterval = 300000, // 5 minutos por defecto
    onError
  } = options;

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

  // Función para cargar estadísticas del dashboard
  const refreshStats = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Cargar estadísticas del dashboard (incluye datos del estudiante)
      const dashboardData = await statsService.getDashboardStats(studentId);
      setDashboardStats(dashboardData);
      setStudentStats(dashboardData.student);
      
      setLastUpdated(new Date());
      
      console.log('✅ Estadísticas actualizadas:', {
        student: dashboardData.student.name,
        progress: dashboardData.student.overall_progress,
        streak: dashboardData.student.streak_days
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido al cargar estadísticas';
      setError(errorMessage);
      
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMessage));
      }
      
      console.error('❌ Error cargando estadísticas:', err);
    } finally {
      setIsLoading(false);
    }
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
      await statsService.updateStudentActivity(studentId, activity);
      
      // Refrescar estadísticas después de actualizar actividad
      await refreshStats();
      
      console.log('✅ Actividad actualizada:', activity);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error actualizando actividad';
      setError(errorMessage);
      
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMessage));
      }
      
      console.error('❌ Error actualizando actividad:', err);
    }
  }, [studentId, refreshStats, onError]);

  // Efecto para carga inicial
  useEffect(() => {
    refreshStats();
  }, [refreshStats]);

  // Efecto para actualización automática
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      refreshStats();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshStats, autoRefresh, refreshInterval]);

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
export function useStudentBasicStats(studentId: string = 'student_001') {
  const [stats, setStats] = useState<StudentStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setIsLoading(true);
        const data = await statsService.getStudentStats(studentId);
        setStats(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error cargando estadísticas');
      } finally {
        setIsLoading(false);
      }
    };

    loadStats();
  }, [studentId]);

  return { stats, isLoading, error };
}

// Hook para recomendaciones personalizadas
export function usePersonalizedRecommendations(studentId: string = 'student_001') {
  const [recommendations, setRecommendations] = useState<DashboardStats['recommendations']>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshRecommendations = useCallback(async () => {
    try {
      setIsLoading(true);
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
    refreshRecommendations();
  }, [refreshRecommendations]);

  return { 
    recommendations, 
    isLoading, 
    error, 
    refreshRecommendations 
  };
}
