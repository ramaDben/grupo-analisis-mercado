# Plan: alerta de la semana para los ejecutivos

Spec: `docs/superpowers/specs/2026-10-18-alerta-semana-ejecutivos-design.md` (léelo primero).
Rama sugerida: `feat/alerta-semana-ejecutivos`, desde `master`. Nunca commitear a `master`; sin push ni merge
sin OK del director. TDD: cada tarea empieza con su test en rojo.

Antes de empezar, lee: `scripts/analista/agenda.py` (`leer_ventana`, hora ya en Santiago),
`scripts/analista/macro_seguimiento.py` (`eventos_de_la_semana`, `_efectos`), `data/glosario_siglas.json`
(`_meta`, claves con `tier`, `canales`, `si_sale_sobre_consenso`), `scripts/analista/bot.py` (clase
`Telegram`, `escuchar`, `trabajador`, `cargar_config`) y `config/analistas_telegram.example.json`.
Reglas del repo: `CLAUDE.md` (sin guion largo en texto, español chileno, hora con `zoneinfo`, nunca offsets
fijos). Heredocs de Bash colapsan barras invertidas: usa Write/Edit para código.

## Tarea 1: completar el glosario de lo que usa el tema

- Test: un test de contrato recorre los eventos que el tema puede elegir (FOMC, TPM, IPC/CPI, NFP, PMI/ISM,
  GDP, IMACEC, Crude Oil Inventories) y exige `tier`, `canales` y `si_sale_sobre_consenso` en el glosario.
- Si falta alguno de OPEP, BCCh, BCE, IPC subyacente, PCE subyacente, o se clasifica (con la misma forma
  que los vecinos) o se declara fuera del tema. No inventes el efecto: si no lo sabes, queda fuera.
- No toques `_meta`. No cambies claves existentes: otros módulos las leen por nombre.

## Tarea 2: `config/guia_eventos.json`

- Por tipo de evento (`tasas`, `inflacion`, `empleo`, `actividad`, `petroleo`): `mueve` (activos),
  `conversar` (una frase), `no_decir` (una frase), `titular` (como aparece en "Semana de ...").
- Contenido inicial: el de la tabla del spec y la propuesta de agy (tasas: "el mercado ya descuenta un
  escenario, la sorpresa está en el tono"; empleo: "habrá movimiento rápido, revisa tu exposición"; etc.).
- Test: todo tipo tiene los cuatro campos, sin guion largo, sin las palabras `compra`, `vende`,
  `oportunidad`, `cobertura`.

## Tarea 3: `scripts/analista/semana.py`

- `tipo_de_evento(ev) -> str | None`: del evento y el glosario al tipo de la guía.
- `tema_de_la_semana(eventos) -> dict`: orden de precedencia del spec; semana tranquila si no hay tier alto.
- `armar_mapa(eventos, ahora) -> str` y `armar_vispera(evento, ahora) -> str`. Python puro, sin red, sin IA.
- Formato del mapa: titular "Semana de X", 3 a 5 eventos (día, hora con CLT/CLST, nombre en español con
  sigla explicada una vez, activos), una línea "qué conversar", aviso de riesgo corto (reusa el del bot).
- Tests: cada tema (FOMC, IPC, NFP, solo PMI, tranquila, empate); semana que cruza un cambio de horario;
  sin guion largo; ninguna palabra prohibida; sin línea de efecto si el glosario no la tiene.

## Tarea 4: agendador interno `scripts/analista/avisos_semana.py`

- `que_toca(ahora, eventos, estado) -> list[Aviso]`: lunes 07:45 a 08:15 Santiago el mapa; 16:00 a 16:30 del
  día hábil anterior a un evento de impacto 3 la víspera. Ventana de gracia solo hacia adelante.
- Tope de 2 por ejecutivo por día, orden por tier.
- Estado en `data/semanal/avisos_semana.json` (agrégalo a `.gitignore`), escritura atómica como
  `registro_semanal._escribir`. Se anota solo con envío confirmado.
- Calendario caído: no envía, avisa una vez al director (`rol` director del config) y reintenta en el
  siguiente latido. Distingue `vacia` de `sin_calendario` como `agenda.py`.
- Tests con reloj inyectado: dispara una vez, no repite tras reinicio, respeta ventana, tope de 2, falla
  pendiente, calendario caído.
- Test de contrato: el módulo no importa `enviar_whatsapp` ni `whatsapp_sender`.

## Tarea 5: integrarlo en `bot.py`

- Hilo daemon que cada 60 s llama a `que_toca` y envía con `Telegram.mensaje` al `id` de cada ejecutivo del
  config. Errores del hilo se loguean con `_log` y nunca tumban el polling.
- Botón de la víspera: teclado en línea con el ticker más afectado; al tocarlo se procesa como el pedido
  `/oportunidad <ticker>` de ese ejecutivo (reúso de 7 días incluido).
- Test: el hilo no se arranca en los tests existentes (flag inyectable); una víspera genera el pedido
  correcto.

## Tarea 6: verificación y cierre

- Corre `uv run pytest -q -k "analista or semana or glosario"` y la suite completa.
- Mira el texto real del mapa de esta semana con el calendario en vivo, impreso en consola, y pásaselo al
  director antes de activar el envío. Primera semana en modo prueba: manda solo al director.
- Actualiza `docs/bot-analistas.md` con una sección corta y deja una memoria del proyecto.
- Commit con el trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Sin push.

## Decisiones abiertas del director (no bloquean construir)

1. ¿Cumplimiento revisa `config/guia_eventos.json` antes de abrir a todos los ejecutivos?
2. Después de 3 semanas: ¿se suma la pieza de reacción y el cierre del viernes?
