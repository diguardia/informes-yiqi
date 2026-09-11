// Genera Claude/RESUMEN-MES-AAAA-MM.md desde el objeto RESUMEN_MES de
// comercial.html. Una sola fuente: el HTML. El markdown agrega lo que la
// pagina no muestra —la fuente de cada frente— para que cualquier linea se
// pueda fundamentar sin volver a buscar.
//
//   node scripts/resumen-mes-md.mjs ago [ruta/salida.md]
//
// Sin ruta, escribe en ../../RESUMEN-MES-<anio>-<mes>.md relativo a este
// repo (Documents/Claude/).

import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const aqui = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(resolve(aqui, '..', 'comercial.html'), 'utf8');

const ini = html.indexOf('const RESUMEN_MES = {');
const fin = html.indexOf('\n    };', ini);
if (ini < 0 || fin < 0) throw new Error('No encuentro RESUMEN_MES en comercial.html');
const RESUMEN_MES = new Function(html.slice(ini, fin + 7).replace('const RESUMEN_MES =', 'return') + ';')();

const MESES = { ene:['2026','01','Enero'], feb:['2026','02','Febrero'], mar:['2026','03','Marzo'], abr:['2026','04','Abril'],
  may:['2026','05','Mayo'], jun:['2026','06','Junio'], jul:['2026','07','Julio'], ago:['2026','08','Agosto'],
  sep:['2026','09','Septiembre'], oct:['2026','10','Octubre'], nov:['2026','11','Noviembre'], dic:['2026','12','Diciembre'] };

/* Fuente de cada frente, en el orden de sus lineas. Esto es lo que el HTML
   no tiene y lo que hace que el md valga como registro. Se completa a mano
   cada mes, junto con RESUMEN_MES. */
