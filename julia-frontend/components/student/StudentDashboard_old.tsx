'use client'

import React, { useState } from 'react'
import { Card, CardBody, CardHeader, Progress, Avatar, Badge, Chip, Button, Tabs, Tab } from '@nextui-org/react'
import { 
  BookOpen, 
  TrendingUp, 
  Calendar, 
  Award, 
  Clock, 
  Brain, 
  Target, 
  Star, 
  Trophy, 
  Zap, 
  Heart, 
  MessageSquare,
  RefreshCw,
  Wifi,
  WifiOff,
  AlertCircle,
  CheckCircle,
  Activity,
  Flame
} from 'lucide-react'
import AgentChat from './AgentChat'
import MultiAgentChat from './MultiAgentChat'
import { useStudentStats } from '../../hooks/useStudentStats'

interface StudentDashboardProps {
  studentId?: string;
}

export default function StudentDashboard({ studentId = 'student_001' }: StudentDashboardProps) {
  const [selectedTab, setSelectedTab] = useState('dashboard')
  
  // Hook para obtener estadísticas reales
  const { 
    dashboardStats, 
    studentStats, 
    isLoading, 
    error, 
    lastUpdated,
    refreshStats,
    updateActivity,
    clearError 
  } = useStudentStats({ 
    studentId,
    autoRefresh: true,
    refreshInterval: 300000 // 5 minutos
  })
  
  const getProgressColor = (value: number) => {
    if (value >= 80) return 'success'
    if (value >= 60) return 'warning'
    return 'danger'
  }

  const getStreakEmoji = (streak: number) => {
    if (streak >= 30) return '🔥'
    if (streak >= 14) return '⭐'
    if (streak >= 7) return '🌟'
    return '⚡'
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'danger'
      case 'medium': return 'warning'
      case 'low': return 'success'
      default: return 'default'
    }
  }

  const formatStudyTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours > 0) {
      return `${hours}h ${mins}m`
    }
    return `${mins}m`
  }

  const formatLastUpdated = (date: Date | null) => {
    if (!date) return 'Nunca'
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 1) return 'Ahora'
    if (minutes < 60) return `Hace ${minutes}m`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `Hace ${hours}h`
    return date.toLocaleDateString()
  }

  // Componente de estado de carga
  if (isLoading && !studentStats) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Card className="w-96 p-8">
          <CardBody className="text-center space-y-4">
            <RefreshCw className="h-12 w-12 mx-auto animate-spin text-blue-500" />
            <h3 className="text-xl font-semibold">Cargando Dashboard</h3>
            <p className="text-gray-600">Obteniendo tus estadísticas...</p>
          </CardBody>
        </Card>
      </div>
    )
  }

  // Componente de error
  if (error && !studentStats) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-red-50 to-pink-100">
        <Card className="w-96 p-8">
          <CardBody className="text-center space-y-4">
            <WifiOff className="h-12 w-12 mx-auto text-red-500" />
            <h3 className="text-xl font-semibold text-red-700">Error de Conexión</h3>
            <p className="text-gray-600">{error}</p>
            <Button 
              color="danger" 
              variant="flat" 
              onPress={clearError}
              startContent={<RefreshCw className="h-4 w-4" />}
            >
              Reintentar
            </Button>
          </CardBody>
        </Card>
      </div>
    )
  }
  
  const getProgressColor = (value: number) => {
    if (value >= 80) return 'success'
    if (value >= 60) return 'warning'
    return 'danger'
  }

  const getStreakEmoji = (streak: number) => {
    if (streak >= 30) return '🔥'
    if (streak >= 14) return '⭐'
    if (streak >= 7) return '🌟'
    return '⚡'
  }

  return (
    <div className="space-y-6">
      {/* Navigation Tabs - Versión más visible */}
      <Card className="julia-card border-2 border-julia-primary/30 shadow-lg">
        <CardBody className="p-4">
          <div className="text-center mb-4">
            <h2 className="text-xl font-bold text-julia-primary">Panel de Control Estudiantil</h2>
            <p className="text-sm text-gray-600">Navega entre el dashboard y el chat con agentes IA</p>
          </div>
          
          <Tabs 
            selectedKey={selectedTab} 
            onSelectionChange={(key) => setSelectedTab(key as string)}
            variant="underlined"
            size="lg"
            color="primary"
            className="w-full justify-center"
            classNames={{
              tabList: "gap-6 w-full relative rounded-none p-0 border-b border-divider",
              cursor: "w-full bg-julia-primary",
              tab: "max-w-fit px-6 h-12",
              tabContent: "group-data-[selected=true]:text-julia-primary font-semibold"
            }}
          >
            <Tab 
              key="dashboard" 
              title={
                <div className="flex items-center space-x-2 px-2">
                  <TrendingUp size={20} />
                  <span className="font-semibold">📊 Dashboard Principal</span>
                </div>
              }
            />
            <Tab 
              key="multiagent-chat" 
              title={
                <div className="flex items-center space-x-2 px-2">
                  <MessageSquare size={20} />
                  <span className="font-semibold">🤖 Chat Multiagente</span>
                  <Chip 
                    size="sm" 
                    color="success" 
                    variant="solid" 
                    className="text-xs animate-pulse"
                  >
                    TODOS
                  </Chip>
                </div>
              }
            />
            <Tab 
              key="chat" 
              title={
                <div className="flex items-center space-x-2 px-2">
                  <Brain size={20} />
                  <span className="font-semibold">💬 Chat Individual</span>
                  <Chip 
                    size="sm" 
                    color="primary" 
                    variant="flat" 
                    className="text-xs"
                  >
                    1 vs 1
                  </Chip>
                </div>
              }
            />
          </Tabs>
        </CardBody>
      </Card>

      {/* Contenido condicional basado en la pestaña seleccionada */}
      {selectedTab === 'multiagent-chat' ? (
        <div className="space-y-4">
          <Card className="julia-card">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <MessageSquare className="text-julia-primary" size={20} />
                <h3 className="text-lg font-semibold">Chat Multiagente - Todos los Agentes</h3>
                <Chip size="sm" color="success" variant="flat">Sistema Completo</Chip>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm mt-2">
                Interactúa simultáneamente con todos los agentes especializados del sistema Julia. 
                Cada agente aportará su expertise específica a tu consulta.
              </p>
            </CardHeader>
          </Card>
          <MultiAgentChat studentId="student_001" />
        </div>
      ) : selectedTab === 'chat' ? (
        <div className="space-y-4">
          <Card className="julia-card">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Brain className="text-julia-primary" size={20} />
                <h3 className="text-lg font-semibold">Chat Individual - Selección Personalizada</h3>
                <Chip size="sm" color="primary" variant="flat">Personalizado</Chip>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm mt-2">
                Selecciona manualmente los agentes con los que deseas interactuar. 
                Ideal para consultas específicas y sesiones dirigidas.
              </p>
            </CardHeader>
          </Card>
          <AgentChat studentId="student_001" />
        </div>
      ) : (
        <>
          {/* Header Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Progreso General */}
        <Card className="julia-card hover-lift">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-3">
              <TrendingUp className="text-julia-primary" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Progreso General</h3>
            <Progress 
              value={studentData.overallProgress} 
              color={getProgressColor(studentData.overallProgress)}
              className="mt-2"
              size="lg"
            />
            <p className="text-2xl font-bold text-julia-primary mt-2">
              {studentData.overallProgress}%
            </p>
          </CardBody>
        </Card>

        {/* Racha de Estudio */}
        <Card className="julia-card hover-lift">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-3">
              <Zap className="text-orange-500" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Racha Actual</h3>
            <div className="flex items-center justify-center mt-2">
              <span className="text-3xl mr-2">{getStreakEmoji(studentData.streak)}</span>
              <span className="text-2xl font-bold text-orange-500">{studentData.streak}</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">días consecutivos</p>
          </CardBody>
        </Card>

        {/* Meta Semanal */}
        <Card className="julia-card hover-lift">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-3">
              <Target className="text-green-500" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Meta Semanal</h3>
            <Progress 
              value={(studentData.overallProgress / studentData.weeklyGoal) * 100} 
              color="success"
              className="mt-2"
              size="lg"
            />
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              {studentData.overallProgress} / {studentData.weeklyGoal}%
            </p>
          </CardBody>
        </Card>

        {/* Nivel Actual */}
        <Card className="julia-card hover-lift">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-3">
              <Trophy className="text-purple-500" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Nivel Actual</h3>
            <Chip 
              color="secondary" 
              variant="flat" 
              className="mt-2"
              size="lg"
            >
              {studentData.currentLevel}
            </Chip>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              {studentData.grade}
            </p>
          </CardBody>
        </Card>
      </div>

      {/* Contenido Principal */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clases de Hoy */}
        <Card className="julia-card">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Calendar className="text-julia-primary" size={20} />
              <h3 className="text-lg font-semibold">Clases de Hoy</h3>
            </div>
          </CardHeader>
          <CardBody className="space-y-3">
            {studentData.upcomingClasses.map((clase, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <p className="font-semibold text-gray-800 dark:text-white">{clase.subject}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{clase.teacher}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-julia-primary">{clase.time}</p>
                  <div className="flex items-center gap-1">
                    <Clock size={12} className="text-gray-500" />
                    <span className="text-xs text-gray-500">45 min</span>
                  </div>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>

        {/* Logros Recientes */}
        <Card className="julia-card">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Award className="text-yellow-500" size={20} />
              <h3 className="text-lg font-semibold">Logros Recientes</h3>
            </div>
          </CardHeader>
          <CardBody className="space-y-3">
            {studentData.recentAchievements.map((logro, index) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-lg">
                <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <Star size={16} className="text-white" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-800 dark:text-white text-sm">{logro.title}</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{logro.date}</p>
                  <div className="flex items-center gap-1 mt-1">
                    <span className="text-xs font-bold text-yellow-600">+{logro.points} pts</span>
                  </div>
                </div>
              </div>
            ))}
          </CardBody>
        </Card>

        {/* Insignias */}
        <Card className="julia-card">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Trophy className="text-purple-500" size={20} />
              <h3 className="text-lg font-semibold">Mis Insignias</h3>
            </div>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 gap-3">
              {studentData.badges.map((badge, index) => (
                <div key={index} className="flex items-center gap-3 p-3 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg">
                  <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                    <Trophy size={20} className="text-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-800 dark:text-white text-sm">{badge}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Desbloqueada</p>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Resumen de Actividad */}
      <Card className="julia-card">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Brain className="text-julia-primary" size={20} />
            <h3 className="text-lg font-semibold">Resumen de Actividad de Hoy</h3>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <BookOpen className="mx-auto text-blue-500 mb-2" size={24} />
              <p className="text-2xl font-bold text-blue-600">4</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Lecciones</p>
            </div>
            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <Target className="mx-auto text-green-500 mb-2" size={24} />
              <p className="text-2xl font-bold text-green-600">2</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Ejercicios</p>
            </div>
            <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <Award className="mx-auto text-purple-500 mb-2" size={24} />
              <p className="text-2xl font-bold text-purple-600">350</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Puntos</p>
            </div>
            <div className="text-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <Heart className="mx-auto text-orange-500 mb-2" size={24} />
              <p className="text-2xl font-bold text-orange-600">2h 15m</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Tiempo</p>
            </div>
          </div>
        </CardBody>
        </Card>
        </>
      )}
    </div>
  )
}