import { apiBase } from './runtimeApi'
const API_BASE = (apiBase() + '/api').replace(/\/$/, '')

export interface Assignment {
  id: string
  title: string
  description: string
  subject: string
  due_date: string
  status: string
  created_at: string
  submission_status?: string
  submitted_at?: string
  grade?: number | null
}

export async function createAssignment(data: Partial<Assignment> & { creator_teacher_id?: string }) {
  const res = await fetch(`${API_BASE}/assignments`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
  if (!res.ok) throw new Error('Error creating assignment')
  return res.json()
}

export async function listAssignments(teacherId?: string) {
  const url = teacherId ? `${API_BASE}/assignments?teacher_id=${encodeURIComponent(teacherId)}` : `${API_BASE}/assignments`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Error listing assignments')
  return res.json()
}

export async function listStudentAssignments(studentId: string) {
  const res = await fetch(`${API_BASE}/students/${encodeURIComponent(studentId)}/assignments`)
  if (!res.ok) throw new Error('Error listing student assignments')
  return res.json()
}

export async function submitAssignment(assignmentId: string, studentId: string, content: string) {
  const res = await fetch(`${API_BASE}/assignments/${assignmentId}/submit`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ student_id: studentId, content }) })
  if (!res.ok) throw new Error('Error submitting assignment')
  return res.json()
}

export async function gradeSubmission(submissionId: string, grade: number, feedback: string) {
  const res = await fetch(`${API_BASE}/submissions/${submissionId}/grade`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ grade, feedback }) })
  if (!res.ok) throw new Error('Error grading submission')
  return res.json()
}

export async function listSubmissions(assignmentId: string) {
  const res = await fetch(`${API_BASE}/assignments/${assignmentId}/submissions`)
  if (!res.ok) throw new Error('Error listing submissions')
  return res.json()
}

export async function updateAssignmentStatus(assignmentId: string, status: string) {
  const res = await fetch(`${API_BASE}/assignments/${assignmentId}/status`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) })
  if (!res.ok) throw new Error('Error updating status')
  return res.json()
}
