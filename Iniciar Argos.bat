@echo off
chcp 65001 >nul
title Argos v3.2.0 - Sistema de Certificaciones BIDCOM / Gadnic
echo ============================================================
echo   INICIANDO ARGOS v3.2.0 - GADNIC / BIDCOM
echo ============================================================
echo.
echo Iniciando servidor backend y cargando interfaz grafica...
start "" python launcher.py