const FUENTES = {
  ago: {
    'Cifras': [
      'Inversión, alcance, impresiones y conversaciones: `data/meta.json`, mes `ago` (generado 2026-09-10).',
      'ONs y concretadas: exports del CRM `Nuevas_ONs_Detalle_639247202487266257.xlsx` y `ONs_Concretadas_DETALLE_639247234485819268.xlsx`, ambos del 07/09.',
      'Presencia digital 5,4 → 7,0: `claude/Diagnostico-digital-YiQi-ago2026.md` (05/08, promedio 5,4) y `claude/Diagnostico-digital-YiQi-sep2026.md` (08/09, promedio 7,0), mismo prompt y nueve dimensiones, siete aplicables.',
      'Piezas: 16 historias (CREATIVOS/Stories Marketplace, D01–D16) + 20 capturas (15 Analytics Pro en `www.yiqi/img/apps`, 5 Tiendanube en WORK/CAMPAÑA/Tiendanube) + 7 Open Graph (`www.yiqi/img/og-*.jpg`) + 9 anuncios (3 láminas + 3 KV del carrusel, 3 historias de Ayuda ERP). Conteo propio.',
    ],
    'Pauta': [
      'Registro de actividad de la cuenta 370211010327709 (Meta Ads, `ads_account_get_activity_logs`, 10/08–10/09): pausas del 10–11/08, targeting y estado del retargeting, presupuestos del 18/08, alta del carrusel.',
      'Costo por conversación $952 → $680: `claude/Meta-foto-jun-sep-2026-y-base-de-datos.md`, verificado por API el 10/09.',
      'Píxel, preguntas frecuentes y saludo de Instagram: bitácora de cambios en `comercial.html#resumen`, asientos del 11/08; `claude/Activacion-dialogo-mensajes-IG-ago2026.md`.',
    ],
    'Piezas': [
      'CREATIVOS/Stories Marketplace: archivos `2026-08-10_D01` a `2026-08-31_D16`.',
      'CREATIVOS/carrusel costo real: 3 láminas jpg + `AD · Placa KV 4_5` ×3.',
      '`www.yiqi/img/apps/yiqi-analytics-pro-02..15.webp` + hero, commits de agosto; WORK/CAMPAÑA/BLENDER/Analytics Pro: 5 `.blend`.',
      '`www.yiqi/img/og-*.jpg`: home, drubbit, interbanking, sell2ship, shopify, tiendanube, tornado.',
      'CREATIVOS/Ayuda ERP: 3 historias + `mailchimp/ayuda-hero-centro-1200x600.jpg`.',
      '`www.yiqi/system/icons`: logo 100×65 en dos versiones, 24 archivos en LOGOS CLIENTES; commit "optimizar los 54 SVG: -67 KB" del 14/08.',
    ],
    'Campaña en frío': [
      'Grilla de Planificación (Google Sheet), semana del 17/08: "Campaña en frío: inicio de proyecto".',
      '`www.yiqi`: `leads/LEEME.md` creado el 21/08 (hoy `captacion/LEEME.md`), con token por lead, registro de aperturas y aviso por Discord.',
      '`claude/PROMPT-landing-captacion.md`, 21/08.',
    ],
    'Sitio': [
      '34 páginas: `git log --since=2026-08-01 --until=2026-09-01 -- "*.html"` en `www.yiqi`.',
      'Precotizador: bitácora del 11/08 (píxel) y commit "publicar tiendanube y sumar precotizador al sitemap" del 14/08.',
      'Rediagnóstico: `claude/Rediagnostico-sitio-yiqi-14ago2026.md`; auditoría SEO, inventario de CTAs e informe de peso: docs `ago2026` del proyecto (12/08 y 05/08).',
      'Title, 301 y sitemap: commits del 14/08; `fb:app_id`: commit del 21/08.',
      'Clarity: commit `da28928` del 19/08 (`components/clarity.js` en la landing de Tiendanube); 11 de 12 páginas según `claude/Diagnostico-digital-YiQi-sep2026.md`; datos de sesión en el rediagnóstico del 14/08.',
      'Popup y toast: `components/app-promo-popup.js` (28/08), "un aviso por sesión" (31/08), `components/novedad-toast.js`.',
      'Páginas nuevas: `git log --diff-filter=A` de agosto: `app-tiendanube.html`, `shopify.html`, `eco-alcance.html`, `staging-partners.html`, `en-construccion.html`.',
    ],
    'El sitio por dentro': [
      'Export del Dashboard de Microsoft Clarity, proyecto YiQi, rango 01/08–31/08/2026, bajado el 11/09 (`Clarity_YiQi_Dashboard_09112026 12 09 PM.csv`).',
      'Los bloques Navegadores y Sistemas operativos del export suman 156 sesiones —quedaron en "últimos 3 días"— y no se usan.',
      'Home = yiqi.com.ar/ (2.410) + www (92) + index.html (53). Sesiones nuevas: 2.184 / 2.839 = 76,9 %.',
    ],
    'Ayuda y novedades': [
      'Commits en `www.yiqi`: "docu" (06/08, `ayuda-docusaurus.html`), "Unifica las dos landings de ayuda en ayuda-erp.html" (11/08), "nov" (07/08) y los dos `fix(novedades)` del 24/08.',
      'Email: WORK/CAMPAÑA/Emails/ENVIADOS/producto/email-nueva-ayuda.html.',
    ],
    'Alianzas': [
      '`claude/Lanzamiento-app-Tiendanube-ago2026.md` (21/08) y `claude/Checklist-homologacion-TN-appID185.md` (19/08).',
      'WORK/CAMPAÑA/Tiendanube: diagrama de integración (mmd/svg/png/html), Capturas-ficha-Tiendanube, `Lanzamiento_Tiendanube_2026-08.pdf`.',
      '`claude/Auditoria-paginas-partners-ago2026.md` (12/08).',
    ],
    'Marketplace e iA Ready': [
      'Analytics Pro: `claude/Brief-capturas-Analytics-Pro.md` (06/08), `Capturas-Analytics-Pro-ago2026.md` (13/08), `Campana-Analytics-Pro-ago2026.md` (25/08), `Guion-locucion-Analytics-Pro-iAready-ago2026.md` (28/08).',
      'Video: 007 DISEÑO/CAMPAÑAS/iAready/Video iAready — guion, guion fonético y dos mp3 de ElevenLabs del 31/08.',
      'Convocatoria a desarrolladores: commits de `www.yiqi` del 21/08 — "feat: /homologador con destino provisorio" y "fix(api-docs): alinea la barra de busqueda y suma el homologador". `Cargar mi caso` (embed de Tally) queda en `api-docs.html`.',
      'Mails con el homologador y «Cargar mi caso»: WORK/CAMPAÑA/Emails/ENVIADOS/producto/email-api-nueva-en-produccion.html (05/08) y ENVIADOS/iaready/email-iaready-resumen-04.html (20/08).',
      'Seguimientos: grilla de Planificación, semanas del 17/08 al 31/08.',
      '`claude/Marketplace-decisiones-abiertas-ago2026.md` (21/08).',
      'Shopealo: WORK/CAMPAÑA/Consultoria iA Ready/Clientes/Shopealo.',
    ],
    'Consultoría iA Ready': [
      '`REF-CONSULTORIA-IAREADY.md`; WORK/CAMPAÑA/Consultoria iA Ready/Sesiones: `2026-08-04 · S03` y `2026-08-18 · S04`.',
      'Correos: Emails/ENVIADOS/iaready — encuentros 3, 4 (con recordatorio) y 5, resúmenes 03 y 04.',
      'Mensajes de Instagram y Facebook: declaración de Seba. Sin registro que lo cuente.',
    ],
    'Design System': [
      '`yiqi-imagen/version.json`: 1.2.7.9 al 31/07, 1.2.8.28 al 31/08; 26 valores distintos de `ds_version` en los commits de agosto.',
      '`claude/Auditoria-DS-YiQi-ago2026.md` (11/08), `Criterios-botones-DS-ago2026.md` (19/08), `Sesion-DS-tablero-20ago2026.md`, `DS-btn-solid-y-defecto-accent-ink-ago2026.md` (21/08).',
    ],
    'Emails': [
      'WORK/CAMPAÑA/Emails/ENVIADOS (12 con fecha de agosto), POR-ENVIAR (2), TEMPLATES (4).',
      'Hibernando: WORK/ON HIBERNANDO/emails (4 piezas, 29/07), `Hibernando_639220379563353162.xlsx` (11/08), grilla del 24/08 "Emails hibernadores".',
    ],
    'Informes': [
      '`informes-yiqi`: commits del 03/08 (tokens desde el CDN), 05/08 (trimestres, navegación mobile), 11/08 (bitácora).',
      '`yiqi-panel-gerencial`: commit del 10/08 "facturación neta y variación real contra el período anterior".',
      '`YiQi_Informe_Ingenieria_202608.html` en `informes-yiqi`.',
      '`claude/Precios-competencia-ERP-Argentina-ago2026.md` y `Estimacion-precios-ERP-opacos-ago2026.md` (12/08); WORK/COMPETENCIA: `Battlecards_competencia_2026-08-25.pdf`, `Objecion_precio_2026-08.pdf`.',
    ],
    'Comercial': [
      'Exports del CRM del 07/09 (ver Cifras): 16 ONs nuevas y 3 concretadas por $8.524.082,10 en agosto; mayor monto mensual de 2026.',
      '`claude/Buyer-YiQi-evidencia-transcripciones-ago2026.md` (25/08), `Objecion-precio-valor-del-tiempo-ago2026.md` (13/08), `Textuales-costeo-para-citar-ago2026.md` (28/08), `Reunion-Vende-mas-Julieta-28ago2026.md`.',
      'WORK/LEADS: Sonido Electrosistem, TOTOM, MACPropiedades, FerreteriaLincoln (agosto).',
    ],
    'Lo que hay que decidir': [
      'Circuito de cobro: `claude/Marketplace-decisiones-abiertas-ago2026.md`, sección A. La pregunta de Federico Vara por "tarifa mensual y liquidación de revenue" está en el hilo de Gmail con Andrés.',
      'Firmar antes de publicar: `www.yiqi/components/apps-data.js` (`vantig-ai` prov Vantig, `rentabilidad-ml` prov metroblanc); grilla de Planificación del 07/09 "Ver nda y acuerdo comercial - JP"; respuesta de Federico Vara del 10/09: "la gente de Dentalab está haciendo pruebas ya".',
    ],
  },
};

