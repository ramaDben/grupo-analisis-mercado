# Radar multifractal: qué mirar cada mañana

Fecha: 2026-10-26 · Estado: propuesta para aprobación del director (decisiones de §5 y §7 ya tomadas) · Rama: `feat/radar-multifractal`
Recon del repo: Antigravity (agy, solo lectura); verificación y diseño: Claude Code.

## 1. Intención

El director opera la multifractalidad: busca entradas donde el precio toca o se acerca a una
línea en varios marcos a la vez. Hoy tiene que abrir gráfico por gráfico para saberlo. El radar
le dice **qué gráfico abrir cada mañana**: una página HTML con los activos que tienen actividad
reciente sobre sus líneas, en 1H, 4H y 1D. **No arma el setup ni recomienda la operación**: el
setup lo construye el director en MT5 con `GI_Canales_Seguridad`.

Es una herramienta **interna del director** (cockpit), no una pieza de cliente. No pasa por el
flujo de aprobación porque no publica nada.

## 2. Objetivos, no objetivos y anti objetivos

**Objetivos**
- Escanear **todo el universo operable del terminal** (~137 símbolos: FX, acciones `#`, ETF `.US`,
  cripto) en **1H, 4H y 1D**.
- Por activo y marco, detectar eventos sobre **tres tipos de línea**: seguridad, acción y zonas S/R.
- Dos tipos de evento: **tocó** (la última vela cerrada de ese marco) y **por tocar** (a 3 velas o
  menos, sección 5).
- Mostrar una **matriz activo × marco** (boceto B aprobado), ordenada por confluencia.
- Correr **sola a las 07:30 hora de Santiago**, lunes a viernes.

**No objetivos**
- No envía nada a WhatsApp, Telegram ni clientes. No toca `enviar_whatsapp.py`.
- No calcula entrada, stop ni objetivo. No puntúa ni rankea como el escáner del carrusel.
- No modifica el indicador MQL5 (`mql5/GI_Canales_Seguridad.mq5` tiene cambios sin commitear del
  director; no se toca en este trabajo).

**Anti objetivos (lo que lo haría un fracaso aunque "funcione")**
- **Que la matriz contradiga al gráfico.** Si dice "tocó seguridad 4H" y en MT5 la línea está en
  otro lado, el director deja de confiar. Ver sección 7 (paridad).
- **Una segunda implementación de los roles.** Qué diagonal es seguridad y cuál es acción lo
  decide `_estructura` de Tori; el radar no lo vuelve a decidir por su cuenta.
- **Una matriz vacía convincente.** "0 activos con actividad" porque MT5 no respondió es peor que
  fallar. La página distingue siempre "no hubo actividad" de "no se pudo leer".

## 3. Cómo se ve (aprobado en boceto)

Encabezado: fecha, hora del escaneo en Chile, símbolos leídos, con actividad, que fallaron, y la
cuenta MT5 que produjo los datos.

Matriz: una fila por activo **con al menos un evento**; columnas Confluencia, 1H, 4H, 1D. Junto al
nombre, la dirección (⬆️ ⬇️ ↔️) del marco mayor con lectura. Cada celda muestra el evento más
urgente como franja de color (verde seguridad `#26C6A0`, rojo acción `#FF4D5E`, ámbar S/R
`#FFD54F`, la paleta del indicador) con "✅ tocó" o "a N velas", más calidad (A+/B) o rol
(soporte/resistencia); el resto de eventos de la celda, plegados ("+1 evento"). Cada celda estampa
la **hora de la última vela cerrada** que leyó: a las 07:30 el "tocó" 1D de una acción es de ayer.

Al pie: activos que no se pudieron leer, con el motivo. Leyenda de colores y de qué significa
"tocó" y "N velas".

Orden de filas (**decisión de Claude, calibrable**): primero por número de marcos con evento
(3, 2, 1); a igualdad, los que tienen un "tocó" antes que los que solo tienen "por tocar"; luego
por menor número de velas. La confluencia de dirección entre marcos se muestra pero no reordena
en la v1.

## 4. Arquitectura

