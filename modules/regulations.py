"""
modules/regulations.py
======================
Lógica de detección de reglamentos aplicables según normas técnicas.
Centraliza NORM_REGLAMENTO_MAP y PRODUCT_TYPE_OVERRIDES.
"""
from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
#  Mapeo norma → reglamento
#  Cada entrada: (lista keywords regex, reglamento display string)
#  Se evalúan en orden; la primera coincidencia gana.
# ─────────────────────────────────────────────────────────────

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
    # --- Res 16/2025 Ap. III – Iluminación ---
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
    # --- Res 16/2025 Ap. IV – Electrónica ---
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
    # --- Res 163/2004 – Juguetes ---
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
    "fuente":        "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
    "cargador":      "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
    "adaptador":     "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
    "power supply":  "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
    "charger":       "Res. SIyC Nº 16/2025 – Ap. I (Fuentes y Cargadores)",
}


def detect_reglamento(
    normas_text: str,
    producto_desc: str = "",
    log_fn=None,
) -> str:
    """
    Auto-detecta el reglamento aplicable a partir de las normas del certificado.

    Args:
        normas_text:   Texto de normas técnicas del certificado.
        producto_desc: Descripción del producto (para desempate).
        log_fn:        Función opcional de logging (level: str, msg: str).

    Returns:
        String del reglamento detectado o cadena vacía si no se detectó.
    """
    def _log(level: str, msg: str):
        if log_fn:
            log_fn(level, msg)
        else:
            getattr(logger, level, logger.info)(msg)

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
                    for prod_kw, override in PRODUCT_TYPE_OVERRIDES.items():
                        if prod_kw in prod_lower:
                            _log("info", f"Desempate: producto '{producto_desc}' → {override}")
                            return override

                _log("info", f"Reglamento detectado: {detected}")
                return str(detected)

    _log("warning", f"No se detectó reglamento para normas: {str(normas_text)[:80]}")
    return ""
