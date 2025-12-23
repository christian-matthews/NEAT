#!/usr/bin/env python3
"""
Script para actualizar las URLs de CVs en Airtable
"""

import os
import httpx

# Configuración - usar variables de entorno
API_KEY = os.getenv("AIRTABLE_API_KEY", "")
BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")
BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}"

if not API_KEY or not BASE_ID:
    print("Error: Configura AIRTABLE_API_KEY y AIRTABLE_BASE_ID")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

CVS_DIR = "CVs_FIN-002_2025-12-10"

def get_cv_files():
    """Obtener mapeo de tracking code a archivo PDF"""
    cv_map = {}
    for f in os.listdir(CVS_DIR):
        if f.endswith('.pdf'):
            # Extraer tracking code
            tracking = f.split('_')[0]
            cv_map[tracking] = f
    return cv_map

def get_candidates():
    """Obtener todos los candidatos de Airtable"""
    all_records = []
    offset = None
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
            
        response = httpx.get(
            f"{BASE_URL}/Candidatos",
            headers=HEADERS,
            params=params,
            timeout=30
        )
        
        data = response.json()
        all_records.extend(data.get("records", []))
        
        offset = data.get("offset")
        if not offset:
            break
    
    return all_records

def update_candidate_cv(record_id, cv_filename):
    """Actualizar el CV URL de un candidato"""
    # La URL será servida por la API local
    cv_url = f"http://localhost:8000/files/{cv_filename}"
    
    response = httpx.patch(
        f"{BASE_URL}/Candidatos/{record_id}",
        headers=HEADERS,
        json={"fields": {"cv_url": cv_url}},
        timeout=30
    )
    
    return response.status_code == 200

def main():
    print("=" * 60)
    print("📄 ACTUALIZANDO URLs DE CVs")
    print("=" * 60)
    print()
    
    # Obtener mapeo de CVs
    cv_map = get_cv_files()
    print(f"📂 {len(cv_map)} archivos PDF encontrados")
    
    # Obtener candidatos
    candidates = get_candidates()
    print(f"👥 {len(candidates)} candidatos en Airtable")
    print()
    
    # Actualizar cada candidato
    updated = 0
    not_found = 0
    
    for candidate in candidates:
        record_id = candidate["id"]
        fields = candidate["fields"]
        tracking = fields.get("codigo_tracking", "")
        name = fields.get("nombre_completo", "N/A")
        current_cv = fields.get("cv_url", "")
        
        # Buscar CV correspondiente
        cv_file = cv_map.get(tracking)
        
        if cv_file:
            if not current_cv:  # Solo actualizar si no tiene CV
                success = update_candidate_cv(record_id, cv_file)
                if success:
                    print(f"✅ {name}: {cv_file}")
                    updated += 1
                else:
                    print(f"❌ {name}: Error al actualizar")
            else:
                print(f"⏭️  {name}: Ya tiene CV")
        else:
            print(f"⚠️  {name}: No se encontró PDF para {tracking}")
            not_found += 1
    
    print()
    print("=" * 60)
    print(f"✅ COMPLETADO")
    print(f"   - Actualizados: {updated}")
    print(f"   - Sin PDF: {not_found}")
    print("=" * 60)

if __name__ == "__main__":
    main()

