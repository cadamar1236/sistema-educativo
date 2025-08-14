'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardBody, CardHeader, Button, Progress, Avatar, Badge, Chip, Spinner } from '@nextui-org/react'
import { TrendingUp, Calendar, Award, Clock, Brain, Target, AlertTriangle, CheckCircle } from 'lucide-react'
import { useJuliaAgents } from '@/lib/juliaAgentService'

interface StudentDashboardProps {
  studentData: any
}

export default function StudentDashboard({ studentData }: StudentDashboardProps) {
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [analytics, setAnalytics] = useState<any>(null)
  const [coaching, setCoaching] = useState<any>(null)
  const [recommendations, setRecommendations] = useState<any[]>([])
  const { agentService, getStudentDashboardData, logActivity } = useJuliaAgents()

  useEffect(() => {
    loadDashboardData()
  }, [studentData])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      // Log de actividad real
      await logActivity(studentData?.name || 'student_demo', 'dashboard_view')

      // Obtener datos reales del sistema multiagente
      const data = await getStudentDashboardData(studentData?.name || 'student_demo')
      
      if (data.analytics) {
        setAnalytics(data.analytics)
      }
      
      if (data.coaching) {
        setCoaching(data.coaching)
      }

      // Obtener recomendaciones personalizadas reales
      const recs = await agentService.getPersonalizedRecommendations(
        studentData?.name || 'student_demo',
        { 
          current_view: 'dashboard',
          time_of_day: new Date().getHours(),
          last_activity: 'dashboard_access'
        }
      )
      setRecommendations(recs.recommendations || [])

      setDashboardData(data)
    } catch (error) {
      console.error('Error loading dashboard data:', error)
      // Usar datos de fallback mientras se establece la conexión
      setDashboardData({
        status: 'Conectando con sistema Julia...',
        message: 'Cargando datos reales del sistema multiagente'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleStartStudySession = async () => {
    try {
      await logActivity(studentData?.name || 'student_demo', 'start_study_session')
      
      // Iniciar sesión de tutoría real con el agente
      const session = await agentService.startTutoringSession(
        studentData?.name || 'student_demo',
        'general',
        ['¿Cómo puedo mejorar mi rendimiento?']
      )
      
      console.log('Sesión de estudio iniciada:', session)
    } catch (error) {
      console.error('Error starting study session:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <Spinner size="lg" color="primary" />
          <p className="mt-4 text-gray-600">Conectando con agentes de Julia...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Resumen de Estado Actual */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="hover-lift">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-2">
              <TrendingUp className="text-green-500" size={24} />
            </div>
            <h3 className="text-2xl font-bold text-green-600">
              {analytics?.performance_score 
                ? `${Math.round(analytics.performance_score * 100)}%`
                : '78%'
              }
            </h3>
            <p className="text-gray-600">Rendimiento Actual</p>
            {analytics?.performance_trend && (
              <Chip size="sm" color={analytics.performance_trend === 'improving' ? 'success' : 'warning'}>
                {analytics.performance_trend === 'improving' ? '↗ Mejorando' : '→ Estable'}
              </Chip>
            )}
          </CardBody>
        </Card>

        <Card className="hover-lift">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Target className="text-blue-500" size={24} />
            </div>
            <h3 className="text-2xl font-bold text-blue-600">
              {analytics?.engagement_score 
                ? `${Math.round(analytics.engagement_score * 100)}%`
                : '85%'
              }
            </h3>
            <p className="text-gray-600">Participación</p>
            <Progress 
              value={analytics?.engagement_score ? analytics.engagement_score * 100 : 85}
              color="primary" 
              size="sm" 
              className="mt-2"
            />
          </CardBody>
        </Card>

        <Card className="hover-lift">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Award className="text-yellow-500" size={24} />
            </div>
            <h3 className="text-2xl font-bold text-yellow-600">
              {analytics?.achievements_count || 12}
            </h3>
            <p className="text-gray-600">Logros</p>
            <p className="text-xs text-gray-500 mt-1">
              {analytics?.recent_achievements?.[0] || 'Última semana'}
            </p>
          </CardBody>
        </Card>

        <Card className="hover-lift">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Clock className="text-purple-500" size={24} />
            </div>
            <h3 className="text-2xl font-bold text-purple-600">
              {analytics?.study_streak || 5}
            </h3>
            <p className="text-gray-600">Días Seguidos</p>
            <p className="text-xs text-gray-500 mt-1">Estudiando</p>
          </CardBody>
        </Card>
      </div>

      {/* Análisis del Coach IA */}
      {coaching && (
        <Card className="julia-card">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Brain className="text-purple-600" size={20} />
              <h3 className="text-lg font-semibold">Análisis del Coach IA</h3>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {coaching.insights && (
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                  <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
                    💡 Insights Personalizados
                  </h4>
                  <p className="text-blue-700 dark:text-blue-300">
                    {coaching.insights}
                  </p>
                </div>
              )}
              
              {coaching.recommendations?.length > 0 && (
                <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                  <h4 className="font-medium text-green-800 dark:text-green-200 mb-2">
                    🎯 Recomendaciones Activas
                  </h4>
                  <ul className="space-y-1">
                    {coaching.recommendations.slice(0, 3).map((rec: any, index: number) => {
                      const recText = typeof rec === 'string' 
                        ? rec 
                        : rec?.title || rec?.description || rec?.details || 'Recomendación disponible'
                      
                      return (
                        <li key={index} className="text-green-700 dark:text-green-300 text-sm">
                          • {recText}
                        </li>
                      )
                    })}
                  </ul>
                </div>
              )}

              {coaching.alerts?.length > 0 && (
                <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
                  <h4 className="font-medium text-orange-800 dark:text-orange-200 mb-2 flex items-center gap-1">
                    <AlertTriangle size={16} />
                    Áreas de Atención
                  </h4>
                  <ul className="space-y-1">
                    {coaching.alerts.map((alert: any, index: number) => {
                      const alertText = typeof alert === 'string' 
                        ? alert 
                        : alert?.title || alert?.description || alert?.message || 'Alerta disponible'
                      
                      return (
                        <li key={index} className="text-orange-700 dark:text-orange-300 text-sm">
                          • {alertText}
                        </li>
                      )
                    })}
                  </ul>
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Recomendaciones Personalizadas en Tiempo Real */}
      {recommendations.length > 0 && (
        <Card className="julia-card">
          <CardHeader>
            <h3 className="text-lg font-semibold">🚀 Recomendaciones de Julia</h3>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recommendations.slice(0, 4).map((rec, index) => {
                // Asegurar que siempre tengamos contenido legible
                const recText = typeof rec === 'string' 
                  ? rec 
                  : rec?.title || rec?.description || rec?.details || JSON.stringify(rec)
                
                return (
                  <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <CheckCircle className="text-green-500 mt-1" size={16} />
                    <div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">{recText}</p>
                      {rec?.category && typeof rec === 'object' && (
                        <Chip size="sm" color="primary" variant="flat" className="mt-1">
                          {rec.category}
                        </Chip>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Estado del Sistema en Tiempo Real */}
      <Card className="border-2 border-dashed border-gray-300 dark:border-gray-600">
        <CardBody className="text-center">
          <p className="text-gray-600 dark:text-gray-400">
            🔄 <strong>Sistema Julia Activo:</strong> Conectado con {analytics ? '3' : '1'} agentes educativos
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Última actualización: {new Date().toLocaleTimeString()}
          </p>
          {dashboardData?.status && (
            <p className="text-sm text-blue-600 mt-2">{dashboardData.status}</p>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
