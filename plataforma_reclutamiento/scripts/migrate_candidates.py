#!/usr/bin/env python3
"""
Script de migración de candidatos a Airtable
"""

import os
import json
import csv
import httpx
import sys

# Configuración - usar variables de entorno
API_KEY = os.getenv("AIRTABLE_API_KEY", "")
BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")
BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}"

if not API_KEY or not BASE_ID:
    print("Error: Configura AIRTABLE_API_KEY y AIRTABLE_BASE_ID")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# IDs creados previamente
CARGO_ID = "reciMPYk8IqpbUdpx"
PROCESO_ID = "recuBTSuoYl5B5a9Q"

# Directorio de CVs
CVS_DIR = "CVs_FIN-002_2025-12-10"

def load_existing_evaluations():
    """Cargar evaluaciones existentes del JSON"""
    try:
        with open("candidates_db.json", "r") as f:
            return json.load(f)
    except:
        return {}

def get_cv_files():
    """Obtener lista de CVs únicos (excluir duplicados)"""
    files = os.listdir(CVS_DIR)
    pdfs = [f for f in files if f.endswith('.pdf')]
    
    # Detectar duplicados por nombre
    seen_names = {}
    unique_files = []
    
    for pdf in sorted(pdfs):
        # Extraer nombre del archivo
        parts = pdf.replace('.pdf', '').split('_', 1)
        if len(parts) > 1:
            name = parts[1].replace('_', ' ')
        else:
            name = pdf
        
        # Si ya vimos este nombre, usar el más reciente (por fecha en tracking code)
        if name in seen_names:
            # Comparar fechas (están en el tracking code)
            old_file = seen_names[name]
            old_date = old_file.split('_')[0].split('-')[2:5]  # YYYYMMDD
            new_date = pdf.split('_')[0].split('-')[2:5]
            
            if new_date > old_date:
                # Remover el viejo, agregar el nuevo
                unique_files.remove(old_file)
                unique_files.append(pdf)
                seen_names[name] = pdf
                print(f"  ⚠️  Duplicado detectado: {name}")
                print(f"      Usando versión más reciente: {pdf}")
        else:
            seen_names[name] = pdf
            unique_files.append(pdf)
    
    return unique_files

def parse_tracking_code(filename):
    """Extraer tracking code del nombre del archivo"""
    # Formato: NEAT-POST-20251201-211141_Nombre.pdf
    parts = filename.split('_')[0]
    return parts

def parse_candidate_name(filename):
    """Extraer nombre del candidato del archivo"""
    name_part = filename.replace('.pdf', '').split('_', 1)
    if len(name_part) > 1:
        return name_part[1].replace('_', ' ')
    return filename

