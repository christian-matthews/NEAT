"""
Modelos de datos para el motor de evaluación.
Usando Pydantic para validación y serialización.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum


class RetentionRisk(str, Enum):
    LOW = "Bajo"
    MEDIUM = "Medio"
    HIGH = "Alto"


class ProfileType(str, Enum):
    HYBRID = "Híbrido (Gestión + Operación)"
    HANDS_ON = "Ejecutor Hands-On"
    DELEGATOR = "Estratégico / Delegador"
    CORPORATE = "Corporativo Senior / Overqualified"


class IndustryTier(str, Enum):
    FINTECH = "Fintech (Ideal)"
    TECH = "Tech / Digital"
    GENERAL = "General"
    TRADITIONAL = "Traditional"


# ============================================================================
# Configuration Models
# ============================================================================

class CategoryConfig(BaseModel):
    """Configuración de una categoría de evaluación."""
    name: str
    keywords: List[str]
    max_expected: int = 5
    culture_booster_keywords: Optional[List[str]] = None
    
    
class InferenceConfig(BaseModel):
    """Configuración para la inferencia de perfil."""
    technical_keywords: List[str] = Field(default_factory=list)
    strategic_keywords: List[str] = Field(default_factory=list)
    corporate_scope_keywords: List[str] = Field(default_factory=list)


class IndustryMultipliers(BaseModel):
    """Multiplicadores por tipo de industria."""
    fintech: float = 1.5
    tech: float = 1.2
    general: float = 1.0
    traditional: float = 0.7


class EvaluationConfig(BaseModel):
    """Configuración completa del motor de evaluación."""
    version: str = "1.0"
    weights: Dict[str, float] = Field(default_factory=lambda: {
        "admin": 0.33, "ops": 0.33, "biz": 0.33
    })
    categories: Dict[str, CategoryConfig] = Field(default_factory=dict)
    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    industry_multipliers: IndustryMultipliers = Field(default_factory=IndustryMultipliers)
    
    @classmethod
    def default_config(cls) -> "EvaluationConfig":
        """Retorna la configuración por defecto para Senior Finance."""
        return cls(
            version="1.0",
            weights={"admin": 0.33, "ops": 0.33, "biz": 0.33},
            categories={
                "admin": CategoryConfig(
                    name="Admin & Finanzas",
                    keywords=[
                        "cierre contable", "mensual", "imputación", "gastos", "ingresos",
                        "reportes financieros", "análisis de cuentas", "excel", "trazabilidad",
                        "contratos", "auditoría", "estados financieros", "contabilidad", "balance",
                        "control administrativo", "procedimientos", "normativa"
                    ],
                    max_expected=6
                ),
                "ops": CategoryConfig(
                    name="Operaciones y Tesorería",
                    keywords=[
                        "flujo de caja", "cash flow", "semanal", "proyección", "liquidez",
                        "priorizar pagos", "tesorería", "banco", "transferencias", "conciliación bancaria",
                        "contingencias", "pagos", "operaciones financieras", "clearing", "recaudación"
                    ],
                    max_expected=5,
                    culture_booster_keywords=["fintech", "startup", "emprendimiento", "rápido crecimiento", "scaleup"]
                ),
                "biz": CategoryConfig(
                    name="Growth & Cultura",
                    keywords=[
                        "procesos", "implementación", "mejora continua", "liderazgo",
                        "equipo", "autonomía", "proactividad", "bi", "business intelligence",
                        "automatización", "eficiencia", "escalable", "estrategia", "kpi",
                        "growth", "ownership", "colaboración", "user-centric"
                    ],
                    max_expected=6
                )
            },
            inference=InferenceConfig(
                technical_keywords=[
                    "imputación", "asiento", "conciliación", "tabla dinámica", "macros",
                    "sql", "erp", "sap", "manager", "digitación", "facturación", "rendición",
                    "análisis de cuentas", "balance", "declaración"
                ],
                strategic_keywords=[
                    "dirección", "supervisión", "reporta al directorio", "estrategia",
                    "negociación", "fusión", "adquisición", "board", "comité"
                ],
                corporate_scope_keywords=[
                    "regional", "latam", "global", "multinacional", "holding", "filiales",
                    "m&a", "ipo", "apertura en bolsa", "billones", "mmus$", "corporate",
                    "directorio", "gobernanza"
                ]
            ),
            industry_multipliers=IndustryMultipliers()
        )


# ============================================================================
# Result Models
# ============================================================================

class CategoryResult(BaseModel):
    """Resultado de evaluación de una categoría."""
    score: int = Field(ge=0, le=100)
    found: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    reasoning: str = ""
    questions: List[str] = Field(default_factory=list)
    

class InferenceResult(BaseModel):
    """Resultado de la inferencia de perfil."""
    profile_type: ProfileType = ProfileType.HYBRID
    hands_on_index: int = Field(ge=0, le=100, default=0)
    risk_warning: str = ""
    retention_risk: RetentionRisk = RetentionRisk.LOW
    scope_intensity: int = Field(ge=0, default=0)
    potential_score: int = Field(ge=0, le=100, default=0)
    industry_tier: IndustryTier = IndustryTier.GENERAL
    

class EvaluationResult(BaseModel):
    """Resultado completo de la evaluación de un candidato."""
    fits: Dict[str, CategoryResult] = Field(default_factory=dict)
    inference: InferenceResult = Field(default_factory=InferenceResult)
    score_promedio: int = Field(ge=0, le=100, default=0)
    config_version: str = "1.0"
    
    def calculate_average(self) -> int:
        """Calcula el score promedio de todas las categorías."""
        if not self.fits:
            return 0
        scores = [cat.score for cat in self.fits.values()]
        return int(sum(scores) / len(scores))
    
    def model_post_init(self, __context) -> None:
        """Calcula el score promedio después de crear el modelo."""
        if self.fits and self.score_promedio == 0:
            self.score_promedio = self.calculate_average()


# ============================================================================
# Company Knowledge Models
# ============================================================================

class CompanyInfo(BaseModel):
    """Información de una empresa conocida."""
    desc: str
    tier: str
    

class CompanyKnowledge(BaseModel):
    """Base de conocimiento de empresas."""
    companies: Dict[str, CompanyInfo] = Field(default_factory=dict)

