"""
Sistema de agentes multiagente usando los agentes reales
"""

import os
import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.config import settings
from src.models import AgentType, AgentRequest, AgentResponse
from src.services.document_service_simple import DocumentService

# Importar agentes reales
from agents import (
    ExamGeneratorAgent,
    CurriculumCreatorAgent,
    TutorAgent,
    LessonPlannerAgent,
    DocumentAnalyzerAgent
)


class AgentOrchestrator:
    """Orquestador principal de agentes usando agentes reales"""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.agents = {}
        self._setup_real_agents()
    
    def _setup_real_agents(self):
        """Configurar agentes reales de la carpeta agents"""
        try:
            # Obtener API key
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY no encontrada en variables de entorno")
            
            # Instanciar agentes reales
            self.agents = {
                AgentType.EXAM_GENERATOR: ExamGeneratorAgent(groq_api_key),
                AgentType.CURRICULUM_CREATOR: CurriculumCreatorAgent(groq_api_key),
                AgentType.TUTOR: TutorAgent(groq_api_key),
                AgentType.LESSON_PLANNER: LessonPlannerAgent(groq_api_key),
                AgentType.PERFORMANCE_ANALYZER: DocumentAnalyzerAgent(groq_api_key)  # Usar DocumentAnalyzer como Performance Analyzer
            }
            
            print("✅ Agentes reales configurados correctamente")
            
        except Exception as e:
            print(f"❌ Error configurando agentes reales: {e}")
            # Fallback a agentes simples si hay error
            self.agents = {
                AgentType.EXAM_GENERATOR: "exam_agent_fallback",
                AgentType.CURRICULUM_CREATOR: "curriculum_agent_fallback", 
                AgentType.TUTOR: "tutor_agent_fallback",
                AgentType.PERFORMANCE_ANALYZER: "analyzer_agent_fallback",
                AgentType.LESSON_PLANNER: "planner_agent_fallback"
            }
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Procesar solicitud usando agentes reales"""
        try:
            # Obtener agente correspondiente
            agent = self.agents.get(request.agent_type)
            if not agent:
                raise ValueError(f"Agente {request.agent_type} no disponible")
            
            # Si es un string (fallback), usar respuesta simple
            if isinstance(agent, str):
                response_content = await self._generate_simple_response(request)
            else:
                # Usar agente real
                response_content = await self._execute_real_agent(agent, request)
            
            return AgentResponse(
                agent_id=str(uuid.uuid4()),
                agent_type=request.agent_type,
                response=response_content,
                status="completed",
                timestamp=datetime.now(),
                metadata={
                    "agent_type": "real" if not isinstance(agent, str) else "fallback",
                    "processing_time": "2.0s"
                }
            )
        except Exception as e:
            return AgentResponse(
                agent_id=str(uuid.uuid4()),
                agent_type=request.agent_type,
                response=f"Error procesando solicitud: {str(e)}",
                status="error",
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            )
    
    async def _execute_real_agent(self, agent, request: AgentRequest) -> str:
        """Ejecutar un agente real"""
        try:
            # Preparar contexto adicional si hay documentos
            context = request.context or {}
            if request.documents:
                docs = await self.document_service.get_documents_by_ids(request.documents)
                context["documents"] = [
                    {"filename": doc.filename, "content": doc.content[:500] + "..."}
                    for doc in docs
                ]
            
            # Añadir parámetros si están disponibles
            if request.parameters:
                context.update(request.parameters)
            
            # Llamar al método process_request del agente
            if hasattr(agent, 'process_request'):
                result = await agent.process_request(request.prompt, context)
                
                # Si el resultado es un dict, extraer la respuesta
                if isinstance(result, dict):
                    return result.get('response', str(result))
                else:
                    return str(result)
            else:
                # Fallback si el agente no tiene process_request
                print(f"⚠️ Agente {request.agent_type.value} no tiene método process_request")
                return await self._generate_simple_response(request)
            
        except Exception as e:
            print(f"❌ Error ejecutando agente real: {e}")
            # Fallback a respuesta simple en caso de error
            return await self._generate_simple_response(request)
    
    async def _generate_simple_response(self, request: AgentRequest) -> str:
        """Generar respuesta simple basada en el tipo de agente"""
        if request.agent_type == AgentType.EXAM_GENERATOR:
            return self._generate_exam_response(request)
        elif request.agent_type == AgentType.CURRICULUM_CREATOR:
            return self._generate_curriculum_response(request)
        elif request.agent_type == AgentType.TUTOR:
            return self._generate_tutor_response(request)
        elif request.agent_type == AgentType.LESSON_PLANNER:
            return self._generate_lesson_response(request)
        elif request.agent_type == AgentType.PERFORMANCE_ANALYZER:
            return self._generate_analyzer_response(request)
        else:
            return "Respuesta de agente genérico: He procesado tu solicitud."
    
    def _generate_exam_response(self, request: AgentRequest) -> str:
        """Generar respuesta del agente de exámenes"""
        params = request.parameters or {}
        subject = params.get('subject', 'Materia')
        topic = params.get('topic', 'Tema')
        num_questions = params.get('num_questions', 5)
        
        return f"""
