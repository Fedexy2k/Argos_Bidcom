# ARGOS - Changelog

## v3.2.2 (2026-08-19) - Corrección de Color Dinámico de Consumo y Maquetación de Normas en Hornos Eléctricos

### 🐛 Correcciones de Errores
- **Formato de Coma Decimal Argentina/IRAM (`fmtComma`)**: Implementada la función de formateo automático que renderiza todos los valores numéricos decimales usando la coma (`,`) en lugar del punto (`.`) en todas las plantillas de etiquetas (ej: `0,63` kWh/ciclo, `15,7` lts, `7,5` kg), conforme a la norma oficial argentina (Res. SIyC N° 438/2024 y reglamentación IRAM).
- **Color Dinámico de Banda de Consumo en Hornos**: Corregido `TemplateHorno` para que la barra de Consumo de Energía cambie dinámicamente de color según la clase seleccionada (A=Verde, B=Verde Claro, C=Amarillo Verdoso, D=Amarillo, E=Naranja Claro, F=Naranja, G=Rojo), garantizando que el 100% de las plantillas del sistema respondan de forma dinámica.
- **Maquetación Flex de Normas IRAM y Resolución en Hornos**: Reemplazada la posición absoluta fija por un contenedor flex vertical autoadaptable (`display: flex`, `flex-direction: column`, `align-items: center`), evitando que las normas de múltiples líneas (ej: `IRAM 62414-1/2, IRAM 62301`) se tachen o se solapen con la línea separadora gris.

## v3.2.1 (2026-08-17) - Capa OCR Buscable en DJC, Arquitectura Modular FastAPI, Censura Multilínea y Suite QA

### ✨ Nuevas Características y Mejoras
- **Capa OCR Buscable en PDFs de DJC (`render_mode=3`)**: Corrección en `modules/pdf_ops.py` (`merge_pdfs`) para que los certificados rasterizados adjuntos en las DJCs incorporen una capa de texto invisible superpuesta con Tesseract OCR (`pytesseract.image_to_data`). Esto garantiza que los documentos finales sean **100% buscables y seleccionables (Ctrl+F)** en cualquier visor PDF preservando firmas digitales.
- **Arquitectura Modular FastAPI (`api/routers/`)**: Refactorización integral del backend monolítico `main.py` dividiéndolo en routers independientes por dominio (`health.py`, `budget.py`, `djc.py`, `ee.py`, `solicitud.py`, `verify.py`).
- **Indicador Visual de Estado de IA en la UI**: Nuevo endpoint `/api/health/ai` y badge inteligente en el Header de la aplicación que informa en tiempo real la disponibilidad de claves de OpenAI y Gemini con semáforo luminoso (`🟢 IA: OpenAI + Gemini` / `🔴 IA: Sin Clave`).
- **Censura Multilínea para Juguetes y Certificados Complejos**: Actualización de `modules/pdf_ops.py` (`censor_cert_pdf`) para censurar bloques y párrafos multilínea completos de fábrica y dirección, preservando el país de origen.
- **Actualización de Plantilla Oficial Lenor (`Solicitud_Modelo_Lenor.xlsm`)**: Mapeo completo de la nueva versión de solicitud Lenor (`PCE-34 F1 R05` con 7 solapas) automatizada con `win32com`.
- **Integración Oficial de TÜV Rheinland en Solicitudes (M5)**: Incorporación de TÜV Rheinland como organismo certificador oficial con plantilla `assets/solicitud_templates/Solicitud_Modelo_tuv.docx`.
- **Optimización Extrema de Tamaño de Instalador (-77% en disco)**: Exclusión en PyInstaller de librerías innecesarias de Machine Learning (`torch`, `cv2`, `scipy`, `transformers`), reduciendo el instalador a **71.6 MB**.
- **Centralización de Plantillas (`assets/djc_templates/`)**: Reorganización de todas las plantillas Word de DJC dentro de `assets/djc_templates/`.

## v3.2.0 (2026-08-10) - Generación Dinámica de Ficha Técnica, Plantilla Lavarropas de Illustrator y Fondo de Consumo Dinámico

