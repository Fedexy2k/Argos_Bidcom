"""
Extractor para certificados Intertek Argentina (Esquema 2).
Utiliza el texto ordenado por coordenadas (sort=True en PyMuPDF)
para manejar el layout roto de multi-columna de Intertek.
"""
from __future__ import annotations

import re
from modules.extractors.base import empty_result
from modules.extractors.shared import (
    calc_vencimiento, calc_inicio_tramite,
)
import modules.extractors.cb_scheme as cb_scheme

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
    """Retorna (offset, valor) de la primera línea de valor después de las etiquetas."""
    for offset in range(1, 4):
        j = i + offset
        if j >= len(lines):
            break
        candidate = lines[j].strip()
        if not candidate:
            continue
        low = candidate.lower().rstrip(':').rstrip('/')
        if any(low.startswith(lbl) for lbl in BILINGUAL_LABELS):
            continue
        return offset, candidate
    return 1, ""


def extract(lines_unsorted: list[str], text_sorted: str = "", log_fn=None) -> dict:
    """Extrae datos de certificados Intertek Argentina."""
    if not text_sorted:
        return cb_scheme.extract(lines_unsorted, "", log_fn)

    lines = [l.strip() for l in text_sorted.replace('\r\n', '\n').split('\n')]
    result = empty_result()

    _DATE_RE = re.compile(r'(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})')
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

    for i, line in enumerate(lines):
        line_low = line.lower().rstrip(':').rstrip('/')

        # Producto
        if line_low.startswith("producto") and not result["producto_desc"]:
            _, val = _itk_get_val(lines, i)
            if val:
                result["producto_desc"] = val

        # Titular del Certificado (importador — NO es el fabricante)
        elif line_low.startswith("titular del certificado") and not result.get("titular"):
            _, val = _itk_get_val(lines, i)
            if val:
                result["titular"] = val  # type: ignore[assignment]

        # Fábrica / Dirección
        elif (line_low.startswith("fábrica / dirección") or line_low.startswith("fbrica / direccin")
              or line_low.startswith("fábrica / direcci")) and not result["fabricante"]:
            off, val = _itk_get_val(lines, i)
            if val:
                result["fabricante"] = val
                j = i + off + 1
                if j < len(lines) and lines[j].strip():
                    result["direccion"] = lines[j].strip()

        # Specs
        elif (line_low.startswith("características técnicas") or line_low.startswith("caractersticas tcnicas")) and not result["specs"]:
            _, val = _itk_get_val(lines, i)
            if val:
                result["specs"] = val

        # Marca
        elif line_low.startswith("marca comercial") and not result["marca"]:
            _, val = _itk_get_val(lines, i)
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

        # Fechas
        if _INICIAL_KW.search(line):
            dm = _DATE_RE.search(line)
            if not dm and i + 1 < len(lines):
                dm = _DATE_RE.search(lines[i + 1])
            if dm:
                result["fecha_emision"] = dm.group(1)
                if log_fn:
                    log_fn("info", f"[ITK] Fecha emisión (inicial): {dm.group(1)!r}")
        elif _EMIS_KW.search(line) and not result["fecha_emision"]:
            dm = _DATE_RE.search(line)
            if not dm and i + 1 < len(lines):
                dm = _DATE_RE.search(lines[i + 1])
            if dm:
                result["fecha_emision"] = dm.group(1)
                if log_fn:
                    log_fn("info", f"[ITK] Fecha emisión: {dm.group(1)!r}")
        elif _VENC_KW.search(line) and not result["fecha_vencimiento"]:
            dm = _DATE_RE.search(line)
            if not dm and i + 1 < len(lines):
                dm = _DATE_RE.search(lines[i + 1])
            if dm:
                result["fecha_vencimiento"] = dm.group(1)
                if log_fn:
                    log_fn("info", f"[ITK] Fecha vencimiento: {dm.group(1)!r}")

    # Fallback full-text para fecha de emisión
    if not result["fecha_emision"]:
        fb = re.search(
            r'(?:fecha\s*de\s*emisi[oó]n|issue\s*date|date\s*of\s*issue'
            r'|initial\s*issue|fecha\s*de\s*emision)'
            r'\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{4})',
            text_sorted, re.IGNORECASE
        )
        if fb:
            result["fecha_emision"] = fb.group(1)
            if log_fn:
                log_fn("info", f"[ITK] Fecha emisión (fallback): {fb.group(1)!r}")

    result["fecha_vencimiento"] = result["fecha_vencimiento"] or calc_vencimiento(result["fecha_emision"])
    result["fecha_inicio_tramite"] = calc_inicio_tramite(result["fecha_vencimiento"])

    # Si no se extrajo nada relevante, caer en CB Scheme
    if not result["producto_desc"] and not result["modelos"]:
        if log_fn:
            log_fn("info", "Intertek extr. fallback → CB Scheme")
        return cb_scheme.extract(lines_unsorted, "", log_fn)

    if log_fn:
        log_fn("info", f"Intertek extraído: marca={result['marca']}, fab={str(result['fabricante'])[:30]}")
    return result
