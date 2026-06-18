"""
Extractor para certificados Lenor (LCSH-XXXX, LCJ-XXXX).

Soporta:
  - Formato normal: certificado de seguridad eléctrica con Anexo de grupos 3 líneas (modelo/marca/specs)
  - Formato B (juguetes): Anexo con grupos de 4 líneas (nro/marca/modelo/desc)
  - Formato "NOTA DE NO APLICABILIDAD": certificados de ftalatos con tabla en Anexo
"""
from __future__ import annotations

import re
from modules.extractors.base import empty_result
from modules.extractors.shared import (
    find_line, next_non_empty, find_date_after_label,
    calc_vencimiento, calc_inicio_tramite,
)

LENOR_SKIP = {
    "certificate holder", "factory", "address", "product",
    "standard(s)", "testing laboratory", "test report n°",
    "additional information", "c.u.i.t",
}

MESES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
}


def _parse_es_date(text: str) -> str:
    """Parsea '30 de diciembre de 2025' → '30/12/2025'."""
    m = re.search(r'(\d{1,2}) de (\w+) de (\d{4})', text.lower())
    if m:
        day, month_name, year = m.group(1), m.group(2), m.group(3)
        month = MESES.get(month_name)
        if month:
            return f"{day.zfill(2)}/{month}/{year}"
    m2 = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', text)
    return m2.group(1) if m2 else ""


# ── Parsers de Anexo ─────────────────────────────────────────

def _parse_annex_formato_a(ll: list[str], annex_start: int, result: dict) -> dict:
    """Formato A: seguridad eléctrica — grupos de 3 líneas modelo/marca/specs."""
    n = len(ll)
    data_start = -1

    for idx in range(annex_start, min(annex_start + 20, n)):
        if "Main ratings" in ll[idx] or "Características técnicas" in ll[idx]:
            data_start = idx + 1

    if data_start < 0:
        return result

    while data_start < n and not ll[data_start].strip():
        data_start += 1

    modelos: list[str] = []
    marcas: set[str] = set()
    specs_set: set[str] = set()
    cur = data_start

    while cur + 2 < n:
        modelo_val = ll[cur].strip()
        marca_val  = ll[cur + 1].strip()
        specs_val  = ll[cur + 2].strip()

        if not modelo_val or not re.match(r'^[A-Z0-9]', modelo_val) or len(modelo_val) > 50:
            break
        if modelo_val.lower() in ("model", "modelo", "brandname", "marca",
                                   "main ratings", "características técnicas"):
            cur += 1
            continue

        modelos.append(modelo_val)
        if marca_val and marca_val.lower() not in ("brandname", "marca", "brand"):
            marcas.add(marca_val)
        if specs_val and "rating" not in specs_val.lower() and "características" not in specs_val.lower():
            specs_set.add(specs_val)
        cur += 3

        while cur < n and not ll[cur].strip():
            cur += 1

    result["specs"] = list(specs_set)[0] if specs_set else ""
    result["modelos"] = ", ".join(modelos)
    result["marca"] = "; ".join(sorted(list(marcas))) if marcas else ""
    return result


def _parse_annex_formato_b(ll: list[str], annex_start: int, result: dict) -> dict:
    """Formato B: juguetes — grupos de 4 líneas nro/marca/modelo/desc."""
    n = len(ll)
    data_start = -1

    for idx in range(annex_start, min(annex_start + 50, n)):
        if ("Producto (descripción breve)" in ll[idx]
                or "Producto (descripcion breve)" in ll[idx]
                or "Product (brief description)" in ll[idx]):
            data_start = idx + 1

    if data_start < 0:
        for idx in range(annex_start, min(annex_start + 50, n)):
            if "Detalle de productos" in ll[idx]:
                for jj in range(idx + 1, min(idx + 15, n)):
                    if re.match(r'^\d+\*?$', ll[jj].strip()):
                        data_start = jj
                        break
                break

    if data_start < 0:
        return result

    while data_start < n and not ll[data_start].strip():
        data_start += 1

    modelos: list[str] = []
    marcas: set[str] = set()
    cur = data_start
    nro_re = re.compile(r'^\d+\*?$')

    while cur < n:
        nro = ll[cur].strip()
        if not nro_re.match(nro):
            break
        if cur + 3 < n:
            marca_val = ll[cur + 1].strip()
            modelo_val = ll[cur + 2].strip()
            if modelo_val and re.match(r'^[A-Z0-9]', modelo_val):
                modelos.append(modelo_val)
            elif modelo_val:
                candidate = ll[cur + 3].strip() if cur + 3 < n else ""
                modelos.append(candidate if (candidate and re.match(r'^[A-Z0-9]', candidate)) else modelo_val)
            if marca_val and marca_val.lower() not in ("brandname", "marca", "brand"):
                marcas.add(marca_val)
        cur += 4
        while cur < n and ll[cur].strip().startswith("*"):
            cur += 1
        while cur < n and not ll[cur].strip():
            cur += 1

    result["modelos"] = ", ".join(modelos)
    result["marca"] = "; ".join(sorted(list(marcas))) if marcas else ""
    return result


