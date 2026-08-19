import { useState } from 'react'
import { saveAIKeys, type AIHealthResult } from '../api/client'

interface Props {
  isOpen: boolean
  onClose: () => void
  aiHealth: AIHealthResult | null
  onUpdate: (health: AIHealthResult) => void
}

export function AIConfigModal({ isOpen, onClose, aiHealth, onUpdate }: Props) {
  const [openaiKey, setOpenaiKey] = useState('')
  const [geminiKey, setGeminiKey] = useState('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)

  if (!isOpen) return null

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMsg(null)
    try {
      const payload: { openai_api_key?: string; gemini_api_key?: string } = {}
      if (openaiKey.trim()) payload.openai_api_key = openaiKey.trim()
      if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim()

      if (Object.keys(payload).length === 0) {
        setMsg({ type: 'err', text: 'Ingresá al menos una clave de API para guardar.' })
        setSaving(false)
        return
      }

      const res = await saveAIKeys(payload)
      onUpdate(res)
      setMsg({ type: 'ok', text: '✓ Claves guardadas y activadas correctamente en .env' })
      setOpenaiKey('')
      setGeminiKey('')
      setTimeout(() => {
        onClose()
      }, 1200)
    } catch (err: unknown) {
      setMsg({ type: 'err', text: err instanceof Error ? err.message : 'Error al guardar claves' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0,0,0,0.75)',
        backdropFilter: 'blur(6px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 520,
          background: '#16152a',
          border: '1px solid rgba(139,92,246,0.25)',
          borderRadius: 16,
          boxShadow: '0 20px 50px rgba(0,0,0,0.8), 0 0 30px rgba(139,92,246,0.15)',
          padding: 28,
          position: 'relative',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span className="material-symbols-outlined" style={{ color: '#fff', fontSize: 22 }}>
                smart_toy
              </span>
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#f1eeff' }}>Configurar Inteligencia Artificial</h3>
              <p style={{ margin: 0, fontSize: 12, color: '#94a3b8' }}>Ingresá tus claves de API para habilitar la extracción y auditoría</p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              fontSize: 20,
              padding: 4,
            }}
          >
            ✕
          </button>
        </div>

        {/* Estado actual */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '12px 16px',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: 10,
            border: '1px solid rgba(255,255,255,0.06)',
            marginBottom: 20,
          }}
        >
          <span style={{ fontSize: 12, fontWeight: 600, color: '#cbd5e1' }}>Estado actual:</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: 6,
                background: aiHealth?.openai_configured ? 'rgba(74,222,128,0.15)' : 'rgba(239,68,68,0.15)',
                color: aiHealth?.openai_configured ? '#4ade80' : '#f87171',
                border: `1px solid ${aiHealth?.openai_configured ? 'rgba(74,222,128,0.3)' : 'rgba(239,68,68,0.3)'}`,
              }}
            >
              {aiHealth?.openai_configured ? '✓ OpenAI Activo' : '✗ OpenAI Sin Clave'}
            </span>
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: 6,
                background: aiHealth?.gemini_configured ? 'rgba(74,222,128,0.15)' : 'rgba(239,68,68,0.15)',
                color: aiHealth?.gemini_configured ? '#4ade80' : '#f87171',
                border: `1px solid ${aiHealth?.gemini_configured ? 'rgba(74,222,128,0.3)' : 'rgba(239,68,68,0.3)'}`,
              }}
            >
              {aiHealth?.gemini_configured ? '✓ Gemini Activo' : '✗ Gemini Sin Clave'}
            </span>
          </div>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#c4b5fd', marginBottom: 6 }}>
              OpenAI API Key (gpt-4o-mini)
            </label>
            <input
              type="password"
              placeholder={aiHealth?.openai_configured ? '•••••••••••••••••••••••••••••••• (Configurada)' : 'sk-proj-...'}
              value={openaiKey}
              onChange={e => setOpenaiKey(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: 8,
                background: '#0e0d1a',
                border: '1px solid rgba(139,92,246,0.3)',
                color: '#f8fafc',
                fontSize: 13,
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
            <span style={{ fontSize: 11, color: '#64748b', marginTop: 4, display: 'block' }}>
              Utilizado para extracción de alta precisión y tablas complejas.
            </span>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#c4b5fd', marginBottom: 6 }}>
              Google Gemini API Key (gemini-2.5-flash-lite)
            </label>
            <input
              type="password"
              placeholder={aiHealth?.gemini_configured ? '•••••••••••••••••••••••••••••••• (Configurada)' : 'AIzaSy...'}
              value={geminiKey}
              onChange={e => setGeminiKey(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: 8,
                background: '#0e0d1a',
                border: '1px solid rgba(139,92,246,0.3)',
                color: '#f8fafc',
                fontSize: 13,
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
            <span style={{ fontSize: 11, color: '#64748b', marginTop: 4, display: 'block' }}>
              Utilizado como motor de validación semántica gratuita y rápida.
            </span>
          </div>

          {msg && (
            <div
              style={{
                padding: '10px 14px',
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 600,
                background: msg.type === 'ok' ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                color: msg.type === 'ok' ? '#4ade80' : '#f87171',
                border: `1px solid ${msg.type === 'ok' ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
              }}
            >
              {msg.text}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '10px 18px',
                borderRadius: 8,
                background: 'transparent',
                border: '1px solid rgba(255,255,255,0.15)',
                color: '#cbd5e1',
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              style={{
                padding: '10px 22px',
                borderRadius: 8,
                background: saving ? '#4b5563' : 'linear-gradient(135deg, #8b5cf6, #6366f1)',
                border: 'none',
                color: '#fff',
                fontSize: 13,
                fontWeight: 700,
                cursor: saving ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 14px rgba(139,92,246,0.35)',
              }}
            >
              {saving ? 'Guardando...' : 'Guardar Claves'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
