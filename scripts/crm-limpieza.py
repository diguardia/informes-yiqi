"""Pasa a Desestimada las ON «En Curso» con mas de dos anios de antiguedad.

Dos fases separadas a proposito: primero se lista y se mira, despues se
aplica sobre esa lista. Nada se cambia sin que el archivo exista.

    # 1. listar (no toca nada)
    YIQI_API_USER=... YIQI_API_PASS=... python3 scripts/crm-limpieza.py listar

    # 2. aplicar, de a bloques, empezando por una sola para probar
    ... python3 scripts/crm-limpieza.py aplicar --limite 1
    ... python3 scripts/crm-limpieza.py aplicar --bloque 100

El listado y el log se escriben FUERA del repo (../crm-limpieza/), porque
este repo es publico y la lista son nombres de clientes.

Que hace, exactamente:
  - Toma las OPORTUNIDAD_DE_NEGOC en estado «En Curso» cuya AUDI_FECHA_ALTA
    sea anterior a hoy menos ANIOS anios.
  - Las pasa a «Desestimada» con RANE_ID_RANE = la razon «Vencimiento».
  - La transicion exige ese campo, asi que va de a una: ChangeStateMultiple
    de la API no acepta body (YiQi.API/NOTES.md, 07/09/2026). Hibernar si
    se podria en lote, porque no exige nada.
  - Despues de cada ON escribe una linea en el log. Si se corta, se retoma:
    las que ya estan en el log no se vuelven a tocar.

Reversion: todas quedan con la misma AUDI_FECHA_MODIF, asi que la pasada se
identifica por fecha. Volverlas a «En Curso» exige contacto, origen, rubro y
responsable cargados, que en las mas viejas pueden faltar.

Credenciales: solo por variables de entorno. Nunca en un archivo del repo.
"""
import os, sys, json, time, argparse, datetime
import urllib.request, urllib.parse, urllib.error

BASE = os.environ.get('YIQI_API_BASE', 'https://api.yiqi.com.ar')
ANIOS = 2
ENTIDAD = 'OPORTUNIDAD_DE_NEGOC'
ESTADO_ORIGEN = 'En Curso'
ESTADO_DESTINO = 'Desestimada'
RAZON_NOMBRE = 'Vencimiento'

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.abspath(os.environ.get('CRM_LIMPIEZA_DIR') or
                         os.path.join(AQUI, '..', '..', 'crm-limpieza'))
LISTADO = os.path.join(SALIDA, 'por-desestimar.json')
LOG = os.path.join(SALIDA, 'aplicadas.log')


def _http(method, url, data=None, headers=None, form=False):
    body, h = None, dict(headers or {})
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
                crudo = r.read().decode()
                return json.loads(crudo) if crudo.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code == 429 and intento < 3:
                time.sleep(int(e.headers.get('Retry-After') or 2 ** (intento + 1)))
                continue
            raise RuntimeError('%s %s -> %d %s' % (method, url, e.code, e.read().decode()[:300]))


def login():
    usuario, clave = os.environ.get('YIQI_API_USER'), os.environ.get('YIQI_API_PASS')
    assert usuario and clave, 'faltan YIQI_API_USER / YIQI_API_PASS en el entorno'
    t = _http('POST', BASE + '/token',
              {'grant_type': 'password', 'username': usuario, 'password': clave}, form=True)
    h = {'Authorization': 'Bearer ' + t['access_token']}
    info = _http('GET', BASE + '/api/accountapi/GetLoginInformation', headers=h)
    return h, int(info['schemaId'])


def query(h, sid, entidad, columnas, filtros=None):
    url = '%s/api/public/%s/query?schemaId=%d' % (BASE, entidad, sid)
    filas, page = [], 1
    while True:
        r = _http('POST', url, {'page': page, 'pageSize': 1000,
                                'columns': [{'field': c} for c in columnas],
                                'filters': filtros or []}, headers=h)
        datos = r.get('data') or []
        filas.extend(datos)
        if not datos or len(filas) >= int(r.get('total') or 0):
            break
        page += 1
    return filas


def razon_id(h, sid):
    for r in query(h, sid, 'RAZON_NEGATIVA', ['ID', 'RANE_NOMBRE']):
        if (r.get('RANE_NOMBRE') or '').strip() == RAZON_NOMBRE:
            return int(r['ID'])
    raise SystemExit('No existe la razon «%s» en RAZON_NEGATIVA.' % RAZON_NOMBRE)


