import axios from 'axios';

// Configuración base para conectar con el backend de Julia
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Cliente HTTP configurado
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  
  // Conectar con el agente de análisis educativo
  async getStudentAnalytics(studentId: string, performanceData: any): Promise<any> {
    try {
      const response = await apiClient.post('/agents/analytics/analyze', {
        student_id: studentId,
        performance_data: performanceData
      });
      return response.data;
    } catch (error) {
      console.error('Error getting student analytics:', error);
      throw new Error('No se pudo obtener el análisis del estudiante');
    }
  }

  // Conectar con el agente coach estudiantil
  async getStudentCoaching(studentId: string, context: any): Promise<any> {
    try {
      const response = await apiClient.post('/agents/student-coach/get-guidance', {
        student_id: studentId,
        context: context,
        request_type: 'personalized_guidance'
      });
      return response.data;
    } catch (error) {
      console.error('Error getting student coaching:', error);
      throw new Error('No se pudo obtener la orientación del coach');
    }
  }

  // Conectar con el agente planificador de lecciones
  async getStudyPlanning(studentId: string, subjects: string[], goals: any): Promise<any> {
    try {
      const response = await apiClient.post('/agents/lesson-planner/create-plan', {
        student_id: studentId,
        subjects: subjects,
        learning_goals: goals,
        duration: '1_month'
      });
      return response.data;
    } catch (error) {
      console.error('Error getting study planning:', error);
      throw new Error('No se pudo generar el plan de estudio');
    }
  }

  // Conectar con el agente de análisis de documentos
  async analyzeStudentProgress(studentId: string, documents: any[]): Promise<any> {
    try {
      const response = await apiClient.post('/agents/document-analyzer/analyze-progress', {
        student_id: studentId,
        documents: documents,
        analysis_type: 'progress_tracking'
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing student progress:', error);
      throw new Error('No se pudo analizar el progreso');
    }
  }

  // Conectar con el generador de exámenes
  async generatePracticeExam(studentId: string, subject: string, difficulty: string): Promise<any> {
    try {
      const response = await apiClient.post('/agents/exam-generator/create-exam', {
        student_id: studentId,
        subject: subject,
        difficulty: difficulty,
        question_count: 10,
        exam_type: 'practice'
      });
      return response.data;
    } catch (error) {
      console.error('Error generating practice exam:', error);
      throw new Error('No se pudo generar el examen de práctica');
    }
  }

  // Obtener reporte parental real
  async getParentReport(studentId: string): Promise<any> {
    try {
      const response = await apiClient.post('/agents/analytics/parent-report', {
        student_id: studentId
      });
      return response.data;
    } catch (error) {
      console.error('Error getting parent report:', error);
      throw new Error('No se pudo generar el reporte parental');
    }
  }

  // Obtener métricas de clase real
  async getClassroomAnalytics(classId: string, studentsData: any[]): Promise<any> {
    try {
      const response = await apiClient.post('/agents/analytics/classroom-analytics', {
        class_id: classId,
        students_data: studentsData
      });
      return response.data;
    } catch (error) {
      console.error('Error getting classroom analytics:', error);
      throw new Error('No se pudieron obtener las métricas de clase');
    }
  }

  // Coordinador de agentes para solicitudes complejas
  async coordinateAgents(request: MultiAgentRequest): Promise<any> {
    try {
      const response = await apiClient.post('/agents/coordinator/execute', request);
      return response.data;
    } catch (error) {
      console.error('Error coordinating agents:', error);
      throw new Error('Error en la coordinación de agentes');
    }
  }

  // Obtener estado del estudiante en tiempo real
  async getStudentRealTimeData(studentId: string): Promise<any> {
    try {
      const response = await apiClient.get(`/students/${studentId}/realtime`);
      return response.data;
    } catch (error) {
      console.error('Error getting real-time data:', error);
      // Datos de fallback mientras se establece conexión
      return {
        name: "Estudiante Demo",
        grade: "10° Grado",
        status: "Conectando con sistema...",
        last_activity: new Date().toISOString(),
        performance: 0.0,
        engagement: 0.0
      };
    }
  }

  // Enviar interacción del estudiante al sistema
  async logStudentInteraction(studentId: string, interaction: any): Promise<void> {
    try {
      await apiClient.post('/students/interactions', {
        student_id: studentId,
        interaction: interaction,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error logging interaction:', error);
      // No bloqueamos la UI por errores de logging
    }
  }

  // Obtener recomendaciones personalizadas en tiempo real
  async getPersonalizedRecommendations(studentId: string, currentContext: any): Promise<any> {
    try {
      const response = await apiClient.post('/agents/recommendations/generate', {
        student_id: studentId,
        context: currentContext,
        timestamp: new Date().toISOString()
      });
      return response.data;
    } catch (error) {
      console.error('Error getting recommendations:', error);
      return {
        recommendations: [
          "Continúa con tu progreso actual",
          "Revisa los conceptos de la última lección",
          "Practica ejercicios de repaso"
        ],
        priority: "normal",
        generated_by: "Sistema de respaldo"
      };
    }
  }

  // Iniciar sesión de tutoría con IA
  async startTutoringSession(studentId: string, subject: string, questions: string[]): Promise<any> {
    try {
      const response = await apiClient.post('/agents/tutor/start-session', {
        student_id: studentId,
        subject: subject,
        questions: questions,
        session_type: 'interactive'
      });
      return response.data;
    } catch (error) {
      console.error('Error starting tutoring session:', error);
      throw new Error('No se pudo iniciar la sesión de tutoría');
    }
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
