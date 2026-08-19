"""
api/routers/verify.py
=====================
Certificate verification and multi-audit endpoints (M2).
"""
from __future__ import annotations

import os
from fastapi import APIRouter, File, HTTPException, UploadFile

from api.dependencies import gui_logger, save_upload, cleanup_path
from modules.m2_multiaudit import MultiCertAuditor

router = APIRouter(prefix="/api/verify", tags=["Verificación (M2)"])


@router.post("")
async def verify_certs(files: list[UploadFile] = File(...)):
    """
    Receives one or more certificate PDFs, runs MultiAudit, returns results.
    """
    tmp_paths = []
    try:
        for f in files:
            tmp_paths.append(await save_upload(f))

        auditor = MultiCertAuditor(logger=gui_logger)
        pdf_paths_dict = {os.path.basename(p).replace('.pdf','').replace('.PDF',''): p for p in tmp_paths}
        json_data = {"certificados_requeridos": [{"tipo": k} for k in pdf_paths_dict], "tipo_producto": "UNKNOWN"}
        report = auditor.audit_multiple(json_data, pdf_paths_dict)
        return {"report": report}
    except Exception as e:
        gui_logger.error(f"[API] verify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in tmp_paths:
            cleanup_path(p)
