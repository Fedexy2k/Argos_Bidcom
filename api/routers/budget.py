"""
api/routers/budget.py
=====================
AI Cost governance and usage ledger endpoints.
"""
from __future__ import annotations

import json
import os
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/budget", tags=["Budget & AI Governance"])


@router.get("/summary")
def get_budget_summary():
    """Retorna el resumen de gasto acumulado en el mes, saldo disponible y límite."""
    try:
        from modules.budget_manager import BudgetManager
        mgr = BudgetManager()
        return mgr.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen de presupuesto: {e}")


@router.get("/ledger")
def get_budget_ledger():
    """Retorna las entradas registradas en el ledger de gestiones de IA."""
    try:
        from modules.budget_manager import BudgetManager
        mgr = BudgetManager()
        ledger_file = mgr.ledger_path
        if os.path.exists(ledger_file):
            with open(ledger_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"entries": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener ledger de gestiones: {e}")
