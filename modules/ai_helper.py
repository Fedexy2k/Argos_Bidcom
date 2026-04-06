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
