"""
Módulo de Inteligencia Artificial para Argos (OpenAI / Multi-proveedor).
Maneja extracción inteligente, revisión semántica, validación de especificaciones técnicas
y automatización de Eficiencia Energética (EE) con control de presupuesto y caché.
"""

import os
import json
import logging
import time
from typing import Dict, Optional, List, Tuple, Any

# Cargar automáticamente variables de entorno desde .env en la raíz del proyecto
_root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_root_env):
    try:
        with open(_root_env, encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ[_k.strip()] = _v.strip()
    except Exception:
        pass

from modules.budget_manager import BudgetManager
from modules.ai_cache import AICacheManager

logger = logging.getLogger(__name__)

# ── Carga de contexto por OEC ─────────────────────────────────────────────────

def load_oec_context(oec_key: str, rules_path: Optional[str] = None) -> str:
    """
    Carga las reglas del OEC desde oec_rules.json y las formatea como bloque
    de texto legible para inyectar al inicio del prompt de la IA.
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
        lines.append("MAPEO DE ETIQUETAS DEL CERT → CAMPO DESTINO:")
        for label, campo in mapeo.items():
            lines.append(f'  - "{label}" → {campo}')

    advertencias = oec_data.get('advertencias', [])
    if advertencias:
        lines.append("ADVERTENCIAS / CASOS ESPECIALES:")
        for adv in advertencias:
            lines.append(f"  ! {adv}")

    lines.append("=== FIN CONTEXTO ===")
    lines.append("")
    return "\n".join(lines)


# ── Motor Central de Ejecución de IA ─────────────────────────────────────────

class AIEngine:
    """Motor unificado que gestiona llamadas a OpenAI/Gemini con presupuesto y caché."""

    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.model_id = os.getenv("OPENAI_MODEL", "gpt-4o-mini") if self.provider == "openai" else "gemini-2.5-flash-lite"
        self.budget_mgr = BudgetManager()
        self.cache_mgr = AICacheManager()

    def generate_json(self, prompt: str, gestion: str = "AI_Task", documento: str = "document.pdf") -> Tuple[Optional[Dict], str]:
        """
        Ejecuta una consulta a la IA esperando una respuesta JSON.
        Verifica caché y presupuesto antes de llamar a la API.

        Returns:
            (dict_resultado, fuente_info) -> ("cache", "openai", "gemini", "blocked_budget", "error")
        """
        # 1. Verificar Caché Local
        cached_result = self.cache_mgr.get(self.model_id, prompt)
        if cached_result is not None:
            self.budget_mgr.record_request(
                provider=self.provider,
                model_id=self.model_id,
                gestion=gestion,
                documento=documento,
                prompt_tokens=0,
                completion_tokens=0,
                cached=True
            )
            return cached_result, "cache"

        # 2. Verificar Presupuesto Mensual
        allowed, block_msg = self.budget_mgr.can_make_request()
        if not allowed:
            logger.warning(f"[AI] Solicitud bloqueada por presupuesto: {block_msg}")
            return None, "blocked_budget"

        # 3. Ejecutar llamada al Proveedor
        if self.provider == "openai" and self.openai_key and self.openai_key != "tu_openai_key_aqui":
            return self._call_openai(prompt, gestion, documento)
        elif self.gemini_key:
            return self._call_gemini(prompt, gestion, documento)
        elif self.openai_key and self.openai_key != "tu_openai_key_aqui":
            return self._call_openai(prompt, gestion, documento)
        else:
            logger.error("[AI] Ninguna API Key válida configurada en .env (OPENAI_API_KEY / GEMINI_API_KEY)")
            return None, "error"

    def _call_openai(self, prompt: str, gestion: str, documento: str) -> Tuple[Optional[Dict], str]:
        """Llamada nativa a OpenAI API con response_format json_object."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_key)

            system_msg = (
                "Sos un auditor experto en certificación de productos eléctricos y documentación aduanera. "
                "Responde SIEMPRE única y exclusivamente con un objeto JSON válido, sin bloques markdown ```json ni texto adicional."
            )

            response = client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            response_text = response.choices[0].message.content.strip()
            result = json.loads(response_text)

            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

            # Guardar en caché y en el ledger
            self.cache_mgr.set(self.model_id, prompt, result)
            self.budget_mgr.record_request(
                provider="openai",
                model_id=self.model_id,
                gestion=gestion,
                documento=documento,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached=False
            )

            return result, "openai"

        except Exception as e:
            logger.error(f"[AI] Error ejecutando OpenAI: {e}")
            # Fallback a Gemini si está disponible
            if self.gemini_key:
                logger.info("[AI] Intentando fallback a Gemini...")
                return self._call_gemini(prompt, gestion, documento)
            return None, "error"

    def _call_gemini(self, prompt: str, gestion: str, documento: str) -> Tuple[Optional[Dict], str]:
        """Llamada a Google GenAI SDK (Gemini)."""
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_key)
            model_id = "gemini-2.5-flash-lite"

            response = client.models.generate_content(
                model=model_id,
                contents=prompt
            )

            response_text = response.text.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            result = json.loads(response_text)

            # Estimado para Gemini
            p_tokens = len(prompt) // 4
            c_tokens = len(response_text) // 4

            self.cache_mgr.set(model_id, prompt, result)
            self.budget_mgr.record_request(
                provider="gemini",
                model_id=model_id,
                gestion=gestion,
                documento=documento,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                cached=False
            )

            return result, "gemini"

        except Exception as e:
            logger.error(f"[AI] Error ejecutando Gemini: {e}")
            return None, "error"


