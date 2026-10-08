# Bot de Telegram para analistas: informes HTML personalizados por trader

## Contexto

El director decidió que su equipo de analistas y ejecutivos pueda pedirle a un bot de Telegram
las mismas piezas que hoy le pide a Claude Code (informe de un activo, calendario económico,
resultado de un dato, informe de la jornada), generadas en el momento con datos del terminal, y
recibirlas como **HTML** en Drive y en el chat, con una **versión dedicada para su trader**.

AGY dejó un primer garabato (`scripts/bot_analistas_telegram.py` y compañía) que se revisó y no
sirve de base: no llama a agy, no autoriza usuarios, entrega siempre el mismo PDF estático de
USD/CLP con precios escritos a mano (Regla 1; dice cobre $9.500 y el terminal está sobre 14.400),
cae en silencio a un gráfico de prueba y nunca sube a Drive. Se rescata solo el bucle de
long polling y `probar_token_telegram`.

### Diseño aprobado (4 secciones, 2026-10-08)
1. **Arquitectura**: bot → cola → **Python prepara** (datos + imágenes de WhatsApp) → **agy solo
   escribe textos** en un JSON de esquema fijo → **Python arma el HTML** con plantillas propias.
   agy no toca nada visual. Identidad visual: cabecera, franja *Preparado para / Asesor
   asignado / Cotización / Edición*, lema «Primero entiende. Después decide. Luego invierte.» y
   pie legal **del evergreen GI**; cuerpo con la tipografía y legibilidad **de la guía USD/CLP**
   (Goldman / Plus Jakarta Sans / Space Grotesk, cuerpo 11-13 pt, nada bajo 9,5 pt salvo legal,
   3 capas). Cifras solo del payload del terminal.
2. **Piezas v1**: `/activo`, `/calendario [hoy|semana]`, `/dato [nombre|último]`,
   `/jornada [apertura|cierre]`, cada una con `para <trader>` opcional.
3. **Seguridad/cupos/fallas**: allowlist de chat_id; agy nunca recibe texto del usuario; la
   personalización no gasta agy (rehace solo el HTML); reuso de la pieza base mientras está
   vigente; cola de uno; cupo diario por analista; fallas con motivo y sin rellenos; carpeta
   aislada por pedido; nunca tocar WhatsApp ni la bitácora.
4. **Pruebas**: unidad sin agy/MT5, bot con dobles, contratos, prueba real por pieza.

Ajuste respecto de lo conversado, que sale de la exploración: **la preparación la hace Python,
no agy**. Los constructores puros ya existen y son deterministas; así el bot valida datos antes
de gastar créditos, y agy queda reducido a su única tarea con juicio (redactar).

## Flujo

```
Telegram ─► bot.py (allowlist, gramática, cupo) ─► cola (1 worker)
  worker:
   1. preparar.py  → data/informes_analistas/<pedido>/pieza.json (datos + campos "[[ESCRIBIR]]") + PNG
   2. ¿pieza base vigente en caché?  sí → saltar a 4
   3. agy_encargo.invocar("/analista <ruta pieza.json>")  → rellena SOLO campos editoriales
   4. validar (vacíos, guion largo, voseo, HTML, cifras ajenas) → informe_html.py
   5. HTML genérico (+ dedicado si "para X") → carpeta Drive + sendDocument + link carpeta
```

## Archivos nuevos (paquete `scripts/analista/`)