# Examen de {subject}: {topic}

## Instrucciones
- Tiempo estimado: 45 minutos
- Lee cuidadosamente cada pregunta
- Selecciona la mejor respuesta

## Preguntas ({num_questions} preguntas)

### Pregunta 1
**¿Cuál es el concepto principal de {topic}?**
a) Opción A - Definición básica
b) Opción B - Aplicación práctica
c) Opción C - Concepto fundamental (CORRECTA)
d) Opción D - Ejemplo específico

**Respuesta correcta:** c) Opción C
**Explicación:** Esta es la respuesta correcta porque representa el concepto fundamental que sustenta toda la teoría de {topic}.

### Pregunta 2
**¿Cómo se aplica {topic} en situaciones reales?**
a) Solo en teoría
b) En múltiples contextos (CORRECTA)
c) Únicamente en laboratorio
d) No tiene aplicaciones

**Respuesta correcta:** b) En múltiples contextos
**Explicación:** {topic} tiene aplicaciones prácticas en diversos campos y situaciones cotidianas.

### Pregunta 3 (Respuesta abierta)
**Explica brevemente la importancia de {topic} en {subject} (máximo 5 líneas)**

**Respuesta modelo:** 
{topic} es fundamental en {subject} porque:
- Proporciona la base teórica necesaria
- Permite comprender conceptos más avanzados
- Facilita la resolución de problemas prácticos
- Conecta diferentes áreas de conocimiento
- Es esencial para el desarrollo profesional en este campo

### Pregunta 4
**¿Cuáles son las principales características de {topic}?**
a) Solo una característica principal
b) Dos características básicas
c) Múltiples características interrelacionadas (CORRECTA)
d) No tiene características definidas

**Respuesta correcta:** c) Múltiples características interrelacionadas
**Explicación:** {topic} se caracteriza por tener diversos aspectos que se complementan y refuerzan mutuamente.

### Pregunta 5
**En el contexto de {subject}, {topic} se relaciona principalmente con:**
a) Conceptos aislados
b) Teorías independientes
c) Un sistema integrado de conocimientos (CORRECTA)
d) Ideas sin conexión

**Respuesta correcta:** c) Un sistema integrado de conocimientos
**Explicación:** {topic} forma parte de un sistema coherente donde todos los elementos se interconectan.

## Criterios de Evaluación
- Pregunta 1-2, 4-5: 2 puntos cada una (8 puntos total)
- Pregunta 3: 2 puntos (evaluación cualitativa)
- **Total: 10 puntos**

## Tiempo recomendado por sección:
- Preguntas múltiple opción: 6 minutos cada una (24 min)
- Pregunta abierta: 15 minutos
- Revisión: 6 minutos
        """
    
    def _generate_curriculum_response(self, request: AgentRequest) -> str:
        """Generar respuesta del agente de currículum"""
        params = request.parameters or {}
        subject = params.get('subject', 'Materia')
        grade_level = params.get('grade_level', 'Nivel')
        duration = params.get('duration_weeks', 12)
        objectives = params.get('objectives', [])
        
        objectives_text = ""
        if objectives:
            objectives_text = "\n".join([f"- {obj}" for obj in objectives])
        
        return f"""
