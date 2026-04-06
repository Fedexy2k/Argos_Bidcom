import customtkinter as ctk
import os

# --- Configuration & Constants ---
THEME_COLOR_BG = "#000000"         # Pure Black
THEME_COLOR_FG = "#00FF00"         # Neon Green
THEME_COLOR_ACCENT = "#003300"     # Darker Green for backgrounds/contrast
THEME_FONT_FAMILY = "Consolas"     # Monospaced font for Matrix feel
THEME_FONT_SIZE_MAIN = 14
THEME_FONT_SIZE_HEADER = 24

class ArgosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("ARGOS PROJECT - v1.0")
        self.geometry("1100x700")
        self.configure(fg_color=THEME_COLOR_BG) # Set main window background

        # Grid Layout (2 columns: Sidebar, Main Content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=THEME_COLOR_BG, border_width=2, border_color=THEME_COLOR_FG)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ARGOS\nSYSTEM", font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=THEME_FONT_SIZE_HEADER, weight="bold"), text_color=THEME_COLOR_FG)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Navigation Buttons
        self.btn_toys = self.create_nav_button("MODULE: TOYS", self.show_toys)
        self.btn_toys.grid(row=1, column=0, padx=20, pady=10)

        self.btn_electrical = self.create_nav_button("MODULE: ELECTRICAL", self.show_electrical)
        self.btn_electrical.grid(row=2, column=0, padx=20, pady=10)

        self.btn_ee = self.create_nav_button("MODULE: EE", self.show_ee)
        self.btn_ee.grid(row=3, column=0, padx=20, pady=10)

        # Footer / Status
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="STATUS: CONNECTED", font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=10), text_color=THEME_COLOR_FG)
        self.status_label.grid(row=5, column=0, padx=20, pady=20)


        # --- Main Content Area ---
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color=THEME_COLOR_BG)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Initialize Frames
        self.frames = {}
        for F in (ToysView, ElectricalView, EEView):
            page_name = F.__name__
            frame = F(parent=self.main_area, controller=self)
            self.frames[page_name] = frame
            # Stack all frames in the same grid cell
            frame.grid(row=0, column=0, sticky="nsew")

        # Select default view
        self.show_toys()

    def create_nav_button(self, text, command):
        """Helper to create consistent styled buttons"""
        return ctk.CTkButton(self.sidebar_frame, text=text, command=command,
                             fg_color="transparent", 
                             border_color=THEME_COLOR_FG, 
                             border_width=2,
                             text_color=THEME_COLOR_FG,
                             hover_color=THEME_COLOR_ACCENT,
                             font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=12, weight="bold"),
                             corner_radius=5,
                             height=40,
                             anchor="w")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def show_toys(self):
        self.show_frame("ToysView")

    def show_electrical(self):
        self.show_frame("ElectricalView")

    def show_ee(self):
        self.show_frame("EEView")


# --- Module Views (Placeholders) ---

class ModuleFrame(ctk.CTkFrame):
    def __init__(self, parent, controller, title="Module"):
        super().__init__(parent, fg_color=THEME_COLOR_BG, border_width=1, border_color=THEME_COLOR_FG)
        self.controller = controller
        
        # Header
        self.header = ctk.CTkLabel(self, text=f">_ {title}", font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=24, weight="bold"), text_color=THEME_COLOR_FG, anchor="w")
        self.header.pack(fill="x", padx=20, pady=20)
        
        # Content Placeholder
        self.content_label = ctk.CTkLabel(self, text="[ SYSTEM READY ]\n[ AWAITING INPUT ]", font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=16), text_color=THEME_COLOR_FG)
        self.content_label.pack(expand=True)

class ToysView(ModuleFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, title="INTERVENTION: TOYS")
        
        # --- Top Bar (Search & Actions) ---
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=20, pady=(0, 20))

        self.search_entry = ctk.CTkEntry(self.top_bar, placeholder_text="SEARCH SKU / CERTIFICATE...", 
                                         width=300, 
                                         fg_color=THEME_COLOR_BG, border_color=THEME_COLOR_FG, text_color=THEME_COLOR_FG)
        self.search_entry.pack(side="left", padx=(0, 10))

        self.btn_search = ctk.CTkButton(self.top_bar, text="SEARCH", width=100,
                                        fg_color=THEME_COLOR_ACCENT, hover_color=THEME_COLOR_FG, text_color=THEME_COLOR_BG)
        self.btn_search.pack(side="left")

        self.btn_new = ctk.CTkButton(self.top_bar, text="+ NEW ENTRY", width=120,
                                     fg_color=THEME_COLOR_FG, hover_color=THEME_COLOR_ACCENT, text_color=THEME_COLOR_BG)
        self.btn_new.pack(side="right")

        # --- Data Grid (Scrollable) ---
        self.data_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", label_text="ACTIVE CERTIFICATES", label_text_color=THEME_COLOR_FG)
        self.data_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Mock Data
        self.populate_mock_data()

    def populate_mock_data(self):
        # Header Row
        headers = ["ID", "PRODUCT", "CERTIFICATE", "STATUS", "ACTIONS"]
        for col, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.data_frame, text=h, font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=12, weight="bold"), text_color=THEME_COLOR_FG)
            lbl.grid(row=0, column=col, sticky="w", padx=10, pady=5)

        # Data Rows
        mock_data = [
            ("T-001", "OPTIMUS PRIME FIG", "C-837-2024", "VALID", "VIEW"),
            ("T-002", "RC RACER 3000", "C-912-2024", "PENDING", "EDIT"),
            ("T-003", "LEGO CITY SET", "C-110-2023", "EXPIRED", "RENEW"),
            ("T-004", "BARBIE DREAMHOUSE", "C-555-2025", "VALID", "VIEW"),
            ("T-005", "NERF BLASTER", "C-202-2024", "AUDIT", "CHECK"),
        ]

        for i, row_data in enumerate(mock_data, start=1):
            for j, val in enumerate(row_data):
                if j == 4: # Action Button
                    btn = ctk.CTkButton(self.data_frame, text=val, width=60, height=20, 
                                        fg_color="transparent", border_color=THEME_COLOR_FG, border_width=1, text_color=THEME_COLOR_FG,
                                        hover_color=THEME_COLOR_ACCENT)
                    btn.grid(row=i, column=j, padx=10, pady=2, sticky="w")
                else:
                    color = THEME_COLOR_FG
                    if j == 3: # Status Color Logic
                        if val == "VALID": color = "#00FF00"
                        elif val == "PENDING": color = "#FFFF00" # Yellow
                        elif val == "EXPIRED": color = "#FF0000" # Red
                        elif val == "AUDIT": color = "#FFA500"   # Orange

                    lbl = ctk.CTkLabel(self.data_frame, text=val, font=ctk.CTkFont(family=THEME_FONT_FAMILY, size=12), text_color=color)
                    lbl.grid(row=i, column=j, sticky="w", padx=10, pady=2)

class ElectricalView(ModuleFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, title="INTERVENTION: ELECTRICAL")

class EEView(ModuleFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, title="INTERVENTION: ENERGY EFFICIENCY")


if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = ArgosApp()
    app.mainloop()