# ── AISpecsHelper (Compatibilidad con módulos M1/M2) ─────────────────────────

class AISpecsHelper:
    """Helper para extracción y validación de specs usando la IA configurada."""

    def __init__(self, api_key: Optional[str] = None, delay_seconds: float = 0.5):
        self.logger = logging.getLogger(__name__)
        self.engine = AIEngine()
        self.delay_seconds = delay_seconds

    def extract_specs_from_text(self, text: str, context: str = "datasheet") -> Optional[Dict]:
        prompt = f'''Sos un experto en análisis de documentación técnica de productos eléctricos.

Analiza el siguiente texto de un {context} y extrae TODAS las especificaciones técnicas eléctricas.

Busca especialmente:
- Voltaje (V, Vcc, Vdc, VAC, VDC)
- Corriente (A, mA, Amp)
- Potencia (W, KW, watts)
- Frecuencia (Hz, KHz)
- Clase de protección (Clase I, Clase II, Clase III, Class I, Class II, Class III)

TEXTO A ANALIZAR:
{text[:6000]}

Responde SOLO con este JSON exacto:
{{
  "voltage": "valor con unidad o null",
  "current": "valor con unidad o null",
  "power": "valor con unidad o null",
  "frequency": "valor con unidad o null",
  "class": "clase de protección o null",
  "full_spec": "especificación completa como aparece o null",
  "raw_specs": ["lista", "de", "todas", "las", "specs", "encontradas"]
}}'''

        result, source = self.engine.generate_json(prompt, gestion="Extracción Specs", documento="datasheet")
        return result

    def validate_specs_in_text(self, pdf_text: str, expected_specs: Dict[str, str], strict: bool = False) -> Dict:
        prompt = f'''Sos un auditor técnico experto. Verifica si un certificado contiene las especificaciones técnicas requeridas.

ESPECIFICACIONES ESPERADAS:
{json.dumps(expected_specs, indent=2, ensure_ascii=False)}

TEXTO DEL CERTIFICADO:
{pdf_text[:7000]}

REGLAS DE VALIDACIÓN:
- Tolerá variaciones mínimas de formato: "17,9Vcc" = "17.9 Vcc" = "17,9 Vcc"
- Los valores numéricos y unidades DEBEN estar presentes
- {"STRICT MODE: Match exacto requerido" if strict else "FLEXIBLE: Tolerá formato pero verificá valores"}

Responde SOLO con este JSON exacto:
{{
  "found": true o false,
  "matches": {{"voltage": true, "current": true, "power": true, "class": true}},
  "missing": ["lista de specs faltantes"],
  "confidence": 0.95,
  "reasoning": "breve explicación de qué encontraste o qué falta"
}}'''

        result, source = self.engine.generate_json(prompt, gestion="Validación Specs", documento="certificado.pdf")
        if result:
            return result
        return {
            'found': False,
            'matches': {},
            'missing': list(expected_specs.keys()),
            'confidence': 0.0,
            'reasoning': 'No se pudo realizar la validación por IA'
        }


# ── Funciones Standalone para el Extractor Dispatcher (M3) ───────────────────

