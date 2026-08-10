/**
 * =========================================================================
 * MÓDULO PARSER Y AUTOMATIZACIÓN DE EMAILS — VERSIÓN 1.5 (Smart Unread Scope)
 * =========================================================================
 * - v1.5: Mantiene como NO LEÍDO ÚNICAMENTE los mails de solicitudes NUEVAS (los viejos no se tocan).
 * - v1.4: Mantiene los mails como NO LEÍDOS (markUnread) en la bandeja de Federico.
 * - v1.3: Mapeo completo de 6 tipos reales (SE, Convenio, Juguetes, Puericultura, INAL RE, Ampliaciones).
 * - v1.2: Soporte para INAL Registro de Envase (RE) excluyendo Libre Circulación (LC).
 * - v1.1: Pausa automática de SLA en 'En Consulta' por falta de muestra / dudas técnicas.
 * - v1.0: Parseo de Solicitudes iniciales + Timestamp Fecha_Solicitud_Ing.
 */

const CONFIG_EMAIL_PARSER = {
  NOMBRE_HOJA_BD: 'BD_Gestiones',
  LABEL_PROCESADO: 'Certificaciones/Procesado',
  SEARCH_SOLICITUDES: 'from:david.b@bidcom.com.ar subject:"Solicitud CERTIFICADO" -label:Certificaciones/Procesado newer_than:14d',
  SEARCH_HILOS_ACTIVOS: 'label:Certificaciones/Procesado -label:Certificaciones/Cerrado newer_than:30d',
  GEMINI_API_KEY: '' // Insertar API Key de Gemini si se ejecuta vía Apps Script directo
};

/**
 * Función principal ejecutada por Trigger de tiempo (cada 5 o 10 minutos)
 */
function procesarFlujoEmailsCertificaciones() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheetBD = ss.getSheetByName(CONFIG_EMAIL_PARSER.NOMBRE_HOJA_BD);
  if (!sheetBD) return;

  let labelProc = GmailApp.getUserLabelByName(CONFIG_EMAIL_PARSER.LABEL_PROCESADO);
  if (!labelProc) labelProc = GmailApp.createLabel(CONFIG_EMAIL_PARSER.LABEL_PROCESADO);

  // 1. PROCESAR SOLICITUDES NUEVAS DE DAVID
  procesarNuevasSolicitudes_(sheetBD, labelProc);

  // 2. MONITOREAR HILOS PARA CAMBIOS DE ESTADO (Consulta, Enviado, Borrador)
  actualizarEstadosPorHilos_(sheetBD);
}

/**
 * 1. Lee solicitudes entrantes de David y las da de alta en BD_Gestiones
 */
function procesarNuevasSolicitudes_(sheetBD, labelProc) {
  const threads = GmailApp.search(CONFIG_EMAIL_PARSER.SEARCH_SOLICITUDES, 0, 10);
  if (!threads || threads.length === 0) return;

  const headers = sheetBD.getRange(2, 1, 1, sheetBD.getLastColumn()).getValues()[0];

  for (const thread of threads) {
    const msg = thread.getMessages()[0];
    const subject = msg.getSubject();
    const plainBody = msg.getPlainBody();
    const htmlBody = msg.getBody();
    const fechaEmail = msg.getDate();

    try {
      const datos = parsearEmailSolicitud_(subject, plainBody, htmlBody);
      if (!datos || !datos.id_unico) continue;

      // Verificar si ya existe en BD
      const filaExistente = buscarFilaPorID_(sheetBD, headers, datos.id_unico);

      if (filaExistente > 0) {
        // Si existe y la acción es Modificación en estado 'Por Ingresar', actualizar
        if (datos.tipo_accion === 'MODIFICACION') {
          actualizarFilaExistente_(sheetBD, headers, filaExistente, datos);
          Logger.log(`🔄 Actualizada solicitud existente: ${datos.id_unico}`);
        } else if (datos.tipo_accion === 'AMPLIACION') {
          // Crear fila con sufijo Ampliación
          datos.id_unico = `${datos.id_unico} - AMP`;
          datos.intervencion = 'Ampliacion';
          insertarNuevaFilaBD_(sheetBD, headers, datos, fechaEmail);
          Logger.log(`➕ Creada Ampliación: ${datos.id_unico}`);
        }
      } else {
        // Alta limpia normal
        insertarNuevaFilaBD_(sheetBD, headers, datos, fechaEmail);
        thread.markUnread(); // Solo marca como NO LEÍDO los mails de solicitudes NUEVAS
        Logger.log(`✅ Alta nueva creada y marcada como no leída: ${datos.id_unico}`);
      }

      thread.addLabel(labelProc);

    } catch (err) {
      Logger.log(`❌ Error procesando thread [${subject}]: ${err.message}`);
    }
  }
}