const key = process.argv[2] || 'ago';
const d = RESUMEN_MES[key];
if (!d) throw new Error(`RESUMEN_MES.${key} no existe o está vacío`);
const [anio, mm, nombre] = MESES[key];
const F = FUENTES[key] || {};

const L = [];
L.push(`# Resumen del mes — ${nombre} ${anio}`);
L.push('');
L.push(`Generado desde \`RESUMEN_MES.${key}\` de \`informes-yiqi/comercial.html\` con \`scripts/resumen-mes-md.mjs\`.`);
L.push('El HTML es la fuente del contenido; este archivo agrega la fuente de cada frente. Si algo cambia, se edita en el HTML y se vuelve a generar.');
L.push('');
L.push('## El mes en números');
L.push('');
L.push('| Cifra | Valor | Nota |'); L.push('|---|---|---|');
for (const k of d.kpis) L.push(`| ${k.l} | **${k.v}** | ${k.d || ''} |`);
if (F['Cifras']) { L.push(''); L.push('Fuentes:'); for (const f of F['Cifras']) L.push(`- ${f}`); }
L.push(''); L.push('## Tres cosas que hay que saber'); L.push('');
d.claves.forEach((c, i) => L.push(`${i + 1}. ${c}`));
L.push(''); L.push('## Por frente');
for (const f of d.frentes) {
  L.push(''); L.push(`### ${f.n}${f.href ? ` — ${f.href}` : ''}`); L.push('');
  for (const it of f.items) L.push(`- ${it.t}${it.href ? ` — ${it.href}` : ''}`);
  if (F[f.n]) { L.push(''); L.push('Fuentes:'); for (const s of F[f.n]) L.push(`- ${s}`); }
}
L.push(''); L.push('## Lo que corre todos los meses'); L.push('');
for (const r of d.recurrente) L.push(`- **${r.t}** · ${r.d}`);
if (d.decidir && d.decidir.length) {
  L.push(''); L.push('## Lo que hay que decidir'); L.push('');
  d.decidir.forEach((x, i) => L.push(`${i + 1}. ${x.t}${x.href ? ` — ${x.href}` : ''}`));
  if (F['Lo que hay que decidir']) { L.push(''); L.push('Fuentes:'); for (const s of F['Lo que hay que decidir']) L.push(`- ${s}`); }
}
L.push(''); L.push('## Qué sigue'); L.push('');
d.sigue.forEach((s, i) => L.push(`${i + 1}. ${s}`));
L.push('');

const salida = process.argv[3] || resolve(aqui, '..', '..', '..', `RESUMEN-MES-${anio}-${mm}.md`);
writeFileSync(salida, L.join('\n'), 'utf8');
console.log(`${salida} · ${L.length} líneas`);
