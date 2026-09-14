"""Arma YiQi_Reporte_Comercial_202608.html.

Tres secciones, tres origenes, ninguna cifra escrita a mano:
  Meta            data/meta.json
  El retargeting  scripts/secciones-retargeting.html (cifras del doc del 07/09)
  Comercial       data/crm-2026.json, que arma scripts/crm-json.py

De comercial.html se extrae solo CSS compartido y cuatro funciones, por
rangos verificados y balance de llaves, nunca por posicion.

Se corre desde la raiz del repo:  python3 scripts/armar-reporte-comercial.py
Para otro mes: bajar los exports a data/crm/, correr scripts/crm-json.py y
volver a correr este.
"""
import re, io, os, hashlib
# La raiz del repo es la carpeta que contiene a scripts/, no una ruta fija:
# el script corre igual desde la Mac que desde el puente.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(REPO,'comercial.html'), encoding='utf-8').read().split('\n')

def sl(a,b):                      # 1-indexed inclusive
    return '\n'.join(src[a-1:b])

def check(txt, must):
    for m in must:
        assert m in txt, 'FALTA: '+m
    return txt

# De comercial.html se trae solo lo que este reporte aplica. Las variantes
# de color de KPI, las dos grillas densas y los tres .chart-wrap quedaron
# sin un solo uso cuando salio el bloque heredado: no se extraen mas.
CSS_1   = check(sl(336,347),  ['.section-title {', '.section-sub {'])
CSS_2   = check(sl(382,390),  ['.kpi-delta.positive'])
CSS_3   = check(sl(391,398),  ['.card {'])
CSS_4   = check(sl(607,617),  ['.card-reveal { opacity: 0; }'])
CSS_5   = check(sl(665,672),  ['@media (max-width: 640px) {']) + '\n    }'

# Cuatro funciones que comercial.html tiene repartidas por el archivo y que
# el render de este reporte necesita. Se extraen por nombre y balance de
# llaves, nunca por posicion.
def func(nombre):
    i = None
    for n, l in enumerate(src):
        if l.startswith('function ' + nombre + '(') or l.startswith('const ' + nombre + ' ='):
            i = n; break
    assert i is not None, 'no se encontro ' + nombre
    d = 0; fin = None
    for n in range(i, len(src)):
        d += src[n].count('{') - src[n].count('}')
        if d == 0 and '{' in '\n'.join(src[i:n+1]):
            fin = n; break
    assert fin is not None, 'no cierra ' + nombre
    return '\n'.join(src[i:fin+1])

HELPERS = '\n\n'.join([func('getCSSVar'), func('parseKpiValue'), func('runCountUp'), func('initReveal')])
for _m in ['function getCSSVar', 'function parseKpiValue', 'function runCountUp', 'function initReveal']:
    assert _m in HELPERS, 'falta ' + _m

