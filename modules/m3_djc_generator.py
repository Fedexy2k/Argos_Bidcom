"""
Módulo 3: Generador de DJC (Declaración Jurada de Conformidad)
Llena la plantilla Word, exporta a PDF, merge con certificado, y sube a Drive.
"""
from __future__ import annotations

import os
import re
import json
import copy
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF  # type: ignore[import-untyped]
from docx import Document  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
#  Constantes de mapeo norma → reglamento
# ─────────────────────────────────────────────────────────────

# Cada entrada: (lista de keywords regex, reglamento display string)
# Se evalúan en orden; la primera coincidencia gana.
# Para desempatar normas compartidas (ej: IEC 62368-1) se usa tipo_producto.
NORM_REGLAMENTO_MAP = [
    # --- Res 17/2025 – Máquinas (evaluar antes de Res 16 para priorizar IEC 62841/60745) ---
    {
        "keywords": [
            r"IEC 62841", r"IEC 60745", r"IEC 61029",
            r"IEC 60974", r"IEC 60204", r"IEC 60825", r"IEC 60034",
            r"IEC 60335-2-41", r"IEC 60335-2-45", r"IEC 60335-2-51",
            r"IEC 60335-2-77", r"IEC 60335-2-91", r"IEC 60335-2-92",
            r"IEC 60335-2-94", r"IEC 60335-2-100",
        ],
        "reglamento": "Res. SIyC Nº 17/2025 – Ap. I (Máquinas y Herramientas)",
    },
    # --- Res 16/2025 Ap. III – Iluminación (evaluar antes de genéricos) ---
    {
        "keywords": [
            r"IEC 60598", r"IEC 61347", r"IEC 60155", r"IEC 60400",
            r"IEC 60238", r"IEC 60838", r"IEC 61184", r"IEC 60570",
            r"IEC 62560", r"IEC 60968", r"IEC 61195", r"IEC 62776",
            r"IEC 62031", r"IEC 62868", r"IEC 62035", r"IEC 62532",
        ],
        "reglamento": "Res. SIyC Nº 16/2025 – Ap. III (Iluminación)",
    },
    # --- Res 16/2025 Ap. I – Fuentes y Cargadores ---
    {
        "keywords": [
            r"IEC 60335-2-29",
            r"IEC 61558", r"IEC 62109", r"IEC 62477",
            r"IEC 62040", r"IEC 61851", r"IEC 62752",
        ],
        "reglamento": "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
    },
    # --- Res 16/2025 Ap. II – Electrodomésticos (IEC 60335 genérico) ---
    {
        "keywords": [r"IEC 60335"],
        "reglamento": "Res. SIyC Nº 16/2025 – Ap. II (Aparatos Eléctricos Domésticos)",
    },
    # --- Res 16/2025 Ap. IV – Electrónica (IEC 62368, 60065, 60950) ---
    {
        "keywords": [r"IEC 62368", r"IEC 60065", r"IEC 60950"],
        "reglamento": "Res. SIyC Nº 16/2025 – Ap. IV (Electrónica, Audio, Video)",
    },
    # --- Res 26/2025 – Instalaciones Eléctricas ---
    {
        "keywords": [
            r"IEC 61386", r"IEC 61084", r"IEC 60670", r"IEC 60715",
            r"IEC 62208", r"IEC 61537", r"IEC 60227", r"IEC 60245",
            r"IEC 60502", r"IEC 60947", r"IEC 60884", r"IEC 60898",
            r"IEC 61008", r"IEC 61009", r"IEC 60309", r"IEC 60669",
            r"IEC 60454", r"IEC 60320", r"IEC 60998", r"IEC 61238",
            r"IEC 62444", r"IEC 60730", r"IEC 61508",
            r"IEC 62052", r"IEC 60831",
            r"IRAM 2063", r"IRAM 2073", r"IRAM 2005", r"IRAM 2205",
            r"IRAM 2224", r"IRAM 2309", r"IRAM 2310", r"IRAM 2314",
            r"IRAM 2346", r"IRAM 2353", r"IRAM 2390",
        ],
        "reglamento": "Res. SIyC Nº 26/2025 (= 236/2024) – Materiales Inst. Eléctricas",
    },
    # --- Res 313/2025 – Encendedores ---
    {
        "keywords": [r"IRAM 3980", r"IRAM 3981", r"IRAM 3982", r"ISO 9994", r"ISO 22702", r"ASTM F400"],
        "reglamento": "Res. SIyC Nº 313/2025 – Ap. I (Encendedores)",
    },
    # --- Res 313/2025 – Anteojos ---
    {
        "keywords": [r"ISO 12312"],
        "reglamento": "Res. SIyC Nº 313/2025 – Ap. II (Anteojos de Sol)",
    },
    # --- Res 163/2004 – Juguetes (legacy, activa) ---
    {
        "keywords": [r"NM 300", r"IRAM NM 300", r"ISO 8124", r"ASTM F963", r"EN 71", r"IEC 62115"],
        "reglamento": "Res. SCT Nº 163/2004 (Juguetes – vigente)",
    },
    # --- Res 313/2025 – Bicicletas ---
    {
        "keywords": [r"NM 301", r"IRAM NM 301", r"ISO 8098"],
        "reglamento": "Res. SIyC Nº 313/2025 – Ap. IV (Bicicletas Infantiles)",
    },
]

# Desempate: si una norma matchea Ap. IV (Electrónica) pero el producto es fuente/cargador → Ap. I
PRODUCT_TYPE_OVERRIDES = {
    # keywords en producto → reglamento forzado
    "fuente": "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
    "cargador": "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
    "adaptador": "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
    "power supply": "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
    "charger": "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
}

# Keywords para detección de OEC (orden de prioridad)
OEC_KEYWORDS = {
    "q-ar": "Quektra",
    "quektra": "Quektra",
    "qetkra": "Quektra",
    "intertek": "Intertek",
    "bureau veritas": "Bureau Veritas",
    "bv ": "Bureau Veritas",
    "tüv": "TÜV",
    "tuv": "TÜV",
    "lenor": "Lenor",
    "iram": "IRAM",
}


# ─────────────────────────────────────────────────────────────
#  Clase principal
# ─────────────────────────────────────────────────────────────

