/**
 * Estadísticas de la Biblioteca Educativa
 * Muestra métricas y actividad reciente
 */

'use client';

import React from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Progress,
  Chip,
  Button
} from '@nextui-org/react';
import {
  BookOpenIcon,
  DocumentTextIcon,
  ClockIcon,
  ChartBarIcon,
  EyeIcon,
  HeartIcon
} from '@heroicons/react/24/outline';
import type { LibraryStats } from '@/lib/libraryService';

interface LibraryStatsProps {
  stats: LibraryStats | null;
  loading?: boolean;
}

export default function LibraryStats({ stats, loading = false }: LibraryStatsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardBody className="text-center">
              <div className="h-8 bg-gray-200 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
            </CardBody>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <Card>
        <CardBody className="text-center py-8">
          <BookOpenIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No hay estadísticas disponibles</p>
        </CardBody>
      </Card>
    );
  }

  // Validaciones defensivas para evitar errores
  const documentsBySubject = stats?.documents_by_subject || {};
  const documentsByType = stats?.documents_by_type || {};
  const recentUploads = stats?.recent_uploads || [];
  const usageStats = stats?.usage_stats || {};
  const popularSearches = stats?.popular_searches || [];
  const popularTags = stats?.popular_tags || [];
  const totalStorage = stats?.total_storage_used || (stats as any)?.total_storage || '0 MB';

  const subjectEntries = Object.entries(documentsBySubject);
  const topSubjects = subjectEntries
    .sort(([,a], [,b]) => (b as number) - (a as number))
    .slice(0, 3);

  return (
    <div className="space-y-6">
      {/* Métricas principales */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-2">
              <DocumentTextIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="text-2xl font-bold text-blue-700">{stats?.total_documents || 0}</div>
            <div className="text-sm text-blue-600">Documentos</div>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-2">
              <BookOpenIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="text-2xl font-bold text-green-700">{subjectEntries.length}</div>
            <div className="text-sm text-green-600">Asignaturas</div>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-2">
              <ChartBarIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div className="text-2xl font-bold text-purple-700">{totalStorage}</div>
            <div className="text-sm text-purple-600">Almacenado</div>
          </CardBody>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardBody className="text-center">
            <div className="flex items-center justify-center mb-2">
              <ClockIcon className="h-6 w-6 text-orange-600" />
            </div>
            <div className="text-2xl font-bold text-orange-700">{recentUploads.length}</div>
            <div className="text-sm text-orange-600">Recientes</div>
          </CardBody>
        </Card>
      </div>

      {/* Asignaturas más populares */}
      {topSubjects.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <HeartIcon className="h-5 w-5 text-primary" />
              <span className="font-semibold">Asignaturas más populares</span>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {topSubjects.map(([subject, count], index) => {
                const percentage = (count / (stats?.total_documents || 1)) * 100;
                const colors = ['primary', 'secondary', 'success'] as const;
                
                return (
                  <div key={subject} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{subject}</span>
                        <Chip size="sm" variant="flat" color={colors[index] || 'default'}>
                          {count} docs
                        </Chip>
                      </div>
                      <span className="text-sm text-gray-500">{percentage.toFixed(1)}%</span>
                    </div>
                    <Progress
                      value={percentage}
                      color={colors[index] || 'default'}
                      size="sm"
                      className="max-w-full"
                    />
                  </div>
                );
              })}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Actividad reciente */}
      {recentUploads.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <ClockIcon className="h-5 w-5 text-primary" />
              <span className="font-semibold">Actividad reciente</span>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {recentUploads.map((upload, index) => (
                <div key={index} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-sm">{(upload as any).name || upload.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Chip size="sm" variant="flat" color="primary">
                        {upload.subject}
                      </Chip>
                      <span className="text-xs text-gray-500">
                        {new Date(upload.date).toLocaleDateString('es-ES', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="light"
                    startContent={<EyeIcon className="h-3 w-3" />}
                  >
                    Ver
                  </Button>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Búsquedas populares */}
      {popularSearches.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <ChartBarIcon className="h-5 w-5 text-primary" />
              <span className="font-semibold">Búsquedas populares</span>
            </div>
          </CardHeader>
          <CardBody>
            <div className="flex flex-wrap gap-2">
              {popularSearches.map((search, index) => (
                <Chip
                  key={index}
                  variant="flat"
                  color="secondary"
                  size="sm"
                  className="cursor-pointer hover:opacity-80"
                >
                  {search}
                </Chip>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
