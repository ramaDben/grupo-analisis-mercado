Genera el brief de un carrusel de LinkedIn para el equipo de diseño: texto por página, copy
del post y ficha de cifras, con postura híbrida (lo que dicen los bancos al lado de lo que
dicen nuestros datos del terminal).

Uso: `/linkedin <formato> <tickers>` · ej. `/linkedin cita USDCLP` ·
`/linkedin problema_solucion XAUUSD,WTI.spot,US100.spot,USDCLP` ·
`/linkedin agenda USDCLP,XAUUSD,WTI.spot,US100.spot`

Argumentos: $ARGUMENTS

Si falta el formato o los tickers, **pregúntale al director**. Elegir el activo por cuenta
propia es decidir qué se publica.

## Qué NO hace

- **No publica en LinkedIn.** Automatizar LinkedIn va contra sus términos; el brief lo
  entrega el director a diseño y la publicación es manual.
- **No diseña.** La salida es texto y cifras; las láminas las arma diseño.
- **No es un informe institucional.** No pasa por `generar_pdf.py`: es un documento interno.

## Los tres formatos

Cada formato replica la estructura de una referencia de LinkedIn que el director eligió el
2026-09-28. Los campos de cada página están en `pipeline_linkedin.FORMATOS`, que es la
fuente única; un test verifica que este archivo nombre los tres.

| Formato | Referencia | Páginas | Activo principal |
|---|---|---|---|
| `cita` | Tarjeta de cita (DF / BTG): frase textual grande y firma | 5 | Sí, el primero de la lista |
| `problema_solucion` | Gancho, giro, método y llamada a la acción | 5 | Sí |
| `agenda` | Una página por día con hora y qué pasa (feria IACC) | 3 + una por día | No |

En `cita` y `problema_solucion`, la página de datos lleva **el mapa de niveles 🟢🟡🔴 armado
por el script con cifras medidas**. No se escribe a mano.

## PASO 1: preparar los datos

```bash
uv run --with MetaTrader5 python scripts/pipeline_linkedin.py --preparar --formato <formato> --activos <tickers>
```

El script imprime la ruta del `payload.json` que creó. **Esa carpeta es la tanda** de los
pasos siguientes: donde este archivo dice `<tanda>`, va esa ruta, no el texto literal.

Deja `data/linkedin/<fecha>_<hora>_<formato>/payload.json` con los precios, niveles y
dirección de cada activo (marco diario), la curva del Tesoro y, en `agenda`, los eventos de
impacto alto de los próximos siete días en hora de Chile. Todos los huecos editoriales dicen
`[[ESCRIBIR]]`.

Sin terminal no hay payload: el script se detiene. Un carrusel sin cifras medidas no se
prepara.

## PASO 2: la visión de los bancos

Las citas **no se escriben en el payload**: se registran en `data/visiones_expertos.json` y
la página las referencia por `id`.

1. Mira primero lo que ya hay en el registro. Una visión de menos de 45 días sirve.
2. Si falta una, búscala en la web y **abre la página de la fuente** para leer la cita, la
   fecha y la firma. Un snippet de búsqueda no es fuente: el 2026-09-28 los snippets
   mezclaban proyecciones de fechas distintas. En orden:
   - buscar: la búsqueda web del runner (WebSearch en Claude Code);
   - leer: la lectura de páginas del runner (WebFetch en Claude Code);
   - si la página bloquea (CNBC devuelve 403 a WebFetch): el navegador (MCP `playwright`).
     Abre el Chrome real del director con sus sesiones iniciadas: úsalo solo para leer la
     nota puntual, **nunca para recorrer LinkedIn** buscando opiniones (va contra sus términos).
   - muro de pago (Diario Financiero, Bloomberg): no se evade. Usa una fuente abierta que
     reproduzca la cita, o regístrala como `parafrasis` con la fuente secundaria.
   Si el runner no tiene ninguna forma de leer páginas, **detente y avísale al director**:
   una visión sin leer su fuente no se registra.