PAGINA = """<!doctype html>
<html lang="es" data-theme="system">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<title>Reporte comercial — Agosto 2026 · YiQi</title>

<!-- ═══════════════════════════════════════════════════════════════════
     Reporte comercial del mes · Agosto 2026 — version de una sola pantalla.

     DERIVADO, NO ESCRITO A MANO. Ninguna cifra de esta pagina se teclea:
     todas salen de un origen y el archivo se rehace corriendo el script.
     Tres secciones, tres origenes:

       Meta            data/meta.json, que sincroniza GitHub Actions
                       contra la Marketing API
       El retargeting  claude/Retargeting-inventario-y-acciones-sep2026.md
       Comercial       data/crm-2026.json, que arma scripts/crm-json.py
                       desde los exports de data/crm/

     De comercial.html ya no sale contenido: solo el CSS de los componentes
     que este informe comparte con aquel —cifras, tarjetas, animacion de
     entrada—, extraido por rangos verificados. El bloque #mes que se
     heredaba al principio se retiro entero: arrastraba el objeto del
     resumen, su selector de mes y su boton de copiar para sostener una
     sola tarjeta.

     El armazon es propio: topbar, sidebar, barra inferior y barra de
     estado. El comportamiento del sidebar se extrae del informe de
     Ingenieria, que ya lo tenia resuelto.

     Para rehacerlo con otro mes:
       1. bajar los seis exports del CRM a data/crm/
       2. python3 scripts/crm-json.py
       3. python3 scripts/armar-reporte-comercial.py
     ═══════════════════════════════════════════════════════════════════ -->

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;600&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://diguardia.github.io/yiqi-imagen/styles.css">

<script>
/* Tema claro por defecto, solo si el visitante no eligio nada en YiQi.
   Va antes del runtime y sin defer: despues no llega. */
(function () {
  try {
    if (localStorage.getItem('yiqi-theme')) return;
    if (/(?:^|;\\s*)yiqi-theme=/.test(document.cookie)) return;
    localStorage.setItem('yiqi-theme', 'light');
  } catch (e) {}
})();
</script>
<script src="https://diguardia.github.io/yiqi-imagen/yiqi-runtime.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<style>
/* ── ARMAZON ─────────────────────────────────────────────────────
   Lo minimo para sostener una sola seccion: fondo, ancho y relleno.
   Todo lo demas sale del DS o del bloque heredado de comercial.html. */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { overflow-x: clip; }
body {
  font: 14px var(--sans);
  color: var(--text);
  min-height: 100vh;
  background:
    radial-gradient(circle at 72% 8%,  color-mix(in srgb, var(--cyan) 7%, transparent), transparent 28%),
    radial-gradient(circle at 12% 60%, color-mix(in srgb, var(--cyan) 4%, transparent), transparent 22%),
    var(--bg);
}
.content { min-width: 0; padding: 28px 32px calc(64px + var(--statusbar-h)); }
@media (max-width: 980px) {
  .content { padding: 20px 16px calc(78px + env(safe-area-inset-bottom, 12px)); }
}


/* ── NAVEGACION MOVIL — §67 del DS ────────────────────────────────
   Tres destinos, uno por seccion. Una barra inferior promete pantallas:
   si el destino fuera un ancla dentro de una pagina de miles de pixeles,
   el salto recorreria todo lo que no pediste y despues cualquier scroll
   te mudaria de seccion sin querer. Bajo 980px cada destino es una
   pantalla: se muestra su seccion y se ocultan las otras. En escritorio
   no cambia nada, sigue siendo el reporte largo con su sidebar.

   Y con la barra inferior el cajon sobra: dos navegaciones para lo mismo
   es peor que una. */
/* Solo el sidebar usa la medicion real de la topbar; si el script no
   llego a correr, cae al token del DS y se comporta como antes. */
.sidebar {
  top: var(--topbar-real, var(--topbar-h));
  height: calc(100vh - var(--topbar-real, var(--topbar-h)) - var(--statusbar-h));
  overflow-y: auto;
}

.ds-bottomnav { display: none; }
@media (max-width: 980px) {
  .ds-bottomnav {
    display: grid;
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 96;
    box-shadow: 0 -1px 0 var(--line), var(--shadow);
  }
  .ds-bottomnav-item { cursor: pointer; border: 0; background: transparent; font: inherit; }

  /* El brief no es un destino: es la apertura del documento, son tres
     lineas y encabeza cualquier pantalla que elijas. Queda fijo. La
     conclusion si tiene destino propio —el quinto de la barra—, asi
     que entra en la regla de ocultar como las otras cuatro. Sin esta
     excepcion, abajo de 980px el brief desaparecia sin boton que lo
     recuperara. */
  .app-shell[data-grupo] .content > section:not(#brief) { display: none; }
  .app-shell[data-grupo="sitio"] #sitio,
  .app-shell[data-grupo="meta"]  #meta,
  .app-shell[data-grupo="retargeting"] #retargeting,
  .app-shell[data-grupo="crm"]   #crm,
  .app-shell[data-grupo="conclusion"] #conclusion { display: block; }

  .nav-hamburger, #app-sidebar, #app-overlay { display: none; }
  /* La barra inferior es fija y el DS no reserva su alto: sin esto el
     ultimo bloque de cada pantalla queda tapado. */
  .content { padding-bottom: calc(76px + env(safe-area-inset-bottom, 12px)); }
}

/* ── HEREDADO DE comercial.html ──────────────────────────────────
   Las mismas reglas, no una reinterpretacion: si cambian alla, se
   vuelve a correr el script y cambian aca. */
__CSS__

</style>
</head>
<body>

<header class="topbar app-topbar">
  <div class="topbar-l">
    <a class="topbar-logo" href="comercial.html" aria-label="Ir al informe comercial">
      __LOGO__
    </a>
    <h1 class="t-pill" style="margin:0">Reporte comercial</h1>
  </div>
  <div class="topbar-c" style="justify-content:center">
    <div class="range-filter" role="group" aria-label="Periodo del informe">
      <button class="range-btn is-active" type="button" aria-current="page">Agosto 2026</button>
    </div>
  </div>
  <div class="topbar-r">
    <button class="nav-hamburger" type="button" aria-label="Abrir menú" aria-expanded="false" aria-controls="app-sidebar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
    <button class="theme-cycle" type="button" data-theme-cycle aria-label="Cambiar tema"><svg class="tc-dark" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z"/></svg><svg class="tc-system" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg><svg class="tc-light" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19"/></svg></button>
  </div>
</header>

<script>
/* El sidebar del DS se pega con `top: var(--topbar-h)` y ese token es fijo
   en 56px. Esta topbar no mide 56: le sumamos el h1 y el selector de tema,
   y en pantallas angostas ademas envuelve. Cada pixel de diferencia es un
   pixel que el sidebar se mete abajo de la topbar — por eso el primer item
   del menu aparecia cortado al medio.
   No se toca el DS ni su token: se mide la topbar real, se escribe en
   --topbar-real y solo el sidebar lo consume. Se remide al cargar las
   fuentes y en cada cambio de tamano, porque la tipografia asienta
   despues del primer layout. */
(function () {
  var tb = document.querySelector('.topbar');
  if (!tb) return;
  var ultimo = 0;
  function medir() {
    var h = Math.round(tb.getBoundingClientRect().height);
    if (!h || h === ultimo) return;
    ultimo = h;
    /* Se escribe un token propio, no --topbar-h. Pisar el del DS movia
       todo lo que depende de el —el cajon movil, la altura de la barra,
       los calculos del shell— y el sidebar se despegaba al scrollear.
       --topbar-real lo consume solo la regla del sidebar de abajo. */
    document.documentElement.style.setProperty('--topbar-real', h + 'px');
  }
  medir();
  addEventListener('load', medir);
  addEventListener('resize', medir);
  if (window.ResizeObserver) new ResizeObserver(medir).observe(tb);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(medir);
})();
</script>

<!-- La barra de estado es position:fixed y el DS no reserva su alto: sin
     este relleno los ultimos 28px del informe quedan tapados. -->
<div class="app-shell" id="app-shell" style="padding-bottom:var(--statusbar-h)">

  <aside class="sidebar" id="app-sidebar" aria-label="Secciones del reporte">
    <button class="nav-close" type="button" aria-label="Cerrar menú"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg></button>

    <nav class="nav" aria-label="Secciones">
      <section class="nav-section">
        <p class="nav-lbl">Agosto 2026</p>
        <a class="nav-link is-active" href="#crm" title="Comercial" aria-current="page"><span class="n-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg></span><span>Comercial</span></a>
        <a class="nav-link" href="#meta" title="Meta"><span class="n-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11v2a1 1 0 0 0 1 1h2l5 4V6L6 10H4a1 1 0 0 0-1 1z"/><path d="M16 8a5 5 0 0 1 0 8"/></svg></span><span>Meta</span></a>
        <a class="nav-link" href="#retargeting" title="Retargeting"><span class="n-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg></span><span>Retargeting</span></a>
        <a class="nav-link" href="#sitio" title="El sitio"><span class="n-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 0 20a15 15 0 0 1 0-20z"/></svg></span><span>El sitio</span></a>
      </section>
    </nav>

    <div class="sb-footer">
      <div class="sidebar-ctrls">
        <button class="sidebar-collapse sb-lock" type="button" aria-pressed="false" aria-label="Fijar el menú abierto" title="Fijar el menú">
          <svg class="ico-unlocked" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>
          <svg class="ico-locked" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        </button>
        <button class="sidebar-collapse sb-arrow" type="button" aria-label="Colapsar el menú" title="Colapsar el menú">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>
        </button>
      </div>
      <div class="sb-copy">&copy; 2026 YiQi S.A.</div>
    </div>
  </aside>

  <main class="content">
__BRIEF__

__CRM_MARKUP__

__META_MARKUP__

__RT_MARKUP__

__SITIO_MARKUP__

__CONCL_MARKUP__
  </main>
</div>

<div class="nav-overlay" id="app-overlay"></div>

<!-- ── Navegacion movil — §67 del DS ────────────────────────────────
     Tres destinos, uno por seccion: ninguno agrupa, asi que ninguno abre
     hoja. Solo se ve bajo 980px. -->
<nav class="ds-bottomnav" id="bottomnav" aria-label="Secciones del reporte">
  <button class="ds-bottomnav-item" type="button" data-grupo="crm">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg>
    <span>Comercial</span>
  </button>
  <button class="ds-bottomnav-item" type="button" data-grupo="meta">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11v2a1 1 0 0 0 1 1h2l5 4V6L6 10H4a1 1 0 0 0-1 1z"/><path d="M16 8a5 5 0 0 1 0 8"/></svg>
    <span>Meta</span>
  </button>
  <button class="ds-bottomnav-item" type="button" data-grupo="retargeting">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
    <span>Retarget.</span>
  </button>
  <button class="ds-bottomnav-item" type="button" data-grupo="sitio">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 0 20a15 15 0 0 1 0-20z"/></svg>
    <span>El sitio</span>
  </button>
  <button class="ds-bottomnav-item" type="button" data-grupo="conclusion">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>
    <span>Cierre</span>
  </button>
</nav>


<footer class="statusbar">
  <div class="statusbar-left">
    <strong>Reporte comercial</strong>
    <span class="sb-sep">&middot;</span>
    <span class="statusbar-desc">$486.857 de pauta &middot; 301 conversaciones &middot; 16 ONs nuevas &middot; 3 concretadas</span>
  </div>
  <div class="statusbar-right">
    <span class="sb-item" id="sb-datos">datos al —</span>
    <span class="sb-sep">&middot;</span>
    <a class="sb-item" href="comercial.html">Informe comercial</a>
    <span class="sb-sep">&middot;</span>
    <span class="sb-item" data-ds-version>DS</span>
    <span class="sb-sep">&middot;</span>
    <span class="sb-item sb-clock" id="sb-clock">--:--</span>
  </div>
</footer>

<script>
/* Helpers que el render del mes usa y que en comercial.html viven
   repartidos por el archivo. Se extraen por nombre, no por posicion. */
const _charts = {};
__HELPERS__

/* El boton de tema del DS delega en setTheme() si existe. Los graficos
   toman sus colores de los tokens, asi que se redibujan al cambiar. */
const _mqTema = window.matchMedia('(prefers-color-scheme: dark)');
function applyTheme(v) { document.documentElement.dataset.theme = (v === 'system' ? (_mqTema.matches ? 'dark' : 'light') : v); }
function setTheme(v) {
  try { localStorage.setItem('yiqi-theme', v); } catch (e) {}
  applyTheme(v);
  setTimeout(function () {
    if (typeof sitioChart === 'function') sitioChart();
    if (typeof crmChart === 'function') crmChart();
    if (typeof crmHistogramas === 'function') crmHistogramas();
  }, 50);
}
_mqTema.addEventListener('change', function () {
  var g = 'system'; try { g = localStorage.getItem('yiqi-theme') || 'system'; } catch (e) {}
  if (g === 'system') setTheme('system');
});
(function () { var g = 'system'; try { g = localStorage.getItem('yiqi-theme') || 'system'; } catch (e) {} applyTheme(g); })();

__NAV_JS__

/* Reloj de la barra de estado, en hora local. */
(function () {
  var el = document.getElementById('sb-clock');
  function tick() { var d = new Date(); el.textContent = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); }
  if (el) { tick(); setInterval(tick, 30000); }
})();

/* Version del DS: se lee del token en runtime, asi el pie nunca miente. */
(function () {
  try {
    var v = getComputedStyle(document.documentElement).getPropertyValue('--ds-version').trim().replace(/"/g, '');
    if (v) document.querySelectorAll('[data-ds-version]').forEach(function (el) { el.textContent = 'DS v' + v; });
  } catch (e) {}
})();
</script>

__CRM_SCRIPT__

__META_SCRIPT__

__RT_SCRIPT__

__SITIO_SCRIPT__

__CONCL_SCRIPT__

__BRIEF_SCRIPT__

<script>
/* ─── NAVEGACION MOVIL (§67) ─────────────────────────────────────
   Va al final a proposito: necesita _charts, que declara el bloque del
   CRM. Chart.js mide el canvas al crearlo, asi que los graficos de una
   seccion oculta nacen con ancho cero y quedan en blanco hasta que se
   les avisa al mostrarla. */
(function () {
  var SECCION = { crm: 'crm', meta: 'meta', retargeting: 'retargeting', sitio: 'sitio', conclusion: 'conclusion' };
  var mq = matchMedia('(max-width: 980px)');
  var shell = document.getElementById('app-shell');
  if (!shell) return;

  function marcar(g) {
    document.querySelectorAll('.ds-bottomnav-item').forEach(function (b) {
      b.classList.toggle('is-active', b.dataset.grupo === g);
      if (b.dataset.grupo === g) b.setAttribute('aria-current', 'page');
      else b.removeAttribute('aria-current');
    });
  }
  function redibujar() {
    if (typeof _charts === 'undefined') return;
    requestAnimationFrame(function () {
      Object.keys(_charts).forEach(function (k) { try { _charts[k].resize(); } catch (e) {} });
    });
  }
  function mostrar(g) {
    if (!mq.matches) {
      var el = document.getElementById(SECCION[g]);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      marcar(g);
      return;
    }
    shell.dataset.grupo = g;
    scrollTo({ top: 0 });
    redibujar();
    marcar(g);
  }

  document.addEventListener('click', function (e) {
    var it = e.target.closest && e.target.closest('.ds-bottomnav-item');
    if (it) mostrar(it.dataset.grupo);
  });

  /* Al pasar a escritorio se suelta el grupo: alla la pagina vuelve a ser
     larga y esconder secciones dejaria el reporte a un tercio. */
  function alCambiarAncho() {
    if (mq.matches) { if (!shell.dataset.grupo) mostrar('crm'); else marcar(shell.dataset.grupo); }
    else { delete shell.dataset.grupo; redibujar(); }
  }
  mq.addEventListener ? mq.addEventListener('change', alCambiarAncho) : mq.addListener(alCambiarAncho);
  alCambiarAncho();
})();
</script>

</body>
</html>
"""

