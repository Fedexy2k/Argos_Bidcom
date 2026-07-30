"""
modules/pdf_ops.py
==================
Operaciones de manipulación de PDF:
  - censor_cert_pdf : censura fabricante/dirección en el certificado
  - merge_pdfs      : combina DJC + extras + certificado rasterizado
  - _strip_old_djc  : elimina carátulas de DJC anterior del certificado
"""
from __future__ import annotations

import os
import logging
from typing import Callable, Optional

import fitz  # PyMuPDF  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


def _log_fn(level: str, msg: str, log_fn: Optional[Callable] = None):
    if log_fn:
        log_fn(level, msg)
    else:
        getattr(logger, level, logger.info)(msg)


def extract_pdf_clean_text(pdf_path: str) -> str:
    """
    Extrae el texto completo de un PDF preservando la estructura de bloques y tablas multi-columna.
    Ordena los bloques por coordenada (y0, x0) para evitar que tablas de Intertek/IRAM/Lenor
    se mezclen entre columnas o pierdan líneas de modelos/specs.
    """
    if not os.path.exists(pdf_path):
        return ""
    doc = fitz.open(pdf_path)
    all_pages_text = []
    for page in doc:
        blocks = page.get_text("blocks")
        # Ordenar por fila (y0 agrupado en bandas de 15px) y luego por columna (x0)
        blocks.sort(key=lambda b: (round(b[1] / 15), b[0]))
        page_str = "\n".join(b[4].strip() for b in blocks if b[4].strip())
        if page_str:
            all_pages_text.append(page_str)
    doc.close()
    return "\n\n--- Hoja del Certificado ---\n\n".join(all_pages_text)



# ─────────────────────────────────────────────────────────────
#  Detección y remoción de DJC anterior
# ─────────────────────────────────────────────────────────────

def strip_old_djc(doc: fitz.Document, log_fn: Optional[Callable] = None) -> None:
    """
    Escanea las primeras páginas del certificado para detectar si es una DJC
    generada anteriormente (carátula) pegada al certificado real.
    Si la detecta, elimina esas primeras páginas.
    """
    pages_to_delete = []
    for i in range(min(3, len(doc))):
        page_text = doc[i].get_text("text").lower()
        if ("documento de justificación de conformidad" in page_text and
                ("djc-" in page_text or "bidcom" in page_text or "gadnic" in page_text)):
            pages_to_delete.append(i)
            _log_fn("info", f"[M3-Merge] Hoja {i+1} detectada como vieja DJC — se removerá.", log_fn)
        elif pages_to_delete:
            break

    if pages_to_delete:
        for p in reversed(pages_to_delete):
            doc.delete_page(p)
        _log_fn("info", f"[M3-Merge] Removidas {len(pages_to_delete)} hoja(s) de DJC anterior.", log_fn)


# ─────────────────────────────────────────────────────────────
#  Censura de datos del fabricante
# ─────────────────────────────────────────────────────────────

DEFAULT_PRESERVE_WORDS = [
    "China", "china", "Korea", "korea", "Taiwan", "taiwan",
    "Vietnam", "vietnam", "India", "india",
    "Japan", "Japon", "USA", "usa",
]


