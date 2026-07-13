# Conectar la encuesta al Google Sheet

Flujo: el formulario (HTML) envía cada respuesta → un Web App de Apps Script → agrega una fila en el Sheet.

**Sheet de respuestas:** https://docs.google.com/spreadsheets/d/1lZU_j6U_ke1gDfcvRmn4-Mx-Fvoxj3osWWRXrk3j54E/edit

## Pasos (una sola vez)

1. Abrí el Sheet → menú **Extensiones → Apps Script**.
2. Borrá el contenido de `Código.gs` y pegá todo el contenido de **`encuesta-appscript.gs`**. Guardá (💾).
3. Botón **Implementar → Nueva implementación**.
   - Tipo: **Aplicación web** (ícono de engranaje → "Aplicación web").
   - **Ejecutar como:** Yo (tu cuenta).
   - **Quién tiene acceso:** **Cualquiera**.
   - **Implementar** → autorizá los permisos cuando lo pida (es tu propio script; Google avisa que "no está verificado", elegí *Configuración avanzada → Ir a (proyecto)*).
4. Copiá la **URL del Web App** (termina en `/exec`).
5. Abrí `encuesta-experiencia-yiqi.html` y pegá esa URL en la línea:
   ```js
   const SHEET_ENDPOINT = '';   // ← pegar acá la URL /exec
   ```
6. Guardá y volvé a publicar el HTML en `informes-yiqi`.

## Verificación

- Pegá la URL `/exec` en el navegador: debería responder `{"ok":true,"service":"Encuesta YiQi",...}`.
- Completá la encuesta de punta a punta: al enviar, debería aparecer una fila nueva en la pestaña **Respuestas**.
- La primera fila (encabezados) se crea sola en el primer envío.

## Columnas (orden)

Fecha/hora · Empresa · Nombre y apellido · Email · Área · Área — Otra (especificar) · Frecuencia de uso · NPS (0–10) · Atención del equipo · Tiempos de respuesta · Resolución de consultas · Acompaña necesidades · Aspecto a mejorar primero · Aspecto a mejorar — Otro (especificar) · Funcionalidades a incorporar · Funcionalidades — Otra (especificar) · Proyecto próximos 12 meses · Qué valora de YiQi · Qué mejorar

## Notas

- Las preguntas de opción múltiple (Área, Aspecto a mejorar, Funcionalidades) se guardan en una sola celda separadas por `; `.
- El envío usa `mode:'no-cors'`: el formulario no lee la respuesta del script, solo dispara el guardado. Por eso la pantalla de "¡Gracias!" aparece siempre, aunque el Sheet esté mal configurado. Verificá con una prueba real.
- Si cambiás el script, tenés que crear una **Nueva implementación** (o "Gestionar implementaciones" → editar) para que la URL tome los cambios.
