"""
Argos API — FastAPI backend
Wraps the existing M1/M2/M3 Python modules as REST endpoints.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
import shutil
import tempfile
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import (
    FastAPI, File, Form, HTTPException, UploadFile, WebSocket,
    WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent   # → Argos Proyect/
sys.path.insert(0, str(ROOT))

# Cargar variables de entorno desde .env si existe (para API keys locales)
_env_file = ROOT / ".env"
if _env_file.exists():
    with open(_env_file, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from modules.m3_djc_generator import DJCGenerator
from modules.m2_multiaudit import MultiCertAuditor

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_PATH = ROOT / "m3_config.json"
PORT = 8742

# ── WebSocket log manager ─────────────────────────────────────────────────────

class LogBroadcaster:
    """Broadcasts log messages to all connected WebSocket clients."""

    def __init__(self):
        self._clients: list[WebSocket] = []
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=500)

    def connect(self, ws: WebSocket):
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._clients:
            self._clients.remove(ws)

    def push(self, level: str, message: str):
        """Sync-safe: puts a log entry into the queue (from any thread)."""
        entry = json.dumps({"level": level, "msg": message})
        try:
            self._queue.put_nowait(entry)
        except asyncio.QueueFull:
            pass  # drop if backpressure

    async def _broadcast_loop(self):
        while True:
            entry = await self._queue.get()
            dead = []
            for ws in list(self._clients):
                try:
                    await ws.send_text(entry)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws)

log_broadcaster = LogBroadcaster()


class GUILogger:
    """Adapter: makes DJCGenerator / MultiAudit / dispatcher log into the broadcaster."""

    def log(self, msg: str, level: str = "INFO"):
        """Método que llama DJCGenerator._log() → gui_logger.log(msg, level).
        Sin este método, todos los logs del dispatcher y de la IA se tragaban silenciosamente."""
        level_lower = level.lower()
        log_broadcaster.push(
            level_lower if level_lower in ("info", "warning", "error", "debug") else "info",
            msg
        )

    def info(self, msg: str):
        log_broadcaster.push("info", msg)

    def warning(self, msg: str):
        log_broadcaster.push("warning", msg)

    def error(self, msg: str):
        log_broadcaster.push("error", msg)

    def debug(self, msg: str):
        log_broadcaster.push("debug", msg)


# ── App startup ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(log_broadcaster._broadcast_loop())
    yield
    task.cancel()


app = FastAPI(title="Argos API", version="2.0.3", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared logger ─────────────────────────────────────────────────────────────
_gui_logger = GUILogger()


# ─────────────────────────────────────────────────────────────────────────────
#  WebSocket: live logs
# ─────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws/log")
async def ws_log(websocket: WebSocket):
    await websocket.accept()
    log_broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()   # keep-alive pings
    except WebSocketDisconnect:
        log_broadcaster.disconnect(websocket)


# ─────────────────────────────────────────────────────────────────────────────
#  Config endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/config")
async def get_config():
    """Returns the full m3_config.json as JSON."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


