# Resumen de Funcionalidades: NeatTalent AI Dashboard

Este documento detalla las capacidades de la plataforma construida, con énfasis en la nueva interfaz (Frontend) y su integración con el motor de inteligencia artificial (Backend).

## 🎨 1. Frontend Premium (React + Tailwind + Framer Motion)

La interfaz ha sido rediseñada totalmente bajo el estilo **"Linear / Vercel"**, priorizando la densidad de información, el modo oscuro profundo y la fluidez.

### **A. Dashboard Principal (Bento Grid)**
*   **Estética Moderna:** Fondo *Zinc-950*, bordes sutiles y efectos de *glassmorphism* (vidrio esmerilado).
*   **KPIs en Tiempo Real:** Tarjetas superiores con métricas clave (Total Candidatos, Score Promedio, Alertas de Riesgo).
*   **Buscador Instantáneo:** Filtrado en tiempo real por nombre de candidato.
*   **Tarjetas de Candidatos:**
    *   Visualización rápida de **Score Global** (con código de colores semáforo).
    *   Indicadores clave visibles sin entrar al detalle:
        *   ⚡ **Hands-On %:** ¿Qué tan operativo es?
        *   🛡 **Riesgo Fuga:** ¿Está sobrecalificado?
    *   Animaciones de entrada escalonada al cargar.

### **B. Vista de Detalle ("IDE Style")**
Diseñada para parecer un entorno de desarrollo profesional, maximizando el espacio de trabajo.
*   **Split View (Pantalla Dividida):**
    *   **Izquierda (70%):** Visor PDF incrustado con controles nativos. Permite leer el CV original sin salir de la app.
    *   **Derecha (30%):** Panel lateral de análisis estilo "Inspector".
*   **Panel de Inteligencia Artificial:**
    *   Resumen del perfil inferido (Ej: *"Corporativo Senior"* vs *"Ejecutor Hands-On"*).
    *   Desglose de puntajes por área (Finanzas, Operaciones, Growth).
    *   Explicación textual de *por qué* se asignó ese puntaje (Reasoning).
*   **Sistema de Notas (Chat):**
    *   Chat persistente para dejar comentarios sobre el candidato.
    *   Registro de timestamp y autor.
    *   Ideal para tomar notas durante la entrevista telefónica.

### **C. Configuración Dinámica**
*   Interfaz para editar los pesos y palabras clave del algoritmo ("JSON Config").
*   Permite ajustar qué define a un candidato "Senior" sin tocar código Python.

---

## ⚙️ 2. Conexión con Backend (Python / FastAPI)

El Frontend no es solo "cosmético"; es una aplicación SPA (Single Page Application) totalmente conectada vía API REST.

### **Arquitectura de Conexión**
1.  **Motor de Lógica (`engine.py`):** Reutiliza tu lógica experta original de Python para parsear PDFs y calcular puntajes.
2.  **API Server (`main.py`):** Expone esta lógica a través de endpoints HTTP.
3.  **Persistencia Ligera:** Utiliza un archivo `candidates_db.json` para guardar las notas y metadatos extras sin necesitar una base de datos SQL compleja.

### **Flujo de Datos**
*   **Lectura:** Cuando abres el Dashboard, React pide `GET /api/candidates`. El backend lee el CSV, cruza con los PDFs y devuelve el JSON.
*   **Archivos:** El visor de PDF carga el archivo real desde tu disco local sirviendo la ruta `/files/{nombre}.pdf` de forma segura.
*   **Escritura:** Al enviar una nota, React hace `POST /api/candidates/{id}/comment`. El backend actualiza el JSON local inmediatamente.

---

## 🚀 Resumen Técnico

| Componente | Tecnología | Función Principal |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite | Interfaz de usuario interactiva y reactiva. |
| **Estilos** | TailwindCSS v4 | Diseño "Pixel-perfect", modo oscuro, grillas. |
| **Iconos** | Lucide React | Iconografía vectorial moderna y consistente. |
| **Backend** | FastAPI (Python) | API de alto rendimiento, puente con tu lógica de negocio. |
| **PDF Parsing** | pdfplumber | Extracción de texto de los CVs originales. |
| **Datos** | JSON | Persistencia local simple y portable. |
