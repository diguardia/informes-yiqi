# Sincronización de comercial.html con la Marketing API de Meta

`comercial.html` ya no necesita que le escribas los números de Meta a mano. Un
workflow de GitHub Actions consulta la API una vez por día, deja los datos en
`data/meta.json`, y el informe los lee al abrirse.

## Qué se actualiza solo

Los KPIs de **Resumen Meta** (alcance, conversaciones iniciadas, gasto,
interacciones y clics en enlace), el **gráfico de evolución mensual** y la
**tabla y el gráfico de Anuncios**. Los meses aparecen solos: cuando arranque
agosto, el filtro de período suma el botón "Ago" sin que toques nada, y el
subtítulo pasa a mostrar el rango hasta el día de la última sincronización.

## Qué sigue siendo manual

**Contactos nuevos.** No existe en la API de Ads: viene del panel de Meta
Business Suite, que suma orgánico más pauta. Se carga en el objeto
`CONTACTOS_MANUALES` dentro de `comercial.html`, con la clave del mes:

```js
const CONTACTOS_MANUALES = {
  may: 86,
};
```

Todo lo del CRM — Funnel, Nuevas ONs, ONs Concretadas — tampoco pasa por acá.

## Puesta en marcha

**1. Generar el token.** En Business Manager, en Configuración del negocio →
Usuarios → Usuarios del sistema, creá o elegí un usuario del sistema, asignale
la cuenta publicitaria con permiso de lectura y generá un token con el permiso
`ads_read`. Usá un usuario del sistema y no tu usuario personal: el token de
usuario común vence a los sesenta días y la sincronización se corta sola.

**2. Poner el workflow en su lugar.** El archivo del workflow quedó en
`scripts/github-workflow-meta.yml` porque las herramientas remotas no pueden
escribir dentro de `.github/`. Movelo a mano:

```
mkdir -p .github/workflows
mv scripts/github-workflow-meta.yml .github/workflows/meta.yml
```

**3. Guardar el token como secreto.** En el repositorio, Settings → Secrets and
variables → Actions → New repository secret, con nombre `META_TOKEN`.

Opcionalmente podés definir las variables `META_AD_ACCOUNT_ID` y
`META_API_VERSION` en la pestaña Variables de la misma pantalla. Si no las
definís, se usan `370211010327709` y `v25.0`.

**4. Correrlo la primera vez a mano.** En la pestaña Actions, elegí el workflow
*Meta · sincronizar informe comercial* y usá el botón *Run workflow*. Si termina
en verde, va a aparecer `data/meta.json` en el repositorio.

**5. Verificar en el informe.** Abrí `informes.yiqi.com.ar/comercial.html` y
mirá el extremo derecho de la barra de período. Si dice `API · 26-jul, 06:03`,
está leyendo el JSON. Si dice `datos embebidos`, no lo encontró y está usando
los valores escritos en el archivo.

## Nunca poner el token en el HTML

El repositorio se publica por GitHub Pages en `informes.yiqi.com.ar`. Cualquier
cosa que esté en `comercial.html` es pública, incluido un token. Con un token de
la cuenta publicitaria, un tercero puede leer y gastar. El token vive en los
secretos del repositorio y solo lo ve el runner de Actions.

## Cada cuánto se actualiza

Una vez por día, a las 09:00 UTC (06:00 en Buenos Aires). Los cron de GitHub
pueden demorarse algunos minutos cuando la plataforma está cargada. Para más
frecuencia, cambiá el `cron` en `.github/workflows/meta.yml` a `'0 */6 * * *'`,
teniendo en cuenta que cada corrida que encuentre diferencias genera un commit.

Si necesitaras datos **en vivo al abrir**, y no del último cierre diario, el
camino es un proxy — por ejemplo un Worker de Cloudflare que guarde el token y
al que el HTML le pegue directo. Es una pieza más de infraestructura para
mantener; el cron diario evita ese costo.

## Si algo falla

El informe nunca se rompe: si `data/meta.json` no está, está vacío o no se puede
leer, `comercial.html` usa los valores embebidos y lo avisa en la barra de
período. Para ver qué pasó, entrá al log de la corrida en la pestaña Actions. Un
error de la Graph API aparece con su código y su mensaje. Los dos más frecuentes
son el token vencido y la versión de la API ya retirada: en ese caso, actualizá
la variable `META_API_VERSION`.

## Archivos

`scripts/fetch-meta.mjs` consulta la API y escribe el JSON con números crudos,
sin decidir formato. El workflow que lo corre y commitea se instala en
`.github/workflows/meta.yml`. `data/meta.json` es la salida, generada por el workflow. En
`comercial.html`, la función `hydrateMeta()` convierte esos números en lo que
dibuja el informe, y `loadMetaJSON()` es la que hace el pedido.
