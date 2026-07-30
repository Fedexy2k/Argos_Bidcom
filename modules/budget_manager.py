"""
Módulo de Control de Presupuesto y Registro de Gestiones (Budget Manager) para Argos.
Permite establecer un tope de gasto mensual en USD, registrar consumos de tokens
y bloquear llamadas a la API de IA si se supera el presupuesto.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)

# Precios por 1,000,000 tokens (USD)
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "o3-mini": {"input": 1.10, "output": 4.40},
    "gemini-2.5-flash-lite": {"input": 0.00, "output": 0.00},
    "gemini-2.0-flash": {"input": 0.00, "output": 0.00},
}

class BudgetManager:
    """Administra el tope mensual de gasto y el registro de llamadas a IA."""

    def __init__(self, ledger_path: Optional[str] = None):
        if ledger_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logs_dir = os.path.join(base_dir, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            ledger_path = os.path.join(logs_dir, "usage_ledger.json")

        self.ledger_path = ledger_path
        self._ensure_ledger_exists()

    def _ensure_ledger_exists(self):
        """Crea el archivo usage_ledger.json si no existe."""
        if not os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, 'w', encoding='utf-8') as f:
                    json.dump({"entries": []}, f, indent=2)
            except Exception as e:
                logger.error(f"Error creando usage_ledger.json: {e}")

    def get_monthly_limit_usd(self) -> float:
        """Obtiene el tope mensual configurado en la variable de entorno."""
        env_val = os.getenv("MAX_MONTHLY_AI_BUDGET_USD", "5.00")
        try:
            return float(env_val)
        except ValueError:
            return 5.00

    def calculate_cost_usd(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calcula el costo en USD basado en el modelo y tokens consumidos."""
        rates = MODEL_PRICING.get(model_id, {"input": 0.15, "output": 0.60})
        cost_input = (prompt_tokens / 1_000_000.0) * rates["input"]
        cost_output = (completion_tokens / 1_000_000.0) * rates["output"]
        return round(cost_input + cost_output, 6)

    def get_monthly_spend(self, year_month: Optional[str] = None) -> float:
        """Obtiene el gasto total acumulado en el mes en curso (YYYY-MM)."""
        if year_month is None:
            year_month = datetime.now().strftime("%Y-%m")

        if not os.path.exists(self.ledger_path):
            return 0.0

        try:
            with open(self.ledger_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            entries = data.get("entries", [])
            total = sum(
                entry.get("costo_usd", 0.0)
                for entry in entries
                if entry.get("timestamp", "").startswith(year_month)
            )
            return round(total, 4)
        except Exception as e:
            logger.error(f"Error leyendo usage_ledger.json: {e}")
            return 0.0

    def can_make_request(self) -> Tuple[bool, Optional[str]]:
        """
        Verifica si el presupuesto mensual permite realizar una nueva consulta a la IA.

        Returns:
            (True, None) si se permite la consulta.
            (False, "Mensaje de error/bloqueo") si se superó el tope.
        """
        limit = self.get_monthly_limit_usd()
        current_spend = self.get_monthly_spend()

        if current_spend >= limit:
            msg = (
                f"⚠️ Límite de presupuesto mensual alcanzado (${limit:.2f} USD). "
                f"Gasto acumulado este mes: ${current_spend:.4f} USD. "
                "Consultas de IA pausadas para proteger el presupuesto."
            )
            logger.warning(msg)
            return False, msg

        return True, None

    def record_request(
        self,
        provider: str,
        model_id: str,
        gestion: str,
        documento: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached: bool = False
    ) -> Dict:
        """
        Registra una gestión en el ledger y retorna los datos del consumo.
        """
        if cached:
            costo_usd = 0.0
        else:
            costo_usd = self.calculate_cost_usd(model_id, prompt_tokens, completion_tokens)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "timestamp": now_str,
            "provider": provider,
            "model_id": model_id,
            "gestion": gestion,
            "documento": documento,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "costo_usd": costo_usd,
            "cached": cached
        }

        try:
            data = {"entries": []}
            if os.path.exists(self.ledger_path):
                with open(self.ledger_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            data.setdefault("entries", []).append(entry)

            with open(self.ledger_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(
                f"[Budget] Registro OK | {gestion} | Doc: {documento} | "
                f"Tokens: {prompt_tokens}+{completion_tokens} | Costo: ${costo_usd:.6f} USD"
            )
        except Exception as e:
            logger.error(f"Error escribiendo en usage_ledger.json: {e}")

        return entry

    def get_summary(self) -> Dict:
        """Retorna un resumen del consumo acumulado y el saldo disponible."""
        now_ym = datetime.now().strftime("%Y-%m")
        limit = self.get_monthly_limit_usd()
        spent = self.get_monthly_spend(now_ym)
        remaining = max(0.0, limit - spent)
        pct = (spent / limit * 100.0) if limit > 0 else 0.0

        return {
            "periodo": now_ym,
            "limite_mensual_usd": limit,
            "gasto_acumulado_usd": spent,
            "saldo_disponible_usd": round(remaining, 4),
            "porcentaje_usado": round(pct, 1)
        }
