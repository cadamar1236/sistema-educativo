import React, { useState } from 'react';
import AgentResponseRenderer from './AgentResponseRenderer';
import { agentService, type CoachResponse } from '../lib/agentService';

const AICoachEnhanced: React.FC = () => {
  const [message, setMessage] = useState('');
  const [responses, setResponses] = useState<CoachResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const quickPrompts = [
    "¿Cómo puedo mejorar mis hábitos de estudio?",
    "Tengo problemas para concentrarme al estudiar",
    "¿Qué técnicas de memorización me recomiendas?",
    "Siento ansiedad antes de los exámenes",
    "¿Cómo organizo mejor mi tiempo de estudio?",
    "No entiendo bien las matemáticas"
  ];

  const handleSend = async () => {
    if (!message.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await agentService.getCoachGuidance(message);
      
      console.log('✅ Respuesta del coach recibida:', response);
      
      setResponses(prev => [...prev, response]);
      setMessage('');
      
    } catch (err) {
      console.error('Error enviando mensaje al coach:', err);
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    setMessage(prompt);
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
    <div className="ai-coach-container max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="coach-header mb-6 text-center">
        <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white p-6 rounded-lg">
          <h1 className="text-3xl font-bold mb-2">
            🎯 Coach IA Estudiantil
          </h1>
          <p className="text-green-100">
            Tu mentor personal para mejorar tus técnicas de estudio y rendimiento académico
          </p>
        </div>
      </div>
      
      {/* Quick Prompts */}
      <div className="quick-prompts mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">
          💡 Preguntas frecuentes:
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {quickPrompts.map((prompt, index) => (
            <button
              key={index}
              onClick={() => handleQuickPrompt(prompt)}
              className="text-left p-3 bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 transition-colors text-sm"
              disabled={loading}
            >
              💬 {prompt}
            </button>
          ))}
        </div>
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
            placeholder="Cuéntale al coach sobre tus desafíos académicos..."
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
            rows={3}
            disabled={loading}
          />
          <div className="flex flex-col gap-2">
            <button
              onClick={handleSend}
              disabled={loading || !message.trim()}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '⏳ Analizando...' : '🎯 Pedir Consejo'}
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
          💡 Tip: Sé específico sobre tus dificultades para recibir consejos más personalizados
        </div>
      </div>
      
      {/* Responses */}
      <div className="responses-section">
        {responses.length === 0 && !loading && (
          <div className="empty-state text-center py-12 text-gray-500">
            <div className="text-6xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-2">¡Tu coach está listo para ayudarte!</h3>
            <p>Describe tus desafíos académicos y recibe orientación personalizada.</p>
          </div>
        )}
        
        {responses.map((response, index) => {
          // Convertir respuesta del coach al formato esperado por AgentResponseRenderer
          const formattedResponse = {
            success: true,
            agent: {
              id: 'student_coach',
              name: 'Coach Estudiantil IA',
              icon: '🎯',
              is_real: true,
              status: '🤖 Coach Real'
            },
            interaction: {
              user_message: message,
              agent_response: response.guidance || response.formatted_content || '',
              formatted_content: response.formatted_content || response.guidance || '',
              contains_markdown: response.response_metadata?.has_markdown || false
            },
            response_metadata: response.response_metadata,
            timestamp: new Date().toISOString()
          };
          
          return (
            <AgentResponseRenderer key={index} response={formattedResponse} />
          );
        })}
        
        {loading && (
          <div className="loading-message bg-green-50 border border-green-200 p-4 rounded-lg flex items-center gap-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-600"></div>
            <span className="text-green-700">El coach está analizando tu situación y preparando consejos personalizados...</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default AICoachEnhanced;