def _parse_annex_formato_c(ll: list[str], annex_start: int, result: dict) -> dict:
    """Formato C: nuevo tabular (Caso 14) — Marca, Modelo, Specs en la misma línea separados por múltiples espacios."""
    n = len(ll)
    data_start = -1

    for idx in range(annex_start, min(annex_start + 40, n)):
        if "Caracter" in ll[idx] or "Main ratings" in ll[idx]:
            data_start = idx + 1
            break

    if data_start < 0:
        return result

    modelos: list[str] = []
    marcas: set[str] = set()
    specs_set: set[str] = set()
    
    for idx in range(data_start, n):
        line = ll[idx].strip()
        # Cortar si encontramos pie de página o nueva sección
        if "Página" in line or "CERTIFICADO DE CONFORMIDAD" in line or "lenorgroup.com" in line or "Laboratorio:" in line or "Fábrica:" in line:
            break
        if not line:
            continue
            
        # Ignorar lineas de header
        low_line = line.lower()
        if "model:" in low_line or "brandname:" in low_line or "main ratings:" in low_line:
            continue
            
        parts = re.split(r'\s{2,}', line) # Usamos splits de espacios múltiples
        if len(parts) >= 2:
            mod_val = parts[0].strip()
            if mod_val not in ("DE", "CERTIFICADO"):
                modelos.append(mod_val)
            marc_val = parts[1].strip()
            if marc_val not in ("DE", "CERTIFICADO"):
                marcas.add(marc_val)
            if len(parts) >= 3:
                specs_set.add(parts[2].strip().replace("CONFORMIDAD", ""))
        elif "GADNIC" in line:
            parts = line.split(" GADNIC ")
            if len(parts) == 2:
                modelos.append(parts[0].strip())
                marcas.add("GADNIC")
                specs_set.add(parts[1].strip().replace("CONFORMIDAD", ""))
                
    result["modelos"] = ", ".join(modelos)
    result["marca"] = "; ".join(sorted(list(marcas))) if marcas else ""
    result["specs"] = list(specs_set)[0] if specs_set else ""
    return result


def _parse_lenor_annex(lines: list[str]) -> dict:
    """Detecta el formato del Anexo y delega al parser correspondiente."""
    result: dict = {"modelos": "", "marca": "", "specs": ""}
    ll = list(lines)
    annex_start = -1

    for i, line in enumerate(ll):
        if "Anexo al Certificado" in line or "Annex of Certificate" in line or "Annex to Certificate" in line:
            annex_start = i
            break

    if annex_start < 0:
        return result

    window_text = " ".join(ll[annex_start: min(annex_start + 50, len(ll))])
    is_formato_b = (
        "Detalle de productos" in window_text
        or "Producto (descripcion breve)" in window_text
        or "Producto (descripción breve)" in window_text
        or "Product (brief description)" in window_text
    )
    is_formato_c = "Main ratings" in window_text and "Brandname" in window_text and "Model" in window_text

    if is_formato_c:
        return _parse_annex_formato_c(ll, annex_start, result)
    elif is_formato_b:
        return _parse_annex_formato_b(ll, annex_start, result)
    else:
        return _parse_annex_formato_a(ll, annex_start, result)


# ── Formato NOTA DE NO APLICABILIDAD ─────────────────────────

