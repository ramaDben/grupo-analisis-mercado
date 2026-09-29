# Plan: la agenda del día manda en Avisos

Spec: `docs/superpowers/specs/2026-09-28-carruseles-avisos-design.md`, secciones 3.7 a 3.9 (hito 2)
y 13. Rama `feat/avisos-agenda-del-dia`. Cada tarea termina con sus tests verdes y un commit.

| # | Tarea | Archivos | Test que la fija |
|---|---|---|---|
| 1 | El carrusel temático deja de escribir en Avisos (revierte la regla 3 de `canales_con_contexto_macro`) | `pipeline_carrusel.py` | Una tanda del carrusel no crea `01_macro_y_apertura`, ni con `--matriz` ni con `--grupo` |
| 2 | Reacciones de la confianza del consumidor y de JOLTS en el glosario | `data/glosario_siglas.json` | Todo dato de la agenda de hoy tiene `si_sale_sobre_consenso` |
| 3 | `leer_agenda` entrega también `diccionario`, `actual` y `resultado` | `pipeline_linkedin.py` | Los 37 tests de LinkedIn siguen verdes; campos nuevos presentes |
| 4 | Momentos nuevos de `pipeline_avisos`: `avisos_agenda`, `avisos_resultado`; `avisos_mediodia` fuera; `avisos_manana` solo sin datos | `pipeline_avisos.py` | Formato por momento y por día, con y sin datos |
| 5 | Formato `agenda_dia`: portada, la agenda de la jornada (hasta 18:30), lectura con reacciones del glosario | `pipeline_avisos.py` | Ventana 18:30; cero eventos cae a `agenda`; dato sin reacción frena |
| 6 | Formato `resultado`: una lámina `calendario` con resultado y veredicto, movimiento medido de la moneda, datos de la misma hora juntos | `pipeline_avisos.py` | Sin `actual` = código 1; misma hora = una pieza; "señales mixtas"; no se repite en el día |
| 7 | Despacho por `_plantilla` para tandas con `_avisos.json` (3.7: refresco, cupo del canal, divergencia del canal, refresco fallido) | `pipeline_carrusel.py`, `src/whatsapp_sender.py` | Pieza sin `_plantilla` igual que hoy; portada con su plantilla; cupo insuficiente no envía |
| 8 | Momentos del reloj | `config/agenda_mercado.json`, `reloj_gi.py` | Tolerancia en las tres configuraciones de desfase; el reloj nunca envía |
| 9 | Comando `/avisos`, flechas y Avisos en `CLAUDE.md`, AGY regenerado | `.claude/commands/avisos.md`, `agy_workflows.py`, `CLAUDE.md` | `agy_workflows --check`, `agy_reglas` |

Prueba real al final: preparar `avisos_agenda` y un `resultado` contra el terminal, rendir, y
despachar con `--pruebas` al banco de pruebas. Nada a un canal de clientes sin aprobación.
