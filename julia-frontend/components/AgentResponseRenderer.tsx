import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

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
  guidance?: string;  // Añadido para CoachResponse compatibility
}

interface AgentResponseRendererProps {
  response: AgentResponse;
}

const AgentResponseRenderer: React.FC<AgentResponseRendererProps> = ({ response }) => {
  // Función para limpiar códigos ANSI de escape
  const cleanAnsiCodes = (text: string): string => {
    if (typeof text !== 'string') return text;
    
    // Remover códigos ANSI de escape (colores de terminal)
    return text
      .replace(/\x1b\[[0-9;]*m/g, '') // Códigos ANSI básicos
      .replace(/\[\d{1,2}m/g, '')     // Códigos de color simplificados [36m, [0m, etc.
      .replace(/\[0m/g, '')          // Reset de color específico
      .replace(/┃/g, '')             // Caracteres de caja/bordes
      .replace(/┗━+┛/g, '')          // Bordes inferiores
      .replace(/━+/g, '')            // Líneas horizontales
      .trim();
  };

  // Extraer contenido con múltiples fallbacks y debug detallado
  let content = '';
  
  console.log('🔍 Debug AgentResponseRenderer - Respuesta completa:', response);
  
  // Prioridad: formatted_content > agent_response > respuesta directa
  if (response.interaction?.formatted_content) {
    content = response.interaction.formatted_content;
    console.log('✅ Usando interaction.formatted_content');
  } else if (response.formatted_content) {
    content = response.formatted_content;
    console.log('✅ Usando formatted_content');
  } else if (response.interaction?.agent_response) {
    content = response.interaction.agent_response;
    console.log('✅ Usando interaction.agent_response');
  } else if (response.guidance) {
    // Para CoachResponse que tiene campo guidance
    content = response.guidance;
    console.log('✅ Usando guidance');
  } else if (typeof response === 'string') {
    content = response;
    console.log('✅ Usando response como string');
  } else {
    // Si no hay contenido específico, buscar en toda la respuesta
    const responseKeys = Object.keys(response);
    console.log('🔍 Campos disponibles en response:', responseKeys);
    
    // Intentar extraer cualquier campo que parezca ser contenido
    for (const key of responseKeys) {
      const value = (response as any)[key];
      if (typeof value === 'string' && value.length > 10 && !['id', 'timestamp', 'type'].includes(key)) {
        content = value;
        console.log(`✅ Usando campo ${key} como contenido`);
        break;
      }
    }
    
    if (!content) {
      content = JSON.stringify(response, null, 2);
      console.log('⚠️ Usando JSON completo como fallback');
    }
  }

  // LIMPIAR códigos ANSI antes de procesar
  if (content) {
    const originalContent = content;
    content = cleanAnsiCodes(content);
    
    if (originalContent !== content) {
      console.log('🧹 Códigos ANSI removidos:', {
        antes: originalContent.substring(0, 100) + '...',
        despues: content.substring(0, 100) + '...'
      });
    }
  }

  // SIEMPRE asegurar que el contenido tenga estructura markdown
  if (content && content.length > 20) {
    // Si el contenido no tiene markdown, crear estructura
    if (!content.includes('#') && !content.includes('**') && !content.includes('*')) {
      console.log('🔧 Convirtiendo texto plano a markdown');
      
      // Detectar si es una respuesta larga que podemos estructurar
      const lines = content.split('\n').filter(line => line.trim());
      
      if (lines.length > 3) {
        // Respuesta multi-línea: agregar header y formatear
        content = `## 📚 Respuesta\n\n${content}`;
      } else if (content.length > 100) {
        // Respuesta larga de una sola línea: agregar header
        content = `## 📚 Respuesta\n\n${content}`;
      }
      
      // Intentar detectar listas y formatearlas
      content = content.replace(/(\d+)\.\s+/g, '\n$1. ');
      content = content.replace(/(-|\*)\s+/g, '\n- ');
    }
  }

  const agent = response.agent || {};
  const metadata = response.response_metadata || response.interaction?.response_metadata || {};
  
  console.log('🎯 Contenido final para renderizar:', {
    contentLength: content.length,
    contentPreview: content.substring(0, 200) + '...',
    hasMarkdown: content.includes('#') || content.includes('**') || content.includes('*'),
    agent: (agent as any)?.name || 'Sin nombre'
  });
  
  return (
    <div className="agent-response-container bg-white rounded-lg p-6 shadow-lg border border-gray-200 mb-6">
      {/* Header del agente */}
      <div className="agent-header flex items-center gap-3 mb-4 pb-3 border-b border-gray-100">
        <span className="agent-icon text-2xl">{(agent as any)?.icon || response.agent_icon}</span>
        <span className="agent-name font-semibold text-gray-800 text-lg">
          {(agent as any)?.name || response.agent_name}
        </span>
        {((agent as any)?.is_real || response.is_real_agent) && (
          <span className="real-agent-badge bg-green-500 text-white text-xs px-2 py-1 rounded-full font-medium">
            🤖 Agente Real
          </span>
        )}
      </div>
      
      {/* Contenido markdown renderizado */}
      <div className="markdown-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex]}
          components={{
            // Headers con estilos bonitos y degradados azules
            h1: ({children}) => (
              <h1 className="text-3xl font-bold mb-6 text-blue-700 border-b-2 border-blue-200 pb-2">
                {children}
              </h1>
            ),
            h2: ({children}) => (
              <h2 className="text-2xl font-bold mb-4 text-blue-600 mt-6">
                {children}
              </h2>
            ),
            h3: ({children}) => (
              <h3 className="text-xl font-semibold mb-3 text-blue-500 mt-4">
                {children}
              </h3>
            ),
            h4: ({children}) => (
              <h4 className="text-lg font-semibold mb-2 text-blue-400 mt-3">
                {children}
              </h4>
            ),
            
            // Párrafos con espaciado mejorado
            p: ({children}) => (
              <p className="mb-4 leading-relaxed text-gray-700">
                {children}
              </p>
            ),
            
            // Quotes con estilo hermoso y sombra
            blockquote: ({children}) => (
              <blockquote className="border-l-4 border-blue-300 bg-blue-50 dark:bg-blue-900/20 pl-4 py-3 mb-4 italic rounded-r-lg shadow-sm">
                {children}
              </blockquote>
            ),
            
            // Código inline y bloques con mejor contraste
              code(codeProps: any) {
                const { node, inline, className, children, ...props } = codeProps || {};
                const match = /language-(\w+)/.exec(className || '');
                const lang = match ? match[1] : '';
                const content = String(children || '').replace(/\n$/, '');
              if (inline) {
                return (
                  <code className="bg-gray-200 dark:bg-gray-700 text-red-600 dark:text-red-400 px-2 py-1 rounded text-sm font-mono">
                    {children}
                  </code>
                );
              }
              
              return (
                <div className="mb-4">
                  {lang && (
                    <div className="bg-gray-700 text-white px-3 py-1 text-xs rounded-t-lg font-medium">
                      {lang}
                    </div>
                  )}
                  <pre className={`bg-gray-100 dark:bg-gray-800 p-4 overflow-x-auto font-mono text-sm border ${lang ? 'rounded-b-lg border-t-0' : 'rounded-lg'} border-gray-200 dark:border-gray-600`}>
                    <code {...props}>{children}</code>
                  </pre>
                </div>
              );
            },
            
            // Listas con mejor espaciado y jerarquía
            ul: ({children}) => (
              <ul className="list-disc list-inside mb-4 space-y-1 text-gray-700 ml-4">
                {children}
              </ul>
            ),
            ol: ({children}) => (
              <ol className="list-decimal list-inside mb-4 space-y-1 text-gray-700 ml-4">
                {children}
              </ol>
            ),
            li: ({children}) => (
              <li className="mb-1 leading-relaxed">{children}</li>
            ),
            
            // Tablas responsivas con mejor diseño
            table: ({children}) => (
              <div className="overflow-x-auto mb-6 shadow-sm rounded-lg border border-gray-200 dark:border-gray-600">
                <table className="min-w-full border-collapse">
                  {children}
                </table>
              </div>
            ),
            thead: ({children}) => (
              <thead className="bg-gray-50 dark:bg-gray-700">{children}</thead>
            ),
            th: ({children}) => (
              <th className="border-b border-gray-300 dark:border-gray-600 px-4 py-3 text-left font-semibold text-gray-800 dark:text-gray-200">
                {children}
              </th>
            ),
            td: ({children}) => (
              <td className="border-b border-gray-200 dark:border-gray-700 px-4 py-2 text-gray-700 dark:text-gray-300">
                {children}
              </td>
            ),
            
            // Enlaces con mejor hover
            a: ({href, children}) => (
              <a 
                href={href} 
                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline transition-colors duration-200"
                target="_blank" 
                rel="noopener noreferrer"
              >
                {children}
              </a>
            ),
            
            // Texto en negrita y cursiva mejorado
            strong: ({children}) => (
              <strong className="font-bold text-gray-900 dark:text-gray-100">{children}</strong>
            ),
            em: ({children}) => (
              <em className="italic text-gray-800 dark:text-gray-200">{children}</em>
            ),
            
            // Separadores elegantes
            hr: () => (
              <hr className="my-6 border-t-2 border-gray-200 dark:border-gray-600" />
            )
          }}
        >
          {content || `## ⚠️ Contenido Vacío\n\nNo se recibió respuesta del agente. Por favor, intenta nuevamente.`}
        </ReactMarkdown>
      </div>
      
      {/* Metadata */}
      <div className="response-metadata">
        <div className="text-sm text-gray-500 flex flex-wrap gap-4 pt-3 border-t border-gray-200">
          <span>📏 {metadata.length || content?.length || 0} caracteres</span>
          <span>🕒 {response.timestamp ? new Date(response.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}</span>
          {metadata.model_used && (
            <span>🤖 {metadata.model_used}</span>
          )}
          {(metadata.has_markdown || response.interaction?.contains_markdown) && (
            <span>📝 Contiene Markdown</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentResponseRenderer;