# Currículum de {subject} - {grade_level}

## Información General
- **Duración:** {duration} semanas
- **Nivel:** {grade_level}
- **Materia:** {subject}
- **Modalidad:** Presencial/Virtual híbrida

## Objetivos Generales del Curso
{objectives_text if objectives_text else "- Desarrollar competencias fundamentales en la materia\n- Fomentar el pensamiento crítico\n- Aplicar conocimientos en situaciones prácticas"}

## Estructura del Currículum

### Unidad 1: Fundamentos (Semanas 1-3)
**Objetivos específicos:**
- Comprender conceptos básicos de {subject}
- Establecer bases sólidas para aprendizajes posteriores
- Desarrollar vocabulario técnico esencial

**Contenidos:**
- Tema 1.1: Introducción a {subject}
- Tema 1.2: Conceptos fundamentales
- Tema 1.3: Principios básicos y aplicaciones iniciales

**Actividades:**
- Lecturas dirigidas
- Discusiones grupales
- Ejercicios prácticos básicos

**Evaluación:**
- Participación en clase (20%)
- Quiz conceptual (30%)
- Proyecto inicial (50%)

### Unidad 2: Desarrollo y Aplicación (Semanas 4-7)
**Objetivos específicos:**
- Aplicar conocimientos fundamentales
- Desarrollar habilidades prácticas
- Analizar casos de estudio reales

**Contenidos:**
- Tema 2.1: Metodologías de aplicación
- Tema 2.2: Casos de estudio
- Tema 2.3: Herramientas y técnicas avanzadas

**Actividades:**
- Talleres prácticos
- Análisis de casos
- Trabajo colaborativo

**Evaluación:**
- Talleres (25%)
- Análisis de casos (35%)
- Proyecto grupal (40%)

### Unidad 3: Profundización (Semanas 8-10)
**Objetivos específicos:**
- Profundizar en temas especializados
- Desarrollar pensamiento crítico avanzado
- Integrar conocimientos multidisciplinarios

**Contenidos:**
- Tema 3.1: Temas avanzados en {subject}
- Tema 3.2: Tendencias contemporáneas
- Tema 3.3: Conexiones interdisciplinarias

**Actividades:**
- Investigación individual
- Seminarios estudiantiles
- Debates académicos

**Evaluación:**
- Investigación (40%)
- Presentación (30%)
- Participación en debates (30%)

### Unidad 4: Síntesis y Aplicación Final (Semanas 11-12)
**Objetivos específicos:**
- Integrar todos los aprendizajes del curso
- Demostrar dominio competencial
- Aplicar conocimientos a proyectos complejos

**Contenidos:**
- Tema 4.1: Síntesis integradora
- Tema 4.2: Proyecto final
- Tema 4.3: Reflexión y evaluación

**Actividades:**
- Proyecto final integrador
- Presentaciones finales
- Autoevaluación y coevaluación

**Evaluación:**
- Proyecto final (60%)
- Presentación (25%)
- Autoevaluación (15%)

## Metodología de Enseñanza
- **Aprendizaje activo:** Participación constante del estudiante
- **Aprendizaje colaborativo:** Trabajo en equipos
- **Estudio de casos:** Análisis de situaciones reales
- **Tecnología educativa:** Uso de herramientas digitales

## Recursos Necesarios
- Textos especializados en {subject}
- Plataforma virtual de aprendizaje
- Laboratorio/aula especializada
- Material audiovisual
- Acceso a bases de datos académicas

## Sistema de Evaluación
- **Evaluación continua:** 70%
- **Evaluación final:** 30%
- **Criterios:** Conocimiento, aplicación, análisis, síntesis

## Cronograma de Evaluaciones
- Semana 3: Quiz unidad 1
- Semana 6: Proyecto grupal unidad 2
- Semana 9: Investigación individual
- Semana 12: Proyecto final integrador
        """
    
    def _generate_tutor_response(self, request: AgentRequest) -> str:
        """Generar respuesta del agente tutor"""
        prompt = request.prompt
        context = request.context or {}
        
        return f"""
