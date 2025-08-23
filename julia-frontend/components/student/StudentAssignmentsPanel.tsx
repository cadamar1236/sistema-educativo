"use client"
import React, { useEffect, useState } from 'react'
import { Card, CardHeader, CardBody, Button, Textarea, Chip, Accordion, AccordionItem } from '@nextui-org/react'
import { listStudentAssignments, submitAssignment, Assignment } from '@/lib/assignmentsService'
import { Send, RefreshCw } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

export default function StudentAssignmentsPanel({ studentId }: { studentId?: string }) {
  const { user, loading: authLoading } = useAuth() as any
  const effectiveStudentId = studentId || user?.id
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [localLoading, setLocalLoading] = useState(false)
  const [submittingId, setSubmittingId] = useState<string | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})

  const load = async () => {
  setLocalLoading(true)
    try {
    if (!effectiveStudentId) return
    const data = await listStudentAssignments(effectiveStudentId)
      setAssignments(data.assignments || [])
  } catch (e) { console.error(e) } finally { setLocalLoading(false) }
  }

  useEffect(() => { if (effectiveStudentId) load() }, [effectiveStudentId])

  const submit = async (id: string) => {
    setSubmittingId(id)
    try {
      if (!effectiveStudentId) return
      await submitAssignment(id, effectiveStudentId, answers[id] || '')
      load()
    } catch (e) { console.error(e) } finally { setSubmittingId(null) }
  }

  if (authLoading || localLoading || !effectiveStudentId) {
    return <Card><CardBody>Cargando tareas...</CardBody></Card>
  }
  return (
    <Card>
      <CardHeader className="flex justify-between items-center">
        <h3 className="font-semibold">Mis Tareas</h3>
        <Button size="sm" variant="flat" startContent={<RefreshCw size={16}/>} onPress={load}>Refrescar</Button>
      </CardHeader>
      <CardBody>
        <Accordion selectionMode="multiple">
          {assignments.map(a => (
            <AccordionItem key={a.id} aria-label={a.title} title={
              <div className="flex items-center gap-3">
                <span className="font-medium">{a.title}</span>
                <Chip size="sm" color={a.submission_status === 'submitted' ? 'success' : 'warning'}>{a.submission_status === 'submitted' ? 'Entregada' : 'Pendiente'}</Chip>
                {a.grade != null && <Chip size="sm" color="primary">Nota: {a.grade}</Chip>}
              </div>
            }>
              <div className="space-y-4">
                <p className="text-sm text-gray-600">{a.description}</p>
                <p className="text-xs text-gray-500">Vence: {a.due_date ? new Date(a.due_date).toLocaleDateString() : '—'}</p>
                {a.submission_status !== 'submitted' && (
                  <>
                    <Textarea label="Tu respuesta" value={answers[a.id] || ''} onChange={e => setAnswers(ans => ({...ans, [a.id]: e.target.value}))} />
                    <Button color="primary" size="sm" startContent={<Send size={16}/>} isLoading={submittingId===a.id} onPress={() => submit(a.id)}>Entregar</Button>
                  </>
                )}
                {a.submission_status === 'submitted' && <p className="text-green-600 text-sm">Ya entregada {a.submitted_at && 'el ' + new Date(a.submitted_at).toLocaleString()}</p>}
              </div>
            </AccordionItem>
          ))}
        </Accordion>
  {assignments.length === 0 && !localLoading && <p className="text-sm text-gray-500 mt-4">No hay tareas asignadas.</p>}
      </CardBody>
    </Card>
  )
}
