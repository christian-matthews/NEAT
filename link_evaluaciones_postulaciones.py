#!/usr/bin/env python3
"""
1. Crear campo 'postulacion' en Evaluaciones_AI
2. Vincular cada evaluación a su postulación correspondiente
"""

import os
import requests
import time
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "plataforma_reclutamiento", ".env")
load_dotenv(env_path)

API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def get_table_id(table_name):
    """Obtener ID de una tabla"""
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        for t in response.json().get("tables", []):
            if t["name"] == table_name:
                return t["id"]
    return None


def add_link_field(table_id, field_name, linked_table_id):
    """Agregar campo Link"""
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{table_id}/fields"
    payload = {
        "name": field_name,
        "type": "multipleRecordLinks",
        "options": {"linkedTableId": linked_table_id}
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    return response.status_code == 200, response.text


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
    response = requests.patch(url, headers=HEADERS, json={"fields": fields})
    return response.status_code == 200


def main():
    print("=" * 70)
    print("   🔗 VINCULAR EVALUACIONES → POSTULACIONES")
    print("=" * 70)
    print()
    
    # Obtener IDs de tablas
    eval_table_id = get_table_id("Evaluaciones_AI")
    post_table_id = get_table_id("Postulaciones")
    
    print(f"   Evaluaciones_AI: {eval_table_id}")
    print(f"   Postulaciones: {post_table_id}")
    print()
    
    # 1. Crear campo 'postulacion' en Evaluaciones_AI
    print("1️⃣  Creando campo 'postulacion'...")
    success, msg = add_link_field(eval_table_id, "postulacion", post_table_id)
    if success:
        print("   ✅ Campo creado")
    elif "already exists" in msg.lower() or "DUPLICATE" in msg:
        print("   ⚠️  Ya existe")
    else:
        print(f"   ❌ Error: {msg[:100]}")
    print()
    
    # 2. Obtener postulaciones y crear mapa tracking → ID
    print("2️⃣  Cargando postulaciones...")
    postulaciones = get_all_records("Postulaciones")
    tracking_to_id = {}
    for p in postulaciones:
        tracking = p["fields"].get("codigo_tracking", "")
        if tracking:
            tracking_to_id[tracking] = p["id"]
    print(f"   {len(tracking_to_id)} postulaciones cargadas")
    print()
    
    # 3. Actualizar evaluaciones
    print("3️⃣  Vinculando evaluaciones...")
    evaluaciones = get_all_records("Evaluaciones_AI")
    
    updated = 0
    for ev in evaluaciones:
        ev_id = ev["id"]
        fields = ev["fields"]
        
        # El tracking está en el campo 'candidato' (texto)
        candidato_tracking = fields.get("candidato", "")
        
        if candidato_tracking and candidato_tracking in tracking_to_id:
            post_id = tracking_to_id[candidato_tracking]
            success = update_record("Evaluaciones_AI", ev_id, {
                "postulacion": [post_id]
            })
            if success:
                score = fields.get("score_promedio", "?")
                print(f"   ✅ {candidato_tracking} (score: {score}) → {post_id[:12]}...")
                updated += 1
            time.sleep(0.1)
    
    print()
    print("=" * 70)
    print(f"   ✅ Evaluaciones vinculadas: {updated}/{len(evaluaciones)}")
    print("=" * 70)


if __name__ == "__main__":
    main()




