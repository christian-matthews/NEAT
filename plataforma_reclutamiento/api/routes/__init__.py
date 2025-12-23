from .candidates import router as candidates_router
from .processes import router as processes_router
from .evaluations import router as evaluations_router
from .config import router as config_router
from .auth import router as auth_router
from .applications import router as applications_router
from .cargos import router as cargos_router

__all__ = [
    'candidates_router',
    'processes_router', 
    'evaluations_router',
    'config_router',
    'auth_router',
    'applications_router',
    'cargos_router'
]

