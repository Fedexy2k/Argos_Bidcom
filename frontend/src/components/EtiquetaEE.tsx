// Componente para renderizar la Etiqueta de Eficiencia Energética (EE)

// ── TYPES ───────────────────────────────────────────────────────────────────

export interface EtiquetaData {
  marca: string;
  modelo: string;
  origen: string;
  eficiencia: string; // 'A', 'B', etc.
  qrImageUrl?: string;
  referenciaIram: string;
  resolucion: string;
  
  // Hornos específicos
  descripcion?: string;
  consumoConvencional?: string;
  consumoForzada?: string;
  volumen?: string;
  clasificacion?: 'CHICO' | 'MEDIANO' | 'GRANDE';
  consumoEspera?: string;

  // Lavavajillas específicos
  consumoEnergia?: string;
  consumoAgua?: string;
  eficaciaSecado?: string;
  capacidad?: string;
  ruido?: string;

  // Genéricos / Otros
  [key: string]: any;
}

interface Props {
  familyId: string;
  data: EtiquetaData;
  id?: string;
}

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];
const COLORS = [
  '#009640', // A - Dark Green
  '#50AF31', // B - Green
  '#C8D400', // C - Light Green
  '#FFED00', // D - Yellow
  '#FBBA00', // E - Light Orange
  '#EC6707', // F - Orange
  '#E3001B'  // G - Red
];

const MM = 3.78;
const mm = (v: number) => Math.round(v * MM);
const pt = (v: number) => Math.round(v * 1.333 * (MM / 3.78));

const BLUE = '#2E3092';
const GRAY_BG = '#eae9ea';

// ── COMPONENTE TEMPLATE: HORNO ELÉCTRICO ───────────────────────────────────