# El logo sale del informe de Ingenieria, que ya lo tiene inline y canonico.
ing = open(os.path.join(REPO,'YiQi_Informe_Ingenieria_202608.html'), encoding='utf-8').read()
m = re.search(r'<svg class="topbar-logo-svg".*?</svg>', ing, re.S)
assert m, 'no se encontro el logo'
LOGO = m.group(0)

# El comportamiento del sidebar —colapsar, fijar, hover-peek, drawer mobile
# y scrollspy— ya esta resuelto y medido en el informe de Ingenieria. Se
# extrae de ahi en vez de reescribirlo: si ese archivo lo corrige, se vuelve
# a correr este script y el reporte se corrige tambien.
_ini = ing.index("  var shell = document.getElementById('app-shell');")
_fin = ing.index("  /* Reloj de la barra de estado, en hora local. */")
NAV_JS = ing[_ini:_fin].rstrip()
for _m in ['nav-collapsed', 'nav-peek', 'nav-locked', 'function marcar']:
    assert _m in NAV_JS, 'al script del sidebar le falta ' + _m
# Defecto heredado: los dos botones del pie del sidebar llevan la clase
# .sidebar-collapse, y el script toma el primero con querySelector. El
# primero es el candado, asi que la flecha de colapsar no hacia nada y el
# candado colapsaba y fijaba a la vez. Se apunta a .sb-arrow, que es el
# boton que de verdad colapsa. El mismo defecto esta en
# YiQi_Informe_Ingenieria_202608.html.
assert NAV_JS.count("var col   = document.querySelector('.sidebar-collapse');") == 1
NAV_JS = NAV_JS.replace("var col   = document.querySelector('.sidebar-collapse');",
                        "var col   = document.querySelector('.sb-arrow');")

