"""
Módulo de Caché de Respuestas para la IA de Argos.
Almacena resultados de consultas previa en un archivo local .cache/ai_responses.json
para evitar repetir llamadas a la API sobre el mismo documento/prompt.
"""
import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AICacheManager:
    """Administra la caché local de consultas a la IA."""

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(base_dir, ".cache")

        os.makedirs(cache_dir, exist_ok=True)
        self.cache_file = os.path.join(cache_dir, "ai_responses.json")
        self._ensure_cache_exists()

    def _ensure_cache_exists(self):
        """Crea el archivo de caché si no existe."""
        if not os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, indent=2)
            except Exception as e:
                logger.error(f"Error creando ai_responses.json: {e}")

    def _hash_prompt(self, model_id: str, prompt: str) -> str:
        """Genera un hash MD5 único basado en el modelo y el contenido del prompt."""
        key = f"{model_id}::{prompt.strip()}"
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    def get(self, model_id: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Recupera el resultado en caché si existe.

        Returns:
            Dict con la respuesta guardada o None.
        """
        if not os.path.exists(self.cache_file):
            return None

        key = self._hash_prompt(model_id, prompt)
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            cached_item = cache_data.get(key)
            if cached_item:
                logger.info(f"[Cache] HIT para hash {key[:8]}")
                return cached_item.get("response")
        except Exception as e:
            logger.error(f"Error leyendo caché AI: {e}")

        return None

    def set(self, model_id: str, prompt: str, response: Dict[str, Any]):
        """Guarda un resultado en la caché local."""
        key = self._hash_prompt(model_id, prompt)
        try:
            cache_data = {}
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

            cache_data[key] = {
                "model_id": model_id,
                "response": response
            }

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"[Cache] SET guardado para hash {key[:8]}")
        except Exception as e:
            logger.error(f"Error guardando en caché AI: {e}")