```
Programador de tareas (07:30 L-V)
  └─ uv run --with MetaTrader5 python scripts/radar_multifractal.py
       ├─ guardrails/cuenta.py      → verifica la cuenta declarada (51257)
       ├─ universo: mt5.symbols_get(), trade_mode FULL   (patrón de simulador_gi.py)
       ├─ por símbolo: velas H1/H4/D1/W1 vía mt5_client.get_rates, sin la vela en curso
       ├─ estrategia/tori/radar.py  → eventos por marco (dentro del motor)
       └─ HTML → data/radar/<AAAA-MM-DD>/radar_<HH-MM>.html  (+ data/radar/ultimo.html)
```

### 4.1 El cálculo vive dentro del motor
Archivo nuevo **`scripts/estrategia/tori/radar.py`**, con una función pública del estilo
`eventos(velas, marco, digits, p) -> list[Evento]`. Reutiliza, sin copiar:
- `_serie` / `_ventana` (la misma ventana y el mismo corte por salto de datos que la lectura),
- `trazar` + `_estructura` para las diagonales **y sus roles** (seguridad / acción / rango),
- `calificar` para A+/B,
- `detectar` para las horizontales,
- `_rebote` y la tolerancia `tolerancia_toque_atr` para el toque diagonal.

Para leer cada marco como operativo se usan los `Marcos` que ya existen: 1H con
`MARCOS_INTRADIA` (H1 600 velas), 4H con `MARCOS` (H4 180), 1D con un `Marcos` de operativo D1
(D1 250, contexto W1 156). Así la ventana de cada marco es **la misma con que se publica**.

Motivo: `tests/test_guardian_estrategia.py` exige que la técnica viva en `scripts/estrategia/`, y
toda lógica de líneas fuera del motor es la segunda implementación que el repo ya pagó varias veces.

### 4.2 El script orquestador
**`scripts/radar_multifractal.py`**: universo, lectura de velas, llamada a `radar.eventos` por
marco, armado del HTML. No usa `get_asset_levels`, `direccion_tecnica` ni `ema_50` (lo prohíbe el
guardián). Flags: `--simbolos A,B` (prueba acotada), `--sin-abrir`, `--salida <ruta>`.

### 4.3 Agenda: Programador de tareas, NO el reloj de sucesos
**Cambio respecto de lo conversado**: se había propuesto engancharlo como un momento de
`reloj_gi.py`. No se puede sin romper dos invariantes que imponen tests:
- `test_todo_momento_llega_a_algun_canal`: todo momento mapea a un canal; el radar no tiene canal.
- `test_ningun_par_de_momentos_se_pisa_en_ningun_desfase_del_ano`: 07:30 Santiago queda a 15 min
  de `avisos_agenda` (07:45 Santiago), dentro de la tolerancia de 20.

Y el reloj es la vía de **publicación**; mezclarle una herramienta interna lo ensucia. Se instala una
tarea propia **`GI-Radar`** con un instalador `scripts/instalar_radar.ps1` (sin parámetros muestra
qué haría y no instala, como `instalar_reloj.ps1`). La trampa de "hora local vs Nueva York" no
aplica: el ancla es Santiago, que es la hora local de la máquina. Sí aplican las lecciones del
instalador del reloj:
- flags de batería en `False` (`DisallowStartIfOnBatteries`, `StopIfGoingOnBatteries`),
- un ancla de disparo que exista (no la medianoche de un cambio de horario),
- `StartWhenAvailable` para que corra al encender si a las 07:30 el equipo estaba apagado.
Correr dos veces no hace daño: el radar solo escribe un HTML.

## 5. Definición de los eventos

Todas las distancias en múltiplos del ATR 14 **simple** del marco (el de `pivotes._atr`, el mismo
del indicador). Solo velas cerradas: la vela en curso se descarta (`copy_rates_from_pos` la incluye).

| Evento | Diagonal (seguridad / acción) | Zona S/R |
|---|---|---|
| **Tocó** | La última vela cerrada llegó a la línea a ≤ `tolerancia_toque_atr` (0,25 ATR): `low − línea ≤ tol` en alcista, `línea − high ≤ tol` en bajista. Se informa además si **cerró a favor** (rebote, mismo criterio que `_rebote`) o **cerró al otro lado** (rompió). | El rango de la última vela cerrada intersecta la zona `nivel ± media_zona`, con `media_zona = 0,18 ATR`, el semiancho que ya dibujan el indicador y `tradingview_grafico.py:491`. |
| **Por tocar** | Distancia del último cierre a la línea **proyectada en cada una de las próximas 3 velas** ≤ `k × ATR × n` para algún n ∈ {1,2,3}, con `k = 1` en la v1: "llega en n velas al ritmo típico". Se informa el menor n. | Igual, contra el borde más cercano de la zona (la horizontal no se mueve). |

