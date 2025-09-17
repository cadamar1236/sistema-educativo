#!/usr/bin/env python3
"""
Test directo del comportamiento del agente coach
Simula exactamente lo que pasa en producción
"""

import os
import sys
from io import StringIO
from contextlib import redirect_stdout
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_groq_raw():
    """Test de Groq sin Agno"""
    print("🧪 Test directo de Groq API...")
    
    try:
        from groq import Groq as GroqClient
        
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            print("❌ GROQ_API_KEY no encontrada")
            return False, ""
            
        client = GroqClient(api_key=groq_api_key)
        
        # Simular la consulta del coach
        system_prompt = """Eres un coach estudiantil experto y empático especializado en ayudar a estudiantes a alcanzar su máximo potencial académico y personal.

Tu personalidad:
- Motivador y alentador, pero realista
- Empático y comprensivo
- Práctico y orientado a resultados
- Adaptable al nivel y necesidades del estudiante

Siempre proporciona:
- Consejos específicos y accionables
- Estrategias personalizadas
- Motivación positiva
- Técnicas de estudio efectivas

Responde en español de manera clara y estructurada."""

        user_message = "¿Qué estrategias de estudio me recomiendas para mejorar en matemáticas?"
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        print(f"📊 Respuesta de Groq:")
        print(f"   - Longitud: {len(content)} caracteres")
        print(f"   - Contiene estrategias: {'estrategi' in content.lower()}")
        print(f"   - Preview: {content[:200]}...")
        
        if len(content) > 200:
            print("✅ Groq API funciona perfectamente")
            return True, content
        else:
            print("❌ Respuesta muy corta")
            return False, content
            
    except Exception as e:
        print(f"❌ Error con Groq: {e}")
        return False, ""

def test_capture_logic():
    """Test de la lógica de captura exacta del coach"""
    print("\n🧪 Test de la lógica de captura...")
    
    # Función exacta del coach
    def capture_agent_response(agent, message):
        import io
        import contextlib
        
        print(f"🎯 Intentando capturar respuesta para: {message[:50]}...")
        
        stdout_capture = io.StringIO()
        result = None
        
        try:
            with contextlib.redirect_stdout(stdout_capture):
                result = agent.print_response(message, stream=False)
            
            stdout_content = stdout_capture.getvalue()
            
            print(f"🔍 Análisis de captura:")
            print(f"   - Result type: {type(result)}, length: {len(str(result)) if result else 4}")
            print(f"   - Stdout length: {len(stdout_content)}")
            
            # Si result tiene contenido útil, úsalo
            if result and isinstance(result, str) and len(result.strip()) > 50:
                print("✅ Usando result directo")
                return result.strip()
            
            # Si no, usar stdout de manera súper agresiva
            if stdout_content:
                print("🏃‍♂️ Procesando stdout...")
                
                cleaned = stdout_content.strip()
                lines = cleaned.split('\n')
                while lines and not lines[0].strip():
                    lines.pop(0)
                while lines and not lines[-1].strip():
                    lines.pop()
                
                if lines:
                    final_content = '\n'.join(lines)
                    
                    if len(final_content) > 200:
                        print(f"🏃‍♂️ Found substantial content: {len(final_content)} chars")
                        return final_content
                    
                    if len(final_content) > 50 and any(keyword in final_content.lower() for keyword in 
                        ['recomend', 'consejo', 'estrategi', 'técnica', 'método', 'estudi', 'concentr', 'motiv']):
                        print(f"🏃‍♂️ Found relevant content: {len(final_content)} chars")
                        return final_content
            
            print("⚠️ No se encontró contenido válido, usando fallback")
            return "Como tu coach personal, te recomiendo establecer metas claras, crear un horario de estudio consistente y tomar descansos regulares. ¿En qué área específica te gustaría que te ayude?"
            
        except Exception as e:
            print(f"❌ Error en captura: {e}")
            return "Como tu coach personal, estoy aquí para ayudarte. ¿Podrías reformular tu pregunta?"
    
    # Agente simulado que hace exactamente lo que hace Groq
    class MockGroqAgent:
        def __init__(self, groq_response):
            self.groq_response = groq_response
            
        def print_response(self, message, stream=False):
            # Simular que imprime la respuesta de Groq pero devuelve None
            print(self.groq_response)
            return None
    
    # Obtener respuesta real de Groq
    groq_works, groq_content = test_groq_raw()
    
    if groq_works:
        # Test con respuesta real de Groq
        mock_agent = MockGroqAgent(groq_content)
        message = "¿Qué estrategias de estudio me recomiendas para mejorar en matemáticas?"
        
        captured = capture_agent_response(mock_agent, message)
        
        print(f"📊 Resultado de captura:")
        print(f"   - Longitud capturada: {len(captured)} caracteres")
        print(f"   - Es la respuesta de Groq: {captured == groq_content}")
        print(f"   - Es fallback: {'coach personal' in captured}")
        print(f"   - Preview: {captured[:200]}...")
        
        if len(captured) > 200 and not 'coach personal' in captured:
            print("✅ Captura funciona correctamente")
            return True
        else:
            print("❌ Captura no funciona correctamente")
            return False
    else:
        print("❌ No se puede testear captura sin respuesta de Groq")
        return False

