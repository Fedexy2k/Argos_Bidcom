"""
Protocolo base para todos los extractores de OEC.
Cada extractor debe retornar un dict con estas claves.
"""
from __future__ import annotations
from typing import Protocol, runtime_checkable

EMPTY_RESULT: dict = {
    "marca": "",
    "fabricante": "",
    "direccion": "",
    "modelos": "",
    "specs": "",
    "producto_desc": "",
    "normas": "",
    "fecha_emision": "",
    "fecha_vencimiento": "",
    "fecha_inicio_tramite": "",
}


def empty_result() -> dict:
    """Retorna un dict vacío con todas las claves esperadas."""
    return dict(EMPTY_RESULT)


@runtime_checkable
class OECExtractor(Protocol):
    """Protocolo que deben cumplir todos los extractores de OEC."""
    def extract(self, lines: list[str], text_sorted: str = "") -> dict:
        """
        Extrae datos del producto desde las líneas de texto del certificado.

        Args:
            lines: Líneas del texto del certificado (unsorted).
            text_sorted: Texto completo ordenado por coordenadas (PyMuPDF sort=True).

        Returns:
            dict con claves: marca, fabricante, direccion, modelos, specs,
            producto_desc, fecha_emision, fecha_vencimiento, fecha_inicio_tramite.
        """
        ...
