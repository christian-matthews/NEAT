#!/usr/bin/env python3
"""
Script para subir CVs locales a Airtable como attachments.
Los sube a catbox.moe primero y luego Airtable los descarga.
"""

import os
import sys
import httpx
import asyncio
from pathlib import Path
from typing import Optional

# Configuración desde variables de entorno
API_KEY = os.getenv("AIRTABLE_API_KEY", "")
BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")

if not API_KEY or not BASE_ID:
    print("❌ Error: Configura AIRTABLE_API_KEY y AIRTABLE_BASE_ID")
    print("   Ejecuta: source .env && python3 scripts/upload_cvs_to_airtable.py")
    sys.exit(1)

BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

CVS_DIR = Path(__file__).parent.parent / "data" / "cvs"


async def upload_to_catbox(file_path: Path) -> Optional[str]:
    """Sube archivo a catbox.moe y retorna URL pública."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            files = {
                'reqtype': (None, 'fileupload'),
                'fileToUpload': (file_path.name, content, 'application/pdf')
            }
            
            response = await client.post(
                'https://catbox.moe/user/api.php',
                files=files
            )
            
            if response.status_code == 200 and response.text.startswith('https://'):
                return response.text.strip()
            
            print(f"  ⚠️ Catbox respondió: {response.status_code} - {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"  ❌ Error subiendo a catbox: {e}")
        return None


async def get_candidatos():
    """Obtiene todos los candidatos de Airtable."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/Postulaciones",
            headers=HEADERS
        )
        
        if response.status_code != 200:
            print(f"❌ Error obteniendo candidatos: {response.text}")
            return []
        
        return response.json().get("records", [])


async def update_candidato_cv(record_id: str, cv_url: str):
    """Actualiza el campo cv_archivo de un candidato."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        data = {
            "fields": {
                "cv_archivo": [{"url": cv_url}]
            }
        }
        
        response = await client.patch(
            f"{BASE_URL}/Postulaciones/{record_id}",
            headers=HEADERS,
            json=data
        )
        
        return response.status_code == 200


def find_cv_for_candidato(nombre: str, tracking: str) -> Optional[Path]:
    """Busca el CV local que corresponde al candidato."""
    if not CVS_DIR.exists():
        return None
    
    # Buscar por tracking code
    if tracking:
        for f in CVS_DIR.glob(f"*{tracking}*"):
            if f.suffix.lower() == '.pdf':
                return f
    
    # Buscar por nombre
    nombre_parts = nombre.lower().replace(" ", "_").split("_")
    for f in CVS_DIR.iterdir():
        if f.suffix.lower() != '.pdf':
            continue
        fname_lower = f.name.lower()
        # Si al menos 2 partes del nombre coinciden
        matches = sum(1 for part in nombre_parts if part in fname_lower)
        if matches >= 2:
            return f
    
    return None


async def main():
    print("=" * 60)
    print("📤 Subiendo CVs locales a Airtable")
    print("=" * 60)
    
    # Obtener candidatos
    print("\n📋 Obteniendo candidatos de Airtable...")
    candidatos = await get_candidatos()
    print(f"   Encontrados: {len(candidatos)} candidatos")
    
    # Listar CVs locales
    cvs_locales = list(CVS_DIR.glob("*.pdf")) if CVS_DIR.exists() else []
    print(f"   CVs locales: {len(cvs_locales)} archivos")
    
    subidos = 0
    errores = 0
    ya_tienen = 0
    sin_cv = 0
    
    print("\n" + "-" * 60)
    
    for record in candidatos:
        fields = record.get("fields", {})
        record_id = record["id"]
        nombre = fields.get("nombre_completo", "Sin nombre")
        tracking = fields.get("codigo_tracking", "")
        cv_existente = fields.get("cv_archivo")
        
        # Si ya tiene CV en Airtable, skip
        if cv_existente:
            print(f"✅ {nombre}: Ya tiene CV en Airtable")
            ya_tienen += 1
            continue
        
        # Buscar CV local
        cv_local = find_cv_for_candidato(nombre, tracking)
        
        if not cv_local:
            print(f"⚠️  {nombre}: Sin CV local encontrado")
            sin_cv += 1
            continue
        
        print(f"📤 {nombre}:")
        print(f"   Archivo: {cv_local.name}")
        
        # Subir a catbox
        public_url = await upload_to_catbox(cv_local)
        
        if not public_url:
            print(f"   ❌ Error subiendo a catbox")
            errores += 1
            continue
        
        print(f"   URL: {public_url}")
        
        # Actualizar en Airtable
        success = await update_candidato_cv(record_id, public_url)
        
        if success:
            print(f"   ✅ Actualizado en Airtable")
            subidos += 1
        else:
            print(f"   ❌ Error actualizando Airtable")
            errores += 1
        
        # Pequeña pausa para no saturar APIs
        await asyncio.sleep(1)
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"   ✅ Subidos exitosamente: {subidos}")
    print(f"   ✅ Ya tenían CV: {ya_tienen}")
    print(f"   ⚠️  Sin CV local: {sin_cv}")
    print(f"   ❌ Errores: {errores}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

