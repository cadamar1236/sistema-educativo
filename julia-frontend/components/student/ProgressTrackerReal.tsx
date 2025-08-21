'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Card, CardBody, CardHeader, Progress, Chip, Button, Select, SelectItem, Tabs, Tab } from '@nextui-org/react'
import { TrendingUp, Award, Clock, Target, BookOpen, Brain, Calendar, BarChart3, PieChart, LineChart } from 'lucide-react'
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPieChart, Pie, Cell, BarChart, Bar } from 'recharts'
import { useJuliaAgents } from '@/lib/juliaAgentService'

// Añadir helper de fetch
async function fetchProgress(studentName: string, period: string) {
  const rawBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
  const base = rawBase.replace(/\/$/, '')
  const pathApi = `${base}/students/${encodeURIComponent(studentName)}/progress?period=${period}`
  let res = await fetch(pathApi)
  if (res.status === 404) {
    // Intentar sin /api por si el backend corre con alias
    const alt = base.endsWith('/api')
      ? base.replace(/\/api$/, '') + `/students/${encodeURIComponent(studentName)}/progress?period=${period}`
      : base + `/students/${encodeURIComponent(studentName)}/progress?period=${period}`
    res = await fetch(alt)
  }
  if (!res.ok) throw new Error('Failed to load progress')
  return res.json()
}

interface ProgressTrackerProps {
  studentData: any
}

interface SubjectProgress {
  subject: string
  progress: number
  grade: number
  trend: 'up' | 'down' | 'stable'
  timeSpent: number
  completedTasks: number
  totalTasks: number
}

interface Achievement {
  id: string
  title: string
  description: string
  icon: string
  unlockedAt: Date
  category: 'academic' | 'time' | 'streak' | 'skill'
}

