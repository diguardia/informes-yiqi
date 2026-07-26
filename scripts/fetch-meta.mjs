#!/usr/bin/env node
/**
 * Trae los datos de Meta Ads que alimentan el informe comercial y los deja
 * en data/meta.json, con números crudos. El formato, los deltas y los
 * colores los resuelve comercial.html: acá no se decide presentación.
 *
 * Variables de entorno:
 *   META_TOKEN          (obligatoria) token de System User de Business Manager
 *   META_AD_ACCOUNT_ID  id numérico de la cuenta, sin el prefijo act_
 *   META_API_VERSION    versión de la Graph API (por defecto v25.0)
 *   META_ANIO           año en curso a traer (por defecto, el año actual)
 *   META_ANIOS_ATRAS    cuántos años anteriores traer además (por defecto 1)
 *
 * Sin dependencias: usa el fetch nativo de Node 18+.
 */

import { writeFile, mkdir } from 'node:fs/promises';
import { dirname } from 'node:path';

const TOKEN   = process.env.META_TOKEN;
const ACCOUNT = (process.env.META_AD_ACCOUNT_ID || '370211010327709').replace(/^act_/, '');
const VERSION = process.env.META_API_VERSION || 'v25.0';
const ANIO    = Number(process.env.META_ANIO || new Date().getFullYear());
const ATRAS   = Math.max(0, Number(process.env.META_ANIOS_ATRAS ?? 1));
const OUT     = 'data/meta.json';

const CLAVES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

// Tipos de acción de la Marketing API que nos interesan.
const A_CONV  = 'onsite_conversion.messaging_conversation_started_7d';
const A_CLIC  = 'link_click';
const A_ENG   = 'page_engagement';
const A_LEAD  = 'lead';
const A_LEADG = 'onsite_conversion.lead_grouped';

if (!TOKEN) {
  console.error('Falta META_TOKEN. Cargalo como secreto del repositorio.');
  process.exit(1);
}

const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const accion = (acciones, tipo) => {
  const a = (acciones || []).find(x => x.action_type === tipo);
  return a ? Math.round(Number(a.value) || 0) : 0;
};

async function insights(params) {
  let url = `https://graph.facebook.com/${VERSION}/act_${ACCOUNT}/insights?` +
    new URLSearchParams({ limit: '500', access_token: TOKEN, ...params });
  const filas = [];
  for (let pagina = 0; url && pagina < 40; pagina++) {
    const res = await fetch(url);
    const body = await res.json();
    if (body.error) {
      throw new Error(`Graph API ${body.error.code}/${body.error.error_subcode ?? '-'}: ${body.error.message}`);
    }
    filas.push(...(body.data || []));
    url = body.paging?.next || null;
  }
  return filas;
}

/**
 * Resultado principal de una campaña según su objetivo, para la columna
 * "Resultado" de la tabla de anuncios.
 */
function resultadoDe(objetivo, acciones) {
  const conv = accion(acciones, A_CONV);
  const clic = accion(acciones, A_CLIC);
  const lead = accion(acciones, A_LEAD) || accion(acciones, A_LEADG);

  const porObjetivo = {
    MESSAGES:           ['conversaciones', conv],
    OUTCOME_ENGAGEMENT: ['conversaciones', conv],
    LINK_CLICKS:        ['clics',          clic],
    OUTCOME_TRAFFIC:    ['clics',          clic],
    LEAD_GENERATION:    ['leads',          lead],
    OUTCOME_LEADS:      ['leads',          lead],
  };
  let [tipo, valor] = porObjetivo[objetivo] || [null, 0];

  // Si el objetivo no dio resultado, se cae al primero que tenga valor.
  if (!valor) {
    if (conv) [tipo, valor] = ['conversaciones', conv];
    else if (lead) [tipo, valor] = ['leads', lead];
    else if (clic) [tipo, valor] = ['clics', clic];
    else return { tipo: null, valor: 0 };
  }
  return { tipo, valor };
}

