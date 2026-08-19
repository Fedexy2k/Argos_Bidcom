"""
api/routers/solicitud.py
========================
Solicitud generation and parsing endpoints (M5).
"""
from __future__ import annotations

import io
import json
import os
import tempfile
import traceback
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from api.dependencies import CONFIG_PATH, gui_logger, log_broadcaster
from modules.m5_solicitud_generator import parse_datasheet, generate_solicitud

router = APIRouter(prefix="/api/solicitud", tags=["Solicitudes (M5)"])


@router.post("/parse")
async def solicitud_parse(file: UploadFile = File(...)):
    """
    Carga el Excel de ingeniería o PDF y retorna un JSON estructurado con:
      - oec_detected: 'lenor' | 'qetkra'
      - certificado, producto, normas, laboratorio, fabrica, ...
      - skus: lista de bloques con modelos y especificaciones técnicas
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se recibió archivo.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".xlsx", ".xlsm", ".xls", ".pdf"):
        raise HTTPException(status_code=400, detail=f"Formato no soportado: {suffix}. Use .xlsx, .xlsm o .pdf")

    tmp_path: str | None = None
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        gui_logger.info(f"[Solicitud/Parse] Parseando archivo subido: {file.filename}")
        
        if suffix == ".pdf":
            from modules.m3_djc_generator import DJCGenerator
            from modules.m5_solicitud_generator import parse_specs_string
            
            gui_logger.info("[Solicitud/Parse] Detectado archivo PDF de certificado. Ejecutando motor de extracción...")
            gen = DJCGenerator(config_path=str(CONFIG_PATH), gui_logger=gui_logger)
            cert_data = gen.prepare_from_certificate(tmp_path)
            
            oec_key = cert_data.get("oec_key", "")
            oec_detected = "lenor"
            if oec_key and oec_key.lower() in ("quektra", "qetkra"):
                oec_detected = "qetkra"
            elif oec_key and ("tuv" in oec_key.lower() or "tüv" in oec_key.lower()):
                oec_detected = "tuv"
                
            modelos_str = cert_data.get("modelos", "")
            modelos_list = [m.strip() for m in modelos_str.split(",") if m.strip()]
            first_model = modelos_list[0] if modelos_list else "MODELO_BASE"
            
            raw_specs = cert_data.get("specs", "")
            parsed_specs = parse_specs_string(raw_specs) if raw_specs else {}
            
            sku_block = {
                "sku": first_model,
                "marca": cert_data.get("marca", "") or "SIN_MARCA",
                "modelos": modelos_list,
                "modelo_fabrica": "---",
                "tension": parsed_specs.get("tension", "") or "---",
                "frecuencia": parsed_specs.get("frecuencia", "") or "---",
                "corriente": parsed_specs.get("corriente", "") or "---",
                "potencia": parsed_specs.get("potencia", "") or "---",
                "aislacion": parsed_specs.get("aislacion", "") or "---",
                "specs": raw_specs or "---"
            }
            
            data = {
                "oec_detected": oec_detected,
                "certificado": cert_data.get("cert_number", "") or "SIN_NRO",
                "producto": cert_data.get("producto_desc", "") or "---",
                "motivo": "Renovación / Certificación documental",
                "oec": cert_data.get("oec_key", "") or "LENOR",
                "normas": cert_data.get("normas", "") or "---",
                "laboratorio": cert_data.get("oec_key", "") or "LENOR",
                "reglamento": cert_data.get("reglamento", "") or "---",
                "fabrica": cert_data.get("fabricante", "") or "---",
                "direccion": cert_data.get("direccion_fabrica", "") or "---",
                "contacto": "",
                "email": "",
                "telefono": "",
                "skus": [sku_block]
            }
        else:
            data = parse_datasheet(tmp_path, logger=gui_logger)
            
        return JSONResponse(content=data)

    except Exception as e:
        log_broadcaster.push("error", f"[Solicitud/Parse] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al parsear el datasheet: {e}")
    finally:
        try:
            if tmp_path:
                os.unlink(tmp_path)
        except Exception:
            pass


@router.post("/generate")
async def solicitud_generate(
    request_json: str = Form(...),
    svg_file: Optional[UploadFile] = File(default=None),
):
    """
    Genera los archivos de solicitud (Excel + Word + PDF QR opcional) y
    retorna el ZIP en streaming.
    """
    try:
        req = json.loads(request_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON inválido: {e}")

    data = req.get("data", {})
    oec = req.get("oec", "lenor").lower()
    esquema = req.get("esquema", "")

    if not data:
        raise HTTPException(status_code=400, detail="El campo 'data' es requerido.")

    svg_bytes: Optional[bytes] = None
    if svg_file and svg_file.filename:
        svg_bytes = await svg_file.read()

    try:
        gui_logger.info(f"[Solicitud/Generate] Iniciando generación OEC={oec}, Nro={data.get('certificado','?')}")
        result = generate_solicitud(data=data, oec=oec, esquema=esquema, svg_bytes=svg_bytes, logger=gui_logger)
        gui_logger.info(f"[Solicitud/Generate] Generado en {result['output_dir']} — {len(result['files'])} archivos")

        zip_bytes = result["zip_bytes"]
        nro = data.get("certificado", "solicitud")
        filename = f"Solicitud_{nro}.zip"

        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_broadcaster.push("error", f"[Solicitud/Generate] {type(e).__name__}: {e}")
        log_broadcaster.push("error", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error al generar la solicitud: {e}")
