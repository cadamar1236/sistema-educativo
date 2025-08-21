/**
 * Servicio para obtener estadísticas del estudiante desde el backend
 * Maneja métricas de progreso, actividad y rendimiento académico
 */

export interface StudentStats {
  // Datos básicos del estudiante
  student_id: string;
  name: string;
  grade: string;
  current_level: string;
  
  // Progreso y rendimiento
  overall_progress: number;
  weekly_goal: number;
  weekly_progress: number;
  streak_days: number;
  
  // Actividad diaria
  today_activity: {
    lessons_completed: number;
    exercises_completed: number;
    points_earned: number;
    study_time_minutes: number;
    sessions_count: number;
  };
  
  // Clases programadas
  upcoming_classes: Array<{
    subject: string;
    time: string;
    teacher: string;
    duration_minutes: number;
    classroom?: string;
  }>;
  
  // Logros recientes
  recent_achievements: Array<{
    title: string;
    description: string;
    date: string;
    points: number;
    badge_type: string;
  }>;
  
  // Insignias desbloqueadas
  badges: Array<{
    id: string;
    name: string;
    description: string;
    icon: string;
    unlocked_date: string;
    category: string;
  }>;
  
  // Estadísticas por materia
  subject_stats: Array<{
    subject: string;
    progress: number;
    grade: number;
    time_spent_hours: number;
    exercises_completed: number;
    last_activity: string;
  }>;
  
  // Tendencias y análisis
  trends: {
    weekly_performance: number[];
    best_study_time: string;
    most_improved_subject: string;
    needs_attention: string[];
  };
}

export interface DashboardStats {
  student: StudentStats;
  system_status: {
    agents_active: number;
    total_agents: number;
    last_interaction: string;
    system_health: 'good' | 'warning' | 'error';
  };
  recommendations: Array<{
    type: 'study_plan' | 'focus_area' | 'motivation' | 'health';
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
  }>;
}

class StatsService {
  private baseUrl: string;

  constructor(baseUrl: string = '') {
    const envBase = (typeof process !== 'undefined' ? (process as any).env?.NEXT_PUBLIC_API_URL : '') || '';
    const cleaned = (baseUrl || envBase).replace(/\/$/, '');
    this.baseUrl = cleaned; // puede estar vacío para usar rutas relativas (/api)
  }

  /**
   * Obtiene las estadísticas completas del dashboard para un estudiante
   */
  async getDashboardStats(studentId: string): Promise<DashboardStats> {
    if (!studentId) throw new Error('studentId requerido');
    try {
      const apiRoot = this.baseUrl
        ? (/\/api$/.test(this.baseUrl) ? this.baseUrl : `${this.baseUrl}/api`)
        : '/api';

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 6000); // 6s timeout

      const response = await fetch(`${apiRoot}/students/${studentId}/dashboard-stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      });
      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data: DashboardStats = await response.json();
      
      console.log('✅ Estadísticas del dashboard obtenidas:', data);
      
      return data;
    } catch (error: any) {
      console.error('Error obteniendo estadísticas del dashboard:', error?.message || error);
      
      // Fallback con datos simulados si el backend no está disponible
      return this.getFallbackStats(studentId);
    }
  }

  /**
   * Obtiene estadísticas específicas del estudiante
   */
  async getStudentStats(studentId: string): Promise<StudentStats> {
    if (!studentId) throw new Error('studentId requerido');
    try {
      const apiRoot = this.baseUrl
        ? (/\/api$/.test(this.baseUrl) ? this.baseUrl : `${this.baseUrl}/api`)
        : '/api';
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 6000);
      const response = await fetch(`${apiRoot}/students/${studentId}/stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      });
      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data: StudentStats = await response.json();
      
      console.log('✅ Estadísticas del estudiante obtenidas:', data);
      
