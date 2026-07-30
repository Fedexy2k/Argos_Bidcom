import { useEffect, useState } from 'react'
import { getBudgetSummary, getBudgetLedger, type BudgetSummary, type BudgetLedgerItem } from '../api/client'

interface BudgetModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function BudgetModal({ isOpen, onClose }: BudgetModalProps) {
  const [summary, setSummary] = useState<BudgetSummary | null>(null)
  const [entries, setEntries] = useState<BudgetLedgerItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [sum, ledg] = await Promise.all([
        getBudgetSummary(),
        getBudgetLedger()
      ])
      setSummary(sum)
      setEntries(ledg.entries || [])
    } catch (e: any) {
      setError(e.message || 'Error cargando presupuesto')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  if (!isOpen) return null

  const cachedCount = entries.filter(e => e.cached).length
  const totalCalls = entries.length

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div
        className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden"
        style={{ background: '#12111c' }}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <span className="material-symbols-outlined text-xl">payments</span>
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">Control de Consumo & Registro de IA (Argos Ledger)</h2>
              <p className="text-xs text-slate-400 font-mono">Monitoreo de gasto en OpenAI gpt-4o-mini & Caché Inteligente</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center transition-all"
          >
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto custom-scrollbar flex-1 flex flex-col gap-6">
          {error && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
              ⚠️ {error}
            </div>
          )}

          {/* Cards de Resumen */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Presupuesto Mensual</span>
              <span className="text-xl font-extrabold text-purple-400 font-mono">
                ${summary ? summary.limite_mensual_usd.toFixed(2) : '5.00'} USD
              </span>
              <span className="text-[10px] text-slate-400">Límite asignado ({summary?.periodo || '2026-07'})</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Gasto Acumulado</span>
              <span className="text-xl font-extrabold text-emerald-400 font-mono">
                ${summary ? summary.gasto_acumulado_usd.toFixed(4) : '0.0000'} USD
              </span>
              <span className="text-[10px] text-emerald-500 font-semibold">
                {summary ? summary.porcentaje_usado.toFixed(2) : '0.00'}% consumido
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Saldo Disponible</span>
              <span className="text-xl font-extrabold text-white font-mono">
                ${summary ? summary.saldo_disponible_usd.toFixed(4) : '5.0000'} USD
              </span>
              <span className="text-[10px] text-slate-400">Restante para peticiones</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Peticiones Caché</span>
              <span className="text-xl font-extrabold text-cyan-400 font-mono">
                {cachedCount} / {totalCalls}
              </span>
              <span className="text-[10px] text-cyan-400 font-semibold">⚡ Re-uso $0.00 (Gratis)</span>
            </div>
          </div>

          {/* Rutas de Archivos Locales */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-purple-500/10 flex flex-col gap-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
              <span className="material-symbols-outlined text-purple-400 text-sm">folder_zip</span>
              <span>Ubicación de Registros Físicos en Disco:</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] font-mono text-purple-300">
              <div className="p-2 rounded bg-slate-900 border border-slate-800/60">
                📁 Historial completo (Ledger): <span className="text-white">logs/usage_ledger.json</span>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800/60">
                📊 Resumen acumulado (Budget): <span className="text-white">logs/budget_summary.json</span>
              </div>
            </div>
          </div>

          {/* Tabla de Historial (Ledger) */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <span className="material-symbols-outlined text-sm text-purple-400">history</span>
                Historial de Solicitudes Registradas ({entries.length})
              </h3>
              <button
                onClick={loadData}
                disabled={loading}
                className="px-3 py-1 rounded-lg border border-slate-800 text-slate-400 hover:text-white text-xs flex items-center gap-1.5 transition-all"
              >
                <span className={`material-symbols-outlined text-xs ${loading ? 'animate-spin' : ''}`}>refresh</span>
                <span>Actualizar</span>
              </button>
            </div>

            <div className="border border-slate-800/80 rounded-xl overflow-hidden bg-slate-950/40">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/80 border-b border-slate-800 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                  <tr>
                    <th className="py-2.5 px-4">Fecha / Hora</th>
                    <th className="py-2.5 px-4">Gestión</th>
                    <th className="py-2.5 px-4">Documento</th>
                    <th className="py-2.5 px-4">Modelo</th>
                    <th className="py-2.5 px-4 text-right">Tokens</th>
                    <th className="py-2.5 px-4 text-right">Costo USD</th>
                    <th className="py-2.5 px-4 text-center">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50 font-mono text-[11px]">
                  {entries.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-6 text-slate-400 font-sans text-xs">
                        No hay consumos registrados aún.
                      </td>
                    </tr>
                  ) : (
                    entries.slice().reverse().map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-4 text-slate-400 whitespace-nowrap">{item.timestamp}</td>
                        <td className="py-2.5 px-4 font-sans font-medium text-white">{item.gestion}</td>
                        <td className="py-2.5 px-4 text-slate-400 max-w-[150px] truncate" title={item.documento}>
                          {item.documento}
                        </td>
                        <td className="py-2.5 px-4 text-purple-300">{item.model_id}</td>
                        <td className="py-2.5 px-4 text-right text-slate-400">
                          {item.total_tokens > 0 ? item.total_tokens.toLocaleString() : '0'}
                        </td>
                        <td className="py-2.5 px-4 text-right font-bold text-emerald-400">
                          ${item.costo_usd.toFixed(6)}
                        </td>
                        <td className="py-2.5 px-4 text-center">
                          {item.cached ? (
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                              ⚡ CACHÉ (FREE)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                              OPENAI API
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/60 flex justify-between items-center text-xs text-slate-400">
          <span>Sistema de Cuotas Argos — OpenAI gpt-4o-mini ($0.15 / 1M input - $0.60 / 1M output)</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium transition-all"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
