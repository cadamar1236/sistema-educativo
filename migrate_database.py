#!/usr/bin/env python3
"""
Script para migrar/actualizar la estructura de las tablas de coaching
"""

import asyncio
import asyncpg
import sys
import os

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql://eduadmin:c1d2Papa1236.,@julialabs.postgres.database.azure.com:5432/sistema_educativo?sslmode=require"

async def migrate_database():
    """Migrar la estructura de la base de datos"""
    print("🔄 MIGRANDO ESTRUCTURA DE BASE DE DATOS...")
    print("=" * 60)
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # 1. Verificar estructura actual
        print("\n1️⃣ Verificando estructura actual...")
        
        # Verificar si existen las tablas
        tables_check = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('coaching_sessions', 'student_stats')
        """)
        
        existing_tables = [row['table_name'] for row in tables_check]
        print(f"✅ Tablas existentes: {existing_tables}")
        
        # 2. Verificar columnas de student_stats
        if 'student_stats' in existing_tables:
            print("\n2️⃣ Verificando columnas de student_stats...")
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'student_stats'
                ORDER BY ordinal_position
            """)
            
            column_names = [col['column_name'] for col in columns]
            print(f"📋 Columnas actuales: {column_names}")
            
            # Verificar si falta student_name
            if 'student_name' not in column_names:
                print("⚠️ Columna student_name no existe, agregándola...")
                await conn.execute("""
                    ALTER TABLE student_stats 
                    ADD COLUMN IF NOT EXISTS student_name VARCHAR(255) NOT NULL DEFAULT 'Unknown User'
                """)
                print("✅ Columna student_name agregada")
            else:
                print("✅ Columna student_name ya existe")
        
        # 3. Recrear tablas si es necesario
        print("\n3️⃣ Verificando/creando estructura completa...")
        
        # Coaching sessions
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS coaching_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                student_id VARCHAR(255) NOT NULL,
                student_name VARCHAR(255) NOT NULL,
                student_message TEXT NOT NULL,
                coach_response TEXT NOT NULL,
                emotional_state VARCHAR(50) DEFAULT 'neutral',
                session_metadata JSONB DEFAULT '{}',
                intervention_needed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Tabla coaching_sessions verificada")

        # Student stats
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS student_stats (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                student_id VARCHAR(255) UNIQUE NOT NULL,
                student_name VARCHAR(255) NOT NULL DEFAULT 'Unknown User',
                total_sessions INTEGER DEFAULT 0,
                coaching_sessions INTEGER DEFAULT 0,
                last_activity TIMESTAMP WITH TIME ZONE,
                emotional_trend JSONB DEFAULT '[]',
                intervention_alerts INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        print("✅ Tabla student_stats verificada")

        # 4. Crear índices
        print("\n4️⃣ Creando índices...")
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_coaching_sessions_student_id 
            ON coaching_sessions(student_id);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_coaching_sessions_created_at 
            ON coaching_sessions(created_at);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_student_stats_student_id 
            ON student_stats(student_id);
        """)
        print("✅ Índices creados")

        # 5. Verificar estructura final
        print("\n5️⃣ Verificando estructura final...")
        
        final_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'student_stats'
            ORDER BY ordinal_position
        """)
        
        print("📊 Estructura final de student_stats:")
        for col in final_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   - {col['column_name']}: {col['data_type']} {nullable} {default}")
        
        await conn.close()
        
        print("\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_after_migration():
    """Probar el servicio después de la migración"""
    print("\n🧪 PROBANDO SERVICIO DESPUÉS DE MIGRACIÓN...")
    print("=" * 60)
    
    try:
        from src.services.coaching_database_service import CoachingDatabaseService
        
        # Crear servicio
        coaching_db = CoachingDatabaseService(DATABASE_URL)
        await coaching_db.initialize()
        print("✅ Servicio inicializado correctamente")
        
        # Probar guardado de sesión
        test_session = {
            'student_id': 'test_migration_123',
            'student_name': 'Usuario Migración',
            'student_message': '¿Cómo funciona después de la migración?',
            'coach_response': '## 🚀 Post-Migración\n\n¡Todo funciona perfectamente!',
            'emotional_state': 'confident',
            'metadata': {
                'migration_test': True,
                'version': '2.0'
            },
            'intervention_needed': False
        }
        
        session_id = await coaching_db.save_coaching_session(test_session)
        print(f"✅ Sesión guardada exitosamente: {session_id}")
        
        # Probar consultas
        history = await coaching_db.get_student_coaching_history('test_migration_123', 5)
        print(f"✅ Historial recuperado: {len(history)} sesiones")
        
        stats = await coaching_db.get_student_stats('test_migration_123')
        print(f"✅ Estadísticas: {stats['coaching_sessions'] if stats else 0} sesiones")
        
        analytics = await coaching_db.get_coaching_analytics()
        print(f"✅ Analytics: {analytics['total_sessions']} sesiones totales")
        
        await coaching_db.close()
        
        print("\n🎉 TODAS LAS PRUEBAS POST-MIGRACIÓN EXITOSAS")
        return True
        
    except Exception as e:
        print(f"❌ Error en pruebas post-migración: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal"""
    print("🔄 MIGRACIÓN Y PRUEBAS DE BASE DE DATOS")
    print("=" * 60)
    
    # Paso 1: Migrar
    migration_success = await migrate_database()
    
    # Paso 2: Probar
    if migration_success:
        test_success = await test_after_migration()
    else:
        test_success = False
        print("\n⚠️ Saltando pruebas por error en migración")
    
    # Resumen
    print("\n📊 RESUMEN FINAL:")
    print("=" * 60)
    print(f"🔄 Migración: {'✅ EXITOSA' if migration_success else '❌ FALLÓ'}")
    print(f"🧪 Pruebas: {'✅ EXITOSAS' if test_success else '❌ FALLARON'}")
    
    if migration_success and test_success:
        print("\n🎉 BASE DE DATOS LISTA PARA PRODUCCIÓN")
        return 0
    else:
        print("\n⚠️ REVISAR ERRORES ANTES DE CONTINUAR")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Migración interrumpida")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        sys.exit(2)
