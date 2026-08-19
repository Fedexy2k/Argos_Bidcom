# ⚡ ARGOS — Sistema Inteligente de Certificaciones (v3.2.2)
> **Solución Integrada para Declaraciones Juradas de Conformidad (DJC), Eficiencia Energética (Res. 438/2024), Solicitudes Lenor/QETKRA y Control de Presupuesto IA.**
> **GADNIC / BIDCOM S.R.L.**

---

## 🚀 Características Principales

### ⚡ 1. Eficiencia Energética (SIyC Res. N° 438/2024)
- **Extracción Inteligente por IA (`gpt-4o-mini`)**: Procesa Informes de Ensayo en PDF (TÜV Rheinland, IRAM, etc.) extrayendo automáticamente:
  - Marca comercial (ej: `GADNIC`) y lista de modelos (ej: `GADW14`).
  - Clase de Eficiencia Energética re-escalada (Escala estricta **A** a **G**, sin clases obsoletas A+++/A++/A+).
  - Índice de Eficiencia Energética (IEE), consumos anuales y por ciclo, ruido (dB), capacidad y secado.
  - Especificaciones eléctricas base (Tensión, Frecuencia, Potencia nominal y Clase I de aislación).
  - Laboratorio de ensayo, correo/web de contacto, fecha de emisión y vencimiento automático a +4 años.
- **Generación de Ficha Técnica Dinámica (Art. 7°)**: Emisión automática de la Ficha Técnica de Información de Producto en Word/PDF con superset de 44 especificaciones técnicas y borrado dinámico de filas no aplicables.
- **Generación de Etiquetas en Vivo**: Visualizador dinámico SVG/HTML de la etiqueta oficial de Eficiencia Energética por modelo (con plantillas 1:1 de Illustrator para Lavarropas, Heladeras, etc.).
- **DJC-EE Word & PDF**: Compilación automática del documento de Declaración Jurada de Eficiencia Energética con etiquetas incrustadas.

### 📜 2. Generador DJC de Seguridad Eléctrica
- **Revisión Semántica por IA**: Cruza el texto del certificado contra la base de datos para verificar que fabricante, marca, modelos y normas coincidan al 100%.
- **Censura y Censura de PDFs**: Elimina carátulas viejas y aplica censura de datos sensibles sobre los certificados escaneados.
- **Salida Multimodelo**: Exporta documentos en Word y PDF con firmas, marcas registradas y código QR integrado.

### 📦 3. Solicitudes de Certificación (Lenor / QETKRA)
- **Parseo Inteligente de Datasheets**: Lee planillas de ingeniería en Excel (`.xlsx`, `.xlsm`) y certificados en PDF.
- **Clasificador Automático**: Agrupa SKUs, detecta la certificadora aplicable (**Lenor** o **QETKRA**) y sugiere la norma técnica (**Res. SIC 16/2025**, **Res. SIC 17/2025**, etc.).

### 💰 4. Control de Consumo IA & Argos Ledger
- **Transparencia Total**: Indicador en vivo en el Header (`💰 $0.0060 / $5.00 USD`) con el gasto acumulado del mes.
- **Modal de Auditoría**: Pestaña visual con la tabla de historial de peticiones, tokens consumidos, costo exacto y peticiones resueltas mediante **Caché Inteligente** (`⚡ $0.00 FREE`).
- **Registros Físicos**: Generación automática de `logs/usage_ledger.json` y `logs/budget_summary.json`.

---

## 🛠️ Instalación y Ejecución

### Opción A: Instalador Ejecutable Standalone (Recomendado para Usuario Final)
1. Ejecutá el instalador oficial `Argos_Setup_v3_2_2.exe`.
2. El instalador creará un acceso directo en tu Escritorio y Menú Inicio.
3. Al hacer doble clic en **Argos**, se abrirá la aplicación en modo ventana independiente (App Mode).

### Opción B: Ejecución desde Código Fuente (Entorno de Desarrollo)
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/Fedexy2k/Argos_Bidcom.git
   cd Argos_Bidcom
   ```
2. Ejecutar el instalador automático:
   ```cmd
   Instalar_Argos.bat
   ```
3. Iniciar la aplicación:
   ```cmd
   Iniciar Argos.bat
   ```
   *O alternativamente mediante el launcher directo de Python:*
   ```cmd
   python launcher.py
   ```

---

## 🏗️ Arquitectura del Sistema

```
Argos_Bidcom/
├── api/                   # Backend FastAPI (REST API & WebSockets)
│   ├── main.py            # Endpoints principales y montaje de assets
│   └── startup.py         # Script de arranque del servidor Uvicorn (Puerto 8742)
├── frontend/              # Interfaz de Usuario React + Vite + TailwindCSS
│   ├── src/
│   │   ├── views/         # EficienciaEnergetica.tsx, GeneradorDJC.tsx, Solicitudes.tsx
│   │   ├── components/    # BudgetModal.tsx, Sidebar.tsx, LogBar.tsx
│   │   └── api/           # Clientes HTTP (client_ee.ts, client_solicitud.ts, client.ts)
├── modules/               # Motores de Inteligencia Artificial y Procesamiento
│   ├── ai_helper.py       # OpenAI gpt-4o-mini client, prompts y estructuración JSON
│   ├── ai_cache.py        # Caché inteligente de respuestas IA (Costo $0)
│   ├── budget_manager.py  # Control de cuota mensual USD y Ledger
│   ├── pdf_ops.py         # Extracción de layout por bloques (y0, x0) y censura de PDFs
│   └── m5_solicitud_generator.py # Generador de solicitudes Lenor/QETKRA
├── ee_families.json       # Catálogo oficial de familias de Eficiencia Energética
├── build_exe.py           # Compilador de ejecutable PyInstaller
└── argos_installer.iss    # Guion de compilación de instalador Inno Setup
```

---

## 📄 Licencia y Créditos
Desarrollado para el Departamento de Certificaciones e Ingeniería de **BIDCOM S.R.L. / GADNIC**.
Todos los derechos reservados © 2026.
