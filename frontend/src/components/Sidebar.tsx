// Sidebar — v4: inline styles for consistent font + spacing
const NAV = [
  { icon: 'assignment',  label: 'Solicitudes',   id: 'solicitudes' },
  { icon: 'fact_check',  label: 'Verificador',   id: 'verificador' },
  { icon: 'description', label: 'Generador DJC', id: 'generador' },
  { icon: 'electric_bolt', label: 'Eficiencia Energética', id: 'ee' },
  { icon: 'info',        label: 'Info Panel',     id: 'info' },
  { icon: 'settings',    label: 'Configuracion',  id: 'config' },
]

interface SidebarProps {
  activeTab: string
  onTabChange: (id: string) => void
  apiVersion?: string | null
}

export default function Sidebar({ activeTab, onTabChange, apiVersion }: SidebarProps) {
  return (
    <aside style={{
      width: 220,
      height: '100vh',
      background: '#12121e',
      position: 'fixed',
      left: 0, top: 0,
      zIndex: 50,
      display: 'flex',
      flexDirection: 'column',
      fontFamily: '"Plus Jakarta Sans", "Inter", sans-serif',
      borderRight: '1px solid rgba(255,255,255,0.04)',
    }}>

      {/* Logo */}
      <div style={{ padding: '28px 20px 24px', display: 'flex', alignItems: 'center', gap: 12 }}>
        <svg viewBox="0 0 80 80" width="36" height="36" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0 }}>
          <circle cx="40" cy="18" r="6" fill="#8b5cf6"/>
          <circle cx="62" cy="32" r="4" fill="#a78bfa"/>
          <circle cx="58" cy="58" r="5" fill="#8b5cf6"/>
          <circle cx="32" cy="65" r="4" fill="#a78bfa"/>
          <circle cx="16" cy="48" r="5" fill="#8b5cf6"/>
          <circle cx="20" cy="26" r="3.5" fill="#a78bfa"/>
          <circle cx="40" cy="42" r="7" fill="#7c3aed"/>
          <line x1="40" y1="24" x2="40" y2="35" stroke="#8b5cf6" strokeWidth="1.5" strokeOpacity="0.5"/>
          <line x1="45" y1="18" x2="58" y2="30" stroke="#8b5cf6" strokeWidth="1.5" strokeOpacity="0.5"/>
          <line x1="62" y1="36" x2="55" y2="54" stroke="#8b5cf6" strokeWidth="1.5" strokeOpacity="0.5"/>
          <line x1="53" y1="60" x2="43" y2="64" stroke="#8b5cf6" strokeWidth="1.5" strokeOpacity="0.5"/>
          <line x1="28" y1="63" x2="21" y2="52" stroke="#8b5cf6" strokeWidth="1.5" strokeOpacity="0.5"/>
          <line x1="16" y1="43" x2="20" y2="30" stroke="#8b5cf6" strokeWidth="1.5" strokeOpacity="0.5"/>
          <line x1="23" y1="26" x2="35" y2="38" stroke="#8b5cf6" strokeWidth="1.5" strokeOpacity="0.5"/>
          <line x1="45" y1="46" x2="54" y2="56" stroke="#8b5cf6" strokeWidth="1.5" strokeOpacity="0.35"/>
          <line x1="35" y1="44" x2="21" y2="48" stroke="#8b5cf6" strokeWidth="1.5" strokeOpacity="0.35"/>
        </svg>
        <span style={{ color: '#f8fafc', fontWeight: 700, fontSize: 17, letterSpacing: '0.06em' }}>ARGOS</span>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '0 12px', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {NAV.map(item => {
          const isActive = activeTab === item.id
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '11px 14px',
                borderRadius: 10,
                border: 'none',
                cursor: 'pointer',
                fontFamily: 'inherit',
                fontWeight: isActive ? 600 : 500,
                fontSize: 13,
                letterSpacing: '0.01em',
                textAlign: 'left',
                width: '100%',
                transition: 'all 0.15s',
                background: isActive ? '#1f1e2a' : 'transparent',
                color: isActive ? (item.id === 'ee' ? '#6bd8cb' : '#d0bcff') : '#64748b',
                borderLeft: isActive ? (item.id === 'ee' ? '3px solid #6bd8cb' : '3px solid #8b5cf6') : '3px solid transparent',
              }}
              onMouseEnter={e => {
                if (!isActive) {
                  (e.currentTarget as HTMLButtonElement).style.background = '#1a1929'
                  ;(e.currentTarget as HTMLButtonElement).style.color = item.id === 'ee' ? '#6bd8cb' : '#cbc3d7'
                }
              }}
              onMouseLeave={e => {
                if (!isActive) {
                  (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                  ;(e.currentTarget as HTMLButtonElement).style.color = '#64748b'
                }
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 20, lineHeight: 1 }}>{item.icon}</span>
              {item.label}
            </button>
          )
        })}

        {/* Divider */}
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', margin: '8px 0' }} />
      </nav>

      {/* Version */}
      <div style={{ padding: '16px 28px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <span style={{ fontSize: 10, fontFamily: 'monospace', color: 'rgba(255,255,255,0.35)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
          v{apiVersion || '3.2.2'}
        </span>
      </div>
    </aside>
  )
}