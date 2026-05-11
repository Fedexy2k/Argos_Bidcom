"""
Extractor para certificados Intertek Argentina (Esquema 2).
Utiliza el texto ordenado por coordenadas (sort=True en PyMuPDF)
para manejar el layout roto de multi-columna de Intertek.

Soporta dos formatos de tabla:
  - Clásico: etiqueta en línea N, valor en línea N+1
  - Inline (Caso 15 / certs simplificados IACSA): "Etiqueta    Valor" en la misma línea
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
    "observaciones", "remarks",
    "firma", "signature",
}


def _itk_get_val(lines: list[str], i: int) -> tuple[int, str]:
    """Retorna (offset, valor) buscando en las líneas siguientes a la etiqueta."""
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


def _itk_split_inline(line: str) -> str:
    """
    Detecta el formato "Etiqueta    Valor" en la misma línea (Caso 15 / certs simplificados).
    Usa 2+ espacios consecutivos como separador entre etiqueta y valor.
    Retorna la parte del valor, o "" si no hay separación inline.
    """
    parts = re.split(r' {2,}', line, maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        return parts[1].strip()
    return ""


def _itk_get_val_smart(lines: list[str], i: int) -> tuple[int, str]:
    """
    Estrategia dual:
    1. Primero intenta extraer el valor inline (misma línea, 2+ espacios de separación).
    2. Si no hay inline, busca en las líneas siguientes (comportamiento original).
    """
    inline = _itk_split_inline(lines[i])
    if inline:
        return 0, inline
    return _itk_get_val(lines, i)


def extract(lines_unsorted: list[str], text_sorted: str = "", log_fn=None) -> dict:
    """Extrae datos de certificados Intertek Argentina."""
    if not text_sorted:
        return cb_scheme.extract(lines_unsorted, "", log_fn)

    lines = [l.strip() for l in text_sorted.replace('\r\n', '\n').split('\n')]
    result = empty_result()

    _DATE_RE = re.compile(r'(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4})')
    _INICIAL_KW = re.compile(
        r'(?:fecha\s*de\s*emisi[o\xf3]n\s*inicial'
        r'|date\s*of\s*first\s*edition'
        r'|initial\s*issue)',
        re.IGNORECASE
    )
    _EMIS_KW = re.compile(
        r'(?:fecha\s*de\s*emisi[o\xf3]n|issue\s*date|date\s*of\s*issue'
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

        # ── Producto ──────────────────────────────────────────
        if line_low.startswith("producto") and not result["producto_desc"]:
            _, val = _itk_get_val_smart(lines, i)
            if val:
                result["producto_desc"] = val.rstrip('.')

        # ── Titular del Certificado (importador, NO el fabricante) ──
        elif line_low.startswith("titular del certificado") and not result.get("titular"):
            _, val = _itk_get_val_smart(lines, i)
            if val:
                result["titular"] = val  # type: ignore[assignment]

        # ── Fábrica / Dirección ───────────────────────────────
        elif (
            line_low.startswith("f\xe1brica / direcci\xf3n")
            or line_low.startswith("fbrica / direccin")
            or line_low.startswith("f\xe1brica / direcci")
            or line_low.startswith("factory / address")
        ) and not result["fabricante"]:
            off, val = _itk_get_val_smart(lines, i)
            if val:
                # Detectar cert simplificado/codificado (Disposición 1/24):
                # la fábrica aparece como un código de cert en lugar del nombre real
                es_codificado = bool(re.match(r'^[A-Z]{2,6}-[A-Z]{2,5}-\d{4}', val))
                if es_codificado:
                    result["fabricante"] = val  # código del cert — dispatcher lo marca como simplificado
                    if log_fn:
                        log_fn("info", f"[ITK] Cert simplificado/codificado — F\xe1brica={val!r}")
                else:
                    # Nuevo formato: fab y dirección en la misma línea separados por " // "
                    # Ej: "Yuyao Lanqiang Electrical Co. // No.19 Nanzh Ave, Yuyao, China"
                    if " // " in val:
                        parts = val.split(" // ", 1)
                        result["fabricante"] = parts[0].strip()
                        result["direccion"] = parts[1].strip()
                    else:
                        result["fabricante"] = val
                        # Formato clásico: dirección en la línea siguiente al nombre
                        j = i + max(off, 1) + 1
                        if j < len(lines) and lines[j].strip():
                            cand = lines[j].strip()
                            clow = cand.lower()
                            if not any(clow.startswith(lbl) for lbl in BILINGUAL_LABELS):
                                result["direccion"] = cand

        # ── Specs / Características técnicas ─────────────────
        elif (
            line_low.startswith("caracter\xedsticas t\xe9cnicas")
            or line_low.startswith("caractersticas tcnicas")
            or line_low.startswith("technical caracteristics")
            or line_low.startswith("technical characteristics")
        ) and not result["specs"]:
            _, val = _itk_get_val_smart(lines, i)
            if val:
                result["specs"] = val

        # ── Marca ─────────────────────────────────────────────
        elif (line_low.startswith("marca comercial") or line_low.startswith("trade mark")) \
                and not result["marca"]:
            _, val = _itk_get_val_smart(lines, i)
            if val:
                result["marca"] = val.rstrip('.')

        # ── Modelos ───────────────────────────────────────────
        elif (line_low.startswith("modelo o tipo") or line_low.startswith("model or type")) \
                and not result["modelos"]:
            off, val = _itk_get_val_smart(lines, i)
            model_lines = [val] if val else []
            # Buscar continuación (valor puede seguir en línea siguiente con bilingual label en medio)
            j = i + max(off, 1) + 1
            while j < min(i + 15, len(lines)):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                nlow = next_line.lower()
                # Saltar bilingual label secundaria (ej: "Model or type")
                if nlow.startswith("model or type") or nlow.startswith("modelo o tipo"):
                    j += 1
                    continue
                if any(nlow.startswith(lbl) for lbl in BILINGUAL_LABELS):
                    break
                if re.match(r'^[\dA-Z\(]', next_line):
                    model_lines.append(next_line)
                else:
                    break
                j += 1
            if model_lines:
                combined = " ".join(m for m in model_lines if m)
                # Formato "1) FKN700; 2) FKN70; 3) FKN75; ..." → extraer solo los códigos
                # Splitear por ";" primero, luego extraer código de cada ítem "N) CODIGO"
                items = re.split(r'[;,]\s*', combined)
                codes = []
                for item in items:
                    item = item.strip()
                    m = re.match(r'^\d+\)\s*([A-Z0-9][A-Z0-9\-]+)', item)
                    if m:
                        codes.append(m.group(1))
                result["modelos"] = ", ".join(codes) if codes else combined

        # ── Normas ────────────────────────────────────────────
        elif (line_low.startswith("norma(s) aplicada(s)") or line_low.startswith("standard(s) used")) \
                and not result.get("normas"):
            _, val = _itk_get_val_smart(lines, i)
            if val:
                result["normas"] = val  # type: ignore[assignment]

        # ── Fechas ────────────────────────────────────────────
        if _INICIAL_KW.search(line):
            dm = _DATE_RE.search(line)
            if not dm and i + 1 < len(lines):
                dm = _DATE_RE.search(lines[i + 1])
            if not dm and i + 2 < len(lines):
                dm = _DATE_RE.search(lines[i + 2])
            if dm:
                result["fecha_emision"] = dm.group(1)
                if log_fn:
                    log_fn("info", f"[ITK] Fecha emisi\xf3n (inicial): {dm.group(1)!r}")
        elif _EMIS_KW.search(line) and not result["fecha_emision"]:
            dm = _DATE_RE.search(line)
            if not dm and i + 1 < len(lines):
                dm = _DATE_RE.search(lines[i + 1])
            if dm:
                result["fecha_emision"] = dm.group(1)
                if log_fn:
                    log_fn("info", f"[ITK] Fecha emisi\xf3n: {dm.group(1)!r}")
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
            r'(?:fecha\s*de\s*emisi[o\xf3]n|issue\s*date|date\s*of\s*issue'
            r'|initial\s*issue|fecha\s*de\s*emision)'
            r'\s*[:\-]?\s*(\d{2}[/\-.]\d{2}[/\-.]\d{4})',
            text_sorted, re.IGNORECASE
        )
        if fb:
            result["fecha_emision"] = fb.group(1)
            if log_fn:
                log_fn("info", f"[ITK] Fecha emisi\xf3n (fallback): {fb.group(1)!r}")

    result["fecha_vencimiento"] = result["fecha_vencimiento"] or calc_vencimiento(result["fecha_emision"])
    result["fecha_inicio_tramite"] = calc_inicio_tramite(result["fecha_vencimiento"])

    # Si no se extrajo nada relevante, caer en CB Scheme
    if not result["producto_desc"] and not result["modelos"]:
        if log_fn:
            log_fn("info", "Intertek extr. fallback → CB Scheme")
        return cb_scheme.extract(lines_unsorted, "", log_fn)

    if log_fn:
        log_fn("info",
               f"[ITK] Extra\xeddo: marca={result['marca']}, "
               f"prod={result['producto_desc']}, "
               f"modelos={result['modelos'][:50] if result['modelos'] else '[vac\xedo]'}, "
               f"specs={result['specs'][:50] if result['specs'] else '[vac\xedo]'}, "
               f"fab={str(result['fabricante'])[:30]}, "
               f"emision={result['fecha_emision']}")
    return result
