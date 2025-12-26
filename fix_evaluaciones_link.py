#!/usr/bin/env python3
"""
Arreglar el campo candidato en Evaluaciones_AI:
1. Buscar el candidato por código tracking
2. Actualizar el campo candidato_link con el ID correcto
"""

import os
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "plataforma_reclutamiento", ".env")
load_dotenv(env_path)

API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def get_all_records(table_name):
    """Obtener todos los registros"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}"
    records = []
    offset = None
    while True:
        params = {}
        if offset:
            params["offset"] = offset
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            return []
        data = response.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records


def update_record(table_name, record_id, fields):
    """Actualizar un registro"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}/{record_id}"
    payload = {"fields": fields}
    response = requests.patch(url, headers=HEADERS, json=payload)
    return response.status_code == 200


def main():
    print("=" * 70)
    print("   🔧 ARREGLAR LINKS EN EVALUACIONES_AI")
    print("=" * 70)
    print()
    
    # Obtener candidatos
    print("📥 Cargando candidatos...")
    candidatos = get_all_records("Candidatos")
    
    # Crear mapa: tracking -> record_id
    tracking_to_id = {}
    for cand in candidatos:
        tracking = cand["fields"].get("codigo_tracking", "")
        if tracking:
            tracking_to_id[tracking] = cand["id"]
    
    print(f"   {len(tracking_to_id)} candidatos con tracking code")
    print()
    
    # Obtener evaluaciones
    print("📥 Cargando evaluaciones...")
    evaluaciones = get_all_records("Evaluaciones_AI")
    print(f"   {len(evaluaciones)} evaluaciones")
    print()
    
    # Arreglar cada evaluación
    print("🔧 Actualizando evaluaciones...")
    print()
    
    updated = 0
    failed = 0
    
    for ev in evaluaciones:
        ev_id = ev["id"]
        fields = ev["fields"]
        candidato_ref = fields.get("candidato", "")
        score = fields.get("score_promedio", "?")
        
        # Si ya es un link, saltar
        if isinstance(candidato_ref, list):
            print(f"   ⏭️  Ya es Link: {ev_id}")
            continue
        
        # Buscar el candidato por tracking
        if candidato_ref in tracking_to_id:
            candidato_id = tracking_to_id[candidato_ref]
            
            # Actualizar el campo candidato_link
            success = update_record("Evaluaciones_AI", ev_id, {
                "candidato_link": [candidato_id]
            })
            
            if success:
                print(f"   ✅ {candidato_ref} → {candidato_id[:10]}... (score: {score})")
                updated += 1
            else:
                print(f"   ❌ Error actualizando: {candidato_ref}")
                failed += 1
        else:
            print(f"   ⚠️  Candidato no encontrado: {candidato_ref}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"   ✅ Actualizadas: {updated}")
    print(f"   ❌ Fallidas: {failed}")
    print("=" * 70)
    print()
    print("📝 NOTA: El campo 'candidato' (texto) aún existe.")
    print("   Puedes eliminarlo manualmente en Airtable.")
    print("   El nuevo campo 'candidato_link' tiene los links correctos.")


if __name__ == "__main__":
    main()



