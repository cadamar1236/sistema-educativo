#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos PostgreSQL
"""

import asyncio
import asyncpg
import sys
import os
from datetime import datetime

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql://eduadmin:c1d2Papa1236.,@julialabs.postgres.database.azure.com:5432/sistema_educativo?sslmode=require"

async def test_database_connection():
    """Probar la conexión a la base de datos"""
    print("🧪 Probando conexión a la base de datos PostgreSQL...")
    print(f"📍 Host: julialabs.postgres.database.azure.com")
    print(f"🗄️ Database: sistema_educativo")
    print(f"👤 User: eduadmin")
    
    try:
        # Intentar conexión básica
        print("\n1️⃣ Probando conexión básica...")
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Conexión básica exitosa")
        
        # Probar consulta simple
        print("\n2️⃣ Probando consulta simple...")
        result = await conn.fetchval("SELECT version()")
        print(f"✅ PostgreSQL Version: {result}")
        
        # Probar permisos
        print("\n3️⃣ Probando permisos de creación de tablas...")
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS test_connection (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ Permisos de CREATE TABLE: OK")
            
            # Probar inserción
            print("\n4️⃣ Probando inserción de datos...")
            test_id = await conn.fetchval("""
                INSERT INTO test_connection (test_data) 
                VALUES ($1) 
                RETURNING id
            """, f"Test desde Python - {datetime.now()}")
            print(f"✅ Inserción exitosa: ID {test_id}")
            
            # Probar consulta
            print("\n5️⃣ Probando consulta de datos...")
            test_data = await conn.fetchrow("""
                SELECT * FROM test_connection WHERE id = $1
            """, test_id)
            print(f"✅ Consulta exitosa: {test_data['test_data']}")
            
            # Limpiar tabla de prueba
            await conn.execute("DROP TABLE IF EXISTS test_connection")
            print("✅ Limpieza exitosa")
            
        except Exception as perm_error:
            print(f"❌ Error de permisos: {perm_error}")
        
        await conn.close()
        
        # Probar con pool de conexiones
        print("\n6️⃣ Probando pool de conexiones...")
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=5,
            command_timeout=10
        )
        
        async with pool.acquire() as pool_conn:
            databases = await pool_conn.fetch("SELECT datname FROM pg_database WHERE datistemplate = false")
            print(f"✅ Pool funcionando. Databases disponibles: {[db['datname'] for db in databases]}")
        
        await pool.close()
        
        print("\n🎉 TODAS LAS PRUEBAS DE BASE DE DATOS EXITOSAS")
        return True
        
    except asyncpg.exceptions.InvalidPasswordError:
        print("❌ Error de autenticación: Contraseña incorrecta")
        return False
    except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
        print("❌ Error de autorización: Usuario no tiene permisos")
        return False
    except asyncpg.exceptions.CannotConnectNowError:
        print("❌ Error de conexión: El servidor no acepta conexiones")
        return False
    except asyncpg.exceptions.ConnectionDoesNotExistError:
        print("❌ Error de conexión: La base de datos no existe")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {type(e).__name__}: {e}")
        return False

async def test_coaching_service():
    """Probar el servicio de coaching database"""
    print("\n🧪 Probando servicio de coaching database...")
    
    try:
        from src.services.coaching_database_service import CoachingDatabaseService
        
        # Crear servicio
        coaching_db = CoachingDatabaseService(DATABASE_URL)
        await coaching_db.initialize()
        print("✅ Servicio de coaching inicializado")
        
        # Probar guardado de sesión
        test_session = {
            'student_id': 'test_user_123',
            'student_name': 'Usuario de Prueba',
            'student_message': '¿Cómo puedo mejorar mis estudios?',
            'coach_response': '## 🎯 Consejos para Mejorar\n\nTe recomiendo:\n1. Establecer horarios\n2. Hacer pausas\n3. Practicar regularmente',
            'emotional_state': 'motivated',
            'metadata': {
                'test': True,
                'timestamp': datetime.now().isoformat()
            },
            'intervention_needed': False
        }
        
        session_id = await coaching_db.save_coaching_session(test_session)
        print(f"✅ Sesión de prueba guardada: {session_id}")
        
        # Probar obtener historial
        history = await coaching_db.get_student_coaching_history('test_user_123', 10)
        print(f"✅ Historial obtenido: {len(history)} sesiones")
        
        # Probar estadísticas
        stats = await coaching_db.get_student_stats('test_user_123')
        print(f"✅ Estadísticas obtenidas: {stats['coaching_sessions'] if stats else 0} sesiones")
        
        # Probar analytics
        analytics = await coaching_db.get_coaching_analytics()
        print(f"✅ Analytics obtenidos: {analytics['total_sessions']} sesiones totales")
        
        await coaching_db.close()
        
        print("\n🎉 TODAS LAS PRUEBAS DEL SERVICIO DE COACHING EXITOSAS")
        return True
        
    except Exception as e:
        print(f"❌ Error en servicio de coaching: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal de pruebas"""
    print("🧪 PRUEBAS DE BASE DE DATOS Y SERVICIOS")
    print("=" * 60)
    
    # Test 1: Conexión básica
    db_success = await test_database_connection()
    
    # Test 2: Servicio de coaching (solo si la DB funciona)
    if db_success:
        coaching_success = await test_coaching_service()
    else:
        coaching_success = False
        print("\n⚠️ Saltando pruebas de coaching por error en DB")
    
    # Resumen final
    print("\n📊 RESUMEN DE PRUEBAS:")
    print("=" * 60)
    print(f"🗄️ Base de datos: {'✅ FUNCIONA' if db_success else '❌ FALLA'}")
    print(f"🤖 Servicio coaching: {'✅ FUNCIONA' if coaching_success else '❌ FALLA'}")
    
    if db_success and coaching_success:
        print("\n🎉 SISTEMA DE PERSISTENCIA LISTO PARA USAR")
        return 0
    else:
        print("\n⚠️ HAY PROBLEMAS QUE RESOLVER")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        sys.exit(2)
