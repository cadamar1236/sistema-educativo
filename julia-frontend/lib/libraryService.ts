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
  documents: LibraryDocument[];
  total_results: number;
}

export interface UploadResponse {
  success: boolean;
  document_id: string;
  title: string;
  subject: string;
  message: string;
  timestamp: string;
}

export interface QuestionResponse {
  success: boolean;
  question: string;
  answer: string;
  subject?: string;
  timestamp: string;
}

export interface SearchParams {
  query: string;
  subject?: string;
}

export interface QuestionParams {
  question: string;
  subject?: string;
}

export interface UploadParams {
  name: string;
  content: string;
  subject: string;
  file_type: string;
  topic?: string;
}

export interface DocumentsBySubject {
  [subject: string]: LibraryDocument[];
}

/**
 * Servicio principal para la biblioteca educativa
 */
class LibraryService {
  /**
   * Obtener todos los documentos organizados por asignatura
   */
  async getDocuments(): Promise<{
    success: boolean;
    documents: LibraryDocument[];
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
  async searchDocuments(query: string, subject?: string): Promise<SearchResults> {
    try {
      const response = await fetch(`${API_BASE}/api/library/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          subject: subject || '',
          top_k: 10
        }),
      });

      if (!response.ok) {
        throw new Error(`Error searching documents: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Adaptar la respuesta del backend al formato esperado por el frontend
      return {
        success: result.success,
        query: result.query,
        documents: result.results || [],
        total_results: result.total_results || 0
      };
    } catch (error) {
      console.error('Error searching documents:', error);
      throw error;
    }
  }

  /**
   * Hacer una pregunta sobre los documentos
   */
  async askQuestion(question: string, subject?: string): Promise<QuestionResponse> {
    try {
      const response = await fetch(`${API_BASE}/api/library/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          subject: subject || ''
        }),
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
   * Subir un documento a la biblioteca
   */
  async uploadDocument(
    title: string, 
    content: string, 
    subject: string, 
    type: string = 'text', 
  tags: string[] = [],
  studentId?: string
  ): Promise<UploadResponse> {
    try {
      const response = await fetch(`${API_BASE}/api/library/upload-text`, {
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
      // Incluir solo si tenemos identificador real del estudiante
      ...(studentId ? { student_id: studentId } : {})
        }),
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
   * Subir un archivo real (PDF, Word, etc.)
   */
  async uploadFile(file: File, metadata?: { subject?: string; topic?: string }): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      if (metadata?.subject) {
        formData.append('subject', metadata.subject);
      }
      if (metadata?.topic) {
        formData.append('topic', metadata.topic);
      }

      const response = await fetch(`${API_BASE}/api/library/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Error uploading file: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  }

  /**
   * Subir un documento de texto directo
   */
  async uploadTextDocument(title: string, content: string, subject: string): Promise<UploadResponse> {
    try {
      const response = await fetch(`${API_BASE}/api/library/upload-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          content,
          subject
        }),
      });

      if (!response.ok) {
        throw new Error(`Error uploading text document: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading text document:', error);
      throw error;
    }
  }

  /**
   * Obtener estadísticas de la biblioteca
   */
  async getLibraryStats(): Promise<LibraryStats> {
    try {
      const response = await fetch(`${API_BASE}/api/library/stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting library stats:', error);
      throw error;
    }
  }

  /**
   * Obtener emoji para una asignatura
   */
  getSubjectEmoji(subject: string): string {
    const emojiMap: Record<string, string> = {
      'Matemáticas': '📊',
      'Física': '⚛️',
      'Química': '🧪',
      'Biología': '🧬',
      'Historia': '🏛️',
      'Literatura': '📚',
      'Inglés': '🇺🇸',
      'Filosofía': '🤔',
      'Arte': '🎨',
      'Música': '🎵',
      'Educación Física': '⚽',
      'Informática': '💻',
      'Ciencias': '🔬',
      'General': '📝'
    };
    return emojiMap[subject] || '📄';
  }

  /**
   * Obtener emoji para un tipo de documento
   */
  getTypeEmoji(type: string): string {
    const emojiMap: Record<string, string> = {
      'pdf': '📄',
      'document': '📝',
      'presentation': '📊',
      'video': '🎥',
      'text': '📋'
    };
    return emojiMap[type] || '📄';
  }

  /**
   * Obtener icono de archivo (alias para getTypeEmoji)
   */
  getFileIcon(type: string): string {
    return this.getTypeEmoji(type);
  }

  /**
   * Obtener color de tema para una asignatura
   */
  getSubjectColor(subject: string): string {
    const colorMap: Record<string, string> = {
      'Matemáticas': 'bg-blue-100 text-blue-800',
      'Física': 'bg-purple-100 text-purple-800',
      'Química': 'bg-green-100 text-green-800',
      'Biología': 'bg-emerald-100 text-emerald-800',
      'Historia': 'bg-orange-100 text-orange-800',
      'Literatura': 'bg-pink-100 text-pink-800',
      'Inglés': 'bg-indigo-100 text-indigo-800',
      'Filosofía': 'bg-gray-100 text-gray-800',
      'Arte': 'bg-red-100 text-red-800',
      'Música': 'bg-yellow-100 text-yellow-800',
      'Educación Física': 'bg-green-100 text-green-800',
      'Informática': 'bg-blue-100 text-blue-800',
      'Ciencias': 'bg-cyan-100 text-cyan-800',
      'General': 'bg-gray-100 text-gray-800'
    };
    return colorMap[subject] || 'bg-gray-100 text-gray-800';
  }

  /**
   * Formatear fecha para mostrar
   */
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
}

export const libraryService = new LibraryService();
export default libraryService;
