# Reglas de Proyecto: Argos Proyect

Este archivo hereda las directivas maestras de `..\antigravity_work.md`.

**Objetivo del Proyecto:** Plataforma principal para el procesamiento, validación y generación masiva de Declaraciones Juradas de Composición (DJC) y auditoría (m1_ingest, m2_audit, etc.).

**Stack:** 
- Python, Tkinter (Frontend), Vite/React (Web App si aplica), PyMuPDF/pdfplumber, Pandas.

**Directivas Locales:**
- Mantener la arquitectura segmentada (extractors, modules).
- Tipado estricto (Strict Typing) en todas las funciones nuevas.
- Toda nueva interfaz debe seguir el estilo minimalista o ser migrada a interfaces modernas (CustomTkinter o React) según corresponda.
- Manejo inquebrantable de valores nulos (Null-Safety) al extraer datos de aduana.
- Siempre que un cambio esté probado y aceptado por el usuario, se debe agregar obligatoriamente el registro en `CHANGELOG.md`, actualizar las variables de versión en el código y correr la compilación/build del proyecto.
