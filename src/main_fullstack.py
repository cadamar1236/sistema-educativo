"""
API fullstack: Backend FastAPI + Frontend Next.js integrados
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from pathlib import Path

# Importar tu API principal
from src.main import app as backend_app

# Crear nueva app fullstack
app = FastAPI(
    title="Sistema Educativo Fullstack",
    description="Backend FastAPI + Frontend Next.js integrados",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths del frontend
FRONTEND_DIR = Path(__file__).parent / "frontend"
NEXT_BUILD_DIR = FRONTEND_DIR / ".next"
NEXT_STATIC_DIR = NEXT_BUILD_DIR / "static"
PUBLIC_DIR = FRONTEND_DIR / "public"

# Montar archivos estáticos del frontend Next.js
if NEXT_STATIC_DIR.exists():
    app.mount("/_next/static", StaticFiles(directory=str(NEXT_STATIC_DIR)), name="next-static")

if PUBLIC_DIR.exists():
    app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")

# Incluir todas las rutas de la API backend con prefijo /api
app.mount("/api", backend_app)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fullstack"}

@app.get("/api/health")
async def api_health_check():
    """API Health check endpoint"""
    return {"status": "healthy", "service": "backend"}

# Endpoint para servir el frontend Next.js
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_frontend(request: Request, full_path: str):
    """
    Sirve el frontend Next.js para todas las rutas no-API
    """
    # Si es una ruta de API, no manejarla aquí
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Archivos estáticos específicos
    if full_path.startswith("_next/"):
        file_path = FRONTEND_DIR / full_path
        if file_path.exists():
            return FileResponse(file_path)
        raise HTTPException(status_code=404, detail="Static file not found")
    
    # Servir index.html para rutas SPA (Single Page Application)
    index_path = FRONTEND_DIR / "out" / "index.html"
    
    # Si no existe out/index.html, usar .next/server/pages/index.html
    if not index_path.exists():
        index_path = NEXT_BUILD_DIR / "server" / "pages" / "index.html"
    
    # Si tampoco existe, crear un HTML básico
    if not index_path.exists():
        return HTMLResponse(content=create_fallback_html(), status_code=200)
    
    try:
        return FileResponse(index_path)
    except Exception as e:
        return HTMLResponse(content=create_fallback_html(), status_code=200)

def create_fallback_html():
    """
    HTML básico de fallback si no se encuentra el build de Next.js
    """
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema Educativo</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: white;
                border-radius: 10px;
                padding: 2rem;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 500px;
            }
            .status {
                color: #28a745;
                font-size: 1.2em;
                margin-bottom: 1rem;
            }
            .links {
                margin-top: 2rem;
            }
            .links a {
                display: inline-block;
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                margin: 0 10px;
                transition: background 0.3s;
            }
            .links a:hover {
                background: #0056b3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎓 Sistema Educativo</h1>
            <div class="status">✅ Backend funcionando correctamente</div>
            <p>El frontend se está inicializando...</p>
            <div class="links">
                <a href="/api/docs">📚 API Docs</a>
                <a href="/api/health">🔍 Health Check</a>
            </div>
            <script>
                // Auto-refresh cada 5 segundos hasta que el frontend esté listo
                setTimeout(() => {
                    fetch('/api/health')
                        .then(() => window.location.reload())
                        .catch(() => window.location.reload());
                }, 5000);
            </script>
        </div>
    </body>
    </html>
    """

# Para ejecutar directamente
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "src.main_fullstack:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1
    )
