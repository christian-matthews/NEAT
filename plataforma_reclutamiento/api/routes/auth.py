"""
Rutas de autenticación.
Maneja login, logout, registro y gestión de sesiones.
"""

from fastapi import APIRouter, HTTPException, Depends, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import secrets
import os

from ..services.airtable import AirtableService

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

# Almacenamiento de sesiones en memoria (en producción usar Redis)
active_sessions: dict = {}

# ============================================================================
# Models
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nombre_completo: str

class UserResponse(BaseModel):
    id: str
    email: str
    nombre_completo: str
    rol: str
    activo: bool

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

class UpdateRoleRequest(BaseModel):
    rol: str

# ============================================================================
# Helpers
# ============================================================================

def get_airtable_service() -> AirtableService:
    """Dependency para obtener el servicio de Airtable."""
    return AirtableService.from_env()

def hash_password(password: str) -> str:
    """Hashea una contraseña con salt."""
    salt = os.getenv("PASSWORD_SALT", "neat-platform-salt")
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash."""
    return hash_password(password) == hashed

def generate_token() -> str:
    """Genera un token de sesión seguro."""
    return secrets.token_urlsafe(32)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    airtable: AirtableService = Depends(get_airtable_service)
) -> Optional[dict]:
    """Obtiene el usuario actual desde el token."""
    if not credentials:
        return None
    
    token = credentials.credentials
    session = active_sessions.get(token)
    
    if not session:
        return None
    
    # Verificar expiración
    if datetime.now() > session["expires_at"]:
        del active_sessions[token]
        return None
    
    return session["user"]

async def require_auth(
    user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """Requiere autenticación."""
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user

async def require_role(roles: list):
    """Factory para requerir roles específicos."""
    async def check_role(user: dict = Depends(require_auth)) -> dict:
        if user["rol"] not in roles:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return user
    return check_role

# ============================================================================
# Endpoints
# ============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """
    Inicia sesión con email y contraseña.
    Retorna un token de sesión.
    """
    try:
        # Buscar usuario por email
        user = await airtable.get_usuario_by_email(data.email)
        
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Verificar contraseña
        if not verify_password(data.password, user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Verificar que esté activo
        if not user.get("activo", False):
            raise HTTPException(status_code=401, detail="Usuario desactivado")
        
        # Generar token
        token = generate_token()
        
        # Guardar sesión (expira en 24 horas)
        expires_at = datetime.now() + timedelta(hours=24)
        active_sessions[token] = {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "nombre_completo": user["nombre_completo"],
                "rol": user["rol"],
                "activo": user["activo"]
            },
            "expires_at": expires_at
        }
        
        # Actualizar last_login en Airtable
        await airtable.update_usuario_last_login(user["id"])
        
        return LoginResponse(
            token=token,
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                nombre_completo=user["nombre_completo"],
                rol=user["rol"],
                activo=user["activo"]
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Cierra la sesión actual."""
    if credentials and credentials.credentials in active_sessions:
        del active_sessions[credentials.credentials]
    
    return {"message": "Sesión cerrada"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(require_auth)):
    """Obtiene información del usuario actual."""
    return UserResponse(**user)


@router.post("/register", response_model=UserResponse)
async def register(
    data: RegisterRequest,
    airtable: AirtableService = Depends(get_airtable_service)
):
    """
    Registra un nuevo usuario.
    Por defecto se asigna rol 'usuario'.
    """
    try:
        # Verificar que no exista
        existing = await airtable.get_usuario_by_email(data.email)
        if existing:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        # Crear usuario
        user = await airtable.create_usuario({
            "email": data.email,
            "nombre_completo": data.nombre_completo,
            "password_hash": hash_password(data.password),
            "rol": "usuario",
            "activo": True
        })
        
        return UserResponse(
            id=user["id"],
            email=user["email"],
            nombre_completo=user["nombre_completo"],
            rol=user["rol"],
            activo=user["activo"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    user: dict = Depends(require_auth),
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Lista todos los usuarios (solo admin/supervisor)."""
    if user["rol"] not in ["superadmin", "supervisor"]:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    users = await airtable.get_usuarios()
    return [UserResponse(**u) for u in users]


@router.post("/users", response_model=UserResponse)
async def create_user(
    data: RegisterRequest,
    user: dict = Depends(require_auth),
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Crea un nuevo usuario (solo superadmin)."""
    if user["rol"] != "superadmin":
        raise HTTPException(status_code=403, detail="Solo superadmin puede crear usuarios")
    
    # Verificar que no exista
    existing = await airtable.get_usuario_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Crear usuario
    new_user = await airtable.create_usuario({
        "email": data.email,
        "nombre_completo": data.nombre_completo,
        "password_hash": hash_password(data.password),
        "rol": "usuario",
        "activo": True
    })
    
    return UserResponse(**new_user)


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    data: UpdateRoleRequest,
    user: dict = Depends(require_auth),
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Actualiza el rol de un usuario (solo superadmin)."""
    if user["rol"] != "superadmin":
        raise HTTPException(status_code=403, detail="Solo superadmin puede cambiar roles")
    
    if data.rol not in ["superadmin", "supervisor", "usuario"]:
        raise HTTPException(status_code=400, detail="Rol inválido")
    
    await airtable.update_usuario_role(user_id, data.rol)
    
    return {"message": f"Rol actualizado a {data.rol}"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    user: dict = Depends(require_auth),
    airtable: AirtableService = Depends(get_airtable_service)
):
    """Elimina un usuario (solo superadmin)."""
    if user["rol"] != "superadmin":
        raise HTTPException(status_code=403, detail="Solo superadmin puede eliminar usuarios")
    
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    
    await airtable.delete_usuario(user_id)
    
    return {"message": "Usuario eliminado"}

