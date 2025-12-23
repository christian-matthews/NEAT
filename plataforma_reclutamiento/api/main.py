"""
The Wingman API Gateway
=======================

API REST moderna para la plataforma de reclutamiento The Wingman.
Integra el motor de evaluación de candidatos con Airtable.

Ejecutar con:
    uvicorn api.main:app --reload --port 8000
    
O:
    python -m api.main
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import os
import sys
from pathlib import Path
import urllib.parse

# Asegurar que el engine esté en el path
engine_path = Path(__file__).parent.parent
sys.path.insert(0, str(engine_path))

from .routes import (
    candidates_router,
    processes_router,
    evaluations_router,
    config_router,
    auth_router,
    applications_router,
    cargos_router
)


# ============================================================================
# App Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para la app."""
    # Startup
    print("🚀 The Wingman API starting...")
    
    # Verificar variables de entorno
    required_env = ["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID"]
    missing = [v for v in required_env if not os.getenv(v)]
    
    if missing:
        print(f"⚠️  Variables de entorno faltantes: {missing}")
        print("   Algunas funcionalidades estarán deshabilitadas.")
    else:
        print("✅ Conexión a Airtable configurada")
    
    print("✅ Motor de evaluación cargado")
    print("📊 API lista en http://localhost:8000")
    print("📚 Documentación en http://localhost:8000/docs")
    
    yield
    
    # Shutdown
    print("👋 The Wingman API shutting down...")


# ============================================================================
# App Configuration
# ============================================================================

app = FastAPI(
    title="The Wingman API",
    description="""
    ## API de Reclutamiento con IA
    
    Sistema de evaluación de candidatos usando inteligencia artificial.
    
    ### Características:
    - 📊 **Dashboard**: Estadísticas y métricas en tiempo real
    - 👥 **Candidatos**: Gestión completa de postulantes
    - 🤖 **Evaluación IA**: Motor de scoring basado en keywords e inferencia
    - 💬 **Comentarios**: Sistema de notas por candidato
    - ⚙️ **Configuración**: Personalización del modelo de evaluación
    
    ### Integración:
    - Airtable como base de datos
    - Extracción de texto de PDFs
    - API REST moderna con FastAPI
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Permitir frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"  # Para desarrollo, restringir en producción
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error interno: {str(exc)}"}
    )


# ============================================================================
# Routes
# ============================================================================

# Health check
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "The Wingman API",
        "version": "2.0.0"
    }


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Verificación de salud detallada."""
    airtable_ok = bool(os.getenv("AIRTABLE_API_KEY") and os.getenv("AIRTABLE_BASE_ID"))
    
    return {
        "status": "healthy",
        "services": {
            "api": True,
            "engine": True,
            "airtable": airtable_ok
        }
    }


# Registrar routers
app.include_router(candidates_router, prefix="/api")
app.include_router(processes_router, prefix="/api")
app.include_router(evaluations_router, prefix="/api")
app.include_router(config_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(applications_router, prefix="/api")
app.include_router(cargos_router, prefix="/api")


# ============================================================================
# File Server - Servir CVs
# ============================================================================

# Directorios de CVs (unificados en data/cvs)
CVS_DIR = Path(__file__).parent.parent / "data" / "cvs"
CVS_DIR.mkdir(parents=True, exist_ok=True)
CVS_UPLOADS_DIR = CVS_DIR  # Mismo directorio para uploads


@app.get("/files/{filename}", tags=["Files"])
async def serve_cv_file(filename: str):
    """
    Sirve archivos PDF de CVs.
    
    Busca en ambos directorios: CVs existentes y uploads nuevos.
    El filename debe estar URL-encoded si contiene caracteres especiales.
    """
    # Decodificar el nombre del archivo
    decoded_filename = urllib.parse.unquote(filename)
    
    # Buscar en ambos directorios
    file_path = None
    allowed_dirs = [CVS_DIR, CVS_UPLOADS_DIR]
    
    for dir_path in allowed_dirs:
        potential_path = dir_path / decoded_filename
        if potential_path.exists():
            try:
                resolved = potential_path.resolve()
                if str(resolved).startswith(str(dir_path.resolve())):
                    file_path = resolved
                    break
            except Exception:
                continue
    
    if not file_path:
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {decoded_filename}")
    
    # Detectar tipo MIME
    ext = decoded_filename.split(".")[-1].lower()
    media_types = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
    media_type = media_types.get(ext, "application/octet-stream")
    
    return FileResponse(
        path=str(file_path),
        filename=decoded_filename,
        media_type=media_type
    )


# ============================================================================
# Run with python -m api.main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