function TemplateHorno({ data, id = "label-export" }: { data: EtiquetaData; id?: string }) {
  const FS6  = 8;
  const FS7  = 9;
  const FS8  = 11;
  const FS10 = 13;
  const FS11 = 15;
  const FS12 = 16;

  const BLUE    = '#2E3092';
  const GREEN   = '#009640';
  const GRAY_BG = '#eae9ea';
  const COLORS_MAP: Record<string, string> = {
    A: '#009640', B: '#52AE32', C: '#C8D400',
    D: '#FFED00', E: '#FBBA00', F: '#EC6608', G: '#E3001B',
  };

  const selIdx = LETTERS.indexOf(data.eficiencia);
  const W  = mm(116);
  const H  = mm(195);
  const MX = mm(2);
  const LW = W - 2 * MX;

  const HDR_T = MX;
  const HDR_H = mm(8);

  const LINE1_Y     = mm(12);
  const ARR_BLOCK_H = mm(85);
  const LINE2_Y     = LINE1_Y + ARR_BLOCK_H;
  const ARR_H       = mm(10);
  const ARR_GAP     = mm(1);
  const LBL_AREA    = Math.round(4.5 * MM);
  const IND_W       = mm(39);
  const IND_H       = mm(17);
  const IND_TRI     = mm(8);
  const ARR_TIP     = mm(5);
  const ARROW_WIDTHS_MM: Record<string, number> = {
    A: 22, B: 27.5, C: 33, D: 38.5, E: 44, F: 49.5, G: 55,
  };

  const BAR_TOP = LINE2_Y + 1 + mm(1);
  const BAR_H   = mm(20);

  const CARACT_TOP     = BAR_TOP + BAR_H;
  const CARACT_TITLE_H = mm(6);
  const ROW_H          = mm(13);

  const ROWS_TOP = CARACT_TOP + CARACT_TITLE_H;
  const ROW1_T   = ROWS_TOP;
  const ROW2_T   = ROW1_T + ROW_H;
  const ROW3_T   = ROW2_T + ROW_H;
  const ROW4_T   = ROW3_T + ROW_H;

  const FOOTER_SEP_Y = ROW4_T + ROW_H;
  const FOOTER_T     = FOOTER_SEP_Y + 1;

  const LEFT_COL_W = mm(50);
  const LEFT_COL_R = MX + LEFT_COL_W;

  const SEP_X = MX + mm(1);
  const SEP_W = LEFT_COL_W - mm(2);

  const LBL_X  = MX + 4;
  const ICON_CX = MX + mm(23);
  const VAL_X   = MX + mm(35);
  const VAL_W   = LEFT_COL_W - mm(35) - 2;

  const RIGHT_COL_X = LEFT_COL_R;
  const QR_SZ       = mm(26);
  const QR_LEFT     = MX + LW - QR_SZ - 2;
  const TEXT_COL_X  = RIGHT_COL_X + 4;
  const TEXT_COL_W  = QR_LEFT - RIGHT_COL_X - 10;
  const THREE_ROW_H = ROW_H * 3;
  const QR_TOP      = ROWS_TOP + Math.round((THREE_ROW_H - QR_SZ) / 2);
  const TEXT_MID_Y  = ROWS_TOP + Math.round(THREE_ROW_H / 2);

  const BAR_LH       = 20;
  const BAR_TEXT_TOP = BAR_TOP + Math.round((BAR_H - BAR_LH * 3) / 2);
  const lhMult = 1.1;

  const Hline = ({ y, x = SEP_X, w = SEP_W, color = '#000', thick = 1 }:
    { y: number; x?: number; w?: number; color?: string; thick?: number }) =>
    <div style={{ position: 'absolute', top: y, left: x, width: w, height: thick, backgroundColor: color }} />;

  const vc = (rowT: number, rowH: number, textH: number) =>
    rowT + Math.round((rowH - textH) / 2);

  return (
    <div
      id={id}
      style={{
        position: 'relative', width: W, height: H, fontFamily: 'Arial, Helvetica, sans-serif',
        backgroundColor: '#fff', border: '1.5px solid #000', boxSizing: 'border-box', color: '#000',
        lineHeight: 1
      }}
    >
      {/* 1. HEADER */}
      <div style={{ position: 'absolute', top: HDR_T, left: MX, width: LW, height: HDR_H, backgroundColor: BLUE }} />
      <div style={{ position: 'absolute', top: HDR_T, left: MX, width: LW, height: HDR_H, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 900, fontSize: FS12, letterSpacing: 1 }}>
        EFICIENCIA ENERG&Eacute;TICA
      </div>
      <Hline y={LINE1_Y} x={MX} w={LW} />

      {/* 2. ARROWS */}
      <div style={{ position: 'absolute', top: LINE1_Y + 1, left: MX, height: LBL_AREA, display: 'flex', alignItems: 'center', fontSize: FS6, fontWeight: 700 }}>
        M&Aacute;S EFICIENTE
      </div>

      {LETTERS.map((letter, i) => {
        const aTop  = LINE1_Y + 1 + LBL_AREA + i * (ARR_H + ARR_GAP);
        const aW    = mm(ARROW_WIDTHS_MM[letter]);
        const color = COLORS_MAP[letter] || '#000';
        const bodyW = aW - ARR_TIP;
        return (
          <div
            key={letter}
            style={{ position: 'absolute', top: aTop, left: MX, width: aW + ARR_TIP, height: ARR_H, display: 'flex', alignItems: 'center' }}
          >
            {/* Arrow body */}
            <div style={{ width: bodyW, height: '100%', backgroundColor: color, display: 'flex', alignItems: 'center', flexShrink: 0 }}>
              <span style={{ paddingLeft: 8, color: '#fff', fontWeight: 700, fontSize: 22, lineHeight: 1 }}>{letter}</span>
            </div>
            {/* Arrow tip */}
            <div style={{ width: 0, height: 0, borderTop: `${ARR_H / 2}px solid transparent`, borderBottom: `${ARR_H / 2}px solid transparent`, borderLeft: `${ARR_TIP}px solid ${color}`, flexShrink: 0 }} />
          </div>
        );
      })}

      <div style={{ position: 'absolute', top: LINE1_Y + 1 + LBL_AREA + 7 * ARR_H + 6 * ARR_GAP, left: MX, height: LBL_AREA, display: 'flex', alignItems: 'center', fontSize: FS6, fontWeight: 700 }}>
        MENOS EFICIENTE
      </div>

      {(() => {
        const safeSelIdx = selIdx >= 0 ? selIdx : 0;
        const cy      = LINE1_Y + 1 + LBL_AREA + safeSelIdx * (ARR_H + ARR_GAP) + Math.round(ARR_H / 2);
        const indTop  = cy - Math.round(IND_H / 2);
        const indLeft = MX + LW - IND_W;
        return (
          <>
            <div style={{ position: 'absolute', top: indTop, left: indLeft - IND_TRI + 1, width: 0, height: 0, borderTop: `${IND_H / 2}px solid transparent`, borderBottom: `${IND_H / 2}px solid transparent`, borderRight: `${IND_TRI}px solid #000` }} />
            <div style={{ position: 'absolute', top: indTop, left: indLeft, width: IND_W, height: IND_H, backgroundColor: '#000' }} />
            <div style={{ position: 'absolute', top: indTop, left: indLeft, width: IND_W, height: IND_H, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 44, paddingBottom: '4px' }}>
              {data.eficiencia}
            </div>
          </>
        );
      })()}
      <Hline y={LINE2_Y} x={MX} w={LW} />

      {/* 3. CONSUMPTION BAR */}
      <div style={{ position: 'absolute', top: BAR_TOP, left: MX, width: LW, height: BAR_H, backgroundColor: GREEN }} />
      {['CONSUMO DE', 'ENERG\u00CDA EN MODO', 'CONVENCIONAL'].map((txt, i) => (
        <div key={i} style={{ position: 'absolute', top: BAR_TEXT_TOP + i * BAR_LH, left: MX + mm(2), height: BAR_LH, display: 'flex', alignItems: 'center', fontWeight: 700, fontSize: FS12, color: '#000' }}>{txt}</div>
      ))}
      <div style={{ position: 'absolute', top: BAR_TOP, left: MX + mm(45), width: LW - mm(45) - 4, height: BAR_H, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '5px' }}>
        <span style={{ fontWeight: 700, fontSize: 58, color: '#000' }}>{data.consumoConvencional || '0.00'}</span>
        <span style={{ fontSize: FS12, fontWeight: 400, color: '#000', position: 'relative', top: '16px' }}>kWh/ciclo</span>
      </div>

      {/* 4. CARACTERÍSTICAS */}
      <div style={{ position: 'absolute', top: CARACT_TOP, left: MX, width: LEFT_COL_W, height: CARACT_TITLE_H, backgroundColor: GRAY_BG }} />
      <div style={{ position: 'absolute', top: CARACT_TOP, left: LBL_X, width: LEFT_COL_W - 8, height: CARACT_TITLE_H, display: 'flex', alignItems: 'center', fontWeight: 700, fontSize: FS10, color: BLUE }}>
        CARACTER&Iacute;STICAS
      </div>

      <div style={{ position: 'absolute', top: ROWS_TOP, left: MX, width: LEFT_COL_W, height: ROW_H * 4, backgroundColor: GRAY_BG }} />
      <div style={{ position: 'absolute', top: ROW4_T, left: LEFT_COL_R, width: LW - LEFT_COL_W, height: ROW_H, backgroundColor: GRAY_BG }} />

      {/* ROW 1 */}
      {(() => {
        const lbTop = vc(ROW1_T, ROW_H, FS6 * 2 * lhMult);
        const iconSz  = mm(8);
        const iconTop = vc(ROW1_T, ROW_H, iconSz);
        const iconLeft = ICON_CX - Math.round(iconSz / 2);
        return (
          <>
            <div style={{ position: 'absolute', top: lbTop, left: LBL_X, fontSize: FS6, lineHeight: lhMult, color: '#000', fontWeight: 'bold' }}>VOLUMEN DE<br />LA CAVIDAD</div>
            <img src="/icons/volumen-cavidad.png" alt="Oven" style={{ position: 'absolute', top: iconTop, left: iconLeft, width: iconSz, height: iconSz, objectFit: 'contain' }} />
            <div style={{ position: 'absolute', top: ROW1_T, left: VAL_X, width: VAL_W, height: ROW_H, display: 'flex', alignItems: 'center', fontWeight: 700, fontSize: FS10, color: '#000' }}>
              {data.volumen || '0'} <span style={{ fontWeight: 400, fontSize: FS6, marginLeft: 3 }}>lts</span>
            </div>
          </>
        );
      })()}
      <Hline y={ROW2_T} />

      {/* ROW 2 */}
      {(() => {
        const lbTop  = vc(ROW2_T, ROW_H, FS6 * 3 * lhMult);
        const iconSz = mm(8);
        const iconTop  = vc(ROW2_T, ROW_H, iconSz);
        const iconLeft = ICON_CX - Math.round(iconSz / 2);
        const valTop   = ROW2_T + Math.round((ROW_H - (FS10 + FS6)) / 2);
        return (
          <>
            <div style={{ position: 'absolute', top: lbTop, left: LBL_X, fontSize: FS6, lineHeight: lhMult, color: '#000', fontWeight: 'bold' }}>CONSUMO<br />DE ENERG&Iacute;A<br />CONVENCIONAL</div>
            <img src="/icons/consumo-convencional.png" alt="Meter" style={{ position: 'absolute', top: iconTop, left: iconLeft, width: iconSz, height: iconSz, objectFit: 'contain' }} />
            <div style={{ position: 'absolute', top: valTop, left: VAL_X, width: VAL_W, fontWeight: 700, fontSize: FS10, color: '#000', lineHeight: 1 }}>{data.consumoConvencional || '0.00'}</div>
            <div style={{ position: 'absolute', top: valTop + FS10 + 2, left: VAL_X, width: VAL_W, fontSize: FS6, color: '#000', lineHeight: 1 }}>kWh/ciclo</div>
          </>
        );
      })()}
      <Hline y={ROW3_T} />

      {/* ROW 3 */}
      {(() => {
        const lbTop  = vc(ROW3_T, ROW_H, FS6 * 4 * lhMult);
        const iconSz = mm(8);
        const iconTop  = vc(ROW3_T, ROW_H, iconSz);
        const iconLeft = ICON_CX - Math.round(iconSz / 2);
        const valTop   = ROW3_T + Math.round((ROW_H - (FS10 + FS6)) / 2);
        return (
          <>
            <div style={{ position: 'absolute', top: lbTop, left: LBL_X, fontSize: FS6, lineHeight: lhMult, color: '#000', fontWeight: 'bold' }}>CONSUMO<br />DE ENERG&Iacute;A<br />CONVENCIONAL<br />FORZADA</div>
            <img src="/icons/consumo-forzada.png" alt="Gauge" style={{ position: 'absolute', top: iconTop, left: iconLeft, width: iconSz, height: iconSz, objectFit: 'contain' }} />
            <div style={{ position: 'absolute', top: valTop, left: VAL_X, width: VAL_W, fontWeight: 700, fontSize: FS10, color: '#000', lineHeight: 1 }}>{data.consumoForzada || '0.00'}</div>
            <div style={{ position: 'absolute', top: valTop + FS10 + 2, left: VAL_X, width: VAL_W, fontSize: FS6, color: '#000', lineHeight: 1 }}>kWh/ciclo</div>
          </>
        );
      })()}
      <Hline y={ROW4_T} />

      {/* ROW 4 */}
      {(() => {
        const lbTop     = vc(ROW4_T, ROW_H, FS6 * 2 * lhMult);
        const clsLineH  = FS6 + 3;
        const clsTop    = ROW4_T + Math.round((ROW_H - clsLineH * 3) / 2);
        const clsColX   = LEFT_COL_R - mm(17);
        const arrowW    = mm(4);
        const arrowX    = clsColX - arrowW - 2;

        return (
          <>
            <div style={{ position: 'absolute', top: lbTop, left: LBL_X, fontSize: FS6, lineHeight: lhMult, color: '#000', fontWeight: 'bold' }}>CLASIFICACI&Oacute;N<br />POR VOLUMEN</div>
            {(['CHICO', 'MEDIANO', 'GRANDE'] as const).map((cls, ci) => (
              <div key={cls} style={{ position: 'absolute', top: clsTop + ci * clsLineH, left: clsColX, width: mm(16), height: clsLineH, display: 'flex', alignItems: 'center', fontSize: FS6, fontWeight: 400, color: '#000' }}>
                {cls}
              </div>
            ))}
            {(() => {
              const clsOrder = ['CHICO', 'MEDIANO', 'GRANDE'];
              const selCi = clsOrder.indexOf(data.clasificacion || 'CHICO');
              const arrowY = clsTop + (selCi >= 0 ? selCi : 0) * clsLineH;
              return (
                <div style={{ position: 'absolute', top: arrowY, left: arrowX, width: arrowW, height: clsLineH, display: 'flex', alignItems: 'center', fontSize: FS6, fontWeight: 700, color: '#000' }}>
                  &rarr;
                </div>
              );
            })()}

            <div style={{ position: 'absolute', top: ROW4_T, left: LEFT_COL_R + 4, width: LW - LEFT_COL_W - mm(20), height: ROW_H, display: 'flex', alignItems: 'center', fontWeight: 700, fontSize: FS8, color: '#000' }}>
              CONSUMO EN ESPERA
            </div>
            {(() => {
              const sz   = mm(5);
              const pTop = ROW4_T + Math.round((ROW_H - sz) / 2);
              const pLft = MX + LW - mm(20);
              return (
                <img src="/icons/consumo-espera.png" alt="Standby" style={{ position: 'absolute', top: pTop, left: pLft, width: sz, height: sz, objectFit: 'contain' }} />
              );
            })()}
            <div style={{ position: 'absolute', top: ROW4_T, left: MX + LW - mm(13), width: mm(13), height: ROW_H, display: 'flex', alignItems: 'center', fontWeight: 700, fontSize: FS8, color: '#000' }}>
              {data.consumoEspera || '0.00'}w
            </div>
          </>
        );
      })()}

      {/* RIGHT COLUMN */}
      <div style={{ position: 'absolute', top: QR_TOP, left: QR_LEFT, width: QR_SZ, height: QR_SZ, border: '1.5px solid #000', boxSizing: 'border-box' }}>
        {data.qrImageUrl ? (
          <img src={data.qrImageUrl} alt="QR" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
        ) : (
          <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: 7, textAlign: 'center', lineHeight: lhMult, fontWeight: 'bold' }}>ESPACIO<br />CODIGO QR</span>
          </div>
        )}
      </div>
      <div style={{ position: 'absolute', top: TEXT_MID_Y - (FS10 + 4) * 2 - 6, left: TEXT_COL_X, width: TEXT_COL_W, textAlign: 'center', fontWeight: 700, color: '#000' }}>
        <div style={{ fontSize: FS10, lineHeight: 1.2 }}>Referencia IRAM</div>
        <div style={{ fontSize: FS10, lineHeight: 1.2 }}>{data.referenciaIram || '62414-1/2'}</div>
      </div>
      <Hline y={TEXT_MID_Y} x={TEXT_COL_X + mm(1)} w={TEXT_COL_W - mm(2)} color="#999" />
      <div style={{ position: 'absolute', top: TEXT_MID_Y + 4, left: TEXT_COL_X, width: TEXT_COL_W, textAlign: 'center', fontWeight: 700, color: '#000' }}>
        <div style={{ fontSize: FS10, lineHeight: 1.2 }}>Res. SIyC N&deg;</div>
        <div style={{ fontSize: FS10, lineHeight: 1.2 }}>{data.resolucion || '438/24'}</div>
      </div>

      <Hline y={FOOTER_SEP_Y} x={MX} w={LW} />

      {/* 5. FOOTER */}
      <div style={{ position: 'absolute', top: FOOTER_T + 4, left: MX, width: LW, height: mm(5), display: 'flex', alignItems: 'center', fontFamily: '"Arial Black", Arial, sans-serif', fontSize: FS11, fontWeight: 900 }}>
        {data.descripcion || 'HORNO ELÉCTRICO'}
      </div>
      {[
        { label: 'MODELO',          val: data.modelo },
        { label: 'MARCA COMERCIAL', val: data.marca },
        { label: 'ORIGEN',          val: data.origen },
      ].map(({ label, val }, i) => (
        <div key={label} style={{ position: 'absolute', top: FOOTER_T + 4 + mm(5) + i * mm(3.8), left: MX, width: LW, height: mm(3.8), display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: FS7, fontWeight: 'bold' }}>
          <span>{label}</span>
          <span style={{ fontWeight: 900 }}>{val || '—'}</span>
        </div>
      ))}
    </div>
  );
}

