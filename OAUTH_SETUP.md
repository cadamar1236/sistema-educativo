# 🚀 Guía Rápida: Solución al Error redirect_uri_mismatch

## 🚨 Problema
El error `redirect_uri_mismatch` ocurre cuando el URI de redirección configurado en tu aplicación no coincide con el registrado en Google Cloud Console.

## ✅ Solución Inmediata

### 1. Configurar la Variable de Entorno
```bash
# Desarrollo local
echo "GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback" >> .env

# Producción
echo "GOOGLE_REDIRECT_URI=https://tudominio.com/auth/callback" >> .env
```

### 2. Usar el Configurador Interactivo
```bash
python configure_oauth.py
```

### 3. Configurar Manualmente
Edita el archivo `.env` y actualiza:
```bash
GOOGLE_CLIENT_ID=tu_client_id_real
GOOGLE_CLIENT_SECRET=tu_client_secret_real
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback  # O tu dominio en producción
```

## 📋 Configuración en Google Cloud Console

### URIs de Redirección Permitidas
Registra estas URIs en Google Cloud Console > APIs & Services > Credentials:

```
# Desarrollo
http://localhost:8000/auth/callback
http://localhost:3000/auth/callback
http://127.0.0.1:8000/auth/callback

# Producción (actualiza con tu dominio)
https://tudominio.com/auth/callback
https://www.tudominio.com/auth/callback
```

### URIs de Origen Permitidas
```
http://localhost:8000
http://localhost:3000
https://tudominio.com
https://www.tudominio.com
```

## 🎯 Iniciar la Aplicación

### Desarrollo
```bash
# Opción 1: Usar el script de inicio
python start_server.py

# Opción 2: Usar uvicorn directamente
uvicorn src.main_simple:app --reload --host 0.0.0.0 --port 8000
```

### Producción
```bash
# Establecer variables de producción
export GOOGLE_REDIRECT_URI=https://tudominio.com/auth/callback
export ENVIRONMENT=production
python start_server.py
```

## 🔍 Verificación

1. **Verificar configuración actual:**
```bash
python configure_oauth.py
# Selecciona opción 1 para ver el estado
```

2. **Verificar URIs registradas:**
```bash
curl http://localhost:8000/api/auth/debug/config
```

3. **Probar autenticación:**
```bash
# Visita en tu navegador:
http://localhost:8000/api/auth/google/login
```

## 🔄 Flujo de Redirección Después del Login

Después de autenticarse exitosamente con Google:

1. Google redirige a: `http://localhost:8000/auth/callback`
2. La aplicación procesa el token
3. Redirección automática a: `/dashboard` (ya autenticado)

### Personalizar la Redirección
Puedes cambiar la URI de redirección con:
```bash
export GOOGLE_REDIRECT_URI=https://tudominio.com/auth/callback
```

## 🆘 Solución de Problemas

### Error Persistente
Si el error continúa:
1. Verifica que la URI exacta esté registrada en Google Cloud
2. Asegúrate de no tener espacios extra en las URLs
3. Comprueba que el puerto sea el correcto
4. Reinicia la aplicación después de cambios

### Verificar Variables de Entorno
```bash
# Ver variables actuales
python -c "import os; print('REDIRECT_URI:', os.getenv('GOOGLE_REDIRECT_URI'))"
```

## 🚀 Próximos Pasos
1. Obtén tus credenciales de Google Cloud Console
2. Configura las variables de entorno
3. Ejecuta el configurador interactivo
4. Inicia el servidor
5. ¡Listo para usar!