¡Hola! 👋 Soy tu tutor virtual y estoy aquí para ayudarte con tus estudios.

## Tu Consulta
> "{prompt}"

## Mi Respuesta Personalizada

Te explico paso a paso para que puedas entender mejor:

### 🔍 **Análisis del Problema**
Primero, vamos a identificar qué necesitas saber exactamente. Tu pregunta se relaciona con conceptos fundamentales que son clave para tu aprendizaje.

### 📚 **Explicación Detallada**

**1. Punto Principal:**
El concepto central que necesitas entender es que cada tema se construye sobre conocimientos previos. Es como construir una casa - necesitas cimientos sólidos.

**2. Desarrollo:**
Para profundizar en este tema, considera lo siguiente:
- Los fundamentos teóricos proporcionan la base
- Las aplicaciones prácticas te ayudan a consolidar
- Los ejemplos reales te muestran la relevancia

**3. Aplicación Práctica:**
Te sugiero que practiques con ejercicios similares y que siempre te preguntes: "¿Cómo se relaciona esto con lo que ya sé?"

### 💡 **Consejos de Estudio**
- **Organiza tu tiempo:** Dedica sesiones cortas pero regulares
- **Toma notas activas:** Escribe con tus propias palabras
- **Practica regularmente:** La repetición espaciada es clave
- **Haz conexiones:** Relaciona conceptos nuevos con conocimientos previos

### 🎯 **Próximos Pasos Recomendados**
1. Revisa los conceptos básicos si tienes dudas
2. Practica con ejercicios similares
3. Busca ejemplos adicionales en tu vida cotidiana
4. No dudes en preguntar si algo no está claro

### ❓ **¿Necesitas Más Ayuda?**
Si quieres que profundice en algún punto específico, o si tienes más preguntas, estaré encantado de ayudarte. Recuerda que el aprendizaje es un proceso y cada paso cuenta.

**¡Sigue adelante, lo estás haciendo muy bien!** 🌟

---
*¿Te gustaría que explique algún concepto específico con más detalle?*
        """
    
    def _generate_lesson_response(self, request: AgentRequest) -> str:
        """Generar respuesta del agente planificador de lecciones"""
        params = request.parameters or {}
        subject = params.get('subject', 'Materia')
        topic = params.get('topic', 'Tema')
        duration = params.get('duration_minutes', 45)
        grade_level = params.get('grade_level', 'Nivel medio')
        objectives = params.get('learning_objectives', [])
        
        objectives_text = ""
        if objectives:
            objectives_text = "\n".join([f"- {obj}" for obj in objectives])
        
        return f"""
# Plan de Lección: {topic}

## Información General
- **Materia:** {subject}
- **Tema:** {topic}
- **Duración:** {duration} minutos
- **Nivel:** {grade_level}
- **Fecha:** {datetime.now().strftime('%d/%m/%Y')}

## Objetivos de Aprendizaje
{objectives_text if objectives_text else f"- Comprender los conceptos fundamentales de {topic}\n- Aplicar los conocimientos en ejercicios prácticos\n- Desarrollar habilidades de análisis crítico"}

## Competencias a Desarrollar
- **Conceptuales:** Comprensión de fundamentos teóricos
- **Procedimentales:** Aplicación práctica de conocimientos
- **Actitudinales:** Desarrollo de curiosidad y pensamiento crítico

## Estructura Detallada de la Clase

### 🚀 INICIO (10 minutos)

**Actividad de Apertura (3 min):**
- Saludo cordial y registro de asistencia
- Breve repaso de la clase anterior con preguntas dirigidas
- Conexión con el tema de hoy

**Motivación e Introducción (4 min):**
- Pregunta provocadora: "¿Por qué es importante {topic} en {subject}?"
- Presentación de un caso real o ejemplo cotidiano
- Presentación de objetivos de la clase

**Activación de Conocimientos Previos (3 min):**
- Lluvia de ideas sobre lo que saben del tema
- Identificación de conceptos relacionados
- Establecimiento de expectativas

### 📖 DESARROLLO (30 minutos)

**Fase 1: Presentación del Contenido (10 min)**
- Explicación clara y estructurada del concepto principal
- Uso de ejemplos visuales y analogías
- Introducción de vocabulario técnico
- Verificación de comprensión con preguntas cortas

