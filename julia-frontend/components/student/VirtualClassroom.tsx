'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardBody, CardHeader, Button, Avatar, Badge, Chip, Input, Tabs, Tab } from '@nextui-org/react'
import { Users, Video, MessageCircle, BookOpen, Calendar, Globe, Mic, Camera, Share, Hand } from 'lucide-react'
import { useJuliaAgents } from '@/lib/juliaAgentService'

interface VirtualClassroomProps {
  studentData: any
}

interface ClassSession {
  id: string
  title: string
  subject: string
  teacher: string
  time: string
  duration: number
  participants: number
  status: 'live' | 'upcoming' | 'recorded'
}

interface ClassMessage {
  id: string
  sender: string
  message: string
  timestamp: Date
  type: 'student' | 'teacher' | 'system'
}

export default function VirtualClassroom({ studentData }: VirtualClassroomProps) {
  const [currentSession, setCurrentSession] = useState<ClassSession | null>(null)
  const [sessions, setSessions] = useState<ClassSession[]>([])
  const [messages, setMessages] = useState<ClassMessage[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [isHandRaised, setIsHandRaised] = useState(false)
  const [selectedTab, setSelectedTab] = useState('live')
  const { agentService, logActivity } = useJuliaAgents()

  useEffect(() => {
    loadClassroomData()
  }, [studentData])

  const loadClassroomData = async () => {
    try {
      await logActivity(studentData?.name || 'student_demo', 'virtual_classroom_access')

      // Simular sesiones de clase
      const mockSessions: ClassSession[] = [
        {
          id: '1',
          title: 'Álgebra Avanzada',
          subject: 'Matemáticas',
          teacher: 'Prof. García',
          time: '09:00',
          duration: 50,
          participants: 24,
          status: 'live'
        },
        {
          id: '2', 
          title: 'Química Orgánica',
          subject: 'Química',
          teacher: 'Prof. Martínez',
          time: '11:00',
          duration: 45,
          participants: 18,
          status: 'upcoming'
        },
        {
          id: '3',
          title: 'Literatura Contemporánea',
          subject: 'Literatura',
          teacher: 'Prof. López',
          time: '14:00',
          duration: 40,
          participants: 22,
          status: 'upcoming'
        }
      ]

      setSessions(mockSessions)
      setCurrentSession(mockSessions.find(s => s.status === 'live') || null)

      // Mensajes simulados del chat
      const mockMessages: ClassMessage[] = [
        {
          id: '1',
          sender: 'Prof. García',
          message: 'Buenos días clase, hoy veremos ecuaciones cuadráticas',
          timestamp: new Date(Date.now() - 300000),
          type: 'teacher'
        },
        {
          id: '2',
          sender: 'Ana',
          message: '¿Podría repetir la fórmula por favor?',
          timestamp: new Date(Date.now() - 240000),
          type: 'student'
        },
        {
          id: '3',
          sender: 'Sistema',
          message: 'María se unió a la clase',
          timestamp: new Date(Date.now() - 180000),
          type: 'system'
        }
      ]

      setMessages(mockMessages)
    } catch (error) {
      console.error('Error loading classroom data:', error)
    }
  }

  const sendMessage = async () => {
    if (!newMessage.trim()) return

    const message: ClassMessage = {
      id: Date.now().toString(),
      sender: studentData?.name || 'Estudiante',
      message: newMessage,
      timestamp: new Date(),
      type: 'student'
    }

    setMessages(prev => [...prev, message])
    setNewMessage('')

    await logActivity(studentData?.name || 'student_demo', 'classroom_message', {
      session: currentSession?.id,
      message: newMessage
    })
  }

  const toggleHandRaise = async () => {
    setIsHandRaised(!isHandRaised)
    
    await logActivity(studentData?.name || 'student_demo', 'hand_raised', {
      session: currentSession?.id,
      raised: !isHandRaised
    })

    const systemMessage: ClassMessage = {
      id: Date.now().toString(),
      sender: 'Sistema',
      message: `${studentData?.name || 'Estudiante'} ${isHandRaised ? 'bajó' : 'levantó'} la mano`,
      timestamp: new Date(),
      type: 'system'
    }

    setMessages(prev => [...prev, systemMessage])
  }

  const joinSession = async (session: ClassSession) => {
    setCurrentSession(session)
    
    await logActivity(studentData?.name || 'student_demo', 'join_session', {
      session: session.id,
      subject: session.subject
    })

    const joinMessage: ClassMessage = {
      id: Date.now().toString(),
      sender: 'Sistema',
      message: `${studentData?.name || 'Estudiante'} se unió a la clase`,
      timestamp: new Date(),
      type: 'system'
    }

    setMessages(prev => [...prev, joinMessage])
  }

  return (
    <div className="space-y-6">
      {/* Header del Aula Virtual */}
      <Card className="julia-card">
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
                <Users className="text-white" size={20} />
              </div>
              <div>
                <h3 className="text-lg font-semibold">Aula Virtual Julia</h3>
                <p className="text-sm text-gray-600">
                  {currentSession ? `En vivo: ${currentSession.title}` : 'No hay sesión activa'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge content={sessions.filter(s => s.status === 'live').length} color="danger">
                <Chip color="success" size="sm">
                  {sessions.filter(s => s.status === 'live').length} En Vivo
                </Chip>
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Navegación */}
      <Tabs selectedKey={selectedTab} onSelectionChange={setSelectedTab}>
        <Tab 
          key="live" 
          title={
            <div className="flex items-center gap-2">
              <Video size={16} />
              <span>Sesión Actual</span>
            </div>
          }
        />
        <Tab 
          key="schedule" 
          title={
            <div className="flex items-center gap-2">
              <Calendar size={16} />
              <span>Horario</span>
            </div>
          }
        />
        <Tab 
          key="resources" 
          title={
            <div className="flex items-center gap-2">
              <BookOpen size={16} />
              <span>Recursos</span>
            </div>
          }
        />
      </Tabs>

      {/* Contenido basado en la pestaña */}
      {selectedTab === 'live' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Área de Video Principal */}
          <div className="lg:col-span-2 space-y-4">
            <Card className="julia-card">
              <CardBody>
                {currentSession ? (
                  <div>
                    <div className="aspect-video bg-gradient-to-br from-blue-900 to-purple-900 rounded-lg flex items-center justify-center mb-4">
                      <div className="text-center text-white">
                        <Video size={48} className="mx-auto mb-4" />
                        <h3 className="text-xl font-semibold">{currentSession.title}</h3>
                        <p className="text-blue-200">{currentSession.teacher}</p>
                        <Badge color="success" className="mt-2">EN VIVO</Badge>
                      </div>
                    </div>
                    
                    {/* Controles de Video */}
                    <div className="flex items-center justify-center gap-4">
                      <Button 
                        color="primary" 
                        variant="flat"
                        startContent={<Mic size={16} />}
                      >
                        Micrófono
                      </Button>
                      <Button 
                        color="primary" 
                        variant="flat"
                        startContent={<Camera size={16} />}
                      >
                        Cámara
                      </Button>
                      <Button 
                        color={isHandRaised ? 'warning' : 'default'} 
                        variant={isHandRaised ? 'solid' : 'flat'}
                        startContent={<Hand size={16} />}
                        onPress={toggleHandRaise}
                      >
                        {isHandRaised ? 'Bajar mano' : 'Levantar mano'}
                      </Button>
                      <Button 
                        color="secondary" 
                        variant="flat"
                        startContent={<Share size={16} />}
                      >
                        Compartir
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="aspect-video bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <Globe size={48} className="mx-auto mb-4 opacity-50" />
                      <h3 className="text-lg font-medium">No hay sesión activa</h3>
                      <p className="text-sm">Revisa tu horario para próximas clases</p>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>

            {/* Participantes */}
            <Card className="julia-card">
              <CardHeader>
                <h4 className="font-semibold">Participantes ({currentSession?.participants || 0})</h4>
              </CardHeader>
              <CardBody>
                <div className="grid grid-cols-6 gap-3">
                  {[...Array(Math.min(currentSession?.participants || 0, 12))].map((_, i) => (
                    <div key={i} className="text-center">
                      <Avatar 
                        name={`E${i + 1}`} 
                        size="sm" 
                        className={i === 0 ? "ring-2 ring-blue-500" : ""}
                      />
                      <p className="text-xs mt-1 truncate">
                        {i === 0 ? (studentData?.name || 'Tú') : `Estudiante ${i + 1}`}
                      </p>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          </div>

          {/* Chat de la Clase */}
          <div className="space-y-4">
            <Card className="julia-card">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <MessageCircle size={16} />
                  <h4 className="font-semibold">Chat de Clase</h4>
                </div>
              </CardHeader>
              <CardBody>
                <div className="h-64 overflow-y-auto mb-4 space-y-2">
                  {messages.map((msg) => (
                    <div key={msg.id} className={`p-2 rounded text-sm ${
                      msg.type === 'teacher' 
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-500' 
                        : msg.type === 'system'
                        ? 'bg-gray-50 dark:bg-gray-800 text-gray-600 text-center'
                        : 'bg-green-50 dark:bg-green-900/20'
                    }`}>
                      <div className="flex justify-between items-start">
                        <span className="font-medium text-xs">
                          {msg.sender}
                        </span>
                        <span className="text-xs text-gray-500">
                          {msg.timestamp.toLocaleTimeString().slice(0, 5)}
                        </span>
                      </div>
                      <p className="mt-1">{msg.message}</p>
                    </div>
                  ))}
                </div>
                
                <div className="flex gap-2">
                  <Input
                    placeholder="Escribe un mensaje..."
                    value={newMessage}
                    onValueChange={setNewMessage}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        sendMessage()
                      }
                    }}
                    className="flex-1"
                  />
                  <Button 
                    color="primary" 
                    onPress={sendMessage}
                    isDisabled={!newMessage.trim()}
                  >
                    Enviar
                  </Button>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      )}

      {selectedTab === 'schedule' && (
        <Card className="julia-card">
          <CardHeader>
            <h3 className="text-lg font-semibold">Horario de Clases</h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {sessions.map((session) => (
                <div 
                  key={session.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold">{session.time}</div>
                      <div className="text-xs text-gray-500">{session.duration}min</div>
                    </div>
                    <div>
                      <h4 className="font-medium">{session.title}</h4>
                      <p className="text-sm text-gray-600">{session.teacher} • {session.subject}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Users size={12} />
                        <span className="text-xs">{session.participants} participantes</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Chip 
                      color={
                        session.status === 'live' ? 'success' : 
                        session.status === 'upcoming' ? 'warning' : 'default'
                      }
                      size="sm"
                    >
                      {session.status === 'live' ? 'En Vivo' : 
                       session.status === 'upcoming' ? 'Próxima' : 'Grabada'}
                    </Chip>
                    <Button 
                      color="primary" 
                      size="sm"
                      onPress={() => joinSession(session)}
                      isDisabled={session.status === 'recorded'}
                    >
                      {session.status === 'live' ? 'Unirse' : 'Programar'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {selectedTab === 'resources' && (
        <Card className="julia-card">
          <CardHeader>
            <h3 className="text-lg font-semibold">Recursos de Clase</h3>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg">
                <BookOpen className="text-blue-500 mb-2" size={24} />
                <h4 className="font-medium">Material de Estudio</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Accede a presentaciones, ejercicios y recursos complementarios
                </p>
                <Button color="primary" size="sm" className="mt-2">
                  Ver Recursos
                </Button>
              </div>
              
              <div className="p-4 border rounded-lg">
                <Video className="text-green-500 mb-2" size={24} />
                <h4 className="font-medium">Grabaciones</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Revisa clases anteriores y repasa conceptos importantes
                </p>
                <Button color="success" size="sm" className="mt-2">
                  Ver Grabaciones
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Estado del Sistema */}
      <Card className="border-2 border-dashed border-gray-300 dark:border-gray-600">
        <CardBody className="text-center">
          <p className="text-gray-600 dark:text-gray-400">
            🎓 <strong>Aula Virtual Julia:</strong> {currentSession ? 'Conectado a sesión en vivo' : 'Esperando próxima clase'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Sistema de videoconferencia integrado con seguimiento de participación
          </p>
        </CardBody>
      </Card>
    </div>
  )
}
