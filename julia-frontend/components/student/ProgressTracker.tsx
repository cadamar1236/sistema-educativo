'use client'

import React, { useState } from 'react'
import { Card, CardBody, CardHeader, Progress, Tabs, Tab, Chip, Select, SelectItem } from '@nextui-org/react'
import { TrendingUp, BookOpen, Award, Target, Calendar, BarChart3, PieChart, Activity } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Cell } from 'recharts'

interface Props {
  studentData: any
}

export default function ProgressTracker({ studentData }: Props) {
  const [selectedPeriod, setSelectedPeriod] = useState('month')
  const [selectedSubject, setSelectedSubject] = useState('all')

  // Datos de ejemplo para gráficos
  const performanceData = [
    { name: 'Ene', matematicas: 75, literatura: 82, ciencias: 78, promedio: 78 },
    { name: 'Feb', matematicas: 78, literatura: 85, ciencias: 80, promedio: 81 },
    { name: 'Mar', matematicas: 82, literatura: 88, ciencias: 85, promedio: 85 },
    { name: 'Abr', matematicas: 85, literatura: 90, ciencias: 87, promedio: 87 },
    { name: 'May', matematicas: 88, literatura: 92, ciencias: 90, promedio: 90 }
  ]

  const weeklyActivityData = [
    { day: 'Lun', horas: 2.5, tareas: 4 },
    { day: 'Mar', horas: 3.2, tareas: 5 },
    { day: 'Mié', horas: 2.8, tareas: 3 },
    { day: 'Jue', horas: 4.1, tareas: 6 },
    { day: 'Vie', horas: 2.3, tareas: 3 },
    { day: 'Sáb', horas: 1.5, tareas: 2 },
    { day: 'Dom', horas: 1.8, tareas: 2 }
  ]

  const subjectDistribution = [
    { name: 'Matemáticas', value: 30, color: '#8884d8' },
    { name: 'Literatura', value: 25, color: '#82ca9d' },
    { name: 'Ciencias', value: 20, color: '#ffc658' },
    { name: 'Historia', value: 15, color: '#ff7300' },
    { name: 'Inglés', value: 10, color: '#0088fe' }
  ]

  const achievements = [
    { title: 'Racha de 30 días', description: 'Estudió 30 días consecutivos', date: '2024-01-15', type: 'consistency' },
    { title: 'Matemático Excepcional', description: 'Promedio superior al 90% en Matemáticas', date: '2024-01-10', type: 'academic' },
    { title: 'Lector Avanzado', description: 'Completó 5 libros este mes', date: '2024-01-08', type: 'reading' },
    { title: 'Colaborador Estrella', description: 'Participó activamente en proyectos grupales', date: '2024-01-05', type: 'collaboration' }
  ]

  const getAchievementIcon = (type: string) => {
    switch (type) {
      case 'consistency': return '🔥'
      case 'academic': return '🎓'
      case 'reading': return '📚'
      case 'collaboration': return '🤝'
      default: return '⭐'
    }
  }

  const getProgressLevel = (score: number) => {
    if (score >= 90) return { level: 'Excelente', color: 'success' }
    if (score >= 80) return { level: 'Muy Bueno', color: 'primary' }
    if (score >= 70) return { level: 'Bueno', color: 'warning' }
    return { level: 'Necesita Mejora', color: 'danger' }
  }

  const subjects = ['Matemáticas', 'Literatura', 'Ciencias', 'Historia', 'Inglés']

  return (
    <div className="space-y-6">
      {/* Filtros */}
      <div className="flex gap-4 items-center">
        <Select
          label="Período"
          selectedKeys={[selectedPeriod]}
          onSelectionChange={(keys) => setSelectedPeriod(Array.from(keys)[0] as string)}
          className="w-48"
        >
          <SelectItem key="week" value="week">Esta Semana</SelectItem>
          <SelectItem key="month" value="month">Este Mes</SelectItem>
          <SelectItem key="quarter" value="quarter">Este Trimestre</SelectItem>
          <SelectItem key="year" value="year">Este Año</SelectItem>
        </Select>

        <Select
          label="Materia"
          selectedKeys={[selectedSubject]}
          onSelectionChange={(keys) => setSelectedSubject(Array.from(keys)[0] as string)}
          className="w-48"
          items={[{ key: 'all', label: 'Todas las Materias' }, ...subjects.map(s => ({ key: s.toLowerCase(), label: s }))]}
        >
          {(item: any) => (
            <SelectItem key={item.key} value={item.key}>
              {item.label}
            </SelectItem>
          )}
        </Select>
      </div>

      {/* Resumen de Progreso */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="julia-card">
          <CardBody className="text-center">
            <TrendingUp className="mx-auto text-green-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-green-500">+12%</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Mejora este mes</p>
          </CardBody>
        </Card>

        <Card className="julia-card">
          <CardBody className="text-center">
            <Target className="mx-auto text-blue-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-blue-500">87%</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Promedio General</p>
          </CardBody>
        </Card>

        <Card className="julia-card">
          <CardBody className="text-center">
            <BookOpen className="mx-auto text-purple-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-purple-500">24h</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Tiempo Estudiado</p>
          </CardBody>
        </Card>

        <Card className="julia-card">
          <CardBody className="text-center">
            <Award className="mx-auto text-yellow-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-yellow-500">15</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Logros Desbloqueados</p>
          </CardBody>
        </Card>
      </div>

      <Tabs aria-label="Progreso" variant="bordered" className="w-full">
        {/* Rendimiento Académico */}
        <Tab key="performance" title={
          <div className="flex items-center gap-2">
            <BarChart3 size={18} />
            <span>Rendimiento</span>
          </div>
        }>
          <div className="space-y-6 mt-6">
            {/* Progreso por Materia */}
            <Card className="julia-card">
              <CardHeader>
                <h3 className="text-lg font-semibold">Progreso por Materia</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  {subjects.map((subject, index) => {
                    const score = performanceData[performanceData.length - 1][subject.toLowerCase() as keyof typeof performanceData[0]] as number || 80
                    const progress = getProgressLevel(score)
                    
                    return (
                      <div key={index} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium text-gray-800 dark:text-white">{subject}</span>
                          <div className="flex items-center gap-2">
                            <Chip size="sm" color={progress.color as any} variant="flat">
                              {progress.level}
                            </Chip>
                            <span className="font-bold text-julia-primary">{score}%</span>
                          </div>
                        </div>
                        <Progress 
                          value={score} 
                          color={progress.color as any}
                          className="w-full"
                        />
                      </div>
                    )
                  })}
                </div>
              </CardBody>
            </Card>

            {/* Gráfico de Tendencias */}
            <Card className="julia-card">
              <CardHeader>
                <h3 className="text-lg font-semibold">Tendencia de Rendimiento</h3>
              </CardHeader>
              <CardBody>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={performanceData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Line type="monotone" dataKey="promedio" stroke="#6366f1" strokeWidth={3} />
                      <Line type="monotone" dataKey="matematicas" stroke="#8884d8" strokeWidth={2} />
                      <Line type="monotone" dataKey="literatura" stroke="#82ca9d" strokeWidth={2} />
                      <Line type="monotone" dataKey="ciencias" stroke="#ffc658" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardBody>
            </Card>
          </div>
        </Tab>

        {/* Actividad Semanal */}
        <Tab key="activity" title={
          <div className="flex items-center gap-2">
            <Activity size={18} />
            <span>Actividad</span>
          </div>
        }>
          <div className="space-y-6 mt-6">
            {/* Actividad Diaria */}
            <Card className="julia-card">
              <CardHeader>
                <h3 className="text-lg font-semibold">Actividad de la Semana</h3>
              </CardHeader>
              <CardBody>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={weeklyActivityData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="horas" fill="#6366f1" name="Horas de Estudio" />
                      <Bar dataKey="tareas" fill="#8b5cf6" name="Tareas Completadas" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardBody>
            </Card>

            {/* Distribución por Materia */}
            <Card className="julia-card">
              <CardHeader>
                <h3 className="text-lg font-semibold">Distribución de Tiempo por Materia</h3>
              </CardHeader>
              <CardBody>
                <div className="flex items-center justify-center">
                  <div className="h-80 w-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPieChart>
                        <Tooltip />
                        <RechartsPieChart data={subjectDistribution} cx="50%" cy="50%" outerRadius={100}>
                          {subjectDistribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </RechartsPieChart>
                      </RechartsPieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="ml-8 space-y-2">
                    {subjectDistribution.map((entry, index) => (
                      <div key={index} className="flex items-center gap-3">
                        <div 
                          className="w-4 h-4 rounded-full" 
                          style={{ backgroundColor: entry.color }}
                        ></div>
                        <span className="text-sm font-medium">{entry.name}</span>
                        <span className="text-sm text-gray-500">{entry.value}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        </Tab>

        {/* Logros */}
        <Tab key="achievements" title={
          <div className="flex items-center gap-2">
            <Award size={18} />
            <span>Logros</span>
          </div>
        }>
          <div className="space-y-6 mt-6">
            <Card className="julia-card">
              <CardHeader>
                <h3 className="text-lg font-semibold">Logros Recientes</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  {achievements.map((achievement, index) => (
                    <div key={index} className="flex items-start gap-4 p-4 bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-lg">
                      <div className="text-3xl">{getAchievementIcon(achievement.type)}</div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-800 dark:text-white">{achievement.title}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{achievement.description}</p>
                        <p className="text-xs text-gray-500 mt-2">Obtenido el {achievement.date}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>

            {/* Próximos Objetivos */}
            <Card className="julia-card">
              <CardHeader>
                <h3 className="text-lg font-semibold">Próximos Objetivos</h3>
              </CardHeader>
              <CardBody>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <Target className="text-julia-primary" size={20} />
                    <div>
                      <p className="font-medium text-gray-800 dark:text-white">Alcanzar 90% en Matemáticas</p>
                      <Progress value={85} color="primary" className="w-48" size="sm" />
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <BookOpen className="text-green-500" size={20} />
                    <div>
                      <p className="font-medium text-gray-800 dark:text-white">Leer 3 libros más este mes</p>
                      <Progress value={60} color="success" className="w-48" size="sm" />
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <Calendar className="text-purple-500" size={20} />
                    <div>
                      <p className="font-medium text-gray-800 dark:text-white">Mantener racha de 45 días</p>
                      <Progress value={75} color="secondary" className="w-48" size="sm" />
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        </Tab>
      </Tabs>
    </div>
  )
}
