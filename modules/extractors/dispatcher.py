"""
modules/extractors/dispatcher.py
=================================
Detecta el OEC del texto del certificado y delega al extractor correcto.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Keywords para detección de OEC (orden de prioridad)
OEC_KEYWORDS: dict[str, str] = {
    "q-ar":         "Quektra",
    "quektra":      "Quektra",
    "qetkra":       "Quektra",
    "intertek":     "Intertek",
    "bureau veritas": "Bureau Veritas",
    "bv ":          "Bureau Veritas",
    "tüv":          "TÜV",
    "tuv":          "TÜV",
    "lenor":        "Lenor",
    "iram":         "IRAM",
}


def detect_oec(cert_text: str, log_fn: Optional[Callable] = None) -> str:
    """
    Auto-detecta el Organismo de Evaluación de Conformidad desde el texto del certificado.

    Returns:
        Key del OEC (ej: "Lenor", "Quektra") o cadena vacía.
    """
    if not cert_text:
        return ""

    text_lower = cert_text.lower()
    for keyword, oec_key in OEC_KEYWORDS.items():
        if keyword in text_lower:
            if log_fn:
                log_fn("info", f"OEC detectado: {oec_key}")
            else:
                logger.info(f"OEC detectado: {oec_key}")
            return oec_key

    if log_fn:
        log_fn("warning", "No se detectó OEC en el certificado")
    else:
        logger.warning("No se detectó OEC en el certificado")
    return ""


def extract_product_data(
    text: str,
    text_sorted: str = "",
    oec_key: str = "",
    log_fn: Optional[Callable] = None,
) -> dict:
    """
    Dispatcher principal: delega la extracción al módulo correcto según el OEC.

    Args:
        text:       Texto completo del certificado (unsorted).
        text_sorted: Texto ordenado por coordenadas (PyMuPDF sort=True).
        oec_key:    OEC ya detectado (si vacío, se auto-detecta).
        log_fn:     Función de logging (level: str, msg: str).

    Returns:
        dict con claves: marca, fabricante, direccion, modelos, specs,
        producto_desc, fecha_emision, fecha_vencimiento, fecha_inicio_tramite.
    """
    def _log(level: str, msg: str):
        if log_fn:
            log_fn(level, msg)
        else:
            getattr(logger, level, logger.info)(msg)

    if not oec_key:
        oec_key = detect_oec(text, log_fn)

    lines = [l.strip() for l in text.replace('\r\n', '\n').split('\n')]
    _log("info", f"[M3] Despachando extractor para OEC='{oec_key or 'Desconocido'}'")

    if oec_key == "Quektra":
        _log("info", "[M3] Usando extractor QUEKTRA")
        from modules.extractors import quektra
        return quektra.extract(lines, text_sorted, log_fn)

    elif oec_key == "Lenor":
        _log("info", "[M3] Usando extractor LENOR")
        from modules.extractors import lenor
        return lenor.extract(lines, text_sorted, log_fn)

    elif oec_key == "Intertek":
        _log("info", "[M3] Usando extractor INTERTEK ARGENTINA")
        from modules.extractors import intertek
        return intertek.extract(lines, text_sorted, log_fn)

    elif oec_key in ("Bureau Veritas", "TÜV"):
        _log("info", f"[M3] Usando extractor CB SCHEME ({oec_key})")
        from modules.extractors import cb_scheme
        return cb_scheme.extract(lines, text_sorted, log_fn)

    elif oec_key == "IRAM":
        _log("info", "[M3] Usando extractor IRAM")
        from modules.extractors import iram
        return iram.extract(lines, text_sorted, log_fn)

    else:
        _log("warning", "[M3] OEC no reconocido — usando extractor GENÉRICO")
        from modules.extractors import generic
        return generic.extract(lines, text_sorted, log_fn)
