"""
Argos - Sistema de logging con GUI
"""
import logging
from datetime import datetime
from pathlib import Path


class GuiLogger:
    """Logger con interfaz visual y archivo"""
    
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Crear archivo de log con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"argos_{timestamp}.log"
        
        # Configurar logging
        self.logger = logging.getLogger("Argos")
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para archivo
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Lista para GUI
        self.gui_messages = []
        self.max_gui_messages = 1000
    
    def _add_to_gui(self, level, message):
        """Agrega mensaje a la lista para GUI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{level}] {timestamp} - {message}"
        self.gui_messages.append(formatted)
        
        # Limitar tamaño
        if len(self.gui_messages) > self.max_gui_messages:
            self.gui_messages.pop(0)
    
    def debug(self, message):
        """Log nivel DEBUG"""
        self.logger.debug(message)
        self._add_to_gui("DEBUG", message)
    
    def info(self, message):
        """Log nivel INFO"""
        self.logger.info(message)
        self._add_to_gui("INFO", message)
    
    def warning(self, message):
        """Log nivel WARNING"""
        self.logger.warning(message)
        self._add_to_gui("WARN", message)
    
    def error(self, message):
        """Log nivel ERROR"""
        self.logger.error(message)
        self._add_to_gui("ERROR", message)
    
    def get_gui_messages(self, last_n=None):
        """Retorna mensajes para mostrar en GUI"""
        if last_n:
            return self.gui_messages[-last_n:]
        return self.gui_messages
    
    def clear_gui(self):
        """Limpia mensajes de GUI (no del archivo)"""
        self.gui_messages = []
    
    def export_log(self):
        """Retorna path del archivo de log"""
        return str(self.log_file)