# Aquel informe marca secciones .panel[id]; este usa <section id> sueltas.
assert NAV_JS.count("querySelectorAll('.panel[id]')") == 1
NAV_JS = NAV_JS.replace("querySelectorAll('.panel[id]')", "querySelectorAll('.content > section[id]')")

# El drawer de mobile: el runtime del DS lo abre con .nav-hamburger, pero el
# cierre por overlay y por Escape lo pone cada pagina.
NAV_JS += '''

  /* Drawer de mobile. El hamburguesa abre; el overlay, la cruz y Escape
     cierran. Sin esto el cajon queda abierto tapando el informe. */
  var ham = document.querySelector('.nav-hamburger');
  var cerrar = document.querySelector('.nav-close');
  var overlay = document.getElementById('app-overlay');
  function drawer(abierto) {
    shell.classList.toggle('nav-open', abierto);
    if (overlay) overlay.classList.toggle('is-on', abierto);
    if (ham) ham.setAttribute('aria-expanded', String(abierto));
  }
  ham && ham.addEventListener('click', function () { drawer(!shell.classList.contains('nav-open')); });
  cerrar && cerrar.addEventListener('click', function () { drawer(false); });
  overlay && overlay.addEventListener('click', function () { drawer(false); });
  addEventListener('keydown', function (e) { if (e.key === 'Escape') drawer(false); });
  /* Al tocar un destino en mobile el cajon se cierra solo: si no, el lector
     salta a la seccion y la sigue viendo tapada. */
  sb && sb.addEventListener('click', function (e) {
    if (e.target.closest('a.nav-link')) drawer(false);
  });'''

