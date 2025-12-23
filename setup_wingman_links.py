#!/usr/bin/env python3
"""
Crear Links (relaciones) entre tablas de THE WINGMAN
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


def get_table_ids():
    """Obtener IDs de todas las tablas"""
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return {t["name"]: t["id"] for t in response.json().get("tables", [])}
    return {}


def add_link_field(table_id, field_name, linked_table_id, table_name, target_name):
    """Agregar campo Link a una tabla"""
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{table_id}/fields"
    payload = {
        "name": field_name,
        "type": "multipleRecordLinks",
        "options": {
            "linkedTableId": linked_table_id
        }
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print(f"   ✅ {table_name}.{field_name} → {target_name}")
        return True
    elif "already exists" in response.text.lower() or "DUPLICATE" in response.text:
        print(f"   ⚠️  {table_name}.{field_name} ya existe")
        return True
    else:
        print(f"   ❌ Error: {response.text[:150]}")
        return False


def main():
    print("=" * 70)
    print("   🔗 CREAR RELACIONES - THE WINGMAN")
    print("=" * 70)
    print()
    
    tables = get_table_ids()
    print(f"📊 Tablas encontradas: {len(tables)}")
    for name, tid in tables.items():
        print(f"   • {name}: {tid}")
    print()
    
    # Verificar que existan las tablas necesarias
    required = ["Procesos", "Postulaciones", "Historial_Estados", "Cargos", "Usuarios", "Evaluaciones_AI"]
    missing = [t for t in required if t not in tables]
    if missing:
        print(f"❌ Tablas faltantes: {missing}")
        return
    
    print("🔗 Creando Links...")
    print()
    
    # 1. Procesos.cargo → Cargos
    print("1️⃣  Procesos → Cargos")
    add_link_field(tables["Procesos"], "cargo", tables["Cargos"], "Procesos", "Cargos")
    time.sleep(0.3)
    
    # 2. Procesos.usuario_asignado → Usuarios
    print("2️⃣  Procesos → Usuarios")
    add_link_field(tables["Procesos"], "usuario_asignado", tables["Usuarios"], "Procesos", "Usuarios")
    time.sleep(0.3)
    
    # 3. Postulaciones.proceso → Procesos
    print("3️⃣  Postulaciones → Procesos")
    add_link_field(tables["Postulaciones"], "proceso", tables["Procesos"], "Postulaciones", "Procesos")
    time.sleep(0.3)
    
    # 4. Postulaciones.cargo → Cargos
    print("4️⃣  Postulaciones → Cargos")
    add_link_field(tables["Postulaciones"], "cargo", tables["Cargos"], "Postulaciones", "Cargos")
    time.sleep(0.3)
    
    # 5. Postulaciones.evaluacion → Evaluaciones_AI
    print("5️⃣  Postulaciones → Evaluaciones_AI")
    add_link_field(tables["Postulaciones"], "evaluacion", tables["Evaluaciones_AI"], "Postulaciones", "Evaluaciones_AI")
    time.sleep(0.3)
    
    # 6. Historial_Estados.proceso → Procesos
    print("6️⃣  Historial_Estados → Procesos")
    add_link_field(tables["Historial_Estados"], "proceso", tables["Procesos"], "Historial_Estados", "Procesos")
    time.sleep(0.3)
    
    # 7. Historial_Estados.usuario → Usuarios
    print("7️⃣  Historial_Estados → Usuarios")
    add_link_field(tables["Historial_Estados"], "usuario", tables["Usuarios"], "Historial_Estados", "Usuarios")
    
    print()
    print("=" * 70)
    print("   ✅ RELACIONES CREADAS")
    print("=" * 70)


if __name__ == "__main__":
    main()


