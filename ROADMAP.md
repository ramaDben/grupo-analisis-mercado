# Hoja de ruta de grupo-analisis-mercado

La lista única de tareas del proyecto. Se revisa con `/roadmap`.

## Cómo se lee y se escribe

- **Fase**: un tramo grande de trabajo. **Hito**: un resultado que se puede mostrar, con fecha si la tiene.
  **Módulo**: la parte del sistema que toca la tarea (prefijo del ID).
- **Cada tarea es atómica**: una sola cosa, que se termina en una sesión y se puede comprobar.
- Formato: `- [ ] **MOD-NN** qué se hace. (requiere MOD-NN)`. Al terminarla: `- [x]`, sin borrarla.
- `(requiere ...)` marca el orden lógico: una tarea no se empieza antes que las que requiere.
- `(decide el director)` marca una decisión que no se toma sin él.
- Una tarea nueva va al final de su hito, con el siguiente número de su módulo. Los IDs no se reutilizan.

Estado al 2026-11-04: el `master` local está 29 commits atrás de `origin/master` (GIT-06). Lo "fusionado" se
mide contra `origin/master`. El checkout principal está en `feat/webinar-diseno-v2`, y el bot corre desde ahí.

## Módulos

| Prefijo | Módulo |
|---|---|
| `MOT` | Motor Tori, escáner y carrusel |
| `BOT` | Bot de analistas: Telegram, `/oportunidad`, `/seguimiento`, alerta semanal, aviso por correo |
| `WEB` | Lienzo del webinar |
| `DES` | Despacho a WhatsApp y textos de los grupos |
| `RAD` | Radar multifractal e indicador de MT5 |
| `EST` | Estudios y mediciones contra el azar |
| `DAT` | Datos, ingesta, CI y MCP market-data |
| `TAR` | Tareas del Programador de tareas |
| `STO` | Stories GI |
| `DOC` | Documentación y manual |
| `MEM` | Memoria y AGY |
| `GIT` | Ramas, worktrees y PR viejos |
| `FUT` | Para después (fuera de las fases activas) |

---

## Fase 1 · Motor Tori, bot y webinar (hecha)

