"""
Rutas de la API para gestión de candidatos.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
import uuid

from ..models import (
    CandidatoCreate,
    CandidatoResponse,
    CandidatoWithEvaluation,
    CandidatoRanking,
    ComentarioCreate,
    ComentarioResponse,
    DashboardStats
)
from ..services.airtable import AirtableService

router = APIRouter(prefix="/candidates", tags=["Candidates"])


def get_airtable_service() -> AirtableService:
    """Dependency para obtener el servicio de Airtable."""
    return AirtableService.from_env()


def generate_tracking_code() -> str:
    """Genera un código de tracking único."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"TW-POST-{timestamp}"


# ============================================================================
# Dashboard & Stats
# ============================================================================

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Obtiene estadísticas para el dashboard."""
    try:
        candidatos = await airtable.get_candidatos()
        procesos = await airtable.get_procesos(estado="publicado")
        
        # Calcular stats
        total = len(candidatos)
        evaluados = 0
        scores = []
        alto_riesgo = 0
        
        for c in candidatos:
            evaluacion = await airtable.get_evaluacion(c["id"], c.get("codigo_tracking"))
            if evaluacion:
                evaluados += 1
                scores.append(evaluacion.get("score_promedio", 0))
                if evaluacion.get("retention_risk") == "Alto":
                    alto_riesgo += 1
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return DashboardStats(
            total_candidatos=total,
            score_promedio=round(avg_score, 1),
            candidatos_alto_riesgo=alto_riesgo,
            candidatos_evaluados=evaluados,
            candidatos_pendientes=total - evaluados,
            procesos_activos=len(procesos)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# List & Search
# ============================================================================

@router.get("/", response_model=List[CandidatoRanking])
async def list_candidates(
    proceso_id: Optional[str] = Query(None, description="Filtrar por proceso"),
    limit: Optional[int] = Query(None, description="Límite de resultados"),
    airtable: AirtableService = Depends(get_airtable_service)
):
    """
    Lista todos los candidatos con sus scores.
    Ordenados por score_promedio descendente.
    """
    try:
        candidatos = await airtable.get_candidatos(proceso_id=proceso_id, limit=limit)
        
        result = []
        for c in candidatos:
            # Obtener evaluación si existe (pasando tracking code para búsqueda eficiente)
            evaluacion = await airtable.get_evaluacion(c["id"], c.get("codigo_tracking"))
            
            ranking = CandidatoRanking(
                id=c["id"],
                nombre_completo=c["nombre_completo"],
                email=c["email"],
                score_promedio=evaluacion.get("score_promedio", 0) if evaluacion else 0,
                hands_on_index=evaluacion.get("hands_on_index", 0) if evaluacion else 0,
                retention_risk=evaluacion.get("retention_risk", "Bajo") if evaluacion else "Bajo",
                profile_type=evaluacion.get("profile_type") if evaluacion else None,
                industry_tier=evaluacion.get("industry_tier") if evaluacion else None,
                interview_status="Pendiente"  # TODO: Integrar entrevistas
            )
            result.append(ranking)
        
        # Ordenar por score descendente
        result.sort(key=lambda x: x.score_promedio, reverse=True)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CRUD Operations
# ============================================================================

@router.get("/{candidate_id}", response_model=CandidatoWithEvaluation)
async def get_candidate(
    candidate_id: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Obtiene un candidato por ID con su evaluación."""
    try:
        # Intentar buscar por ID primero
        candidato = await airtable.get_candidato_by_id(candidate_id)
        
        # Si no encuentra, intentar por código de tracking
        if not candidato or not candidato.get("id"):
            candidato = await airtable.get_candidato(candidate_id)
        
        if not candidato or not candidato.get("id"):
            raise HTTPException(status_code=404, detail="Candidato no encontrado")
        
        # Obtener evaluación (pasando tracking code para búsqueda eficiente)
        evaluacion = await airtable.get_evaluacion(candidato["id"], candidato.get("codigo_tracking"))
        
        return CandidatoWithEvaluation(
            id=candidato["id"],
            codigo_tracking=candidato.get("codigo_tracking", ""),
            nombre_completo=candidato["nombre_completo"],
            email=candidato["email"],
            telefono=candidato.get("telefono"),
            cv_url=candidato.get("cv_url"),
            fecha_postulacion=candidato.get("fecha_postulacion"),
            proceso=candidato.get("proceso"),
            cargo=candidato.get("cargo"),
            created_at=candidato.get("created_at"),
            score_promedio=evaluacion.get("score_promedio", 0) if evaluacion else 0,
            hands_on_index=evaluacion.get("hands_on_index", 0) if evaluacion else 0,
            retention_risk=evaluacion.get("retention_risk", "Bajo") if evaluacion else "Bajo",
            profile_type=evaluacion.get("profile_type") if evaluacion else None,
            industry_tier=evaluacion.get("industry_tier") if evaluacion else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=CandidatoResponse)