/* ── Un año ────────────────────────────────────────────────────── */
async function traerAnio(anio) {
  const hoy = new Date();
  const inicio = new Date(anio, 0, 1);
  const finAnio = new Date(anio, 11, 31);
  if (inicio > hoy) return null;                 // año futuro: nada que traer
  const fin = finAnio > hoy ? hoy : finAnio;
  const rango = { since: iso(inicio), until: iso(fin) };

  console.log(`\n${anio}  ${rango.since} → ${rango.until}`);

  // 1. Cuenta, mes a mes.
  const porMes = await insights({
    level: 'account',
    fields: 'reach,spend,impressions,actions',
    time_range: JSON.stringify(rango),
    time_increment: 'monthly',
  });
  if (!porMes.length) {
    console.log(`  sin datos`);
    return null;
  }

  // 2. Cuenta, período completo (el alcance único NO es la suma de los meses).
  const [totales] = await insights({
    level: 'account',
    fields: 'reach,spend,impressions,actions',
    time_range: JSON.stringify(rango),
    time_increment: 'all_days',
  });

  // 3. Campañas, mes a mes, para la tabla y el gráfico de anuncios.
  const campanasMes = await insights({
    level: 'campaign',
    fields: 'campaign_id,campaign_name,objective,spend,impressions,actions',
    time_range: JSON.stringify(rango),
    time_increment: 'monthly',
  });

  const mesDe = f => new Date(f.date_start + 'T12:00:00').getMonth();

  const meses = porMes.map(f => {
    const m = mesDe(f);
    const finMes = new Date(anio, m + 1, 0);
    const campanas = campanasMes
      .filter(c => mesDe(c) === m)
      .map(c => {
        const r = resultadoDe(c.objective, c.actions);
        const gasto = Math.round(Number(c.spend) || 0);
        return {
          nombre: c.campaign_name,
          gasto,
          impresiones: Math.round(Number(c.impressions) || 0),
          resultadoTipo: r.tipo,
          resultado: r.valor,
          costoResultado: r.valor ? Math.round(gasto / r.valor) : null,
        };
      })
      .sort((a, b) => b.gasto - a.gasto);

    return {
      key: CLAVES[m],
      mes: m + 1,
      desde: f.date_start,
      hasta: f.date_stop,
      parcial: finMes > hoy,
      alcance: Math.round(Number(f.reach) || 0),
      gasto: Math.round(Number(f.spend) || 0),
      impresiones: Math.round(Number(f.impressions) || 0),
      conv: accion(f.actions, A_CONV),
      inter: accion(f.actions, A_ENG),
      clics: accion(f.actions, A_CLIC),
      campanas,
    };
  }).sort((a, b) => a.mes - b.mes);

  const acum = {};
  for (const m of meses) {
    for (const c of m.campanas) {
      const k = c.nombre;
      if (!acum[k]) acum[k] = { nombre: k, gasto: 0, impresiones: 0, resultadoTipo: c.resultadoTipo, resultado: 0 };
      acum[k].gasto += c.gasto;
      acum[k].impresiones += c.impresiones;
      acum[k].resultado += c.resultado;
      if (c.resultadoTipo) acum[k].resultadoTipo = c.resultadoTipo;
    }
  }
  const campanasYtd = Object.values(acum)
    .map(c => ({ ...c, costoResultado: c.resultado ? Math.round(c.gasto / c.resultado) : null }))
    .sort((a, b) => b.gasto - a.gasto);

  for (const m of meses) {
    console.log(`  ${m.key}  alcance ${String(m.alcance).padStart(7)}  conv ${String(m.conv).padStart(4)}  clics ${String(m.clics).padStart(5)}  gasto $${m.gasto.toLocaleString('es-AR').padStart(11)}  ${m.campanas.length} camp.${m.parcial ? '  (parcial)' : ''}`);
  }

  return {
    desde: rango.since,
    hasta: rango.until,
    ytd: {
      // El alcance viene del período completo: es alcance único, no la suma mensual.
      alcance: Math.round(Number(totales?.reach) || 0),
      gasto: meses.reduce((s, m) => s + m.gasto, 0),
      impresiones: meses.reduce((s, m) => s + m.impresiones, 0),
      conv: meses.reduce((s, m) => s + m.conv, 0),
      inter: meses.reduce((s, m) => s + m.inter, 0),
      clics: meses.reduce((s, m) => s + m.clics, 0),
      campanas: campanasYtd,
    },
    meses,
  };
}

/* ── Main ──────────────────────────────────────────────────────── */
console.log(`Cuenta act_${ACCOUNT} · ${VERSION}`);

// Se traen los años anteriores además del actual para que el informe no pierda
// el histórico cuando cambia el año. Sin esto, cada 1 de enero el informe
// arrancaría vacío y el año anterior desaparecería de la vista.
const datos = {};
for (let a = ANIO - ATRAS; a <= ANIO; a++) {
  const bloque = await traerAnio(a);
  if (bloque) datos[String(a)] = bloque;
}

if (!Object.keys(datos).length) {
  console.error('La API no devolvió datos para ningún año pedido.');
  process.exit(1);
}

// Año efectivo: el más reciente que devolvió datos. Puede no ser ANIO —
// el 1 de enero, antes de la primera entrega, el año nuevo todavía viene vacío.
const anios = Object.keys(datos).sort();
const anioEfectivo = Number(anios[anios.length - 1]);
const actual = datos[String(anioEfectivo)];

const salida = {
  generado: new Date().toISOString(),
  cuenta: ACCOUNT,
  version: VERSION,
  anio: anioEfectivo,
  anios,
  datos,
  // Compatibilidad con la versión de un solo año del informe.
  desde: actual.desde,
  hasta: actual.hasta,
  ytd: actual.ytd,
  meses: actual.meses,
};

await mkdir(dirname(OUT), { recursive: true });
await writeFile(OUT, JSON.stringify(salida, null, 2) + '\n', 'utf8');

console.log(`\nAños: ${salida.anios.join(', ')}`);
console.log(`${anioEfectivo}: alcance único ${actual.ytd.alcance.toLocaleString('es-AR')}  ·  gasto $${actual.ytd.gasto.toLocaleString('es-AR')}`);
console.log(`Escrito ${OUT}`);
