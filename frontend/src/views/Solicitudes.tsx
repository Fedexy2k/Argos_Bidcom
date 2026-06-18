import { useState, useRef } from 'react'
import {
  parseDatasheet, generateSolicitud, downloadZip,
  type DatasheetParseResult, type SkuBlock,
} from '../api/client_solicitud'

interface Props {
  onLog: (level: string, msg: string) => void
}

// ── Estilos compartidos ────────────────────────────────────────────────────────
const inputStyle: React.CSSProperties = {
  width: '100%',
  minHeight: 46,
  background: '#161522',
  border: '1px solid rgba(139,92,246,0.18)',
  borderRadius: 10,
  padding: '0 16px',
  color: '#f1eeff',
  fontSize: 14,
  boxSizing: 'border-box',
  outline: 'none',
  appearance: 'none',
}

const labelStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  letterSpacing: '0.08em',
  color: '#958ea0',
  textTransform: 'uppercase',
  marginBottom: 6,
  display: 'block',
}

const cardStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.03)',
  border: '1px solid rgba(255,255,255,0.06)',
  borderRadius: 16,
  padding: '24px 28px',
  marginBottom: 24,
}

const sectionTitle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 700,
  color: '#d0bcff',
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  marginBottom: 18,
  display: 'flex',
  alignItems: 'center',
  gap: 8,
}

// ── ESQUEMAS DISPONIBLES ───────────────────────────────────────────────────────
const ESQUEMAS_QETKRA = [
  'Seguridad Eléctrica Res. SIC 16/2025',
  'Seguridad Eléctrica Res. SIC 17/2025',
]