class DJCGenerator:
    """Genera Declaraciones Juradas de Conformidad a partir de datos de certificados."""

    TEMPLATE_FILENAME = "DJ Conformidad Modelo SE.docx"

    def __init__(self, config_path: Optional[str] = None, gui_logger=None):
        """
        Args:
            config_path: Ruta al m3_config.json. Si None, busca en el directorio del proyecto.
            gui_logger: Logger de GUI para mensajes visibles al usuario.
        """
        self.gui_logger = gui_logger
        
        # Buscar config
        if config_path is None:
            base_dir = Path(__file__).parent.parent
            config_path = str(base_dir / "m3_config.json")
        
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        
        # Buscar template
        self.template_path = Path(__file__).parent.parent / self.TEMPLATE_FILENAME
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template DJC no encontrado: {self.template_path}")
        
        self._log("info", f"DJCGenerator inicializado. Template: {self.template_path.name}")

    def _log(self, level: str, message: str):
        """Logging dual: logger estándar + GUI logger."""
        getattr(logger, level, logger.info)(message)
        if self.gui_logger:
            try:
                self.gui_logger.log(message, level.upper())
            except Exception:
                pass

    # ─── Detección automática ───────────────────────────────

    def detect_reglamento(self, normas_text: str, producto_desc: str = "") -> str:
        """
        Auto-detecta el reglamento aplicable a partir de las normas del certificado.
        
        Args:
            normas_text: Texto de normas técnicas del certificado.
            producto_desc: Descripción del producto (para desempate).
        
        Returns:
            String del reglamento detectado o cadena vacía si no se detectó.
        """
        if not normas_text:
            return ""
        
        normas_upper = normas_text.upper()
        
        for entry in NORM_REGLAMENTO_MAP:
            for kw in entry["keywords"]:
                if re.search(kw, normas_upper, re.IGNORECASE):
                    detected = entry["reglamento"]
                    
                    # Desempate por tipo de producto
                    if producto_desc and "Ap. IV" in detected:
                        prod_lower = producto_desc.lower()
                        for prod_kw, override_reglamento in PRODUCT_TYPE_OVERRIDES.items():
                            if prod_kw in prod_lower:
                                self._log("info", 
                                    f"Desempate: producto '{producto_desc}' → {override_reglamento}")
                                return override_reglamento
                    
                    self._log("info", f"Reglamento detectado: {detected}")
                    return str(detected)
        
        self._log("warning", f"No se detectó reglamento para normas: {str(normas_text)[:80]}  # type: ignore[index]")
        return ""

    def detect_oec(self, cert_text: str) -> str:
        """
        Auto-detecta el Organismo de Evaluación de Conformidad.
        
        Args:
            cert_text: Texto completo del certificado PDF.
        
        Returns:
            Key del OEC en config (ej: "Lenor") o cadena vacía.
        """
        if not cert_text:
            return ""
        
        text_lower = cert_text.lower()
        for keyword, oec_key in OEC_KEYWORDS.items():
            if keyword in text_lower:
                self._log("info", f"OEC detectado: {oec_key}")
                return oec_key
        
        self._log("warning", "No se detectó OEC en el certificado")
        return ""

    def extract_cert_data(self, pdf_path: str) -> dict:
        """
        Extrae datos clave de un certificado PDF.
        
        Returns:
            dict con keys: cert_number, normas, fecha_emision, fecha_vencimiento,
                          oec_key, cert_text
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Certificado no encontrado: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        full_text = ""
        full_text_sorted = ""
        for page in doc:
            full_text += page.get_text()
            full_text_sorted += page.get_text("text", sort=True)
        doc.close()
        
        result = {
            "cert_number": self._extract_cert_number(full_text),
            "normas": self._extract_normas(full_text),
            "fecha_emision": self._extract_date(full_text, "emision"),
            "fecha_vencimiento": self._extract_date(full_text, "vencimiento"),
            "oec_key": self.detect_oec(full_text),
            "cert_text": full_text,
            "cert_text_sorted": full_text_sorted,
        }
        
        self._log("info", f"Datos extraídos del certificado: Nro={result['cert_number']}")
        return result

    def _extract_cert_number(self, text: str) -> str:
        """Extrae referencia del certificado del PDF (ej: LCSH-2058, Q-AR-123)."""
        patterns = [
            # Lenor: "Referencia de Certificado: LCSH-XXXX" o "Certificate reference: LCSH-XXXX"
            r"(?:Referencia\s*de\s*Certificado|Certificate\s*reference)\s*:?\s*([A-Z]{2,6}-\d{3,6})",
            # Quektra: "Q-AR-XXXXXX" (puede tener sufijo como -T-0)
            r"\b(Q-AR-\d{4,8}(?:-[A-Z0-9]+)*)\b",
            # CB Scheme: "CB Certificate No. XXXX"
            r"(?:CB\s*Certificate\s*(?:No|N[\u00b0\u00ba])\.?\s*:?\s*)([A-Z0-9][\w\-/.]+)",
            # Genérico: Certificate No / Certificado N°
            r"(?:Certificate\s*(?:No|Number|#|N[\u00b0\u00ba])\.?\s*:?\s*)([A-Z0-9][\w\-/.]+)",
            r"(?:Certificado\s*(?:No|N[\u00b0\u00ba]|Nro)\.?\s*:?\s*)([A-Z0-9][\w\-/.]+)",
            r"(?:Report\s*(?:No|Number)\.?\s*:?\s*)([A-Z0-9][\w\-/.]+)",
            # IRAM: "DC-E-[A-Z0-9\-]+" (puede aparecer en encabezado)
            r"\b(DC-[A-Z]-[A-Z0-9]{2,6}\s*-\d+(?:\.\d+)?)\b",
            r"\b(DC-[A-Z0-9\-]{5,15})\b",
            # Fallback: patrón alfanumérico tipo LCSH-2058
            r"\b([A-Z]{2,5}[\-/]\d{3,6}(?:[\-/]\w+)?)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_normas(self, text: str) -> str:
        """
        Extrae normas técnicas del certificado.

        Familias soportadas (según NORM_REGLAMENTO_MAP):
          IEC  – excluye 17xxx (esquemas de conformidad como IEC 17067, ISO/IEC 17065)
          CISPR – p. ej. CISPR 14, CISPR 22, CISPR 32
          ISO  – excluye 17xxx (ISO/IEC 17067, etc.)
          EN   – p. ej. EN 71, EN 55032
          IRAM – p. ej. IRAM 2063, IRAM NM 300
          NM   – p. ej. NM 300, NM 301
          ASTM – p. ej. ASTM F963

        Captura la línea completa para incluir año, edición y enmiendas (+ A1: 2013…).
        """
        patterns = [
            # IEC: 4-5 dígitos, excluye serie 17xxx (conformidad)
            re.compile(
                r'IEC\s*(?!17\d{3})\d{4,5}(?:[\-\.\w]*)?(?:[^\n]*)',
                re.IGNORECASE
            ),
            # CISPR: 2-3 dígitos (ej. CISPR 14, CISPR 32)
            re.compile(
                r'CISPR\s*\d{1,3}(?:[\-\.\w]*)?(?:[^\n]*)',
                re.IGNORECASE
            ),
            # ISO y ISO/IEC: excluye serie 17xxx
            re.compile(
                r'ISO(?:/IEC)?\s*(?!17\d{3})\d{4,5}(?:[\-\.\w]*)?(?:[^\n]*)',
                re.IGNORECASE
            ),
            # EN (IEC): 2-5 dígitos (ej. EN 71, EN 55032, EN IEC 62368)
            re.compile(
                r'EN\s*(?:IEC\s*)?(?!17\d{3})\d{2,5}(?:[\-\.\w]*)?(?:[^\n]*)',
                re.IGNORECASE
            ),
            # IRAM e IRAM NM
            re.compile(
                r'IRAM\s*(?:NM\s*)?\d{3,5}(?:[\-\.\w]*)?(?:[^\n]*)',
                re.IGNORECASE
            ),
            # NM (MERCOSUR): ej. NM 300, NM 301
            re.compile(
                r'NM\s*\d{3}(?:[\-\.\w]*)?',
                re.IGNORECASE
            ),
            # ASTM: ej. ASTM F963
            re.compile(
                r'ASTM\s*[A-Z]\d+(?:[\-\.\w]*)?',
                re.IGNORECASE
            ),
        ]

        found = []
        seen_spans = set()   # (start, end) en el texto original
        for pattern in patterns:
            for m in pattern.finditer(text):
                span = m.span()
                # Ignorar si este span solapa con uno ya capturado
                if any(span[0] >= s[0] and span[1] <= s[1] for s in seen_spans):
                    continue
                norm = m.group(0).strip().rstrip(".,;")
                norm = re.sub(r' {2,}', ' ', norm)
                if not norm:
                    continue
                norm_l = norm.lower()
                # Ignorar si ya existe una norma que lo contiene (duplicado corto)
                if any(norm_l in f.lower() for f in found):
                    continue
                # Si contiene algo que ya registramos (match más largo), reemplazarlo
                found = [f for f in found if f.lower() not in norm_l]
                found.append(norm)
                seen_spans.add(span)

        return ", ".join(found) if found else ""

    def _extract_date(self, text: str, date_type: str) -> str:
        """Extrae fechas del certificado."""
        if date_type == "emision":
            context_patterns = [
                r"(?:Date\s*of\s*[Ii]ssu(?:e|ance)|Fecha\s*de\s*[Ee]misi[oó]n|[Ii]ssued?)\s*:?\s*",
            ]
        else:
            context_patterns = [
                r"(?:Valid\s*(?:until|to|through)|Expir[ey]|Vencimiento|[Vv]igencia\s*hasta)\s*:?\s*",
            ]
        
        date_pattern = r"(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})"
        
        for ctx in context_patterns:
            match = re.search(ctx + date_pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""

    # ─── Llenado de plantilla ───────────────────────────────

    def fill_template(self, data: dict) -> Document:
        """
        Llena la plantilla DJC Word con los datos proporcionados.
        
        Args:
            data: dict con las claves necesarias para llenar el template.
                  Keys esperadas:
                    - djc_id: str (ID de la DJC)
                    - fabricante: str (código de fábrica)
                    - direccion_fabrica: str
                    - producto_desc: str (identificación del producto)
                    - marca: str
                    - modelos: str (modelos separados por coma)
                    - specs: str (características técnicas)
                    - reglamento: str
                    - normas: str
                    - cert_number: str
                    - esquema: str
                    - fecha_emision: str
                    - fecha_vigilancia: str (o "No aplicable")
                    - fecha_proxima_vigilancia: str
                    - oec_nombre: str
                    - oec_contacto: str
                    - enlace_djc: str
                    - representante (dict, opcional para extensiones)
        
        Returns:
            Document object listo para guardar.
        """
        doc = Document(str(self.template_path))
        tables = doc.tables
        
        if len(tables) < 8:
            raise ValueError(f"Template inválido: esperaba 8 tablas, encontró {len(tables)}")
        
        # T0: ID de DJC — fondo blanco, negrita, centrado
        self._set_cell_id(tables[0], 1, 0, data.get("djc_id", ""))
        
        # T1: Datos empresa (generalmente fijos desde config)
        emp = self.config["empresa"]
        self._set_cell(tables[1], 0, 1, emp["razon_social"])
        self._set_cell(tables[1], 1, 1, emp["cuit"])
        self._set_cell(tables[1], 2, 1, emp["marca_registrada"])
        self._set_cell(tables[1], 3, 1, emp["domicilio_legal"])
        self._set_cell(tables[1], 4, 1, emp["domicilio_deposito"])
        self._set_cell(tables[1], 5, 1, emp["telefono"])
        self._set_cell(tables[1], 6, 1, emp["email"])
        
        # T2: Representante Autorizado
        rep = data.get("representante", self.config.get("representante_autorizado")) or {}
        self._set_cell(tables[2], 0, 1, rep.get("nombre", "No Aplica"))
        self._set_cell(tables[2], 1, 1, rep.get("cuit", "No Aplica"))
        self._set_cell(tables[2], 2, 1, rep.get("domicilio", "No Aplica"))
        
        # T3: Producto
        self._set_cell(tables[3], 0, 1, "ver «Modelo» más abajo")  # Código autodeterminado
        self._set_cell(tables[3], 1, 1, data.get("fabricante", ""))
        self._set_cell(tables[3], 2, 1, data.get("direccion_fabrica", ""))
        self._set_cell(tables[3], 3, 1, data.get("producto_desc", ""))
        self._set_cell(tables[3], 4, 1, data.get("marca", ""))
        self._set_cell(tables[3], 5, 1, data.get("modelos", ""))
        self._set_cell(tables[3], 6, 1, data.get("specs", ""))
        
        # T4: Normas y Evaluación de Conformidad
        self._set_cell(tables[4], 0, 1, data.get("reglamento", ""))
        self._set_cell(tables[4], 0, 2, data.get("reglamento", ""))
        self._set_cell(tables[4], 1, 1, data.get("normas", ""))
        self._set_cell(tables[4], 1, 2, data.get("normas", ""))
        self._set_cell(tables[4], 2, 2, data.get("cert_number", ""))
        self._set_cell(tables[4], 3, 2, data.get("esquema", ""))
        self._set_cell(tables[4], 4, 2, data.get("fecha_emision", ""))
        self._set_cell(tables[4], 5, 2, data.get("fecha_vigilancia", "No aplicable"))
        self._set_cell(tables[4], 6, 2, data.get("fecha_proxima_vigilancia", ""))
        self._set_cell(tables[4], 7, 2, data.get("oec_nombre", ""))
        self._set_cell(tables[4], 8, 2, data.get("oec_nombre", ""))
        self._set_cell(tables[4], 9, 2, data.get("oec_contacto", ""))
        
        # T5: Enlace DJC (crear hipervínculo real)
        enlace = data.get("enlace_djc", "")
        if enlace:
            self._set_cell_hyperlink(tables[5], 0, 1, enlace, enlace)
        else:
            self._set_cell(tables[5], 0, 1, "")
        
        # T6: Emisión
        import zoneinfo
        tz = zoneinfo.ZoneInfo("America/Argentina/Buenos_Aires")
        fecha_hoy = datetime.now(tz).strftime("%d/%m/%Y")
        
        self._set_cell(tables[6], 0, 1, data.get("fecha_emision_djc", fecha_hoy))
        self._set_cell(tables[6], 1, 1, self.config["emision"]["lugar"])
        
        # T7: Firma
        self._set_cell(tables[7], 1, 1, self.config["firma"]["aclaracion"])
        
        self._log("info", f"Template DJC llenado para cert: {data.get('cert_number', 'N/A')}")
        return doc

    def _set_cell(self, table, row: int, col: int, value: str):
        """Establece el texto de una celda con fuente Arial 8pt."""
        from docx.shared import Pt  # type: ignore[import-untyped]
        try:
            cell = table.rows[row].cells[col]
            if cell.paragraphs:
                para = cell.paragraphs[0]
                if para.runs:
                    run = para.runs[0]
                    run.text = str(value) if value else ""
                    run.font.name = "Arial"
                    run.font.size = Pt(8)
                    # Limpiar runs adicionales
                    for extra_run in para.runs[1:]:
                        extra_run.text = ""
                else:
                    # No hay runs → crear uno con formato
                    para.clear()
                    run = para.add_run(str(value) if value else "")
                    run.font.name = "Arial"
                    run.font.size = Pt(8)
            else:
                cell.text = str(value) if value else ""
        except (IndexError, AttributeError) as e:
            self._log("warning", f"No se pudo escribir en celda [{row},{col}]: {e}")
    
    def _set_cell_id(self, table, row: int, col: int, value: str):
        """Celda para el Número de Identificación de DJC: fondo blanco, negrita, centrado, Arial 10pt."""
        from docx.shared import Pt, RGBColor  # type: ignore[import-untyped]
        from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore[import-untyped]
        from docx.oxml.ns import qn as _qn  # type: ignore[import-untyped]
        from lxml import etree  # type: ignore[import-untyped]
        try:
            cell = table.rows[row].cells[col]

            # 1. Fondo blanco en la celda (shading XML)
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            # Eliminar shading existente si hay
            for shd in tcPr.findall(_qn('w:shd')):
                tcPr.remove(shd)
            shd = etree.SubElement(tcPr, _qn('w:shd'))
            shd.set(_qn('w:val'), 'clear')
            shd.set(_qn('w:color'), 'auto')
            shd.set(_qn('w:fill'), 'FFFFFF')

            # 2. Escribir el texto: negrita, centrado, Arial 10pt
            para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            para.clear()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(str(value) if value else "")
            run.font.name = 'Arial'
            run.font.size = Pt(10)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
        except Exception as e:
            self._log('warning', f'[M3] No se pudo formatear celda ID [{row},{col}]: {e}')
            self._set_cell(table, row, col, value)

    def _set_cell_hyperlink(self, table, row: int, col: int, url: str, display_text: Optional[str] = None):
        """Crea un hipervínculo en una celda."""
        try:
            from docx.oxml.shared import OxmlElement, qn  # type: ignore[import-untyped]
            
            cell = table.rows[row].cells[col]
            para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            
            # Limpiar contenido previo
            para.clear()
            
            # Crear el hipervínculo
            hyperlink = OxmlElement('w:hyperlink')
            hyperlink.set(qn('r:id'), para.part.relate_to(
                url, 
                'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
                is_external=True
            ))
            
            # Crear el run con el texto
            new_run = OxmlElement('w:r')
            rPr = OxmlElement('w:rPr')
            
            # Estilo de hipervínculo (azul + subrayado + Arial 8pt)
            color = OxmlElement('w:color')
            color.set(qn('w:val'), '0000FF')
            rPr.append(color)
            
            u = OxmlElement('w:u')
            u.set(qn('w:val'), 'single')
            rPr.append(u)
            
            # Fuente Arial 8pt
            rFonts = OxmlElement('w:rFonts')
            rFonts.set(qn('w:ascii'), 'Arial')
            rFonts.set(qn('w:hAnsi'), 'Arial')
            rPr.append(rFonts)
            
            sz = OxmlElement('w:sz')
            sz.set(qn('w:val'), '16')  # 8pt = 16 half-points
            rPr.append(sz)
            
            szCs = OxmlElement('w:szCs')
            szCs.set(qn('w:val'), '16')
            rPr.append(szCs)
            
            new_run.append(rPr)
            new_run.text = display_text if display_text else url
            hyperlink.append(new_run)
            
            para._element.append(hyperlink)
            
        except (IndexError, AttributeError) as e:
            self._log("warning", f"No se pudo crear hipervínculo en celda [{row},{col}]: {e}")
            # Fallback: texto simple
            self._set_cell(table, row, col, url)

    # ─── Flujos de generación ───────────────────────────────

    def prepare_from_audit(self, json_data: dict, cert_data: dict) -> dict:
        """
        Prepara datos DJC desde resultado de auditoría (Módulo 2 → OK).
        
        Args:
            json_data: JSON normalizado del M1 (DatasheetParser).
            cert_data: dict retornado por extract_cert_data().
        
        Returns:
            dict listo para pasar a fill_template().
        """
        normas = cert_data.get("normas", "")
        producto_desc = json_data.get("specs_tecnicas", "")
        if isinstance(producto_desc, list):
            producto_desc = ", ".join(producto_desc)
        
        # Auto-detectar reglamento
        reglamento = self.detect_reglamento(normas, producto_desc)
        
        # Auto-detectar OEC
        oec_key = cert_data.get("oec_key", "")
        oec_info = self.config["oec_options"].get(oec_key, {})
        
        # Calcular fechas de vigilancia
        fecha_emision = cert_data.get("fecha_emision", "")
        fecha_vencimiento = cert_data.get("fecha_vencimiento", "")
        
        if not fecha_vencimiento and fecha_emision:
            fecha_vencimiento = self._calc_vencimiento(fecha_emision, reglamento)
        
        fecha_inicio_tramite = self._calc_inicio_tramite(fecha_vencimiento)
        
        # Número interno Bidcom (del datasheet) → para enlace y ID DJC
        bidcom_number = json_data.get("id_gestion", "")
        
        # Referencia del certificado PDF (ej: LCSH-2058) → para datos del certificado
        cert_ref = cert_data.get("cert_number", "")
        
        # ID DJC con formato editable
        djc_id = f"DJC-CERTIFICADO {bidcom_number}-V1" if bidcom_number else "DJC-V1"
        
        # Modelos
        modelos = json_data.get("modelos_solicitados", [])
        if isinstance(modelos, list):
            modelos_str = ", ".join(modelos)
        else:
            modelos_str = str(modelos)
        
        # Specs
        specs = json_data.get("specs_tecnicas", "")
        if isinstance(specs, list):
            specs = ", ".join(specs)
        
        data = {
            "djc_id": djc_id,                              # "DJC-CERTIFICADO 337-V1" (editable)
            "bidcom_number": bidcom_number,                 # "337" (número interno Bidcom)
            "cert_number": cert_ref,                        # "LCSH-2058" (referencia del PDF)
            "fabricante": json_data.get("fabrica", ""),
            "direccion_fabrica": json_data.get("direccion_fabrica", ""),
            "producto_desc": self._infer_product_description(json_data),
            "marca": json_data.get("marca", ""),
            "modelos": modelos_str,
            "specs": specs,
            "reglamento": reglamento,
            "normas": normas,
            "esquema": self.config["esquema_options"][0],
            "fecha_emision": fecha_emision,
            "fecha_vigilancia": "No aplicable",
            "fecha_proxima_vigilancia": fecha_vencimiento,
            "fecha_inicio_tramite":     fecha_inicio_tramite,
            "oec_nombre": oec_info.get("nombre", ""),
            "oec_contacto": oec_info.get("contacto", ""),
            "enlace_djc": self._generate_djc_link(bidcom_number),
        }
        
        return data

    def prepare_from_certificate(self, cert_pdf_path: str) -> dict:
        """
        Prepara datos DJC desde un certificado nuevo (sin auditoría previa).
        Extrae TODOS los datos del producto directamente del PDF.
        """
        cert_data = self.extract_cert_data(cert_pdf_path)
        text = cert_data.get("cert_text", "")
        text_sorted = cert_data.get("cert_text_sorted", "")
        
        normas = cert_data.get("normas", "")
        reglamento = self.detect_reglamento(normas)
        
        oec_key = cert_data.get("oec_key", "")
        oec_info = self.config["oec_options"].get(oec_key, {})
        cert_number = cert_data.get("cert_number", "")
        
        self._log("info", f"[M3] OEC={oec_key or '[no detectado]'}, Cert={cert_number or '[no encontrado]'}, Reglamento={reglamento or '[no detectado]'}")
        
        # ── Extraer datos del producto + fechas del texto del certificado ──
        product = self.extract_product_data_from_cert(text, text_sorted)
        
        # Fechas: priorizar lo extraído por la estrategia
        fecha_emision = product.get("fecha_emision", "") or cert_data.get("fecha_emision", "")
        fecha_vencimiento = product.get("fecha_vencimiento", "") or cert_data.get("fecha_vencimiento", "")
        fecha_inicio_tramite = product.get("fecha_inicio_tramite", "")
        
        # Fallback: calcular si faltan
        if not fecha_vencimiento and fecha_emision:
            fecha_vencimiento = self._calc_vencimiento(fecha_emision, reglamento)
        if not fecha_inicio_tramite and fecha_vencimiento:
            fecha_inicio_tramite = self._calc_inicio_tramite(fecha_vencimiento)
        
        data = {
            "djc_id":                   self.generate_djc_id(reglamento, oec_key, bidcom_num=""),
            "oec_key":                  oec_key,
            "fabricante":               product["fabricante"],
            "direccion_fabrica":        product["direccion"],
            "producto_desc":            product["producto_desc"],
            "marca":                    product["marca"],
            "modelos":                  product["modelos"],
            "specs":                    product["specs"],
            "reglamento":               reglamento,
            "normas":                   normas,
            "cert_number":              cert_number,
            "esquema":                  self.config["esquema_options"][0],
            "fecha_emision":            fecha_emision,
            "fecha_vigilancia":         "No aplicable",
            "fecha_proxima_vigilancia": fecha_vencimiento,
            "fecha_inicio_tramite":     fecha_inicio_tramite,
            "oec_nombre":               oec_info.get("nombre", ""),
            "oec_contacto":             oec_info.get("contacto", ""),
            "enlace_djc":               "https://qr.gadnic.com/certifications/certificado-",
        }
        
        self._log("info", f"Datos extraídos del cert: marca={product['marca']}, "
                  f"emision={fecha_emision}, vencimiento={fecha_vencimiento}")
        self._log("info", f"[M3] DJC ID propuesto: {data['djc_id']}")
        return data

    # ─── Generación del código ID de DJC ──────────────────────────────

    def generate_djc_id(self, reglamento: str, oec_nombre: str, bidcom_num: Optional[str] = None) -> str:
        """
        Genera el código propuesto para el ID de la DJC con el formato:
          DJC-{REG}-{AÑO}{MES}-{BIDCOM}-{OEC}-V1
        Ejemplo: DJC-SE-202602-C912-LEN-V1

        Si bidcom_num no se conoce, se usa 'XXXX' como placeholder.
        El usuario edita el campo en la GUI antes de generar.
        """
        from datetime import datetime as _dt

        # Abreviatura de reglamento
        regl_abrev_map = [
            (["juguete", "163/2004", "nm 300"],                                   "SJ"),
            (["16/2025", "17/2025", "60335", "62368", "62841", "62040", "60065"], "SE"),
            (["eficiencia energ", "mínima eficien"],                              "EE"),
            (["biciclet", "nm 301"],                                               "BI"),
            (["anteojos", "iso 12312"],                                            "AO"),
            (["encendedor", "iso 9994", "iram 3980"],                             "EN"),
            (["ftalato", "583/2008"],                                              "FT"),
        ]
        reglamento_raw = (reglamento or "").lower()
        regl_abrev = "OT"
        for keywords, code in regl_abrev_map:
            if any(kw in reglamento_raw for kw in keywords):
                regl_abrev = code
                break

        # Abreviatura del OEC
        oec_abrev_map = {
            "Lenor":          "LNR",
            "Quektra":        "QKA",
            "Intertek":       "ITK",
            "Bureau Veritas": "BVA",
            "TÜV":            "TUV",
        }
        oec_raw = (oec_nombre or "").strip()
        oec_abrev = next(
            (v for k, v in oec_abrev_map.items() if k.lower() in oec_raw.lower()),
            str(oec_raw)[:3].upper() if oec_raw else "OEC"  # type: ignore[index]
        )

        anio_mes = _dt.now().strftime("%m%y")   # ej: 0226 (MM + 2 dígitos año)
        bidcom = (str(bidcom_num) if bidcom_num else "XXXX").replace("/", "-")

        return f"DJC-{regl_abrev}-{anio_mes}-{bidcom}-{oec_abrev}-V1"

    # ─── Extracción de datos del producto desde texto del certificado ───

    def extract_product_data_from_cert(self, text: str, text_sorted: str = "") -> dict:
        """
        Dispatcher: detecta OEC y aplica extracción específica por certificadora.
        Misma lógica que StrategyFactory en m2_strategies.
        """
        oec_key = self.detect_oec(text)
        lines = [l.strip() for l in text.replace('\r\n', '\n').split('\n')]

        self._log("info", f"[M3] Despachando estrategia para OEC='{oec_key or 'Desconocido'}'")

        if oec_key == "Quektra":
            self._log("info", "[M3] Usando extractor QUEKTRA")
            return self._extract_quektra(lines)
        elif oec_key == "Lenor":
            self._log("info", "[M3] Usando extractor LENOR")
            return self._extract_lenor(lines, text_sorted)
        elif oec_key == "Intertek":
            self._log("info", "[M3] Usando extractor INTERTEK ARGENTINA")
            return self._extract_intertek(text_sorted, lines)
        elif oec_key in ("Bureau Veritas", "TÜV"):
            self._log("info", f"[M3] Usando extractor CB SCHEME ({oec_key})")
            return self._extract_cb(lines, text_sorted)
        elif oec_key == "IRAM":
            self._log("info", "[M3] Usando extractor IRAM")
            return self._extract_iram(lines)
        else:
            self._log("warning", "[M3] OEC no reconocido — usando extractor GENÉRICO")
            return self._extract_generic(lines)

    # ── Utilidades compartidas ──

    def _find_line(self, lines: list[str], labels: list[str], start: int = 0, end: Optional[int] = None) -> int:
        """Busca la primera línea que coincida con algún label (case-insensitive, ignora ':')."""
        if end is None:
            end = len(lines)
        for i in range(start, min(end, len(lines))):
            clean = lines[i].strip().rstrip(':').lower()
            for label in labels:
                if clean == label.rstrip(':').lower():
                    return i
        return -1

    def _next_non_empty(self, lines: list[str], after: int, skip_labels: Optional[set[str]] = None) -> tuple[int, str]:
        """
        Devuelve (indice, texto) de la siguiente línea no vacía después de 'after'.
        Salta labels conocidos si se proporcionan.
        """
        if skip_labels is None:
            skip_labels = set()
        for j in range(after + 1, min(after + 8, len(lines))):
            val = lines[j].strip()
            if not val:
                continue
            if val.rstrip(':').lower() in skip_labels:
                continue
            # Saltar códigos de formulario y páginación
            if re.match(r'^\d+ de \d+$', val) or re.match(r'^[A-Z]{2,5}-\d+\s+[A-Z]\d', val):
                continue
            return j, val
        return -1, ""

    def _find_date_after_label(self, lines: list[str], labels: list[str], start: int = 0) -> str:
        """
        Busca una fecha (dd/mm/yyyy) en las líneas siguientes a un label.
        Salta líneas que son traducciones bilingües o vacías.
        """
        idx = self._find_line(lines, labels, start=start)
        if idx < 0:
            return ""
        # Buscar la primera línea con formato de fecha en las siguientes 4 líneas
        date_re = re.compile(r'^(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})$')
        for j in range(idx + 1, min(idx + 5, len(lines))):
            val = lines[j].strip()
            if not val:
                continue
            m = date_re.match(val)
            if m:
                return m.group(1)
        return ""

    def _vigencia_days(self, reglamento: str = "") -> int:
        """Retorna la vigencia en días según el reglamento.
        Ap. IV Electrónica = 4 años (1460d), resto = 2 años (730d)."""
        if reglamento and "Ap. IV" in reglamento and "Electrónica" in reglamento:
            return 1460
        return 730

    def _calc_vencimiento(self, fecha_emision: str, reglamento: str = "") -> str:
        """Calcula vencimiento = emisión + vigencia según reglamento."""
        if not fecha_emision:
            return ""
        try:
            fe = self._parse_date(fecha_emision)
            days = self._vigencia_days(reglamento)
            return (fe + timedelta(days=days)).strftime("%d/%m/%Y")
        except (ValueError, Exception):
            return ""

    def _calc_inicio_tramite(self, fecha_vencimiento: str) -> str:
        """Calcula inicio de trámite = vencimiento - 3 meses (90 días)."""
        if not fecha_vencimiento:
            return ""
        try:
            fv = self._parse_date(fecha_vencimiento)
            return (fv - timedelta(days=90)).strftime("%d/%m/%Y")
        except (ValueError, Exception):
            return ""

    # ── Quektra ──────────────────────────────────────────────

    def _extract_quektra(self, lines: list[str]) -> dict:
        """
        Extrae datos de certificados Quektra (Q-AR-XXXXX).
        
        Estructura conocida (bilingual):
          Producto / Product → descripción
          Nombre y dirección del solicitante → BIDCOM (IGNORAR)
          Nombre y dirección del fabricante → fab name → dir
          Nombre y dirección de la fábrica → (duplicado, IGNORAR)
          Valores nominales y características principales → specs
          Marca / Trademark → marca
          Modelo / Referencia de Tipo → modelos (separados por ';')
        """
        result = {"marca": "", "fabricante": "", "direccion": "",
                  "modelos": "", "specs": "", "producto_desc": "",
                  "fecha_emision": "", "fecha_vencimiento": "",
                  "fecha_inicio_tramite": ""}

        # Labels bilingües que son traducción (no datos)
        bilingual_skip = {
            "product", "name and address of the applicant",
            "name and address of the manufacturer",
            "name and address of the factory",
            "nombre y dirección del solicitante",
            "nombre y dirección del fabricante",
            "nombre y dirección de la fábrica",
            "ratings and principal characteristics",
            "valores nominales y características",
            "principales", "trademark", "marca",
            "model / type ref.", "modelo / referencia de tipo",
            "additional information", "información adicional",
            "battery charger for cordless drill",  # traducción inglesa del producto
        }

        # ── PRODUCTO ──
        idx = self._find_line(lines, ["Producto"])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, bilingual_skip)
            if val:
                result["producto_desc"] = val

        # ── FABRICANTE + DIRECCIÓN ──
        # Buscar "Nombre y dirección del fabricante" (NO del solicitante)
        idx = self._find_line(lines, ["Nombre y dirección del fabricante"])
        if idx >= 0:
            # Saltar la línea inglesa "Name and address of the manufacturer"
            _, fab_name = self._next_non_empty(lines, idx, bilingual_skip)
            if fab_name:
                result["fabricante"] = fab_name
                # La dirección es la línea siguiente al nombre
                fab_name_idx = self._find_line(lines, [fab_name], start=idx)
                if fab_name_idx >= 0 and fab_name_idx + 1 < len(lines):
                    addr = lines[fab_name_idx + 1].strip()
                    if addr:
                        result["direccion"] = addr

        # ── SPECS ──
        # "Valores nominales y características" → "principales" → "Ratings..." → datos
        idx = self._find_line(lines, ["Valores nominales y características"])
        if idx >= 0:
            # Recoger TODAS las líneas de specs hasta la línea vacía
            specs_lines = []
            j = idx + 1
            while j < len(lines):
                val = lines[j].strip()
                if not val:
                    break  # Línea vacía = fin de sección
                low = val.rstrip(':').lower()
                if low in bilingual_skip:
                    j += 1
                    continue
                # Saltar códigos de formulario
                if re.match(r'^[A-Z]{2,5}-\d+\s+[A-Z]\d', val):
                    j += 1
                    continue
                specs_lines.append(val)
                j += 1
            if specs_lines:
                result["specs"] = "; ".join(specs_lines)

        # ── MARCA ──
        idx = self._find_line(lines, ["Marca"])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, bilingual_skip)
            if val:
                result["marca"] = val

        # ── MODELOS ──
        idx = self._find_line(lines, ["Modelo / Referencia de Tipo"])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, bilingual_skip)
            if val:
                items = [x.strip() for x in re.split(r'[;,]+', val) if x.strip()]
                result["modelos"] = ", ".join(items)

        # ── FECHAS ──
        # Quektra: "Fecha de emisión:" → "Issuance date (dd/mm/yyyy)" → fecha
        result["fecha_emision"] = self._find_date_after_label(
            lines, ["Fecha de emisión"])
        # Quektra no tiene fecha de vencimiento explícita → calcular
        result["fecha_vencimiento"] = self._calc_vencimiento(result["fecha_emision"])
        result["fecha_inicio_tramite"] = self._calc_inicio_tramite(result["fecha_vencimiento"])

        self._log("info", f"Quektra extraído: marca={result['marca']}, "
                  f"fab={str(result['fabricante'])[:30]}  # type: ignore[index], emision={result['fecha_emision']}")
        return result

    # ── Lenor ────────────────────────────────────────────────

    def _extract_lenor(self, lines: list[str], text_sorted: str = "") -> dict:
        """
        Extrae datos de certificados Lenor (LCSH-XXXX).
        
        Estructura conocida:
          Titular del certificado / Certificate holder → BIDCOM (IGNORAR)
          Dirección / Address → dirección BIDCOM (IGNORAR)
          Fábrica / Factory → nombre fab
          Dirección / Address → dirección fab (puede ser multi-línea)
          Producto / Product → descripción
          
          Anexo (página 2): tabla con grupos de 3 líneas:
            modelo, marca, specs
        """
        result = {"marca": "", "fabricante": "", "direccion": "",
                  "modelos": "", "specs": "", "producto_desc": "",
                  "fecha_emision": "", "fecha_vencimiento": "",
                  "fecha_inicio_tramite": ""}

        # Usar texto sorted para detección de formato 'NOTA DE NO APLICABILIDAD'
        # pero conservar las líneas unsorted para el parsing normal (mejor estructura para Lenor)
        detect_text = text_sorted if text_sorted else "\n".join(lines)
        detect_lines_sorted = [l.strip() for l in detect_text.replace('\r\n', '\n').split('\n') if l.strip()]

        # Detectar si es formato 'NOTA DE NO APLICABILIDAD' (ftalatos, Lenor especial)
        _dls: list[str] = detect_lines_sorted
        text_block = " ".join(_dls[:15])  # type: ignore[index]
        is_nota_no_aplicabilidad = "NOTA DE NO APLICABILIDAD" in text_block or "Norma con la cual se" in " ".join(_dls[:30])  # type: ignore[index]

        if is_nota_no_aplicabilidad:
            return self._extract_lenor_nota(detect_lines_sorted)

        # Para formato Lenor NORMAL usar las líneas unsorted (mejor parseadas)
        detect_lines = lines

        # Labels que son traducciones a saltar
        lenor_skip = {
            "certificate holder", "factory", "address", "product",
            "standard(s)", "testing laboratory", "test report n°",
            "additional information", "c.u.i.t",
        }

        # ── FÁBRICA + DIRECCIÓN ── (usa sorted lines para capturar inline labels)
        fab_idx = self._find_line(detect_lines, ["Fábrica"])
        if fab_idx >= 0:
            _, fab_name = self._next_non_empty(detect_lines, fab_idx, lenor_skip)
            if fab_name:
                result["fabricante"] = fab_name
                dir_idx = self._find_line(detect_lines, ["Dirección"], start=fab_idx + 1)
                if dir_idx >= 0:
                    _, dir_val = self._next_non_empty(detect_lines, dir_idx, lenor_skip)
                    if dir_val:
                        next_idx = dir_idx + 3
                        if next_idx < len(detect_lines):
                            next_line = detect_lines[next_idx].strip()
                            if (next_line and len(next_line) > 3
                                and next_line.rstrip(':').lower() not in
                                {"producto", "product", "norma(s)", "standard(s)",
                                 "c.u.i.t", "fábrica", "factory", "dirección", "address"}):
                                dir_val = dir_val + " " + next_line
                        result["direccion"] = dir_val

        # ── PRODUCTO ──
        idx = self._find_line(detect_lines, ["Producto"])
        if idx >= 0:
            _, val = self._next_non_empty(detect_lines, idx, lenor_skip)
            if val:
                result["producto_desc"] = val

        # ── MODELOS, MARCA, SPECS desde ANEXO ──
        annex = self._parse_lenor_annex(detect_lines)
        if annex["modelos"]:
            result["modelos"] = annex["modelos"]
        if annex["marca"]:
            result["marca"] = annex["marca"]
        if annex["specs"]:
            result["specs"] = annex["specs"]

        # ── FECHAS ──
        result["fecha_emision"] = self._find_date_after_label(
            detect_lines, ["Fecha de emisión"])
        result["fecha_vencimiento"] = self._find_date_after_label(
            detect_lines, ["Fecha de próxima vigilancia", "Fecha de vencimiento"])
        if not result["fecha_vencimiento"]:
            result["fecha_vencimiento"] = self._calc_vencimiento(result["fecha_emision"])
        result["fecha_inicio_tramite"] = self._calc_inicio_tramite(result["fecha_vencimiento"])

        self._log("info", f"Lenor extraído: marca={result['marca']}, "
                  f"fab={str(result['fabricante'])[:30]}  # type: ignore[index], emision={result['fecha_emision']}")
        return result

    def _extract_lenor_nota(self, lines: list[str]) -> dict:
        """
        Extrae datos del formato Lenor 'NOTA DE NO APLICABILIDAD' (certificados de ftalatos).
        
        Estructura:
          Fabricante: NOMBRE\n  Dirección: DIR
          Producto: VER ANEXO  Modelo: VER ANEXO
          Norma con la cual se certifica el producto: ...
          Laboratorio interviniente / Reporte N°
          Fecha de emisión: 30 de diciembre de 2025
          Fecha de vencimiento: 29 de diciembre de 2026
          Pág 2: tabla con Código de origen | Código comercial | Denominación | Descripción
        """
        result = {"marca": "", "fabricante": "", "direccion": "",
                  "modelos": "", "specs": "", "producto_desc": "",
                  "fecha_emision": "", "fecha_vencimiento": "",
                  "fecha_inicio_tramite": ""}

        MESES = {
            "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
            "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
            "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
        }

        def parse_es_date(text):
            """Parsea '30 de diciembre de 2025' → '30/12/2025'."""
            m = re.search(r'(\d{1,2}) de (\w+) de (\d{4})', text.lower())
            if m:
                day, month_name, year = m.group(1), m.group(2), m.group(3)
                month = MESES.get(month_name)
                if month:
                    return f"{day.zfill(2)}/{month}/{year}"
            # fallback: dd/mm/yyyy
            m2 = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', text)
            return m2.group(1) if m2 else ""

        for i, line in enumerate(lines):
            ll = line.lower()
            # Fabricante
            if ll.startswith('fabricante:') or ll.startswith('fabricante '):
                val = re.sub(r'^fabricante[:\s]+', '', line, flags=re.IGNORECASE).strip()
                if val:
                    result["fabricante"] = val
                    # línea siguiente suele ser dirección
                    if i + 1 < len(lines):
                        nxt = lines[i+1].strip()
                        if nxt and not nxt.lower().startswith('producto'):
                            if not result["direccion"]:
                                result["direccion"] = nxt
            # Dirección
            elif (ll.startswith('dirección:') or ll.startswith('dirección ')) and not result["direccion"]:
                val = re.sub(r'^direcci[oó]n[:\s]+', '', line, flags=re.IGNORECASE).strip()
                # puede continuar en siguiente línea
                if val:
                    j: int = i + 1  # type: ignore[operator]
                    while j < len(lines) and lines[j].strip():  # type: ignore[index]
                        low_j = lines[j].strip().lower()  # type: ignore[index]
                        if low_j.startswith('producto') or low_j.startswith('modelo') or low_j.startswith('norma'):
                            break
                        val = val + " " + lines[j].strip()  # type: ignore[operator]
                        j = j + 1  # type: ignore[operator]
                    result["direccion"] = val
            # Producto
            elif ll.startswith('producto:') or ll.startswith('producto '):
                val = re.sub(r'^producto[:\s]+', '', line, flags=re.IGNORECASE).strip()
                if val and val.upper() != "VER ANEXO":
                    result["producto_desc"] = val
            # Modelo en la cert principal (puede decir VER ANEXO)
            elif ll.startswith('modelo:') or ll.startswith('modelo '):
                val = re.sub(r'^modelo[:\s]+', '', line, flags=re.IGNORECASE).strip()
                if val and val.upper() != "VER ANEXO" and not result["modelos"]:
                    result["modelos"] = val
            # Fechas en texto español
            elif 'fecha de emisi' in ll:
                val = re.sub(r'^fecha de emisi[oó]n[:\s]*', '', line, flags=re.IGNORECASE).strip()
                result["fecha_emision"] = parse_es_date(val)
            elif 'fecha de vencimiento' in ll:
                val = re.sub(r'^fecha de vencimiento[:\s]*', '', line, flags=re.IGNORECASE).strip()
                result["fecha_vencimiento"] = parse_es_date(val)

        # Parsear anexo de tabla (página 2): columnas Nº | orig | comercial | denominación | descripción
        annex = self._parse_lenor_nota_annex(lines)
        if annex["modelos"] and not result["modelos"]:
            result["modelos"] = annex["modelos"]
        if not result["producto_desc"] and annex["producto_desc"]:
            result["producto_desc"] = annex["producto_desc"]

        # Marca viene del código comercial (el modelo es el código comercial)
        # Para ftalatos la marca no está explícita — dejar vacía

        if not result["fecha_vencimiento"]:
            result["fecha_vencimiento"] = self._calc_vencimiento(result["fecha_emision"])
        result["fecha_inicio_tramite"] = self._calc_inicio_tramite(result["fecha_vencimiento"])

        self._log("info", f"Lenor-Nota extraído: fab={str(result['fabricante'])[:30]}  # type: ignore[index], emision={result['fecha_emision']}")
        return result

    def _parse_lenor_nota_annex(self, lines: list[str]) -> dict:
        """
        Parsea el Anexo del certificado Lenor 'NOTA DE NO APLICABILIDAD'.
        Estructura de tabla: Nº | código_origen | código_comercial | denominación | descripción breve
        """
        result = {"modelos": "", "producto_desc": ""}
        
        # Buscar inicio del Anexo
        annex_start = -1
        for i, line in enumerate(lines):
            if "Anexo" in line or "N°" in line and "Certificado" in line:
                if "Código" in lines[i] if i < len(lines) else False:
                    annex_start = i
                    break
                if i + 1 < len(lines) and "Código" in lines[i+1]:
                    annex_start = i
                    break

        if annex_start < 0:
            # Buscar por presencia del encabezado de tabla
            for i, line in enumerate(lines):
                if ("Código de" in line or "código de" in line) and "origen" in line.lower():
                    annex_start = i
                    break

        if annex_start < 0:
            return result

        # Buscar filas de datos: líneas que empiezan con número de ítem
        modelos = []
        denominaciones = []
        item_re = re.compile(r'^(\d+)\s+')
        
        _annex_lines: list[str] = list(lines)
        for line in _annex_lines[annex_start:]:  # type: ignore[index]
            m = item_re.match(line)
            if m:
                # Extraer columnas separadas por espacios múltiples
                parts = re.split(r'\s{2,}', line.strip())
                # Esperado: ['1', 'MGN2100B', 'MGN2100B', 'JUGUETE BLOQUES', 'BLOQUES MAGNÉTICOS']
                if len(parts) >= 3:
                    codigo_comercial = parts[2].strip() if len(parts) > 2 else parts[1].strip()
                    denominacion = parts[3].strip() if len(parts) > 3 else ""
                    if codigo_comercial and not codigo_comercial.lower().startswith(('rev', 'fecha')):
                        modelos.append(codigo_comercial)
                    if denominacion:
                        denominaciones.append(denominacion)

        result["modelos"] = ", ".join(modelos)
        result["producto_desc"] = denominaciones[0] if denominaciones else ""
        return result

    def _parse_lenor_annex(self, lines: list[str]) -> dict:
        """
        Parsea la tabla Anexo de certificados Lenor.
        
        Soporta dos formatos:
        
        Formato A (LCSH - seguridad eléctrica):
          Modelo / Model          <- headers
          Marca / Brandname
          Caracteristicas tecnicas / Main ratings
          [modelo1]               <- datos en grupos de 3
          [marca1]
          [specs1]
        
        Formato B (LCJ - juguetes):
          N / Marca / Modelo / Producto   <- headers bilinguales (6 lineas)
          Detalle de productos...         <- linea antes de datos
          [1*]                            <- datos: Nro, Marca, Descripcion, Modelo
          [GADNIC]
          [Bloques Magneticos]
          [MGN2100B]
        """
        result: dict = {"modelos": "", "marca": "", "specs": ""}

        # Buscar inicio del Anexo (ambos formatos)
        _ll: list[str] = list(lines)
        annex_start: int = -1
        for _i, _line in enumerate(_ll):
            if ("Anexo al Certificado" in _line or "Annex of Certificate" in _line
                    or "Annex to Certificate" in _line):
                annex_start = _i
                break
        if annex_start < 0:
            return result

        # Detectar formato segun los headers del Anexo (buscar hasta 50 lineas)
        window_text = " ".join(_ll[annex_start: min(annex_start + 50, len(_ll))])  # type: ignore[index]

        # Formato B: juguetes tienen "Detalle de productos" o table con "Marca / Modelo / Producto"
        is_formato_b = ("Detalle de productos" in window_text
                        or "Producto (descripcion breve)" in window_text
                        or "Producto (descripci\u00f3n breve)" in window_text
                        or "Product (brief description)" in window_text)

        if is_formato_b:
            return self._parse_annex_formato_b(_ll, annex_start, result)
        else:
            return self._parse_annex_formato_a(_ll, annex_start, result)

    def _parse_annex_formato_b(self, _ll: list[str], annex_start: int, result: dict) -> dict:
        """Formato B del Anexo Lenor (juguetes): grupos de 4 lineas nro/marca/modelo/desc."""
        n: int = len(_ll)
        data_start: int = -1

        # Buscar ultimo header
        for idx in range(annex_start, min(annex_start + 50, n)):
            if ("Producto (descripci\u00f3n breve)" in _ll[idx]
                    or "Producto (descripcion breve)" in _ll[idx]
                    or "Product (brief description)" in _ll[idx]):
                data_start = idx + 1

        # Fallback: usar "Detalle de productos" y buscar primer numero de item
        if data_start < 0:
            for idx in range(annex_start, min(annex_start + 50, n)):
                if "Detalle de productos" in _ll[idx]:
                    for jj in range(idx + 1, min(idx + 15, n)):
                        if re.match(r'^\d+\*?$', _ll[jj].strip()):  # type: ignore[index]
                            data_start = jj
                            break
                    break

        if data_start < 0:
            return result

        # Saltar lineas vacias
        while data_start < n and not _ll[data_start].strip():  # type: ignore[index]
            data_start += 1  # type: ignore[operator]

        modelos: list[str] = []
        marcas: set[str] = set()
        cur: int = int(data_start)
        nro_re = re.compile(r'^\d+\*?$')

        while cur < n:
            nro = _ll[cur].strip()
            if not nro_re.match(nro):
                break
            if cur + 3 < n:
                marca_val = _ll[cur + 1].strip()
                modelo_val = _ll[cur + 2].strip()
                if modelo_val and re.match(r'^[A-Z0-9]', modelo_val):
                    modelos.append(modelo_val)
                elif modelo_val:
                    candidate = _ll[cur + 3].strip() if cur + 3 < n else ""
                    if candidate and re.match(r'^[A-Z0-9]', candidate):
                        modelos.append(candidate)
                    else:
                        modelos.append(modelo_val)
                if marca_val and marca_val.lower() not in ("brandname", "marca", "brand"):
                    marcas.add(marca_val)
            cur += 4  # type: ignore[operator]
            while cur < n and _ll[cur].strip().startswith("*"):  # type: ignore[operator,index]
                cur += 1  # type: ignore[operator]
            while cur < n and not _ll[cur].strip():  # type: ignore[operator,index]
                cur += 1  # type: ignore[operator]

        result["modelos"] = ", ".join(modelos)
        result["marca"] = list(marcas)[0] if marcas else ""
        return result

    def _parse_annex_formato_a(self, _ll: list[str], annex_start: int, result: dict) -> dict:
        """Formato A del Anexo Lenor (seguridad electrica): grupos de 3 lineas modelo/marca/specs."""
        n: int = len(_ll)
        data_start: int = -1

        for idx in range(annex_start, min(annex_start + 20, n)):
            if "Main ratings" in _ll[idx] or "Caracter\u00edsticas t\u00e9cnicas" in _ll[idx]:
                data_start = idx + 1

        if data_start < 0:
            return result

        while data_start < n and not _ll[data_start].strip():  # type: ignore[index]
            data_start += 1  # type: ignore[operator]

        modelos: list[str] = []
        marcas: set[str] = set()
        specs_set: set[str] = set()
        cur: int = int(data_start)

        while cur + 2 < n:  # type: ignore[operator]
            modelo_val = _ll[cur].strip()  # type: ignore[index]
            marca_val = _ll[cur + 1].strip()  # type: ignore[operator,index]
            specs_val = _ll[cur + 2].strip()  # type: ignore[operator,index]

            if not modelo_val or not re.match(r'^[A-Z0-9]', modelo_val) or len(modelo_val) > 50:
                break
            if modelo_val.lower() in ("model", "modelo", "brandname", "marca",
                                      "main ratings", "caracter\u00edsticas t\u00e9cnicas"):
                cur += 1  # type: ignore[operator]
                continue

            modelos.append(modelo_val)
            if marca_val and marca_val.lower() not in ("brandname", "marca", "brand"):
                marcas.add(marca_val)
            if specs_val and "rating" not in specs_val.lower() and "caracter\u00edsticas" not in specs_val.lower():
                specs_set.add(specs_val)
            cur += 3

            while cur < n and not _ll[cur].strip():  # type: ignore[operator,index]
                cur += 1  # type: ignore[operator]

        result["specs"] = list(specs_set)[0] if specs_set else ""
        result["modelos"] = ", ".join(modelos)
        result["marca"] = list(marcas)[0] if marcas else ""
        return result




    # ── CB Scheme ────────────────────────────────────────────

    def _extract_cb(self, lines: list[str], text_sorted: str = "") -> dict:
        """
        Extrae datos de certificados CB Scheme (TÜV, Bureau Veritas).
        """
        result = {"marca": "", "fabricante": "", "direccion": "",
                  "modelos": "", "specs": "", "producto_desc": "",
                  "fecha_emision": "", "fecha_vencimiento": "",
                  "fecha_inicio_tramite": ""}

        # Usar sorted lines solo para el fallback de fechas ISO
        # El resto de la extracción CB funciona mejor con el texto unsorted
        detect_lines = lines
        sorted_lines_for_dates = []
        if text_sorted:
            sorted_lines_for_dates = [l.strip() for l in text_sorted.replace('\r\n', '\n').split('\n')]

        cb_skip = {
            "trademark", "brand", "model", "type reference",
            "model / type ref.", "name and address of the manufacturer",
            "name and address of the factory",
            "name and address of the applicant",
            "ratings and principal characteristics",
            "product", "additional information",
        }

        # ── MARCA ── (match flexible: 'Trademark / Brand (if any)' también)
        for i, line in enumerate(detect_lines):
            lower = line.rstrip(':').lower()
            if lower.startswith('trademark') or lower.startswith('brand'):
                _, val = self._next_non_empty(detect_lines, i, cb_skip)
                if val:
                    result["marca"] = val
                break

        # ── MODELOS ──
        idx = self._find_line(detect_lines, ["Model / Type Ref.", "Model"])
        if idx >= 0:
            _, val = self._next_non_empty(detect_lines, idx, cb_skip)
            if val:
                items = [x.strip() for x in re.split(r'[;,]+', val) if x.strip()]
                result["modelos"] = ", ".join(items)

        # ── FABRICANTE + DIRECCIÓN ──
        idx = self._find_line(detect_lines, [
            "Name and address of the manufacturer",
            "Name and address of the factory",
        ])
        if idx >= 0:
            _, fab_name = self._next_non_empty(detect_lines, idx, cb_skip)
            if fab_name:
                result["fabricante"] = fab_name
                fab_line = self._find_line(detect_lines, [fab_name], start=idx)
                if fab_line >= 0 and fab_line + 1 < len(detect_lines):
                    addr = detect_lines[fab_line + 1].strip()
                    if addr:
                        result["direccion"] = addr

        # ── PRODUCTO ──
        idx = self._find_line(detect_lines, ["Product"])
        if idx >= 0:
            _, val = self._next_non_empty(detect_lines, idx, cb_skip)
            if val:
                result["producto_desc"] = val

        # ── SPECS ── (puede decir 'See page 2' — capturar lo que haya)
        idx = self._find_line(detect_lines, ["Ratings and principal characteristics", "Ratings"])
        if idx >= 0:
            _, val = self._next_non_empty(detect_lines, idx, cb_skip)
            if val:
                result["specs"] = val

        # ── FECHAS ──
        iso_date_re = re.compile(r'(\d{4}-\d{2}-\d{2})')
        result["fecha_emision"] = self._find_date_after_label(
            detect_lines, ["Date of issue", "Fecha de emisión", "Issued"])
        result["fecha_vencimiento"] = self._find_date_after_label(
            detect_lines, ["Valid until", "Expiry", "Valid to", "Fecha de próxima vigilancia"])

        # Fallback: buscar fecha ISO en líneas sorted de firma/pie de página
        if not result["fecha_emision"]:
            search_lines_for_iso = sorted_lines_for_dates if sorted_lines_for_dates else detect_lines
            for line in search_lines_for_iso:
                if 'signature' in line.lower() or 'date:' in line.lower():
                    m = iso_date_re.search(line)
                    if m:
                        try:
                            from datetime import datetime
                            dt = datetime.strptime(m.group(1), '%Y-%m-%d')
                            result["fecha_emision"] = dt.strftime('%d/%m/%Y')
                        except ValueError:
                            pass
                        break

        if not result["fecha_vencimiento"]:
            result["fecha_vencimiento"] = self._calc_vencimiento(result["fecha_emision"])
        result["fecha_inicio_tramite"] = self._calc_inicio_tramite(result["fecha_vencimiento"])
        self._log("info", f"CB extraído: marca={result['marca']}, "
                  f"fab={str(result['fabricante'])[:30]}  # type: ignore[index], emision={result['fecha_emision']}")
        return result

    def _extract_iram(self, lines: list[str]) -> dict:
        """
        Extrae datos de un certificado de tipo IRAM.
        Etiquetas características suelen ser bilingües:
        - "EMPRESA BENEFICIARIA ... :" -> Marca (Titular) pero no fabrica necesariamente. 
        - "DOMICILIO DE LA(S) PLANTA(S) DE PRODUCCIÓN ... :" -> Fábrica + Dirección
        - "PRODUCTO / PRODUCT :"
        - "REFERENCIA DE TIPO O MODELO / TYPE REFERENCE OR MODEL :"
        - "CARACTERÍSTICAS PRINCIPALES / MAIN CHARACTERISTICS :"
        - "MARCA / TRADE MARK OR NAME :"
        """
        result = {
            "fabricante": "",
            "direccion": "",
            "producto_desc": "",
            "marca": "",
            "modelos": "",
            "specs": "",
            "fecha_emision": "",
            "fecha_vencimiento": "",
            "fecha_inicio_tramite": ""
        }
        
        # 1. Fábrica y Dirección
        idx = self._find_line(lines, ["DOMICILIO DE LA(S) PLANTA(S) DE PRODUCCIÓN SUJETA(S) A INSPECCIÓN / ADDRESS(ES) OF THE PRODUCTION PLANT(S) UNDER INSPECTION", "PLANTA ELABORADORA / FACTORY"])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, skip_labels={"PRODUCTO / PRODUCT"})
            if val:
                # IRAM suele poner: "Nombre de Fabrica / Direccion, Ciudad, Pais" o sin barra.
                parts = val.split(" / ")
                if len(parts) >= 2:
                    result["fabricante"] = parts[0].strip()
                    _parts_rest: list[str] = list(parts)[1:]  # type: ignore[index]
                    result["direccion"] = " / ".join(_parts_rest).strip()
                else:
                    # Fallback (ej: todo junto, o la siguiente linea es la direccion)
                    result["fabricante"] = val
                    _, next_val = self._next_non_empty(lines, idx+1, skip_labels={"PRODUCTO / PRODUCT"})
                    if next_val and len(next_val) > 10:
                        result["direccion"] = next_val

        # 2. Producto
        idx = self._find_line(lines, ["PRODUCTO / PRODUCT", "PRODUCTO:"])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, skip_labels={"REFERENCIA DE TIPO O MODELO / TYPE REFERENCE OR MODEL"})
            if val:
                # Quitar parte en inglés si hay " / "
                result["producto_desc"] = val.split(" / ")[0].strip() if " / " in val else val

        # 3. Modelos
        idx = self._find_line(lines, ["REFERENCIA DE TIPO O MODELO / TYPE REFERENCE OR MODEL"])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, skip_labels={"CARACTERÍSTICAS PRINCIPALES / MAIN CHARACTERISTICS"})
            if val:
                result["modelos"] = val

        # 4. Specs técnicas
        idx = self._find_line(lines, ["CARACTERÍSTICAS PRINCIPALES / MAIN CHARACTERISTICS"])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, skip_labels={"MARCA / TRADE MARK OR NAME"})
            if val:
                result["specs"] = val

        # 5. Marca
        idx = self._find_line(lines, ["MARCA / TRADE MARK OR NAME"])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, skip_labels={"EN CONFORMIDAD CON LA(S) NORMA(S) / IN CONFORMITY WITH THE STANDARD(S)"})
            if val:
                # Suele estar entre comillas o apostrofes -> "MAVERICK; HAMILTON BEACH"
                clean_marca = re.sub(r'[\'\"”“]', '', val).strip()
                result["marca"] = clean_marca

        # Fechas: usar regex sobre todo el texto para obviar saltos de linea y bilingüismo
        full_text = "\n".join(lines)
        
        m_emi = re.search(r'(?:Issue date:|Fecha de emisi[oó]n\s*:)\s*(\d{4}\s*-\d{2}-\d{2})', full_text, re.IGNORECASE)
        if m_emi:
            # IRAM usa yyyy -mm-dd (a veces con espacio extra)
            result["fecha_emision"] = m_emi.group(1).replace(" ", "")
            
        m_vto = re.search(r'(?:Next surveillance activity due date:|Fecha de pr[oó]ximo seguimiento\s*:?)\s*(\d{4}\s*-\d{2}-\d{2})', full_text, re.IGNORECASE)
        if m_vto:
            result["fecha_vencimiento"] = m_vto.group(1).replace(" ", "")

        return result

    # ── Intertek Argentina ───────────────────────────────────

    def _extract_intertek(self, text_sorted: str, lines_unsorted: list[str]) -> dict:
        """
        Extrae datos de certificados Intertek Argentina (Esquema 2).
        Utiliza el texto ordenado por coordenadas para manejar el layout roto de Intertek.
        """
        if not text_sorted:
            return self._extract_cb(lines_unsorted)

        lines = [l.strip() for l in text_sorted.replace('\r\n', '\n').split('\n')]
        result = {"marca": "", "fabricante": "", "direccion": "",
                  "modelos": "", "specs": "", "producto_desc": "",
                  "fecha_emision": "", "fecha_vencimiento": "",
                  "fecha_inicio_tramite": ""}


        # Intertek Argentina usa un layout bilingüe: Etiqueta ES → Etiqueta EN → Valor
        # Helper: dada una posición i (label ES), saltea la label EN y devuelve el valor
        BILINGUAL_LABELS = {
            "product", "producto", "titular del certificado", "certificate holder",
            "fábrica / dirección", "fbrica / direccin", "factory / address",
            "características técnicas", "caractersticas tcnicas", "technical characteristics",
            "technical caracteristics",
            "marca comercial", "trade mark",
            "modelo o tipo", "model or type",
            "norma(s) aplicada(s)", "standard(s) used",
            "informe(s) de ensayo", "test report",
        }

        def _itk_get_val(lines: list[str], i: int) -> tuple[int, str]:
            """Retorna (offset, valor) de la primera línea de valor después de la/s etiquetas."""
            for offset in range(1, 4):
                j = i + offset
                if j >= len(lines):
                    break
                candidate = lines[j].strip()
                if not candidate:
                    continue
                low = candidate.lower().rstrip(':').rstrip('/')
                # Si la línea candidata también es una etiqueta conocida, seguir buscando
                if any(low.startswith(lbl) for lbl in BILINGUAL_LABELS):
                    continue
                return offset, candidate
            return 1, ""

        # Parse Intertek Argentina format layout
        for i, line in enumerate(lines):
            line_low = line.lower().rstrip(':').rstrip('/')

            # Producto
            if line_low.startswith("producto") and not result["producto_desc"]:
                off, val = _itk_get_val(lines, i)
                if val:
                    result["producto_desc"] = val

            # Titular del Certificado (holder/importador)
            elif line_low.startswith("titular del certificado") and not result.get("titular"):
                off, val = _itk_get_val(lines, i)
                if val:
                    result["titular"] = val

            # Fábrica / Dirección
            elif (line_low.startswith("fábrica / dirección") or line_low.startswith("fbrica / direccin")
                  or line_low.startswith("fábrica / direcci")) and not result["fabricante"]:
                off, val = _itk_get_val(lines, i)
                if val:
                    result["fabricante"] = val
                    # Dirección en la línea siguiente al valor
                    j = i + off + 1
                    if j < len(lines) and lines[j].strip():
                        result["direccion"] = lines[j].strip()

            # Specs
            elif (line_low.startswith("características técnicas") or line_low.startswith("caractersticas tcnicas")) and not result["specs"]:
                off, val = _itk_get_val(lines, i)
                if val:
                    result["specs"] = val

            # Marca
            elif (line_low.startswith("marca comercial")) and not result["marca"]:
                off, val = _itk_get_val(lines, i)
                if val:
                    result["marca"] = val

            # Modelos
            elif line_low.startswith("modelo o tipo") and not result["modelos"]:
                off, val = _itk_get_val(lines, i)
                model_lines = [val] if val else []
                j = i + off + 1
                while j < min(i + 15, len(lines)):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    nlow = next_line.lower()
                    if any(nlow.startswith(lbl) for lbl in BILINGUAL_LABELS):
                        break
                    if re.match(r'^[\dA-Z\(]', next_line):
                        model_lines.append(next_line)
                    else:
                        break
                    j += 1
                if model_lines:
                    result["modelos"] = " ".join([m for m in model_lines if m])

            # Fechas — cubrir TODAS las variantes de etiqueta Intertek (ES + EN)
            _DATE_RE = re.compile(r'(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})')
            # Si hay múltiples fechas (ej: revision), dar prioridad a la inicial si existe
            _INICIAL_KW = re.compile(
                r'(?:fecha\s*de\s*emisi[oó]n\s*inicial'
                r'|date\s*of\s*first\s*edition'
                r'|initial\s*issue)',
                re.IGNORECASE
            )
            _EMIS_KW = re.compile(
                r'(?:fecha\s*de\s*emisi[oó]n|issue\s*date|date\s*of\s*issue'
                r'|fecha\s*de\s*emision)',
                re.IGNORECASE
            )
            _VENC_KW = re.compile(
                r'(?:fecha\s*de\s*vencimiento|valid\s*(?:until|to|through)'
                r'|expir[ye]|vigencia\s*hasta)',
                re.IGNORECASE
            )
            
            # Chequeamos INICIAL primero para asegurarnos de que no sea sobrescrito accidentalmente si ambas están juntas
            if _INICIAL_KW.search(line):
                dm = _DATE_RE.search(line)
                if not dm and i + 1 < len(lines):
                    dm = _DATE_RE.search(lines[i + 1])
                if dm:
                    result["fecha_emision"] = dm.group(1)
                    self._log("info", f"[ITK] Fecha emisión (inicial): {dm.group(1)!r}")
            # Si todavía no hay fecha y encontramos una etiqueta de emisión común
            elif _EMIS_KW.search(line) and not result["fecha_emision"]:
                # Evitar capturar la de "revisión" si hay una inicial en algún lado? 
                # Con el sort_text de fitz, normalmente la inicial está primero así que result["fecha_emision"] ya va a estar lista.
                dm = _DATE_RE.search(line)
                if not dm and i + 1 < len(lines):
                    dm = _DATE_RE.search(lines[i + 1])
                if dm:
                    result["fecha_emision"] = dm.group(1)
                    self._log("info", f"[ITK] Fecha emisión: {dm.group(1)!r}")
            elif _VENC_KW.search(line) and not result["fecha_vencimiento"]:
                dm = _DATE_RE.search(line)
                if not dm and i + 1 < len(lines):
                    dm = _DATE_RE.search(lines[i + 1])
                if dm:
                    result["fecha_vencimiento"] = dm.group(1)
                    self._log("info", f"[ITK] Fecha vencimiento: {dm.group(1)!r}")

        # Fallback full-text si la pasada línea a línea no encontró fecha
        if not result["fecha_emision"]:
            _fb = re.search(
                r'(?:fecha\s*de\s*emisi[oó]n|issue\s*date|date\s*of\s*issue'
                r'|initial\s*issue|fecha\s*de\s*emision)'
                r'\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{4})',
                text_sorted, re.IGNORECASE
            )
            if _fb:
                result["fecha_emision"] = _fb.group(1)
                self._log("info", f"[ITK] Fecha emisión (fallback): {_fb.group(1)!r}")

        result["fecha_vencimiento"] = (
            result["fecha_vencimiento"]
            or self._calc_vencimiento(result["fecha_emision"])
        )
        result["fecha_inicio_tramite"] = self._calc_inicio_tramite(result["fecha_vencimiento"])

        # Fallback to generic CB if fundamental fields are missing
        if not result["producto_desc"] and not result["modelos"]:
            self._log("info", "Intertek Argentina extr. failed, falling back to CB Scheme variables")
            return self._extract_cb(lines_unsorted)

        self._log("info", f"Intertek extraído: marca={result['marca']}, fab={str(result['fabricante'])[:30]}  # type: ignore[index]")
        return result

    # ── Generic (fallback) ───────────────────────────────────

    def _extract_generic(self, lines: list[str]) -> dict:
        """
        Fallback genérico: intenta extraer con los labels más comunes.
        Usado cuando no se detecta ningún OEC conocido.
        """
        result = {"marca": "", "fabricante": "", "direccion": "",
                  "modelos": "", "specs": "", "producto_desc": "",
                  "fecha_emision": "", "fecha_vencimiento": "",
                  "fecha_inicio_tramite": ""}

        generic_skip = {
            "product", "producto", "trademark", "marca", "model",
            "modelo", "manufacturer", "fabricante", "factory", "fábrica",
            "address", "dirección", "ratings", "características",
            "additional information", "información adicional",
        }

        for label_set, key in [
            (["Trademark", "Marca"], "marca"),
            (["Product", "Producto"], "producto_desc"),
        ]:
            idx = self._find_line(lines, label_set)
            if idx >= 0:
                _, val = self._next_non_empty(lines, idx, generic_skip)
                if val:
                    result[key] = val

        # Fabricante
        idx = self._find_line(lines, [
            "Name and address of the manufacturer",
            "Nombre y dirección del fabricante",
            "Factory", "Fábrica",
        ])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, generic_skip)
            if val:
                result["fabricante"] = val

        # Modelos
        idx = self._find_line(lines, [
            "Model / Type Ref.", "Modelo / Referencia de Tipo",
            "Model", "Modelo",
        ])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, generic_skip)
            if val:
                items = [x.strip() for x in re.split(r'[;,]+', val) if x.strip()]
                result["modelos"] = ", ".join(items)

        # Specs
        idx = self._find_line(lines, [
            "Ratings and principal characteristics",
            "Valores nominales y características",
        ])
        if idx >= 0:
            _, val = self._next_non_empty(lines, idx, generic_skip)
            if val:
                result["specs"] = val

        # Fechas (intenta ambos idiomas)
        result["fecha_emision"] = self._find_date_after_label(
            lines, ["Fecha de emisión", "Date of issue", "Issued"])
        result["fecha_vencimiento"] = self._find_date_after_label(
            lines, ["Fecha de próxima vigilancia", "Valid until", "Expiry"])
        if not result["fecha_vencimiento"]:
            result["fecha_vencimiento"] = self._calc_vencimiento(result["fecha_emision"])
        result["fecha_inicio_tramite"] = self._calc_inicio_tramite(result["fecha_vencimiento"])

        self._log("info", f"Generic extraído: marca={result['marca']}, "
                  f"fab={str(result['fabricante'])[:30]}  # type: ignore[index], emision={result['fecha_emision']}")
        return result

    # ─── Export y Merge ─────────────────────────────────────

    def save_docx(self, doc: Document, output_path: str) -> str:
        """Guarda el documento Word."""
        doc.save(output_path)
        self._log("info", f"DJC Word guardada: {output_path}")
        return output_path

    def export_to_pdf(self, docx_path: str, pdf_path: Optional[str] = None) -> str:
        """
        Convierte Word a PDF usando docx2pdf (requiere MS Word instalado).
        
        Returns:
            Ruta al PDF generado.
        """
        if pdf_path is None:
            pdf_path = docx_path.replace(".docx", ".pdf")
        
        try:
            from docx2pdf import convert  # type: ignore[import-untyped]
            convert(docx_path, pdf_path)
            self._log("info", f"DJC PDF generado: {pdf_path}")
            return pdf_path
        except ImportError:
            self._log("error", "docx2pdf no instalado. Ejecutar: pip install docx2pdf")
            raise
        except Exception as e:
            self._log("error", f"Error convirtiendo a PDF: {e}")
            raise

    def _strip_old_djc(self, doc: fitz.Document):
        """
        Escanea las primeras páginas del certificado para detectar si es una DJC
        generada anteriormente (carátula) pegada al certificado real.
        Si la detecta, elimina esas primeras páginas para no volver a agregarlas.
        """
        pages_to_delete = []
        for i in range(min(3, len(doc))):
            page_text = doc[i].get_text("text").lower()
            # Patrones muy fuertes de que es nuestra propia DJC
            if "documento de justificación de conformidad" in page_text and \
               ("djc-" in page_text or "bidcom" in page_text or "gadnic" in page_text):
                pages_to_delete.append(i)
                self._log("info", f"[M3-Merge] Hoja {i+1} detectada como vieja DJC — se removerá.")
            elif pages_to_delete:
                # Si las anteriores eran DJC, pero esta ya no lo parece, detenemos el escaneo
                break
                
        if pages_to_delete:
            # Hay que borrarlas de atrás para adelante para no romper los índices
            for p in reversed(pages_to_delete):
                doc.delete_page(p)
            self._log("info", f"[M3-Merge] Removidas {len(pages_to_delete)} hoja(s) de DJC anterior.")

    def censor_cert_pdf(self, doc,
                        fabricante: str = "",
                        direccion: str = "",
                        preserve_words: Optional[list[str]] = None):
        """
        Censura el fabricante y la direccion de fabrica en el certificado PDF.

        Estrategia:
          1. Localiza la zona del campo con search_for() usando los primeros tokens unicos.
          2. Dentro de esa banda horizontal, extrae cada PALABRA con get_text('words').
          3. Agrupa palabras consecutivas que NO estan en preserve_words y las pinta de negro.
          4. Las palabras en preserve_words (ej. "China") se saltan y QUEDAN VISIBLES.
        """
        if preserve_words is None:
            preserve_words = [
                "China", "china", "Korea", "korea", "Taiwan", "taiwan",
                "Vietnam", "vietnam", "India", "india",
                "Japan", "Japon", "USA", "usa",
            ]

        BLACK  = (0, 0, 0)
        MARGIN = 0  # no margin to avoid stroke overlaps with tight words

        preserve_lower = {pw.lower() for pw in preserve_words}

        def _clean_word(w):
            return w.rstrip(".,;:.")

        def _should_preserve(word_text):
            return _clean_word(word_text).lower() in preserve_lower

        def _anchor_tokens(text, n=3):
            """Primeros n tokens de 5+ chars que no son preserve_words."""
            tokens = []
            for t in text.replace(",", " ").replace(".", " ").split():
                t = t.strip()
                if len(t) >= 5 and not _should_preserve(t):
                    tokens.append(t)
                    if len(tokens) >= n:
                        break
            return tokens

        def _censor_field(page, field_text, label):
            if not field_text or not field_text.strip():
                return 0

            anchors = _anchor_tokens(field_text)
            if not anchors:
                return 0

            # Buscar la zona con los primeros dos anchors
            _anchors_copy: list[str] = list(anchors)
            search_text = " ".join(_anchors_copy[:2]) if len(_anchors_copy) >= 2 else _anchors_copy[0]  # type: ignore[index]
            hit_rects = page.search_for(search_text, quads=False)

            if not hit_rects:
                hit_rects = page.search_for(anchors[0], quads=False)

            if not hit_rects:
                self._log("warning", f"[M3-Censor] '{label}' no encontrado en pag {page.number+1}.")
                return 0

            count = 0
            for zone in hit_rects:
                # Expandir horizontalmente al ancho de la pagina para capturar toda la linea
                band = fitz.Rect(zone.x0, zone.y0 - 2, page.rect.width, zone.y1 + 2)
                all_words = page.get_text("words", clip=band)
                if not all_words:
                    continue

                # Ordenar izq -> der
                all_words_sorted = sorted(all_words, key=lambda w: w[0])

                group_rect = None
                for word_entry in all_words_sorted:
                    word_text = word_entry[4]
                    wr = fitz.Rect(word_entry[:4])

                    if _should_preserve(word_text):
                        # Flush del grupo y dejar esta palabra libre
                        if group_rect is not None:
                            page.draw_rect(group_rect, color=None, fill=BLACK, width=0)
                            count += 1
                            group_rect = None
                    else:
                        inflated = fitz.Rect(
                            wr.x0 - MARGIN, wr.y0 - MARGIN,
                            wr.x1 + MARGIN, wr.y1 + MARGIN,
                        )
                        if group_rect is None:
                            group_rect = inflated
                        else:
                            assert group_rect is not None  # Help Pyre2
                            group_rect = fitz.Rect(
                                min(group_rect.x0, inflated.x0),
                                min(group_rect.y0, inflated.y0),
                                max(group_rect.x1, inflated.x1),
                                max(group_rect.y1, inflated.y1),
                            )

                if group_rect is not None:
                    page.draw_rect(group_rect, color=None, fill=BLACK, width=0)
                    count += 1

            return count

        total_rects = 0
        for page in doc:
            page_text = page.get_text("text").strip()
            if not page_text:
                self._log("warning",
                    f"[M3-Censor] Pag {page.number+1} es imagen pura, no se puede censurar.")
                continue

            total_rects += _censor_field(page, fabricante, "Fabricante")
            total_rects += _censor_field(page, direccion,  "Direccion")

        if total_rects > 0:
            self._log("info",
                f"[M3-Censor] {total_rects} bloque(s) censurados (preserve_words respetadas).")
        else:
            self._log("warning", "[M3-Censor] No se encontraron coincidencias de texto.")

        return doc


    def merge_pdfs(self, djc_pdf_path: str, cert_pdf_path: str, output_path: Optional[str] = None, extra_pdfs: Optional[list[str]] = None) -> str:
        """
        Combina DJC PDF + (opcionalmente Nota de Extensión u otros PDFs) + Certificado PDF.
        
        El certificado se RASTERIZA (cada página → imagen a 150 DPI) antes de
        agregarlo, para preservar las firmas digitales que se pierden en un
        merge directo de PDFs firmados.
        
        Args:
            djc_pdf_path:  Ruta al PDF de la DJC generada.
            cert_pdf_path: Ruta al PDF del certificado original.
            output_path:   (Opcional) Ruta de salida para el PDF combinado.
            extra_pdfs:    (Opcional) Lista de rutas a PDFs intermedios (ej. Nota de Extensión)
                           que se insertan ENTRE la DJC y el certificado, sin rasterizar.
        
        Returns:
            Ruta al PDF combinado.
        """
        if output_path is None:
            base = os.path.splitext(djc_pdf_path)[0]
            output_path = f"{base}_completo.pdf"
        
        merged = fitz.open()
        
        # 1. Insertar DJC directamente (es nuestro PDF, sin firmas digitales)
        if os.path.exists(djc_pdf_path):
            self._log("info", "[M3-Merge] Insertando DJC PDF...")
            src = fitz.open(djc_pdf_path)
            merged.insert_pdf(src)
            src.close()
        else:
            self._log("warning", f"[M3-Merge] DJC PDF no encontrado: {djc_pdf_path}")
        
        # 1b. Insertar PDFs intermedios (Nota de Extensión, etc.) sin rasterizar
        if extra_pdfs:
            for extra_path in extra_pdfs:
                if os.path.exists(extra_path):
                    self._log("info", f"[M3-Merge] Insertando PDF intermedio: {os.path.basename(extra_path)}")
                    extra_src = fitz.open(extra_path)
                    merged.insert_pdf(extra_src)
                    extra_src.close()
                else:
                    self._log("warning", f"[M3-Merge] PDF intermedio no encontrado: {extra_path}")
        
        # 2. Rasterizar el certificado para preservar la firma digital visual y aplicar OCR
        if os.path.exists(cert_pdf_path):
            self._log("info", "[M3-Merge] Rasterizando certificado (preserva firma digital + OCR)...")
            cert_src = fitz.open(cert_pdf_path)
            
            # 2a. Limpiar carátulas de DJC anteriores (recursividad)
            self._strip_old_djc(cert_src)
            
            n_pages = len(cert_src)
            self._log("info", f"[M3-Merge] Certificado procesará {n_pages} página(s)")
            
            # Detectar si pytesseract está instalado y configurado
            has_tesseract = False
            try:
                import pytesseract  # type: ignore[import-untyped]
                # En Windows, Tesseract a menudo no se agrega al PATH. Buscamos en variantes comunes:
                posibles_rutas = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    os.path.expanduser(r'~\AppData\Local\Tesseract-OCR\tesseract.exe'),
                    os.path.expanduser(r'~\Tesseract-OCR\tesseract.exe'),
                ]
                
                for ruta in posibles_rutas:
                    if os.path.exists(ruta):
                        pytesseract.pytesseract.tesseract_cmd = ruta
                        break
                        
                # Verificamos si tesseract está accesible
                pytesseract.get_tesseract_version()
                has_tesseract = True
            except Exception as e:
                self._log("warning", f"[M3-Merge] Tesseract no disponible ({e}). PDF final será imagen pura.")
                self._log("warning", "[M3-Merge] Para habilitar OCR, instalá Tesseract en C:\\Program Files\\Tesseract-OCR")
            
            for page_num in range(n_pages):
                page = cert_src[page_num]
                
                # Renderizar a ~200 DPI (2.0x escala)
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_bytes = pix.tobytes("png")
                
                inserted_ocr = False
                
                if has_tesseract:
                    try:
                        from PIL import Image  # type: ignore[import-untyped]
                        import io
                        
                        img_pil = Image.open(io.BytesIO(img_bytes))
                        # Generar PDF unitario con la imagen + capa de texto (lang español+inglés idealmente)
                        pdf_ocr_bytes = pytesseract.image_to_pdf_or_hocr(img_pil, extension='pdf', lang='spa+eng')
                        
                        ocr_doc = fitz.open("pdf", pdf_ocr_bytes)
                        # Creamos la página en blaco en el destino con el tamaño real (page.rect)
                        rect = page.rect
                        new_page = merged.new_page(width=rect.width, height=rect.height)
                        
                        # Dibujamos/escalamos la página de ocr_doc (de mayor resolución) 
                        # para que "encaje" en la página real que acabamos de crear.
                        new_page.show_pdf_page(rect, ocr_doc, 0)
                        
                        ocr_doc.close()
                        inserted_ocr = True
                        self._log("info", f"[M3-Merge] Página {page_num+1}/{n_pages}: OCR aplicado y escalado.")
                    except Exception as e:
                        self._log("warning", f"[M3-Merge] Página {page_num+1}: Error OCR ({e}), fallback a imagen.")
                
                # Fallback: OCR falló, está deshabilitado, o no hay Tesseract
                if not inserted_ocr:
                    rect = page.rect
                    new_page = merged.new_page(width=rect.width, height=rect.height)
                    new_page.insert_image(
                        fitz.Rect(0, 0, rect.width, rect.height),
                        stream=img_bytes,
                    )
                
                pix = None  # Liberar memoria
            
            cert_src.close()
            self._log("info", f"[M3-Merge] Certificado rasterizado: {n_pages} página(s) incluidas")
        else:
            self._log("warning", f"[M3-Merge] Certificado PDF no encontrado: {cert_pdf_path}")
        
        # 3. Guardar resultado
        try:
            merged.save(output_path)
        except Exception as e:
            if "Permission denied" in str(e) or "cannot remove file" in str(e):
                # Archivo abierto en visor PDF → usar nombre alternativo
                import time
                ts = int(time.time())
                alt_path = output_path.replace(".pdf", f"_{ts}.pdf")
                self._log("warning", f"[M3-Merge] PDF abierto, guardando como: {alt_path}")
                merged.save(alt_path)
                output_path = alt_path
            else:
                raise
        merged.close()
        
        self._log("info", f"[M3-Merge] ✓ PDF completo guardado: {os.path.basename(output_path)}")
        return output_path


    # ─── Utilidades ─────────────────────────────────────────

    def _generate_djc_link(self, cert_number: str) -> str:
        """Genera el enlace público de la DJC."""
        base = self.config.get("enlace_djc_base", "https://qr.gadnic.com/certifications/certificado-")
        # Extraer solo el número del certificado
        num_match = re.search(r"(\d+)", cert_number)
        if num_match:
            return f"{base}{num_match.group(1)}"
        return f"{base}{cert_number}"

    def _infer_product_description(self, json_data: dict) -> str:
        """Infiere la descripción del producto desde el tipo de intervención o specs."""
        tipo = json_data.get("tipo_intervencion", "")
        if tipo:
            return tipo
        
        specs = json_data.get("specs_tecnicas", "")
        if isinstance(specs, list) and specs:
            return specs[0][:50] if len(specs[0]) > 50 else specs[0]
        elif isinstance(specs, str) and specs:
            return str(specs)[:50]  # type: ignore[index]
        
        return ""

    def _parse_date(self, date_str: str) -> datetime:
        """Parsea una fecha en formatos comunes."""
        formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"Formato de fecha no reconocido: {date_str}")

    def calculate_dates(self, fecha_emision: str, fecha_vencimiento: str = "") -> dict:
        """
        Calcula las fechas derivadas para el panel de info.
        
        Returns:
            dict con: fecha_inicio, fecha_vencimiento, fecha_inicio_tramite
        """
        result = {
            "fecha_inicio": fecha_emision,
            "fecha_vencimiento": fecha_vencimiento,
            "fecha_inicio_tramite": "",
        }
        
        # Si no hay vencimiento, calcular como emisión + 2 años
        if not fecha_vencimiento and fecha_emision:
            try:
                fe = self._parse_date(fecha_emision)
                venc = fe + timedelta(days=730)
                result["fecha_vencimiento"] = venc.strftime("%d/%m/%Y")
            except ValueError:
                pass
        
        # Calcular inicio de trámite = vencimiento - 3 meses
        if result["fecha_vencimiento"]:
            try:
                fv = self._parse_date(result["fecha_vencimiento"])
                inicio_tramite = fv - timedelta(days=90)
                result["fecha_inicio_tramite"] = inicio_tramite.strftime("%d/%m/%Y")
            except ValueError:
                pass
        
        return result

    def get_reglamento_options(self) -> list:
        """Retorna la lista de reglamentos disponibles para dropdown."""
        return self.config.get("reglamento_options", [])

    def get_esquema_options(self) -> list:
        """Retorna la lista de esquemas de certificación."""
        return self.config.get("esquema_options", [])

    def get_oec_options(self) -> dict:
        """Retorna las opciones de OEC."""
        return self.config.get("oec_options", {})


# ─────────────────────────────────────────────────────────────
#  CLI para testing rápido
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    gen = DJCGenerator()
    
    if len(sys.argv) > 1:
        cert_path = sys.argv[1]
        print(f"Extrayendo datos de: {cert_path}")
        cert_data = gen.extract_cert_data(cert_path)
        
        print(f"\n  Cert Number: {cert_data['cert_number']}")
        print(f"  Normas:      {cert_data['normas']}")
        print(f"  Emisión:     {cert_data['fecha_emision']}")
        print(f"  Vencimiento: {cert_data['fecha_vencimiento']}")
        print(f"  OEC:         {cert_data['oec_key']}")
        
        reglamento = gen.detect_reglamento(cert_data["normas"])
        print(f"  Reglamento:  {reglamento}")
    else:
        print("Uso: python m3_djc_generator.py <cert.pdf>")
        print("\nReglamentos disponibles:")
        for r in gen.get_reglamento_options():
            print(f"  • {r}")
