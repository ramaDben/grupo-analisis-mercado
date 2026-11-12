Prepara el lienzo del webinar diario: refresca las cifras de MT5, escribe el editorial con fuente
y rinde `lienzo.html` y `lienzo.pdf`. No envía nada: el lienzo lo proyecta el director.

Uso: `/webinar` (hoy) · `/webinar AAAA-MM-DD` (otra fecha, por ejemplo el día de mañana).

Argumentos: $ARGUMENTS

Lienzo y guion: `config/webinar.json` (`dias.<día>.guion` fija el recorrido de ←/→/espacio),
`scripts/webinar/preparar.py`, `scripts/webinar/rendir.py` y `templates/webinar/lienzo.html`.
Lee `.agents/rules/proyecto.md` si no tienes `CLAUDE.md` a mano: las reglas de abajo salen de ahí.

## Reglas que no se negocian
- **Cero precios escritos a mano (Regla 1).** Los niveles salen de MT5 vía `preparar.py`. En el
  editorial no va ningún precio ni nivel técnico.
- **Cada afirmación lleva fuente.** Una cita se coteja palabra por palabra contra el documento
  primario (comunicado, transcripción oficial). Lo que sea interpretación tuya no entra: ni
  "firme", ni "duro", ni "el dólar no la acompaña". Se escribe lo comprobado.
- **Sin guion largo** (`—`, `–`) en ningún texto de cliente. Para "3,75 % y 4 %" usa espacio no
  separable (U+00A0). El validador lo exige.
- **Tono cercano, sin dramatizar**, en tuteo chileno neutro. Toda sigla se explica en simple.
- **Hora de Chile con el reloj del sistema** (PowerShell o zoneinfo), nunca con offsets fijos ni
  `TZ=` en Git Bash.
- **Texto con acentos o precios por Python o `Write`**, nunca por la consola de PowerShell.
- **Un evento futuro va en modo anticipación**, no en pasado.

## Pasos

### 1. Contexto
Obtén fecha y hora de Chile. Resuelve el día (`dias.<día>` en `config/webinar.json`); si la fecha
cae en un día sin entrada, dilo y detente. Revisa que el protocolo `gi-mt5://` esté registrado
(`reg query HKCU\Software\Classes\gi-mt5`); si no, avisa que el botón "Abrir MT5" no abrirá nada
y que se arregla con `scripts/webinar/registrar_mt5.ps1`.

### 2. Cifras de MT5
```bash
uv run --with MetaTrader5 python scripts/webinar/preparar.py [--fecha AAAA-MM-DD]
```
Se detiene si MT5 no responde: **no rindas con datos viejos**, avisa. Lee `datos.json` y anota la
hora (`meta.generado`) y la dirección y estado de cada activo. Si cambió algo respecto del
editorial del día (por ejemplo un activo pasó de lateral a tendencia), revisa que el texto no lo
contradiga.

### 3. Editorial
Si ya existe `data/webinar/<fecha>/editorial.json` y sigue vigente, **se conserva**: solo se
rehace si el tema del día cambió. Si no existe o hay que rehacerlo:
1. Busca el hecho del día en la **fuente oficial** (Fed, BCE, BCCh, BLS, EIA). Para el calendario
   usa `obtener_calendario_macro`; para noticias, WebSearch solo como puntero y la fuente
   primaria como respaldo. Una transcripción de video (Gemini) se coteja contra el documento.
2. Si la fuente primaria todavía no está publicada, **no inventes contenido**: rinde con lo que
   sí tiene fuente y deja dicho qué falta.
3. Escribe el editorial con Python o `Write`. Los campos y límites los define `validar_editorial`
   en `scripts/webinar/rendir.py`: léela antes de escribir. Secciones: `noticia`, `bancos`,
   `contexto` (opcional, 1 a 3 citas con `es` y `original`), `teoria` y `notas_guion`.
4. El tema debe llevar a los gráficos: el foco del webinar es operar en vivo en MT5.

### 4. Rendir y validar
```bash
uv run --extra stories python scripts/webinar/rendir.py --fecha AAAA-MM-DD --pdf
uv run pytest tests/test_webinar.py -q
```
Si el validador rechaza algo, corrige el editorial; nunca relajes el validador.

### 5. Revisión visual
Levanta el HTML por HTTP (Playwright bloquea `file://`) con `python -m http.server <puerto>` en la
carpeta del día, revisa a 1533×862 cada lámina del guion (portada, noticia, contexto, teoría,
MT5, cierre) y confirma que ningún control flotante se monta sobre una lámina. Al terminar, detén
**solo** ese proceso (selecciónalo por su línea de comandos; nunca un `taskkill` masivo) y borra
las capturas temporales. Abre `lienzo.html` para el director.

### 6. Reporte
Dile al director, en pocas líneas:
- A qué hora quedaron las cifras de MT5 y que son una foto de ese momento.
- Dirección y estado de cada activo de la lámina MT5.
- Qué láminas llevan fuente y cuál; qué no se pudo verificar.
- Resultado de las pruebas.
- Cómo navegar: ←/→/espacio sigue el guion, `↑`/`↓` recorre todas las láminas, `O` abre la vista
  general.

No commitees ni publiques sin que lo pida.
