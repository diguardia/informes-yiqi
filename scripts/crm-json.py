"""Arma data/crm-2026.json desde los exports del CRM.

Se corre desde la raiz del repo:  python3 scripts/crm-json.py
Lee todos los .xlsx que haya en data/crm/ y los reconoce por sus columnas,
no por el nombre del archivo: los exports del CRM traen un id distinto en
cada descarga. Cada mes se vuelven a bajar los seis, se dejan ahi, se corre
este script y despues scripts/armar-reporte-comercial.py.

Los siete que hacen falta:
  ONs - Detalle con estado      Fecha de creacion, Origen, Empresa, Titulo, Estado,
                                Campana. Reemplaza al export sin estado: sin la
                                columna Descripcion de estado no se reconoce.
  ONs Concretadas - DETALLE     Empresa, Origen, Importe total, Fecha de concrecion
  Consulta comercial            Contacto, Cliente, Telefono, Mail, Origen, Fecha
  Cotizaciones (default)        Raiz, Version, Nro, Fecha, Centro de costos, Estado
  Cotiz. enviadas               Nro. Cotizacion, Fecha de envio
  Cotiz. aprobadas              Neto implementacion, Neto soporte, Nro, Fecha de aprobacion
  Nuevas ON mensuales           Empresa, Fecha de creacion  (el agregado del tablero)

Tres fechas distintas y a proposito: emitidas se cuenta por la fecha de la
cotizacion, enviadas por fecha de envio y aprobadas por fecha de aprobacion.
El informe lo dice en su nota; no se mezclan.
"""
import os, glob, json, math
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORI = 'Origen del Contacto - Origen del Contacto'
ANIO = 2026

# Los detalles se reconocen por las columnas que tienen que estar; los
# agregados, por su juego exacto de columnas: 'Empresa' + 'Fecha de creacion'
# tambien esta en el detalle de ONs, y sin igualdad exacta uno se comeria al
# otro segun el orden de lectura.
FIRMAS = {
    'ons': {'Fecha de creación', 'Empresa', 'Título', 'Descripción de estado'},
    'con': {'Empresa', 'Importe total implementación', 'Fecha de concreción'},
    'cc':  {'Contacto', 'Cliente', 'Mail'},
    'cot': {'Raíz', 'Versión', 'Nro. Cotización', 'Fecha'},
}
FIRMAS_EXACTAS = {
    'onsmes': {'Empresa', 'Fecha de creación'},
    'env':    {'Nro. Cotización', 'Fecha de envío'},
    'apr':    {'Neto implementación', 'Neto soporte', 'Nro. Cotización', 'Fecha de aprobación'},
}

def reconocer(carpeta):
    hallado = {}
    for ruta in sorted(glob.glob(os.path.join(carpeta, '*.xlsx'))):
        d = pd.ExcelFile(ruta).parse(0)
        cols = set(d.columns)
        clave = next((k for k, fi in FIRMAS_EXACTAS.items() if fi == cols and k not in hallado), None)
        if clave is None:
            clave = next((k for k, fi in FIRMAS.items() if fi <= cols and k not in hallado), None)
        if clave:
            hallado[clave] = (os.path.basename(ruta), d)
    faltan = [k for k in list(FIRMAS) + list(FIRMAS_EXACTAS) if k not in hallado]
    assert not faltan, 'faltan exports en data/crm/: ' + ', '.join(faltan)
    return hallado

def _historico(ons):
    """La cartera, y dentro de ella lo que esta abierto de verdad.

    'En Curso' arrastra oportunidades que nadie cerro ni descarto: al
    14/09/2026 eran 1.411, y solo 26 de los ultimos dos anios. Sin partirlo,
    cualquier tasa de cierre sale con el denominador inflado.
    """
    f = pd.to_datetime(ons['Fecha de creación'], errors='coerce')
    est = ons['Descripción de estado'].fillna('Sin estado').astype(str).str.strip()
    corte = pd.Timestamp.today().normalize() - pd.DateOffset(months=24)
    abierta = est.str.lower() == 'en curso'
    return {
        'total': int(len(ons)),
        'desde': str(f.min().date()),
        'estado': est.value_counts().to_dict(),
        'enCursoNuevas': int((abierta & (f >= corte)).sum()),
        'enCursoViejas': int((abierta & (f < corte)).sum()),
    }


