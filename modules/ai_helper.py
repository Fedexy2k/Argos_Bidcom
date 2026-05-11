"""
Módulo de ayuda con IA (Gemini) para Argos
Maneja extracción y validación inteligente de especificaciones técnicas
"""
from google import genai
from google.genai import types
import os
import json
import logging
import time
from typing import Dict, Optional, List


# ── Carga de contexto por OEC ─────────────────────────────────────────────────

def load_oec_context(oec_key: str, rules_path: Optional[str] = None) -> str:
    """
    Carga las reglas del OEC desde oec_rules.json y las formatea como bloque
    de texto legible para inyectar al inicio del prompt de Gemini.

    Args:
        oec_key:    Clave del OEC (ej: 'Intertek', 'Quektra', 'Lenor').
        rules_path: Ruta al archivo JSON (por defecto: oec_rules.json en raíz del proyecto).

    Returns:
        String con el contexto formateado, o cadena vacía si no hay reglas para ese OEC.
    """
    if not oec_key:
        return ""

    if rules_path is None:
        rules_path = os.path.join(
            os.path.dirname(__file__), '..', 'oec_rules.json'
        )

    try:
        with open(rules_path, encoding='utf-8') as f:
            rules = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return ""

    oec_data = rules.get(oec_key)
    if not oec_data or oec_data.get('_meta'):
        return ""

    lines: list[str] = [f"=== CONTEXTO DEL CERTIFICADO: {oec_key} ==="]

    actores = oec_data.get('actores', [])
    if actores:
        lines.append("ACTORES Y ROL EN ESTE TIPO DE CERTIFICADO:")
        for a in actores:
            lines.append(f"  - {a}")

    mapeo = oec_data.get('mapeo', {})
    if mapeo:
        lines.append("MAPEO DE ETIQUETAS DEL CERT \u2192 CAMPO DESTINO:")
        for label, campo in mapeo.items():
            lines.append(f'  - "{label}" \u2192 {campo}')

    advertencias = oec_data.get('advertencias', [])
    if advertencias:
        lines.append("ADVERTENCIAS / CASOS ESPECIALES:")
        for adv in advertencias:
            lines.append(f"  ! {adv}")

    lines.append("=== FIN CONTEXTO ===")
    lines.append("")  # línea en blanco de separación
    return "\n".join(lines)

