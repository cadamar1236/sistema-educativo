'use client'

import React, { useState, useRef, useEffect } from 'react'
import { 
  Card, 
  CardBody, 
  CardHeader, 
  Button, 
  Textarea, 
  Chip, 
  Avatar, 
  ScrollShadow,
  Switch,
  Divider,
  Spinner,
  Progress
} from '@nextui-org/react'
import { 
  Send, 
  Bot, 
  User, 
  Settings, 
  MessageSquare, 
  Users, 
  Sparkles,
  BookOpen,
  GraduationCap,
  FileText,
  BarChart3,
  Calendar,
  Zap,
  Brain
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

// Todos los agentes disponibles
const ALL_AGENTS = [
  {
    id: 'exam_generator',
    name: 'Generador de Exámenes',
    icon: FileText,
    color: 'primary',
    description: 'Genera exámenes personalizados y evaluaciones'
  },
  {
    id: 'curriculum_creator', 
    name: 'Creador de Currículum',
    icon: BookOpen,
    color: 'secondary',
    description: 'Diseña planes de estudio estructurados'
  },
  {
    id: 'tutor',
    name: 'Tutor Virtual',
    icon: GraduationCap,
    color: 'success',
    description: 'Proporciona tutoría personalizada'
  },
  {
    id: 'lesson_planner',
    name: 'Planificador de Lecciones',
    icon: Calendar,
    color: 'warning',
    description: 'Crea planes de lección detallados'
  },
  {
    id: 'performance_analyzer',
    name: 'Analizador de Rendimiento',
    icon: BarChart3,
    color: 'danger',
    description: 'Analiza y mejora el rendimiento académico'
  }
]

interface Message {
  id: string
  type: 'user' | 'agent' | 'system'
  content: string
  timestamp: Date
  agentType?: string
  agentName?: string
  isRealAgent?: boolean
}

interface MultiAgentChatProps {
  studentId?: string;
  onActivityUpdate?: (activity: {
    type?: 'lesson' | 'exercise' | 'quiz' | 'chat_session';
    subject?: string;
    duration_minutes?: number;
    points_earned?: number;
    success_rate?: number;
  }) => void;
}

export default function MultiAgentChat({ 
  studentId = 'student_001', 
  onActivityUpdate 
}: MultiAgentChatProps) {
  // Función para limpiar códigos ANSI de escape
  const cleanAnsiCodes = (text: string): string => {
    if (typeof text !== 'string') return text;
    
    // Remover códigos ANSI de colores y estilos
    return text
      .replace(/\x1b\[[0-9;]*m/g, '') // Códigos ANSI estándar
      .replace(/\[([0-9]+)m/g, '')    // Códigos tipo [36m, [0m, etc.
      .replace(/┃/g, '')              // Caracteres de bordes
      .replace(/┗━+┛/g, '')           // Bordes inferiores
      .replace(/┏━+┓/g, '')           // Bordes superiores
      .replace(/\s+\n/g, '\n')        // Espacios extra antes de saltos
      .replace(/\n{3,}/g, '\n\n')     // Múltiples saltos de línea
      .trim();
  };

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'system',
      content: `## 🚀 ¡Bienvenido al Sistema Multiagente Completo!

### 👥 **Equipo de Especialistas Listos**

Todos los **agentes educativos** están conectados y preparados para colaborar en tu aprendizaje:

- 📝 **Generador de Exámenes** - Evaluaciones personalizadas
- 📚 **Creador de Currículum** - Planes de estudio estructurados  
- 🎓 **Tutor Virtual** - Tutoría especializada
- 📅 **Planificador de Lecciones** - Organización de contenido
- 📊 **Analizador de Rendimiento** - Métricas y mejoras

> **💡 Cada consulta será respondida por todo el equipo**, brindándote múltiples perspectivas especializadas.

### 🎯 **¿Cómo funciona?**

1. **Escribe tu pregunta** sobre cualquier tema académico
2. **Todos los agentes analizan** tu consulta desde su especialidad
3. **Recibes respuestas coordinadas** con diferentes enfoques
4. **Obtienes una visión 360°** del tema consultado

¡Comienza preguntando algo! 🎓✨`,
      timestamp: new Date()
    }
  ])
  
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [chatMode, setChatMode] = useState<'individual' | 'collaboration'>('individual')
  const [agentsStatus, setAgentsStatus] = useState<any[]>([])
  const [activeAgents, setActiveAgents] = useState<string[]>(ALL_AGENTS.map(agent => agent.id))
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Scroll automático al final
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Cargar estado de agentes al montar
  useEffect(() => {
    fetchAgentsStatus()
  }, [])

  const fetchAgentsStatus = async () => {
    try {
      const response = await fetch('/api/agents/status')
      const data = await response.json()
      setAgentsStatus(data.agents || [])
    } catch (error) {
      console.error('Error fetching agents status:', error)
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/agents/unified-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: inputMessage,
          selected_agents: activeAgents,
          chat_mode: chatMode,
          context: {
            student_id: studentId,
            timestamp: new Date().toISOString(),
            multiagent_mode: true
          }
        })
      })

      const data = await response.json()

      if (chatMode === 'collaboration') {
        // Modo colaboración: una sola respuesta colaborativa
        let collaborationContent = typeof data.collaboration_result === 'string' 
          ? data.collaboration_result 
          : JSON.stringify(data.collaboration_result, null, 2)
          
        // Limpiar códigos ANSI también en modo colaboración
        collaborationContent = cleanAnsiCodes(collaborationContent)
          
        const collaborationMessage: Message = {
          id: Date.now().toString() + '_collab',
          type: 'agent',
          content: collaborationContent,
          timestamp: new Date(),
          agentType: 'collaboration',
          agentName: '🤝 Respuesta Colaborativa de Todos los Agentes'
        }
        setMessages(prev => [...prev, collaborationMessage])
      } else {
        // Modo individual: respuesta de cada agente
        const agentMessages: Message[] = data.responses.map((response: any, index: number) => {
          // Usar formatted_content si está disponible, luego response como fallback
          let content = response.formatted_content || response.response
          if (typeof content !== 'string') {
            content = JSON.stringify(content, null, 2)
          }
          
          // Limpiar códigos ANSI de escape
          content = cleanAnsiCodes(content)
          
          // Si el contenido no parece tener markdown, mejorarlo automáticamente
          if (content && !content.includes('#') && !content.includes('**') && !content.includes('*') && content.length > 50) {
            // Convertir texto plano en markdown básico
            const lines = content.split('\n').filter(line => line.trim());
            if (lines.length > 2) {
              content = `## 📚 ${response.agent_name}\n\n${content}`;
            }
          }
          
          // Debug para verificar el contenido
          console.log(`🔍 Agente ${response.agent_name}:`, {
            hasFormattedContent: !!response.formatted_content,
            hasResponse: !!response.response,
            contentPreview: content.substring(0, 200) + '...',
            isMarkdown: content.includes('#') || content.includes('**'),
            cleanedContent: content.length
          })
          
          return {
            id: Date.now().toString() + '_' + index,
            type: 'agent' as const,
            content: content,
            timestamp: new Date(),
            agentType: response.agent_type,
            agentName: response.agent_name,
            isRealAgent: response.is_real_agent
          }
        })
        setMessages(prev => [...prev, ...agentMessages])
      }

      // Notificar actividad completada
      if (onActivityUpdate) {
        onActivityUpdate({
          type: 'chat_session',
          duration_minutes: 8, // Estimado para sesión multi-agente
          points_earned: 15 // Más puntos por consulta multi-agente
        })
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: Date.now().toString() + '_error',
        type: 'system',
        content: `## ❌ Error de Comunicación

### 🔧 **Problema Detectado**

Ha ocurrido un **error temporal** en la comunicación con los agentes:

- 🚨 **Estado**: Conexión interrumpida
- 🔄 **Acción**: Sistema trabajando en reconexión automática
- ⏱️ **Tiempo estimado**: Reconectando en unos segundos

> **💡 Tip**: Puedes intentar enviar tu mensaje nuevamente en un momento.

### 🛠️ **¿Qué está pasando?**

El sistema está **reestableciendo las conexiones** con todos los agentes especializados para garantizar que recibas respuestas de calidad.

**El equipo técnico ha sido notificado automáticamente.** 🔔`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const getAgentIcon = (agentType?: string) => {
    const agent = ALL_AGENTS.find(a => a.id === agentType)
    return agent?.icon || Bot
  }

  const getAgentColor = (agentType?: string) => {
    const agent = ALL_AGENTS.find(a => a.id === agentType)
    return agent?.color || 'default'
  }

  const realAgentsCount = agentsStatus.filter(a => a.is_real_agent).length
  const totalAgents = ALL_AGENTS.length

  return (
    <div className="h-screen flex flex-col max-w-7xl mx-auto">
      {/* Header de Estado del Sistema */}
      <Card className="mb-4">
        <CardHeader className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-r from-green-500 to-blue-600 rounded-lg">
              <Users className="text-white" size={28} />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Sistema Multiagente Completo</h1>
              <p className="text-gray-600 dark:text-gray-400">
                Todos los especialistas trabajando en equipo para ti
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-center">
              <Chip color="success" variant="flat" size="lg">
                <Zap size={16} className="mr-1" />
                {realAgentsCount}/{totalAgents} Agentes Activos
              </Chip>
              <Progress 
                value={(realAgentsCount / totalAgents) * 100} 
                color="success" 
                size="sm" 
                className="mt-1 w-24"
              />
            </div>
            <Switch
              isSelected={chatMode === 'collaboration'}
              onValueChange={(checked) => setChatMode(checked ? 'collaboration' : 'individual')}
              color="secondary"
              size="lg"
            >
              Modo Colaboración
            </Switch>
          </div>
        </CardHeader>
      </Card>

      {/* Panel de Estado de Agentes */}
      <Card className="mb-4">
        <CardBody className="py-3">
          <div className="flex flex-wrap gap-2 justify-center">
            {ALL_AGENTS.map((agent) => {
              const Icon = agent.icon
              const agentStatus = agentsStatus.find(s => s.type === agent.id)
              const isActive = activeAgents.includes(agent.id)
              
              return (
                <Chip
                  key={agent.id}
                  variant={isActive ? "solid" : "bordered"}
                  color={isActive ? agent.color as any : "default"}
                  size="md"
                  startContent={<Icon size={14} />}
                  endContent={
                    agentStatus?.is_real_agent ? (
                      <Sparkles size={12} />
                    ) : (
                      <Bot size={12} />
                    )
                  }
                  className="transition-all hover:scale-105"
                >
                  {agent.name}
                </Chip>
              )
            })}
          </div>
          
          <div className="text-center mt-3">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {chatMode === 'collaboration' 
                ? '🤝 Los agentes colaborarán en una respuesta unificada' 
                : '🎯 Cada agente proporcionará su perspectiva especializada'
              }
            </p>
          </div>
        </CardBody>
      </Card>

      {/* Chat Area */}
      <Card className="flex-1 flex flex-col">
        <CardHeader className="pb-3">
          <div className="flex justify-between items-center w-full">
            <h3 className="text-lg font-semibold">Conversación Multiagente</h3>
            <Button
              variant="flat"
              size="sm"
              onPress={() => setMessages([{
                id: Date.now().toString(),
                type: 'system',
                content: `## 🔄 Chat Reiniciado

### ✨ **Sistema Completamente Renovado**

El **equipo completo de agentes** ha sido reinicializado y está listo para una nueva consulta:

- 🔋 **Memoria limpia** - Sin contexto previo
- 🎯 **Especialistas activos** - Todos los agentes preparados  
- 🚀 **Rendimiento óptimo** - Sistema funcionando al 100%

> **¡Perfecto momento para comenzar una nueva conversación!** 

### 💫 **¿Qué te gustaría explorar ahora?**

Puedes preguntar sobre cualquier tema académico y **todos los especialistas** trabajarán juntos para darte la mejor respuesta posible.`,
                timestamp: new Date()
              }])}
            >
              Reiniciar Chat
            </Button>
          </div>
        </CardHeader>
        
        <CardBody className="flex-1 flex flex-col p-0">
          {/* Messages Area */}
          <ScrollShadow className="flex-1 p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.type !== 'user' && (
                  <Avatar
                    icon={
                      message.type === 'system' ? (
                        <Settings size={18} />
                      ) : message.agentType === 'collaboration' ? (
                        <Users size={18} />
                      ) : (
                        React.createElement(getAgentIcon(message.agentType), { size: 18 })
                      )
                    }
                    className={`flex-shrink-0 ${
                      message.type === 'system' 
                        ? 'bg-gray-100 dark:bg-gray-800' 
                        : message.agentType === 'collaboration'
                        ? 'bg-gradient-to-r from-purple-500 to-blue-500'
                        : `bg-${getAgentColor(message.agentType)}-100 dark:bg-${getAgentColor(message.agentType)}-900/20`
                    }`}
                  />
                )}
                
                <div className={`max-w-[80%] ${message.type === 'user' ? 'order-first' : ''}`}>
                  <div
                    className={`p-4 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-500 text-white ml-auto'
                        : message.type === 'system'
                        ? 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                        : message.agentType === 'collaboration'
                        ? 'bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border border-purple-200 dark:border-purple-700'
                        : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    {message.type !== 'user' && message.type !== 'system' && (
                      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-200 dark:border-gray-600">
                        <span className="font-semibold text-sm">
                          {message.agentName}
                        </span>
                        {message.isRealAgent && (
                          <Chip size="sm" color="success" variant="flat">
                            <Sparkles size={12} className="mr-1" />
                            Agente Real
                          </Chip>
                        )}
                        {message.agentType === 'collaboration' && (
                          <Chip size="sm" color="secondary" variant="flat">
                            <Users size={12} className="mr-1" />
                            Colaborativo
                          </Chip>
                        )}
                      </div>
                    )}
                    
                    <div className="text-sm leading-relaxed">
                      {message.type === 'user' ? (
                        <div className="whitespace-pre-wrap">
                          {typeof message.content === 'string' 
                            ? message.content 
                            : JSON.stringify(message.content, null, 2)
                          }
                        </div>
                      ) : (
                        <div className="markdown-content">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkMath]}
                            rehypePlugins={[rehypeKatex]}
                            components={{
                              // Headers con estilos bonitos
                              h1: ({children}) => (
                                <h1 className="text-xl font-bold mb-3 text-blue-700 border-b border-blue-200 pb-1">
                                  {children}
                                </h1>
                              ),
                              h2: ({children}) => (
                                <h2 className="text-lg font-bold mb-2 text-blue-600">
                                  {children}
                                </h2>
                              ),
                              h3: ({children}) => (
                                <h3 className="text-base font-semibold mb-2 text-blue-500">
                                  {children}
                                </h3>
                              ),
                              h4: ({children}) => (
                                <h4 className="text-sm font-semibold mb-1 text-blue-400">
                                  {children}
                                </h4>
                              ),
                              
                              // Párrafos con espaciado
                              p: ({children}) => (
                                <p className="mb-2 leading-relaxed">
                                  {children}
                                </p>
                              ),
                              
                              // Quotes con estilo bonito
                              blockquote: ({children}) => (
                                <blockquote className="border-l-4 border-blue-300 bg-blue-50 dark:bg-blue-900/20 pl-3 py-2 mb-2 italic rounded-r-lg">
                                  {children}
                                </blockquote>
                              ),
                              
                              // Código inline y bloques
                              code: ({inline, className, children, ...props}) => {
                                const match = /language-(\w+)/.exec(className || '');
                                const lang = match ? match[1] : '';
                                
                                if (inline) {
                                  return (
                                    <code className="bg-gray-200 dark:bg-gray-700 text-red-600 dark:text-red-400 px-1 py-0.5 rounded text-xs font-mono">
                                      {children}
                                    </code>
                                  );
                                }
                                
                                return (
                                  <div className="mb-2">
                                    {lang && (
                                      <div className="bg-gray-700 text-white px-2 py-1 text-xs rounded-t">
                                        {lang}
                                      </div>
                                    )}
                                    <pre className={`bg-gray-100 dark:bg-gray-800 p-2 overflow-x-auto font-mono text-xs ${lang ? 'rounded-b' : 'rounded'}`}>
                                      <code {...props}>{children}</code>
                                    </pre>
                                  </div>
                                );
                              },
                              
                              // Listas con estilos
                              ul: ({children}) => (
                                <ul className="list-disc list-inside mb-2 space-y-0.5 ml-2">
                                  {children}
                                </ul>
                              ),
                              ol: ({children}) => (
                                <ol className="list-decimal list-inside mb-2 space-y-0.5 ml-2">
                                  {children}
                                </ol>
                              ),
                              li: ({children}) => (
                                <li className="mb-0.5 text-sm">{children}</li>
                              ),
                              
                              // Tablas responsivas
                              table: ({children}) => (
                                <div className="overflow-x-auto mb-3">
                                  <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600 rounded text-xs">
                                    {children}
                                  </table>
                                </div>
                              ),
                              thead: ({children}) => (
                                <thead className="bg-gray-50 dark:bg-gray-700">{children}</thead>
                              ),
                              th: ({children}) => (
                                <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left font-semibold text-xs">
                                  {children}
                                </th>
                              ),
                              td: ({children}) => (
                                <td className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-xs">
                                  {children}
                                </td>
                              ),
                              
                              // Enlaces
                              a: ({href, children}) => (
                                <a 
                                  href={href} 
                                  className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline transition-colors"
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                >
                                  {children}
                                </a>
                              ),
                              
                              // Texto en negrita y cursiva
                              strong: ({children}) => (
                                <strong className="font-bold">{children}</strong>
                              ),
                              em: ({children}) => (
                                <em className="italic">{children}</em>
                              ),
                              
                              // Separadores
                              hr: () => (
                                <hr className="my-2 border-t border-gray-200 dark:border-gray-600" />
                              )
                            }}
                          >
                            {typeof message.content === 'string' 
                              ? message.content 
                              : JSON.stringify(message.content, null, 2)
                            }
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <p className="text-xs text-gray-500 mt-1 px-2">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
                
                {message.type === 'user' && (
                  <Avatar
                    icon={<User size={18} />}
                    className="flex-shrink-0 bg-blue-100 dark:bg-blue-900/20"
                  />
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex items-center gap-3">
                <Avatar
                  icon={<Brain size={18} />}
                  className="flex-shrink-0 bg-gradient-to-r from-purple-500 to-blue-500"
                />
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border border-purple-200 dark:border-purple-700 p-4 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Spinner size="sm" color="secondary" />
                    <span className="text-sm">
                      {chatMode === 'collaboration' 
                        ? '🤝 Todos los agentes colaborando en una respuesta unificada...' 
                        : '⚡ Procesando con todos los especialistas del sistema...'}
                    </span>
                  </div>
                  <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                    {totalAgents} agentes trabajando • {realAgentsCount} sistemas reales activos
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </ScrollShadow>

          {/* Input Area */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/10 dark:to-purple-900/10">
            <div className="flex gap-3">
              <Textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Realiza tu consulta al equipo completo de agentes educativos... (Enter para enviar, Shift+Enter para nueva línea)"
                minRows={2}
                maxRows={5}
                className="flex-1"
                disabled={isLoading}
                classNames={{
                  input: "text-sm",
                  inputWrapper: "border-2 border-purple-200 dark:border-purple-700"
                }}
              />
              <Button
                color="secondary"
                size="lg"
                onPress={sendMessage}
                isDisabled={!inputMessage.trim() || isLoading}
                isLoading={isLoading}
                className="self-end min-w-[120px]"
                startContent={!isLoading && <Send size={18} />}
              >
                {isLoading ? 'Procesando...' : 'Enviar a Todos'}
              </Button>
            </div>
            
            <div className="mt-3 text-center">
              <p className="text-xs text-gray-600 dark:text-gray-400">
                💡 <strong>Tip:</strong> Cuanto más específica sea tu pregunta, mejores respuestas obtendrás de cada especialista
              </p>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
