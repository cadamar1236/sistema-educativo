import React, { useState } from 'react';
import AgentResponseRenderer from './AgentResponseRenderer';
import { useAgentChat } from '../hooks/useAgentChat';

const ChatInterface: React.FC = () => {
  const [message, setMessage] = useState('');
  const { responses, loading, error, sendMessage, clearResponses } = useAgentChat();

  const handleSend = async () => {
    if (!message.trim()) return;
    
    try {
      await sendMessage(message);
      setMessage('');
    } catch (err) {
      // Error ya manejado en el hook
      console.error('Error en handleSend:', err);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="chat-header mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          🤖 Tutor IA - Sistema Educativo
        </h1>
        <p className="text-gray-600">
          Pregunta cualquier duda académica y recibe respuestas detalladas y formateadas.
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
            placeholder="Pregunta algo al tutor... (Ej: ¿Qué es una derivada?)"
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={3}
            disabled={loading}
          />
          <div className="flex flex-col gap-2">
            <button
              onClick={handleSend}
              disabled={loading || !message.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '⏳ Enviando...' : '📤 Enviar'}
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
          💡 Tip: Usa Enter para enviar, Shift+Enter para nueva línea
        </div>
      </div>
      
      {/* Responses */}
      <div className="responses-section">
        {responses.length === 0 && !loading && (
          <div className="empty-state text-center py-12 text-gray-500">
            <div className="text-6xl mb-4">💬</div>
            <h3 className="text-xl font-semibold mb-2">¡Haz tu primera pregunta!</h3>
            <p>El tutor IA está listo para ayudarte con cualquier tema académico.</p>
          </div>
        )}
        
        {responses.map((response, index) => (
          <AgentResponseRenderer key={index} response={response} />
        ))}
        
        {loading && (
          <div className="loading-message bg-blue-50 border border-blue-200 p-4 rounded-lg flex items-center gap-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="text-blue-700">El tutor está preparando tu respuesta...</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
