# 🚀 Sistema Educativo Multiagente

Un sistema completo de agentes de IA especializados para colegios, construido con **Agno Framework** y **Groq**. Permite crear una biblioteca digital donde los docentes pueden subir archivos y consultar a agentes especializados en generación de exámenes, creación de currículums, tutoría personalizada y más.

## ✨ Características Principales

### 🤖 Agentes Especializados
- **📝 Generador de Exámenes**: Crea evaluaciones personalizadas con diferentes tipos de preguntas
- **📚 Creador de Currículums**: Diseña programas educativos completos y estructurados
- **👨‍🏫 Tutor Personal**: Proporciona apoyo educativo adaptado al estilo de aprendizaje
- **📋 Planificador de Lecciones**: Genera planes de clase detallados y efectivos
- **📄 Analizador de Documentos**: Extrae información y responde preguntas sobre documentos

### 🧠 Tecnología Avanzada
- **Framework**: Agno (memoria, coordinación y colaboración entre agentes)
- **Modelos**: Groq (Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B)
- **Memoria**: Sistema de memoria persistente con Agno Memory
- **Búsqueda**: Base de datos vectorial ChromaDB para consultas inteligentes
- **Interfaz**: Aplicación web moderna con Streamlit

### 🎯 Funcionalidades
- **Biblioteca Digital**: Sube PDFs, DOCX, PPTX y otros documentos
- **Consultas Inteligentes**: Pregunta sobre cualquier contenido subido
- **Colaboración Multi-Agente**: Los agentes trabajan en equipo para tareas complejas
- **Personalización**: Adapta las respuestas al nivel educativo y estilo de aprendizaje
- **Exportación**: Genera reportes en múltiples formatos

## 🚀 Instalación Rápida

### Opción 1: Instalación Automática (Recomendada)

```bash
# Clona o descarga el proyecto
git clone [tu-repositorio]
cd sistema-educativo

# Ejecuta el instalador automático
python install.py
```

El instalador creará automáticamente:
- ✅ Entorno virtual
- ✅ Instalación de dependencias
- ✅ Configuración de archivos
- ✅ Estructura de directorios

### Opción 2: Instalación Manual

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar entorno
cp env_template.txt .env
```

## ⚙️ Configuración

### 1. API Key de Groq (Obligatoria)

1. Visita [Groq Console](https://console.groq.com/keys)
2. Crea una cuenta gratuita
3. Genera una API key
4. Edita el archivo `.env`:

```env
GROQ_API_KEY=tu_api_key_real_aqui
```

### 2. Configuración Opcional

El archivo `.env` permite personalizar:

```env
# Modelos de Groq
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FAST_MODEL=llama-3.1-8b-instant

# Configuración de la app
DEBUG=true
LOG_LEVEL=INFO
MAX_FILE_SIZE=50

# Agentes
MAX_CONCURRENT_AGENTS=5
AGENT_TIMEOUT=300
```

## 🧪 Pruebas del Sistema

```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/macOS
# o
venv\Scripts\activate     # Windows

# Probar todos los agentes
python test_agents.py
```

Las pruebas incluyen:
- ✅ Generación de exámenes
- ✅ Creación de currículums
- ✅ Tutoría personalizada
- ✅ Planificación de lecciones
- ✅ Colaboración multi-agente
- ✅ Búsqueda inteligente

## 🌐 Interfaz Web

```bash
# Ejecutar aplicación web
streamlit run src/web/app.py
```

La interfaz incluye:

### 📚 Biblioteca Digital
- Sube documentos (PDF, DOCX, PPTX, TXT)
- Visualiza archivos subidos
- Busca contenido en documentos

### 🤖 Chat con Agentes
- Selecciona el agente especializado
- Realiza consultas específicas
- Obtén respuestas personalizadas

### 📊 Panel de Control
- Estado de agentes
- Métricas del sistema
- Historial de consultas

## 📖 Ejemplos de Uso

### Generador de Exámenes
```python
from src.core.agent_coordinator import AgentCoordinator
from src.models import AgentRequest, AgentType

coordinator = AgentCoordinator()

request = AgentRequest(
    agent_type=AgentType.EXAM_GENERATOR,
    prompt="Crea un examen de matemáticas sobre fracciones para 5to grado",
    parameters={
        "subject": "Matemáticas",
        "grade_level": "5to Primaria", 
        "num_questions": 10,
        "difficulty": "intermediate"
    }
)

response = await coordinator.process_request(request)
print(response.content)
```

### Tutor Personalizado
```python
request = AgentRequest(
    agent_type=AgentType.TUTOR,
    prompt="Explica qué son las fracciones con ejemplos visuales",
    context={
        "student_grade": "4to Primaria",
        "learning_style": "Visual",
        "difficulty_areas": ["Matemáticas abstractas"]
    }
)

