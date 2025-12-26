# 🗄️ THE WINGMAN - Configuración de Airtable

## 📋 RESUMEN DE TABLAS REQUERIDAS

| # | Tabla | Propósito | Prioridad |
|---|-------|-----------|-----------|
| 1 | `Usuarios` | Staff del sistema (superadmin, supervisor) | ✅ Existe |
| 2 | `Cargos` | Catálogo de posiciones/vacantes | 🆕 Crear |
| 3 | `Procesos` | Procesos de reclutamiento activos | 🆕 Crear |
| 4 | `Postulaciones` | Candidatos que postulan | 🔄 Renombrar/Adaptar |
| 5 | `Evaluaciones_AI` | Resultados del motor IA | ✅ Existe |
| 6 | `Historial_Estados` | Auditoría de cambios | 🆕 Crear |
| 7 | `Solicitudes_GDPR` | Eliminación de datos | 🆕 Crear (opcional) |

---

## 📊 TABLA 1: Usuarios (YA EXISTE - ADAPTAR)

### Campos Actuales + Nuevos

| Campo | Tipo | Descripción | Estado |
|-------|------|-------------|--------|
| `email` | Email | Correo del usuario | ✅ Existe |
| `password_hash` | Single line text | Hash de contraseña | ✅ Existe |
| `nombre_completo` | Single line text | Nombre del usuario | 🆕 Agregar |
| `rol` | Single select | superadmin / supervisor / usuario | 🆕 Agregar |
| `activo` | Checkbox | Si el usuario está activo | 🆕 Agregar |
| `created_at` | Created time | Fecha de creación | ✅ Existe |

### Opciones del campo `rol`
```
- superadmin  → Control total del sistema
- supervisor  → Gestiona sus procesos asignados
- usuario     → Solo puede postular (público)
```

### Usuarios Iniciales Sugeridos
| Email | Rol | Nombre |
|-------|-----|--------|
| a@a.com | superadmin | Administrador |

---

## 📊 TABLA 2: Cargos (NUEVA)

> Catálogo maestro de posiciones/vacantes disponibles en la empresa.

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| `codigo` | Single line text | Código único (ej: DEV-001) | ✅ |
| `nombre` | Single line text | Nombre del cargo | ✅ |
| `descripcion` | Long text | Descripción detallada | ❌ |
| `vacantes` | Number | Cantidad de vacantes totales | ✅ (default: 1) |
| `activo` | Checkbox | Si el cargo está disponible | ✅ (default: true) |
| `fecha_activacion` | Date | Cuándo se activó | ❌ |
| `created_at` | Created time | Fecha de creación | Auto |

### Ejemplo de Registros
| codigo | nombre | vacantes | activo |
|--------|--------|----------|--------|
| DEV-001 | Desarrollador Full Stack | 3 | ✅ |
| PM-001 | Project Manager | 1 | ✅ |
| DS-001 | Data Scientist | 2 | ❌ |

---

## 📊 TABLA 3: Procesos (NUEVA - CENTRAL)

> Cada proceso representa una búsqueda activa para llenar vacantes de un cargo.

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| `codigo_proceso` | Single line text | Código único (ej: DEV-001-P001) | ✅ |
| `cargo` | Link to Cargos | Cargo asociado | ✅ |
| `estado` | Single select | Estado actual del proceso | ✅ |
| `fecha_inicio` | Date | Inicio del proceso | ✅ (default: hoy) |
| `fecha_cierre` | Date | Fecha tentativa de cierre | ❌ |
| `vacantes_proceso` | Number | Vacantes para este proceso | ✅ (default: 1) |
| `usuario_asignado` | Link to Usuarios | Supervisor responsable | ✅ |
| `avances` | Long text | Descripción de avances | ❌ |
| `bloqueos` | Long text | Bloqueos actuales | ❌ |
| `proximos_pasos` | Long text | Próximos pasos | ❌ |
| `notas` | Long text | Notas generales | ❌ |
| `resultado` | Long text | Resultado final | ❌ |
| `created_at` | Created time | Fecha de creación | Auto |
| `updated_at` | Last modified time | Última modificación | Auto |

### Opciones del campo `estado`
```
publicado       → 🟢 Visible para postulantes
en_revision     → 🔵 Revisando CVs recibidos
en_entrevistas  → 🟡 Entrevistando candidatos
finalizado      → ⚫ Proceso cerrado
cancelado       → 🔴 Proceso cancelado
```