def _parse_lenor_nota_annex(lines: list[str]) -> dict:
    """Parsea el Anexo del certificado Lenor 'NOTA DE NO APLICABILIDAD' (ftalatos)."""
    result = {"modelos": "", "producto_desc": ""}
    annex_start = -1

    for i, line in enumerate(lines):
        if "Anexo" in line or ("N°" in line and "Certificado" in line):
            if "Código" in lines[i] if i < len(lines) else False:
                annex_start = i
                break
            if i + 1 < len(lines) and "Código" in lines[i + 1]:
                annex_start = i
                break

    if annex_start < 0:
        for i, line in enumerate(lines):
            if ("Código de" in line or "código de" in line) and "origen" in line.lower():
                annex_start = i
                break

    if annex_start < 0:
        return result

    modelos = []
    denominaciones = []
    item_re = re.compile(r'^(\d+)\s+')

    for line in lines[annex_start:]:
        m = item_re.match(line)
        if m:
            parts = re.split(r'\s{2,}', line.strip())
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


def _extract_lenor_nota(lines: list[str], log_fn=None) -> dict:
    """Extrae del formato Lenor NOTA DE NO APLICABILIDAD (ftalatos)."""
    result = empty_result()

    for i, line in enumerate(lines):
        ll = line.lower()
        if ll.startswith('fabricante:') or ll.startswith('fabricante '):
            val = re.sub(r'^fabricante[:\s]+', '', line, flags=re.IGNORECASE).strip()
            if val:
                result["fabricante"] = val
                if i + 1 < len(lines):
                    nxt = lines[i + 1].strip()
                    if nxt and not nxt.lower().startswith('producto'):
                        if not result["direccion"]:
                            result["direccion"] = nxt
        elif (ll.startswith('dirección:') or ll.startswith('dirección ')) and not result["direccion"]:
            val = re.sub(r'^direcci[oó]n[:\s]+', '', line, flags=re.IGNORECASE).strip()
            if val:
                j = i + 1
                while j < len(lines) and lines[j].strip():
                    low_j = lines[j].strip().lower()
                    if low_j.startswith('producto') or low_j.startswith('modelo') or low_j.startswith('norma'):
                        break
                    val = val + " " + lines[j].strip()
                    j += 1
                result["direccion"] = val
        elif ll.startswith('producto:') or ll.startswith('producto '):
            val = re.sub(r'^producto[:\s]+', '', line, flags=re.IGNORECASE).strip()
            if val and val.upper() != "VER ANEXO":
                result["producto_desc"] = val
        elif ll.startswith('modelo:') or ll.startswith('modelo '):
            val = re.sub(r'^modelo[:\s]+', '', line, flags=re.IGNORECASE).strip()
            if val and val.upper() != "VER ANEXO" and not result["modelos"]:
                result["modelos"] = val
        elif 'fecha de emisi' in ll:
            val = re.sub(r'^fecha de emisi[oó]n[:\s]*', '', line, flags=re.IGNORECASE).strip()
            result["fecha_emision"] = _parse_es_date(val)
        elif 'fecha de vencimiento' in ll:
            val = re.sub(r'^fecha de vencimiento[:\s]*', '', line, flags=re.IGNORECASE).strip()
            result["fecha_vencimiento"] = _parse_es_date(val)

    annex = _parse_lenor_nota_annex(lines)
    if annex["modelos"] and not result["modelos"]:
        result["modelos"] = annex["modelos"]
    if not result["producto_desc"] and annex["producto_desc"]:
        result["producto_desc"] = annex["producto_desc"]

    if not result["fecha_vencimiento"]:
        result["fecha_vencimiento"] = calc_vencimiento(result["fecha_emision"])
    result["fecha_inicio_tramite"] = calc_inicio_tramite(result["fecha_vencimiento"])

    if log_fn:
        log_fn("info", f"Lenor-Nota extraído: fab={str(result['fabricante'])[:30]}, emision={result['fecha_emision']}")
    return result


# ── Extractor principal ──────────────────────────────────────

