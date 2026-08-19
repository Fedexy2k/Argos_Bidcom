"""
api/main.py
===========
Argos API — FastAPI backend entry point.
Modular architecture with clean router separation.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.dependencies import PORT, ROOT, log_broadcaster
from api.routers import budget, djc, ee, health, solicitud, verify


# ── App Lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(log_broadcaster._broadcast_loop())
    yield
    task.cancel()


# ── FastAPI Instance ──────────────────────────────────────────────────────────

app = FastAPI(
    title="Argos API",
    version="3.2.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── WebSocket: Live Logs ──────────────────────────────────────────────────────

@app.websocket("/ws/log")
async def ws_log(websocket: WebSocket):
    await websocket.accept()
    log_broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive pings
    except WebSocketDisconnect:
        log_broadcaster.disconnect(websocket)


# ── Mount Routers ─────────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(budget.router)
app.include_router(djc.router)
app.include_router(ee.router)
app.include_router(solicitud.router)
app.include_router(verify.router)


# ── Frontend Static Files (SPA) ───────────────────────────────────────────────

frontend_path = ROOT / "frontend" / "dist"
if frontend_path.exists():
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


# ── Local Development Entry Point ─────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=PORT,
        log_level="warning",
        reload=False,
    )
