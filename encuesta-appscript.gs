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

var SHEET_NAME = 'Respuestas';

var HEADERS = [
  'Fecha/hora',
  'Empresa',
  'Nombre y apellido',
  'Área',
  'Frecuencia de uso',
  'NPS (0–10)',
  'Atención del equipo',
  'Tiempos de respuesta',
  'Resolución de consultas',
  'Acompaña necesidades',
  'Aspecto a mejorar primero',
  'Funcionalidades a incorporar',
  'Proyecto próximos 12 meses',
  'Qué valora de YiQi',
  'Qué mejorar'
];

// Debe coincidir con las claves del payload que envía el formulario.
var KEYS = [
  'fecha', 'empresa', 'nombre', 'area', 'frecuencia', 'nps',
  'atencion', 'tiempos', 'resolucion', 'acompana', 'mejora',
  'oportunidades', 'proyecto', 'valoras', 'mejorar'
];

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(30000);
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);

    if (sheet.getLastRow() === 0) {
      sheet.appendRow(HEADERS);
      sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
      sheet.setFrozenRows(1);
    }

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

// Permite verificar en el navegador que el Web App está publicado.
function doGet() {
  return json({ ok: true, service: 'Encuesta YiQi', ts: new Date().toISOString() });
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
