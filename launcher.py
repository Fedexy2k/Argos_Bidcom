import threading
import time
import urllib.request
import webbrowser
import sys
import os
import traceback

log_path = os.path.join(os.path.expanduser("~"), "Desktop", "argos_debug.log")
log_file = open(log_path, "w", encoding="utf-8")

if sys.stdout is None:
    sys.stdout = log_file
if sys.stderr is None:
    sys.stderr = log_file

try:
    import customtkinter as ctk
except ImportError:
    import tkinter as ctk

from api.main import app
import uvicorn
import asyncio
import socket

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

PORT = get_free_port()
URL = f"http://127.0.0.1:{PORT}"

def start_server():
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        # Hide uvicorn access logs for a cleaner console if run from CMD
        uvicorn.run(app, host="127.0.0.1", port=PORT, log_config=None)
    except Exception as e:
        print(f"ERROR Fatal al iniciar servidor: {e}")
        traceback.print_exc()
        log_file.flush()

def is_server_running():
    try:
        urllib.request.urlopen(f"{URL}/api/health", timeout=1)
        return True
    except Exception:
        return False

def open_app_mode():
    """Attempt to open in Chrome/Edge App Mode (borderless), fallback to default browser."""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    ]
    
    browser_opened = False
    for path in chrome_paths:
        if os.path.exists(path):
            try:
                import subprocess
                subprocess.Popen([path, f"--app={URL}"])
                browser_opened = True
                break
            except Exception:
                pass
                
    if not browser_opened:
        webbrowser.open(URL)

def main():
    if hasattr(ctk, 'set_appearance_mode'):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        root = ctk.CTk()
    else:
        root = ctk.Tk()
        
    root.title("Argos Server")
    root.geometry("450x220")
    root.resizable(False, False)
    
    # Try to set icon
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    server_thread = None
    launched = False

    def btn_start_clicked():
        nonlocal server_thread
        btn_start.configure(state="disabled")
        status_label.configure(text="Iniciando motor de red...", text_color="orange")
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        # No llamamos a check_and_launch aca porque ya hay un loop de after corriendo

    def check_and_launch():
        nonlocal launched
        if launched:
            return
        if is_server_running():
            launched = True
            if hasattr(ctk, 'CTkLabel'):
                status_label.configure(text="¡Servidor Activo y Escuchando!", text_color="#00FF41")
                open_btn.configure(state="normal")
            else:
                status_label.configure(text="¡Servidor Activo y Escuchando!", fg="green")
                open_btn.configure(state="normal")
            open_app_mode()
        else:
            root.after(1000, check_and_launch)

    # UI Elements
    if hasattr(ctk, 'CTkLabel'):
        title_font = ctk.CTkFont(size=22, weight="bold")
        ctk.CTkLabel(root, text="Argos V2.5.0", font=title_font).pack(pady=(15, 5))
        
        status_label = ctk.CTkLabel(root, text="Servidor Apagado.", text_color="gray")
        status_label.pack(pady=5)
        
        btn_start = ctk.CTkButton(root, text="▶ Iniciar Servidor", command=btn_start_clicked, fg_color="#4B0082", hover_color="#300055")
        btn_start.pack(pady=5)
        
        open_btn = ctk.CTkButton(root, text="Abrir Interfaz UI", command=open_app_mode, state="disabled")
        open_btn.pack(pady=5)
        
        ctk.CTkLabel(root, text="Este panel lanzará la interfaz principal de Argos.", font=ctk.CTkFont(size=11), text_color="gray").pack(side="bottom", pady=10)
    else:
        ctk.Label(root, text="Argos V2.5.0", font=("Arial", 16, "bold")).pack(pady=(20, 5))
        status_label = ctk.Label(root, text="Iniciando servidor...", fg="orange")
        status_label.pack(pady=5)
        
        open_btn = ctk.Button(root, text="Abrir Interfaz UI", command=open_app_mode, state="disabled")
        open_btn.pack(pady=10)
        
        ctk.Label(root, text="Cierre esta ventana para apagar el sistema completamente.", font=("Arial", 9), fg="gray").pack(side="bottom", pady=10)

    if not hasattr(ctk, 'CTkLabel'):
        # Fallback de Tkinter: iniciar el servidor de red automáticamente en un hilo
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

    root.after(500, check_and_launch)
    root.mainloop()
    
    # On mainloop exit (window closed)
    print("Cerrando Argos...")
    sys.exit(0)

if __name__ == "__main__":
    main()