class AISpecsHelper:
    """Helper para extracción y validación de specs usando Gemini 2.0 Flash (gratis)."""
    
    def __init__(self, api_key: Optional[str] = None, delay_seconds: float = 2.0):
        """
        Inicializa el helper de IA.
        
        Args:
            api_key: API key de Gemini. Si no se provee, busca en variable de entorno.
            delay_seconds: Segundos de espera entre requests para evitar rate limits (default: 2.0)
        """
        self.logger = logging.getLogger(__name__)
        
        # Configurar API key
        key = api_key or os.getenv('GEMINI_API_KEY')
        if not key:
            raise ValueError(
                "GEMINI_API_KEY no encontrada. "
                "Configurala en variable de entorno o pásala al constructor."
            )
        
        # Crear cliente con la nueva API
        self.client = genai.Client(api_key=key)
        
        # Usar Gemini 2.5 Flash Lite (límites más altos que 2.0)
        self.model_id = "gemini-2.5-flash-lite"
        
        # Delay entre requests para evitar saturar API (como en INAL Suite)
        self.delay_seconds = delay_seconds
        
        self.logger.info(f"AISpecsHelper inicializado con {self.model_id} (delay: {delay_seconds}s)")
    
    def extract_specs_from_text(self, text: str, context: str = "datasheet") -> Optional[Dict]:
        """
        Extrae especificaciones técnicas de texto usando IA.
        
        Args:
            text: Texto del cual extraer specs (puede ser Excel crudo, fragmentos, etc.)
            context: Contexto del texto ("datasheet", "certificado", etc.)
        
        Returns:
            Dict con specs extraídas o None si falla
            {
                'voltage': '17,9Vcc',
                'current': '0,35A', 
                'power': '6,2W',
                'class': 'Clase III',
                'full_spec': '17,9Vcc; 0,35A; 6,2W; Clase III',
                'raw_specs': ['spec1', 'spec2', ...]
            }
        """
        prompt = f'''Sos un experto en análisis de documentación técnica de productos eléctricos.

Analiza el siguiente texto de un {context} y extrae TODAS las especificaciones técnicas eléctricas.

Busca especialmente:
- Voltaje (V, Vcc, Vdc, VAC, VDC)
- Corriente (A, mA, Amp)
- Potencia (W, KW, watts)
- Frecuencia (Hz, KHz)
- Clase de protección (Clase I, Clase II, Clase III, Class I, Class II, Class III)

TEXTO A ANALIZAR:
{text}

IMPORTANTE:
- Si ves una línea tipo "ESPECIFICACIONES: 17,9Vcc; 0,35A; 6,2W; Clase III", tómala completa.
- Respeta el formato original (comas, puntos, espacios).
- Si no hay specs eléctricas claras, retorna null en los campos.

Responde SOLO con este JSON exacto (sin markdown, sin explicaciones):
{{
  "voltage": "valor con unidad o null",
  "current": "valor con unidad o null",
  "power": "valor con unidad o null",
  "frequency": "valor con unidad o null",
  "class": "clase de protección o null",
  "full_spec": "especificación completa como aparece o null",
  "raw_specs": ["lista", "de", "todas", "las", "specs", "encontradas"]
}}'''


        try:
            self.logger.debug(f"Solicitando extracción de specs a Gemini...")
            
            # Usar nueva API con el cliente
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            # Delay para evitar saturar API (como en INAL Suite)
            time.sleep(self.delay_seconds)
            
            # Limpiar respuesta (por si tiene markdown)
            response_text = response.text.strip()
            if response_text.startswith('```'):
                # Remover bloques de código markdown
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            
            result = json.loads(response_text)
            self.logger.info(f"✓ Specs extraídas por IA: {result.get('full_spec', 'N/A')}")
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parseando respuesta JSON de IA: {e}")
            self.logger.error(f"Respuesta recibida: {response.text[:200]}")
            return None
        except Exception as e:
            # Si es error de rate limit, loguear específicamente
            error_msg = str(e)
            if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
                self.logger.warning(f"Rate limit alcanzado. Esperando {self.delay_seconds * 2}s...")
                time.sleep(self.delay_seconds * 2)  # Esperar el doble en caso de rate limit
            
            self.logger.error(f"Error en extracción con IA: {e}")
            return None
    
    def validate_specs_in_text(
        self, 
        pdf_text: str, 
        expected_specs: Dict[str, str],
        strict: bool = False
    ) -> Dict:
        """
        Valida si las specs esperadas están presentes en el texto del certificado.
        
        Args:
            pdf_text: Texto extraído del PDF del certificado
            expected_specs: Dict con specs que se esperan encontrar
            strict: Si True, requiere match exacto. Si False, permite variaciones.
        
        Returns:
            {
                'found': True/False,
                'matches': {'voltage': True, 'current': False, ...},
                'missing': ['current', ...],
                'confidence': 0.0-1.0,
                'reasoning': 'explicación breve'
            }
        """
        prompt = f'''Sos un auditor técnico experto. Debes verificar si un certificado contiene las especificaciones técnicas requeridas.

ESPECIFICACIONES ESPERADAS:
{json.dumps(expected_specs, indent=2, ensure_ascii=False)}

TEXTO DEL CERTIFICADO:
{pdf_text}

REGLAS DE VALIDACIÓN:
- Tolerá variaciones mínimas de formato: "17,9Vcc" = "17.9 Vcc" = "17,9 Vcc"
- Los valores numéricos y unidades DEBEN estar presentes
- {"STRICT MODE: Match exacto requerido" if strict else "FLEXIBLE: Tolerá formato pero verificá valores"}

Analiza si TODAS las especificaciones esperadas están presentes en el certificado.

Responde SOLO con este JSON exacto:
{{
  "found": true o false,
  "matches": {{"voltage": true/false, "current": true/false, "power": true/false, "class": true/false}},
  "missing": ["lista de specs faltantes"],
  "confidence": 0.95,
  "reasoning": "breve explicación de qué encontraste o qué falta"
}}'''


        try:
            self.logger.debug("Solicitando validación de specs a Gemini...")
            
            # Usar nueva API
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            # Delay para evitar saturar API
            time.sleep(self.delay_seconds)
            
            # Limpiar respuesta
            response_text = response.text.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            
            result = json.loads(response_text)
            
            self.logger.info(
                f"✓ Validación IA: {'ENCONTRADO' if result['found'] else 'FALTA'} "
                f"(confianza: {result.get('confidence', 0):.0%})"
            )
            self.logger.debug(f"  Razón: {result.get('reasoning', 'N/A')}")
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parseando respuesta JSON de IA: {e}")
            self.logger.error(f"Respuesta recibida: {response.text[:200]}")
            return {
                'found': False,
                'matches': {},
                'missing': list(expected_specs.keys()),
                'confidence': 0.0,
                'reasoning': f'Error parseando respuesta IA: {e}'
            }
        except Exception as e:
            # Manejo específico de rate limit
            error_msg = str(e)
            if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
                self.logger.warning(f"Rate limit alcanzado. Esperando {self.delay_seconds * 2}s...")
                time.sleep(self.delay_seconds * 2)
            
            self.logger.error(f"Error en validación con IA: {e}")
            return {
                'found': False,
                'matches': {},
                'missing': list(expected_specs.keys()),
                'confidence': 0.0,
                'reasoning': f'Error ejecutando IA: {e}'
            }


