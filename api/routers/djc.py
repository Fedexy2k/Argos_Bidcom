"""
api/routers/djc.py
==================
Declaración Jurada de Conformidad (DJC) generation, extraction, and confirmation endpoints.
"""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import tempfile
import time
import traceback
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from api.dependencies import CONFIG_PATH, gui_logger, save_upload, cleanup_path
from modules.m3_djc_generator import DJCGenerator, normalize_oec_key

router = APIRouter(prefix="/api/djc", tags=["DJC Generator"])


# ── Pydantic Models ───────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    versiones: list[str]          # ["normal", "codificada"]
    modo: str                     # "comun" | "extension" | "extension_terceros"
    djc_id: str = ""              # ID editado en el frontend
    enlace_djc: str = ""          # Enlace QR editado en el frontend
    cert_number: str = ""
    oec_key: str = ""
    normas: str = ""
    fecha_emision: str = ""
    fecha_vencimiento: str = ""
    fecha_vigilancia: str = "---"
    fabricante: str = ""
    direccion: str = ""
    marca: str = ""
    modelos: str = ""
    producto_desc: str = ""
    specs: str = ""
    bidcom_num: str = ""
    reglamento: str = ""
    esquema: str = ""
    sociedades: list[str] = []    # ["Bemotec S.R.L.", ...]
    empresa_override: dict = {}   # solo en modo extension_terceros
    output_dir: str = ""          # "" = temp dir (preview mode)
    save_to_disk: bool = False


class ConfirmItem(BaseModel):
    filename: str          # ej: DJC-SE-0426-C383-LNR-V1.pdf
    bidcom_num: str        # ej: C383 (para la carpeta)
    society_key: str = ""  # solo para extensiones
    pdf_b64: str           # datos del PDF en base64


class ConfirmRequest(BaseModel):
    items: list[ConfirmItem]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/extract")
