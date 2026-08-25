"""
api/routers/ee.py
=================
Eficiencia Energética (EE) generation, family configurations, and auto-extraction endpoints.
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import shutil
import tempfile
import time
import traceback
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from api.dependencies import CONFIG_PATH, ROOT, gui_logger
from modules.m4_djc_ee_generator import DJCEEGenerator

router = APIRouter(prefix="/api/ee", tags=["Eficiencia Energética"])


# ── Pydantic Models ───────────────────────────────────────────────────────────

class EEGenerateRequest(BaseModel):
    family_id: str = ""
    bidcom_num: str = ""
    marca: str = ""
    modelo: str = ""
    producto_desc: str = ""
    base_specs: dict[str, Any] = {}
    ee_fields: dict[str, Any] = {}
    normas: str = ""
    cert_number: str = ""
    oec_nombre: str = ""
    oec_contacto: str = ""
    fecha_emision: str = ""
    fecha_proxima_vigilancia: str = ""
    fecha_emision_djc: str = ""
    label_images_base64: list[str] = []


class EEConfirmRequest(BaseModel):
    filename: str
    bidcom_num: str
    pdf_b64: str
    docx_b64: str


class EEExtractRequest(BaseModel):
    report_text: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/families")
async def get_ee_families():
    """Returns all efficiency energy product families and their dynamic fields."""
    ee_path = ROOT / "ee_families.json"
    with open(ee_path, encoding="utf-8") as f:
        return json.load(f)


@router.post("/generate")
async def generate_ee_djc(req: EEGenerateRequest):
    """Generates DJC-EE preview, returns PDF and DOCX in base64."""
    try:
        images_bytes: list[bytes] = []
        for b64_img in req.label_images_base64:
            if not b64_img:
                continue
            try:
                _header, encoded = b64_img.split(";base64,")
                images_bytes.append(base64.b64decode(encoded))
            except Exception as e:
                gui_logger.warning(f"Error al decodificar imagen de etiqueta: {e}")
        gui_logger.info(f"[API] {len(images_bytes)} imagen(es) de etiqueta decodificada(s).")

        ee_gen = DJCEEGenerator(config_path=str(CONFIG_PATH), ee_config_path=str(ROOT / "ee_families.json"))

        fecha_emision = (req.fecha_emision or "").strip()
        fecha_vencimiento = (req.fecha_proxima_vigilancia or "").strip()
        if not fecha_vencimiento and fecha_emision:
            try:
                from datetime import datetime
                dt = datetime.strptime(fecha_emision, "%d/%m/%Y")
                dt_venc = dt.replace(year=dt.year + 4)
                fecha_vencimiento = dt_venc.strftime("%d/%m/%Y")
            except Exception as e:
                gui_logger.warning(f"Error al calcular fecha vencimiento: {e}")

        djc_id = ee_gen.generate_djc_id(req.bidcom_num, fecha_emision)
        specs_text = ee_gen.build_specs_text(req.family_id, req.base_specs, req.ee_fields)

        normas = req.normas
        if not normas:
            fam = ee_gen.get_family_by_id(req.family_id)
            if fam:
                normas = fam.get("norma_base", "")

        data = {
            "djc_id": djc_id,
            "producto_desc": req.producto_desc,
            "marca": req.marca,
            "modelo": req.modelo,
            "specs": specs_text,
            "normas": normas,
            "cert_number": req.cert_number,
            "fecha_emision": fecha_emision,
            "fecha_proxima_vigilancia": fecha_vencimiento,
            "oec_nombre": req.oec_nombre,
            "oec_contacto": req.oec_contacto,
            "enlace_djc": f"https://qr.gadnic.com/certifications/certificado-{req.bidcom_num.lstrip('Cc')}-ee" if req.bidcom_num else "",
            "fecha_emision_djc": req.fecha_emision_djc,
        }

        gui_logger.info(f"[API] Generando previsualización DJC-EE ID: {djc_id}")

        tmp_dir = tempfile.mkdtemp()
        try:
            doc_word = ee_gen.fill_template_ee(data, images_bytes)
            stem = djc_id.replace("/", "-").replace("\\", "-")
            word_path = os.path.join(tmp_dir, f"{stem}.docx")
            doc_word.save(word_path)

            pdf_path = os.path.join(tmp_dir, f"{stem}.pdf")
            pdf_final_path = ee_gen.export_to_pdf(word_path, pdf_path)

            with open(pdf_final_path, "rb") as f:
                pdf_data = f.read()
            with open(word_path, "rb") as f:
                docx_data = f.read()

            return {
                "djc_id": djc_id,
                "filename": stem,
                "pdf_b64": base64.b64encode(pdf_data).decode(),
                "docx_b64": base64.b64encode(docx_data).decode(),
            }
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    except Exception as e:
        gui_logger.error(f"[API] Error generando DJC-EE: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm")
async def confirm_ee_djc(req: EEConfirmRequest):
    """Saves confirmed DJC-EE (both Word and PDF) to user's Documents/DJC folder."""
    try:
        pdf_bytes = base64.b64decode(req.pdf_b64)
        docx_bytes = base64.b64decode(req.docx_b64)

        raw_bidcom = (req.bidcom_num or "").strip()
        num_only = raw_bidcom.lstrip("Cc") if raw_bidcom else ""
        bidcom_folder = f"C{num_only}" if num_only else "SIN-NUMERO"

        save_dir = os.path.join(
            os.path.expanduser("~"), "Documents", "DJC generadas", bidcom_folder
        )
        os.makedirs(save_dir, exist_ok=True)

        safe_fname = re.sub(r'[\\/:*?"<>|]', "-", req.filename)
        
        pdf_save_path = os.path.join(save_dir, f"{safe_fname}.pdf")
        if os.path.exists(pdf_save_path):
            pdf_save_path = os.path.join(save_dir, f"{safe_fname}_{int(time.time())}.pdf")

        with open(pdf_save_path, "wb") as f:
            f.write(pdf_bytes)

        docx_save_path = os.path.join(save_dir, f"{safe_fname}.docx")
        if os.path.exists(docx_save_path):
            docx_save_path = os.path.join(save_dir, f"{safe_fname}_{int(time.time())}.docx")

        with open(docx_save_path, "wb") as f:
            f.write(docx_bytes)

        gui_logger.info(f"[API] ✓ Guardado DJC-EE Word: {docx_save_path}")
        gui_logger.info(f"[API] ✓ Guardado DJC-EE PDF: {pdf_save_path}")

        return {"saved": [pdf_save_path, docx_save_path]}
    except Exception as e:
        gui_logger.error(f"[API] Error al confirmar DJC-EE {req.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-extract")
