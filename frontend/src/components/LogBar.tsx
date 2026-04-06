// Log bar at the bottom of the screen
interface LogEntry {
  level: string
  msg: string
  ts: string
}

interface Props {
  logs: LogEntry[]
  expanded: boolean
  onToggle: () => void
}

const levelColor: Record<string, string> = {
  info:    '#4ae176',
  warning: '#f59e0b',
  error:   '#ef4444',
}

export default function LogBar({ logs, expanded, onToggle }: Props) {
  const last = logs[logs.length - 1]

  return (
    <footer
      className="fixed bottom-0 right-0 z-50 border-t transition-all duration-300"
      style={{
        width: 'calc(100% - 220px)',
        background: '#080810',
        borderColor: 'rgba(255,255,255,0.05)',
        height: expanded ? 200 : 40,
      }}
    >
      {/* Collapsed strip */}
      <div className="flex items-center justify-between px-6 h-10">
        <div className="flex items-center gap-4">
          {last && (
            <>
              <span className="font-mono text-[10px] animate-pulse" style={{ color: levelColor[last.level] ?? '#fff' }}>
                [{last.level === 'info' ? '✓' : last.level === 'warning' ? '⚠' : '✕'}]
              </span>
              <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">
                {last.msg.length > 80 ? last.msg.slice(0, 80) + '…' : last.msg}
              </span>
            </>
          )}
          {!last && (
            <span className="font-mono text-[10px] text-slate-600 uppercase tracking-widest">
              Sistema listo
            </span>
          )}
        </div>
        <button
          onClick={onToggle}
          className="flex items-center gap-2 px-3 h-full hover:bg-white/5 transition-colors group"
        >
          <span className="text-[10px] font-mono font-bold tracking-widest uppercase" style={{ color: '#8b5cf6' }}>
            Logs del Sistema
          </span>
          <span
            className="material-symbols-outlined text-[#8b5cf6] group-hover:text-white transition-all"
            style={{
              fontSize: 16,
              transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s ease',
            }}
          >
            keyboard_arrow_up
          </span>
        </button>
      </div>

      {/* Expanded panel */}
      {expanded && (
        <div className="overflow-y-auto custom-scrollbar px-6 pb-2" style={{ maxHeight: 156 }}>
          {logs.slice().reverse().map((entry, i) => (
            <div key={i} className="flex items-start gap-3 py-0.5">
              <span className="font-mono text-[9px] text-slate-600 shrink-0 mt-0.5">{entry.ts}</span>
              <span
                className="font-mono text-[10px] uppercase tracking-widest shrink-0"
                style={{ color: levelColor[entry.level] ?? '#fff' }}
              >
                [{entry.level.slice(0,4).toUpperCase()}]
              </span>
              <span className="font-mono text-[10px] text-slate-300 break-all">{entry.msg}</span>
            </div>
          ))}
          {logs.length === 0 && (
            <p className="font-mono text-[10px] text-slate-600 pt-2">Sin entradas en el log.</p>
          )}
        </div>
      )}
    </footer>
  )
}
