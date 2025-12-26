#!/usr/bin/env python3
"""
Setup completo de tablas para THE WINGMAN según AIRTABLE_SETUP.md
"""

import os
import requests
import time
from dotenv import load_dotenv

# Cargar .env
env_path = os.path.join(os.path.dirname(__file__), "plataforma_reclutamiento", ".env")
load_dotenv(env_path)

API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

BASE_URL = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"


def get_existing_tables():
    """Obtener tablas existentes"""
    response = requests.get(BASE_URL, headers=HEADERS)
    if response.status_code == 200:
        return {t["name"]: t for t in response.json().get("tables", [])}
    return {}


def create_table(name, fields, description=""):
    """Crear una tabla"""
    payload = {
        "name": name,
        "description": description,
        "fields": fields
    }
    response = requests.post(BASE_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print(f"   ✅ Tabla '{name}' creada")
        return response.json()
    else:
        print(f"   ❌ Error creando '{name}': {response.text[:200]}")
        return None


def add_field_to_table(table_id, field_config):
    """Agregar campo a tabla existente"""
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{table_id}/fields"
    response = requests.post(url, headers=HEADERS, json=field_config)
    if response.status_code == 200:
        print(f"      ✅ Campo '{field_config['name']}' agregado")
        return True
    else:
        if "already exists" in response.text.lower() or "DUPLICATE" in response.text:
            print(f"      ⚠️  Campo '{field_config['name']}' ya existe")
            return True
        print(f"      ❌ Error: {response.text[:150]}")
        return False


def main():
    print("=" * 70)
    print("   🚀 SETUP THE WINGMAN - Airtable Tables")
    print("=" * 70)
    print()
    
    existing = get_existing_tables()
    print(f"📊 Tablas existentes: {list(existing.keys())}")
    print()
    
    # =========================================================================
    # 1. CARGOS
    # =========================================================================
    print("1️⃣  TABLA: Cargos")
    if "Cargos" in existing:
        print("   ⚠️  Ya existe")
    else:
        create_table("Cargos", [
            {"name": "codigo", "type": "singleLineText", "description": "Código único (ej: DEV-001)"},
            {"name": "nombre", "type": "singleLineText", "description": "Nombre del cargo"},
            {"name": "descripcion", "type": "multilineText", "description": "Descripción detallada"},
            {"name": "vacantes", "type": "number", "options": {"precision": 0}, "description": "Cantidad de vacantes"},
            {"name": "activo", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
            {"name": "fecha_activacion", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
        ], "Catálogo maestro de posiciones/vacantes")
    time.sleep(0.3)
    print()
    
    # =========================================================================
    # 2. PROCESOS
    # =========================================================================
    print("2️⃣  TABLA: Procesos")
    if "Procesos" in existing:
        print("   ⚠️  Ya existe")
    else:
        create_table("Procesos", [
            {"name": "codigo_proceso", "type": "singleLineText", "description": "Código único (ej: DEV-001-P001)"},
            {"name": "estado", "type": "singleSelect", "options": {
                "choices": [
                    {"name": "publicado", "color": "greenLight2"},
                    {"name": "en_revision", "color": "blueLight2"},
                    {"name": "en_entrevistas", "color": "yellowLight2"},
                    {"name": "finalizado", "color": "grayLight2"},
                    {"name": "cancelado", "color": "redLight2"}
                ]
            }},
            {"name": "fecha_inicio", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "fecha_cierre", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "vacantes_proceso", "type": "number", "options": {"precision": 0}},
            {"name": "avances", "type": "multilineText"},
            {"name": "bloqueos", "type": "multilineText"},
            {"name": "proximos_pasos", "type": "multilineText"},
            {"name": "notas", "type": "multilineText"},
            {"name": "resultado", "type": "multilineText"},
        ], "Procesos de reclutamiento activos")
    time.sleep(0.3)
    print()
    
    # =========================================================================
    # 3. POSTULACIONES
    # =========================================================================
    print("3️⃣  TABLA: Postulaciones")
    if "Postulaciones" in existing:
        print("   ⚠️  Ya existe")
    else:
        create_table("Postulaciones", [
            {"name": "codigo_tracking", "type": "singleLineText", "description": "Código único TW-POST-xxx"},
            {"name": "nombre_completo", "type": "singleLineText"},
            {"name": "email", "type": "email"},
            {"name": "telefono", "type": "phoneNumber"},
            {"name": "cv_archivo", "type": "multipleAttachments", "description": "CV subido (PDF/DOC)"},
            {"name": "cv_url", "type": "url", "description": "URL del CV"},
            {"name": "estado_candidato", "type": "singleSelect", "options": {
                "choices": [
                    {"name": "nuevo", "color": "blueLight2"},
                    {"name": "en_revision", "color": "cyanLight2"},
                    {"name": "preseleccionado", "color": "tealLight2"},
                    {"name": "entrevista", "color": "yellowLight2"},
                    {"name": "finalista", "color": "orangeLight2"},
                    {"name": "seleccionado", "color": "greenLight2"},
                    {"name": "descartado", "color": "redLight2"}
                ]
            }},
            {"name": "score_ai", "type": "number", "options": {"precision": 0}, "description": "Score del motor IA (0-100)"},
            {"name": "notas", "type": "multilineText", "description": "Notas del reclutador"},
            {"name": "tags", "type": "multipleSelects", "options": {
                "choices": [
                    {"name": "experiencia_senior", "color": "blueLight2"},
                    {"name": "experiencia_junior", "color": "cyanLight2"},
                    {"name": "ingles_avanzado", "color": "greenLight2"},
                    {"name": "disponibilidad_inmediata", "color": "yellowLight2"},
                    {"name": "pretension_alta", "color": "redLight2"},
                    {"name": "referido", "color": "purpleLight2"}
                ]
            }},
        ], "Candidatos que postulan a procesos")
    time.sleep(0.3)
    print()
    
    # =========================================================================
    # 4. HISTORIAL_ESTADOS
    # =========================================================================
    print("4️⃣  TABLA: Historial_Estados")
    if "Historial_Estados" in existing:
        print("   ⚠️  Ya existe")
    else:
        create_table("Historial_Estados", [
            {"name": "estado_anterior", "type": "singleLineText"},
            {"name": "estado_nuevo", "type": "singleLineText"},
            {"name": "notas", "type": "multilineText", "description": "Razón del cambio"},
        ], "Auditoría de cambios de estado")
    time.sleep(0.3)
    print()
    
    # =========================================================================
    # 5. SOLICITUDES_GDPR (Opcional)
    # =========================================================================
    print("5️⃣  TABLA: Solicitudes_GDPR")
    if "Solicitudes_GDPR" in existing:
        print("   ⚠️  Ya existe")
    else:
        create_table("Solicitudes_GDPR", [
            {"name": "email", "type": "email"},
            {"name": "tipo_identificacion", "type": "singleSelect", "options": {
                "choices": [
                    {"name": "cedula", "color": "blueLight2"},
                    {"name": "pasaporte", "color": "greenLight2"}
                ]
            }},
            {"name": "numero_identificacion", "type": "singleLineText"},
            {"name": "nacionalidad", "type": "singleLineText"},
            {"name": "motivo", "type": "multilineText"},
            {"name": "estado", "type": "singleSelect", "options": {
                "choices": [
                    {"name": "pendiente", "color": "yellowLight2"},
                    {"name": "procesada", "color": "greenLight2"},
                    {"name": "rechazada", "color": "redLight2"}
                ]
            }},
        ], "Solicitudes de eliminación de datos (GDPR)")
    time.sleep(0.3)
    print()
    
    print("=" * 70)
    print("   ✅ SETUP COMPLETADO")
    print("=" * 70)
    print()
    print("📝 SIGUIENTE PASO: Configurar relaciones (Links) manualmente en Airtable:")
    print()
    print("   1. Procesos.cargo → Link to Cargos")
    print("   2. Procesos.usuario_asignado → Link to Usuarios")
    print("   3. Postulaciones.proceso → Link to Procesos")
    print("   4. Postulaciones.cargo → Link to Cargos")
    print("   5. Postulaciones.evaluacion → Link to Evaluaciones_AI")
    print("   6. Historial_Estados.proceso → Link to Procesos")
    print("   7. Historial_Estados.usuario → Link to Usuarios")
    print()


if __name__ == "__main__":
    main()



