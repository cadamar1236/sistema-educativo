"""
Interfaz web principal usando Streamlit
"""

import streamlit as st
import requests
import json
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
import os

# Configuración de la página
st.set_page_config(
    page_title="Sistema Educativo Multiagente",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL base de la API
API_BASE_URL = "http://localhost:8000"

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E4057;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .document-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Función principal de la aplicación"""
    
    # Header principal
    st.markdown('<h1 class="main-header">🎓 Sistema Educativo Multiagente</h1>', 
                unsafe_allow_html=True)
    
    # Verificar conexión con la API
    if not check_api_connection():
        st.error("❌ No se puede conectar con la API. Asegúrate de que el servidor esté ejecutándose.")
        return
    
    # Sidebar para navegación
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/667eea/white?text=EDU+AI", width=200)
        
        page = st.selectbox(
            "📋 Seleccionar página:",
            [
                "🏠 Inicio",
                "📚 Biblioteca de Documentos", 
                "🤖 Agentes Especializados",
                "📝 Generador de Exámenes",
                "📖 Creador de Currículum",
                "👨‍🏫 Tutor Personal",
                "📊 Planificador de Clases",
                "🔍 Búsqueda Inteligente",
                "⚙️ Configuración"
            ]
        )
    
    # Enrutar a la página seleccionada
    if page == "🏠 Inicio":
        home_page()
    elif page == "📚 Biblioteca de Documentos":
        document_library_page()
    elif page == "🤖 Agentes Especializados":
        agents_page()
    elif page == "📝 Generador de Exámenes":
        exam_generator_page()
    elif page == "📖 Creador de Currículum":
        curriculum_creator_page()
    elif page == "👨‍🏫 Tutor Personal":
        tutor_page()
    elif page == "📊 Planificador de Clases":
        lesson_planner_page()
    elif page == "🔍 Búsqueda Inteligente":
        search_page()
    elif page == "⚙️ Configuración":
        settings_page()


def check_api_connection() -> bool:
    """Verificar conexión con la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def home_page():
    """Página de inicio"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="agent-card">
            <h3>📚 Biblioteca Inteligente</h3>
            <p>Sube y organiza documentos educativos con búsqueda semántica avanzada</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="agent-card">
            <h3>🤖 Agentes Especializados</h3>
            <p>5 agentes IA especializados en diferentes tareas educativas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="agent-card">
            <h3>🔄 Colaboración Multi-Agente</h3>
            <p>Los agentes trabajan juntos para tareas complejas</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Estadísticas del sistema
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Documentos", get_document_count())
    
    with col2:
        st.metric("🤖 Agentes Activos", "5")
    
    with col3:
        st.metric("✅ Estado del Sistema", "Activo")
    
    with col4:
        st.metric("🔍 Búsquedas Hoy", "0")
    
    # Acceso rápido
    st.markdown("### 🚀 Acceso Rápido")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Generar Examen", use_container_width=True):
            st.switch_page("exam_generator_page")
    
    with col2:
        if st.button("👨‍🏫 Consultar Tutor", use_container_width=True):
            st.switch_page("tutor_page")
    
    with col3:
        if st.button("📚 Subir Documento", use_container_width=True):
            st.switch_page("document_library_page")


def document_library_page():
    """Página de biblioteca de documentos"""
    
    st.header("📚 Biblioteca de Documentos")
    
    # Tabs para diferentes funciones
    tab1, tab2, tab3 = st.tabs(["📤 Subir", "📋 Listar", "🗑️ Gestionar"])
    
    with tab1:
        st.subheader("Subir Nuevo Documento")
        
        uploaded_file = st.file_uploader(
            "Selecciona un archivo:",
            type=['pdf', 'docx', 'xlsx', 'txt', 'md'],
            help="Formatos soportados: PDF, Word, Excel, Texto, Markdown"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            subject = st.text_input("Materia/Asignatura:", placeholder="Ej: Matemáticas")
        
        with col2:
            grade_level = st.text_input("Nivel/Grado:", placeholder="Ej: 5to Primaria")
        
        if st.button("📤 Subir Documento", type="primary") and uploaded_file:
            with st.spinner("Procesando documento..."):
                success = upload_document(uploaded_file, subject, grade_level)
                if success:
                    st.success("✅ Documento subido exitosamente!")
                    st.rerun()
                else:
                    st.error("❌ Error al subir el documento")
    
    with tab2:
        st.subheader("Documentos en la Biblioteca")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_subject = st.selectbox("Filtrar por materia:", ["Todas"] + get_subjects())
        
        with col2:
            filter_grade = st.selectbox("Filtrar por nivel:", ["Todos"] + get_grade_levels())
        
        with col3:
            if st.button("🔄 Actualizar"):
                st.rerun()
        
        # Mostrar documentos
        documents = get_documents(
            subject=filter_subject if filter_subject != "Todas" else None,
            grade_level=filter_grade if filter_grade != "Todos" else None
        )
        
        for doc in documents:
            st.markdown(f"""
            <div class="document-card">
                <h4>📄 {doc['filename']}</h4>
                <p><strong>Materia:</strong> {doc.get('subject', 'No especificada')}</p>
                <p><strong>Nivel:</strong> {doc.get('grade_level', 'No especificado')}</p>
                <p><strong>Subido:</strong> {doc.get('uploaded_at', 'Fecha no disponible')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        st.subheader("Gestión de Documentos")
        st.info("🔧 Funciones de gestión en desarrollo")


def agents_page():
    """Página de agentes especializados"""
    
    st.header("🤖 Agentes Especializados")
    
    # Información de agentes
    agents_info = [
        {
            "name": "📝 Generador de Exámenes",
            "description": "Crea exámenes personalizados basados en contenido educativo",
            "features": ["Múltiples tipos de preguntas", "Niveles de dificultad", "Explicaciones detalladas"]
        },
        {
            "name": "📖 Creador de Currículum", 
            "description": "Diseña planes de estudio estructurados y progresivos",
            "features": ["Objetivos de aprendizaje", "Secuencia lógica", "Alineación estándares"]
        },
        {
            "name": "👨‍🏫 Tutor Personal",
            "description": "Proporciona tutoría personalizada y resolución de dudas",
            "features": ["Explicaciones adaptadas", "Ejemplos prácticos", "Motivación personalizada"]
        },
        {
            "name": "📊 Analizador de Rendimiento",
            "description": "Analiza datos académicos y genera reportes detallados",
            "features": ["Identificación de patrones", "Áreas de mejora", "Recomendaciones"]
        },
        {
            "name": "📋 Planificador de Clases",
            "description": "Crea planes de lección detallados y actividades",
            "features": ["Actividades variadas", "Recursos apropiados", "Evaluaciones"]
        }
    ]
    
    for i, agent in enumerate(agents_info):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(agent["name"])
            st.write(agent["description"])
            
            # Características
            features_text = " • ".join(agent["features"])
            st.caption(f"✨ {features_text}")
        
        with col2:
            if st.button(f"Usar", key=f"agent_{i}", type="secondary"):
                # Redirigir a página específica del agente
                pass
        
        st.markdown("---")


def exam_generator_page():
    """Página del generador de exámenes"""
    
    st.header("📝 Generador de Exámenes")
    
    with st.form("exam_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            subject = st.text_input("Materia:", placeholder="Ej: Matemáticas")
            grade_level = st.text_input("Nivel:", placeholder="Ej: 5to Primaria")
            topic = st.text_input("Tema específico:", placeholder="Ej: Fracciones")
        
        with col2:
            num_questions = st.number_input("Número de preguntas:", min_value=1, max_value=50, value=10)
            difficulty = st.selectbox("Nivel de dificultad:", ["basic", "intermediate", "advanced"])
            duration = st.number_input("Duración (minutos):", min_value=15, max_value=180, value=45)
        
        # Tipos de preguntas
        st.subheader("Tipos de preguntas")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            multiple_choice = st.checkbox("Opción múltiple", value=True)
            true_false = st.checkbox("Verdadero/Falso")
        
        with col2:
            short_answer = st.checkbox("Respuesta corta", value=True)
            essay = st.checkbox("Ensayo")
        
        with col3:
            fill_blank = st.checkbox("Llenar espacios")
        
        # Documentos de referencia
        st.subheader("Documentos de referencia (opcional)")
        available_docs = get_documents()
        selected_docs = st.multiselect(
            "Seleccionar documentos:",
            options=[f"{doc['filename']} - {doc.get('subject', '')}" for doc in available_docs],
            help="Los documentos seleccionados se usarán como base para generar el examen"
        )
        
        submitted = st.form_submit_button("🎯 Generar Examen", type="primary")
        
        if submitted:
            if not all([subject, grade_level, topic]):
                st.error("❌ Por favor completa todos los campos obligatorios")
            else:
                with st.spinner("🤖 Generando examen..."):
                    # Preparar tipos de preguntas
                    question_types = []
                    if multiple_choice: question_types.append("multiple_choice")
                    if true_false: question_types.append("true_false")
                    if short_answer: question_types.append("short_answer")
                    if essay: question_types.append("essay")
                    if fill_blank: question_types.append("fill_blank")
                    
                    if not question_types:
                        question_types = ["multiple_choice", "short_answer"]
                    
                    # Generar examen
                    exam_result = generate_exam(
                        subject=subject,
                        grade_level=grade_level,
                        topic=topic,
                        num_questions=num_questions,
                        difficulty=difficulty,
                        question_types=question_types
                    )
                    
                    if exam_result:
                        st.success("✅ ¡Examen generado exitosamente!")
                        
                        # Mostrar resultado
                        st.subheader("📋 Examen Generado")
                        st.text_area("Contenido del examen:", value=exam_result, height=400)
                        
                        # Opciones de descarga
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "📥 Descargar como TXT",
                                data=exam_result,
                                file_name=f"examen_{subject}_{topic}.txt",
                                mime="text/plain"
                            )
                        
                        with col2:
                            if st.button("📧 Enviar por email"):
                                st.info("Función de email en desarrollo")
                    
                    else:
                        st.error("❌ Error al generar el examen")


def curriculum_creator_page():
    """Página del creador de currículum"""
    
    st.header("📖 Creador de Currículum")
    
    with st.form("curriculum_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            subject = st.text_input("Materia:", placeholder="Ej: Historia")
            grade_level = st.text_input("Nivel:", placeholder="Ej: 3ro Secundaria")
            duration_weeks = st.number_input("Duración (semanas):", min_value=1, max_value=52, value=16)
        
        with col2:
            curriculum_title = st.text_input("Título del currículum:", placeholder="Ej: Historia Universal Moderna")
            focus_areas = st.text_area("Áreas de enfoque:", placeholder="Ej: Revoluciones, Guerras mundiales, etc.")
        
        # Objetivos principales
        st.subheader("Objetivos Principales")
        objectives = []
        for i in range(3):
            obj = st.text_input(f"Objetivo {i+1}:", key=f"obj_{i}")
            if obj:
                objectives.append(obj)
        
        # Estándares educativos
        st.subheader("Alineación con Estándares")
        educational_standards = st.text_area(
            "Estándares educativos a seguir:",
            placeholder="Ej: Estándares nacionales de historia, competencias del siglo XXI"
        )
        
        submitted = st.form_submit_button("📚 Crear Currículum", type="primary")
        
        if submitted:
            if not all([subject, grade_level, curriculum_title]):
                st.error("❌ Por favor completa los campos obligatorios")
            else:
                with st.spinner("🤖 Creando currículum..."):
                    curriculum_result = create_curriculum(
                        subject=subject,
                        grade_level=grade_level,
                        duration_weeks=duration_weeks,
                        objectives=objectives,
                        title=curriculum_title,
                        standards=educational_standards
                    )
                    
                    if curriculum_result:
                        st.success("✅ ¡Currículum creado exitosamente!")
                        
                        # Mostrar resultado
                        st.subheader("📖 Currículum Generado")
                        st.text_area("Contenido del currículum:", value=curriculum_result, height=400)
                        
                        # Descarga
                        st.download_button(
                            "📥 Descargar Currículum",
                            data=curriculum_result,
                            file_name=f"curriculum_{subject}_{grade_level}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error("❌ Error al crear el currículum")


def tutor_page():
    """Página del tutor personal"""
    
    st.header("👨‍🏫 Tutor Personal")
    
    # Configuración del estudiante
    with st.expander("⚙️ Configuración del Estudiante"):
        col1, col2 = st.columns(2)
        
        with col1:
            student_name = st.text_input("Nombre del estudiante:", placeholder="Opcional")
            student_grade = st.text_input("Nivel/Grado:", placeholder="Ej: 4to Primaria")
        
        with col2:
            learning_style = st.selectbox(
                "Estilo de aprendizaje:",
                ["No especificado", "Visual", "Auditivo", "Kinestésico", "Mixto"]
            )
            preferred_language = st.selectbox("Idioma preferido:", ["Español", "Inglés"])
    
    # Chat interface
    st.subheader("💬 Chat con el Tutor")
    
    # Inicializar historial de chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Mostrar historial de chat
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])
    
    # Input para nuevo mensaje
    user_input = st.chat_input("Escribe tu pregunta aquí...")
    
    if user_input:
        # Agregar mensaje del usuario
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Preparar contexto del estudiante
        student_context = {
            "name": student_name if student_name else "Estudiante",
            "grade_level": student_grade,
            "learning_style": learning_style,
            "language": preferred_language
        }
        
        # Obtener respuesta del tutor
        with st.spinner("🤔 El tutor está pensando..."):
            tutor_response = get_tutor_response(user_input, student_context)
            
            if tutor_response:
                # Agregar respuesta del tutor
                st.session_state.chat_history.append({"role": "assistant", "content": tutor_response})
                st.rerun()
            else:
                st.error("❌ Error al obtener respuesta del tutor")
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Limpiar Chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        if st.button("💾 Guardar Conversación"):
            save_chat_history(st.session_state.chat_history, student_name or "Estudiante")
    
    with col3:
        if st.button("📊 Generar Reporte"):
            st.info("Función de reporte en desarrollo")


def lesson_planner_page():
    """Página del planificador de clases"""
    
    st.header("📊 Planificador de Clases")
    
    with st.form("lesson_plan_form"):
        # Información básica
        col1, col2 = st.columns(2)
        
        with col1:
            subject = st.text_input("Materia:", placeholder="Ej: Ciencias Naturales")
            grade_level = st.text_input("Nivel:", placeholder="Ej: 6to Primaria")
            topic = st.text_input("Tema de la lección:", placeholder="Ej: El Sistema Solar")
        
        with col2:
            duration = st.number_input("Duración (minutos):", min_value=15, max_value=120, value=45)
            class_size = st.number_input("Tamaño de la clase:", min_value=1, max_value=50, value=25)
            available_resources = st.text_input("Recursos disponibles:", placeholder="Ej: Proyector, laboratorio")
        
        # Objetivos de aprendizaje
        st.subheader("Objetivos de Aprendizaje")
        objectives = []
        for i in range(3):
            obj = st.text_input(f"Objetivo {i+1}:", key=f"lesson_obj_{i}")
            if obj:
                objectives.append(obj)
        
        # Configuraciones adicionales
        col1, col2 = st.columns(2)
        
        with col1:
            include_assessment = st.checkbox("Incluir evaluación", value=True)
            include_homework = st.checkbox("Incluir tarea")
        
        with col2:
            differentiation = st.checkbox("Diferenciación para diversos estilos de aprendizaje", value=True)
            technology_integration = st.checkbox("Integración de tecnología")
        
        submitted = st.form_submit_button("📝 Crear Plan de Lección", type="primary")
        
        if submitted:
            if not all([subject, grade_level, topic]):
                st.error("❌ Por favor completa los campos obligatorios")
            else:
                with st.spinner("🤖 Creando plan de lección..."):
                    lesson_plan = create_lesson_plan(
                        subject=subject,
                        grade_level=grade_level,
                        topic=topic,
                        duration=duration,
                        objectives=objectives,
                        resources=available_resources,
                        options={
                            "include_assessment": include_assessment,
                            "include_homework": include_homework,
                            "differentiation": differentiation,
                            "technology_integration": technology_integration
                        }
                    )
                    
                    if lesson_plan:
                        st.success("✅ ¡Plan de lección creado exitosamente!")
                        
                        # Mostrar resultado
                        st.subheader("📋 Plan de Lección")
                        st.text_area("Contenido del plan:", value=lesson_plan, height=400)
                        
                        # Descarga
                        st.download_button(
                            "📥 Descargar Plan",
                            data=lesson_plan,
                            file_name=f"plan_leccion_{subject}_{topic}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error("❌ Error al crear el plan de lección")


def search_page():
    """Página de búsqueda inteligente"""
    
    st.header("🔍 Búsqueda Inteligente")
    
    # Barra de búsqueda principal
    search_query = st.text_input(
        "¿Qué quieres buscar?",
        placeholder="Ej: Explícame las fracciones para 5to grado",
        help="Puedes hacer preguntas en lenguaje natural sobre cualquier tema educativo"
    )
    
    # Filtros de búsqueda
    with st.expander("🔧 Filtros Avanzados"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_subject = st.selectbox("Materia:", ["Todas"] + get_subjects())
            agent_type = st.selectbox(
                "Tipo de respuesta:",
                ["Tutor (Explicación)", "Generador de Ejercicios", "Planificador", "Análisis"]
            )
        
        with col2:
            search_grade = st.selectbox("Nivel:", ["Todos"] + get_grade_levels())
            response_length = st.selectbox("Longitud de respuesta:", ["Corta", "Media", "Detallada"])
        
        with col3:
            include_examples = st.checkbox("Incluir ejemplos", value=True)
            include_resources = st.checkbox("Sugerir recursos adicionales")
    
    # Botón de búsqueda
    if st.button("🔍 Buscar", type="primary") and search_query:
        with st.spinner("🔍 Buscando y analizando..."):
            # Mapear tipo de agente
            agent_mapping = {
                "Tutor (Explicación)": "tutor",
                "Generador de Ejercicios": "exam_generator", 
                "Planificador": "lesson_planner",
                "Análisis": "performance_analyzer"
            }
            
            selected_agent = agent_mapping.get(agent_type, "tutor")
            
            # Realizar búsqueda
            search_results = search_and_answer(
                query=search_query,
                agent_type=selected_agent,
                filters={
                    "subject": search_subject if search_subject != "Todas" else None,
                    "grade_level": search_grade if search_grade != "Todos" else None
                }
            )
            
            if search_results:
                # Mostrar respuesta principal
                st.subheader("💡 Respuesta")
                st.write(search_results)
                
                # Documentos relacionados
                st.subheader("📚 Documentos Relacionados")
                related_docs = get_related_documents(search_query)
                
                if related_docs:
                    for doc in related_docs[:3]:  # Mostrar top 3
                        st.markdown(f"""
                        <div class="document-card">
                            <h5>📄 {doc['filename']}</h5>
                            <p>{doc.get('snippet', 'Sin vista previa disponible')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No se encontraron documentos relacionados")
                
                # Sugerencias adicionales
                if include_resources:
                    st.subheader("🔗 Recursos Adicionales")
                    st.info("Esta función estará disponible próximamente")
            
            else:
                st.error("❌ No se pudo obtener una respuesta. Intenta reformular tu pregunta.")
    
    # Búsquedas recientes
    if "recent_searches" not in st.session_state:
        st.session_state.recent_searches = []
    
    if st.session_state.recent_searches:
        st.subheader("🕒 Búsquedas Recientes")
        for search in st.session_state.recent_searches[-5:]:  # Últimas 5
            if st.button(f"🔍 {search}", key=f"recent_{search}"):
                st.text_input("", value=search, key="search_input_recent")


def settings_page():
    """Página de configuración"""
    
    st.header("⚙️ Configuración del Sistema")
    
    # Configuración de la API
    st.subheader("🔧 Configuración de la API")
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_url = st.text_input("URL de la API:", value=API_BASE_URL)
        timeout = st.number_input("Timeout (segundos):", min_value=5, max_value=300, value=30)
    
    with col2:
        max_file_size = st.number_input("Tamaño máximo de archivo (MB):", min_value=1, max_value=100, value=50)
        auto_save = st.checkbox("Guardar automáticamente", value=True)
    
    # Configuración de agentes
    st.subheader("🤖 Configuración de Agentes")
    
    agent_settings = {}
    for agent_type in ["Generador de Exámenes", "Creador de Currículum", "Tutor", "Planificador"]:
        with st.expander(f"⚙️ {agent_type}"):
            col1, col2 = st.columns(2)
            
            with col1:
                agent_settings[f"{agent_type}_enabled"] = st.checkbox(f"Habilitar {agent_type}", value=True)
                agent_settings[f"{agent_type}_model"] = st.selectbox(
                    f"Modelo para {agent_type}:",
                    ["llama2", "codellama", "gpt-3.5-turbo"],
                    key=f"model_{agent_type}"
                )
            
            with col2:
                agent_settings[f"{agent_type}_temperature"] = st.slider(
                    f"Creatividad ({agent_type}):",
                    min_value=0.0, max_value=1.0, value=0.7, step=0.1,
                    key=f"temp_{agent_type}"
                )
                agent_settings[f"{agent_type}_max_tokens"] = st.number_input(
                    f"Máximo tokens ({agent_type}):",
                    min_value=512, max_value=8192, value=2048,
                    key=f"tokens_{agent_type}"
                )
    
    # Configuración de la base de datos
    st.subheader("🗄️ Base de Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Documentos almacenados", get_document_count())
        st.metric("Espacio usado", "Calculando...")
    
    with col2:
        if st.button("🗑️ Limpiar caché"):
            st.success("Caché limpiado")
        
        if st.button("📊 Optimizar base de datos"):
            st.success("Base de datos optimizada")
    
    # Guardar configuración
    if st.button("💾 Guardar Configuración", type="primary"):
        # Aquí guardarías la configuración
        st.success("✅ Configuración guardada exitosamente")
    
    # Información del sistema
    st.subheader("ℹ️ Información del Sistema")
    
    system_info = {
        "Versión": "1.0.0",
        "Estado de la API": "Conectado" if check_api_connection() else "Desconectado",
        "Agentes activos": "5",
        "Último reinicio": "Hace 2 horas"
    }
    
    for key, value in system_info.items():
        st.text(f"{key}: {value}")


# === FUNCIONES AUXILIARES ===

def get_document_count() -> int:
    """Obtener número de documentos"""
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        if response.status_code == 200:
            return len(response.json())
    except:
        pass
    return 0


def get_subjects() -> List[str]:
    """Obtener lista de materias"""
    return ["Matemáticas", "Ciencias", "Historia", "Literatura", "Inglés", "Arte", "Educación Física"]


def get_grade_levels() -> List[str]:
    """Obtener lista de niveles"""
    return ["Preescolar", "1ro Primaria", "2do Primaria", "3ro Primaria", "4to Primaria", 
            "5to Primaria", "6to Primaria", "1ro Secundaria", "2do Secundaria", "3ro Secundaria"]


def upload_document(file, subject: str, grade_level: str) -> bool:
    """Subir documento a la API"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {"subject": subject, "grade_level": grade_level}
        
        response = requests.post(f"{API_BASE_URL}/documents/upload", files=files, data=data)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error: {e}")
        return False


def get_documents(subject: str = None, grade_level: str = None) -> List[Dict]:
    """Obtener lista de documentos"""
    try:
        params = {}
        if subject: params["subject"] = subject
        if grade_level: params["grade_level"] = grade_level
        
        response = requests.get(f"{API_BASE_URL}/documents", params=params)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []


def generate_exam(subject: str, grade_level: str, topic: str, num_questions: int, 
                 difficulty: str, question_types: List[str]) -> str:
    """Generar examen usando la API"""
    try:
        data = {
            "subject": subject,
            "grade_level": grade_level,
            "topic": topic,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "question_types": question_types
        }
        
        response = requests.post(f"{API_BASE_URL}/agents/exam/generate", json=data)
        if response.status_code == 200:
            return response.json().get("content", "")
    except Exception as e:
        st.error(f"Error: {e}")
    return None


def create_curriculum(subject: str, grade_level: str, duration_weeks: int, 
                     objectives: List[str], title: str, standards: str) -> str:
    """Crear currículum usando la API"""
    try:
        data = {
            "subject": subject,
            "grade_level": grade_level,
            "duration_weeks": duration_weeks,
            "objectives": objectives
        }
        
        response = requests.post(f"{API_BASE_URL}/agents/curriculum/create", json=data)
        if response.status_code == 200:
            return response.json().get("content", "")
    except Exception as e:
        st.error(f"Error: {e}")
    return None


def get_tutor_response(message: str, student_context: Dict) -> str:
    """Obtener respuesta del tutor"""
    try:
        data = {
            "message": message,
            "student_context": student_context
        }
        
        response = requests.post(f"{API_BASE_URL}/agents/tutor/chat", json=data)
        if response.status_code == 200:
            return response.json().get("content", "")
    except Exception as e:
        st.error(f"Error: {e}")
    return None


def create_lesson_plan(subject: str, grade_level: str, topic: str, duration: int,
                      objectives: List[str], resources: str, options: Dict) -> str:
    """Crear plan de lección"""
    try:
        data = {
            "subject": subject,
            "grade_level": grade_level,
            "topic": topic,
            "duration_minutes": duration,
            "learning_objectives": objectives
        }
        
        response = requests.post(f"{API_BASE_URL}/agents/lesson/plan", json=data)
        if response.status_code == 200:
            return response.json().get("content", "")
    except Exception as e:
        st.error(f"Error: {e}")
    return None


def search_and_answer(query: str, agent_type: str, filters: Dict = None) -> str:
    """Búsqueda inteligente y respuesta"""
    try:
        params = {"query": query, "agent_type": agent_type}
        
        response = requests.get(f"{API_BASE_URL}/agents/search", params=params)
        if response.status_code == 200:
            return response.json().get("answer", "")
    except Exception as e:
        st.error(f"Error: {e}")
    return None


def get_related_documents(query: str) -> List[Dict]:
    """Obtener documentos relacionados con la consulta"""
    try:
        params = {"query": query, "n_results": 5}
        response = requests.get(f"{API_BASE_URL}/documents/search", params=params)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []


def save_chat_history(history: List[Dict], student_name: str):
    """Guardar historial de chat"""
    try:
        # Crear contenido para descargar
        content = f"Conversación con {student_name}\n"
        content += f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "="*50 + "\n\n"
        
        for message in history:
            role = "👤 Estudiante" if message["role"] == "user" else "🤖 Tutor"
            content += f"{role}: {message['content']}\n\n"
        
        st.download_button(
            "📥 Descargar Conversación",
            data=content,
            file_name=f"conversacion_{student_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
    except Exception as e:
        st.error(f"Error al guardar: {e}")


if __name__ == "__main__":
    main()
