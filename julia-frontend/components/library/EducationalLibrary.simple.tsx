/**
 * Biblioteca Educativa - Componente principal simplificado
 * Maneja documentos, búsquedas y consultas inteligentes
 */

'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Button,
  Input,
  Textarea,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure,
  Tabs,
  Tab,
  Chip,
  Spinner,
  Select,
  SelectItem,
  Divider
} from '@nextui-org/react';
import {
  BookOpenIcon,
  MagnifyingGlassIcon,
  DocumentPlusIcon,
  ChatBubbleLeftRightIcon,
  CloudArrowUpIcon,
  FolderIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { libraryService, type LibraryDocument, type LibraryStats, type DocumentsBySubject } from '@/lib/libraryService';

const SUBJECTS = [
  'Matemáticas', 'Física', 'Química', 'Biología',
  'Historia', 'Literatura', 'Inglés', 'Filosofía',
  'Arte', 'Música', 'Educación Física', 'Informática'
];

const FILE_TYPES = [
  { key: 'text', label: 'Texto' },
  { key: 'pdf', label: 'PDF' },
  { key: 'document', label: 'Word' },
  { key: 'presentation', label: 'PowerPoint' }
];

export default function EducationalLibrary() {
  // Estados principales
  const [documents, setDocuments] = useState<LibraryDocument[]>([]);
  const [documentsBySubject, setDocumentsBySubject] = useState<DocumentsBySubject>({});
  const [stats, setStats] = useState<LibraryStats | null>(null);
  const [searchResults, setSearchResults] = useState<LibraryDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  // Estados de UI
  const [selectedTab, setSelectedTab] = useState('browse');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSubject, setSearchSubject] = useState('');
  const [question, setQuestion] = useState('');
  const [questionAnswer, setQuestionAnswer] = useState<string>('');

  // Modal de upload
  const { isOpen: isUploadOpen, onOpen: onUploadOpen, onOpenChange: onUploadOpenChange } = useDisclosure();
  const [uploadForm, setUploadForm] = useState({
    name: '',
    content: '',
    subject: '',
    topic: '',
    file_type: 'text'
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMode, setUploadMode] = useState<'text' | 'file'>('text');

  // Cargar datos iniciales
  useEffect(() => {
    loadDocuments();
    loadStats();
  }, []);

  const loadDocuments = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const response = await libraryService.getDocuments();
      setDocuments(response.documents || []);
      setDocumentsBySubject(response.documents_by_subject || {});
    } catch (err) {
      setError('Error al cargar documentos');
      console.error('Error loading documents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await libraryService.getLibraryStats();
      setStats(statsData);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const handleUpload = async () => {
    try {
      setIsLoading(true);
      setError('');

      if (uploadMode === 'file') {
        // Subir archivo real
        if (!selectedFile) {
          setError('Por favor selecciona un archivo');
          return;
        }

        await libraryService.uploadFile(selectedFile);
      } else {
        // Subir texto
        if (!uploadForm.name || !uploadForm.content || !uploadForm.subject) {
          setError('Por favor completa todos los campos requeridos');
          return;
        }

        await libraryService.uploadTextDocument(
          uploadForm.name,
          uploadForm.content,
          uploadForm.subject
        );
      }

      // Limpiar formulario
      setUploadForm({
        name: '',
        content: '',
        subject: '',
        topic: '',
        file_type: 'text'
      });
      setSelectedFile(null);
      setUploadMode('text');

      await Promise.all([loadDocuments(), loadStats()]);
      onUploadOpenChange();
    } catch (err) {
      setError('Error al subir documento');
      console.error('Error uploading document:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      setIsLoading(true);
      setError('');

      const results = await libraryService.searchDocuments(searchQuery, searchSubject);
      setSearchResults(results.documents || []);
    } catch (err) {
      setError('Error en la búsqueda');
      console.error('Error searching:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuestion = async () => {
    if (!question.trim()) return;

    try {
      setIsLoading(true);
      setError('');

      const response = await libraryService.askQuestion(question, searchSubject);
      setQuestionAnswer(response.answer);
      setQuestion('');
    } catch (err) {
      setError('Error al procesar la pregunta');
      console.error('Error asking question:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl">
            <BookOpenIcon className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Biblioteca Educativa</h1>
            <p className="text-gray-600">Gestiona tus documentos y consulta con IA</p>
          </div>
        </div>

        <Button
          color="primary"
          size="lg"
          startContent={<DocumentPlusIcon className="h-5 w-5" />}
          onPress={onUploadOpen}
          isLoading={isLoading}
        >
          Subir Documento
        </Button>
      </div>

      {/* Estadísticas básicas */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-gradient-to-r from-blue-50 to-blue-100">
            <CardBody className="text-center">
              <div className="text-3xl font-bold text-blue-600">{stats.total_documents}</div>
              <div className="text-sm text-blue-500">Documentos</div>
            </CardBody>
          </Card>

          <Card className="bg-gradient-to-r from-green-50 to-green-100">
            <CardBody className="text-center">
              <div className="text-3xl font-bold text-green-600">{Object.keys(stats.documents_by_subject).length}</div>
              <div className="text-sm text-green-500">Asignaturas</div>
            </CardBody>
          </Card>

          <Card className="bg-gradient-to-r from-purple-50 to-purple-100">
            <CardBody className="text-center">
              <div className="text-3xl font-bold text-purple-600">{stats.usage_stats.total_searches}</div>
              <div className="text-sm text-purple-500">Búsquedas</div>
            </CardBody>
          </Card>

          <Card className="bg-gradient-to-r from-orange-50 to-orange-100">
            <CardBody className="text-center">
              <div className="text-3xl font-bold text-orange-600">{stats.usage_stats.total_questions}</div>
              <div className="text-sm text-orange-500">Preguntas</div>
            </CardBody>
          </Card>
        </div>
      )}

      {/* Error */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardBody>
            <p className="text-red-600">{error}</p>
          </CardBody>
        </Card>
      )}

      {/* Tabs principales */}
      <Tabs
        selectedKey={selectedTab}
        onSelectionChange={(key) => setSelectedTab(key as string)}
        variant="bordered"
        size="lg"
      >
        <Tab
          key="browse"
          title={
            <div className="flex items-center gap-2">
              <FolderIcon className="h-5 w-5" />
              <span>Explorar</span>
            </div>
          }
        >
          <div className="mt-6">
            <h2 className="text-xl font-semibold mb-4">Mis Documentos</h2>

            {isLoading ? (
              <div className="flex justify-center py-12">
                <Spinner size="lg" />
              </div>
            ) : documents.length === 0 ? (
              <Card>
                <CardBody className="text-center py-12">
                  <DocumentTextIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No hay documentos</h3>
                  <p className="text-gray-500 mb-4">Sube tu primer documento para comenzar</p>
                  <Button
                    color="primary"
                    startContent={<DocumentPlusIcon className="h-4 w-4" />}
                    onPress={onUploadOpen}
                  >
                    Subir Documento
                  </Button>
                </CardBody>
              </Card>
            ) : (
              <div className="grid gap-4">
                {documents.map((doc) => (
                  <Card key={doc.id} className="hover:shadow-lg transition-shadow">
                    <CardBody>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4 flex-1">
                          <div className="text-3xl">
                            {libraryService.getFileIcon(doc.type)}
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-lg text-gray-900">{doc.title}</h3>
                            <p className="text-gray-600 mt-1">{doc.summary}</p>
                            <div className="flex items-center gap-2 mt-3">
                              <Chip
                                size="sm"
                                variant="flat"
                                className="bg-blue-100 text-blue-800"
                                startContent={<span>{libraryService.getSubjectEmoji(doc.subject)}</span>}
                              >
                                {doc.subject}
                              </Chip>
                              <span className="text-sm text-gray-500">
                                {new Date(doc.upload_date).toLocaleDateString()}
                              </span>
                              <span className="text-sm text-gray-500">•</span>
                              <span className="text-sm text-gray-500">{doc.size}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardBody>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </Tab>

        <Tab
          key="search"
          title={
            <div className="flex items-center gap-2">
              <MagnifyingGlassIcon className="h-5 w-5" />
              <span>Buscar</span>
            </div>
          }
        >
          <div className="mt-6 space-y-6">
            <Card>
              <CardHeader>
                <h2 className="text-xl font-semibold">Buscar en la biblioteca</h2>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="grid md:grid-cols-3 gap-4">
                    <Input
                      placeholder="¿Qué estás buscando?"
                      value={searchQuery}
                      onValueChange={setSearchQuery}
                      startContent={<MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />}
                      className="md:col-span-2"
                    />
                    <Select
                      placeholder="Filtrar por asignatura"
                      value={searchSubject}
                      onChange={(e) => setSearchSubject(e.target.value)}
                    >
                      {SUBJECTS.map((subject) => (
                        <SelectItem key={subject} value={subject}>
                          {libraryService.getSubjectEmoji(subject)} {subject}
                        </SelectItem>
                      ))}
                    </Select>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      color="primary"
                      onPress={handleSearch}
                      isLoading={isLoading}
                      isDisabled={!searchQuery.trim()}
                    >
                      Buscar
                    </Button>
                    {searchResults.length > 0 && (
                      <Button variant="flat" onPress={() => setSearchResults([])}>
                        Limpiar
                      </Button>
                    )}
                  </div>
                </div>
              </CardBody>
            </Card>

            {/* Resultados de búsqueda */}
            {searchResults.length > 0 && (
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold">
                    Resultados ({searchResults.length})
                  </h3>
                </CardHeader>
                <CardBody>
                  <div className="space-y-3">
                    {searchResults.map((doc) => (
                      <div key={doc.id} className="p-3 border border-gray-200 rounded-lg">
                        <div className="flex items-start gap-3">
                          <span className="text-2xl">{libraryService.getFileIcon(doc.type)}</span>
                          <div className="flex-1">
                            <h4 className="font-medium">{doc.title}</h4>
                            <p className="text-sm text-gray-600 mt-1">{doc.summary}</p>
                            <div className="flex items-center gap-2 mt-2">
                              <Chip size="sm" variant="flat" className="bg-blue-100 text-blue-800">
                                {doc.subject}
                              </Chip>
                              {doc.relevance && (
                                <span className="text-xs text-gray-500">
                                  {(doc.relevance * 100).toFixed(0)}% relevante
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardBody>
              </Card>
            )}
          </div>
        </Tab>

        <Tab
          key="ask"
          title={
            <div className="flex items-center gap-2">
              <ChatBubbleLeftRightIcon className="h-5 w-5" />
              <span>Preguntar</span>
            </div>
          }
        >
          <div className="mt-6 space-y-6">
            <Card>
              <CardHeader>
                <h2 className="text-xl font-semibold">Pregunta a tu biblioteca</h2>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <Textarea
                    placeholder="Haz una pregunta sobre tus documentos..."
                    value={question}
                    onValueChange={setQuestion}
                    minRows={3}
                  />

                  <div className="flex gap-2">
                    <Button
                      color="primary"
                      onPress={handleQuestion}
                      isLoading={isLoading}
                      isDisabled={!question.trim()}
                      startContent={<ChatBubbleLeftRightIcon className="h-4 w-4" />}
                    >
                      Preguntar
                    </Button>
                    {questionAnswer && (
                      <Button variant="flat" onPress={() => setQuestionAnswer('')}>
                        Limpiar
                      </Button>
                    )}
                  </div>
                </div>
              </CardBody>
            </Card>

            {/* Respuesta */}
            {questionAnswer && (
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold">Respuesta</h3>
                </CardHeader>
                <CardBody>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-green-800 whitespace-pre-wrap">
                      {questionAnswer}
                    </div>
                  </div>
                </CardBody>
              </Card>
            )}
          </div>
        </Tab>
      </Tabs>

      {/* Modal de upload */}
      <Modal
        isOpen={isUploadOpen}
        onOpenChange={onUploadOpenChange}
        size="2xl"
        scrollBehavior="inside"
      >
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex items-center gap-2">
                <CloudArrowUpIcon className="h-5 w-5 text-primary" />
                <span>Subir Documento</span>
              </ModalHeader>
              <ModalBody>
                <div className="space-y-4">
                  {/* Selector de modo de upload */}
                  <Tabs
                    selectedKey={uploadMode}
                    onSelectionChange={(key) => setUploadMode(key as 'text' | 'file')}
                    variant="bordered"
                  >
                    <Tab key="text" title="Texto">
                      <div className="space-y-4 mt-4">
                        <Input
                          label="Título del documento"
                          placeholder="Ej: Introducción al Cálculo"
                          value={uploadForm.name}
                          onValueChange={(value) => setUploadForm(prev => ({ ...prev, name: value }))}
                          isRequired
                        />

                        <div className="grid md:grid-cols-2 gap-4">
                          <Select
                            label="Asignatura"
                            placeholder="Selecciona una asignatura"
                            selectedKeys={uploadForm.subject ? [uploadForm.subject] : []}
                            onSelectionChange={(keys) => {
                              const selected = Array.from(keys)[0] as string;
                              setUploadForm(prev => ({ ...prev, subject: selected }));
                            }}
                            isRequired
                          >
                            {SUBJECTS.map((subject) => (
                              <SelectItem key={subject} value={subject}>
                                {libraryService.getSubjectEmoji(subject)} {subject}
                              </SelectItem>
                            ))}
                          </Select>

                          <Input
                            label="Tema (opcional)"
                            placeholder="Ej: derivadas, integrales"
                            value={uploadForm.topic}
                            onValueChange={(value) => setUploadForm(prev => ({ ...prev, topic: value }))}
                          />
                        </div>

                        <Textarea
                          label="Contenido del documento"
                          placeholder="Pega o escribe el contenido del documento..."
                          value={uploadForm.content}
                          onValueChange={(value) => setUploadForm(prev => ({ ...prev, content: value }))}
                          minRows={8}
                          isRequired
                        />
                      </div>
                    </Tab>
                    
                    <Tab key="file" title="Archivo">
                      <div className="space-y-4 mt-4">
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                          <input
                            type="file"
                            accept=".pdf,.docx,.doc,.txt"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) {
                                setSelectedFile(file);
                              }
                            }}
                            className="hidden"
                            id="file-upload"
                          />
                          <label
                            htmlFor="file-upload"
                            className="cursor-pointer"
                          >
                            <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                            <div className="text-lg font-medium text-gray-900 mb-2">
                              {selectedFile ? selectedFile.name : 'Selecciona un archivo'}
                            </div>
                            <div className="text-sm text-gray-500">
                              PDF, Word (.docx), o archivos de texto (.txt)
                            </div>
                            <div className="text-xs text-gray-400 mt-2">
                              Máximo 10MB
                            </div>
                          </label>
                        </div>

                        {selectedFile && (
                          <div className="bg-blue-50 p-4 rounded-lg">
                            <div className="flex items-center gap-3">
                              <DocumentTextIcon className="h-8 w-8 text-blue-600" />
                              <div>
                                <div className="font-medium text-blue-900">{selectedFile.name}</div>
                                <div className="text-sm text-blue-600">
                                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                </div>
                              </div>
                              <Button
                                size="sm"
                                variant="flat"
                                onPress={() => setSelectedFile(null)}
                              >
                                Quitar
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    </Tab>
                  </Tabs>
                </div>
              </ModalBody>
              <ModalFooter>
                <Button variant="flat" onPress={onClose}>
                  Cancelar
                </Button>
                <Button
                  color="primary"
                  onPress={handleUpload}
                  isLoading={isLoading}
                  isDisabled={
                    uploadMode === 'file' 
                      ? !selectedFile 
                      : !uploadForm.name || !uploadForm.content || !uploadForm.subject
                  }
                >
                  {uploadMode === 'file' ? 'Subir Archivo' : 'Subir Documento'}
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}