| Archivo | Responsabilidad | Reusa |
|---|---|---|
| `scripts/analista/orden.py` | Gramática del pedido → `Orden(pieza, args, trader, analista)`; saneo del nombre (letras, tildes, espacios, ≤60); resolución de activo por alias | alias de `config/activos.json` / `catalog` |
| `scripts/analista/preparar.py` | Una función por pieza que escribe `pieza.json` + PNG en el dir del pedido. **Nunca** llama a los `preparar()` de producción | ver tabla siguiente |
| `scripts/analista/esquema.py` | Campos editoriales por pieza y su validación | `pipeline_carrusel.exigir_texto_editorial`, `validador_editorial.validar_payload_editorial`, `MARCA_EDITORIAL="[[ESCRIBIR]]"` |
| `scripts/analista/informe_html.py` | `pieza.json` → HTML autocontenido; `html.escape` en todo texto; PNG y fuentes en base64 | `guia_usdclp/estilos.caras_de_fuente`, `codificar_asset_base64` |
| `scripts/analista/agy.py` | Envoltorio de una línea sobre `agy_encargo.invocar`/`clasificar` con prompt fijo y timeout 12 min | `scripts/agy_encargo.py` |
| `scripts/analista/bot.py` | Long polling con `requests`, allowlist, cola + hilo worker, cupo, caché de reuso, respuestas | bucle y `probar_token_telegram` del garabato |
| `templates/informes_analista/base.html` + `informe.css` | Cabecera/franja/lema/pie del evergreen reescritos con `var(--rol)`; cuerpo con medidas de la guía; barra de personalización `.no-print` | clases y JS de `construir_evergreen_usdclp.py` (header ~:160-270/:745-783, lema :666/:1038, pie :677, JS ?cliente=&asesor= :1057-1090) |
| `templates/informes_analista/{activo,calendario,dato,jornada}.html` | Cuerpo por pieza | — |
| `config/analistas_telegram.json` | `{chat_id: {nombre, cargo, contacto, rol, cupo_diario}}` + `ruta_drive`, `url_carpeta_drive`, ventanas de reuso | — |
| `.claude/commands/analista.md` | Workflow de agy: leer `pieza.json`, rellenar solo `[[ESCRIBIR]]` siguiendo `.agents/rules/proyecto.md`, no ejecutar nada más | — |
| `scripts/instalar_bot_telegram.ps1` | Tarea `GI-BotTelegram` AtLogOn, `-RestartCount`, sin límite de tiempo, flags de batería; dry-run por defecto | clon de `scripts/instalar_reloj.ps1` |
| `docs/bot-analistas.md` | Manual de operación y uso | — |

### Fuentes por pieza (`preparar.py`)

- **activo**: `mt5_client.connect()` → `sc.evaluar_activo(activo, [], None, ahora, fijo=True, ignorar_agotamiento=True)` → `pc._serie_para` → `pc.construir_payload` (receta de `pipeline_avisos.leer_terminal`, L1193). Imagen: TradingView `generar_grafico_tv(..., n_velas=320)` embebido en `alerta.html` vía `_con_grafico_tv` + `tokens_de` (modelo de `pipeline_avisos` L1142). Escenarios y "por qué H1" se arman en Python desde `construir_mensaje_alerta` / `MARCOS_CANONICOS` / `nota_volatilidad`. Editorial: titular, lectura, drivers (alza/baja), qué NO hacer.
- **calendario hoy**: `pipeline_avisos.leer_jornada` + `lamina_dia` (+ `lamina_lectura_dia`); **semana**: `pipeline_linkedin.leer_agenda` + `lamina_semana`. Imagen: `calendario.html` vía `story_render.render_story`. Marca ✅/🕐 contra el reloj. Editorial: explicación novata por evento fuerte.
- **dato**: `resultado_pendiente` / eventos del día → `leer_movimiento` + `monedas_de` → `lamina_resultado` (es la imagen que hoy sale por WhatsApp, plantilla `calendario`). Si no salió: modo anticipación con `lamina_dia` filtrada. Editorial: 3 capas + impacto por activo.
- **jornada**: piezas de librería de `pipeline_informe` (`_curva`, `_calendario`, `leer_activos(destino)`, `_lectura_por_activo`, `_tabla_curva`) + `grafico_informe.construir_grafico`. **No** `pipeline_informe.preparar` (dir fijo `data/informes`, colisiona). Editorial: lectura por activo.

Ojo detectado: `pipeline_datos` y otros importan `guardrails.*` asumiendo `scripts/` en `sys.path`; el paquete lo agrega al importar.

