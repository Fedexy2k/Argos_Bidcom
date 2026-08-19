"""
api/routers/health.py
=====================
Healthcheck and system configuration endpoints.
"""
from __future__ import annotations

import json
from fastapi import APIRouter

from api.dependencies import CONFIG_PATH, ROOT
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter(tags=["Health & Config"])


class EnvConfigPayload(BaseModel):
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None


@router.get("/api/health")
def health_check():
    """Returns the API health status and current semantic version."""
    return {"status": "ok", "version": "3.2.1"}


@router.get("/api/config")
async def get_config():
    """Returns the full m3_config.json as JSON."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


@router.put("/api/config")
async def save_config(payload: dict):
    """Saves updated m3_config.json."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)
    return {"ok": True}


@router.get("/api/health/ai")
def ai_health_check():
    """Checks whether AI provider API keys are configured and available."""
    openai_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
    gemini_key = bool(os.getenv("GEMINI_API_KEY", "").strip())
    
    providers = []
    if openai_key:
        providers.append("OpenAI (gpt-4o-mini)")
    if gemini_key:
        providers.append("Gemini (2.5-flash-lite)")
        
    status = "ok" if (openai_key or gemini_key) else "missing_keys"
    
    return {
        "status": status,
        "openai_configured": openai_key,
        "gemini_configured": gemini_key,
        "providers": providers,
    }


@router.post("/api/config/env")
async def save_env_keys(payload: EnvConfigPayload):
    """Guarda las API keys en el archivo .env y actualiza las variables de entorno en tiempo de ejecución."""
    env_path = ROOT / ".env"
    
    current_vars = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    current_vars[k.strip()] = v.strip()
                    
    if payload.openai_api_key is not None:
        val = payload.openai_api_key.strip()
        if val:
            current_vars["OPENAI_API_KEY"] = val
            os.environ["OPENAI_API_KEY"] = val
        elif "OPENAI_API_KEY" in current_vars:
            del current_vars["OPENAI_API_KEY"]
            os.environ.pop("OPENAI_API_KEY", None)
            
    if payload.gemini_api_key is not None:
        val = payload.gemini_api_key.strip()
        if val:
            current_vars["GEMINI_API_KEY"] = val
            os.environ["GEMINI_API_KEY"] = val
        elif "GEMINI_API_KEY" in current_vars:
            del current_vars["GEMINI_API_KEY"]
            os.environ.pop("GEMINI_API_KEY", None)

    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in current_vars.items():
            f.write(f"{k}={v}\n")
            
    return ai_health_check()