@app.put("/api/config")
async def save_config(payload: dict):
    """Saves updated m3_config.json."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────
#  DJC: extract certificate data
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/djc/extract")
async def extract_cert(file: UploadFile = File(...)):
    """
    Receives a certificate PDF, returns extracted fields:
    cert_number, normas, oec_key, fecha_emision, fabricante, direccion, etc.
    """
    tmp_path = await _save_upload(file)
    try:
        gen = DJCGenerator(config_path=str(CONFIG_PATH), gui_logger=_gui_logger)
        data = gen.prepare_from_certificate(tmp_path)
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
            "specs":             data.get("specs", ""),
            "reglamento":        data.get("reglamento", ""),
        }
    except Exception as e:
        _gui_logger.error(f"extract error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _cleanup(tmp_path)


# ─────────────────────────────────────────────────────────────────────────────
#  DJC: generate (Normal and/or Codificada)
# ─────────────────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    # Versiones a generar
    versiones: list[str]          # ["normal", "codificada"]
    modo: str                     # "comun" | "extension" | "extension_terceros"
    # Identificación (editada por el usuario en el formulario)
    djc_id: str = ""              # ID editado en el frontend
    enlace_djc: str = ""          # Enlace QR editado en el frontend
    # Datos del certificate (rellenados por el frontend después de /extract o editados)
    cert_number: str = ""
    oec_key: str = ""
    normas: str = ""
    fecha_emision: str = ""
    fecha_vencimiento: str = ""
    fecha_vigilancia: str = "---"  # '---' si cert nuevo, fecha real si hubo vigilancia previa
    fabricante: str = ""
    direccion: str = ""
    marca: str = ""
    modelos: str = ""
    producto_desc: str = ""
    specs: str = ""
    bidcom_num: str = ""
    reglamento: str = ""
    esquema: str = ""
    # Extension options
    sociedades: list[str] = []    # ["Bemotec S.R.L.", ...]
    empresa_override: dict = {}   # solo en modo extension_terceros: sobreescribe config["empresa"]
    # Output
    output_dir: str = ""          # "" = temp dir (preview mode)
    save_to_disk: bool = False


@app.post("/api/djc/generate")
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
    tmp_cert = await _save_upload(cert_file)
    tmp_nota = await _save_upload(nota_file) if nota_file and nota_file.filename else None

    results = []
    try:
        gen = DJCGenerator(config_path=str(CONFIG_PATH), gui_logger=_gui_logger)

        # Build the base data dict
        data = _build_data_dict(req, gen)

        # ── Resumen de la solicitud ───────────────────────────────────────
        bidcom_display = req.bidcom_num or '[sin bidcom]'
        _gui_logger.info(
            f"[API] ═══ INICIANDO GENERACIÓN DJC ═══"
        )
        _gui_logger.info(
            f"[API]   Modo: {req.modo.upper()} | "
            f"Versiones: {', '.join(req.versiones)} | "
            f"Bidcom: {bidcom_display}"
        )
        _gui_logger.info(
            f"[API]   DJC-ID: {data.get('djc_id', '?')} | "
            f"OEC: {req.oec_key} | Reglamento: {req.reglamento[:60] if req.reglamento else '?'}"
        )
        _gui_logger.info(
            f"[API]   Fabricante: {req.fabricante[:50] if req.fabricante else '[no]'} | "
            f"Marca: {req.marca or '[no]'}"
        )
        if req.modo == "extension":
            _gui_logger.info(
                f"[API]   Sociedades ({len(req.sociedades)}): {', '.join(req.sociedades)}"
            )
        if nota_file and nota_file.filename:
            _gui_logger.info(f"[API]   Nota de extensión adjunta: {nota_file.filename}")

        total_runs = len(req.versiones) * max(len(req.sociedades), 1)
        run_n = 0

        for version in req.versiones:
            is_codificada = (version == "codificada")

            if req.modo in ("comun", "extension_terceros"):
                societies_list = [None]   # single run, no society injection
            else:
                societies_list = req.sociedades or []
                if not societies_list:
                    raise HTTPException(400, "modo extension requiere al menos una sociedad")

            for society_key in societies_list:
                run_n += 1
                run_data = dict(data)
                censor_terms = None

                soc_display = society_key or "—"
                _gui_logger.info(
                    f"[API] ► Tarea {run_n}/{total_runs}: versión={version} | sociedad={soc_display}"
                )

                if is_codificada:
                    _gui_logger.info("[API]   → Aplicando modo CODIFICADA (enmascarando fabricante/dirección)")
                    run_data, censor_terms = _apply_codificada(run_data, gen)
                    _gui_logger.info(f"[API]   → Fabricante reemplazado por: '{run_data['fabricante'][:60]}'")

                if society_key:
                    soc_cfg = gen.config.get("sociedades_extension", {}).get(society_key, {})
                    _gui_logger.info(
                        f"[API]   → Inyectando sociedad: '{soc_cfg.get('nombre', society_key)}' "
                        f"(CUIT: {soc_cfg.get('cuit', 'N/A')})"
                    )
                    run_data = _inject_society(run_data, society_key, gen)

                _gui_logger.info(f"[API]   → Ejecutando pipeline de generación...")
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
                    _gui_logger.error(f"[API] PDF sospechosamente pequeño: {len(pdf_bytes)} bytes")
                else:
                    _gui_logger.info(
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

        _gui_logger.info(
            f"[API] ═══ GENERACIÓN COMPLETA: {len(results)} archivo(s) listos para preview ═══"
        )
        return {"results": results}

    except HTTPException:
        raise
    except Exception as e:
        _gui_logger.error(f"[API] generate error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _cleanup(tmp_cert)
        if tmp_nota:
            _cleanup(tmp_nota)


# ─────────────────────────────────────────────────────────────────────────────
#  DJC: confirm preview → save to disk
# ─────────────────────────────────────────────────────────────────────────────

class ConfirmItem(BaseModel):
    filename: str          # ej: DJC-SE-0426-C383-LNR-V1.pdf
    bidcom_num: str        # ej: C383  (para la carpeta)
    society_key: str = "" # solo para extensiones
    pdf_b64: str           # datos del PDF en base64

class ConfirmRequest(BaseModel):
    items: list[ConfirmItem]

@app.post("/api/djc/confirm")
async def confirm_djc(req: ConfirmRequest):
    """
    El usuario aceptó la previsualización: guarda los PDFs en disco.
    Equivalente al 'Sí' del messagebox legacy.
    """
    saved = []
    import re as _re
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
                safe_soc = _re.sub(r'[\\/:*?"<>|]', "-", item.society_key)
                save_dir = os.path.join(save_dir, "Extensiones", safe_soc)

            os.makedirs(save_dir, exist_ok=True)
            safe_fname = _re.sub(r'[\\/:*?"<>|]', "-", item.filename)
            if not safe_fname.endswith(".pdf"):
                safe_fname += ".pdf"

            save_path = os.path.join(save_dir, safe_fname)
            # Si ya existe, agregar timestamp
            if os.path.exists(save_path):
                import time as _t
                stem = safe_fname[:-4]
                save_path = os.path.join(save_dir, f"{stem}_{int(_t.time())}.pdf")

            with open(save_path, "wb") as f:
                f.write(pdf_bytes)

            _gui_logger.info(f"[API] ✓ Confirmado y guardado: {save_path}")
            saved.append(save_path)
        except Exception as e:
            _gui_logger.error(f"[API] Error guardando {item.filename}: {e}")

    _gui_logger.info(f"[API] === DJC CONFIRMADA POR USUARIO ({len(saved)} archivo(s) guardado(s)) ===")
    return {"saved": saved}


# ─────────────────────────────────────────────────────────────────────────────
#  Verification (M2)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/verify")
async def verify_certs(files: list[UploadFile] = File(...)):
    """
    Receives one or more certificate PDFs, runs MultiAudit, returns results.
    """
    tmp_paths = []
    try:
        for f in files:
            tmp_paths.append(await _save_upload(f))

        auditor = MultiCertAuditor(logger=_gui_logger)
        # Build a simple json_data structure and paths dict for the auditor
        pdf_paths_dict = {os.path.basename(p).replace('.pdf','').replace('.PDF',''): p for p in tmp_paths}
        json_data = {"certificados_requeridos": [{"tipo": k} for k in pdf_paths_dict], "tipo_producto": "UNKNOWN"}
        report = auditor.audit_multiple(json_data, pdf_paths_dict)
        return {"report": report}
    except Exception as e:
        _gui_logger.error(f"[API] verify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in tmp_paths:
            _cleanup(p)


# ─────────────────────────────────────────────────────────────────────────────
#  Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.3"}


# ─────────────────────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _save_upload(upload: UploadFile) -> str:
    """Saves an upload to a temp file and returns its path."""
    suffix = Path(upload.filename or "file.pdf").suffix
    fd, path = tempfile.mkstemp(suffix=suffix)
    content = await upload.read()
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    return path



def _cleanup(path: Optional[str]):
    """Deletes a temp file."""
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def _build_data_dict(req: GenerateRequest, gen: DJCGenerator) -> dict:
    """Builds the data dict expected by DJCGenerator.fill_template()."""
    cfg = gen.config
    oec_info = cfg.get("oec_options", {}).get(req.oec_key, {})

    # Normalizar bidcom: siempre C + número
    raw_bidcom = (req.bidcom_num or "").strip()
    num_bidcom = raw_bidcom.lstrip("Cc") if raw_bidcom else ""
    bidcom_display = f"C{num_bidcom}" if num_bidcom else ""

    # DJC ID: si el frontend lo editó úsalo; si no, auto-generar
    djc_id = (req.djc_id.strip() if hasattr(req, 'djc_id') and req.djc_id else None) or gen.generate_djc_id(
        reglamento=req.reglamento,
        oec_nombre=oec_info.get("nombre", req.oec_key),
        bidcom_num=bidcom_display or None,
    )

    # Enlace QR: https://qr.gadnic.com/certifications/certificacion-{NUM_BIDCOM}
    enlace_djc = (req.enlace_djc.strip() if hasattr(req, 'enlace_djc') and req.enlace_djc else None) \
        or f"https://qr.gadnic.com/certifications/certificacion-{num_bidcom}" if num_bidcom \
        else ""

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

    # Modo extensión de terceros: BIDCOM como importador/representante autorizado
    # y opcionalmente datos de empresa sobreescritos (los 7 campos editables)
    if req.modo == "extension_terceros":
        # 1. Representante Autorizado fijo (Tabla 2)
        data["representante"] = {
            "nombre":    "BIDCOM SRL",
            "cuit":      "30-71106936-0",
            "domicilio": "Bouchard 468, 5° I, CABA. CP 1004",
        }
        
        # 2. Información del Importador / Empresa editable (Tabla 1)
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
    """Masks fabricante/dirección and returns censor_terms for PDF."""
    import re
    fab_original = data.get("fabricante", "")
    dir_original = data.get("direccion_fabrica", "")

    # Detect country from address
    country_map = {
        "china": "China", "korea": "Corea", "taiwan": "Taiwan",
        "india": "India", "vietnam": "Vietnam", "japan": "Japón",
        "japon": "Japón", "usa": "EE.UU.",
    }
    pais = ""
    # Buscar país en dirección Y en nombre del fabricante (igual que legacy)
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
    """Injects the extension society as representante in data, and appends its
    code to the DJC-ID (e.g. DJC-SE-0226-C912-ITK-V1 → DJC-SE-0226-C912-ITK-BEMO-V1)."""
    import re as _re
    soc = gen.config.get("sociedades_extension", {}).get(society_key, {})
    new_data = dict(data)

    # Inyectar representante
    new_data["representante"] = {
        "nombre":   soc.get("nombre", society_key),
        "cuit":     soc.get("cuit", ""),
        "domicilio": soc.get("domicilio", ""),
    }

    # Actualizar DJC-ID: insertar codigo ANTES del sufijo -Vx
    # DJC-SE-0226-C912-ITK-V1 + BEMO  →  DJC-SE-0226-C912-ITK-BEMO-V1
    soc_codigo = soc.get("codigo", "")
    if soc_codigo:
        base_id = new_data.get("djc_id", "")
        m = _re.match(r'^(.*?)(-V\d+)$', base_id)
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
    """Core: fill template, export to PDF, optionally censor cert, merge, return bytes."""
    import fitz
    import time as _t

    tmp_dir = tempfile.mkdtemp()
    t0 = _t.monotonic()
    try:
        stem = data.get("djc_id", "DJC").replace("/", "-").replace("\\", "-")
        _gui_logger.info(f"[Pipeline] ID: {stem}")

        # 1. Fill Word template
        _gui_logger.info("[Pipeline] 1/4 Llenando plantilla Word...")
        doc_word = gen.fill_template(data)
        word_path = os.path.join(tmp_dir, f"{stem}.docx")
        doc_word.save(word_path)
        _gui_logger.info(f"[Pipeline]      Word guardado: {os.path.basename(word_path)}")

        # 2. Export Word → PDF
        _gui_logger.info("[Pipeline] 2/4 Convirtiendo Word a PDF (LibreOffice)...")
        djc_pdf_path = gen.export_to_pdf(word_path, os.path.join(tmp_dir, stem + ".pdf"))
        djc_size = os.path.getsize(djc_pdf_path)
        _gui_logger.info(f"[Pipeline]      PDF DJC: {djc_size:,} bytes")

        # 3. Optionally censor the cert
        cert_to_merge = cert_path
        if censor_terms:
            _gui_logger.info("[Pipeline] 3/4 Censurando certificado (modo codificada)...")
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
            _gui_logger.info(f"[Pipeline]      Cert censurado: {os.path.basename(censored_path)}")
        else:
            _gui_logger.info("[Pipeline] 3/4 Cert original (sin censura)")

        # 4. Merge DJC + (nota) + cert
        extra = [nota_path] if nota_path else None
        if extra:
            _gui_logger.info(f"[Pipeline] 4/4 Mergeando DJC + Nota + Cert ({len(extra)+2} PDFs)...")
        else:
            _gui_logger.info("[Pipeline] 4/4 Mergeando DJC + Cert...")
        merged_path = gen.merge_pdfs(djc_pdf_path, cert_to_merge, extra_pdfs=extra)
        merged_size = os.path.getsize(merged_path)
        elapsed = _t.monotonic() - t0
        _gui_logger.info(
            f"[Pipeline]      Merge completo: {merged_size:,} bytes | tiempo total: {elapsed:.1f}s"
        )

        # 5. Optionally copy to output_dir
        if save_to_disk and output_dir:
            os.makedirs(output_dir, exist_ok=True)
            dest = os.path.join(output_dir, os.path.basename(merged_path))
            shutil.copy2(merged_path, dest)
            _gui_logger.info(f"[Pipeline]      Guardado en disco: {dest}")

        with open(merged_path, "rb") as f:
            return f.read()

    except Exception as e:
        _gui_logger.error(f"[Pipeline] ERROR en generación: {type(e).__name__}: {e}")
        _gui_logger.error(traceback.format_exc())
        raise
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Frontend Static Files
# ─────────────────────────────────────────────────────────────────────────────

frontend_path = ROOT / "frontend" / "dist"
if frontend_path.exists():
    # Solo montamos /assets directamente
    assets_path = frontend_path / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Ignorar rutas API y WS
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        target_file = frontend_path / full_path
        if full_path and target_file.exists() and target_file.is_file():
            return FileResponse(target_file)
            
        # Fallback a index.html para react-router
        return FileResponse(frontend_path / "index.html")

# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=PORT,
        log_level="warning",
        reload=False,
    )