def fill_missing_fields_ai(
    cert_text: str,
    missing_fields: List[str],
    api_key: Optional[str] = None,
    log_fn=None,
    oec_context: str = "",
) -> Dict[str, str]:
    """Completado inteligente de campos vacíos."""
    logger_local = logging.getLogger(__name__)
    def _log(level: str, msg: str):
        if log_fn:
            log_fn(level, msg)
        else:
            getattr(logger_local, level, logger_local.info)(msg)

    engine = AIEngine()

    field_descriptions = {
        "marca": "La marca comercial del producto (ej: GADNIC). NO incluir specs eléctricas aquí.",
        "fabricante": "Nombre de la empresa FABRICANTE en China u origen. NUNCA Lenor, IRAM, Intertek o Qetkra.",
        "direccion": "Dirección física de la FÁBRICA.",
        "modelos": "Todos los números/códigos de modelo completos separados por coma. NUNCA truncar.",
        "specs": "Especificaciones eléctricas (ej: 220V~; 50Hz; 500W; Clase II).",
        "producto_desc": "Descripción del tipo de producto.",
        "fecha_emision": "Fecha de emisión (dd/mm/yyyy).",
    }

    campos_solicitados = "\n".join(f'- "{f}": {field_descriptions.get(f, f)}' for f in missing_fields)
    context_block = f"{oec_context}\n" if oec_context else ""

    prompt = f"""{context_block}Sos un auditor experto en certificación de productos eléctricos.

CAMPOS A EXTRAER:
{campos_solicitados}

TEXTO DEL CERTIFICADO:
{cert_text[:15000]}

REGLAS STRICTAS:
1. FIDELIDAD ABSOLUTA: Extrae ÚNICAMENTE información que esté expresamente en el certificado. NUNCA inventes, adivines ni asumas datos que no figuren explícitamente. Si un dato no figura, asigna "".
2. 'fabricante': Es la fábrica real. NUNCA pongas 'LENOR S.R.L.', 'IRAM', 'Intertek', 'Qetkra' ni códigos de formulario como 'AAB817'.
3. 'marca': Solo el nombre de marca (ej: GADNIC). NUNCA pongas especificaciones eléctricas (voltaje/potencia) dentro del campo marca.
4. 'modelos': Devuelve la LISTA COMPLETA de todos los modelos separados por comas (leé los anexos completos). No recortes la lista.
5. 'specs': Pon únicamente el bloque eléctrico (voltaje, corriente, potencia, frecuencia, clase).


JSON esperado (solo estas claves):
{{
  {', '.join(f'"{f}": "valor"' for f in missing_fields)}
}}"""

    _log("info", f"[AI] Solicitando campos vacíos {missing_fields} a la IA...")
    result, source = engine.generate_json(prompt, gestion="Completar Campos Vacíos", documento="certificado.pdf")

    if result:
        filled = {f: str(result.get(f, '')).strip() for f in missing_fields}
        _log("info", f"[AI] ✓ Campos completados por IA ({source}): {filled}")
        return filled

    return {f: '' for f in missing_fields}


