# Configuración de API Key de Gemini para Argos

## Pasos para configurar (solo 2 minutos):

### 1. Obtener API Key (GRATIS)
1. Ve a: https://aistudio.google.com/app/apikey
2. Haz clic en "Create API Key"
3. Copia la clave generada

### 2. Configurar en Argos

**Opción A: Archivo .env (Recomendado)**
```bash
# Crear archivo .env desde el template
copy .env.example .env

# Editar .env y reemplazar YOUR_API_KEY_HERE con tu API key real
```

**Opción B: Variable de Entorno del Sistema**
```powershell
# En PowerShell (temporal, solo para esta sesión):
$env:GEMINI_API_KEY="tu-api-key-aqui"

# Para hacerlo permanente:
# Panel de Control > Sistema > Variables de entorno > Nueva
# Nombre: GEMINI_API_KEY
# Valor: tu-api-key-aqui
```

### 3. Verificar que funciona
```bash
python test_ai_helper.py
```

## Qué hace la integración de IA:

### Extracción Inteligente (m1_ingest.py)
- **Cuándo se activa**: Si el parser clásico NO encuentra specs en el datasheet
- **Qué hace**: Lee el texto del Excel y extrae specs técnicas usando comprensión de lenguaje natural
- **Ejemplo**: Encuentra "17,9Vcc; 0,35A; 6,2W; Clase III" aunque esté en columnas raras o formato inusual

### Validación Inteligente (m2_strategies.py)
- **Cuándo se activa**: Si la validación regex/fuzzy FALLA o da WARNING
- **Qué hace**: Compara specs del datasheet con el PDF del certificado de forma semántica
- **Ejemplo**: Entiende que "17,9Vcc" en el datasheet = "17.9 Vcc" en el PDF (tolerancia de formato)

## Costos
**Gemini 2.0 Flash es 100% GRATIS** con límites generosos:
- 15 requests/minuto
- 1M tokens/minuto
- Argos usa ~2-3 requests por auditoría = GRATIS para siempre

## Privacidad
- Los datos del datasheet/PDF se envían a la API de Google
- Google NO usa estos datos para entrenar modelos (según sus términos)
- Si tenés datos sensibles, podés desactivar el AI fallback comentando las líneas respectivas

## Troubleshooting

### Error: "GEMINI_API_KEY no encontrada"
- Asegurate de haber creado el archivo `.env` con tu API key
- O configurar la variable de entorno del sistema

### Error: "API key inválida"
- Verificá que copiaste la key completa (sin espacios extra)
- Creá una nueva API key en https://aistudio.google.com/app/apikey

### La IA no se ejecuta
- Si no hay API key configurada, el sistema simplemente omite la IA y usa solo regex/fuzzy
- Revisá los logs: si dice "API key no configurada", es normal y no crítico
