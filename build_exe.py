import os
import subprocess
import shutil
import sys

def run_step(step_name, cmd, cwd=None):
    print(f"\n{'='*50}\n--> PASO: {step_name}\n{'='*50}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"ERROR en {step_name}")
        exit(1)

def kill_running_argos():
    print("Cerrando instancias de Argos que puedan estar bloqueando archivos...")
    subprocess.run("taskkill /F /IM Argos.exe /T", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def clean_directory(path, label):
    if os.path.exists(path):
        print(f"Limpiando {label} ({path})...")
        try:
            shutil.rmtree(path)
        except Exception as e:
            print(f"Advertencia: No se pudo eliminar completamente {path}: {e}")

def find_iscc():
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Inno Setup 6\ISCC.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Antigravity IDE\resources\app\node_modules\innosetup\bin\ISCC.exe")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    dist_py_dir = os.path.join(root_dir, "dist")
    build_py_dir = os.path.join(root_dir, "build")
    frontend_dist_dir = os.path.join(frontend_dir, "dist")
    
    # 0. Matar instancias ejecutándose que bloqueen archivos
    kill_running_argos()

    # 1. Limpieza estricta previa de caches y dists desactualizados
    clean_directory(frontend_dist_dir, "dist de Frontend")
    clean_directory(dist_py_dir, "dist de PyInstaller")
    clean_directory(build_py_dir, "cache build de PyInstaller")

    # 2. Frontend Build
    run_step("Construir Frontend (Vite)", "npm run build", cwd=frontend_dir)
    
    if not os.path.exists(frontend_dist_dir):
        print("ERROR: No se generó la carpeta frontend/dist")
        exit(1)
        
    # 3. Instalar y asegurar dependencias de Python
    reqs = ["fastapi", "uvicorn[standard]", "python-multipart", "pydantic", 
            "customtkinter", "pymupdf", "thefuzz", "openpyxl", "python-docx"]
    run_step("Instalar Dependencias de Python", f"{sys.executable} -m pip install {' '.join(reqs)}", cwd=root_dir)

    # 4. PyInstaller Build con flag --clean para evitar bytecodes (.pyc) viejos
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--console",
        "--icon=icon.ico",
        "--name=Argos",
        "--collect-all=fastapi",
        "--collect-all=uvicorn",
        "--collect-all=pydantic",
        "--collect-all=customtkinter",
        "--collect-all=fitz",
        '--add-data="frontend/dist;frontend/dist"',
        '--add-data="modules;modules"',
        '--add-data="assets;assets"',
        '--add-data="ee_families.json;."',
        '--add-data="m3_config.json;."',
        '--add-data="DJ Conformidad Modelo SE LIMPIO.docx;."',
        '--add-data="DJ Conformidad Modelo SE.docx;."',
        '--add-data="DJ Conformidad Modelo EE.docx;."',
        '--add-data="Ficha Tecnica Modelo EE.docx;."',
        'launcher.py'
    ]

    run_step("Empaquetar Backend y Frontend (PyInstaller)", " ".join(pyinstaller_cmd), cwd=root_dir)
    
    print("\n" + "="*50)
    print("¡COMPILACIÓN PYINSTALLER EXITOSA!")
    print("La carpeta ejecutable se encuentra en: dist/Argos")
    
    # 5. Compilar Instalador Inno Setup automáticamente si ISCC está presente
    iscc_path = find_iscc()
    iss_file = os.path.join(root_dir, "argos_installer.iss")
    if iscc_path and os.path.exists(iss_file):
        run_step("Generar Instalador 1-Clic (Inno Setup)", f'"{iscc_path}" "{iss_file}"', cwd=root_dir)
        print("\n" + "="*50)
        print("¡INSTALADOR GENERADO CON ÉXITO!")
        print("Instalador listo: Argos_Setup_v3_2_0.exe")
        print("="*50 + "\n")
    else:
        print("\nSi tenés Inno Setup instalado, podés compilar argos_installer.iss para generar el archivo instalador .exe")
        print("="*50 + "\n")

if __name__ == "__main__":
    main()
