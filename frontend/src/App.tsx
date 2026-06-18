import { useEffect, useRef, useState } from 'react'
import Sidebar from './components/Sidebar'
import LogBar from './components/LogBar'
import GeneradorDJC from './views/GeneradorDJC'
import EficienciaEnergetica from './views/EficienciaEnergetica'
import Solicitudes from './views/Solicitudes'
import { checkHealth, getConfig, type Config } from './api/client'
import './index.css'

interface LogEntry {
  level: string
  msg: string
  ts: string
}

function now() {
  return new Date().toLocaleTimeString('es-AR', { hour12: false })
}

export default function App() {
  const [activeTab, setActiveTab] = useState('generador')
  const [apiOk, setApiOk]         = useState<boolean | null>(null)
  const [apiVersion, setApiVersion] = useState<string | null>(null)
  const [config, setConfig]       = useState<Config | null>(null)
  const [logs, setLogs]           = useState<LogEntry[]>([])
  const [logsExpanded, setLogsExpanded] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const addLog = (level: string, msg: string) => {
    setLogs(prev => [...prev.slice(-200), { level, msg, ts: now() }])
  }

  // Health check — polls every 5s, auto-recovers when API comes online
  useEffect(() => {
    let cancelled = false
    let configLoaded = false

    const poll = async () => {
      if (cancelled) return
      const ver = await checkHealth()
      const ok = ver !== null
      if (cancelled) return
      setApiOk(prev => {
        if (prev === false && ok) addLog('info', 'Backend conectado')
        if (prev !== false && !ok && prev !== null) addLog('error', 'Backend no disponible — iniciá Iniciar API.bat')
        return ok
      })
      if (ok && ver) {
        setApiVersion(ver)
      }
      // Load config once API is up
      if (ok && !configLoaded) {
        configLoaded = true
        getConfig().then(setConfig).catch(() =>
          addLog('warning', 'No se pudo cargar la configuracion')
        )
      }
      setTimeout(poll, 5000)
    }
    poll()
    return () => { cancelled = true }
  }, [])

  // WebSocket live logs — auto-reconnects every 3s
  useEffect(() => {
    const connect = () => {
      const host = window.location.host;
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${wsProtocol}//${host}/ws/log`)
      wsRef.current = ws
      ws.onmessage = (e) => {
        try {
          const d = JSON.parse(e.data)
          addLog(d.level ?? 'info', d.msg ?? String(e.data))
        } catch {
          addLog('info', e.data)
        }
      }
      ws.onerror = () => ws.close()
      ws.onclose = () => setTimeout(connect, 3000)
    }
    connect()
    return () => { wsRef.current?.close() }
  }, [])

  return (
    <div className="flex h-screen overflow-hidden relative">
      {/* Ambient glows */}
      <div className="glow-purple" />
      <div className="glow-teal" />

      {/* Sidebar */}
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} apiVersion={apiVersion} />

      {/* Main */}
      <main className="flex-1 flex flex-col h-screen relative" style={{ marginLeft: 220 }}>

        {/* Top bar — fixed 64px */}
        <header
          className="fixed top-0 right-0 h-16 z-40 flex justify-between items-center"
          style={{
            width: 'calc(100% - 220px)',
            padding: '0 28px 0 32px',
            background: 'rgba(13,13,24,0.85)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(255,255,255,0.04)',
          }}
        >
          <h1 className="text-2xl font-bold tracking-tight text-white">
          {activeTab === 'generador'     ? 'Generador DJC'
             : activeTab === 'verificador' ? 'Verificador'
             : activeTab === 'ee'          ? 'Eficiencia Energética'
             : activeTab === 'solicitudes' ? 'Solicitudes'
             : activeTab === 'info'        ? 'Info Panel'
             : 'Configuracion'}
          </h1>
          <div className="flex items-center gap-5" style={{ marginRight: 4 }}>
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold tracking-wide uppercase"
              style={{
                background: apiOk ? 'rgba(0,167,75,0.1)' : 'rgba(239,68,68,0.1)',
                borderColor: apiOk ? 'rgba(74,225,118,0.2)' : 'rgba(239,68,68,0.2)',
                color: apiOk === null ? '#94a3b8' : apiOk ? '#4ae176' : '#ef4444',
              }}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{
                  background: apiOk === null ? '#94a3b8' : apiOk ? '#4ae176' : '#ef4444',
                  boxShadow: apiOk ? '0 0 8px rgba(74,225,118,0.6)' : undefined,
                }}
              />
              {apiOk === null ? 'Conectando...' : apiOk ? 'API Active: OK' : 'API Offline'}
            </div>
          </div>
        </header>

        {/* Content — offset 64px header + 12px breathing room */}
        <div
          className="overflow-y-auto custom-scrollbar"
          style={{
            paddingTop: 88,
            paddingLeft: 32,
            paddingRight: 32,
            paddingBottom: logsExpanded ? 212 : 56,
          }}
        >
          {activeTab === 'generador' && (
            <GeneradorDJC config={config} onLog={addLog} />
          )}
          {activeTab === 'ee' && (
            <EficienciaEnergetica onLog={addLog} />
          )}
          {activeTab === 'solicitudes' && (
            <Solicitudes onLog={addLog} />
          )}
          {activeTab === 'verificador' && (
            <PlaceholderView title="Verificador" icon="fact_check" msg="Modulo en construccion" />
          )}
          {activeTab === 'info' && (
            <PlaceholderView title="Info Panel" icon="info" msg="Modulo en construccion" />
          )}
          {activeTab === 'config' && (
            <PlaceholderView title="Configuracion" icon="settings" msg="Modulo en construccion" />
          )}
        </div>

        {/* Log bar */}
        <LogBar logs={logs} expanded={logsExpanded} onToggle={() => setLogsExpanded(v => !v)} />
      </main>
    </div>
  )
}

function PlaceholderView({ title, icon, msg }: { title: string; icon: string; msg: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-96 gap-4">
      <span className="material-symbols-outlined" style={{ fontSize: 56, color: '#343440' }}>{icon}</span>
      <p className="text-lg font-bold" style={{ color: '#494454' }}>{title}</p>
      <p className="text-sm" style={{ color: '#343440' }}>{msg}</p>
    </div>
  )
}