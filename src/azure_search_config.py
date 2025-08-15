"""
Configuración mejorada de Azure Search con fallback local
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AzureSearchConfig:
    """Configuración de Azure Search con manejo de errores"""
    
    def __init__(self):
        self.service_name = os.getenv("AZURE_SEARCH_SERVICE_NAME", "juliaai")
        self.admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY", "")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "universidad")
        self.endpoint = f"https://{self.service_name}.search.windows.net"
        self.use_local_fallback = os.getenv("USE_LOCAL_FALLBACK", "true").lower() == "true"
        
        # Verificar conectividad
        self.is_available = self._check_availability()
        
        if not self.is_available:
            logger.warning("⚠️ Azure Search no disponible, usando almacenamiento local")
    
    def _check_availability(self) -> bool:
        """Verificar si Azure Search está disponible"""
        if not self.admin_key:
            logger.info("🔐 Azure Search API Key no configurada")
            return False
        
        try:
            import socket
            # Intentar resolver el host
            socket.gethostbyname(f"{self.service_name}.search.windows.net")
            return True
        except socket.gaierror:
            logger.error(f"❌ No se puede resolver el host: {self.service_name}.search.windows.net")
            return False
        except Exception as e:
            logger.error(f"❌ Error verificando Azure Search: {e}")
            return False

class LocalSearchFallback:
    """Sistema de búsqueda local como fallback"""
    
    def __init__(self):
        self.documents_dir = "local_search_db"
        os.makedirs(self.documents_dir, exist_ok=True)
        self.index_file = os.path.join(self.documents_dir, "index.json")
        self._load_index()
    
    def _load_index(self):
        """Cargar índice local"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except:
                self.index = {"documents": [], "metadata": {}}
        else:
            self.index = {"documents": [], "metadata": {}}
    
    def _save_index(self):
        """Guardar índice local"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
    
    def upload_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Subir documento al índice local"""
        try:
            # Generar ID único
            doc_id = f"local_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.index['documents'])}"
            
            # Agregar documento con ID y timestamp
            document['id'] = doc_id
            document['upload_date'] = datetime.now().isoformat()
            
            self.index['documents'].append(document)
            self._save_index()
            
            return {
                'success': True,
                'document_id': doc_id,
                'message': 'Documento guardado localmente'
            }
        except Exception as e:
            logger.error(f"Error guardando documento localmente: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_documents(self, query: str, top_k: int = 5) -> list:
        """Buscar documentos en el índice local"""
        try:
            results = []
            query_lower = query.lower()
            
            for doc in self.index['documents']:
                # Búsqueda simple en título y contenido
                score = 0
                if 'title' in doc and query_lower in doc['title'].lower():
                    score += 2
                if 'content' in doc and query_lower in doc['content'].lower():
                    score += 1
                if 'filename' in doc and query_lower in doc['filename'].lower():
                    score += 1.5
                
                if score > 0:
                    results.append({
                        'document': doc,
                        'score': score
                    })
            
            # Ordenar por score y retornar top_k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error buscando documentos: {e}")
            return []

# Instancia global
azure_config = AzureSearchConfig()
local_search = LocalSearchFallback()

def get_search_client():
    """Obtener cliente de búsqueda apropiado"""
    if azure_config.is_available:
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            
            return SearchClient(
                endpoint=azure_config.endpoint,
                index_name=azure_config.index_name,
                credential=AzureKeyCredential(azure_config.admin_key)
            )
        except Exception as e:
            logger.error(f"Error creando Azure Search Client: {e}")
    
    # Retornar fallback local
    return local_search