### Hito 1.1 · Motor Tori enchufado (PR #255 a #265, octubre)
- [x] **MOT-01** Contrato, trazado y lectura de la estrategia Tori (S1 a S3, PR #256, #257, #258).
- [x] **MOT-02** Escáner, carrusel, gráfico, informe y Avisos leen la Lectura (S4 a S7, PR #259 a #262).
- [x] **MOT-03** Purga de la lectura vieja y cierre semanal con `editorial.json` (S8, PR #263 a #265).
- [x] **MOT-04** Niveles publicados: horizontales con espacio operable (PR #276).

### Hito 1.2 · Bot de analistas en marcha (PR #248 a #305)
- [x] **BOT-01** Bot de Telegram con informe general firmado, en PDF para celular (PR #248, #251, #252).
- [x] **BOT-02** `/oportunidad` por activo, con correo editorial y noticia de apertura (PR #249, #266 a #268, #271, #277, #292, #300).
- [x] **BOT-03** `/seguimiento` con suceso único, velas de 30 minutos y tres mensajes de contexto (PR #281 a #288, #291, #296).
- [x] **BOT-04** La fuente oficial es el escalón 0 de la noticia (PR #302, #304).
- [x] **BOT-05** Ayuda de lanzamiento, bitácora de uso y panel por usuario (PR #272, #289, #305).
- [x] **BOT-06** Alerta de la semana para ejecutivos, con sus seis menores (PR #270).

### Hito 1.3 · Webinar y CI
- [x] **WEB-01** Lienzo diario con zoom para el webinar (PR #295).
- [x] **DAT-01** CI de master en verde: dos pruebas que dependían de MT5 o de Windows (PR #294).
- [x] **DAT-02** El refresco horario también renueva la ingesta de acciones (PR #293).

---

## Fase 2 · Integrar lo que quedó en ramas (en curso)

### Hito 2.1 · Webinar v2 (PR #306, rama `feat/webinar-diseno-v2`, checkout principal)
- [ ] **WEB-02** Commitear los cambios del lienzo que están sin commit en el checkout principal (`config/webinar.json`, `scripts/webinar/preparar.py`, `scripts/webinar/rendir.py`, `templates/webinar/lienzo.html`, `tests/test_webinar.py`) y subirlos al PR #306.
- [ ] **WEB-03** Decidir si el lienzo sigue en este repo o lo reemplaza el material del webinar de Resilency (rama `feat/webinar-material`). (decide el director)
- [ ] **WEB-04** Integrar el PR #306 (CI verde, mergeable). (requiere WEB-02, WEB-03; decide el director)
- [ ] **WEB-05** Automatizar el lienzo a las 08:00 (fase B). (requiere WEB-04)
- [ ] **WEB-06** Paso editorial diario del lienzo: noticia, bancos y teoría, cada uno con fuente. (requiere WEB-04)
- [ ] **WEB-07** Decidir qué se versiona del material sin seguimiento: `data/webinar/2026-10-29` a `2026-11-03`, `docs/presentaciones/introduccion-trading/` y `scripts/introduccion_trading_ppt.py`. (decide el director)

### Hito 2.2 · Despacho seguro a los grupos
- [ ] **DES-01** Abrir PR de `fix/freno-canal-avisos` (commit be5f06f, worktree `gam-freno`, solo local): freno de canal en el sender y bitácora del envío directo.
- [ ] **DES-02** Pasar a una rama `fix/` propia el cambio "sin invitar a opinar", que está sin commit en el checkout principal (`pipeline_avisos.py`, `contexto_macro_grupos.py`, `pipeline_carrusel.py`), y abrir su PR.
- [ ] **DES-03** Integrar DES-01 y DES-02 y dejar el checkout principal en master al día: el freno solo vale desde ahí. (requiere DES-01, DES-02, WEB-04; decide el director)
- [ ] **DES-04** Volver a medir contra el DOM real el selector que confirma imágenes sin pie (falso negativo "El adjunto no apareció"), sin relajar la verificación.

### Hito 2.3 · Bot: aviso por correo y lanzamiento
- [ ] **BOT-07** Abrir PR de `feat/aviso-correo-drive` (2 commits, worktree `gam-aviso-correo`, solo local).
- [ ] **BOT-08** Integrar ese PR y reiniciar GI-BotTelegram con `instalar_bot_telegram.ps1 -Reiniciar`. (requiere BOT-07, DES-03; decide el director)
- [ ] **BOT-09** Comprobar con un `/oportunidad` nuevo real que el aviso llega a los dos destinatarios y deja copia en Enviados. (requiere BOT-08)
- [ ] **BOT-10** Verificar `/estado` desde el Telegram del director (tarea 3 del plan de lanzamiento).
- [ ] **BOT-11** Abrir PR de `docs/bot-energia-pc` (energía del equipo anfitrión, tarea 4; solo local).
- [ ] **BOT-12** Abrir PR de `docs/lanzamiento-bot-analistas` (spec y plan del lanzamiento, worktree `gam-lanzamiento`, solo local).
- [ ] **BOT-13** Prueba punta a punta en el celular del director: `/oportunidad oro` y `/seguimiento oro` (tarea 5).
- [ ] **BOT-14** Completar `contacto` de los 4 usuarios en `config/analistas_telegram.json`, hoy vacío en los 4 (tarea 6).
- [ ] **BOT-15** Agregar 2027 a `config/feriados_chile.json` desde fuente oficial, con su test (hoy no trae ninguna fecha de 2027; tarea 7).
- [ ] **BOT-16** Go-live: checklist final y mensaje del director al equipo (tarea 8). (requiere BOT-10, BOT-13, BOT-14, BOT-15)
- [ ] **BOT-17** Confirmar el cargo de la firma del informe: hoy dice "Departamento de Análisis Técnico", una memoria decía "Dirección" y desde el 2026-11-02 el área es el Departamento de Estudio. (decide el director)
- [ ] **BOT-18** Cargar la firma escaneada del director (`config/autor/` solo tiene `foto.png`).
- [ ] **BOT-19** Definir el chat_id del equipo en la configuración del bot.

### Hito 2.4 · Radar multifractal (rama `feat/radar-multifractal`, en origin, sin PR)
- [ ] **RAD-01** Elegir la calibración: `radar_velas_max`, `radar_k_atr` o mostrar solo «tocó» (hoy 145 de 146 símbolos salen con actividad). (decide el director)
- [ ] **RAD-02** Aplicar la calibración y comprobar que la matriz filtra. (requiere RAD-01)
- [ ] **RAD-03** Confirmar, en una primera corrida de la mañana con la caché fría, que funciona la regla de la vela que contiene el tick.
- [ ] **RAD-04** Alinear `InpMaxBarras=600` del indicador con la ventana por marco del motor (10 diferencias de paridad en 4 gráficos).
- [ ] **RAD-05** Abrir PR de `feat/radar-multifractal` (20 commits sobre master; trae el indicador v2.10, y master todavía tiene la v1.00). (requiere RAD-02)
- [ ] **RAD-06** Registrar la tarea GI-Radar con `scripts/instalar_radar.ps1 -Instalar` (lunes a viernes, 07:30). (requiere RAD-05; decide el director)

### Hito 2.5 · Estudios a master
Ramas encadenadas: `feat/indicador-murphy` está contenida en `feat/radar-multifractal`, que está contenida en
`feat/ea-retroceso-seguridad`. Se fusionan en ese orden o se archivan.
- [ ] **EST-01** Abrir PR de `docs/estudio-diagonales-vs-azar` (1 commit, worktree `gam-diagonales`, solo local).
- [ ] **EST-02** Versionar los scripts y tablas del estudio de diagonales, que quedaron en el scratchpad de la sesión e60bb514, si todavía existen. (requiere EST-01)
- [ ] **EST-03** Pasar `docs/estudios/2026-10-27-murphy-zonas-sr/` (sin commit en `gam-murphy`) a una rama `docs/` y abrir PR.
- [ ] **EST-04** Descartar la v2.20 del indicador (sin commit en `gam-murphy`, en desuso desde el 2026-10-29) y retirar el worktree. (requiere EST-03, RAD-05)
- [ ] **EST-05** Decidir qué pasa a master de `feat/ea-retroceso-seguridad` (veredicto: no pasa): informe, probador y EA como estudio, o archivar la rama. (requiere RAD-05; decide el director)
- [ ] **EST-06** Hacer lo decidido en EST-05 y retirar `gam-ea`, con sus `tester_configs/` y los logs de compilación sin seguimiento. (requiere EST-05)

---

## Fase 3 · Decisiones de contenido abiertas

### Hito 3.1 · Seguimiento del bot
- [ ] **BOT-20** Medir en 20 días hábiles cuántas veces el suceso queda sin objetivo porque la lectura de 15 minutos no trae invalidación (caso WTI).
- [ ] **BOT-21** Elegir el respaldo: riesgo igual a 1 ATR de 15 minutos, o dejar sin objetivo. (requiere BOT-20; decide el director)
- [ ] **BOT-22** Decidir el nivel del día del seguimiento: horizontal o diagonal fijada. (decide el director)
- [ ] **BOT-23** Corregir el texto "El mercado está cerrado" del análisis técnico del seguimiento (defecto anotado en la spec de fuente oficial).

### Hito 3.2 · `/oportunidad`
- [ ] **BOT-24** Decidir el rótulo para cuando el precio de la tarjeta y la etiqueta del gráfico no coinciden (ej. 694,00 contra 690,59), sin pisar la vela. (decide el director)
- [ ] **BOT-25** Revisar en una pieza actual las deudas anotadas el 2026-10-22: frase repetida (`hechos.py`), todos los eventos como "Alto impacto", cifras sin unidad, EIA sin esperado y cabecera sin año.
- [ ] **BOT-26** Corregir las deudas de BOT-25 que sigan vivas. (requiere BOT-25)
- [ ] **BOT-27** Gráficos recortados para celular en el correo (quedó fuera del PR #300). (decide el director)
- [ ] **BOT-28** Un solo logo de GI en el correo (quedó fuera del PR #300). (decide el director)
- [ ] **BOT-29** Poner los resultados corporativos antes que "Lo último de" (quedó fuera del PR #300). (decide el director)

### Hito 3.3 · Alerta de la semana
- [ ] **BOT-30** Que cumplimiento revise `config/guia_eventos.json`. (decide el director)
- [ ] **BOT-31** Pasar `avisos_semana.modo` de "prueba" (hoy solo le llega al director) a "todos". (requiere BOT-30)
- [ ] **BOT-32** Con 3 semanas de medición, decidir si se suman la pieza de reacción y el cierre del viernes. (decide el director)

### Hito 3.4 · Carrusel y grupos
- [ ] **MOT-05** Decidir cómo se publica un USD/CLP con rango H4 de más de 50 pesos (quedó fuera de la tanda del 2026-11-04). (decide el director)
- [ ] **MOT-06** Verificar si `refrescar_payload` todavía revierte en silencio el USD/CLP de D1 a H1 antes de enviar y, si es así, abrir el issue que pidió el director.
- [x] **MOT-07** Imagen y texto del contexto macro de Metales se contradecían (la imagen comparaba 2 días, el texto 5 ruedas con rezago). Ahora comparten `_mov_de_delta` y `_delta_vigente`. Rama `fix/carrusel-brechas-lectura` (worktree `gam-brechas`), commit 5044e98.
- [x] **MOT-08** El titular y el párrafo de las alertas llevan marcas (`[[OBJETIVO]]`, `[[VIGILAR]]`, `[[INVALIDACION]]`, `[[PRECIO]]`) y el despacho las reescribe con la lectura de ahora; un precio tipeado detiene el render. Commit 2e1a7f5, misma rama.
- [x] **MOT-09** En una ruptura con la línea rota a más de 2 ATR diarios del precio se vigila el horizontal cercano (oro: 4.134,10 en vez de 4.738,54) y el gráfico acota la proyección de la diagonal. Commits 1147e73 y 7e58357, misma rama.
- [ ] **MOT-10** Abrir el PR de `fix/carrusel-brechas-lectura` e integrarlo; hasta entonces el checkout principal (y el bot) corre el código viejo. (requiere MOT-07, MOT-08, MOT-09; decide el director)
- [ ] **MOT-11** `tests/test_analista_preparar.py::test_seguimiento_mide_la_simulacion_y_entrega_el_suceso` falla en `origin/master` (espera `en_curso`, devuelve `objetivo`), y `tests/test_pipeline_linkedin.py::test_rendir_sin_pdf_escribe_brief_y_quita_la_marca` falla por una visión de 52 días (máximo 45).

---

## Fase 4 · Limpieza de ramas y PR viejos

### Hito 4.1 · PR de septiembre (522 commits atrás de master)
- [ ] **GIT-01** PR #234 (el IPC de Chile se publicaba con el signo al revés): comprobar si el defecto sigue en master y, si sigue, rehacer el arreglo sobre master.
- [ ] **GIT-02** PR #228 (una tanda vacía sin terminal salía con código 0): rehacer sobre master o cerrar. (decide el director)
- [ ] **GIT-03** PR #235 (borde Donchian): el texto con `don_low` ya no está en los scripts de master; cerrarlo si ya no aplica.
- [ ] **GIT-04** PR #233 (auditoría del manual con AGY): resolverlo junto con DOC-02. (requiere DOC-01)
- [ ] **GIT-05** Cerrar el PR #236 (reingesta del 2026-09-08, datos viejos). (decide el director)

### Hito 4.2 · Ramas y worktrees sin trabajo vivo
- [ ] **GIT-06** Poner al día el master local (29 commits atrás de origin/master).
- [ ] **GIT-07** Retirar el worktree `gam-niveles`: su rama ya está en master (PR #276).
- [ ] **GIT-08** Decidir qué hacer con `gam-semanal` y `feat/semanal-prototipo` (PR #254 cerrado; el informe semanal se descartó el 2026-11-02). (decide el director)
- [ ] **GIT-09** Decidir si se guardan `docs/despliegue-nube-opcion-a.md`, `deploy/nube/` y `docs/diagramas/sistema-actual.html` (sin seguimiento en `gam-nube`; la nube se descartó el 2026-10-22) y retirar el worktree. (decide el director)
- [ ] **GIT-10** Decidir el destino de `wip/evergreen-usdclp` (código de AGY sin revisar) y de `wip/grafico-y-lamina-seguimiento`. (decide el director)
- [ ] **GIT-11** Borrar `respaldo/agy-delta-2026-09-27` (cuarentena con consenso inventado y atribuido a bancos reales). (decide el director)
- [ ] **GIT-12** Ordenar lo que está sin seguimiento en el checkout principal: `.bak`, `jinteco.html`, `data/uso_bot.html`, `mql5/*.log` y la copia de la spec y el plan de Resilency (ya viven en Resilency). (decide el director)
- [ ] **GIT-13** Borrar las 17 ramas locales que ya están en master. (requiere GIT-06)

---

## Pendientes sueltos

- [ ] **TAR-01** GI-Reloj, GI-Ingesta y GI-CalculadoraLotaje están deshabilitadas desde el 21-10-2026 y no hay decisión anotada: confirmar si quedan así o se reactivan. (decide el director)
- [ ] **DAT-03** Issue #240: las series OHLC declaran UTC pero están en hora de Santiago.
- [ ] **DAT-04** Issue #136: la conexión a MT5 solo se intenta al arrancar el MCP.
- [ ] **DAT-05** Issue #237: comprobar si sigue vigente tras el retiro del Playbook V2 (el gate de confianza ya no existe) y cerrarlo si no.
- [ ] **DAT-06** Declarar `MetaTrader5` en `pyproject.toml` y `uv.lock`: hoy no está, y un `uv sync` puede dejar el MCP market-data sin datos (nota del CLAUDE.md global).
- [ ] **DOC-01** Issue #232: revisar una por una las cuatro contradicciones (manual, cierre semanal), ya sin el Playbook.
- [ ] **DOC-02** Revisión editorial del Manual de Operaciones, pendiente desde el 2026-09-27. (requiere DOC-01)
- [ ] **STO-01** Cerrar los issues #127 y #129: sus PR (#128 y #130) ya están en master.
- [ ] **STO-02** Issue #148: `ruta_story.ps1` no distingue horizontal de vertical.
- [ ] **MEM-01** Decidir qué memoria usa AGY: hoy lee OMEGA y no episteme, y la sección de OMEGA del CLAUDE.md alimenta `.agents/rules/proyecto.md`. (decide el director)
- [ ] **MEM-02** Retirar OMEGA del scope user cuando genesis y pepo hayan corrido `/episteme-setup`.

---

## Para después (fuera de las fases activas)

- [ ] **FUT-01** Issue #141: exponer velas OHLC en market-data.
- [ ] **FUT-02** Stories GI: issues #110 a #115 y lo que falta de la fase C (calendario, semanal, earnings).
- [ ] **FUT-03** Issue #87 (reabierto): pipeline de gráficos propio.
- [ ] **FUT-04** Issue #132: columna vertebral del cockpit de decisión.
- [ ] **FUT-05** Evergreens por activo: USD/CLP, oro, WTI, US100, cobre y Brent.
- [ ] **FUT-06** Medir contra el azar la línea usada como stop o referencia de salida, y los números redondos.
- [ ] **FUT-07** El 10 años del día con `tasas_en_vivo` en vez de FRED, y el diferencial BCCh contra Fed del USD/CLP.
- [ ] **FUT-08** Calendario económico de otros países (Suiza, Reino Unido, Canadá).
- [ ] **FUT-09** Lector del BCCh como fuente oficial y lectura de sitios de empresas sin RSS ni EDGAR.
- [ ] **FUT-10** Columnas "sin efecto atribuido" del correo y drivers de las acciones (diseño aparte).
- [ ] **FUT-11** `pipeline_linkedin.leer_agenda` lee una sola pestaña del calendario.
- [ ] **FUT-12** Plantillas semanales comerciales: en pausa, faltan el visto bueno de marketing y el de cumplimiento.
- [ ] **FUT-13** Que `avisos_resultado` (`leer_jornada`, `pipeline_avisos.py`) acepte datos de impacto bajo de Chile clasificados en el glosario, como el IPC mensual (real, esperado y anterior), hoy filtrado por `min_impact="high"`.
