"""
modules/extractors/dispatcher.py
=================================
Detecta el OEC del texto del certificado y delega al extractor correcto.
"""
from __future__ import annotations

import logging
import os
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Keywords para detección de OEC (orden de prioridad)
# NOTA: se aplica .lower() al texto antes de comparar, así que las keys deben ser minúsculas.
OEC_KEYWORDS: dict[str, str] = {
    "q-ar":           "Quektra",
    "quektra":        "Quektra",
    "qetkra":         "Quektra",
    "intertek":       "Intertek",
    "bureau veritas": "Bureau Veritas",
    "bv ":            "Bureau Veritas",
    "tüv":            "TÜV",
    "tuv":            "TÜV",
    "lenor group":    "Lenor",   # variante "Lenor Group"
    "lenorgroup":     "Lenor",   # variante sin espacio (sitio web)
    "lenor":          "Lenor",   # keyword base
    "iram":           "IRAM",
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
        result = quektra.extract(lines, text_sorted, log_fn)

    elif oec_key == "Lenor":
        _log("info", "[M3] Usando extractor LENOR")
        from modules.extractors import lenor
        result = lenor.extract(lines, text_sorted, log_fn)

    elif oec_key == "Intertek":
        _log("info", "[M3] Usando extractor INTERTEK ARGENTINA")
        from modules.extractors import intertek
        result = intertek.extract(lines, text_sorted, log_fn)

    elif oec_key in ("Bureau Veritas", "TÜV"):
        _log("info", f"[M3] Usando extractor CB SCHEME ({oec_key})")
        from modules.extractors import cb_scheme
        result = cb_scheme.extract(lines, text_sorted, log_fn)

    elif oec_key == "IRAM":
        _log("info", "[M3] Usando extractor IRAM")
        from modules.extractors import iram
        result = iram.extract(lines, text_sorted, log_fn)

    else:
        _log("warning", "[M3] OEC no reconocido — usando extractor GENÉRICO")
        from modules.extractors import generic
        result = generic.extract(lines, text_sorted, log_fn)

    # ── Log de resultado del extractor regex ──────────────────────────────────
    CRITICAL_FIELDS = ["fabricante", "marca", "modelos", "specs", "producto_desc",
                       "direccion", "fecha_emision"]
    regex_found   = [f for f in CRITICAL_FIELDS if result.get(f)]
    regex_missing = [f for f in CRITICAL_FIELDS if not result.get(f)]
    _log("info", f"[M3] Regex → encontrados: {regex_found or '(ninguno)'}")
    if regex_missing:
        _log("info", f"[M3] Regex → vacíos:      {regex_missing}")

    # ── Detectar si es certificado VERSION SIMPLIFICADA / CODIFICADA ──────────
    # En estos casos, si fabricante/dirección ya tienen un valor (aunque sea
    # un código como 'AAB382'), se respeta y NO se manda a Gemini.
    # Si están vacíos, algo falló en la lectura → sí se manda a Gemini.
    text_lower = text.lower()
    is_simplificado = any(kw in text_lower for kw in [
        "version simplificada", "versión simplificada",
        "version reducida",     "versión reducida",       # Intertek IACSA usa esta frase
        "simplificada", "codificada", "simplified version", "reduced version",
        "disposición 1/24", "disposicion 1/24",            # referencia legal en cert simplificado
    ])
    if is_simplificado:
        _log("info", "[M3] Certificado SIMPLIFICADO/CODIFICADO detectado")
        if result.get("fabricante") and "fabricante" in regex_missing:
            regex_missing.remove("fabricante")
            _log("info", f"[M3]   fabricante='{result['fabricante']}' (código de cert) — NO se envía a Gemini")
        
        # En certs codificados, la dirección real no figura. Asignamos "China" por defecto.
        if not result.get("direccion"):
            result["direccion"] = "China"
            if "direccion" in regex_missing:
                regex_missing.remove("direccion")
            _log("info", "[M3]   direccion asignada por defecto a 'China' (cert simplificado)")

    # ── Contexto OEC para IA (cargado una vez, pasado a ambas llamadas) ─────────
    api_key = os.getenv("GEMINI_API_KEY")
    text_disponible = bool(text.strip())
    oec_ctx = ""
    if api_key:
        try:
            from modules.ai_helper import load_oec_context
            oec_ctx = load_oec_context(oec_key)
            if oec_ctx:
                _log("info", f"[M3] Contexto OEC cargado: {oec_key}")
        except Exception:
            pass

    # ── PASO 1: Fallback IA — completar campos vacíos ──────────────────────────

    if regex_missing:
        if api_key:
            if not text_disponible:
                _log("warning",
                     f"[M3] Campos vacíos {regex_missing} — texto del cert VACÍO, "
                     "Gemini no puede extraer (PDF escaneado sin OCR?)")
            else:
                _log("info", f"[M3] Paso 1 — Gemini completando campos vacíos: {regex_missing}")
                try:
                    from modules.ai_helper import fill_missing_fields_ai
                    filled = fill_missing_fields_ai(
                        cert_text=text,
                        missing_fields=regex_missing,
                        api_key=api_key,
                        log_fn=log_fn,
                        oec_context=oec_ctx,
                    )
                    ai_filled = []
                    ai_empty  = []
                    for field, value in filled.items():
                        if value and not result.get(field):
                            result[field] = value
                            ai_filled.append(f"{field}='{value[:40]}'")
                        else:
                            ai_empty.append(field)
                    if ai_filled:
                        _log("info",  f"[M3] Gemini → completó: {', '.join(ai_filled)}")
                    if ai_empty:
                        _log("warning", f"[M3] Gemini → no encontró: {ai_empty}")
                except Exception as e:
                    _log("warning", f"[M3] Error en fallback IA: {e}")
        else:
            _log("warning", f"[M3] Campos vacíos {regex_missing} — GEMINI_API_KEY no configurada")
    else:
        _log("info", "[M3] Todos los campos críticos detectados por regex")

    # ── PASO 2: Revisión semántica — Gemini verifica que todo sea correcto ──────
    # Corre SIEMPRE (no solo cuando hay campos vacíos) para detectar valores
    # mal asignados, truncados o incorrectos aunque el regex haya "encontrado algo".
    if api_key and text_disponible:
        try:
            from modules.ai_helper import review_extraction_ai
            campos_para_revisar = {
                "cert_number":   result.get("cert_number", ""),
                "normas":        result.get("normas", ""),
                "marca":         result.get("marca", ""),
                "fabricante":    result.get("fabricante", ""),
                "direccion":     result.get("direccion", ""),
                "modelos":       result.get("modelos", ""),
                "specs":         result.get("specs", ""),
                "producto_desc": result.get("producto_desc", ""),
                "fecha_emision": result.get("fecha_emision", ""),
            }
            # En certs simplificados/codificados el fabricante y dirección son
            # códigos legales (ej: 'TCSE-IACSA-0146/324.1 - F40.') — NO deben
            # ser sobreescritos por Gemini (que confundiría el laboratorio con el fabricante).
            campos_bloqueados_ia: list[str] = []
            if is_simplificado:
                campos_bloqueados_ia = ["fabricante", "direccion"]
                _log("info", "[M3] Reviewer IA: fabricante/dirección bloqueados (cert simplificado)")

            reviewed = review_extraction_ai(
                cert_text=text,
                extracted=campos_para_revisar,
                api_key=api_key,
                log_fn=log_fn,
                locked_fields=campos_bloqueados_ia,
                oec_context=oec_ctx,
            )
            # Aplicar solo mejoras (nunca vaciar un campo existente, nunca tocar bloqueados)
            for field, new_val in reviewed.items():
                if field in campos_bloqueados_ia:
                    continue
                if new_val and new_val != result.get(field, ""):
                    result[field] = new_val
        except Exception as e:
            _log("warning", f"[M3] Error en revisión semántica IA: {e}")

    return result
