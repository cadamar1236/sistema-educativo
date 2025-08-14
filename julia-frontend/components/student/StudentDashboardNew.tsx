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
  Flame,
  BarChart3
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        
        {/* Header con información del estudiante y estado del sistema */}
        <div className="mb-6 flex justify-between items-start">
          <div className="flex items-center space-x-4">
            <Avatar 
              size="lg" 
              name={studentStats?.name || 'Estudiante'} 
              className="bg-gradient-to-r from-purple-500 to-pink-500"
            />
            <div>
              <h1 className="text-3xl font-bold text-gray-800">
                ¡Hola, {studentStats?.name || 'Estudiante'}! 👋
              </h1>
              <p className="text-gray-600">{studentStats?.grade} • {studentStats?.current_level}</p>
              <div className="flex items-center space-x-2 mt-1">
                <Chip 
                  size="sm" 
                  variant="flat" 
                  color={dashboardStats?.system_status.system_health === 'good' ? 'success' : 'warning'}
                  startContent={dashboardStats?.system_status.system_health === 'good' ? 
                    <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                >
                  {dashboardStats?.system_status.agents_active}/{dashboardStats?.system_status.total_agents} Agentes Activos
                </Chip>
                <Chip size="sm" variant="flat" color="default">
                  Actualizado: {formatLastUpdated(lastUpdated)}
                </Chip>
              </div>
            </div>
          </div>
          
          <Button
            color="primary"
            variant="flat"
            size="sm"
            isLoading={isLoading}
            onPress={refreshStats}
            startContent={<RefreshCw className="h-4 w-4" />}
          >
            Actualizar
          </Button>
        </div>

        {/* Error banner si hay problemas */}
        {error && (
          <Card className="mb-6 border-l-4 border-warning-500">
            <CardBody>
              <div className="flex items-center space-x-3">
                <AlertCircle className="h-5 w-5 text-warning-500" />
                <div className="flex-1">
                  <p className="text-warning-700 font-medium">Problema de Conectividad</p>
                  <p className="text-warning-600 text-sm">{error}</p>
                </div>
                <Button size="sm" variant="light" onPress={clearError}>
                  Descartar
                </Button>
              </div>
            </CardBody>
          </Card>
        )}

        {/* Navegación por pestañas */}
        <Tabs 
          selectedKey={selectedTab} 
          onSelectionChange={(key) => setSelectedTab(key as string)}
          size="lg"
          className="mb-6"
        >
          <Tab key="dashboard" title={
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Dashboard</span>
            </div>
          }>
            
            {/* Dashboard Principal */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Columna izquierda - Progreso y estadísticas */}
              <div className="lg:col-span-2 space-y-6">
                
                {/* Tarjetas de progreso principal */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  
                  {/* Progreso General */}
                  <Card className="bg-gradient-to-br from-blue-500 to-purple-600 text-white">
                    <CardBody className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-blue-100 text-sm">Progreso General</p>
                          <p className="text-3xl font-bold">{studentStats?.overall_progress || 0}%</p>
                        </div>
                        <TrendingUp className="h-8 w-8 text-blue-200" />
                      </div>
                      <Progress 
                        value={studentStats?.overall_progress || 0} 
                        className="mb-2"
                        color="warning"
                      />
                      <p className="text-blue-100 text-xs">
                        Meta semanal: {studentStats?.weekly_goal || 0}%
                      </p>
                    </CardBody>
                  </Card>

                  {/* Racha de días */}
                  <Card className="bg-gradient-to-br from-orange-500 to-red-600 text-white">
                    <CardBody className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-orange-100 text-sm">Racha de Estudio</p>
                          <p className="text-3xl font-bold">{studentStats?.streak_days || 0} días</p>
                        </div>
                        <Flame className="h-8 w-8 text-orange-200" />
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">{getStreakEmoji(studentStats?.streak_days || 0)}</span>
                        <p className="text-orange-100 text-xs">
                          ¡Mantén el ritmo!
                        </p>
                      </div>
                    </CardBody>
                  </Card>

                  {/* Actividad de hoy */}
                  <Card className="bg-gradient-to-br from-green-500 to-teal-600 text-white">
                    <CardBody className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-green-100 text-sm">Hoy</p>
                          <p className="text-3xl font-bold">{studentStats?.today_activity.points_earned || 0}</p>
                          <p className="text-green-100 text-xs">puntos ganados</p>
                        </div>
                        <Star className="h-8 w-8 text-green-200" />
                      </div>
                      <div className="text-green-100 text-xs space-y-1">
                        <p>{studentStats?.today_activity.lessons_completed || 0} lecciones • {studentStats?.today_activity.exercises_completed || 0} ejercicios</p>
                        <p>{formatStudyTime(studentStats?.today_activity.study_time_minutes || 0)} estudiados</p>
                      </div>
                    </CardBody>
                  </Card>
                </div>

                {/* Progreso por materias */}
                <Card>
                  <CardHeader>
                    <h3 className="text-xl font-semibold flex items-center">
                      <BookOpen className="h-5 w-5 mr-2" />
                      Progreso por Materias
                    </h3>
                  </CardHeader>
                  <CardBody>
                    <div className="space-y-4">
                      {studentStats?.subject_stats.map((subject, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium">{subject.subject}</h4>
                              <span className="text-sm text-gray-600">
                                Nota: {subject.grade.toFixed(1)} • {subject.exercises_completed} ejercicios
                              </span>
                            </div>
                            <Progress 
                              value={subject.progress} 
                              color={getProgressColor(subject.progress)}
                              className="mb-1"
                            />
                            <div className="flex justify-between text-xs text-gray-500">
                              <span>{subject.progress}% completado</span>
                              <span>{subject.time_spent_hours}h estudiadas</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardBody>
                </Card>

                {/* Recomendaciones personalizadas */}
                {dashboardStats?.recommendations && dashboardStats.recommendations.length > 0 && (
                  <Card>
                    <CardHeader>
                      <h3 className="text-xl font-semibold flex items-center">
                        <Brain className="h-5 w-5 mr-2" />
                        Recomendaciones Personalizadas
                      </h3>
                    </CardHeader>
                    <CardBody>
                      <div className="space-y-3">
                        {dashboardStats.recommendations.map((rec, index) => (
                          <div key={index} className="flex items-start space-x-3 p-3 rounded-lg border">
                            <div className={`p-2 rounded-full ${
                              rec.priority === 'high' ? 'bg-red-100' : 
                              rec.priority === 'medium' ? 'bg-yellow-100' : 'bg-green-100'
                            }`}>
                              {rec.type === 'focus_area' && <Target className="h-4 w-4 text-red-600" />}
                              {rec.type === 'study_plan' && <Calendar className="h-4 w-4 text-yellow-600" />}
                              {rec.type === 'motivation' && <Heart className="h-4 w-4 text-green-600" />}
                              {rec.type === 'health' && <Activity className="h-4 w-4 text-blue-600" />}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <h4 className="font-medium">{rec.title}</h4>
                                <Chip size="sm" color={getPriorityColor(rec.priority)} variant="flat">
                                  {rec.priority === 'high' ? 'Alta' : rec.priority === 'medium' ? 'Media' : 'Baja'}
                                </Chip>
                              </div>
                              <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardBody>
                  </Card>
                )}
              </div>

              {/* Columna derecha - Horarios y logros */}
              <div className="space-y-6">
                
                {/* Clases de hoy */}
                <Card>
                  <CardHeader>
                    <h3 className="text-lg font-semibold flex items-center">
                      <Calendar className="h-5 w-5 mr-2" />
                      Clases de Hoy
                    </h3>
                  </CardHeader>
                  <CardBody>
                    <div className="space-y-3">
                      {studentStats?.upcoming_classes.map((clase, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                          <div>
                            <p className="font-medium text-sm">{clase.subject}</p>
                            <p className="text-xs text-gray-600">{clase.teacher}</p>
                            {clase.classroom && (
                              <p className="text-xs text-gray-500">{clase.classroom}</p>
                            )}
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium text-blue-600">{clase.time}</p>
                            <p className="text-xs text-gray-500">{clase.duration_minutes}min</p>
                          </div>
                        </div>
                      ))}
                      {(!studentStats?.upcoming_classes || studentStats.upcoming_classes.length === 0) && (
                        <p className="text-gray-500 text-sm text-center py-4">
                          No hay clases programadas para hoy
                        </p>
                      )}
                    </div>
                  </CardBody>
                </Card>

                {/* Logros recientes */}
                <Card>
                  <CardHeader>
                    <h3 className="text-lg font-semibold flex items-center">
                      <Trophy className="h-5 w-5 mr-2" />
                      Logros Recientes
                    </h3>
                  </CardHeader>
                  <CardBody>
                    <div className="space-y-3">
                      {studentStats?.recent_achievements.map((achievement, index) => (
                        <div key={index} className="flex items-center space-x-3 p-3 bg-yellow-50 rounded-lg">
                          <div className="p-2 bg-yellow-200 rounded-full">
                            <Award className="h-4 w-4 text-yellow-700" />
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-sm">{achievement.title}</p>
                            <p className="text-xs text-gray-600">{achievement.description}</p>
                            <div className="flex items-center justify-between mt-1">
                              <span className="text-xs text-gray-500">
                                {new Date(achievement.date).toLocaleDateString()}
                              </span>
                              <Chip size="sm" color="warning" variant="flat">
                                +{achievement.points} pts
                              </Chip>
                            </div>
                          </div>
                        </div>
                      ))}
                      {(!studentStats?.recent_achievements || studentStats.recent_achievements.length === 0) && (
                        <p className="text-gray-500 text-sm text-center py-4">
                          ¡Completa actividades para desbloquear logros!
                        </p>
                      )}
                    </div>
                  </CardBody>
                </Card>

                {/* Insignias desbloqueadas */}
                <Card>
                  <CardHeader>
                    <h3 className="text-lg font-semibold flex items-center">
                      <Star className="h-5 w-5 mr-2" />
                      Insignias
                    </h3>
                  </CardHeader>
                  <CardBody>
                    <div className="grid grid-cols-2 gap-3">
                      {studentStats?.badges.map((badge, index) => (
                        <div key={index} className="text-center p-3 bg-purple-50 rounded-lg">
                          <div className="text-2xl mb-1">{badge.icon}</div>
                          <p className="text-xs font-medium">{badge.name}</p>
                          <p className="text-xs text-gray-600 mt-1">{badge.description}</p>
                          <p className="text-xs text-purple-600 mt-1">
                            {new Date(badge.unlocked_date).toLocaleDateString()}
                          </p>
                        </div>
                      ))}
                      {(!studentStats?.badges || studentStats.badges.length === 0) && (
                        <div className="col-span-2 text-center py-4">
                          <p className="text-gray-500 text-sm">
                            ¡Completa desafíos para ganar insignias!
                          </p>
                        </div>
                      )}
                    </div>
                  </CardBody>
                </Card>
              </div>
            </div>
          </Tab>

          <Tab key="multiagent-chat" title={
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4" />
              <span>Chat Multi-Agente</span>
            </div>
          }>
            <MultiAgentChat 
              onActivityUpdate={(activity) => {
                // Actualizar estadísticas cuando el estudiante interactúe
                updateActivity({
                  type: 'chat_session',
                  duration_minutes: 15, // Estimado
                  ...activity
                })
              }}
            />
          </Tab>

          <Tab key="agent-chat" title={
            <div className="flex items-center space-x-2">
              <MessageSquare className="h-4 w-4" />
              <span>Chat Individual</span>
            </div>
          }>
            <AgentChat 
              onActivityUpdate={(activity) => {
                // Actualizar estadísticas cuando el estudiante interactúe
                updateActivity({
                  type: 'chat_session',
                  duration_minutes: 10, // Estimado
                  ...activity
                })
              }}
            />
          </Tab>
        </Tabs>
      </div>
    </div>
  )
}