Qué líneas entran (director, 2026-10-26, sobre la recomendación de Claude):
- **Zonas S/R: solo el soporte más cercano y la resistencia más cercana** al último cierre, por
  marco, de las que devuelve `detectar` para ese marco. Son las dos que dibuja el indicador
  (`ObtenerNivelesPublicados`); avisar de zonas que no se ven en MT5 es el anti objetivo de §2.
  Una zona que la última vela cerrada cruzó cuenta igual como "tocó" ese día: el par más cercano
  se calcula con el cierre **anterior** a esa vela para el evento "tocó", y con el último cierre
  para "por tocar".
- **Retesteo de una línea rota**: mientras dure la ruptura según `_estructura` (hasta
  `velas_ruptura_max` = 30 velas y con el cierre todavía afuera), la línea rota sí genera "tocó" y
  "por tocar", marcados **"retesteo"**. Pasada la ruptura, una línea no vigente no genera nada.
- **Línea de acción en TENDENCIA** (la opuesta vigente, el otro borde del canal): se muestra en
  rojo con el mismo peso en el orden que las demás.

Notas:
- **Decisión de Claude, calibrable**: "3 velas = 3 ATR" es generoso, porque el ATR mide el rango
  de una vela, no cuánto avanza el precio en una dirección. Por eso `k` y el número de velas son
  parámetros con nombre en `tori/parametros.py` (`radar_velas_max = 3`, `radar_k_atr = 1.0`,
  `media_zona_atr = 0.18`), y la página muestra la distancia en ATR además de las velas para que
  el director calibre mirando.
- Si la línea se rompió en la última vela cerrada, el evento es "tocó · rompió".
- Las líneas de los marcos de contexto que `leer` adjunta no se cuentan dos veces: cada marco
  aporta solo sus propias líneas como operativo.
- "Rango" (dos diagonales sin A+): se informan como líneas de rango, en gris, con el mismo criterio.

## 6. Integridad de los datos

- **Cuenta** (decisión de Claude): el radar lee en vivo y no tiene sello en archivo, así que antes
  de escanear compara `mt5.account_info().login` con `config/cuenta_mt5.json` (vía
  `guardrails/cuenta.py`). Si no coincide, o no hay cuenta, **no escanea**: escribe una página de
  error que lo dice. La cuenta leída se estampa en el encabezado.
- **Historia insuficiente** (decisión de Claude): `exigir_velas` no cuenta velas, así que el radar
  agrega el chequeo **antes** del corte por salto de datos: si MT5 devuelve menos velas que la
  ventana del marco, ese marco del activo va a fallas con el motivo. **Nunca se traza sobre
  historia parcial**. El corte por salto (`salto_max_rango`) se acepta igual que en `leer()`, con
  el aviso visible en la celda: así el radar no diverge de las piezas.
- **Observación de Mercado**: `mt5_client.get_rates` ya hace `symbol_select(True)`, así que el
  estado original de cada símbolo se **registra antes de la primera lectura** y se restaura al
  final, como `simulador_gi.py`, para no ensuciar el terminal del director.
- **Feriados y mercado cerrado**: no excluyen el activo (la última vela cerrada sigue siendo
  válida), pero la hora estampada en la celda lo deja a la vista.
- **Matriz vacía**: el encabezado dice siempre cuántos se leyeron y cuántos fallaron. Si fallan
  más del 50 % se muestra un aviso arriba de todo: "lectura incompleta, no confiar en la ausencia".
- **Sin precios escritos a mano**: todo valor sale de MT5 en el momento; los precios se formatean
  con `digits` de `mt5.symbol_info`.

## 7. Paridad con el indicador de MT5

**Decisión del director (2026-10-26):** el indicador sigue calculando solo dentro de MT5 (es cómodo
y no debe depender de Python) y el radar corre afuera, con el motor Python. La referencia del radar
es **el motor** (`leer()`), que es lo que publican las piezas. La diferencia con el gráfico no se
elimina en la v1: **se hace visible y se mide**.

Por qué pueden diferir (del código, no medido):
1. **Ventana**: Python lee H1 = 600, H4 = 180, D1 = 250; el indicador usa `InpMaxBarras = 600` fijo.
   Con otra ventana el ancla A (extremo visible) puede ser otra.