def extract(lines: list[str], text_sorted: str = "", log_fn=None) -> dict:
    """Extrae datos de certificados Lenor."""
    result = empty_result()

    detect_text = text_sorted if text_sorted else "\n".join(lines)
    detect_lines_sorted = [l.strip() for l in detect_text.replace('\r\n', '\n').split('\n') if l.strip()]

    # Detectar formato NOTA DE NO APLICABILIDAD (ftalatos)
    text_block = " ".join(detect_lines_sorted[:15])
    is_nota = "NOTA DE NO APLICABILIDAD" in text_block or "Norma con la cual se" in " ".join(detect_lines_sorted[:30])

    if is_nota:
        return _extract_lenor_nota(detect_lines_sorted, log_fn)

    detect_lines = lines

    # ── FÁBRICA + DIRECCIÓN ──
    fab_idx = find_line(detect_lines, ["Fábrica"])
    if fab_idx >= 0:
        fab_sub_idx, fab_name = next_non_empty(detect_lines, fab_idx, LENOR_SKIP)
        if fab_name:
            # Acaparar siguientes líneas para fábrica por si salto a otro renglón
            if fab_sub_idx + 1 < len(detect_lines) and detect_lines[fab_sub_idx+1].strip() == "LTD.":
                fab_name += " LTD."
                fab_sub_idx += 1
            result["fabricante"] = fab_name
            
            dir_idx = find_line(detect_lines, ["Dirección"], start=fab_idx + 1)
            if dir_idx >= 0:
                _, dir_val = next_non_empty(detect_lines, dir_idx, LENOR_SKIP)
                if dir_val:
                    next_idx = dir_idx + 3
                    if next_idx < len(detect_lines):
                        next_line = detect_lines[next_idx].strip()
                        if (next_line and len(next_line) > 3
                                and next_line.rstrip(':').lower() not in
                                {"producto", "product", "norma(s)", "standard(s)",
                                 "c.u.i.t", "fábrica", "factory", "dirección", "address", "laboratorio:", "testing laboratory:"}):
                            dir_val = dir_val + " " + next_line
                    result["direccion"] = dir_val
            else:
                # Si no hay "Dirección", generalmente sigue justo abajo de "LTD." o el fin del nombre
                dir_lines = []
                for j in range(fab_sub_idx + 1, min(fab_sub_idx + 5, len(detect_lines))):
                    line = detect_lines[j].strip()
                    if not line or line.lower().startswith(("laboratorio:", "testing laboratory:", "informe", "test report")):
                        break
                    dir_lines.append(line)
                if dir_lines:
                    result["direccion"] = " ".join(dir_lines)

    # ── PRODUCTO ──
    idx = find_line(detect_lines, ["Producto"])
    if idx >= 0:
        _, val = next_non_empty(detect_lines, idx, LENOR_SKIP)
        if val:
            result["producto_desc"] = val

    # ── NORMAS ──
    # Lenor SE usa dos variantes de label según el formato:
    #   - Formato clásico (LCSH):  "Norma(s):" / "Standard(s):"
    #   - Formato tabular (caso 14): "Documento(s) normativo(s):" / "Normative document(s):"
    idx = find_line(detect_lines, [
        "Norma(s)", "Norma(s):",
        "Documento(s) normativo(s)", "Documento(s) normativo(s):",
    ])
    if idx >= 0:
        # LENOR_SKIP incluye "standard(s)" y "standard(s):" — salta el bilingüe automáticamente
        _, val = next_non_empty(detect_lines, idx, LENOR_SKIP | {"normative document(s)"})
        if val:
            result["normas"] = val

    # ── MODELOS, MARCA, SPECS desde ANEXO ──
    # Para el Anexo C (tabular) dependemos de text_sorted porque el layout raw destruye las tablas
    annex = _parse_lenor_annex(detect_lines_sorted)
    # Si detect_lines_sorted no sacó nada, fallback a detect_lines
    if not annex["modelos"]:
        annex = _parse_lenor_annex(detect_lines)
    
    if annex["modelos"]:
        result["modelos"] = annex["modelos"]
    if annex["marca"]:
        result["marca"] = annex["marca"]
    if annex["specs"]:
        result["specs"] = annex["specs"]

    # ── FECHAS ──
    result["fecha_emision"] = find_date_after_label(detect_lines, ["Fecha de emisión"])
    result["fecha_vencimiento"] = find_date_after_label(
        detect_lines, ["Fecha de próxima vigilancia", "Fecha de vencimiento"])
    if not result["fecha_vencimiento"]:
        result["fecha_vencimiento"] = calc_vencimiento(result["fecha_emision"])
    result["fecha_inicio_tramite"] = calc_inicio_tramite(result["fecha_vencimiento"])

    if log_fn:
        log_fn("info", f"Lenor extraído: marca={result['marca']}, fab={str(result['fabricante'])[:30]}, emision={result['fecha_emision']}")
    return result
