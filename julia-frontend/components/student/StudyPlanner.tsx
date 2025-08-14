'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardBody, CardHeader, Button, Input, Textarea, Select, SelectItem, Chip, DatePicker, Spinner, Progress } from '@nextui-org/react'
import { Calendar, Clock, BookOpen, Target, Plus, CheckCircle, AlertCircle, Edit, Trash2, Brain, Lightbulb, TrendingUp } from 'lucide-react'
import { useJuliaAgents } from '@/lib/juliaAgentService'

interface Task {
  id: string
  title: string
  subject: string
  dueDate: string
  priority: 'alta' | 'media' | 'baja'
  status: 'pendiente' | 'en-progreso' | 'completada'
  estimatedTime: number
  description?: string
  aiGenerated?: boolean
  difficulty?: number
  prerequisites?: string[]
}

interface StudyPlan {
  id: string
  title: string
  subject: string
  totalHours: number
  weeklyGoal: number
  topics: string[]
  progress: number
  createdByAI: boolean
}

interface StudyPlannerProps {
  studentData: any
}

export default function StudyPlanner({ studentData }: StudyPlannerProps) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [studyPlans, setStudyPlans] = useState<StudyPlan[]>([])
  const [isLoadingAI, setIsLoadingAI] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [showPlanForm, setShowPlanForm] = useState(false)
  const [selectedTab, setSelectedTab] = useState('tasks')
  const { agentService, logActivity } = useJuliaAgents()

  const [newTask, setNewTask] = useState<Partial<Task>>({
    title: '',
    subject: '',
    priority: 'media',
    estimatedTime: 60,
    description: ''
  })

  const [newPlan, setNewPlan] = useState({
    subject: '',
    goal: '',
    timeframe: 'week',
    currentLevel: 'beginner'
  })

  useEffect(() => {
    loadStudyData()
  }, [studentData])

  const loadStudyData = async () => {
    try {
      await logActivity(studentData?.name || 'student_demo', 'study_planner_access')

      // Cargar tareas iniciales (simuladas)
      const initialTasks: Task[] = [
        {
          id: '1',
          title: 'Ensayo de Literatura',
          subject: 'Literatura',
          dueDate: '2024-01-20',
          priority: 'alta',
          status: 'en-progreso',
          estimatedTime: 120,
          description: 'Análisis de "Cien años de soledad"',
          difficulty: 7,
          prerequisites: ['Lectura del libro', 'Investigación del autor']
        },
        {
          id: '2',
          title: 'Ejercicios de Álgebra',
          subject: 'Matemáticas',
          dueDate: '2024-01-18',
          priority: 'media',
          status: 'pendiente',
          estimatedTime: 60,
          description: 'Capítulo 5: Ecuaciones cuadráticas',
          difficulty: 5,
          aiGenerated: true
        }
      ]

      setTasks(initialTasks)

      // Cargar planes de estudio
      const mockPlans: StudyPlan[] = [
        {
          id: '1',
          title: 'Dominar Cálculo Diferencial',
          subject: 'Matemáticas',
          totalHours: 40,
          weeklyGoal: 8,
          topics: ['Límites', 'Derivadas', 'Aplicaciones'],
          progress: 35,
          createdByAI: true
        }
      ]

      setStudyPlans(mockPlans)
    } catch (error) {
      console.error('Error loading study data:', error)
    }
  }

  const generateAIStudyPlan = async () => {
    if (!newPlan.subject || !newPlan.goal) return

    setIsLoadingAI(true)
    try {
      await logActivity(studentData?.name || 'student_demo', 'ai_study_plan_request', {
        subject: newPlan.subject,
        goal: newPlan.goal,
        level: newPlan.currentLevel
      })

      // Simular respuesta del agente de planificación
      const aiPlan: StudyPlan = {
        id: Date.now().toString(),
        title: `Plan de Estudio: ${newPlan.goal}`,
        subject: newPlan.subject,
        totalHours: newPlan.timeframe === 'week' ? 10 : 40,
        weeklyGoal: newPlan.timeframe === 'week' ? 10 : 8,
        topics: generateTopicsForSubject(newPlan.subject),
        progress: 0,
        createdByAI: true
      }

      setStudyPlans(prev => [...prev, aiPlan])

      // Generar tareas automáticamente del plan
      const aiTasks = generateTasksFromPlan(aiPlan)
      setTasks(prev => [...prev, ...aiTasks])

      setShowPlanForm(false)
      setNewPlan({ subject: '', goal: '', timeframe: 'week', currentLevel: 'beginner' })
      
    } catch (error) {
      console.error('Error generating AI study plan:', error)
    } finally {
      setIsLoadingAI(false)
    }
  }

  const generateTopicsForSubject = (subject: string): string[] => {
    const topicMap: { [key: string]: string[] } = {
      'Matemáticas': ['Fundamentos', 'Práctica', 'Aplicaciones', 'Evaluación'],
      'Literatura': ['Lectura', 'Análisis', 'Redacción', 'Crítica'],
      'Química': ['Teoría', 'Experimentos', 'Fórmulas', 'Aplicaciones'],
      'Física': ['Conceptos', 'Problemas', 'Laboratorio', 'Proyecto'],
      'Historia': ['Investigación', 'Cronología', 'Análisis', 'Ensayo'],
      'Inglés': ['Vocabulario', 'Gramática', 'Conversación', 'Escritura']
    }
    return topicMap[subject] || ['Estudio', 'Práctica', 'Evaluación', 'Repaso']
  }

  const generateTasksFromPlan = (plan: StudyPlan): Task[] => {
    return plan.topics.map((topic, index) => ({
      id: `ai_${Date.now()}_${index}`,
      title: `${topic} - ${plan.subject}`,
      subject: plan.subject,
      dueDate: new Date(Date.now() + (index + 1) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      priority: index === 0 ? 'alta' : 'media' as Task['priority'],
      status: 'pendiente' as Task['status'],
      estimatedTime: Math.floor(plan.totalHours / plan.topics.length * 60),
      description: `Tarea generada por IA para el plan: ${plan.title}`,
      aiGenerated: true,
      difficulty: Math.floor(Math.random() * 5) + 3
    }))
  }

  const priorityColors = {
    alta: 'danger',
    media: 'warning',
    baja: 'success'
  } as const

  const statusColors = {
    pendiente: 'default',
    'en-progreso': 'primary',
    completada: 'success'
  } as const

  const subjects = [
    'Matemáticas',
    'Literatura',
    'Química',
    'Física',
    'Historia',
    'Inglés',
    'Biología',
    'Geografía'
  ]

  const addTask = async () => {
    if (newTask.title && newTask.subject) {
      const task: Task = {
        id: Date.now().toString(),
        title: newTask.title,
        subject: newTask.subject,
        dueDate: newTask.dueDate || new Date().toISOString().split('T')[0],
        priority: newTask.priority || 'media',
        status: 'pendiente',
        estimatedTime: newTask.estimatedTime || 60,
        description: newTask.description
      }
      
      setTasks([...tasks, task])
      setNewTask({ title: '', subject: '', priority: 'media', estimatedTime: 60, description: '' })
      setShowAddForm(false)

      await logActivity(studentData?.name || 'student_demo', 'task_created', {
        title: task.title,
        subject: task.subject,
        priority: task.priority
      })
    }
  }

  const updateTaskStatus = async (taskId: string, newStatus: Task['status']) => {
    setTasks(tasks.map(task => 
      task.id === taskId ? { ...task, status: newStatus } : task
    ))

    await logActivity(studentData?.name || 'student_demo', 'task_status_updated', {
      taskId,
      newStatus
    })

    // Actualizar progreso del plan si la tarea es generada por IA
    const updatedTask = tasks.find(t => t.id === taskId)
    if (updatedTask?.aiGenerated && newStatus === 'completada') {
      updatePlanProgress(updatedTask.subject)
    }
  }

  const updatePlanProgress = (subject: string) => {
    setStudyPlans(plans => 
      plans.map(plan => {
        if (plan.subject === subject) {
          const completedTasks = tasks.filter(t => 
            t.subject === subject && t.status === 'completada' && t.aiGenerated
          ).length + 1
          const totalTasks = tasks.filter(t => t.subject === subject && t.aiGenerated).length
          const newProgress = Math.min(100, (completedTasks / totalTasks) * 100)
          return { ...plan, progress: newProgress }
        }
        return plan
      })
    )
  }

  const deleteTask = async (taskId: string) => {
    const taskToDelete = tasks.find(t => t.id === taskId)
    setTasks(tasks.filter(task => task.id !== taskId))
    
    await logActivity(studentData?.name || 'student_demo', 'task_deleted', {
      taskId,
      title: taskToDelete?.title
    })
  }

  const getTasksByStatus = (status: Task['status']) => {
    return tasks.filter(task => task.status === status)
  }

  const getTotalStudyTime = () => {
    return tasks.reduce((total, task) => total + task.estimatedTime, 0)
  }

  const getWeeklySchedule = () => {
    const today = new Date()
    const weekDays = []
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      weekDays.push({
        date: date.toISOString().split('T')[0],
        dayName: date.toLocaleDateString('es', { weekday: 'short' }),
        tasks: tasks.filter(task => task.dueDate === date.toISOString().split('T')[0])
      })
    }
    
    return weekDays
  }

  return (
    <div className="space-y-6">
      {/* Header con IA */}
      <Card className="julia-card">
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg">
                <Brain className="text-white" size={20} />
              </div>
              <div>
                <h3 className="text-lg font-semibold">Planificador Inteligente Julia</h3>
                <p className="text-sm text-gray-600">
                  Organiza tu estudio con ayuda de IA
                </p>
              </div>
            </div>
            <Button 
              color="secondary" 
              startContent={<Lightbulb size={16} />}
              onPress={() => setShowPlanForm(true)}
              isLoading={isLoadingAI}
            >
              Crear Plan con IA
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Estadísticas Mejoradas */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="julia-card">
          <CardBody className="text-center">
            <Target className="mx-auto text-julia-primary mb-2" size={24} />
            <p className="text-2xl font-bold text-julia-primary">{tasks.length}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Tareas Totales</p>
          </CardBody>
        </Card>

        <Card className="julia-card">
          <CardBody className="text-center">
            <CheckCircle className="mx-auto text-green-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-green-500">{getTasksByStatus('completada').length}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Completadas</p>
          </CardBody>
        </Card>

        <Card className="julia-card">
          <CardBody className="text-center">
            <AlertCircle className="mx-auto text-orange-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-orange-500">{getTasksByStatus('pendiente').length}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Pendientes</p>
          </CardBody>
        </Card>

        <Card className="julia-card">
          <CardBody className="text-center">
            <Clock className="mx-auto text-purple-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-purple-500">{Math.round(getTotalStudyTime() / 60)}h</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Tiempo Total</p>
          </CardBody>
        </Card>

        <Card className="julia-card">
          <CardBody className="text-center">
            <Brain className="mx-auto text-blue-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-blue-500">{tasks.filter(t => t.aiGenerated).length}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Tareas IA</p>
          </CardBody>
        </Card>
      </div>

      {/* Formulario para Plan con IA */}
      {showPlanForm && (
        <Card className="julia-card border-2 border-purple-200 dark:border-purple-800">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Brain className="text-purple-500" size={20} />
              <h4 className="text-lg font-semibold">Crear Plan de Estudio con IA</h4>
            </div>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Materia"
                placeholder="Selecciona una materia"
                selectedKeys={newPlan.subject ? [newPlan.subject] : []}
                onSelectionChange={(keys) => setNewPlan({...newPlan, subject: Array.from(keys)[0] as string})}
              >
                {subjects.map((subject) => (
                  <SelectItem key={subject} value={subject}>
                    {subject}
                  </SelectItem>
                ))}
              </Select>

              <Select
                label="Nivel actual"
                selectedKeys={[newPlan.currentLevel]}
                onSelectionChange={(keys) => setNewPlan({...newPlan, currentLevel: Array.from(keys)[0] as string})}
              >
                <SelectItem key="beginner" value="beginner">Principiante</SelectItem>
                <SelectItem key="intermediate" value="intermediate">Intermedio</SelectItem>
                <SelectItem key="advanced" value="advanced">Avanzado</SelectItem>
              </Select>
            </div>

            <Input
              label="Objetivo de aprendizaje"
              placeholder="Ej: Dominar ecuaciones cuadráticas"
              value={newPlan.goal}
              onValueChange={(value) => setNewPlan({...newPlan, goal: value})}
            />

            <Select
              label="Marco temporal"
              selectedKeys={[newPlan.timeframe]}
              onSelectionChange={(keys) => setNewPlan({...newPlan, timeframe: Array.from(keys)[0] as string})}
            >
              <SelectItem key="week" value="week">1 Semana</SelectItem>
              <SelectItem key="month" value="month">1 Mes</SelectItem>
              <SelectItem key="quarter" value="quarter">3 Meses</SelectItem>
            </Select>

            <div className="flex gap-2">
              <Button 
                color="secondary" 
                onPress={generateAIStudyPlan}
                isLoading={isLoadingAI}
                startContent={!isLoadingAI && <Brain size={16} />}
              >
                {isLoadingAI ? 'Generando Plan...' : 'Generar con IA'}
              </Button>
              <Button variant="ghost" onPress={() => setShowPlanForm(false)}>
                Cancelar
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Planes de Estudio Activos */}
      {studyPlans.length > 0 && (
        <Card className="julia-card">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="text-blue-500" size={20} />
              <h3 className="text-lg font-semibold">Planes de Estudio Activos</h3>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {studyPlans.map((plan) => (
                <div key={plan.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold">{plan.title}</h4>
                      {plan.createdByAI && (
                        <Chip size="sm" color="secondary" variant="flat">
                          <Brain size={12} className="mr-1" />
                          IA
                        </Chip>
                      )}
                    </div>
                    <Chip size="sm" color="primary">
                      {plan.subject}
                    </Chip>
                  </div>
                  
                  <div className="mb-3">
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>Progreso</span>
                      <span>{Math.round(plan.progress)}%</span>
                    </div>
                    <Progress 
                      value={plan.progress} 
                      color="secondary"
                      className="mb-2"
                    />
                  </div>

                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>{plan.totalHours}h total</span>
                    <span>{plan.weeklyGoal}h/semana</span>
                    <span>{plan.topics.length} temas</span>
                  </div>
                  
                  <div className="flex flex-wrap gap-1 mt-2">
                    {plan.topics.map((topic, index) => (
                      <Chip key={index} size="sm" variant="flat">
                        {topic}
                      </Chip>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lista de Tareas Mejorada */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-800 dark:text-white">Mis Tareas</h3>
            <Button 
              color="primary" 
              startContent={<Plus size={16} />}
              onPress={() => setShowAddForm(!showAddForm)}
            >
              Nueva Tarea
            </Button>
          </div>

          {/* Formulario para nueva tarea */}
          {showAddForm && (
            <Card className="julia-card">
              <CardHeader>
                <h4 className="text-lg font-semibold">Agregar Nueva Tarea</h4>
              </CardHeader>
              <CardBody className="space-y-4">
                <Input
                  label="Título de la tarea"
                  placeholder="Ej: Ensayo de historia"
                  value={newTask.title}
                  onValueChange={(value) => setNewTask({...newTask, title: value})}
                />
                
                <Select
                  label="Materia"
                  placeholder="Selecciona una materia"
                  selectedKeys={newTask.subject ? [newTask.subject] : []}
                  onSelectionChange={(keys) => setNewTask({...newTask, subject: Array.from(keys)[0] as string})}
                >
                  {subjects.map((subject) => (
                    <SelectItem key={subject} value={subject}>
                      {subject}
                    </SelectItem>
                  ))}
                </Select>

                <div className="grid grid-cols-2 gap-4">
                  <Select
                    label="Prioridad"
                    selectedKeys={[newTask.priority || 'media']}
                    onSelectionChange={(keys) => setNewTask({...newTask, priority: Array.from(keys)[0] as Task['priority']})}
                  >
                    <SelectItem key="alta" value="alta">Alta</SelectItem>
                    <SelectItem key="media" value="media">Media</SelectItem>
                    <SelectItem key="baja" value="baja">Baja</SelectItem>
                  </Select>

                  <Input
                    type="number"
                    label="Tiempo estimado (minutos)"
                    value={newTask.estimatedTime?.toString()}
                    onValueChange={(value) => setNewTask({...newTask, estimatedTime: parseInt(value) || 60})}
                  />
                </div>

                <Textarea
                  label="Descripción"
                  placeholder="Detalles adicionales sobre la tarea"
                  value={newTask.description}
                  onValueChange={(value) => setNewTask({...newTask, description: value})}
                />

                <div className="flex gap-2">
                  <Button color="primary" onPress={addTask}>
                    Agregar Tarea
                  </Button>
                  <Button variant="ghost" onPress={() => setShowAddForm(false)}>
                    Cancelar
                  </Button>
                </div>
              </CardBody>
            </Card>
          )}

          {/* Lista de tareas con mejoras */}
          <div className="space-y-3">
            {tasks.map((task) => (
              <Card key={task.id} className="julia-card hover-lift">
                <CardBody>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-semibold text-gray-800 dark:text-white">{task.title}</h4>
                        <Chip 
                          size="sm" 
                          color={priorityColors[task.priority]}
                          variant="flat"
                        >
                          {task.priority}
                        </Chip>
                        <Chip 
                          size="sm" 
                          color={statusColors[task.status]}
                          variant="flat"
                        >
                          {task.status}
                        </Chip>
                        {task.aiGenerated && (
                          <Chip size="sm" color="secondary" variant="flat">
                            <Brain size={10} className="mr-1" />
                            IA
                          </Chip>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-2">
                        <span className="flex items-center gap-1">
                          <BookOpen size={14} />
                          {task.subject}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar size={14} />
                          {task.dueDate}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock size={14} />
                          {task.estimatedTime} min
                        </span>
                        {task.difficulty && (
                          <span className="flex items-center gap-1">
                            <Target size={14} />
                            Dificultad: {task.difficulty}/10
                          </span>
                        )}
                      </div>
                      
                      {task.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{task.description}</p>
                      )}

                      {task.prerequisites && task.prerequisites.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-2">
                          <span className="text-xs text-gray-500">Prerequisitos:</span>
                          {task.prerequisites.map((prereq, index) => (
                            <Chip key={index} size="sm" variant="flat" color="default">
                              {prereq}
                            </Chip>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2 ml-4">
                      {task.status === 'pendiente' && (
                        <Button
                          size="sm"
                          color="primary"
                          variant="flat"
                          onPress={() => updateTaskStatus(task.id, 'en-progreso')}
                        >
                          Iniciar
                        </Button>
                      )}
                      {task.status === 'en-progreso' && (
                        <Button
                          size="sm"
                          color="success"
                          variant="flat"
                          onPress={() => updateTaskStatus(task.id, 'completada')}
                        >
                          Completar
                        </Button>
                      )}
                      <Button
                        size="sm"
                        color="danger"
                        variant="light"
                        isIconOnly
                        onPress={() => deleteTask(task.id)}
                      >
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>

        {/* Calendario Semanal */}
        <Card className="julia-card">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Calendar className="text-julia-primary" size={20} />
              <h3 className="text-lg font-semibold">Esta Semana</h3>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {getWeeklySchedule().map((day, index) => (
                <div key={index} className="border-l-4 border-julia-primary pl-4">
                  <h4 className="font-semibold text-gray-800 dark:text-white capitalize">
                    {day.dayName} {day.date.split('-')[2]}
                  </h4>
                  {day.tasks.length > 0 ? (
                    <div className="space-y-2 mt-2">
                      {day.tasks.map((task) => (
                        <div key={task.id} className="text-sm">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-gray-700 dark:text-gray-300">{task.title}</p>
                            {task.aiGenerated && (
                              <Brain size={10} className="text-purple-500" />
                            )}
                          </div>
                          <p className="text-gray-500">{task.subject}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 mt-1">Sin tareas programadas</p>
                  )}
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Estado del Sistema */}
      <Card className="border-2 border-dashed border-gray-300 dark:border-gray-600">
        <CardBody className="text-center">
          <p className="text-gray-600 dark:text-gray-400">
            🧠 <strong>Planificador Julia:</strong> {tasks.filter(t => t.aiGenerated).length} tareas generadas por IA • {studyPlans.length} planes activos
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Sistema de planificación inteligente con seguimiento de progreso y recomendaciones personalizadas
          </p>
        </CardBody>
      </Card>
    </div>
  )
}