## Archivos a modificar

- `scripts/agy_workflows.py`: `COMANDOS["analista"]` y regenerar `.agents/workflows/analista.md`.
- `scripts/marca_tokens.py`: `DIR_STORIES` pasa a lista de directorios que incluye `templates/informes_analista/` (hoy el gate solo cubre `templates/stories/`; `estilos.py` hardcodea hex, por eso no se importa su CSS, solo medidas y fuentes).
- `.gitignore`: `data/informes_analistas/`, `data/.bot_telegram_*`, `config/service_account.json`.
- `CLAUDE.md`: una línea que enlaza `docs/bot-analistas.md` (no cambia lo que sale a un grupo) + `agy_reglas.py` si aplica.

## Retiro del garabato

Archivos sin versionar de AGY: `scripts/bot_analistas_telegram.py`, `iniciar_bot_telegram.ps1`,
`gestor_drive.py`, `compilar_informes_evergreen.py`, `construir_evergreen_usdclp.py`,
`templates/informes/evergreen_usdclp.html`, `data/cache_solicitudes.json`, `data/drive_staging/`,
`data/informes_evergreen/`. Se mueven a `respaldo/garabato-bot-2026-10-08/` (fuera de git)
**después** de extraer la cabecera, y se pide confirmación antes de borrar nada.
`TORPEDO_MICRO_PYTHON.md` y los cambios ajenos (`pipeline_carrusel --grupo`, imagen del cobre)
no se tocan ni entran en esta rama.

## Orden de trabajo (TDD, rama `feat/bot-analistas-telegram` desde `master` en worktree)

1. Escribir la spec en `docs/superpowers/specs/2026-10-08-bot-telegram-analistas-design.md` (este diseño) y commit.
2. `orden.py` + tests de gramática y saneo.
3. `esquema.py` + tests (vacío, `—`, voseo, etiquetas HTML, cifra ajena: todo número con decimales o ≥3 dígitos en texto editorial debe existir en los datos de la pieza).
4. Plantillas + `informe_html.py` con fixtures por pieza; tests: escape, dedicada solo cambia la franja, tamaño mínimo 9,5 pt salvo `.legal`, gate de `marca_tokens` verde.
5. `preparar.py` por pieza con MT5 doble (inyectando lectores, como ya hacen `pipeline_avisos`/`screener`); test de que no escribe fuera del dir del pedido.
6. `analista.md` + `agy_workflows` + `agy.py`; test `--check`.
7. `bot.py` con Telegram y agy dobles: allowlist, desconocido recibe su ID, cola, cupo, reuso, personalización sin agy, falla con motivo.
8. Contrato: el paquete no contiene `enviar_whatsapp`, `whatsapp_sender`, `despachar(`, `bitacora_despachos`, `historial_despachos` (patrón de `tests/test_reloj_gi.py:153`).
9. `instalar_bot_telegram.ps1`, `.gitignore`, docs; retiro del garabato.

## Verificación

- `uv run pytest` completo (incluye `test_agy_workflows`, `test_marca_tokens`, nuevos).
- `uv run python scripts/marca_tokens.py --check` y `scripts/agy_workflows.py --check`.
- E2E por CLI sin Telegram: `uv run --with MetaTrader5 --extra stories --extra informe python -m analista.bot --una "/activo oro para Juan Pérez" --chat <id director>` para cada pieza; abrir cada HTML en Chrome al 100 %, revisar acentos `¿ ¡ ·`, que todo nivel citado esté trazado, cifras = terminal (`get_asset_levels`), barra de personalización genera la dedicada.
- E2E real: `--test-token`, luego el director pide una pieza desde Telegram; verificar archivo en la carpeta Drive sincronizada (ruta a confirmar cuando esté instalado Drive para escritorio).
- Nada en `data/carrusel/`, `data/screener/`, `historial_despachos.json` cambió tras las pruebas (`git status`).
