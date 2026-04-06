"""
Extractor genérico (fallback).
Intenta extraer con los labels más comunes.
Usado cuando no se detecta ningún OEC conocido.
"""
from __future__ import annotations

import re
from modules.extractors.base import empty_result
from modules.extractors.shared import (
    find_line, next_non_empty, find_date_after_label,
    calc_vencimiento, calc_inicio_tramite,
)

GENERIC_SKIP = {
    "product", "producto", "trademark", "marca", "model",
    "modelo", "manufacturer", "fabricante", "factory", "fábrica",
    "address", "dirección", "ratings", "características",
    "additional information", "información adicional",
}


def extract(lines: list[str], text_sorted: str = "", log_fn=None) -> dict:
    """Extractor genérico (fallback)."""
    result = empty_result()

    # Marca y Producto
    for label_set, key in [
        (["Trademark", "Marca"], "marca"),
        (["Product", "Producto"], "producto_desc"),
    ]:
        idx = find_line(lines, label_set)
        if idx >= 0:
            _, val = next_non_empty(lines, idx, GENERIC_SKIP)
            if val:
                result[key] = val

    # Fabricante
    idx = find_line(lines, [
        "Name and address of the manufacturer",
        "Nombre y dirección del fabricante",
        "Factory", "Fábrica",
    ])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, GENERIC_SKIP)
        if val:
            result["fabricante"] = val

    # Modelos
    idx = find_line(lines, [
        "Model / Type Ref.", "Modelo / Referencia de Tipo",
        "Model", "Modelo",
    ])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, GENERIC_SKIP)
        if val:
            items = [x.strip() for x in re.split(r'[;,]+', val) if x.strip()]
            result["modelos"] = ", ".join(items)

    # Specs
    idx = find_line(lines, [
        "Ratings and principal characteristics",
        "Valores nominales y características",
    ])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, GENERIC_SKIP)
        if val:
            result["specs"] = val

    # Fechas
    result["fecha_emision"] = find_date_after_label(
        lines, ["Fecha de emisión", "Date of issue", "Issued"])
    result["fecha_vencimiento"] = find_date_after_label(
        lines, ["Fecha de próxima vigilancia", "Valid until", "Expiry"])
    if not result["fecha_vencimiento"]:
        result["fecha_vencimiento"] = calc_vencimiento(result["fecha_emision"])
    result["fecha_inicio_tramite"] = calc_inicio_tramite(result["fecha_vencimiento"])

    if log_fn:
        log_fn("info", f"Generic extraído: marca={result['marca']}, fab={str(result['fabricante'])[:30]}, emision={result['fecha_emision']}")
    return result
