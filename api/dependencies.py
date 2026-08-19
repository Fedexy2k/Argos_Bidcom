"""
api/dependencies.py
===================
Shared state, singletons, logging, and common utilities for FastAPI routers.
Zero circular dependencies.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, WebSocket

# Root path setup
ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "m3_config.json"
PORT = 8742

# ── Environment Variables ──────────────────────────────────────────────────────
_env_file = ROOT / ".env"
if _env_file.exists():
    with open(_env_file, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())


# ── WebSocket Log Broadcaster ─────────────────────────────────────────────────

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
            pass

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
    """Adapter: forwards module logs directly to the WebSocket broadcaster."""

    def log(self, msg: str, level: str = "INFO"):
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


gui_logger = GUILogger()


# ── Shared File Upload Helpers ────────────────────────────────────────────────

async def save_upload(upload: UploadFile) -> str:
    """Saves an upload to a temporary file and returns its path."""
    suffix = Path(upload.filename or "file.pdf").suffix
    fd, path = tempfile.mkstemp(suffix=suffix)
    content = await upload.read()
    with os.fdopen(fd, "wb") as f:
        f.write(content)
    return path


def cleanup_path(path: Optional[str]):
    """Deletes a temporary file safely."""
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass
