"""
Agente Educativo Premium con RAG Híbrido
- Biblioteca personal de documentos educativos
- Búsqueda en internet con Exa Tools
- Azure Search para documentos personales
- Funcionalidad premium para suscriptores
"""

import sys
import os
sys.path.append('.')

from src.config import settings
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
from textwrap import dedent
from dotenv import load_dotenv
import json
import hashlib
import uuid

# Importar Groq para respuestas
try:
    from groq import Groq as GroqClient
    GROQ_AVAILABLE = True
except ImportError:
    GroqClient = None
    GROQ_AVAILABLE = False

# Importar Exa para búsquedas web
try:
    from exa_py import Exa
    EXA_AVAILABLE = True
    print("✅ Exa disponible para búsquedas web")
except ImportError:
    print("⚠️ Exa no disponible - búsquedas web deshabilitadas temporalmente")
    Exa = None
    EXA_AVAILABLE = False

# Importar framework Agno
try:
    from agno.agent import Agent, RunResponse
    from agno.models.openai import OpenAIChat
    AGNO_AVAILABLE = True
except ImportError:
    Agent = object
    RunResponse = dict
    OpenAIChat = object
    AGNO_AVAILABLE = False

load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Azure Search
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://juliaai.search.windows.net")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY", "")
AZURE_SEARCH_INDEX = os.getenv("UNIVERSITY_INDEX_NAME", "universidad")