def review_extraction_ai(
    cert_text: str,
    extracted: Dict[str, str],
    api_key: Optional[str] = None,
    log_fn=None,
    locked_fields: Optional[List[str]] = None,
    oec_context: str = "",
) -> Dict[str, str]:
    """Revisión semántica completa de los datos extraídos."""
    logger_local = logging.getLogger(__name__)
    def _log(level: str, msg: str):
        if log_fn:
            log_fn(level, msg)
        else:
            getattr(logger_local, level, logger_local.info)(msg)

    engine = AIEngine()
    campos_actuales = json.dumps(extracted, ensure_ascii=False, indent=2)
    context_block = f"{oec_context}\n" if oec_context else ""

    prompt = f"""{context_block}Sos un auditor experto en revisión de certificados de seguridad eléctrica.
Revisa los datos extraídos por regex y corrige cualquier desalineación o confusión.

DATOS EXTRAÍDOS POR REGEX:
{campos_actuales}

TEXTO DEL CERTIFICADO:
{cert_text[:8000]}

REGLAS CRÍTICAS DE CORRECCIÓN:
1. 'marca': Si el regex guardó especificaciones eléctricas (ej: '220V~; 50Hz; 250W') dentro de 'marca', EXTRAELAS de allí y deja solo el nombre de la marca (ej: 'GADNIC').
2. 'fabricante': El fabricante es la FÁBRICA. Si en 'fabricante' figura 'LENOR S.R.L.', 'IRAM', 'Intertek', 'Qetkra' o un código como 'AAB817', BÚSCALO en el texto y CORRÍGELO por el nombre real de la empresa fabricante.
3. 'modelos': Si ves que la palabra de la marca (ej: 'GADNIC') o sufijos están pegados a cada modelo (ej: 'BAR01 GADNIC'), limpia la lista para que queden solo los códigos o separados por comas. Asegúrate de incluir TODOS los modelos del anexo.
4. 'specs': Si las specs estaban vacías o cruzadas, colócalas correctamente en 'specs'.
5. NUNCA borres un valor válido si no tienes una corrección mejor.

JSON esperado (mismas claves exactas):
{{
  "cert_number": "valor",
  "normas": "valor",
  "marca": "valor",
  "fabricante": "valor",
  "direccion": "valor",
  "modelos": "valor",
  "specs": "valor",
  "producto_desc": "valor",
  "fecha_emision": "valor"
}}"""

    _log("info", "[AI] Iniciando revisión semántica inteligente (OpenAI/AI Engine)...")
    reviewed, source = engine.generate_json(prompt, gestion="Revisión Semántica", documento="certificado.pdf")

    if not reviewed:
        return extracted

    result = dict(extracted)
    changes = []
    locked = locked_fields or []

    for field, new_val in reviewed.items():
        if field not in result or field in locked:
            continue
        old_val = str(result.get(field, '')).strip()
        new_val = str(new_val).strip()

        if new_val and new_val != old_val:
            if not old_val:
                result[field] = new_val
                changes.append(f"{field}: [vacío] → '{new_val[:40]}'")
            elif new_val != old_val:
                result[field] = new_val
                changes.append(f"{field}: '{old_val[:25]}' → '{new_val[:25]}'")

    if changes:
        _log("info", f"[AI] Revisor ({source}) → cambios aplicados: {' | '.join(changes)}")
    else:
        _log("info", f"[AI] Revisor ({source}) → datos validados sin desalineaciones.")

    return result


# ── Extracción Especializada para DJC Eficiencia Energética (EE) ──────────────