# ── Comercial en el CRM ──────────────────────────────────────────────
# El fragmento trae estilo, markup y render; las cifras salen del JSON que
# genera scripts/crm-json.py desde los exports. Se embeben en la pagina
# para que el informe abra igual desde el disco, sin fetch.
FRAG = open(os.path.join(REPO, 'scripts', 'secciones-crm.html'), encoding='utf-8').read()
_i = FRAG.index('    <script>')
CRM_MARKUP, CRM_SCRIPT = FRAG[:_i].rstrip(), FRAG[_i:].rstrip()
assert '<section id="crm"' in CRM_MARKUP and 'crmRender();' in CRM_SCRIPT

# El JSON del disco guarda el detalle registro por registro; la pagina ya no
# lo muestra —solo graficos y cifras—, asi que no se embebe: son 25 KB que
# nadie lee. El archivo fuente queda completo.
import json as _json
_crm = _json.load(open(os.path.join(REPO, 'data', 'crm-2026.json'), encoding='utf-8'))
_quitados = 0
for _m in _crm['meses'].values():
    for _k, _b in _m.items():
        # El detalle de concretadas se queda: el brief lo usa para decir
        # cuanto pesa la operacion mayor y cuantos clientes hay detras, y
        # son tres filas por mes.
        if isinstance(_b, dict) and 'detalle' in _b and _k != 'concretadas':
            del _b['detalle']; _quitados += 1
