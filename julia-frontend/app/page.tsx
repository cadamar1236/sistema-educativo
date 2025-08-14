'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardBody, CardHeader, Button, Progress, Avatar, Badge, Chip, Tabs, Tab } from '@nextui-org/react'
import { BookOpen, TrendingUp, Calendar, Award, Clock, Brain, Target, MessageCircle, BarChart3, Users, Star, Library } from 'lucide-react'
import StudentDashboard from '@/components/student/StudentDashboard'
import StudyPlanner from '@/components/student/StudyPlanner'
import ProgressTrackerReal from '@/components/student/ProgressTrackerReal'
import AICoachReal from '@/components/student/AICoachReal'
import VirtualClassroom from '@/components/student/VirtualClassroom'
import EducationalLibrary from '@/components/library/EducationalLibrary'
import MainDashboard from "../components/MainDashboard"

export default function StudentPortal() {
  const [selectedTab, setSelectedTab] = useState('dashboard')
  const [studentData, setStudentData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulamos la carga de datos del estudiante
    const loadStudentData = async () => {
      try {
        // En producción, esto sería una llamada a la API
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        setStudentData({
          name: "María González",
          grade: "10° Grado",
          avatar: "/avatars/student-maria.jpg",
          currentLevel: "Intermedio Avanzado",
          overallProgress: 78,
          weeklyGoal: 85,
          streak: 12,
          badges: ['Lectora Avanzada', 'Matemática Estrella', 'Científica Curiosa'],
          upcomingClasses: [
            { subject: 'Matemáticas', time: '09:00', teacher: 'Prof. García' },
            { subject: 'Química', time: '11:00', teacher: 'Prof. Martínez' },
            { subject: 'Literatura', time: '14:00', teacher: 'Prof. López' }
          ],
          recentAchievements: [
            { title: 'Completó módulo de Álgebra', date: '2024-01-15', points: 150 },
            { title: 'Perfect Score en Quiz de Historia', date: '2024-01-14', points: 100 },
            { title: '7 días consecutivos estudiando', date: '2024-01-13', points: 75 }
          ]
        })
        setIsLoading(false)
      } catch (error) {
        console.error('Error loading student data:', error)
        setIsLoading(false)
      }
    }

    loadStudentData()
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-purple-900 dark:to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="julia-spinner mb-4"></div>
          <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">Cargando tu espacio de aprendizaje...</h2>
          <p className="text-gray-600 dark:text-gray-300">Julia está preparando todo para ti</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-purple-900 dark:to-gray-900">
      {/* Header del Estudiante */}
      <header className="julia-navbar p-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-xl">J</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Julia</h1>
                <p className="text-sm text-gray-600 dark:text-gray-300">Tu Asistente Educativo</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="font-semibold text-gray-800 dark:text-white">{studentData?.name}</p>
              <p className="text-sm text-gray-600 dark:text-gray-300">{studentData?.grade}</p>
            </div>
            <Avatar
              src={studentData?.avatar}
              name={studentData?.name}
              size="lg"
              className="border-2 border-purple-200"
            />
            <Badge content={3} color="danger" shape="circle">
              <Button isIconOnly variant="light" className="text-gray-600">
                <MessageCircle size={20} />
              </Button>
            </Badge>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {/* Navegación por pestañas */}
        <div className="mb-8">
          <Tabs 
            selectedKey={selectedTab} 
            onSelectionChange={setSelectedTab}
            variant="bordered"
            size="lg"
            className="w-full"
          >
            <Tab 
              key="dashboard" 
              title={
                <div className="flex items-center gap-2">
                  <BarChart3 size={18} />
                  <span>Panel Principal</span>
                </div>
              }
            />
            <Tab 
              key="planner" 
              title={
                <div className="flex items-center gap-2">
                  <Calendar size={18} />
                  <span>Planificador</span>
                </div>
              }
            />
            <Tab 
              key="progress" 
              title={
                <div className="flex items-center gap-2">
                  <TrendingUp size={18} />
                  <span>Mi Progreso</span>
                </div>
              }
            />
            <Tab 
              key="coach" 
              title={
                <div className="flex items-center gap-2">
                  <Brain size={18} />
                  <span>Coach IA</span>
                </div>
              }
            />
            <Tab 
              key="classroom" 
              title={
                <div className="flex items-center gap-2">
                  <Users size={18} />
                  <span>Aula Virtual</span>
                </div>
              }
            />
            <Tab 
              key="library" 
              title={
                <div className="flex items-center gap-2">
                  <Library size={18} />
                  <span>Biblioteca</span>
                </div>
              }
            />
          </Tabs>
        </div>

        {/* Contenido basado en la pestaña seleccionada */}
        <div className="animate-fade-in-up">
          {selectedTab === 'dashboard' && (
            <StudentDashboard studentData={studentData} />
          )}
          {selectedTab === 'planner' && <StudyPlanner studentData={studentData} />}
          {selectedTab === 'progress' && <ProgressTrackerReal studentData={studentData} />}
          {selectedTab === 'coach' && <AICoachReal studentData={studentData} />}
          {selectedTab === 'classroom' && <VirtualClassroom studentData={studentData} />}
          {selectedTab === 'library' && <EducationalLibrary />}
        </div>
      </main>
    </div>
  )
}
