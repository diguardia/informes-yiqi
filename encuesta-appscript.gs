/**
 * Encuesta de Experiencia YiQi — puente Formulario → Google Sheet
 * Pegar este código en: Extensiones → Apps Script del Sheet de respuestas.
 * Sheet destino: https://docs.google.com/spreadsheets/d/1lZU_j6U_ke1gDfcvRmn4-Mx-Fvoxj3osWWRXrk3j54E/edit
 *
 * Deploy: Implementar → Nueva implementación → Aplicación web
 *   - Ejecutar como: Yo
 *   - Quién tiene acceso: Cualquiera
 * Copiar la URL (termina en /exec) y pegarla en SHEET_ENDPOINT del HTML del formulario.
 */

// Versión del script — abrí la URL /exec para ver cuál está publicada.
var VERSION = '2026-07-13 · 19 columnas';

// ID de la planilla de respuestas (de la URL del Sheet).
var SHEET_ID = '1lZU_j6U_ke1gDfcvRmn4-Mx-Fvoxj3osWWRXrk3j54E';
var SHEET_NAME = 'Respuestas';

// Devuelve la pestaña de respuestas (la crea si no existe) y SE AUTO-CORRIGE los
// encabezados: si la fila 1 no coincide con HEADERS, la reescribe. Así el orden
// de columnas siempre coincide con la versión publicada, sin borrar la hoja.
function getSheet_() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  var needHeader = sheet.getLastRow() === 0;
  if (!needHeader) {
    var cur = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
    for (var i = 0; i < HEADERS.length; i++) {
      if (String(cur[i]) !== HEADERS[i]) { needHeader = true; break; }
    }
  }
  if (needHeader) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

// Corré ESTA función desde el editor (Ejecutar) para probar la escritura
// sin depender del formulario. Debe autorizar y crear una fila de prueba.
function pruebaEscritura() {
  var sheet = getSheet_();
  sheet.appendRow(KEYS.map(function (k) {
    return k === 'fecha' ? new Date() : 'PRUEBA';
  }));
}

var HEADERS = [
  'Fecha/hora',
  'Empresa',
  'Nombre y apellido',
  'Email',
  'Área',
  'Área — Otra (especificar)',
  'Frecuencia de uso',
  'NPS (0–10)',
  'Atención del equipo',
  'Tiempos de respuesta',
  'Resolución de consultas',
  'Acompaña necesidades',
  'Aspecto a mejorar primero',
  'Aspecto a mejorar — Otro (especificar)',
  'Funcionalidades a incorporar',
  'Funcionalidades — Otra (especificar)',
  'Proyecto próximos 12 meses',
  'Qué valora de YiQi',
  'Qué mejorar'
];

// Debe coincidir con las claves del payload que envía el formulario.
var KEYS = [
  'fecha', 'empresa', 'nombre', 'email', 'area', 'area_otro', 'frecuencia', 'nps',
  'atencion', 'tiempos', 'resolucion', 'acompana', 'mejora', 'mejora_otro',
  'oportunidades', 'oportunidades_otro', 'proyecto', 'valoras', 'mejorar'
];

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(30000);
  try {
    var sheet = getSheet_();

    var data = JSON.parse(e.postData.contents);
    if (data.fecha) { data.fecha = new Date(data.fecha); }

    var row = KEYS.map(function (k) { return data[k] !== undefined ? data[k] : ''; });
    sheet.appendRow(row);

    return json({ ok: true });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

// Abrí esta URL /exec en el navegador para verificar QUÉ versión está publicada.
// Si "version" no dice "19 columnas", lo que deployaste NO es este archivo.
function doGet() {
  return json({ ok: true, service: 'Encuesta YiQi', version: VERSION, columnas: HEADERS.length, ts: new Date().toISOString() });
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
