"""
pdf_check.py - Diagnostica si un PDF tiene texto extraible o es imagen pura.
Uso: python pdf_check.py "ruta/al/archivo.pdf"
"""
import sys
import os

def check_pdf(pdf_path: str) -> dict:
    try:
        import fitz
    except ImportError:
        print("Error: PyMuPDF no instalado. Ejecutá: pip install pymupdf")
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"Error: Archivo no encontrado: {pdf_path}")
        sys.exit(1)

    doc = fitz.open(pdf_path)
    total_chars = 0
    total_images = 0
    page_info = []

    for i, page in enumerate(doc):
        text = page.get_text().strip()
        images = page.get_images()
        chars = len(text)
        total_chars += chars
        total_images += len(images)
        page_info.append({
            "pagina": i + 1,
            "chars": chars,
            "imagenes": len(images),
            "muestra": text[:80].replace('\n', ' ') if text else "(vacío)"
        })

    doc.close()

    has_text = total_chars > 50
    tipo = "TEXTO_EXTRAIBLE" if has_text else "IMAGEN_PURA (OCR necesario)"

    resultado = {
        "archivo": os.path.basename(pdf_path),
        "tipo": tipo,
        "total_chars": total_chars,
        "total_imagenes": total_images,
        "paginas": page_info
    }

    return resultado


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python pdf_check.py <ruta_al_pdf>")
        print("Ejemplo: python pdf_check.py 'certificado.pdf'")
        sys.exit(1)

    pdf_path = sys.argv[1]
    r = check_pdf(pdf_path)

    print(f"\n{'='*60}")
    print(f"  DIAGNÓSTICO PDF: {r['archivo']}")
    print(f"{'='*60}")
    print(f"  Tipo: {r['tipo']}")
    print(f"  Caracteres totales: {r['total_chars']}")
    print(f"  Imágenes en el PDF: {r['total_imagenes']}")
    print(f"  Páginas analizadas: {len(r['paginas'])}")
    print()
    for p in r["paginas"]:
        print(f"  Pág {p['pagina']}: {p['chars']} chars | {p['imagenes']} imgs | '{p['muestra']}'")
    print(f"{'='*60}\n")

    if r["tipo"] == "IMAGEN_PURA (OCR necesario)":
        print("⚠  ACCIÓN REQUERIDA: Este PDF no tiene texto extraíble.")
        print("   → Usá el Nivel 5 (Gemini OCR) de la skill 'reading-pdfs'.")
    else:
        print("✓ Este PDF tiene texto extraíble directamente con fitz.")