def auto_extract_ee(req: EEExtractRequest):
    """Extrae automáticamente la familia y métricas de Eficiencia Energética usando IA."""
    try:
        generator = DJCEEGenerator()
        result = generator.auto_extract_ee_from_report(req.report_text)
        if not result:
            raise HTTPException(status_code=400, detail="No se pudo extraer información del informe EE.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al extraer Eficiencia Energética: {e}")


@router.post("/auto-extract-file")
async def auto_extract_ee_file(file: UploadFile = File(...)):
    """Extrae automáticamente la familia y métricas de Eficiencia Energética desde un archivo PDF subido."""
    try:
        pdf_bytes = await file.read()
        full_text = ""

        # 1. Intentar con PyMuPDF (fitz)
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            texts = [page.get_text() for page in doc if page.get_text()]
            full_text = "\n".join(texts)
        except Exception as e:
            gui_logger.warning(f"fitz text extraction warning: {e}")

        # 2. Fallback a pypdf
        if not full_text.strip():
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                texts = [page.extract_text() for page in reader.pages if page.extract_text()]
                full_text = "\n".join(texts)
            except Exception as e:
                gui_logger.warning(f"pypdf text extraction warning: {e}")

        if not full_text.strip():
            raise HTTPException(status_code=400, detail="El archivo PDF no contiene texto legible.")

        generator = DJCEEGenerator()
        result = generator.auto_extract_ee_from_report(full_text)
        if not result:
            raise HTTPException(status_code=400, detail="No se pudo extraer información del informe EE.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar archivo PDF de EE: {e}")