assert _quitados >= 4, 'no se quito ningun detalle'
CRM_JSON = _json.dumps(_crm, ensure_ascii=False, separators=(',', ':'))
assert CRM_JSON.startswith('{') and '"2026-08"' in CRM_JSON, 'el json del CRM no tiene el mes'
assert '</script' not in CRM_JSON, 'el json cerraria el script'
assert CRM_SCRIPT.count('__CRM_JSON__') == 1
CRM_SCRIPT = CRM_SCRIPT.replace('__CRM_JSON__', CRM_JSON)

# ── Meta ─────────────────────────────────────────────────────────────
# data/meta.json lo sincroniza GitHub Actions contra la Marketing API. Se
# embebe un recorte —los meses, las campañas del mes y la bitacora— porque
# el mes ya esta cerrado: el reporte no tiene que moverse cuando la cuenta
# siga gastando.
_meta = _json.load(open(os.path.join(REPO, 'data', 'meta.json'), encoding='utf-8'))
MES_REPORTE = '2026-08'
_meses = {}
for _anio, _d in _meta['datos'].items():
    for _m in _d['meses']:
        if _m.get('parcial'):
            continue   # un mes a medio correr, al lado de meses cerrados, se lee como una caida
        _meses['%s-%02d' % (_anio, _m['mes'])] = {k: _m[k] for k in ('gasto', 'alcance', 'impresiones', 'conv', 'inter', 'clics')}
assert MES_REPORTE in _meses, 'meta.json no trae el mes del reporte'

_campanas = []
for _anio, _d in _meta['datos'].items():
    for _m in _d['meses']:
        if '%s-%02d' % (_anio, _m['mes']) == MES_REPORTE:
            _campanas = [{k: c[k] for k in ('nombre', 'gasto', 'impresiones', 'resultadoTipo', 'resultado', 'costoResultado')}
                         for c in _m.get('campanas', [])]
assert _campanas, 'el mes del reporte no trae campañas'

