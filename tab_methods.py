"""
Métodos de navegación por tabs para argos_main.py
Añadir estos métodos a la clase ArgosApp
"""
import customtkinter as ctk
import os
from tkinterdnd2 import DND_FILES

def switch_tab(self, tab_id):
    """Cambia entre tabs del sistema Argos"""
    self.logger.info(f"Cambiando a tab: {tab_id}")
    self.current_tab = tab_id
    
    # Actualizar est\u00e9tica de botones
    for tid, btn in self.tab_buttons.items():
        if tid == tab_id:
            btn.configure(
                fg_color="#333333",
                text_color="#00ff41",
                font=("Roboto", 11, "bold")
            )
        else:
            btn.configure(
                fg_color="transparent",
                text_color="#888888",
                font=("Roboto", 11, "normal")
            )
    
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
    """Muestra tab de Solicitud (en mantenimiento)"""
    colors = self.theme_manager.get_current_colors()
    
    # Frame principal del tab
    tab_frame = ctk.CTkFrame(self.content_container, fg_color=colors["bg_primary"])
    tab_frame.pack(fill="both", expand=True, padx=50, pady=50)
    
    # Mensaje de mantenimiento
    icon_label = ctk.CTkLabel(
        tab_frame,
        text="\u25c9\u25c9\u25c9\\n\\n\u25c9  \u25c9\\n\\n\u25c9\u25c9\u25c9",
        font=("Roboto", 48),
        text_color="#555555"
    )
    icon_label.pack(pady=(30, 20))
    
    title_label = ctk.CTkLabel(
        tab_frame,
        text="M\u00d3DULO EN MANTENIMIENTO",
        font=("Roboto", 20, "bold"),
        text_color=colors["text_primary"]
    )
    title_label.pack(pady=10)
    
    desc_label = ctk.CTkLabel(
        tab_frame,
        text="El m\u00f3dulo de Solicitud estar\u00e1 disponible pr\u00f3ximamente.\\n\\n"
             "Por ahora, puedes usar el Verificador o el Generador DJC.",
        font=("Roboto", 12),
        text_color=colors["text_secondary"],
        justify="center"
    )
    desc_label.pack(pady=10)

def show_verificador_tab(self):
    """Muestra tab de Verificador (flujo actual: datasheet + certs + auditoria)"""
    colors = self.theme_manager.get_current_colors()
    
    # Crear main_frame para compatibilidad con código existente
    self.main_frame = ctk.CTkFrame(self.content_container, fg_color=colors["bg_primary"], corner_radius=0)
    self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)
    
    # NOTA: El c\u00f3digo existente (PASO 1, PASO 2, etc.) ya est\u00e1 en create_widgets
    # y usa self.main_frame. Al crear este frame arriba, el c\u00f3digo existente funciona.
    # TODO: Refactorizar para mover todo el c\u00f3digo de verificador aqu\u00ed

def show_generador_tab(self):
    """Muestra tab de Generador DJC (flujo directo: cert -> DJC)"""
    colors = self.theme_manager.get_current_colors()
    
    tab_frame = ctk.CTkFrame(self.content_container, fg_color=colors["bg_primary"])
    tab_frame.pack(fill="both", expand=True, padx=0, pady=0)
    
    # T\u00edtulo
    title_frame = ctk.CTkFrame(tab_frame, fg_color=colors["bg_secondary"], corner_radius=0)
    title_frame.pack(fill="x", pady=(15, 10), padx=20)
    
    title_label = ctk.CTkLabel(
        title_frame,
        text="\u25c9\u25c9\u25c9 GENERADOR DE DJC",
        font=("Roboto", 18, "bold"),
        text_color=colors["text_primary"]
    )
    title_label.pack(anchor="w", padx=15, pady=15)
    
    # Instrucci\u00f3n
    inst_label = ctk.CTkLabel(
        title_frame,
        text="Genera una Declaraci\u00f3n Jurada de Conformidad directamente desde un certificado PDF.",
        font=("Roboto", 11),
        text_color=colors["text_secondary"]
    )
    inst_label.pack(anchor="w", padx=15, pady=(0, 15))
    
    # Drag & Drop para certificado
    cert_frame = ctk.CTkFrame(tab_frame, fg_color=colors["bg_secondary"], corner_radius=0)
    cert_frame.pack(fill="x", pady=10, padx=20)
    
    cert_label = ctk.CTkLabel(
        cert_frame,
        text="CERTIFICADO PDF",
        font=("Roboto", 12, "bold"),
        text_color=colors["text_primary"]
    )
    cert_label.pack(anchor="w", padx=15, pady=(15, 10))
    
    self.drop_cert_direct = ctk.CTkFrame(
        cert_frame,
        fg_color=colors["bg_tertiary"],
        border_width=2,
        border_color=colors["border"],
        corner_radius=0,
        height=100
    )
    self.drop_cert_direct.pack(fill="x", padx=15, pady=(5, 15))
    
    drop_label = ctk.CTkLabel(
        self.drop_cert_direct,
        text="\ud83d\udcc4 Arrastrar certificado aqu\u00ed",
        font=("Roboto", 12),
        text_color=colors["text_secondary"]
    )
    drop_label.pack(expand=True)
    
    # Registrar drag & drop
    self.drop_cert_direct.drop_target_register(DND_FILES)
    self.drop_cert_direct.dnd_bind('<<Drop>>', self.on_drop_cert_direct)
    
    # Archivo cargado
    self.cert_direct_label = ctk.CTkLabel(
        cert_frame,
        text="",
        font=("Roboto", 10),
        text_color=colors["accent_primary"]
    )
    self.cert_direct_label.pack(padx=15, pady=(0, 15))
    
    # Bot\u00f3n generar
    self.gen_djc_btn = ctk.CTkButton(
        tab_frame,
        text="\u25c9\u25c9\u25c9 GENERAR DJC",
        font=("Roboto", 13, "bold"),
        height=50,
        fg_color=colors["accent_primary"],
        hover_color=colors["bg_tertiary"],
        state="disabled",
        command=self.generate_djc_direct
    )
    self.gen_djc_btn.pack(pady=20, padx=20, fill="x")

def on_drop_cert_direct(self, event):
    """Maneja drop de certificado en tab Generador"""
    file_path = event.data.strip('{}')
    if file_path.lower().endswith('.pdf'):
        self.cert_direct_path = file_path
        filename = os.path.basename(file_path)
        self.cert_direct_label.configure(text=f"\u2713 {filename}")
        self.gen_djc_btn.configure(state="normal")
        self.logger.info(f"Certificado cargado: {filename}")
    else:
        self.logger.error("Solo se aceptan archivos PDF")

def generate_djc_direct(self):
    """Genera DJC directamente desde certificado (sin auditar)"""
    self.logger.info("=== GENERANDO DJC DIRECTO ===")
    
    try:
        from modules.m3_djc_generator import DJCGenerator
        
        gen = DJCGenerator(gui_logger=self.logger)
        
        # Preparar datos desde certificado
        djc_data = gen.prepare_from_certificate(self.cert_direct_path)
        
        # Mostrar vista DJC para edici\u00f3n
        self.djc_data = djc_data
        self.djc_gen = gen
        self.show_djc_view()
        
    except Exception as e:
        self.logger.error(f"Error al generar DJC: {e}")
