// GeneradorDJC — flujo completo replicando el legacy argos_main.py
// FASE 1: Config inicial (Bidcom + Modo + cert drop)
// FASE 2: Panel de revisión/edición de todos los campos extraídos
// FASE 3: GENERAR (usa los valores editados, no los crudos)

import { useState, useRef, useCallback } from 'react'
import {
  extractCert, generateDJC, confirmDJC, downloadPdf, makeBlobUrl,
  type Config, type GenerateParams, type GenerateResult,
} from '../api/client'

interface Props {
  config: Config | null
  onLog: (level: string, msg: string) => void
}

// Todos los campos editables del formulario de revisión
interface DJCFormData {
  // Identificación
  djc_id: string
  enlace_djc: string
  // Producto
  marca: string
  fabricante: string
  direccion: string
  producto_desc: string
  modelos: string
  specs: string
  // Certificado
  cert_number: string
  normas: string
  fecha_emision: string
  fecha_vencimiento: string
  // Certificación
  reglamento: string
  esquema: string
  oec_key: string
}

function cleanSocName(key: string): string {
  return key.replace(/\s*S\.R\.L\.?/gi, '').replace(/\s*SRL/gi, '').replace(/\s*S\.A\.?/gi, '').trim()
}

export default function GeneradorDJC({ config, onLog }: Props) {
  // ── Fase 1: config ──────────────────────────────────────────────
  const [bidcom, setBidcom]         = useState('')
  const [modo, setModo]             = useState<'comun' | 'extension'>('comun')
  const [sociedades, setSociedades] = useState<string[]>([])
  const [notaFile, setNotaFile]     = useState<File | null>(null)

  // ── Fase 1: cert drop ───────────────────────────────────────────
  const [certFile, setCertFile]   = useState<File | null>(null)
  const [dragging, setDragging]   = useState(false)
  const [extracting, setExtracting] = useState(false)

  // ── Fase 2: form de revisión ────────────────────────────────────
  const [form, setForm]           = useState<DJCFormData | null>(null)
  const [wantNormal, setWantNormal]         = useState(true)
  const [wantCodificada, setWantCodificada] = useState(false)

  // ── Fase 3: generación + preview ───────────────────────────────────
  const [generating, setGenerating] = useState(false)
  const [previewResults, setPreviewResults] = useState<GenerateResult[] | null>(null)
  const [previewIdx, setPreviewIdx] = useState(0)
  const [confirming, setConfirming] = useState(false)
  // Nombres de archivo calculados para cada resultado en preview
  const [previewFilenames, setPreviewFilenames] = useState<string[]>([])
  // bidComStr guardado para el confirm
  const [lastBidcom, setLastBidcom] = useState('')

  const certInputRef = useRef<HTMLInputElement>(null)
  const notaInputRef = useRef<HTMLInputElement>(null)

  // ── Helpers ─────────────────────────────────────────────────────
  const reglamentoOptions = config?.reglamento_options ?? []
  const esquemaOptions    = config?.esquema_options ?? []
  const oecOptions        = Object.keys(config?.oec_options ?? {})
  const sociedadesOptions = Object.keys(config?.sociedades_extension ?? {})
  const enlaceDjcBase     = config?.enlace_djc_base ?? 'https://qr.gadnic.com/certifications/certificado-'

  function buildDjcId(reglamento: string, oec_key: string, bidcomVal: string): string {
    // Réplica exacta de generate_djc_id() en m3_djc_generator.py
    const reglRaw = reglamento.toLowerCase()
    const reglAbrev =
      /juguete|163\/2004|nm 300/.test(reglRaw)                               ? 'SJ' :
      /16\/2025|17\/2025|60335|62368|62841|62040|60065/.test(reglRaw)        ? 'SE' :
      /eficiencia energ|mínima eficien/.test(reglRaw)                        ? 'EE' :
      /biciclet|nm 301/.test(reglRaw)                                         ? 'BI' :
      /anteojos|iso 12312/.test(reglRaw)                                      ? 'AO' :
      /encendedor|iso 9994|iram 3980/.test(reglRaw)                          ? 'EN' :
      /ftalato|583\/2008/.test(reglRaw)                                       ? 'FT' : 'OT'

    // OEC — mismo mapa que el backend
    const oecAbrevMap: Record<string, string> = {
      'Lenor':          'LNR',
      'Quektra':        'QKA',
      'Intertek':       'ITK',
      'Bureau Veritas': 'BVA',
      'TÜV':            'TUV',
      'IRAM':           'IRM',
    }
    const oecAbrev = oecAbrevMap[oec_key] ?? (oec_key.slice(0, 3).toUpperCase() || 'OEC')

    // Formato fecha: MMAA (mes primero, 2 dígitos año) — ej: 0426
    const now = new Date()
    const mm = String(now.getMonth() + 1).padStart(2, '0')  // 04
    const aa = String(now.getFullYear()).slice(2)             // 26
    const mmaa = `${mm}${aa}`                                 // 0426

    const bidStr = bidcomVal ? `C${bidcomVal.replace(/^C/i, '')}` : 'XXXX'
    return `DJC-${reglAbrev}-${mmaa}-${bidStr}-${oecAbrev}-V1`
  }

  // ── PASO 1: Archivo cargado → extrae ───────────────────────────
  const handleCertFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      onLog('warning', 'Solo se aceptan archivos PDF')
      return
    }
    setCertFile(file)
    setForm(null)
    setExtracting(true)
    onLog('info', `[M3] Extrayendo texto del PDF: ${file.name}`)
    try {
      const r = await extractCert(file)

      onLog('info', `[M3] ── Nro. Certificado : ${r.cert_number || '[no encontrado]'}`)
      onLog('info', `[M3] ── OEC detectado   : ${r.oec_key || '[desconocido]'}`)
      onLog('info', `[M3] ── Reglamento      : ${r.reglamento || '[no detectado]'}`)
      onLog('info', `[M3] ── Normas          : ${r.normas || '[ninguna]'}`)
      onLog('info', `[M3] ── Fecha emisión   : ${r.fecha_emision || '[no encontrada]'}`)
      onLog('info', `[M3] ── Fecha venc.     : ${r.fecha_vencimiento || '[no encontrada]'}`)
      onLog('info', `[M3] ── Marca           : ${r.marca || '[vacía]'}`)
      onLog('info', `[M3] ── Fabricante      : ${r.fabricante?.slice(0, 60) || '[vacío]'}`)
      onLog('info', `[M3] ── Modelos         : ${r.modelos?.slice(0, 80) || '[vacíos]'}`)

      const bidVal = bidcom.trim() ? (bidcom.trim().match(/^\d+$/) ? `C${bidcom.trim()}` : bidcom.trim()) : ''
      const numBidcom = bidVal.replace(/^C/i, '')
      const djcId = buildDjcId(r.reglamento, r.oec_key, numBidcom)
      // Siempre certificacion- + nro bidcom (no certificado- y no nro de cert)
      const enlace = numBidcom ? `https://qr.gadnic.com/certifications/certificacion-${numBidcom}` : ''

      setForm({
        djc_id: djcId,
        enlace_djc: enlace,
        marca: r.marca,
        fabricante: r.fabricante,
        direccion: r.direccion,
        producto_desc: r.producto_desc,
        modelos: r.modelos,
        specs: r.specs,
        cert_number: r.cert_number,
        normas: r.normas,
        fecha_emision: r.fecha_emision,
        fecha_vencimiento: r.fecha_vencimiento,
        reglamento: r.reglamento || (reglamentoOptions[0] ?? ''),
        esquema: esquemaOptions[0] ?? '',
        oec_key: r.oec_key || (oecOptions[0] ?? ''),
      })

      onLog('info', '[M3] ✓ Datos listos — revisá el formulario antes de generar')
    } catch (e: unknown) {
      onLog('error', `[M3] Error en extracción: ${e instanceof Error ? e.message : String(e)}`)
      setCertFile(null)
    } finally {
      setExtracting(false)
    }
  }, [bidcom, enlaceDjcBase, esquemaOptions, oecOptions, reglamentoOptions, onLog])

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleCertFile(file)
  }

  const setField = (key: keyof DJCFormData, val: string) =>
    setForm(prev => prev ? { ...prev, [key]: val } : prev)

  // Cuando cambia Bidcom → recalcular djc_id y enlace si ya hay form
  const handleBidcomChange = (val: string) => {
    setBidcom(val)
    if (form) {
      const numBidcom = val.trim().replace(/^C/i, '')
      const bidStr = numBidcom || '0000'
      // Reemplaza el número en el djc_id existente
      const newId = form.djc_id.replace(/C\d+/, `C${bidStr}`)
      setForm(prev => prev ? {
        ...prev,
        djc_id: newId,
        enlace_djc: `${enlaceDjcBase}${numBidcom}`,
      } : prev)
    }
  }

  // ── PASO 3: Generar ─────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!certFile || !form) { onLog('warning', 'Primero cargá un certificado'); return }
    const versiones = [...(wantNormal ? ['normal'] : []), ...(wantCodificada ? ['codificada'] : [])]
    if (versiones.length === 0) { onLog('warning', 'Seleccioná al menos una versión (Normal o Codificada)'); return }
    if (modo === 'extension' && sociedades.length === 0) { onLog('warning', '[M3] Seleccioná al menos una sociedad para extender'); return }
    if (modo === 'extension' && !notaFile) { onLog('warning', '[M3] Cargá la Nota de Extensión (PDF) antes de generar'); return }

    const bidComStr = bidcom.trim().match(/^\d+$/) ? `C${bidcom.trim()}` : bidcom.trim()

    setGenerating(true)
    onLog('info', `=== GENERANDO DJC ===`)
    onLog('info', `[M3] Modo: ${modo} | Versiones: ${versiones.join('+')} | Bidcom: ${bidComStr || '[sin número]'}`)
    if (modo === 'extension') {
      onLog('info', `[M3] Extensiones: ${sociedades.join(', ')}`)
    }

    const params: GenerateParams = {
      versiones,
      modo,
      sociedades: modo === 'extension' ? sociedades : [],
      djc_id: form.djc_id,
      enlace_djc: form.enlace_djc,
      cert_number: form.cert_number,
      oec_key: form.oec_key,
      normas: form.normas,
      fecha_emision: form.fecha_emision,
      fecha_vencimiento: form.fecha_vencimiento,
      fabricante: form.fabricante,
      direccion: form.direccion,
      marca: form.marca,
      modelos: form.modelos,
      producto_desc: form.producto_desc,
      specs: form.specs,
      bidcom_num: bidComStr,
      reglamento: form.reglamento,
      esquema: form.esquema,
      output_dir: '',
      save_to_disk: false,
    }

    try {
      const results = await generateDJC(params, certFile, notaFile ?? undefined)
      // Calcular filenames: normal = djc_id, codificada = djc_id con COD antes del V
      const fnames = results.map(r => {
        const socSuffix = r.society ? `_${cleanSocName(r.society)}` : ''
        if (r.version === 'codificada') {
          // DJC-SE-0426-C916-QKA-V1 → DJC-SE-0426-C916-QKA-COD-V1
          const codId = form.djc_id.replace(/-V(\d+)$/, '-COD-V$1')
          return `${codId}${socSuffix}.pdf`
        }
        return `${form.djc_id}${socSuffix}.pdf`
      })
      setPreviewFilenames(fnames)
      setPreviewResults(results)
      setPreviewIdx(0)
      setLastBidcom(bidComStr)
      onLog('info', `[M3] Prevista lista — revisá el PDF antes de confirmar (${results.length} archivo(s))`)
    } catch (e: unknown) {
      onLog('error', `[M3] Error generando: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setGenerating(false)
    }
  }

  // ── Confirmar preview → guardar en disco + descargar ──────────────
  const handleConfirm = async () => {
    if (!previewResults || !form) return
    setConfirming(true)
    try {
      const items = previewResults.map((r, i) => ({
        filename: previewFilenames[i] ?? `DJC_${r.version}.pdf`,
        bidcom_num: lastBidcom,
        society_key: r.society ?? '',
        pdf_b64: r.pdf_b64,
      }))
      await confirmDJC(items)
      // Descargar cada archivo
      for (let i = 0; i < previewResults.length; i++) {
        const r = previewResults[i]
        const fname = previewFilenames[i] ?? `DJC_${r.version}.pdf`
        downloadPdf(r.pdf_b64, fname)
        onLog('info', `Descargado: ${fname}`)
      }
      onLog('info', `[M3] === DJC GUARDADA EXITOSAMENTE ===`)
    } catch (e: unknown) {
      onLog('error', `[M3] Error guardando: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      // Siempre cerrar el panel — si hubo error el log lo muestra
      setConfirming(false)
      setPreviewResults(null)
    }
  }

  const handleDiscard = () => {
    onLog('info', '[M3] Generación descartada por el usuario. Podés editar y reintentar.')
    setPreviewResults(null)
  }

  const toggleSociedad = (key: string) =>
    setSociedades(prev => prev.includes(key) ? prev.filter(s => s !== key) : [...prev, key])

  const resetCert = () => { setCertFile(null); setForm(null); }

  const busy = extracting || generating

  // ────────────────────────────────────────────────────────────────
  // RENDER
  // ────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Panel de preview — full-screen overlay cuando hay resultados */}
      {previewResults && (
        <PreviewPanel
          results={previewResults}
          filenames={previewFilenames}
          activeIdx={previewIdx}
          onTabChange={setPreviewIdx}
          onConfirm={handleConfirm}
          onDiscard={handleDiscard}
          confirming={confirming}
        />
      )}

    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 860, margin: '0 auto' }}>

      {/* ══════════════════════════════════════════════════════
          BLOQUE 1: CONFIGURACIÓN INICIAL
          ══════════════════════════════════════════════════════ */}
      <Card>
        <SectionTitle icon="settings" text="Configuración" />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          {/* Bidcom */}
          <FormField label="Nro. Bidcom">
            <div style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#8b5cf6', fontWeight: 700, fontSize: 14 }}>C</span>
              <input
                type="text"
                value={bidcom}
                onChange={e => handleBidcomChange(e.target.value)}
                placeholder="912"
                style={inputStyle({ pl: 28 })}
              />
            </div>
            <span style={{ fontSize: 11, color: '#64748b', marginTop: 3 }}>Editable también en el formulario</span>
          </FormField>

          {/* Modo */}
          <FormField label="Tipo de DJC">
            <div style={{ display: 'flex', gap: 8 }}>
              {(['comun', 'extension'] as const).map(m => (
                <button key={m} onClick={() => setModo(m)} style={modoBtnStyle(modo === m)}>
                  {m === 'comun' ? '📋 Común' : '🔗 Extensión'}
                </button>
              ))}
            </div>
          </FormField>
        </div>

        {/* Panel de extensión */}
        {modo === 'extension' && (
          <div style={{ marginTop: 16, padding: '16px', background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 10 }}>
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', color: '#8b5cf6', textTransform: 'uppercase', marginBottom: 10 }}>
              Sociedades a extender
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 14 }}>
              {sociedadesOptions.map(key => {
                const active = sociedades.includes(key)
                return (
                  <button key={key} onClick={() => toggleSociedad(key)}
                    style={{ padding: '7px 14px', borderRadius: 7, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer', transition: 'all 0.15s',
                      background: active ? '#8b5cf6' : 'transparent',
                      color: active ? '#fff' : '#8b5cf6',
                      border: active ? 'none' : '1px solid rgba(139,92,246,0.35)' }}
                  >{cleanSocName(key)}</button>
                )
              })}
            </div>

            {/* Nota de extensión */}
            <div
              onClick={() => notaInputRef.current?.click()}
              style={{ border: `2px dashed ${notaFile ? 'rgba(139,92,246,0.6)' : 'rgba(73,68,84,0.4)'}`,
                borderRadius: 8, padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 10,
                cursor: 'pointer', background: notaFile ? 'rgba(139,92,246,0.06)' : 'transparent' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 22, color: notaFile ? '#8b5cf6' : '#64748b' }}>attach_file</span>
              <div>
                <p style={{ fontSize: 13, fontWeight: 600, color: notaFile ? '#f8fafc' : '#64748b' }}>
                  {notaFile ? notaFile.name : 'Arrastrar Nota de Extensión (PDF) aquí'}
                </p>
                {notaFile && (
                  <button style={{ fontSize: 11, color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer', padding: 0, marginTop: 2 }}
                    onClick={e => { e.stopPropagation(); setNotaFile(null) }}>✕ quitar</button>
                )}
                {!notaFile && <p style={{ fontSize: 11, color: '#475569', marginTop: 1 }}>PDF requerido para modo Extensión</p>}
              </div>
            </div>
            <input ref={notaInputRef} type="file" accept=".pdf" style={{ display: 'none' }}
              onChange={e => setNotaFile(e.target.files?.[0] ?? null)} />
          </div>
        )}
      </Card>

      {/* ══════════════════════════════════════════════════════
          BLOQUE 2: CERTIFICADO PDF
          ══════════════════════════════════════════════════════ */}
      <Card>
        <SectionTitle icon="description" text="Certificado PDF" />

        {!certFile ? (
          <div
            onDragOver={e => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => certInputRef.current?.click()}
            style={{
              minHeight: 130, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              border: `2px dashed ${dragging ? '#8b5cf6' : 'rgba(139,92,246,0.35)'}`,
              borderRadius: 10, cursor: 'pointer', transition: 'all 0.2s',
              background: dragging ? 'rgba(139,92,246,0.06)' : 'transparent',
              boxShadow: dragging ? '0 0 24px rgba(139,92,246,0.15)' : undefined,
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 44, color: '#8b5cf6', marginBottom: 10 }}>cloud_upload</span>
            <p style={{ color: '#f8fafc', fontWeight: 600, fontSize: 15 }}>Arrastrar certificado aquí</p>
            <p style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>o hacé click para explorar (Max 10MB)</p>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 18px',
            background: 'rgba(74,225,118,0.06)', border: '1px solid rgba(74,225,118,0.2)', borderRadius: 10 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 28, color: '#4ae176' }}>check_circle</span>
            <div style={{ flex: 1 }}>
              <p style={{ fontWeight: 600, fontSize: 14, color: '#f8fafc' }}>{certFile.name}</p>
              <p style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{(certFile.size / 1024).toFixed(0)} KB</p>
            </div>
            {!extracting && (
              <button onClick={resetCert}
                style={{ fontSize: 12, color: '#94a3b8', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: 6, padding: '4px 10px', cursor: 'pointer' }}>✕ quitar</button>
            )}
          </div>
        )}

        <input ref={certInputRef} type="file" accept=".pdf" style={{ display: 'none' }}
          onChange={e => e.target.files?.[0] && handleCertFile(e.target.files[0])} />

        {extracting && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 18px', marginTop: 10,
            background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 10 }}>
            <Spinner />
            <p style={{ fontSize: 13, color: '#94a3b8' }}>Extrayendo datos del certificado...</p>
          </div>
        )}
      </Card>

      {/* ══════════════════════════════════════════════════════
          BLOQUE 3: FORMULARIO DE REVISIÓN (aparece post-extracción)
          ══════════════════════════════════════════════════════ */}
      {form && (
        <>
          {/* Sección: Identificación */}
          <Card>
            <SectionTitle icon="badge" text="Identificación de la DJC" hint="Auto-generado desde el N° interno Bidcom" />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <EditField label="ID DJC" value={form.djc_id} onChange={v => setField('djc_id', v)}
                hint="Editá el número de versión si es necesario (ej: -V2)" />
              <EditField label="Enlace DJC" value={form.enlace_djc} onChange={v => setField('enlace_djc', v)} />
            </div>
          </Card>

          {/* Sección: Datos del Producto */}
          <Card>
            <SectionTitle icon="inventory_2" text="Datos del Producto" hint="Extraídos del PDF — verificá que coincidan" />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <EditField label="Marca" value={form.marca} onChange={v => setField('marca', v)} />
              <EditField label="Fabricante" value={form.fabricante} onChange={v => setField('fabricante', v)} />
              <EditField label="Dir. Fábrica" value={form.direccion} onChange={v => setField('direccion', v)} />
              <EditField label="Descripción del Producto" value={form.producto_desc} onChange={v => setField('producto_desc', v)} />
              <EditField label="Modelos" value={form.modelos} onChange={v => setField('modelos', v)} multiline />
              <EditField label="Specs Técnicas" value={form.specs} onChange={v => setField('specs', v)} multiline />
            </div>
          </Card>

          {/* Sección: Datos del Certificado */}
          <Card>
            <SectionTitle icon="verified_user" text="Datos del Certificado" hint="Extraídos automáticamente del PDF" />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <EditField label="Nro. Certificado (PDF)" value={form.cert_number} onChange={v => setField('cert_number', v)}
                hint="Ref. según la certificadora (ej: LCSH-2058)" />
              <EditField label="Normas Aplicadas" value={form.normas} onChange={v => setField('normas', v)} multiline />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <EditField label="Fecha Emisión" value={form.fecha_emision} onChange={v => setField('fecha_emision', v)} />
                <EditField label="Próx. Vigilancia" value={form.fecha_vencimiento} onChange={v => setField('fecha_vencimiento', v)} />
              </div>
            </div>
          </Card>

          {/* Sección: Datos de Certificación */}
          <Card>
            <SectionTitle icon="workspace_premium" text="Datos de Certificación" hint="Detectados automáticamente — podés cambiarlos si es necesario" />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <SelectField label="Reglamento Aplicable" value={form.reglamento}
                options={reglamentoOptions} onChange={v => setField('reglamento', v)} />
              <SelectField label="Esquema" value={form.esquema}
                options={esquemaOptions} onChange={v => setField('esquema', v)} />
              <SelectField label="OEC (Organismo)" value={form.oec_key}
                options={oecOptions} onChange={v => setField('oec_key', v)} />
            </div>
          </Card>

          {/* Sección: Versiones + Generar */}
          <Card>
            <SectionTitle icon="output" text="Versiones a Generar" />

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 32, marginBottom: 20 }}>
              <VersionCheck label="📄  Normal" checked={wantNormal} onChange={setWantNormal} />
              <VersionCheck label="🔒  Codificada" checked={wantCodificada} onChange={setWantCodificada} />
            </div>

            {/* Hint debajo de los checkboxes, separado */}
            <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
              {wantCodificada && (
                <span style={{ fontSize: 12, color: '#8b5cf6', background: 'rgba(139,92,246,0.08)',
                  border: '1px solid rgba(139,92,246,0.2)', borderRadius: 6, padding: '4px 10px' }}>
                  🔒 Fabricante y dirección se reemplazan con texto restringido
                </span>
              )}
              {wantNormal && wantCodificada && (
                <span style={{ fontSize: 12, color: '#64748b' }}>· generará 2 archivos</span>
              )}
            </div>

            <button
              onClick={handleGenerate}
              disabled={busy}
              style={{
                width: '100%', height: 54, borderRadius: 12, display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: 10, color: '#fff', fontWeight: 700, fontSize: 15,
                letterSpacing: '0.08em', textTransform: 'uppercase', border: 'none', cursor: busy ? 'not-allowed' : 'pointer',
                opacity: busy ? 0.5 : 1,
                background: busy ? '#343440' : 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                boxShadow: busy ? 'none' : '0 4px 20px rgba(139,92,246,0.35)',
                transition: 'all 0.2s',
              }}
            >
              {generating
                ? <><Spinner /><span>Generando...</span></>
                : <><span className="material-symbols-outlined" style={{ fontSize: 22 }}>description</span>
                   <span>GENERAR DJC {modo === 'extension' ? `(${sociedades.length} sociedad${sociedades.length !== 1 ? 'es' : ''})` : ''}</span></>
              }
            </button>
          </Card>
        </>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
        input, textarea, select { transition: border-color 0.15s; }
        input:focus, textarea:focus, select:focus { outline: none; border-color: rgba(139,92,246,0.7) !important; }
      `}</style>
    </div>
    </>
  )
}

// ── Sub-components ────────────────────────────────────────────────

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ background: '#1f1e2a', borderRadius: 14, padding: 28,
      border: '1px solid rgba(255,255,255,0.04)', boxShadow: '0 4px 24px rgba(0,0,0,0.25)' }}>
      {children}
    </div>
  )
}

function SectionTitle({ icon, text, hint }: { icon: string; text: string; hint?: string }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="material-symbols-outlined" style={{ fontSize: 18, color: '#8b5cf6' }}>{icon}</span>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc', letterSpacing: '0.05em', textTransform: 'uppercase' }}>{text}</h3>
      </div>
      {hint && <p style={{ fontSize: 11, color: '#64748b', marginTop: 4, marginLeft: 26 }}>{hint}</p>}
    </div>
  )
}

function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <label style={{ fontSize: 12, fontWeight: 600, color: '#cbc3d7' }}>{label}</label>
      {children}
    </div>
  )
}

function EditField({ label, value, onChange, hint, mono, multiline }:
  { label: string; value: string; onChange: (v: string) => void; hint?: string; mono?: boolean; multiline?: boolean }) {
  const base = inputStyle({ mono, multiline })
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#958ea0', textTransform: 'uppercase' }}>{label}</label>
      {multiline
        ? <textarea value={value} onChange={e => onChange(e.target.value)} rows={3} style={base} />
        : <input type="text" value={value} onChange={e => onChange(e.target.value)} style={base} />
      }
      {hint && <p style={{ fontSize: 10, color: '#475569' }}>{hint}</p>}
    </div>
  )
}

function SelectField({ label, value, options, onChange }:
  { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#958ea0', textTransform: 'uppercase' }}>{label}</label>
      <div style={{ position: 'relative' }}>
        <select value={value} onChange={e => onChange(e.target.value)} style={inputStyle({})}>
          {options.length === 0 && <option value="">Cargando...</option>}
          {options.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
        <span className="material-symbols-outlined" style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
          fontSize: 18, color: '#64748b', pointerEvents: 'none' }}>expand_more</span>
      </div>
    </div>
  )
}

function VersionCheck({ label, checked, onChange, hint }:
  { label: string; checked: boolean; onChange: (v: boolean) => void; hint?: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }} onClick={() => onChange(!checked)}>
        <div style={{
            width: 22, height: 22, borderRadius: 6, flexShrink: 0,
            border: `2px solid ${checked ? '#8b5cf6' : 'rgba(139,92,246,0.35)'}`,
            background: checked ? '#8b5cf6' : 'rgba(139,92,246,0.05)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.15s', cursor: 'pointer',
          }}
        >
          {checked && <span style={{ color: '#fff', fontSize: 14, lineHeight: 1, fontWeight: 700 }}>✓</span>}
        </div>
        <span style={{ fontSize: 14, fontWeight: 600, color: checked ? '#f8fafc' : '#94a3b8', userSelect: 'none' }}>{label}</span>
      </div>
      {hint && <p style={{ fontSize: 11, color: '#475569', marginTop: 4, marginLeft: 32 }}>{hint}</p>}
    </div>
  )
}

function Spinner() {
  return <div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: '#fff', animation: 'spin 0.7s linear infinite', flexShrink: 0 }} />
}

function inputStyle({ pl, mono, multiline }: { pl?: number; mono?: boolean; multiline?: boolean }): React.CSSProperties {
  return {
    width: '100%',
    minHeight: multiline ? undefined : 46,
    background: '#161522',
    border: '1px solid rgba(139,92,246,0.18)',
    borderRadius: 10,
    padding: multiline ? '12px 16px' : '0 16px',
    paddingLeft: pl ? pl : 16,
    color: '#f1eeff',
    fontSize: mono ? 13 : 14,
    fontFamily: mono ? "'Courier New', monospace" : undefined,
    letterSpacing: mono ? '0.03em' : undefined,
    resize: multiline ? 'vertical' as const : undefined,
    boxSizing: 'border-box',
    lineHeight: multiline ? '1.6' : undefined,
  }
}

function modoBtnStyle(active: boolean): React.CSSProperties {
  return {
    flex: 1, height: 40, borderRadius: 9, fontSize: 13, fontWeight: 700, cursor: 'pointer', transition: 'all 0.15s',
    background: active ? '#8b5cf6' : 'transparent',
    color: active ? '#fff' : '#8b5cf6',
    border: active ? 'none' : '1px solid rgba(139,92,246,0.4)',
    boxShadow: active ? '0 4px 14px rgba(139,92,246,0.3)' : undefined,
  }
}

function PreviewPanel({
  results, filenames, activeIdx, onTabChange, onConfirm, onDiscard, confirming
}: {
  results: import('../api/client').GenerateResult[]
  filenames: string[]
  activeIdx: number
  onTabChange: (i: number) => void
  onConfirm: () => Promise<void>
  onDiscard: () => void
  confirming: boolean
}) {
  const active = results[activeIdx]
  const blobUrl = active ? makeBlobUrl(active.pdf_b64) : ''

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(10,10,20,0.97)',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Top bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16,
        padding: '14px 24px',
        background: '#16152a',
        borderBottom: '1px solid rgba(139,92,246,0.2)',
        flexShrink: 0,
      }}>
        <span className="material-symbols-outlined" style={{ color: '#8b5cf6', fontSize: 22 }}>preview</span>
        <span style={{ fontWeight: 700, fontSize: 15, color: '#f1eeff' }}>Previsualización DJC</span>
        <span style={{ fontSize: 12, color: '#64748b', flex: 1 }}>Revisá el PDF antes de confirmar</span>

        {/* Tabs si hay más de 1 */}
        {results.length > 1 && (
          <div style={{ display: 'flex', gap: 6 }}>
            {results.map((r, i) => (
              <button key={i} onClick={() => onTabChange(i)} style={{
                padding: '5px 14px', borderRadius: 7, fontSize: 12, fontWeight: 600,
                cursor: 'pointer', border: 'none',
                background: i === activeIdx ? '#8b5cf6' : 'rgba(139,92,246,0.15)',
                color: i === activeIdx ? '#fff' : '#a78bfa',
              }}>
                {r.version === 'normal' ? '📄 Normal' : '🔒 Codificada'}
              </button>
            ))}
          </div>
        )}

        {/* Nombre de archivo activo */}
        <span style={{
          fontSize: 11, color: '#8b5cf6', fontFamily: "'Courier New', monospace",
          background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)',
          borderRadius: 6, padding: '3px 10px',
        }}>
          {filenames[activeIdx] ?? 'DJC.pdf'}
        </span>
      </div>

      {/* Iframe — ocupa todo el espacio disponible */}
      <div style={{ flex: 1, overflow: 'hidden', background: '#111' }}>
        {blobUrl && (
          <iframe
            key={blobUrl}
            src={blobUrl}
            style={{ width: '100%', height: '100%', border: 'none' }}
            title="Vista previa DJC"
          />
        )}
      </div>

      {/* Bottom bar — acciones */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 14,
        padding: '16px 28px',
        background: '#16152a',
        borderTop: '1px solid rgba(139,92,246,0.2)',
        flexShrink: 0,
      }}>
        <span style={{ fontSize: 13, color: '#64748b', flex: 1 }}>
          {results.length > 1
            ? `${results.length} archivos listos para guardar`
            : '1 archivo listo para guardar'}
        </span>

        <button onClick={onDiscard} disabled={confirming} style={{
          padding: '10px 24px', borderRadius: 10, fontSize: 14, fontWeight: 600,
          cursor: confirming ? 'not-allowed' : 'pointer',
          background: 'transparent',
          border: '1px solid rgba(239,68,68,0.4)',
          color: '#f87171',
          display: 'flex', alignItems: 'center', gap: 8,
          opacity: confirming ? 0.5 : 1,
          transition: 'all 0.15s',
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>close</span>
          Descartar y corregir
        </button>

        <button onClick={onConfirm} disabled={confirming} style={{
          padding: '10px 30px', borderRadius: 10, fontSize: 14, fontWeight: 700,
          cursor: confirming ? 'not-allowed' : 'pointer',
          background: confirming ? '#343440' : 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
          border: 'none',
          color: '#fff',
          display: 'flex', alignItems: 'center', gap: 8,
          boxShadow: confirming ? 'none' : '0 4px 16px rgba(34,197,94,0.3)',
          letterSpacing: '0.05em',
          transition: 'all 0.15s',
        }}>
          {confirming
            ? <><Spinner /> Guardando...</>
            : <><span className="material-symbols-outlined" style={{ fontSize: 18 }}>check_circle</span> Confirmar y guardar</>
          }
        </button>
      </div>
    </div>
  )
}