### ✨ Nuevas Características
- **Ficha Técnica de Información de Producto (Res. SIyC N° 438/2024 Art. 7°)**: Generación automática de la Ficha Técnica oficial en formato Word y PDF. Implementado superset de 44 especificaciones técnicas y borrado dinámico de filas por familia en `fill_template_ft()`.
- **Plantilla Oficial de Lavarropas (`TemplateLavarropas`)**: Reconstrucción 1:1 en React/HTML del diseño oficial de Illustrator (`GAD-WM80.ai`, `GAD-WM60.ai`, `GAD-WM120.ai`), incluyendo grid de características 4x2 con íconos vectoriales SVG (Agua, Capacidad, Duración, Ruido, Standby, RPM y escala A-G de Centrifugado).
- **Fondo de Consumo de Energía Dinámico**: Ajuste automático del fondo del bloque de Consumo de Energía para que adopte el color exacto correspondiente a la letra seleccionada (A=Verde Oscuro, B=Verde Claro, C=Verde Amarillento, D=Amarillo, E=Naranja Claro, F=Naranja, G=Rojo) en todas las familias de etiquetas según Res. 438/24 Anexo I Pág. 10.
- **Soporte de Standby / Consumo en Espera para Heladeras**: Incorporación del campo `consumo_espera` en la plantilla de Ficha Técnica y etiqueta de Refrigeradores/Freezers (Res. 438/2024 Anexo I pág. 19).
- **Inclusión de `Ficha Tecnica Modelo EE.docx` en PyInstaller**: Configurado `build_exe.py` para empaquetar la nueva plantilla Word de Ficha Técnica dentro de `dist/Argos` en instalaciones standalone.

## v3.1.0 (2026-07-29) - Sistema Inteligente Completo, Instalable 1-Clic, Bloques Intertek y Argos Ledger

### ✨ Nuevas Características
- **Ejecutable e Instalador Windows Standalone (v3.1.0)**: Creados los compiladores `build_exe.py` (PyInstaller) e `argos_installer.iss` (Inno Setup) para empaquetar toda la aplicación (FastAPI + React Frontend + PyMuPDF + CustomTkinter) en un instalador Windows instalable en 1-clic (`Argos_Setup_v3_1_0.exe`).
- **Nuevos Ejecutables de Instalación Directa**: Añadidos `Instalar_Argos.bat` e `Iniciar Argos.bat` en la raíz para permitir instalación y arranque inmediato en cualquier PC con 1 clic.
- **Parser por Bloques de Coordenadas (`extract_pdf_clean_text`)**: Implementada la extracción espacial por coordenadas `(y0, x0)` en PyMuPDF que previene el entrelazado de columnas y garantiza la lectura de todas las líneas en certificados complejos de **Intertek**, **IRAM** y **Lenor**.
- **Regla Estricta de Fidelidad sin Alucinaciones en IA**: Reforzadas las instrucciones de OpenAI `gpt-4o-mini` para prohibir expresamente la invención o suposición de datos que no figuren explícitamente en el certificado.
- **Modal de Control de Presupuesto & Argos Ledger**: Incorporado el botón dinámico `💰 Presupuesto & Consumo IA` en el Header del frontend con modal interactivo de consumo acumulado, saldo mensual disponible, peticiones en caché gratuita (`⚡ $0.00 FREE`) e historial detallado.
- **Eficiencia Energética Re-escalada (Res. SIyC N° 438/2024)**: Re-escaladas las familias de Eficiencia Energética estrictamente a letras **A** a **G** (eliminando clases obsoletas A+++/A++/A+) y agregando extracción explícita de **Marca comercial** y **Modelo/s** que autocompleta el Paso 1 al subir el informe PDF.
- **Navegación Fluida en Paso 5**: Corregido el flujo UI del Paso 5 de Eficiencia Energética, asegurando que el panel nunca quede en blanco y habilitando los botones de navegación "Anterior" y "Generar DJC-EE" en todos los pasos.

---


