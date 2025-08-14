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
          student_id: 'student_001'
        }),
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
  async askQuestion(question: string, subject?: string): Promise<QuestionResponse> {
    try {
      const response = await fetch(`${API_BASE}/api/library/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          subject: subject || '',
          student_id: 'student_001'
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
    tags: string[] = []
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
          student_id: 'student_001'
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
   * Obtener estadísticas de la biblioteca
   */
  async getLibraryStats(): Promise<LibraryStats> {
    try {
      const response = await fetch(`${API_BASE}/api/library/stats?student_id=student_001`);
      
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
}

export const libraryService = new LibraryService();
export default libraryService;