def extract_ee_specs_ai(
    report_text: str,
    ee_families_config: List[Dict],
    log_fn=None
) -> Optional[Dict[str, Any]]:
    """
    Analiza un Informe de Ensayo o Certificado de Eficiencia Energética (EE)
    y extrae automáticamente la familia correspondiente, métricas, datos de laboratorio y specs base.
    """
    engine = AIEngine()

    # Filtrar bloques de texto relevantes si el informe es muy extenso
    lines_relevant = []
    for line in report_text.split('\n'):
        l_low = line.lower()
        if any(k in l_low for k in ['test report', 'prprüfbericht', 'client:', 'applicant', 'identification', 'model', 'modelo', 'brand', 'marca', 'iram', 'resolution', '438/2024', 'energy efficiency', 'clase', 'class', 'consumption', 'consumo', 'volume', 'volumen', 'eei', 'noise', 'ruido', 'capacity', 'capacidad', 'place settings', 'cubiertos', 'standby', 'off-mode', 'appendix', 'issue date', 'date:', 'voltage', 'frequency', 'power', 'potencia', 'tüv', 'iram', 'service-gc@tuv.com', 'web:', 'duration', 'duración', 'programme', 'minutes', 'min', 'watt', 'rated', 'input', '1900', '1760', '2100']):
            lines_relevant.append(line)

    text_to_analyze = "\n".join(lines_relevant) if len(lines_relevant) > 20 else report_text
    if len(text_to_analyze) > 15000:
        text_to_analyze = text_to_analyze[:15000]

    familias_summary = []
    for fam in ee_families_config:
        fields_str = ", ".join(f"{f['key']} ({f['label']})" for f in fam.get("fields", []))
        familias_summary.append(f"- ID: '{fam['id']}' | Nombre: '{fam['label']}' | Campos: {fields_str}")

    prompt = f"""Sos un experto técnico en certificación de Eficiencia Energética (SENCE / IRAM / Res. 438/2024).
Analiza el siguiente Informe de Ensayo o Certificado de Eficiencia Energética y extrae los datos requeridos.

CATÁLOGO DE FAMILIAS DE EFICIENCIA ENERGÉTICA PERMITIDAS:
{chr(10).join(familias_summary)}

TEXTO DEL INFORME DE ENSAYO / CERTIFICADO EE:
{text_to_analyze}

INSTRUCCIONES DE EXTRACCIÓN COMPLETA:
1. Identifica a qué 'family_id' pertenece el producto.
2. Extrae la 'clase_ee' (Clase de Eficiencia Energética). IMPORTANTE: La escala fue RE-ESCALADA bajo la Res. 438/2024, por lo que arranca strictly en 'A' y va hasta la 'G' (NO existen las clases A+++, A++, A+).
3. Extrae la marca comercial ('marca'), ej: 'GADNIC'. Si no figura explícita o figura N/A, infiérelas del cliente/marca si aplica o asigna null.
4. Extrae el modelo o lista de modelos comerciales ('modelos'), ej: 'GADW14' o 'CS-100L-M, CS-100L-G'.
5. Extrae la descripción técnica corta del producto ('producto_desc'), ej: 'Lavavajillas de 14 cubiertos' o 'Heladera con congelador'.
6. Extrae los datos del informe y laboratorio:
   - 'cert_number': Número de Informe de Ensayo (ej: 'CN26L8YX 001' o 'AR EE CN26ADZ3 001').
   - 'oec_nombre': Nombre del Laboratorio (ej: 'TÜV Rheinland (Guangdong) Ltd.').
   - 'oec_contacto': Correo o web de contacto (ej: 'service-gc@tuv.com' o 'www.tuv.com').
   - 'fecha_emision': Fecha de emisión en formato DD/MM/YYYY.
7. Extrae las especificaciones eléctricas base del producto ('base_specs'):
   - 'tension': Tensión nominal en V~ (ej: '220 V~' o '220-240 V~').
   - 'frecuencia': Frecuencia nominal en Hz (ej: '50 Hz').
   - 'potencia': Potencia nominal en W (ej: '1900 W' o '1760-2100 W'). Busca la potencia de consumo/rated power. Si es lavavajillas y no la halla explícita, asigna '1760-2100 W'.
   - 'clase': Clase eléctrica (SIEMPRE asigna 'Clase I' para electrodomésticos salvo que explicite Clase II).
   - 'ip': Grado IP de protección si figura (ej: 'IPX1' o null si no especifica).

8. Extrae todas las métricas de la familia ('ee_fields'):
   - 'iee': Índice de Eficiencia Energética (EEI), ej: 47.5 o 41.8.
   - Para Lavavajillas: 'capacidad' (cubiertos), 'consumo_anual' (kWh/año), 'consumo_ciclo' (kWh/ciclo), 'consumo_espera' (W), 'agua_ciclo' (L/ciclo), 'agua_anual' (L/año), 'clase_secado', 'duracion_ciclo' (min, ej: 220), 'duracion_sin_apagar' (min, ej: 5), 'ruido' (dB(A)).
   - Para Refrigeradores: 'categoria', 'consumo_anual', 'vol_frescos', 'vol_congelados', 'ruido', 'estrellas', 'clase_climatica'.

JSON ESPERADO ESTRICTO:
{{
  "family_id": "lavavajillas",
  "clase_ee": "A",
  "marca": "GADNIC",
  "modelos": "GADW14",
  "producto_desc": "Lavavajillas de 14 cubiertos",
  "cert_number": "CN26L8YX 001",
  "oec_nombre": "TÜV Rheinland",
  "oec_contacto": "service-gc@tuv.com",
  "fecha_emision": "02/04/2026",
  "base_specs": {{
    "tension": "220-240 V~",
    "frecuencia": "50 Hz",
    "potencia": "1900 W",
    "clase": "Clase I",
    "ip": null
  }},
  "ee_fields": {{
    "iee": 47.5,
    "capacidad": 14,
    "consumo_anual": 227.48,
    "consumo_ciclo": 0.835,
    "consumo_espera": 0.45,
    "agua_ciclo": 9.6,
    "agua_anual": 2688,
    "clase_secado": "A",
    "duracion_ciclo": 220,
    "duracion_sin_apagar": "5 min",
    "ruido": 48
  }}
}}"""


    result, source = engine.generate_json(prompt, gestion="Extracción DJC EE", documento="informe_ee.pdf")
    return result
