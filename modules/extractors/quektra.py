"""
Extractor para certificados Quektra (Q-AR-XXXXX).

Estructura conocida (bilingüe):
  Producto / Product → descripción
  Nombre y dirección del fabricante → fab name → dir
  Valores nominales y características principales → specs
  Marca / Trademark → marca
  Modelo / Referencia de Tipo → modelos (separados por ';')
"""
from __future__ import annotations

import re
from modules.extractors.base import empty_result
from modules.extractors.shared import (
    find_line, next_non_empty, find_date_after_label,
    calc_vencimiento, calc_inicio_tramite,
)

BILINGUAL_SKIP = {
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
    "battery charger for cordless drill",
}


def extract(lines: list[str], text_sorted: str = "", log_fn=None) -> dict:
    """Extrae datos de certificados Quektra."""
    result = empty_result()

    # ── PRODUCTO ──
    idx = find_line(lines, ["Producto"])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, BILINGUAL_SKIP)
        if val:
            result["producto_desc"] = val

    # ── FABRICANTE + DIRECCIÓN ──
    idx = find_line(lines, ["Nombre y dirección del fabricante"])
    if idx >= 0:
        _, fab_name = next_non_empty(lines, idx, BILINGUAL_SKIP)
        if fab_name:
            result["fabricante"] = fab_name
            fab_name_idx = find_line(lines, [fab_name], start=idx)
            if fab_name_idx >= 0 and fab_name_idx + 1 < len(lines):
                addr = lines[fab_name_idx + 1].strip()
                if addr:
                    result["direccion"] = addr

    # ── SPECS ──
    idx = find_line(lines, ["Valores nominales y características"])
    if idx >= 0:
        specs_lines = []
        j = idx + 1
        while j < len(lines):
            val = lines[j].strip()
            if not val:
                break
            low = val.rstrip(':').lower()
            if low in BILINGUAL_SKIP:
                j += 1
                continue
            if re.match(r'^[A-Z]{2,5}-\d+\s+[A-Z]\d', val):
                j += 1
                continue
            specs_lines.append(val)
            j += 1
        if specs_lines:
            result["specs"] = "; ".join(specs_lines)

    # ── MARCA ──
    idx = find_line(lines, ["Marca"])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, BILINGUAL_SKIP)
        if val:
            result["marca"] = val

    # ── MODELOS ──
    idx = find_line(lines, ["Modelo / Referencia de Tipo"])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, BILINGUAL_SKIP)
        if val:
            items = [x.strip() for x in re.split(r'[;,]+', val) if x.strip()]
            result["modelos"] = ", ".join(items)

    # ── NORMAS ──
    # En certs Quektra el label es "En conformidad con" / "In conformity with"
    idx = find_line(lines, ["En conformidad con", "In conformity with", "In confortmity with"])
    if idx >= 0:
        normas_lines = []
        j = idx + 1
        while j < len(lines):
            val = lines[j].strip()
            if not val:
                break
            low = val.rstrip(':').lower()
            # Saltar el label bilingüe
            if low.startswith("in con") or low.startswith("en con"):
                j += 1
                continue
            if low in BILINGUAL_SKIP:
                break
            normas_lines.append(val)
            j += 1
        if normas_lines:
            result["normas"] = " ".join(normas_lines)

    # ── FECHAS ──
    result["fecha_emision"] = find_date_after_label(lines, ["Fecha de emisión"])
    result["fecha_vencimiento"] = calc_vencimiento(result["fecha_emision"])
    result["fecha_inicio_tramite"] = calc_inicio_tramite(result["fecha_vencimiento"])

    if log_fn:
        log_fn("info", f"Qetkra extraído: marca={result['marca']}, fab={str(result['fabricante'])[:30]}, emision={result['fecha_emision']}")
    return result
