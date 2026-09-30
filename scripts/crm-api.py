"""Arma data/crm-2026.json leyendo el CRM por la API de YiQi.

Reemplaza a los siete exports manuales de crm-json.py: consulta las tres
entidades del esquema Comercial/CRM y arma los mismos siete DataFrames, con
los mismos nombres de columna, y llama al mismo armar(). El JSON que sale es
identico en estructura, asi que comercial.html no cambia.

Se corre desde la raiz del repo:

    YIQI_API_USER=... YIQI_API_PASS=... python3 scripts/crm-api.py

Las credenciales van SOLO por variables de entorno (en local, en la terminal;
en GitHub Actions, como secretos). Nunca en un archivo del repo.

Fuentes (yiqi-api-doc/llms.txt y los swaggers que paso Andres el 30/09/2026):
  POST /token                            grant_type=password
  GET  /api/accountapi/GetLoginInformation  -> schemaId
  POST /api/public/<ENTIDAD>/query       columnas + filtros, pageSize max 1000

Como se reconstruye cada export:
  ONs - Detalle con estado    OPORTUNIDAD_DE_NEGOC, todas
  ONs Concretadas - DETALLE   las mismas, DESC_ESTADO = 'Concretada'
                              (verificado 30/09: 459 = 459 en el export del 14/09)
  Consulta comercial          CONSULTA_COMERCIAL, todas
  Cotizaciones (default)      COTIZACION_COMERCIAL, todas
  Cotiz. enviadas             conteo por mes de COCO_FECHA_DE_ENVIO
  Cotiz. aprobadas            conteo y netos por mes de COCO_FECHA_DE_APROBACION,
                              solo las que siguen en estado Aprobada
  Nuevas ON mensuales         ONs por mes de creacion, el mismo numero que el
                              titular del reporte. El tablero del CRM contaba
                              empresas distintas (20 de 21 meses del export del
                              14/09; agosto daba 8 y nada lo reproduce) y el
                              reporte mostraba dos cifras para lo mismo.
"""
import os, sys, json, time
import urllib.request, urllib.parse, urllib.error
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
crm_json = importlib.import_module('crm-json')   # el archivo tiene guion
armar, REPO = crm_json.armar, crm_json.REPO

BASE = os.environ.get('YIQI_API_BASE', 'https://api.yiqi.com.ar')
ORI = 'Origen del Contacto - Origen del Contacto'