def test_coach_simulation():
    """Simula el comportamiento completo del coach"""
    print("\n🧪 Simulación completa del coach...")
    
    try:
        from groq import Groq as GroqClient
        
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            print("❌ GROQ_API_KEY no encontrada")
            return False
            
        # Clase que simula StudentCoachAgent
        class SimulatedCoach:
            def __init__(self):
                self.groq_client = GroqClient(api_key=groq_api_key)
                
            async def coach_student(self, message, student_context):
                """Simula el método coach_student"""
                
                # Construir prompt como lo hace el coach real
                context_prompt = f"""
Información del estudiante:
- Nombre: {student_context.get('name', 'Estudiante')}
- Grado: {student_context.get('grade', 'No especificado')}
- Materia: {student_context.get('subject', 'General')}

Pregunta del estudiante: {message}
"""
                
                system_prompt = """Eres un coach estudiantil experto y empático especializado en ayudar a estudiantes a alcanzar su máximo potencial académico y personal.

Tu personalidad:
- Motivador y alentador, pero realista
- Empático y comprensivo
- Práctico y orientado a resultados
- Adaptable al nivel y necesidades del estudiante

Siempre proporciona:
- Consejos específicos y accionables
- Estrategias personalizadas
- Motivación positiva
- Técnicas de estudio efectivas

Responde en español de manera clara y estructurada."""
                
                try:
                    response = self.groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": context_prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.7
                    )
                    
                    content = response.choices[0].message.content
                    print(f"🤖 Coach respondió: {len(content)} caracteres")
                    return content
                    
                except Exception as e:
                    print(f"❌ Error en coach: {e}")
                    return "Como tu coach personal, estoy aquí para ayudarte. ¿Podrías reformular tu pregunta?"
        
        # Test del coach simulado
        coach = SimulatedCoach()
        
        test_context = {
            "name": "María",
            "grade": "10°",
            "subject": "Matemáticas"
        }
        
        import asyncio
        
        # Test 1
        response1 = asyncio.run(coach.coach_student(
            "¿Qué estrategias de estudio me recomiendas para mejorar en matemáticas?",
            test_context
        ))
        
        # Test 2
        response2 = asyncio.run(coach.coach_student(
            "Me siento desmotivado con mis estudios, ¿cómo puedo recuperar la motivación?",
            test_context
        ))
        
        print(f"\n📊 Resultados de la simulación:")
        print(f"Test 1 - Longitud: {len(response1)} chars, Fallback: {'coach personal' in response1}")
        print(f"Test 2 - Longitud: {len(response2)} chars, Fallback: {'coach personal' in response2}")
        
        success_count = 0
        if len(response1) > 200 and 'coach personal' not in response1:
            success_count += 1
        if len(response2) > 200 and 'coach personal' not in response2:
            success_count += 1
            
        print(f"\n🎯 Tasa de éxito: {success_count}/2 ({success_count*50}%)")
        
        if success_count >= 1:
            print("✅ Simulación del coach EXITOSA")
            return True
        else:
            print("❌ Simulación del coach FALLÓ")
            return False
            
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test principal"""
    print("🧪 TEST DIRECTO DEL COMPORTAMIENTO DEL COACH")
    print("=" * 60)
    
    # Test 1: Groq API
    groq_works, _ = test_groq_raw()
    
    # Test 2: Lógica de captura
    capture_works = test_capture_logic()
    
    # Test 3: Simulación completa
    simulation_works = test_coach_simulation()
    
    # Resumen final
    print("\n🏁 RESULTADO FINAL:")
    print("=" * 60)
    print(f"🔧 API Groq: {'✅ FUNCIONA' if groq_works else '❌ FALLA'}")
    print(f"📡 Captura: {'✅ FUNCIONA' if capture_works else '❌ FALLA'}")
    print(f"🤖 Coach completo: {'✅ FUNCIONA' if simulation_works else '❌ FALLA'}")
    
    if groq_works and capture_works and simulation_works:
        print("\n🎉 EL AGENTE COACH DEBERÍA FUNCIONAR PERFECTAMENTE")
        print("El problema puede estar en el deployment o en la autenticación.")
        return 0
    else:
        print("\n⚠️ HAY PROBLEMAS EN LOS COMPONENTES BÁSICOS")
        if groq_works:
            print("   - Groq API funciona, el problema está en la captura o integración")
        else:
            print("   - Problema fundamental con Groq API")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
