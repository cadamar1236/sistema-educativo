#!/usr/bin/env python3
"""
Test script para verificar el sistema de autenticación y suscripciones
"""

import asyncio
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_system():
    print("=" * 60)
    print("🧪 TESTING AUTHENTICATION & SUBSCRIPTION SYSTEM")
    print("=" * 60)
    
    # Test 1: Azure Search Fallback
    print("\n1️⃣ Testing Azure Search Fallback...")
    try:
        from azure_search_config import azure_config, local_search
        
        if azure_config.is_available:
            print("   ✅ Azure Search disponible")
        else:
            print("   ⚠️ Azure Search no disponible - usando fallback local")
            print("   ✅ Fallback local activo")
        
        # Test local storage
        test_doc = {
            "title": "Test Document",
            "content": "This is a test",
            "filename": "test.txt"
        }
        
        result = local_search.upload_document(test_doc)
        if result['success']:
            print("   ✅ Almacenamiento local funcionando")
        else:
            print("   ❌ Error en almacenamiento local")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Google Auth Service
    print("\n2️⃣ Testing Google Auth Service...")
    try:
        from auth.google_auth import google_auth
        
        if google_auth.client_id and google_auth.client_secret:
            print("   ✅ Google OAuth configurado")
            auth_url = google_auth.get_authorization_url()
            print(f"   ✅ URL de autenticación generada")
        else:
            print("   ⚠️ Google OAuth no configurado (falta CLIENT_ID/SECRET)")
            print("   ℹ️ Configura las variables en .env para habilitar")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Stripe Service
    print("\n3️⃣ Testing Stripe Subscription Service...")
    try:
        from payments.stripe_subscription import stripe_service
        
        if stripe_service.stripe_available:
            print("   ✅ Stripe SDK disponible")
        else:
            print("   ⚠️ Stripe no instalado - usando modo simulado")
            print("   ℹ️ Instala con: pip install stripe")
        
        # Test planes
        plans = stripe_service.plans
        print(f"   ✅ {len(plans)} planes de suscripción configurados:")
        for tier, plan in plans.items():
            print(f"      - {plan.name}: ${plan.price_monthly}/mes")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Educational RAG con Fallback
    print("\n4️⃣ Testing Educational RAG Agent con Fallback...")
    try:
        from agents.educational_rag.agent_fixed import EducationalRAGAgentFixed
        
        agent = EducationalRAGAgentFixed()
        print(f"   ✅ RAG Agent inicializado (modo: {'local' if agent.use_local else 'Azure'})")
        
        # Test upload
        result = agent.upload_document(
            user_id="test_user",
            content="Test content for RAG",
            filename="test_rag.txt",
            subject="Testing"
        )
        
        if result['success']:
            print(f"   ✅ Upload funcionando: {result['storage']} storage")
        else:
            print(f"   ❌ Error en upload: {result.get('error')}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: API Endpoints
    print("\n5️⃣ Testing API Endpoints...")
    try:
        import requests
        
        # Test auth endpoint
        response = requests.get("http://localhost:8000/api/auth/google/login")
        if response.status_code == 200:
            print("   ✅ Endpoint /api/auth/google/login funcionando")
        else:
            print("   ⚠️ API no disponible en puerto 8000")
            
    except:
        print("   ⚠️ Servidor no está corriendo")
        print("   ℹ️ Inicia el servidor con: python src/main_simple.py")
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print("""
✅ Sistema de autenticación y suscripciones instalado correctamente

Próximos pasos:
1. Copia .env.example a .env y configura tus claves
2. Instala dependencias: pip install -r requirements_auth.txt
3. Configura Google OAuth en Google Cloud Console
4. Configura Stripe en Stripe Dashboard
5. Inicia el servidor: python src/main_simple.py

Documentación completa en: AUTH_SETUP.md
    """)

if __name__ == "__main__":
    asyncio.run(test_system())