async def extract_cert(file: UploadFile = File(...)):
    """
    Receives a certificate PDF, returns extracted fields:
    cert_number, normas, oec_key, fecha_emision, fabricante, direccion, etc.
    """
    tmp_path = await save_upload(file)
    try:
        gen = DJCGenerator(config_path=str(CONFIG_PATH), gui_logger=gui_logger)
        data = gen.prepare_from_certificate(tmp_path)
        specs_val = data.get("specs", "")
        reglamento_val = data.get("reglamento", "")
        if any(j in (reglamento_val or "").lower() for j in ["juguete", "163/2004", "nm 300", "lcj"]) and not (specs_val or "").strip():
            specs_val = "----"

        return {
            "cert_number":       data.get("cert_number", ""),
            "oec_key":           data.get("oec_key", ""),
            "normas":            data.get("normas", ""),
            "fecha_emision":     data.get("fecha_emision", ""),
            "fecha_vencimiento": data.get("fecha_proxima_vigilancia", ""),
            "fabricante":        data.get("fabricante", ""),
            "direccion":         data.get("direccion_fabrica", ""),
            "marca":             data.get("marca", ""),
            "modelos":           data.get("modelos", ""),
            "producto_desc":     data.get("producto_desc", ""),
            "specs":             specs_val,
            "reglamento":        reglamento_val,
        }
    except Exception as e:
        gui_logger.error(f"extract error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cleanup_path(tmp_path)


@router.post("/generate")
async def generate_djc(
    request_json: str = Form(...),
    cert_file: UploadFile = File(...),
    nota_file: Optional[UploadFile] = File(None),
):
    """
    Main DJC generation endpoint.
    Returns: list of { version, filename, pdf_b64 } objects.
    """
    req = GenerateRequest(**json.loads(request_json))
    tmp_cert = await save_upload(cert_file)
    tmp_nota = await save_upload(nota_file) if nota_file and nota_file.filename else None

    results = []
    try:
        gen = DJCGenerator(config_path=str(CONFIG_PATH), gui_logger=gui_logger)

        data = _build_data_dict(req, gen)

        bidcom_display = req.bidcom_num or '[sin bidcom]'
        gui_logger.info("[API] ═══ INICIANDO GENERACIÓN DJC ═══")
        gui_logger.info(
            f"[API]   Modo: {req.modo.upper()} | "
            f"Versiones: {', '.join(req.versiones)} | "
            f"Bidcom: {bidcom_display}"
        )
        gui_logger.info(
            f"[API]   DJC-ID: {data.get('djc_id', '?')} | "
            f"OEC: {req.oec_key} | Reglamento: {req.reglamento[:60] if req.reglamento else '?'}"
        )
        gui_logger.info(
            f"[API]   Fabricante: {req.fabricante[:50] if req.fabricante else '[no]'} | "
            f"Marca: {req.marca or '[no]'}"
        )
        if req.modo == "extension":
            gui_logger.info(f"[API]   Sociedades ({len(req.sociedades)}): {', '.join(req.sociedades)}")
        if nota_file and nota_file.filename:
            gui_logger.info(f"[API]   Nota de extensión adjunta: {nota_file.filename}")

        total_runs = len(req.versiones) * max(len(req.sociedades), 1)
        run_n = 0

        for version in req.versiones:
            is_codificada = (version == "codificada")

            if req.modo in ("comun", "extension_terceros"):
                societies_list = [None]
            else:
                societies_list = req.sociedades or []
                if not societies_list:
                    raise HTTPException(400, "modo extension requiere al menos una sociedad")

            for society_key in societies_list:
                run_n += 1
                run_data = dict(data)
                censor_terms = None

                soc_display = society_key or "—"
                gui_logger.info(f"[API] ► Tarea {run_n}/{total_runs}: versión={version} | sociedad={soc_display}")

                if is_codificada:
                    gui_logger.info("[API]   → Aplicando modo CODIFICADA (enmascarando fabricante/dirección)")
                    run_data, censor_terms = _apply_codificada(run_data, gen)
                    gui_logger.info(f"[API]   → Fabricante reemplazado por: '{run_data['fabricante'][:60]}'")

                if society_key:
                    soc_cfg = gen.config.get("sociedades_extension", {}).get(society_key, {})
                    gui_logger.info(
                        f"[API]   → Inyectando sociedad: '{soc_cfg.get('nombre', society_key)}' "
                        f"(CUIT: {soc_cfg.get('cuit', 'N/A')})"
                    )
                    run_data = _inject_society(run_data, society_key, gen)

                gui_logger.info("[API]   → Ejecutando pipeline de generación...")
                pdf_bytes = _run_generation(
                    gen=gen,
                    data=run_data,
                    cert_path=tmp_cert,
                    nota_path=tmp_nota,
                    censor_terms=censor_terms,
                    save_to_disk=req.save_to_disk,
                    output_dir=req.output_dir or None,
                )

                if len(pdf_bytes) < 1000:
                    gui_logger.error(f"[API] PDF sospechosamente pequeño: {len(pdf_bytes)} bytes")
                else:
                    gui_logger.info(
                        f"[API]   ✔ PDF OK: {len(pdf_bytes):,} bytes | versión: {version}"
                        + (f" | sociedad: {soc_display}" if society_key else "")
                    )

                label = version.capitalize()
                if society_key:
                    soc_info = gen.config.get("sociedades_extension", {}).get(society_key, {})
                    label += f" – {soc_info.get('codigo', society_key)}"

                results.append({
                    "version": version,
                    "society": society_key,
                    "label": label,
                    "pdf_b64": base64.b64encode(pdf_bytes).decode(),
                })

        gui_logger.info(f"[API] ═══ GENERACIÓN COMPLETA: {len(results)} archivo(s) listos para preview ═══")
        return {"results": results}

    except HTTPException:
        raise
    except Exception as e:
        gui_logger.error(f"[API] generate error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cleanup_path(tmp_cert)
        if tmp_nota:
            cleanup_path(tmp_nota)


@router.post("/confirm")
async def confirm_djc(req: ConfirmRequest):
    """
    El usuario aceptó la previsualización: guarda los PDFs en disco.
    """
    saved = []
    for item in req.items:
        try:
            pdf_bytes = base64.b64decode(item.pdf_b64)

            raw_bidcom = (item.bidcom_num or "").strip()
            num_only = raw_bidcom.lstrip("Cc") if raw_bidcom else ""
            bidcom_folder = f"C{num_only}" if num_only else "SIN-NUMERO"

            save_dir = os.path.join(
                os.path.expanduser("~"), "Documents", "DJC generadas", bidcom_folder
            )
            if item.society_key:
                safe_soc = re.sub(r'[\\/:*?"<>|]', "-", item.society_key)
                save_dir = os.path.join(save_dir, "Extensiones", safe_soc)

            os.makedirs(save_dir, exist_ok=True)
            safe_fname = re.sub(r'[\\/:*?"<>|]', "-", item.filename)
            if not safe_fname.endswith(".pdf"):
                safe_fname += ".pdf"

            save_path = os.path.join(save_dir, safe_fname)
            if os.path.exists(save_path):
                stem = safe_fname[:-4]
                save_path = os.path.join(save_dir, f"{stem}_{int(time.time())}.pdf")

            with open(save_path, "wb") as f:
                f.write(pdf_bytes)

            gui_logger.info(f"[API] ✓ Confirmado y guardado: {save_path}")
            saved.append(save_path)
        except Exception as e:
            gui_logger.error(f"[API] Error guardando {item.filename}: {e}")

    gui_logger.info(f"[API] === DJC CONFIRMADA POR USUARIO ({len(saved)} archivo(s) guardado(s)) ===")
    return {"saved": saved}


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _build_data_dict(req: GenerateRequest, gen: DJCGenerator) -> dict:
    cfg = gen.config
    normalized_oec_key = normalize_oec_key(req.oec_key)
    oec_info = cfg.get("oec_options", {}).get(normalized_oec_key, {})

    raw_bidcom = (req.bidcom_num or "").strip()
    num_bidcom = raw_bidcom.lstrip("Cc") if raw_bidcom else ""
    bidcom_display = f"C{num_bidcom}" if num_bidcom else ""

    djc_id = (req.djc_id.strip() if hasattr(req, 'djc_id') and req.djc_id else None) or gen.generate_djc_id(
        reglamento=req.reglamento,
        oec_nombre=oec_info.get("nombre", req.oec_key),
        bidcom_num=bidcom_display or None,
    )

    enlace_djc = (req.enlace_djc.strip() if hasattr(req, 'enlace_djc') and req.enlace_djc else None) \
        or (f"https://qr.gadnic.com/certifications/certificacion-{num_bidcom}" if num_bidcom else "")

    data = {
        "djc_id": djc_id,
        "fabricante": req.fabricante,
        "direccion_fabrica": req.direccion,
        "producto_desc": req.producto_desc,
        "marca": req.marca,
        "modelos": req.modelos,
        "specs": req.specs,
        "reglamento": req.reglamento,
        "normas": req.normas,
        "cert_number": req.cert_number,
        "esquema": req.esquema,
        "fecha_emision": req.fecha_emision,
        "fecha_vigilancia": req.fecha_vigilancia or "---",
        "fecha_proxima_vigilancia": req.fecha_vencimiento,
        "oec_nombre": oec_info.get("nombre", req.oec_key),
        "oec_contacto": oec_info.get("contacto", ""),
        "enlace_djc": enlace_djc,
    }

    if req.modo == "extension_terceros":
        data["representante"] = {
            "nombre":    "BIDCOM SRL",
            "cuit":      "30-71106936-0",
            "domicilio": "Bouchard 468, 5° I, CABA. CP 1004",
        }
        if req.empresa_override:
            data["empresa_override"] = req.empresa_override
        else:
            data["empresa_override"] = {
                "razon_social":     "BIDCOM SRL",
                "cuit":             "30-71106936-0",
                "marca_registrada": "BIDCOM SRL",
                "domicilio_legal":  "Bouchard 468, 5° I, CABA. CP 1004",
                "domicilio_deposito": "Caldas 1535, CABA, ARGENTINA",
                "telefono":         "3960-0184",
                "email":            "emanuel@bidcom.com.ar",
            }

    return data


def _apply_codificada(data: dict, gen: DJCGenerator) -> tuple[dict, dict]:
    fab_original = data.get("fabricante", "")
    dir_original = data.get("direccion_fabrica", "")

    country_map = {
        "china": "China", "korea": "Corea", "taiwan": "Taiwan",
        "india": "India", "vietnam": "Vietnam", "japan": "Japón",
        "japon": "Japón", "usa": "EE.UU.",
    }
    pais = ""
    search_text = (dir_original + " " + fab_original).lower()
    for kw, label in country_map.items():
        if kw in search_text:
            pais = label
            break

    restricted = f"Información Restringida - Res. SIyC 237/2024 ({pais})" if pais \
        else "Información Restringida - Res. SIyC 237/2024"
    new_data = dict(data)
    new_data["fabricante"] = restricted
    new_data["direccion_fabrica"] = restricted

    censor_terms = {
        "fabricante": fab_original,
        "direccion": dir_original,
    }
    return new_data, censor_terms


def _inject_society(data: dict, society_key: str, gen: DJCGenerator) -> dict:
    soc = gen.config.get("sociedades_extension", {}).get(society_key, {})
    new_data = dict(data)

    new_data["representante"] = {
        "nombre":   soc.get("nombre", society_key),
        "cuit":     soc.get("cuit", ""),
        "domicilio": soc.get("domicilio", ""),
    }

    soc_codigo = soc.get("codigo", "")
    if soc_codigo:
        base_id = new_data.get("djc_id", "")
        m = re.match(r'^(.*?)(-V\d+)$', base_id)
        if m:
            new_data["djc_id"] = f"{m.group(1)}-{soc_codigo}{m.group(2)}"
        elif base_id:
            new_data["djc_id"] = f"{base_id}-{soc_codigo}"

    return new_data


def _run_generation(
    gen: DJCGenerator,
    data: dict,
    cert_path: str,
    nota_path: Optional[str],
    censor_terms: Optional[dict],
    save_to_disk: bool,
    output_dir: Optional[str],
) -> bytes:
    import fitz

    tmp_dir = tempfile.mkdtemp()
    t0 = time.monotonic()
    try:
        stem = data.get("djc_id", "DJC").replace("/", "-").replace("\\", "-")
        gui_logger.info(f"[Pipeline] ID: {stem}")

        gui_logger.info("[Pipeline] 1/4 Llenando plantilla Word...")
        doc_word = gen.fill_template(data)
        word_path = os.path.join(tmp_dir, f"{stem}.docx")
        doc_word.save(word_path)
        gui_logger.info(f"[Pipeline]      Word guardado: {os.path.basename(word_path)}")

        gui_logger.info("[Pipeline] 2/4 Convirtiendo Word a PDF...")
        djc_pdf_path = gen.export_to_pdf(word_path, os.path.join(tmp_dir, stem + ".pdf"))
        djc_size = os.path.getsize(djc_pdf_path)
        gui_logger.info(f"[Pipeline]      PDF DJC: {djc_size:,} bytes")

        cert_to_merge = cert_path
        if censor_terms:
            gui_logger.info("[Pipeline] 3/4 Censurando certificado (modo codificada)...")
            cert_doc = fitz.open(cert_path)
            cert_doc = gen.censor_cert_pdf(
                cert_doc,
                fabricante=censor_terms["fabricante"],
                direccion=censor_terms["direccion"],
            )
            censored_path = os.path.join(tmp_dir, f"{stem}_cert_censored.pdf")
            cert_doc.save(censored_path)
            cert_doc.close()
            cert_to_merge = censored_path
            gui_logger.info(f"[Pipeline]      Cert censurado: {os.path.basename(censored_path)}")
        else:
            gui_logger.info("[Pipeline] 3/4 Cert original (sin censura)")

        extra = [nota_path] if nota_path else None
        if extra:
            gui_logger.info(f"[Pipeline] 4/4 Mergeando DJC + Nota + Cert ({len(extra)+2} PDFs)...")
        else:
            gui_logger.info("[Pipeline] 4/4 Mergeando DJC + Cert...")
        merged_path = gen.merge_pdfs(djc_pdf_path, cert_to_merge, extra_pdfs=extra)
        merged_size = os.path.getsize(merged_path)
        elapsed = time.monotonic() - t0
        gui_logger.info(
            f"[Pipeline]      Merge completo: {merged_size:,} bytes | tiempo total: {elapsed:.1f}s"
        )

        if save_to_disk and output_dir:
            os.makedirs(output_dir, exist_ok=True)
            dest = os.path.join(output_dir, os.path.basename(merged_path))
            shutil.copy2(merged_path, dest)
            gui_logger.info(f"[Pipeline]      Guardado en disco: {dest}")

        with open(merged_path, "rb") as f:
            return f.read()

    except Exception as e:
        gui_logger.error(f"[Pipeline] ERROR en generación: {type(e).__name__}: {e}")
        gui_logger.error(traceback.format_exc())
        raise
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
