"""
Utilidades compartidas por todos los extractores de OEC.
Estas funciones son puras (no dependen de estado de clase).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional


# ── Navegación de líneas ─────────────────────────────────────

def find_line(lines: list[str], labels: list[str], start: int = 0, end: Optional[int] = None) -> int:
    """Busca la primera línea que coincida con algún label (case-insensitive, ignora ':')."""
    if end is None:
        end = len(lines)
    for i in range(start, min(end, len(lines))):
        clean = lines[i].strip().rstrip(':').lower()
        for label in labels:
            if clean == label.rstrip(':').lower():
                return i
    return -1


def next_non_empty(
    lines: list[str],
    after: int,
    skip_labels: Optional[set[str]] = None,
) -> tuple[int, str]:
    """
    Devuelve (indice, texto) de la siguiente línea no vacía después de 'after'.
    Salta labels conocidos si se proporcionan.
    """
    if skip_labels is None:
        skip_labels = set()
    for j in range(after + 1, min(after + 8, len(lines))):
        val = lines[j].strip()
        if not val:
            continue
        if val.rstrip(':').lower() in skip_labels:
            continue
        # Saltar códigos de formulario y páginación
        if re.match(r'^\d+ de \d+$', val) or re.match(r'^[A-Z]{2,5}-\d+\s+[A-Z]\d', val):
            continue
        return j, val
    return -1, ""


def find_date_after_label(lines: list[str], labels: list[str], start: int = 0) -> str:
    """
    Busca una fecha (dd/mm/yyyy) en las líneas siguientes a un label.
    Salta líneas que son traducciones bilingüísticas o vacías.
    """
    idx = find_line(lines, labels, start=start)
    if idx < 0:
        return ""
    date_re = re.compile(r'^(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})$')
    for j in range(idx + 1, min(idx + 5, len(lines))):
        val = lines[j].strip()
        if not val:
            continue
        m = date_re.match(val)
        if m:
            return m.group(1)
    return ""


# ── Cálculo de fechas ────────────────────────────────────────

def parse_date(date_str: str) -> datetime:
    """Parsea una fecha en formatos comunes."""
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato de fecha no reconocido: {date_str}")


def vigencia_days(reglamento: str = "") -> int:
    """Retorna la vigencia en días según el reglamento.
    Ap. IV Electrónica = 4 años (1460d), resto = 2 años (730d).
    """
    if reglamento and "Ap. IV" in reglamento and "Electrónica" in reglamento:
        return 1460
    return 730


def calc_vencimiento(fecha_emision: str, reglamento: str = "") -> str:
    """Calcula vencimiento = emisión + vigencia según reglamento."""
    if not fecha_emision:
        return ""
    try:
        fe = parse_date(fecha_emision)
        days = vigencia_days(reglamento)
        return (fe + timedelta(days=days)).strftime("%d/%m/%Y")
    except (ValueError, Exception):
        return ""


def calc_inicio_tramite(fecha_vencimiento: str) -> str:
    """Calcula inicio de trámite = vencimiento - 3 meses (90 días)."""
    if not fecha_vencimiento:
        return ""
    try:
        fv = parse_date(fecha_vencimiento)
        return (fv - timedelta(days=90)).strftime("%d/%m/%Y")
    except (ValueError, Exception):
        return ""
