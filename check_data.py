#!/usr/bin/env python3
"""
Revisar datos cargados en todas las tablas de Airtable
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


def get_table_records(table_name):
    """Obtener todos los registros de una tabla"""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_name}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("records", [])
    return []


def main():
    print("=" * 70)
    print("   📊 REVISIÓN DE DATOS - THE WINGMAN")
    print("=" * 70)
    print()
    
    tables = [
        "Usuarios",
        "Cargos", 
        "Procesos",
        "Postulaciones",
        "Evaluaciones_AI",
        "Historial_Estados",
        "Candidatos",
        "Procesos_Reclutamiento"
    ]
    
    for table in tables:
        records = get_table_records(table)
        print(f"📋 {table}: {len(records)} registro(s)")
        
        if records:
            print("-" * 50)
            for i, rec in enumerate(records[:5], 1):  # Mostrar max 5
                fields = rec.get("fields", {})
                rec_id = rec.get("id", "")
                
                # Mostrar campos principales
                if table == "Usuarios":
                    print(f"   {i}. {fields.get('email', '?')} | {fields.get('nombre_completo', '?')} | rol: {fields.get('rol', '?')}")
                elif table == "Cargos":
                    print(f"   {i}. [{fields.get('codigo', '?')}] {fields.get('nombre', '?')} | vacantes: {fields.get('vacantes', 0)} | activo: {fields.get('activo', False)}")
                elif table == "Procesos":
                    print(f"   {i}. [{fields.get('codigo_proceso', '?')}] estado: {fields.get('estado', '?')} | vacantes: {fields.get('vacantes_proceso', 0)}")
                    if fields.get('cargo'):
                        print(f"      → cargo: {fields.get('cargo')}")
                    if fields.get('usuario_asignado'):
                        print(f"      → asignado: {fields.get('usuario_asignado')}")
                elif table == "Postulaciones":
                    print(f"   {i}. {fields.get('nombre_completo', '?')} | {fields.get('email', '?')} | estado: {fields.get('estado_candidato', '?')}")
                elif table == "Evaluaciones_AI":
                    print(f"   {i}. score: {fields.get('score_promedio', fields.get('score_total', '?'))} | candidato: {fields.get('candidato', '?')}")
                elif table == "Candidatos":
                    print(f"   {i}. {fields.get('nombre_completo', '?')} | {fields.get('email', '?')} | tracking: {fields.get('codigo_tracking', '?')}")
                elif table == "Procesos_Reclutamiento":
                    print(f"   {i}. [{fields.get('codigo_proceso', '?')}] estado: {fields.get('estado', '?')}")
                else:
                    # Genérico
                    keys = list(fields.keys())[:3]
                    vals = [f"{k}: {fields.get(k)}" for k in keys]
                    print(f"   {i}. {' | '.join(vals)}")
            
            if len(records) > 5:
                print(f"   ... y {len(records) - 5} más")
        
        print()
    
    print("=" * 70)


if __name__ == "__main__":
    main()