# Función auxiliar para uso rápido
def extract_specs_ai(text: str, api_key: Optional[str] = None) -> Optional[Dict]:
    """
    Función helper rápida para extraer specs con IA.
    
    Args:
        text: Texto del cual extraer especificaciones
        api_key: API key de Gemini (opcional)
    
    Returns:
        Dict con specs extraídas o None
    """
    helper = AISpecsHelper(api_key=api_key)
    return helper.extract_specs_from_text(text)


def validate_specs_ai(
    pdf_text: str, 
    expected_specs: Dict[str, str],
    api_key: Optional[str] = None
) -> Dict:
    """
    Función helper rápida para validar specs con IA.
    
    Args:
        pdf_text: Texto del PDF del certificado
        expected_specs: Specs que se esperan encontrar
        api_key: API key de Gemini (opcional)
    
    Returns:
        Dict con resultado de validación
    """
    helper = AISpecsHelper(api_key=api_key)
    return helper.validate_specs_in_text(pdf_text, expected_specs)


def fill_missing_fields_ai(
    cert_text: str,
    missing_fields: list[str],
    api_key: Optional[str] = None,
    log_fn=None,
    oec_context: str = "",
) -> Dict[str, str]:
    """
    Función helper rápida para completar campos faltantes de un certificado usando IA.

    Args:
        cert_text: Texto completo extraído del certificado PDF.
        missing_fields: Lista de campos vacíos a completar (ej: ['fabricante', 'marca']).
        api_key: API key de Gemini (opcional, busca en env GEMINI_API_KEY).
        log_fn: Función de log (level, msg) opcional.

    Returns:
        Dict con los campos completados. Los que no se pudieron extraer quedan como ''.
    """
    logger_local = logging.getLogger(__name__)
    def _log(level: str, msg: str):
        if log_fn:
            log_fn(level, msg)
        else:
            getattr(logger_local, level, logger_local.info)(msg)

    key = api_key or os.getenv('GEMINI_API_KEY')
    if not key:
        _log("warning", "[AI] GEMINI_API_KEY no configurada — saltando fallback de IA")
        return {f: '' for f in missing_fields}

    try:
        client = genai.Client(api_key=key)
        model_id = "gemini-2.5-flash-lite"

        # Mapeo de campos a descripciones en lenguaje natural para el prompt
        field_descriptions = {
            "marca":         "La marca comercial del producto (ej: GADNIC, Samsung, Lenovo)",
            "fabricante":    "Nombre de la empresa fabricante (ej: Shenzhen XYZ Electronics Co., Ltd.)",
            "direccion":     "Dirección física del fabricante (calle, ciudad, país)",
            "modelos":       "Los números o nombres de modelo del producto (pueden ser varios, separados por coma)",
            "specs":         "Especificaciones técnicas eléctricas (voltaje, corriente, potencia, frecuencia, clase)",
            "producto_desc": "Descripción general del tipo de producto (ej: Fuente de alimentación, Luminaria LED)",
            "fecha_emision": "Fecha en que fue emitido el certificado (formato dd/mm/yyyy)",
            "fecha_vencimiento": "Fecha de vencimiento o próxima vigilancia del certificado (formato dd/mm/yyyy)",
        }

        campos_solicitados = "\n".join(
            f'- "{f}": {field_descriptions.get(f, f)}'
            for f in missing_fields
        )

        context_block = f"{oec_context}\n" if oec_context else ""
        prompt = f"""{context_block}Sos un experto en análisis de certificados de seguridad eléctrica de productos.

Tu tarea es extraer campos específicos de un certificado. SOLO respondé con un JSON válido.

CAMPOS QUE NECESITO EXTRAER:
{campos_solicitados}

TEXTO DEL CERTIFICADO:
{cert_text[:6000]}

REGLAS:
- Si un campo no está claramente en el texto, retorná "" (string vacío).
- No inventes datos. Solo extraé lo que definitivamente está en el texto.
- Para 'modelos': si hay múltiples, unilos con ', ' (coma espacio).
- Para 'specs': incluí todo el bloque de specs eléctricas en una sola línea.
- Para fechas: formato dd/mm/yyyy.
- Si el CONTEXTO DEL CERTIFICADO fue provisto arriba, usalo para identificar los labels correctos.
- Respondé SOLO con el JSON, sin markdown, sin explicaciones.

JSON esperado (solo las claves pedidas):
{{{{
  {', '.join(f'"{f}": "valor o vacío"' for f in missing_fields)}
}}}}"""

        context_block = f"{oec_context}\n" if oec_context else ""

        _log("info", f"[AI] Fallback Gemini para campos vacios: {missing_fields}")


        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )

        response_text = response.text.strip()
        # Limpiar markdown si viene en bloque de código
        if response_text.startswith('```'):
            lines_r = response_text.split('\n')
            response_text = '\n'.join(lines_r[1:-1])

        result = json.loads(response_text)

        # Solo devolver los campos pedidos, nunca extras
        filled = {f: str(result.get(f, '')) for f in missing_fields}
        filled_info = ', '.join(f"{k}='{v[:30]}'".rstrip("'") + "'" for k, v in filled.items() if v)
        _log("info", f"[AI] ✓ Campos completados por Gemini: {filled_info or '(ninguno)'}")
        return filled

    except json.JSONDecodeError as e:
        _log("warning", f"[AI] Error parseando JSON de Gemini: {e}")
        return {f: '' for f in missing_fields}
    except Exception as e:
        _log("warning", f"[AI] Error en fallback de IA: {e}")
        return {f: '' for f in missing_fields}