def create_candidate(tracking_code, name, email="", phone=""):
    """Crear candidato en Airtable"""
    data = {
        "fields": {
            "codigo_tracking": tracking_code,
            "nombre_completo": name,
            "email": email if email else f"{name.lower().replace(' ', '.')}@pendiente.com",
            "telefono": phone,
            "proceso": [PROCESO_ID],
            "cargo": [CARGO_ID],
            "fecha_postulacion": f"2025-12-{tracking_code.split('-')[2][6:8]}"
        }
    }
    
    response = httpx.post(
        f"{BASE_URL}/Candidatos",
        headers=HEADERS,
        json=data,
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print(f"    Error creando candidato: {response.text}")
        return None

def create_evaluation(candidato_id, tracking_code, eval_data):
    """Crear evaluación en Airtable"""
    if not eval_data or "analysis" not in eval_data:
        return None
    
    analysis = eval_data["analysis"]
    fits = analysis.get("fits", {})
    inference = analysis.get("inference", {})
    
    # Calcular score promedio
    scores = [fits.get(k, {}).get("score", 0) for k in ["admin", "ops", "biz"]]
    score_promedio = int(sum(scores) / len(scores)) if scores else 0
    
    data = {
        "fields": {
            "candidato": tracking_code,
            "candidato_link": [candidato_id],
            "score_promedio": score_promedio,
            "score_admin": fits.get("admin", {}).get("score", 0),
            "score_ops": fits.get("ops", {}).get("score", 0),
            "score_biz": fits.get("biz", {}).get("score", 0),
            "hands_on_index": inference.get("hands_on_index", 0),
            "potential_score": inference.get("potential_score", 0),
            "retention_risk": inference.get("retention_risk", "Bajo"),
            "profile_type": inference.get("profile_type", ""),
            "industry_tier": inference.get("industry_tier", "General"),
            "risk_warning": inference.get("risk_warning", ""),
            "keywords_found_admin": ", ".join(fits.get("admin", {}).get("found", [])),
            "keywords_found_ops": ", ".join(fits.get("ops", {}).get("found", [])),
            "keywords_found_biz": ", ".join(fits.get("biz", {}).get("found", [])),
            "reasoning_admin": fits.get("admin", {}).get("reasoning", ""),
            "reasoning_ops": fits.get("ops", {}).get("reasoning", ""),
            "reasoning_biz": fits.get("biz", {}).get("reasoning", ""),
            "config_version": "1.0"
        }
    }
    
    response = httpx.post(
        f"{BASE_URL}/Evaluaciones_AI",
        headers=HEADERS,
        json=data,
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print(f"    Error creando evaluación: {response.text}")
        return None

def load_csv_data():
    """Cargar datos del CSV"""
    csv_data = {}
    try:
        with open("postulaciones_FIN-002_2025-12-09.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tracking = row.get("Código Tracking", "")
                csv_data[tracking] = {
                    "nombre": row.get("Nombre Completo", ""),
                    "email": row.get("Email", ""),
                    "telefono": row.get("Teléfono", "")
                }
    except Exception as e:
        print(f"Error leyendo CSV: {e}")
    return csv_data

def main():
    print("=" * 60)
    print("🚀 MIGRACIÓN DE CANDIDATOS A AIRTABLE")
    print("=" * 60)
    print()
    
    # Cargar datos existentes
    print("📂 Cargando datos...")
    evaluations = load_existing_evaluations()
    csv_data = load_csv_data()
    cv_files = get_cv_files()
    
    print(f"   - {len(evaluations)} evaluaciones existentes")
    print(f"   - {len(csv_data)} registros en CSV")
    print(f"   - {len(cv_files)} CVs únicos encontrados")
    print()
    
    # Migrar candidatos
    print("👥 Migrando candidatos...")
    print("-" * 60)
    
    created = 0
    errors = 0
    
    for pdf in cv_files:
        tracking = parse_tracking_code(pdf)
        name = parse_candidate_name(pdf)
        
        # Buscar datos adicionales en CSV
        csv_info = csv_data.get(tracking, {})
        email = csv_info.get("email", "")
        phone = csv_info.get("telefono", "")
        
        # Usar nombre del CSV si está disponible
        if csv_info.get("nombre"):
            name = csv_info["nombre"]
        
        print(f"\n📄 {name}")
        print(f"   Tracking: {tracking}")
        
        # Crear candidato
        candidato_id = create_candidate(tracking, name, email, phone)
        
        if candidato_id:
            print(f"   ✅ Candidato creado: {candidato_id}")
            
            # Crear evaluación si existe
            eval_data = evaluations.get(tracking)
            if eval_data:
                eval_id = create_evaluation(candidato_id, tracking, eval_data)
                if eval_id:
                    print(f"   ✅ Evaluación creada: {eval_id}")
                else:
                    print(f"   ⚠️  Sin evaluación (error)")
            else:
                print(f"   ⚠️  Sin evaluación previa (candidato nuevo)")
            
            created += 1
        else:
            print(f"   ❌ Error al crear candidato")
            errors += 1
    
    print()
    print("=" * 60)
    print(f"✅ MIGRACIÓN COMPLETADA")
    print(f"   - Candidatos creados: {created}")
    print(f"   - Errores: {errors}")
    print("=" * 60)

if __name__ == "__main__":
    main()