// ── COMPONENTE PRINCIPAL ───────────────────────────────────────────────────────
export default function Solicitudes({ onLog }: Props) {
  // ── PASO 1: Carga de archivo ─────────────────────────────────────────────────
  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [dragOver, setDragOver] = useState(false)
  const [dsFile, setDsFile] = useState<File | null>(null)
  const [parsing, setParsing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // ── PASO 2: Formulario ───────────────────────────────────────────────────────
  const [data, setData] = useState<DatasheetParseResult | null>(null)
  const [oec, setOec] = useState<'lenor' | 'qetkra' | 'juguetes' | 'ftalatos'>('lenor')
  const [esquema, setEsquema] = useState(ESQUEMAS_QETKRA[0])
  const [svgFile, setSvgFile] = useState<File | null>(null)
  const svgInputRef = useRef<HTMLInputElement>(null)

  // ── PASO 3: Generación ───────────────────────────────────────────────────────
  const [generating, setGenerating] = useState(false)
  const [resultDir, setResultDir] = useState<string>('')
  const [zipBlob, setZipBlob] = useState<Blob | null>(null)

  // ── Helpers ────────────────────────────────────────────────────────────────
  const updateData = (key: keyof DatasheetParseResult, value: string) => {
    if (!data) return
    setData({ ...data, [key]: value })
  }

  const updateSku = (idx: number, field: keyof SkuBlock, value: string) => {
    if (!data) return
    const skus = [...data.skus]
    skus[idx] = { ...skus[idx], [field]: value }
    setData({ ...data, skus })
  }

  const updateSkuModelos = (idx: number, modelosStr: string) => {
    if (!data) return
    const skus = [...data.skus]
    skus[idx] = {
      ...skus[idx],
      modelos: modelosStr.split(/[,;\n]+/).map(m => m.trim()).filter(Boolean),
    }
    setData({ ...data, skus })
  }

  // ── PASO 1: Cargar y parsear datasheet ────────────────────────────────────
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleFile = (f: File) => {
    setDsFile(f)
  }

  const handleParse = async () => {
    if (!dsFile) return
    setParsing(true)
    try {
      onLog('info', `Parseando datasheet: ${dsFile.name}…`)
      const result = await parseDatasheet(dsFile)
      setData(result)
      setOec(result.oec_detected)
      setStep(2)
      onLog('info', `✓ Datasheet procesado: ${result.skus.length} SKU(s) | OEC sugerido: ${result.oec_detected.toUpperCase()}`)
    } catch (e: any) {
      onLog('error', `Error al parsear: ${e.message}`)
    } finally {
      setParsing(false)
    }
  }

  // ── PASO 3: Generar archivos ───────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!data) return
    setGenerating(true)
    setResultDir('')
    setZipBlob(null)

    try {
      onLog('info', `Generando solicitud ${oec.toUpperCase()} para ${data.certificado}…`)
      const blob = await generateSolicitud(
        { data, oec, esquema },
        (oec === 'lenor' || oec === 'qetkra') && svgFile ? svgFile : undefined,
      )
      setZipBlob(blob)
      setResultDir(`Solicitudes/${data.certificado}/`)
      setStep(3)
      onLog('info', `✓ Solicitud generada — archivos guardados en Solicitudes/${data.certificado}/`)
    } catch (e: any) {
      onLog('error', `Error al generar: ${e.message}`)
    } finally {
      setGenerating(false)
    }
  }

  const handleDownload = () => {
    if (!zipBlob || !data) return
    downloadZip(zipBlob, `Solicitud_${data.certificado}.zip`)
  }

  // ── RENDER ─────────────────────────────────────────────────────────────────
  return (
    <div style={{ maxWidth: 920, fontFamily: '"Plus Jakarta Sans", "Inter", sans-serif' }}>

      {/* Header + Stepper */}
      <div style={{ marginBottom: 32 }}>
        <p style={{ fontSize: 14, color: '#64748b', marginTop: 6 }}>
          Generá automáticamente la solicitud de certificación Excel, la nota Word y el PDF QR
          a partir de la planilla de ingeniería o un certificado PDF viejo para renovaciones.
        </p>
      </div>

      {/* Progress Steps */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 36 }}>
        {[
          { n: 1, label: 'Cargar Archivo' },
          { n: 2, label: 'Revisar y Configurar' },
          { n: 3, label: 'Descargar' },
        ].map((s, i) => (
          <div key={s.n} style={{ display: 'flex', alignItems: 'center', flex: i < 2 ? 1 : undefined }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              opacity: step >= s.n ? 1 : 0.35,
            }}>
              <div style={{
                width: 32, height: 32, borderRadius: '50%',
                background: step > s.n ? '#8b5cf6' : step === s.n ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.04)',
                border: `2px solid ${step >= s.n ? '#8b5cf6' : 'rgba(255,255,255,0.1)'}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, fontWeight: 700,
                color: step > s.n ? '#fff' : step === s.n ? '#d0bcff' : '#64748b',
                flexShrink: 0,
              }}>
                {step > s.n
                  ? <span className="material-symbols-outlined" style={{ fontSize: 16 }}>check</span>
                  : s.n}
              </div>
              <span style={{
                fontSize: 13, fontWeight: step === s.n ? 700 : 500,
                color: step === s.n ? '#d0bcff' : '#64748b',
                whiteSpace: 'nowrap',
              }}>{s.label}</span>
            </div>
            {i < 2 && (
              <div style={{
                flex: 1, height: 1, margin: '0 16px',
                background: step > s.n ? 'rgba(139,92,246,0.4)' : 'rgba(255,255,255,0.06)',
              }} />
            )}
          </div>
        ))}
      </div>

      {/* ══ PASO 1: DROPZONE ══════════════════════════════════════════════════ */}
      {step === 1 && (
        <div style={cardStyle}>
          <p style={sectionTitle}>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>upload_file</span>
            Planilla Excel (.xlsx / .xlsm) o Certificado viejo (.pdf)
          </p>

          {/* Dropzone */}
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${dragOver ? '#8b5cf6' : dsFile ? 'rgba(139,92,246,0.4)' : 'rgba(255,255,255,0.1)'}`,
              borderRadius: 14,
              padding: '52px 32px',
              textAlign: 'center',
              cursor: 'pointer',
              background: dragOver ? 'rgba(139,92,246,0.06)' : dsFile ? 'rgba(139,92,246,0.04)' : 'transparent',
              transition: 'all 0.2s',
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 48, color: dsFile ? '#8b5cf6' : '#343440' }}>
              {dsFile ? (dsFile.name.endsWith('.pdf') ? 'picture_as_pdf' : 'check_circle') : 'table_view'}
            </span>
            <p style={{ color: dsFile ? '#d0bcff' : '#64748b', marginTop: 12, fontSize: 14 }}>
              {dsFile ? dsFile.name : 'Arrastrá o hacé clic para seleccionar la planilla (.xlsx / .xlsm) o certificado viejo (.pdf)'}
            </p>
            {dsFile && (
              <p style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>
                {(dsFile.size / 1024).toFixed(1)} KB
              </p>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xlsm,.xls,.pdf"
            style={{ display: 'none' }}
            onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]) }}
          />

          {dsFile && (
            <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={handleParse}
                disabled={parsing}
                style={{
                  padding: '12px 28px',
                  background: parsing ? 'rgba(139,92,246,0.3)' : '#8b5cf6',
                  border: 'none', borderRadius: 10, cursor: parsing ? 'not-allowed' : 'pointer',
                  color: '#fff', fontSize: 14, fontWeight: 700,
                  display: 'flex', alignItems: 'center', gap: 8,
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                  {parsing ? 'sync' : 'arrow_forward'}
                </span>
                {parsing ? 'Procesando…' : 'Analizar Datasheet'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* ══ PASO 2: FORMULARIO ════════════════════════════════════════════════ */}
      {step === 2 && data && (
        <>
          {/* ── Certificadora y Trámite ─────────────────────────────────────── */}
          <div style={cardStyle}>
            <p style={sectionTitle}>
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>badge</span>
              Certificadora y Trámite
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {/* Selector OEC */}
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Organismo Certificador (OEC)</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  {[
                    { id: 'lenor', label: '🏛️ Lenor (Eléctrica)' },
                    { id: 'qetkra', label: '🔬 Qetkra (Convenio)' },
                    { id: 'juguetes', label: '🧸 Lenor Juguetes (Próximamente)' },
                    { id: 'ftalatos', label: '🧪 Lenor Ftalatos (Próximamente)' }
                  ].map(opt => (
                    <button
                      key={opt.id}
                      onClick={() => setOec(opt.id as any)}
                      style={{
                        padding: '12px 16px', borderRadius: 10,
                        border: `2px solid ${oec === opt.id ? '#8b5cf6' : 'rgba(255,255,255,0.08)'}`,
                        background: oec === opt.id ? 'rgba(139,92,246,0.12)' : 'rgba(255,255,255,0.03)',
                        color: oec === opt.id ? '#d0bcff' : '#64748b',
                        fontSize: 14, fontWeight: oec === opt.id ? 700 : 500,
                        cursor: 'pointer', textTransform: 'uppercase',
                        letterSpacing: '0.06em',
                      }}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                {(oec === 'lenor' || oec === 'qetkra') && data.oec_detected !== oec && (
                  <p style={{ fontSize: 11, color: '#f59e0b', marginTop: 6 }}>
                    ⚠️ El datasheet sugería <strong>{data.oec_detected.toUpperCase()}</strong>. Modificado manualmente.
                  </p>
                )}
              </div>

              {(oec === 'lenor' || oec === 'qetkra') && (
                <>
                  <div>
                    <label style={labelStyle}>N° de Certificado</label>
                    <input
                      style={inputStyle}
                      value={data.certificado}
                      onChange={e => updateData('certificado', e.target.value)}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Producto</label>
                    <input
                      style={inputStyle}
                      value={data.producto}
                      onChange={e => updateData('producto', e.target.value)}
                    />
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label style={labelStyle}>Normas Aplicables</label>
                    <input
                      style={inputStyle}
                      value={data.normas}
                      onChange={e => updateData('normas', e.target.value)}
                      placeholder="IEC 62040-1:2017 | IEC 62040-2:2016 (separar con |)"
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Reglamento Técnico</label>
                    <input
                      style={inputStyle}
                      value={data.reglamento}
                      onChange={e => updateData('reglamento', e.target.value)}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Laboratorio</label>
                    <input
                      style={inputStyle}
                      value={data.laboratorio}
                      onChange={e => updateData('laboratorio', e.target.value)}
                    />
                  </div>

                  {/* Esquema solo para qetkra */}
                  {oec === 'qetkra' && (
                    <div style={{ gridColumn: '1 / -1' }}>
                      <label style={labelStyle}>Esquema de Certificación (qetkra)</label>
                      <select
                        style={{ ...inputStyle, cursor: 'pointer' }}
                        value={esquema}
                        onChange={e => setEsquema(e.target.value)}
                      >
                        {ESQUEMAS_QETKRA.map(s => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {(oec === 'lenor' || oec === 'qetkra') && (
            <>
              {/* ── Datos de Fábrica ─────────────────────────────────────────────── */}
              <div style={cardStyle}>
            <p style={sectionTitle}>
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>factory</span>
              Datos de Fábrica
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Razón Social Fábrica</label>
                <input
                  style={inputStyle}
                  value={data.fabrica}
                  onChange={e => updateData('fabrica', e.target.value)}
                />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Dirección Fábrica</label>
                <input
                  style={inputStyle}
                  value={data.direccion}
                  onChange={e => updateData('direccion', e.target.value)}
                />
              </div>
              <div>
                <label style={labelStyle}>Contacto</label>
                <input
                  style={inputStyle}
                  value={data.contacto}
                  onChange={e => updateData('contacto', e.target.value)}
                  placeholder="Nombre del contacto (o dejar vacío)"
                />
              </div>
              <div>
                <label style={labelStyle}>Email</label>
                <input
                  style={inputStyle}
                  value={data.email}
                  onChange={e => updateData('email', e.target.value)}
                  placeholder="email@factory.com"
                />
              </div>
              <div>
                <label style={labelStyle}>Teléfono</label>
                <input
                  style={inputStyle}
                  value={data.telefono}
                  onChange={e => updateData('telefono', e.target.value)}
                  placeholder="+86 755 1234"
                />
              </div>
            </div>
          </div>

          {/* ── Modelos / SKUs ────────────────────────────────────────────────── */}
          <div style={cardStyle}>
            <p style={sectionTitle}>
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>inventory_2</span>
              Modelos ({data.skus.length} SKU{data.skus.length !== 1 ? 's' : ''})
            </p>
            {data.skus.length === 0 && (
              <p style={{ color: '#ef4444', fontSize: 13 }}>
                ⚠️ No se encontraron modelos en el datasheet. Revisá el archivo.
              </p>
            )}
            {data.skus.map((sku, idx) => (
              <div key={idx} style={{
                background: 'rgba(139,92,246,0.05)',
                border: '1px solid rgba(139,92,246,0.12)',
                borderRadius: 12,
                padding: '16px 20px',
                marginBottom: 12,
              }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: '#8b5cf6', marginBottom: 12, letterSpacing: '0.06em' }}>
                  SKU {idx + 1}: {sku.sku || '(sin SKU)'}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={labelStyle}>SKU</label>
                    <input
                      style={inputStyle}
                      value={sku.sku}
                      onChange={e => updateSku(idx, 'sku', e.target.value)}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Marca</label>
                    <input
                      style={inputStyle}
                      value={sku.marca}
                      onChange={e => updateSku(idx, 'marca', e.target.value)}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Modelo Fábrica / CB</label>
                    <input
                      style={inputStyle}
                      value={sku.modelo_fabrica}
                      onChange={e => updateSku(idx, 'modelo_fabrica', e.target.value)}
                      placeholder="Modelo certificado / CB"
                    />
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label style={labelStyle}>Modelos Bidcom (uno por línea o separados por coma)</label>
                    <textarea
                      style={{
                        ...inputStyle,
                        minHeight: 72,
                        padding: '10px 16px',
                        resize: 'vertical',
                        lineHeight: '1.6',
                      }}
                      value={sku.modelos.join('\n')}
                      onChange={e => updateSkuModelos(idx, e.target.value)}
                    />
                  </div>
                  <div>
                    <label style={labelStyle}>Tensión</label>
                    <input style={inputStyle} value={sku.tension} onChange={e => updateSku(idx, 'tension', e.target.value)} />
                  </div>
                  <div>
                    <label style={labelStyle}>Frecuencia</label>
                    <input style={inputStyle} value={sku.frecuencia} onChange={e => updateSku(idx, 'frecuencia', e.target.value)} />
                  </div>
                  <div>
                    <label style={labelStyle}>Potencia</label>
                    <input style={inputStyle} value={sku.potencia} onChange={e => updateSku(idx, 'potencia', e.target.value)} />
                  </div>
                  <div>
                    <label style={labelStyle}>Corriente</label>
                    <input style={inputStyle} value={sku.corriente} onChange={e => updateSku(idx, 'corriente', e.target.value)} />
                  </div>
                  <div>
                    <label style={labelStyle}>Aislación</label>
                    <input style={inputStyle} value={sku.aislacion} onChange={e => updateSku(idx, 'aislacion', e.target.value)} />
                  </div>
                  <div>
                    <label style={labelStyle}>Specs / Info técnica</label>
                    <input style={inputStyle} value={sku.specs} onChange={e => updateSku(idx, 'specs', e.target.value)} />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* ── QR SVG ───────────────────────────────────────────────────────── */}
          {(oec === 'lenor' || oec === 'qetkra') && (
            <div style={cardStyle}>
              <p style={sectionTitle}>
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>qr_code_2</span>
                Archivo QR (SVG) — Opcional
              </p>
              <div
                onClick={() => svgInputRef.current?.click()}
                style={{
                  border: `2px dashed ${svgFile ? 'rgba(139,92,246,0.4)' : 'rgba(255,255,255,0.1)'}`,
                  borderRadius: 12, padding: '28px 24px', cursor: 'pointer',
                  textAlign: 'center',
                  background: svgFile ? 'rgba(139,92,246,0.04)' : 'transparent',
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 36, color: svgFile ? '#8b5cf6' : '#343440' }}>
                  {svgFile ? 'check_circle' : 'qr_code'}
                </span>
                <p style={{ color: svgFile ? '#d0bcff' : '#64748b', marginTop: 8, fontSize: 13 }}>
                  {svgFile ? svgFile.name : 'Hacé clic para seleccionar el archivo .svg del QR de conformidad'}
                </p>
              </div>
              <input
                ref={svgInputRef}
                type="file"
                accept=".svg"
                style={{ display: 'none' }}
                onChange={e => { if (e.target.files?.[0]) setSvgFile(e.target.files[0]) }}
              />
              {svgFile && (
                <button
                  onClick={() => setSvgFile(null)}
                  style={{
                    marginTop: 8, background: 'none', border: 'none',
                    color: '#64748b', fontSize: 12, cursor: 'pointer', padding: 0,
                  }}
                >
                  × Quitar SVG
                </button>
              )}
            </div>
          )}

          {/* Botones de navegación */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
            <button
              onClick={() => setStep(1)}
              style={{
                padding: '12px 24px', background: 'transparent',
                border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10,
                color: '#64748b', fontSize: 14, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 8,
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>arrow_back</span>
              Volver
            </button>
            <button
              onClick={handleGenerate}
              disabled={generating}
              style={{
                padding: '14px 32px',
                background: generating ? 'rgba(139,92,246,0.3)' : 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
                border: 'none', borderRadius: 10,
                cursor: generating ? 'not-allowed' : 'pointer',
                color: '#fff', fontSize: 15, fontWeight: 700,
                display: 'flex', alignItems: 'center', gap: 10,
                boxShadow: generating ? 'none' : '0 4px 24px rgba(139,92,246,0.35)',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                {generating ? 'sync' : 'auto_awesome'}
              </span>
              {generating ? 'Generando…' : `Generar Solicitud ${oec.toUpperCase()}`}
            </button>
          </div>
            </>
          )}

          {/* Si se selecciona juguetes o ftalatos (Próximamente) */}
          {(oec === 'juguetes' || oec === 'ftalatos') && (
            <div style={{ ...cardStyle, textAlign: 'center', padding: '48px 32px' }}>
              <span className="material-symbols-outlined" style={{ fontSize: 64, color: '#a78bfa', marginBottom: 16 }}>
                {oec === 'juguetes' ? 'smart_toy' : 'science'}
              </span>
              <h3 style={{ fontSize: 20, color: '#f1eeff', fontWeight: 700, marginBottom: 8 }}>
                {oec === 'juguetes' ? '🧸 Certificación de Juguetes (Lenor)' : '🧪 Certificación de Ftalatos (Lenor)'}
              </h3>
              <p style={{ color: '#64748b', fontSize: 14, maxWidth: 480, margin: '0 auto', lineHeight: 1.6 }}>
                Este tipo de solicitud se encuentra en planificación para el siguiente desarrollo. 
                Aquí podrás procesar automáticamente datasheets de juguetes o ensayos de ftalatos y generar las notas de solicitud y anexos en formato Lenor.
              </p>
              <div style={{ marginTop: 24, display: 'flex', justifyContent: 'center', gap: 12 }}>
                <button
                  onClick={() => setStep(1)}
                  style={{
                    padding: '10px 18px', borderRadius: 8,
                    border: '1px solid rgba(255,255,255,0.08)',
                    background: 'rgba(255,255,255,0.03)',
                    color: '#64748b', fontSize: 13, fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Volver al Inicio
                </button>
                <button
                  onClick={() => setOec('lenor')}
                  style={{
                    padding: '10px 18px', borderRadius: 8,
                    border: 'none',
                    background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
                    color: '#fff', fontSize: 13, fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Volver a Eléctrica
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* ══ PASO 3: RESULTADO ═════════════════════════════════════════════════ */}
      {step === 3 && (
        <div style={cardStyle}>
          {/* Éxito header */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 16,
            padding: '20px 24px', marginBottom: 24,
            background: 'rgba(74,225,118,0.06)',
            border: '1px solid rgba(74,225,118,0.15)',
            borderRadius: 12,
          }}>
            <div style={{
              width: 48, height: 48, borderRadius: '50%',
              background: 'rgba(74,225,118,0.12)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: 28, color: '#4ae176' }}>check_circle</span>
            </div>
            <div>
              <p style={{ color: '#4ae176', fontWeight: 700, fontSize: 16 }}>¡Solicitud generada con éxito!</p>
              <p style={{ color: '#64748b', fontSize: 13, marginTop: 2 }}>
                Los archivos fueron guardados en: <code style={{ color: '#a78bfa', background: 'rgba(139,92,246,0.1)', padding: '2px 6px', borderRadius: 4 }}>{resultDir}</code>
              </p>
            </div>
          </div>

          {/* Info del certificado */}
          {data && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 24 }}>
              {[
                { label: 'Certificado', value: data.certificado },
                { label: 'Certificadora', value: oec.toUpperCase() },
                { label: 'SKUs', value: `${data.skus.length} SKU(s)` },
              ].map(item => (
                <div key={item.label} style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: 10, padding: '14px 18px',
                }}>
                  <p style={{ fontSize: 11, color: '#64748b', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase' }}>{item.label}</p>
                  <p style={{ fontSize: 16, color: '#f1eeff', fontWeight: 700, marginTop: 4 }}>{item.value}</p>
                </div>
              ))}
            </div>
          )}

          {/* Botones de acción */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button
              onClick={handleDownload}
              style={{
                padding: '14px 28px',
                background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
                border: 'none', borderRadius: 10, cursor: 'pointer',
                color: '#fff', fontSize: 14, fontWeight: 700,
                display: 'flex', alignItems: 'center', gap: 10,
                boxShadow: '0 4px 24px rgba(139,92,246,0.35)',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>download</span>
              Descargar ZIP
            </button>
            <button
              onClick={() => { setStep(1); setData(null); setDsFile(null); setSvgFile(null); setZipBlob(null) }}
              style={{
                padding: '14px 24px', background: 'transparent',
                border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10,
                color: '#94a3b8', fontSize: 14, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 8,
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>restart_alt</span>
              Nueva Solicitud
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
