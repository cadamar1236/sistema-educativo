"""
Educational RAG Agent con fallback local para Azure Search
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

try:
    from azure_search_config import get_search_client, local_search
    SEARCH_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Azure Search config no disponible")
    SEARCH_AVAILABLE = False

class EducationalRAGAgentFixed:
    """Agente RAG educativo con manejo robusto de errores"""
    
    def __init__(self, groq_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.search_client = None
        self.use_local = True  # Por defecto usar local
        
        # Intentar configurar búsqueda
        if SEARCH_AVAILABLE:
            try:
                self.search_client = get_search_client()
                # Si el cliente es el local_search, estamos en modo local
                if hasattr(self.search_client, 'upload_document'):
                    self.use_local = True
                    logger.info("📁 Usando almacenamiento local para documentos")
                else:
                    self.use_local = False
                    logger.info("☁️ Usando Azure Search para documentos")
            except Exception as e:
                logger.error(f"Error inicializando búsqueda: {e}")
                self.search_client = local_search if SEARCH_AVAILABLE else None
                self.use_local = True
        
        logger.info(f"✅ Educational RAG Agent inicializado (modo: {'local' if self.use_local else 'Azure'})")
    
    def upload_document(
        self,
        user_id: str,
        content: str,  # Nota: ahora usa 'content', no 'file_content'
        filename: str,
        category: str = "general",
        subject: str = "general",
        level: str = "general"
    ) -> Dict[str, Any]:
        """Subir documento al sistema"""
        try:
            # Preparar documento
            document = {
                "user_id": user_id,
                "filename": filename,
                "content": content[:10000] if content else "",  # Limitar tamaño
                "category": category,
                "subject": subject,
                "level": level,
                "upload_date": datetime.now().isoformat(),
                "doc_id": hashlib.md5(f"{filename}{datetime.now()}".encode()).hexdigest()[:12]
            }
            
            if self.use_local:
                # Usar almacenamiento local
                if self.search_client and hasattr(self.search_client, 'upload_document'):
                    result = self.search_client.upload_document(document)
                    return {
                        "success": result.get('success', True),
                        "document_id": result.get('document_id', document['doc_id']),
                        "message": "Documento guardado localmente",
                        "storage": "local"
                    }
                else:
                    # Fallback: guardar en archivo
                    self._save_to_file(document)
                    return {
                        "success": True,
                        "document_id": document['doc_id'],
                        "message": "Documento guardado en archivo local",
                        "storage": "file"
                    }
            else:
                # Intentar Azure Search
                try:
                    self.search_client.upload_documents([document])
                    return {
                        "success": True,
                        "document_id": document['doc_id'],
                        "message": "Documento subido a Azure Search",
                        "storage": "azure"
                    }
                except Exception as e:
                    logger.error(f"Error con Azure, usando fallback local: {e}")
                    # Fallback a local
                    self._save_to_file(document)
                    return {
                        "success": True,
                        "document_id": document['doc_id'],
                        "message": "Documento guardado localmente (fallback)",
                        "storage": "local"
                    }
                    
        except Exception as e:
            logger.error(f"Error subiendo documento: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_to_file(self, document: Dict[str, Any]):
        """Guardar documento en archivo como último recurso"""
        docs_dir = "local_documents"
        os.makedirs(docs_dir, exist_ok=True)
        
        file_path = os.path.join(docs_dir, f"{document['doc_id']}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(document, f, indent=2, ensure_ascii=False)
    
    def search_documents(
        self,
        user_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Buscar documentos"""
        try:
            if self.use_local:
                # Búsqueda local
                if self.search_client and hasattr(self.search_client, 'search_documents'):
                    results = self.search_client.search_documents(query, top_k)
                    return [r['document'] for r in results]
                else:
                    return self._search_in_files(query, top_k)
            else:
                # Búsqueda en Azure
                try:
                    results = self.search_client.search(query, top=top_k)
                    return list(results)
                except Exception as e:
                    logger.error(f"Error buscando en Azure: {e}")
                    return self._search_in_files(query, top_k)
                    
        except Exception as e:
            logger.error(f"Error buscando documentos: {e}")
            return []
    
    def _search_in_files(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Buscar en archivos locales"""
        docs_dir = "local_documents"
        if not os.path.exists(docs_dir):
            return []
        
        results = []
        query_lower = query.lower()
        
        for filename in os.listdir(docs_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(docs_dir, filename), 'r', encoding='utf-8') as f:
                        doc = json.load(f)
                        # Búsqueda simple
                        if (query_lower in doc.get('content', '').lower() or
                            query_lower in doc.get('filename', '').lower() or
                            query_lower in doc.get('subject', '').lower()):
                            results.append(doc)
                except:
                    continue
        
        return results[:top_k]
    
    def list_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Listar documentos del usuario"""
        try:
            if self.use_local:
                # Listar documentos locales
                docs_dir = "local_documents"
                if not os.path.exists(docs_dir):
                    return []
                
                documents = []
                for filename in os.listdir(docs_dir):
                    if filename.endswith('.json'):
                        try:
                            with open(os.path.join(docs_dir, filename), 'r', encoding='utf-8') as f:
                                doc = json.load(f)
                                if doc.get('user_id') == user_id or user_id == "system":
                                    documents.append(doc)
                        except:
                            continue
                return documents
            else:
                # Listar de Azure
                try:
                    results = self.search_client.search("*", top=100)
                    return [doc for doc in results if doc.get('user_id') == user_id or user_id == "system"]
                except:
                    return []
        except Exception as e:
            logger.error(f"Error listando documentos: {e}")
            return []