#!/usr/bin/env python3
"""
Limpiar duplicados en Postulaciones y vincular Evaluaciones
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


def delete_records(table_name, record_ids):
    """Eliminar registros en batch (max 10 por request)"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}"
    deleted = 0
    
    for i in range(0, len(record_ids), 10):
        batch = record_ids[i:i+10]
        params = "&".join([f"records[]={rid}" for rid in batch])
        response = requests.delete(f"{url}?{params}", headers=HEADERS)
        if response.status_code == 200:
            deleted += len(batch)
        else:
            print(f"   Error eliminando: {response.text[:100]}")
        time.sleep(0.3)
    
    return deleted


def main():
    print("=" * 70)
    print("   🧹 LIMPIAR DUPLICADOS EN POSTULACIONES")
    print("=" * 70)
    print()
    
    # Obtener postulaciones
    postulaciones = get_all_records("Postulaciones")
    print(f"📋 Total postulaciones: {len(postulaciones)}")
    
    # Encontrar duplicados por codigo_tracking
    tracking_map = {}
    for p in postulaciones:
        tracking = p["fields"].get("codigo_tracking", "")
        if tracking:
            if tracking not in tracking_map:
                tracking_map[tracking] = []
            tracking_map[tracking].append(p["id"])
    
    # Identificar duplicados (quedarse con el primero)
    to_delete = []
    unique_ids = {}
    
    for tracking, ids in tracking_map.items():
        unique_ids[tracking] = ids[0]  # Guardar el primero
        if len(ids) > 1:
            to_delete.extend(ids[1:])  # Eliminar los demás
    
    print(f"   Únicos: {len(tracking_map)}")
    print(f"   Duplicados a eliminar: {len(to_delete)}")
    print()
    
    if to_delete:
        print("🗑️  Eliminando duplicados...")
        deleted = delete_records("Postulaciones", to_delete)
        print(f"   ✅ Eliminados: {deleted}")
    
    print()
    print("=" * 70)
    print("   ✅ LIMPIEZA COMPLETADA")
    print("=" * 70)
    
    # Mostrar mapeo para uso posterior
    print()
    print(f"📊 Postulaciones únicas: {len(unique_ids)}")


if __name__ == "__main__":
    main()


