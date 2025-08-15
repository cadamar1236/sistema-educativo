'use client';

import React, { useState, useCallback, useRef } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Button,
  Input,
  Progress,
  Chip,
  Divider,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure,
  Tabs,
  Tab,
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
  Badge,
  Tooltip,
  ScrollShadow,
  Spacer
} from '@nextui-org/react';
import { 
  Upload, 
  FileText, 
  Image, 
  Video, 
  Music, 
  Archive,
  Link,
  X,
  CheckCircle,
  AlertCircle,
  Download,
  Eye,
  Trash2,
  Filter,
  Search,
  Grid,
  List,
  FolderOpen,
  Globe
} from 'lucide-react';
import { useEnhancedLibrary } from '../../hooks/useEnhancedLibrary';
import axios from 'axios';

// File type categories with icons and colors
const FILE_CATEGORIES = {
  documents: {
    icon: FileText,
    color: 'primary',
    extensions: ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'],
    label: 'Documents'
  },
  spreadsheets: {
    icon: Grid,
    color: 'success',
    extensions: ['xls', 'xlsx', 'csv', 'ods'],
    label: 'Spreadsheets'
  },
  presentations: {
    icon: FileText,
    color: 'warning',
    extensions: ['ppt', 'pptx', 'odp'],
    label: 'Presentations'
  },
  images: {
    icon: Image,
    color: 'secondary',
    extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'tiff'],
    label: 'Images'
  },
  videos: {
    icon: Video,
    color: 'danger',
    extensions: ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'],
    label: 'Videos'
  },
  audio: {
    icon: Music,
    color: 'default',
    extensions: ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'],
    label: 'Audio'
  },
  archives: {
    icon: Archive,
    color: 'primary',
    extensions: ['zip', 'rar', '7z', 'tar', 'gz', 'bz2'],
    label: 'Archives'
  },
  code: {
    icon: FileText,
    color: 'success',
    extensions: ['py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'json', 'xml', 'yaml', 'yml'],
    label: 'Code'
  }
};

const getFileCategory = (fileName: string) => {
  const extension = fileName.split('.').pop()?.toLowerCase();
  for (const [category, config] of Object.entries(FILE_CATEGORIES)) {
    if (config.extensions.includes(extension || '')) {
      return { category, ...config };
    }
  }
  return { category: 'other', icon: FileText, color: 'default' as any, label: 'Other' };
};

