# The Wingman 🚀

Plataforma de Reclutamiento con Evaluación por IA

## 📁 Estructura del Proyecto

```
NEAT/
├── .venv/                    # Entorno virtual Python
├── .git/                     # Repositorio Git
└── plataforma_reclutamiento/ # 🎯 Proyecto Principal
    ├── api/                  # Backend FastAPI
    │   ├── routes/           # Endpoints de la API
    │   │   ├── auth.py       # Autenticación
    │   │   ├── applications.py # Postulaciones públicas
    │   │   ├── candidates.py # Gestión de candidatos
    │   │   ├── evaluations.py # Evaluaciones IA
    │   │   ├── processes.py  # Procesos de reclutamiento
    │   │   └── config.py     # Configuración
    │   └── services/
    │       └── airtable.py   # Cliente Airtable
    ├── engine/               # Motor de Evaluación IA
    │   ├── evaluator.py      # Lógica de evaluación
    │   ├── pdf_extractor.py  # Extracción de CVs
    │   └── models.py         # Modelos Pydantic
    ├── frontend/             # React + Vite + TailwindCSS
    │   └── src/
    │       ├── pages/        # Páginas de la app
    │       └── lib/api.ts    # Cliente API
    ├── data/
    │   ├── cvs/              # CVs de candidatos
    │   └── reports/          # Reportes generados
    ├── scripts/              # Scripts de utilidad
    ├── .env                  # Variables de entorno
    └── requirements.txt      # Dependencias Python
```

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

```bash
cd plataforma_reclutamiento
cp env.example.txt .env
# Editar .env con tus credenciales de Airtable
```

### 2. Instalar Dependencias

```bash
# Python (desde la raíz del proyecto)
source .venv/bin/activate
pip install -r plataforma_reclutamiento/requirements.txt

# Frontend
cd plataforma_reclutamiento/frontend
npm install
```

### 3. Crear Tabla Usuarios en Airtable

Crear tabla `Usuarios` con campos:
- `email` (Email) - Campo primario
- `nombre_completo` (Single line text)
- `password_hash` (Single line text)
- `rol` (Single select: superadmin, supervisor, usuario)
- `activo` (Checkbox)
- `last_login` (Date time)

### 4. Crear Usuario Superadmin

```bash
cd plataforma_reclutamiento
python scripts/create_superadmin.py
```

### 5. Ejecutar

```bash
# Terminal 1 - API (puerto 8000)
cd plataforma_reclutamiento
source ../.venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend (puerto 5173)
cd plataforma_reclutamiento/frontend
npm run dev
```

## 🌐 URLs

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| Postulación Pública | http://localhost:5173/postular |
| Login Staff | http://localhost:5173/login |
| API | http://localhost:8000 |
| Docs API | http://localhost:8000/docs |

## 🔑 Endpoints API

### Públicos (sin auth)
- `GET /api/applications/processes` - Procesos disponibles
- `POST /api/applications/submit` - Enviar postulación
- `GET /api/applications/track/{code}` - Consultar estado

### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/logout` - Cerrar sesión
- `GET /api/auth/me` - Usuario actual

### Candidatos (requiere auth)
- `GET /api/candidates/` - Listar candidatos
- `GET /api/candidates/stats` - Estadísticas dashboard
- `GET /api/candidates/{id}` - Detalle candidato

### Evaluaciones (requiere auth)
- `GET /api/evaluations/{id}` - Obtener evaluación
- `POST /api/evaluations/{id}/evaluate` - Evaluar candidato

## 📊 Base de Datos (Airtable)

| Tabla | Descripción |
|-------|-------------|
| Cargos | Posiciones disponibles |
| Procesos_Reclutamiento | Procesos activos |
| Candidatos | Postulantes |
| Evaluaciones_AI | Resultados de evaluación |
| Comentarios | Notas de reclutadores |
| Usuarios | Staff del sistema |

## 🔧 Tecnologías

- **Backend:** Python 3.11+, FastAPI, Pydantic
- **Frontend:** React 18, TypeScript, Vite, TailwindCSS
- **Base de datos:** Airtable
- **IA:** OpenAI (opcional para PDFs escaneados)
- **PDF:** pdfplumber

## 📝 Licencia

Propietario - Uso interno

