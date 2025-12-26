"""
Rutas de la API para gestión de procesos de reclutamiento.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from fastapi.responses import StreamingResponse
from typing import List, Optional
import csv
import io

from ..models import ProcesoResponse, ProcesoCreate, ProcesoUpdate
from ..services.airtable import AirtableService

router = APIRouter(prefix="/processes", tags=["Processes"])


def get_airtable_service() -> AirtableService:
    """Dependency para obtener el servicio de Airtable."""
    return AirtableService.from_env()


async def get_current_user_id(
    authorization: str = Header(None),
    airtable: AirtableService = Depends(get_airtable_service)
) -> Optional[str]:
    """Extrae el usuario actual del token."""
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "")
        import jwt
        import os
        payload = jwt.decode(token, os.getenv("JWT_SECRET", "your-secret-key"), algorithms=["HS256"])
        return payload.get("user_id")
    except:
        return None


# ============================================================================
# Procesos CRUD
# ============================================================================

@router.get("/", response_model=List[ProcesoResponse])
async def list_processes(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Lista todos los procesos de reclutamiento."""
    try:
        procesos = await airtable.get_procesos(estado=estado)
        return [ProcesoResponse(**p) for p in procesos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mine", response_model=List[ProcesoResponse])
async def list_my_processes(
    authorization: str = Header(None),
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Lista los procesos asignados al usuario actual."""
    try:
        user_id = await get_current_user_id(authorization, airtable)
        if not user_id:
            raise HTTPException(status_code=401, detail="No autenticado")
        
        procesos = await airtable.get_procesos(usuario_id=user_id)
        return [ProcesoResponse(**p) for p in procesos]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proceso_id}", response_model=ProcesoResponse)
async def get_process(
    proceso_id: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Obtiene un proceso por su ID."""
    try:
        proceso = await airtable.get_proceso_by_id(proceso_id)
        
        if not proceso or not proceso.get("id"):
            raise HTTPException(status_code=404, detail="Proceso no encontrado")
        
        return ProcesoResponse(**proceso)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ProcesoResponse)
async def create_process(
    data: ProcesoCreate,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Crea un nuevo proceso de reclutamiento."""
    try:
        proceso = await airtable.create_proceso({
            "codigo_proceso": data.codigo_proceso,
            "cargo": [data.cargo_id] if data.cargo_id else [],
            "usuario_asignado": [data.usuario_asignado_id] if data.usuario_asignado_id else [],
            "vacantes_proceso": data.vacantes_proceso,
            "fecha_cierre": data.fecha_cierre,
            "notas": data.notas,
            "estado": "publicado"
        })
        return ProcesoResponse(**proceso)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{proceso_id}", response_model=ProcesoResponse)
async def update_process(
    proceso_id: str,
    data: ProcesoUpdate,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Actualiza un proceso existente."""
    try:
        update_data = {}
        if data.estado is not None:
            update_data["estado"] = data.estado
        if data.vacantes_proceso is not None:
            update_data["vacantes_proceso"] = data.vacantes_proceso
        if data.fecha_cierre is not None:
            update_data["fecha_cierre"] = data.fecha_cierre
        if data.notas is not None:
            update_data["notas"] = data.notas
        if data.avances is not None:
            update_data["avances"] = data.avances
        if data.bloqueos is not None:
            update_data["bloqueos"] = data.bloqueos
        if data.proximos_pasos is not None:
            update_data["proximos_pasos"] = data.proximos_pasos
        if data.resultado is not None:
            update_data["resultado"] = data.resultado
        
        proceso = await airtable.update_proceso(proceso_id, update_data)
        return ProcesoResponse(**proceso)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{proceso_id}")
async def delete_process(
    proceso_id: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Elimina un proceso (soft delete - cambio de estado)."""
    try:
        await airtable.update_proceso(proceso_id, {"estado": "cancelado"})
        return {"message": "Proceso cancelado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proceso_id}/export")
async def export_process_csv(
    proceso_id: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Exporta los candidatos de un proceso a CSV."""
    try:
        proceso = await airtable.get_proceso_by_id(proceso_id)
        if not proceso:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")
        
        candidatos = await airtable.get_candidatos(proceso_id=proceso_id)
        
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Código Tracking", "Nombre", "Email", "Teléfono",
            "Fecha Postulación", "Estado", "CV URL"
        ])
        
        # Data
        for c in candidatos:
            writer.writerow([
                c.get("codigo_tracking", ""),
                c.get("nombre_completo", ""),
                c.get("email", ""),
                c.get("telefono", ""),
                c.get("fecha_postulacion", ""),
                c.get("estado_candidato", ""),
                c.get("cv_url", "")
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={proceso.get('codigo_proceso', 'proceso')}_candidatos.csv"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proceso_id}/export-pdf")
async def export_process_pdf(
    proceso_id: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """
    Exporta un resumen completo del proceso a PDF.
    
    Incluye:
    - Resumen ejecutivo con estadísticas
    - Vista Canvas con pipeline de candidatos (4 columnas)
    - Fichas individuales de candidatos con evaluaciones y comentarios
    """
    try:
        from ..services.pdf_generator import generate_proceso_pdf
        
        # Obtener datos del proceso
        proceso = await airtable.get_proceso_by_id(proceso_id)
        if not proceso:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")
        
        # Obtener candidatos
        candidatos = await airtable.get_candidatos(proceso_id=proceso_id)
        
        # Obtener evaluaciones y comentarios para cada candidato
        evaluaciones = {}
        comentarios = {}
        
        for c in candidatos:
            cid = c['id']
            tracking = c.get('codigo_tracking')
            
            # Evaluación
            eval_data = await airtable.get_evaluacion(cid, tracking)
            if eval_data:
                evaluaciones[cid] = eval_data
            
            # Comentarios
            coms = await airtable.get_comentarios(cid)
            if coms:
                comentarios[cid] = coms
        
        # Generar PDF (async para usar IA en resumen de comentarios)
        pdf_bytes = await generate_proceso_pdf(
            proceso=proceso,
            candidatos=candidatos,
            evaluaciones=evaluaciones,
            comentarios=comentarios
        )
        
        # Nombre del archivo
        codigo = proceso.get('codigo_proceso', 'proceso')
        filename = f"{codigo}_resumen.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