def _http(method, url, data=None, headers=None, form=False):
    body = None
    h = dict(headers or {})
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            h['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            body = json.dumps(data).encode()
            h['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    for intento in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429 and intento < 3:
                espera = int(e.headers.get('Retry-After') or 2 ** (intento + 1))
                time.sleep(espera)
                continue
            raise RuntimeError('%s %s -> %d %s' % (method, url, e.code, e.read().decode()[:300]))


def login():
    usuario, clave = os.environ.get('YIQI_API_USER'), os.environ.get('YIQI_API_PASS')
    assert usuario and clave, 'faltan YIQI_API_USER / YIQI_API_PASS en el entorno'
    t = _http('POST', BASE + '/token',
              {'grant_type': 'password', 'username': usuario, 'password': clave}, form=True)
    h = {'Authorization': 'Bearer ' + t['access_token']}
    info = _http('GET', BASE + '/api/accountapi/GetLoginInformation', headers=h)
    return h, int(info['schemaId']), info.get('schemaName')


def query(h, schema_id, entidad, columnas, filtros=None):
    """Trae todas las paginas de /query. Devuelve lista de dicts."""
    url = '%s/api/public/%s/query?schemaId=%d' % (BASE, entidad, schema_id)
    filas, page = [], 1
    while True:
        r = _http('POST', url, {
            'page': page, 'pageSize': 1000,
            'columns': [{'field': c} for c in columnas],
            'filters': filtros or [],
        }, headers=h)
        datos = r.get('data') or []
        filas.extend(datos)
        if not datos or len(filas) >= int(r.get('total') or 0):
            break
        page += 1
    return filas


def traer(h, sid):
    ons = pd.DataFrame(query(h, sid, 'OPORTUNIDAD_DE_NEGOC', [
        'OPDN_NRO_ID', 'CONT_NOMBRE', 'OPDN_EMPRESA', 'OPDN_TITULO', 'ORCO_ORIGENCONTACTO',
        'CAMP_NOMBRE', 'AUDI_FECHA_ALTA', 'DESC_ESTADO',
        'OPDN_IMPORTE_TOTAL_IMPLEM', 'OPDN_ANTICIPO', 'OPDN_FECHA_DE_CONCRECION']))
    cc = pd.DataFrame(query(h, sid, 'CONSULTA_COMERCIAL', [
        'COCO_CONTACTO', 'COCO_CLIENTE', 'COCO_TELEFONO', 'COCO_MAIL', 'ORCO_ORIGENCONTACTO',
        'AUDI_FECHA_ALTA', 'DESC_ESTADO']))
    cot = pd.DataFrame(query(h, sid, 'COTIZACION_COMERCIAL', [
        'COCO_RAIZ', 'COCO_VERSION', 'COCO_NRO_COTIZACION', 'COCO_FECHA',
        'AUDI_FECHA_ALTA', 'DESC_ESTADO', 'COCO_FECHA_DE_ENVIO', 'COCO_FECHA_DE_APROBACION',
        'COCO_NETO_IMPLEMENTACION', 'COCO_NETO_SOPORTE']))
    return ons, cc, cot


def a_exports(ons, cc, cot):
    """Los siete DataFrames con los nombres de columna de los exports del CRM."""
    fecha = lambda s: pd.to_datetime(s, errors='coerce')
    mes = lambda s: fecha(s).dt.to_period('M').astype(str)

    ons_x = pd.DataFrame({
        'Nro ID': ons['OPDN_NRO_ID'], 'Contacto - Nombre': ons['CONT_NOMBRE'],
        'Empresa': ons['OPDN_EMPRESA'], 'Título': ons['OPDN_TITULO'],
        ORI: ons['ORCO_ORIGENCONTACTO'], 'Campaña - Nombre ': ons['CAMP_NOMBRE'],
        'Fecha de creación': fecha(ons['AUDI_FECHA_ALTA']),
        'Descripción de estado': ons['DESC_ESTADO']})

    k = ons[ons['DESC_ESTADO'] == 'Concretada']
    con_x = pd.DataFrame({
        'Empresa': k['OPDN_EMPRESA'], ORI: k['ORCO_ORIGENCONTACTO'],
        'Importe total implementación': pd.to_numeric(k['OPDN_IMPORTE_TOTAL_IMPLEM'], errors='coerce').fillna(0.0),
        'Anticipo (si es distinto)': pd.to_numeric(k['OPDN_ANTICIPO'], errors='coerce'),
        'Fecha de concreción': fecha(k['OPDN_FECHA_DE_CONCRECION'])}).reset_index(drop=True)

    cc_x = pd.DataFrame({
        'Contacto': cc['COCO_CONTACTO'], 'Cliente': cc['COCO_CLIENTE'],
        'Teléfono': cc['COCO_TELEFONO'], 'Mail': cc['COCO_MAIL'],
        ORI: cc['ORCO_ORIGENCONTACTO'],
        'Fecha de creación': fecha(cc['AUDI_FECHA_ALTA']),
        'Descripción de estado': cc['DESC_ESTADO']})

    cot_x = pd.DataFrame({
        'Raíz': cot['COCO_RAIZ'], 'Versión': cot['COCO_VERSION'],
        'Nro. Cotización': cot['COCO_NRO_COTIZACION'], 'Fecha': fecha(cot['COCO_FECHA']),
        # PROY_NOMBRE figura en el swagger pero la API lo rechaza (30/09:
        # "Column PROY_NOMBRE not found"). armar() no lo usa.
        'Centro de costos - Nombre': None,
        'Fecha de creación': fecha(cot['AUDI_FECHA_ALTA']),
        'Descripción de estado': cot['DESC_ESTADO']})

    # Las series largas arrancan donde arrancaban los exports del tablero
    # (ONs desde 2025-01, cotizaciones desde 2025-07): la API trae historia
    # desde 2014 y el grafico de comercial.html no recorta por abajo.
    DESDE_ON, DESDE_COT = '2025-01', '2025-07'
    valido = lambda m: m.notna() & (m != 'NaT')

    env = cot[cot['COCO_FECHA_DE_ENVIO'].notna()].assign(m=lambda d: mes(d['COCO_FECHA_DE_ENVIO']))
    env = env[valido(env['m']) & (env['m'] >= DESDE_COT)]
    env_x = (env.groupby('m').size().rename('Nro. Cotización').reset_index()
             .rename(columns={'m': 'Fecha de envío'})[['Nro. Cotización', 'Fecha de envío']])

    # Aprobadas: las que HOY siguen en estado Aprobada, por fecha de aprobacion.
    # Una versionada o rechazada despues de aprobarse conserva la fecha pero el
    # tablero no la cuenta. Verificado 30/09 contra el export del 14/09: 13 de
    # 14 meses exactos (contando todas las que tienen fecha, 11 de 14).
    apr = cot[cot['COCO_FECHA_DE_APROBACION'].notna() & (cot['DESC_ESTADO'] == 'Aprobada')]
    apr = apr.assign(m=lambda d: mes(d['COCO_FECHA_DE_APROBACION']))
    apr = apr[valido(apr['m']) & (apr['m'] >= DESDE_COT)]
    apr['ni'] = pd.to_numeric(apr['COCO_NETO_IMPLEMENTACION'], errors='coerce')
    apr['ns'] = pd.to_numeric(apr['COCO_NETO_SOPORTE'], errors='coerce')
    g = apr.groupby('m')
    apr_x = pd.DataFrame({
        'Neto implementación': g['ni'].sum(min_count=1),
        'Neto soporte': g['ns'].sum(min_count=1),
        'Nro. Cotización': g.size(),
    }).reset_index().rename(columns={'m': 'Fecha de aprobación'})

    om = ons_x.assign(m=mes(ons_x['Fecha de creación']))
    om = om[valido(om['m']) & (om['m'] >= DESDE_ON)]
    # Una fila por ON, igual que el titular del reporte ("16 ONs nuevas").
    # El tablero del CRM contaba empresas distintas (13 en agosto) y el
    # reporte mostraba los dos numeros. Decision de Seba, 30/09/2026.
    onsmes_x = (om.groupby('m').size().rename('Empresa').reset_index()
                .rename(columns={'m': 'Fecha de creación'})[['Empresa', 'Fecha de creación']])

    return {'ons': ('API OPORTUNIDAD_DE_NEGOC', ons_x), 'con': ('API OPORTUNIDAD_DE_NEGOC (Concretada)', con_x),
            'cc': ('API CONSULTA_COMERCIAL', cc_x), 'cot': ('API COTIZACION_COMERCIAL', cot_x),
            'env': ('API COTIZACION_COMERCIAL (fecha de envio)', env_x),
            'apr': ('API COTIZACION_COMERCIAL (fecha de aprobacion)', apr_x),
            'onsmes': ('API OPORTUNIDAD_DE_NEGOC (ONs por mes)', onsmes_x)}


if __name__ == '__main__':
    h, sid, nombre = login()
    print('esquema:', sid, nombre)
    ons, cc, cot = traer(h, sid)
    print('filas: ONs %d · consultas %d · cotizaciones %d' % (len(ons), len(cc), len(cot)))
    if os.environ.get('CRM_RAW_OUT'):
        # Volcado crudo de las tres entidades, para auditar criterios de conteo.
        open(os.environ['CRM_RAW_OUT'], 'w', encoding='utf-8').write(json.dumps(
            {'ons': ons.to_dict('records'), 'cc': cc.to_dict('records'), 'cot': cot.to_dict('records')},
            ensure_ascii=False, default=str))
        print('crudo:', os.environ['CRM_RAW_OUT'])
    hallado = a_exports(ons, cc, cot)
    out = armar(hallado)
    out['nota'] = ('Calculado desde la API de YiQi (Comercial/CRM). Emitidas se cuenta por fecha de la '
                   'cotizacion; enviadas por fecha de envio y aprobadas por fecha de aprobacion. '
                   'Son tres fechas distintas. Aprobadas son las que siguen en estado Aprobada. '
                   'Nuevas ON mensuales cuenta ONs por mes, igual que el titular.')
    dst = os.environ.get('CRM_JSON_OUT') or os.path.join(REPO, 'data', 'crm-2026.json')
    open(dst, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
    print('escrito:', dst)
    print('meses:', ', '.join(out['meses']))
