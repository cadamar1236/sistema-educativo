import React, { useState } from 'react';
import AgentResponseRenderer from './AgentResponseRenderer';
import { useMathProcessor } from '@/hooks/useMathProcessor';

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

const MultiAgentChat: React.FC = () => {
  const [message, setMessage] = useState('');
  const [responses, setResponses] = useState<MultiAgentResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { processAgentResponse } = useMathProcessor();

  const handleSend = async () => {
    if (!message.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/agents/unified-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          context: {}
        })
      });
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const data: MultiAgentResponse = await response.json();
      
      console.log('✅ Respuesta multi-agente recibida:', data);
      
      // Procesar respuestas para mejorar el rendering matemático
      const processedData = processAgentResponse(data);
      
      setResponses(prev => [...prev, processedData]);
      setMessage('');
      
    } catch (err) {
      console.error('Error enviando mensaje multi-agente:', err);
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearResponses = () => {
    setResponses([]);
    setError(null);
  };

  return (
    <div className="multi-agent-chat max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="chat-header mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          🎯 Chat Multi-Agente - Sistema Educativo
        </h1>
        <p className="text-gray-600">
          Pregunta algo y recibe respuestas de múltiples agentes especializados.
        </p>
      </div>
      
      {/* Error display */}
      {error && (
        <div className="error-message bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          ❌ Error: {error}
        </div>
      )}
      
      {/* Input section */}
      <div className="input-section mb-6">
        <div className="flex gap-2">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Pregunta algo a todos los agentes... (Ej: ¿Cómo puedo mejorar en matemáticas?)"
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={3}
            disabled={loading}
          />
          <div className="flex flex-col gap-2">
            <button
              onClick={handleSend}
              disabled={loading || !message.trim()}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '⏳ Consultando...' : '🚀 Consultar Todos'}
            </button>
            
            {responses.length > 0 && (
              <button
                onClick={clearResponses}
                disabled={loading}
                className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 text-sm"
              >
                🗑️ Limpiar
              </button>
            )}
          </div>
        </div>
        
        <div className="text-sm text-gray-500 mt-2">
          💡 Tip: Esta consulta llegará a todos los agentes especializados
        </div>
      </div>
      
      {/* Responses */}
      <div className="responses-section">
        {responses.length === 0 && !loading && (
          <div className="empty-state text-center py-12 text-gray-500">
            <div className="text-6xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-2">¡Consulta a todos los agentes!</h3>
            <p>Haz una pregunta y recibe perspectivas de múltiples agentes especializados.</p>
          </div>
        )}
        
        {responses.map((responseGroup, groupIndex) => (
          <div key={groupIndex} className="response-group mb-8">
            <div className="group-header bg-gradient-to-r from-purple-500 to-blue-500 text-white p-4 rounded-t-lg">
              <h3 className="text-lg font-semibold">
                📊 Respuestas de {responseGroup.responses?.length || 0} Agentes
              </h3>
            </div>
            
            <div className="agent-responses grid gap-4 mt-4">
              {responseGroup.responses?.map((agentResponse, agentIndex) => {
                // Convertir respuesta multi-agente al formato esperado por AgentResponseRenderer
                const formattedResponse = {
                  success: true,
                  agent: {
                    id: agentResponse.agent_type,
                    name: agentResponse.agent_name,
                    icon: agentResponse.agent_icon,
                    is_real: agentResponse.is_real_agent,
                    status: agentResponse.is_real_agent ? '🤖 Agente Real' : '🎭 Simulado'
                  },
                  interaction: {
                    user_message: message,
                    agent_response: agentResponse.response,
                    formatted_content: agentResponse.formatted_content,
                    contains_markdown: agentResponse.response_metadata?.has_markdown || false
                  },
                  response_metadata: agentResponse.response_metadata,
                  timestamp: new Date().toISOString()
                };
                
                return (
                  <AgentResponseRenderer 
                    key={agentIndex} 
                    response={formattedResponse} 
                  />
                );
              })}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="loading-message bg-purple-50 border border-purple-200 p-6 rounded-lg">
            <div className="flex items-center gap-3 mb-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
              <span className="text-purple-700 font-semibold">Consultando a todos los agentes...</span>
            </div>
            <div className="text-sm text-purple-600">
              Esto puede tomar unos momentos mientras cada agente especializado prepara su respuesta.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MultiAgentChat;