export default function EnhancedLibrary() {
  const {
    documents,
    uploadProgress,
    isUploading,
    error,
    uploadDocument,
    uploadMultiple,
    deleteDocument,
    refreshDocuments,
    supportedFormats
  } = useEnhancedLibrary();

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [urlInput, setUrlInput] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTab, setSelectedTab] = useState('upload');
  const [ocrEnabled, setOcrEnabled] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedDocument, setSelectedDocument] = useState<any>(null);

  // Drag and drop handlers
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const files = Array.from(e.dataTransfer.files);
      setSelectedFiles(prev => [...prev, ...files]);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setSelectedFiles(prev => [...prev, ...files]);
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    if (selectedFiles.length === 1) {
      await uploadDocument(selectedFiles[0], { ocr_enabled: ocrEnabled });
    } else {
      await uploadMultiple(selectedFiles, { ocr_enabled: ocrEnabled });
    }
    
    setSelectedFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUrlUpload = async () => {
    if (!urlInput.trim()) return;
    
    try {
      const response = await axios.post('/api/library/upload/url', {
        url: urlInput,
        ocr_enabled: ocrEnabled
      });
      
      if (response.data.success) {
        setUrlInput('');
        refreshDocuments();
      }
    } catch (error) {
      console.error('URL upload error:', error);
    }
  };

  const removeSelectedFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         doc.content?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterCategory === 'all' || 
                         getFileCategory(doc.title).category === filterCategory;
    return matchesSearch && matchesFilter;
  });

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <Card className="bg-gradient-to-r from-blue-500/10 to-purple-500/10">
        <CardBody>
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">Enhanced Document Library</h2>
              <p className="text-sm text-gray-500 mt-1">
                Support for {supportedFormats.length}+ file types with OCR capabilities
              </p>
            </div>
            <div className="flex gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{documents.length}</p>
                <p className="text-xs text-gray-500">Total Documents</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">
                  {documents.reduce((acc, doc) => acc + (doc.size || 0), 0) / 1024 / 1024 | 0} MB
                </p>
                <p className="text-xs text-gray-500">Total Size</p>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Upload Interface */}
      <Card>
        <CardHeader>
          <Tabs 
            selectedKey={selectedTab}
            onSelectionChange={(key) => setSelectedTab(key as string)}
            className="w-full"
          >
            <Tab key="upload" title="File Upload">
              <div className="space-y-4 mt-4">
                {/* Drag & Drop Zone */}
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
                    dragActive 
                      ? 'border-primary bg-primary/10' 
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-lg font-medium">
                    {dragActive ? 'Drop files here' : 'Drag & drop files or click to browse'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Supports: Documents, Images, Spreadsheets, Presentations, and more
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    onChange={handleFileSelect}
                    className="hidden"
                    accept="*"
                  />
                </div>

                {/* Selected Files */}
                {selectedFiles.length > 0 && (
                  <div className="space-y-2">
                    <p className="font-medium">Selected Files ({selectedFiles.length})</p>
                    <ScrollShadow className="max-h-48">
                      {selectedFiles.map((file, index) => {
                        const category = getFileCategory(file.name);
                        const Icon = category.icon;
                        return (
                          <div key={index} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                            <div className="flex items-center gap-2">
                              <Icon className="h-4 w-4" />
                              <span className="text-sm">{file.name}</span>
                              <Chip size="sm" color={category.color} variant="flat">
                                {category.label}
                              </Chip>
                              <span className="text-xs text-gray-500">
                                {formatFileSize(file.size)}
                              </span>
                            </div>
                            <Button
                              isIconOnly
                              size="sm"
                              variant="light"
                              onPress={() => removeSelectedFile(index)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        );
                      })}
                    </ScrollShadow>
                  </div>
                )}

                {/* OCR Option */}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="ocr"
                    checked={ocrEnabled}
                    onChange={(e) => setOcrEnabled(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="ocr" className="text-sm">
                    Enable OCR for image files (extract text from images)
                  </label>
                </div>

                {/* Upload Progress */}
                {isUploading && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} color="primary" />
                  </div>
                )}

                {/* Upload Button */}
                <Button
                  color="primary"
                  onPress={handleUpload}
                  isDisabled={selectedFiles.length === 0 || isUploading}
                  className="w-full"
                  startContent={<Upload className="h-4 w-4" />}
                >
                  Upload {selectedFiles.length > 0 ? `${selectedFiles.length} File(s)` : 'Files'}
                </Button>
              </div>
            </Tab>

            <Tab key="url" title="URL Upload">
              <div className="space-y-4 mt-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter document URL (PDF, webpage, etc.)"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    startContent={<Globe className="h-4 w-4 text-gray-400" />}
                  />
                  <Button
                    color="primary"
                    onPress={handleUrlUpload}
                    isDisabled={!urlInput.trim() || isUploading}
                    startContent={<Download className="h-4 w-4" />}
                  >
                    Fetch
                  </Button>
                </div>
              </div>
            </Tab>
          </Tabs>
        </CardHeader>
      </Card>

      {/* Document Library */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center w-full">
            <h3 className="text-lg font-semibold">Document Library</h3>
            <div className="flex gap-2">
              {/* Search */}
              <Input
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                startContent={<Search className="h-4 w-4 text-gray-400" />}
                className="w-64"
                size="sm"
              />
              
              {/* Filter */}
              <Dropdown>
                <DropdownTrigger>
                  <Button variant="flat" size="sm" startContent={<Filter className="h-4 w-4" />}>
                    {filterCategory === 'all' ? 'All Types' : FILE_CATEGORIES[filterCategory as keyof typeof FILE_CATEGORIES]?.label}
                  </Button>
                </DropdownTrigger>
                <DropdownMenu
                  selectedKeys={[filterCategory]}
                  onSelectionChange={(keys) => setFilterCategory(Array.from(keys)[0] as string)}
                >
                  <DropdownItem key="all">All Types</DropdownItem>
                  {Object.entries(FILE_CATEGORIES).map(([key, config]) => (
                    <DropdownItem key={key} startContent={<config.icon className="h-4 w-4" />}>
                      {config.label}
                    </DropdownItem>
                  ))}
                </DropdownMenu>
              </Dropdown>

              {/* View Mode */}
              <div className="flex gap-1">
                <Button
                  isIconOnly
                  size="sm"
                  variant={viewMode === 'grid' ? 'solid' : 'light'}
                  onPress={() => setViewMode('grid')}
                >
                  <Grid className="h-4 w-4" />
                </Button>
                <Button
                  isIconOnly
                  size="sm"
                  variant={viewMode === 'list' ? 'solid' : 'light'}
                  onPress={() => setViewMode('list')}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardBody>
          {filteredDocuments.length === 0 ? (
            <div className="text-center py-12">
              <FolderOpen className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500">No documents found</p>
            </div>
          ) : (
            <div className={viewMode === 'grid' ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4' : 'space-y-2'}>
              {filteredDocuments.map((doc) => {
                const category = getFileCategory(doc.title);
                const Icon = category.icon;
                
                return viewMode === 'grid' ? (
                  <Card
                    key={doc.id}
                    isPressable
                    onPress={() => {
                      setSelectedDocument(doc);
                      onOpen();
                    }}
                    className="hover:shadow-lg transition-shadow"
                  >
                    <CardBody className="text-center p-4">
                      <Icon className="mx-auto h-8 w-8 mb-2" />
                      <p className="text-sm font-medium truncate">{doc.title}</p>
                      <Chip size="sm" color={category.color} variant="flat" className="mt-2">
                        {category.label}
                      </Chip>
                      {doc.ocr_enabled && (
                        <Badge content="OCR" color="success" size="sm" className="mt-1">
                          <div />
                        </Badge>
                      )}
                    </CardBody>
                  </Card>
                ) : (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer"
                    onClick={() => {
                      setSelectedDocument(doc);
                      onOpen();
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="h-5 w-5" />
                      <div>
                        <p className="font-medium">{doc.title}</p>
                        <div className="flex gap-2 mt-1">
                          <Chip size="sm" color={category.color} variant="flat">
                            {category.label}
                          </Chip>
                          {doc.size && (
                            <span className="text-xs text-gray-500">
                              {formatFileSize(doc.size)}
                            </span>
                          )}
                          {doc.ocr_enabled && (
                            <Chip size="sm" color="success" variant="flat">
                              OCR
                            </Chip>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Tooltip content="View">
                        <Button isIconOnly size="sm" variant="light">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Tooltip>
                      <Tooltip content="Delete">
                        <Button
                          isIconOnly
                          size="sm"
                          variant="light"
                          color="danger"
                          onPress={(e) => {
                            e.stopPropagation();
                            deleteDocument(doc.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </Tooltip>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Document Preview Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="3xl">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">
                {selectedDocument?.title}
              </ModalHeader>
              <ModalBody>
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <Chip color={getFileCategory(selectedDocument?.title || '').color} variant="flat">
                      {getFileCategory(selectedDocument?.title || '').label}
                    </Chip>
                    {selectedDocument?.ocr_enabled && (
                      <Chip color="success" variant="flat">
                        OCR Processed
                      </Chip>
                    )}
                    {selectedDocument?.size && (
                      <Chip variant="flat">
                        {formatFileSize(selectedDocument.size)}
                      </Chip>
                    )}
                  </div>
                  
                  {selectedDocument?.metadata && (
                    <div>
                      <p className="font-medium mb-2">Metadata</p>
                      <div className="bg-gray-50 rounded p-3">
                        <pre className="text-xs">{JSON.stringify(selectedDocument.metadata, null, 2)}</pre>
                      </div>
                    </div>
                  )}
                  
                  {selectedDocument?.content && (
                    <div>
                      <p className="font-medium mb-2">Content Preview</p>
                      <ScrollShadow className="h-64">
                        <div className="bg-gray-50 rounded p-3">
                          <p className="text-sm whitespace-pre-wrap">
                            {selectedDocument.content.substring(0, 1000)}
                            {selectedDocument.content.length > 1000 && '...'}
                          </p>
                        </div>
                      </ScrollShadow>
                    </div>
                  )}
                </div>
              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="light" onPress={() => {
                  deleteDocument(selectedDocument.id);
                  onClose();
                }}>
                  Delete
                </Button>
                <Button color="primary" onPress={onClose}>
                  Close
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      {/* Error Display */}
      {error && (
        <Card className="border-danger">
          <CardBody>
            <div className="flex items-center gap-2 text-danger">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}