def censor_cert_pdf(
    doc: fitz.Document,
    fabricante: str = "",
    direccion: str = "",
    preserve_words: Optional[list[str]] = None,
    log_fn: Optional[Callable] = None,
) -> fitz.Document:
    """
    Censura el fabricante y la dirección de fábrica en el certificado PDF.

    Estrategia:
      1. Localiza la zona del campo con search_for() usando los primeros tokens únicos.
      2. Dentro de esa banda horizontal, extrae cada PALABRA con get_text('words').
      3. Agrupa palabras consecutivas que NO están en preserve_words y las pinta de negro.
      4. Las palabras en preserve_words (ej. "China") se saltan y QUEDAN VISIBLES.
    """
    if preserve_words is None:
        preserve_words = DEFAULT_PRESERVE_WORDS

    BLACK = (0, 0, 0)
    MARGIN = 0
    preserve_lower = {pw.lower() for pw in preserve_words}

    def _clean_word(w: str) -> str:
        return w.rstrip(".,;:.")

    def _should_preserve(word_text: str) -> bool:
        return _clean_word(word_text).lower() in preserve_lower

    def _anchor_tokens(text: str, n: int = 3) -> list[str]:
        tokens = []
        for t in text.replace(",", " ").replace(".", " ").split():
            t = t.strip()
            if len(t) >= 5 and not _should_preserve(t):
                tokens.append(t)
                if len(tokens) >= n:
                    break
        return tokens

    def _censor_field(page, field_text: str, label: str) -> int:
        if not field_text or not field_text.strip():
            return 0

        anchors = _anchor_tokens(field_text)
        if not anchors:
            return 0

        search_text = " ".join(anchors[:2]) if len(anchors) >= 2 else anchors[0]
        hit_rects = page.search_for(search_text, quads=False)

        if not hit_rects:
            hit_rects = page.search_for(anchors[0], quads=False)

        if not hit_rects:
            _log_fn("warning", f"[M3-Censor] '{label}' no encontrado en pag {page.number+1}.", log_fn)
            return 0

        count = 0
        for zone in hit_rects:
            # Evitar censurar la linea de la marca comercial si el nombre del fabricante/direccion
            # coincide con la marca y la coincidencia de anclaje cae en la declaracion de marca.
            line_rect = fitz.Rect(0, zone.y0 - 15, page.rect.width, zone.y1 + 15)
            line_words = page.get_text("words", clip=line_rect)
            is_brand_line = False
            for w in line_words:
                w_lower = w[4].lower()
                if any(k in w_lower for k in ("marca", "trademark", "brand", "marque", "tradename")):
                    is_brand_line = True
                    break
            if is_brand_line:
                _log_fn("info", f"[M3-Censor] Saltando linea de marca/trademark en Y={zone.y0:.1f} para evitar censura erronea.", log_fn)
                continue

            band = fitz.Rect(zone.x0, zone.y0 - 2, page.rect.width, zone.y1 + 2)
            all_words = page.get_text("words", clip=band)
            if not all_words:
                continue

            all_words_sorted = sorted(all_words, key=lambda w: w[0])
            group_rect = None

            for word_entry in all_words_sorted:
                word_text = word_entry[4]
                wr = fitz.Rect(word_entry[:4])

                if _should_preserve(word_text):
                    if group_rect is not None:
                        page.draw_rect(group_rect, color=None, fill=BLACK, width=0)
                        count += 1
                        group_rect = None
                else:
                    inflated = fitz.Rect(
                        wr.x0 - MARGIN, wr.y0 - MARGIN,
                        wr.x1 + MARGIN, wr.y1 + MARGIN,
                    )
                    if group_rect is None:
                        group_rect = inflated
                    else:
                        group_rect = fitz.Rect(
                            min(group_rect.x0, inflated.x0),
                            min(group_rect.y0, inflated.y0),
                            max(group_rect.x1, inflated.x1),
                            max(group_rect.y1, inflated.y1),
                        )

            if group_rect is not None:
                page.draw_rect(group_rect, color=None, fill=BLACK, width=0)
                count += 1

        return count

    def _censor_factory_block(page) -> int:
        factory_hits = page.search_for("de la fabrica", quads=False)
        if not factory_hits:
            factory_hits = page.search_for("de la fábrica", quads=False)
        if not factory_hits:
            factory_hits = page.search_for("of the factory", quads=False)
            
        if not factory_hits:
            return 0
            
        zone_factory = factory_hits[0]
        next_labels = [
            "valores nominales", "ratings", "marca", "trademark",
            "modelo", "model", "informacion", "información",
            "additional", "normas", "standards"
        ]
        zone_next = None
        for lbl in next_labels:
            lbl_hits = page.search_for(lbl, quads=False)
            for hit in lbl_hits:
                if hit.y0 > zone_factory.y0 + 5:
                    if zone_next is None or hit.y0 < zone_next.y0:
                        zone_next = hit
                        
        y_start = zone_factory.y0 - 2
        if zone_next:
            y_end = zone_next.y0 - 4
        else:
            y_end = zone_factory.y1 + 100
            
        rect_factory_val = fitz.Rect(zone_factory.x1 + 5, y_start, page.rect.width, y_end)
        factory_words = page.get_text("words", clip=rect_factory_val)
        if not factory_words:
            return 0
            
        factory_words_sorted = sorted(factory_words, key=lambda w: (w[1], w[0]))
        group_rect = None
        count = 0
        
        for word_entry in factory_words_sorted:
            word_text = word_entry[4]
            wr = fitz.Rect(word_entry[:4])
            
            if _should_preserve(word_text):
                if group_rect is not None:
                    page.draw_rect(group_rect, color=None, fill=BLACK, width=0)
                    count += 1
                    group_rect = None
            else:
                if group_rect is None:
                    group_rect = wr
                else:
                    group_rect = fitz.Rect(
                        min(group_rect.x0, wr.x0),
                        min(group_rect.y0, wr.y0),
                        max(group_rect.x1, wr.x1),
                        max(group_rect.y1, wr.y1),
                    )
                    
        if group_rect is not None:
            page.draw_rect(group_rect, color=None, fill=BLACK, width=0)
            count += 1
            
        if count > 0:
            _log_fn("info", f"[M3-Censor] Bloque de fabrica censurado en pag {page.number+1}.", log_fn)
        return count

    total_rects = 0
    for page in doc:
        page_text = page.get_text("text").strip()
        if not page_text:
            _log_fn("warning", f"[M3-Censor] Pag {page.number+1} es imagen pura, no se puede censurar.", log_fn)
            continue
        total_rects += _censor_field(page, fabricante, "Fabricante")
        total_rects += _censor_field(page, direccion, "Direccion")
        total_rects += _censor_factory_block(page)

    if total_rects > 0:
        _log_fn("info", f"[M3-Censor] {total_rects} bloque(s) censurados (preserve_words respetadas).", log_fn)
    else:
        _log_fn("warning", "[M3-Censor] No se encontraron coincidencias de texto.", log_fn)

    return doc