response = await coordinator.process_request(request)
```

### Colaboración Multi-Agente
```python
# Los agentes trabajan en equipo
task = "Crear un módulo completo sobre el Sistema Solar para 6to grado"
agents = [AgentType.CURRICULUM_CREATOR, AgentType.LESSON_PLANNER, AgentType.EXAM_GENERATOR]

result = await coordinator.multi_agent_collaboration(
    task, 
    agents, 
    coordination_strategy="sequential"
)
```

## 🏗️ Arquitectura del Sistema

```
Sistema Educativo Multiagente
│
├── 🧠 Agno Framework
│   ├── Memoria persistente
│   ├── Coordinación de agentes
│   └── Herramientas especializadas
│
├── 🤖 Agentes Especializados
│   ├── ExamGeneratorAgent
│   ├── CurriculumCreatorAgent
│   ├── TutorAgent
│   ├── LessonPlannerAgent
│   └── DocumentAnalyzerAgent
│
├── 🔗 Coordinador Central
│   ├── Enrutamiento de solicitudes
│   ├── Colaboración multi-agente
│   └── Gestión de recursos
│
├── 💾 Almacenamiento
│   ├── ChromaDB (vectores)
│   ├── Archivos locales
│   └── Memoria de sesiones
│
└── 🌐 Interfaz Web
    ├── Biblioteca digital
    ├── Chat con agentes
    └── Panel de control
```

## 🛠️ Estructura del Proyecto

```
sistema-educativo/
│
├── agents/                     # Agentes especializados
│   ├── base_agent.py          # Clase base con Agno
│   ├── exam_generator/        # Generador de exámenes
│   ├── curriculum_creator/    # Creador de currículums
│   ├── tutor/                 # Tutor personalizado
│   ├── lesson_planner/        # Planificador de lecciones
│   └── document_analyzer/     # Analizador de documentos
│
├── src/                       # Código fuente principal
│   ├── config.py             # Configuración con Groq
│   ├── models.py             # Modelos de datos
│   ├── core/
│   │   └── agent_coordinator.py  # Coordinador con Agno
│   ├── services/
│   │   └── document_service.py   # Gestión de documentos
│   └── web/
│       └── app.py            # Interfaz Streamlit
│
├── data/                     # Datos y almacenamiento
├── requirements.txt          # Dependencias Python
├── test_agents.py           # Script de pruebas
├── install.py               # Instalador automático
└── README.md               # Este archivo
```

## 📋 Modelos Disponibles

### Groq Models
- **llama-3.3-70b-versatile**: Modelo principal para tareas complejas
- **llama-3.1-8b-instant**: Modelo rápido para consultas simples
- **llama-3.2-90b-text-preview**: Modelo experimental avanzado
- **mixtral-8x7b-32768**: Modelo multilingüe especializado

### Configuración por Agente
Cada agente usa el modelo más apropiado para su especialidad, optimizando velocidad y calidad.

## 🎯 Casos de Uso

### Para Docentes
- ✅ Crear exámenes personalizados rápidamente
- ✅ Diseñar currículums alineados con estándares
- ✅ Planificar lecciones detalladas y efectivas
- ✅ Analizar documentos educativos
- ✅ Obtener ideas para actividades

### Para Estudiantes
- ✅ Tutoría personalizada 24/7
- ✅ Explicaciones adaptadas a su estilo de aprendizaje
- ✅ Ayuda con tareas sin dar respuestas directas
- ✅ Motivación y apoyo académico
- ✅ Planes de estudio personalizados

### Para Instituciones
- ✅ Biblioteca digital centralizada
- ✅ Consultas inteligentes sobre contenido
- ✅ Generación automatizada de materiales
- ✅ Análisis de documentos institucionales
- ✅ Soporte educativo escalable

## 🔧 Solución de Problemas

### Error: "GROQ_API_KEY no está configurada"
```bash
# Verifica que el archivo .env existe y contiene:
GROQ_API_KEY=tu_api_key_real

# Reinicia la aplicación después de configurar
```

### Error: "No module named 'agno'"
```bash
# Reinstala las dependencias
pip install -r requirements.txt

# O ejecuta el instalador automático
python install.py
```

### Error: "Agent not available"
```bash
# Verifica que todas las dependencias están instaladas
python test_agents.py

# Revisa los logs en la carpeta logs/
```

## 🤝 Contribuciones

El proyecto está diseñado para ser extensible:

1. **Nuevos Agentes**: Hereda de `BaseEducationalAgent`
2. **Nuevas Herramientas**: Implementa herramientas de Agno
3. **Nuevos Modelos**: Configura en `config.py`
4. **Nueva UI**: Extiende la aplicación Streamlit

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## 🆘 Soporte

- **Documentación**: Este README
- **Ejemplos**: `test_agents.py`
- **Configuración**: Archivo `.env`
- **Logs**: Carpeta `logs/`

---

¡Disfruta creando experiencias educativas increíbles con IA! 🚀📚
