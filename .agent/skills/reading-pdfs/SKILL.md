---
name: reading-pdfs
description: Extrae texto de PDFs de forma robusta con estrategia de múltiples intentos. Úsala cuando haya que leer certificados, resoluciones u otros PDFs que pueden estar escaneados, tener capas de imagen o ser difíciles de parsear.
---

# Lectura Robusta de PDFs

## Cuándo usar esta habilidad
- El PDF puede ser un escaneado (imagen) o tener capas mixtas.
- `fitz.get_text()` devuelve texto vacío, muy corto o sin sentido.
- Se trabaja con certificados, resoluciones o datasheets técnicos argentinos.

> [!IMPORTANT]
> Siempre intentar Nivel 1 y 2 primero. El Nivel 5 (OCR con IA) gasta tokens y es más lento — **solo como último recurso**.

---

## Instrucciones

### 0. Idioma
**Español de Latinoamérica** en toda explicación, log y documentación generada.

---

### Estrategia multinivel — función única

```python
import fitz, os, re

def extract_pdf_text(pdf_path: str, api_key: str = None) -> str:
    """
    Extrae texto de un PDF con estrategia multinivel automática.
    Nivel 1 → texto nativo │ Nivel 2 → coordenadas │ Nivel 3 → bloques │ Nivel 5 → OCR Gemini
    """
    doc = fitz.open(pdf_path)

    # Nivel 1: texto nativo simple
    text = "".join(p.get_text() for p in doc)
    if len(text.strip()) >= 100:
        doc.close()
        return text

    # Nivel 2: texto ordenado por coordenadas (layout roto / columnas)
    text_sorted = "".join(p.get_text("text", sort=True) for p in doc)
    if len(text_sorted.strip()) >= 100:
        doc.close()
        return text_sorted

    # Nivel 3: bloques manuales reordenados
    text_blocks = ""
    for page in doc:
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (round(b[1], 5), b[0]))  # y0 luego x0
        for b in blocks:
            if b[6] == 0:  # tipo texto
                text_blocks += b[4]
    if len(text_blocks.strip()) >= 100:
        doc.close()
        return text_blocks

    # Nivel 5: OCR con Gemini Vision (imagen pura / escaneado)
    doc.close()
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("PDF sin texto y sin GEMINI_API_KEY para OCR.")
    return _ocr_with_gemini(pdf_path, api_key)


def _ocr_with_gemini(pdf_path: str, api_key: str) -> str:
    """
    OCR página a página con Gemini — SDK nueva google.genai.
    Resolución 2x para mejor calidad de OCR.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    MODEL = "gemini-2.5-flash-lite"   # modelo vigente con mejor eficiencia de tokens

    doc = fitz.open(pdf_path)
    pages_text = []
    for page in doc:
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                "Extraé SOLO el texto de esta imagen de documento. "
                "Sin comentarios ni formato markdown. "
                "Preservá el orden de lectura natural (izq→der, arriba→abajo). "
                "Transcribí todos los campos técnicos completos.",
                types.Part.from_bytes(data=img_bytes, mime_type="image/png")
            ]
        )
        pages_text.append(response.text.strip())
    doc.close()
    return "\n".join(pages_text)
```

> [!WARNING]
> El paquete `google.generativeai` está **deprecado**. Siempre usar `from google import genai` (paquete `google-genai`).
> El modelo `gemini-2.0-flash` fue dado de baja. Usar `gemini-2.5-flash-lite`.

---

### Diagnóstico rápido de calidad

```python
def diagnose_extraction(text: str, filename: str) -> dict:
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    return {
        "archivo":       filename,
        "chars_totales": len(text),
        "lineas":        len(lines),
        "es_util":       len(text.strip()) > 100,
        "muestra":       lines[:5],
    }
```

---

### Limpieza de texto (documentos argentinos)

```python
def clean_cert_text(text: str) -> str:
    """Normalización básica para certificados y resoluciones INAL/Argos."""
    text = re.sub(r'\s+', ' ', text)                                              # colapsar espacios
    text = re.sub(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', r'\1/\2/\3', text)    # fechas → dd/mm/yyyy
    text = ''.join(c for c in text if c.isprintable() or c == '\n')               # quitar ctrl chars
    return text.strip()
```

---

## Checklist de uso
- [ ] Llamé a `extract_pdf_text()` — intenta Niveles 1→2→3→5 automáticamente.
- [ ] Verifiqué calidad con `diagnose_extraction()`.
- [ ] Apliqué `clean_cert_text()` antes de procesar con regex.
- [ ] Si usé OCR (Nivel 5), confirmé que el costo de API es aceptable.


# Lectura Robusta de PDFs
