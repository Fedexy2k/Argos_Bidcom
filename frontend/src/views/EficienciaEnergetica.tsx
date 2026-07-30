import { useState, useEffect, useRef } from 'react';
import * as htmlToImage from 'html-to-image';
import { getEEFamilies, generateEEDJC, confirmEEDJC, autoExtractEEFile, type EEFamily, type EEGenerateResult } from '../api/client_ee';
import EtiquetaEE, { type EtiquetaData } from '../components/EtiquetaEE';

interface Props {
  onLog: (level: string, msg: string) => void;
}

export default function EficienciaEnergetica({ onLog }: Props) {
  // ── PESTAÑAS PRINCIPALES ──
  const [activeSubTab, setActiveSubTab] = useState<'generador' | 'etiquetas'>('generador');

  // ── ESTADOS DEL FORMULARIO ──
  const [families, setFamilies] = useState<EEFamily[]>([]);
  const [selectedFamilyId, setSelectedFamilyId] = useState<string>('');

  const [loadingAiReport, setLoadingAiReport] = useState(false);
  const eeReportInputRef = useRef<HTMLInputElement>(null);

  const handleEeReportUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      onLog('warning', 'El informe debe ser un archivo PDF');
      return;
    }
    setLoadingAiReport(true);
    onLog('info', `[EE/AI] 📄 Archivo cargado: '${file.name}' (${(file.size / 1024).toFixed(1)} KB)`);
    onLog('info', `[EE/AI] 🤖 Enviando informe a OpenAI (gpt-4o-mini) para análisis estructural y extracción...`);
    try {
      const res = await autoExtractEEFile(file);
      if (res) {
        // Paso 1: Marca, Modelo y Descripción
        if (res.marca) setMarca(res.marca);
        if (res.modelos) setModelo(res.modelos);
        if (res.producto_desc) setProductoDesc(res.producto_desc);


        // Paso 2: Familia, Specs Base y Métricas EE
        if (res.family_id) setSelectedFamilyId(res.family_id);
        if (res.base_specs) {
          setBaseSpecs(prev => ({
            ...prev,
            ...res.base_specs
          }));
        }
        if (res.ee_fields) {
          setEeFields(prev => ({
            ...prev,
            ...(res.clase_ee ? { clase_ee: res.clase_ee } : {}),
            ...res.ee_fields
          }));
        }

        // Paso 3: Informe, Laboratorio, Contacto y Fechas (+4 años auto)
        if (res.cert_number) setCertNumber(res.cert_number);
        if (res.oec_nombre) setOecNombre(res.oec_nombre);
        if (res.oec_contacto) setOecContacto(res.oec_contacto);
        if (res.fecha_emision) setFechaEmision(res.fecha_emision);
        if (res.fecha_proxima_vigilancia) setFechaVencimiento(res.fecha_proxima_vigilancia);

        // Logs detallados campo a campo para trazabilidad completa
        onLog('info', `[EE/AI] 🏷️ Marca: '${res.marca || 'N/A'}' | Modelo/s: '${res.modelos || 'N/A'}'`);
        onLog('info', `[EE/AI] 📦 Familia identificada: '${res.family_id || 'N/A'}' | Descripción: '${res.producto_desc || 'N/A'}'`);
        onLog('info', `[EE/AI] ⚡ Clase Eficiencia Energética: '${res.clase_ee || 'N/A'}' (Res. 438/2024 escala A-G)`);


        if (res.ee_fields) {
          const metricsStr = Object.entries(res.ee_fields)
            .filter(([_, v]) => v !== null && v !== undefined)
            .map(([k, v]) => `${k}: ${v}`)
            .join(' | ');
          onLog('info', `[EE/AI] 📊 Métricas EE Extraídas: [ ${metricsStr} ]`);
        }

        if (res.base_specs) {
          onLog('info', `[EE/AI] 🔌 Specs Eléctricas Base: Tensión '${res.base_specs.tension || 'N/A'}' | Frecuencia '${res.base_specs.frecuencia || 'N/A'}' | Potencia '${res.base_specs.potencia || 'N/A'}'`);
        }

        onLog('info', `[EE/AI] 🏭 Ensayo & Laboratorio: N° Informe '${res.cert_number || 'N/A'}' | OEC '${res.oec_nombre || 'N/A'}' | Contacto '${res.oec_contacto || 'N/A'}'`);
        onLog('info', `[EE/AI] 📅 Vigencia: Emisión '${res.fecha_emision || 'N/A'}' → Próx. Vigilancia '${res.fecha_proxima_vigilancia || 'N/A'}' (+4 años auto)`);
        onLog('info', `[EE/AI] ✓ Autocompletado del Paso 1, Paso 2 y Paso 3 finalizado exitosamente.`);
      }
    } catch (e: any) {
      onLog('error', `[EE/AI] Error analizando informe con IA: ${e.message || e}`);
    } finally {
      setLoadingAiReport(false);
    }
  };





  
  const [bidcom, setBidcom] = useState('');
  const [marca, setMarca] = useState('');
  const [modelo, setModelo] = useState('');
  const [origen, setOrigen] = useState('China');
  const [productoDesc, setProductoDesc] = useState('');
  
  // Specs eléctricas base (incluyendo adicionales opcionales)
  const [baseSpecs, setBaseSpecs] = useState({
    tension: '220-240 V~',
    frecuencia: '50 Hz',
    potencia: '',
    clase: 'Clase I',
    ip: 'IPX1',
    adicionales: ''
  });

  // Campos específicos de la familia
  const [eeFields, setEeFields] = useState<Record<string, any>>({});

  // Informe de ensayo
  const [certNumber, setCertNumber] = useState('');
  const [oecNombre, setOecNombre] = useState('TÜV Rheinland');
  const [oecContacto, setOecContacto] = useState('');
  const [fechaEmision, setFechaEmision] = useState('');
  const [fechaVencimiento, setFechaVencimiento] = useState('');
  const [fechaEmisionDjc, setFechaEmisionDjc] = useState('');

  // Imagen QR
  const [qrImageUrl, setQrImageUrl] = useState<string>('');
  const qrInputRef = useRef<HTMLInputElement>(null);

  // ── PASOS Y NAVEGACIÓN ──
  const [currentStep, setCurrentStep] = useState(1);
  const [generating, setGenerating] = useState(false);
  const [previewResult, setPreviewResult] = useState<EEGenerateResult | null>(null);
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string>('');
  const [confirming, setConfirming] = useState(false);
  const [savedPaths, setSavedPaths] = useState<string[] | null>(null);

  // ── MULTIMODELO ──
  // Parsear el campo modelo en un array limpio de hasta 6 modelos
  const modelList = modelo
    .split(/[,;\n]+/)
    .map(m => m.trim())
    .filter(m => m.length > 0)
    .slice(0, 6);
  const [activeModelIndex, setActiveModelIndex] = useState(0);

  // ── ESTILOS PREMIUM (REPLICANDO GENERADOR DJC) ──
  const inputStyle = ({ pl, multiline }: { pl?: number; multiline?: boolean } = {}) => ({
    width: '100%',
    minHeight: multiline ? undefined : 46,
    background: '#161522',
    border: '1px solid rgba(139,92,246,0.18)',
    borderRadius: 10,
    padding: multiline ? '12px 16px' : '0 16px',
    paddingLeft: pl ? pl : 16,
    color: '#f1eeff',
    fontSize: 14,
    boxSizing: 'border-box' as const,
    resize: multiline ? 'vertical' as const : undefined,
    lineHeight: multiline ? '1.6' : undefined,
    outline: 'none',
    appearance: 'none' as const,
    WebkitAppearance: 'none' as const,
    MozAppearance: 'none' as const,
  });

  const labelStyle = {
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: '0.08em',
    color: '#958ea0',
    textTransform: 'uppercase' as const,
    marginBottom: 6,
    display: 'block'
  };

  // ── CARGAR CONFIGURACIÓN ──
  useEffect(() => {
    getEEFamilies()
      .then(d => {
        setFamilies(d.families);
        if (d.families.length > 0) {
          // Inicializar con la primera familia
          const firstFam = d.families[0];
          setSelectedFamilyId(firstFam.id);
          const initial: Record<string, any> = {};
          firstFam.fields.forEach(field => {
            initial[field.key] = field.default || (field.type === 'select' ? field.options?.[0] : '');
          });
          setProductoDesc(firstFam.label);
          setEeFields(initial);
        }
      })
      .catch(e => {
        onLog('error', `Error cargando familias: ${e.message}`);
      });

    // Inicializar fecha de hoy en formato DD/MM/YYYY para la DJC
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const mon = String(now.getMonth() + 1).padStart(2, '0');
    setFechaEmisionDjc(`${day}/${mon}/${now.getFullYear()}`);
  }, []);

  // Revocar el blob URL en el desmontaje para evitar pérdidas de memoria
  useEffect(() => {
    return () => {
      if (previewBlobUrl) {
        URL.revokeObjectURL(previewBlobUrl);
      }
    };
  }, [previewBlobUrl]);

  // Inicializar campos de la familia elegida
  const handleFamilyChange = (famId: string) => {
    setSelectedFamilyId(famId);
    const fam = families.find(f => f.id === famId);
    if (fam) {
      const initial: Record<string, any> = {};
      fam.fields.forEach(field => {
        initial[field.key] = field.default || (field.type === 'select' ? field.options?.[0] : '');
      });
      // Predeterminar descripción de producto según la familia
      setProductoDesc(fam.label);
      setEeFields(initial);
    }
  };

  // Escuchar fecha de emisión para autocalcular el vencimiento (+4 años)
  useEffect(() => {
    if (fechaEmision && /^\d{2}\/\d{2}\/\d{4}$/.test(fechaEmision)) {
      try {
        const [d, m, y] = fechaEmision.split('/');
        const year = parseInt(y) + 4;
        setFechaVencimiento(`${d}/${m}/${year}`);
      } catch (e) {
        // Ignorar errores de formateo
      }
    }
  }, [fechaEmision]);

  // Carga de QR
  const handleQrUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (ev) => {
      setQrImageUrl(ev.target?.result as string);
      onLog('info', 'QR cargado exitosamente en la etiqueta');
    };
    reader.readAsDataURL(file);
  };

  // Generar URL del Blob para el visualizador PDF
  const makeBlobUrl = (b64: string): string => {
    const bytes = atob(b64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) {
      arr[i] = bytes.charCodeAt(i);
    }
    const blob = new Blob([arr], { type: 'application/pdf' });
    return URL.createObjectURL(blob);
  };

  // Mapear campos de la familia seleccionada a campos de etiqueta
  // modelOverride permite generar datos para un modelo específico de la lista
  const getEtiquetaData = (modelOverride?: string): EtiquetaData => {
    const fam = families.find(f => f.id === selectedFamilyId);
    return {
      marca,
      modelo: modelOverride ?? (modelList[0] || modelo),
      origen,
      eficiencia: eeFields.clase_ee || 'A',
      qrImageUrl,
      referenciaIram: fam?.norma_base || '',
      resolucion: 'Res. 438/2024',
      descripcion: productoDesc,
      ...eeFields
    };
  };

  // Renderizar la etiqueta en tiempo real
  const selectedFamily = families.find(f => f.id === selectedFamilyId);

  // ── EXPORTAR ETIQUETA PNG DIRECTA ──
  const handleExportEtiquetaPng = async () => {
    try {
      const el = document.getElementById('label-export');
      if (!el) {
        alert('Elemento de etiqueta no encontrado en el DOM.');
        return;
      }
      onLog('info', 'Generando imagen PNG de la etiqueta...');
      const dataUrl = await htmlToImage.toPng(el, {
        quality: 1.0,
        pixelRatio: 4,
        style: {
          transform: 'scale(1)',
        }
      });

      const a = document.createElement('a');
      a.href = dataUrl;
      a.download = `etiqueta-${selectedFamilyId}-${modelo || 'export'}.png`;
      a.click();
      onLog('info', '✓ Imagen de etiqueta descargada exitosamente.');
    } catch (err: any) {
      onLog('error', `Error al exportar etiqueta: ${err.message}`);
    }
  };

  // ── GENERAR DJC PREVIEW (PASO 5) ──
  const handleGenerate = async () => {
    if (!bidcom.trim()) {
      onLog('warning', 'Ingresá el Nro de Bidcom.');
      return;
    }
    setGenerating(true);
    const effectiveModels = modelList.length > 0 ? modelList : [modelo];
    onLog('info', `Iniciando generación de DJC-EE para ${effectiveModels.length} modelo(s)...`);
    
    try {
      // 1. Capturar una imagen PNG por cada modelo (hasta 6)
      const labelImages: string[] = [];
      for (let i = 0; i < effectiveModels.length; i++) {
        const el = document.getElementById(`label-export-${i}`);
        if (!el) {
          onLog('warning', `No se encontró la etiqueta del modelo ${i + 1}, omitiendo.`);
          continue;
        }
        const png = await htmlToImage.toPng(el, { quality: 0.9, pixelRatio: 3 });
        labelImages.push(png);
        onLog('info', `  ✓ Etiqueta ${i + 1}/${effectiveModels.length} capturada (${effectiveModels[i]})`);
      }

      if (labelImages.length === 0) throw new Error('No se pudieron capturar las imágenes de las etiquetas.');

      // 2. Armar parámetros — enviar array de imágenes
      const params = {
        family_id: selectedFamilyId,
        bidcom_num: bidcom.trim().match(/^\d+$/) ? `C${bidcom.trim()}` : bidcom.trim(),
        marca,
        modelo,
        producto_desc: productoDesc,
        base_specs: baseSpecs,
        ee_fields: eeFields,
        normas: selectedFamily?.norma_base || '',
        cert_number: certNumber,
        oec_nombre: oecNombre,
        oec_contacto: oecContacto,
        fecha_emision: fechaEmision,
        fecha_proxima_vigilancia: fechaVencimiento,
        fecha_emision_djc: fechaEmisionDjc,
        label_images_base64: labelImages,  // array multimodelo
      };

      // 3. POST api
      const result = await generateEEDJC(params);
      setPreviewResult(result);

      if (previewBlobUrl) URL.revokeObjectURL(previewBlobUrl);
      const newBlobUrl = makeBlobUrl(result.pdf_b64);
      setPreviewBlobUrl(newBlobUrl);

      setCurrentStep(5);
      onLog('info', `✓ Previsualización de DJC-EE lista — ${labelImages.length} etiqueta(s) insertada(s).`);
    } catch (e: any) {
      onLog('error', `Error generando DJC-EE: ${e.message}`);
    } finally {
      setGenerating(false);
    }
  };

  // ── CONFIRMAR PREVIEW ──
  const handleConfirm = async () => {
    if (!previewResult) return;
    setConfirming(true);
    onLog('info', 'Guardando DJC de Eficiencia Energética en el disco local...');
    try {
      const res = await confirmEEDJC({
        filename: previewResult.filename,
        bidcom_num: bidcom,
        pdf_b64: previewResult.pdf_b64,
        docx_b64: previewResult.docx_b64
      });
      setSavedPaths(res);
      onLog('info', '✓ ¡DJC-EE Guardada con éxito en tu carpeta de Documentos!');
      
      // Descargar PDF final automáticamente
      const bytes = atob(previewResult.pdf_b64);
      const arr = new Uint8Array(bytes.length);
      for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
      const blob = new Blob([arr], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${previewResult.filename}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      
    } catch (e: any) {
      onLog('error', `Error al confirmar: ${e.message}`);
    } finally {
      setConfirming(false);
    }
  };

  const handleDiscard = () => {
    setPreviewResult(null);
    if (previewBlobUrl) {
      URL.revokeObjectURL(previewBlobUrl);
      setPreviewBlobUrl('');
    }
    setSavedPaths(null);
    setCurrentStep(4);
    onLog('info', 'Generación descartada. Podés corregir datos y reintentar.');
  };

  const renderStepIndicator = () => {
    const steps = [
      { num: 1, label: 'Identificación' },
      { num: 2, label: 'Características' },
      { num: 3, label: 'Informe' },
      { num: 4, label: 'Etiqueta EE' },
      { num: 5, label: 'Vista Previa' }
    ];
    return (
      <div style={{ marginBottom: 28 }}>
        <div className="flex justify-between items-center px-4 relative" style={{ height: 42 }}>
          <div className="absolute left-6 right-6 top-1/2 h-0.5 -translate-y-1/2 z-0" style={{ backgroundColor: 'rgba(139,92,246,0.12)' }} />
          {steps.map(s => {
            const active = currentStep === s.num;
            const passed = currentStep > s.num;
            return (
              <div key={s.num} className="z-10">
                <button
                  onClick={() => previewResult ? setCurrentStep(s.num) : s.num < currentStep && setCurrentStep(s.num)}
                  disabled={!previewResult && s.num > currentStep}
                  className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300 border"
                  style={{
                    backgroundColor: active ? '#8b5cf6' : passed ? '#10b981' : '#161522',
                    borderColor: active ? '#8b5cf6' : passed ? '#10b981' : 'rgba(139,92,246,0.18)',
                    color: active || passed ? '#fff' : '#64748b',
                    boxShadow: active ? '0 0 15px rgba(139,92,246,0.4)' : undefined,
                    cursor: (previewResult || s.num < currentStep) ? 'pointer' : 'default',
                  }}
                >
                  {passed ? '✓' : s.num}
                </button>
              </div>
            );
          })}
        </div>
        <div style={{ textAlign: 'center', marginTop: 12 }}>
          <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', color: '#8b5cf6', textTransform: 'uppercase' }}>
            Paso {currentStep} de 5: {steps[currentStep - 1].label}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="p-8 flex-1 flex flex-col h-full overflow-y-auto">
      
      {/* HEADER DE PESTAÑA */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-black text-white flex items-center gap-3">
            <span className="material-symbols-outlined text-purple-500 text-3xl">electric_bolt</span>
            EFICIENCIA ENERGÉTICA
          </h2>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest font-bold">
            Resolución SIyC N° 438/2024 — Etiquetado y Declaración Jurada
          </p>
        </div>

        {/* SUB-TABS INTERNAS (MÓDULO REDISEÑADO PREMIUM) */}
        <div style={{
          display: 'flex',
          background: '#161522',
          border: '1px solid rgba(139,92,246,0.18)',
          borderRadius: 12,
          padding: 4,
          gap: 6
        }}>
          <button
            onClick={() => setActiveSubTab('generador')}
            style={{
              height: 38,
              padding: '0 20px',
              fontSize: 12,
              fontWeight: 700,
              borderRadius: 8,
              textTransform: 'uppercase',
              transition: 'all 0.15s',
              cursor: 'pointer',
              border: 'none',
              background: activeSubTab === 'generador' ? '#8b5cf6' : 'transparent',
              color: activeSubTab === 'generador' ? '#fff' : '#958ea0',
              boxShadow: activeSubTab === 'generador' ? '0 4px 12px rgba(139,92,246,0.25)' : undefined
            }}
          >
            📋 Generador DJC-EE
          </button>
          <button
            onClick={() => setActiveSubTab('etiquetas')}
            style={{
              height: 38,
              padding: '0 20px',
              fontSize: 12,
              fontWeight: 700,
              borderRadius: 8,
              textTransform: 'uppercase',
              transition: 'all 0.15s',
              cursor: 'pointer',
              border: 'none',
              background: activeSubTab === 'etiquetas' ? '#8b5cf6' : 'transparent',
              color: activeSubTab === 'etiquetas' ? '#fff' : '#958ea0',
              boxShadow: activeSubTab === 'etiquetas' ? '0 4px 12px rgba(139,92,246,0.25)' : undefined
            }}
          >
            🎨 Sandbox de etiquetas
          </button>
        </div>
      </div>

      {activeSubTab === 'etiquetas' ? (
        /* ─── VISTA: SANDBOX DE ETIQUETAS INDEPENDIENTE ─── */
        <div className="flex-1 flex gap-8">
          <div className="w-[480px] shrink-0 flex flex-col max-h-[calc(100vh-180px)]">
            <div style={{
              flex: 1,
              background: '#1f1e2a',
              borderRadius: 14,
              padding: 28,
              border: '1px solid rgba(255,255,255,0.04)',
              boxShadow: '0 4px 24px rgba(0,0,0,0.25)',
              display: 'flex',
              flexDirection: 'column',
              overflowY: 'auto'
            }}>
              <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 12, marginBottom: 20 }}>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                  Configurar Etiqueta
                </h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <label style={labelStyle}>Familia de Producto</label>
                  <div style={{ position: 'relative' }}>
                    <select
                      value={selectedFamilyId}
                      onChange={e => handleFamilyChange(e.target.value)}
                      style={inputStyle()}
                    >
                      {families.map(f => <option key={f.id} value={f.id}>{f.label}</option>)}
                    </select>
                    <span className="material-symbols-outlined" style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', fontSize: 18, color: '#64748b', pointerEvents: 'none' }}>expand_more</span>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Marca</label>
                    <input type="text" value={marca} onChange={e => setMarca(e.target.value)} style={inputStyle()} placeholder="Ej: GADNIC" />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Modelo</label>
                    <input type="text" value={modelo} onChange={e => setModelo(e.target.value)} style={inputStyle()} placeholder="Ej: W10" />
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <label style={labelStyle}>Origen</label>
                  <input type="text" value={origen} onChange={e => setOrigen(e.target.value)} style={inputStyle()} />
                </div>

                <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 16, marginTop: 8 }}>
                  <h4 style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#8b5cf6', textTransform: 'uppercase', marginBottom: 14 }}>
                    Métricas de la Familia
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {selectedFamily?.fields.map(field => (
                      <div key={field.key} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: 10, fontWeight: 700, color: '#958ea0', textTransform: 'uppercase' }}>
                          {field.label} {field.unit ? `(${field.unit})` : ''}
                        </label>
                        {field.type === 'select' ? (
                          <div style={{ position: 'relative' }}>
                            <select
                              value={eeFields[field.key] || ''}
                              onChange={e => setEeFields({ ...eeFields, [field.key]: e.target.value })}
                              style={inputStyle()}
                            >
                              {field.options?.map(o => <option key={o} value={o}>{o}</option>)}
                            </select>
                            <span className="material-symbols-outlined" style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', fontSize: 18, color: '#64748b', pointerEvents: 'none' }}>expand_more</span>
                          </div>
                        ) : (
                          <input
                            type={field.type === 'number' ? 'number' : 'text'}
                            value={eeFields[field.key] || ''}
                            onChange={e => setEeFields({ ...eeFields, [field.key]: e.target.value })}
                            style={inputStyle()}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 16, marginTop: 8 }}>
                  <label style={labelStyle}>Subir Imagen QR</label>
                  <input
                    ref={qrInputRef}
                    type="file"
                    accept="image/*"
                    onChange={e => { const f = e.target.files?.[0]; if (f) handleQrUpload(f); }}
                    className="hidden"
                  />
                  {qrImageUrl ? (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      padding: 12,
                      background: '#161522',
                      border: '1px solid rgba(139,92,246,0.18)',
                      borderRadius: 10
                    }}>
                      <img src={qrImageUrl} style={{ width: 48, height: 48, backgroundColor: '#fff', objectFit: 'contain', borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }} alt="QR" />
                      <div style={{ flex: 1 }}>
                        <p style={{ fontSize: 12, fontWeight: 700, color: '#10b981' }}>QR cargado ✓</p>
                        <button onClick={() => setQrImageUrl('')} style={{ fontSize: 10, color: '#f87171', fontWeight: 700, textTransform: 'uppercase', marginTop: 4, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>✕ Quitar</button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => qrInputRef.current?.click()}
                      style={{
                        width: '100%',
                        height: 52,
                        border: '2px dashed rgba(139,92,246,0.25)',
                        borderRadius: 10,
                        background: 'rgba(139,92,246,0.02)',
                        color: '#a78bfa',
                        fontSize: 12,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                        transition: 'all 0.15s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = '#8b5cf6';
                        e.currentTarget.style.background = 'rgba(139,92,246,0.05)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = 'rgba(139,92,246,0.25)';
                        e.currentTarget.style.background = 'rgba(139,92,246,0.02)';
                      }}
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: 18 }}>photo_camera</span>
                      <span>📷 Cargar imagen de QR</span>
                    </button>
                  )}
                </div>

                <button
                  onClick={handleExportEtiquetaPng}
                  style={{
                    width: '100%',
                    height: 52,
                    borderRadius: 10,
                    backgroundColor: '#8b5cf6',
                    color: '#fff',
                    fontWeight: 700,
                    fontSize: 12,
                    textTransform: 'uppercase',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                    boxShadow: '0 4px 14px rgba(139,92,246,0.3)',
                    marginTop: 12,
                    transition: 'all 0.15s'
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#7c3aed'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#8b5cf6'; }}
                >
                  💾 Exportar Etiqueta PNG
                </button>
              </div>
            </div>
          </div>

          <div className="flex-1 bg-slate-950 border border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center min-h-[500px]">
            <div className="mb-4 bg-slate-900 px-4 py-2 rounded-full border border-slate-800 flex items-center gap-2">
              <span className="material-symbols-outlined text-purple-400 text-sm">print</span>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Escala Real de Impresión (116 mm)</span>
            </div>
            <div className="shadow-2xl ring-1 ring-white/10 rounded-sm bg-white overflow-hidden">
              <EtiquetaEE familyId={selectedFamilyId} data={getEtiquetaData()} />
            </div>
          </div>
        </div>
      ) : (
        /* ─── VISTA: GENERADOR DJC-EE COMPLETO (PASOS) ─── */
        <div className="flex-1 flex gap-8">
          
          {/* COLUMNA IZQUIERDA: FORMULARIO */}
          <div className="w-[480px] shrink-0 flex flex-col max-h-[calc(100vh-180px)]">
            <div style={{
              flex: 1,
              background: '#1f1e2a',
              borderRadius: 14,
              padding: 28,
              border: '1px solid rgba(255,255,255,0.04)',
              boxShadow: '0 4px 24px rgba(0,0,0,0.25)',
              display: 'flex',
              flexDirection: 'column',
              overflowY: 'auto'
            }}>
              
              {renderStepIndicator()}

              {/* PASO 1: IDENTIFICACIÓN Y ORIGEN */}
              {currentStep === 1 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }} className="animate-fadeIn">
                  <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 12, marginBottom: 4 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                      Paso 1: Identificación
                    </h3>
                  </div>

                  {/* BLOQUE DE AUTOCOMPLETADO POR IA */}
                  <div style={{
                    padding: 14,
                    background: 'linear-gradient(135deg, rgba(139,92,246,0.1) 0%, rgba(59,130,246,0.05) 100%)',
                    borderRadius: 12,
                    border: '1px dashed rgba(139,92,246,0.3)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 10
                  }}>
                    <input
                      ref={eeReportInputRef}
                      type="file"
                      accept=".pdf"
                      style={{ display: 'none' }}
                      onChange={e => { const f = e.target.files?.[0]; if (f) handleEeReportUpload(f); }}
                    />
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 20, color: '#a78bfa' }}>auto_awesome</span>
                      <span style={{ fontSize: 12, fontWeight: 700, color: '#c4b5fd', textTransform: 'uppercase' }}>
                        Autocompletar con IA (Informe de Ensayo)
                      </span>
                    </div>
                    <p style={{ fontSize: 11, color: '#94a3b8', margin: 0, lineHeight: 1.4 }}>
                      Sube el PDF del Informe de Ensayo de EE (ej: TÜV Rheinland / IRAM) para extraer la familia, clase y métricas automáticamente.
                    </p>
                    <button
                      onClick={() => eeReportInputRef.current?.click()}
                      disabled={loadingAiReport}
                      style={{
                        width: '100%',
                        height: 42,
                        borderRadius: 8,
                        background: loadingAiReport ? '#4c1d95' : '#7c3aed',
                        color: '#ffffff',
                        fontSize: 11,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        border: 'none',
                        cursor: loadingAiReport ? 'wait' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                        boxShadow: '0 4px 12px rgba(124,58,237,0.25)',
                        transition: 'all 0.15s'
                      }}
                      onMouseEnter={(e) => { if (!loadingAiReport) e.currentTarget.style.background = '#6d28d9'; }}
                      onMouseLeave={(e) => { if (!loadingAiReport) e.currentTarget.style.background = '#7c3aed'; }}
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                        {loadingAiReport ? 'sync' : 'upload_file'}
                      </span>
                      <span>{loadingAiReport ? 'Analizando Informe de Ensayo con IA...' : '📄 Subir Informe de Ensayo (PDF)'}</span>
                    </button>
                  </div>

                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Número de Gestión Bidcom</label>
                    <div style={{ position: 'relative' }}>
                      <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#8b5cf6', fontWeight: 700, fontSize: 14 }}>C</span>
                      <input
                        type="text"
                        value={bidcom}
                        onChange={e => setBidcom(e.target.value.replace(/^C/i, ''))}
                        style={inputStyle({ pl: 28 })}
                        placeholder="877"
                      />
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Marca Comercial</label>
                    <input
                      type="text"
                      value={marca}
                      onChange={e => setMarca(e.target.value)}
                      style={inputStyle()}
                      placeholder="Ej: GADNIC"
                    />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Modelo</label>
                    <input
                      type="text"
                      value={modelo}
                      onChange={e => setModelo(e.target.value)}
                      style={inputStyle()}
                      placeholder="Ej: W10"
                    />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Origen del Producto</label>
                    <input
                      type="text"
                      value={origen}
                      onChange={e => setOrigen(e.target.value)}
                      style={inputStyle()}
                    />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Fabricante y Dirección (Codificados)</label>
                    <div style={{
                      minHeight: 46,
                      background: '#161522',
                      border: '1px solid rgba(139,92,246,0.08)',
                      borderRadius: 10,
                      padding: '12px 16px',
                      color: '#64748b',
                      fontSize: 13,
                      fontStyle: 'italic',
                      lineHeight: '1.4',
                      boxSizing: 'border-box'
                    }}>
                      Información Restringida - Res. SIyC 237/2024 (China)
                    </div>
                    <span style={{ fontSize: 10, color: '#475569', marginTop: 4 }}>La codificación obligatoria se aplica automáticamente en todas las DJC-EE.</span>
                  </div>
                </div>
              )}

              {/* PASO 2: FAMILIA & specs */}
              {currentStep === 2 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }} className="animate-fadeIn">
                  <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 12, marginBottom: 4 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                      Paso 2: Familia & Características
                    </h3>
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Familia de Producto</label>
                    <div style={{ position: 'relative' }}>
                      <select
                        value={selectedFamilyId}
                        onChange={e => handleFamilyChange(e.target.value)}
                        style={inputStyle()}
                      >
                        {families.map(f => <option key={f.id} value={f.id}>{f.label}</option>)}
                      </select>
                      <span className="material-symbols-outlined" style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', fontSize: 18, color: '#64748b', pointerEvents: 'none' }}>expand_more</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Identificación / Descripción de Producto</label>
                    <input
                      type="text"
                      value={productoDesc}
                      onChange={e => setProductoDesc(e.target.value)}
                      style={inputStyle()}
                    />
                  </div>

                  {/* Especificaciones Eléctricas Base con Características Adicionales */}
                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 16, marginTop: 8 }}>
                    <h4 style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#8b5cf6', textTransform: 'uppercase', marginBottom: 14 }}>
                      Especificaciones Eléctricas Base
                    </h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: 10, fontWeight: 700, color: '#958ea0', textTransform: 'uppercase' }}>Tensión</label>
                        <input type="text" value={baseSpecs.tension} onChange={e => setBaseSpecs({...baseSpecs, tension: e.target.value})} style={inputStyle()} />
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: 10, fontWeight: 700, color: '#958ea0', textTransform: 'uppercase' }}>Frecuencia</label>
                        <input type="text" value={baseSpecs.frecuencia} onChange={e => setBaseSpecs({...baseSpecs, frecuencia: e.target.value})} style={inputStyle()} />
                      </div>
                      <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: 10, fontWeight: 700, color: '#958ea0', textTransform: 'uppercase' }}>Potencia Nominal</label>
                        <input type="text" value={baseSpecs.potencia} onChange={e => setBaseSpecs({...baseSpecs, potencia: e.target.value})} style={inputStyle()} placeholder="Ej: 1700-2040 W" />
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: 10, fontWeight: 700, color: '#958ea0', textTransform: 'uppercase' }}>Clase Eléctrica</label>
                        <input type="text" value={baseSpecs.clase} onChange={e => setBaseSpecs({...baseSpecs, clase: e.target.value})} style={inputStyle()} />
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: 10, fontWeight: 700, color: '#958ea0', textTransform: 'uppercase' }}>Grado Protección IP</label>
                        <input type="text" value={baseSpecs.ip} onChange={e => setBaseSpecs({...baseSpecs, ip: e.target.value})} style={inputStyle()} />
                      </div>
                      {/* NUEVO CAMPO: Características adicionales opcionales */}
                      <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: 10, fontWeight: 700, color: '#958ea0', textTransform: 'uppercase' }}>Características Eléctricas Adicionales (Opcional)</label>
                        <input
                          type="text"
                          value={baseSpecs.adicionales}
                          onChange={e => setBaseSpecs({...baseSpecs, adicionales: e.target.value})}
                          style={inputStyle()}
                          placeholder="Ej: Consumo espera: 0.30 W; 20 L; IPX0..."
                        />
                      </div>
                    </div>
                  </div>

                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 16, marginTop: 16 }}>
                    <h4 style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#8b5cf6', textTransform: 'uppercase', marginBottom: 14 }}>
                      Métricas Eficiencia Energética
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                      {selectedFamily?.fields.map(field => (
                        <div key={field.key} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          <label style={{ fontSize: 10, fontWeight: 700, color: '#958ea0', textTransform: 'uppercase' }}>
                            {field.label} {field.unit ? `(${field.unit})` : ''}
                          </label>
                          {field.type === 'select' ? (
                            <div style={{ position: 'relative' }}>
                              <select
                                value={eeFields[field.key] || ''}
                                onChange={e => setEeFields({ ...eeFields, [field.key]: e.target.value })}
                                style={inputStyle()}
                              >
                                {field.options?.map(o => <option key={o} value={o}>{o}</option>)}
                              </select>
                              <span className="material-symbols-outlined" style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', fontSize: 18, color: '#64748b', pointerEvents: 'none' }}>expand_more</span>
                            </div>
                          ) : (
                            <input
                              type={field.type === 'number' ? 'number' : 'text'}
                              value={eeFields[field.key] || ''}
                              onChange={e => setEeFields({ ...eeFields, [field.key]: e.target.value })}
                              style={inputStyle()}
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              )}

              {/* PASO 3: INFORME DE ENSAYO */}
              {currentStep === 3 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }} className="animate-fadeIn">
                  <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 12, marginBottom: 4 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                      Paso 3: Informe de Ensayo
                    </h3>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Número de Ensayo / Informe</label>
                    <input
                      type="text"
                      name="certNumber"
                      autoComplete="off"
                      value={certNumber}
                      onChange={e => setCertNumber(e.target.value)}
                      style={inputStyle()}
                      placeholder="Ej: CN26BARV 001"
                    />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Laboratorio de Ensayo</label>
                    <div style={{ position: 'relative' }}>
                      <input
                        list="lab-list"
                        value={oecNombre}
                        onChange={e => setOecNombre(e.target.value)}
                        style={inputStyle()}
                        placeholder="Seleccioná o escribí un laboratorio"
                      />
                      <datalist id="lab-list">
                        <option value="TÜV Rheinland" />
                        <option value="INTI" />
                        <option value="Lenor" />
                        <option value="SGS" />
                        <option value="Bureau Veritas" />
                      </datalist>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Datos de Contacto del Laboratorio</label>
                    <input
                      type="text"
                      value={oecContacto}
                      onChange={e => setOecContacto(e.target.value)}
                      style={inputStyle()}
                      placeholder="Ej: https://www.tuv.com/argentina/ o info@laboratorio.com"
                    />
                    <span style={{ fontSize: 10, color: '#64748b', marginTop: 4 }}>Dirección web o email de contacto del laboratorio (se incluye en la Tabla 4 de la DJC).</span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Fecha Emisión del Informe</label>
                    <input
                      type="text"
                      value={fechaEmision}
                      onChange={e => setFechaEmision(e.target.value)}
                      style={inputStyle()}
                      placeholder="DD/MM/YYYY"
                    />
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Fecha Próxima Vigilancia / Vencimiento</label>
                    <input
                      type="text"
                      value={fechaVencimiento}
                      onChange={e => setFechaVencimiento(e.target.value)}
                      style={{ ...inputStyle(), borderColor: 'rgba(245, 158, 11, 0.4)' }}
                      placeholder="DD/MM/YYYY"
                    />
                    <span style={{ fontSize: 10, color: '#f59e0b', marginTop: 4 }}>Calculada automáticamente (+4 años desde emisión) por Res. 438/2024.</span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Fecha Emisión de la DJC</label>
                    <input
                      type="text"
                      value={fechaEmisionDjc}
                      onChange={e => setFechaEmisionDjc(e.target.value)}
                      style={inputStyle()}
                      placeholder="DD/MM/YYYY"
                    />
                  </div>
                </div>
              )}

              {/* PASO 4: ETIQUETA EE & QR UPLOAD */}
              {currentStep === 4 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }} className="animate-fadeIn">
                  <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 12, marginBottom: 4 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, color: '#f8fafc', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                      Paso 4: Etiqueta EE & QR
                    </h3>
                  </div>

                  {/* Info multimodelo */}
                  <div style={{
                    background: 'rgba(139,92,246,0.06)',
                    border: '1px solid rgba(139,92,246,0.2)',
                    borderRadius: 10,
                    padding: 16,
                    fontSize: 12,
                    color: '#c084fc',
                    lineHeight: '1.6'
                  }}>
                    {modelList.length > 1 ? (
                      <><strong>Modo multimodelo activo ({modelList.length} modelos).</strong> Se generará una etiqueta por modelo. Usá las flechas del panel derecho para revisar cada una antes de generar.</>
                    ) : (
                      <><strong>¡Etiqueta autogenerada en tiempo real!</strong> Los datos de características y especificaciones ingresados ya están inyectados en la etiqueta oficial.</>
                    )}
                  </div>

                  {/* Selector de modelo activo (solo si hay más de 1) */}
                  {modelList.length > 1 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <label style={labelStyle}>Vista previa de modelo ({activeModelIndex + 1}/{modelList.length})</label>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {modelList.map((m, idx) => (
                          <button
                            key={idx}
                            onClick={() => setActiveModelIndex(idx)}
                            style={{
                              padding: '6px 14px',
                              borderRadius: 8,
                              fontSize: 11,
                              fontWeight: 700,
                              border: 'none',
                              cursor: 'pointer',
                              background: activeModelIndex === idx ? '#8b5cf6' : 'rgba(139,92,246,0.1)',
                              color: activeModelIndex === idx ? '#fff' : '#a78bfa',
                              transition: 'all 0.15s',
                            }}
                          >
                            {m}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <label style={labelStyle}>Código QR de la Etiqueta</label>
                    <input
                      ref={qrInputRef}
                      type="file"
                      accept="image/*"
                      onChange={e => { const f = e.target.files?.[0]; if (f) handleQrUpload(f); }}
                      className="hidden"
                    />
                    {qrImageUrl ? (
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 12,
                        padding: 12,
                        background: '#161522',
                        border: '1px solid rgba(139,92,246,0.18)',
                        borderRadius: 10
                      }}>
                        <img src={qrImageUrl} style={{ width: 48, height: 48, backgroundColor: '#fff', objectFit: 'contain', borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' }} alt="QR" />
                        <div style={{ flex: 1 }}>
                          <p style={{ fontSize: 12, fontWeight: 700, color: '#10b981' }}>QR cargado ✓</p>
                          <button onClick={() => setQrImageUrl('')} style={{ fontSize: 10, color: '#f87171', fontWeight: 700, textTransform: 'uppercase', marginTop: 4, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>✕ Quitar</button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => qrInputRef.current?.click()}
                        style={{
                          width: '100%',
                          height: 52,
                          border: '2px dashed rgba(139,92,246,0.25)',
                          borderRadius: 10,
                          background: 'rgba(139,92,246,0.02)',
                          color: '#a78bfa',
                          fontSize: 12,
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 8,
                          transition: 'all 0.15s'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.borderColor = '#8b5cf6';
                          e.currentTarget.style.background = 'rgba(139,92,246,0.05)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.borderColor = 'rgba(139,92,246,0.25)';
                          e.currentTarget.style.background = 'rgba(139,92,246,0.02)';
                        }}
                      >
                        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>photo_camera</span>
                        <span>Cargar imagen QR (Ej: Gadnic URL)</span>
                      </button>
                    )}
                    <span style={{ fontSize: 10, color: '#64748b', marginTop: 4 }}>El QR de la etiqueta debe contener el enlace de eficiencia energética.</span>
                  </div>

                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 16, marginTop: 16 }}>
                    <button
                      onClick={handleGenerate}
                      disabled={generating}
                      style={{
                        width: '100%',
                        height: 52,
                        borderRadius: 10,
                        backgroundColor: '#8b5cf6',
                        color: '#fff',
                        fontWeight: 700,
                        fontSize: 13,
                        textTransform: 'uppercase',
                        border: 'none',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                        boxShadow: '0 4px 14px rgba(139,92,246,0.3)',
                        transition: 'all 0.15s'
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#7c3aed'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#8b5cf6'; }}
                    >
                      {generating ? (
                        <>
                          <div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 0.7s linear infinite' }} />
                          <span>Generando previsualización...</span>
                        </>
                      ) : (
                        <>
                          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>picture_as_pdf</span>
                          <span>GENERAR DJC-EE</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* PASO 5: VISTA PREVIA Y CONFIRMACIÓN */}
              {currentStep === 5 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }} className="animate-fadeIn">
                  <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 12, marginBottom: 4 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, color: previewResult ? '#10b981' : '#f59e0b', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                      Paso 5: Vista Previa y Confirmación
                    </h3>
                  </div>

                  {!previewResult ? (
                    <div style={{
                      background: 'rgba(245,158,11,0.06)',
                      border: '1px solid rgba(245,158,11,0.2)',
                      borderRadius: 10,
                      padding: 16,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 12
                    }}>
                      <p style={{ fontSize: 12, color: '#fbbf24', margin: 0, lineHeight: 1.5 }}>
                        <strong>Previsualización pendiente:</strong> Presioná el botón a continuación para compilar el documento oficial en Word (.docx) y PDF con las etiquetas capturadas.
                      </p>
                      <button
                        onClick={handleGenerate}
                        disabled={generating}
                        style={{
                          width: '100%',
                          height: 48,
                          borderRadius: 10,
                          backgroundColor: '#8b5cf6',
                          color: '#fff',
                          fontWeight: 700,
                          fontSize: 12,
                          textTransform: 'uppercase',
                          border: 'none',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 8,
                          boxShadow: '0 4px 14px rgba(139,92,246,0.3)'
                        }}
                      >
                        {generating ? (
                          <>
                            <div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 0.7s linear infinite' }} />
                            <span>Generando previsualización...</span>
                          </>
                        ) : (
                          <>
                            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>picture_as_pdf</span>
                            <span>⚡ GENERAR Y VER PREVISUALIZACIÓN DJC-EE</span>
                          </>
                        )}
                      </button>
                    </div>
                  ) : (
                    <>
                      <div style={{
                        background: 'rgba(16,185,129,0.06)',
                        border: '1px solid rgba(16,185,129,0.2)',
                        borderRadius: 10,
                        padding: 16,
                        fontSize: 12,
                        color: '#34d399',
                        lineHeight: '1.6'
                      }}>
                        <strong>¡DJC-EE generada exitosamente en memoria!</strong> Podés ver la previsualización del PDF en la pantalla derecha.
                      </div>

                      <div style={{
                        background: '#161522',
                        border: '1px solid rgba(139,92,246,0.18)',
                        borderRadius: 10,
                        padding: 16
                      }}>
                        <div style={{ fontSize: 9, fontWeight: 700, color: '#958ea0', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Resumen Archivo</div>
                        <div style={{
                          fontFamily: "'Courier New', monospace",
                          fontSize: 12,
                          color: '#a78bfa',
                          userSelect: 'all',
                          padding: 10,
                          background: '#0f0e15',
                          border: '1px solid rgba(139,92,246,0.08)',
                          borderRadius: 6,
                          marginBottom: 12,
                          wordBreak: 'break-all'
                        }}>
                          {previewResult.filename}
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 11, color: '#94a3b8' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>Bidcom:</span>
                            <span style={{ fontWeight: 700, color: '#fff' }}>C{bidcom}</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>Marca/Modelo:</span>
                            <span style={{ fontWeight: 700, color: '#fff' }}>{marca} / {modelo}</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>ID DJC:</span>
                            <span style={{ fontWeight: 700, color: '#fff' }}>{previewResult.djc_id}</span>
                          </div>
                        </div>
                      </div>

                      {savedPaths ? (
                        <div style={{
                          background: 'rgba(16,185,129,0.06)',
                          border: '1px solid rgba(16,185,129,0.2)',
                          borderRadius: 10,
                          padding: 16,
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 8
                        }}>
                          <p style={{ fontSize: 12, fontWeight: 700, color: '#34d399' }}>✓ Guardado físicamente en tu PC:</p>
                          {savedPaths.map((p, idx) => (
                            <div key={idx} style={{
                              fontFamily: "'Courier New', monospace",
                              fontSize: 10,
                              color: '#e2e8f0',
                              padding: 8,
                              background: '#0f0e15',
                              borderRadius: 4,
                              wordBreak: 'break-all',
                              userSelect: 'all'
                            }}>
                              {p}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                          <button
                            onClick={handleDiscard}
                            disabled={confirming}
                            style={{
                              flex: 1,
                              height: 48,
                              borderRadius: 10,
                              background: 'transparent',
                              color: '#64748b',
                              border: '1px solid rgba(255,255,255,0.08)',
                              fontWeight: 700,
                              fontSize: 12,
                              textTransform: 'uppercase',
                              cursor: 'pointer',
                              transition: 'all 0.15s'
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.02)'; e.currentTarget.style.color = '#fff'; }}
                            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#64748b'; }}
                          >
                            Descartar
                          </button>
                          <button
                            onClick={handleConfirm}
                            disabled={confirming}
                            style={{
                              flex: 1,
                              height: 48,
                              borderRadius: 10,
                              background: '#10b981',
                              color: '#fff',
                              border: 'none',
                              fontWeight: 700,
                              fontSize: 12,
                              textTransform: 'uppercase',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: 6,
                              boxShadow: '0 4px 14px rgba(16,185,129,0.3)',
                              transition: 'all 0.15s'
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#059669'; }}
                            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#10b981'; }}
                          >
                            {confirming ? (
                              <>
                                <div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 0.7s linear infinite' }} />
                                <span>Guardando...</span>
                              </>
                            ) : (
                              <>
                                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>cloud_done</span>
                                <span>Confirmar & Guardar</span>
                              </>
                            )}
                          </button>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

            </div>

            {/* BOTONES ANTERIOR / SIGUIENTE (SIEMPRE VISIBLES PARA NAVEGACIÓN LIBRE) */}
            <div style={{
              display: 'flex',
              gap: 16,
              marginTop: 20,
              paddingTop: 16,
              borderTop: '1px solid rgba(255,255,255,0.06)'
            }}>
              <button
                onClick={() => setCurrentStep(prev => Math.max(1, prev - 1))}
                disabled={currentStep === 1}
                style={{
                  flex: 1,
                  height: 48,
                  borderRadius: 10,
                  background: 'transparent',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: currentStep === 1 ? '#475569' : '#94a3b8',
                  fontWeight: 700,
                  fontSize: 12,
                  textTransform: 'uppercase',
                  cursor: currentStep === 1 ? 'default' : 'pointer',
                  opacity: currentStep === 1 ? 0.4 : 1,
                  transition: 'all 0.15s'
                }}
                onMouseEnter={(e) => {
                  if (currentStep !== 1) {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
                    e.currentTarget.style.color = '#fff';
                  }
                }}
                onMouseLeave={(e) => {
                  if (currentStep !== 1) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = '#94a3b8';
                  }
                }}
              >
                Anterior
              </button>

              {currentStep < 4 ? (
                <button
                  onClick={() => setCurrentStep(prev => prev + 1)}
                  disabled={
                    (currentStep === 1 && (!bidcom.trim() || !marca.trim() || !modelo.trim())) ||
                    (currentStep === 2 && !selectedFamilyId) ||
                    (currentStep === 3 && (!certNumber.trim() || !fechaEmision.trim() || !fechaVencimiento.trim()))
                  }
                  style={{
                    flex: 1,
                    height: 48,
                    borderRadius: 10,
                    background: (
                      (currentStep === 1 && (!bidcom.trim() || !marca.trim() || !modelo.trim())) ||
                      (currentStep === 2 && !selectedFamilyId) ||
                      (currentStep === 3 && (!certNumber.trim() || !fechaEmision.trim() || !fechaVencimiento.trim()))
                    ) ? '#161522' : '#8b5cf6',
                    border: (
                      (currentStep === 1 && (!bidcom.trim() || !marca.trim() || !modelo.trim())) ||
                      (currentStep === 2 && !selectedFamilyId) ||
                      (currentStep === 3 && (!certNumber.trim() || !fechaEmision.trim() || !fechaVencimiento.trim()))
                    ) ? '1px solid rgba(139,92,246,0.1)' : 'none',
                    color: (
                      (currentStep === 1 && (!bidcom.trim() || !marca.trim() || !modelo.trim())) ||
                      (currentStep === 2 && !selectedFamilyId) ||
                      (currentStep === 3 && (!certNumber.trim() || !fechaEmision.trim() || !fechaVencimiento.trim()))
                    ) ? '#475569' : '#fff',
                    fontWeight: 700,
                    fontSize: 12,
                    textTransform: 'uppercase',
                    cursor: (
                      (currentStep === 1 && (!bidcom.trim() || !marca.trim() || !modelo.trim())) ||
                      (currentStep === 2 && !selectedFamilyId) ||
                      (currentStep === 3 && (!certNumber.trim() || !fechaEmision.trim() || !fechaVencimiento.trim()))
                    ) ? 'default' : 'pointer',
                    boxShadow: (
                      (currentStep === 1 && (!bidcom.trim() || !marca.trim() || !modelo.trim())) ||
                      (currentStep === 2 && !selectedFamilyId) ||
                      (currentStep === 3 && (!certNumber.trim() || !fechaEmision.trim() || !fechaVencimiento.trim()))
                    ) ? undefined : '0 4px 14px rgba(139,92,246,0.3)',
                    transition: 'all 0.15s'
                  }}
                  onMouseEnter={(e) => {
                    const isDisabled = (
                      (currentStep === 1 && (!bidcom.trim() || !marca.trim() || !modelo.trim())) ||
                      (currentStep === 2 && !selectedFamilyId) ||
                      (currentStep === 3 && (!certNumber.trim() || !fechaEmision.trim() || !fechaVencimiento.trim()))
                    );
                    if (!isDisabled) {
                      e.currentTarget.style.backgroundColor = '#7c3aed';
                    }
                  }}
                  onMouseLeave={(e) => {
                    const isDisabled = (
                      (currentStep === 1 && (!bidcom.trim() || !marca.trim() || !modelo.trim())) ||
                      (currentStep === 2 && !selectedFamilyId) ||
                      (currentStep === 3 && (!certNumber.trim() || !fechaEmision.trim() || !fechaVencimiento.trim()))
                    );
                    if (!isDisabled) {
                      e.currentTarget.style.backgroundColor = '#8b5cf6';
                    }
                  }}
                >
                  Siguiente
                </button>
              ) : currentStep === 4 ? (
                <button
                  onClick={handleGenerate}
                  disabled={generating}
                  style={{
                    flex: 1,
                    height: 48,
                    borderRadius: 10,
                    background: '#8b5cf6',
                    color: '#fff',
                    fontWeight: 700,
                    fontSize: 12,
                    textTransform: 'uppercase',
                    border: 'none',
                    cursor: 'pointer',
                    boxShadow: '0 4px 14px rgba(139,92,246,0.3)',
                    transition: 'all 0.15s'
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#7c3aed'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#8b5cf6'; }}
                >
                  {generating ? 'Generando...' : 'Generar DJC-EE →'}
                </button>
              ) : null}
            </div>

          </div>

          {/* COLUMNA DERECHA: VISUALIZADOR (PDF O ETIQUETA SEGÚN EL PASO) */}
          <div className="flex-1 bg-slate-950 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-2xl relative">
            
            {currentStep === 5 && previewResult ? (
              /* MOSTRAR PREVIEW DE DJC PDF EN PASO 5 USANDO BLOB URL */
              <div className="flex-1 flex flex-col h-full">
                <div className="h-12 border-b border-slate-800 bg-slate-950/80 backdrop-blur px-6 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-purple-400 text-sm">preview</span>
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Previsualización DJC-EE PDF</span>
                  </div>
                  <span className="font-mono text-[10px] text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                    {previewResult.filename}.pdf
                  </span>
                </div>
                <div className="flex-1 bg-slate-900 overflow-hidden">
                  {previewBlobUrl && (
                    <iframe
                      src={previewBlobUrl}
                      className="w-full h-full border-none"
                      title="DJC PDF Preview"
                    />
                  )}
                </div>
              </div>
            ) : (
              /* MOSTRAR ETIQUETA(S) EN VIVO EN PASOS 1-4 */
              <div className="flex-1 flex flex-col items-center justify-start p-6 overflow-y-auto gap-6">
                <div className="bg-slate-900 px-4 py-2 rounded-full border border-slate-800 flex items-center gap-2">
                  <span className="material-symbols-outlined text-purple-400 text-sm">print</span>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    {modelList.length > 1
                      ? `Etiqueta ${activeModelIndex + 1}/${modelList.length}: ${modelList[activeModelIndex]}`
                      : `Vista Previa EE — Paso ${currentStep}/4`
                    }
                  </span>
                </div>

                {/* Navegación entre modelos */}
                {modelList.length > 1 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button
                      onClick={() => setActiveModelIndex(i => Math.max(0, i - 1))}
                      disabled={activeModelIndex === 0}
                      style={{
                        width: 32, height: 32, borderRadius: 8, border: '1px solid rgba(139,92,246,0.25)',
                        background: 'rgba(139,92,246,0.08)', color: activeModelIndex === 0 ? '#475569' : '#a78bfa',
                        cursor: activeModelIndex === 0 ? 'default' : 'pointer', fontSize: 16, display: 'flex', alignItems: 'center', justifyContent: 'center'
                      }}
                    >‹</button>
                    {modelList.map((_m, idx) => (
                      <button key={idx} onClick={() => setActiveModelIndex(idx)}
                        style={{
                          width: 8, height: 8, borderRadius: '50%', border: 'none', cursor: 'pointer',
                          background: activeModelIndex === idx ? '#8b5cf6' : 'rgba(139,92,246,0.2)',
                          transition: 'all 0.2s',
                        }}
                      />
                    ))}
                    <button
                      onClick={() => setActiveModelIndex(i => Math.min(modelList.length - 1, i + 1))}
                      disabled={activeModelIndex === modelList.length - 1}
                      style={{
                        width: 32, height: 32, borderRadius: 8, border: '1px solid rgba(139,92,246,0.25)',
                        background: 'rgba(139,92,246,0.08)', color: activeModelIndex === modelList.length - 1 ? '#475569' : '#a78bfa',
                        cursor: activeModelIndex === modelList.length - 1 ? 'default' : 'pointer', fontSize: 16, display: 'flex', alignItems: 'center', justifyContent: 'center'
                      }}
                    >›</button>
                  </div>
                )}

                {/* Etiqueta visible (la activa del carrusel) */}
                <div className="shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-slate-800/40 rounded-sm bg-white overflow-hidden scale-90 sm:scale-100 transition-all">
                  <EtiquetaEE familyId={selectedFamilyId} data={getEtiquetaData(modelList[activeModelIndex])} />
                </div>

                {/* Etiquetas ocultas para captura por html-to-image (una por modelo) */}
                <div style={{ position: 'absolute', left: -9999, top: 0, pointerEvents: 'none', opacity: 0 }}>
                  {(modelList.length > 0 ? modelList : [modelo]).map((m, idx) => (
                    <div key={idx} id={`label-export-${idx}`}>
                      <EtiquetaEE familyId={selectedFamilyId} data={getEtiquetaData(m)} />
                    </div>
                  ))}
                </div>

                <span className="text-[10px] text-slate-500 max-w-sm text-center leading-relaxed">
                  {modelList.length > 1
                    ? `${modelList.length} etiquetas se insertarán en la DJC — una por celda.`
                    : 'Esta etiqueta se exportará automáticamente a la DJC. No requiere descarga manual.'
                  }
                </span>
              </div>
            )}

          </div>

        </div>
      )}
      
      <style>{`
        .animate-fadeIn {
          animation: fadeIn 0.25s ease-out forwards;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        input:focus, select:focus, textarea:focus {
          outline: none !important;
          border-color: rgba(139,92,246,0.7) !important;
        }
      `}</style>
    </div>
  );
}
