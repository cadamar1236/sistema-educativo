import { useCallback } from 'react';
import { processMathInMessage } from '@/lib/mathUtils';

interface Message {
  id: string;
  content: string;
  type: 'user' | 'agent';
  timestamp: Date;
  agent_type?: string;
  [key: string]: any;
}

/**
 * Hook para procesar mensajes y mejorar el rendering de matemáticas
 */
export const useMathProcessor = () => {
  
  const processMessage = useCallback((message: Message): Message => {
    if (typeof message.content === 'string') {
      return {
        ...message,
        content: processMathInMessage(message.content)
      };
    }
    return message;
  }, []);

  const processMessages = useCallback((messages: Message[]): Message[] => {
    return messages.map(processMessage);
  }, [processMessage]);

  const processAgentResponse = useCallback((response: any): any => {
    if (response && typeof response === 'object') {
      // Procesar respuesta individual
      if (response.content && typeof response.content === 'string') {
        return {
          ...response,
          content: processMathInMessage(response.content)
        };
      }
      
      // Procesar múltiples respuestas
      if (response.responses && Array.isArray(response.responses)) {
        return {
          ...response,
          responses: response.responses.map((resp: any) => 
            resp.content ? {
              ...resp,
              content: processMathInMessage(resp.content)
            } : resp
          )
        };
      }
      
      // Procesar resultado de colaboración
      if (response.collaboration_result && typeof response.collaboration_result === 'string') {
        return {
          ...response,
          collaboration_result: processMathInMessage(response.collaboration_result)
        };
      }
    }
    
    return response;
  }, []);

  return {
    processMessage,
    processMessages,
    processAgentResponse
  };
};

export default useMathProcessor;
