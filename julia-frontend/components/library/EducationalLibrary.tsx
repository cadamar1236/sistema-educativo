/**
 * Biblioteca Educativa - Componente principal
 * Maneja documentos, búsquedas y consultas inteligentes
 */

'use client';

import React, { useState } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Button,
  Input,
  Textarea,
  Tabs,
  Tab,
  Chip,
  Spinner,
  Select,
  SelectItem,
  Divider,
  Badge,
  Accordion,
  AccordionItem
} from '@nextui-org/react';
import {
  BookOpenIcon,
  MagnifyingGlassIcon,
  DocumentPlusIcon,
  ChatBubbleLeftRightIcon,
  CloudArrowUpIcon,
  FolderIcon,
  DocumentTextIcon,
  QuestionMarkCircleIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline';
import { useLibrary } from '@/hooks/useLibrary';
import { libraryService } from '@/lib/libraryService';
import LibraryStats from './LibraryStats';

const SUBJECTS = [
  'Matemáticas', 'Física', 'Química', 'Biología',
  'Historia', 'Literatura', 'Inglés', 'Filosofía',
  'Arte', 'Música', 'Educación Física', 'Informática'
];

const FILE_TYPES = [
  { key: 'text', label: 'Texto' },
  { key: 'pdf', label: 'PDF' },
  { key: 'docx', label: 'Word' },
  { key: 'pptx', label: 'PowerPoint' }
];

export default function EducationalLibrary() {
  const {
    documents,
    documentsBySubject,
    stats,
    searchResults,
    questionAnswer,
    loading,
    uploading,
    searching,
    asking,
    error,
    uploadDocument,
    searchDocuments,
    askQuestion,
    loadDocuments,
    clearError,
    clearResults
  } = useLibrary();

  // Estados locales
  const [selectedTab, setSelectedTab] = useState('browse');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSubject, setSearchSubject] = useState('');
  const [question, setQuestion] = useState('');
  const [questionSubject, setQuestionSubject] = useState('');
  const [fileUploading, setFileUploading] = useState(false);
  
  // Estados del formulario de upload
  const [uploadForm, setUploadForm] = useState({
    name: '',
    content: '',
    subject: '',
    topic: '',
    file_type: 'text',
    selectedFile: null as File | null
  });

  /**
   * Manejar upload de documento de texto
   */
  const handleUpload = async () => {
    if (!uploadForm.name || !uploadForm.content || !uploadForm.subject) {
      return;
    }

    try {
      await uploadDocument(uploadForm);
      
      // Limpiar formulario
      setUploadForm({
        name: '',
        content: '',
        subject: '',
        topic: '',
        file_type: 'text',
        selectedFile: null
      });
      
      alert('¡Documento subido exitosamente!');
    } catch (err) {
      // El error ya se maneja en el hook
      alert('Error al subir el documento');
    }
  };

  /**
   * Manejar búsqueda
   */
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    await searchDocuments({
      query: searchQuery,
      subject: searchSubject || undefined
    });
  };

  /**
   * Manejar pregunta
   */
  const handleQuestion = async () => {
    if (!question.trim()) return;
    
    await askQuestion({
      question: question,
      subject: questionSubject || undefined
    });
  };

  /**
   * Renderizar estadísticas
   */
  const renderStats = () => {
    return <LibraryStats stats={stats} loading={loading} />;
  };

  /**
   * Renderizar documentos por asignatura
   */
  const renderDocuments = () => {
    const subjects = Object.keys(documentsBySubject);
    
    if (subjects.length === 0) {
      return (
        <Card>
          <CardBody className="text-center py-8">
            <BookOpenIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No hay documentos en la biblioteca</p>
            <Button
              color="primary"
              variant="flat"
              startContent={<DocumentPlusIcon className="h-4 w-4" />}
              onPress={() => setSelectedTab('upload')}
              className="mt-4"
            >
              Subir primer documento
            </Button>
          </CardBody>
        </Card>
      );
    }

    return (
      <Accordion variant="bordered" selectionMode="multiple">
        {subjects.map((subject) => (
          <AccordionItem
            key={subject}
            title={
              <div className="flex items-center gap-3">
                <span className="text-xl">{libraryService.getSubjectEmoji(subject)}</span>
                <span className="font-medium">{subject}</span>
                <Badge color="primary" variant="flat" size="sm">
                  {documentsBySubject[subject]?.length || 0}
                </Badge>
              </div>
            }
          >
            <div className="grid gap-3">
              {(documentsBySubject[subject] || []).map((doc) => (
                <Card key={doc.id} className="hover:shadow-md transition-shadow">
                  <CardBody>
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="text-2xl">
                          {libraryService.getFileIcon(doc.type)}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">{doc.name}</h4>
                          <p className="text-sm text-gray-500 mt-1">{doc.topic}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Chip
                              size="sm"
                              variant="flat"
                              className={libraryService.getSubjectColor(subject)}
                            >
                              {subject}
                            </Chip>
                            <span className="text-xs text-gray-400">
                              {libraryService.formatDate(doc.upload_date)}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500">{doc.size}</div>
                        <div className="text-xs text-gray-400">{doc.type}</div>
                      </div>
                    </div>
                  </CardBody>
                </Card>
              ))}
            </div>
          </AccordionItem>
        ))}
      </Accordion>
    );
  };

  /**
   * Renderizar resultados de búsqueda
   */
  const renderSearchResults = () => {
    if (!searchResults) return null;

    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <MagnifyingGlassIcon className="h-5 w-5 text-primary" />
            <span className="font-medium">Resultados de búsqueda</span>
          </div>
        </CardHeader>
        <CardBody>
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Búsqueda: <span className="font-medium">"{searchResults.query}"</span>
              {searchResults.subject_filter && (
                <span> en <span className="font-medium">{searchResults.subject_filter}</span></span>
              )}
            </p>
          </div>
          
          <div className="prose prose-sm max-w-none">
            <div dangerouslySetInnerHTML={{ 
              __html: searchResults.formatted_results?.replace(/\n/g, '<br>') || searchResults.results 
            }} />
          </div>
        </CardBody>
      </Card>
    );
  };

  /**
   * Renderizar respuesta a pregunta
   */
  const renderAnswer = () => {
    if (!questionAnswer) return null;

    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <ChatBubbleLeftRightIcon className="h-5 w-5 text-primary" />
            <span className="font-medium">Respuesta de la biblioteca</span>
          </div>
        </CardHeader>
        <CardBody>
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Pregunta: <span className="font-medium">"{questionAnswer.question}"</span>
              {questionAnswer.subject && (
                <span> sobre <span className="font-medium">{questionAnswer.subject}</span></span>
              )}
            </p>
          </div>
          
          <div className="prose prose-sm max-w-none">
            <div dangerouslySetInnerHTML={{ 
              __html: questionAnswer.formatted_answer?.replace(/\n/g, '<br>') || questionAnswer.answer 
            }} />
          </div>
        </CardBody>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
            <BookOpenIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Biblioteca Educativa</h2>
            <p className="text-gray-600">Gestiona y consulta tus documentos académicos</p>
          </div>
        </div>
        
        <Button
          color="primary"
          startContent={<DocumentPlusIcon className="h-4 w-4" />}
          onPress={() => setSelectedTab('upload')}
          isLoading={uploading}
        >
          Subir Documento
        </Button>
      </div>

      {/* Estadísticas */}
      {renderStats()}

      {/* Error */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardBody>
            <div className="flex items-center justify-between">
              <p className="text-red-600">{error}</p>
              <Button size="sm" variant="light" onPress={clearError}>
                Cerrar
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Tabs principales */}
      <Tabs
        selectedKey={selectedTab}
        onSelectionChange={(key) => setSelectedTab(key as string)}
        variant="bordered"
        classNames={{
          tabList: "gap-6 w-full relative rounded-none p-0 border-b border-divider",
          cursor: "w-full bg-primary",
          tab: "max-w-fit px-0 h-12",
          tabContent: "group-data-[selected=true]:text-primary"
        }}
      >
        <Tab
          key="browse"
          title={
            <div className="flex items-center gap-2">
              <FolderIcon className="h-4 w-4" />
              <span>Explorar</span>
            </div>
          }
        >
          <div className="mt-6">
            {loading ? (
              <div className="flex justify-center py-8">
                <Spinner size="lg" />
              </div>
            ) : (
              renderDocuments()
            )}
          </div>
        </Tab>

        <Tab
          key="search"
          title={
            <div className="flex items-center gap-2">
              <MagnifyingGlassIcon className="h-4 w-4" />
              <span>Buscar</span>
            </div>
          }
        >
          <div className="mt-6 space-y-6">
            <Card>
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
                      isLoading={searching}
                      isDisabled={!searchQuery.trim()}
                    >
                      Buscar
                    </Button>
                    {searchResults && (
                      <Button
                        variant="flat"
                        onPress={clearResults}
                      >
                        Limpiar
                      </Button>
                    )}
                  </div>
                </div>
              </CardBody>
            </Card>

            {searching && (
              <div className="flex justify-center py-8">
                <Spinner size="lg" />
              </div>
            )}

            {renderSearchResults()}
          </div>
        </Tab>

        <Tab
          key="ask"
          title={
            <div className="flex items-center gap-2">
              <QuestionMarkCircleIcon className="h-4 w-4" />
              <span>Preguntar</span>
            </div>
          }
        >
          <div className="mt-6 space-y-6">
            <Card>
              <CardBody>
                <div className="space-y-4">
                  <Textarea
                    placeholder="Haz una pregunta sobre tus documentos..."
                    value={question}
                    onValueChange={setQuestion}
                    minRows={3}
                    maxRows={6}
                  />
                  
                  <Select
                    placeholder="Asignatura (opcional)"
                    value={questionSubject}
                    onChange={(e) => setQuestionSubject(e.target.value)}
                  >
                    {SUBJECTS.map((subject) => (
                      <SelectItem key={subject} value={subject}>
                        {libraryService.getSubjectEmoji(subject)} {subject}
                      </SelectItem>
                    ))}
                  </Select>
                  
                  <div className="flex gap-2">
                    <Button
                      color="primary"
                      onPress={handleQuestion}
                      isLoading={asking}
                      isDisabled={!question.trim()}
                      startContent={<ChatBubbleLeftRightIcon className="h-4 w-4" />}
                    >
                      Preguntar
                    </Button>
                    {questionAnswer && (
                      <Button
                        variant="flat"
                        onPress={clearResults}
                      >
                        Limpiar
                      </Button>
                    )}
                  </div>
                </div>
              </CardBody>
            </Card>

            {asking && (
              <div className="flex justify-center py-8">
                <Spinner size="lg" />
              </div>
            )}

            {renderAnswer()}
          </div>
        </Tab>

        <Tab
          key="upload"
          title={
            <div className="flex items-center gap-2">
              <CloudArrowUpIcon className="h-4 w-4" />
              <span>Subir</span>
            </div>
          }
        >
          <div className="mt-6">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CloudArrowUpIcon className="h-5 w-5 text-primary" />
                  <span className="text-lg font-semibold">Subir Documento</span>
                </div>
              </CardHeader>
              <CardBody>
                <Tabs
                  variant="bordered"
                  classNames={{
                    tabList: "gap-6 w-full",
                    cursor: "w-full bg-primary",
                    tab: "max-w-fit px-4 h-10"
                  }}
                >
                  <Tab
                    key="text"
                    title={
                      <div className="flex items-center gap-2">
                        <DocumentTextIcon className="h-4 w-4" />
                        <span>Texto</span>
                      </div>
                    }
                  >
                    <div className="space-y-4 mt-4">
                      <Input
                        label="Nombre del documento"
                        placeholder="Ej: Álgebra Lineal - Capítulo 1"
                        value={uploadForm.name}
                        onValueChange={(value) => setUploadForm(prev => ({ ...prev, name: value }))}
                        isRequired
                      />
                      
                      <div className="grid md:grid-cols-2 gap-4">
                        <Select
                          label="Asignatura"
                          placeholder="Selecciona una asignatura"
                          value={uploadForm.subject}
                          onChange={(e) => setUploadForm(prev => ({ ...prev, subject: e.target.value }))}
                          isRequired
                        >
                          {SUBJECTS.map((subject) => (
                            <SelectItem key={subject} value={subject}>
                              {libraryService.getSubjectEmoji(subject)} {subject}
                            </SelectItem>
                          ))}
                        </Select>
                        
                        <Input
                          label="Tema específico"
                          placeholder="Ej: Vectores y matrices"
                          value={uploadForm.topic}
                          onValueChange={(value) => setUploadForm(prev => ({ ...prev, topic: value }))}
                        />
                      </div>
                      
                      <Textarea
                        label="Contenido del documento"
                        placeholder="Pega o escribe el contenido del documento..."
                        value={uploadForm.content}
                        onValueChange={(value) => setUploadForm(prev => ({ ...prev, content: value }))}
                        minRows={6}
                        maxRows={12}
                        isRequired
                      />
                      
                      <Button
                        color="primary"
                        onPress={handleUpload}
                        isLoading={uploading}
                        isDisabled={!uploadForm.name || !uploadForm.content || !uploadForm.subject}
                        startContent={<CloudArrowUpIcon className="h-4 w-4" />}
                        size="lg"
                        className="w-full"
                      >
                        Subir Documento de Texto
                      </Button>
                    </div>
                  </Tab>

                  <Tab
                    key="file"
                    title={
                      <div className="flex items-center gap-2">
                        <DocumentTextIcon className="h-4 w-4" />
                        <span>Archivo</span>
                      </div>
                    }
                  >
                    <div className="space-y-4 mt-4">
                      <div className="grid md:grid-cols-2 gap-4">
                        <Select
                          label="Asignatura"
                          placeholder="Selecciona una asignatura"
                          value={uploadForm.subject}
                          onChange={(e) => setUploadForm(prev => ({ ...prev, subject: e.target.value }))}
                          isRequired
                        >
                          {SUBJECTS.map((subject) => (
                            <SelectItem key={subject} value={subject}>
                              {libraryService.getSubjectEmoji(subject)} {subject}
                            </SelectItem>
                          ))}
                        </Select>
                        
                        <Input
                          label="Tema específico"
                          placeholder="Ej: Vectores y matrices"
                          value={uploadForm.topic}
                          onValueChange={(value) => setUploadForm(prev => ({ ...prev, topic: value }))}
                        />
                      </div>
                      
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                        <div className="space-y-4">
                          <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto" />
                          <div>
                            <p className="text-lg font-medium text-gray-900">
                              Selecciona un archivo
                            </p>
                            <p className="text-sm text-gray-500">
                              PDF, Word (.docx) o archivos de texto
                            </p>
                          </div>
                          
                          <input
                            type="file"
                            accept=".pdf,.docx,.txt"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) {
                                setUploadForm(prev => ({ 
                                  ...prev, 
                                  selectedFile: file,
                                  name: file.name.replace(/\.[^/.]+$/, "")
                                }));
                              }
                            }}
                            className="hidden"
                            id="file-upload"
                          />
                          
                          <label
                            htmlFor="file-upload"
                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary-dark cursor-pointer"
                          >
                            Seleccionar archivo
                          </label>
                          
                          {uploadForm.selectedFile && (
                            <div className="mt-4 p-3 bg-gray-100 rounded-md">
                              <p className="text-sm font-medium text-gray-900">
                                Archivo seleccionado: {uploadForm.selectedFile.name}
                              </p>
                              <p className="text-xs text-gray-500">
                                Tamaño: {(uploadForm.selectedFile.size / 1024 / 1024).toFixed(2)} MB
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <Button
                        color="primary"
                        onPress={async () => {
                          if (uploadForm.selectedFile && uploadForm.subject) {
                            setFileUploading(true);
                            try {
                              await libraryService.uploadFile(uploadForm.selectedFile, {
                                subject: uploadForm.subject,
                                topic: uploadForm.topic
                              });
                              
                              // Limpiar formulario
                              setUploadForm({
                                name: '',
                                content: '',
                                subject: '',
                                topic: '',
                                file_type: 'text',
                                selectedFile: null
                              });
                              
                              // Limpiar input file
                              const fileInput = document.getElementById('file-upload') as HTMLInputElement;
                              if (fileInput) {
                                fileInput.value = '';
                              }
                              
                              // Recargar documentos
                              await loadDocuments();
                              
                              alert('¡Archivo subido exitosamente!');
                            } catch (error) {
                              console.error('Error uploading file:', error);
                              alert('Error al subir el archivo');
                            } finally {
                              setFileUploading(false);
                            }
                          }
                        }}
                        isLoading={fileUploading}
                        isDisabled={!uploadForm.selectedFile || !uploadForm.subject}
                        startContent={<CloudArrowUpIcon className="h-4 w-4" />}
                        size="lg"
                        className="w-full"
                      >
                        Subir Archivo
                      </Button>
                    </div>
                  </Tab>
                </Tabs>
              </CardBody>
            </Card>
          </div>
        </Tab>
      </Tabs>
    </div>
  );
}
