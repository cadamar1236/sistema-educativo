"""
Endpoints mejorados para la API de biblioteca con soporte ampliado de archivos
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import os
from datetime import datetime

# Importar el servicio mejorado
from enhanced_library_service import enhanced_library_service

async def upload_document_enhanced(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    grade_level: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    ocr_enabled: bool = Form(False),
    extract_text: bool = Form(True)
):
    """
    Endpoint mejorado para subir documentos con soporte ampliado
    Soporta: PDF, Word, PowerPoint, Excel, Imágenes, CSV, JSON, etc.
    """
    try:
        # Leer contenido del archivo
        content = await file.read()
        file_size = len(content)
        
        # Validar tamaño (máximo 100MB)
        max_size = 100 * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo muy grande: {file_size / 1024 / 1024:.2f}MB (máximo: 100MB)"
            )
        
        # Preparar metadata
        metadata = {
            'subject': subject,
            'topic': topic,
            'grade_level': grade_level,
            'upload_source': 'api_enhanced'
        }
        
        # Procesar tags
        if tags:
            metadata['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Usar el servicio mejorado
        result = await enhanced_library_service.upload_document(
            file_content=content,
            filename=file.filename,
            content_type=file.content_type,
            metadata=metadata,
            extract_text=extract_text,
            ocr_enabled=ocr_enabled
        )
        
        # Preparar respuesta
        return {
            "success": True,
            "message": f"Documento '{file.filename}' subido exitosamente",
            "document_id": result.get("document_id"),
            "filename": file.filename,
            "file_size": f"{file_size / 1024:.2f} KB" if file_size < 1024 * 1024 else f"{file_size / 1024 / 1024:.2f} MB",
            "content_type": file.content_type,
            "metadata": metadata,
            "processing": {
                "text_extracted": bool(result.get("processed_content")),
                "ocr_used": metadata.get("ocr_used", False),
                "enhanced_processing": result.get("enhanced_processing", False)
            },
            "preview": result.get("processed_content", "")[:500] if result.get("processed_content") else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")


async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    subject: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    grade_level: Optional[str] = Form(None),
    ocr_enabled: bool = Form(False)
):
    """Endpoint para subir múltiples documentos de una vez"""
    try:
        results = []
        errors = []
        
        # Metadata común
        common_metadata = {
            'subject': subject,
            'topic': topic,
            'grade_level': grade_level,
            'batch_upload': True,
            'batch_timestamp': datetime.now().isoformat()
        }
        
        # Procesar cada archivo
        for file in files:
            try:
                content = await file.read()
                
                result = await enhanced_library_service.upload_document(
                    file_content=content,
                    filename=file.filename,
                    content_type=file.content_type,
                    metadata=common_metadata,
                    ocr_enabled=ocr_enabled
                )
                
                results.append({
                    "filename": file.filename,
                    "document_id": result.get("document_id"),
                    "status": "success",
                    "size": len(content)
                })
                
            except Exception as e:
                errors.append({
                    "filename": file.filename,
                    "error": str(e),
                    "status": "failed"
                })
        
        return {
            "success": len(errors) == 0,
            "message": f"Procesados {len(results)} de {len(files)} archivos",
            "successful_uploads": results,
            "failed_uploads": errors,
            "summary": {
                "total_files": len(files),
                "successful": len(results),
                "failed": len(errors)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en carga múltiple: {str(e)}")


async def get_supported_formats():
    """Endpoint para obtener información sobre formatos soportados"""
    try:
        formats = await enhanced_library_service.get_supported_formats()
        
        return {
            "success": True,
            "formats": formats,
            "message": "Formatos de archivo soportados por el sistema",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo formatos: {str(e)}")


def register_enhanced_endpoints(app: FastAPI):
    """Función para registrar los endpoints mejorados en la aplicación FastAPI"""
    
    # Endpoints de carga
    app.post("/api/library/upload/enhanced")(upload_document_enhanced)
    app.post("/api/library/upload/multiple")(upload_multiple_documents)
    
    # Endpoints de información
    app.get("/api/library/formats")(get_supported_formats)
    
    print("✅ Endpoints mejorados de biblioteca registrados")