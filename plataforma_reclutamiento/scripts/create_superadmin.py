#!/usr/bin/env python3
"""
Script para crear el primer usuario superadmin en Airtable.
Ejecutar una vez después de crear la tabla Usuarios.
"""

import os
import hashlib
import httpx
from getpass import getpass

# Configuración
API_KEY = os.getenv("AIRTABLE_API_KEY", "")
BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")

if not API_KEY or not BASE_ID:
    # Intentar leer de .env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    if key == "AIRTABLE_API_KEY":
                        API_KEY = value
                    elif key == "AIRTABLE_BASE_ID":
                        BASE_ID = value

BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def hash_password(password: str) -> str:
    """Hashea una contraseña."""
    salt = "neat-platform-salt"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def create_superadmin():
    print("=" * 60)
    print("🔐 CREAR USUARIO SUPERADMIN")
    print("=" * 60)
    print()
    
    # Solicitar datos
    email = input("Email: ").strip()
    nombre = input("Nombre completo: ").strip()
    password = getpass("Contraseña: ")
    password_confirm = getpass("Confirmar contraseña: ")
    
    if password != password_confirm:
        print("\n❌ Las contraseñas no coinciden")
        return
    
    if len(password) < 6:
        print("\n❌ La contraseña debe tener al menos 6 caracteres")
        return
    
    # Crear usuario
    print("\n📤 Creando usuario en Airtable...")
    
    fields = {
        "email": email,
        "nombre_completo": nombre,
        "password_hash": hash_password(password),
        "rol": "superadmin",
        "activo": True
    }
    
    try:
        response = httpx.post(
            f"{BASE_URL}/Usuarios",
            headers=HEADERS,
            json={"fields": fields},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n" + "=" * 60)
            print("✅ USUARIO SUPERADMIN CREADO EXITOSAMENTE")
            print("=" * 60)
            print(f"   ID: {data['id']}")
            print(f"   Email: {email}")
            print(f"   Rol: superadmin")
            print()
            print("Ahora puedes iniciar sesión en http://localhost:5173/login")
        else:
            error = response.json()
            print(f"\n❌ Error: {error}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    create_superadmin()

