"use client"
import React, { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Card, CardHeader, CardBody, Button, Input, Textarea, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure, Chip } from '@nextui-org/react'
import { createAssignment, listAssignments, Assignment, listSubmissions, gradeSubmission, updateAssignmentStatus } from '@/lib/assignmentsService'
import { Plus, RefreshCw } from 'lucide-react'

export default function TeacherAssignmentsPanel({ teacherId }: { teacherId?: string }) {
  const { user } = useAuth()
  const effectiveTeacherId = teacherId || user?.id
  const { isOpen, onOpen, onOpenChange } = useDisclosure()
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ title: '', description: '', subject: '', due_date: '' })
  const [creating, setCreating] = useState(false)
  const [detailAssignment, setDetailAssignment] = useState<Assignment | null>(null)
  const [submissions, setSubmissions] = useState<any[]>([])
  const [grading, setGrading] = useState<string | null>(null)
  const [statusUpdating, setStatusUpdating] = useState(false)
  const [gradeValues, setGradeValues] = useState<Record<string, { grade: string, feedback: string }>>({})

  const load = async () => {
    setLoading(true)
    try {
    const data = await listAssignments(effectiveTeacherId)
      setAssignments(data.assignments || [])
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { if (effectiveTeacherId) load() }, [effectiveTeacherId])

  const submit = async () => {
    setCreating(true)
    try {
  await createAssignment({ ...form, creator_teacher_id: effectiveTeacherId })
      onOpenChange()
      setForm({ title: '', description: '', subject: '', due_date: '' })
      load()
    } catch (e) { console.error(e) } finally { setCreating(false) }
  }

  const openDetail = async (a: Assignment) => {
    setDetailAssignment(a)
    try {
      const data = await listSubmissions(a.id)
      setSubmissions(data.submissions || [])
    } catch (e) { console.error(e) }
  }

  const submitGrade = async (subId: string) => {
    const g = gradeValues[subId]
    if (!g || g.grade === '') return
    setGrading(subId)
    try {
      await gradeSubmission(subId, parseFloat(g.grade), g.feedback || '')
      const data = await listSubmissions(detailAssignment!.id)
      setSubmissions(data.submissions || [])
    } catch(e){ console.error(e) } finally { setGrading(null) }
  }

  const changeStatus = async (status: string) => {
    if (!detailAssignment) return
    setStatusUpdating(true)
    try {
      const res = await updateAssignmentStatus(detailAssignment.id, status)
      setDetailAssignment(res.assignment)
      load()
    } catch(e){ console.error(e) } finally { setStatusUpdating(false) }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex justify-between items-center">
          <h3 className="font-semibold">Tareas / Asignaciones</h3>
          <div className="flex gap-2">
            <Button size="sm" variant="flat" onPress={load} startContent={<RefreshCw size={16}/>}>Refrescar</Button>
            <Button size="sm" color="primary" startContent={<Plus size={16}/>} onPress={onOpen}>Nueva</Button>
          </div>
        </CardHeader>
        <CardBody>
          <Table aria-label="Listado de tareas">
            <TableHeader>
              <TableColumn>Título</TableColumn>
              <TableColumn>Materia</TableColumn>
              <TableColumn>Vence</TableColumn>
              <TableColumn>Estado</TableColumn>
              <TableColumn>Creada</TableColumn>
            </TableHeader>
            <TableBody emptyContent={loading ? 'Cargando...' : 'Sin tareas'} items={assignments}>
              {assignments.map(a => (
                <TableRow key={a.id} onClick={() => openDetail(a)} className="cursor-pointer hover:bg-default-100">
                  <TableCell>{a.title}</TableCell>
                  <TableCell>{a.subject}</TableCell>
                  <TableCell>{a.due_date ? new Date(a.due_date).toLocaleDateString() : '-'}</TableCell>
                  <TableCell><Chip size="sm" color={a.status === 'active' ? 'success' : 'default'}>{a.status}</Chip></TableCell>
                  <TableCell>{new Date(a.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>

      <Modal isOpen={isOpen} onOpenChange={onOpenChange} placement="center">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Nueva Asignación</ModalHeader>
              <ModalBody>
                <Input label="Título" value={form.title} onChange={e => setForm(f => ({...f, title: e.target.value}))} />
                <Input label="Materia" value={form.subject} onChange={e => setForm(f => ({...f, subject: e.target.value}))} />
                <Input type="date" label="Fecha límite" value={form.due_date} onChange={e => setForm(f => ({...f, due_date: e.target.value}))} />
                <Textarea label="Descripción" value={form.description} onChange={e => setForm(f => ({...f, description: e.target.value}))} />
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>Cancelar</Button>
                <Button color="primary" isLoading={creating} onPress={submit}>Crear</Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      <Modal isOpen={!!detailAssignment} onOpenChange={() => setDetailAssignment(null)} size="3xl" scrollBehavior="inside">
        <ModalContent>
          {onClose => detailAssignment && (
            <>
              <ModalHeader className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold">{detailAssignment.title}</h4>
                  <p className="text-xs text-gray-500">Materia: {detailAssignment.subject} • Vence: {detailAssignment.due_date ? new Date(detailAssignment.due_date).toLocaleDateString() : '—'}</p>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="flat" isLoading={statusUpdating} onPress={() => changeStatus(detailAssignment.status === 'active' ? 'closed' : 'active')}>
                    {detailAssignment.status === 'active' ? 'Cerrar' : 'Reabrir'}
                  </Button>
                </div>
              </ModalHeader>
              <ModalBody>
                <p className="text-sm whitespace-pre-wrap mb-4">{detailAssignment.description}</p>
                <h5 className="font-medium mb-2">Entregas ({submissions.length})</h5>
                <div className="space-y-4">
                  {submissions.map(s => (
                    <Card key={s.id} className="border border-default-200">
                      <CardBody>
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <p className="text-sm font-semibold">Estudiante: {s.student_id}</p>
                            <p className="text-xs text-gray-500">Entregada: {new Date(s.submitted_at).toLocaleString()}</p>
                          </div>
                          <Chip size="sm" color={s.grade != null ? 'primary' : 'warning'}>{s.grade != null ? `Nota ${s.grade}` : 'Sin nota'}</Chip>
                        </div>
                        <p className="text-sm bg-default-50 rounded p-2 mb-3 whitespace-pre-wrap max-h-40 overflow-auto">{s.content}</p>
                        <div className="grid grid-cols-12 gap-2 items-end">
                          <div className="col-span-2">
                            <Input label="Nota" size="sm" type="number" min={0} max={10} value={gradeValues[s.id]?.grade || ''} onChange={e => setGradeValues(v => ({...v, [s.id]: { grade: e.target.value, feedback: v[s.id]?.feedback || '' }}))} />
                          </div>
                          <div className="col-span-7">
                            <Textarea label="Feedback" size="sm" value={gradeValues[s.id]?.feedback || ''} onChange={e => setGradeValues(v => ({...v, [s.id]: { grade: v[s.id]?.grade || '', feedback: e.target.value }}))} />
                          </div>
                          <div className="col-span-3 flex justify-end">
                            <Button size="sm" color="primary" isLoading={grading===s.id} onPress={() => submitGrade(s.id)}>Guardar Nota</Button>
                          </div>
                        </div>
                      </CardBody>
                    </Card>
                  ))}
                  {submissions.length === 0 && <p className="text-xs text-gray-500">Sin entregas aún.</p>}
                </div>
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>Cerrar</Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  )
}