/**
 * Parsea el mail usando reglas Regex estables + IA Gemini para comentarios/intención
 */
function parsearEmailSolicitud_(subject, plainBody, htmlBody) {
  const datos = {
    id_unico: '',
    intervencion: 'Electrica',
    descripcion: '',
    sku: '',
    marca: '',
    modelos: '',
    specs: '',
    link_drive: '',
    observaciones: '',
    tipo_accion: 'ALTA_NUEVA'
  };

  // 1. Regex Parse del Asunto: "Solicitud CERTIFICADO 998 [SE] Velador de escritorio // DESKL034"
  const subjRegex = /CERTIFICADO\s+(\d+)\s*\[([^\]]+)\]\s*(.+?)\s*\/\/\s*(\S+)/i;
  const matchSubj = subject.match(subjRegex);

  if (matchSubj) {
    datos.id_unico = `CERTIFICADO ${matchSubj[1]}`;
    const rawTipo = matchSubj[2].trim().toUpperCase();
    datos.descripcion = matchSubj[3].trim();
    datos.sku = matchSubj[4].trim();

    if (rawTipo.includes('CONVENIO')) datos.intervencion = 'Convenio';
    else if (rawTipo.includes('INAL')) datos.intervencion = 'INAL';
    else if (rawTipo.includes('JUGUETE')) datos.intervencion = 'Juguetes';
    else if (rawTipo.includes('PUERICULTURA')) datos.intervencion = 'Puericultura';
    else datos.intervencion = 'Electrica';
  } else {
    // Fallback: buscar solo "CERTIFICADO XXX"
    const mAlt = subject.match(/CERTIFICADO\s+(\d+)/i);
    if (mAlt) datos.id_unico = `CERTIFICADO ${mAlt[1]}`;
  }

  // Detectar palabras de ampliación
  if (/amplia|extens/i.test(subject) || /amplia|extens/i.test(plainBody)) {
    datos.tipo_accion = 'AMPLIACION';
  }

  // 2. Extraer Link de Drive
  const driveMatch = plainBody.match(/(https:\/\/drive\.google\.com\/drive\/folders\/[^\s\>]+)/);
  if (driveMatch) {
    datos.link_drive = driveMatch[1].replace(/=3D/g, '=');
  }

  // 3. Extraer Observaciones y Comentarios clave del cuerpo
  const comentarios = [];
  const mMuestra = plainBody.match(/MUESTRA:\s*(.+)/i);
  if (mMuestra && mMuestra[1].trim()) {
    comentarios.push(`📦 Muestra: ${mMuestra[1].trim()}`);
  }

  const mManual = plainBody.match(/MANUAL:\s*(.+)/i);
  if (mManual && mManual[1].trim() && !mManual[1].toLowerCase().includes('en caja')) {
    comentarios.push(`📄 Manual: ${mManual[1].trim()}`);
  }

  if (/urgente|embarque|vuelo|viaje/i.test(plainBody)) {
    comentarios.push(`🚨 Urgente por embarque`);
  }

  datos.observaciones = comentarios.join(' | ');

  return datos;
}

/**
 * Insertar nueva fila en BD_Gestiones
 */
