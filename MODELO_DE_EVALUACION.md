# Modelo de Evaluación de Candidatos: Senior Finance (Fintech)

Este documento detalla la lógica, parámetros y criterios utilizados por el algoritmo para evaluar y rankear a los candidatos en el proceso de selección "Senior Financial".

## 1. Objetivo del Modelo
Identificar un perfil **"Híbrido Senior"** capaz de operar con autonomía (Hands-On) pero con visión estratégica, priorizando la **agilidad Fintech** sobre la jerarquía corporativa tradicional.

---

## 2. Categorías de Evaluación (Score Base 0-100)

El puntaje base se calcula detectando la presencia de conceptos clave en el CV.

### A. Admin & Finanzas (Peso: 33%)
*Evalúa la capacidad de ejecutar el cierre y control.*
*   **Keywords Clave (6 requeridas):** `cierre contable`, `mensual`, `imputación`, `gastos`, `ingresos`, `reportes financieros`, `análisis de cuentas`, `excel`.
*   **Pregunta Clave:** "¿Sabe cerrar el mes solo o solo supervisa?"

### B. Operaciones y Tesorería (Peso: 33%)
*Evalúa el manejo del flujo de dinero real.*
*   **Keywords Clave (5 requeridas):** `flujo de caja`, `cash flow`, `semanal`, `proyección`, `liquidez`, `pagos`, `tesorería`.
*   **Booster:** Se aplica un bonificador (x1.25) si menciona términos como `fintech` o `startup` en esta sección.

### C. Growth & Cultura (Peso: 33%)
*Evalúa el fit con una startup en crecimiento.*
*   **Keywords Clave (6 requeridas):** `procesos`, `implementación`, `liderazgo`, `toma de decisiones`, `bi`, `automatización`, `eficiencia`, `kpi`.

---

## 3. Motores de Inferencia (Ajustes de Score)

El modelo no solo cuenta palabras, sino que "infiere" comportamientos basándose en patrones.

### 🔍 Índice "Hands-On" (Manos a la Obra)
Mide qué tan operativo es el candidato.
*   **Fórmula:** % de herrmientas técnicas encontradas (`tabla dinámica`, `macros`, `imputación`, `conciliación`, `sql`, `erp`, `ejecución`).
*   **Umbral Crítico:** **60%**.
*   **Penalización:** Si un candidato tiene cargo de **Gerente/Jefe** Y su Hands-On es **< 60%**, se le etiqueta como **"Delegador"** y su nota técnica baja un 20%.

### 🚨 Riesgo de Retención (Overqualification)
Detecta perfiles acostumbrados a estructuras demasiado grandes.
*   **Indicadores:** `regional`, `latam`, `global`, `billones`, `m&a`, `directorio`.
*   **Regla:** Si tiene cargo Alto + >3 Indicadores Corporativos → **Alerta: "Riesgo Fuga Alto"**.

### 🌟 Potencialidad (Adaptabilidad)
Mide la capacidad de aprendizaje.
*   **Indicadores:** `aprendizaje`, `autodidacta`, `adaptación`, `flexible`, `innovación`.

---

## 4. Filtro de Industria (El "Multiplicador")

Para asegurar el fit cultural, se aplican multiplicadores sobre el puntaje final basándose en la empresa de procedencia (detectada automáticamente).

| Tipo de Industria | Ejemplos | Multiplicador | Efecto |
| :--- | :--- | :---: | :--- |
| **Fintech (Ideal)** | Zippy, MercadoPago, Fintoc | **x 1.5** | **BONUS:** Premia la experiencia directa, aunque el CV sea breve. |
| **Tech / Digital** | Software, Marketplaces | **x 1.2** | Bonus moderado. |
| **General** | Retail, Servicios | **x 1.0** | Neutro. |
| **Tradicional** | Minería, Educación, Construcción | **x 0.7** | **PENALIZACIÓN:** Castiga perfiles de industrias lentas ("Dinosaurios"). |

---

## 5. Resumen de Criterios de Éxito

Para ser el candidato #1 (como Jorge Guzmán o Constanza Pino), se requiere:
1.  **Cobertura de Keywords:** Mencionar explícitamente "Cierre", "Flujo" y "Procesos".
2.  **Alto Hands-On:** Demostrar uso de herramientas, no solo "gestión de equipos".
3.  **Origen Ágil:** Venir de Tech/Fintech o evitar industrias pesadas.
4.  **Recencia:** Las palabras clave deben aparecer en el primer tercio del CV (experiencia reciente).
