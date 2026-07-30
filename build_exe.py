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

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # 1. Frontend Build
    run_step("Construir Frontend (Vite)", "npm run build", cwd=frontend_dir)
    
    # Check if dist exists
    if not os.path.exists(os.path.join(frontend_dir, "dist")):
        print("ERROR: No se generó la carpeta frontend/dist")
        exit(1)
        
    # 2. Instalar y asegurar dependencias
    reqs = ["fastapi", "uvicorn[standard]", "python-multipart", "pydantic", 
            "customtkinter", "pymupdf", "thefuzz", "openpyxl", "python-docx"]
    run_step("Instalar Dependencias de Python", f"{sys.executable} -m pip install {' '.join(reqs)}", cwd=root_dir)
    
    # 3. Limpiar dist viejo de PyInstaller
    dist_py_dir = os.path.join(root_dir, "dist")
    if os.path.exists(dist_py_dir):
        print("\nLimpiando carpeta dist/ de builds anteriores...")
        try:
            shutil.rmtree(dist_py_dir)
        except:
            pass

    # 3. PyInstaller Build
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
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
        'launcher.py'
    ]

    
    run_step("Empaquetar Backend y Frontend (PyInstaller)", " ".join(pyinstaller_cmd), cwd=root_dir)
    
    print("\n" + "="*50)
    print("¡COMPILACIÓN EXITOSA!")
    print("La carpeta ejecutable se encuentra en: dist/Argos")
    print("Siguiente paso: Compilar el instalador con argos_installer.iss")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