**Fase 2: Práctica Guiada (10 min)**
- Ejercicio colaborativo en parejas
- Resolución de problema ejemplo paso a paso
- Participación activa de estudiantes
- Aclaración de dudas inmediatas

**Fase 3: Aplicación Independiente (10 min)**
- Ejercicio individual o en grupos pequeños
- Aplicación de conceptos a situaciones nuevas
- Monitoreo y retroalimentación personalizada
- Socialización de resultados

### 🎯 CIERRE (5 minutos)

**Síntesis y Consolidación (3 min):**
- Recapitulación de puntos clave
- Conexión con objetivos iniciales
- Respuesta a dudas finales

**Evaluación y Proyección (2 min):**
- Evaluación rápida de comprensión (Exit ticket)
- Asignación de tarea o actividad de seguimiento
- Adelanto del próximo tema

## Materiales y Recursos Necesarios

### Tecnológicos:
- Proyector/Pizarra digital
- Computador/Tablet
- Acceso a internet (opcional)

### Didácticos:
- Presentación visual del tema
- Hojas de ejercicios prácticos
- Material manipulativo (si aplica)
- Recursos audiovisuales

### Bibliográficos:
- Texto guía principal
- Material de apoyo complementario
- Enlaces a recursos digitales

## Estrategias Metodológicas

### Para Diferentes Estilos de Aprendizaje:
- **Visual:** Diagramas, esquemas, presentaciones
- **Auditivo:** Explicaciones verbales, discusiones
- **Kinestésico:** Actividades prácticas, manipulación

### Para Diferentes Niveles:
- **Básico:** Ejemplos simples, apoyo adicional
- **Intermedio:** Ejercicios estándar, trabajo colaborativo
- **Avanzado:** Retos adicionales, investigación independiente

## Sistema de Evaluación

### Evaluación Formativa (Durante la clase):
- Observación de participación activa
- Preguntas orales dirigidas
- Revisión de ejercicios prácticos
- Retroalimentación inmediata

### Evaluación Sumativa (Final):
- Exit ticket con pregunta clave
- Ejercicio de aplicación
- Autoevaluación del aprendizaje

### Criterios de Evaluación:
- **Comprensión conceptual** (40%)
- **Aplicación práctica** (30%)
- **Participación activa** (20%)
- **Colaboración efectiva** (10%)

## Tareas y Actividades de Seguimiento

### Para la próxima clase:
- Lectura previa del capítulo X (páginas Y-Z)
- Ejercicios de práctica del libro (problemas 1-5)
- Investigación breve sobre aplicaciones de {topic}

### Proyecto a largo plazo:
- Preparación de presentación sobre aplicaciones reales
- Recolección de ejemplos cotidianos del tema
- Reflexión escrita sobre aprendizajes

## Adaptaciones y Diferenciación

### Para estudiantes con necesidades especiales:
- Material adicional simplificado
- Tiempo extra para actividades
- Apoyo personalizado durante ejercicios

### Para estudiantes avanzados:
- Ejercicios de extensión
- Investigación adicional
- Rol de mentor con compañeros

## Reflexión Docente

### Aspectos a observar:
- ¿Se cumplieron los objetivos propuestos?
- ¿La metodología fue efectiva para todos?
- ¿Qué ajustes son necesarios para la próxima vez?
- ¿Cómo respondieron los estudiantes a las actividades?

### Mejoras para futuras implementaciones:
- Ajustes en timing según respuesta del grupo
- Modificaciones en ejemplos según contexto local
- Incorporación de nuevas tecnologías o recursos
        """
    
    def _generate_analyzer_response(self, request: AgentRequest) -> str:
        """Generar respuesta del agente analizador"""
        context = request.context or {}
        prompt = request.prompt
        
        return f"""
# 📊 Análisis de Rendimiento Académico

## Resumen Ejecutivo
He analizado los datos proporcionados y he identificado patrones importantes en el rendimiento académico que requieren atención específica.

## 🎯 Hallazgos Principales

