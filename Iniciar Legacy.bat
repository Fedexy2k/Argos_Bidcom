@echo off
echo Iniciando Argos Legacy (Desktop App)
echo Carpeta actual: %cd%

:: Agregar la carpeta raiz al PYTHONPATH para que encuentre 'modules'
set PYTHONPATH=%~dp0

:: Ejecutar el script desde app_legacy
python "%~dp0app_legacy\argos_main.py"

pause
