// client_solicitud.ts — API client para el módulo de Generador de Solicitudes

const BASE = '/api/solicitud'

// ── Tipos ────────────────────────────────────────────────────────────────────

export interface SkuBlock {
  sku: string
  marca: string
  modelos: string[]
  modelo_fabrica: string
  tension: string
  frecuencia: string
  corriente: string
  potencia: string
  aislacion: string
  specs: string
}

export interface DatasheetParseResult {
  oec_detected: 'lenor' | 'qetkra'
  certificado: string
  producto: string
  motivo: string
  oec: string
  normas: string
  laboratorio: string
  reglamento: string
  fabrica: string
  direccion: string
  contacto: string
  email: string
  telefono: string
  skus: SkuBlock[]
}

export interface GenerateRequest {
  data: DatasheetParseResult
  oec: 'lenor' | 'qetkra' | 'juguetes' | 'ftalatos'
  esquema: string
}

// ── Funciones ─────────────────────────────────────────────────────────────────

/**
 * Sube el Excel de ingeniería y obtiene los datos parseados del datasheet.
 */
export async function parseDatasheet(file: File): Promise<DatasheetParseResult> {
  const form = new FormData()
  form.append('file', file)

  const r = await fetch(`${BASE}/parse`, { method: 'POST', body: form })
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Error al parsear el datasheet' }))
    throw new Error(err.detail || 'Error en el parseo del datasheet')
  }
  return r.json()
}

/**
 * Genera los archivos de solicitud y descarga el ZIP resultante.
 * También guarda los archivos en la carpeta local Solicitudes/[Nro]/.
 */
export async function generateSolicitud(
  req: GenerateRequest,
  svgFile?: File,
): Promise<Blob> {
  const form = new FormData()
  form.append('request_json', JSON.stringify(req))
  if (svgFile) {
    form.append('svg_file', svgFile)
  }

  const r = await fetch(`${BASE}/generate`, { method: 'POST', body: form })
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Error al generar la solicitud' }))
    throw new Error(err.detail || 'Error en la generación de solicitud')
  }
  return r.blob()
}

/**
 * Dispara la descarga de un Blob como archivo ZIP.
 */
export function downloadZip(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
