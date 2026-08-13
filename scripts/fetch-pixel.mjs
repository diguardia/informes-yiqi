#!/usr/bin/env node
/**
 * Trae los eventos del píxel de YiQi y los deja en data/pixel.json, agregados
 * por día en hora de Buenos Aires. La API los devuelve por hora y en hora del
 * Pacífico: si se agrupa en crudo, los eventos de la madrugada caen en el día
 * anterior y el conteo diario queda mal.
 *
 * Va aparte de fetch-meta.mjs a propósito: si este falla, la sincronización
 * del informe comercial sigue funcionando igual.
 *
 * Variables de entorno:
 *   META_TOKEN        (obligatoria) mismo secreto que usa fetch-meta.mjs
 *   META_PIXEL_ID     id del píxel (por defecto, el de YiQi SA)
 *   META_API_VERSION  versión de la Graph API (por defecto v25.0)
 *   META_DIAS         días hacia atrás a traer (por defecto 8)
 *
 * Sin dependencias: fetch nativo de Node 18+.
 */

import { writeFile, mkdir } from 'node:fs/promises';
import { dirname } from 'node:path';

const TOKEN   = process.env.META_TOKEN;
const PIXEL   = process.env.META_PIXEL_ID || '455192279196875';
const VERSION = process.env.META_API_VERSION || 'v25.0';
const DIAS    = Math.max(1, Number(process.env.META_DIAS || 8));
const OUT     = 'data/pixel.json';

// Eventos que nos importa vigilar. El resto se guarda igual, pero estos son
// los que disparan aviso.
const VIGILADOS = ['Lead', 'InitiateCheckout'];

/** Día calendario en Buenos Aires (UTC-3) para un timestamp cualquiera. */
function diaEnBuenosAires(ts) {
  const d = new Date(ts);
  // Se corre el reloj a UTC-3 y recién ahí se lee la fecha.
  const arg = new Date(d.getTime() - 3 * 60 * 60 * 1000);
  return arg.toISOString().slice(0, 10);
}

async function traerStats() {
  const hasta = new Date();
  const desde = new Date(hasta.getTime() - DIAS * 24 * 60 * 60 * 1000);
  const url = `https://graph.facebook.com/${VERSION}/${PIXEL}/stats?` +
    new URLSearchParams({
      aggregation: 'event',
      start_time: desde.toISOString(),
      end_time: hasta.toISOString(),
      access_token: TOKEN,
    });
  const res = await fetch(url);
  const body = await res.json();
  if (body.error) {
    throw new Error(`Graph API ${body.error.code}/${body.error.error_subcode ?? '-'}: ${body.error.message}`);
  }
  return body.data || [];
}

/** Convierte la respuesta por hora en { '2026-08-11': { Lead: 1, PageView: 80 } }. */
export function agregarPorDia(filas) {
  const dias = {};
  for (const fila of filas) {
    const dia = diaEnBuenosAires(fila.timestamp);
    dias[dia] = dias[dia] || {};
    for (const ev of fila.data || []) {
      dias[dia][ev.value] = (dias[dia][ev.value] || 0) + Number(ev.count || 0);
    }
  }
  return dias;
}

/* ── Main ──────────────────────────────────────────────────────── */
if (import.meta.url === `file://${process.argv[1]}`) {
  if (!TOKEN) {
    console.error('Falta META_TOKEN. Cargalo como secreto del repositorio.');
    process.exit(1);
  }
  const filas = await traerStats();
  const dias = agregarPorDia(filas);
  const fechas = Object.keys(dias).sort();

  const totales = {};
  for (const f of fechas) for (const [ev, n] of Object.entries(dias[f])) totales[ev] = (totales[ev] || 0) + n;

  // Ayer en hora de Buenos Aires: es el último día completo.
  const ayer = diaEnBuenosAires(Date.now() - 24 * 60 * 60 * 1000);
  const deAyer = dias[ayer] || {};
  const aviso = VIGILADOS.filter((ev) => (deAyer[ev] || 0) > 0);

  const salida = {
    generado: new Date().toISOString(),
    pixel: PIXEL,
    version: VERSION,
    zona: 'America/Argentina/Buenos_Aires',
    desde: fechas[0] || null,
    hasta: fechas[fechas.length - 1] || null,
    eventos: Object.keys(totales).sort(),
    totales,
    dias,
    ayer: { fecha: ayer, eventos: deAyer },
  };

  await mkdir(dirname(OUT), { recursive: true });
  await writeFile(OUT, JSON.stringify(salida, null, 2) + '\n', 'utf8');

  for (const f of fechas) {
    const e = dias[f];
    console.log(`  ${f}  ` + Object.entries(e).map(([k, v]) => `${k}=${v}`).join('  '));
  }
  console.log(`\nEventos vistos: ${salida.eventos.join(', ') || 'ninguno'}`);
  console.log(`Escrito ${OUT}`);

  // Lo consume el paso de aviso del workflow.
  if (process.env.GITHUB_OUTPUT) {
    const { appendFileSync } = await import('node:fs');
    appendFileSync(process.env.GITHUB_OUTPUT, `avisar=${aviso.length ? 'si' : 'no'}\n`);
    appendFileSync(process.env.GITHUB_OUTPUT, `eventos=${aviso.join(', ')}\n`);
    appendFileSync(process.env.GITHUB_OUTPUT, `fecha=${ayer}\n`);
    appendFileSync(process.env.GITHUB_OUTPUT, `detalle=${JSON.stringify(deAyer)}\n`);
  }
}
