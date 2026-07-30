"""
Argos - Sistema de Auditoría de Certificados
Interfaz gráfica principal
"""
import customtkinter as ctk
from PIL import Image
import os
import logging
from datetime import datetime
from tkinterdnd2 import DND_FILES, TkinterDnD
from gui.themes import ThemeManager
from gui.logger import GuiLogger
from pathlib import Path
import sys

# Cargar variables de entorno del archivo .env (para API keys, etc.)
def load_env_file():
    """Carga variables del archivo .env si existe."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Cargar .env antes de importar módulos que puedan necesitar variables de entorno
load_env_file()


class ArgosApp(TkinterDnD.Tk):
    """Aplicación principal de Argos"""
    
    VERSION = "1.0.0"
    
    def __init__(self):
        super().__init__()
        
        # Aplicar tema de CustomTkinter manualmente
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        
        # Inicializar componentes
        self.theme_manager = ThemeManager()
        self.logger = GuiLogger()
        
        # Variables de estado
        self.datasheet_path: str | None = None
        self.parsed_data: dict = {}  # Datos parseados del datasheet
        self.certificate_paths: list[str] = []
        self.audit_results: dict = {}  # Resultados de auditoría
        self.current_tab = "verificador"  # Tab activo por defecto
        
        # Configurar ventana
        self.setup_window()
        self.setup_theme()
        self.create_widgets()
        
        self.logger.info("Argos iniciado correctamente")
    
    def setup_window(self):
        """Configura la ventana principal"""
        self.title(f"ARGOS v{self.VERSION} - Auditor de Certificados")
        
        # Tamaño adaptado a la pantalla
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width  = min(1250, screen_width  - 100)
        window_height = min(800,  screen_height - 80)
        x = (screen_width  - window_width)  // 2
        y = max(0, (screen_height - window_height) // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Mínimo tamaño
        self.minsize(950, 650)
    
    def setup_theme(self):
        """Configura el tema de CustomTkinter"""
        colors = self.theme_manager.get_current_colors()
        
        # Aplicar configuración de CTk
        ctk.set_appearance_mode("dark" if self.theme_manager.get_theme_name() == "Matrix" else "light")
        ctk.set_default_color_theme("green")
    
    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""
        colors = self.theme_manager.get_current_colors()
        
        # === HEADER ===
        # Estilo fijo y oscuro para el header (independiente del tema)
        header_bg = "#1a1a1a"
        
        self.header_frame = ctk.CTkFrame(self, fg_color=header_bg, corner_radius=0)
        self.header_frame.pack(fill="x", padx=0, pady=0)
        
        # Logo ASCII minimalista (Argos Panoptes - vigilancia total)
        # Usando círculos pequeños para representar ojos
        logo_text = "◉  ◉\n  ●\n◉  ◉"  # 5 ojos geométricos
        logo_label = ctk.CTkLabel(
            self.header_frame,
            text=logo_text,
            font=("Roboto Medium", 12),
            text_color="#00ff41", # Verde Matrix
            justify="center"
        )
        logo_label.pack(side="left", padx=(20, 10), pady=6)
        
        # Título ARGOS
        name_label = ctk.CTkLabel(
            self.header_frame,
            text="ARGOS",
            font=("Roboto", 22, "bold"),
            text_color="#ffffff"
        )
        name_label.pack(side="left", padx=(0, 5), pady=6)
        
        version_label = ctk.CTkLabel(
            self.header_frame,
            text=f"v{self.VERSION}",
            font=("Roboto", 10),
            text_color="#888888"
        )
        version_label.pack(side="left", padx=0, pady=6)
        
        # Botones de header
        btn_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, pady=6)
        
        # Botón Debug
        self.debug_btn = ctk.CTkButton(
            btn_frame,
            text="🐛 Debug",
            width=80,
            command=self.toggle_debug,
            fg_color="#333333",
            hover_color="#444444",
            text_color="white",
            font=("Roboto", 11)
        )
        self.debug_btn.pack(side="left", padx=5)
        
        # Botón Theme Cycle
        self.theme_btn = ctk.CTkButton(
            btn_frame,
            text=f"🌓 {self.theme_manager.get_theme_name()}",
            width=100,
            command=self.cycle_theme,
            fg_color="#0066cc",
            hover_color="#0055aa",
            text_color="white",
            font=("Roboto", 11)
        )
        self.theme_btn.pack(side="left", padx=5)
        
        # === TABS NAVIGATION ===
        tab_bar_bg = "#252525"
        self.tab_bar = ctk.CTkFrame(self, fg_color=tab_bar_bg, corner_radius=0, height=40)
        self.tab_bar.pack(fill="x", padx=0, pady=0)
        
        # Contenedor para botones de tabs
        tabs_container = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        tabs_container.pack(side="left", padx=20, pady=3)
        
        # Definir tabs con iconos de ojos de Argos
        self.tabs = [
            {"id": "solicitud", "name": "\u25c9 Solicitud", "icon": "\u25c9"},
            {"id": "verificador", "name": "\u25c9\u25c9 Verificador", "icon": "\u25c9\u25c9"},
            {"id": "generador", "name": "\u25c9\u25c9\u25c9 Generador DJC", "icon": "\u25c9\u25c9\u25c9"},
        ]
        
        self.tab_buttons = {}
        for tab in self.tabs:
            btn = ctk.CTkButton(
                tabs_container,
                text=tab["name"],
                width=140,
                height=34,
                corner_radius=0,
                fg_color="#333333" if tab["id"] == self.current_tab else "transparent",
                hover_color="#444444",
                text_color="#00ff41" if tab["id"] == self.current_tab else "#888888",
                font=("Roboto", 11, "bold" if tab["id"] == self.current_tab else "normal"),
                command=lambda t=tab["id"]: self.switch_tab(t)
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons[tab["id"]] = btn
        
        # === MAIN CONTENT ===
        # Container para el contenido de cada tab
        self.content_container = ctk.CTkFrame(self, fg_color=colors["bg_primary"], corner_radius=0)
        self.content_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Mostrar tab inicial
        self.switch_tab(self.current_tab)
        
        # ### PASO 1 y 2 MOVIDOS A show_verificador_tab() ###
        # (El código de datasheet y certificados ahora se crea dinámicamente en el tab correspondiente)
        
        # === DEBUG PANEL (oculto por defecto) ===
        self.debug_panel = None
    
    def on_drop_datasheet(self, event):
        """Maneja el drop de datasheet"""
        files = self.tk.splitlist(event.data)
        if files:
            file_path = files[0]
            if file_path.endswith('.xlsx'):
                self.datasheet_path = file_path
                self.logger.info(f"Datasheet cargado: {file_path}")
                
                # Parsear automáticamente
                self.parse_datasheet()
            else:
                self.datasheet_status.configure(
                    text="✗ Error: Solo archivos .xlsx",
                    text_color=self.theme_manager.get_current_colors()["error"]
                )
                self.logger.error("Intento de cargar archivo no .xlsx como datasheet")
    
    def parse_datasheet(self):
        """Parsea el datasheet y muestra preview de datos"""
        from modules.m1_ingest import DatasheetParser
        
        try:
            if not self.datasheet_path:
                return
            self.logger.info("Parseando datasheet...")
            parser = DatasheetParser(self.datasheet_path)
            self.parsed_data = parser.parse()
            
            filename = Path(self.datasheet_path).name
            
            # Extraer info clave para preview
            id_gestion = self.parsed_data.get('id_gestion', 'N/A')
            tipo = self.parsed_data.get('tipo_producto', 'N/A')
            marca = self.parsed_data.get('marca', 'N/A')
            modelos = self.parsed_data.get('modelos_solicitados', [])
            num_modelos = len(modelos)
            
            # Actualizar status con preview
            preview_text = f"✓ {filename}\n"
            preview_text += f"   ID: {id_gestion} | Tipo: {tipo}\n"
            preview_text += f"   Marca: {marca} | Modelos: {num_modelos}"
            
            self.datasheet_status.configure(
                text=preview_text,
                text_color=self.theme_manager.get_current_colors()["success"]
            )
            
            self.logger.info(f"Datasheet parseado: {tipo} - {marca} - {num_modelos} modelo(s)")
            self.check_ready_to_audit()
            
        except Exception as e:
            self.logger.error(f"Error al parsear datasheet: {str(e)}")
            self.datasheet_status.configure(
                text=f"✗ Error al parsear archivo\n{str(e)}",
                text_color=self.theme_manager.get_current_colors()["error"]
            )
            self.parsed_data = None
    
    def on_drop_certificates(self, event):
        """Maneja el drop de certificados"""
        files = self.tk.splitlist(event.data)
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        if pdf_files:
            self.certificate_paths.extend(pdf_files)
            self.update_certificates_list()
            self.logger.info(f"{len(pdf_files)} certificado(s) agregado(s)")
            self.check_ready_to_audit()
        else:
            self.logger.error("Intento de cargar archivos no PDF")
    
    def update_certificates_list(self):
        """Actualiza la lista visual de certificados"""
        # Limpiar lista actual
        for widget in self.certs_list_frame.winfo_children():
            widget.destroy()
        
        colors = self.theme_manager.get_current_colors()
        
        # Agregar cada certificado
        for i, cert_path in enumerate(self.certificate_paths):
            cert_frame = ctk.CTkFrame(self.certs_list_frame, fg_color=colors["bg_primary"])
            cert_frame.pack(fill="x", pady=2)
            
            label = ctk.CTkLabel(
                cert_frame,
                text=f"✓ {Path(cert_path).name}",
                font=("Segoe UI", 10),
                text_color=colors["success"],
                anchor="w"
            )
            label.pack(side="left", padx=10, pady=5)
            
            # Botón eliminar
            remove_btn = ctk.CTkButton(
                cert_frame,
                text="✖",
                width=30,
                height=25,
                command=lambda idx=i: self.remove_certificate(idx),
                fg_color=colors["error"],
                hover_color=colors["bg_tertiary"]
            )
            remove_btn.pack(side="right", padx=5)
        
        # Actualizar status
        num_certs = len(self.certificate_paths)
        if num_certs == 0:
            self.certs_status.configure(
                text="Sin certificados cargados",
                text_color=colors["text_secondary"]
            )
        else:
            plural = "certificado" if num_certs == 1 else "certificados"
            self.certs_status.configure(
                text=f"✓ {num_certs} {plural} cargado(s)",
                text_color=colors["success"]
            )
    
    def remove_certificate(self, index):
        """Elimina un certificado de la lista"""
        if 0 <= index < len(self.certificate_paths):
            removed = self.certificate_paths.pop(index)
            self.logger.info(f"Certificado eliminado: {Path(removed).name}")
            self.update_certificates_list()
            self.check_ready_to_audit()
    
    def check_ready_to_audit(self):
        """Verifica si se puede iniciar auditoría"""
        if self.parsed_data and len(self.certificate_paths) > 0:
            self.audit_btn.configure(state="normal")
        else:
            self.audit_btn.configure(state="disabled")
    
    def load_from_link(self):
        """Carga datasheet desde link de Google Drive"""
        link = self.link_entry.get()
        if link:
            self.logger.info(f"Intentando cargar desde link: {link}")
            # TODO: Implementar descarga desde Google Drive
            self.datasheet_status.configure(
                text="⚠ Función de descarga en desarrollo",
                text_color=self.theme_manager.get_current_colors()["warning"]
            )
        else:
            self.logger.warning("Link vacío")
    
    def start_audit(self):
        """Inicia el proceso de auditoría"""
        if not self.parsed_data:
            self.logger.error("No hay datos parseados del datasheet")
            return
        
        self.logger.info("=== INICIANDO AUDITORÍA ===")
        self.logger.info(f"Datasheet: {self.datasheet_path}")
        self.logger.info(f"Certificados: {len(self.certificate_paths)}")
        
        try:
            from modules.m2_multiaudit import MultiCertAuditor
            
            # Crear mapa de certificados
            # Por ahora asumimos que el usuario arrastra en orden correcto
            # TODO: Mejorar detección automática de tipo de certificado
            cert_types = self.parsed_data.get("certificados_requeridos", [])
            paths_map = {}
            
            for i, req in enumerate(cert_types):
                cert_type = req["tipo"]
                if i < len(self.certificate_paths):
                    paths_map[cert_type] = self.certificate_paths[i]
                    self.logger.info(f"Mapeado: {cert_type} -> {Path(self.certificate_paths[i]).name}")
            
            # Ejecutar auditoría
            self.logger.info("Ejecutando auditoría con estrategias adaptativas...")
            auditor = MultiCertAuditor(logger=self.logger)
            self.audit_results = auditor.audit_multiple(self.parsed_data, paths_map)
            
            self.logger.info(f"Auditoría completada. Estado: {self.audit_results.get('status')}")
            
            # Mostrar resultados
            self.show_results()
            
        except Exception as e:
            self.logger.error(f"Error durante auditoría: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            colors = self.theme_manager.get_current_colors()
            self.datasheet_status.configure(
                text=f"✗ Error en auditoría: {str(e)}",
                text_color=colors["error"]
            )
    def show_results(self):
        """Muestra los resultados de la auditoría inline"""
        self.logger.info("Mostrando pantalla de resultados...")
        
        if not self.audit_results:
            self.logger.error("❌ show_results llamado sin audit_results")
            return
        
        try:
            colors = self.theme_manager.get_current_colors()
            
            # Ocultar tab bar y content_container
            if hasattr(self, 'tab_bar') and self.tab_bar.winfo_exists():
                self.tab_bar.pack_forget()
                self.logger.info("Tab bar oculto")
            
            if hasattr(self, 'content_container') and self.content_container.winfo_exists():
                self.content_container.pack_forget()
                self.logger.info("Content container oculto correctamente")
            
            # Crear frame de resultados
            self.results_frame = ctk.CTkFrame(self, fg_color=colors["bg_primary"], corner_radius=0)
            self.results_frame.pack(fill="both", expand=True)
            
            # Barra de navegación simple con estilo consistente
            nav_bg = "#1a1a1a"
            nav_frame = ctk.CTkFrame(self.results_frame, fg_color=nav_bg, height=50, corner_radius=0)
            nav_frame.pack(fill="x", padx=0, pady=0)
            
            # Botón Volver grande y claro
            back_btn = ctk.CTkButton(
                nav_frame,
                text="← VOLVER A CARGA",
                font=("Roboto", 12, "bold"),
                command=self.return_to_main,
                fg_color="#333333",
                text_color="white",
                hover_color="#444444",
                width=150,
                height=35
            )
            back_btn.pack(side="left", padx=20, pady=10)
            
            # Botón Generar DJC
            djc_btn = ctk.CTkButton(
                nav_frame,
                text="📋 GENERAR DJC",
                font=("Roboto", 12, "bold"),
                command=self.show_djc_view,
                fg_color="#1976D2",
                text_color="white",
                hover_color="#1565C0",
                width=150,
                height=35
            )
            djc_btn.pack(side="left", padx=10, pady=10)
            
            # Estado Global con fuente grande
            status = self.audit_results.get("status", "UNKNOWN")
            self.logger.info(f"Estado global auditoría: {status}")
            
            status_map = {
                "OK": ("✅ CERTIFICADO APROBADO", colors["success"]),
                "WARNING": ("⚠️ REVISIÓN REQUERIDA", colors["warning"]),
                "FAIL": ("❌ RECHAZADO", colors["error"])
            }
            text, color = status_map.get(status, ("UNKNOWN", colors["text_primary"]))
            
            status_label = ctk.CTkLabel(
                nav_frame,
                text=text,
                font=("Roboto", 20, "bold"),
                text_color=color
            )
            status_label.pack(side="right", padx=20)
            self.nav_status_label = status_label # Guardar referencia para actualizaciones
            
            # Área scrollable principal
            scroll_frame = ctk.CTkScrollableFrame(
                self.results_frame,
                fg_color="transparent", 
                corner_radius=0
            )
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
            self.logger.info("Scroll frame creado")
            
            # Detalles por certificado
            details = self.audit_results.get("details", {})
            self.logger.info(f"Procesando {len(details)} certificados en UI")
            
            for cert_key, cert_res in details.items():
                self.logger.info(f"Creando tarjeta para: {cert_key}")
                self.create_certificate_card(scroll_frame, cert_key, cert_res, colors)
                
            self.logger.info("Pantalla de resultados renderizada completamente")

        except Exception as e:
            self.logger.error(f"❌ Error CRÍTICO renderizando resultados: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            # Intentar volver a main si falla
            self.return_to_main()

    def create_certificate_card(self, parent, cert_key, cert_res, colors):
        """Crea una tarjeta visual para cada certificado"""
        
        cert_status = cert_res.get("status", "UNKNOWN")
        
        # Tarjeta contenedora con borde estándar (Usuario pidió no usar verde en toda la tarjeta)
        card = ctk.CTkFrame(
            parent, 
            fg_color=colors["bg_secondary"], 
            corner_radius=10, 
            border_width=1, 
            border_color=colors["border"]
        )
        card.pack(fill="x", pady=15, padx=5)
        
        # Header de la tarjeta
        header = ctk.CTkFrame(card, fg_color="transparent", height=40)
        header.pack(fill="x", padx=20, pady=15)
        
        # Íconos y Nombres Personalizados
        raw_name = cert_key.replace('CERT_', '')
        display_name = raw_name.replace('_', ' ') # Quitar guiones bajos
        
        type_icon = "📄" # Default
        if "SEGURIDAD" in raw_name and "ELECTRICA" in raw_name:
            type_icon = "⚡"
        elif "JUGUETES" in raw_name:
            type_icon = "🧸"
        elif "FTALATOS" in raw_name:
            type_icon = "🧪"
            
        # Título limpio (Solo ícono de tipo + Nombre)
        title = ctk.CTkLabel(
            header, 
            text=f"{type_icon} {display_name}",
            font=("Segoe UI", 18, "bold"),
            text_color=colors["text_primary"]
        )
        title.pack(side="left")
        
        # Metadata (Checklist)
        metadata = cert_res.get("metadata", {})
        
        # Separador
        ctk.CTkFrame(card, height=2, fg_color=colors["bg_tertiary"]).pack(fill="x", padx=20, pady=(0, 20))
        
        # Contenedor de items
        items_frame = ctk.CTkFrame(card, fg_color="transparent")
        items_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        if metadata:
            for field, data in metadata.items():
                # Pasamos cert_key para poder identificar el item único en overrides
                self.create_field_row(items_frame, field, data, colors, cert_key)
        
        # Mensajes extra (si hay errores críticos que no vienen de metadatos)
        details = cert_res.get("details", {})
        criticos = details.get("critical", [])
        if criticos:
            for msg in criticos:
                if "mismatch" not in msg: # Evitar duplicados si ya está en metadatos
                    ctk.CTkLabel(items_frame, text=f"❌ {msg}", text_color=colors["error"]).pack(anchor="w", pady=2)

    def create_field_row(self, parent, field, data, colors, cert_key):
        """Crea una fila de comparación con alineación estricta usando Grid"""
        
        row = ctk.CTkFrame(parent, fg_color=colors["bg_tertiary"], corner_radius=6)
        
        # Estado inicial visual
        status = data.get("status", "UNKNOWN")
        if status == "OK":
            row.configure(border_color=colors["success"], border_width=2)
            
        row.pack(fill="x", pady=5)
        
        # Configuración de Grid - 4 columnas con pesos fijos
        # Col 0: Título y Acciones (fijo 260px)
        # Col 1: Datasheet (flexible, igual peso que col 3)
        # Col 2: Separador visual (fijo 10px)
        # Col 3: Certificado (flexible, igual peso que col 1)
        row.grid_columnconfigure(0, minsize=260, weight=0)
        row.grid_columnconfigure(1, weight=1, uniform="data_cols")
        row.grid_columnconfigure(2, minsize=10, weight=0)
        row.grid_columnconfigure(3, weight=1, uniform="data_cols")
        
        # Guardar referencia para actualizaciones
        row.field_data = data
        
        # --- COLUMNA 0: Título y Acciones ---
        col0_frame = ctk.CTkFrame(row, fg_color="transparent")
        col0_frame.grid(row=0, column=0, sticky="nw", padx=15, pady=10)
        
        status = data.get("status", "UNKNOWN")
        icon_map = {"OK": "✅", "WARNING": "⚠️", "FAIL": "❌"}
        
        self.create_status_label(col0_frame, field, status, icon_map, colors)
        
        if status in ["WARNING", "FAIL"]:
            self.create_action_buttons(col0_frame, field, row, colors, cert_key)

        # --- PREPARAR DATOS ---
        expected = str(data.get("expected", "-"))
        found = str(data.get("found", "-"))
        
        if isinstance(data.get("expected"), list):
            expected = "\n".join(map(str, data["expected"]))
        if isinstance(data.get("found"), list):
            found = "\n".join(map(str, data["found"]))
            
        # --- COLUMNA 1: Datasheet ---
        ds_frame = ctk.CTkFrame(row, fg_color="transparent")
        ds_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=8)
        ds_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            ds_frame, text="DATASHEET",
            font=("Roboto", 9, "bold"), text_color=colors["text_secondary"]
        ).grid(row=0, column=0, sticky="w")
        
        # Usar Text widget para wrap correcto y lectura completa
        ds_text = ctk.CTkTextbox(
            ds_frame,
            font=("Roboto", 11),
            text_color=colors["text_primary"],
            fg_color="transparent",
            border_width=0,
            wrap="word",
            activate_scrollbars=False,
            height=self._calc_text_height(expected),
        )
        ds_text.insert("1.0", expected)
        ds_text.configure(state="disabled")
        ds_text.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        
        # --- COLUMNA 3: Certificado ---
        cert_frame = ctk.CTkFrame(row, fg_color="transparent")
        cert_frame.grid(row=0, column=3, sticky="nsew", padx=(5, 15), pady=8)
        cert_frame.grid_columnconfigure(0, weight=1)
        
        status_color = colors["error"] if status == "FAIL" else colors["text_primary"]
        if status == "OK": status_color = colors["text_primary"]
        
        ctk.CTkLabel(
            cert_frame, text="CERTIFICADO",
            font=("Roboto", 9, "bold"), text_color=colors["text_secondary"]
        ).grid(row=0, column=0, sticky="w")
        
        cert_text = ctk.CTkTextbox(
            cert_frame,
            font=("Roboto", 11, "bold"),
            text_color=status_color,
            fg_color="transparent",
            border_width=0,
            wrap="word",
            activate_scrollbars=False,
            height=self._calc_text_height(found),
        )
        cert_text.insert("1.0", found)
        cert_text.configure(state="disabled")
        cert_text.grid(row=1, column=0, sticky="ew", pady=(2, 0))

    def _calc_text_height(self, text: str, line_height: int = 20, min_h: int = 24, max_h: int = 120) -> int:
        """Calcula altura aproximada para CTkTextbox según cantidad de líneas."""
        lines = text.count("\n") + 1 if text else 1
        # Texto largo en una línea también puede hacer wrap (~60 chars por línea)
        for part in text.split("\n"):
            lines += max(0, len(part) // 60)
        return max(min_h, min(lines * line_height, max_h))

    def create_status_label(self, parent, field, status, icon_map, colors):
        """Helper para crear label de estado que se pueda actualizar"""
        icon = icon_map.get(status, "")
        
        # Color dinámico para el texto
        text_color = colors["text_primary"]
        if status == "OK":
            text_color = colors["success"]
        elif status == "FAIL":
            text_color = colors["error"]
            
        lbl = ctk.CTkLabel(
            parent, 
            text=f"{icon} {field}", 
            font=("Segoe UI", 13, "bold"),
            text_color=text_color,
            wraplength=200,
            justify="left"
        )
        lbl.pack(anchor="w", pady=(0, 5))
        parent.status_label = lbl # Guardar referencia

    def create_action_buttons(self, parent, field_id, row_widget, colors, cert_key):
        """Crea botones de aprobar/rechazar con lógica de toggle y actualización dinámica."""
        
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=(5, 0))
        
        # Referencias a botones para actualizar su estilo
        btn_approve = None
        btn_reject = None
        
        # Estado actual (inicialmente del data, pero puede cambiar)
        current_status = row_widget.field_data.get("status", "UNKNOWN")
        
        def update_ui_state(new_status):
            # Actualizar estilo de la fila
            if new_status == "OK":
                row_widget.configure(border_color=colors["success"], border_width=2)
                if hasattr(parent, 'status_label'):
                    parent.status_label.configure(text=f"✅ {field_id}", text_color=colors["success"])
                # Estilo botones
                if btn_approve: btn_approve.configure(fg_color=colors["success"], state="normal")
                if btn_reject: btn_reject.configure(fg_color=colors["bg_tertiary"], state="normal")
                
            elif new_status == "FAIL":
                row_widget.configure(border_color=colors["error"], border_width=2)
                if hasattr(parent, 'status_label'):
                    parent.status_label.configure(text=f"❌ {field_id}", text_color=colors["error"])
                # Estilo botones
                if btn_approve: btn_approve.configure(fg_color=colors["bg_tertiary"], state="normal")
                if btn_reject: btn_reject.configure(fg_color=colors["error"], state="normal")
            
            else: # WARNING o Reset
                row_widget.configure(border_color="transparent", border_width=0)
                if hasattr(parent, 'status_label'):
                     parent.status_label.configure(text=f"⚠️ {field_id}", text_color=colors["text_primary"])
                # Estilo botones
                if btn_approve: btn_approve.configure(fg_color=colors["bg_tertiary"], state="normal")
                if btn_reject: btn_reject.configure(fg_color=colors["bg_tertiary"], state="normal")

        def on_toggle(action):
            nonlocal current_status
            
            # Determinar nuevo estado
            if action == "approve":
                new_st = "OK" if current_status != "OK" else "WARNING" # Toggle off returns to warning/initial
            else:
                new_st = "FAIL" if current_status != "FAIL" else "WARNING"
            
            current_status = new_st
            
            self.logger.info(f"🔄 Cambio manual: {field_id} -> {new_st}")
            
            # 1. Actualizar Data
            # Importante: Actualizar la estructura de datos real para el recálculo global
            row_widget.field_data["status"] = new_st
            if "manual_override" not in self.audit_results:
                self.audit_results["manual_override"] = {}
            self.audit_results["manual_override"][f"{cert_key}|{field_id}"] = new_st
            
            # 2. Actualizar UI Local
            update_ui_state(new_st)
            
            # 3. Recalcular Estado Global del Certificado y Auditoría
            self.recalculate_global_status()

        btn_approve = ctk.CTkButton(
            btn_frame, 
            text="✓", 
            width=30,
            height=24,
            font=("Roboto", 12, "bold"),
            fg_color=colors["success"] if current_status == "OK" else colors["bg_tertiary"], 
            hover_color=colors["success"],
            command=lambda: on_toggle("approve")
        )
        btn_approve.pack(side="left", padx=(0, 5))
        
        btn_reject = ctk.CTkButton(
            btn_frame, 
            text="✗", 
            width=30,
            height=24,
            font=("Roboto", 12, "bold"),
            fg_color=colors["error"] if current_status == "FAIL" else colors["bg_tertiary"], 
            hover_color=colors["error"],
            command=lambda: on_toggle("reject")
        )
        btn_reject.pack(side="left")

    def recalculate_global_status(self):
        """Recalcula el estado de toda la auditoría basado en los cambios manuales."""
        self.logger.info("⚡ Recalculando estado global...")
        
        global_status = "OK"
        details = self.audit_results.get("details", {})
        
        for cert_name, cert_data in details.items():
            # Recalcular estado del certificado
            cert_failures: int = 0
            cert_warnings: int = 0
            
            # Iterar sobre las validaciones de este certificado
            # NOTA: Esto asume que 'validations' o similar contiene la lista de campos.
            # Como la estructura actual en 'details' es un dict con 'status', 'critical', 'warnings', 
            # necesitamos iterar sobre la metadata si existe, o inferirlo.
            # En la implementación actual de create_certificate_card, iteramos sobre metadata.
            
            meta = cert_data.get("metadata", {})
            for field, data in meta.items():
                st = data.get("status", "OK")
                if st == "FAIL": cert_failures += 1
                elif st == "WARNING": cert_warnings += 1
            
            # Determinar nuevo estado del cert
            new_cert_status = "OK"
            if cert_failures > 0: new_cert_status = "FAIL"
            elif cert_warnings > 0: new_cert_status = "WARNING"
            
            # Actualizar en estructura de datos
            cert_data["status"] = new_cert_status
            
            # Actualizar visualmente la tarjeta (si es posible, requeriría referencias guardadas)
            # Por ahora actualizamos el global status
            if new_cert_status == "FAIL": global_status = "FAIL"
            elif new_cert_status == "WARNING" and global_status != "FAIL": global_status = "WARNING"
            
        # Actualizar self.audit_results
        self.audit_results["status"] = global_status
        
        # Actualizar Header UI
        self.update_header_status(global_status)

    def update_header_status(self, status):
        """Actualiza la barra de navegación con el nuevo estado."""
        colors = self.theme_manager.get_current_colors()
        status_map = {
            "OK": ("✅ AUDITORÍA APROBADA", colors["success"]),
            "WARNING": ("⚠️ REVISIÓN REQUERIDA", colors["warning"]),
            "FAIL": ("❌ FALLO DE AUDITORÍA", colors["error"])
        }
        text, color = status_map.get(status, ("UNKNOWN", colors["text_primary"]))
        
        # Buscar el label en results_frame (hacky pero efectivo si mantenemos estructura)
        # Mejor: guardar referencia en self.nav_status_label
        if hasattr(self, 'nav_status_label'):
             self.nav_status_label.configure(text=text, text_color=color)
    
    def return_to_main(self):
        """Vuelve a la pantalla principal"""
        self.logger.info("Volviendo a pantalla principal")
        
        # Destruir frame de resultados
        if hasattr(self, 'results_frame') and self.results_frame.winfo_exists():
            self.results_frame.destroy()
        
        # Destruir frame de DJC si existe
        if hasattr(self, 'djc_frame') and self.djc_frame.winfo_exists():
            self.djc_frame.destroy()
        
        # Restaurar tab_bar y content_container
        if hasattr(self, 'tab_bar') and self.tab_bar.winfo_exists():
            self.tab_bar.pack(fill="x", padx=0, pady=0, after=self.header_frame)
            self.logger.info("Tab bar restaurado")
        
        if hasattr(self, 'content_container') and self.content_container.winfo_exists():
            self.content_container.pack(fill="both", expand=True, padx=0, pady=0)
            self.logger.info("Content container restaurado")
            
            # Recargar el tab actual
            self.switch_tab(self.current_tab)
        else:
            # Si no existe, recrear widgets
            self.refresh_widgets()

    # ─────────────────────────────────────────────────────────────
    #  Módulo 3: Vista de Generación de DJC
    # ─────────────────────────────────────────────────────────────

    def show_djc_view(self):
        """Muestra la vista de generación de DJC con campos editables."""
        self.logger.info("=== ABRIENDO VISTA DJC ===")
        
        try:
            from modules.m3_djc_generator import DJCGenerator
            from modules.m3_info_panel import DJCInfoPanel
            
            # Solo inicializar si no viene pre-cargado (flujo directo)
            if not hasattr(self, 'djc_gen') or self.djc_gen is None:
                self.djc_gen = DJCGenerator(gui_logger=self.logger)
            
            if not hasattr(self, 'djc_data') or not self.djc_data:
                # Preparar datos desde auditoría
                cert_path = self.certificate_paths[0] if hasattr(self, 'certificate_paths') and self.certificate_paths else None
                if cert_path:
                    cert_data = self.djc_gen.extract_cert_data(cert_path)
                else:
                    cert_data = {}
                
                if hasattr(self, 'parsed_data') and self.parsed_data:
                    self.djc_data = self.djc_gen.prepare_from_audit(self.parsed_data, cert_data)
                    self._djc_source = "audit"
                elif cert_path:
                    self.djc_data = self.djc_gen.prepare_from_certificate(cert_path)
                    self._djc_source = "direct"
                else:
                    self.djc_data = {}
                    self._djc_source = "direct"
            
            # Detectar fuente si no se seteó
            if not hasattr(self, '_djc_source'):
                self._djc_source = "audit"
            
            # Extraer cert_data para dropdowns detectados
            cert_path = self.certificate_paths[0] if hasattr(self, 'certificate_paths') and self.certificate_paths else None
            if cert_path:
                cert_data = self.djc_gen.extract_cert_data(cert_path)
            else:
                cert_data = {}
            
            colors = self.theme_manager.get_current_colors()

            # Ocultar results_frame
            if hasattr(self, 'results_frame') and self.results_frame.winfo_exists():
                self.results_frame.pack_forget()
            
            # Ocultar tab bar y content_container
            if hasattr(self, 'tab_bar') and self.tab_bar.winfo_exists():
                self.tab_bar.pack_forget()
            
            if hasattr(self, 'content_container') and self.content_container.winfo_exists():
                self.content_container.pack_forget()
            
            # Frame principal DJC
            self.djc_frame = ctk.CTkFrame(self, fg_color=colors["bg_primary"], corner_radius=0)
            self.djc_frame.pack(fill="both", expand=True)
            
            # ─── Nav Bar ───
            nav_bg = "#1a1a1a"
            nav = ctk.CTkFrame(self.djc_frame, fg_color=nav_bg, height=50, corner_radius=0)
            nav.pack(fill="x")
            
            back_text = "<< VOLVER A RESULTADOS" if self._djc_source == "audit" else "<< VOLVER AL GENERADOR"
            ctk.CTkButton(
                nav, text=back_text,
                font=("Roboto", 12, "bold"),
                command=self._return_to_results,
                fg_color="#333333", text_color="white", hover_color="#444444",
                width=200, height=35
            ).pack(side="left", padx=20, pady=10)
            
            ctk.CTkLabel(
                nav, text="GENERAR DJC",
                font=("Roboto", 18, "bold"), text_color="#1976D2"
            ).pack(side="right", padx=20)
            
            # ─── Barra de acción FIJA (se packea antes del scroll para que quede abajo) ───
            action_bar = ctk.CTkFrame(self.djc_frame, fg_color="#111111", corner_radius=0, height=75)
            action_bar.pack(fill="x", side="bottom")
            action_bar.pack_propagate(False)
            
            gen_btn = ctk.CTkButton(
                action_bar,
                text="◉  GENERAR DJC  (Word + PDF)",
                font=("Segoe UI", 15, "bold"),
                height=46,
                command=self._execute_djc_generation,
                fg_color="#1976D2",
                hover_color="#1565C0"
            )
            gen_btn.pack(fill="x", padx=20, pady=(10, 4))
            
            self.djc_status = ctk.CTkLabel(
                action_bar, text="", font=("Segoe UI", 10),
                text_color="#aaaaaa"
            )
            self.djc_status.pack()
            
            # ─── Content Area (scrollable) ───
            scroll = ctk.CTkScrollableFrame(self.djc_frame, fg_color="transparent", corner_radius=0)
            scroll.pack(fill="both", expand=True, padx=10, pady=(10, 0))
            
            # Almacenar widgets editables
            self.djc_entries = {}
            
            # --- Indicador de Extensiones seleccionadas ---
            if getattr(self, "_djc_gen_mode", "") == "extension" and getattr(self, "_djc_ext_companies", []):
                ext_frame = ctk.CTkFrame(scroll, fg_color=colors["bg_tertiary"], corner_radius=6, border_width=1, border_color=colors["accent_secondary"])
                ext_frame.pack(fill="x", pady=(0, 15), ipady=8, ipadx=10)
                
                header = ctk.CTkLabel(ext_frame, text="📌 GENERANDO MODO EXTENSIÓN PARA:", font=("Roboto", 12, "bold"), text_color=colors["accent_primary"])
                header.pack(anchor="w", padx=10, pady=(5, 2))
                
                companies_str = " • ".join(self._djc_ext_companies)
                ctk.CTkLabel(ext_frame, text=companies_str, font=("Roboto", 13), text_color=colors["text_primary"], wraplength=700).pack(anchor="w", padx=20, pady=(0, 5))
            
            # ═══════════════════════════════════════════════════════
            # SECCIÓN 1: IDENTIFICACIÓN DJC
            # ═══════════════════════════════════════════════════════
            self._djc_section(scroll, "📋 IDENTIFICACIÓN DE LA DJC", colors,
                              hint="Auto-generado desde el N° interno Bidcom")
            
            # ID DJC - campo editable (para cambiar versión)
            self._djc_field(scroll, "ID DJC",
                            self.djc_data.get("djc_id", ""),
                            colors,
                            hint="Editá el número de versión si es necesario (ej: -V2)",
                            is_editable=True)
            
            # Enlace DJC (usa N° Bidcom)
            self._djc_field(scroll, "Enlace DJC",
                            self.djc_data.get("enlace_djc", ""),
                            colors,
                            is_editable=True)
            
            # ═══════════════════════════════════════════════════════
            # SECCIÓN 2: DATOS DEL PRODUCTO
            # ═══════════════════════════════════════════════════════
            self._djc_section(scroll, "📦 DATOS DEL PRODUCTO", colors,
                              hint="Datos del datasheet — verificá que coincidan con el certificado")
            
            self._djc_field(scroll, "Marca",         self.djc_data.get("marca", ""),             colors)
            self._djc_field(scroll, "Fabricante",    self.djc_data.get("fabricante", ""),         colors)
            self._djc_field(scroll, "Dir. Fábrica",  self.djc_data.get("direccion_fabrica", ""),  colors)
            self._djc_field(scroll, "Descripción",   self.djc_data.get("producto_desc", ""),      colors)
            self._djc_field(scroll, "Modelos",       self.djc_data.get("modelos", ""),            colors)
            self._djc_field(scroll, "Specs Técnicas",self.djc_data.get("specs", ""),              colors)
            
            # ═══════════════════════════════════════════════════════
            # SECCIÓN 3: DATOS DEL CERTIFICADO
            # ═══════════════════════════════════════════════════════
            self._djc_section(scroll, "📄 DATOS DEL CERTIFICADO", colors,
                              hint="Datos extraídos del PDF del certificado")
            
            # Nro de certificado del PDF (ej: LCSH-2058) — NO el número Bidcom
            self._djc_field(scroll, "Nro Certificado (PDF)",
                            self.djc_data.get("cert_number", ""),
                            colors,
                            hint="Ref. según la certificadora (ej: LCSH-2058)")
            
            self._djc_field(scroll, "Normas",           self.djc_data.get("normas", ""),                   colors)
            self._djc_field(scroll, "Fecha Emisión",    self.djc_data.get("fecha_emision", ""),            colors)
            self._djc_field(scroll, "Próx. Vigilancia", self.djc_data.get("fecha_proxima_vigilancia", ""), colors)
            
            # ═══════════════════════════════════════════════════════
            # SECCIÓN 4: DATOS DE CERTIFICACIÓN (dropdowns)
            # ═══════════════════════════════════════════════════════
            self._djc_section(scroll, "⚙️ DATOS DE CERTIFICACIÓN", colors,
                              hint="Detectados automáticamente — podés cambiarlos si es necesario")
            
            # Reglamento dropdown (con callback para recalcular vigencia)
            regl_options = self.djc_gen.get_reglamento_options()
            detected_regl = self.djc_data.get("reglamento", "")
            self._djc_dropdown(scroll, "Reglamento", regl_options, detected_regl, colors,
                               command=self._on_reglamento_changed)
            
            # Esquema dropdown
            esq_options = self.djc_gen.get_esquema_options()
            detected_esq = self.djc_data.get("esquema", "")
            self._djc_dropdown(scroll, "Esquema", esq_options, detected_esq, colors)
            
            # OEC dropdown
            oec_options = list(self.djc_gen.get_oec_options().keys())
            detected_oec_key = cert_data.get("oec_key", "")
            self._djc_dropdown(scroll, "OEC", oec_options, detected_oec_key, colors)
            
            # ═══════════════════════════════════════════════════════
            # SECCIÓN 5: PANEL DE INFORMACIÓN COPIABLE
            # ═══════════════════════════════════════════════════════
            self._djc_section(scroll, "📋 PANEL DE INFORMACIÓN", colors,
                              hint="Datos para copiar al expediente")
            info_panel = DJCInfoPanel(self.djc_data)
            self._djc_info_panel(scroll, info_panel, colors)
            
            # ═══════════════════════════════════════════════════════
            # VERSIONES: DJC NORMAL y/o CODIFICADA
            # Cada checkbox es independiente: pueden estar ambas activas.
            # ═══════════════════════════════════════════════════════
            self._djc_version_normal_var   = ctk.BooleanVar(value=True)
            self._djc_version_cod_var      = ctk.BooleanVar(value=False)
            
            versions_frame = ctk.CTkFrame(scroll, fg_color=colors.get("surface", "#1e1e1e"),
                                           corner_radius=8)
            versions_frame.pack(fill="x", pady=(12, 4), padx=2)
            
            ctk.CTkLabel(
                versions_frame,
                text="Versiones a generar:",
                font=("Roboto", 12, "bold"),
                text_color=colors["text_primary"],
                anchor="w",
            ).pack(side="left", padx=12, pady=8)
            
            ctk.CTkCheckBox(
                versions_frame,
                text="📄  Normal",
                variable=self._djc_version_normal_var,
                font=("Roboto", 12),
                text_color=colors["text_primary"],
                fg_color=colors.get("accent", "#f97316"),
                hover_color=colors.get("accent_hover", "#ea6c0a"),
                corner_radius=5,
            ).pack(side="left", padx=14, pady=8)
            
            ctk.CTkCheckBox(
                versions_frame,
                text="🔒  Codificada",
                variable=self._djc_version_cod_var,
                font=("Roboto", 12),
                text_color="#f97316",
                fg_color=colors.get("accent", "#f97316"),
                hover_color=colors.get("accent_hover", "#ea6c0a"),
                corner_radius=5,
            ).pack(side="left", padx=4, pady=8)
            
            ctk.CTkLabel(
                versions_frame,
                text="(pueden estar ambas activas)",
                font=("Roboto", 10),
                text_color=colors["text_secondary"],
                anchor="w",
            ).pack(side="left", padx=8, pady=8)
            
            self.logger.info("Vista DJC renderizada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error abriendo vista DJC: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _on_codificada_toggle(self):
        """Callback legacy — reemplazado por checkboxes; se mantiene por compatibilidad."""
        pass

    def _djc_section(self, parent, title, colors, hint=None):
        """Encabezado de sección compacto: título + hint + línea."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(10, 2))
        
        # Título y hint en una sola línea
        header_row = ctk.CTkFrame(frame, fg_color="transparent")
        header_row.pack(fill="x")
        
        ctk.CTkLabel(
            header_row, text=title,
            font=("Roboto", 13, "bold"), text_color=colors["accent_secondary"],
            anchor="w"
        ).pack(side="left")
        
        if hint:
            ctk.CTkLabel(
                header_row, text=f"  —  {hint}",
                font=("Roboto", 11), text_color=colors["text_secondary"],
                anchor="w"
            ).pack(side="left", padx=(4, 0))
        
        # Línea divisoria fina
        ctk.CTkFrame(frame, height=1, fg_color=colors["border"]).pack(fill="x", pady=(3, 0))

    def _djc_field(self, parent, label, value, colors, hint=None, is_editable=False):
        """Campo editable con label a la izquierda y entry a la derecha."""
        border_col = colors.get("accent_primary", "#1976D2") if is_editable else colors["border"]
        
        row = ctk.CTkFrame(parent, fg_color=colors["bg_secondary"], corner_radius=8,
                           border_width=1 if is_editable else 0, border_color=border_col)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(0, minsize=180, weight=0)
        row.grid_columnconfigure(1, weight=1)
        
        # Label izquierda
        lbl_frame = ctk.CTkFrame(row, fg_color="transparent")
        lbl_frame.grid(row=0, column=0, sticky="nw", padx=(12, 6), pady=7)
        
        ctk.CTkLabel(
            lbl_frame, text=label,
            font=("Roboto", 12, "bold"),
            text_color=colors["text_primary"],
            anchor="w"
        ).pack(anchor="w")
        
        if hint:
            ctk.CTkLabel(
                lbl_frame, text=hint,
                font=("Roboto", 9), text_color=colors["text_secondary"],
                anchor="w", justify="left", wraplength=170
            ).pack(anchor="w")
        
        # Entry derecha
        entry = ctk.CTkEntry(
            row,
            font=("Roboto", 12),
            fg_color=colors["bg_tertiary"],
            border_color=border_col,
            text_color=colors["text_primary"],
            height=34
        )
        entry.insert(0, str(value) if value else "")
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=7)
        
        self.djc_entries[label] = entry

    def _djc_dropdown(self, parent, label, options, detected, colors, hint=None, command=None):
        """Dropdown auto-detectado compacto."""
        row = ctk.CTkFrame(parent, fg_color=colors["bg_secondary"], corner_radius=8)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(0, minsize=180, weight=0)
        row.grid_columnconfigure(1, weight=1)
        
        # Label izquierda
        lbl_frame = ctk.CTkFrame(row, fg_color="transparent")
        lbl_frame.grid(row=0, column=0, sticky="nw", padx=(12, 6), pady=7)
        
        lbl_row = ctk.CTkFrame(lbl_frame, fg_color="transparent")
        lbl_row.pack(anchor="w")
        
        ctk.CTkLabel(
            lbl_row, text=label,
            font=("Roboto", 12, "bold"),
            text_color=colors["text_primary"]
        ).pack(side="left")
        
        if detected:
            ctk.CTkLabel(
                lbl_row, text="  ✓",
                font=("Roboto", 10, "bold"), text_color=colors["success"]
            ).pack(side="left")
        
        if hint:
            ctk.CTkLabel(
                lbl_frame, text=hint,
                font=("Roboto", 9), text_color=colors["text_secondary"],
                anchor="w", justify="left", wraplength=170
            ).pack(anchor="w")
        
        # Dropdown derecha
        combo = ctk.CTkComboBox(
            row, values=options,
            font=("Roboto", 12),
            fg_color=colors["bg_tertiary"],
            border_color=colors["border"],
            button_color=colors["accent_primary"],
            text_color=colors["text_primary"],
            dropdown_fg_color=colors["bg_secondary"],
            dropdown_text_color=colors["text_primary"],
            height=34,
            command=command
        )
        if detected and detected in options:
            combo.set(detected)
        elif options:
            combo.set(options[0])
        combo.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=7)
        
        self.djc_entries[label] = combo

    def _on_reglamento_changed(self, new_value):
        """
        Callback: recalcula vencimiento e inicio de trámite
        cuando el usuario cambia el Reglamento.
        Ap. IV Electrónica = 4 años, resto = 2 años.
        """
        try:
            emision_widget = self.djc_entries.get("Fecha Emisión")
            vig_widget = self.djc_entries.get("Próx. Vigilancia")
            
            if not emision_widget or not vig_widget:
                return
            
            fecha_emision = emision_widget.get().strip()
            if not fecha_emision:
                return
            
            # Recalcular con el nuevo reglamento
            new_venc = self.djc_gen._calc_vencimiento(fecha_emision, new_value)
            if new_venc:
                vig_widget.delete(0, "end")
                vig_widget.insert(0, new_venc)
                self.logger.info(f"Vigencia recalculada: {new_value} → {new_venc}")
        except Exception as e:
            self.logger.error(f"Error recalculando vigencia: {e}")

    def _djc_info_panel(self, parent, info_panel, colors):
        """Panel de información copiable estilo INAL Suite."""
        panel = ctk.CTkFrame(parent, fg_color=colors["bg_secondary"], corner_radius=8,
                            border_width=1, border_color=colors["accent_secondary"])
        panel.pack(fill="x", pady=5)
        
        for field in info_panel.get_fields():
            row = ctk.CTkFrame(panel, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=3)
            row.grid_columnconfigure(0, minsize=180, weight=0)
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, minsize=65, weight=0)
            
            ctk.CTkLabel(
                row, text=field["label"] + ":",
                font=("Roboto", 11, "bold"),
                text_color=colors["text_secondary"],
                anchor="w"
            ).grid(row=0, column=0, sticky="w")
            
            val_label = ctk.CTkLabel(
                row, text=field["value"] or "-",
                font=("Roboto", 12),
                text_color=colors["text_primary"],
                anchor="w"
            )
            val_label.grid(row=0, column=1, sticky="w")
            
            # Botón copiar
            copy_btn = ctk.CTkButton(
                row, text="Copiar", width=60, height=24,
                font=("Roboto", 9),
                fg_color=colors["bg_tertiary"],
                hover_color=colors["accent_primary"],
                command=lambda v=field["value"]: self._copy_to_clipboard(v)
            )
            copy_btn.grid(row=0, column=2, sticky="e", padx=(5, 0))

    def _copy_to_clipboard(self, text):
        """Copia texto al clipboard."""
        if text:
            self.clipboard_clear()
            self.clipboard_append(str(text))
            self.logger.info(f"Copiado: {str(text)[:40]}")

    def _return_to_results(self):
        """Vuelve a la vista anterior según el flujo de origen."""
        if hasattr(self, 'djc_frame') and self.djc_frame.winfo_exists():
            self.djc_frame.destroy()
        
        # Limpiar datos DJC para permitir re-entrada limpia
        self.djc_data = None
        self.djc_gen = None
        
        source = getattr(self, '_djc_source', 'audit')
        
        if source == "audit":
            # Volver a resultados de auditoría
            if hasattr(self, 'results_frame') and self.results_frame.winfo_exists():
                self.results_frame.pack(fill="both", expand=True)
        else:
            # Volver al tab Generador
            if hasattr(self, 'tab_bar'):
                self.tab_bar.pack(fill="x")
            if hasattr(self, 'content_container'):
                self.content_container.pack(fill="both", expand=True)
            self.switch_tab("generador")

    def _execute_djc_generation(self):
        """Ejecuta la generación de DJC con los datos editados del formulario."""
        self.logger.info("=== GENERANDO DJC ===")
        colors = self.theme_manager.get_current_colors()
        
        try:
            # Recoger datos editados
            data = dict(self.djc_data)  # Copia base
            
            # Actualizar con campos editados (nombres coinciden con los labels en show_djc_view)
            field_map = {
                # Sección Identificación
                "ID DJC":               "djc_id",
                "Enlace DJC":           "enlace_djc",
                # Sección Producto
                "Marca":                "marca",
                "Fabricante":           "fabricante",
                "Dir. Fábrica":         "direccion_fabrica",
                "Descripción":          "producto_desc",
                "Modelos":              "modelos",
                "Specs Técnicas":       "specs",
                # Sección Certificado
                "Nro Certificado (PDF)":"cert_number",
                "Normas":               "normas",
                "Fecha Emisión":        "fecha_emision",
                "Próx. Vigilancia":     "fecha_proxima_vigilancia",
            }
            
            for ui_key, data_key in field_map.items():
                widget = self.djc_entries.get(ui_key)
                if widget:
                    data[data_key] = widget.get()
            
            # Dropdowns
            regl_widget = self.djc_entries.get("Reglamento")
            if regl_widget:
                data["reglamento"] = regl_widget.get()
            
            esq_widget = self.djc_entries.get("Esquema")
            if esq_widget:
                data["esquema"] = esq_widget.get()
            
            oec_widget = self.djc_entries.get("OEC")
            if oec_widget:
                oec_key = oec_widget.get()
                from modules.m3_djc_generator import normalize_oec_key
                normalized_oec_key = normalize_oec_key(oec_key)
                oec_info = self.djc_gen.get_oec_options().get(normalized_oec_key, {})
                data["oec_nombre"] = oec_info.get("nombre", oec_key)
                data["oec_contacto"] = oec_info.get("contacto", "")
            
            # djc_id ya viene del campo editable "ID DJC" — no regenerar
            
            # ═══════════════════════════════════════════════════════
            # DETERMINAR SI ES EXTENSIÓN (bucle) O GENERACIÓN ÚNICA
            # ═══════════════════════════════════════════════════════
            gen_mode = getattr(self, "_djc_gen_mode", "comun")
            
            if gen_mode == "extension":
                # Modo extensión: generar una DJC por cada sociedad seleccionada
                companies = getattr(self, "_djc_ext_companies", [])
                nota_path = getattr(self, "_djc_ext_nota_path", None)
                sociedades_cfg = self.djc_gen.config.get("sociedades_extension", {})
                
                generated_files = []
                for i, company_name in enumerate(companies):
                    self.djc_status.configure(
                        text=f"Generando DJC {i+1}/{len(companies)}: {company_name}...",
                        text_color=colors["text_secondary"]
                    )
                    self.update_idletasks()
                    
                    # Crear copia del data dict para esta iteración
                    ext_data = dict(data)
                    
                    # Inyectar representante autorizado
                    soc_info = sociedades_cfg.get(company_name, {})
                    soc_codigo = soc_info.get("codigo", "LIBR") if soc_info else "LIBR"  # siempre definido
                    if soc_info:
                        ext_data["representante"] = {
                            "nombre": soc_info.get("nombre", company_name),
                            "cuit": soc_info.get("cuit", ""),
                            "domicilio": soc_info.get("domicilio", ""),
                        }
                    else:
                        # Botón "Libre / Otra" → usar nombre tal cual
                        ext_data["representante"] = {
                            "nombre": company_name,
                            "cuit": "",
                            "domicilio": "",
                        }
                    
                    # Generar ID: insertar codigo ANTES del sufijo de versión
                    # DJC-SE-0226-C912-ITK-V1 + BEMO → DJC-SE-0226-C912-ITK-BEMO-V1
                    import re as _re_ext
                    base_id = ext_data.get("djc_id", "DJC-SIN-ID")
                    m_ver = _re_ext.match(r'^(.*?)(-V\d+)$', base_id)
                    if m_ver:
                        ext_data["djc_id"] = f"{m_ver.group(1)}-{soc_codigo}{m_ver.group(2)}"
                    else:
                        ext_data["djc_id"] = f"{base_id}-{soc_codigo}"
                    ext_data["_ext_company_name"] = company_name  # para el subfolder
                    
                    # Bucle de versiones por cada empresa (normal y/o codificada)
                    import copy as _copy
                    gen_normal_ch  = getattr(self, '_djc_version_normal_var', None)
                    gen_cod_ch     = getattr(self, '_djc_version_cod_var', None)
                    want_normal_x  = gen_normal_ch  is None or gen_normal_ch.get()
                    want_cod_x     = gen_cod_ch is not None and gen_cod_ch.get()
                    
                    if want_normal_x:
                        result_n = self._generate_single_djc(
                            _copy.copy(ext_data), colors,
                            extra_pdfs=[nota_path] if nota_path else None)
                        if result_n:
                            generated_files.append(result_n)
                    
                    if want_cod_x:
                        ext_cod = _copy.copy(ext_data)
                        ct_ext = self._build_censor_terms(ext_cod)
                        result_c = self._generate_single_djc(
                            ext_cod, colors,
                            extra_pdfs=[nota_path] if nota_path else None,
                            censor_terms=ct_ext)
                        if result_c:
                            generated_files.append(result_c)
                    
                    self.logger.info(f"[M3] ✓ Extensión {company_name} completada")
                
                self._handle_preview_and_save(generated_files, colors)
            else:
                # Modo Común: generar versión Normal y/o Codificada según seleccion
                gen_normal    = getattr(self, '_djc_version_normal_var', None)
                gen_codificada = getattr(self, '_djc_version_cod_var', None)
                want_normal   = gen_normal    is None or gen_normal.get()
                want_cod      = gen_codificada is not None and gen_codificada.get()
                
                all_results = []
                
                if want_normal:
                    result_n = self._generate_single_djc(dict(data), colors)
                    if result_n:
                        all_results.append(result_n)
                
                if want_cod:
                    cod_data = dict(data)
                    censor_terms = self._build_censor_terms(cod_data)  # modifica cod_data in-place
                    result_c = self._generate_single_djc(cod_data, colors, censor_terms=censor_terms)
                    if result_c:
                        all_results.append(result_c)
                
                if all_results:
                    self._handle_preview_and_save(all_results, colors)
                else:
                    self.djc_status.configure(
                        text="Seleccioná al menos una versión (Normal o Codificada).",
                        text_color=colors["warning"]
                    )
            
        except Exception as e:
            self.logger.error(f"Error generando DJC: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.djc_status.configure(
                text=f"Error: {str(e)}",
                text_color=colors["error"]
            )
    
    def _build_censor_terms(self, data: dict) -> dict:
        """
        En modo codificado: sobreescribe fabricante/direccion en el dict con el
        texto de resguardo y devuelve un dict con los valores originales para censurarlos
        en el PDF del certificado.
        """
        import re as _re
        fab_orig: str = str(data.get("fabricante", "") or "")
        dir_orig: str = str(data.get("direccion_fabrica", "") or "")
        
        # Detectar país: buscar uno de los países en la dirección original
        paises_conocidos = ["China", "Korea", "Taiwan", "Vietnam", "India", "Japón", "Japan", "USA"]
        pais_detectado = ""
        for pais in paises_conocidos:
            if pais.lower() in dir_orig.lower() or pais.lower() in fab_orig.lower():
                pais_detectado = pais
                break
        
        if pais_detectado:
            texto_res = f"Información Restringida - Res. SIyC 237/2024 ({pais_detectado})"
        else:
            texto_res = "Información Restringida - Res. SIyC 237/2024"
        
        # Sobreescribir en el data ORIGINAL (que ya es una copia en _execute_djc_generation)
        data["fabricante"]        = texto_res
        data["direccion_fabrica"] = texto_res
        
        self.logger.info(f"[M3] DJC Codificada — Fabricante original: '{fab_orig[:40]}...'")
        self.logger.info(f"[M3] DJC Codificada — Texto de resguardo: '{texto_res}'")
        
        return {"fabricante": fab_orig, "direccion": dir_orig}

    def _generate_single_djc(self, data, colors, extra_pdfs=None, censor_terms=None):
        """
        Pipeline de generación de una única DJC en carpeta TEMPORAL.
        Retorna un dict con las rutas temporales y la info de destino final.
        """
        import re as _re
        import tempfile
        import time as _time
        
        # 1. Llenar template
        self.djc_status.configure(text="Llenando plantilla Word...", text_color=colors["text_secondary"])
        self.update_idletasks()
        
        doc = self.djc_gen.fill_template(data)
        
        # 2. Determinar rutas
        djc_id_raw = data.get("djc_id", "").strip()
        file_stem = _re.sub(r'[\\/:*?"<>|]', "-", djc_id_raw) or "DJC-SIN-ID"
        
        # Extraer Bidcom
        parts = file_stem.split("-")
        bidcom_folder = parts[3] if len(parts) >= 4 else (parts[-1] if parts else "SIN-NUMERO")
        
        # Carpeta FINAL (destino)
        base_dir = os.path.join(os.path.expanduser("~"), "Documents", "DJC generadas", bidcom_folder)
        company_name = data.get("_ext_company_name")
        if company_name:
            safe_company = _re.sub(r'[\\/:*?"<>|]', "-", company_name)
            final_docs_dir = os.path.join(base_dir, "Extensiones", safe_company)
        else:
            final_docs_dir = base_dir
            
        # Carpeta TEMPORAL
        tmp_dir = os.path.join(tempfile.gettempdir(), "argos_djc_preview")
        os.makedirs(tmp_dir, exist_ok=True)
        
        # Archivos intermedios en TEMP
        tmp_stem = f"{file_stem}_djc"
        docx_path = os.path.join(tmp_dir, f"{tmp_stem}.docx")
        if os.path.exists(docx_path):
            counter = 2
            while os.path.exists(os.path.join(tmp_dir, f"{tmp_stem}_{counter}.docx")):
                counter += 1
            docx_path = os.path.join(tmp_dir, f"{tmp_stem}_{counter}.docx")
        
        # El ID en el Word = nombre declarado
        self.djc_gen._set_cell_id(doc.tables[0], 1, 0, file_stem)
        
        self.djc_gen.save_docx(doc, docx_path)
        self.logger.info(f"[M3] DJC Word guardada en temp: {docx_path}")
        
        # 3. Exportar a PDF (en TEMP)
        self.djc_status.configure(text="Convirtiendo a PDF...", text_color=colors["text_secondary"])
        self.update_idletasks()
        
        try:
            raw_pdf_path = self.djc_gen.export_to_pdf(docx_path)
            
            # 4. Merge → PDF final en TEMP
            if self.certificate_paths:
                self.djc_status.configure(text="Combinando con certificado...", text_color=colors["text_secondary"])
                self.update_idletasks()
                
                tmp_final_pdf = os.path.join(tmp_dir, f"{file_stem}.pdf")
                if os.path.exists(tmp_final_pdf):
                    ts = int(_time.time())
                    tmp_final_pdf = os.path.join(tmp_dir, f"{file_stem}_{ts}.pdf")
                
                cert_to_merge = self.certificate_paths[0]
                
                # Si es DJC codificada, censurar el certificado primero
                if censor_terms:
                    try:
                        import fitz as _fitz
                        cert_doc = _fitz.open(self.certificate_paths[0])
                        cert_doc = self.djc_gen.censor_cert_pdf(
                            cert_doc,
                            fabricante=censor_terms.get("fabricante", ""),
                            direccion=censor_terms.get("direccion", ""),
                        )
                        censored_cert_path = os.path.join(tmp_dir, f"{file_stem}_cert_cod.pdf")
                        cert_doc.save(censored_cert_path)
                        cert_doc.close()
                        cert_to_merge = censored_cert_path
                        self.logger.info(f"[M3] Certificado censurado guardado en: {censored_cert_path}")
                    except Exception as e:
                        self.logger.warning(f"[M3] Error al censurar certificado: {e}. Usando original.")
                
                merged_path = self.djc_gen.merge_pdfs(
                    raw_pdf_path, cert_to_merge,
                    output_path=tmp_final_pdf,
                    extra_pdfs=extra_pdfs
                )
                self.logger.info(f"[M3] ✓ PDF borrador listo: {merged_path}")
                
                return {
                    "tmp_pdf": merged_path,
                    "final_dir": final_docs_dir,
                    "final_filename": f"{file_stem}.pdf"
                }
            else:
                return {
                    "tmp_pdf": raw_pdf_path,
                    "final_dir": final_docs_dir,
                    "final_filename": f"{file_stem}.pdf"
                }
        except ImportError:
            self.djc_status.configure(text="Error de conversion PDF, revisar consola", text_color=colors["error"])
            return None

    def _handle_preview_and_save(self, generated_files, colors):
        """Abre los PDFs generados en el visor y programa la consulta al usuario de forma segura."""
        if not generated_files:
            return
            
        import os
        # Abrir los PDFs generados para preview
        for res in generated_files:
            try:
                if hasattr(os, 'startfile'):
                    getattr(os, 'startfile')(res["tmp_pdf"])
            except Exception as e:
                self.logger.warning(f"No se pudo abrir el PDF borrador: {e}")
        
        self.djc_status.configure(
            text="Abriendo PDF(s) borrador... Esperando confirmación.", 
            text_color=colors["warning"]
        )
        
        # Diferir la apertura del messagebox usando el mainloop de Tkinter
        # Esto previene el crash Fatal Python Error PyEval_RestoreThread asociado al GIL
        self.after(500, lambda: self._show_preview_prompt(generated_files, colors))

    def _show_preview_prompt(self, generated_files, colors):
        """Muestra el diálogo de confirmación y mueve los archivos al destino final."""
        import tkinter.messagebox as messagebox
        import shutil
        import os
        
        # Armar mensaje
        msg = f"Se han abierto {len(generated_files)} PDF(s) en tu visor predeterminado para que los revises.\n\n¿Están correctos y deseás guardarlos definitivamente?\n(Si elegís NO, se descartarán para que puedas corregir)."
        if len(generated_files) == 1:
            msg = "El PDF borrador de la DJC se abrió en tu visor.\n\n¿Está correcto y deseás guardarlo definitivamente?\n(Si elegís NO, se descartará)."
            
        confirm = messagebox.askyesno("Confirmar DJC", msg, parent=self)
        
        if confirm:
            saved_paths = []
            for res in generated_files:
                os.makedirs(res["final_dir"], exist_ok=True)
                final_path = os.path.join(res["final_dir"], res["final_filename"])
                
                if os.path.exists(final_path):
                    import time
                    stem, ext = os.path.splitext(res["final_filename"])
                    final_path = os.path.join(res["final_dir"], f"{stem}_{int(time.time())}{ext}")
                
                shutil.copy2(res["tmp_pdf"], final_path)
                self.logger.info(f"[M3] Guardado final (solo PDF final): {final_path}")
                saved_paths.append(final_path)
                
            self.djc_status.configure(
                text=f"✓ {len(saved_paths)} DJC(s) guardada(s) exitosamente", 
                text_color=colors["success"]
            )
            self.logger.info(f"[M3] === GENERACIÓN FINALIZADA Y GUARDADA ===")
        else:
            self.djc_status.configure(
                text="Generación descartada por el usuario. Podés editar y reintentar.", 
                text_color=colors["warning"]
            )
            self.logger.info("[M3] El usuario descartó las DJC generadas temporalmente.")
    
    def cycle_theme(self):
        """Cicla entre temas"""
        new_theme = self.theme_manager.cycle_theme()
        self.logger.info(f"Tema cambiado a: {new_theme}")
        
        # Actualizar texto del botón
        colors = self.theme_manager.get_current_colors()
        
        # Recargar interfaz
        self.setup_theme()
        self.refresh_widgets()
    
    def refresh_widgets(self):
        """Recarga los colores de todos los widgets"""
        # Destruir y recrear widgets para aplicar nuevo tema
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()
    
    def toggle_debug(self):
        """Muestra/oculta panel de debug"""
        if self.debug_panel is None or not self.debug_panel.winfo_exists():
            self.show_debug_panel()
        else:
            self.debug_panel.destroy()
            self.debug_panel = None
    
    def show_debug_panel(self):
        """Muestra el panel de debug"""
        import tkinter as tk
        colors = self.theme_manager.get_current_colors()
        
        # Ventana toplevel estándar (no CTk para evitar conflictos)
        self.debug_panel = tk.Toplevel(self)
        self.debug_panel.title("🐛 Debug Console - Argos")
        self.debug_panel.geometry("700x500")
        self.debug_panel.configure(bg=colors["bg_primary"])
        
        # Frame principal
        self.main_frame = tk.Frame(self.debug_panel, bg=colors["bg_primary"])
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Text area para logs con scrollbar
        text_frame = tk.Frame(self.main_frame, bg=colors["bg_secondary"])
        text_frame.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        log_text = tk.Text(
            text_frame,
            font=("Courier New", 10),
            bg=colors["bg_secondary"],
            fg=colors["text_primary"],
            insertbackground=colors["text_primary"],
            yscrollcommand=scrollbar.set
        )
        log_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=log_text.yview)
        
        # Insertar logs
        for msg in self.logger.get_gui_messages():
            log_text.insert("end", msg + "\n")
        log_text.see("end")  # Scroll al final
        
        # Botones con CTk
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Guardar Log",
            command=self.save_log,
            fg_color=colors["accent_primary"],
            width=120
        )
        save_btn.pack(side="left", padx=5)
        
        copy_btn = ctk.CTkButton(
            btn_frame,
            text="📋 Copiar",
            command=lambda: [self.clipboard_clear(), self.clipboard_append(log_text.get("1.0", "end")), self.update()], # Update necesari en Windows
            fg_color=colors["success"],
            width=120
        )
        copy_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ Limpiar",
            command=lambda: [self.logger.clear_gui(), log_text.delete("1.0", "end")],
            fg_color=colors["error"],
            width=120
        )
        clear_btn.pack(side="left", padx=5)
        
        close_btn = ctk.CTkButton(
            btn_frame,
            text="✖ Cerrar",
            command=self.debug_panel.destroy,
            fg_color=colors["bg_tertiary"],
            width=120
        )
        close_btn.pack(side="right", padx=5)
    
    def save_log(self):
        """Exporta el log a archivo"""
        log_path = self.logger.export_log()
        self.logger.info(f"Log guardado en: {log_path}")

    # ────────────────────────────────────────────────────────────────
    #  Tab Navigation
    # ────────────────────────────────────────────────────────────────

    def switch_tab(self, tab_id):
        """Cambia entre tabs del sistema Argos"""
        self.logger.info(f"Cambiando a tab:  {tab_id}")
        self.current_tab = tab_id
        
        # Actualizar estética de botones
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(fg_color="#333333", text_color="#00ff41", font=("Roboto", 11, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color="#888888", font=("Roboto", 11, "normal"))
        
        # Limpiar contenido actual
        for widget in self.content_container.winfo_children():
            widget.destroy()
        
        # Mostrar contenido del tab
        if tab_id == "solicitud":
            self.show_solicitud_tab()
        elif tab_id == "verificador":
            self.show_verificador_tab()
        elif tab_id == "generador":
            self.show_generador_tab()

    def show_solicitud_tab(self):
        """Tab Solicitud - En mantenimiento"""
        colors = self.theme_manager.get_current_colors()
        tab_frame = ctk.CTkFrame(self.content_container, fg_color=colors["bg_primary"])
        tab_frame.pack(fill="both", expand=True, padx=50, pady=50)
        
        icon_label = ctk.CTkLabel(tab_frame, text="\u25c9\u25c9\u25c9\n\n\u25c9  \u25c9\n\n\u25c9\u25c9\u25c9", font=("Roboto", 48), text_color="#555555")
        icon_label.pack(pady=(30, 20))
        
        title_label = ctk.CTkLabel(tab_frame, text="MÓDULO EN MANTENIMIENTO", font=("Roboto", 20, "bold"), text_color=colors["text_primary"])
        title_label.pack(pady=10)
        
        desc_label = ctk.CTkLabel(tab_frame, text="El módulo de Solicitud estará disponible próximamente.\n\nPor ahora, puedes usar el Verificador o el Generador DJC.", font=("Roboto", 12), text_color=colors["text_secondary"], justify="center")
        desc_label.pack(pady=10)

    def show_verificador_tab(self):
        """Tab Verificador - Flujo actual (datasheet + certs + auditoría)"""
        colors = self.theme_manager.get_current_colors()
        
        # Crear main_frame para compatibilidad con código existente
        self.main_frame = ctk.CTkFrame(self.content_container, fg_color=colors["bg_primary"], corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # PASO 1: DATASHEET
        step1_frame = ctk.CTkFrame(self.main_frame, fg_color=colors["bg_secondary"], corner_radius=0)
        step1_frame.pack(fill="x", pady=(8, 5), padx=20)
        
        step1_label = ctk.CTkLabel(
            step1_frame,
            text="PASO 1: DATASHEET",
            font=("Courier New" if self.theme_manager.get_theme_name() == "Matrix" else "Segoe UI", 14, "bold"),
            text_color=colors["text_primary"]
        )
        step1_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Entry para link
        self.link_entry = ctk.CTkEntry(
            step1_frame,
            placeholder_text="🔗 Link del datasheet (Google Drive)...",
            height=34,
            font=("Segoe UI", 11),
            fg_color=colors["bg_tertiary"],
            border_color=colors["border"]
        )
        self.link_entry.pack(fill="x", padx=15, pady=(0, 6))
        
        load_btn = ctk.CTkButton(
            step1_frame,
            text="📥 Cargar desde Link",
            command=self.load_from_link,
            fg_color=colors["accent_primary"],
            hover_color=colors["bg_tertiary"]
        )
        load_btn.pack(padx=15, pady=(0, 6))
        
        # Drag & Drop Area para Datasheet
        self.drop_datasheet = ctk.CTkFrame(
            step1_frame,
            fg_color=colors["bg_tertiary"],
            border_width=2,
            border_color=colors["border"],
            corner_radius=0,
            height=45
        )
        self.drop_datasheet.pack(fill="x", padx=15, pady=(3, 5))
        
        drop_label = ctk.CTkLabel(
            self.drop_datasheet,
            text="─── O ARRASTRA ARCHIVO AQUÍ ───\n💾 .xlsx",
            font=("Courier New" if self.theme_manager.get_theme_name() == "Matrix" else "Segoe UI", 12),
            text_color=colors["text_secondary"]
        )
        drop_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Habilitar drag and drop
        self.drop_datasheet.drop_target_register(DND_FILES)
        self.drop_datasheet.dnd_bind('<<Drop>>', self.on_drop_datasheet)
        
        # Status datasheet
        self.datasheet_status_frame = ctk.CTkFrame(
            step1_frame,
            fg_color="transparent",
            height=20
        )
        self.datasheet_status_frame.pack(fill="x", padx=15, pady=(0, 3))
        
        self.datasheet_status = ctk.CTkLabel(
            self.datasheet_status_frame,
            text="Sin archivo cargado",
            font=("Segoe UI", 11),
            text_color=colors["text_secondary"]
        )
        self.datasheet_status.pack(pady=2)
        
        # PASO 2: CERTIFICADOS
        step2_frame = ctk.CTkFrame(self.main_frame, fg_color=colors["bg_secondary"], corner_radius=0)
        step2_frame.pack(fill="x", pady=(0, 5), padx=20)
        
        step2_label = ctk.CTkLabel(
            step2_frame,
            text="PASO 2: CERTIFICADOS",
            font=("Courier New" if self.theme_manager.get_theme_name() == "Matrix" else "Segoe UI", 14, "bold"),
            text_color=colors["text_primary"]
        )
        step2_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Drag & Drop Area para Certificados
        self.drop_certs = ctk.CTkFrame(
            step2_frame,
            fg_color=colors["bg_tertiary"],
            border_width=2,
            border_color=colors["border"],
            corner_radius=0,
            height=50
        )
        self.drop_certs.pack(fill="x", padx=15, pady=(3, 5))
        
        drop_certs_label = ctk.CTkLabel(
            self.drop_certs,
            text="─── ARRASTRA PDFs AQUÍ ───\n📄 Puedes arrastrar múltiples archivos",
            font=("Courier New" if self.theme_manager.get_theme_name() == "Matrix" else "Segoe UI", 12),
            text_color=colors["text_secondary"]
        )
        drop_certs_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Habilitar drag and drop
        self.drop_certs.drop_target_register(DND_FILES)
        self.drop_certs.dnd_bind('<<Drop>>', self.on_drop_certificates)
        
        # Lista de certificados cargados
        self.certs_list_frame = ctk.CTkScrollableFrame(
            step2_frame,
            fg_color="transparent",
            height=30
        )
        self.certs_list_frame.pack(fill="x", padx=15, pady=(0, 3))
        
        # Status certificados
        self.certs_status_frame = ctk.CTkFrame(
            step2_frame,
            fg_color="transparent",
            height=18
        )
        self.certs_status_frame.pack(fill="x", padx=15, pady=(0, 5))
        
        self.certs_status = ctk.CTkLabel(
            self.certs_status_frame,
            text="Sin certificados cargados",
            font=("Segoe UI", 11),
            text_color=colors["text_secondary"]
        )
        self.certs_status.pack(pady=2)
        
        # BOTÓN AUDITORÍA
        self.audit_btn = ctk.CTkButton(
            self.main_frame,
            text="▶️ INICIAR AUDITORÍA",
            font=("Segoe UI", 16, "bold"),
            height=44,
            command=self.start_audit,
            fg_color=colors["success"],
            hover_color=colors["accent_primary"],
            state="disabled"
        )
        self.audit_btn.pack(fill="x", pady=(0, 10), padx=20)

    def show_generador_tab(self):
        """Tab Generador DJC - Flujo directo (cert PDF -> DJC)"""
        colors = self.theme_manager.get_current_colors()
        tab_frame = ctk.CTkFrame(self.content_container, fg_color=colors["bg_primary"])
        tab_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # ═══════════════════════════════════════════════════════════
        # TÍTULO
        # ═══════════════════════════════════════════════════════════
        title_frame = ctk.CTkFrame(tab_frame, fg_color=colors["bg_secondary"], corner_radius=0)
        title_frame.pack(fill="x", pady=(8, 5), padx=20)
        
        title_label = ctk.CTkLabel(title_frame, text="◉◉◉ GENERADOR DE DJC", font=("Roboto", 18, "bold"), text_color=colors["text_primary"])
        title_label.pack(anchor="w", padx=15, pady=8)
        
        inst_label = ctk.CTkLabel(title_frame, text="Genera una Declaración Jurada de Conformidad directamente desde un certificado PDF.", font=("Roboto", 11), text_color=colors["text_secondary"])
        inst_label.pack(anchor="w", padx=15, pady=(0, 8))
        
        # ═══════════════════════════════════════════════════════════
        # NÚMERO DE BIDCOM (fila compacta)
        # ═══════════════════════════════════════════════════════════
        bidcom_frame = ctk.CTkFrame(tab_frame, fg_color=colors["bg_secondary"], corner_radius=0)
        bidcom_frame.pack(fill="x", pady=(0, 5), padx=20)
        
        ctk.CTkLabel(bidcom_frame, text="Nro. Bidcom:", font=("Roboto", 11, "bold"),
                     text_color=colors["text_primary"]).pack(side="left", padx=(15, 8), pady=6)
        
        ctk.CTkLabel(bidcom_frame, text="C", font=("Roboto", 12, "bold"),
                     text_color=colors["accent_primary"]).pack(side="left", pady=6)
        
        self._bidcom_entry = ctk.CTkEntry(
            bidcom_frame, font=("Roboto", 11), height=30, width=120,
            fg_color=colors["bg_tertiary"], text_color=colors["text_primary"],
            border_color=colors["accent_primary"], border_width=1,
            placeholder_text="912"
        )
        self._bidcom_entry.pack(side="left", pady=6)
        
        ctk.CTkLabel(bidcom_frame, text="(editable en el formulario)",
                     font=("Roboto", 9), text_color=colors["text_secondary"]).pack(side="left", padx=(6, 0), pady=6)
        
        # ═══════════════════════════════════════════════════════════
        # SELECTOR DE MODO: Común / Extensión / Codificada
        # ═══════════════════════════════════════════════════════════
        mode_frame = ctk.CTkFrame(tab_frame, fg_color=colors["bg_secondary"], corner_radius=0)
        mode_frame.pack(fill="x", pady=(0, 5), padx=20)
        
        mode_label = ctk.CTkLabel(mode_frame, text="TIPO DE DJC", font=("Roboto", 11, "bold"), text_color=colors["text_secondary"])
        mode_label.pack(anchor="w", padx=15, pady=(8, 4))
        
        mode_btns_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        mode_btns_frame.pack(fill="x", padx=15, pady=(0, 8))
        mode_btns_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="mode_cols")
        
        self._djc_mode = "comun"  # Default
        self._mode_buttons = {}
        
        def _set_mode(mode_id):
            self._djc_mode = mode_id
            # Update button visual states
            for mid, btn in self._mode_buttons.items():
                if mid == mode_id:
                    btn.configure(fg_color=colors["accent_primary"], text_color="#FFFFFF")
                else:
                    btn.configure(fg_color=colors["bg_tertiary"], text_color=colors["text_primary"])
            # Show/hide extension panel
            if mode_id == "extension":
                self._ext_panel.pack(fill="x", pady=5, padx=20, after=mode_frame)
            else:
                self._ext_panel.pack_forget()
        
        modes = [
            ("comun",     "📋 DJC Común"),
            ("extension", "🔗 Extensión"),
            ("codificada","🔒 Codificada"),
        ]
        for i, (mid, mlabel) in enumerate(modes):
            btn = ctk.CTkButton(
                mode_btns_frame, text=mlabel, font=("Roboto", 12, "bold"),
                height=36, corner_radius=4,
                fg_color=colors["accent_primary"] if mid == "comun" else colors["bg_tertiary"],
                text_color="#FFFFFF" if mid == "comun" else colors["text_primary"],
                hover_color=colors["accent_secondary"],
                command=lambda m=mid: _set_mode(m)
            )
            btn.grid(row=0, column=i, padx=3, sticky="ew")
            self._mode_buttons[mid] = btn
        
        # ═══════════════════════════════════════════════════════════
        # PANEL DE EXTENSIONES (oculto por defecto)
        # ═══════════════════════════════════════════════════════════
        self._ext_panel = ctk.CTkFrame(tab_frame, fg_color=colors["bg_secondary"], corner_radius=0)
        # No se empaqueta hasta que se seleccione el modo "extension"
        
        ext_title = ctk.CTkLabel(self._ext_panel, text="SOCIEDADES A EXTENDER", font=("Roboto", 11, "bold"), text_color=colors["text_secondary"])
        ext_title.pack(anchor="w", padx=15, pady=(8, 4))
        
        ext_hint = ctk.CTkLabel(self._ext_panel, text="Seleccioná las empresas para las que querés generar DJC extendidas.", font=("Roboto", 10), text_color=colors["text_secondary"])
        ext_hint.pack(anchor="w", padx=15, pady=(0, 6))
        
        # Toggle buttons grid (4 columns x 2 rows)
        ext_grid = ctk.CTkFrame(self._ext_panel, fg_color="transparent")
        ext_grid.pack(fill="x", padx=15, pady=(0, 6))
        ext_grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="ext_cols")
        
        # Load sociedades from config
        from modules.m3_djc_generator import DJCGenerator
        _temp_gen = DJCGenerator(gui_logger=self.logger)
        sociedades = _temp_gen.config.get("sociedades_extension", {})
        
        self._ext_selected = {}  # {"Bemotec S.R.L.": True/False, ...}
        self._ext_toggle_btns = {}
        
        company_names = list(sociedades.keys()) + ["Libre / Otra"]
        
        def _toggle_ext(name):
            current = self._ext_selected.get(name, False)
            self._ext_selected[name] = not current
            btn = self._ext_toggle_btns[name]
            if self._ext_selected[name]:
                btn.configure(fg_color=colors["accent_primary"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color=colors["bg_tertiary"], text_color=colors["text_primary"])
        
        for idx, name in enumerate(company_names):
            row = idx // 4
            col = idx % 4
            short_name = name.split(" S.R.L.")[0] if "S.R.L." in name else name
            btn = ctk.CTkButton(
                ext_grid, text=short_name, font=("Roboto", 10, "bold"),
                height=32, corner_radius=4,
                fg_color=colors["bg_tertiary"],
                text_color=colors["text_primary"],
                hover_color=colors["accent_secondary"],
                command=lambda n=name: _toggle_ext(n)
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            self._ext_selected[name] = False
            self._ext_toggle_btns[name] = btn
        
        # Nota de extensión PDF upload
        nota_frame = ctk.CTkFrame(self._ext_panel, fg_color="transparent")
        nota_frame.pack(fill="x", padx=15, pady=(4, 8))
        
        self._nota_ext_path = None
        
        def _on_drop_nota(event):
            file_path = event.data.strip('{}')
            if file_path.lower().endswith('.pdf'):
                self._nota_ext_path = file_path
                nota_label.configure(text=f"✓ {os.path.basename(file_path)}", text_color=colors["success"])
                self.logger.info(f"Nota de extensión cargada: {os.path.basename(file_path)}")
            else:
                self.logger.error("Solo se aceptan archivos PDF para la nota de extensión")
        
        nota_drop = ctk.CTkFrame(nota_frame, fg_color=colors["bg_tertiary"], border_width=2, border_color=colors["border"], corner_radius=0, height=52)
        nota_drop.pack(fill="x")
        nota_drop.pack_propagate(False)
        
        nota_drop_label = ctk.CTkLabel(nota_drop, text="📄 Arrastrar Nota de Extensión (PDF) aquí", font=("Roboto", 11), text_color=colors["text_secondary"])
        nota_drop_label.pack(expand=True)
        
        nota_drop.drop_target_register(DND_FILES)
        nota_drop.dnd_bind('<<Drop>>', _on_drop_nota)
        
        nota_label = ctk.CTkLabel(nota_frame, text="", font=("Roboto", 10), text_color=colors["accent_primary"])
        nota_label.pack(anchor="w", pady=(2, 0))
        
        # ═══════════════════════════════════════════════════════════
        # CERTIFICADO PDF (compartido por los 3 modos)
        # ═══════════════════════════════════════════════════════════
        cert_frame = ctk.CTkFrame(tab_frame, fg_color=colors["bg_secondary"], corner_radius=0)
        cert_frame.pack(fill="x", pady=5, padx=20)
        
        cert_label = ctk.CTkLabel(cert_frame, text="CERTIFICADO PDF", font=("Roboto", 12, "bold"), text_color=colors["text_primary"])
        cert_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.drop_cert_direct = ctk.CTkFrame(cert_frame, fg_color=colors["bg_tertiary"], border_width=2, border_color=colors["border"], corner_radius=0, height=75)
        self.drop_cert_direct.pack(fill="x", padx=15, pady=(3, 8))
        self.drop_cert_direct.pack_propagate(False)
        
        drop_label = ctk.CTkLabel(self.drop_cert_direct, text="📄 Arrastrar certificado aquí", font=("Roboto", 12), text_color=colors["text_secondary"])
        drop_label.pack(expand=True)
        
        self.drop_cert_direct.drop_target_register(DND_FILES)
        self.drop_cert_direct.dnd_bind('<<Drop>>', self.on_drop_cert_direct)
        
        self.cert_direct_label = ctk.CTkLabel(cert_frame, text="", font=("Roboto", 10), text_color=colors["accent_primary"])
        self.cert_direct_label.pack(padx=15, pady=(0, 8))
        
        # Botón generar
        self.gen_djc_btn = ctk.CTkButton(tab_frame, text="◉◉◉ GENERAR DJC", font=("Roboto", 13, "bold"), height=44, fg_color=colors["accent_primary"], hover_color=colors["bg_tertiary"], state="disabled", command=self.generate_djc_direct)
        self.gen_djc_btn.pack(pady=10, padx=20, fill="x")

    def on_drop_cert_direct(self, event):
        """Maneja drop de certificado en tab Generador"""
        file_path = event.data.strip('{}')
        if file_path.lower().endswith('.pdf'):
            self.cert_direct_path = file_path
            filename = os.path.basename(file_path)
            self.cert_direct_label.configure(text=f"OK {filename}")
            self.gen_djc_btn.configure(state="normal")
            self.logger.info(f"Certificado cargado: {filename}")
        else:
            self.logger.error("Solo se aceptan archivos PDF")

    def generate_djc_direct(self):
        """Genera DJC directamente desde certificado (sin auditar)"""
        self.logger.info("=== GENERANDO DJC DIRECTO ===")
        self.logger.info(f"[M3] Modo: {getattr(self, '_djc_mode', 'comun')}")
        self.logger.info(f"[M3] Archivo: {os.path.basename(self.cert_direct_path)}")
        
        # Validaciones por modo
        mode = getattr(self, "_djc_mode", "comun")
        
        if mode == "extension":
            selected = [k for k, v in getattr(self, "_ext_selected", {}).items() if v]
            if not selected:
                self.logger.error("[M3] Seleccioná al menos una sociedad para extender")
                return
            nota_path = getattr(self, "_nota_ext_path", None)
            if not nota_path:
                self.logger.error("[M3] Cargá la Nota de Extensión (PDF) antes de generar")
                return
            self.logger.info(f"[M3] Extensiones seleccionadas: {', '.join(selected)}")
        
        try:
            from modules.m3_djc_generator import DJCGenerator
            
            self.logger.info("[M3] Inicializando DJCGenerator...")
            gen = DJCGenerator(gui_logger=self.logger)
            
            self.logger.info("[M3] Extrayendo texto del PDF...")
            cert_data = gen.extract_cert_data(self.cert_direct_path)
            
            self.logger.info(f"[M3] ── Nro. Certificado : {cert_data.get('cert_number') or '[no encontrado]'}")
            self.logger.info(f"[M3] ── OEC detectado   : {cert_data.get('oec_key') or '[desconocido]'}")
            self.logger.info(f"[M3] ── Normas          : {cert_data.get('normas') or '[ninguna]'}")
            self.logger.info(f"[M3] ── Fecha emisión   : {cert_data.get('fecha_emision') or '[no encontrada]'}")
            self.logger.info(f"[M3] ── Fecha venc.     : {cert_data.get('fecha_vencimiento') or '[no encontrada]'}")
            
            reglamento = gen.detect_reglamento(cert_data.get("normas", ""))
            self.logger.info(f"[M3] ── Reglamento      : {reglamento or '[no detectado]'}")
            
            self.logger.info("[M3] Extrayendo datos del producto...")
            text = cert_data.get("cert_text", "")
            text_sorted = cert_data.get("cert_text_sorted", "")
            product = gen.extract_product_data_from_cert(text, text_sorted)
            
            self.logger.info(f"[M3] ── Marca           : {product.get('marca') or '[vacía]'}")
            self.logger.info(f"[M3] ── Fabricante      : {(product.get('fabricante') or '[vacío]')[:60]}")
            self.logger.info(f"[M3] ── Producto desc   : {product.get('producto_desc') or '[vacío]'}")
            modelos_preview = (product.get('modelos') or '[vacíos]')[:80]
            self.logger.info(f"[M3] ── Modelos         : {modelos_preview}")
            self.logger.info(f"[M3] ── Specs           : {product.get('specs') or '[vacías]'}")
            self.logger.info(f"[M3] ── Fecha emisión   : {product.get('fecha_emision') or '[no extraída]'}")
            self.logger.info(f"[M3] ── Fecha venc.     : {product.get('fecha_vencimiento') or '[no extraída]'}")
            
            self.logger.info("[M3] Armando datos finales DJC...")
            djc_data = gen.prepare_from_certificate(self.cert_direct_path)
            
            # ── Usar Nro. Bidcom del campo GUI si el usuario lo ingresó ──
            bidcom_manual = getattr(self, "_bidcom_entry", None)
            if bidcom_manual:
                bidcom_val = bidcom_manual.get().strip()
                if bidcom_val:
                    # Siempre anteponer 'C' si el usuario solo puso el número
                    if not bidcom_val.upper().startswith('C'):
                        bidcom_val = f"C{bidcom_val}"
                    djc_data["bidcom_number"] = bidcom_val
                    # Regenerar el djc_id con el Bidcom correcto
                    djc_data["djc_id"] = gen.generate_djc_id(
                        reglamento=djc_data.get("reglamento", ""),
                        oec_nombre=djc_data.get("oec_key", "") or djc_data.get("oec_nombre", ""),
                        bidcom_num=bidcom_val
                    )
                    # Actualizar enlace_djc: usar el nro numerico (sin la C)
                    num_bidcom = bidcom_val.lstrip("Cc") or bidcom_val
                    base_url = gen.config.get("enlace_djc_base", "https://qr.gadnic.com/certifications/certificado-")
                    djc_data["enlace_djc"] = f"{base_url}{num_bidcom}"
                    self.logger.info(f"[M3] Bidcom manual: '{bidcom_val}' → ID: {djc_data['djc_id']}")
            
            # ── Modo Codificada: sobreescribir fabricante/dirección ──
            if mode == "codificada":
                # Intentar extraer el país de la dirección original
                dir_orig = djc_data.get("direccion_fabrica", "")
                pais = "China"  # Default
                for pais_candidate in ["China", "Vietnam", "India", "Indonesia", "Taiwan", "Korea", "Japan", "Thailand", "Malaysia", "Bangladesh"]:
                    if pais_candidate.lower() in dir_orig.lower():
                        pais = pais_candidate
                        break
                texto_restringido = f"Información Restringida de acuerdo con Res. SIyC 237/2024 - {pais}"
                djc_data["fabricante"] = texto_restringido
                djc_data["direccion_fabrica"] = texto_restringido
                self.logger.info(f"[M3] Modo CODIFICADA: Fabricante/Dirección → '{texto_restringido}'")
            
            self.logger.info("[M3] ✓ Datos listos — abriendo formulario DJC")
            
            # Pre-cargar datos para que show_djc_view los use
            self.djc_data = djc_data
            self.djc_gen = gen
            self._djc_source = "direct"
            
            # Asegurar que certificate_paths tiene el cert para la generación
            if not hasattr(self, 'certificate_paths'):
                self.certificate_paths = []
            self.certificate_paths = [self.cert_direct_path]
            
            # Guardar estado de modo para _execute_djc_generation
            self._djc_gen_mode = mode
            if mode == "extension":
                self._djc_ext_companies = [k for k, v in self._ext_selected.items() if v]
                self._djc_ext_nota_path = self._nota_ext_path
            
            self.show_djc_view()
            
        except Exception as e:
            self.logger.error(f"[M3] Error al generar DJC: {e}")
            import traceback
            self.logger.error(traceback.format_exc())


def main():
    """Punto de entrada de la aplicación"""
    app = ArgosApp()
    app.mainloop()


if __name__ == "__main__":
    main()
