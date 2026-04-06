# ARGOS - Changelog

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