function insertarNuevaFilaBD_(sheetBD, headers, datos, fechaEmail) {
  const nuevaFila = new Array(headers.length).fill('');

  const setVal = (headerName, val) => {
    const idx = headers.findIndex(h => sinAcentos_(h) === sinAcentos_(headerName));
    if (idx >= 0) nuevaFila[idx] = val;
  };

  setVal('ID_Unico', datos.id_unico);
  setVal('Descripcion', datos.descripcion);
  setVal('SKU', datos.sku);
  setVal('Estado', 'Por Ingresar');
  setVal('Intervencion', datos.intervencion);
  setVal('Sector_Actual', 'Bidcom');
  setVal('Fecha_Solicitud_Ing', fechaEmail); // Timestamp original del mail de David
  setVal('Observaciones', datos.observaciones);

  sheetBD.appendRow(nuevaFila);
}

/**
 * 2. Monitorea hilos recientes para detectar cambio de estado (En Consulta, Enviado, Borrador)
 */
function actualizarEstadosPorHilos_(sheetBD) {
  const threads = GmailApp.search(CONFIG_EMAIL_PARSER.SEARCH_HILOS_ACTIVOS, 0, 15);
  if (!threads) return;

  const headers = sheetBD.getRange(2, 1, 1, sheetBD.getLastColumn()).getValues()[0];

  for (const thread of threads) {
    const lastMsg = thread.getMessages().pop(); // Último mensaje del hilo
    const body = lastMsg.getPlainBody().toLowerCase();
    const subject = thread.getFirstMessageSubject();

    const mID = subject.match(/CERTIFICADO\s+(\d+)/i);
    if (!mID) continue;
    const idUnico = `CERTIFICADO ${mID[1]}`;

    const fila = buscarFilaPorID_(sheetBD, headers, idUnico);
    if (fila <= 0) continue;

    // Detectar patrones en el último mensaje
    let nuevoEstado = '';
    let obsExtra = '';

    if (/falta\s+muestra|sin\s+muestra|muestras?\s+pendiente|consulta\s+t[eé]cnica/i.test(body)) {
      nuevoEstado = 'En Consulta';
      obsExtra = '⏸️ Pausado por consulta/falta de muestra en email';
    } else if (/borrador|revisi[oó]n\s+de\s+certificado|draft/i.test(body)) {
      nuevoEstado = 'Borrador Recibido';
      obsExtra = '📄 Borrador recibido de la certificadora';
    } else if (/muestra\s+recibida|muestra\s+en\s+jaula|consulta\s+resuelta/i.test(body)) {
      nuevoEstado = 'En Curso';
      obsExtra = '▶️ Muestra/Consulta resuelta';
    }

    if (nuevoEstado) {
      const idxEst = headers.findIndex(h => sinAcentos_(h) === 'estado');
      const idxObs = headers.findIndex(h => sinAcentos_(h) === 'observaciones');

      if (idxEst >= 0) {
        const estActual = sheetBD.getRange(fila, idxEst + 1).getValue();
        if (estActual !== nuevoEstado) {
          sheetBD.getRange(fila, idxEst + 1).setValue(nuevoEstado);
          if (idxObs >= 0) {
            const obsPrev = sheetBD.getRange(fila, idxObs + 1).getValue();
            sheetBD.getRange(fila, idxObs + 1).setValue(`${obsPrev} | ${obsExtra}`);
          }
          Logger.log(`🔄 Cambiado estado de ${idUnico} a '${nuevoEstado}' por mail`);
        }
      }
    }
  }
}

/**
 * Auxiliares de búsqueda y normalización
 */
function buscarFilaPorID_(sheetBD, headers, idUnico) {
  const idxID = headers.findIndex(h => sinAcentos_(h) === 'id_unico');
  if (idxID < 0) return -1;

  const data = sheetBD.getRange(3, idxID + 1, sheetBD.getLastRow() - 2, 1).getValues();
  const idNorm = sinAcentos_(idUnico);

  for (let i = 0; i < data.length; i++) {
    if (sinAcentos_(data[i][0]) === idNorm) {
      return i + 3; // Fila real en Sheet
    }
  }
  return -1;
}

