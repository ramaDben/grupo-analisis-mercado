# La oportunidad semanal: `/oportunidad` y `/seguimiento` en el bot de analistas

> Diseño aprobado por el director el 2026-10-12, en brainstorming por secciones. Es el último
> pendiente post-S8 del enchufe de estrategia (`2026-10-09-enchufe-estrategia-design.md` §4 y §7;
> plan `2026-10-11-enchufe-fase-3.md`, Task S7-6: "la pieza de publicación del lunes no existe y
> su formato no está en el spec").

## 1. Qué es y para quién

Una pieza **HTML para el equipo comercial** que une dos cosas con autoría separada:

- **El análisis técnico de la semana**, firmado por la «Dirección de Análisis Técnico»: la
  lectura de Tori de cada activo, tal como quedó fijada el lunes.
- **Una simulación hecha por el ejecutivo** para su cliente: él escribe cuánto está dispuesto a
  perder y la pieza calcula el volumen y el retorno con un objetivo fijo de **3 veces el riesgo
  (1:3)**.

Se pide en el bot de Telegram con `/oportunidad`, una vez por semana, y entrega **los 6 activos**
de la semana en una sola pieza. Durante el resto de la semana, `/seguimiento <activo>` informa el
avance de un activo contra la foto del lunes.

### Por qué 1:3 y por qué vive en la simulación

La gerencia pidió retornos de al menos 1:5. Medido sobre la W41 desde el precio del lunes con el
stop en la invalidación, los objetivos de Tori quedaban en 0,40R (USD/CLP), 0,88R (oro) y 1,05R
(WTI): un 1:5 no cabe en sus niveles. El director fijó **1:3** (2026-10-12).

Ese objetivo **no es de Tori** (su salida es "no hay objetivo fijo") y por eso **no aparece en la
sección del análisis**: pertenece a la simulación del ejecutivo, rotulado «Objetivo de la
simulación (1:3)». Así la firma del director queda sobre lo que el método dice, y la meta
comercial queda donde corresponde.

## 2. El bot queda con dos comandos

| Comando | Qué hace |
|---|---|
| `/oportunidad` | La pieza HTML de la semana con los 6 activos |
| `/seguimiento <activo>` | Lámina + texto de WhatsApp con el avance de un activo de la foto |

Se retiran `/activo`, `/calendario`, `/dato`, `/jornada` y el foco técnico del día
(`analista/foco.py`). Un comando retirado responde con la ayuda de los dos que quedan. Con ellos
se va el código que solo ellos usan (foco, plan del día, armado de jornada), cuidando lo que
siga teniendo consumidores fuera del bot.

Siguen vigentes las reglas del bot (`2026-10-08-bot-telegram-analistas-design.md`): no se llaman
los `preparar()` de producción ni se tocan `data/carrusel`, `data/screener` ni sus historiales;
AGY solo redacta los campos sellados `[[ESCRIBIR]]` vía `/analista`; la maqueta es nuestra; sin
estadística ni tasa de acierto; informe general (sin "para <trader>"); firma «Dirección de
Análisis Técnico»; no se menciona a la CMF.

**Excepción de formato:** hasta ahora del bot salía solo PDF. Esta pieza sale en **HTML** porque
es una herramienta interna con panel interactivo; lo que llega al cliente es el correo que arma
el ejecutivo desde ella, el texto de WhatsApp y las láminas.

## 3. Enfoque de implementación

Rama nueva desde master. El PR #254 (`feat/semanal-prototipo`) **se cierra sin mergear**: su
`semanal.py` decide con la EMA 50 D1 y el Chandelier, que el enchufe borró. Se rescata lo que no
depende del método:

- el correo para Outlook (`correo.py`, `templates/correo_semanal/{correo,cuerpo}.html`, los
  commits del Outlook clásico: 6a801be, dc5d0bb, f1d1896, c4c0c7b);
- el registro (`registro_semanal.py`, `data/semanal/registro.json`);
- el redondeo de la simulación igual que JS (mitad hacia arriba);
- las plantillas de lámina (`templates/stories/{semanal,seguimiento}.html`). Ojo: `recorrido` es
  una clave reservada en los payloads de `story_render`.

La lógica nueva va en `scripts/analista/oportunidad.py`, escrita sobre `Lectura`.

### Flujo

```
data/referencias_semanales/<AAAA-Www>/_semana.json + JSON por activo
        │  (los fija el análisis semanal del escáner; el bot no lo corre)
        ▼
escenario(lectura) por activo ──► foto en data/semanal/registro.json (una por semana)
        │
        ├──► /oportunidad  → HTML con los 6 activos (análisis + panel de simulación)
        └──► /seguimiento  → lámina + WhatsApp de un activo, contra la foto
```

Los activos son los `elegidos` de `_semana.json`, en **orden de puntaje**.

## 4. El escenario de la simulación

`escenario(lectura, atr_4h)` traduce la lectura a entrada, stop y objetivo. Todo sale de la
`Lectura`; nada se calcula con indicadores.

| Estado | Entrada | Stop | Objetivo |
|---|---|---|---|
| TENDENCIA, REBOTE, RUPTURA | precio del lunes (`lectura.precio`) | la invalidación | entrada ± 3 × riesgo, a favor de la dirección |
| RANGO | el borde vigilado (falso quiebre) | ese borde ± 0,5 × ATR 4H, por fuera | 3R hacia el borde contrario |
| PRUEBA sobre línea A+ | sin simulación hasta el cierre de la vela (§5) | | |
| PRUEBA sin A+, o sin invalidación | sin simulación, con el motivo | | |

**El motivo lo lee el cliente** en el correo («Sin simulación esta semana: …») y en
`/seguimiento`, así que va en su idioma, uno por uno, sin jerga interna (nada de ATR, contrato
ni invalidación). Decisión del director, 2026-10-12. El activo sin simulación sigue entrando al
correo con su análisis y `/seguimiento` le entrega igual la lectura de hoy.

- **Riesgo** = |entrada − stop|. Si es menor que **0,25 × ATR 4H** (la `tolerancia_toque_atr`
  de Tori), no hay simulación: "el precio está pegado al nivel clave". El 0,5 × ATR del rango es la
  `tolerancia_horizontal_atr` de Tori. Los dos se leen de `scripts/estrategia/tori/parametros.py`,
  no se escriben de nuevo.
- En RANGO la simulación va en el **falso quiebre** (decisión del 2026-09-28: quien sabe operar la
  configuración no tiene que quedarse esperando), con la misma regla de salida que ya trae la
  lectura: se cierra si el precio vuelve a cerrar fuera del borde que había roto.
- **Objetivo lejano:** se simula igual, con una línea que dice a cuántos días de movimiento
  típico (ATR D1, `lectura.metricas`) está el objetivo.

## 5. `/oportunidad`

- **Una foto por semana**, reusada por todos los ejecutivos: el segundo pedido de la semana no
  vuelve a armar la pieza, entrega la misma con la fecha y el precio de la foto a la vista.
- Si `estado_semanal` indica una línea A+ en PRUEBA, el bot responde "se publica al cierre de la
  vela HH:MM" (hora Chile) y no arma nada todavía.
- Sin `_semana.json` de la semana no hay pieza: el bot lo dice y no corre el escáner.
- Un pedido a mitad de semana recibe la misma foto, con una remisión a `/seguimiento`.

### Lo que trae la pieza, por activo

**Sección del análisis (firma del director):** la lectura en marco 4H, swing de una a dos
semanas: dirección, estado, la línea que se vigila, la invalidación, el objetivo de Tori (el
horizontal mayor, como referencia técnica), los tres escenarios ⬆️ ↔️ ⬇️ y la regla de salida. El
contexto de la semana con sus drivers lo redacta AGY.

**Panel de simulación (del ejecutivo):**

- casilla «incluir»;
- pérdida aceptable en CLP;
- capital, opcional, solo para ver los montos en %.

El JS lleva incrustado el contrato de cada activo de la cuenta MT5 **51257** (en CLP): valor del
punto por lote, volumen mínimo y paso. Calcula:

1. volumen = pérdida ÷ (|entrada − stop| × valor del punto por lote), **redondeado hacia abajo**
   al paso;
2. la pérdida se recalcula con el volumen real;
3. ganancia = 3 × pérdida.

**Pérdida y ganancia van juntas y del mismo tamaño.** Si la pérdida no alcanza el volumen mínimo,
se muestra la pérdida que implica el volumen mínimo. El panel rotula «Objetivo de la simulación
(1:3)» y «Simulación realizada por <ejecutivo>».

**Salida:** el botón arma el correo para Outlook **solo con los activos marcados**; cada activo
trae además su texto de WhatsApp y su lámina.

La simulación es una **foto** con los precios del lunes: no se mueve aunque la línea de Tori se
mueva durante la semana.

## 6. `/seguimiento <activo>`

Solo acepta activos de la foto de esta semana; con cualquier otro responde con la lista de los
que sí están. Informa **dos cosas por separado y con el mismo peso**:

1. **La simulación**, contra sus precios fijos del lunes, recorriendo las velas 4H desde la foto:
   - *entrada pendiente* (rango: el precio todavía no llegó al borde);
   - *en curso*, con el % del recorrido hacia el objetivo 1:3;
   - *objetivo 1:3 alcanzado*;
   - *stop tocado*;
   - *rango roto* (solo en rango): la vela que cruza el borde llega hasta el stop sin que la
     entrada se haya activado. Es una ruptura, no el falso quiebre que se simula, así que la
     simulación queda **descartada** y no vuelve a activarse. No se informa «stop tocado» de una
     entrada que nunca se activó ni «pendiente» de un precio que ya no vale (director,
     2026-10-12, tras la prueba real de la W41 con el cobre).

   Si una misma vela tocó el stop y el objetivo, cuenta **stop** (el lado prudente). Se informa en
   precio y en %, **nunca en pesos**, porque los pesos dependen del volumen de cada ejecutivo. Y
   nunca «si hubieras entrado ganarías X».
2. **La lectura de Tori hoy** (`lectura_actual` contra la referencia): si la línea del lunes sigue
   en pie, si está en prueba o si se rompió y la referencia se reemplazó.

Salida: lámina + texto de WhatsApp («te envío una actualización»). La del mismo activo se reusa
durante 30 minutos.

## 7. El texto

- El contexto de la semana por activo, con los drivers bajados a esa semana, lo redacta AGY por
  `/analista` en campos sellados, como hoy. Las cifras, los niveles y la simulación los pone
  Python.
- Con un campo editorial vacío la pieza no sale: `exigir_texto_editorial`, el mismo freno del
  resto del repo.
- En lo que lee el cliente no aparecen «oportunidad» ni «recomendación» (el nombre del comando es
  interno), no se usa guion largo y el aviso legal es fijo y no editable.
- Tuteo chileno, precios con los `digits` del activo, horas en hora Chile.

## 8. Errores

Siempre como respuesta clara del bot, nunca en silencio:

- la semana sin `_semana.json`;
- espera por una línea A+ en prueba, con la hora del cierre de la vela;
- MT5 caído en `/seguimiento` (la foto se puede entregar; el avance no);
- AGY sin responder.

## 9. Pruebas (TDD)

- `escenario()` por estado: tendencia alcista y bajista, rango con el borde vigilado arriba y
  abajo, ruptura, prueba, sin invalidación y riesgo bajo el mínimo.
- La simulación en Python con valores de referencia, y **el mismo caso corrido en el JS del
  panel**, para que redondeen igual.
- Los estados de `/seguimiento`, con el caso de la vela que toca las dos puntas.
- La gramática del bot con dos comandos (los retirados responden con la ayuda).
- El reuso semanal: el segundo pedido no vuelve a armar la pieza.
- `test_guardian_estrategia.py` cubriendo `scripts/analista/`: nada de EMA 50 ni Chandelier.

## 10. Fuera de alcance

- Conectar `/oportunidad` al reloj de los lunes: la pide el ejecutivo.
- La plantilla de marketing de GI para el correo y la validación de cumplimiento con legal: la
  pieza sale con la maqueta propia y los criterios de cumplimiento de arriba.
- Backtesting o tasa de acierto de la simulación (decisión del 2026-10-10: no hay backtesting).