def listar(h, sid):
    corte = (datetime.date.today() - datetime.timedelta(days=365 * ANIOS)).isoformat()
    filas = query(h, sid, ENTIDAD,
                  ['ID', 'OPDN_NRO_ID', 'OPDN_EMPRESA', 'OPDN_TITULO',
                   'AUDI_FECHA_ALTA', 'DESC_ESTADO'],
                  [{'field': 'DESC_ESTADO', 'operator': '=', 'value': ESTADO_ORIGEN}])
    viejas = [f for f in filas if (f.get('AUDI_FECHA_ALTA') or '')[:10] < corte]
    os.makedirs(SALIDA, exist_ok=True)
    with open(LISTADO, 'w', encoding='utf-8') as fh:
        json.dump({'generado': datetime.datetime.now().isoformat(timespec='seconds'),
                   'corte': corte, 'estado_origen': ESTADO_ORIGEN,
                   'estado_destino': ESTADO_DESTINO, 'razon': RAZON_NOMBRE,
                   'total_en_curso': len(filas), 'total': len(viejas),
                   'ons': viejas}, fh, ensure_ascii=False, indent=1)
    print('En Curso: %d · con mas de %d anios: %d' % (len(filas), ANIOS, len(viejas)))
    print('listado: %s' % LISTADO)
    if viejas:
        v = sorted(viejas, key=lambda f: (f.get('AUDI_FECHA_ALTA') or ''))
        print('la mas vieja: %s (%s) · la mas nueva: %s' %
              (v[0].get('AUDI_FECHA_ALTA', '')[:10], v[0].get('OPDN_EMPRESA'),
               v[-1].get('AUDI_FECHA_ALTA', '')[:10]))


def ya_hechas():
    if not os.path.exists(LOG):
        return set()
    hechas = set()
    with open(LOG, encoding='utf-8') as fh:
        for linea in fh:
            p = linea.split('\t')
            if len(p) > 2 and p[1] == 'ok':
                hechas.add(int(p[2]))
    return hechas


def aplicar(h, sid, limite, bloque, pausa):
    if not os.path.exists(LISTADO):
        raise SystemExit('Falta %s. Corre primero: crm-limpieza.py listar' % LISTADO)
    d = json.load(open(LISTADO, encoding='utf-8'))
    rid = razon_id(h, sid)
    hechas = ya_hechas()
    pendientes = [o for o in d['ons'] if int(o['ID']) not in hechas]
    if limite:
        pendientes = pendientes[:limite]
    print('listado %s · pendientes %d · se procesan %d · razon %s (%d)'
          % (d['generado'], len(d['ons']) - len(hechas), len(pendientes), RAZON_NOMBRE, rid))
    url = '%s/api/public/%s/ChangeState' % (BASE, ENTIDAD)
    ok = err = 0
    with open(LOG, 'a', encoding='utf-8') as log:
        for i, o in enumerate(pendientes, 1):
            oid = int(o['ID'])
            ahora = datetime.datetime.now().isoformat(timespec='seconds')
            try:
                _http('POST', '%s?schemaId=%d&id=%d&state=%s'
                      % (url, sid, oid, urllib.parse.quote(ESTADO_DESTINO)),
                      {'RANE_ID_RANE': rid}, headers=h)
                log.write('%s\tok\t%d\t%s\t%s\n' % (ahora, oid, o.get('OPDN_NRO_ID'),
                                                    (o.get('OPDN_EMPRESA') or '')[:60]))
                ok += 1
            except Exception as e:
                log.write('%s\terror\t%d\t%s\t%s\n' % (ahora, oid, o.get('OPDN_NRO_ID'), str(e)[:200]))
                err += 1
                print('  error en %d: %s' % (oid, str(e)[:160]))
            log.flush()
            if bloque and i % bloque == 0:
                print('  %d/%d · ok %d · error %d · pausa %ss' % (i, len(pendientes), ok, err, pausa))
                time.sleep(pausa)
    print('listo: ok %d · error %d · log %s' % (ok, err, LOG))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fase', choices=['listar', 'aplicar'])
    p.add_argument('--limite', type=int, default=0, help='cuantas procesar (0 = todas las pendientes)')
    p.add_argument('--bloque', type=int, default=100, help='cada cuantas informar y pausar')
    p.add_argument('--pausa', type=float, default=2, help='segundos de pausa entre bloques')
    a = p.parse_args()
    h, sid = login()
    if a.fase == 'listar':
        listar(h, sid)
    else:
        aplicar(h, sid, a.limite, a.bloque, a.pausa)


if __name__ == '__main__':
    main()
