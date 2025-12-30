"""
Rutas de la API para gestión de cargos.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from ..models import CargoResponse, CargoCreate, CargoUpdate
from ..services.airtable import AirtableService

router = APIRouter(prefix="/cargos", tags=["Cargos"])


def get_airtable_service() -> AirtableService:
    """Dependency para obtener el servicio de Airtable."""
    return AirtableService.from_env()


@router.get("/", response_model=List[CargoResponse])
async def list_cargos(
    solo_activos: bool = Query(False, description="Solo cargos activos"),
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Lista todos los cargos."""
    try:
        cargos = await airtable.get_cargos(solo_activos=solo_activos)
        return [CargoResponse(**c) for c in cargos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cargo_id}", response_model=CargoResponse)
async def get_cargo(
    cargo_id: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Obtiene un cargo por su ID."""
    try:
        cargo = await airtable.get_cargo_by_id(cargo_id)
        
        if not cargo or not cargo.get("id"):
            raise HTTPException(status_code=404, detail="Cargo no encontrado")
        
        return CargoResponse(**cargo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=CargoResponse)
async def create_cargo(
    data: CargoCreate,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Crea un nuevo cargo."""
    try:
        cargo = await airtable.create_cargo({
            "codigo": data.codigo,
            "nombre": data.nombre,
            "descripcion": data.descripcion or "",
            "vacantes": data.vacantes or 1,
            "activo": True
        })
        return CargoResponse(**cargo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{cargo_id}", response_model=CargoResponse)
async def update_cargo(
    cargo_id: str,
    data: CargoUpdate,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Actualiza un cargo existente."""
    try:
        update_data = {}
        if data.codigo is not None:
            update_data["codigo"] = data.codigo
        if data.nombre is not None:
            update_data["nombre"] = data.nombre
        if data.descripcion is not None:
            update_data["descripcion"] = data.descripcion
        if data.vacantes is not None:
            update_data["vacantes"] = data.vacantes
        if data.activo is not None:
            update_data["activo"] = data.activo
        
        cargo = await airtable.update_cargo(cargo_id, update_data)
        return CargoResponse(**cargo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{cargo_id}")
async def delete_cargo(
    cargo_id: str,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Desactiva un cargo (soft delete)."""
    try:
        await airtable.update_cargo(cargo_id, {"activo": False})
        return {"message": "Cargo desactivado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




