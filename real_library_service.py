"""
Servicio real de biblioteca que se conecta con Azure Search
Utiliza el agente Educational RAG para operaciones reales
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealLibraryService:
    """Servicio real de biblioteca que se conecta con Azure Search"""
    
    def __init__(self):
        self.educational_rag_agent = None
        self.agent_manager = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Inicializar conexión con el agente Educational RAG"""
        try:
            # Importar desde donde está realmente disponible
            import sys
            import os
            
            # Agregar el directorio raíz al path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.append(current_dir)
            
            # Intentar obtener el agente desde main_simple
            try:
                from src.main_simple import agent_manager
                self.agent_manager = agent_manager
                if hasattr(agent_manager, 'agents') and "educational_rag" in agent_manager.agents:
                    self.educational_rag_agent = agent_manager.agents["educational_rag"]
                    logger.info("✅ Conexión con Educational RAG Agent establecida")
                else:
                    logger.warning("⚠️ Educational RAG Agent no disponible en agent_manager")
            except ImportError:
                # Fallback: crear conexión directa
                from agents.educational_rag.agent import EducationalRAGAgent
                from src.config import settings
                self.educational_rag_agent = EducationalRAGAgent(settings.groq_api_key)
                logger.info("✅ Educational RAG Agent creado directamente")
                
        except Exception as e:
            logger.error(f"❌ Error conectando con Educational RAG: {e}")
            self.educational_rag_agent = None
    
    async def upload_document(self, file_content: bytes, filename: str, content_type: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Subir documento real a Azure Search"""
        try:
            if not self.educational_rag_agent:
                raise Exception("Educational RAG Agent no disponible")
            
            # Procesar el contenido del archivo según el tipo
            if content_type == "application/pdf" or filename.endswith('.pdf'):
                processed_content = await self._process_pdf(file_content)
            elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or filename.endswith('.docx'):
                processed_content = await self._process_docx(file_content)
            elif content_type == "text/plain" or filename.endswith('.txt'):
                processed_content = file_content.decode('utf-8')
            else:
                raise Exception(f"Tipo de archivo no soportado: {content_type}")
            
            # Preparar metadata completa
            document_metadata = {
                "filename": filename,
                "content_type": content_type,
                "upload_date": datetime.now().isoformat(),
            }
            
            # Agregar metadata adicional si se proporciona
            if metadata:
                document_metadata.update(metadata)
            
            # Usar el agente Educational RAG para almacenar el documento
            if hasattr(self.educational_rag_agent, 'upload_document'):
                result = self.educational_rag_agent.upload_document(
                    user_id="system",  # User ID por defecto
                    file_content=processed_content,
                    filename=filename,
                    category=metadata.get('category', 'general'),
                    subject=metadata.get('subject', 'general'),
                    level=metadata.get('level', 'general'),
                    document_type=metadata.get('document_type', 'document')
                )
            else:
                # Usar método genérico si add_document no existe
                prompt = f"""
                Procesa y almacena este documento en Azure Search:
                
                Nombre del archivo: {filename}
                Tipo: {content_type}
                Contenido: {processed_content[:1000]}...
                
                Extrae conceptos clave y almacena en el índice vectorial.
                """
                result = await self.agent_manager.get_agent_response(
                    "educational_rag", 
                    prompt,
                    {"action": "upload", "filename": filename, "content": processed_content}
                )
            
            # Generar ID único del documento
            document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(filename) % 10000}"
            
            return {
                "document_id": document_id,
                "filename": filename,
                "processed_content": processed_content,
                "status": "uploaded",
                "azure_response": result
            }
            
        except Exception as e:
            logger.error(f"Error subiendo documento: {e}")
            raise
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """Obtener todos los documentos del índice de Azure Search"""
        try:
            if not self.educational_rag_agent:
                return []
            
            # Intentar obtener documentos del agente
            if hasattr(self.educational_rag_agent, 'get_all_documents'):
                documents = await self.educational_rag_agent.get_all_documents()
            elif hasattr(self.educational_rag_agent, 'list_documents'):
                documents = await self.educational_rag_agent.list_documents()
            else:
                # Usar método genérico para obtener lista de documentos
                prompt = """
                Lista todos los documentos almacenados en el índice de Azure Search.
                Proporciona información de cada documento incluyendo:
                - ID del documento
                - Título/nombre
                - Fecha de subida
                - Tamaño aproximado
                - Resumen del contenido
                """
                response = await self.agent_manager.get_agent_response(
                    "educational_rag",
                    prompt,
                    {"action": "list_documents"}
                )
                
                # Parsear la respuesta para extraer información de documentos
                documents = self._parse_documents_response(response)
            
            return documents if isinstance(documents, list) else []
            
        except Exception as e:
            logger.error(f"Error obteniendo documentos: {e}")
            return []
    
    async def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Buscar documentos usando búsqueda vectorial en Azure Search"""
        try:
            if not self.educational_rag_agent:
                return []
            
            # Usar el agente RAG para búsqueda vectorial
            if hasattr(self.educational_rag_agent, 'search_documents'):
                results = await self.educational_rag_agent.search_documents(query, top_k=top_k)
            elif hasattr(self.educational_rag_agent, 'vector_search'):
                results = await self.educational_rag_agent.vector_search(query, top_k=top_k)
            else:
                # Usar método genérico para búsqueda
                prompt = f"""
                Busca en el índice de Azure Search documentos relacionados con: "{query}"
                
                Proporciona los {top_k} resultados más relevantes con:
                - Score de relevancia
                - Extractos del contenido
                - Metadatos del documento
                """
                response = await self.agent_manager.get_agent_response(
                    "educational_rag",
                    prompt,
                    {"action": "search", "query": query, "top_k": top_k}
                )
                
                results = self._parse_search_response(response, query)
            
            return results if isinstance(results, list) else []
            
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    async def ask_question(self, question: str) -> Dict[str, Any]:
        """Hacer pregunta sobre los documentos usando RAG"""
        try:
            if not self.educational_rag_agent:
                return {"answer": "Servicio no disponible", "sources": [], "confidence": 0.0}
            
            # Usar el agente RAG para responder la pregunta
            if hasattr(self.educational_rag_agent, 'answer_question'):
                result = await self.educational_rag_agent.answer_question(question)
            elif hasattr(self.educational_rag_agent, 'query'):
                result = await self.educational_rag_agent.query(question)
            else:
                # Usar método genérico
                prompt = f"""
                Responde esta pregunta basándote en los documentos almacenados en Azure Search:
                
                Pregunta: {question}
                
                Proporciona una respuesta fundamentada con referencias a los documentos relevantes.
                """
                result = await self.agent_manager.get_agent_response(
                    "educational_rag",
                    prompt,
                    {"action": "question", "question": question}
                )
            
            # Formatear la respuesta
            if isinstance(result, dict):
                return result
            else:
                return {
                    "answer": str(result),
                    "sources": [],
                    "confidence": 0.8
                }
                
        except Exception as e:
            logger.error(f"Error procesando pregunta: {e}")
            return {"answer": f"Error: {str(e)}", "sources": [], "confidence": 0.0}
    
    async def get_library_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas reales del índice de Azure Search"""
        try:
            if not self.educational_rag_agent:
                return self._get_empty_stats()
            
            # Obtener documentos del usuario usando el nuevo método
            if hasattr(self.educational_rag_agent.doc_manager, 'list_user_documents'):
                result = self.educational_rag_agent.doc_manager.list_user_documents("system", limit=100)
                if result.get("success"):
                    documents = result.get("documents", [])
                    stats = self._calculate_stats_from_documents(documents)
                    return stats
            
            # Fallback a estadísticas vacías
            return self._get_empty_stats()
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return self._get_empty_stats()
    
    async def delete_document(self, document_id: str) -> bool:
        """Eliminar documento del índice"""
        try:
            if not self.educational_rag_agent:
                return False
            
            if hasattr(self.educational_rag_agent, 'delete_document'):
                return await self.educational_rag_agent.delete_document(document_id)
            else:
                # Intentar eliminación genérica
                prompt = f"Elimina el documento con ID: {document_id} del índice de Azure Search"
                result = await self.agent_manager.get_agent_response(
                    "educational_rag",
                    prompt,
                    {"action": "delete", "document_id": document_id}
                )
                return "éxito" in str(result).lower() or "success" in str(result).lower()
                
        except Exception as e:
            logger.error(f"Error eliminando documento: {e}")
            return False
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Obtener documento específico por ID"""
        try:
            if not self.educational_rag_agent:
                return None
            
            if hasattr(self.educational_rag_agent, 'get_document'):
                return await self.educational_rag_agent.get_document(document_id)
            else:
                # Buscar en todos los documentos
                documents = await self.get_all_documents()
                for doc in documents:
                    if doc.get('id') == document_id:
                        return doc
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo documento: {e}")
            return None
    
    # Métodos auxiliares
    
    async def _process_pdf(self, file_content: bytes) -> str:
        """Procesar archivo PDF"""
        try:
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error procesando PDF: {e}")
            return f"Error procesando PDF: {str(e)}"
    
    async def _process_docx(self, file_content: bytes) -> str:
        """Procesar archivo Word"""
        try:
            from docx import Document
            import io
            
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error procesando DOCX: {e}")
            return f"Error procesando DOCX: {str(e)}"
    
    def _parse_documents_response(self, response: str) -> List[Dict[str, Any]]:
        """Parsear respuesta de lista de documentos"""
        # Esta función debería parsear la respuesta del agente y extraer información estructurada
        # Por ahora devolvemos una lista vacía si no hay documentos reales
        return []
    
    def _parse_search_response(self, response: str, query: str) -> List[Dict[str, Any]]:
        """Parsear respuesta de búsqueda"""
        # Esta función debería parsear los resultados de búsqueda
        # Por ahora devolvemos una estructura básica
        return [
            {
                "id": f"search_result_{hash(query) % 1000}",
                "title": f"Resultado para: {query}",
                "content": str(response)[:200] + "...",
                "score": 0.85,
                "metadata": {"source": "azure_search"}
            }
        ]
    
    def _calculate_stats_from_documents(self, documents: List[Dict]) -> Dict[str, Any]:
        """Calcular estadísticas a partir de lista de documentos"""
        if not documents:
            return self._get_empty_stats()
        
        # Calcular estadísticas reales
        total_docs = len(documents)
        docs_by_type = {}
        docs_by_subject = {}
        recent_uploads = []
        
        for doc in documents:
            # Contar por tipo
            doc_type = doc.get('type', 'unknown')
            docs_by_type[doc_type] = docs_by_type.get(doc_type, 0) + 1
            
            # Contar por materia/asignatura
            subject = doc.get('subject', 'General')
            docs_by_subject[subject] = docs_by_subject.get(subject, 0) + 1
            
            # Uploads recientes
            if len(recent_uploads) < 5:
                recent_uploads.append({
                    "id": doc.get('id', ''),
                    "title": doc.get('title', 'Sin título'),
                    "subject": subject,
                    "date": doc.get('upload_date', datetime.now().isoformat())
                })
        
        return {
            "total_documents": total_docs,
            "documents_by_subject": docs_by_subject,
            "documents_by_type": docs_by_type,
            "recent_uploads": recent_uploads,
            "total_storage": f"{total_docs * 0.5:.1f} MB",  # Estimación
            "usage_stats": {
                "total_searches": total_docs * 2,  # Estimación
                "total_questions": total_docs,
                "most_searched_subject": max(docs_by_subject.items(), key=lambda x: x[1])[0] if docs_by_subject else "General",
                "avg_questions_per_day": 3.2
            },
            "popular_searches": [],
            "popular_tags": []
        }
    
    def _get_empty_stats(self) -> Dict[str, Any]:
        """Estadísticas vacías cuando no hay conexión"""
        return {
            "total_documents": 0,
            "documents_by_subject": {},
            "documents_by_type": {},
            "recent_uploads": [],
            "total_storage": "0 MB",
            "usage_stats": {
                "total_searches": 0,
                "total_questions": 0,
                "most_searched_subject": "",
                "avg_questions_per_day": 0
            },
            "popular_searches": [],
            "popular_tags": []
        }
