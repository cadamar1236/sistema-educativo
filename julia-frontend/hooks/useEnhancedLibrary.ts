import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

interface Document {
  id: string;
  title: string;
  content?: string;
  file_type?: string;
  size?: number;
  metadata?: any;
  ocr_enabled?: boolean;
  upload_date?: string;
  chunks?: number;
  status?: 'processing' | 'completed' | 'error';
}

interface UploadOptions {
  ocr_enabled?: boolean;
  chunk_size?: number;
  chunk_overlap?: number;
}

interface UseEnhancedLibraryReturn {
  documents: Document[];
  uploadProgress: number;
  isUploading: boolean;
  isLoading: boolean;
  error: string | null;
  uploadDocument: (file: File, options?: UploadOptions) => Promise<void>;
  uploadMultiple: (files: File[], options?: UploadOptions) => Promise<void>;
  deleteDocument: (id: string) => Promise<void>;
  refreshDocuments: () => Promise<void>;
  searchDocuments: (query: string) => Promise<Document[]>;
  getDocument: (id: string) => Promise<Document | null>;
  supportedFormats: string[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useEnhancedLibrary(): UseEnhancedLibraryReturn {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [supportedFormats, setSupportedFormats] = useState<string[]>([]);

  // Fetch supported formats on mount
  useEffect(() => {
    fetchSupportedFormats();
    refreshDocuments();
  }, []);

  const fetchSupportedFormats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/library/formats`);
      setSupportedFormats(response.data.formats || []);
    } catch (err) {
      console.error('Failed to fetch supported formats:', err);
      // Fallback to common formats
      setSupportedFormats([
        'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
        'xls', 'xlsx', 'csv', 'ods',
        'ppt', 'pptx', 'odp',
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
        'mp4', 'avi', 'mov', 'mp3', 'wav',
        'zip', 'rar', '7z', 'tar',
        'html', 'xml', 'json', 'py', 'js', 'css'
      ]);
    }
  };

  const refreshDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/library/documents`);
      setDocuments(response.data.documents || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch documents');
      console.error('Failed to fetch documents:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(async (file: File, options?: UploadOptions) => {
    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);
    
    if (options?.ocr_enabled) {
      formData.append('ocr_enabled', 'true');
    }
    if (options?.chunk_size) {
      formData.append('chunk_size', options.chunk_size.toString());
    }
    if (options?.chunk_overlap) {
      formData.append('chunk_overlap', options.chunk_overlap.toString());
    }

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/library/upload/enhanced`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            setUploadProgress(percentCompleted);
          },
        }
      );

      if (response.data.success) {
        await refreshDocuments();
        setUploadProgress(100);
      } else {
        throw new Error(response.data.error || 'Upload failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
      console.error('Upload error:', err);
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  }, [refreshDocuments]);

  const uploadMultiple = useCallback(async (files: File[], options?: UploadOptions) => {
    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    
    if (options?.ocr_enabled) {
      formData.append('ocr_enabled', 'true');
    }
    if (options?.chunk_size) {
      formData.append('chunk_size', options.chunk_size.toString());
    }
    if (options?.chunk_overlap) {
      formData.append('chunk_overlap', options.chunk_overlap.toString());
    }

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/library/upload/multiple`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 1)
            );
            setUploadProgress(percentCompleted);
          },
        }
      );

      if (response.data.success) {
        await refreshDocuments();
        setUploadProgress(100);
      } else {
        throw new Error(response.data.error || 'Upload failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
      console.error('Upload error:', err);
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  }, [refreshDocuments]);

  const deleteDocument = useCallback(async (id: string) => {
    try {
      const response = await axios.delete(`${API_BASE_URL}/api/library/document/${id}`);
      if (response.data.success) {
        setDocuments(prev => prev.filter(doc => doc.id !== id));
      } else {
        throw new Error(response.data.error || 'Delete failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Delete failed');
      console.error('Delete error:', err);
    }
  }, []);

  const searchDocuments = useCallback(async (query: string): Promise<Document[]> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/library/search`, {
        params: { query }
      });
      return response.data.documents || [];
    } catch (err) {
      console.error('Search error:', err);
      return [];
    }
  }, []);

  const getDocument = useCallback(async (id: string): Promise<Document | null> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/library/document/${id}`);
      return response.data.document || null;
    } catch (err) {
      console.error('Get document error:', err);
      return null;
    }
  }, []);

  return {
    documents,
    uploadProgress,
    isUploading,
    isLoading,
    error,
    uploadDocument,
    uploadMultiple,
    deleteDocument,
    refreshDocuments,
    searchDocuments,
    getDocument,
    supportedFormats
  };
}