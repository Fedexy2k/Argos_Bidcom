// API client — all calls to the FastAPI backend (http://127.0.0.1:8742 via Vite proxy)

const BASE = '/api'

export interface CertExtractResult {
  cert_number: string
  oec_key: string
  normas: string
  fecha_emision: string
  fecha_vencimiento: string
  fabricante: string
  direccion: string
  marca: string
  modelos: string
  producto_desc: string
  specs: string
  reglamento: string
  djc_id?: string
}

export interface GenerateResult {
  version: string
  society: string | null
  label: string
  pdf_b64: string
}

export interface Config {
  empresa: Record<string, string>
  sociedades_extension: Record<string, { nombre: string; cuit: string; domicilio: string; codigo: string }>
  oec_options: Record<string, { nombre: string; contacto: string }>
  reglamento_options: string[]
  esquema_options: string[]
  enlace_djc_base: string
  [key: string]: unknown
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<string | null> {
  try {
    const r = await fetch(`${BASE}/health`)
    const d = await r.json()
    return d.status === 'ok' ? d.version : null
  } catch {
    return null
  }
}

// ── Config ────────────────────────────────────────────────────────────────────

export async function getConfig(): Promise<Config> {
  const r = await fetch(`${BASE}/config`)
  if (!r.ok) throw new Error('Error cargando configuración')
  return r.json()
}

// ── Extract ───────────────────────────────────────────────────────────────────

export async function extractCert(file: File): Promise<CertExtractResult> {
  const form = new FormData()
  form.append('file', file)
  const r = await fetch(`${BASE}/djc/extract`, { method: 'POST', body: form })
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Error extrayendo datos' }))
    throw new Error(err.detail || 'Error en la extracción')
  }
  return r.json()
}

// ── Generate ──────────────────────────────────────────────────────────────────

export interface EmpresaOverride {
  razon_social: string
  cuit: string
  marca_registrada: string
  domicilio_legal: string
  domicilio_deposito: string
  telefono: string
  email: string
}

export interface GenerateParams {
  versiones: string[]       // ['normal'] | ['codificada'] | ['normal','codificada']
  modo: string              // 'comun' | 'extension' | 'extension_terceros'
  sociedades: string[]
  djc_id: string
  enlace_djc: string
  cert_number: string
  oec_key: string
  normas: string
  fecha_emision: string
  fecha_vencimiento: string
  fecha_vigilancia: string  // '———' si cert nuevo, fecha real si hubo vigilancia previa
  fabricante: string
  direccion: string
  marca: string
  modelos: string
  producto_desc: string
  specs: string
  bidcom_num: string
  reglamento: string
  esquema: string
  output_dir: string
  save_to_disk: boolean
  empresa_override?: EmpresaOverride  // solo en modo extension_terceros
}

export async function generateDJC(
  params: GenerateParams,
  certFile: File,
  notaFile?: File,
): Promise<GenerateResult[]> {
  const form = new FormData()
  form.append('request_json', JSON.stringify(params))
  form.append('cert_file', certFile)
  if (notaFile) form.append('nota_file', notaFile)

  const r = await fetch(`${BASE}/djc/generate`, { method: 'POST', body: form })
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Error generando DJC' }))
    throw new Error(err.detail || 'Error en la generación')
  }
  const d = await r.json()
  return d.results as GenerateResult[]
}

// ── Helpers ───────────────────────────────────────────────────────────────────

export interface ConfirmItem {
  filename: string
  bidcom_num: string
  society_key: string
  pdf_b64: string
}

export async function confirmDJC(items: ConfirmItem[]): Promise<string[]> {
  const r = await fetch(`${BASE}/djc/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items }),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Error guardando' }))
    throw new Error(err.detail || 'Error al confirmar')
  }
  const d = await r.json()
  return d.saved as string[]
}

export function downloadPdf(b64: string, filename: string) {
  const bytes = atob(b64)
  const arr = new Uint8Array(bytes.length)
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
  const blob = new Blob([arr], { type: 'application/pdf' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function makeBlobUrl(b64: string): string {
  const bytes = atob(b64)
  const arr = new Uint8Array(bytes.length)
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
  const blob = new Blob([arr], { type: 'application/pdf' })
  return URL.createObjectURL(blob)
}
