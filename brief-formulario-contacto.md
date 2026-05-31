# Brief — Endpoint formulario de contacto

> Para Andrés · de Sebastián · 28 may 2026
> **Estado: endpoint implementado y funcionando.** Solo quedan 2 confirmaciones técnicas tuyas para que la creación automática de ON en CRM funcione end-to-end.

---

## Resumen rápido

- **Frontend (`contacto.html` y form hero de `index.html`)**: ya hacen `POST /api/contact` con el JSON del formulario. Tienen fallback a localStorage si el endpoint no responde. Redirigen a `/gracias.html?from=*` post-submit. **Listo.**
- **Backend (`server.js`)**: sumé el handler `POST /api/contact`. Valida, guarda a `contact-submissions.jsonl` (red de seguridad), intenta crear la ON en YiQi API, responde 200. **Listo y probado.**
- **CTAs Meta**: están desactivados hasta confirmar punto 1+2 abajo. Cuando confirmemos, los reactivo.

---

## Qué hace el endpoint hoy

```
POST /api/contact (Content-Type: application/json)

1. Lee body con límite de 32 KB → 400 si JSON inválido
2. Valida campos requeridos: nombre, apellido, email, empresa, mensaje
   → 400 si falta algo o el email tiene formato inválido
3. Persiste el payload en contact-submissions.jsonl  ← red de seguridad
4. Intenta crear ON en YiQi (best-effort):
   - Usa el patrón de auth/token cacheado ya existente en server.js
   - POST a {publicBaseUrl}/{CONTACT_ENTITY}/insert?schemaId={schemaId}
   - Si falla → re-loguea con onError y responde igual 200 al cliente
5. Responde:
   - { ok: true, id: <on_id>, crm: "synced" }     si se creó la ON
   - { ok: true, id: null,    crm: "deferred" }   si falló (data ya está en jsonl)
```

**Cliente nunca ve un error técnico.** El usuario siempre llega a `/gracias.html` y la data queda persistida sí o sí.

---

## Pruebas que ya hice (sandbox)

| Caso | Resultado |
|---|---|
| Payload válido | `200 {ok:true, crm:"deferred"}` + 1 línea en jsonl |
| Faltan campos | `400 {ok:false, error:"Campo requerido: email"}` |
| Email inválido | `400 {ok:false, error:"Email con formato inválido"}` |
| JSON corrupto | `400 {ok:false, error:"Invalid JSON: ..."}` |
| Falla creación ON | re-log con `onError`, igual 200 al cliente |

---

## Lo que necesito confirmar con vos (2 cosas)

### 1. Nombre de la entidad para crear ONs

Hoy el endpoint apunta a:
```
{publicBaseUrl}/ONS/insert?schemaId={schemaId}
```

¿Es correcto `ONS` o la entidad se llama distinto (por ejemplo `OPORTUNIDADES`, `ON`, `LEADS`)?

Si es otro nombre, lo seteamos via variable de entorno **sin tocar código**:
```bash
export YIQI_CONTACT_ENTITY=OPORTUNIDADES
```

### 2. Mapeo de campos del registro

Hoy en `buildOnPayloadFromContact()` el body que mando a la API es:
```js
{
  record: {
    EMPRESA:           "...",
    CONTACTO_NOMBRE:   "Nombre Apellido",
    CONTACTO_EMAIL:    "...",
    CONTACTO_TELEFONO: "...",
    ORIGEN:            "Web yiqi.com.ar (contacto|hero)",
    PAIS:              "...",
    TITULO:            "Contacto web — <empresa>",
    DESCRIPCION:       "<mensaje>\n\nRubros: ...\nMódulos: ...\nEmpleados: ...\n¿Cómo nos conoció?: ..."
  }
}
```

¿Los nombres de columna en la entidad ON son esos, o son otros (ej. `EMP`, `CONT_NOM`, `EMAIL`, etc.)? Si son distintos, me decís cuáles y los ajusto en `buildOnPayloadFromContact()` en una sola edición. Lo mismo si la API espera el body sin el wrapper `record`.

---

## Cómo probarlo vos

```bash
cd www.yiqi
node server.js
# en otra terminal:
curl -X POST http://localhost:8080/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Andrés",
    "apellido": "Test",
    "email": "andres@yiqi.com.ar",
    "empresa": "YiQi",
    "mensaje": "Probando el endpoint",
    "celular": "+54 11 0000 0000",
    "pais": "Argentina",
    "rubros": ["Servicios"],
    "modulos": ["Ventas"],
    "meta": { "form": "contacto" }
  }'
```

Mirá la consola del server — vas a ver el error real de la API YiQi (status code + body) si el mapeo está mal. Con eso ajustamos.

Y revisás `contact-submissions.jsonl` — ahí va a estar el payload que mandaste, con `_server.receivedAt` y, si falló, con `_server.onError`.

---

## Variables de entorno disponibles (todas opcionales con default razonable)

```bash
YIQI_API_AUTH_URL=https://api.yiqi.com.ar/token       # endpoint de auth
YIQI_API_PUBLIC_BASE_URL=https://api.yiqi.com.ar/api/public  # base de la API
YIQI_API_SCHEMA_ID=1387                                # schemaId del CRM
YIQI_API_USER=cristal@yiqi.com.ar                      # usuario API
YIQI_API_PASSWORD=...                                  # password API
YIQI_CONTACT_ENTITY=ONS                                # ← este es nuevo: nombre de entidad para crear ONs
```

---

## Checklist final

- [ ] Confirmar nombre real de la entidad (`YIQI_CONTACT_ENTITY`)
- [ ] Confirmar/ajustar nombres de campos en `buildOnPayloadFromContact()`
- [ ] Probar end-to-end: que aparezca una ON nueva en CRM
- [ ] Reactivar CTAs de Meta apuntando a `https://yiqi.com.ar/contacto.html`
- [ ] (Opcional, más adelante) Sumar Meta Conversions API server-side desde el handler para reforzar el tracking de Lead
