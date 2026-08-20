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

const fmtComma = (val: any, fallback = ''): string => {
  if (val === undefined || val === null || val === '') return fallback ? String(fallback).replace(/\./g, ',') : '';
  const str = String(val).trim();
  return str.replace(/(\d+)\.(\d+)/g, '$1,$2');
};

// ── COMPONENTE TEMPLATE: HORNO ELÉCTRICO ───────────────────────────────────

function TemplateHorno({ data, id = "label-export" }: { data: EtiquetaData; id?: string }) {
  const FS6 = 8;
  const FS7 = 9;
  const FS8 = 11;
  const FS10 = 13;
  const FS11 = 15;
  const FS12 = 16;

  const BLUE = '#2E3092';
  const GREEN = '#009640';
  const GRAY_BG = '#eae9ea';
  const COLORS_MAP: Record<string, string> = {
    A: '#009640', B: '#52AE32', C: '#C8D400',
    D: '#FFED00', E: '#FBBA00', F: '#EC6608', G: '#E3001B',
  };

  const selIdx = LETTERS.indexOf(data.eficiencia);
  const W = mm(116);
  const H = mm(195);
  const MX = mm(2);
  const LW = W - 2 * MX;

  const HDR_T = MX;
  const HDR_H = mm(8);

  const LINE1_Y = mm(12);
  const ARR_BLOCK_H = mm(85);
  const LINE2_Y = LINE1_Y + ARR_BLOCK_H;
  const ARR_H = mm(10);
  const ARR_GAP = mm(1);
  const LBL_AREA = Math.round(4.5 * MM);
  const IND_W = mm(39);
  const IND_H = mm(17);
  const IND_TRI = mm(8);
  const ARR_TIP = mm(5);
  const ARROW_WIDTHS_MM: Record<string, number> = {
    A: 22, B: 27.5, C: 33, D: 38.5, E: 44, F: 49.5, G: 55,
  };

  const BAR_TOP = LINE2_Y + 1 + mm(1);
  const BAR_H = mm(20);

  const CARACT_TOP = BAR_TOP + BAR_H;
  const CARACT_TITLE_H = mm(6);
  const ROW_H = mm(13);

  const ROWS_TOP = CARACT_TOP + CARACT_TITLE_H;
  const ROW1_T = ROWS_TOP;
  const ROW2_T = ROW1_T + ROW_H;
  const ROW3_T = ROW2_T + ROW_H;
  const ROW4_T = ROW3_T + ROW_H;

  const FOOTER_SEP_Y = ROW4_T + ROW_H;
  const FOOTER_T = FOOTER_SEP_Y + 1;

  const LEFT_COL_W = mm(50);
  const LEFT_COL_R = MX + LEFT_COL_W;

  const SEP_X = MX + mm(1);
  const SEP_W = LEFT_COL_W - mm(2);

  const LBL_X = MX + 4;
  const ICON_CX = MX + mm(23);
  const VAL_X = MX + mm(35);
  const VAL_W = LEFT_COL_W - mm(35) - 2;

  const RIGHT_COL_X = LEFT_COL_R;
  const QR_SZ = mm(26);
  const QR_LEFT = MX + LW - QR_SZ - 2;
  const TEXT_COL_X = RIGHT_COL_X + 4;
  const TEXT_COL_W = QR_LEFT - RIGHT_COL_X - 10;
  const THREE_ROW_H = ROW_H * 3;
  const QR_TOP = ROWS_TOP + Math.round((THREE_ROW_H - QR_SZ) / 2);

  const BAR_LH = 20;
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
        const aTop = LINE1_Y + 1 + LBL_AREA + i * (ARR_H + ARR_GAP);
        const aW = mm(ARROW_WIDTHS_MM[letter]);
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
        const cy = LINE1_Y + 1 + LBL_AREA + safeSelIdx * (ARR_H + ARR_GAP) + Math.round(ARR_H / 2);
        const indTop = cy - Math.round(IND_H / 2);
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
      {(() => {
        const safeSelIdx = selIdx >= 0 ? selIdx : 0;
        const consumptionColor = COLORS_MAP[LETTERS[safeSelIdx]] || COLORS_MAP[data.eficiencia] || GREEN;
        return (
          <div style={{ position: 'absolute', top: BAR_TOP, left: MX, width: LW, height: BAR_H, backgroundColor: consumptionColor }} />
        );
      })()}
      {['CONSUMO DE', 'ENERG\u00CDA EN MODO', 'CONVENCIONAL'].map((txt, i) => (
        <div key={i} style={{ position: 'absolute', top: BAR_TEXT_TOP + i * BAR_LH, left: MX + mm(2), height: BAR_LH, display: 'flex', alignItems: 'center', fontWeight: 700, fontSize: FS12, color: '#000' }}>{txt}</div>
      ))}
      <div style={{ position: 'absolute', top: BAR_TOP, left: MX + mm(45), width: LW - mm(45) - 4, height: BAR_H, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '5px' }}>
        <span style={{ fontWeight: 700, fontSize: 58, color: '#000' }}>{fmtComma(data.consumoConvencional, '0,00')}</span>
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
        const iconSz = mm(8);
        const iconTop = vc(ROW1_T, ROW_H, iconSz);
        const iconLeft = ICON_CX - Math.round(iconSz / 2);
        return (
          <>
            <div style={{ position: 'absolute', top: lbTop, left: LBL_X, fontSize: FS6, lineHeight: lhMult, color: '#000', fontWeight: 'bold' }}>VOLUMEN DE<br />LA CAVIDAD</div>
            <img src="/icons/volumen-cavidad.png" alt="Oven" style={{ position: 'absolute', top: iconTop, left: iconLeft, width: iconSz, height: iconSz, objectFit: 'contain' }} />
            <div style={{ position: 'absolute', top: ROW1_T, left: VAL_X, width: VAL_W, height: ROW_H, display: 'flex', alignItems: 'center', fontWeight: 700, fontSize: FS10, color: '#000' }}>
              {fmtComma(data.volumen, '0')} <span style={{ fontWeight: 400, fontSize: FS6, marginLeft: 3 }}>lts</span>
            </div>
          </>
        );
      })()}
      <Hline y={ROW2_T} />

      {/* ROW 2 */}
      {(() => {
        const lbTop = vc(ROW2_T, ROW_H, FS6 * 3 * lhMult);
        const iconSz = mm(8);
        const iconTop = vc(ROW2_T, ROW_H, iconSz);
        const iconLeft = ICON_CX - Math.round(iconSz / 2);
        const valTop = ROW2_T + Math.round((ROW_H - (FS10 + FS6)) / 2);
        return (
          <>
            <div style={{ position: 'absolute', top: lbTop, left: LBL_X, fontSize: FS6, lineHeight: lhMult, color: '#000', fontWeight: 'bold' }}>CONSUMO<br />DE ENERG&Iacute;A<br />CONVENCIONAL</div>
            <img src="/icons/consumo-convencional.png" alt="Meter" style={{ position: 'absolute', top: iconTop, left: iconLeft, width: iconSz, height: iconSz, objectFit: 'contain' }} />
            <div style={{ position: 'absolute', top: valTop, left: VAL_X, width: VAL_W, fontWeight: 700, fontSize: FS10, color: '#000', lineHeight: 1 }}>{fmtComma(data.consumoConvencional, '0,00')}</div>
            <div style={{ position: 'absolute', top: valTop + FS10 + 2, left: VAL_X, width: VAL_W, fontSize: FS6, color: '#000', lineHeight: 1 }}>kWh/ciclo</div>
          </>
        );
      })()}
      <Hline y={ROW3_T} />

      {/* ROW 3 */}
      {(() => {
        const lbTop = vc(ROW3_T, ROW_H, FS6 * 4 * lhMult);
        const iconSz = mm(8);
        const iconTop = vc(ROW3_T, ROW_H, iconSz);
        const iconLeft = ICON_CX - Math.round(iconSz / 2);
        const valTop = ROW3_T + Math.round((ROW_H - (FS10 + FS6)) / 2);
        return (
          <>
            <div style={{ position: 'absolute', top: lbTop, left: LBL_X, fontSize: FS6, lineHeight: lhMult, color: '#000', fontWeight: 'bold' }}>CONSUMO<br />DE ENERG&Iacute;A<br />CONVENCIONAL<br />FORZADA</div>
            <img src="/icons/consumo-forzada.png" alt="Gauge" style={{ position: 'absolute', top: iconTop, left: iconLeft, width: iconSz, height: iconSz, objectFit: 'contain' }} />
            <div style={{ position: 'absolute', top: valTop, left: VAL_X, width: VAL_W, fontWeight: 700, fontSize: FS10, color: '#000', lineHeight: 1 }}>{fmtComma(data.consumoForzada, '0,00')}</div>
            <div style={{ position: 'absolute', top: valTop + FS10 + 2, left: VAL_X, width: VAL_W, fontSize: FS6, color: '#000', lineHeight: 1 }}>kWh/ciclo</div>
          </>
        );
      })()}
      <Hline y={ROW4_T} />

      {/* ROW 4 */}
      {(() => {
        const lbTop = vc(ROW4_T, ROW_H, FS6 * 2 * lhMult);
        const clsLineH = FS6 + 3;
        const clsTop = ROW4_T + Math.round((ROW_H - clsLineH * 3) / 2);
        const clsColX = LEFT_COL_R - mm(17);
        const arrowW = mm(4);
        const arrowX = clsColX - arrowW - 2;

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
              const sz = mm(5);
              const pTop = ROW4_T + Math.round((ROW_H - sz) / 2);
              const pLft = MX + LW - mm(20);
              return (
                <img src="/icons/consumo-espera.png" alt="Standby" style={{ position: 'absolute', top: pTop, left: pLft, width: sz, height: sz, objectFit: 'contain' }} />
              );
            })()}
            <div style={{ position: 'absolute', top: ROW4_T, left: MX + LW - mm(13), width: mm(13), height: ROW_H, display: 'flex', alignItems: 'center', fontWeight: 700, fontSize: FS8, color: '#000' }}>
              {fmtComma(data.consumoEspera, '0,00')}w
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
      <div style={{
        position: 'absolute',
        top: ROWS_TOP,
        left: TEXT_COL_X,
        width: TEXT_COL_W,
        height: THREE_ROW_H,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        fontWeight: 700,
        color: '#000',
        boxSizing: 'border-box'
      }}>
        <div style={{ fontSize: FS10, lineHeight: 1.15 }}>Referencia IRAM</div>
        <div style={{ fontSize: FS10, lineHeight: 1.15, whiteSpace: 'pre-line' }}>
          {data.referenciaIram || '62414-1/2'}
        </div>
        <div style={{ width: '80%', height: '1px', backgroundColor: '#999', margin: '4px 0' }} />
        <div style={{ fontSize: FS10, lineHeight: 1.15 }}>Res. SIyC N&deg;</div>
        <div style={{ fontSize: FS10, lineHeight: 1.15 }}>
          {data.resolucion || '438/24'}
        </div>
      </div>

      <Hline y={FOOTER_SEP_Y} x={MX} w={LW} />

      {/* 5. FOOTER */}
      <div style={{ position: 'absolute', top: FOOTER_T + 4, left: MX, width: LW, height: mm(5), display: 'flex', alignItems: 'center', fontFamily: '"Arial Black", Arial, sans-serif', fontSize: FS11, fontWeight: 900, textTransform: 'uppercase' }}>
        {(data.descripcion || 'HORNO ELÉCTRICO').toUpperCase()}
      </div>
      {[
        { label: 'MODELO', val: data.modelo },
        { label: 'MARCA COMERCIAL', val: data.marca },
        { label: 'ORIGEN', val: data.origen },
      ].map(({ label, val }, i) => (
        <div key={label} style={{ position: 'absolute', top: FOOTER_T + 4 + mm(5) + i * mm(3.8), left: MX, width: LW, height: mm(3.8), display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: FS7, fontWeight: 'bold' }}>
          <span>{label}</span>
          <span style={{ fontWeight: 900 }}>{(val || '—').toUpperCase()}</span>
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
          <span style={{ color: '#fff' }}>{text}</span>
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
          <div style={{ position: 'absolute', top: mm(5.5 + (selectedIndex * (11.5 + 1.41))) + (mm(11.5 - 20) / 2), right: 0, width: mm(46), height: mm(20), display: 'flex' }}>
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

        {/* BLOCK 3: Energía (Color dinámico según la clase de eficiencia) */}
        <div style={{ position: 'absolute', top: yEnergia, left: 0, width: '100%', height: H_ENERGIA, backgroundColor: COLORS[selectedIndex] || '#009640', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', padding: `0 ${mm(4)}px ${mm(2.5)}px ${mm(4)}px` }}>
          <div style={{ fontSize: pt(14), fontWeight: 'bold', lineHeight: '16pt', color: '#000', paddingBottom: mm(1) }}>
            CONSUMO<br />DE ENERGÍA<br />POR CICLO
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline' }}>
            <span style={{ fontSize: pt(60), fontWeight: 'bold', color: '#000', lineHeight: '0.8' }}>{fmtComma(data.consumoEnergia, '0,00')}</span>
            <span style={{ fontSize: pt(16), marginLeft: mm(1), color: '#000' }}>kWh</span>
          </div>
        </div>

        {/* BLOCK 4: Agua */}
        <div style={{ position: 'absolute', top: yAgua, left: 0, width: '100%', height: H_AGUA, backgroundColor: bgGrisClaro }}>
          <div style={{ position: 'absolute', top: mm(2), left: mm(4), fontSize: pt(10), fontWeight: 'bold', lineHeight: '1.1', color: '#27348b' }}>
            CONSUMO<br />DE AGUA<br />POR CICLO
          </div>
          <img src="/icons/agua.png" style={{ position: 'absolute', left: mm(25), top: mm(2.5), height: mm(12.5) }} alt="agua" />

          {/* Water Slider Line */}
          <div style={{ position: 'absolute', bottom: mm(4), right: mm(4), width: mm(63), height: mm(10) }}>

            {/* Slider Top Values (Dynamic Triangle) */}
            <div style={{ position: 'absolute', left: `${sliderPct}%`, bottom: mm(5), transform: 'translateX(-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'baseline', whiteSpace: 'nowrap' }}>
                <span style={{ fontFamily: 'Arial', fontWeight: 'bold', fontSize: pt(12) }}>{fmtComma(data.consumoAgua, '0')}</span>
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
              <div style={{ width: mm(18), fontSize: pt(6), lineHeight: '1.2', fontWeight: 'bold' }}>EFICACIA<br />DE SECADO</div>
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
              <div style={{ width: mm(18), fontSize: pt(6), lineHeight: '1.2', fontWeight: 'bold' }}>CAPACIDAD<br />DECLARADA</div>
              <div style={{ width: mm(12), display: 'flex', justifyContent: 'center' }}>
                <img src="/icons/capacidad.png" style={{ height: mm(8) }} alt="capacidad" />
              </div>
              <div style={{ width: mm(22), display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start' }}>
                <span style={{ fontSize: pt(10), fontFamily: '"Arial Black", Arial', lineHeight: 1, fontWeight: 'bold' }}>{fmtComma(data.capacidad, '0')}</span>
                <span style={{ fontSize: pt(5), fontFamily: 'Arial' }}>Cubiertos</span>
              </div>
              <div style={{ position: 'absolute', bottom: 0, left: mm(2), width: mm(53), height: `${lineW}px`, backgroundColor: '#000' }} />
            </div>

            {/* Ruido */}
            <div style={{ position: 'absolute', top: mm(30), left: 0, width: '100%', height: mm(15), display: 'flex', alignItems: 'center', paddingLeft: mm(2) }}>
              <div style={{ width: mm(18), fontSize: pt(6), lineHeight: '1.2', fontWeight: 'bold' }}>NIVEL<br />DE RUIDO</div>
              <div style={{ width: mm(12), display: 'flex', justifyContent: 'center' }}>
                <img src="/icons/ruido.png" style={{ height: mm(8) }} alt="ruido" />
              </div>
              <div style={{ width: mm(22), display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start' }}>
                <span style={{ fontSize: pt(10), fontFamily: '"Arial Black", Arial', lineHeight: 1, fontWeight: 'bold' }}>{fmtComma(data.ruido, '0')}</span>
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
                  <span style={{ fontSize: pt(8), fontFamily: '"Arial Black", Arial', fontWeight: 'bold' }}>ESPACIO<br />CODIGO QR</span>
                )}
              </div>
            </div>

          </div>

          {/* Consumo Espera */}
          <div style={{ position: 'absolute', left: mm(57), top: mm(35), width: mm(55), height: mm(10), backgroundColor: bgGrisClaro, display: 'flex', alignItems: 'center', justifyContent: 'center', paddingRight: mm(1) }}>
            <span style={{ fontSize: pt(8), fontWeight: 'bold', whiteSpace: 'nowrap', fontFamily: 'Arial' }}>CONSUMO EN ESPERA</span>
            <img src="/icons/espera.png" style={{ height: mm(6), marginLeft: mm(1), marginRight: mm(1) }} alt="standby" />
            <span style={{ fontSize: pt(8), fontFamily: '"Arial Black", Arial', fontWeight: 'bold' }}>{fmtComma(data.consumoEspera, '0,00')}W</span>
          </div>

        </div>

        <div style={{ position: 'absolute', top: yFooter, left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />

        {/* Footer */}
        <div style={{ position: 'absolute', top: yFooter + mm(2), left: 0, width: '100%', height: H_FOOTER - mm(2), display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: pt(12), fontWeight: 900, fontFamily: '"Arial Black", Arial', marginBottom: mm(1), textTransform: 'uppercase' }}>
            {(data.descripcion || 'LAVAVAJILLAS').toUpperCase()}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>MODELO</span>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>{(data.modelo || '').toUpperCase()}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>MARCA COMERCIAL</span>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>{(data.marca || '').toUpperCase()}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>ORIGEN</span>
              <span style={{ fontSize: pt(7), fontWeight: 'bold' }}>{(data.origen || '').toUpperCase()}</span>
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
      <div style={{ position: 'absolute', top: BAR_TOP, left: MX, width: LW, height: BAR_H, backgroundColor: COLORS[selIdx] || '#52AE32', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: `0 ${mm(3)}px` }} />
      <div style={{ position: 'absolute', top: BAR_TOP, left: MX + mm(3), height: BAR_H, display: 'flex', flexDirection: 'column', justifyContent: 'center', fontSize: pt(7.5), fontWeight: 'bold', color: '#000' }}>
        <span>CONSUMO</span>
        <span>DE ENERG&Iacute;A</span>
      </div>
      <div style={{ position: 'absolute', top: BAR_TOP, right: MX + mm(3), height: BAR_H, display: 'flex', alignItems: 'baseline', justifyContent: 'flex-end', gap: '3px' }}>
        <span style={{ fontWeight: 900, fontSize: pt(36), color: '#000', lineHeight: 0.8 }}>
          {fmtComma(data.consumo_anual || data.consumo_ciclo || data.consumo_encendido, '0,00')}
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
              {fmtComma(val)}
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
      <div style={{ position: 'absolute', top: FOOTER_Y + 2, left: MX, width: LW, height: mm(5), display: 'flex', alignItems: 'center', fontFamily: '"Arial Black", Arial, sans-serif', fontSize: pt(9.5), fontWeight: 900, textTransform: 'uppercase' }}>
        {(data.descripcion || familyId || 'PRODUCTO').toUpperCase()}
      </div>
      {[
        { label: 'MODELO', val: data.modelo },
        { label: 'MARCA COMERCIAL', val: data.marca },
        { label: 'ORIGEN', val: data.origen },
      ].map(({ label, val }, i) => (
        <div key={label} style={{ position: 'absolute', top: FOOTER_Y + 2 + mm(5) + i * mm(3.8), left: MX, width: LW, height: mm(3.8), display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: pt(6.5), fontWeight: 'bold' }}>
          <span>{label}</span>
          <span style={{ fontWeight: 900 }}>{(val || '—').toUpperCase()}</span>
        </div>
      ))}
    </div>
  );
}

// ── COMPONENTE TEMPLATE: LAVARROPAS ELÉCTRICOS (IRAM 2141-3) ────────────────

function TemplateLavarropas({ data, id = "label-export" }: { data: EtiquetaData; id?: string }) {
  const scale = 3.78;
  const mm = (val: number) => val * scale;
  const pt = (val: number) => val * 1.333 * (scale / 3.78);

  const outerW = mm(124);
  const outerH = mm(212);
  const lineW = mm(0.5);

  const m = mm(2);
  const innerW = outerW - m * 2;
  const innerH = outerH - m * 2;

  const H_CABEZAL = mm(11.5);
  const H_ESCALA = mm(98);
  const H_ENERGIA = mm(24);

  const yCabezal = 0;
  const yEscala = yCabezal + H_CABEZAL;
  const yEnergia = yEscala + H_ESCALA;
  const yCaract = yEnergia + H_ENERGIA;

  const bgGrisClaro = '#eae9ea';

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
          <span style={{ color: '#fff' }}>{text}</span>
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
  const ribbonWidths = [31.5, 36.3, 41.1, 45.9, 50.7, 55.5, 60.3];

  const consumoCiclo = fmtComma(data.consumoCiclo || data.consumo_ciclo || data.consumoEnergia, '0,26');
  const capacidad = fmtComma(data.capacidad || data.capacidad_carga, '7,5');
  const claseCentrifugado = (data.claseCentrifugado || data.clase_centrifugado || data.eficaciaCentrifugado || 'B').toUpperCase();
  const aguaCiclo = fmtComma(data.aguaCiclo || data.agua_ciclo || data.consumoAgua, '62');
  const rpmMax = fmtComma(data.rpmMax || data.rpm_max || data.velocidadCentrifugado, '1200');
  const duracionCiclo = fmtComma(data.duracionCiclo || data.duracion_ciclo || data.duracion, '235');
  const consumoEspera = fmtComma(data.consumoEspera || data.consumo_espera, '0,50');
  const nivelRuido = fmtComma(data.ruido || data.nivel_ruido || data.ruido_centrifugado, '74');

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
      <div style={{ position: 'absolute', top: m, left: m, width: innerW, height: innerH, boxSizing: 'border-box' }}>

        {/* BLOCK 1: Cabezal */}
        <div style={{ position: 'absolute', top: yCabezal, left: 0, width: '100%', height: mm(11.5) }}>
          <div style={{ backgroundColor: '#21337B', height: mm(10), width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#fff', fontFamily: '"Arial Black", Arial, sans-serif', fontSize: pt(14), fontWeight: 900, letterSpacing: '0.5px' }}>
              EFICIENCIA ENERGÉTICA
            </span>
          </div>
          <div style={{ position: 'absolute', top: mm(11), left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />
        </div>

        {/* BLOCK 2: Escala A-G */}
        <div style={{ position: 'absolute', top: yEscala, left: 0, width: '100%', height: H_ESCALA }}>
          <div style={{ position: 'absolute', top: mm(1.5), left: 0, fontSize: pt(6), fontWeight: 'bold' }}>MÁS EFICIENTE</div>
          <div style={{ position: 'absolute', bottom: mm(1.5), left: 0, fontSize: pt(6), fontWeight: 'bold' }}>MENOS EFICIENTE</div>

          <div style={{ position: 'absolute', top: mm(6.5), left: 0, width: '100%' }}>
            {LETTERS.map((label, i) => {
              const h = 11.2;
              const gap = 1.2;
              return (
                <div key={label} style={{ position: 'absolute', top: mm(i * (h + gap)), left: 0 }}>
                  {renderRibbon(COLORS[i], ribbonWidths[i], mm(h), label)}
                </div>
              );
            })}
          </div>

          {/* Indicator Arrow */}
          {(() => {
            const ribbonH = 11.2;
            const ribbonGap = 1.2;
            const topInicial = 6.5;
            const selTop = topInicial + selectedIndex * (ribbonH + ribbonGap);
            const selCenter = selTop + ribbonH / 2;
            const indH = 20;
            const indTop = selCenter - indH / 2;
            return (
              <div style={{ position: 'absolute', top: mm(indTop), right: 0, width: mm(46), height: mm(indH), display: 'flex' }}>
                <div style={{
                  width: 0,
                  height: 0,
                  borderTop: `${mm(indH / 2)}px solid transparent`,
                  borderBottom: `${mm(indH / 2)}px solid transparent`,
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
            );
          })()}

          <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />
        </div>

        {/* BLOCK 3: Consumo de Energía por Ciclo */}
        <div style={{ position: 'absolute', top: yEnergia, left: 0, width: '100%', height: mm(25) }}>
          <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: mm(1), backgroundColor: '#fff' }} />
          <div style={{ position: 'absolute', top: mm(1), left: 0, width: '100%', height: mm(24), backgroundColor: COLORS[selectedIndex] || '#009640', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: `0 ${mm(3)}px`, boxSizing: 'border-box' }}>
            <div style={{ fontSize: pt(13), fontWeight: 'bold', lineHeight: '15pt', color: '#000' }}>
              CONSUMO DE ENERGÍA<br />POR CICLO
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline' }}>
              <span style={{ fontSize: pt(56), fontWeight: 'bold', color: '#000', lineHeight: '0.8' }}>{consumoCiclo}</span>
              <span style={{ fontSize: pt(15), marginLeft: mm(1), color: '#000', fontWeight: 'bold' }}>kWh</span>
            </div>
          </div>
        </div>

        {/* BLOCK 4: Grid de Características específicas de Lavarropas */}
        <div style={{ position: 'absolute', top: yEnergia + mm(25), left: 0, width: '100%', height: mm(51), backgroundColor: '#fff' }}>
          {/* LADO IZQUIERDO: Tarjeta gris con íconos (54 mm de ancho) */}
          <div style={{ position: 'absolute', left: 0, top: 0, width: mm(54), height: mm(51), backgroundColor: bgGrisClaro, borderRight: `${lineW * 1.5}px solid #fff`, boxSizing: 'border-box' }}>
            
            {/* Fila 1: Consumo Agua */}
            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: mm(12.75), display: 'flex', alignItems: 'center', paddingLeft: mm(2), paddingRight: mm(2), justifyContent: 'space-between' }}>
              <div style={{ fontSize: pt(5.5), fontWeight: 'bold', lineHeight: '7pt' }}>
                CONSUMO DE AGUA<br />POR CICLO
              </div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <svg width={mm(6)} height={mm(7)} viewBox="0 0 24 24" fill="#000" style={{ marginRight: mm(1) }}>
                  <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
                </svg>
                <span style={{ fontSize: pt(13), fontWeight: 'bold' }}>{aguaCiclo}</span>
                <span style={{ fontSize: pt(7), marginLeft: 2, fontWeight: 'bold' }}>lts</span>
              </div>
            </div>

            <div style={{ position: 'absolute', top: mm(12.75), left: mm(2), width: mm(50), height: `${lineW}px`, backgroundColor: '#000' }} />

            {/* Fila 2: Capacidad */}
            <div style={{ position: 'absolute', top: mm(12.75), left: 0, width: '100%', height: mm(12.75), display: 'flex', alignItems: 'center', paddingLeft: mm(2), paddingRight: mm(2), justifyContent: 'space-between' }}>
              <div style={{ fontSize: pt(5.5), fontWeight: 'bold', lineHeight: '7pt' }}>
                CAPACIDAD<br />DEL LAVARROPAS
              </div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <svg width={mm(6)} height={mm(7)} viewBox="0 0 24 24" fill="#000" style={{ marginRight: mm(1) }}>
                  <path d="M6 2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm6 4a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6z" />
                </svg>
                <span style={{ fontSize: pt(13), fontWeight: 'bold' }}>{capacidad}</span>
                <span style={{ fontSize: pt(7), marginLeft: 2, fontWeight: 'bold' }}>Kg</span>
              </div>
            </div>

            <div style={{ position: 'absolute', top: mm(25.5), left: mm(2), width: mm(50), height: `${lineW}px`, backgroundColor: '#000' }} />

            {/* Fila 3: Duración */}
            <div style={{ position: 'absolute', top: mm(25.5), left: 0, width: '100%', height: mm(12.75), display: 'flex', alignItems: 'center', paddingLeft: mm(2), paddingRight: mm(2), justifyContent: 'space-between' }}>
              <div style={{ fontSize: pt(5.5), fontWeight: 'bold', lineHeight: '7pt' }}>
                DURACIÓN
              </div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <svg width={mm(6)} height={mm(6)} viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: mm(1) }}>
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <span style={{ fontSize: pt(13), fontWeight: 'bold' }}>{duracionCiclo}</span>
                <span style={{ fontSize: pt(7), marginLeft: 2, fontWeight: 'bold' }}>min</span>
              </div>
            </div>

            <div style={{ position: 'absolute', top: mm(38.25), left: mm(2), width: mm(50), height: `${lineW}px`, backgroundColor: '#000' }} />

            {/* Fila 4: Ruido */}
            <div style={{ position: 'absolute', top: mm(38.25), left: 0, width: '100%', height: mm(12.75), display: 'flex', alignItems: 'center', paddingLeft: mm(2), paddingRight: mm(2), justifyContent: 'space-between' }}>
              <div style={{ fontSize: pt(5.5), fontWeight: 'bold', lineHeight: '7pt' }}>
                NIVEL<br />DE RUIDO
              </div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <svg width={mm(6)} height={mm(6)} viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="2" style={{ marginRight: mm(1) }}>
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="#000" />
                  <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                </svg>
                <span style={{ fontSize: pt(13), fontWeight: 'bold' }}>{nivelRuido}</span>
                <span style={{ fontSize: pt(5.5), marginLeft: 2, fontWeight: 'bold', lineHeight: '6pt' }}>dB(A)<br />re 1 pW</span>
              </div>
            </div>

          </div>

          {/* LADO DERECHO: Especificaciones Técnicas secundarias */}
          <div style={{ position: 'absolute', left: mm(54), top: 0, width: mm(66), height: mm(51), backgroundColor: '#fff', paddingLeft: mm(2), paddingRight: mm(2), boxSizing: 'border-box' }}>
            
            {/* Centrifugado & Eficacia */}
            <div style={{ height: mm(12.75), borderBottom: `${lineW}px solid #000`, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <div style={{ fontSize: pt(5), fontWeight: 'bold', letterSpacing: '0.2px' }}>CENTRIFUGADO</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 1 }}>
                <span style={{ fontSize: pt(4.5), fontWeight: 'bold' }}>CLASE DE EFICACIA</span>
                <div style={{ display: 'flex', gap: 1 }}>
                  {LETTERS.map(l => (
                    <span key={l} style={{
                      fontSize: pt(6.5),
                      fontWeight: 'bold',
                      padding: '0 1px',
                      backgroundColor: l === claseCentrifugado ? '#000' : 'transparent',
                      color: l === claseCentrifugado ? '#fff' : '#000',
                      borderRadius: 1
                    }}>{l}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Velocidad máxima */}
            <div style={{ height: mm(12.75), borderBottom: `${lineW}px solid #000`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: pt(5.5), fontWeight: 'bold', lineHeight: '7pt' }}>
                VELOCIDAD<br />MÁXIMA
              </div>
              <div style={{ fontSize: pt(12), fontWeight: 'bold' }}>
                {rpmMax} <span style={{ fontSize: pt(7), fontWeight: 'normal' }}>rpm</span>
              </div>
            </div>

            {/* Consumo en espera */}
            <div style={{ height: mm(12.75), borderBottom: `${lineW}px solid #000`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: pt(5), fontWeight: 'bold', lineHeight: '6.5pt' }}>
                CONSUMO EN ESPERA
              </div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <svg width={mm(4.5)} height={mm(4.5)} viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="2.5" strokeLinecap="round" style={{ marginRight: mm(1) }}>
                  <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
                  <line x1="12" y1="2" x2="12" y2="12" />
                </svg>
                <span style={{ fontSize: pt(11), fontWeight: 'bold' }}>{consumoEspera}</span>
                <span style={{ fontSize: pt(7), marginLeft: 1, fontWeight: 'bold' }}>W</span>
              </div>
            </div>

            {/* Normas e IRAM */}
            <div style={{ height: mm(12.75), display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: pt(5), fontWeight: 'bold', lineHeight: '6.5pt' }}>
                IRAM 2141-3<br />
                IRAM 62301<br />
                Res. SIyC N° 438/24
              </div>
              <div style={{ width: mm(14), height: mm(11), border: '1px solid #999', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: pt(4), color: '#666', textAlign: 'center' }}>
                CÓDIGO QR
              </div>
            </div>

          </div>

        </div>

        {/* BLOCK 5: Footer / Modelo / Origen */}
        <div style={{ position: 'absolute', top: yCaract + mm(51), left: 0, width: '100%', height: mm(13) }}>
          <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', paddingTop: mm(1.5) }}>
            <div style={{ fontSize: pt(12), fontFamily: '"Arial Black", Arial, sans-serif', fontWeight: 900, textTransform: 'uppercase' }}>
              {(data.descripcion || 'LAVARROPAS').toUpperCase()}
            </div>

            <div style={{ fontSize: pt(6.5), textAlign: 'right', lineHeight: '8.5pt' }}>
              <div>MODELO <span style={{ fontWeight: 'bold', marginLeft: mm(2) }}>{(data.modelo || 'GAD-WM80').toUpperCase()}</span></div>
              <div>MARCA COMERCIAL <span style={{ fontWeight: 'bold', marginLeft: mm(2) }}>{(data.marca || 'GADNIC').toUpperCase()}</span></div>
              <div>ORIGEN <span style={{ fontWeight: 'bold', marginLeft: mm(2) }}>{(data.origen || 'CHINA').toUpperCase()}</span></div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

// ── COMPONENTE TEMPLATE: REFRIGERADORES Y CONGELADORES (IRAM 2404-3) ────────

function TemplateRefrigeradores({ data, id = "label-export" }: { data: EtiquetaData; id?: string }) {
  const scale = 3.78;
  const mm = (val: number) => val * scale;
  const pt = (val: number) => val * 1.333 * (scale / 3.78);

  // Global Dimensions: 124 mm width x 212 mm height (según Hoja 3 IRAM 2404-3)
  const outerW = mm(124);
  const outerH = mm(212);
  const lineW = mm(0.5); // Líneas divisoras de 0,5 mm exactos según plano Hoja 3

  // Inner margins: 2 mm
  const m = mm(2);
  const innerW = outerW - m * 2; // 120 mm
  const innerH = outerH - m * 2; // 208 mm

  const H_CABEZAL = mm(11.5);
  const H_ESCALA = mm(98);
  const H_ENERGIA = mm(24);

  const yCabezal = 0;
  const yEscala = yCabezal + H_CABEZAL;
  const yEnergia = yEscala + H_ESCALA;
  const yCaract = yEnergia + H_ENERGIA;

  const bgGrisClaro = '#eae9ea';

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
          <span style={{ color: '#fff' }}>{text}</span>
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

  const volFrescos = fmtComma(data.vol_frescos || data.volFrescos || data.volumen_frescos, '274');
  const volCongelados = fmtComma(data.vol_congelados || data.volCongelados || data.volumen_congelados, '168');
  const consumoAnual = fmtComma(data.consumo_anual || data.consumoAnual || data.consumo_energia, '308');
  const nivelRuido = fmtComma(data.ruido || data.nivelRuido || data.nivel_ruido, '36');
  const claseClimatica = data.clase_climatica || data.claseClimatica || 'T';
  const consumoEspera = fmtComma(data.consumo_espera || data.consumoEspera, '0,28');

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
      {/* Inner Container: 120x208 mm (2mm margin all around) */}
      <div style={{ position: 'absolute', top: m, left: m, width: innerW, height: innerH, boxSizing: 'border-box' }}>

        {/* BLOCK 1: Cabezal */}
        <div style={{ position: 'absolute', top: yCabezal, left: 0, width: '100%', height: mm(11.5) }}>
          <div style={{ backgroundColor: '#21337B', height: mm(10), width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#fff', fontFamily: '"Arial Black", Arial, sans-serif', fontSize: pt(14), fontWeight: 900, letterSpacing: '0.5px' }}>
              EFICIENCIA ENERGÉTICA
            </span>
          </div>
          {/* Línea negra 1mm debajo del recuadro azul */}
          <div style={{ position: 'absolute', top: mm(11), left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />
        </div>

        {/* BLOCK 2: Escala A-G (98 mm entre línea superior e inferior) */}
        <div style={{ position: 'absolute', top: yEscala, left: 0, width: '100%', height: H_ESCALA }}>
          <div style={{ position: 'absolute', top: mm(1.5), left: 0, fontSize: pt(6), fontWeight: 'bold', fontFamily: 'Arial, sans-serif' }}>
            MÁS EFICIENTE
          </div>
          <div style={{ position: 'absolute', bottom: mm(1.5), left: 0, fontSize: pt(6), fontWeight: 'bold', fontFamily: 'Arial, sans-serif' }}>
            MENOS EFICIENTE
          </div>

          <div style={{ position: 'absolute', top: mm(6.5), left: 0, width: '100%' }}>
            {LETTERS.map((label, i) => {
              const h = 11.2;
              const gap = 1.2;
              return (
                <div key={label} style={{ position: 'absolute', top: mm(i * (h + gap)), left: 0 }}>
                  {renderRibbon(COLORS[i], ribbonWidths[i], mm(h), label)}
                </div>
              );
            })}
          </div>

          {/* Black Indicator Arrow (centrado verticalmente con la bandera seleccionada) */}
          {(() => {
            const ribbonH = 11.2;
            const ribbonGap = 1.2;
            const topInicial = 6.5;
            const selTop = topInicial + selectedIndex * (ribbonH + ribbonGap);
            const selCenter = selTop + ribbonH / 2;
            const indH = 20;
            const indTop = selCenter - indH / 2;
            return (
              <div style={{ position: 'absolute', top: mm(indTop), right: 0, width: mm(46), height: mm(indH), display: 'flex' }}>
                <div style={{
                  width: 0,
                  height: 0,
                  borderTop: `${mm(indH / 2)}px solid transparent`,
                  borderBottom: `${mm(indH / 2)}px solid transparent`,
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
            );
          })()}

          {/* Línea negra horizontal de 0.5mm que separa la escala del bloque de consumo */}
          <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />
        </div>

        {/* BLOCK 3: Consumo de Energía (24 mm de alto con 1 mm de gap superior, SIN línea negra abajo) */}
        <div style={{ position: 'absolute', top: yEnergia, left: 0, width: '100%', height: mm(25) }}>
          {/* Espacio en blanco de 1mm */}
          <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: mm(1), backgroundColor: '#fff' }} />

          {/* Recuadro de consumo dinámico según la clase de eficiencia energética (Res. 438/2024 Anexo I Pág. 10) */}
          <div style={{ position: 'absolute', top: mm(1), left: 0, width: '100%', height: mm(24), backgroundColor: COLORS[selectedIndex] || '#009640', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: `0 ${mm(3)}px`, boxSizing: 'border-box' }}>
            <div style={{ fontSize: pt(14), fontWeight: 'bold', lineHeight: '16pt', color: '#000' }}>
              CONSUMO<br />DE ENERGÍA
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline' }}>
              <span style={{ fontSize: pt(60), fontWeight: 'bold', color: '#000', lineHeight: '0.8' }}>{consumoAnual}</span>
              <span style={{ fontSize: pt(16), marginLeft: mm(1), color: '#000', fontWeight: 'normal' }}>kWh/año</span>
            </div>
          </div>
        </div>

        {/* BLOCK 4: Características (51 mm de alto total, pegado directamente debajo del recuadro verde) */}
        <div style={{ position: 'absolute', top: yEnergia + mm(25), left: 0, width: '100%', height: mm(51), backgroundColor: '#fff' }}>

          {/* Columna Izquierda (54 mm de ancho, fondo gris `#eae9ea` ÍNTEGRO de 51 mm de alto, con borde blanco a la derecha) */}
          <div style={{ position: 'absolute', left: 0, top: 0, width: mm(54), height: mm(51), backgroundColor: bgGrisClaro, borderRight: `${lineW * 1.5}px solid #fff`, boxSizing: 'border-box' }}>

            {/* Fila 0: Título CARACTERÍSTICAS (11pt bold) + Clase Climática T (21pt bold) - Alto 12.75 mm */}
            <div style={{ position: 'absolute', top: 0, left: mm(2), width: mm(50), height: mm(12.75), display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxSizing: 'border-box' }}>
              <span style={{ fontSize: pt(11), fontWeight: 'bold', color: '#27348b' }}>CARACTERÍSTICAS</span>
              <span style={{ fontSize: pt(21), fontWeight: 'bold', fontFamily: 'Arial, sans-serif', color: '#000' }}>{claseClimatica}</span>
            </div>
            {/* Línea 1: Debajo de CARACTERÍSTICAS T (arranca a 3 mm del borde izquierdo) */}
            <div style={{ position: 'absolute', top: mm(12.75), left: mm(3), width: mm(48), height: `${lineW}px`, backgroundColor: '#000' }} />

            {/* Fila 1: Alimentos Frescos - Alto 12.75 mm */}
            <div style={{ position: 'absolute', top: mm(12.75), left: mm(3), width: mm(48), height: mm(12.75), display: 'flex', alignItems: 'center', boxSizing: 'border-box' }}>
              <div style={{ width: mm(19), fontSize: pt(6.2), lineHeight: '1.1', fontFamily: 'Arial, sans-serif' }}>
                VOLUMEN<br />ALIMENTOS<br />FRESCOS
              </div>
              {/* Ícono 1: Cartón de Leche 3D (Centrado) */}
              <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <img src="/icons/frescos_icon.png" alt="frescos" style={{ height: mm(9.5), objectFit: 'contain' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'flex-end', gap: '1px' }}>
                <span style={{ fontSize: pt(10), fontWeight: 'bold' }}>{volFrescos}</span>
                <span style={{ fontSize: pt(8) }}>lts</span>
              </div>
            </div>
            {/* Línea 2: Entre Frescos y Congelados (arranca a 3 mm del borde izquierdo, grosor lineW = 0.5 mm) */}
            <div style={{ position: 'absolute', top: mm(25.5), left: mm(3), width: mm(48), height: `${lineW}px`, backgroundColor: '#000' }} />

            {/* Fila 2: Alimentos Congelados - Alto 12.75 mm */}
            <div style={{ position: 'absolute', top: mm(25.5), left: mm(3), width: mm(48), height: mm(12.75), display: 'flex', alignItems: 'center', boxSizing: 'border-box' }}>
              <div style={{ width: mm(19), fontSize: pt(6.2), lineHeight: '1.1', fontFamily: 'Arial, sans-serif' }}>
                VOLUMEN<br />ALIMENTOS<br />CONGELADOS
              </div>
              {/* Ícono 2: Copo con 4 estrellas celestes (Centrado) */}
              <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <img src="/icons/congelados_icon.png" alt="congelados" style={{ height: mm(10), objectFit: 'contain' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'flex-end', gap: '1px' }}>
                <span style={{ fontSize: pt(10), fontWeight: 'bold' }}>{volCongelados}</span>
                <span style={{ fontSize: pt(8) }}>lts</span>
              </div>
            </div>
            {/* Línea 3: Entre Congelados y Ruido (arranca a 3 mm del borde izquierdo, grosor lineW = 0.5 mm) */}
            <div style={{ position: 'absolute', top: mm(38.25), left: mm(3), width: mm(48), height: `${lineW}px`, backgroundColor: '#000' }} />

            {/* Fila 3: Ruido - Alto 12.75 mm */}
            <div style={{ position: 'absolute', top: mm(38.25), left: mm(2), width: mm(50), height: mm(12.75), display: 'flex', alignItems: 'center', boxSizing: 'border-box' }}>
              <div style={{ width: mm(19), fontSize: pt(6.2), lineHeight: '1.1', fontFamily: 'Arial, sans-serif' }}>
                RUIDO
              </div>
              {/* Ícono 3: Parlante Ruido (Centrado) */}
              <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <img src="/icons/ruido_icon.png" alt="ruido" style={{ height: mm(8.5), objectFit: 'contain' }} />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'flex-end', gap: '1px' }}>
                <span style={{ fontSize: pt(10), fontWeight: 'bold' }}>{nivelRuido}</span>
                <span style={{ fontSize: pt(8) }}>dB <sup style={{ fontSize: '5px' }}>(A)</sup></span>
              </div>
            </div>

          </div>

          {/* Columna Derecha (66 mm de ancho): Referencias + QR + Consumo en Espera */}
          <div style={{ position: 'absolute', left: mm(54), top: 0, width: mm(66), height: mm(51) }}>

            {/* Sub-bloque superior: Referencia IRAM + Res SIyC + QR */}
            <div style={{ display: 'flex', width: '100%', height: mm(38) }}>
              {/* Referencias (IRAM + Res SIyC) ambos Arial Bold 11 pt */}
              <div style={{ width: mm(38), height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: pt(11), fontWeight: 'bold', display: 'block' }}>Referencia IRAM</span>
                  <span style={{ fontSize: pt(11), fontWeight: 'bold', display: 'block' }}>{data.referenciaIram || '2404-3'}</span>
                </div>
                <div style={{ width: mm(28), height: `${lineW}px`, flexShrink: 0, backgroundColor: '#000', margin: `${mm(2)}px 0` }} />
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: pt(11), fontWeight: 'bold', display: 'block' }}>Res. SIyC N°</span>
                  <span style={{ fontSize: pt(11), fontWeight: 'bold', display: 'block' }}>{data.resolucion || '438/24'}</span>
                </div>
              </div>

              {/* Caja QR (28 mm x 28 mm exactos) */}
              <div style={{ width: mm(28), height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', paddingRight: mm(1) }}>
                <div style={{ width: mm(28), height: mm(28), border: `${lineW}px solid #000`, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', textAlign: 'center', boxSizing: 'border-box' }}>
                  {data.qrImageUrl ? (
                    <img src={data.qrImageUrl} alt="QR" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                  ) : (
                    <span style={{ fontSize: pt(8), fontWeight: 'bold', fontFamily: '"Arial Black", Arial' }}>
                      ESPACIO<br />CODIGO QR
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Línea horizontal divisora arriba de Consumo en Espera (0.5mm exactos) */}
            <div style={{ position: 'absolute', top: mm(38), left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />

            {/* Sub-bloque inferior: Consumo en Espera (fondo gris claro `#eae9ea`, 13mm de alto) */}
            <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: mm(13), backgroundColor: bgGrisClaro, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: mm(2), boxSizing: 'border-box' }}>
              <span style={{ fontSize: pt(8), fontWeight: 'bold' }}>CONSUMO EN ESPERA</span>
              {/* Ícono Botón Standby / Power */}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="2.5" strokeLinecap="round">
                <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
                <line x1="12" y1="2" x2="12" y2="12" />
              </svg>
              <div style={{ display: 'flex', alignItems: 'baseline' }}>
                <span style={{ fontSize: pt(10), fontWeight: 'bold', fontFamily: 'Arial, sans-serif' }}>{consumoEspera}</span>
                <span style={{ fontSize: pt(7), fontWeight: 'bold', fontFamily: 'Arial, sans-serif' }}>W</span>
              </div>
            </div>

          </div>

        </div>

        {/* Línea horizontal negra de 0.5mm que separa el Bloque 4 (Características) del Bloque 5 (Footer) */}
        <div style={{ position: 'absolute', top: yCaract + mm(51), left: 0, width: '100%', height: `${lineW}px`, backgroundColor: '#000' }} />

        {/* BLOCK 5: Footer (Interlineado 100% uniforme entre el título y las filas de datos) */}
        <div style={{ position: 'absolute', top: yCaract + mm(51.5), left: 0, width: '100%', bottom: mm(1.5), display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', gap: mm(1.2), paddingTop: mm(0.5), boxSizing: 'border-box' }}>
          <div style={{ fontSize: pt(12), fontWeight: 900, fontFamily: '"Arial Black", Arial, sans-serif', textTransform: 'uppercase', lineHeight: '1.1' }}>
            {(data.descripcion || data.producto_desc || 'REFRIGERADORES Y CONGELADORES').toUpperCase()}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: pt(8), fontFamily: 'Arial, sans-serif', fontWeight: 'normal' }}>MODELO</span>
            <span style={{ fontSize: pt(8), fontFamily: 'Arial, sans-serif', fontWeight: 'normal' }}>{(data.modelo || '—').toUpperCase()}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: pt(8), fontFamily: 'Arial, sans-serif', fontWeight: 'normal' }}>MARCA COMERCIAL</span>
            <span style={{ fontSize: pt(8), fontFamily: 'Arial, sans-serif', fontWeight: 'normal' }}>{(data.marca || '—').toUpperCase()}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: pt(8), fontFamily: 'Arial, sans-serif', fontWeight: 'normal' }}>ORIGEN</span>
            <span style={{ fontSize: pt(8), fontFamily: 'Arial, sans-serif', fontWeight: 'normal' }}>{(data.origen || '—').toUpperCase()}</span>
          </div>
        </div>

      </div>
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
    normalizedData.descripcion = 'HORNO ELÉCTRICO';
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
  } else if (familyId === 'lavarropas') {
    normalizedData.consumoCiclo = data.consumoCiclo || data.consumo_ciclo || data.consumoEnergia || '';
    normalizedData.capacidad = data.capacidad || data.capacidad_carga || '';
    normalizedData.claseCentrifugado = data.claseCentrifugado || data.clase_centrifugado || data.eficaciaCentrifugado || '';
    normalizedData.aguaCiclo = data.aguaCiclo || data.agua_ciclo || data.consumoAgua || '';
    normalizedData.rpmMax = data.rpmMax || data.rpm_max || data.velocidadCentrifugado || '';
    normalizedData.duracionCiclo = data.duracionCiclo || data.duracion_ciclo || data.duracion || '';
    normalizedData.consumoEspera = data.consumoEspera || data.consumo_espera || '';
    normalizedData.ruido = data.ruido || data.nivel_ruido || data.ruido_centrifugado || '';
    return <TemplateLavarropas data={normalizedData} id={id} />;
  } else if (familyId === 'refrigeradores' || familyId === 'heladeras') {
    normalizedData.consumoAnual = data.consumoAnual || data.consumo_anual || data.consumo_energia || '';
    normalizedData.volFrescos = data.volFrescos || data.vol_frescos || data.volumen_frescos || '';
    normalizedData.volCongelados = data.volCongelados || data.vol_congelados || data.volumen_congelados || '';
    normalizedData.ruido = data.ruido || data.nivel_ruido || '';
    normalizedData.estrellas = data.estrellas || '';
    normalizedData.claseClimatica = data.claseClimatica || data.clase_climatica || 'T';
    normalizedData.consumoEspera = data.consumoEspera || data.consumo_espera || '';
    return <TemplateRefrigeradores data={normalizedData} id={id} />;
  } else {
    // Fallback dinámico genérico para las otras familias
    return <TemplateGeneric data={normalizedData} familyId={familyId} id={id} />;
  }
}
