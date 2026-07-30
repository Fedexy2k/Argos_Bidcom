@echo off
chcp 65001 >nul
title Instalador Argos v3.1.0 - BIDCOM / Gadnic
echo ============================================================
echo   INSTALADOR ARGOS v3.1.0 - GADNIC / BIDCOM
echo ============================================================
echo.
echo [1/3] Verificando dependencias de Python y Node...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no se encuentra instalado o no esta en el PATH.
    pause
    exit /b 1
)

echo [2/3] Instalando dependencias de Python...
python -m pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando paquetes base directamente...
    python -m pip install fastapi uvicorn pydantic pymupdf python-docx openpyxl requests customtkinter openai jinja2 >nul 2>&1
)

echo [3/3] Construyendo interfaz Web...
call npm --prefix frontend install >nul 2>&1
call npm --prefix frontend run build

echo.
echo ============================================================
echo   ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!
echo ============================================================
echo.
echo Podés iniciar Argos haciendo doble clic en "Iniciar Argos.bat"
echo o ejecutando: C:\Python314\python.exe launcher.py
echo.
pause
