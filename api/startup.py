"""
api/startup.py
Launches the FastAPI backend in a background thread, then opens the frontend.
In Tauri mode this file is NOT used (Tauri handles the shell command).
In dev mode (python startup.py) it opens the browser for testing.
"""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import threading

PYTHON  = sys.executable
API_DIR = Path(__file__).parent
HOST    = "127.0.0.1"
PORT    = 8742

def _start_server() -> subprocess.Popen:
    proc = subprocess.Popen(
        [PYTHON, str(API_DIR / "main.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc

def _wait_for_ready(retries: int = 30, delay: float = 0.5) -> bool:
    import urllib.request
    url = f"http://{HOST}:{PORT}/api/health"
    for _ in range(retries):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(delay)
    return False

if __name__ == "__main__":
    print("Starting Argos API backend...")
    proc = _start_server()
    if _wait_for_ready():
        print(f"API running at http://{HOST}:{PORT}")
        webbrowser.open(f"http://{HOST}:{PORT}/docs")  # Swagger UI for testing
    else:
        print("ERROR: API did not start in time.")
        proc.terminate()
        sys.exit(1)

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
