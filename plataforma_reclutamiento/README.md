# NEAT Platform v2.0

Plataforma moderna de reclutamiento con evaluación de candidatos por IA.

## 🏗️ Arquitectura

```
neat-platform/
├── engine/                    # Motor de Evaluación (standalone)
│   ├── __init__.py
│   ├── evaluator.py          # Lógica principal de scoring
│   ├── pdf_extractor.py      # Extracción de texto de PDFs
│   └── models.py             # Modelos de datos (Pydantic)
│
├── api/                       # API Gateway (FastAPI)
│   ├── main.py               # Servidor principal
│   ├── models.py             # Esquemas request/response
│   ├── routes/
│   │   ├── candidates.py     # CRUD de candidatos
│   │   ├── processes.py      # Gestión de procesos
│   │   ├── evaluations.py    # Evaluación IA
│   │   └── config.py         # Configuración del motor
│   └── services/
│       └── airtable.py       # Cliente de Airtable
│
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Quick Start

### 1. Crear entorno virtual

```bash
cd neat-platform
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con tus credenciales de Airtable
```

### 4. Crear tablas en Airtable

Sigue las instrucciones en `AIRTABLE_STRUCTURE.md` para crear las 7 tablas necesarias.

### 5. Iniciar la API

```bash
uvicorn api.main:app --reload --port 8000
```

La API estará disponible en:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Base**: http://localhost:8000/api

## 📊 Endpoints Principales

### Candidatos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/candidates/` | Lista candidatos con scores |
| GET | `/api/candidates/stats` | Estadísticas del dashboard |
| GET | `/api/candidates/{id}` | Detalle de candidato |
| POST | `/api/candidates/` | Crear candidato |
| GET | `/api/candidates/{id}/comments` | Comentarios |
| POST | `/api/candidates/{id}/comments` | Agregar comentario |

### Evaluaciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/evaluations/evaluate` | Evaluar candidato |
| GET | `/api/evaluations/{id}` | Obtener evaluación |
| POST | `/api/evaluations/evaluate-text` | Evaluar texto (sin guardar) |

### Procesos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/processes/` | Lista procesos |
| GET | `/api/processes/{codigo}` | Detalle de proceso |
| GET | `/api/processes/{codigo}/candidates` | Candidatos del proceso |
| GET | `/api/processes/cargos/` | Lista de cargos |

### Configuración
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/config/active` | Config activa |
| GET | `/api/config/default` | Config por defecto |
| GET | `/api/config/keywords` | Keywords del modelo |
| POST | `/api/config/` | Crear nueva config |

## 🧠 Motor de Evaluación

El motor evalúa candidatos en 3 categorías:

### 1. Admin & Finanzas (33%)
- Cierre contable, estados financieros, auditoría, Excel...
- Mide capacidad de ejecutar el cierre y control.

### 2. Operaciones & Tesorería (33%)
- Flujo de caja, liquidez, pagos, tesorería...
- Mide manejo del flujo de dinero real.
- **Booster x1.25** si menciona fintech/startup.

### 3. Growth & Cultura (33%)
- Procesos, KPIs, automatización, liderazgo...
- Mide fit con startup en crecimiento.

### Multiplicadores de Industria
| Industria | Multiplicador | Ejemplos |
|-----------|---------------|----------|
| Fintech | x1.5 | Zippy, MercadoPago |
| Tech | x1.2 | Software, Marketplaces |
| General | x1.0 | Retail, Servicios |
| Tradicional | x0.7 | Minería, Construcción |

### Métricas de Inferencia
- **Hands-On Index**: ¿Qué tan operativo es? (< 60% = penalización)
- **Riesgo de Retención**: ¿Está sobrecalificado?
- **Potencial**: Capacidad de adaptación

## 🔗 Integración con Airtable

El sistema se conecta a Airtable como base de datos. Necesitas:

1. Una cuenta de Airtable
2. Una Base con las 7 tablas (ver `AIRTABLE_STRUCTURE.md`)
3. Un Personal Access Token

### Variables de Entorno Requeridas
```env
AIRTABLE_API_KEY=pat_xxxx
AIRTABLE_BASE_ID=appxxxx
```

## 🧪 Uso del Motor como Librería

El motor puede usarse de forma independiente:

```python
from engine import CandidateEvaluator, PDFExtractor

# Extraer texto de PDF
extractor = PDFExtractor()
text = extractor.extract("cv.pdf")

# Evaluar candidato
evaluator = CandidateEvaluator()
result = evaluator.evaluate(text)

print(f"Score: {result.score_promedio}")
print(f"Perfil: {result.inference.profile_type}")
print(f"Riesgo: {result.inference.retention_risk}")
```

## 📝 Ejemplo de Respuesta de Evaluación

```json
{
  "score_promedio": 85,
  "fits": {
    "admin": {
      "score": 90,
      "found": ["excel", "cierre contable", "estados financieros"],
      "missing": ["auditoría", "normativa"],
      "reasoning": "Detectado 5/6 conceptos. **Bonus Fintech:** Experiencia directa."
    },
    "ops": {
      "score": 80,
      "found": ["flujo de caja", "liquidez", "tesorería"],
      "reasoning": "Detectado 3/5 conceptos."
    },
    "biz": {
      "score": 85,
      "found": ["procesos", "kpi", "automatización", "liderazgo"],
      "reasoning": "Detectado 6/6 conceptos."
    }
  },
  "inference": {
    "profile_type": "Ejecutor Hands-On",
    "hands_on_index": 80,
    "risk_warning": "✅ Match Ideal: Sabe operar.",
    "retention_risk": "Bajo",
    "industry_tier": "Fintech (Ideal)"
  }
}
```

## 🛠️ Desarrollo

### Ejecutar tests
```bash
pytest
```

### Hot reload durante desarrollo
```bash
uvicorn api.main:app --reload --port 8000
```

### Estructura de archivos de configuración

El motor puede configurarse modificando las keywords y pesos en:
- Airtable (tabla `Config_Evaluacion`)
- O usando la configuración por defecto en `engine/models.py`

## 📚 Documentación Adicional

- `AIRTABLE_STRUCTURE.md` - Estructura de tablas para Airtable
- `MODELO_DE_EVALUACION.md` - Detalle del algoritmo de scoring

---

Desarrollado con ❤️ para NEAT

