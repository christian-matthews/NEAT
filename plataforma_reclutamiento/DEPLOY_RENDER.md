# 🚀 Despliegue en Render

Guía paso a paso para desplegar NEAT Platform en Render.

## Prerequisitos

1. Cuenta en [Render](https://render.com)
2. Repositorio Git (GitHub, GitLab, o Bitbucket)
3. Variables de entorno configuradas:
   - `AIRTABLE_API_KEY`
   - `AIRTABLE_BASE_ID`
   - `OPENAI_API_KEY` (opcional, para procesamiento de CVs)

---

## Opción A: Deploy con Blueprint (Automático)

### Paso 1: Subir código a GitHub

```bash
cd plataforma_reclutamiento
git init
git add .
git commit -m "Initial commit for Render deploy"
git remote add origin https://github.com/TU_USUARIO/neat-platform.git
git push -u origin main
```

### Paso 2: Crear Blueprint en Render

1. Ve a [Render Dashboard](https://dashboard.render.com)
2. Click en **Blueprints** → **New Blueprint Instance**
3. Conecta tu repositorio de GitHub
4. Render detectará `render.yaml` y creará los servicios automáticamente
5. Configura las variables de entorno:

   | Variable | Valor |
   |----------|-------|
   | `AIRTABLE_API_KEY` | Tu API key de Airtable |
   | `AIRTABLE_BASE_ID` | Tu Base ID (empieza con "app...") |
   | `OPENAI_API_KEY` | Tu API key de OpenAI |

6. Click en **Apply**

---

## Opción B: Deploy Manual (Paso a Paso)

### Paso 1: Backend (FastAPI)

1. Ve a [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Conecta tu repositorio
4. Configura:

   | Campo | Valor |
   |-------|-------|
   | **Name** | `neat-api` |
   | **Region** | Oregon (or nearest) |
   | **Branch** | `main` |
   | **Root Directory** | `plataforma_reclutamiento` |
   | **Runtime** | Python 3 |
   | **Build Command** | `./build.sh` |
   | **Start Command** | `uvicorn api.main:app --host 0.0.0.0 --port $PORT` |

5. En **Environment Variables**, agrega:
   ```
   AIRTABLE_API_KEY=patXXXXXXXXXXXXXX
   AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
   OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXX
   PYTHON_VERSION=3.11
   ```

6. Click **Create Web Service**

### Paso 2: Frontend (Static Site)

1. Click **New** → **Static Site**
2. Conecta el mismo repositorio
3. Configura:

   | Campo | Valor |
   |-------|-------|
   | **Name** | `neat-frontend` |
   | **Branch** | `main` |
   | **Root Directory** | `plataforma_reclutamiento/frontend` |
   | **Build Command** | `npm install && npm run build` |
   | **Publish Directory** | `dist` |

4. En **Environment Variables**:
   ```
   VITE_API_URL=https://neat-api.onrender.com
   ```
   ⚠️ Reemplaza con la URL real de tu backend (la verás después del paso 1)

5. En **Redirects/Rewrites** (para React Router):
   - Source: `/*`
   - Destination: `/index.html`
   - Type: `Rewrite`

6. Click **Create Static Site**

---

## ⚠️ Configuración Importante

### CORS en Producción

Actualiza `api/main.py` para restringir CORS en producción:

```python
# En main.py, reemplaza "*" con tu dominio:
allow_origins=[
    "https://neat-frontend.onrender.com",
    "https://tu-dominio-personalizado.com",
]
```

### Variables de Entorno

| Variable | Backend | Frontend | Descripción |
|----------|:-------:|:--------:|-------------|
| `AIRTABLE_API_KEY` | ✅ | ❌ | Token de Airtable |
| `AIRTABLE_BASE_ID` | ✅ | ❌ | ID de la base |
| `OPENAI_API_KEY` | ✅ | ❌ | Para procesar CVs |
| `VITE_API_URL` | ❌ | ✅ | URL del backend |

---

## 🔍 Verificar Despliegue

### 1. Backend
```bash
curl https://neat-api.onrender.com/api/health
# Debe retornar: {"status":"healthy","services":{...}}
```

### 2. Frontend
- Visita: `https://neat-frontend.onrender.com`
- Deberías ver la página de login

---

## 🐛 Troubleshooting

### Error: "poppler-utils not found"
El `build.sh` debería instalarlo automáticamente. Si falla:
1. Ve a Settings → Build Command
2. Cambia a: `apt-get update && apt-get install -y poppler-utils && pip install -r requirements.txt`

### Error: "CORS blocked"
1. Ve al backend → Settings → Environment
2. Agrega: `ALLOWED_ORIGINS=https://neat-frontend.onrender.com`
3. Actualiza el código para leer esta variable

### Frontend muestra "Network Error"
1. Verifica que `VITE_API_URL` esté correctamente configurado
2. Asegúrate de NO incluir `/api` al final (el código lo agrega automáticamente)
3. Redespliega el frontend después de cambiar variables de entorno

### Backend tarda en responder
El plan gratuito de Render entra en "sleep" después de inactividad.
- Primera request puede tardar ~30 segundos
- Considera plan Starter ($7/mes) para evitar esto

---

## 💡 Tips

1. **Logs en tiempo real**: Dashboard → Service → Logs
2. **Redeploy manual**: Dashboard → Service → Manual Deploy
3. **Dominio personalizado**: Settings → Custom Domains
4. **SSL automático**: Render incluye SSL gratis

---

## Estructura de URLs en Producción

| Servicio | URL |
|----------|-----|
| Backend API | `https://neat-api.onrender.com/api/*` |
| Documentación | `https://neat-api.onrender.com/docs` |
| Frontend | `https://neat-frontend.onrender.com` |
| Formulario Postulación | `https://neat-frontend.onrender.com/apply/CODIGO` |


