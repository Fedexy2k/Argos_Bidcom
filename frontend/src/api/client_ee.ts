const BASE = '/api';

export interface EEField {
  key: string;
  label: string;
  type: 'select' | 'number' | 'text';
  unit?: string;
  options?: string[];
  optional?: boolean;
  default?: string;
}

export interface EEFamily {
  id: string;
  label: string;
  norma_base: string;
  fields: EEField[];
}

export interface EEParentConfig {
  families: EEFamily[];
}

export interface EEGenerateParams {
  family_id: string;
  bidcom_num: string;
  marca: string;
  modelo: string;
  producto_desc: string;
  base_specs: Record<string, string>;
  ee_fields: Record<string, any>;
  normas?: string;
  cert_number?: string;
  oec_nombre?: string;
  oec_contacto?: string; // Datos de contacto del laboratorio (web / email)
  fecha_emision?: string;
  fecha_proxima_vigilancia?: string;
  fecha_emision_djc?: string;
  label_images_base64?: string[]; // array de PNGs base64, uno por modelo (hasta 6)
}

export interface EEGenerateResult {
  djc_id: string;
  filename: string;
  pdf_b64: string;
  docx_b64: string;
}

export interface EEConfirmParams {
  filename: string;
  bidcom_num: string;
  pdf_b64: string;
  docx_b64: string;
}

// ── GET Families ──────────────────────────────────────────────────────────────

export async function getEEFamilies(): Promise<EEParentConfig> {
  const r = await fetch(`${BASE}/ee/families`);
  if (!r.ok) throw new Error('Error cargando familias de Eficiencia Energética');
  return r.json();
}

// ── POST Generate ─────────────────────────────────────────────────────────────

export async function generateEEDJC(params: EEGenerateParams): Promise<EEGenerateResult> {
  const r = await fetch(`${BASE}/ee/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Error generando DJC-EE' }));
    const detailMsg = typeof err.detail === 'string'
      ? err.detail
      : Array.isArray(err.detail)
        ? err.detail.map((d: any) => `${d.loc?.join('.') || 'campo'}: ${d.msg}`).join(', ')
        : JSON.stringify(err.detail);
    throw new Error(detailMsg || 'Error en la generación');
  }
  return r.json();
}

// ── POST Confirm ──────────────────────────────────────────────────────────────

export async function confirmEEDJC(params: EEConfirmParams): Promise<string[]> {
  const r = await fetch(`${BASE}/ee/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Error al confirmar DJC-EE' }));
    throw new Error(err.detail || 'Error al guardar');
  }
  const d = await r.json();
  return d.saved as string[];
}

// ── POST Auto-Extract File ───────────────────────────────────────────────────

export async function autoExtractEEFile(file: File): Promise<any> {
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch(`${BASE}/ee/auto-extract-file`, {
    method: 'POST',
    body: fd,
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: 'Error al autocompletar con IA' }));
    throw new Error(err.detail || 'Error al procesar el archivo');
  }
  return r.json();
}