### ✨ Nuevas Características
- **Planilla de Fotos (Datasheet) Autogenerada**: El orquestador de solicitudes para Lenor ahora genera y adjunta automáticamente en el ZIP de salida la planilla Excel precargada (`Datasheet_[Nro].xlsx`) con las tablas de modelos y especificaciones de todos los SKUs, combinando celdas de marcas/especificaciones/imagen y aplicando bordes negros estéticos listos para pegar fotos.
- **Reordenamiento del Menú UI**: Se reorganizó el sidebar lateral del frontend para que refleje el flujo secuencial real de los procesos: *Solicitudes* arriba (primer proceso), *Verificador* en el medio y *Generador DJC* abajo.
- **Soporte Completo de Múltiples Marcas**: La función `split_marcas` ahora soporta la separación por comas (`,`) y puntos y comas (`;`), permitiendo la correcta duplicación de modelos para marcas declaradas en conjunto como `GADNIC; CARE BY GADNIC`.
- **Extracción de Marcas Combinadas de Anexos**: Modificados los extractores del anexo de Lenor para unir todas las marcas únicas detectadas con punto y coma en lugar de descartar la segunda.
- **Formato Calibri 12 en Word**: Configurada la tabla de la nota comercial Word para Lenor para forzar la tipografía **Calibri** en tamaño **12**.

### 🐛 Correcciones
- **Celdas C51 y C53 de Lenor**: Se eliminó la escritura forzada del script sobre las celdas C51 ("Tipo de solicitud") y C53 ("Esquema de certificación (*)") para conservar los valores estáticos preconfigurados en la plantilla por el usuario.

---

## v2.4.0 (2026-06-09) - Corrección de Fallback openpyxl y Mappings de Celdas

### ✨ Nuevas Características
- **Versión Dinámica en UI**: El panel lateral (sidebar) del frontend ahora consulta el número de versión directamente al backend mediante la llamada de salud (health check), evitando inconsistencias y hardcoding.

### 🐛 Correcciones
- **Alineación de Mappings en Fallback openpyxl**: Se actualizaron por completo las coordenadas de escritura en el generador openpyxl (usado si win32com no está disponible) para coincidir con la automatización win32, solucionando problemas de celdas vacías (`C51`, `C53`, `C57`, `C59`), contacto de fábrica limpio (`C46`) e email/teléfono invertidos (`E46`/`G46`).
- **Renombrado y Duplicado de Marcas**: Se refinó la lógica de marcas múltiples y duplicación de filas (sólo para Lenor) en ambos generadores.

---

## v2.1.0 (2026-05-23) - Módulo de Eficiencia Energética (EE) Integrado

### ✨ Nuevas Características
- **Módulo de Eficiencia Energética Completo**: Implementado el soporte para las 11 familias de la Resolución SIyC 438/2024 a través de un esquema dinámico de características técnicas (`ee_families.json`).
- **Autogeneración e Integración de Etiquetas EE**: El sistema dibuja y renderiza la etiqueta oficial de eficiencia energética en tiempo real en base a los datos cargados en el formulario, eliminando la necesidad de descargas o cargas manuales secundarias.
- **Formato de ID Simplificado**: Ajustado el formato a `DJC-EE-MMYY-CXXX-V1` sin abreviatura de laboratorios por directiva del usuario.
- **Inserción Automática en Word**: Modificado el motor docx para inyectar automáticamente la etiqueta renderizada (PNG) y las características compuestas en la Tabla 5 y Tabla 3 de la plantilla oficial.

### 🐛 Correcciones
- **Compilación estricta del Frontend**: Resueltos errores del compilador tsc de TypeScript relacionados a declaraciones redundantes o variables no utilizadas.

---

## v2.0.3 (2026-05-19) - Optimización de Rasterizado y Empaquetado OCR

### ✨ Nuevas Características
- **Empaquetado de Tesseract OCR**: Se modificó `build_exe.py` y `pdf_ops.py` para incluir Tesseract automáticamente en el `.exe` compilado por PyInstaller (vía `sys._MEIPASS`), permitiendo OCR local y sin dependencias adicionales en cualquier PC.

### 🐛 Correcciones
- **Optimización de PDFs (OOM Fix)**: Se cambió el formato de rasterizado de `png` a `jpeg` (con compresión) en la generación de DJs, reduciendo drásticamente el tamaño de los PDFs de ~74 MB a ~3 MB, y resolviendo los cuelgues del frontend (Unexpected end of JSON input).

---

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