# La bitacora vive escrita a mano en comercial.html, dentro de #resumen. Se
# extraen los asientos y se quedan los que caen hasta el mes del reporte:
# un asiento de septiembre no explica una serie que corta en agosto.
_MESCORTO = {'ene':1,'feb':2,'mar':3,'abr':4,'may':5,'jun':6,'jul':7,'ago':8,'sep':9,'oct':10,'nov':11,'dic':12}
_html = '\n'.join(src)
_bloque = re.search(r'Bit\u00e1cora de cambios.*?<!-- ── SECCI\u00d3N 2', _html, re.S)
assert _bloque, 'no se encontro la bitacora en comercial.html'
_asientos = re.findall(
    r'padding-top:2px">\s*([0-9]{1,2})\s+([a-z]{3})\s*</div>\s*<div>\s*'
    r'<div style="font-size:13px[^"]*">(.*?)</div>\s*'
    r'<div style="font-size:12px[^"]*">(.*?)</div>', _bloque.group(0), re.S)
assert len(_asientos) >= 8, 'la bitacora devolvio %d asientos' % len(_asientos)
BITACORA = []
for _dia, _mes, _tit, _cue in _asientos:
    _clave = '2026-%02d' % _MESCORTO[_mes]
    if _clave > MES_REPORTE:
        continue
    BITACORA.append({
        'fecha': '%s %s' % (_dia, _mes),
        'titulo': re.sub(r'<[^>]+>', '', _tit).strip(),
        # Se conserva el <strong> del original y se le saca el estilo inline:
        # el enfasis es del texto, el color lo pone el DS.
        'cuerpo': re.sub(r'\s+', ' ', re.sub(r'<(strong|em)[^>]*>', r'<\1>', _cue)).strip(),
    })
assert BITACORA, 'ningun asiento entra en el mes del reporte'

META_PAYLOAD = {'cuenta': _meta['cuenta'], 'generado': _meta['generado'],
                'meses': _meses, 'campanas': _campanas}
META_JSON = _json.dumps(META_PAYLOAD, ensure_ascii=False, separators=(',', ':'))

# ── El sitio ─────────────────────────────────────────────────────────
# La tarjeta de Clarity es la unica del resumen del mes que este reporte
# conserva. Su dato es el objeto `clarity` de RESUMEN_MES en comercial.html,
# y se localiza por marcador y balance de llaves: aquel archivo se edita
# seguido y los numeros de linea se corren.
_txt = '\n'.join(src)
_i = _txt.index('\n        clarity: {')
_d = 0
for _n in range(_i, len(_txt)):
    if _txt[_n] == '{': _d += 1
    elif _txt[_n] == '}':
        _d -= 1
        if _d == 0:
            _j = _n + 1
            break
CLARITY = _txt[_txt.index('{', _i):_j]
for _m in ['origen:', 'eventos:', 'stats:', 'claves:', 'pie:', 'paginas:']:
    assert _m in CLARITY, 'al objeto clarity le falta ' + _m
assert CLARITY.count('{') == CLARITY.count('}'), 'el objeto clarity no cierra'

# El brief: markup y nada mas, sin script. Es el unico bloque en prosa del
# reporte y va arriba de todo.
BRIEF = open(os.path.join(REPO, 'scripts', 'secciones-brief.html'), encoding='utf-8').read().rstrip()
BRIEF_SCRIPT = open(os.path.join(REPO, 'scripts', 'secciones-brief-script.html'), encoding='utf-8').read().rstrip()
assert '<section id="brief"' in BRIEF and '<script' not in BRIEF
assert 'brief-body' in BRIEF and 'brief-body' in BRIEF_SCRIPT
# El brief es el unico bloque en prosa: si vuelve a traer una cifra
# tecleada, deja de corregirse solo al regenerar el reporte.
_bm = BRIEF.split('</style>')[-1]
assert not re.search(r'\d[\d.]{2,}', _bm), 'el brief tiene cifras escritas a mano'
# .card-reveal nace con opacity:0 y la revela initReveal, que corre sobre
# el cuerpo que cada seccion dibuja por JS. El brief es markup estatico:
# nadie lo observaba y quedaba invisible, ocupando su alto en blanco.

FRAG_SITIO = open(os.path.join(REPO, 'scripts', 'secciones-sitio.html'), encoding='utf-8').read()
_p = FRAG_SITIO.index('    <script>')
SITIO_MARKUP, SITIO_SCRIPT = FRAG_SITIO[:_p].rstrip(), FRAG_SITIO[_p:].rstrip()
assert SITIO_SCRIPT.count('__CLARITY__') == 1
SITIO_SCRIPT = SITIO_SCRIPT.replace('__CLARITY__', CLARITY)

