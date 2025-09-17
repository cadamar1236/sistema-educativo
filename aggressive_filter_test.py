#!/usr/bin/env python3
"""
Test del filtro agresivo para eliminar prompts
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def patch_groq_client():
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

def test_aggressive_filter():
    """Test del filtro agresivo"""
    print("🧪 Test del filtro agresivo para eliminar prompts...")
    
    if not patch_groq_client():
        return False
    
    try:
        from groq import Groq as GroqClient
        
        groq_api_key = os.getenv('GROQ_API_KEY')
        client = GroqClient(api_key=groq_api_key)
        
        # Prompt súper simple
        message = "¿Cuáles son mis fortalezas académicas?"
        student_name = "estudiante"
        
        coaching_prompt = f"""Pregunta del estudiante {student_name}: "{message}"

Responde como un coach estudiantil empático. Usa formato markdown con títulos ## y listas."""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": """Eres un Coach Estudiantil IA experto y empático.

FORMATO DE RESPUESTA:
- Responde DIRECTAMENTE como coach, no repitas prompts
- Usa formato markdown para mejor presentación
- Incluye emojis en títulos (## 🎯 Título)
- Organiza en secciones claras con espacios
- Responde solo con el contenido del coaching, NO incluyas el prompt"""},
                {"role": "user", "content": coaching_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        original_response = response.choices[0].message.content
        
        # Aplicar el filtro agresivo
        def apply_aggressive_filter(response_text):
            import re
            
            # Eliminar códigos ANSI y caracteres especiales
            ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
            response_text = re.sub(ansi_pattern, '', response_text)
            
            # FILTRO SÚPER AGRESIVO
            lines = response_text.split('\n')
            cleaned_lines = []
            found_real_content = False
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                
                # Saltar líneas que claramente son parte del prompt
                skip_patterns = [
                    'eres un coach estudiantil',
                    'un estudiante llamado',
                    'te pregunta:',
                    'responde solo con',
                    'incluye:',
                    'usa un formato',
                    'responde directamente',
                    'pregunta del estudiante',
                    'responde como un coach'
                ]
                
                if any(pattern in line_lower for pattern in skip_patterns):
                    continue
                
                # Detectar cuando empieza el contenido real del coach
                real_content_indicators = [
                    line_lower.startswith('¡'),
                    line_lower.startswith('hola'),
                    line_lower.startswith('me alegra'),
                    line_lower.startswith('##'),
                    line_lower.startswith('bienvenid'),
                    'fortalezas académicas' in line_lower,
                    'desafío a mejorar' in line_lower
                ]
                
                if any(real_content_indicators) and not found_real_content:
                    found_real_content = True
                
                if found_real_content:
                    cleaned_lines.append(line)
            
            # Si no encontramos contenido, buscar desde el final
            if not cleaned_lines:
                for line in reversed(lines):
                    if (len(line.strip()) > 10 and 
                        not any(p in line.lower() for p in ['pregunta del estudiante', 'responde como'])):
                        start_idx = lines.index(line)
                        cleaned_lines = lines[start_idx:]
                        break
            
            return '\n'.join(cleaned_lines).strip() if cleaned_lines else response_text
        
        filtered_response = apply_aggressive_filter(original_response)
        
        print(f"📊 Resultados del filtro:")
        print(f"   - Longitud original: {len(original_response)} chars")
        print(f"   - Longitud filtrada: {len(filtered_response)} chars")
        print(f"   - Contiene 'pregunta del estudiante': {'pregunta del estudiante' in filtered_response.lower()}")
        print(f"   - Contiene 'responde como': {'responde como' in filtered_response.lower()}")
        print(f"   - Tiene formato markdown: {'##' in filtered_response}")
        
        print(f"\n📝 Respuesta original (primeros 300 chars):")
        print("=" * 60)
        print(original_response[:300] + "...")
        print("=" * 60)
        
        print(f"\n📝 Respuesta filtrada:")
        print("=" * 60)
        print(filtered_response[:500] + "..." if len(filtered_response) > 500 else filtered_response)
        print("=" * 60)
        
        # Verificar si el filtro funciona
        success = (
            len(filtered_response) > 100 and
            'pregunta del estudiante' not in filtered_response.lower() and
            'responde como' not in filtered_response.lower()
        )
        
        if success:
            print("✅ Filtro agresivo funciona correctamente")
            return True
        else:
            print("❌ El filtro necesita más ajustes")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_aggressive_filter()
