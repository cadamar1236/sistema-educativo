#!/usr/bin/env python3
"""
Script para adaptar completamente la estructura de student_stats
"""

import asyncio
import asyncpg

DATABASE_URL = "postgresql://eduadmin:c1d2Papa1236.,@julialabs.postgres.database.azure.com:5432/sistema_educativo?sslmode=require"

async def fix_student_stats_table():
    """Adaptar la tabla student_stats para coaching"""
    print("🔧 ADAPTANDO TABLA STUDENT_STATS PARA COACHING...")
    print("=" * 60)
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # 1. Ver estructura actual
        print("\n1️⃣ Estructura actual de student_stats:")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'student_stats'
            ORDER BY ordinal_position
        """)
        
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   - {col['column_name']}: {col['data_type']} {nullable} {default}")
        
        existing_columns = [col['column_name'] for col in columns]
        
        # 2. Agregar columnas faltantes para coaching
        print("\n2️⃣ Agregando columnas faltantes...")
        
        coaching_columns = {
            'total_sessions': 'INTEGER DEFAULT 0',
            'coaching_sessions': 'INTEGER DEFAULT 0', 
            'last_activity': 'TIMESTAMP WITH TIME ZONE',
            'emotional_trend': 'JSONB DEFAULT \'[]\'',
            'intervention_alerts': 'INTEGER DEFAULT 0'
        }
        
        for col_name, col_definition in coaching_columns.items():
            if col_name not in existing_columns:
                print(f"   ➕ Agregando {col_name}...")
                await conn.execute(f"""
                    ALTER TABLE student_stats 
                    ADD COLUMN {col_name} {col_definition}
                """)
                print(f"   ✅ Columna {col_name} agregada")
            else:
                print(f"   ✅ Columna {col_name} ya existe")
        
        # 3. Verificar estructura final
        print("\n3️⃣ Estructura final de student_stats:")
        final_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'student_stats'
            ORDER BY ordinal_position
        """)
        
        for col in final_columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   - {col['column_name']}: {col['data_type']} {nullable} {default}")
        
        await conn.close()
        
        print("\n🎉 ADAPTACIÓN COMPLETADA")
        return True
        
    except Exception as e:
        print(f"❌ Error adaptando tabla: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_coaching_service_fixed():
    """Probar el servicio con la tabla adaptada"""
    print("\n🧪 PROBANDO SERVICIO CON TABLA ADAPTADA...")
    print("=" * 60)
    
    try:
        from src.services.coaching_database_service import CoachingDatabaseService
        
        # Crear servicio
        coaching_db = CoachingDatabaseService(DATABASE_URL)
        await coaching_db.initialize()
        print("✅ Servicio inicializado")
        
        # Probar guardado de sesión
        test_session = {
            'student_id': 'test_fixed_123',
            'student_name': 'Usuario Tabla Adaptada',
            'student_message': '¿Funciona con la tabla adaptada?',
            'coach_response': '## 🔧 Tabla Adaptada\n\n¡Sí, funciona perfectamente!',
            'emotional_state': 'excited',
            'metadata': {
                'table_fixed': True,
                'test_type': 'adapted_structure'
            },
            'intervention_needed': False
        }
        
        session_id = await coaching_db.save_coaching_session(test_session)
        print(f"✅ Sesión guardada: {session_id}")
        
        # Probar consultas
        history = await coaching_db.get_student_coaching_history('test_fixed_123', 5)
        print(f"✅ Historial: {len(history)} sesiones")
        
        stats = await coaching_db.get_student_stats('test_fixed_123')
        print(f"✅ Estadísticas obtenidas:")
        if stats:
            for key, value in stats.items():
                print(f"   - {key}: {value}")
        
        analytics = await coaching_db.get_coaching_analytics()
        print(f"✅ Analytics: {analytics['total_sessions']} sesiones totales")
        
        await coaching_db.close()
        
        print("\n🎉 TODAS LAS PRUEBAS EXITOSAS")
        return True
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal"""
    print("🔧 ADAPTACIÓN DE TABLA STUDENT_STATS")
    print("=" * 60)
    
    # Paso 1: Adaptar tabla
    fix_success = await fix_student_stats_table()
    
    # Paso 2: Probar servicio
    if fix_success:
        test_success = await test_coaching_service_fixed()
    else:
        test_success = False
    
    # Resumen
    print("\n📊 RESUMEN:")
    print("=" * 60)
    print(f"🔧 Adaptación: {'✅ EXITOSA' if fix_success else '❌ FALLÓ'}")
    print(f"🧪 Pruebas: {'✅ EXITOSAS' if test_success else '❌ FALLARON'}")
    
    if fix_success and test_success:
        print("\n🎉 SISTEMA DE COACHING COMPLETAMENTE FUNCIONAL")
        return 0
    else:
        print("\n⚠️ REVISAR ERRORES")
        return 1

if __name__ == "__main__":
    asyncio.run(main())