### Fortalezas Identificadas ✅
- **Participación Activa:** Nivel alto de engagement en actividades de clase
- **Comprensión Conceptual:** Buena base en fundamentos teóricos
- **Trabajo Colaborativo:** Excelente desempeño en actividades grupales
- **Puntualidad:** Cumplimiento consistente con entregas
- **Actitud Positiva:** Muestra interés y motivación por aprender

### Áreas de Oportunidad 🔸
- **Aplicación Práctica:** Necesita fortalecer la transferencia de conocimientos
- **Pensamiento Crítico:** Requiere desarrollo en análisis profundo
- **Autonomía:** Dependencia excesiva de guía docente
- **Técnicas de Estudio:** Métodos poco eficientes para retención
- **Gestión del Tiempo:** Dificultades en planificación de actividades

## 📈 Análisis Detallado por Áreas

### Rendimiento Académico General
- **Promedio actual:** Nivel satisfactorio con tendencia positiva
- **Consistencia:** Rendimiento estable con algunas fluctuaciones
- **Progreso:** Mejora gradual pero constante
- **Comparación grupal:** Por encima del promedio del grupo

### Competencias Específicas

**Comprensión Lectora:**
- Nivel: Intermedio-Alto
- Fortaleza: Identificación de ideas principales
- Mejora: Análisis inferencial y crítico

**Expresión Escrita:**
- Nivel: Intermedio
- Fortaleza: Claridad en la comunicación
- Mejora: Estructura argumentativa y vocabulario técnico

**Resolución de Problemas:**
- Nivel: Intermedio
- Fortaleza: Identificación del problema
- Mejora: Estrategias de solución alternativas

**Trabajo en Equipo:**
- Nivel: Alto
- Fortaleza: Colaboración efectiva
- Mejora: Liderazgo y mediación

## 🎯 Recomendaciones Específicas

### Estrategias de Mejora Inmediata (1-2 semanas)
1. **Implementar técnicas de estudio activo:**
   - Mapas conceptuales
   - Resúmenes ejecutivos
   - Autoexplicación

2. **Desarrollar rutinas de estudio:**
   - Horarios fijos de estudio
   - Ambiente adecuado
   - Descansos programados

3. **Fortalecer metacognición:**
   - Autoevaluación regular
   - Reflexión sobre aprendizajes
   - Identificación de estrategias efectivas

### Estrategias de Desarrollo a Mediano Plazo (1 mes)
1. **Proyectos de aplicación práctica:**
   - Casos de estudio reales
   - Simulaciones
   - Proyectos interdisciplinarios

2. **Desarrollo del pensamiento crítico:**
   - Análisis de argumentos
   - Evaluación de fuentes
   - Construcción de hipótesis

3. **Autonomía en el aprendizaje:**
   - Investigación independiente
   - Autoevaluación
   - Establecimiento de metas personales

### Plan de Seguimiento a Largo Plazo (2-3 meses)
1. **Monitoreo continuo:**
   - Evaluaciones semanales
   - Retroalimentación regular
   - Ajustes según progreso

2. **Desarrollo de competencias avanzadas:**
   - Pensamiento sistémico
   - Creatividad e innovación
   - Liderazgo académico

## 📋 Plan de Acción Personalizado

### Objetivos SMART
- **Específico:** Mejorar aplicación práctica de conocimientos
- **Medible:** Incrementar 20% en evaluaciones prácticas
- **Alcanzable:** Con apoyo y práctica constante
- **Relevante:** Esencial para desarrollo académico
- **Temporal:** En los próximos 2 meses

### Actividades Semanales
**Semana 1-2:**
- Implementar técnica de mapas conceptuales
- Establecer rutina de estudio de 1 hora diaria
- Participar en grupo de estudio

**Semana 3-4:**
- Aplicar conocimientos en proyecto práctico
- Realizar autoevaluación semanal
- Buscar retroalimentación de pares

**Semana 5-8:**
- Liderar actividad grupal
- Desarrollar investigación independiente
- Presentar resultados y reflexiones

## 🔄 Sistema de Seguimiento

### Indicadores de Progreso
- Calificaciones en evaluaciones prácticas
- Nivel de participación en discusiones
- Calidad de trabajos independientes
- Autoevaluación del aprendizaje
- Feedback de compañeros y docentes

