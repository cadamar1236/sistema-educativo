import React, { useState } from 'react';
import ChatInterface from './ChatInterface';
import MultiAgentChat from './MultiAgentChat';
import AICoachEnhanced from './AICoachEnhanced';
import StudentDashboard from './student/StudentDashboard';

const MainApp: React.FC = () => {
  const [activeView, setActiveView] = useState<'dashboard' | 'tutor' | 'multi' | 'coach'>('dashboard');

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Header Navigation */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <div className="text-2xl font-bold text-gray-800">
                🎓 Sistema Educativo IA
              </div>
            </div>
            
            {/* Navigation Tabs */}
            <nav className="flex space-x-1">
              <button
                onClick={() => setActiveView('dashboard')}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  activeView === 'dashboard'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-indigo-600 hover:bg-indigo-50'
                }`}
              >
                📊 Dashboard
              </button>
              
              <button
                onClick={() => setActiveView('tutor')}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  activeView === 'tutor'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                👨‍🏫 Tutor Personal
              </button>
              
              <button
                onClick={() => setActiveView('multi')}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  activeView === 'multi'
                    ? 'bg-purple-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50'
                }`}
              >
                🎯 Consulta Múltiple
              </button>
              
              <button
                onClick={() => setActiveView('coach')}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  activeView === 'coach'
                    ? 'bg-green-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-green-600 hover:bg-green-50'
                }`}
              >
                🎯 Coach Estudiantil
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="py-8">
        {/* Info Banner - Solo mostrar si no es dashboard */}
        {activeView !== 'dashboard' && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-start space-x-4">
                <div className="text-3xl">
                  {activeView === 'tutor' && '👨‍🏫'}
                  {activeView === 'multi' && '🎯'}
                  {activeView === 'coach' && '🎯'}
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-800 mb-2">
                    {activeView === 'tutor' && 'Tutor Personal IA'}
                    {activeView === 'multi' && 'Consulta Multi-Agente'}
                    {activeView === 'coach' && 'Coach Estudiantil IA'}
                  </h2>
                  <p className="text-gray-600">
                    {activeView === 'tutor' && 
                      'Habla directamente con tu tutor personal. Recibe explicaciones detalladas con formato markdown bonito.'
                    }
                    {activeView === 'multi' && 
                      'Haz una pregunta y recibe respuestas de múltiples agentes especializados simultáneamente.'
                    }
                    {activeView === 'coach' && 
                      'Recibe orientación personalizada para mejorar tus técnicas de estudio y rendimiento académico.'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Content Views */}
        <div className="transition-all duration-300 ease-in-out">
          {activeView === 'dashboard' && <StudentDashboard />}
          {activeView === 'tutor' && <ChatInterface />}
          {activeView === 'multi' && <MultiAgentChat />}
          {activeView === 'coach' && <AICoachEnhanced />}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="text-2xl mb-2">🚀</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              Sistema Educativo con IA Avanzada
            </h3>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Experiencia de aprendizaje personalizada con múltiples agentes especializados. 
              Todas las respuestas se renderizan con markdown bonito para una mejor legibilidad.
            </p>
            
            <div className="mt-6 flex justify-center space-x-8 text-sm text-gray-500">
              <div className="flex items-center space-x-2">
                <span>✅</span>
                <span>Markdown Renderizado</span>
              </div>
              <div className="flex items-center space-x-2">
                <span>🤖</span>
                <span>Agentes Reales</span>
              </div>
              <div className="flex items-center space-x-2">
                <span>🎯</span>
                <span>Respuestas Personalizadas</span>
              </div>
              <div className="flex items-center space-x-2">
                <span>📚</span>
                <span>Soporte Matemático</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default MainApp;