// ── COMPONENTE TEMPLATE: LAVAVAJILLAS ──────────────────────────────────────

function TemplateLavavajillas({ data, id = "label-export" }: { data: EtiquetaData; id?: string }) {
  const scale = 3.78;
  const mm = (val: number) => val * scale;
  const pt = (val: number) => val * 1.333 * (scale / 3.78); 

  // Global Dimensions
  const outerW = mm(116);
  const outerH = mm(222);
  const lineW = mm(0.35);

  // Inner margin
  const m = mm(2);
  const innerW = outerW - m * 2; // 112mm
  const innerH = outerH - m * 2; // 218mm

  const H_CABEZAL = mm(11); 
  const H_ESCALA = mm(99);
  const H_GAP = mm(1);
  const H_ENERGIA = mm(24);
  const H_AGUA = mm(17);
  const H_CARACT = mm(45);
  const H_FOOTER = mm(21); 

  const yCabezal = 0;
  const yEscala = yCabezal + H_CABEZAL;
  const yEnergia = yEscala + H_ESCALA + H_GAP;
  const yAgua = yEnergia + H_ENERGIA;
  const yCaract = yAgua + H_AGUA;
  const yFooter = yCaract + H_CARACT;

  const bgGrisClaro = '#eae9ea';

  // Arrow drawing function
  const renderRibbon = (color: string, bodyWidthMm: number, height: number, text: string) => {
    const tipWidth = mm(5);
    const bodyWidth = mm(bodyWidthMm) - tipWidth;
    
    return (
      <div style={{ position: 'relative', height: height, display: 'flex', alignItems: 'center' }}>
        <div style={{ 
          backgroundColor: color, 
          width: bodyWidth, 
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          paddingLeft: mm(2),
          fontFamily: 'Arial',
          fontWeight: 'bold',
          fontSize: pt(20)
        }}>
          <span style={{color: '#fff'}}>{text}</span>
        </div>
        <div style={{
          width: 0,
          height: 0,
          borderTop: `${height / 2}px solid transparent`,
          borderBottom: `${height / 2}px solid transparent`,
          borderLeft: `${tipWidth}px solid ${color}`
        }} />
      </div>
    );
  };

  const selectedIndex = LETTERS.indexOf(data.eficiencia) >= 0 ? LETTERS.indexOf(data.eficiencia) : 0;
  const ribbonWidths = [31.5, 36.3, 41.1, 45.9, 50.7, 55.5, 60.3]; // mm width of A to G labels

  // Slider Math
  const maxAgua = 300;
  const currentAgua = parseFloat(String(data.consumoAgua || '0').replace(',', '.')) || 0;
  const sliderPct = Math.min(Math.max((currentAgua / maxAgua) * 100, 0), 100);

  return (
    <div
      id={id}
      style={{
        width: outerW,
        height: outerH,
        backgroundColor: '#fff',
        position: 'relative',
        boxSizing: 'border-box',
        overflow: 'hidden',
        fontFamily: 'Arial, sans-serif',
        lineHeight: '1',
        color: '#000',
        border: `${lineW}px solid #000` 
      }}
    >
      {/* Inner Container: 112x218 empty margin (no border) */}
      <div style={{ position: 'absolute', top: m, left: m, width: innerW, height: innerH, boxSizing: 'border-box' }}>
        
        {/* BLOCK 1: Cabezal */}
        <div style={{ position: 'absolute', top: yCabezal, left: 0, width: '100%', height: H_CABEZAL }}>
          <div style={{ backgroundColor: '#21337B', height: mm(10), width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#fff', fontFamily: '"Arial Black", Arial, sans-serif', fontSize: pt(14), fontWeight: 900 }}>
              EFICIENCIA ENERGÉTICA
            </span>
          </div>
          {/* Black line 1mm below blue box */}
          <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />
        </div>

        {/* BLOCK 2: Escala A-G */}
        <div style={{ position: 'absolute', top: yEscala, left: 0, width: '100%', height: H_ESCALA }}>
          <div style={{ position: 'absolute', top: mm(1.5), left: 0, fontSize: pt(6), fontWeight: 'bold' }}>MÁS EFICIENTE</div>
          <div style={{ position: 'absolute', bottom: mm(2), left: 0, fontSize: pt(6), fontWeight: 'bold' }}>MENOS EFICIENTE</div>
          
          <div style={{ position: 'absolute', top: mm(5.5), left: 0, width: '100%' }}>
            {LETTERS.map((label, i) => {
              return (
                <div key={label} style={{ position: 'absolute', top: mm(i * (11.5 + 1.41)), left: 0 }}>
                  {renderRibbon(COLORS[i], ribbonWidths[i], mm(11.5), label)}
                </div>
              );
            })}
          </div>

          {/* Black Indicator Arrow */}
          <div style={{ position: 'absolute', top: mm(5.5 + (selectedIndex * (11.5 + 1.41))) + (mm(11.5 - 20)/2), right: 0, width: mm(46), height: mm(20), display: 'flex' }}>
            <div style={{
              width: 0,
              height: 0,
              borderTop: `${mm(10)}px solid transparent`,
              borderBottom: `${mm(10)}px solid transparent`,
              borderRight: `${mm(10)}px solid #000`
            }} />
            <div style={{ 
              backgroundColor: '#000', 
              flex: 1, 
              height: '100%', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              color: '#fff',
              fontSize: pt(40),
              fontWeight: 700
            }}>
              {data.eficiencia}
            </div>
          </div>
          
          {/* Border below Escala */}
          <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />
        </div>

        {/* BLOCK 3: Energía */}
        <div style={{ position: 'absolute', top: yEnergia, left: 0, width: '100%', height: H_ENERGIA, backgroundColor: '#f1ea3a', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', padding: `0 ${mm(4)}px ${mm(2.5)}px ${mm(4)}px` }}>
          <div style={{ fontSize: pt(14), fontWeight: 'bold', lineHeight: '16pt', color: '#000', paddingBottom: mm(1) }}>
            CONSUMO<br/>DE ENERGÍA<br/>POR CICLO
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline' }}>
            <span style={{ fontSize: pt(60), fontWeight: 'bold', color: '#000', lineHeight: '0.8' }}>{data.consumoEnergia || '0.00'}</span>
            <span style={{ fontSize: pt(16), marginLeft: mm(1), color: '#000' }}>kWh</span>
          </div>
        </div>

        {/* BLOCK 4: Agua */}
        <div style={{ position: 'absolute', top: yAgua, left: 0, width: '100%', height: H_AGUA, backgroundColor: bgGrisClaro }}>
          <div style={{ position: 'absolute', top: mm(2), left: mm(4), fontSize: pt(10), fontWeight: 'bold', lineHeight: '1.1', color: '#27348b' }}>
            CONSUMO<br/>DE AGUA<br/>POR CICLO
          </div>
          <img src="/icons/agua.png" style={{ position: 'absolute', left: mm(25), top: mm(2.5), height: mm(12.5) }} alt="agua" />
          
          {/* Water Slider Line */}
          <div style={{ position: 'absolute', bottom: mm(4), right: mm(4), width: mm(63), height: mm(10) }}>
             
             {/* Slider Top Values (Dynamic Triangle) */}
             <div style={{ position: 'absolute', left: `${sliderPct}%`, bottom: mm(5), transform: 'translateX(-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', whiteSpace: 'nowrap' }}>
                  <span style={{ fontFamily: 'Arial', fontWeight: 'bold', fontSize: pt(12) }}>{data.consumoAgua || '0'}</span>
                  <span style={{ fontFamily: 'Arial', fontSize: pt(8), marginLeft: mm(1) }}>lts</span>
                </div>
                <div style={{
                  width: 0,
                  height: 0,
                  borderLeft: `${mm(2.5)}px solid transparent`,
                  borderRight: `${mm(2.5)}px solid transparent`,
                  borderTop: `${mm(2.5)}px solid #000`,
                  marginTop: mm(0.5)
                }} />
             </div>

             {/* Line */}
             <div style={{ position: 'absolute', bottom: mm(4), left: 0, width: '100%', height: mm(0.8), backgroundColor: '#000' }}>
               {[0, 50, 100, 150, 200, 250, 300].map((val, idx) => {
                 const pct = (idx / 6) * 100;
                 return <div key={val} style={{ position: 'absolute', left: `${pct}%`, top: mm(-0.6), width: mm(2), height: mm(2), borderRadius: '50%', backgroundColor: '#000', transform: 'translateX(-50%)' }} />
               })}
             </div>

             {/* Bottom texts */}
             <div style={{ position: 'absolute', bottom: mm(-1.5), left: 0, width: '100%', height: mm(3) }}>
                {[0, 50, 100, 150, 200, 250, 300].map((val, idx) => {
                  const pct = (idx / 6) * 100;
                  return <div key={val} style={{ position: 'absolute', left: `${pct}%`, top: 0, transform: 'translateX(-50%)', fontSize: pt(5), fontFamily: 'Arial' }}>{val}</div>
                })}
                <div style={{ position: 'absolute', left: mm(-1), top: mm(2.5), fontSize: pt(5), fontFamily: 'Arial' }}>MENOR</div>
                <div style={{ position: 'absolute', right: mm(-1), top: mm(2.5), fontSize: pt(5), fontFamily: 'Arial' }}>MAYOR</div>
             </div>
          </div>
        </div>

        {/* BLOCK 5: Características */}
        <div style={{ position: 'absolute', top: yCaract, left: 0, width: '100%', height: H_CARACT, backgroundColor: '#fff' }}>
          
          <div style={{ position: 'absolute', left: 0, top: 0, width: mm(57), height: mm(45), backgroundColor: bgGrisClaro }}>
             
             {/* Secado */}
             <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: mm(15), display: 'flex', alignItems: 'center', paddingLeft: mm(2) }}>
               <div style={{ width: mm(18), fontSize: pt(6), lineHeight: '1.2', fontWeight: 'bold' }}>EFICACIA<br/>DE SECADO</div>
               <div style={{ width: mm(12), display: 'flex', justifyContent: 'center' }}>
                 <img src="/icons/secado.png" style={{ height: mm(10) }} alt="secado" />
               </div>
               <div style={{ width: mm(22), display: 'flex', alignItems: 'baseline', gap: mm(0.5) }}>
                 {LETTERS.map(l => (
                   <span key={l} style={{ fontSize: pt(data.eficaciaSecado === l ? 12 : 7), fontFamily: '"Arial Black", Arial', color: '#000', lineHeight: 1, fontWeight: 'bold' }}>{l}</span>
                 ))}
               </div>
               <div style={{ position: 'absolute', bottom: 0, left: mm(2), width: mm(53), height: `${lineW}px`, backgroundColor: '#000' }} />
             </div>

             {/* Capacidad */}
             <div style={{ position: 'absolute', top: mm(15), left: 0, width: '100%', height: mm(15), display: 'flex', alignItems: 'center', paddingLeft: mm(2) }}>
               <div style={{ width: mm(18), fontSize: pt(6), lineHeight: '1.2', fontWeight: 'bold' }}>CAPACIDAD<br/>DECLARADA</div>
               <div style={{ width: mm(12), display: 'flex', justifyContent: 'center' }}>
                 <img src="/icons/capacidad.png" style={{ height: mm(8) }} alt="capacidad" />
               </div>
               <div style={{ width: mm(22), display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start' }}>
                 <span style={{ fontSize: pt(10), fontFamily: '"Arial Black", Arial', lineHeight: 1, fontWeight: 'bold' }}>{data.capacidad || '0'}</span> 
                 <span style={{ fontSize: pt(5), fontFamily: 'Arial' }}>Cubiertos</span>
               </div>
               <div style={{ position: 'absolute', bottom: 0, left: mm(2), width: mm(53), height: `${lineW}px`, backgroundColor: '#000' }} />
             </div>

             {/* Ruido */}
             <div style={{ position: 'absolute', top: mm(30), left: 0, width: '100%', height: mm(15), display: 'flex', alignItems: 'center', paddingLeft: mm(2) }}>
               <div style={{ width: mm(18), fontSize: pt(6), lineHeight: '1.2', fontWeight: 'bold' }}>NIVEL<br/>DE RUIDO</div>
               <div style={{ width: mm(12), display: 'flex', justifyContent: 'center' }}>
                 <img src="/icons/ruido.png" style={{ height: mm(8) }} alt="ruido" />
               </div>
               <div style={{ width: mm(22), display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start' }}>
                 <span style={{ fontSize: pt(10), fontFamily: '"Arial Black", Arial', lineHeight: 1, fontWeight: 'bold' }}>{data.ruido || '0'}</span> 
                 <span style={{ fontSize: pt(5), fontFamily: 'Arial' }}>dB(A)re 1 pW</span>
               </div>
             </div>
          </div>

          {/* Right panel */}
          <div style={{ position: 'absolute', left: mm(57), top: 0, width: mm(55), height: mm(35), display: 'flex' }}>
             
             <div style={{ width: mm(27), height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
               <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: mm(1) }}>
                 <span style={{ fontSize: pt(8), fontWeight: 'bold', fontFamily: 'Arial' }}>Referencia IRAM</span>
                 <span style={{ fontSize: pt(8), fontWeight: 'bold', fontFamily: 'Arial' }}>{data.referenciaIram || '2294-3'}</span>
               </div>
               <div style={{ width: mm(18), height: `${lineW}px`, backgroundColor: '#000', margin: `${mm(2)}px 0` }} />
               <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: mm(1) }}>
                 <span style={{ fontSize: pt(8), fontWeight: 'bold', fontFamily: 'Arial' }}>Res. SIyC N°</span>
                 <span style={{ fontSize: pt(8), fontWeight: 'bold', fontFamily: 'Arial' }}>{data.resolucion || '438/24'}</span>
               </div>
             </div>
             
             {/* QR Box */}
             <div style={{ width: mm(28), height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
               <div style={{ width: mm(28), height: mm(28), border: `${lineW}px solid #000`, display: 'flex', justifyContent: 'center', alignItems: 'center', textAlign: 'center', overflow: 'hidden' }}>
                 {data.qrImageUrl ? (
                   <img src={data.qrImageUrl} alt="QR" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                 ) : (
                   <span style={{ fontSize: pt(8), fontFamily: '"Arial Black", Arial', fontWeight: 'bold' }}>ESPACIO<br/>CODIGO QR</span>
                 )}
               </div>
             </div>
             
          </div>

          {/* Consumo Espera */}
          <div style={{ position: 'absolute', left: mm(57), top: mm(35), width: mm(55), height: mm(10), backgroundColor: bgGrisClaro, display: 'flex', alignItems: 'center', justifyContent: 'center', paddingRight: mm(1) }}>
            <span style={{ fontSize: pt(8), fontWeight: 'bold', whiteSpace: 'nowrap', fontFamily: 'Arial' }}>CONSUMO EN ESPERA</span>
            <img src="/icons/espera.png" style={{ height: mm(6), marginLeft: mm(1), marginRight: mm(1) }} alt="standby" />
            <span style={{ fontSize: pt(8), fontFamily: '"Arial Black", Arial', fontWeight: 'bold' }}>{data.consumoEspera || '0.00'}W</span>
          </div>

        </div>

        <div style={{ position: 'absolute', top: yFooter, left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />

        {/* Footer */}
        <div style={{ position: 'absolute', top: yFooter + mm(2), left: 0, width: '100%', height: H_FOOTER - mm(2), display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: pt(12), fontWeight: 900, fontFamily: '"Arial Black", Arial', marginBottom: mm(1) }}>LAVAVAJILLAS</div>
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>MODELO</span>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>{data.modelo}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>MARCA COMERCIAL</span>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>{data.marca}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>ORIGEN</span>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>{data.origen}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

// ── COMPONENTE TEMPLATE: GENÉRICO (UNIVERSAL) ──────────────────────────────

function TemplateGeneric({ data, familyId, id = "label-export" }: { data: EtiquetaData; familyId: string; id?: string }) {
  const selIdx = LETTERS.indexOf(data.eficiencia);
  const W = mm(116);
  const H = mm(220); // standard height
  const MX = mm(2);
  const LW = W - 2 * MX;
  
  const HDR_T = MX;
  const HDR_H = mm(10);
  const LINE1_Y = mm(14);
  const ARR_BLOCK_H = mm(85);
  const LINE2_Y = LINE1_Y + ARR_BLOCK_H;
  
  const ARR_H = mm(9.5);
  const ARR_GAP = mm(1);
  const LBL_AREA = Math.round(4.5 * MM);
  const IND_W = mm(36);
  const IND_H = mm(16);
  const IND_TRI = mm(8);
  const ARR_TIP = mm(5);
  
  const arrowWidths: Record<string, number> = {
    A: 22, B: 27.5, C: 33, D: 38.5, E: 44, F: 49.5, G: 55,
  };

  const BAR_TOP = LINE2_Y + 1 + mm(1);
  const BAR_H = mm(20);
  
  const CARACT_TOP = BAR_TOP + BAR_H + mm(1);
  const CARACT_TITLE_H = mm(6);
  const ROW_H = mm(11.5);
  
  const ROWS_TOP = CARACT_TOP + CARACT_TITLE_H;
  
  const RIGHT_COL_X = MX + mm(60);
  const QR_SZ = mm(26);

  const Hline = ({ y, x = MX, w = LW, color = '#000', thick = 1 }:
    { y: number; x?: number; w?: number; color?: string; thick?: number }) =>
    <div style={{ position: 'absolute', top: y, left: x, width: w, height: thick, backgroundColor: color }} />;

  // Filtrar campos técnicos dinámicos ingresados (que no sean metadatos base)
  const eeFields = Object.entries(data).filter(([k, v]) => {
    return ![
      'marca', 'modelo', 'origen', 'eficiencia', 'qrImageUrl', 
      'referenciaIram', 'resolucion', 'descripcion'
    ].includes(k) && v !== undefined && String(v).trim() !== '';
  }).slice(0, 4); // max 4 rows in generic

  const FOOTER_Y = ROWS_TOP + ROW_H * Math.max(eeFields.length, 3);

  return (
    <div
      id={id}
      style={{
        position: 'relative', width: W, height: H, fontFamily: 'Arial, Helvetica, sans-serif',
        backgroundColor: '#fff', border: '1.5px solid #000', boxSizing: 'border-box', color: '#000',
        lineHeight: 1
      }}
    >
      <div style={{ position: 'absolute', top: HDR_T, left: MX, width: LW, height: HDR_H, backgroundColor: BLUE }} />
      <div style={{ position: 'absolute', top: HDR_T, left: MX, width: LW, height: HDR_H, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 900, fontSize: pt(10), letterSpacing: 0.5 }}>
        EFICIENCIA ENERG&Eacute;TICA
      </div>
      <Hline y={LINE1_Y} />

      <div style={{ position: 'absolute', top: LINE1_Y + 1, left: MX, height: LBL_AREA, display: 'flex', alignItems: 'center', fontSize: pt(5.5), fontWeight: 700 }}>
        M&Aacute;S EFICIENTE
      </div>

      {LETTERS.map((letter, i) => {
        const aTop = LINE1_Y + 1 + LBL_AREA + i * (ARR_H + ARR_GAP);
        const aW = mm(arrowWidths[letter] || 22);
        const color = COLORS[i];
        const bodyW = aW - ARR_TIP;
        return (
          <div
            key={letter}
            style={{ position: 'absolute', top: aTop, left: MX, width: aW + ARR_TIP, height: ARR_H, display: 'flex', alignItems: 'center' }}
          >
            <div style={{ width: bodyW, height: '100%', backgroundColor: color, display: 'flex', alignItems: 'center', flexShrink: 0 }}>
              <span style={{ paddingLeft: 6, color: '#fff', fontWeight: 700, fontSize: pt(12), lineHeight: 1 }}>{letter}</span>
            </div>
            <div style={{ width: 0, height: 0, borderTop: `${ARR_H / 2}px solid transparent`, borderBottom: `${ARR_H / 2}px solid transparent`, borderLeft: `${ARR_TIP}px solid ${color}`, flexShrink: 0 }} />
          </div>
        );
      })}

      <div style={{ position: 'absolute', top: LINE1_Y + 1 + LBL_AREA + 7 * ARR_H + 6 * ARR_GAP, left: MX, height: LBL_AREA, display: 'flex', alignItems: 'center', fontSize: pt(5.5), fontWeight: 700 }}>
        MENOS EFICIENTE
      </div>

      {(() => {
        const cy = LINE1_Y + 1 + LBL_AREA + (selIdx >= 0 ? selIdx : 0) * (ARR_H + ARR_GAP) + Math.round(ARR_H / 2);
        const indTop = cy - Math.round(IND_H / 2);
        const indLeft = MX + LW - IND_W;
        return (
          <>
            <div style={{ position: 'absolute', top: indTop, left: indLeft - IND_TRI + 1, width: 0, height: 0, borderTop: `${IND_H / 2}px solid transparent`, borderBottom: `${IND_H / 2}px solid transparent`, borderRight: `${IND_TRI}px solid #000` }} />
            <div style={{ position: 'absolute', top: indTop, left: indLeft, width: IND_W, height: IND_H, backgroundColor: '#000' }} />
            <div style={{ position: 'absolute', top: indTop, left: indLeft, width: IND_W, height: IND_H, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: pt(28), paddingBottom: '3px' }}>
              {data.eficiencia}
            </div>
          </>
        );
      })()}
      <Hline y={LINE2_Y} />

      {/* Barra de Consumo Primario */}
      <div style={{ position: 'absolute', top: BAR_TOP, left: MX, width: LW, height: BAR_H, backgroundColor: '#52AE32', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: `0 ${mm(3)}px` }} />
      <div style={{ position: 'absolute', top: BAR_TOP, left: MX + mm(3), height: BAR_H, display: 'flex', flexDirection: 'column', justifyContent: 'center', fontSize: pt(7.5), fontWeight: 'bold', color: '#000' }}>
        <span>CONSUMO</span>
        <span>DE ENERG&Iacute;A</span>
      </div>
      <div style={{ position: 'absolute', top: BAR_TOP, right: MX + mm(3), height: BAR_H, display: 'flex', alignItems: 'baseline', justifyContent: 'flex-end', gap: '3px' }}>
        <span style={{ fontWeight: 900, fontSize: pt(36), color: '#000', lineHeight: 0.8 }}>
          {data.consumo_anual || data.consumo_ciclo || data.consumo_encendido || '0.00'}
        </span>
        <span style={{ fontSize: pt(8), fontWeight: 'bold', color: '#000' }}>
          {data.consumo_anual ? 'kWh/año' : 'kWh'}
        </span>
      </div>

      {/* Características Técnicas */}
      <div style={{ position: 'absolute', top: CARACT_TOP, left: MX, width: mm(60), height: CARACT_TITLE_H, backgroundColor: GRAY_BG }} />
      <div style={{ position: 'absolute', top: CARACT_TOP, left: MX + 4, width: mm(60) - 8, height: CARACT_TITLE_H, display: 'flex', alignItems: 'center', fontWeight: 700, fontSize: pt(7.5), color: BLUE }}>
        CARACTER&Iacute;STICAS
      </div>

      {/* Tabla de características dinámicas */}
      {eeFields.map(([k, val], idx) => {
        const top = ROWS_TOP + idx * ROW_H;
        return (
          <div key={k} style={{ position: 'absolute', top, left: MX, width: mm(60), height: ROW_H, backgroundColor: GRAY_BG, display: 'flex', alignItems: 'center', borderBottom: '1px solid #ccc', boxSizing: 'border-box', padding: `0 ${mm(2)}px` }}>
            <span style={{ fontSize: pt(6), textTransform: 'uppercase', flex: 1, fontWeight: 'bold', color: '#333' }}>
              {k.replace('_', ' ')}
            </span>
            <span style={{ fontSize: pt(8.5), fontWeight: 900, color: '#000' }}>
              {String(val)}
            </span>
          </div>
        );
      })}

      {/* Columna Derecha: QR + Referencia */}
      <div style={{ position: 'absolute', top: ROWS_TOP + mm(2), left: RIGHT_COL_X, width: QR_SZ, height: QR_SZ, border: '1.5px solid #000', boxSizing: 'border-box' }}>
        {data.qrImageUrl ? (
          <img src={data.qrImageUrl} alt="QR" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
        ) : (
          <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#eee' }}>
            <span style={{ fontSize: pt(5.5), textAlign: 'center', lineHeight: 1, fontWeight: 'bold' }}>QR CODE</span>
          </div>
        )}
      </div>
      
      <div style={{ position: 'absolute', top: ROWS_TOP + QR_SZ + mm(4), left: RIGHT_COL_X, width: LW - mm(60), display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
        <div style={{ textAlign: 'center', fontWeight: 'bold' }}>
          <div style={{ fontSize: pt(6.5), color: '#555' }}>Norma IRAM</div>
          <div style={{ fontSize: pt(7.5), color: '#000' }}>{data.referenciaIram || 'Referencia'}</div>
        </div>
        <div style={{ width: mm(18), height: 1, backgroundColor: '#bbb', margin: '2px 0' }} />
        <div style={{ textAlign: 'center', fontWeight: 'bold' }}>
          <div style={{ fontSize: pt(6.5), color: '#555' }}>Res. SlyC N&deg;</div>
          <div style={{ fontSize: pt(7.5), color: '#000' }}>{data.resolucion || '438/2024'}</div>
        </div>
      </div>

      {/* Footer */}
      <Hline y={FOOTER_Y} />
      <div style={{ position: 'absolute', top: FOOTER_Y + 2, left: MX, width: LW, height: mm(5), display: 'flex', alignItems: 'center', fontFamily: '"Arial Black", Arial, sans-serif', fontSize: pt(9.5), fontWeight: 900 }}>
        {data.descripcion || familyId.toUpperCase()}
      </div>
      {[
        { label: 'MODELO', val: data.modelo },
        { label: 'MARCA COMERCIAL', val: data.marca },
        { label: 'ORIGEN', val: data.origen },
      ].map(({ label, val }, i) => (
        <div key={label} style={{ position: 'absolute', top: FOOTER_Y + 2 + mm(5) + i * mm(3.8), left: MX, width: LW, height: mm(3.8), display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: pt(6.5), fontWeight: 'bold' }}>
          <span>{label}</span>
          <span style={{ fontWeight: 900 }}>{val || '—'}</span>
        </div>
      ))}
    </div>
  );
}

// ── DISPACHER PRINCIPAL ──────────────────────────────────────────────────────

export default function EtiquetaEE({ familyId, data, id = "label-export" }: Props) {
  // Normalizar datos
  const normalizedData: EtiquetaData = {
    ...data,
    // Asegurar que 'eficiencia' esté en mayúsculas y sea válida (fallback a A)
    eficiencia: (data.eficiencia || data.clase_ee || 'A').toUpperCase().trim(),
    referenciaIram: data.referenciaIram || data.norma_base || '',
    resolucion: data.resolucion || 'Res. 438/24'
  };

  if (familyId === 'hornos') {
    normalizedData.consumoConvencional = data.consumoConvencional || data.consumo_ciclo || '';
    normalizedData.consumoForzada = data.consumoForzada || data.consumo_forzada || '';
    normalizedData.volumen = data.volumen || data.vol_util || '';
    normalizedData.consumoEspera = data.consumoEspera || data.consumo_espera || '';
    return <TemplateHorno data={normalizedData} id={id} />;
  } else if (familyId === 'lavavajillas') {
    normalizedData.consumoEnergia = data.consumoEnergia || data.consumo_ciclo || '';
    normalizedData.consumoAgua = data.consumoAgua || data.agua_ciclo || '';
    normalizedData.eficaciaSecado = data.eficaciaSecado || data.clase_secado || '';
    normalizedData.consumoEspera = data.consumoEspera || data.consumo_espera || '';
    return <TemplateLavavajillas data={normalizedData} id={id} />;
  } else {
    // Fallback dinámico genérico para las otras 9 familias
    return <TemplateGeneric data={normalizedData} familyId={familyId} id={id} />;
  }
}
