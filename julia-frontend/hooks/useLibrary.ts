/**
 * Hook para gestionar la biblioteca educativa
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { libraryService } from '@/lib/libraryService';
import type {
  LibraryDocument,
  LibraryStats,
  SearchResults,
  UploadResponse,
  QuestionResponse,
  SearchParams,
  QuestionParams,
  UploadParams
} from '@/lib/libraryService';

interface SearchResultsState {
  query: string;
  subject_filter?: string;
  formatted_results?: string;
  results?: string;
  documents: LibraryDocument[];
}

interface UseLibraryReturn {
  // Estado
  documents: LibraryDocument[];
  documentsBySubject: Record<string, LibraryDocument[]>;
  stats: LibraryStats | null;
  searchResults: SearchResultsState | null;
  questionAnswer: QuestionResponse | null;
  
  // Estados de carga
  loading: boolean;
  uploading: boolean;
  searching: boolean;
  asking: boolean;
  
  // Error
  error: string | null;
  
  // Acciones
  uploadDocument: (params: UploadParams) => Promise<UploadResponse | null>;
  searchDocuments: (params: SearchParams) => Promise<SearchResults | null>;
  askQuestion: (params: QuestionParams) => Promise<QuestionResponse | null>;
  loadDocuments: () => Promise<void>;
  loadStats: () => Promise<void>;
  clearError: () => void;
  clearResults: () => void;
}

export function useLibrary(): UseLibraryReturn {
  const { user } = useAuth() as any;
  const effectiveStudentId = user?.id || user?.email || undefined;
  // Estados principales
  const [documents, setDocuments] = useState<LibraryDocument[]>([]);
  const [documentsBySubject, setDocumentsBySubject] = useState<Record<string, LibraryDocument[]>>({});
  const [stats, setStats] = useState<LibraryStats | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResultsState | null>(null);
  const [questionAnswer, setQuestionAnswer] = useState<QuestionResponse | null>(null);
  
  // Estados de carga
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [asking, setAsking] = useState(false);
  
  // Error
  const [error, setError] = useState<string | null>(null);

  /**
   * Manejar errores
   */
  const handleError = (err: unknown, defaultMessage: string) => {
    console.error(err);
    const message = err instanceof Error ? err.message : defaultMessage;
    setError(message);
  };

  /**
   * Cargar documentos
   */
  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await libraryService.getDocuments();
      
      // Manejar tanto la estructura plana como la organizada por materias
      const docsArray = response.documents || [];
      const docsBySubject = response.documents_by_subject || {};
      
      setDocuments(docsArray);
      setDocumentsBySubject(docsBySubject);
    } catch (err) {
      handleError(err, 'Error al cargar documentos');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Cargar estadísticas
   */
  const loadStats = useCallback(async () => {
    try {
      setError(null);
      
      const statsData = await libraryService.getLibraryStats();
      setStats(statsData);
    } catch (err) {
      handleError(err, 'Error al cargar estadísticas');
    }
  }, []);

  /**
   * Subir documento
   */
  const uploadDocument = useCallback(async (params: UploadParams): Promise<UploadResponse | null> => {
    try {
      setUploading(true);
      setError(null);
      
      const response = await libraryService.uploadDocument(
        params.name,
        params.content,
        params.subject,
        params.file_type,
        params.topic ? [params.topic] : [],
        effectiveStudentId
      );
      
      // Recargar documentos y estadísticas
      await Promise.all([
        loadDocuments(),
        loadStats()
      ]);
      
      return response;
    } catch (err) {
      handleError(err, 'Error al subir documento');
      return null;
    } finally {
      setUploading(false);
    }
  }, [loadDocuments, loadStats, effectiveStudentId]);

  /**
   * Buscar documentos
   */
  const searchDocuments = useCallback(async (params: SearchParams): Promise<SearchResults | null> => {
    try {
      setSearching(true);
      setError(null);
      
      const response = await libraryService.searchDocuments(params.query, params.subject);
      setSearchResults({
        query: response.query,
        subject_filter: params.subject,
        formatted_results: (response as any).formatted_results,
        results: (response as any).results,
        documents: response.documents || []
      });
      return response;
    } catch (err) {
      handleError(err, 'Error en la búsqueda');
      return null;
    } finally {
      setSearching(false);
    }
  }, []);

  /**
   * Hacer pregunta
   */
  const askQuestion = useCallback(async (params: QuestionParams): Promise<QuestionResponse | null> => {
    try {
      setAsking(true);
      setError(null);
      
      const response = await libraryService.askQuestion(params.question, params.subject);
      setQuestionAnswer(response);
      
      return response;
    } catch (err) {
      handleError(err, 'Error al procesar la pregunta');
      return null;
    } finally {
      setAsking(false);
    }
  }, []);

  /**
   * Limpiar error
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Limpiar resultados
   */
  const clearResults = useCallback(() => {
  setSearchResults(null);
    setQuestionAnswer(null);
  }, []);

  // Cargar datos iniciales
  useEffect(() => {
    loadDocuments();
    loadStats();
  }, [loadDocuments, loadStats]);

  return {
    // Estado
    documents,
    documentsBySubject,
    stats,
    searchResults,
    questionAnswer,
    
    // Estados de carga
    loading,
    uploading,
    searching,
    asking,
    
    // Error
    error,
    
    // Acciones
    uploadDocument,
    searchDocuments,
    askQuestion,
    loadDocuments,
    loadStats,
    clearError,
    clearResults
  };
}