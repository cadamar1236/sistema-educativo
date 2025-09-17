#!/usr/bin/env python3
"""
Test rápido del formato de respuesta mejorado
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def patch_groq_client():
    """Patchea el cliente Groq para evitar el error de proxies"""
    try:
        import groq
        from groq._base_client import SyncHttpxClientWrapper
        
        original_init = SyncHttpxClientWrapper.__init__
        
        def patched_init(self, **kwargs):
            if 'proxies' in kwargs:
                del kwargs['proxies']
            return original_init(self, **kwargs)
        
        SyncHttpxClientWrapper.__init__ = patched_init
        return True
    except Exception:
        return False

def test_new_format():
    """Test del nuevo formato de respuesta"""
    print("🧪 Test del formato de respuesta mejorado...")
    
    if not patch_groq_client():
        print("❌ No se pudo aplicar patch")
        return False
    
    try:
        # Simular el método coach_student con el nuevo prompt
        from groq import Groq as GroqClient
        
        groq_api_key = os.getenv('GROQ_API_KEY')
        client = GroqClient(api_key=groq_api_key)
        
        # Nuevo prompt mejorado
        message = "¿Qué estrategias de estudio me recomiendas?"
        student_name = "María"
        
        coaching_prompt = f"""Eres un coach estudiantil experto y empático. Un estudiante llamado {student_name} te pregunta:

"{message}"

Responde SOLO con tu consejo de coaching. Incluye:
- Saludo empático y motivador
- Consejos específicos y accionables organizados claramente
- Estrategias de estudio relevantes
- Apoyo emocional cuando sea necesario

Usa un formato visual atractivo con:
- Títulos con emojis (##, ###)
- Listas numeradas o con viñetas
- **Texto en negrita** para puntos importantes
- Párrafos cortos y bien separados

Responde directamente como coach, NO repitas el prompt."""
        
        # Obtener respuesta
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": """Eres un Coach Estudiantil IA experto y empático.

FORMATO DE RESPUESTA:
- Responde DIRECTAMENTE como coach, no repitas prompts
- Usa formato markdown para mejor presentación
- Incluye emojis en títulos (## 🎯 Título)
- Organiza en secciones claras con espacios
- Usa listas numeradas o viñetas
- **Resalta puntos importantes en negrita**

SIEMPRE:
- Proporciona respuestas completas y útiles
- Ofrece pasos concretos
- Mantén un tono positivo
- Responde solo con el contenido del coaching, NO incluyas el prompt"""},
                {"role": "user", "content": coaching_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        # Aplicar filtros
        lines = content.split('\n')
        filtered_lines = []
        skip_prompt = False
        
        for line in lines:
            line_clean = line.strip().lower()
            # Detectar si es parte del prompt
            if any(prompt_indicator in line_clean for prompt_indicator in [
                'como coach estudiantil',
                'proporciona:',
                'responde solo con',
                'incluye:',
                'usa un formato',
                'responde directamente como coach'
            ]):
                skip_prompt = True
                continue
            
            # Si encontramos contenido real del coach, empezar a incluir
            if skip_prompt and (line_clean.startswith('¡') or 
                              line_clean.startswith('hola') or
                              line_clean.startswith('##') or
                              line_clean.startswith('me alegra')):
                skip_prompt = False
            
            if not skip_prompt:
                filtered_lines.append(line)
        
        filtered_content = '\n'.join(filtered_lines).strip()
        
        print(f"📊 Resultado del test:")
        print(f"   - Longitud original: {len(content)} caracteres")
        print(f"   - Longitud filtrada: {len(filtered_content)} caracteres")
        print(f"   - Contiene prompt: {'como coach estudiantil' in content.lower()}")
        print(f"   - Prompt filtrado: {'como coach estudiantil' in filtered_content.lower()}")
        print(f"   - Tiene formato markdown: {'##' in filtered_content or '**' in filtered_content}")
        
        print(f"\n📝 Respuesta filtrada:")
        print("=" * 60)
        print(filtered_content[:500] + "..." if len(filtered_content) > 500 else filtered_content)
        print("=" * 60)
        
        # Verificar si el filtro funciona
        if (len(filtered_content) > 200 and 
            'como coach estudiantil' not in filtered_content.lower() and
            ('##' in filtered_content or '**' in filtered_content)):
            print("✅ Formato mejorado funciona correctamente")
            return True
        else:
            print("❌ El formato necesita más ajustes")
            return False
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_new_format()
