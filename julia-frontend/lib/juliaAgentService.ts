import axios, { AxiosRequestConfig } from 'axios';

// Configuración base para conectar con el backend de Julia
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Cliente HTTP configurado (se le podrán inyectar headers dinámicos)
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
});

// Tipos básicos (placeholder – puedes afinar según backend)
interface AnalyticsResponse { [key: string]: any; performance_score?: number }
interface CoachingResponse { guidance?: string; [key: string]: any }
interface RealTimeData { status?: string; [key: string]: any }
interface RecommendationsResponse { recommendations: string[]; priority?: string; generated_by?: string }

// Tipos para el sistema multiagente
export interface StudentData {
  id: string;
  name: string;
  grade_level: string;
  performance_data: any;
}

export interface AgentResponse {
  agent_name: string;
  response: any;
  timestamp: string;
  success: boolean;
}

export interface MultiAgentRequest {
  agent_type: string;
  data: any;
  student_id?: string;
}

class JuliaAgentService {
  private authToken: string | null = null;

  setAuthToken(token: string | null) {
    this.authToken = token;
  }

  // Helper centralizado con reintentos simples (exponencial suave)
  private async request<T>(config: AxiosRequestConfig & { retries?: number; retryDelayMs?: number }): Promise<T> {
    const { retries = 1, retryDelayMs = 500, ...axiosCfg } = config;
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const finalCfg: AxiosRequestConfig = { ...axiosCfg };
        finalCfg.headers = {
          ...(axiosCfg.headers || {}),
          ...(this.authToken ? { Authorization: `Bearer ${this.authToken}` } : {})
        };
        const resp = await apiClient.request<T>(finalCfg);
        return resp.data;
      } catch (err: any) {
        const status = err?.response?.status;
        const retriable = status >= 500 || !status; // network / server error
        if (attempt < retries && retriable) {
          await new Promise(r => setTimeout(r, retryDelayMs * (attempt + 1)));
          continue;
        }
        // Normalizamos el error
        const message = err?.response?.data?.detail || err?.message || 'Error desconocido';
        throw new Error(message);
      }
    }
    throw new Error('Error de petición no especificado');
  }
  
  // Conectar con el agente de análisis educativo
  async getStudentAnalytics(studentId: string, performanceData: any): Promise<AnalyticsResponse> {
    return this.request<AnalyticsResponse>({
      method: 'POST',
      url: '/agents/analytics/analyze',
      data: { student_id: studentId, performance_data: performanceData },
      retries: 1
    });
  }

  // Conectar con el agente coach estudiantil
  async getStudentCoaching(studentId: string, context: any): Promise<CoachingResponse> {
    return this.request<CoachingResponse>({
      method: 'POST',
      url: '/agents/student-coach/get-guidance',
      data: { student_id: studentId, context, request_type: 'personalized_guidance' },
      retries: 1
    });
  }

  // Conectar con el agente planificador de lecciones
  async getStudyPlanning(studentId: string, subjects: string[], goals: any): Promise<any> {
    return this.request({
      method: 'POST',
      url: '/agents/lesson-planner/create-plan',
      data: { student_id: studentId, subjects, learning_goals: goals, duration: '1_month' }
    });
  }

  // Conectar con el agente de análisis de documentos
  async analyzeStudentProgress(studentId: string, documents: any[]): Promise<any> {
    return this.request({
      method: 'POST',
      url: '/agents/document-analyzer/analyze-progress',
      data: { student_id: studentId, documents, analysis_type: 'progress_tracking' }
    });
  }

  // Conectar con el generador de exámenes
  async generatePracticeExam(studentId: string, subject: string, difficulty: string): Promise<any> {
    return this.request({
      method: 'POST',
      url: '/agents/exam-generator/create-exam',
      data: { student_id: studentId, subject, difficulty, question_count: 10, exam_type: 'practice' }
    });
  }

  // Obtener reporte parental real
  async getParentReport(studentId: string): Promise<any> {
    return this.request({
      method: 'POST',
      url: '/agents/analytics/parent-report',
      data: { student_id: studentId }
    });
  }

  // Obtener métricas de clase real
  async getClassroomAnalytics(classId: string, studentsData: any[]): Promise<any> {
    return this.request({
      method: 'POST',
      url: '/agents/analytics/classroom-analytics',
      data: { class_id: classId, students_data: studentsData }
    });
  }

  // Coordinador de agentes para solicitudes complejas
  async coordinateAgents(request: MultiAgentRequest): Promise<any> {
    return this.request({
      method: 'POST',
      url: '/agents/coordinator/execute',
      data: request
    });
  }

  // Obtener estado del estudiante en tiempo real
  async getStudentRealTimeData(studentId: string): Promise<RealTimeData | null> {
    try {
      return await this.request<RealTimeData>({ method: 'GET', url: `/students/${studentId}/realtime` });
    } catch (error) {
      console.error('Error getting real-time data:', error);
      return null; // UI decidirá qué mostrar
    }
  }

  // Enviar interacción del estudiante al sistema
  async logStudentInteraction(studentId: string, interaction: any): Promise<void> {
    try {
      await this.request({
        method: 'POST',
        url: '/students/interactions',
        data: { student_id: studentId, interaction, timestamp: new Date().toISOString() }
      });
    } catch (error) {
      console.error('Error logging interaction:', error);
    }
  }

  // Obtener recomendaciones personalizadas en tiempo real
  async getPersonalizedRecommendations(studentId: string, currentContext: any): Promise<RecommendationsResponse> {
    try {
      return await this.request<RecommendationsResponse>({
        method: 'POST',
        url: '/agents/recommendations/generate',
        data: { student_id: studentId, context: currentContext, timestamp: new Date().toISOString() },
        retries: 1
      });
    } catch (error) {
      console.error('Error getting recommendations:', error);
      return {
        recommendations: [
          'Continúa con tu progreso actual',
          'Revisa los conceptos de la última lección',
          'Practica ejercicios de repaso'
        ],
        priority: 'normal',
        generated_by: 'Sistema de respaldo'
      };
    }
  }

  // Iniciar sesión de tutoría con IA
  async startTutoringSession(studentId: string, subject: string, questions: string[]): Promise<any> {
    return this.request({
      method: 'POST',
      url: '/agents/tutor/start-session',
      data: { student_id: studentId, subject, questions, session_type: 'interactive' }
    });
  }
}

// Instancia singleton del servicio
export const juliaAgentService = new JuliaAgentService();

// Hook personalizado para usar el servicio en componentes React
export const useJuliaAgents = () => {
  return {
    agentService: juliaAgentService,
    
    // Helpers para llamadas comunes
    async getStudentDashboardData(studentId: string) {
      const [analytics, coaching, realTime] = await Promise.allSettled([
        juliaAgentService.getStudentAnalytics(studentId, {}),
        juliaAgentService.getStudentCoaching(studentId, { type: 'dashboard_overview' }),
        juliaAgentService.getStudentRealTimeData(studentId)
      ]);
      return {
        analytics: analytics.status === 'fulfilled' ? analytics.value : null,
        coaching: coaching.status === 'fulfilled' ? coaching.value : null,
        realTime: realTime.status === 'fulfilled' ? realTime.value : null
      };
    },

    async logActivity(studentId: string, activity: string, data?: any) {
      await juliaAgentService.logStudentInteraction(studentId, {
        type: 'activity',
        activity: activity,
        data: data || {}
      });
    }
  };
};

export default juliaAgentService;
