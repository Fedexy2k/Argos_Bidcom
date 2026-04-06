"""
Módulo 3: Panel de Información Copiable
Genera datos formateados para copiar a la base de datos (estilo INAL Suite).
"""
from datetime import datetime, timedelta


class DJCInfoPanel:
    """
    Encapsula los campos de la DJC que se muestran en el panel de info copiable.
    Cada campo puede copiarse individualmente al clipboard.
    """

    def __init__(self, djc_data: dict):
        """
        Args:
            djc_data: dict con los datos de la DJC generada.
        """
        self.cert_number = djc_data.get("cert_number", "")
        self.djc_id = djc_data.get("djc_id", "")
        self.fecha_emision = djc_data.get("fecha_emision", "")
        self.fecha_vencimiento = djc_data.get("fecha_proxima_vigilancia", "")
        self.marca = djc_data.get("marca", "")
        self.modelos = djc_data.get("modelos", "")
        self.reglamento = djc_data.get("reglamento", "")
        
        # Calcular vencimiento si falta
        if not self.fecha_vencimiento and self.fecha_emision:
            self.fecha_vencimiento = self._calc_vencimiento(self.fecha_emision, self.reglamento)
        
        # Calcular fecha de inicio de trámite (3 meses antes del vencimiento)
        self.fecha_inicio_tramite = ""
        if self.fecha_vencimiento:
            self.fecha_inicio_tramite = self._calc_inicio_tramite(self.fecha_vencimiento)

    def _parse_date(self, date_str: str) -> datetime:
        """Parsea fecha en formatos comunes."""
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Formato de fecha no reconocido: {date_str}")

    def _vigencia_days(self, reglamento: str = "") -> int:
        """Ap. IV Electrónica = 4 años (1460d), resto = 2 años (730d)."""
        if reglamento and "Ap. IV" in reglamento and "Electrónica" in reglamento:
            return 1460
        return 730

    def _calc_vencimiento(self, fecha_emision: str, reglamento: str = "") -> str:
        """Calcula vencimiento = emisión + vigencia según reglamento."""
        try:
            fe = self._parse_date(fecha_emision)
            days = self._vigencia_days(reglamento)
            return (fe + timedelta(days=days)).strftime("%d/%m/%Y")
        except ValueError:
            return ""

    def _calc_inicio_tramite(self, fecha_vencimiento: str) -> str:
        """Calcula inicio de trámite = vencimiento - 3 meses."""
        try:
            fv = self._parse_date(fecha_vencimiento)
            return (fv - timedelta(days=90)).strftime("%d/%m/%Y")
        except ValueError:
            return ""

    def get_fields(self) -> list:
        """
        Retorna la lista de campos para el panel de info.
        
        Returns:
            Lista de dicts con 'label', 'value', 'key'.
        """
        return [
            {"label": "Nro de Certificado", "value": self.cert_number, "key": "cert_number"},
            {"label": "Nro de Expediente (DJC)", "value": self.djc_id, "key": "djc_id"},
            {"label": "Marca", "value": self.marca, "key": "marca"},
            {"label": "Modelos", "value": self.modelos, "key": "modelos"},
            {"label": "Reglamento", "value": self.reglamento, "key": "reglamento"},
            {"label": "Fecha de Inicio", "value": self.fecha_emision, "key": "fecha_emision"},
            {"label": "Fecha de Vencimiento", "value": self.fecha_vencimiento, "key": "fecha_vencimiento"},
            {"label": "Fecha Inicio Tramite", "value": self.fecha_inicio_tramite, "key": "fecha_inicio_tramite"},
        ]

    def to_dict(self) -> dict:
        """Retorna todos los campos como dict simple."""
        return {f["key"]: f["value"] for f in self.get_fields()}