async def create_candidate(
    data: CandidatoCreate,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Crea un nuevo candidato."""
    try:
        candidato_data = data.model_dump()
        candidato_data["codigo_tracking"] = generate_tracking_code()
        
        candidato = await airtable.create_candidato(candidato_data)
        
        return CandidatoResponse(**candidato)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# By Proceso
# ============================================================================

@router.get("/by-proceso/{proceso_id}", response_model=List[CandidatoRanking])
async def get_candidates_by_proceso(
    proceso_id: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Obtiene todos los candidatos de un proceso específico."""
    try:
        candidatos = await airtable.get_candidatos(proceso_id=proceso_id)
        
        result = []
        for c in candidatos:
            evaluacion = await airtable.get_evaluacion(c["id"], c.get("codigo_tracking"))
            
            ranking = CandidatoRanking(
                id=c["id"],
                nombre_completo=c["nombre_completo"],
                email=c["email"],
                codigo_tracking=c.get("codigo_tracking"),
                telefono=c.get("telefono"),
                cv_url=c.get("cv_url"),
                fecha_postulacion=c.get("fecha_postulacion"),
                estado_candidato=c.get("estado_candidato", "recibido"),
                score_promedio=evaluacion.get("score_promedio", 0) if evaluacion else 0,
                hands_on_index=evaluacion.get("hands_on_index", 0) if evaluacion else 0,
                retention_risk=evaluacion.get("retention_risk", "Bajo") if evaluacion else "Bajo",
                profile_type=evaluacion.get("profile_type") if evaluacion else None,
                industry_tier=evaluacion.get("industry_tier") if evaluacion else None,
                interview_status="Pendiente"
            )
            result.append(ranking)
        
        result.sort(key=lambda x: x.score_promedio, reverse=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Update Candidate
# ============================================================================

@router.patch("/{candidate_id}", response_model=CandidatoResponse)
async def update_candidate(
    candidate_id: str,
    data: dict,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Actualiza un candidato."""
    try:
        candidato = await airtable.update_candidato(candidate_id, data)
        return CandidatoResponse(**candidato)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Comments
# ============================================================================

@router.get("/{candidate_id}/comments", response_model=List[ComentarioResponse])
async def get_candidate_comments(
    candidate_id: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Obtiene todos los comentarios de un candidato."""
    try:
        comentarios = await airtable.get_comentarios(candidate_id)
        return [ComentarioResponse(**c) for c in comentarios]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{candidate_id}/comments", response_model=ComentarioResponse)
async def add_candidate_comment(
    candidate_id: str,
    data: ComentarioCreate,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Agrega un comentario a un candidato."""
    try:
        comentario = await airtable.create_comentario(
            candidato_id=candidate_id,
            autor=data.autor,
            comentario=data.comentario
        )
        return ComentarioResponse(**comentario)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

