"""
Wrapper unificado para el servicio de biblioteca
Maneja las diferencias entre las interfaces de los diferentes agentes
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LibraryServiceWrapper:
    """Wrapper que unifica las diferentes interfaces de biblioteca"""
    
    def __init__(self):
        self.educational_rag_agent = None
        self.enhanced_service = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Inicializar los servicios disponibles"""
        # Intentar cargar el agente RAG
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            from agents.educational_rag.agent import EducationalRAGAgent
            from src.config import settings
            
            if hasattr(settings, 'groq_api_key') and settings.groq_api_key:
                self.educational_rag_agent = EducationalRAGAgent(settings.groq_api_key)
                logger.info("✅ Educational RAG Agent inicializado")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo inicializar Educational RAG: {e}")
        
        # Intentar cargar el servicio mejorado
        try:
            from enhanced_library_service import enhanced_library_service
            self.enhanced_service = enhanced_library_service
            logger.info("✅ Servicio mejorado inicializado")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo inicializar servicio mejorado: {e}")
    
    async def upload_document(
        self, 
        file_content: bytes, 
        filename: str,
        content_type: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Método unificado para subir documentos
        Intenta usar el mejor servicio disponible
        """
        try:
            # Procesar el contenido según el tipo
            processed_content = await self._process_content(file_content, filename, content_type)
            
            # Preparar metadata
            if metadata is None:
                metadata = {}
            
            # Intentar con Educational RAG primero
            if self.educational_rag_agent and hasattr(self.educational_rag_agent, 'upload_document'):
                try:
                    logger.info(f"📤 Subiendo con Educational RAG: {filename}")
                    
                    # Educational RAG espera 'content' no 'file_content'
                    result = self.educational_rag_agent.upload_document(
                        user_id="system",
                        content=processed_content,  # content, no file_content
                        filename=filename,
                        category=metadata.get('category', 'general'),
                        subject=metadata.get('subject', 'general'),
                        level=metadata.get('level', 'general')
                    )
                    
                    # Agregar información adicional
                    if isinstance(result, dict):
                        result['service_used'] = 'educational_rag'
                        result['processed_content'] = processed_content[:500] if processed_content else ""
                        return result
                    else:
                        return {
                            'success': True,
                            'document_id': f"rag_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            'filename': filename,
                            'processed_content': processed_content[:500] if processed_content else "",
                            'service_used': 'educational_rag',
                            'result': result
                        }
                        
                except Exception as e:
                    logger.error(f"❌ Error con Educational RAG: {e}")
            
            # Intentar con servicio mejorado
            if self.enhanced_service:
                try:
                    logger.info(f"📤 Subiendo con servicio mejorado: {filename}")
                    
                    result = await self.enhanced_service.upload_document(
                        file_content=file_content,
                        filename=filename,
                        content_type=content_type,
                        metadata=metadata
                    )
                    
                    result['service_used'] = 'enhanced_service'
                    return result
                    
                except Exception as e:
                    logger.error(f"❌ Error con servicio mejorado: {e}")
            
            # Fallback: almacenamiento local simple
            logger.info(f"📤 Usando almacenamiento local para: {filename}")
            return await self._local_upload(file_content, filename, processed_content, metadata)
            
        except Exception as e:
            logger.error(f"❌ Error general subiendo documento: {e}")
            raise
    
    async def _process_content(self, file_content: bytes, filename: str, content_type: str = None) -> str:
        """Procesar el contenido del archivo para extraer texto"""
        try:
            # Para archivos de texto simples
            if filename.endswith(('.txt', '.md', '.csv')):
                return file_content.decode('utf-8', errors='ignore')
            
            # Para PDF
            if filename.endswith('.pdf'):
                try:
                    import PyPDF2
                    import io
                    
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text.strip()
                except:
                    return f"[PDF: {filename}] - Contenido no extraído"
            
            # Para Word
            if filename.endswith(('.doc', '.docx')):
                try:
                    from docx import Document
                    import io
                    
                    doc = Document(io.BytesIO(file_content))
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    return text.strip()
                except:
                    return f"[Word: {filename}] - Contenido no extraído"
            
            # Para otros tipos
            return f"[Archivo: {filename}] - Tipo: {content_type or 'desconocido'}"
            
        except Exception as e:
            logger.error(f"Error procesando contenido: {e}")
            return f"[Error procesando: {filename}]"
    
    async def _local_upload(
        self,
        file_content: bytes,
        filename: str,
        processed_content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Almacenamiento local como fallback"""
        try:
            # Crear directorio si no existe
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generar ID único
            document_id = f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(filename) % 10000}"
            
            # Guardar archivo
            file_path = os.path.join(upload_dir, f"{document_id}_{filename}")
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Guardar metadata
            meta_path = os.path.join(upload_dir, f"{document_id}_meta.json")
            with open(meta_path, 'w') as f:
                json.dump({
                    'document_id': document_id,
                    'filename': filename,
                    'upload_date': datetime.now().isoformat(),
                    'size': len(file_content),
                    'metadata': metadata
                }, f, indent=2)
            
            return {
                'success': True,
                'document_id': document_id,
                'filename': filename,
                'processed_content': processed_content[:500] if processed_content else "",
                'file_path': file_path,
                'service_used': 'local_storage',
                'status': 'uploaded',
                'message': 'Archivo guardado localmente'
            }
            
        except Exception as e:
            logger.error(f"Error en almacenamiento local: {e}")
            raise
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """Obtener todos los documentos"""
        documents = []
        
        # Intentar obtener de Educational RAG
        if self.educational_rag_agent:
            try:
                if hasattr(self.educational_rag_agent, 'list_documents'):
                    rag_docs = self.educational_rag_agent.list_documents("system")
                    if rag_docs:
                        documents.extend(rag_docs)
            except Exception as e:
                logger.error(f"Error obteniendo documentos RAG: {e}")
        
        # Obtener documentos locales
        try:
            upload_dir = "uploads"
            if os.path.exists(upload_dir):
                for file in os.listdir(upload_dir):
                    if file.endswith("_meta.json"):
                        with open(os.path.join(upload_dir, file), 'r') as f:
                            meta = json.load(f)
                            documents.append(meta)
        except Exception as e:
            logger.error(f"Error obteniendo documentos locales: {e}")
        
        return documents
    
    async def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Buscar documentos"""
        results = []
        
        # Intentar buscar con Educational RAG
        if self.educational_rag_agent:
            try:
                if hasattr(self.educational_rag_agent, 'search_documents'):
                    rag_results = self.educational_rag_agent.search_documents(
                        user_id="system",
                        query=query,
                        top_k=top_k
                    )
                    if rag_results:
                        results.extend(rag_results)
            except Exception as e:
                logger.error(f"Error buscando con RAG: {e}")
        
        return results

# Instancia global
library_service_wrapper = LibraryServiceWrapper()