interface StudySession {
  date: string
  duration: number
  subject: string
  performance: number
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D']

export default function ProgressTracker({ studentData }: ProgressTrackerProps) {
  const { user } = useAuth() as any
  const effectiveName = studentData?.name || user?.id
  const [progressData, setProgressData] = useState<SubjectProgress[]>([])
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [studySessions, setStudySessions] = useState<StudySession[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedPeriod, setSelectedPeriod] = useState('week')
  const [selectedTab, setSelectedTab] = useState('overview')
  const { agentService, logActivity } = useJuliaAgents()

  useEffect(() => {
    if (effectiveName) loadProgressData()
  }, [effectiveName, selectedPeriod])

  const loadProgressData = async () => {
    setIsLoading(true)
    try {
  if (!effectiveName) return
  await logActivity(effectiveName, 'progress_tracker_access')
  const progress = await fetchProgress(effectiveName, selectedPeriod)

      // Mapear subjects -> SubjectProgress shape
      const subjectProgress: SubjectProgress[] = (progress.subjects || []).map((s: any) => ({
        subject: s.subject,
        progress: s.progress ?? 0,
        grade: s.grade ?? 0,
        trend: (s.trend as 'up'|'down'|'stable') || 'stable',
        timeSpent: Math.round((s.time_spent_hours || 0) * 60),
        completedTasks: s.exercises_completed || 0,
        totalTasks: Math.max(s.exercises_completed || 0, 1)
      }))
      setProgressData(subjectProgress)

      // Achievements: combinar recent_achievements y badges
      const ach: Achievement[] = []
      if (progress.recent_achievements) {
        for (const a of progress.recent_achievements) {
          ach.push({
            id: a.id || a.title || Math.random().toString(36).slice(2),
            title: a.title || a.name || 'Logro',
            description: a.description || '',
            icon: a.icon || '🏆',
            unlockedAt: new Date(a.date || a.unlocked_date || Date.now()),
            category: 'academic'
          })
        }
      }
      if (progress.badges) {
        for (const b of progress.badges) {
          ach.push({
            id: b.id || b.name,
            title: b.name || 'Badge',
            description: b.description || '',
            icon: b.icon || '🎖️',
            unlockedAt: new Date(b.unlocked_date || Date.now()),
            category: 'skill'
          })
        }
      }
      setAchievements(ach)

      const sessions: StudySession[] = (progress.sessions || []).map((sess: any) => ({
        date: sess.date,
        duration: sess.duration,
        subject: sess.subject,
        performance: sess.performance
      }))
      setStudySessions(sessions)

    } catch (error) {
      console.error('Error loading progress data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return <TrendingUp className="text-green-500" size={16} />
      case 'down': return <TrendingUp className="text-red-500 rotate-180" size={16} />
      default: return <div className="w-4 h-0.5 bg-gray-400 rounded" />
    }
  }

  const getOverallProgress = () => {
    if (progressData.length === 0) return 0
    return Math.round(progressData.reduce((sum, item) => sum + item.progress, 0) / progressData.length)
  }

  const getTotalStudyTime = () => {
    return progressData.reduce((sum, item) => sum + item.timeSpent, 0)
  }

  const getAverageGrade = () => {
    if (progressData.length === 0) return 0
    return (progressData.reduce((sum, item) => sum + item.grade, 0) / progressData.length).toFixed(1)
  }

  const getCompletedTasksCount = () => {
    return progressData.reduce((sum, item) => sum + item.completedTasks, 0)
  }

  const pieChartData = progressData.map(item => ({
    name: item.subject,
    value: item.timeSpent
  }))

  const performanceData = studySessions.map(session => ({
    date: session.date.split('-')[2],
    performance: session.performance,
    duration: session.duration
  }))

  if (isLoading) {
    return (
      <Card className="julia-card">
        <CardBody className="text-center py-8">
          <Brain className="mx-auto text-julia-primary mb-4 animate-pulse" size={48} />
          <p>Analizando tu progreso...</p>
        </CardBody>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="julia-card">
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-green-500 to-blue-600 rounded-lg">
                <BarChart3 className="text-white" size={20} />
              </div>
              <div>
                <h3 className="text-lg font-semibold">Seguimiento de Progreso</h3>
                <p className="text-sm text-gray-600">
                  Análisis inteligente de tu rendimiento académico
                </p>
              </div>
            </div>
            <Select
              label="Período"
              size="sm"
              selectedKeys={[selectedPeriod]}
              onSelectionChange={(keys) => setSelectedPeriod(Array.from(keys)[0] as string)}
              className="w-32"
            >
              <SelectItem key="week" value="week">Semana</SelectItem>
              <SelectItem key="month" value="month">Mes</SelectItem>
              <SelectItem key="quarter" value="quarter">Trimestre</SelectItem>
            </Select>
          </div>
        </CardHeader>
      </Card>

      {/* Métricas Principales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="julia-card">
          <CardBody className="text-center">
            <Target className="mx-auto text-blue-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-blue-500">{getOverallProgress()}%</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Progreso General</p>
            <Progress value={getOverallProgress()} color="primary" className="mt-2" />
          </CardBody>
        </Card>

        <Card className="julia-card">
          <CardBody className="text-center">
            <Award className="mx-auto text-yellow-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-yellow-500">{getAverageGrade()}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Promedio General</p>
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
            <BookOpen className="mx-auto text-green-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-green-500">{getCompletedTasksCount()}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Tareas Completadas</p>
          </CardBody>
        </Card>
      </div>

  {/* Navegación por pestañas */}
  <Tabs selectedKey={selectedTab} onSelectionChange={(key) => setSelectedTab(String(key))}>
        <Tab 
          key="overview" 
          title={
            <div className="flex items-center gap-2">
              <BarChart3 size={16} />
              <span>Resumen</span>
            </div>
          }
        />
        <Tab 
          key="subjects" 
          title={
            <div className="flex items-center gap-2">
              <BookOpen size={16} />
              <span>Por Materias</span>
            </div>
          }
        />
        <Tab 
          key="achievements" 
          title={
            <div className="flex items-center gap-2">
              <Award size={16} />
              <span>Logros</span>
            </div>
          }
        />
        <Tab 
          key="analytics" 
          title={
            <div className="flex items-center gap-2">
              <LineChart size={16} />
              <span>Análisis</span>
            </div>
          }
        />
      </Tabs>

      {/* Contenido basado en la pestaña */}
      {selectedTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Gráfico de Rendimiento */}
          <Card className="julia-card">
            <CardHeader>
              <h4 className="font-semibold">Rendimiento Semanal</h4>
            </CardHeader>
            <CardBody>
              <ResponsiveContainer width="100%" height={250}>
                <RechartsLineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="performance" 
                    stroke="#8884d8" 
                    strokeWidth={2}
                    dot={{ fill: '#8884d8' }}
                  />
                </RechartsLineChart>
              </ResponsiveContainer>
            </CardBody>
          </Card>

          {/* Distribución de Tiempo */}
          <Card className="julia-card">
            <CardHeader>
              <h4 className="font-semibold">Tiempo por Materia</h4>
            </CardHeader>
            <CardBody>
              <ResponsiveContainer width="100%" height={250}>
                <RechartsPieChart>
                  <Pie
                    data={pieChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any) => [`${value} min`, 'Tiempo']} />
                </RechartsPieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap gap-2 mt-4">
                {pieChartData.map((entry, index) => (
                  <div key={entry.name} className="flex items-center gap-1 text-sm">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span>{entry.name}</span>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>
      )}

      {selectedTab === 'subjects' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {progressData.map((subject, index) => (
            <Card key={subject.subject} className="julia-card">
              <CardBody>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-lg">{subject.subject}</h4>
                  <div className="flex items-center gap-2">
                    {getTrendIcon(subject.trend)}
                    <Chip 
                      size="sm" 
                      color={subject.grade >= 8 ? 'success' : subject.grade >= 6 ? 'warning' : 'danger'}
                    >
                      {subject.grade}/10
                    </Chip>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Progreso del Curso</span>
                      <span>{subject.progress}%</span>
                    </div>
                    <Progress value={subject.progress} color="primary" />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Tiempo de Estudio</p>
                      <p className="font-semibold">{Math.round(subject.timeSpent / 60)}h {subject.timeSpent % 60}min</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Tareas</p>
                      <p className="font-semibold">{subject.completedTasks}/{subject.totalTasks}</p>
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {selectedTab === 'achievements' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {achievements.map((achievement) => (
            <Card key={achievement.id} className="julia-card">
              <CardBody className="text-center">
                <div className="text-4xl mb-3">{achievement.icon}</div>
                <h4 className="font-semibold mb-2">{achievement.title}</h4>
                <p className="text-sm text-gray-600 mb-3">{achievement.description}</p>
                <Chip 
                  size="sm" 
                  variant="flat"
                  color={
                    achievement.category === 'academic' ? 'primary' :
                    achievement.category === 'time' ? 'secondary' :
                    achievement.category === 'streak' ? 'warning' : 'success'
                  }
                >
                  {achievement.category}
                </Chip>
                <p className="text-xs text-gray-500 mt-2">
                  Desbloqueado: {achievement.unlockedAt.toLocaleDateString()}
                </p>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {selectedTab === 'analytics' && (
        <Card className="julia-card">
          <CardHeader>
            <h4 className="font-semibold">Análisis de Rendimiento por Día</h4>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="performance" fill="#8884d8" />
                <Bar dataKey="duration" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      )}

      {/* Estado del Sistema */}
      <Card className="border-2 border-dashed border-gray-300 dark:border-gray-600">
        <CardBody className="text-center">
          <p className="text-gray-600 dark:text-gray-400">
            📊 <strong>Analytics Julia:</strong> Datos en tiempo real del sistema de seguimiento académico
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Análisis impulsado por IA • Métricas personalizadas • Recomendaciones automáticas
          </p>
        </CardBody>
      </Card>
    </div>
  )
}