      return data;
    } catch (error: any) {
      console.error('Error obteniendo estadísticas del estudiante:', error?.message || error);
      throw error;
    }
  }

  /**
   * Actualiza las estadísticas del estudiante (para cuando complete actividades)
   */
  async updateStudentActivity(
    studentId: string, 
    activity: {
      type: 'lesson' | 'exercise' | 'quiz' | 'chat_session';
      subject?: string;
      duration_minutes?: number;
      points_earned?: number;
      success_rate?: number;
    }
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/students/${studentId}/activity`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          activity,
          timestamp: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      console.log('✅ Actividad del estudiante actualizada:', activity);
    } catch (error) {
      console.error('Error actualizando actividad del estudiante:', error);
      throw error;
    }
  }

  /**
   * Obtiene recomendaciones personalizadas para el estudiante
   */
  async getPersonalizedRecommendations(studentId: string): Promise<DashboardStats['recommendations']> {
    try {
      const apiRoot = this.baseUrl
        ? (/\/api$/.test(this.baseUrl) ? this.baseUrl : `${this.baseUrl}/api`)
        : '/api';
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 6000);
      const response = await fetch(`${apiRoot}/students/${studentId}/recommendations`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      });
      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      console.log('✅ Recomendaciones personalizadas obtenidas:', data);
      
      return data.recommendations || [];
    } catch (error: any) {
      console.error('Error obteniendo recomendaciones:', error?.message || error);
      return [];
    }
  }

  /**
   * Datos de fallback cuando el backend no está disponible
   */
  private getFallbackStats(studentId: string): DashboardStats {
    const now = new Date();
    const today = now.toISOString().split('T')[0];
    
    return {
      student: {
  student_id: studentId,
  name: studentId,
        grade: '10° Grado',
        current_level: 'Intermedio Alto',
        overall_progress: 78,
        weekly_goal: 85,
        weekly_progress: 72,
        streak_days: 12,
        today_activity: {
          lessons_completed: 3,
          exercises_completed: 7,
          points_earned: 245,
          study_time_minutes: 95,
          sessions_count: 4
        },
        upcoming_classes: [
          {
            subject: 'Matemáticas Avanzadas',
            time: '10:00 AM',
            teacher: 'Prof. García',
            duration_minutes: 50,
            classroom: 'Aula 204'
          },
          {
            subject: 'Literatura',
            time: '11:30 AM',
            teacher: 'Prof. Martínez',
            duration_minutes: 45,
            classroom: 'Aula 101'
          },
          {
            subject: 'Química',
            time: '2:00 PM',
            teacher: 'Prof. López',
            duration_minutes: 60,
            classroom: 'Lab. 3'
          }
        ],
        recent_achievements: [
          {
            title: 'Racha de Estudio',
            description: '12 días consecutivos estudiando',
            date: today,
            points: 50,
            badge_type: 'streak'
          },
          {
            title: 'Maestro de Álgebra',
            description: 'Completó todos los ejercicios de álgebra',
            date: new Date(now.getTime() - 86400000).toISOString().split('T')[0],
            points: 100,
            badge_type: 'mastery'
          },
          {
            title: 'Participación Activa',
            description: 'Participó en 5 sesiones de chat con agentes',
            date: new Date(now.getTime() - 172800000).toISOString().split('T')[0],
            points: 75,
            badge_type: 'engagement'
          }
        ],
        badges: [
          {
            id: 'streak_master',
            name: 'Maestro de la Constancia',
            description: 'Estudió 10 días consecutivos',
            icon: '🔥',
            unlocked_date: today,
            category: 'discipline'
          },
          {
            id: 'math_expert',
            name: 'Experto en Matemáticas',
            description: 'Dominó los conceptos básicos de álgebra',
            icon: '🧮',
            unlocked_date: new Date(now.getTime() - 86400000).toISOString().split('T')[0],
            category: 'academic'
          },
          {
            id: 'ai_collaborator',
            name: 'Colaborador IA',
            description: 'Trabajó efectivamente con agentes IA',
            icon: '🤖',
            unlocked_date: new Date(now.getTime() - 172800000).toISOString().split('T')[0],
            category: 'technology'
          }
        ],
        subject_stats: [
          {
            subject: 'Matemáticas',
            progress: 85,
            grade: 8.5,
            time_spent_hours: 24,
            exercises_completed: 45,
            last_activity: today
          },
          {
            subject: 'Literatura',
            progress: 75,
            grade: 7.8,
            time_spent_hours: 18,
            exercises_completed: 23,
            last_activity: today
          },
          {
            subject: 'Química',
            progress: 68,
            grade: 7.2,
            time_spent_hours: 15,
            exercises_completed: 18,
            last_activity: new Date(now.getTime() - 86400000).toISOString().split('T')[0]
          }
        ],
        trends: {
          weekly_performance: [72, 75, 78, 82, 78, 85, 88],
          best_study_time: '2:00 PM - 4:00 PM',
          most_improved_subject: 'Matemáticas',
          needs_attention: ['Química', 'Participación en clase']
        }
      },
      system_status: {
        agents_active: 0,
        total_agents: 0,
        last_interaction: new Date(now.getTime() - 300000).toISOString(),
        system_health: 'good'
      },
      recommendations: []
    };
  }
}

// Crear instancia por defecto con la URL del backend FastAPI
const statsService = new StatsService();

export { StatsService, statsService };
