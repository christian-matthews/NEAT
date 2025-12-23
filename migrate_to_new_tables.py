#!/usr/bin/env python3
"""
Migrar datos de tablas viejas a nuevas:
- Procesos_Reclutamiento → Procesos
- Candidatos → Postulaciones

Y actualizar las referencias en Evaluaciones_AI
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
            print(f"Error obteniendo {table_name}: {response.text}")
            return []
        data = response.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records


def create_record(table_name, fields):
    """Crear un registro"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}"
    payload = {"fields": fields}
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"   Error creando en {table_name}: {response.text[:150]}")
        return None


def update_record(table_name, record_id, fields):
    """Actualizar un registro"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}/{record_id}"
    payload = {"fields": fields}
    response = requests.patch(url, headers=HEADERS, json=payload)
    return response.status_code == 200


def get_table_id(table_name):
    """Obtener ID de una tabla"""
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        for t in response.json().get("tables", []):
            if t["name"] == table_name:
                return t["id"]
    return None


def main():
    print("=" * 70)
    print("   🚀 MIGRACIÓN DE DATOS")
    print("   Procesos_Reclutamiento → Procesos")
    print("   Candidatos → Postulaciones")
    print("=" * 70)
    print()
    
    # =========================================================================
    # 1. MIGRAR PROCESOS_RECLUTAMIENTO → PROCESOS
    # =========================================================================
    print("1️⃣  MIGRANDO PROCESOS...")
    print("-" * 50)
    
    procesos_viejos = get_all_records("Procesos_Reclutamiento")
    print(f"   Procesos a migrar: {len(procesos_viejos)}")
    
    # Mapa de ID viejo → ID nuevo
    proceso_id_map = {}
    
    for proc in procesos_viejos:
        old_id = proc["id"]
        fields = proc["fields"]
        
        # Mapear estados viejos a nuevos
        estado_map = {
            "en_proceso": "en_revision",
            "publicado": "publicado",
            "finalizado": "finalizado",
            "cancelado": "cancelado",
        }
        old_estado = fields.get("estado", "publicado")
        new_estado = estado_map.get(old_estado, "publicado")
        
        # Preparar campos para nueva tabla
        new_fields = {
            "codigo_proceso": fields.get("codigo_proceso", ""),
            "estado": new_estado,
            "vacantes_proceso": fields.get("vacantes_proceso", 1),
            "avances": fields.get("avances", ""),
            "bloqueos": fields.get("bloqueos", ""),
            "proximos_pasos": fields.get("proximos_pasos", ""),
            "notas": fields.get("notas", ""),
            "resultado": fields.get("resultado", ""),
        }
        
        # Copiar fechas si existen
        if fields.get("fecha_inicio"):
            new_fields["fecha_inicio"] = fields.get("fecha_inicio")
        if fields.get("fecha_cierre"):
            new_fields["fecha_cierre"] = fields.get("fecha_cierre")
        
        # Copiar link a Cargo
        if fields.get("cargo"):
            new_fields["cargo"] = fields.get("cargo")
        
        # Crear en nueva tabla
        result = create_record("Procesos", new_fields)
        if result:
            new_id = result["id"]
            proceso_id_map[old_id] = new_id
            print(f"   ✅ {fields.get('codigo_proceso')} → {new_id[:12]}...")
        else:
            print(f"   ❌ Error migrando: {fields.get('codigo_proceso')}")
        
        time.sleep(0.2)
    
    print()
    
    # =========================================================================
    # 2. MIGRAR CANDIDATOS → POSTULACIONES
    # =========================================================================
    print("2️⃣  MIGRANDO CANDIDATOS → POSTULACIONES...")
    print("-" * 50)
    
    candidatos = get_all_records("Candidatos")
    print(f"   Candidatos a migrar: {len(candidatos)}")
    
    # Mapa de ID viejo → ID nuevo
    candidato_id_map = {}
    
    for cand in candidatos:
        old_id = cand["id"]
        fields = cand["fields"]
        
        # Preparar campos
        new_fields = {
            "codigo_tracking": fields.get("codigo_tracking", ""),
            "nombre_completo": fields.get("nombre_completo", ""),
            "email": fields.get("email", ""),
            "telefono": fields.get("telefono", ""),
            "estado_candidato": "nuevo",  # Default
            "notas": "",
        }
        
        # URL del CV
        if fields.get("cv_url"):
            new_fields["cv_url"] = fields.get("cv_url")
        
        # Copiar link a Cargo (si existe en la nueva tabla)
        if fields.get("cargo"):
            new_fields["cargo"] = fields.get("cargo")
        
        # Link a Proceso (convertir de viejo a nuevo)
        if fields.get("proceso"):
            old_proceso_ids = fields.get("proceso", [])
            new_proceso_ids = []
            for old_pid in old_proceso_ids:
                if old_pid in proceso_id_map:
                    new_proceso_ids.append(proceso_id_map[old_pid])
            if new_proceso_ids:
                new_fields["proceso"] = new_proceso_ids
        
        # Crear en nueva tabla
        result = create_record("Postulaciones", new_fields)
        if result:
            new_id = result["id"]
            candidato_id_map[old_id] = new_id
            print(f"   ✅ {fields.get('nombre_completo', '?')[:25]} → {new_id[:12]}...")
        else:
            print(f"   ❌ Error: {fields.get('nombre_completo', '?')}")
        
        time.sleep(0.2)
    
    print()
    
    # =========================================================================
    # 3. ACTUALIZAR EVALUACIONES_AI
    # =========================================================================
    print("3️⃣  ACTUALIZANDO EVALUACIONES_AI...")
    print("-" * 50)
    
    evaluaciones = get_all_records("Evaluaciones_AI")
    print(f"   Evaluaciones a actualizar: {len(evaluaciones)}")
    
    updated = 0
    for ev in evaluaciones:
        ev_id = ev["id"]
        fields = ev["fields"]
        
        # Obtener el candidato viejo (del campo candidato_link)
        old_candidato_ids = fields.get("candidato_link", [])
        
        if old_candidato_ids:
            # Buscar el nuevo ID
            new_ids = []
            for old_cid in old_candidato_ids:
                if old_cid in candidato_id_map:
                    new_ids.append(candidato_id_map[old_cid])
            
            if new_ids:
                # Crear link a la nueva tabla Postulaciones
                # Nota: necesitamos agregar un campo nuevo porque el link actual apunta a Candidatos
                success = update_record("Evaluaciones_AI", ev_id, {
                    "postulacion": new_ids
                })
                if success:
                    updated += 1
                    print(f"   ✅ Evaluación {ev_id[:12]}...")
        
        time.sleep(0.1)
    
    print(f"   Actualizadas: {updated}/{len(evaluaciones)}")
    print()
    
    # =========================================================================
    # RESUMEN
    # =========================================================================
    print("=" * 70)
    print("   ✅ MIGRACIÓN COMPLETADA")
    print("=" * 70)
    print()
    print(f"   📊 Procesos migrados: {len(proceso_id_map)}")
    print(f"   📊 Postulaciones migradas: {len(candidato_id_map)}")
    print(f"   📊 Evaluaciones actualizadas: {updated}")
    print()
    print("   📝 SIGUIENTE PASO (manual en Airtable):")
    print("   1. Verificar que los datos estén correctos en Procesos y Postulaciones")
    print("   2. Eliminar tabla 'Procesos_Reclutamiento'")
    print("   3. Eliminar tabla 'Candidatos'")
    print()


if __name__ == "__main__":
    main()

