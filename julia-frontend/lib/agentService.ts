/**
 * Servicio para interactuar con los agentes del sistema educativo
 * Maneja la comunicación con el backend Python/FastAPI
 */

interface AgentResponse {
  success?: boolean;
  agent?: {
    id: string;
    name: string;
    icon: string;
    description?: string;
    is_real: boolean;
    status: string;
  };
  interaction?: {
    user_message: string;
    agent_response: string;
    formatted_content: string;
    response_length?: number;
    contains_markdown?: boolean;
    has_real_newlines?: boolean;
    response_metadata?: any;
  };
  response_metadata?: any;
  formatted_content?: string;
  agent_name?: string;
  agent_icon?: string;
  is_real_agent?: boolean;
  timestamp?: string;
}

interface MultiAgentResponse {
  success?: boolean;
  responses?: Array<{
    agent_type: string;
    agent_name: string;
    agent_icon: string;
    response: string;
    formatted_content: string;
    is_real_agent: boolean;
    response_metadata?: {
      length: number;
      has_markdown: boolean;
      model_used?: string;
    };
  }>;
}

interface CoachResponse {
  success?: boolean;
  guidance?: string;
  formatted_content?: string;
  response_metadata?: {
    length: number;
    has_markdown: boolean;
    model_used?: string;
  };
}

class AgentService {
  private baseUrl: string;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl;
  }

  /**
   * Envía un mensaje a un agente específico y recibe respuesta formateada
   */
  async sendMessage(message: string, agentId: string = 'tutor', context: any = {}): Promise<AgentResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/agents/chat/formatted`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          agent_id: agentId,
          context: context
        })
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data: AgentResponse = await response.json();
      
      // Agregar timestamp si no existe
      if (!data.timestamp) {
        data.timestamp = new Date().toISOString();
      }

      console.log('✅ Respuesta del agente recibida:', data);
      console.log('📝 Contiene markdown:', data.interaction?.contains_markdown);
      
      return data;
    } catch (error) {
      console.error('Error en sendMessage:', error);
      throw error;
    }
  }

  /**
   * Envía un mensaje a múltiples agentes y recibe todas las respuestas
   */
  async sendMultiAgentMessage(message: string, context: any = {}): Promise<MultiAgentResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/agents/unified-chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          context: context
        })
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data: MultiAgentResponse = await response.json();
      
      console.log('✅ Respuesta multi-agente recibida:', data);
      console.log('🤖 Número de agentes que respondieron:', data.responses?.length || 0);
      
      return data;
    } catch (error) {
      console.error('Error en sendMultiAgentMessage:', error);
      throw error;
    }
  }

  /**
   * Solicita orientación al coach estudiantil
   */
  async getCoachGuidance(message: string, context: any = {}): Promise<CoachResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/agents/student-coach`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          context: context
        })
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data: CoachResponse = await response.json();
      
      console.log('✅ Orientación del coach recibida:', data);
      console.log('📝 Contiene markdown:', data.response_metadata?.has_markdown);
      
      return data;
    } catch (error) {
      console.error('Error en getCoachGuidance:', error);
      throw error;
    }
  }

  /**
   * Prueba la limpieza de respuestas del backend
   */
  async testCleanResponse(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/agents/test-clean-response`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      console.log('✅ Test de limpieza:', data);
      
      return data;
    } catch (error) {
      console.error('Error en testCleanResponse:', error);
      throw error;
    }
  }

  /**
   * Renderiza markdown en el servidor (para casos especiales)
   */
  async renderMarkdown(content: string): Promise<string> {
    try {
      const response = await fetch(`${this.baseUrl}/api/agents/render-markdown`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: content
        })
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      return data.rendered_html || content;
    } catch (error) {
      console.error('Error en renderMarkdown:', error);
      throw error;
    }
  }

  /**
   * Obtiene información sobre los agentes disponibles
   */
  async getAgentsInfo(): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/agents/info`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      console.log('✅ Información de agentes:', data);
      
      return data.agents || [];
    } catch (error) {
      console.error('Error en getAgentsInfo:', error);
      throw error;
    }
  }
}

// Crear instancia por defecto con la URL del backend FastAPI
const agentService = new AgentService('http://localhost:8000');

export { AgentService, agentService };
export type { AgentResponse, MultiAgentResponse, CoachResponse };
