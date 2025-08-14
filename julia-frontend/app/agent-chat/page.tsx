'use client';

import React, { useState } from 'react';
import ChatInterface from '../components/ChatInterface';
import MultiAgentChat from '../components/MultiAgentChat';
import { agentService } from '../lib/agentService';

const AgentChatDemo: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'single' | 'multi' | 'test'>('single');

  const testMarkdownResponse = async () => {
    try {
      const response = await agentService.testCleanResponse();
      console.log('🧪 Test de respuesta limpia:', response);
      alert('✅ Test completado. Revisa la consola para ver los resultados.');
    } catch (error) {
      console.error('❌ Error en test:', error);
      alert('❌ Error en test. Revisa la consola.');
    }
  };

  const testAgentsInfo = async () => {
    try {
      const agents = await agentService.getAgentsInfo();
      console.log('🤖 Agentes disponibles:', agents);
      alert(`✅ Encontrados ${agents.length} agentes. Revisa la consola.`);
    } catch (error) {
      console.error('❌ Error obteniendo agentes:', error);
      alert('❌ Error obteniendo agentes. Revisa la consola.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-lg border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <div className="text-xl font-bold text-gray-800">
              🎓 Sistema Educativo - Demo Chat
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={() => setActiveTab('single')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'single'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                👨‍🏫 Chat Individual
              </button>
              
              <button
                onClick={() => setActiveTab('multi')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'multi'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                🎯 Multi-Agente
              </button>
              
              <button
                onClick={() => setActiveTab('test')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'test'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                🧪 Tests
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="py-8">
        {activeTab === 'single' && (
          <div>
            <div className="max-w-4xl mx-auto px-4 mb-6">
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                <h2 className="text-lg font-semibold text-blue-800 mb-2">
                  💡 Chat Individual con Agente
                </h2>
                <p className="text-blue-700">
                  Habla directamente con un agente específico. Las respuestas se renderizan con markdown bonito.
                </p>
              </div>
            </div>
            <ChatInterface />
          </div>
        )}

        {activeTab === 'multi' && (
          <div>
            <div className="max-w-6xl mx-auto px-4 mb-6">
              <div className="bg-purple-50 border border-purple-200 p-4 rounded-lg">
                <h2 className="text-lg font-semibold text-purple-800 mb-2">
                  🎯 Chat Multi-Agente
                </h2>
                <p className="text-purple-700">
                  Haz una pregunta y recibe respuestas de múltiples agentes especializados simultáneamente.
                </p>
              </div>
            </div>
            <MultiAgentChat />
          </div>
        )}

        {activeTab === 'test' && (
          <div className="max-w-4xl mx-auto px-4">
            <div className="bg-green-50 border border-green-200 p-6 rounded-lg">
              <h2 className="text-xl font-semibold text-green-800 mb-4">
                🧪 Herramientas de Testing
              </h2>
              
              <div className="space-y-4">
                <div className="bg-white p-4 rounded border">
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Test de Respuesta Limpia
                  </h3>
                  <p className="text-gray-600 mb-3">
                    Prueba que el backend está enviando respuestas limpias sin objetos RunResponse.
                  </p>
                  <button
                    onClick={testMarkdownResponse}
                    className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors"
                  >
                    🧪 Ejecutar Test
                  </button>
                </div>

                <div className="bg-white p-4 rounded border">
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Información de Agentes
                  </h3>
                  <p className="text-gray-600 mb-3">
                    Obtiene la lista de agentes disponibles en el sistema.
                  </p>
                  <button
                    onClick={testAgentsInfo}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                  >
                    🤖 Ver Agentes
                  </button>
                </div>

                <div className="bg-white p-4 rounded border">
                  <h3 className="font-semibold text-gray-800 mb-2">
                    Ejemplo de Markdown
                  </h3>
                  <p className="text-gray-600 mb-3">
                    Ejemplo de cómo se ve el contenido markdown renderizado:
                  </p>
                  
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="markdown-content">
                      <h2 className="text-2xl font-bold mb-4 text-blue-600">
                        📚 Ejemplo de Derivada
                      </h2>
                      <p className="mb-4 leading-relaxed text-gray-700">
                        Una derivada es la <strong>velocidad de cambio instantánea</strong> de una función.
                      </p>
                      
                      <blockquote className="border-l-4 border-blue-300 bg-blue-50 pl-4 py-3 mb-4 italic rounded-r-lg">
                        La derivada de f(x) = x² es f'(x) = 2x
                      </blockquote>
                      
                      <h3 className="text-xl font-semibold mb-3 text-blue-500">
                        🎯 Reglas básicas:
                      </h3>
                      
                      <ul className="list-disc list-inside mb-4 space-y-1 text-gray-700 ml-4">
                        <li>Regla de la potencia: d/dx(x^n) = nx^(n-1)</li>
                        <li>Regla de la suma: d/dx(f + g) = f' + g'</li>
                        <li>Regla del producto: d/dx(fg) = f'g + fg'</li>
                      </ul>
                      
                      <div className="overflow-x-auto mb-6">
                        <table className="min-w-full border-collapse border border-gray-300 rounded-lg">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-800">
                                Función
                              </th>
                              <th className="border border-gray-300 px-4 py-3 text-left font-semibold text-gray-800">
                                Derivada
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td className="border border-gray-300 px-4 py-2 text-gray-700">
                                x²
                              </td>
                              <td className="border border-gray-300 px-4 py-2 text-gray-700">
                                2x
                              </td>
                            </tr>
                            <tr>
                              <td className="border border-gray-300 px-4 py-2 text-gray-700">
                                x³
                              </td>
                              <td className="border border-gray-300 px-4 py-2 text-gray-700">
                                3x²
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AgentChatDemo;
