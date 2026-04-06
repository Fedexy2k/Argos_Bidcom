"""
Argos - Sistema de temas (Claro y Matrix)
"""

class Theme:
    """Clase base para temas"""
    def __init__(self, name):
        self.name = name
    
    def get_colors(self) -> dict[str, str]:
        raise NotImplementedError


class LightTheme(Theme):
    """Tema claro profesional"""
    def __init__(self):
        super().__init__("Claro")
    
    def get_colors(self):
        return {
            "bg_primary": "#F5F5F5",      # Fondo principal
            "bg_secondary": "#FFFFFF",    # Paneles
            "bg_tertiary": "#E8E8E8",     # Hover
            "text_primary": "#1A1A1A",    # Texto principal
            "text_secondary": "#666666",  # Texto secundario
            "accent_primary": "#2E7D32",  # Verde profesional
            "accent_secondary": "#1976D2", # Azul
            "success": "#4CAF50",         # Verde success
            "warning": "#FF9800",         # Naranja warning
            "error": "#F44336",           # Rojo error
            "border": "#CCCCCC",          # Bordes
        }


class MatrixTheme(Theme):
    """Tema Matrix (oscuro con verde neón) - Ajustado para legibilidad"""
    def __init__(self):
        super().__init__("Matrix")
    
    def get_colors(self):
        return {
            "bg_primary": "#0D0D0D",      # Negro profundo
            "bg_secondary": "#1A1A1A",    # Gris oscuro
            "bg_tertiary": "#262626",     # Hover oscuro
            "text_primary": "#00CC33",    # Verde más oscuro (mejor legibilidad)
            "text_secondary": "#00AA88",  # Cyan más oscuro
            "accent_primary": "#00AA33",  # Verde Matrix más suave
            "accent_secondary": "#00AA88", # Cyan Matrix
            "success": "#33DD44",         # Verde brillante pero legible
            "warning": "#FFCC00",         # Dorado más oscuro
            "error": "#FF3344",           # Rojo neón
            "border": "#00CC33",          # Borde verde más oscuro
        }


class DarkTheme(Theme):
    """Tema oscuro profesional (no Matrix)"""
    def __init__(self):
        super().__init__("Oscuro")
    
    def get_colors(self):
        return {
            "bg_primary": "#1E1E1E",      # Gris muy oscuro
            "bg_secondary": "#2D2D2D",    # Gris oscuro
            "bg_tertiary": "#3C3C3C",     # Gris hover
            "text_primary": "#E0E0E0",    # Blanco suave
            "text_secondary": "#B0B0B0",  # Gris claro
            "accent_primary": "#4CAF50",  # Verde profesional
            "accent_secondary": "#2196F3", # Azul
            "success": "#66BB6A",         # Verde claro
            "warning": "#FFA726",         # Naranja
            "error": "#EF5350",           # Rojo
            "border": "#555555",          # Gris medio
        }


class ThemeManager:
    """Gestor de temas de la aplicación"""
    
    def __init__(self):
        self.themes = {
            "Oscuro": DarkTheme(),
            "Matrix": MatrixTheme(),
            "Claro": LightTheme()
        }
        self.current_theme = self.themes["Oscuro"]  # Default: Oscuro
    
    def set_theme(self, theme_name):
        """Cambia el tema activo"""
        if theme_name in self.themes:
            self.current_theme = self.themes[theme_name]
            return True
        return False
    
    def get_current_colors(self):
        """Retorna los colores del tema actual"""
        return self.current_theme.get_colors()
    
    def get_theme_name(self):
        """Retorna el nombre del tema actual"""
        return self.current_theme.name
    
    def cycle_theme(self):
        """Cicla entre temas: Oscuro -> Matrix -> Claro -> Oscuro"""
        current = self.get_theme_name()
        theme_order = ["Oscuro", "Matrix", "Claro"]
        current_idx = theme_order.index(current)
        next_idx = (current_idx + 1) % len(theme_order)
        new_theme = theme_order[next_idx]
        self.set_theme(new_theme)
        return new_theme
