"""
Rutas de la API para configuración del motor de evaluación.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import json
import sys
import os

# Agregar el path del engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ..models import EvaluationConfigResponse
from ..services.airtable import AirtableService
from engine import EvaluationConfig

router = APIRouter(prefix="/config", tags=["Configuration"])


def get_airtable_service() -> AirtableService:
    """Dependency para obtener el servicio de Airtable."""
    return AirtableService.from_env()


# ============================================================================
# Configuration Endpoints
# ============================================================================

@router.get("/active", response_model=EvaluationConfigResponse)
async def get_active_config(
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Obtiene la configuración de evaluación activa."""
    try:
        config = await airtable.get_active_config()
        
        if not config or not config.get("id"):
            # Si no hay configuración en Airtable, crear una por defecto
            default_config = EvaluationConfig.default_config()
            
            return EvaluationConfigResponse(
                id="default",
                version=default_config.version,
                nombre="Configuración por defecto",
                is_active=True,
                config_json=default_config.model_dump_json()
            )
        
        return EvaluationConfigResponse(**config)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default")
async def get_default_config():
    """Obtiene la configuración por defecto del motor."""
    try:
        default_config = EvaluationConfig.default_config()
        return default_config.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_config(
    config_data: Dict[str, Any],
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Crea una nueva configuración de evaluación."""
    try:
        # Validar que la configuración sea válida
        try:
            EvaluationConfig(**config_data.get("config", {}))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Configuración inválida: {str(e)}"
            )
        
        saved = await airtable.create_config(config_data)
        return saved
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords")
async def get_keywords():
    """Obtiene las keywords de la configuración por defecto."""
    try:
        config = EvaluationConfig.default_config()
        
        return {
            "categories": {
                k: {
                    "name": v.name,
                    "keywords": v.keywords,
                    "max_expected": v.max_expected,
                    "culture_booster_keywords": v.culture_booster_keywords
                }
                for k, v in config.categories.items()
            },
            "inference": {
                "technical_keywords": config.inference.technical_keywords,
                "strategic_keywords": config.inference.strategic_keywords,
                "corporate_scope_keywords": config.inference.corporate_scope_keywords
            },
            "industry_multipliers": {
                "fintech": config.industry_multipliers.fintech,
                "tech": config.industry_multipliers.tech,
                "general": config.industry_multipliers.general,
                "traditional": config.industry_multipliers.traditional
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

