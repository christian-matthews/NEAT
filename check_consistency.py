#!/usr/bin/env python3
"""
Verificar consistencia de datos entre tablas
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
    """Obtener todos los registros de una tabla"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}"
    all_records = []
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
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    
    return all_records


def main():
    print("=" * 70)
    print("   🔍 VERIFICACIÓN DE CONSISTENCIA - THE WINGMAN")
    print("=" * 70)
    print()
    
    # Obtener datos
    print("📥 Cargando datos...")
    cargos = get_all_records("Cargos")
    procesos = get_all_records("Procesos_Reclutamiento")
    candidatos = get_all_records("Candidatos")
    evaluaciones = get_all_records("Evaluaciones_AI")
    
    print(f"   • Cargos: {len(cargos)}")
    print(f"   • Procesos_Reclutamiento: {len(procesos)}")
    print(f"   • Candidatos: {len(candidatos)}")
    print(f"   • Evaluaciones_AI: {len(evaluaciones)}")
    print()
    
    # =========================================================================
    # 1. CARGO
    # =========================================================================
    print("=" * 70)
    print("1️⃣  CARGO")
    print("=" * 70)
    if cargos:
        cargo = cargos[0]
        cargo_id = cargo["id"]
        cargo_fields = cargo["fields"]
        print(f"   ID: {cargo_id}")
        print(f"   Código: {cargo_fields.get('codigo', '?')}")
        print(f"   Nombre: {cargo_fields.get('nombre', '?')}")
        print(f"   Activo: {cargo_fields.get('activo', False)}")
    print()
    
    # =========================================================================
    # 2. PROCESO
    # =========================================================================
    print("=" * 70)
    print("2️⃣  PROCESO DE RECLUTAMIENTO")
    print("=" * 70)
    if procesos:
        proceso = procesos[0]
        proceso_id = proceso["id"]
        proceso_fields = proceso["fields"]
        print(f"   ID: {proceso_id}")
        print(f"   Código: {proceso_fields.get('codigo_proceso', '?')}")
        print(f"   Estado: {proceso_fields.get('estado', '?')}")
        
        # Verificar link a Cargo
        cargo_link = proceso_fields.get("cargo", [])
        if cargo_link:
            print(f"   ✅ Vinculado a Cargo: {cargo_link}")
        else:
            print(f"   ❌ NO VINCULADO a ningún cargo")
        
        # Verificar candidatos vinculados
        candidatos_link = proceso_fields.get("Candidatos", [])
        print(f"   Candidatos vinculados: {len(candidatos_link)}")
    print()
    
    # =========================================================================
    # 3. CANDIDATOS
    # =========================================================================
    print("=" * 70)
    print("3️⃣  CANDIDATOS (16)")
    print("=" * 70)
    
    candidatos_con_proceso = 0
    candidatos_con_cargo = 0
    candidatos_sin_vinculo = []
    
    for cand in candidatos:
        fields = cand["fields"]
        nombre = fields.get("nombre_completo", "?")
        tracking = fields.get("codigo_tracking", "?")
        
        proceso_link = fields.get("proceso", [])
        cargo_link = fields.get("cargo", [])
        
        if proceso_link:
            candidatos_con_proceso += 1
        if cargo_link:
            candidatos_con_cargo += 1
        
        if not proceso_link and not cargo_link:
            candidatos_sin_vinculo.append(nombre)
    
    print(f"   ✅ Con vínculo a Proceso: {candidatos_con_proceso}/{len(candidatos)}")
    print(f"   ✅ Con vínculo a Cargo: {candidatos_con_cargo}/{len(candidatos)}")
    
    if candidatos_sin_vinculo:
        print(f"   ⚠️  Sin vínculos: {len(candidatos_sin_vinculo)}")
        for name in candidatos_sin_vinculo[:5]:
            print(f"      - {name}")
    print()
    
    # =========================================================================
    # 4. EVALUACIONES
    # =========================================================================
    print("=" * 70)
    print("4️⃣  EVALUACIONES_AI (12)")
    print("=" * 70)
    
    eval_con_candidato = 0
    eval_sin_candidato = []
    
    # Crear mapa de tracking -> candidato_id
    tracking_to_id = {}
    for cand in candidatos:
        tracking = cand["fields"].get("codigo_tracking", "")
        tracking_to_id[tracking] = cand["id"]
    
    for ev in evaluaciones:
        fields = ev["fields"]
        candidato_ref = fields.get("candidato", "")
        candidato_link = fields.get("candidato_link", [])  # Nuevo campo link
        score = fields.get("score_promedio", "?")
        
        # Verificar si tiene link (en cualquiera de los dos campos)
        if isinstance(candidato_link, list) and len(candidato_link) > 0:
            eval_con_candidato += 1
        elif isinstance(candidato_ref, list) and len(candidato_ref) > 0:
            eval_con_candidato += 1
        elif isinstance(candidato_ref, str) and candidato_ref:
            # Es texto (código tracking), no link
            if candidato_ref in tracking_to_id:
                eval_sin_candidato.append(f"{candidato_ref} (score: {score}) - TEXTO, no Link")
            else:
                eval_sin_candidato.append(f"{candidato_ref} (score: {score}) - NO EXISTE")
        else:
            eval_sin_candidato.append(f"Sin referencia (score: {score})")
    
    print(f"   ✅ Con Link a Candidato: {eval_con_candidato}/{len(evaluaciones)}")
    
    if eval_sin_candidato:
        print(f"   ⚠️  Sin Link correcto: {len(eval_sin_candidato)}")
        for item in eval_sin_candidato[:8]:
            print(f"      - {item}")
    print()
    
    # =========================================================================
    # RESUMEN
    # =========================================================================
    print("=" * 70)
    print("📊 RESUMEN DE CONSISTENCIA")
    print("=" * 70)
    
    issues = []
    
    if candidatos_con_proceso < len(candidatos):
        issues.append(f"❌ {len(candidatos) - candidatos_con_proceso} candidatos sin vínculo a Proceso")
    
    if candidatos_con_cargo < len(candidatos):
        issues.append(f"❌ {len(candidatos) - candidatos_con_cargo} candidatos sin vínculo a Cargo")
    
    if eval_con_candidato < len(evaluaciones):
        issues.append(f"❌ {len(evaluaciones) - eval_con_candidato} evaluaciones sin Link a Candidato")
    
    if not procesos or not procesos[0]["fields"].get("cargo"):
        issues.append("❌ Proceso no vinculado a Cargo")
    
    if issues:
        print("   PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("   ✅ TODO CONSISTENTE")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()

