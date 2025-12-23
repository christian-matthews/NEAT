"""
Rutas para postulaciones públicas.
Permite a candidatos postularse a procesos de reclutamiento.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import os
import shutil
from pathlib import Path
import httpx

from ..services.airtable import AirtableService

router = APIRouter(prefix="/applications", tags=["Public Applications"])

# Directorio para guardar CVs (unificado en data/cvs)
CVS_DIR = Path(__file__).parent.parent.parent / "data" / "cvs"
CVS_DIR.mkdir(parents=True, exist_ok=True)


async def upload_to_temp_storage(file_content: bytes, filename: str) -> Optional[str]:
    """
    Sube un archivo a un servicio de almacenamiento temporal para obtener URL pública.
    Airtable descargará el archivo y lo almacenará permanentemente.
    
    Usa catbox.moe (gratis, sin límite de tiempo para archivos <200MB)
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Usar catbox.moe - servicio gratuito que mantiene archivos indefinidamente
            files = {
                'reqtype': (None, 'fileupload'),
                'fileToUpload': (filename, file_content, 'application/pdf')
            }
            
            response = await client.post(
                'https://catbox.moe/user/api.php',
                files=files
            )
            
            if response.status_code == 200 and response.text.startswith('https://'):
                return response.text.strip()
            
            # Fallback: usar file.io
            files_fileio = {'file': (filename, file_content, 'application/pdf')}
            response = await client.post(
                'https://file.io/?expires=1d',
                files=files_fileio
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('link')
            
            return None
            
    except Exception as e:
        print(f"[WARN] Error subiendo a storage temporal: {e}")
        return None

# ============================================================================
# Models
# ============================================================================

class ProcesoPublico(BaseModel):
    id: str
    codigo_proceso: str
    cargo_nombre: str
    cargo_id: str
    vacantes: int
    fecha_cierre: Optional[str] = None

class PostulacionCreate(BaseModel):
    nombre_completo: str
    email: EmailStr
    telefono: str
    proceso_id: str

class PostulacionResponse(BaseModel):
    id: str
    codigo_tracking: str
    nombre_completo: str
    email: str
    mensaje: str

class TrackingResponse(BaseModel):
    codigo_tracking: str
    nombre_completo: str
    proceso: str
    cargo: str
    fecha_postulacion: str
    estado: str

# ============================================================================
# Helpers
# ============================================================================

def get_airtable_service() -> AirtableService:
    """Dependency para obtener el servicio de Airtable."""
    return AirtableService.from_env()

def generate_tracking_code() -> str:
    """Genera un código de tracking único."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"TW-POST-{timestamp}"

# ============================================================================
# Public Endpoints
# ============================================================================

@router.get("/processes", response_model=List[ProcesoPublico])
async def get_public_processes(
    airtable: AirtableService = Depends(get_airtable_service)
):
    """
    Lista procesos de reclutamiento publicados.
    Endpoint público, no requiere autenticación.
    """
    try:
        procesos = await airtable.get_procesos_publicados()
        
        result = []
        for p in procesos:
            # Obtener nombre del cargo
            cargo_nombre = "Sin cargo"
            cargo_id = ""
            if p.get("cargo"):
                cargo_ids = p["cargo"] if isinstance(p["cargo"], list) else [p["cargo"]]
                if cargo_ids:
                    cargo = await airtable.get_cargo_by_id(cargo_ids[0])
                    if cargo:
                        cargo_nombre = cargo.get("nombre", "Sin cargo")
                        cargo_id = cargo.get("id", "")
            
            result.append(ProcesoPublico(
                id=p["id"],
                codigo_proceso=p.get("codigo_proceso", ""),
                cargo_nombre=cargo_nombre,
                cargo_id=cargo_id,
                vacantes=p.get("vacantes_proceso", 1),
                fecha_cierre=p.get("fecha_cierre")
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit", response_model=PostulacionResponse)
async def submit_application(
    nombre_completo: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(...),
    proceso_id: str = Form(...),
    cv_file: UploadFile = File(...),
    airtable: AirtableService = Depends(get_airtable_service)
):
    """
    Envía una nueva postulación con CV.
    Endpoint público, no requiere autenticación.
    
    El CV se:
    1. Guarda localmente como backup
    2. Sube a un servicio temporal para obtener URL pública
    3. Se registra en Airtable como attachment (Airtable lo descarga y guarda)
    """
    try:
        # Validar proceso
        proceso = await airtable.get_proceso_by_id(proceso_id)
        if not proceso:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")
        
        if proceso.get("estado") != "publicado":
            raise HTTPException(status_code=400, detail="El proceso no está abierto para postulaciones")
        
        # Validar archivo
        if not cv_file.filename:
            raise HTTPException(status_code=400, detail="Archivo CV requerido")
        
        file_ext = cv_file.filename.split(".")[-1].lower()
        if file_ext not in ["pdf", "doc", "docx"]:
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF, DOC o DOCX")
        
        # Generar código tracking
        tracking_code = generate_tracking_code()
        
        # Leer contenido del archivo
        cv_content = await cv_file.read()
        
        # Guardar archivo localmente como backup
        nombre_limpio = nombre_completo.replace(" ", "_").replace("/", "_")
        filename = f"{tracking_code}_{nombre_limpio}.{file_ext}"
        file_path = CVS_DIR / filename
        
        with open(file_path, "wb") as buffer:
            buffer.write(cv_content)
        
        print(f"[INFO] CV guardado localmente: {file_path}")
        
        # URL del CV servido por la API (backup local)
        cv_url = f"http://localhost:8000/files/{filename}"
        
        # Obtener cargo del proceso
        cargo_id = None
        if proceso.get("cargo"):
            cargo_ids = proceso["cargo"] if isinstance(proceso["cargo"], list) else [proceso["cargo"]]
            cargo_id = cargo_ids[0] if cargo_ids else None
        
        # Preparar datos del candidato
        candidato_data = {
            "nombre_completo": nombre_completo.strip(),
            "email": email.lower().strip(),
            "telefono": telefono.strip(),
            "codigo_tracking": tracking_code,
            "cv_url": cv_url,
            "proceso": [proceso_id],
            "cargo": [cargo_id] if cargo_id else [],
            "fecha_postulacion": datetime.now().strftime("%Y-%m-%d"),
            "estado_candidato": "nuevo"
        }
        
        # =====================================================================
        # SUBIR CV A AIRTABLE
        # =====================================================================
        # Subir a servicio temporal para obtener URL pública
        public_cv_url = await upload_to_temp_storage(cv_content, filename)
        
        if public_cv_url:
            print(f"[INFO] CV subido a storage temporal: {public_cv_url}")
            # Agregar attachment para que Airtable descargue y guarde el archivo
            candidato_data["cv_archivo"] = [{"url": public_cv_url}]
        else:
            print(f"[WARN] No se pudo subir CV a storage temporal, usando solo local")
        
        # Crear candidato en Airtable
        candidato = await airtable.create_candidato(candidato_data)
        
        return PostulacionResponse(
            id=candidato["id"],
            codigo_tracking=tracking_code,
            nombre_completo=nombre_completo,
            email=email,
            mensaje="¡Postulación recibida exitosamente! Guarda tu código de tracking para consultar el estado."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error en submit_application: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-cv/{tracking_code}")
async def upload_cv_to_airtable(
    tracking_code: str,
    cv_file: UploadFile = File(...),
    airtable: AirtableService = Depends(get_airtable_service)
):
    """
    Sube un CV a Airtable como attachment para un candidato existente.
    Útil para migrar CVs existentes a Airtable.
    
    Requiere que el servidor tenga una URL pública configurada en PUBLIC_URL.
    """
    try:
        # Buscar candidato
        candidato = await airtable.get_candidato(tracking_code)
        if not candidato:
            raise HTTPException(status_code=404, detail="Candidato no encontrado")
        
        # Validar archivo
        if not cv_file.filename:
            raise HTTPException(status_code=400, detail="Archivo CV requerido")
        
        file_ext = cv_file.filename.split(".")[-1].lower()
        if file_ext not in ["pdf", "doc", "docx"]:
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF, DOC o DOCX")
        
        # Leer y guardar archivo
        cv_content = await cv_file.read()
        nombre_limpio = candidato["nombre_completo"].replace(" ", "_").replace("/", "_")
        filename = f"{tracking_code}_{nombre_limpio}.{file_ext}"
        file_path = CVS_DIR / filename
        
        with open(file_path, "wb") as buffer:
            buffer.write(cv_content)
        
        # Actualizar URL local
        cv_url = f"http://localhost:8000/files/{filename}"
        await airtable.update_candidato(candidato["id"], {"cv_url": cv_url})
        
        # Si hay URL pública, intentar subir a Airtable
        public_url = os.getenv("PUBLIC_URL")
        attachment_uploaded = False
        
        if public_url:
            try:
                attachment_url = f"{public_url}/files/{filename}"
                await airtable.update_candidato(candidato["id"], {
                    "cv_archivo": [{"url": attachment_url}]
                })
                attachment_uploaded = True
            except Exception as e:
                print(f"[WARN] No se pudo subir a Airtable attachment: {e}")
        
        return {
            "success": True,
            "tracking_code": tracking_code,
            "cv_url": cv_url,
            "airtable_attachment": attachment_uploaded,
            "message": "CV actualizado" + (" y subido a Airtable" if attachment_uploaded else " (solo local)")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/track/{tracking_code}", response_model=TrackingResponse)
async def track_application(
    tracking_code: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """
    Consulta el estado de una postulación por código de tracking.
    Endpoint público.
    """
    try:
        candidato = await airtable.get_candidato(tracking_code)
        
        if not candidato:
            raise HTTPException(status_code=404, detail="Postulación no encontrada")
        
        # Obtener proceso
        proceso_nombre = "N/A"
        cargo_nombre = "N/A"
        
        if candidato.get("proceso"):
            proceso_ids = candidato["proceso"] if isinstance(candidato["proceso"], list) else [candidato["proceso"]]
            if proceso_ids:
                proceso = await airtable.get_proceso_by_id(proceso_ids[0])
                if proceso:
                    proceso_nombre = proceso.get("codigo_proceso", "N/A")
        
        if candidato.get("cargo"):
            cargo_ids = candidato["cargo"] if isinstance(candidato["cargo"], list) else [candidato["cargo"]]
            if cargo_ids:
                cargo = await airtable.get_cargo_by_id(cargo_ids[0])
                if cargo:
                    cargo_nombre = cargo.get("nombre", "N/A")
        
        # Determinar estado basado en evaluación
        evaluacion = await airtable.get_evaluacion(candidato["id"], candidato.get("codigo_tracking"))
        
        if evaluacion:
            estado = "En evaluación"
        else:
            estado = "Recibido - Pendiente de revisión"
        
        return TrackingResponse(
            codigo_tracking=candidato["codigo_tracking"],
            nombre_completo=candidato["nombre_completo"],
            proceso=proceso_nombre,
            cargo=cargo_nombre,
            fecha_postulacion=candidato.get("fecha_postulacion", "N/A"),
            estado=estado
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