class EducationalDocumentManager:
    """Gestor de documentos educativos personales del usuario con Azure Search"""
    
    def __init__(self):
        """Inicializar gestor de documentos educativos con Azure Search"""
        self.search_client = None
        self.openai_client = None
        self.setup_azure_search()
        self.setup_openai()
        print("📚 Educational Document Manager inicializado con Azure Search")
    
    def setup_azure_search(self):
        """Configurar cliente de Azure Search"""
        try:
            if AZURE_SEARCH_KEY and AZURE_SEARCH_ENDPOINT:
                credentials = AzureKeyCredential(AZURE_SEARCH_KEY)
                self.search_client = SearchClient(
                    endpoint=AZURE_SEARCH_ENDPOINT,
                    index_name=AZURE_SEARCH_INDEX,
                    credential=credentials
                )
                print(f"✅ Azure Search configurado: {AZURE_SEARCH_INDEX}")
            else:
                print("⚠️ Credenciales de Azure Search no encontradas - usando modo simulado")
                self.search_client = None
        except Exception as e:
            print(f"❌ Error configurando Azure Search: {e}")
            self.search_client = None
    
    def setup_openai(self):
        """Configurar cliente OpenAI para embeddings"""
        try:
            # Usar Groq si está disponible, sino OpenAI
            if settings.groq_api_key:
                # Para embeddings podemos usar un servicio local o Groq
                print("📊 Usando Groq para procesamiento")
            else:
                print("⚠️ No hay API key configurada")
        except Exception as e:
            print(f"❌ Error configurando OpenAI: {e}")
    
    def _generate_embeddings(self, text: str) -> List[float]:
        """Generar embeddings para el texto (simulado por ahora)"""
        # Por simplicidad, generar vector dummy
        # En producción, usar OpenAI embeddings o similar
        import random
        return [random.random() for _ in range(1536)]
    
    def upload_document(self, user_id: str, file_content: str, filename: str, 
                       category: str = "general", subject: str = "general", 
                       level: str = "general", document_type: str = "notes") -> Dict:
        """
        Sube un documento educativo a Azure Search
        """
        try:
            # Generar ID único para el documento
            doc_id = str(uuid.uuid4())
            
            # Generar hash del contenido para evitar duplicados
            content_hash = hashlib.md5(file_content.encode()).hexdigest()
            
            if self.search_client:
                # Generar embeddings para el contenido
                content_vector = self._generate_embeddings(file_content)
                
                # Preparar documento para Azure Search
                document = {
                    "id": doc_id,
                    "user_id": user_id,
                    "title": filename,
                    "content": file_content,
                    "content_hash": content_hash,
                    "category": category,
                    "subject": subject,
                    "level": level,
                    "document_type": document_type,
                    "upload_date": datetime.now().isoformat(),
                    "word_count": len(file_content.split()),
                    "content_vector": content_vector,
                    "search_score": 1.0
                }
                
                # Subir a Azure Search
                result = self.search_client.upload_documents([document])
                
                print(f"✅ Documento '{filename}' subido a Azure Search")
                
                return {
                    "success": True,
                    "document_id": doc_id,
                    "message": f"Documento '{filename}' subido exitosamente a Azure Search",
                    "category": category,
                    "subject": subject,
                    "word_count": len(file_content.split()),
                    "azure_result": str(result)
                }
            else:
                # Fallback a almacenamiento simulado
                print("⚠️ Azure Search no disponible - usando almacenamiento simulado")
                return {
                    "success": True,
                    "document_id": doc_id,
                    "message": f"Documento '{filename}' procesado (modo simulado)",
                    "category": category,
                    "subject": subject,
                    "word_count": len(file_content.split())
                }
            
        except Exception as e:
            logger.error(f"Error subiendo documento a Azure Search: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error subiendo el documento a Azure Search"
            }
    
    def search_personal_documents(self, user_id: str, query: str, 
                                 category: str = None, subject: str = None, 
                                 top_k: int = 5) -> Dict:
        """
        Busca en los documentos personales del usuario usando Azure Search
        """
        try:
            if self.search_client:
                # Construir filtro para el usuario específico
                filter_expr = f"user_id eq '{user_id}'"
                
                if category:
                    filter_expr += f" and category eq '{category}'"
                if subject:
                    filter_expr += f" and subject eq '{subject}'"
                
                # Realizar búsqueda en Azure Search
                search_results = self.search_client.search(
                    search_text=query,
                    filter=filter_expr,
                    top=top_k,
                    include_total_count=True
                )
                
                documents = []
                for result in search_results:
                    documents.append({
                        "id": result.get("id"),
                        "title": result.get("title"),
                        "content": result.get("content", "")[:500] + "...",
                        "category": result.get("category"),
                        "subject": result.get("subject"),
                        "upload_date": result.get("upload_date"),
                        "search_score": result.get("@search.score", 0),
                        "word_count": result.get("word_count")
                    })
                
                return {
                    "success": True,
                    "documents": documents,
                    "total_found": len(documents),
                    "query": query,
                    "filters": {"category": category, "subject": subject}
                }
            else:
                # Fallback a búsqueda simulada
                return {
                    "success": True,
                    "documents": [],
                    "total_found": 0,
                    "message": "Azure Search no disponible - búsqueda simulada"
                }
            
        except Exception as e:
            logger.error(f"Error buscando documentos en Azure Search: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents": [],
                "total_found": 0
            }
    
    def list_user_documents(self, user_id: str, limit: int = 50) -> Dict:
        """
        Lista todos los documentos del usuario desde Azure Search
        """
        try:
            if self.search_client:
                # Buscar documentos del usuario específico
                filter_expr = f"user_id eq '{user_id}'"
                
                search_results = self.search_client.search(
                    search_text="*",  # Buscar todos
                    filter=filter_expr,
                    top=limit,
                    include_total_count=True,
                    order_by=["upload_date desc"]  # Más recientes primero
                )
                
                documents = []
                for result in search_results:
                    documents.append({
                        "id": result.get("id"),
                        "title": result.get("title"),
                        "content": result.get("content", "")[:200] + "...",
                        "category": result.get("category"),
                        "subject": result.get("subject"),
                        "upload_date": result.get("upload_date"),
                        "word_count": result.get("word_count"),
                        "document_type": result.get("document_type")
                    })
                
                return {
                    "success": True,
                    "documents": documents,
                    "total_found": len(documents),
                    "user_id": user_id
                }
            else:
                # Fallback a lista simulada
                return {
                    "success": True,
                    "documents": [],
                    "total_found": 0,
                    "message": "Azure Search no disponible - lista simulada"
                }
                
        except Exception as e:
            logger.error(f"Error listando documentos desde Azure Search: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents": [],
                "total_found": 0
            }