function sinAcentos_(str) {
  return String(str || '')
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

/**
 * =========================================================================
 * FUNCION DE EXPORTACIÓN Y DIAGNÓSTICO
 * =========================================================================
 * Exporta tus etiquetas actuales de Gmail y 10 mails de ejemplo a una pestaña 
 * temporal '__Ejemplos_Gmail_Dump' en la Planilla Diaria para que el agente
 * los pueda analizar y adaptar el parser a tus etiquetas y formatos reales.
 */
function exportarEjemplosYEtiquetasGmail() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheetDump = ss.getSheetByName('__Ejemplos_Gmail_Dump');
  if (sheetDump) {
    sheetDump.clear();
  } else {
    sheetDump = ss.insertSheet('__Ejemplos_Gmail_Dump');
  }

  // 1. OBTENER TODAS TUS ETIQUETAS ACTUALES DE GMAIL
  const allLabels = GmailApp.getUserLabels().map(l => l.getName());
  sheetDump.getRange(1, 1).setValue("=== ETIQUETAS ACTUALES DE GMAIL ===").setFontWeight("bold");
  sheetDump.getRange(2, 1, Math.max(allLabels.length, 1), 1).setValues(
    allLabels.length > 0 ? allLabels.map(l => [l]) : [["(No se encontraron etiquetas personalizadas)"]]
  );

  // 2. BUSCAR 10 MAILS RECIENTES REPRESENTATIVOS
  const rowStart = allLabels.length + 4;
  sheetDump.getRange(rowStart, 1).setValue("=== EJEMPLOS DE MAILS ENCONTRADOS ===").setFontWeight("bold");
  
  const headers = ["Fecha", "Remitente", "Asunto", "Etiquetas_Aplicadas", "Cuerpo_Texto"];
  sheetDump.getRange(rowStart + 1, 1, 1, headers.length).setValues([headers]).setFontWeight("bold");

  const threads = GmailApp.search('from:david.b@bidcom.com.ar OR subject:CERTIFICADO OR subject:Solicitud OR subject:Ampliacion OR subject:Borrador OR subject:INAL OR subject:Lenor OR subject:Qetkra', 0, 15);
  const rowsDump = [];

  for (const thread of threads) {
    const threadLabels = thread.getLabels().map(l => l.getName()).join(', ');
    const msgs = thread.getMessages();
    for (const msg of msgs) {
      rowsDump.push([
        msg.getDate(),
        msg.getFrom(),
        msg.getSubject(),
        threadLabels,
        msg.getPlainBody() // Cuerpo de texto completo sin cortar
      ]);
    }
  }

  if (rowsDump.length > 0) {
    sheetDump.getRange(rowStart + 2, 1, rowsDump.length, headers.length).setValues(rowsDump);
  }

  SpreadsheetApp.getUi().alert(`✅ Diagnóstico finalizado:\n- ${allLabels.length} etiquetas encontradas.\n- ${rowsDump.length} mensajes exportados a la pestaña '__Ejemplos_Gmail_Dump'.`);
}

/**
 * EXPORTADOR ESPECÍFICO DE LOS ÚLTIMOS 30 TRÁMITES NO-INAL EN BD_GESTIONES
 * Busca en Gmail los mails exactos que dispararon el alta de los últimos 30 trámites
 * de Seguridad Eléctrica, Convenio, Juguetes y Puericultura (excluyendo INAL).
 */