### Flujo de Estados
```
                    ┌─────────────────┐
                    │   publicado     │ ← Inicio
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   en_revision   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ en_entrevistas  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌─────────────────┐           ┌─────────────────┐
     │   finalizado    │           │   cancelado     │
     └─────────────────┘           └─────────────────┘
```

---

## 📊 TABLA 4: Postulaciones (ADAPTAR DE "Candidatos")

> Registra cada postulación de un candidato a un proceso específico.

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| `codigo_tracking` | Single line text | Código único TW-POST-xxx | ✅ Auto |
| `nombre_completo` | Single line text | Nombre del candidato | ✅ |
| `email` | Email | Correo del candidato | ✅ |
| `telefono` | Phone | Teléfono de contacto | ✅ |
| `proceso` | Link to Procesos | Proceso al que postula | ✅ |
| `cargo` | Link to Cargos | Cargo (redundante, para filtros) | ✅ |
| `cv_archivo` | Attachment | CV subido (PDF/DOC) | ✅ |
| `cv_url` | URL | URL del CV (para compatibilidad) | ❌ |
| `estado_candidato` | Single select | Estado en el proceso | ✅ |
| `score_ai` | Number | Score del motor IA (0-100) | ❌ |
| `evaluacion` | Link to Evaluaciones_AI | Evaluación detallada | ❌ |
| `notas` | Long text | Notas del reclutador | ❌ |
| `tags` | Multiple select | Etiquetas personalizadas | ❌ |
| `created_at` | Created time | Fecha de postulación | Auto |

### Opciones del campo `estado_candidato`
```
nuevo           → 📥 Recién postulado
en_revision     → 📋 CV siendo revisado
preseleccionado → ⭐ Pasó primera fase
entrevista      → 🎤 En proceso de entrevista
finalista       → 🏆 Candidato finalista
seleccionado    → ✅ Contratado
descartado      → ❌ No continúa
```

### Opciones de `tags` (sugeridas)
```
experiencia_senior
experiencia_junior
ingles_avanzado
disponibilidad_inmediata
pretension_alta
referido
```

---

## 📊 TABLA 5: Evaluaciones_AI (YA EXISTE - VERIFICAR)

> Resultados del motor de IA para cada candidato.

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| `candidato` | Link to Postulaciones | Postulación evaluada | ✅ |
| `proceso` | Link to Procesos | Proceso asociado | ✅ |
| `score_total` | Number | Puntuación total (0-100) | ✅ |
| `hands_on_index` | Number | Índice práctico (0-100) | ✅ |
| `retention_risk` | Single select | Riesgo de retención | ✅ |
| `potential` | Single select | Potencial de crecimiento | ✅ |
| `keywords_found` | Long text | Keywords detectadas (JSON) | ❌ |
| `category_scores` | Long text | Scores por categoría (JSON) | ❌ |
| `cv_text` | Long text | Texto extraído del CV | ❌ |
| `created_at` | Created time | Fecha de evaluación | Auto |

### Opciones de `retention_risk`
```
bajo    → 🟢 Probablemente se queda
medio   → 🟡 Riesgo moderado
alto    → 🔴 Alta probabilidad de rotación
```

### Opciones de `potential`
```
bajo        → Crecimiento limitado
moderado    → Puede crecer con guía
alto        → Alto potencial
excepcional → Estrella en potencia
```

---

## 📊 TABLA 6: Historial_Estados (NUEVA)

> Auditoría de cambios de estado en procesos (trazabilidad).

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| `proceso` | Link to Procesos | Proceso modificado | ✅ |
| `estado_anterior` | Single line text | Estado antes del cambio | ❌ |
| `estado_nuevo` | Single line text | Nuevo estado | ✅ |
| `usuario` | Link to Usuarios | Quién hizo el cambio | ✅ |
| `notas` | Long text | Razón del cambio | ❌ |
| `created_at` | Created time | Fecha del cambio | Auto |

---

## 📊 TABLA 7: Solicitudes_GDPR (NUEVA - OPCIONAL)

