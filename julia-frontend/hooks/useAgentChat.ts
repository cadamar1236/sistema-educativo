import { useState, useCallback } from 'react';

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

interface UseAgentChatReturn {
  responses: AgentResponse[];
  loading: boolean;
  error: string | null;
  sendMessage: (message: string, agentId?: string) => Promise<AgentResponse>;
  clearResponses: () => void;
}

export const useAgentChat = (): UseAgentChatReturn => {
  const [responses, setResponses] = useState<AgentResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (message: string, agentId: string = 'tutor'): Promise<AgentResponse> => {
    if (!message.trim()) {
      throw new Error('El mensaje no puede estar vacío');
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/agents/chat/formatted', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          agent_id: agentId,
          context: {}
        })
      });
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const data: AgentResponse = await response.json();
      
      // Debug detallado de la respuesta
      console.log('✅ Respuesta recibida del backend:', data);
      console.log('� Estructura de la respuesta:', {
        hasInteraction: !!data.interaction,
        hasFormattedContent: !!data.formatted_content,
        hasAgent: !!data.agent,
        interactionKeys: data.interaction ? Object.keys(data.interaction) : [],
        topLevelKeys: Object.keys(data)
      });
      
      if (data.interaction) {
        console.log('� Contenido en interaction:', {
          hasFormattedContent: !!data.interaction.formatted_content,
          hasAgentResponse: !!data.interaction.agent_response,
          hasRealNewlines: data.interaction.has_real_newlines,
          containsMarkdown: data.interaction.contains_markdown,
          formattedContentPreview: data.interaction.formatted_content?.substring(0, 100),
          agentResponsePreview: data.interaction.agent_response?.substring(0, 100)
        });
      }
      
      // Agregar timestamp si no existe
      if (!data.timestamp) {
        data.timestamp = new Date().toISOString();
      }
      
      setResponses(prev => [...prev, data]);
      return data;
      
    } catch (err) {
      console.error('Error enviando mensaje:', err);
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearResponses = useCallback(() => {
    setResponses([]);
    setError(null);
  }, []);

  return {
    responses,
    loading,
    error,
    sendMessage,
    clearResponses
  };
};
