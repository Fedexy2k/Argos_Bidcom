"""
Extractor para certificados IRAM.

Etiquetas bilingüísticas características:
  EMPRESA BENEFICIARIA...       → Titular
  DOMICILIO DE LA(S) PLANTA(S)  → Fábrica + Dirección
  PRODUCTO / PRODUCT
  REFERENCIA DE TIPO O MODELO / TYPE REFERENCE OR MODEL
  CARACTERÍSTICAS PRINCIPALES / MAIN CHARACTERISTICS
  MARCA / TRADE MARK OR NAME
"""
from __future__ import annotations

import re
from modules.extractors.base import empty_result
from modules.extractors.shared import (
    find_line, next_non_empty,
    calc_vencimiento, calc_inicio_tramite,
)


def extract(lines: list[str], text_sorted: str = "", log_fn=None) -> dict:
    """Extrae datos de certificados IRAM."""
    result = empty_result()

    # 1. Fábrica y Dirección
    idx = find_line(lines, [
        "DOMICILIO DE LA(S) PLANTA(S) DE PRODUCCIÓN SUJETA(S) A INSPECCIÓN / ADDRESS(ES) OF THE PRODUCTION PLANT(S) UNDER INSPECTION",
        "PLANTA ELABORADORA / FACTORY",
    ])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, skip_labels={"PRODUCTO / PRODUCT"})
        if val:
            parts = val.split(" / ")
            if len(parts) >= 2:
                result["fabricante"] = parts[0].strip()
                result["direccion"] = " / ".join(parts[1:]).strip()
            else:
                result["fabricante"] = val
                _, next_val = next_non_empty(lines, idx + 1, skip_labels={"PRODUCTO / PRODUCT"})
                if next_val and len(next_val) > 10:
                    result["direccion"] = next_val

    # 2. Producto
    idx = find_line(lines, ["PRODUCTO / PRODUCT", "PRODUCTO:"])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, skip_labels={"REFERENCIA DE TIPO O MODELO / TYPE REFERENCE OR MODEL"})
        if val:
            result["producto_desc"] = val.split(" / ")[0].strip() if " / " in val else val

    # 3. Modelos
    idx = find_line(lines, ["REFERENCIA DE TIPO O MODELO / TYPE REFERENCE OR MODEL"])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, skip_labels={"CARACTERÍSTICAS PRINCIPALES / MAIN CHARACTERISTICS"})
        if val:
            result["modelos"] = val

    # 4. Specs
    idx = find_line(lines, ["CARACTERÍSTICAS PRINCIPALES / MAIN CHARACTERISTICS"])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, skip_labels={"MARCA / TRADE MARK OR NAME"})
        if val:
            result["specs"] = val

    # 5. Marca
    idx = find_line(lines, ["MARCA / TRADE MARK OR NAME"])
    if idx >= 0:
        _, val = next_non_empty(lines, idx, skip_labels={"EN CONFORMIDAD CON LA(S) NORMA(S) / IN CONFORMITY WITH THE STANDARD(S)"})
        if val:
            result["marca"] = re.sub(r'[\'\""]', '', val).strip()

    # 6. Normas — label completo bilingüe con slash
    idx = find_line(lines, [
        "EN CONFORMIDAD CON LA(S) NORMA(S) / IN CONFORMITY WITH THE STANDARD(S)",
        "EN CONFORMIDAD CON LA(S) NORMA(S) / IN CONFORMITY WITH THE STANDARD(S):",
        "IN CONFORMITY WITH THE STANDARD(S)",
    ])
    if idx >= 0:
        normas_lines = []
        j = idx + 1
        while j < len(lines):
            val = lines[j].strip()
            if not val:
                break
            low = val.lower()
            if low.startswith("esta certificacion") or low.startswith("this iram") or low.startswith("fecha") or low.startswith("issue"):
                break
            normas_lines.append(val)
            j += 1
        if normas_lines:
            result["normas"] = " ".join(normas_lines)

    # 7. Fechas — regex sobre todo el texto (ignora saltos de línea y bilingüismo)
    full_text = "\n".join(lines)

    m_emi = re.search(
        r'(?:Issue date:|Fecha de emisi[oó]n\s*:)\s*(\d{4}\s*-\d{2}-\d{2})',
        full_text, re.IGNORECASE
    )
    if m_emi:
        result["fecha_emision"] = m_emi.group(1).replace(" ", "")

    m_vto = re.search(
        r'(?:Next surveillance activity due date:|Fecha de pr[oó]ximo seguimiento\s*:?)\s*(\d{4}\s*-\d{2}-\d{2})',
        full_text, re.IGNORECASE
    )
    if m_vto:
        result["fecha_vencimiento"] = m_vto.group(1).replace(" ", "")

    if not result["fecha_vencimiento"]:
        result["fecha_vencimiento"] = calc_vencimiento(result["fecha_emision"])
    result["fecha_inicio_tramite"] = calc_inicio_tramite(result["fecha_vencimiento"])

    if log_fn:
        log_fn("info", f"IRAM extraído: marca={result['marca']}, fab={str(result['fabricante'])[:30]}")
    return result