> Para cumplimiento de normativas de protección de datos.

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| `email` | Email | Email del solicitante | ✅ |
| `tipo_identificacion` | Single select | cedula / pasaporte | ✅ |
| `numero_identificacion` | Single line text | Número de documento | ✅ |
| `nacionalidad` | Single line text | País | ✅ |
| `motivo` | Long text | Razón de la solicitud | ✅ |
| `estado` | Single select | pendiente / procesada / rechazada | ✅ |
| `created_at` | Created time | Fecha de solicitud | Auto |

---

## 🔗 RELACIONES ENTRE TABLAS

```
┌──────────────┐
│   Usuarios   │
└──────┬───────┘
       │
       │ usuario_asignado
       ▼
┌──────────────┐         ┌──────────────┐
│   Procesos   │◄────────│    Cargos    │
└──────┬───────┘  cargo  └──────────────┘
       │
       │ proceso
       ▼
┌──────────────┐         ┌──────────────────┐
│ Postulaciones│────────►│  Evaluaciones_AI │
└──────┬───────┘         └──────────────────┘
       │                  evaluacion
       │
       ▼
┌──────────────────┐
│ Historial_Estados│
└──────────────────┘
```

---

## 📝 PASOS DE IMPLEMENTACIÓN EN AIRTABLE

### Paso 1: Modificar tabla Usuarios
```
1. Abrir tabla "Usuarios"
2. Agregar campo "nombre_completo" (Single line text)
3. Agregar campo "rol" (Single select: superadmin, supervisor, usuario)
4. Agregar campo "activo" (Checkbox, default: checked)
5. Actualizar usuario a@a.com con rol "superadmin"
```

### Paso 2: Crear tabla Cargos
```
1. Crear nueva tabla "Cargos"
2. Agregar todos los campos según especificación
3. Crear al menos 1 cargo de prueba
```

### Paso 3: Crear tabla Procesos
```
1. Crear nueva tabla "Procesos"
2. Agregar todos los campos según especificación
3. Crear link a tabla Cargos
4. Crear link a tabla Usuarios
5. Crear proceso de prueba
```

### Paso 4: Adaptar tabla Candidatos → Postulaciones
```
1. Renombrar tabla "Candidatos" a "Postulaciones"
2. Agregar campo "proceso" (Link to Procesos)
3. Agregar campo "cargo" (Link to Cargos)
4. Agregar campo "cv_archivo" (Attachment)
5. Agregar campo "estado_candidato" (Single select)
6. Agregar campo "score_ai" (Number)
7. Agregar campo "tags" (Multiple select)
```

### Paso 5: Actualizar tabla Evaluaciones_AI
```
1. Agregar campo "proceso" (Link to Procesos)
2. Verificar que "candidato" sea Link to Postulaciones
```

### Paso 6: Crear tabla Historial_Estados
```
1. Crear nueva tabla "Historial_Estados"
2. Agregar todos los campos según especificación
```

---

## 🎯 CHECKLIST FINAL

- [ ] Tabla Usuarios actualizada con roles
- [ ] Tabla Cargos creada con datos de prueba
- [ ] Tabla Procesos creada con relaciones
- [ ] Tabla Postulaciones adaptada
- [ ] Tabla Evaluaciones_AI actualizada
- [ ] Tabla Historial_Estados creada
- [ ] Usuario superadmin configurado
- [ ] Al menos 1 cargo activo
- [ ] Al menos 1 proceso publicado

---

## 📌 NOTAS IMPORTANTES

### Sobre Attachments (CVs)
- Airtable permite archivos de hasta 5MB en plan free
- Los attachments generan URLs temporales
- El motor IA necesitará descargar el archivo para procesarlo

### Sobre Fórmulas Útiles
```javascript
// Días activo del proceso
DATETIME_DIFF(TODAY(), {fecha_inicio}, 'days')

// Proceso atrasado
IF(AND({estado} != "finalizado", {fecha_cierre} < TODAY()), "⚠️ ATRASADO", "✅ OK")

// Código de tracking automático
CONCATENATE("TW-POST-", DATETIME_FORMAT(CREATED_TIME(), "YYYYMMDD-HHmmss"))
```

### Sobre Vistas Recomendadas
1. **Procesos Activos** - Filtro: estado != "finalizado"
2. **Procesos por Supervisor** - Agrupado por usuario_asignado
3. **Candidatos Pendientes** - Filtro: estado_candidato = "nuevo"
4. **Pipeline de Evaluación** - Ordenado por score_ai DESC




