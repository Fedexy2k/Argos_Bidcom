# ARGOS - Changelog

## v2.0.2 (2026-04-23) - AI OEC Context & Extractor Refinements

### ✨ Nuevas Características
- **Contexto OEC Dinámico**: Se implementó un motor de inyección de contexto (`oec_rules.json`) que guía la revisión semántica de Gemini según las reglas estructurales de cada organismo (Intertek, Lenor, Quektra, IRAM, CB Scheme), evitando alucinaciones de roles (ej. confundir un laboratorio de ensayo con el fabricante).

### 🐛 Correcciones
- **Certificados Codificados (Intertek)**: Se previno que Gemini invente direcciones en certificados simplificados (Disposición 1/24). El sistema ahora asigna automáticamente "China" y retira el campo de la evaluación inteligente.
- **División Fábrica/Dirección (Intertek)**: Actualizado el extractor para detectar correctamente el formato moderno de unificación en la misma línea separados por doble barra (`//`).
- **Códigos de Revisión (R1)**: Mejorada la expresión regular global de Nro. de Certificado en el generador para capturar los sufijos de revisión (ej. `TCSE-IACSA-0146/365.1R1`).

---

## v2.0.1 (2026-04-22) - IA Review & Extension Fixes

### ✨ Nuevas Características
- **Revisión Semántica con IA (Gemini)**: Integración de capa de validación inteligente para datos extraídos de certificados.
- **Modo Extensión Terceros**: Implementación de flujo para extensiones de fabricantes externos con datos de BIDCOM fijos como importador/representante.

### 🐛 Correcciones
- **Fix DJC-ID en Extensiones**: Ahora el código de la sociedad se inserta correctamente en el ID (ej: BEMO-V1) para evitar duplicados en carpetas.
- **Detección de País Mejorada**: El motor de codificación ahora busca el origen tanto en la dirección como en el nombre del fabricante.
- **UI Drag & Drop**: Corregido el drop zone de la Nota de Extensión en el generador.

### 🔧 Mejoras Técnicas
- **Formulario Editable de Empresa**: Panel dinámico para editar los 7 campos de la empresa en modo Terceros.
- **Optimización de Inyección**: Refactorizado el diccionario de datos para asegurar la inyección correcta de representantes en el documento Word.

---

## v2.0.0_STABLE (2026-04-15) - Web Architecture & Desktop Installer

### ✨ Nuevas Características
- **Arquitectura Web Local**: Migración completa del framework UI de CustomTkinter a una SPA React moderna (TypeScript, Tailwind V4, Vite).
- **Backend Robusto**: Implementación de servidor FastAPI local para orquestar la comunicación entre los módulos Python core locales (M1, M2, M3) y el nuevo Frontend React .
- **Contenedor Desktop (PyWebview)**: El sistema corre localmente disfrazado como aplicación de escritorio nativa mediante el uso del módulo `pywebview`, abriendo en una ventana dedicada con comportamientos nativos de Windows (minimizar, pantalla completa, cierre con aspas).
- **Instalador Profesional (Inno Setup)**: Nuevo paquete `Setup.exe` autocontenido y simple, con rutinas de desinstalación limpias y acceso directo a Escritorio. 

### 🔧 Mejoras Técnicas
- Frontend SPA estático autoalojado desde los static-assets servidos por FastAPI.  

---

## v1.0.0 (2026-02-10) - Release Inicial

### ✨ Nuevas Características

**GUI Base:**
- Ventana principal con diseño moderno y responsive
- Drag & Drop para datasheet (.xlsx) y certificados (.pdf)
- Sistema de temas con 3 opciones:
  - **Oscuro** (default): Tema profesional gris oscuro
  - **Matrix**: Tema inspirado en Matrix con verde ajustado
  - **Claro**: Tema claro profesional
- Panel de Debug con logging completo
- Feedback visual de archivos cargados
- Validación automática de tipos de archivo

**Backend:**
- Parser de datasheets (`m1_ingest.py`)
- Sistema de auditoría multicertificado (`m2_multiaudit.py`)
- Estrategias adaptativas de validación (`m2_strategies.py`):
  - `LenorToyStrategy`: Juguetes certificados por Lenor
  - `CBSchemeStrategy`: Certificados CB Scheme (TÜV, SGS, Intertek)
  - `AuditStrategy`: Validación estándar

**Logging:**
- Sistema de logs dual (archivo + GUI)
- Niveles: DEBUG, INFO, WARNING, ERROR
- Exportación de logs
- Timestamps automáticos

### 🐛 Correcciones

- **v1.0.0-fix1**: Corregido bug de ventana transparente al abrir panel Debug
  - Cambiado de `CTkToplevel` a `tkinter.Toplevel` para evitar conflictos con TkinterDnD
- **v1.0.0-fix2**: Ajustado verde del tema Matrix para mejor legibilidad
  - Verde: #00FF41 → #00CC33 (contraste mejorado en texto de botones)
- **v1.0.0-fix3**: Agregado tema "Oscuro" profesional como default
- **v1.0.0-fix4**: Mejorado feedback visual de archivos cargados
  - Muestra "Sin archivo cargado" por defecto
  - Estado visible y claro al cargar

### 🔧 Mejoras Técnicas

- Ciclo de temas: Oscuro → Matrix → Claro (en lugar de toggle binario)
- Panel Debug con scrollbar y botón "Cerrar"
- Botón de tema muestra nombre actual: "🌓 Oscuro"
- Herencia simplificada: `TkinterDnD.Tk` directamente

### 📦 Dependencias

- `customtkinter` >= 5.2.2
- `tkinterdnd2` >= 0.4.3
- `openpyxl`
- `PyMuPDF` (fitz)
- `thefuzz`

---

## Próximas Versiones (Planificadas)

### v1.1.0 - Integración Backend
- Conectar GUI con módulos de parsing y auditoría
- Panel de resultados con checklist visual
- Barra de progreso durante auditoría
- Preview de datos extraídos del datasheet

### v1.2.0 - Comparador Visual
- Modal lado-a-lado para warnings
- Visor PDF integrado
- Resaltado de líneas relevantes
- Aprobación/rechazo manual de warnings

### v1.3.0 - Módulo 3 (Finalizer)
- Generación de DJC
- Censura automática de dirección/fábrica
- Merge de PDFs
- Upload a Google Drive

### v2.0.0 - Módulo 1 (Generator)
- Generación de solicitudes a certificadoras
- Integración con plantillas

---

## Formato de Versiones

Seguimos [Semantic Versioning](https://semver.org/):
- **MAJOR**: Cambios incompatibles de API
- **MINOR**: Nuevas funcionalidades retrocompatibles
- **PATCH**: Correcciones de bugs

### Símbolos:
- ✨ Nueva característica
- 🐛 Corrección de bug
- 🔧 Mejora técnica
- 📦 Dependencia
- ⚠️ Breaking change
- 📝 Documentación
