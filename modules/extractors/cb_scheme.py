"""
Extractor para certificados CB Scheme (TÜV, Bureau Veritas).
"""
from __future__ import annotations

import re
from datetime import datetime
from modules.extractors.base import empty_result
from modules.extractors.shared import (
    find_line, next_non_empty, find_date_after_label,
    calc_vencimiento, calc_inicio_tramite,
)

CB_SKIP = {
    "trademark", "brand", "model", "type reference",
    "model / type ref.", "name and address of the manufacturer",
    "name and address of the factory",
    "name and address of the applicant",
    "ratings and principal characteristics",
    "product", "additional information",
}


def extract(lines: list[str], text_sorted: str = "", log_fn=None) -> dict:
    """Extrae datos de certificados CB Scheme (TÜV, Bureau Veritas)."""
    result = empty_result()
    detect_lines = lines

    sorted_lines_for_dates: list[str] = []
    if text_sorted:
        sorted_lines_for_dates = [l.strip() for l in text_sorted.replace('\r\n', '\n').split('\n')]

    # ── MARCA ──
    for i, line in enumerate(detect_lines):
        lower = line.rstrip(':').lower()
        if lower.startswith('trademark') or lower.startswith('brand'):
            _, val = next_non_empty(detect_lines, i, CB_SKIP)
            if val:
                result["marca"] = val
            break

    # ── MODELOS ──
    idx = find_line(detect_lines, ["Model / Type Ref.", "Model"])
    if idx >= 0:
        _, val = next_non_empty(detect_lines, idx, CB_SKIP)
        if val:
            items = [x.strip() for x in re.split(r'[;,]+', val) if x.strip()]
            result["modelos"] = ", ".join(items)

    # ── FABRICANTE + DIRECCIÓN ──
    idx = find_line(detect_lines, [
        "Name and address of the manufacturer",
        "Name and address of the factory",
    ])
    if idx >= 0:
        _, fab_name = next_non_empty(detect_lines, idx, CB_SKIP)
        if fab_name:
            result["fabricante"] = fab_name
            fab_line = find_line(detect_lines, [fab_name], start=idx)
            if fab_line >= 0 and fab_line + 1 < len(detect_lines):
                addr = detect_lines[fab_line + 1].strip()
                if addr:
                    result["direccion"] = addr

    # ── PRODUCTO ──
    idx = find_line(detect_lines, ["Product"])
    if idx >= 0:
        _, val = next_non_empty(detect_lines, idx, CB_SKIP)
        if val:
            result["producto_desc"] = val

    # ── SPECS ──
    idx = find_line(detect_lines, ["Ratings and principal characteristics", "Ratings"])
    if idx >= 0:
        _, val = next_non_empty(detect_lines, idx, CB_SKIP)
        if val:
            result["specs"] = val

    # ── NORMAS ──
    # En CB certs el formato es: "...found to be in conformity with\n IEC 62368-1:2018"
    # No está en el inicio de línea, así que buscamos substring en vez de startswith
    for i, line in enumerate(detect_lines):
        low = line.lower()
        if "conformity with" in low or ("standard" in low and "used" in low):
            # El valor puede estar en la misma línea o en la siguiente
            inline_match = re.search(r'(?:conformity with|standard[s]? used)\s+([A-Z][^\n]+)', line, re.IGNORECASE)
            if inline_match:
                result["normas"] = inline_match.group(1).strip()
            elif i + 1 < len(detect_lines):
                next_line = detect_lines[i + 1].strip()
                if next_line and re.match(r'^[A-Z]{2,5}[\s\-]?\d', next_line):
                    result["normas"] = next_line
            break

    # ── FECHAS ──
    iso_date_re = re.compile(r'(\d{4}-\d{2}-\d{2})')
    result["fecha_emision"] = find_date_after_label(
        detect_lines, ["Date of issue", "Fecha de emisión", "Issued"])
    result["fecha_vencimiento"] = find_date_after_label(
        detect_lines, ["Valid until", "Expiry", "Valid to", "Fecha de próxima vigilancia"])

    # Fallback: buscar fecha ISO en líneas sorted
    if not result["fecha_emision"]:
        search_lines = sorted_lines_for_dates if sorted_lines_for_dates else detect_lines
        for line in search_lines:
            if 'signature' in line.lower() or 'date:' in line.lower():
                m = iso_date_re.search(line)
                if m:
                    try:
                        dt = datetime.strptime(m.group(1), '%Y-%m-%d')
                        result["fecha_emision"] = dt.strftime('%d/%m/%Y')
                    except ValueError:
                        pass
                    break

    if not result["fecha_vencimiento"]:
        result["fecha_vencimiento"] = calc_vencimiento(result["fecha_emision"])
    result["fecha_inicio_tramite"] = calc_inicio_tramite(result["fecha_vencimiento"])

    if log_fn:
        log_fn("info", f"CB extraído: marca={result['marca']}, fab={str(result['fabricante'])[:30]}, emision={result['fecha_emision']}")
    return result
