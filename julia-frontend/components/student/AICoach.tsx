'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Card, CardBody, CardHeader, Button, Input, Avatar, Chip, Textarea } from '@nextui-org/react'
import { MessageCircle, Send, Brain, Lightbulb, BookOpen, Target, Zap, Sparkles, Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
  suggestions?: string[]
}

interface Props {
  studentData: any
}

export default function AICoach({ studentData }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: `## 🎓 ¡Hola ${studentData?.name || 'estudiante'}!

Soy **Julia**, tu **coach educativo personalizado** con IA. 

### 📊 **He analizado tu progreso y estoy aquí para ayudarte**

**Mi misión:** Ayudarte a alcanzar tus **metas académicas** de forma efectiva y personalizada.

> 💡 **Tip**: Puedo ayudarte con planes de estudio, técnicas de concentración, análisis de progreso y mucho más.

### 🎯 **¿En qué puedo ayudarte hoy?**

**Algunas opciones populares:**
- 📚 Estrategias para materias específicas
- ⏰ Planes de estudio personalizados  
- 🧠 Técnicas de concentración y memoria
- 📈 Análisis de tu progreso académico

¡Cuéntame qué necesitas! 🚀`,
      timestamp: new Date(),
      suggestions: [
        'Ayúdame con mis estudios de Matemáticas',
        'Crear un plan de estudio personalizado',
        'Técnicas para mejorar mi concentración',
        'Revisar mi progreso académico'
      ]
    }
  ])
  
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const coachingTips = [
    {
      icon: <Lightbulb className="text-yellow-500" size={20} />,
      title: 'Técnica Pomodoro',
      description: 'Estudia 25 min, descansa 5. Mejora tu concentración.',
    },
    {
      icon: <Target className="text-blue-500" size={20} />,
      title: 'Metas SMART',
      description: 'Establece objetivos Específicos, Medibles, Alcanzables.',
    },
    {
      icon: <BookOpen className="text-green-500" size={20} />,
      title: 'Repaso Espaciado',
      description: 'Revisa el material en intervalos crecientes.',
    },
    {
      icon: <Zap className="text-purple-500" size={20} />,
      title: 'Mapas Mentales',
      description: 'Organiza información visualmente para mejor comprensión.',
    }
  ]

  const personalizedRecommendations = [
    'Basado en tu estilo de aprendizaje visual, te recomiendo usar diagramas para Matemáticas',
    'Has mejorado 12% en Literatura este mes. ¡Sigue así con la lectura diaria!',
    'Tu mejor horario de estudio es entre 2-4 PM. Programa las materias difíciles en ese momento',
    'Necesitas reforzar Química. Te sugiero 30 minutos extra los martes y jueves'
  ]

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const generateAIResponse = async (userMessage: string): Promise<string> => {
    // Simulamos una respuesta de IA personalizada con markdown bonito
    const responses = {
      matematicas: `## 🔢 ¡Excelente pregunta sobre matemáticas, ${studentData?.name}!

📊 Veo que tu rendimiento actual es del **85%**. Para mejorar aún más, te recomiendo:

### 🎯 **Plan de mejora personalizado:**

1. **📚 Práctica diaria**: 20 minutos resolviendo problemas similares
2. **🏗️ Conceptos base**: Revisa álgebra básica si tienes dudas  
3. **📝 Método paso a paso**: Divide problemas complejos en partes simples
4. **🌟 Aplicación práctica**: Conecta las matemáticas con situaciones reales

> **💡 Tip especial**: Las matemáticas son como un idioma. ¡La práctica constante es la clave!

### 📊 **Tu progresión semanal recomendada:**

| Día | Actividad | Tiempo | Dificultad |
|-----|-----------|--------|------------|
| Lun | Teoría nueva | 30 min | ⭐⭐ |
| Mar | Ejercicios básicos | 25 min | ⭐ |
| Mié | Problemas intermedios | 30 min | ⭐⭐⭐ |
| Jue | Aplicaciones prácticas | 25 min | ⭐⭐ |
| Vie | Evaluación semanal | 20 min | ⭐⭐⭐ |

¿Te gustaría que creemos un plan específico para el tema que más te cuesta?`,

      estudio: `## 📅 ¡Perfecto! Creemos tu plan de estudio personalizado

### 🎯 **Basado en tu perfil de aprendizaje visual y horario optimal:**

#### 🌅 **Lunes a Viernes (Rutina de éxito):**
- **2:00-2:30 PM**: 🔢 Matemáticas (tu mejor hora de concentración)
- **2:30-3:00 PM**: ⏸️ Descanso activo (caminar, estirar)
- **3:00-3:45 PM**: 📖 Literatura (lectura comprensiva)
- **4:00-4:30 PM**: 🔬 Ciencias (experimentos visuales)

#### 🏖️ **Fines de semana (Consolidación):**
- **Sábados**: 📚 Repaso general y práctica intensiva
- **Domingos**: 🗓️ Preparación y planificación de la semana

### 🧠 **Técnicas de estudio recomendadas:**

> **Técnica Pomodoro**: 25 minutos de concentración + 5 minutos de descanso

#### 📋 **Método de estudio por materias:**
- **Matemáticas** → Resolución de problemas paso a paso
- **Literatura** → Mapas conceptuales y resúmenes  
- **Ciencias** → Diagramas y experimentos mentales
- **Historia** → Líneas de tiempo visuales

### 🏆 **Metas semanales:**
- [ ] Completar 90% de las tareas programadas
- [ ] Mantener concentración por bloques de 25 min
- [ ] Revisar y ajustar el plan cada domingo

¿Quieres que ajustemos algo específico de este horario?`,

      concentracion: `## 🧠 ¡Te entiendo perfectamente! La concentración es fundamental

### 🎯 **Técnicas científicamente probadas para ti:**

#### 🍅 **Técnica Pomodoro Personalizada:**
1. **25 minutos** de concentración total 
2. **5 minutos** de descanso activo
3. Repetir 4 ciclos
4. **Descanso largo** de 15-30 minutos

#### 🏠 **Optimización del entorno de estudio:**
- ✅ **Lugar fijo** y organizado
- ✅ **Buena iluminación** natural cuando sea posible
- ✅ **Sin distracciones** (teléfono en modo avión 📱✈️)
- ✅ **Temperatura ideal** entre 20-22°C

#### 💪 **Ejercicios de concentración:**

| Técnica | Descripción | Duración |
|---------|-------------|----------|
| **Respiración 4-7-8** | Inhala 4 seg, mantén 7 seg, exhala 8 seg | 2 min |
| **Meditación breve** | Concentración en la respiración | 5 min |
| **Movimiento previo** | Ejercicio ligero antes de estudiar | 5 min |

#### 🏆 **Sistema de recompensas:**
- Cada Pomodoro completado = ⭐ **1 punto**
- 4 Pomodoros = 🎮 **15 min de entretenimiento**
- Meta diaria alcanzada = 🍕 **Comida favorita**

> **🔥 ¡Increíble!** Tu racha actual de **${studentData?.streak || 12} días** muestra que tienes disciplina. ¡Sigamos fortaleciendo estos hábitos!

¿Cuál de estas técnicas te gustaría probar primero?`,

      progreso: `## 📈 ¡Tu progreso es realmente impresionante!

### � **Análisis de tus fortalezas actuales:**

- ✅ **Rendimiento general**: **${studentData?.overallProgress || 78}%** (¡Muy bueno!)
- ✅ **Racha de estudio**: **${studentData?.streak || 12} días** consecutivos
- ✅ **Estilo de aprendizaje**: Bien definido y aplicado correctamente

### 🎯 **Áreas de oportunidad identificadas:**

| Materia | Actual | Meta | Plan de mejora |
|---------|--------|------|----------------|
| 🧪 Química | 78% | 85% | +30 min martes y jueves |
| 📅 Constancia fines de semana | Variable | Estable | Rutina de 2 horas sábados |
| 🗣️ Participación en clase | Media | Alta | 2 preguntas por clase |

### 🚀 **Próximos objetivos SMART:**

#### 🎯 **Objetivo 1: Promedio general 85%**
- **Plazo**: 1 mes
- **Métrica**: Calificaciones semanales
- **Estado**: 🟡 En progreso (falta 7%)

#### 🎯 **Objetivo 2: Racha de 30 días**
- **Plazo**: 18 días más
- **Métrica**: Días consecutivos de estudio
- **Estado**: 🟢 En excelente camino

#### 🎯 **Objetivo 3: Proyecto de ciencias**
- **Plazo**: 2 semanas
- **Métrica**: Entrega completa y a tiempo
- **Estado**: 🔴 Requiere atención inmediata

### 📊 **Tu curva de aprendizaje:**

\`\`\`
Progreso mensual:
Mes 1: ████████░░ 80%
Mes 2: █████████░ 85%
Mes 3: ██████████ 90% ← Proyección
\`\`\`

> **💡 Insight clave**: Tu mejor día de la semana son los **martes** con 92% de rendimiento. ¡Programa las materias más difíciles ese día!

¿En cuál de estas áreas quieres enfocarte primero?`
    }

    // Detectar el tema de la pregunta
    const message = userMessage.toLowerCase()
    if (message.includes('matemática') || message.includes('álgebra') || message.includes('números')) {
      return responses.matematicas
    } else if (message.includes('plan') || message.includes('estudio') || message.includes('horario')) {
      return responses.estudio
    } else if (message.includes('concentra') || message.includes('foco') || message.includes('atención')) {
      return responses.concentracion
    } else if (message.includes('progreso') || message.includes('rendimiento') || message.includes('resultados')) {
      return responses.progreso
    }

    // Respuesta general personalizada con markdown
    return `## 💭 Entiendo tu consulta, ${studentData?.name}

Como tu **coach educativo personalizado**, he notado que prefieres el aprendizaje **${studentData?.currentLevel || 'visual'}**. 

### 🎯 **Para ayudarte mejor con:** *"${userMessage}"*

**Necesito un poco más de contexto:**

- 📚 **¿En qué materia necesitas apoyo?**
- 🤔 **¿Qué aspecto te resulta más desafiante?**  
- ⚠️ **¿Hay algún tema particular que te preocupa?**

### 📊 **Tu situación actual:**

> **Progreso general**: **${studentData?.overallProgress || 78}%** - ¡Muy bien!
> 
> **Racha de estudio**: **${studentData?.streak || 12} días** - ¡Excelente constancia!

### 🚀 **Mientras tanto, recuerda:**

- ✅ Tu progreso está muy bien encaminado
- ✅ La constancia es tu mejor herramienta  
- ✅ Cada día mejoras un poco más

**¡Sigamos trabajando juntos hacia tus metas académicas!** 🎓✨`
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
    setIsTyping(true)

    // Simular tiempo de respuesta de IA
    setTimeout(async () => {
      const aiResponse = await generateAIResponse(inputMessage)
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: aiResponse,
        timestamp: new Date(),
        suggestions: [
          'Explícame más sobre esto',
          'Dame ejercicios prácticos',
          'Crea un horario para mí',
          'Revisa mi progreso'
        ]
      }

      setMessages(prev => [...prev, aiMessage])
      setIsTyping(false)
    }, 2000)
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInputMessage(suggestion)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="flex items-center justify-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
            <Brain className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Coach Julia IA</h2>
            <p className="text-gray-600 dark:text-gray-400">Tu asistente educativo personal</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Principal */}
        <div className="lg:col-span-2">
          <Card className="julia-card h-[600px] flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <MessageCircle className="text-julia-primary" size={20} />
                <h3 className="text-lg font-semibold">Conversación con Julia</h3>
                <Chip size="sm" color="success" variant="dot">En línea</Chip>
              </div>
            </CardHeader>
            
            <CardBody className="flex-1 flex flex-col p-0">
              {/* Mensajes */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {message.type === 'ai' && (
                      <Avatar
                        icon={<Bot size={20} />}
                        className="bg-gradient-to-r from-purple-500 to-pink-500 text-white flex-shrink-0"
                        size="sm"
                      />
                    )}
                    
                    <div className={`max-w-[80%] ${message.type === 'user' ? 'order-1' : 'order-2'}`}>
                      <div className={`p-3 rounded-2xl ${
                        message.type === 'user' 
                          ? 'bg-julia-primary text-white ml-auto' 
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-white'
                      }`}>
                        {message.type === 'ai' ? (
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
                                code: (codeProps: any) => {
                                  const { inline, className, children, ...props } = codeProps || {};
                                  const match = /language-(\w+)/.exec(className || '');
                                  const lang = match ? match[1] : '';
                                  
                                  if (inline) {
                                    return (
                                      <code className="bg-gray-200 dark:bg-gray-700 text-red-600 dark:text-red-400 px-1 py-0.5 rounded text-sm font-mono">
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
                                      <pre className={`bg-gray-100 dark:bg-gray-800 p-2 overflow-x-auto font-mono text-sm ${lang ? 'rounded-b' : 'rounded'}`}>
                                        <code {...props}>{children}</code>
                                      </pre>
                                    </div>
                                  );
                                },
                                
                                // Listas con estilos
                                ul: ({children}) => (
                                  <ul className="list-disc list-inside mb-2 space-y-1 ml-2">
                                    {children}
                                  </ul>
                                ),
                                ol: ({children}) => (
                                  <ol className="list-decimal list-inside mb-2 space-y-1 ml-2">
                                    {children}
                                  </ol>
                                ),
                                li: ({children}) => (
                                  <li className="mb-1">{children}</li>
                                ),
                                
                                // Tablas responsivas
                                table: ({children}) => (
                                  <div className="overflow-x-auto mb-3">
                                    <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600 rounded">
                                      {children}
                                    </table>
                                  </div>
                                ),
                                thead: ({children}) => (
                                  <thead className="bg-gray-50 dark:bg-gray-700">{children}</thead>
                                ),
                                th: ({children}) => (
                                  <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left font-semibold text-sm">
                                    {children}
                                  </th>
                                ),
                                td: ({children}) => (
                                  <td className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-sm">
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
                                  <hr className="my-3 border-t border-gray-200 dark:border-gray-600" />
                                )
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        )}
                      </div>
                      
                      {message.suggestions && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {message.suggestions.map((suggestion, index) => (
                            <Button
                              key={index}
                              size="sm"
                              variant="flat"
                              color="primary"
                              className="text-xs"
                              onPress={() => handleSuggestionClick(suggestion)}
                            >
                              {suggestion}
                            </Button>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    {message.type === 'user' && (
                      <Avatar
                        icon={<User size={20} />}
                        className="bg-julia-secondary text-white flex-shrink-0"
                        size="sm"
                      />
                    )}
                  </div>
                ))}
                
                {isTyping && (
                  <div className="flex gap-3">
                    <Avatar
                      icon={<Bot size={20} />}
                      className="bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                      size="sm"
                    />
                    <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded-2xl">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input de Mensaje */}
              <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex gap-2">
                  <Textarea
                    placeholder="Pregúntame cualquier cosa sobre tus estudios..."
                    value={inputMessage}
                    onValueChange={setInputMessage}
                    onKeyDown={handleKeyPress}
                    minRows={1}
                    maxRows={3}
                    className="flex-1"
                  />
                  <Button
                    color="primary"
                    isIconOnly
                    onPress={sendMessage}
                    isDisabled={!inputMessage.trim()}
                    className="h-auto"
                  >
                    <Send size={18} />
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Panel Lateral */}
        <div className="space-y-6">
          {/* Tips de Coaching */}
          <Card className="julia-card">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Lightbulb className="text-yellow-500" size={20} />
                <h3 className="text-lg font-semibold">Tips del Coach</h3>
              </div>
            </CardHeader>
            <CardBody className="space-y-4">
              {coachingTips.map((tip, index) => (
                <div key={index} className="flex gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  {tip.icon}
                  <div>
                    <h4 className="font-semibold text-sm text-gray-800 dark:text-white">{tip.title}</h4>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{tip.description}</p>
                  </div>
                </div>
              ))}
            </CardBody>
          </Card>

          {/* Recomendaciones Personalizadas */}
          <Card className="julia-card">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Sparkles className="text-purple-500" size={20} />
                <h3 className="text-lg font-semibold">Para Ti</h3>
              </div>
            </CardHeader>
            <CardBody className="space-y-3">
              {personalizedRecommendations.map((rec, index) => (
                <div key={index} className="p-3 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg">
                  <p className="text-sm text-gray-700 dark:text-gray-300">{rec}</p>
                </div>
              ))}
            </CardBody>
          </Card>

          {/* Estado del Estudiante */}
          <Card className="julia-card">
            <CardHeader>
              <h3 className="text-lg font-semibold">Tu Estado Actual</h3>
            </CardHeader>
            <CardBody className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Nivel de energía</span>
                <Chip color="success" size="sm">Alto</Chip>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Motivación</span>
                <Chip color="primary" size="sm">Excelente</Chip>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Estrés</span>
                <Chip color="success" size="sm">Bajo</Chip>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Confianza</span>
                <Chip color="warning" size="sm">Media</Chip>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  )
}