# ─────────────────────────────────────────────────────────────
#  Merge de PDFs con rasterización
# ─────────────────────────────────────────────────────────────

def merge_pdfs(
    djc_pdf_path: str,
    cert_pdf_path: str,
    output_path: Optional[str] = None,
    extra_pdfs: Optional[list[str]] = None,
    log_fn: Optional[Callable] = None,
) -> str:
    """
    Combina DJC PDF + (opcionalmente extras) + Certificado PDF rasterizado.

    El certificado se RASTERIZA (150-200 DPI) antes de agregarlo para preservar
    las firmas digitales que se pierden en un merge directo de PDFs firmados.

    Args:
        djc_pdf_path:  Ruta al PDF de la DJC generada.
        cert_pdf_path: Ruta al PDF del certificado original.
        output_path:   (Opcional) Ruta de salida.
        extra_pdfs:    (Opcional) PDFs intermedios (ej. Nota de Extensión) sin rasterizar.
        log_fn:        Función de logging.

    Returns:
        Ruta al PDF combinado.
    """
    if output_path is None:
        base = os.path.splitext(djc_pdf_path)[0]
        output_path = f"{base}_completo.pdf"

    merged = fitz.open()

    # 1. Insertar DJC
    if os.path.exists(djc_pdf_path):
        _log_fn("info", "[M3-Merge] Insertando DJC PDF...", log_fn)
        src = fitz.open(djc_pdf_path)
        merged.insert_pdf(src)
        src.close()
    else:
        _log_fn("warning", f"[M3-Merge] DJC PDF no encontrado: {djc_pdf_path}", log_fn)

    # 1b. PDFs intermedios
    if extra_pdfs:
        for extra_path in extra_pdfs:
            if os.path.exists(extra_path):
                _log_fn("info", f"[M3-Merge] Insertando PDF intermedio: {os.path.basename(extra_path)}", log_fn)
                extra_src = fitz.open(extra_path)
                merged.insert_pdf(extra_src)
                extra_src.close()
            else:
                _log_fn("warning", f"[M3-Merge] PDF intermedio no encontrado: {extra_path}", log_fn)

    # 2. Rasterizar certificado
    if os.path.exists(cert_pdf_path):
        _log_fn("info", "[M3-Merge] Rasterizando certificado (preserva firma digital)...", log_fn)
        cert_src = fitz.open(cert_pdf_path)
        strip_old_djc(cert_src, log_fn)
        n_pages = len(cert_src)
        _log_fn("info", f"[M3-Merge] Certificado procesará {n_pages} página(s)", log_fn)

        # Detectar Tesseract
        has_tesseract = False
        try:
            import pytesseract  # type: ignore[import-untyped]
            import sys
            posibles_rutas = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                os.path.expanduser(r'~\AppData\Local\Tesseract-OCR\tesseract.exe'),
                os.path.expanduser(r'~\Tesseract-OCR\tesseract.exe'),
            ]
            
            if getattr(sys, 'frozen', False):
                posibles_rutas.insert(0, os.path.join(sys._MEIPASS, 'tesseract', 'tesseract.exe'))
            else:
                local_dev = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin', 'tesseract', 'tesseract.exe')
                posibles_rutas.insert(0, local_dev)

            for ruta in posibles_rutas:
                if os.path.exists(ruta):
                    pytesseract.pytesseract.tesseract_cmd = ruta
                    break
            pytesseract.get_tesseract_version()
            has_tesseract = True
        except Exception as e:
            _log_fn("warning", f"[M3-Merge] Tesseract no disponible ({e}). PDF final será imagen pura.", log_fn)
            _log_fn("warning", r"[M3-Merge] Para habilitar OCR, instalá Tesseract en C:\Program Files\Tesseract-OCR", log_fn)

        for page_num in range(n_pages):
            page = cert_src[page_num]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("jpeg")
            inserted_ocr = False

            if has_tesseract:
                try:
                    from PIL import Image  # type: ignore[import-untyped]
                    import io
                    import tempfile
                    img_pil = Image.open(io.BytesIO(img_bytes))
                    # Usar directorio temporal explícito para evitar errores de ruta
                    with tempfile.TemporaryDirectory() as tess_tmp:
                        old_tmp = os.environ.get("TMPDIR") or os.environ.get("TMP") or os.environ.get("TEMP", "")
                        os.environ["TMPDIR"] = tess_tmp
                        os.environ["TMP"] = tess_tmp
                        os.environ["TEMP"] = tess_tmp
                        try:
                            pdf_ocr_bytes = pytesseract.image_to_pdf_or_hocr(img_pil, extension='pdf', lang='spa+eng')  # type: ignore[reportPossiblyUnbound]
                        finally:
                            if old_tmp:
                                os.environ["TMPDIR"] = old_tmp
                                os.environ["TMP"] = old_tmp
                                os.environ["TEMP"] = old_tmp
                    ocr_doc = fitz.open("pdf", pdf_ocr_bytes)
                    rect = page.rect
                    new_page = merged.new_page(width=rect.width, height=rect.height)
                    new_page.show_pdf_page(rect, ocr_doc, 0)
                    ocr_doc.close()
                    inserted_ocr = True
                    _log_fn("info", f"[M3-Merge] Página {page_num+1}/{n_pages}: OCR aplicado.", log_fn)
                except Exception as e:
                    _log_fn("warning", f"[M3-Merge] Página {page_num+1}: Error OCR ({e}), fallback a imagen.", log_fn)

            if not inserted_ocr:
                rect = page.rect
                new_page = merged.new_page(width=rect.width, height=rect.height)
                new_page.insert_image(fitz.Rect(0, 0, rect.width, rect.height), stream=img_bytes)

            pix = None  # Liberar memoria

        cert_src.close()
        _log_fn("info", f"[M3-Merge] Certificado rasterizado: {n_pages} página(s) incluidas", log_fn)
    else:
        _log_fn("warning", f"[M3-Merge] Certificado PDF no encontrado: {cert_pdf_path}", log_fn)

    # 3. Guardar
    try:
        merged.save(output_path)
    except Exception as e:
        if "Permission denied" in str(e) or "cannot remove file" in str(e):
            import time
            ts = int(time.time())
            alt_path = output_path.replace(".pdf", f"_{ts}.pdf")
            _log_fn("warning", f"[M3-Merge] PDF abierto, guardando como: {alt_path}", log_fn)
            merged.save(alt_path)
            output_path = alt_path
        else:
            raise
    merged.close()

    _log_fn("info", f"[M3-Merge] ✓ PDF completo guardado: {os.path.basename(output_path)}", log_fn)
    return output_path