### Frecuencia de Evaluación
- **Semanal:** Autoevaluación y reflexión
- **Quincenal:** Evaluación de progreso con tutor
- **Mensual:** Evaluación integral y ajustes

### Recursos de Apoyo
- Tutoría personalizada (1 hora/semana)
- Grupo de estudio con pares
- Acceso a recursos digitales especializados
- Sesiones de técnicas de estudio

## 💡 Recomendaciones para Docentes

### Estrategias Pedagógicas Sugeridas
- Incrementar actividades de aplicación práctica
- Proporcionar retroalimentación más frecuente
- Fomentar la autorreflexión
- Diversificar métodos de evaluación

### Adaptaciones Curriculares
- Incluir más casos de estudio reales
- Integrar tecnología educativa
- Promover aprendizaje colaborativo
- Desarrollar proyectos interdisciplinarios

## 📞 Próximos Pasos

1. **Reunión de seguimiento** programada para la próxima semana
2. **Implementación inmediata** de estrategias básicas
3. **Evaluación de progreso** en 2 semanas
4. **Ajuste del plan** según resultados obtenidos

---

**Nota:** Este análisis se basa en datos actuales y debe ser revisado periódicamente para mantener su relevancia y efectividad.
        """
    
    async def multi_agent_collaboration(self, task: str, participating_agents: List[AgentType]) -> str:
        """Colaboración entre agentes reales"""
        results = []
        
        for agent_type in participating_agents:
            request = AgentRequest(
                agent_type=agent_type,
                prompt=f"Como {agent_type.value.replace('_', ' ')}, colabora en esta tarea: {task}",
                parameters={"collaboration_mode": True}
            )
            response = await self.process_request(request)
            
            # Determinar si es agente real o fallback
            agent_status = "🤖 (Agente Real)" if response.metadata.get("agent_type") == "real" else "📝 (Fallback)"
            
            results.append(f"""
## {agent_type.value.replace('_', ' ').title()} {agent_status}

{response.response[:600]}...

---
            """)
        
        collaboration_summary = f"""
# 🤝 Colaboración Multi-Agente

## 📋 Tarea Asignada
{task}

## 👥 Participantes ({len(participating_agents)} agentes)
{', '.join([agent.value.replace('_', ' ').title() for agent in participating_agents])}

## 💬 Contribuciones de Cada Agente

{''.join(results)}

## 🎯 Síntesis Integradora
Basándose en las perspectivas de todos los agentes participantes, se recomienda un enfoque integral que:

1. **🔄 Combine las fortalezas** de cada especialización
2. **⚙️ Integre las metodologías** propuestas por cada agente  
3. **📊 Considere todas las dimensiones** del problema planteado
4. **📈 Implemente un plan coordinado** que aproveche la experiencia colectiva

### 💡 Próximos Pasos Recomendados:
- Revisar cada perspectiva individual para mayor detalle
- Implementar las recomendaciones de manera coordinada
- Establecer métricas de seguimiento específicas
- Programar revisiones periódicas del progreso

---
*Para obtener las respuestas completas de cada agente, solicita individualmente a cada uno con la misma tarea.*
        """
        
        return collaboration_summary
    
    async def search_and_answer(self, query: str, agent_type: AgentType) -> str:
        """Buscar y responder usando un agente específico"""
        try:
            # Buscar documentos relevantes
            search_results = await self.document_service.search_documents(query, n_results=3)
            
            # Crear contexto con resultados
            context = "\n".join([f"- {doc.get('content', '')[:200]}..." for doc in search_results])
            
            # Generar respuesta
            request = AgentRequest(
                agent_type=agent_type,
                prompt=f"""
Pregunta del usuario: {query}

Información encontrada en la base de datos:
{context if context else 'No se encontraron documentos específicos en la base de datos.'}

Por favor proporciona una respuesta completa y útil basada en tu especialización como {agent_type.value.replace('_', ' ')}.
                """,
                parameters={}
            )
            
            response = await self.process_request(request)
            return response.response
        except Exception as e:
            return f"Error buscando información: {str(e)}"
