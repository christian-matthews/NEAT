"""
Modelos Pydantic para la API.
Define los esquemas de request/response.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class ProcesoEstado(str, Enum):
    PUBLICADO = "publicado"
    EN_PROCESO = "en_proceso"
    FINALIZADO = "finalizado"
    CANCELADO = "cancelado"


class RetentionRisk(str, Enum):
    BAJO = "Bajo"
    MEDIO = "Medio"
    ALTO = "Alto"


# ============================================================================
# Cargo Schemas
# ============================================================================

class CargoBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    vacantes: int = 1
    activo: bool = True


class CargoResponse(CargoBase):
    id: str
    created_at: Optional[datetime] = None


class CargoCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    vacantes: Optional[int] = 1


class CargoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    vacantes: Optional[int] = None
    activo: Optional[bool] = None


# ============================================================================
# Proceso Schemas
# ============================================================================

class ProcesoBase(BaseModel):
    codigo_proceso: str
    estado: ProcesoEstado = ProcesoEstado.PUBLICADO
    fecha_inicio: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    vacantes_proceso: int = 1
    notas: Optional[str] = None


class ProcesoResponse(BaseModel):
    id: str
    codigo_proceso: str
    estado: str = "publicado"
    fecha_inicio: Optional[str] = None
    fecha_cierre: Optional[str] = None
    vacantes_proceso: int = 1
    notas: Optional[str] = None
    avances: Optional[str] = None
    bloqueos: Optional[str] = None
    proximos_pasos: Optional[str] = None
    resultado: Optional[str] = None
    cargo: Optional[List[str]] = None
    cargo_id: Optional[str] = None
    cargo_nombre: Optional[str] = None
    usuario_asignado: Optional[List[str]] = None
    usuario_asignado_id: Optional[str] = None
    usuario_asignado_nombre: Optional[str] = None
    postulaciones_count: int = 0
    created_at: Optional[str] = None


class ProcesoCreate(BaseModel):
    codigo_proceso: str
    cargo_id: str
    usuario_asignado_id: str
    vacantes_proceso: int = 1
    fecha_cierre: Optional[str] = None
    notas: Optional[str] = None


class ProcesoUpdate(BaseModel):
    estado: Optional[str] = None
    vacantes_proceso: Optional[int] = None
    fecha_cierre: Optional[str] = None
    notas: Optional[str] = None
    avances: Optional[str] = None
    bloqueos: Optional[str] = None
    proximos_pasos: Optional[str] = None
    resultado: Optional[str] = None


# ============================================================================
# Candidato Schemas
# ============================================================================

class CandidatoCreate(BaseModel):
    nombre_completo: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    telefono: str = Field(..., min_length=8, max_length=20)
    cv_url: Optional[str] = None
    proceso_id: Optional[str] = None
    cargo_id: Optional[str] = None


class CandidatoResponse(BaseModel):
    id: str
    codigo_tracking: str
    nombre_completo: str
    email: str
    telefono: Optional[str] = None
    cv_url: Optional[str] = None
    fecha_postulacion: Optional[str] = None
    proceso: Optional[List[str]] = None
    cargo: Optional[List[str]] = None
    created_at: Optional[str] = None


class CandidatoWithEvaluation(CandidatoResponse):
    """Candidato con datos de evaluación incluidos."""
    score_promedio: int = 0
    hands_on_index: int = 0
    retention_risk: str = "Bajo"
    profile_type: Optional[str] = None
    industry_tier: Optional[str] = None


# ============================================================================
# Evaluación Schemas
# ============================================================================

class CategoryResultSchema(BaseModel):
    score: int = Field(ge=0, le=100)
    found: List[str] = []
    missing: List[str] = []
    reasoning: str = ""
    questions: List[str] = []


class InferenceResultSchema(BaseModel):
    profile_type: str = ""
    hands_on_index: int = Field(ge=0, le=100, default=0)
    risk_warning: str = ""
    retention_risk: str = "Bajo"
    scope_intensity: int = 0
    potential_score: int = Field(ge=0, le=100, default=0)
    industry_tier: str = "General"


class EvaluationResponse(BaseModel):
    id: Optional[str] = None
    candidato_id: str
    score_promedio: int = 0
    fits: Dict[str, CategoryResultSchema] = {}
    inference: InferenceResultSchema = InferenceResultSchema()
    config_version: str = "1.0"
    evaluated_at: Optional[str] = None
    cached: bool = False


class EvaluateRequest(BaseModel):
    """Request para evaluar un candidato."""
    candidato_id: str
    cv_text: Optional[str] = None  # Texto del CV si ya fue extraído
    force_reeval: bool = False     # Forzar re-evaluación aunque exista cache


# ============================================================================
# Comentario Schemas
# ============================================================================

class ComentarioCreate(BaseModel):
    autor: str = Field(..., min_length=1, max_length=100)
    comentario: str = Field(..., min_length=1)


class ComentarioResponse(BaseModel):
    id: str
    autor: str
    comentario: str
    created_at: Optional[str] = None


# ============================================================================
# Entrevista Schemas
# ============================================================================

class EntrevistaCreate(BaseModel):
    entrevistador: str
    score_entrevista: int = Field(ge=0, le=100)
    notas: Optional[str] = None
    tipo_entrevista: str = "Telefónica"
    fecha_entrevista: Optional[datetime] = None


class EntrevistaResponse(EntrevistaCreate):
    id: str
    candidato_id: str
    estado: str = "Realizada"
    created_at: Optional[str] = None


# ============================================================================
# Config Schemas
# ============================================================================

class EvaluationConfigResponse(BaseModel):
    id: str
    version: str
    nombre: str
    is_active: bool
    config_json: Optional[str] = None
    created_at: Optional[str] = None


# ============================================================================
# Dashboard/Stats Schemas
# ============================================================================

class DashboardStats(BaseModel):
    """Estadísticas para el dashboard."""
    total_candidatos: int = 0
    score_promedio: float = 0.0
    candidatos_alto_riesgo: int = 0
    candidatos_evaluados: int = 0
    candidatos_pendientes: int = 0
    procesos_activos: int = 0


class CandidatoRanking(BaseModel):
    """Candidato en el ranking."""
    id: str
    nombre_completo: str
    email: str
    codigo_tracking: Optional[str] = None
    telefono: Optional[str] = None
    cv_url: Optional[str] = None
    fecha_postulacion: Optional[str] = None
    estado_candidato: Optional[str] = "recibido"
    score_promedio: int = 0
    hands_on_index: int = 0
    retention_risk: str = "Bajo"
    profile_type: Optional[str] = None
    industry_tier: Optional[str] = None
    interview_status: str = "Pendiente"

