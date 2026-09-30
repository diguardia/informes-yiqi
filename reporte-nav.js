/* Navegador de meses de los reportes mensuales (YiQi_Reporte_Comercial_AAAAMM.html).

   Reemplaza la pildora fija del mes por un .ds-picker con todos los reportes
   publicados, el mas nuevo arriba; elegir un mes abre ese reporte. Es el
   mismo control de periodo que usa comercial.html. La lista sale de
   data/reportes.json, que escribe scripts/armar-reporte-comercial.py cada vez
   que arma un mes. Vive en un archivo aparte a proposito: los reportes ya
   cerrados no se rearman para sumarle navegacion, solo cargan este script.
   Sin JSON, o con un solo reporte, queda la pildora. Pedido de Seba, 30/09/2026. */
(function () {
  var NOM = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
             'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
  var nombre = function (mes) { return NOM[Number(mes.slice(5, 7)) - 1] + ' ' + mes.slice(0, 4); };
  var CHEV = '<svg class="ds-picker-chev" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>';

  function armar(lista) {
    var grupo = document.querySelector('.range-filter[aria-label="Periodo del informe"]');
    var actual = decodeURIComponent(location.pathname.split('/').pop() || '');
    var hay = lista.some(function (r) { return r.archivo === actual; });
    if (!grupo || lista.length < 2 || !hay) return;

    var el = document.createElement('div');
    el.className = 'ds-picker';
    el.id = 'reporte-mes';
    el.setAttribute('data-ds-picker', '');
    el.innerHTML =
      '<button type="button" class="ds-picker-toggle" aria-haspopup="listbox" aria-expanded="false" aria-label="Mes del reporte">' +
        '<span class="ds-picker-value"></span>' + CHEV + '</button>' +
      '<div class="ds-picker-menu" role="listbox" aria-label="Mes del reporte" hidden></div>';
    var menu = el.querySelector('.ds-picker-menu');
    lista.forEach(function (r) {
      var o = document.createElement('button');
      var esta = r.archivo === actual;
      o.type = 'button';
      o.className = 'ds-picker-option' + (esta ? ' is-active' : '');
      o.setAttribute('role', 'option');
      o.setAttribute('aria-selected', String(esta));
      o.dataset.value = r.archivo;
      o.textContent = nombre(r.mes);
      menu.appendChild(o);
      if (esta) el.querySelector('.ds-picker-value').textContent = nombre(r.mes);
    });
    grupo.replaceWith(el);
    el.addEventListener('ds-picker:change', function (e) {
      var v = e.detail && e.detail.value;
      if (v && v !== actual && /^YiQi_Reporte_Comercial_\d{6}\.html$/.test(v)) location.href = v;
    });
  }

  fetch('data/reportes.json', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (j) { if (j && Array.isArray(j.reportes)) armar(j.reportes); })
    .catch(function () { /* queda la pildora del mes */ });
})();
