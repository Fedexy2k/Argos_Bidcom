# Reglas de Proyecto: Argos

**Objetivo:** Plataforma para generación masiva de DJC (Declaraciones Juradas de Conformidad) y auditoría de certificados para Bidcom SRL.

**Stack:**
- Backend: Python + FastAPI (`:8742`)
- Frontend: Vite + React + TypeScript (SPA servida desde FastAPI)
- Desktop: Chrome `--app` apuntando al puerto local
- Módulos core: PyMuPDF, python-docx, comtypes, openpyxl, Gemini API

**Directivas de Código:**
- Mantener la arquitectura segmentada (`modules/extractors/`, `modules/`)
- Tipado estricto en todas las funciones nuevas
- Toda nueva interfaz respeta el dark theme y accent purple existente
- Null-Safety obligatorio al extraer datos de documentos

---

## 🔄 Metodología de Desarrollo: Validación Previa por Pasos

Antes de escribir o modificar código para cualquier nueva funcionalidad o mejora:
1. **Presentar el Flujo de Usuario Final**: Explicar el proceso paso a paso de cómo interactuará el usuario con la mejora antes de implementarla.
2. **Plan de Pruebas y Verificación**: Detallar exactamente cómo se va a probar la funcionalidad para asegurar que opera sin errores ni efectos colaterales.
3. **Aprobación del Usuario**: Esperar la confirmación explícita del usuario antes de proceder a la implementación.
4. **Desarrollo Iterativo (Bucles Cortos)**: Avanzar en pasos pequeños y autónomos, otorgando control total al usuario en cada etapa.

---

## 📜 Directiva de Logging Extensivo y Visibilidad de Ejecución

- **Logs Explicativos y Detallados en Tiempo Real**: Todo script o módulo (Python, FastAPI, Apps Script) debe contar con un sistema de logging sumamente detallado e informativo.
- En **Apps Script**: Utilizar `Logger.log()` con prefijos visuales claros (`[INICIO]`, `[BUSQUEDA]`, `[PARSEO]`, `[MATCH]`, `[CAMBIO_ESTADO]`, `[DUPLICADO]`, `[ERROR]`) y/o volcar eventos en hojas de log (`Log_Sync`) para que el usuario vea exactamente qué hace el programa paso a paso.
- En **Python / Argos Backend**: Mantener la emisión en vivo por WebSockets (`LogBroadcaster`) y logs de consola formateados para visibilidad total en tiempo real.

---



## 📦 Política de Versionado — Semantic Versioning (MAJOR.MINOR.PATCH)

### Cuándo subir cada número

| Tipo | Cuándo | Ejemplo real |
|------|--------|-------------|
| **PATCH** `x.y.Z` | Bugfix o mejora interna sin funcionalidad nueva visible | Fix crash PDF 74MB → 3MB (v2.0.3) |
| **MINOR** `x.Y.0` | Nueva funcionalidad completa y estable (nuevo módulo, nueva vista) | Agregar DJC-EE, módulo Solicitud → v2.1.0 |
| **MAJOR** `X.0.0` | Cambio de arquitectura disruptivo o breaking change | Migración CustomTkinter → React (v2.0.0) |

> **Regla simple:** ¿El usuario ve algo nuevo que antes no existía? → MINOR. ¿Se arregló algo roto? → PATCH. ¿Se refactorizó todo? → MAJOR.

> [!IMPORTANT]
> **Control estricto de versiones en desarrollo:**
> - **NO** se debe incrementar la versión del software en ningún archivo (`launcher.py`, `api/main.py`, etc.) por cada pequeño cambio o commit intermedio durante el desarrollo de una feature o bugfix.
> - La versión debe permanecer **fija** en la última versión oficial (ej. `v2.5.0`) durante toda la etapa de desarrollo y pruebas.
> - La versión solo se sube de número al finalizar por completo el desarrollo, haberlo verificado con éxito, y estar listos para consolidar una **Release Oficial** y compilar el instalador.

### Archivos que actualizar en CADA release

Estos 6 archivos siempre van juntos. Sin excepción:

| Archivo | Dónde | Qué cambiar |
|---------|-------|-------------|
| `CHANGELOG.md` | Tope del archivo | Nueva entrada `## vX.Y.Z (YYYY-MM-DD) - Título` |
| `launcher.py` | Líneas ~120 y ~133 | `"Argos V2.0.3"` → nuevo número |
| `api/main.py` | Línea ~123 | `FastAPI(version="2.0.3", ...)` |
| `api/main.py` | Línea ~463 | `{"status": "ok", "version": "2.0.3"}` |
| `frontend/src/components/Sidebar.tsx` | Línea ~129 | `v2.0.3` en el badge inferior |
| `argos_installer.iss` | Línea 5 | `AppVersion=2.0.3` |

### Checklist antes de cada commit con cambios

```
[ ] Todos los archivos de versión actualizados (los 6 de arriba)
[ ] Entrada nueva en CHANGELOG.md con fecha, tipo (✨/🐛/🔧) y descripción
[ ] Cambio probado y aprobado por el usuario
[ ] git commit -m "feat: ..." / "fix: ..." / "refactor: ..."
[ ] git push origin main
```

---

## Versión actual: v3.2.2
