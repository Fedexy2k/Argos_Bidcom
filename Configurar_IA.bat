@echo off
chcp 65001 > nul
title Argos - Configuración de Claves de IA
cls
echo ======================================================
echo          ARGOS BIDCOM - CONFIGURACIÓN DE IA
echo ======================================================
echo.
echo Este asistente te permite configurar tus claves de API
echo de forma rápida sin tener que crear o editar archivos a mano.
echo.

python -c "
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

env_file = '.env'
current = {}
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                current[k.strip()] = v.strip()

print('--- Estado Actual ---')
print('OpenAI Key:', '✓ Configurada (' + current['OPENAI_API_KEY'][:7] + '...)' if current.get('OPENAI_API_KEY') else '✗ No configurada')
print('Gemini Key:', '✓ Configurada (' + current['GEMINI_API_KEY'][:7] + '...)' if current.get('GEMINI_API_KEY') else '✗ No configurada')
print('---------------------\n')

op = input('Ingresá tu OpenAI API Key (o Enter para mantener actual): ').strip()
if op:
    current['OPENAI_API_KEY'] = op

gem = input('Ingresá tu Google Gemini API Key (o Enter para mantener actual): ').strip()
if gem:
    current['GEMINI_API_KEY'] = gem

with open(env_file, 'w', encoding='utf-8') as f:
    for k, v in current.items():
        f.write(f'{k}={v}\n')

print('\n✓ Archivo .env guardado exitosamente.')
"

echo.
echo Presioná cualquier tecla para salir...
pause > nul