function exportarMailsExactosDeBD() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheetBD = ss.getSheetByName('BD_Gestiones');
  if (!sheetBD) return;

  let sheetDump = ss.getSheetByName('__Ejemplos_Gmail_Dump');
  if (sheetDump) {
    sheetDump.clear();
  } else {
    sheetDump = ss.insertSheet('__Ejemplos_Gmail_Dump');
  }

  const dataBD = sheetBD.getRange(3, 1, sheetBD.getLastRow() - 2, sheetBD.getLastColumn()).getValues();
  const headersBD = sheetBD.getRange(2, 1, 1, sheetBD.getLastColumn()).getValues()[0];

  const idxID = headersBD.findIndex(h => sinAcentos_(h) === 'id_unico');
  const idxInterv = headersBD.findIndex(h => sinAcentos_(h) === 'intervencion');
  const idxSubInterv = headersBD.findIndex(h => sinAcentos_(h) === 'sub_intervencion');
  const idxSKU = headersBD.findIndex(h => sinAcentos_(h) === 'sku');
  const idxDesc = headersBD.findIndex(h => sinAcentos_(h) === 'descripcion');

  // Filtrar últimos 30 trámites (SE, Convenio, Juguetes, Puericultura e INAL RE)
  const idsSeleccionados = [];
  for (let i = dataBD.length - 1; i >= 0; i--) {
    const idVal = String(dataBD[i][idxID] || '').trim();
    const intervVal = String(dataBD[i][idxInterv] || '').trim().toLowerCase();
    const subIntervVal = idxSubInterv >= 0 ? String(dataBD[i][idxSubInterv] || '').trim().toLowerCase() : '';

    if (!idVal || idVal === 'None' || idVal.length < 3) continue;

    // Si es INAL, incluir SOLO si es Registro de Envase (RE / Envase)
    if (intervVal.includes('inal')) {
      if (!subIntervVal.includes('re') && !subIntervVal.includes('envase')) {
        continue; // Excluir Libre Circulacion (LC)
      }
    }

    idsSeleccionados.push({
      id: idVal,
      sku: dataBD[i][idxSKU],
      desc: dataBD[i][idxDesc],
      intervencion: dataBD[i][idxInterv],
      sub_intervencion: idxSubInterv >= 0 ? dataBD[i][idxSubInterv] : ''
    });

    if (idsSeleccionados.length >= 30) break;
  }

  // Encabezados en el dump
  const headers = ["ID_Unico_BD", "Intervencion_BD", "Sub_Intervencion_BD", "Fecha_Email", "Remitente", "Asunto", "Etiquetas_Aplicadas", "Cuerpo_Texto_Completo"];
  sheetDump.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight("bold");

  const rowsDump = [];

  for (const item of idsSeleccionados) {
    // Extraer número si existe, ej: "CERTIFICADO 998" -> "998"
    const numMatch = item.id.match(/\d+/);
    const queryBusqueda = numMatch ? `subject:"${numMatch[0]}" OR subject:"${item.id}"` : `subject:"${item.id}"`;

    const threads = GmailApp.search(queryBusqueda, 0, 2);
    let encontrado = false;

    if (threads && threads.length > 0) {
      for (const thread of threads) {
        const threadLabels = thread.getLabels().map(l => l.getName()).join(', ');
        const msgs = thread.getMessages();
        for (const msg of msgs) {
          rowsDump.push([
            item.id,
            item.intervencion,
            item.sub_intervencion,
            msg.getDate(),
            msg.getFrom(),
            msg.getSubject(),
            threadLabels,
            msg.getPlainBody()
          ]);
          encontrado = true;
        }
      }
    }

    if (!encontrado) {
      rowsDump.push([
        item.id,
        item.intervencion,
        item.sub_intervencion,
        "-",
        "-",
        "(No se encontró mail en Gmail)",
        "-",
        `SKU: ${item.sku} | Desc: ${item.desc}`
      ]);
    }
  }

  if (rowsDump.length > 0) {
    sheetDump.getRange(2, 1, rowsDump.length, headers.length).setValues(rowsDump);
  }

  SpreadsheetApp.getUi().alert(`✅ Escaneo de trámites finalizado:\n- ${idsSeleccionados.length} trámites (SE, Convenio, Juguetes, Puericultura e INAL RE) analizados de BD_Gestiones.\n- ${rowsDump.length} mensajes/registros exportados a '__Ejemplos_Gmail_Dump'.`);
}


