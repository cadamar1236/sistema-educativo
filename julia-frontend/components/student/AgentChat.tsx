'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { 
  Card, 
  CardBody, 
  CardHeader, 
  Button, 
  Input, 
  Textarea, 
  Chip, 
  Avatar, 
  ScrollShadow,
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
  Switch,
  Divider,
  Spinner
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
  Calendar
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

// Tipos de agentes disponibles
const AGENT_TYPES = [
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

interface AgentChatProps {
  onActivityUpdate?: (activity: {
    type?: 'lesson' | 'exercise' | 'quiz' | 'chat_session';
    subject?: string;
    duration_minutes?: number;
    points_earned?: number;
    success_rate?: number;
  }) => void;
}

export default function AgentChat({ onActivityUpdate }: AgentChatProps) {
  const { user } = useAuth() as any
  const studentId = user?.id
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'system',
      content: '¡Bienvenido al Chat de Agentes Educativos! Selecciona uno o más agentes y comienza a chatear.',
      timestamp: new Date()
    }
  ])
  
  const [inputMessage, setInputMessage] = useState('')
  const [selectedAgents, setSelectedAgents] = useState<string[]>(['tutor'])
  const [chatMode, setChatMode] = useState<'individual' | 'collaboration'>('individual')
  const [isLoading, setIsLoading] = useState(false)
  const [agentsStatus, setAgentsStatus] = useState<any[]>([])
  
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
    if (!inputMessage.trim() || selectedAgents.length === 0) return

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
          selected_agents: selectedAgents,
          chat_mode: chatMode,
          context: {
            student_id: studentId,
            timestamp: new Date().toISOString()
          }
        })
      })

      const data = await response.json()

      if (chatMode === 'collaboration') {
        // Modo colaboración: una sola respuesta
        const collaborationContent = typeof data.collaboration_result === 'string' 
          ? data.collaboration_result 
          : JSON.stringify(data.collaboration_result, null, 2)
          
        const collaborationMessage: Message = {
          id: Date.now().toString() + '_collab',
          type: 'agent',
          content: collaborationContent,
          timestamp: new Date(),
          agentType: 'collaboration',
          agentName: 'Colaboración Multi-Agente'
        }
        setMessages(prev => [...prev, collaborationMessage])
      } else {
        // Modo individual: múltiples respuestas
        const agentMessages: Message[] = data.responses.map((response: any, index: number) => {
          // Usar formatted_content si está disponible, luego response como fallback
          let content = response.formatted_content || response.response
          if (typeof content !== 'string') {
            content = JSON.stringify(content, null, 2)
          }
          
          // Si el contenido no parece tener markdown, mejorarlo automáticamente
          if (content && !content.includes('#') && !content.includes('**') && !content.includes('*') && content.length > 50) {
            content = `## 📚 ${response.agent_name}\n\n${content}`;
          }
          
          // Debug para verificar el contenido
          console.log(`🔍 AgentChat - ${response.agent_name}:`, {
            hasFormattedContent: !!response.formatted_content,
            hasResponse: !!response.response,
            contentPreview: content.substring(0, 100) + '...',
            isMarkdown: content.includes('#') || content.includes('**')
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
          duration_minutes: 5, // Estimado para una sesión de chat
          points_earned: 10
        })
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: Date.now().toString() + '_error',
        type: 'system',
        content: 'Error al comunicarse con los agentes. Por favor, intenta de nuevo.',
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

  const toggleAgent = (agentId: string) => {
    setSelectedAgents(prev => 
      prev.includes(agentId) 
        ? prev.filter(id => id !== agentId)
        : [...prev, agentId]
    )
  }

  const selectAllAgents = () => {
    setSelectedAgents(AGENT_TYPES.map(agent => agent.id))
  }

  const clearAgents = () => {
    setSelectedAgents([])
  }

  const getAgentIcon = (agentType?: string) => {
    const agent = AGENT_TYPES.find(a => a.id === agentType)
    return agent?.icon || Bot
  }

  const getAgentColor = (agentType?: string) => {
    const agent = AGENT_TYPES.find(a => a.id === agentType)
    return agent?.color || 'default'
  }

  return (
    <div className="h-screen flex flex-col max-w-7xl mx-auto p-4">
      {/* Header */}
      <Card className="mb-4">
        <CardHeader className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
              <MessageSquare className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Chat de Agentes Educativos</h1>
              <p className="text-gray-600 dark:text-gray-400">
                Interactúa con múltiples agentes especializados
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Chip color="success" variant="flat">
              {agentsStatus.filter(a => a.is_real_agent).length} Agentes Reales
            </Chip>
            <Switch
              isSelected={chatMode === 'collaboration'}
              onValueChange={(checked) => setChatMode(checked ? 'collaboration' : 'individual')}
              color="secondary"
            >
              Modo Colaboración
            </Switch>
          </div>
        </CardHeader>
      </Card>

      <div className="flex-1 flex gap-4">
        {/* Panel de Agentes */}
        <Card className="w-80 flex-shrink-0">
          <CardHeader className="pb-3">
            <div className="flex justify-between items-center w-full">
              <h3 className="text-lg font-semibold">Agentes Disponibles</h3>
              <div className="flex gap-2">
                <Button size="sm" variant="flat" onPress={selectAllAgents}>
                  Todos
                </Button>
                <Button size="sm" variant="flat" onPress={clearAgents}>
                  Limpiar
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardBody className="space-y-3">
            {AGENT_TYPES.map((agent) => {
              const Icon = agent.icon
              const isSelected = selectedAgents.includes(agent.id)
              const agentStatus = agentsStatus.find(s => s.type === agent.id)
              
              return (
                <div
                  key={agent.id}
                  className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
                    isSelected 
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                  onClick={() => toggleAgent(agent.id)}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg bg-${agent.color}-100 dark:bg-${agent.color}-900/20`}>
                      <Icon className={`text-${agent.color}-600`} size={20} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-sm">{agent.name}</h4>
                        {agentStatus?.is_real_agent && (
                          <Chip size="sm" color="success" variant="flat">Real</Chip>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        {agent.description}
                      </p>
                    </div>
                  </div>
                </div>
              )
            })}
            
            <Divider className="my-4" />
            
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {selectedAgents.length} agente(s) seleccionado(s)
              </p>
              {chatMode === 'collaboration' && (
                <Chip color="secondary" variant="flat" className="mt-2">
                  <Users size={14} className="mr-1" />
                  Modo Colaboración Activo
                </Chip>
              )}
            </div>
          </CardBody>
        </Card>

        {/* Chat Area */}
        <Card className="flex-1 flex flex-col">
          <CardHeader className="pb-3">
            <div className="flex justify-between items-center w-full">
              <h3 className="text-lg font-semibold">Conversación</h3>
              <Button
                variant="flat"
                size="sm"
                onPress={() => setMessages([{
                  id: Date.now().toString(),
                  type: 'system',
                  content: 'Chat reiniciado. ¡Comienza una nueva conversación!',
                  timestamp: new Date()
                }])}
              >
                Limpiar Chat
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
                        ) : (
                          React.createElement(getAgentIcon(message.agentType), { size: 18 })
                        )
                      }
                      className={`flex-shrink-0 ${
                        message.type === 'system' 
                          ? 'bg-gray-100 dark:bg-gray-800' 
                          : `bg-${getAgentColor(message.agentType)}-100 dark:bg-${getAgentColor(message.agentType)}-900/20`
                      }`}
                    />
                  )}
                  
                  <div className={`max-w-[80%] ${message.type === 'user' ? 'order-first' : ''}`}>
                    <div
                      className={`p-3 rounded-lg ${
                        message.type === 'user'
                          ? 'bg-blue-500 text-white ml-auto'
                          : message.type === 'system'
                          ? 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                          : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                      }`}
                    >
                      {message.type !== 'user' && message.type !== 'system' && (
                        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-200 dark:border-gray-600">
                          <span className="font-semibold text-sm">
                            {message.agentName}
                          </span>
                          {message.isRealAgent && (
                            <Chip size="sm" color="success" variant="flat">
                              <Sparkles size={12} className="mr-1" />
                              Real
                            </Chip>
                          )}
                        </div>
                      )}
                      
                      <div className="text-sm">
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
                                  <h1 className="text-lg font-bold mb-3 text-blue-700 border-b border-blue-200 pb-1">
                                    {children}
                                  </h1>
                                ),
                                h2: ({children}) => (
                                  <h2 className="text-base font-bold mb-2 text-blue-600">
                                    {children}
                                  </h2>
                                ),
                                h3: ({children}) => (
                                  <h3 className="text-sm font-semibold mb-2 text-blue-500">
                                    {children}
                                  </h3>
                                ),
                                h4: ({children}) => (
                                  <h4 className="text-xs font-semibold mb-1 text-blue-400">
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
                                code: (codeProps) => {
                                  const { className, children, ...rest } = codeProps as any
                                  const match = /language-(\w+)/.exec(className || '');
                                  const lang = match ? match[1] : '';
                                  const isInline = 'inline' in (codeProps as any) ? (codeProps as any).inline : false
                                  if (isInline) {
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
                                        <code {...rest}>{children}</code>
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
                    icon={<Bot size={18} />}
                    className="flex-shrink-0 bg-gray-100 dark:bg-gray-800"
                  />
                  <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-3 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Spinner size="sm" />
                      <span className="text-sm">
                        {chatMode === 'collaboration' 
                          ? 'Agentes colaborando...' 
                          : 'Agentes procesando...'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </ScrollShadow>

            {/* Input Area */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex gap-3">
                <Textarea
                  // @ts-ignore adapt generic ref
                  ref={inputRef as any}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Escribe tu mensaje aquí... (Enter para enviar, Shift+Enter para nueva línea)"
                  minRows={1}
                  maxRows={4}
                  className="flex-1"
                  disabled={isLoading || selectedAgents.length === 0}
                />
                <Button
                  color="primary"
                  onPress={sendMessage}
                  isDisabled={!inputMessage.trim() || selectedAgents.length === 0 || isLoading}
                  isLoading={isLoading}
                  className="self-end"
                >
                  <Send size={18} />
                </Button>
              </div>
              
              {selectedAgents.length === 0 && (
                <p className="text-sm text-red-500 mt-2">
                  Selecciona al menos un agente para comenzar a chatear
                </p>
              )}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
