"""
modules/extractors
==================
Paquete de extractores de datos de certificados por OEC.

Uso:
    from modules.extractors.dispatcher import extract_product_data
    resultado = extract_product_data(text, text_sorted, oec_key, log_fn)
"""
from modules.extractors.dispatcher import extract_product_data

__all__ = ["extract_product_data"]