3. Regístrala con `quien`, `institucion`, `activo`, `tipo`, `cita`, `fecha` (la de
   publicación, AAAA-MM-DD), `fuente` y `url`. `tipo` es `textual` (frase exacta en
   español), `traduccion` (frase exacta traducida por nosotros, con el original en `nota`) o
   `parafrasis` (cifra o postura sin comillas).
4. Si la única visión disponible tiene más de 45 días, se puede usar solo declarándola en
   `editorial.aceptar_antiguas` con el motivo. El motivo sale impreso en el brief.

## PASO 3: escribir el texto

Rellena `editorial` del `payload.json` de la tanda con la **herramienta de edición de
archivos del runner** (Edit/Write en Claude Code; la edición de archivos nativa en AGY) o con
Python (`Path.write_text(..., encoding="utf-8")`). **Nunca por la consola de PowerShell**: se
come los `$` de los precios y rompe las tildes. No crees un script de un solo uso para esto.

- `paginas.<página>.<campo>`: el texto de cada lámina. `vision` es el `id` del registro.
- `copy`: el texto del post. Abre con la conclusión (lo que se ve antes del "ver más").
- `hashtags`: 4 o 5, terminando en `#GrupoInteligencia`.
- `remates_dia` (solo `agenda`): una línea por día sobre qué mueve ese dato.
- `cifras_citadas`: toda cifra con `$` del texto que no sea una cifra medida ni esté en una
  cita usada, con su motivo. Ej. `{"$971": "redondeo de 971,03 para el titular",
  "US$100": "umbral redondo del Brent"}`.

Reglas de voz (las mismas de todo texto de cliente):
- Dirección clara en cada activo: alcista o bajista, nunca ambiguo.
- **La postura es híbrida**: el banco dice la tesis de fondo y el plazo que mira; nuestros
  datos dicen la dirección de hoy. Cuando no coinciden, se dice cuál manda en qué plazo.
- Tuteo chileno neutro, sin voseo. Sin guion largo ni medio como inciso. Siglas explicadas
  la primera vez. Sin "bps": "puntos base" o "0,24 puntos".
- Cierre: "Análisis informativo. No constituye recomendación de inversión."

## PASO 4: rendir el brief

```bash
uv run python scripts/pipeline_linkedin.py --validar data/linkedin/<tanda>
uv run --extra informe python scripts/pipeline_linkedin.py --rendir data/linkedin/<tanda>
```

`--rendir` se detiene y lista todo lo que falta si:
- queda un `[[ESCRIBIR]]`, una visión sin elegir o un `id` que no está en el registro;
- hay guion largo o medio, voseo o un marcador sin completar;
- una cita no tiene fecha o URL, tiene fecha futura o más de 45 días sin motivo;
- **una cifra con `$` no sale del terminal, de una cita usada ni de `cifras_citadas`**;
- una cifra sin `$` (un nivel de índice, "USD 969") está a menos de 3% de un precio medido
  pero no coincide con ninguno: es la cifra de otra lectura o un nivel redondeado;
- los datos se leyeron hace más de 24 horas (vuelve a preparar; `--aceptar-datos-viejos`
  solo si el director lo pide).

**Lo que el freno NO verifica: tasas y porcentajes** (5,27%, "0,24 puntos"). Cópialos de la
tabla de tasas del brief, que usa la cotización del día si existe y si no la del archivo, con
su fecha y fuente a la vista.

Deja `brief.md` y `brief.pdf` en la carpeta de la tanda. Mira el PDF antes de darlo por
bueno: tildes, eñes, ¿, ¡ y los emoji del mapa.

## PASO 5: mostrar al director

Muestra el copy del post y la ruta del PDF. Nada sale sin su aprobación. Si el carrusel se
publica otro día, se vuelve al PASO 1.