def armar(h):
    ons, con, cc, cot, env, apr, onsmes = (h[k][1] for k in ['ons', 'con', 'cc', 'cot', 'env', 'apr', 'onsmes'])
    for d, c in [(ons, 'Fecha de creación'), (con, 'Fecha de concreción'),
                 (cc, 'Fecha de creación'), (cot, 'Fecha')]:
        d['m'] = pd.to_datetime(d[c]).dt.to_period('M').astype(str)

    d2 = lambda s: pd.to_datetime(s).strftime('%d/%m')
    txt = lambda v, alt: (v if isinstance(v, str) and v.strip() else alt)
    nn = lambda v: (None if (v is None or (isinstance(v, float) and math.isnan(v))) else v)
    envm = dict(zip(env['Fecha de envío'], env['Nro. Cotización'].astype(int)))
    aprm = {r['Fecha de aprobación']: r for _, r in apr.iterrows()}

    out = {'generado': pd.Timestamp.today().strftime('%Y-%m-%d'),
           'fuentes': sorted(h[k][0] for k in h),
           'nota': ('Calculado desde los exports del CRM. Emitidas se cuenta por fecha de la '
                    'cotizacion; enviadas y aprobadas son los agregados del CRM, por fecha de '
                    'envio y de aprobacion. Son tres fechas distintas.'),
           'meses': {},
           # La cartera entera, para poner el mes contra la historia: sin esto
           # no hay tasa de cierre, solo ONs nuevas y concretadas sueltas.
           'historico': _historico(ons),
           # Series largas: son los agregados que el CRM publica en su propio
           # tablero, mes por mes, tal cual. No se recalculan desde el detalle
           # — contarian otra cosa (ver la nota de ONs de agosto).
           'series': {
               'on_mensuales': {str(r['Fecha de creación']): int(r['Empresa']) for _, r in onsmes.iterrows()},
               'cotiz_enviadas': {str(r['Fecha de envío']): int(r['Nro. Cotización']) for _, r in env.iterrows()},
               'cotiz_aprobadas': {str(r['Fecha de aprobación']): {
                   'n': int(r['Nro. Cotización']),
                   'neto_impl': float(r['Neto implementación']),
                   'neto_sop': (0.0 if (isinstance(r['Neto soporte'], float) and math.isnan(r['Neto soporte'])) else float(r['Neto soporte'])),
               } for _, r in apr.iterrows()},
           }}

    for i in range(1, 13):
        m = '%d-%02d' % (ANIO, i)
        o, c, q, k = ons[ons['m'] == m], cc[cc['m'] == m], cot[cot['m'] == m], con[con['m'] == m]
        if not len(o) and not len(c) and not len(q) and not len(k) and m not in aprm:
            continue
        a = aprm.get(m)
        out['meses'][m] = {
            'consultas': {
                'total': int(len(c)),
                'origen': c[ORI].fillna('Sin origen').value_counts().to_dict(),
                'detalle': [{'f': d2(r['Fecha de creación']), 'cliente': txt(r['Cliente'], 'Sin cliente'),
                             'contacto': txt(r['Contacto'], ''), 'origen': txt(r[ORI], 'Sin origen')}
                            for _, r in c.sort_values('Fecha de creación', ascending=False).iterrows()]},
            'ons': {
                'total': int(len(o)),
                'origen': o[ORI].fillna('Sin origen').value_counts().to_dict(),
                # En que quedaron las ONs que nacieron en el mes. Se lee hoy:
                # una ON de agosto puede seguir abierta o cerrar en noviembre.
                'estado': o['Descripción de estado'].fillna('Sin estado').value_counts().to_dict(),
                'detalle': [{'f': d2(r['Fecha de creación']), 'empresa': txt(r['Empresa'], 'Sin empresa'),
                             'origen': txt(r[ORI], 'Sin origen')}
                            for _, r in o.sort_values('Fecha de creación', ascending=False).iterrows()]},
            'cotizaciones': {
                'emitidas': int(len(q)),
                'estado': q['Descripción de estado'].fillna('Sin estado').value_counts().to_dict(),
                'enviadas': int(envm.get(m, 0)),
                'aprobadas': {'n': (int(a['Nro. Cotización']) if a is not None else 0),
                              'neto_impl': (float(a['Neto implementación']) if a is not None else 0.0),
                              'neto_sop': (nn(float(a['Neto soporte'])) if a is not None else None)},
                'detalle': [{'f': d2(r['Fecha']), 'nro': str(r['Nro. Cotización']),
                             'estado': txt(r['Descripción de estado'], 'Sin estado')}
                            for _, r in q.sort_values('Fecha', ascending=False).iterrows()]},
            'concretadas': {
                'n': int(len(k)),
                'importe': float(k['Importe total implementación'].sum()),
                'detalle': [{'f': d2(r['Fecha de concreción']), 'empresa': txt(r['Empresa'], 'Sin empresa'),
                             'origen': txt(r[ORI], 'Sin origen'),
                             'importe': float(r['Importe total implementación'])}
                            for _, r in k.sort_values('Importe total implementación', ascending=False).iterrows()]},
        }
    return out

if __name__ == '__main__':
    carpeta = os.path.join(REPO, 'data', 'crm')
    h = reconocer(carpeta)
    out = armar(h)
    dst = os.path.join(REPO, 'data', 'crm-2026.json')
    open(dst, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
    print('escrito:', dst)
    print('meses:', ', '.join(out['meses']))
    for k, (nombre, d) in sorted(h.items()):
        print('  %-4s %-60s %d filas' % (k, nombre[:60], len(d)))
