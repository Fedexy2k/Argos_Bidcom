@echo off
title Argos Frontend
echo Iniciando Argos Frontend...
set PATH=C:\Program Files\nodejs;%PATH%
cd /d "%~dp0frontend"
npm run dev
pause
