"use client"
import React, { useEffect } from 'react'
import TeacherAssignmentsPanel from '@/components/teacher/TeacherAssignmentsPanel'
import { Tabs, Tab, Card, CardBody } from '@nextui-org/react'
import { useAuth } from '@/hooks/useAuth'
import { useRouter } from 'next/navigation'

export default function TeacherDashboardPage() {
  const { user, loading, role } = useAuth() as any
  const router = useRouter()

  useEffect(() => {
    if (!loading) {
      if (!user) {
        if (typeof window !== 'undefined') {
          try { localStorage.setItem('auth_redirect', '/dashboard/teacher'); } catch {}
        }
        router.push('/login')
      } else if (role !== 'teacher') {
        router.push('/dashboard')
      }
    }
  }, [user, loading, role, router])

  if (loading || !user || role !== 'teacher') {
    return <div className="p-6">Verificando permisos...</div>
  }
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">Panel Docente</h1>
      <Tabs aria-label="Panel docente" variant="bordered">
        <Tab key="assignments" title="Tareas">
          <TeacherAssignmentsPanel teacherId={user.id} />
        </Tab>
      </Tabs>
    </div>
  )
}