def review_extraction_ai(
    cert_text: str,
    extracted: Dict[str, str],
    api_key: Optional[str] = None,
    log_fn=None,
    locked_fields: Optional[List[str]] = None,
    oec_context: str = "",
) -> Dict[str, str]:
    """
    Revisión semántica completa de todos los campos extraídos por el regex.

    Gemini recibe los valores actuales + el texto del cert y verifica:
    - Si cada campo es correcto para lo que debería ser
    - Si hay valores mal asignados (dirección en fabricante, modelo en specs, etc.)
    - Si hay campos con valores incompletos o truncados
    - Completa los que están vacíos si los encuentra en el texto

    Nunca sobreescribe con cadena vacía: solo mejora, nunca empeora.

    Args:
        cert_text: Texto completo del certificado.
        extracted:  Dict con los valores actuales de todos los campos.
        api_key:    API key de Gemini (opcional).
        log_fn:     Función de log (level, msg).

    Returns:
        Dict con los campos corregidos/completados. Mismas claves que extracted.
    """
    logger_local = logging.getLogger(__name__)
    def _log(level: str, msg: str):
        if log_fn:
            log_fn(level, msg)
        else:
            getattr(logger_local, level, logger_local.info)(msg)

    key = api_key or os.getenv('GEMINI_API_KEY')
    if not key:
        _log("debug", "[AI] GEMINI_API_KEY no configurada — saltando revisión")
        return extracted

    try:
        client = genai.Client(api_key=key)
        model_id = "gemini-2.5-flash-lite"

        campos_actuales = json.dumps(extracted, ensure_ascii=False, indent=2)

        context_block = f"{oec_context}\n" if oec_context else ""
        prompt = f"""{context_block}Sos un experto en análisis de certificados de seguridad eléctrica (IRAM, IEC, CB Scheme).
Tu tarea es REVISAR y CORREGIR los datos extraídos de un certificado por un sistema de regex.

DATOS ACTUALES EXTRAÍDOS (pueden tener errores o estar incompletos):
{campos_actuales}

TEXTO COMPLETO DEL CERTIFICADO:
{cert_text[:7000]}

DEFINICIÓN DE CADA CAMPO (qué debe contener):
- cert_number: Código oficial del certificado (ej: LCSH-2466, Q-AR-05917-T-0, TCSE-IACSA-0146/324.1). Solo el código, sin texto extra ni sufijos de formulario.
- normas: Normas técnicas aplicadas (ej: IEC 60335-1:2020, IRAM 2084). Lista completa separada por comas.
- marca: Nombre comercial del producto/marca registrada (ej: GADNIC, Samsung). Solo la marca.
- fabricante: Nombre de la empresa FABRICANTE del producto. NO es el laboratorio de ensayo, NO es el organismo certificador, NO es el importador.
- direccion: Dirección física de la FÁBRICA. NO es la dirección del laboratorio ni del importador.
- modelos: Números o referencias de modelo (ej: MOD-123, GAD-456). Solo códigos de modelo.
- specs: Especificaciones eléctricas (voltaje, corriente, potencia, frecuencia, clase). Todo en una línea.
- producto_desc: Tipo genérico del producto (ej: Fuente de alimentación, Luminaria LED, Calefactor).
- fecha_emision: Fecha de emisión del certificado en formato dd/mm/yyyy.

INSTRUCCIONES:
1. Para cada campo, decidí si el valor actual es CORRECTO, necesita CORRECCIÓN o está VACÍO.
2. Si el valor es correcto: retornalo igual.
3. Si el valor es incorrecto (ej: dirección del laboratorio en 'fabricante'): corregilo con el dato real del fabricante.
4. Si está vacío pero lo encontrás en el texto: completálo.
5. Si no podés determinarlo con certeza: dejálo como está.
6. NUNCA retornes cadena vacía si el campo ya tenía un valor — solo mejorá.
7. ATENCIÓN: El campo 'fabricante' debe ser la empresa que FABRICA el producto, no el laboratorio que lo ensayó ni el organismo que certifica. Si ves "LENOR S.R.L.", "IRAM", "Intertek", etc. como posible fabricante, verificá que efectivamente figure como fabricante en el certificado, no como laboratorio o certificadora.

IMPORTANTE: Respondé SOLO con el JSON con exactamente las mismas claves, sin markdown, sin explicaciones.

JSON esperado:
{{
  "cert_number": "valor corregido o igual",
  "normas": "valor corregido o igual",
  "marca": "valor corregido o igual",
  "fabricante": "valor corregido o igual",
  "direccion": "valor corregido o igual",
  "modelos": "valor corregido o igual",
  "specs": "valor corregido o igual",
  "producto_desc": "valor corregido o igual",
  "fecha_emision": "valor corregido o igual"
}}"""

        context_block = f"{oec_context}\n" if oec_context else ""
        _log("info", "[AI] Revisión semántica completa iniciada (Gemini reviewer)")

        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )

        response_text = response.text.strip()
        if response_text.startswith('```'):
            lines_r = response_text.split('\n')
            response_text = '\n'.join(lines_r[1:-1])

        reviewed = json.loads(response_text)

        # Aplicar correcciones: solo mejorar, nunca vaciar
        result = dict(extracted)
        changes = []
        locked = locked_fields or []
        for field, new_val in reviewed.items():
            if field not in result or field in locked:
                continue
            old_val = result.get(field, '')
            new_val = str(new_val).strip()
            if new_val and new_val != old_val:
                if not old_val:
                    result[field] = new_val
                    changes.append(f"{field}: [vacío]→'{new_val[:40]}'")
                elif new_val != old_val:
                    result[field] = new_val
                    changes.append(f"{field}: '{old_val[:25]}'→'{new_val[:25]}'")

        if changes:
            _log("info", f"[AI] Revisor → cambios: {' | '.join(changes)}")
        else:
            _log("info", "[AI] Revisor → todos los campos validados sin cambios")

        return result

    except json.JSONDecodeError as e:
        _log("warning", f"[AI] Error parseando revisión de Gemini: {e}")
        return extracted
    except Exception as e:
        _log("warning", f"[AI] Error en revisión semántica: {e}")
        return extracted
