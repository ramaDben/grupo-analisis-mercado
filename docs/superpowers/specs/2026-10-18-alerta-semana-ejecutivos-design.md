# Alerta de la semana para los ejecutivos (diseño)

Fecha: 2026-10-18. Estado: aprobado por el director en el chat (recomendación del diseño). Falta que el
director revise este archivo antes de ejecutar el plan.

## Propósito

Que los ejecutivos comerciales sepan **de qué trata la semana** y le saquen provecho: llamar a sus
clientes antes de un dato fuerte, revisar exposición, reaccionar después. Hoy el bot entrega piezas por
activo cuando se piden; nadie le avisa al ejecutivo que viene una semana de IPC o de decisión de tasas.

No es contenido para clientes. Es material interno para el ejecutivo, por el bot de Telegram. Por eso
no pasa por el flujo de aprobación de WhatsApp ni por `reloj_gi.py` (que solo prepara y jamás envía).

## Idea central: la semana tiene un tema

El bot clasifica la semana por su dato dominante y lo dice en el titular: "Semana de IPC", "Semana de
tasas (Fed)", "Semana de empleo", "Semana de PMI", "Semana tranquila". El ejecutivo sabe qué conversación
abrir sin leer una lista de eventos.

**Cómo se elige el tema (determinista, sin IA):** entre los eventos de los próximos 7 días (los mismos de
`agenda.leer_ventana`), manda el de mayor `tier` del glosario; si hay empate, la decisión de tasas gana
sobre inflación, inflación sobre empleo, empleo sobre actividad (PMI, PIB). Sin evento de tier alto, la
semana es "tranquila" y el mapa lo dice en una línea.

## Formatos del MVP

| Formato | Cuándo | Contenido |
|---|---|---|
| **Mapa de la semana** | Lunes 07:45 Santiago | Tema, 3 a 5 eventos fuertes con día y hora Chile, activos que mueve, una línea "qué conversar" |
| **Víspera** | 16:00 Santiago del día hábil anterior, solo eventos de impacto 3 (tasas, IPC, NFP) | 5 líneas y un botón que lanza `/oportunidad` del activo más afectado |

Fuera del MVP, con medición de por medio: la **reacción** (veredicto contra consenso y movimiento medido
en MT5 tras el dato), el cierre del viernes y el banner en el correo. Se decide después de 3 semanas
midiendo cuántos ejecutivos abren la pieza.

## Datos y reglas

1. **Todo sale de lo que ya existe.** Eventos y hora desde `agenda.leer_ventana` (calendario de
   Investing.com, hora ya en Santiago: no se reconvierte, issue #38). Activos que mueve y sentido desde
   `data/glosario_siglas.json` (`canales`, `tier`, `si_sale_sobre_consenso`). Ninguna cifra la escribe un
   modelo (Regla 1).
2. **Sin IA.** El texto lo arma Python con plantillas y el glosario, igual que las piezas de Avisos
   (`sin cifra no hay resultado`). Si el glosario no tiene el dato, el evento sale sin la línea de efecto
   y no se inventa.
3. **La guía "qué conversar / qué no decir" vive en `config/guia_eventos.json`**, por tipo de evento, y la
   edita el director. La escribe Claude la primera vez. Antes de que salga a clientes reales conviene que
   la vea cumplimiento (decisión pendiente del director, no bloquea construirla).
4. **Tope de 2 avisos por ejecutivo por día.** Si hay más víspera que cupo, ganan las de mayor tier; el
   resto queda en el mapa. Si todo es alerta, ignoran todo.
5. **Idempotencia:** `data/semanal/avisos_semana.json` (gitignoreado, estado generado) anota
   `(tipo, fecha, evento)` enviados. Reiniciar el bot no repite el aviso.
6. **Un evento que falló sigue pendiente**, como en el reloj: solo se anota si el envío se confirmó.
7. **Calendario caído:** el aviso no sale con datos viejos. El bot avisa al director una vez ("no pude
   leer el calendario, no mandé el mapa") y el siguiente latido reintenta. Un mapa con la agenda de la
   semana pasada es peor que ninguno.

## Reglas de texto (cliente interno, mismas del proyecto)

- Español de Chile, tuteo neutro, sin guion largo ni medio como inciso.
- Escenarios y no órdenes. Nunca "compra antes del dato" ni "el dólar va a subir". Se dice "revisa tu
  exposición", no "cobertura" (puede leerse como asesoría).
- Cada sigla, explicada una vez en lenguaje simple (diccionario del glosario).
- Cada aviso cierra con el aviso de riesgo corto del CFD que ya usa el bot.
- Horas siempre en hora Chile con etiqueta CLT/CLST.

## Dónde vive en el código

- `scripts/analista/semana.py` (nuevo): `tema_de_la_semana`, `armar_mapa`, `armar_vispera`. Funciones puras
  sobre los eventos que entrega `agenda`; no llaman a la red.
- `scripts/analista/avisos_semana.py` (nuevo): el agendador interno del bot. Un hilo en `bot.py` que cada
  minuto consulta la hora de Santiago y decide qué toca; envía con `Telegram.mensaje` a los ejecutivos
  registrados en `config/analistas_telegram.json`.
- `config/guia_eventos.json` (nuevo): guía por tipo de evento.
- `bot.py`: arranca el hilo; el botón de la víspera reutiliza el flujo de `/oportunidad`.
- El hilo no vive en `reloj_gi.py` porque el bot ya tiene el token y la lista de ejecutivos, y porque este
  envío es interno. Un test impide que el agendador envíe a canales de WhatsApp.

## Pendientes conocidos del glosario (se verifican al construir)

El glosario trae `tier`, `canales` y `si_sale_sobre_consenso` para FOMC, TPM, IPC/CPI, NFP, PMI/ISM,
GDP, IMACEC y Crude Oil Inventories. Faltan o están sin clasificar: OPEP (solo `nombre_es` y
explicación), BCCh, BCE, IPC subyacente, PCE subyacente. El plan los completa antes de usarlos, o los
deja fuera del tema de la semana y lo declara.

## Pruebas

- Tema: semana con FOMC, con IPC, con NFP, con solo PMI, sin eventos fuertes, empate de tier.
- Mapa y víspera: formato, hora CLT/CLST en cambio de horario, sigla explicada, sin guion largo, sin
  `compra`/`venta`, aviso de riesgo presente.
- Tope de 2 por día y orden por tier. Idempotencia tras reinicio.
- Calendario caído: no envía y avisa una vez.
- Contrato: el agendador no importa ni llama a `enviar_whatsapp`.

## Fuera de alcance

Avisos a clientes, la pieza de reacción, medición de aperturas, el banner del correo.
