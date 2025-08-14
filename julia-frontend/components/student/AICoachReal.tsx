'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Card, CardBody, CardHeader, Button, Input, Avatar, Spinner, Chip, Textarea } from '@nextui-org/react'
import { Send, Brain, Sparkles, MessageCircle, Lightbulb, Target } from 'lucide-react'
import { useJuliaAgents } from '@/lib/juliaAgentService'

interface AICoachProps {
  studentData: any
}

interface Message {
  id: string
  content: string
  sender: 'student' | 'coach'
  timestamp: Date
  type?: 'text' | 'recommendation' | 'analysis'
  metadata?: any
}

export default function AICoach({ studentData }: AICoachProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [coachingSession, setCoachingSession] = useState<any>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { agentService, logActivity } = useJuliaAgents()

  useEffect(() => {
    initializeCoach()
  }, [studentData])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const initializeCoach = async () => {
    try {
      setIsLoading(true)
      
      // Log de actividad
      await logActivity(studentData?.name || 'student_demo', 'ai_coach_init')

      // Inicializar sesión de coaching con el agente real
      const session = await agentService.getStudentCoaching(
        studentData?.name || 'student_demo',
        {
          type: 'coaching_session_init',
          student_context: {
            name: studentData?.name,
            grade: studentData?.grade,
            current_time: new Date().toISOString()
          }
        }
      )

      setCoachingSession(session)

      // Mensaje de bienvenida del coach IA
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        content: session?.welcome_message || `¡Hola ${studentData?.name || 'estudiante'}! 👋 Soy tu Coach IA personalizado. Estoy aquí para ayudarte a alcanzar tus objetivos académicos. ¿En qué puedo ayudarte hoy?`,
        sender: 'coach',
        timestamp: new Date(),
        type: 'text',
        metadata: { source: 'ai_agent_initialization' }
      }

      setMessages([welcomeMessage])

      // Si hay recomendaciones iniciales del agente
      if (session?.initial_recommendations?.length > 0) {
        const recMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: 'Basándome en tu progreso reciente, tengo algunas recomendaciones personalizadas para ti:',
          sender: 'coach',
          timestamp: new Date(),
          type: 'recommendation',
          metadata: { 
            recommendations: session.initial_recommendations,
            source: 'ai_agent_analysis'
          }
        }
        setMessages(prev => [...prev, recMessage])
      }

      setIsInitialized(true)
    } catch (error) {
      console.error('Error initializing coach:', error)
      
      // Mensaje de fallback
      const fallbackMessage: Message = {
        id: Date.now().toString(),
        content: '¡Hola! Soy tu Coach IA. Estoy conectándome con el sistema Julia para brindarte la mejor ayuda personalizada. ¡Pregúntame lo que necesites!',
        sender: 'coach',
        timestamp: new Date(),
        type: 'text',
        metadata: { source: 'fallback' }
      }
      setMessages([fallbackMessage])
      setIsInitialized(true)
    } finally {
      setIsLoading(false)
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: 'student',
      timestamp: new Date(),
      type: 'text'
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      // Log de la interacción real
      await logActivity(studentData?.name || 'student_demo', 'ai_coach_interaction', {
        question: inputMessage,
        timestamp: new Date().toISOString()
      })

      // Obtener respuesta del agente coach real
      const response = await agentService.getStudentCoaching(
        studentData?.name || 'student_demo',
        {
          type: 'interactive_coaching',
          message: inputMessage,
          conversation_history: messages.slice(-5), // Últimos 5 mensajes para contexto
          session_id: coachingSession?.session_id
        }
      )

      // Procesar respuesta del agente
      const coachResponse: Message = {
        id: Date.now().toString(),
        content: response?.response || response?.guidance || 'Permíteme analizar tu situación para darte la mejor recomendación...',
        sender: 'coach',
        timestamp: new Date(),
        type: response?.type || 'text',
        metadata: {
          confidence: response?.confidence,
          recommendations: response?.recommendations,
          insights: response?.insights,
          source: 'ai_agent_response'
        }
      }

      setMessages(prev => [...prev, coachResponse])

      // Si hay análisis adicional, agregarlo
      if (response?.analysis) {
        const analysisMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: response.analysis,
          sender: 'coach',
          timestamp: new Date(),
          type: 'analysis',
          metadata: { source: 'ai_agent_analysis' }
        }
        setTimeout(() => {
          setMessages(prev => [...prev, analysisMessage])
        }, 1000)
      }

    } catch (error) {
      console.error('Error getting coach response:', error)
      
      // Respuesta de fallback
      const errorResponse: Message = {
        id: Date.now().toString(),
        content: 'Estoy procesando tu consulta con el sistema Julia. Mientras tanto, ¿podrías darme más detalles sobre lo que necesitas?',
        sender: 'coach',
        timestamp: new Date(),
        type: 'text',
        metadata: { source: 'error_fallback' }
      }
      setMessages(prev => [...prev, errorResponse])
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickQuestion = async (question: string) => {
    setInputMessage(question)
    setTimeout(() => sendMessage(), 100)
  }

  const renderMessage = (message: Message) => {
    const isCoach = message.sender === 'coach'
    
    return (
      <div key={message.id} className={`flex ${isCoach ? 'justify-start' : 'justify-end'} mb-4`}>
        <div className={`flex items-start gap-3 max-w-[80%] ${isCoach ? 'flex-row' : 'flex-row-reverse'}`}>
          {isCoach && (
            <Avatar
              icon={<Brain size={20} />}
              className="bg-gradient-to-r from-purple-500 to-blue-500"
              size="sm"
            />
          )}
          
          <div className={`px-4 py-3 rounded-lg ${
            isCoach 
              ? 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200' 
              : 'bg-blue-500 text-white'
          }`}>
            <p className="text-sm">{message.content}</p>
            
            {/* Mostrar recomendaciones si las hay */}
            {message.type === 'recommendation' && message.metadata?.recommendations && (
              <div className="mt-3 space-y-2">
                {message.metadata.recommendations.map((rec: string, index: number) => (
                  <div key={index} className="flex items-start gap-2 text-xs bg-blue-50 dark:bg-blue-900/20 p-2 rounded">
                    <Lightbulb size={12} className="text-blue-500 mt-0.5" />
                    <span className="text-blue-700 dark:text-blue-300">{rec}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Mostrar insights si los hay */}
            {message.metadata?.insights && (
              <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs">
                <div className="flex items-center gap-1 text-green-700 dark:text-green-300">
                  <Sparkles size={12} />
                  <span className="font-medium">Insight:</span>
                </div>
                <p className="text-green-600 dark:text-green-400 mt-1">{message.metadata.insights}</p>
              </div>
            )}

            <div className="flex items-center justify-between mt-2">
              <span className="text-xs opacity-60">
                {message.timestamp.toLocaleTimeString()}
              </span>
              {message.metadata?.source && (
                <Chip size="sm" variant="flat" className="text-xs">
                  {message.metadata.source === 'ai_agent_response' ? 'IA Real' : 'Sistema'}
                </Chip>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <Spinner size="lg" color="primary" />
          <p className="mt-4 text-gray-600">Inicializando Coach IA...</p>
          <p className="text-sm text-gray-500">Conectando con agentes de Julia</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header del Coach */}
      <Card className="julia-card">
        <CardHeader>
          <div className="flex items-center gap-3">
            <Avatar
              icon={<Brain size={24} />}
              className="bg-gradient-to-r from-purple-500 to-blue-500"
            />
            <div>
              <h3 className="text-lg font-semibold">Coach IA Personalizado</h3>
              <p className="text-sm text-gray-600">
                Conectado con sistema Julia • {isInitialized ? 'Activo' : 'Inicializando'}
              </p>
            </div>
            <div className="ml-auto">
              <Chip color="success" size="sm">En línea</Chip>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Área de Chat */}
      <Card className="julia-card">
        <CardBody>
          <div className="h-96 overflow-y-auto p-4 border border-gray-200 dark:border-gray-700 rounded-lg mb-4">
            {messages.map(renderMessage)}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="flex items-center gap-3">
                  <Avatar
                    icon={<Brain size={20} />}
                    className="bg-gradient-to-r from-purple-500 to-blue-500"
                    size="sm"
                  />
                  <div className="bg-gray-100 dark:bg-gray-800 px-4 py-3 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Spinner size="sm" />
                      <span className="text-sm text-gray-600">Analizando con IA...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input de Mensaje */}
          <div className="flex gap-2">
            <Textarea
              value={inputMessage}
              onValueChange={setInputMessage}
              placeholder="Escribe tu pregunta o inquietud..."
              className="flex-1"
              minRows={1}
              maxRows={3}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
            />
            <Button
              color="primary"
              onPress={sendMessage}
              isLoading={isLoading}
              isDisabled={!inputMessage.trim()}
              className="self-end"
            >
              <Send size={16} />
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Preguntas Rápidas */}
      <Card className="julia-card">
        <CardHeader>
          <h4 className="font-semibold">💬 Preguntas Frecuentes</h4>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <Button
              variant="flat"
              size="sm"
              onPress={() => handleQuickQuestion('¿Cómo puedo mejorar mis calificaciones?')}
              className="justify-start h-auto p-3"
            >
              <Target size={16} className="mr-2" />
              <span className="text-left">¿Cómo puedo mejorar mis calificaciones?</span>
            </Button>
            
            <Button
              variant="flat"
              size="sm"
              onPress={() => handleQuickQuestion('¿Qué estrategias de estudio me recomiendas?')}
              className="justify-start h-auto p-3"
            >
              <Lightbulb size={16} className="mr-2" />
              <span className="text-left">¿Qué estrategias de estudio me recomiendas?</span>
            </Button>
            
            <Button
              variant="flat"
              size="sm"
              onPress={() => handleQuickQuestion('¿Cómo manejo el estrés académico?')}
              className="justify-start h-auto p-3"
            >
              <MessageCircle size={16} className="mr-2" />
              <span className="text-left">¿Cómo manejo el estrés académico?</span>
            </Button>
            
            <Button
              variant="flat"
              size="sm"
              onPress={() => handleQuickQuestion('¿Cuáles son mis fortalezas académicas?')}
              className="justify-start h-auto p-3"
            >
              <Sparkles size={16} className="mr-2" />
              <span className="text-left">¿Cuáles son mis fortalezas académicas?</span>
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Estado del Sistema */}
      <Card className="border-2 border-dashed border-gray-300 dark:border-gray-600">
        <CardBody className="text-center">
          <p className="text-gray-600 dark:text-gray-400">
            🤖 <strong>Coach IA Julia:</strong> {coachingSession ? 'Sesión activa' : 'Inicializando'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Powered by Sistema Multiagente Julia • Respuestas en tiempo real
          </p>
        </CardBody>
      </Card>
    </div>
  )
}
