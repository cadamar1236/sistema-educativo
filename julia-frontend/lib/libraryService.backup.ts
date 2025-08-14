/**
 * Servicio para interactuar con la biblioteca educativa
 * Maneja documentos, búsquedas y consultas RAG
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface LibraryDocument {
  id: string;
  title: string;
  subject: string;
  type: string;
  upload_date: string;
  size: string;
  tags: string[];
  summary: string;
  relevance?: number;
}

export interface LibraryStats {
  total_documents: number;
  documents_by_subject: Record<string, number>;
  documents_by_type: Record<string, number>;
  recent_uploads: Array<{
    id: string;
    title: string;
    subject: string;
    date: string;
  }>;
  usage_stats: {
    total_searches: number;
    total_questions: number;
    most_searched_subject: string;
    avg_questions_per_day: number;
  };
  popular_searches: string[];
  popular_tags: Array<{
    tag: string;
    count: number;
  }>;
  total_storage_used: string;
  timestamp: string;
}

export interface SearchResults {
  success: boolean;
  query: string;
  results: LibraryDocument[];
  ai_analysis: string;
  total_results: number;
}

export interface UploadResponse {
  success: boolean;
  document_id: string;
  title: string;
  subject: string;
  processing_result: string;
  message: string;
}

export interface QuestionResponse {
  success: boolean;
  question: string;
  answer: string;
  document_ids: string[];
  context: any;
}

// Legacy interface for backward compatibility
export interface Document {
  id: string;
  name: string;
  topic: string;
  upload_date: string;
  size: string;
  type: string;
  subject?: string;
}

export interface DocumentsBySubject {
  [subject: string]: Document[];
}

export interface LibraryStats {
  total_documents: number;
  documents_by_subject: { [subject: string]: number };
  recent_uploads: Array<{
    name: string;
    subject: string;
    date: string;
  }>;
  popular_searches: string[];
  total_storage: string;
  last_activity: string;
}

export interface UploadDocumentRequest {
  content: string;
  name: string;
  subject: string;
  topic?: string;
  file_type?: string;
}

export interface SearchRequest {
  query: string;
  subject?: string;
}

export interface AskRequest {
  question: string;
  context_documents?: string[];
  subject?: string;
}

class LibraryService {
  
  /**
   * Subir un documento a la biblioteca
   */
  async uploadDocument(documentData: UploadDocumentRequest) {
    try {
      const response = await fetch(`${API_BASE}/api/library/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(documentData),
      });

      if (!response.ok) {
        throw new Error(`Error uploading document: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading document:', error);
      throw error;
    }
  }

  /**
   * Obtener todos los documentos organizados por asignatura
   */
  async getDocuments(): Promise<{
    success: boolean;
    documents_by_subject: DocumentsBySubject;
    total_documents: number;
    subjects: string[];
  }> {
    try {
      const response = await fetch(`${API_BASE}/api/library/documents`);
      
      if (!response.ok) {
        throw new Error(`Error fetching documents: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching documents:', error);
      throw error;
    }
  }

  /**
   * Buscar documentos en la biblioteca
   */
  async searchDocuments(searchData: SearchRequest) {
    try {
      const response = await fetch(`${API_BASE}/api/library/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchData),
      });

      if (!response.ok) {
        throw new Error(`Error searching documents: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error searching documents:', error);
      throw error;
    }
  }

  /**
   * Hacer una pregunta sobre los documentos
   */
  async askQuestion(askData: AskRequest) {
    try {
      const response = await fetch(`${API_BASE}/api/library/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(askData),
      });

      if (!response.ok) {
        throw new Error(`Error asking question: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error asking question:', error);
      throw error;
    }
  }

  /**
   * Obtener estadísticas de la biblioteca
   */
  async getLibraryStats(): Promise<{
    success: boolean;
    stats: LibraryStats;
  }> {
    try {
      const response = await fetch(`${API_BASE}/api/library/stats`);
      
      if (!response.ok) {
        throw new Error(`Error fetching library stats: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching library stats:', error);
      throw error;
    }
  }

  /**
   * Formatear fecha para mostrar
   */
  formatDate(dateString: string): string {
    try {
      return new Date(dateString).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  }

  /**
   * Obtener icono según el tipo de archivo
   */
  getFileIcon(fileType: string): string {
    const icons: { [key: string]: string } = {
      'PDF': '📄',
      'DOCX': '📝',
      'TXT': '📃',
      'DOC': '📝',
      'PPT': '📊',
      'PPTX': '📊',
      'XLS': '📈',
      'XLSX': '📈',
      'IMAGE': '🖼️',
      'VIDEO': '🎥',
      'AUDIO': '🎵'
    };
    
    return icons[fileType.toUpperCase()] || '📄';
  }

  /**
   * Obtener color según la asignatura
   */
  getSubjectColor(subject: string): string {
    const colors: { [key: string]: string } = {
      'Matemáticas': 'bg-blue-100 text-blue-800',
      'Física': 'bg-purple-100 text-purple-800',
      'Química': 'bg-green-100 text-green-800',
      'Biología': 'bg-emerald-100 text-emerald-800',
      'Historia': 'bg-amber-100 text-amber-800',
      'Literatura': 'bg-rose-100 text-rose-800',
      'Inglés': 'bg-indigo-100 text-indigo-800',
      'Filosofía': 'bg-gray-100 text-gray-800',
      'Arte': 'bg-pink-100 text-pink-800',
      'Música': 'bg-violet-100 text-violet-800',
      'Educación Física': 'bg-orange-100 text-orange-800',
      'Informática': 'bg-cyan-100 text-cyan-800'
    };
    
    return colors[subject] || 'bg-gray-100 text-gray-800';
  }

  /**
   * Obtener emoji según la asignatura
   */
  getSubjectEmoji(subject: string): string {
    const emojis: { [key: string]: string } = {
      'Matemáticas': '🔢',
      'Física': '⚛️',
      'Química': '🧪',
      'Biología': '🧬',
      'Historia': '📜',
      'Literatura': '📚',
      'Inglés': '🇬🇧',
      'Filosofía': '🤔',
      'Arte': '🎨',
      'Música': '🎵',
      'Educación Física': '⚽',
      'Informática': '💻'
    };
    
    return emojis[subject] || '📖';
  }

  // === NUEVOS MÉTODOS PARA BIBLIOTECA EDUCATIVA ===

  async uploadDocument(
    title: string,
    content: string,
    subject: string,
    type: string = 'pdf',
    tags: string[] = [],
    studentId: string = 'student_001'
  ): Promise<UploadResponse> {
    try {
      const response = await fetch(`${API_BASE}/api/library/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          content,
          subject,
          type,
          tags,
          student_id: studentId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading document:', error);
      throw error;
    }
  }

  async searchDocuments(
    query: string,
    subject: string = '',
    type: string = '',
    studentId: string = 'student_001'
  ): Promise<SearchResults> {
    try {
      const response = await fetch(`${API_BASE}/api/library/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          subject,
          type,
          student_id: studentId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error searching documents:', error);
      throw error;
    }
  }

  async askQuestion(
    question: string,
    documentIds: string[] = [],
    context: any = {},
    studentId: string = 'student_001'
  ): Promise<QuestionResponse> {
    try {
      const response = await fetch(`${API_BASE}/api/library/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          document_ids: documentIds,
          context,
          student_id: studentId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error asking question:', error);
      throw error;
    }
  }

  async getLibraryStats(studentId: string = 'student_001'): Promise<{ success: boolean; library_stats: LibraryStats }> {
    try {
      const response = await fetch(`${API_BASE}/api/library/stats?student_id=${studentId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting library stats:', error);
      throw error;
    }
  }

  async getAllDocuments(
    studentId: string = 'student_001',
    subject: string = '',
    limit: number = 20
  ): Promise<{ success: boolean; documents: LibraryDocument[]; total: number }> {
    try {
      const params = new URLSearchParams({
        student_id: studentId,
        limit: limit.toString(),
      });

      if (subject) {
        params.append('subject', subject);
      }

      const response = await fetch(`${API_BASE}/api/library/documents?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting documents:', error);
      throw error;
    }
  }

  // Métodos utilitarios mejorados
  getSubjectIcon(subject: string): string {
    return this.getSubjectEmoji(subject);
  }

  getTypeIcon(type: string): string {
    return this.getFileIcon(type);
  }

  formatFileSize(size: string): string {
    // Si ya viene formateado, devolverlo tal como está
    if (size.includes('MB') || size.includes('KB') || size.includes('GB')) {
      return size;
    }
    
    // Si es un número, convertir a formato legible
    const bytes = parseInt(size);
    if (isNaN(bytes)) return size;
    
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  }
}

export const libraryService = new LibraryService();