2. **Memoria**: el indicador v2 conserva su línea hasta que se rompe o el ancla sale de la ventana;
   `trazar` recalcula en cada corrida y puede elegir otro punto B si aparece un pivote mejor.
3. **Dos implementaciones** del mismo algoritmo; el `.mq5` además tiene cambios sin commitear.

Lo que entra en la v1:
- **Precio de la línea en cada evento** ("seguridad 4H en <valor>", con los `digits` del símbolo),
  para que el director compare de un vistazo con el gráfico.
- **Control de paridad medido** (`--paridad`, también en la corrida de las 07:30): para los
  gráficos que el director tenga abiertos con el indicador, el radar lee sus objetos con
  `get_chart_objects` (el exportador `ChartObjectsExporter.mq5` recorre **todos** los objetos del
  gráfico, y el indicador dibuja `OBJ_TREND` con prefijo `GI_TV_`: `GI_TV_DIAG_SEGURIDAD`,
  `GI_TV_DIAG_ACCION`, `GI_TV_LINE_SOPORTE`, `GI_TV_LINE_RESISTENCIA`) y compara su `valor_actual`
  con el del motor, por rol. Diferencia mayor que `tolerancia_toque_atr` → se informa al pie de la
  página ("XAUUSD 4H: indicador y motor difieren en la línea de seguridad: <a> vs <b>").
  Limitación conocida: solo ve los gráficos abiertos y en ese marco. **Verificación pendiente en
  vivo**: que el exportador efectivamente entregue los objetos del indicador (en el código sí).
  Si el exportador no responde, la página lo dice; no se omite en silencio.
- Un test de paridad del radar contra `leer()` para 2-3 series fijas: mismas líneas y mismos roles.

Fuera de la v1 (trabajo aparte, cuando el director cierre sus cambios del `.mq5`): ventana
automática por marco en el indicador (600 / 180 / 250, como ya hace `InpVelasABMin = -1`), y
decidir sobre la memoria **con los datos del control de paridad**, no por intuición. Mientras tanto
el director puede ajustar `InpMaxBarras` a mano en cada gráfico.

## 8. Rendimiento

~137 símbolos × 4 marcos (W1 solo para el contexto de 1D) ≈ 550 llamadas a `copy_rates_from_pos`,
más el trazado. **No está medido**; se mide en la primera corrida real y se reporta en la página
(duración del escaneo). Si supera ~5 min, se paraleliza el trazado (no las lecturas de MT5, que
van por un solo IPC). No hay caché de velas en el repo y no se agrega en la v1.

## 9. Pruebas

- Unitarias de `radar.eventos` con series sintéticas: toque alcista/bajista, rebote vs rompió,
  por tocar en 1/2/3 velas, diagonal rota sin "por tocar", zona S/R por intersección.
- Paridad con `leer()` (sección 7).
- El guardián (`test_guardian_estrategia.py`) sigue verde.
- Un test que verifica que `radar_multifractal.py` no importa nada de envío
  (`enviar_whatsapp`, `whatsapp_sender`, `despachar`).
- Render del HTML con un conjunto de eventos fijo (fixture), revisado a ojo una vez.

## 10. Lo que queda al implementador

- Nombres internos, estructura del dataclass `Evento`, plantilla HTML (inline, sin dependencias;
  basta con `<details>` para plegar eventos).
- Cómo se abre la página: el script deja `data/radar/ultimo.html`; abrirla en el navegador al
  terminar es opcional (`--sin-abrir` en la tarea programada).
- `data/radar/` va al `.gitignore` (estado generado, como `data/.reloj_disparos.json`).

## 11. Decisiones tomadas por Claude (para revisar al leer)

- Lunes a viernes, aunque la cripto opere 24/7.
- Orden de filas de la sección 3.
- Umbral de "por tocar": 3 velas con `k = 1` ATR por vela, calibrable.
- Toque de S/R por intersección con la zona de 0,18 ATR.
- Tarea `GI-Radar` propia en vez del reloj de sucesos (forzado por los tests).
- Salida en `data/radar/`, no versionada.
- Cuenta verificada en vivo contra `config/cuenta_mt5.json`; si no coincide, no escanea.
- Historia insuficiente se mide antes del corte por salto; el corte se acepta como en `leer()`.