class WebSearchManager:
    """Gestor de búsquedas web educativas - Versión simulada"""
    
    def __init__(self):
        print("🌐 Web Search Manager inicializado (modo simulado)")
    
    def search_educational_content(self, query: str, subject: str = None, 
                                 type_filter: str = "educational", 
                                 num_results: int = 5) -> Dict:
        """
        Búsqueda web simulada para pruebas
        """
        try:
            # Resultados simulados educativos
            simulated_results = [
                {
                    "title": f"Recursos educativos sobre {query}",
                    "url": f"https://khanacademy.org/search?q={query.replace(' ', '+')}",
                    "snippet": f"Explicación completa sobre {query} con ejemplos prácticos y ejercicios interactivos.",
                    "domain": "khanacademy.org",
                    "score": 0.9
                },
                {
                    "title": f"Curso universitario: {query}",
                    "url": f"https://coursera.org/learn/{query.replace(' ', '-')}",
                    "snippet": f"Curso completo sobre {query} impartido por profesores universitarios reconocidos.",
                    "domain": "coursera.org", 
                    "score": 0.8
                },
                {
                    "title": f"Wikipedia: {query}",
                    "url": f"https://es.wikipedia.org/wiki/{query.replace(' ', '_')}",
                    "snippet": f"Artículo enciclopédico sobre {query} con referencias académicas y fuentes verificadas.",
                    "domain": "wikipedia.org",
                    "score": 0.7
                }
            ]
            
            return {
                "success": True,
                "results": simulated_results[:num_results],
                "query": query,
                "enhanced_query": f"{subject}: {query}" if subject else query,
                "total_results": len(simulated_results)
            }
            
        except Exception as e:
            logger.error(f"Error en búsqueda web: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }

class EducationalRAGAgent:
    """Agente Educativo Premium con RAG Híbrido - Versión simplificada"""
    
    def __init__(self, api_key: str = None):
        self.doc_manager = EducationalDocumentManager()
        self.web_manager = WebSearchManager()
        self.api_key = api_key or settings.groq_api_key
        
        print("🎓 Educational RAG Agent inicializado")
    
    async def process_request(self, message: str, context: Dict = None) -> str:
        """
        Procesa una consulta educativa con RAG híbrido
        """
        try:
            if not message or not message.strip():
                return "Por favor, formule su consulta educativa."
            
            # Extraer parámetros del contexto
            user_id = context.get("user_id", "default") if context else "default"
            subject = context.get("subject") if context else None
            category = context.get("category") if context else None
            search_web = context.get("search_web", True) if context else True
            
            logger.info(f"🎓 Consulta educativa: {message[:100]}...")
            
            # PASO 1: Buscar en documentos personales
            personal_results = self.doc_manager.search_personal_documents(
                user_id=user_id,
                query=message,
                subject=subject,
                category=category,
                top_k=3
            )
            
            # PASO 2: Buscar en web si está habilitado
            web_results = {"success": False, "results": []}
            if search_web:
                web_results = self.web_manager.search_educational_content(
                    query=message,
                    subject=subject,
                    num_results=3
                )
            
            # PASO 3: Generar respuesta combinada
            response_content = await self._generate_educational_response(
                query=message,
                personal_docs=personal_results.get('documents', []),
                web_results=web_results.get('results', []),
                user_id=user_id,
                subject=subject
            )
            
            return response_content
            
        except Exception as e:
            logger.error(f"Error en agente educativo: {e}")
            return "Disculpe, hubo un error procesando su consulta educativa. Por favor, intente nuevamente."
    
    async def _generate_educational_response(self, query: str, personal_docs: List[Dict], 
                                           web_results: List[Dict], user_id: str, 
                                           subject: str = None) -> str:
        """Genera respuesta educativa combinando fuentes personales y web"""
        
        try:
            # Usar Groq si está disponible
            if GROQ_AVAILABLE and self.api_key:
                # Preparar contexto de documentos personales
                personal_context = ""
                if personal_docs:
                    personal_context = "\n📚 **DOCUMENTOS PERSONALES ENCONTRADOS:**\n"
                    for i, doc in enumerate(personal_docs[:3], 1):
                        content = doc.get('content', '')[:800]
                        personal_context += f"""
📄 **Documento {i}**: {doc['filename']}
📂 Materia: {doc['subject']} | Categoría: {doc['category']}
📝 Contenido relevante: {content}...
"""
                
                # Preparar contexto web
                web_context = ""
                if web_results:
                    web_context = "\n🌐 **RECURSOS WEB ADICIONALES:**\n"
                    for i, result in enumerate(web_results[:3], 1):
                        web_context += f"""
🔗 **Fuente {i}**: {result['title']}
🌍 URL: {result['url']}
📄 Resumen: {result['snippet']}
"""
                
                # Crear prompt para Groq
                prompt = f"""
Eres un tutor educativo personal especializado. Un estudiante te ha hecho esta consulta:

**CONSULTA DEL ESTUDIANTE**: "{query}"
{f"**MATERIA**: {subject}" if subject else ""}

{personal_context}

{web_context}

**INSTRUCCIONES**:
1. Analiza primero los documentos personales del estudiante (si los hay)
2. Complementa con información de fuentes web cuando sea útil
3. Proporciona una respuesta educativa clara y personalizada
4. Usa un tono motivador y pedagógico
5. Estructura la información de manera clara (usa markdown)
6. Sé un Tutor Educativo Premium especializado

**FORMATO DE RESPUESTA**:
- Respuesta principal basada en documentos personales (si los hay)
- Complementos de fuentes web (si es relevante)
- Recomendaciones de estudio personalizadas
- Referencias a los documentos/fuentes consultados

Genera una respuesta educativa completa y personalizada.
"""
                
                try:
                    groq_client = GroqClient(api_key=self.api_key)
                    
                    response = groq_client.chat.completions.create(
                        model=settings.groq_model,
                        messages=[
                            {"role": "system", "content": "Eres un tutor educativo experto especializado en aprendizaje personalizado."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1200,
                        temperature=0.3,
                        top_p=0.9
                    )
                    
                    ai_response = response.choices[0].message.content
                    
                except Exception as e:
                    logger.error(f"Error con Groq: {e}")
                    ai_response = self._generate_fallback_response(query, personal_docs, web_results)
            else:
                ai_response = self._generate_fallback_response(query, personal_docs, web_results)
            
            # Agregar información de fuentes
            sources_info = "\n\n---\n\n"
            sources_info += f"📊 **FUENTES CONSULTADAS:**\n"
            
            if personal_docs:
                sources_info += f"📚 Documentos personales: {len(personal_docs)}\n"
                for doc in personal_docs[:2]:
                    sources_info += f"  • {doc['filename']} ({doc['subject']})\n"
            
            if web_results:
                sources_info += f"🌐 Fuentes web: {len(web_results)}\n"
                for result in web_results[:2]:
                    sources_info += f"  • {result['title']}\n"
            
            sources_info += f"\n🤖 **Tutor Educativo Premium** | 📚 Biblioteca Personal RAG"
            
            return ai_response + sources_info
            
        except Exception as e:
            logger.error(f"Error generando respuesta educativa: {e}")
            return f"Error generando respuesta para: {query}"
    
    def _generate_fallback_response(self, query: str, personal_docs: List[Dict], 
                                  web_results: List[Dict]) -> str:
        """Respuesta de fallback cuando Groq no está disponible"""
        
        response = f"## 📚 Respuesta a: {query}\n\n"
        
        if personal_docs:
            response += "### 📄 Desde tus documentos personales:\n\n"
            for doc in personal_docs[:2]:
                response += f"**{doc['filename']}** ({doc['subject']}):\n"
                response += f"{doc['content'][:400]}...\n\n"
        
        if web_results:
            response += "### 🌐 Recursos adicionales en web:\n\n"
            for result in web_results[:2]:
                response += f"**{result['title']}**\n"
                response += f"{result['snippet']}\n"
                response += f"🔗 [Ver más]({result['url']})\n\n"
        
        if not personal_docs and not web_results:
            response += "No encontré información específica sobre este tema en tus documentos ni en web. Te recomiendo:\n\n"
            response += "1. Subir documentos relacionados a tu biblioteca personal\n"
            response += "2. Reformular la consulta con términos más específicos\n"
            response += "3. Especificar la materia o área de estudio\n"
        
        return response
    
    # Métodos específicos para la biblioteca
    def upload_document(self, user_id: str, content: str, filename: str, 
                       category: str = "general", subject: str = "general",
                       level: str = "general") -> Dict:
        """API para subir documento educativo"""
        return self.doc_manager.upload_document(
            user_id=user_id, 
            file_content=content, 
            filename=filename, 
            category=category, 
            subject=subject, 
            level=level
        )

    def search_documents(self, user_id: str, query: str, subject: str = None, 
                        category: str = None) -> Dict:
        """API para búsqueda en documentos"""
        return self.doc_manager.search_personal_documents(
            user_id=user_id,
            query=query,
            subject=subject,
            category=category,
            top_k=5
        )

# Funciones de API para integración
def upload_educational_document(user_id: str, content: str, filename: str, 
                               category: str = "general", subject: str = "general",
                               level: str = "general") -> Dict:
    """API para subir documento educativo"""
    try:
        agent = EducationalRAGAgent()
        return agent.upload_document(
            user_id=user_id, 
            content=content, 
            filename=filename, 
            category=category, 
            subject=subject, 
            level=level
        )
    except Exception as e:
        logger.error(f"Error en upload_educational_document: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error al subir el documento educativo"
        }

def search_educational_query(user_id: str, query: str, subject: str = None, 
                           include_web: bool = True) -> str:
    """API para consulta educativa"""
    try:
        agent = EducationalRAGAgent()
        response = agent.process_request(
            message=query,
            context={
                "user_id": user_id,
                "subject": subject,
                "search_web": include_web
            }
        )
        return response
    except Exception as e:
        logger.error(f"Error en search_educational_query: {e}")
        return f"Error procesando consulta: {str(e)}"

def get_library_stats(user_id: str) -> Dict:
    """API para estadísticas de biblioteca"""
    try:
        agent = EducationalRAGAgent()
        return agent.get_library_stats(user_id)
    except Exception as e:
        logger.error(f"Error en get_library_stats: {e}")
        return {"success": False, "error": str(e)}