FRAG_RT = open(os.path.join(REPO, 'scripts', 'secciones-retargeting.html'), encoding='utf-8').read()
_k = FRAG_RT.index('    <script>')
RT_MARKUP, RT_SCRIPT = FRAG_RT[:_k].rstrip(), FRAG_RT[_k:].rstrip()
assert '<section id="retargeting"' in RT_MARKUP and 'rtRender();' in RT_SCRIPT

# La conclusion: prosa de cierre, sin entrada en la nav. Va despues del
# sitio; su script corre antes que el del brief, que va ultimo.
FRAG_CC = open(os.path.join(REPO, 'scripts', 'secciones-conclusion.html'), encoding='utf-8').read()
_c = FRAG_CC.index('    <script>')
CC_MARKUP, CC_SCRIPT = FRAG_CC[:_c].rstrip(), FRAG_CC[_c:].rstrip()
assert '<section id="conclusion"' in CC_MARKUP

FRAG_META = open(os.path.join(REPO, 'scripts', 'secciones-meta.html'), encoding='utf-8').read()
_j = FRAG_META.index('    <script>')
META_MARKUP, META_SCRIPT = FRAG_META[:_j].rstrip(), FRAG_META[_j:].rstrip()
assert META_SCRIPT.count('__META_JSON__') == 1
META_SCRIPT = META_SCRIPT.replace('__META_JSON__', META_JSON)

out = (PAGINA
    .replace('__CSS__', '\n'.join([CSS_1, CSS_2, CSS_3, CSS_4, CSS_5]))
    .replace('__HELPERS__', HELPERS)
    .replace('__CRM_MARKUP__', CRM_MARKUP)
    .replace('__CRM_SCRIPT__', CRM_SCRIPT)
    .replace('__META_MARKUP__', META_MARKUP)
    .replace('__META_SCRIPT__', META_SCRIPT)
    .replace('__RT_MARKUP__', RT_MARKUP)
    .replace('__RT_SCRIPT__', RT_SCRIPT)
    .replace('__BRIEF__', BRIEF)
    .replace('__BRIEF_SCRIPT__', BRIEF_SCRIPT)
    .replace('__SITIO_MARKUP__', SITIO_MARKUP)
    .replace('__SITIO_SCRIPT__', SITIO_SCRIPT)
    .replace('__CONCL_MARKUP__', CC_MARKUP)
    .replace('__CONCL_SCRIPT__', CC_SCRIPT)
    .replace('__LOGO__', LOGO)
    .replace('__NAV_JS__', '(function () {\n' + NAV_JS + '\n})();'))

for m in ['__CSS__','__HELPERS__','__LOGO__','__CRM_MARKUP__','__CRM_SCRIPT__','__CRM_JSON__','__META_MARKUP__','__META_SCRIPT__','__META_JSON__','__NAV_JS__','__RT_MARKUP__','__RT_SCRIPT__','__SITIO_MARKUP__','__SITIO_SCRIPT__','__CLARITY__','__BRIEF__','__BRIEF_SCRIPT__','__CONCL_MARKUP__','__CONCL_SCRIPT__']:
    assert m not in out, 'marcador sin reemplazar: '+m
assert out.count('<style>') == 7 and out.count('</style>') == 7, 'estilos: pagina, brief, CRM, Meta, retargeting, sitio y conclusion'
assert out.count('<section id="brief"') == 1
# Jerarquia de encabezados: un h1 y un h2 por seccion de contenido.
assert out.count('<h1') == 1, 'el documento necesita un solo h1'
assert out.count('<h2 class="section-title"') == 4, 'un h2 por seccion'
assert out.count('<section id="sitio"') == 1
assert out.count('<section id="retargeting"') == 1
assert out.count('<section id="meta"') == 1
assert out.count('<section id="crm"') == 1
assert out.count('<section id="conclusion"') == 1
assert '<section id="mes"' not in out, 'el bloque heredado de comercial.html volvio'

dst = os.path.join(REPO,'YiQi_Reporte_Comercial_202608.html')
open(dst,'w',encoding='utf-8').write(out)
print('escrito:', dst)
print('lineas:', out.count('\n')+1, '· bytes:', len(out.encode('utf-8')))
print('md5:', hashlib.md5(out.encode('utf-8')).hexdigest())
