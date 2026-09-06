# Notas de implementación

Decisiones técnicas **ya aplicadas** que no hace falta volver a tomar, y el árbol del proyecto.
Nada de esto cambia lo que sale a un canal: se consulta cuando algo no funciona y conviene
saber si ya se resolvió una vez.

---

## Estructura del proyecto
```
grupo-analisis-mercado/
├── README.md              ← introducción y referencia rápida
├── CLAUDE.md              ← este archivo (instrucciones para Claude Code)
├── docs/
│   ├── architecture.md    ← flujo del sistema, MCPs, aprobación, señales
│   ├── commands-reference.md ← referencia detallada de los comandos
│   ├── setup-guide.md     ← instalación paso a paso + troubleshooting
│   ├── activos-y-drivers.md  ← 20 activos con drivers y datos macro
│   ├── design/            ← diseños técnicos vigentes (ciclo Pulse) — incluye stories-gi/ y motor-como-cerebro-hub-gi
│   └── archive/           ← docs históricos de features ya implementadas (design/plan/superpowers)
├── .claude/
│   ├── commands/          ← 6 slash commands (invocar con /nombre)
│       ├── carrusel.md · informe.md   ← la produccion diaria
│       ├── story.md                   ← una pieza suelta (4 plantillas)
│       └── encuesta.md · rencuesta.md · estado.md
├── agents/                ← prompts de sub-agents
│   ├── recolector.md · analista.md · redactor.md
├── config/                ← configuración del sistema
│   ├── activos.json       ← 38 tickers: forex + commodities + 6 criptos + índices + 5 ETF + 14 acciones
│   ├── drivers.json · drivers_indices_sectores.json
│   ├── agenda_mercado.json  ← ventanas de sesion, anclajes de tanda y momentos del dia
│   ├── agenda_semanal.json · feriados_bolsa.json
├── scripts/               ← scripts auxiliares
│   ├── screener_gi.py     ← Score_GI sobre el universo + gates (feriado, blackout, Playbook, ATR)
│   ├── agenda_mercado.py  ← el unico reloj: ventanas, anclajes y momentos
│   ├── reloj_gi.py        ← el decisor del latido (solo prepara, nunca envia)
│   ├── instalar_reloj.ps1 ← registra el latido en el Programador de tareas
│   ├── noticia_oficial.py ← la nota oficial fresca que suplementa (EIA, BCE, Fed)
│   ├── pipeline_carrusel.py ← Top 3 del escaner → 3 Stories (--preparar / --rendir)
│   ├── pipeline_informe.py  ← informe de apertura (PDF) y de cierre (chat-first)
│   ├── sincronizar_css_plantillas.py ← re-embebe marca.css/piel.css en los 12 snapshots
│   ├── story_render.py    ← renderer de Stories GI (payload JSON → HTML → PNG con Playwright)
│   ├── story_grafico.py ← geometría del gráfico de recorrido (paso previo al render)
│   ├── serie_mt5.py       ← serie real de precios desde MT5 → bloque `recorrido`
│   ├── rendir_todas.py    ← rinde las 10 plantillas juntas, para revisión visual
│   ├── marca_tokens.py    ← verifica que ninguna plantilla hardcodee un color
│   ├── capacitacion_fundamental_ppt.py + _contenido.py ← generador del PPTX de capacitación (motor / contenido)
│   └── hora_chile.ps1 · ruta_mensaje.ps1 · ruta_story.ps1  ← helpers deterministas (hora Chile, ruta de guardado)
├── templates/             ← templates de mensajes WhatsApp
│   ├── encuesta_tendencia.txt · encuesta_posicion.txt · encuesta_movimiento.txt
│   ├── mapa_conceptos.txt
│   └── stories/           ← snapshots de marca GI (11 plantillas) + marca.css · fonts/ · assets/activos/
├── conceptos/             ← notas canónicas de conceptos educativos (malla /rencuesta)
│   ├── README.md · stop-loss.md
├── data/                  ← datos persistentes
│   ├── historial_senales.json · historial_encuestas.json
│   ├── mapa_conceptos.json · glosario_siglas.json · glosario_motor.json
│   └── charts/ · mensajes/ · stories/  ← generados (gitignored)
├── mql5/                  ← Service MQL5 (ChartObjectsExporter) + archive/ (CalendarExporter, deprecado)
└── mcp/
    ├── mcp_config.example.json ← template sin credenciales (en git)
    └── mcp_config.json         ← config real con API keys (gitignored)
```

## Stories GI — CSS embebido (solución Playwright 2026-08-12)

**Problema:** `story_render.py` genera HTML temporal y lo navega con `file://`, pero Playwright no resolvía las rutas relativas `<link href="marca.css">`, causando que los estilos no se cargaran. Resultado: elementos visibles en el HTML (como fecha/hora) no aparecían en el PNG final, sin error visible.

**Solución (IMPLEMENTADA):** Embeber CSS directamente en cada plantilla HTML en bloques `<style>`, eliminando la dependencia de rutas externas.

**Cómo se aplicó:**
- Todas las plantillas (`alerta.html`, `dato_macro.html`, `calendario.html`, etc.) ahora incluyen `marca.css` y `piel.css` (si aplica) incrustados en `<style>` en el `<head>`.
- Script de automatización: `scripts/embeber_css_plantillas_v3.py` (incrusta CSS en cualquier plantilla que lo use).

**Impacto:**
- ✅ Playwright siempre tiene estilos disponibles, sin resolver rutas.
- ✅ Elementos como fecha/hora ahora son visibles en los PNG.
- ✅ No hay cambio en el contrato de tokens `{{campo}}` ni en `build_context`.

**Si agregas una plantilla nueva:**
- Si usa `<link rel="stylesheet" href="marca.css">` o `piel.css`, ejecuta:
  ```bash
  uv run python scripts/embeber_css_plantillas_v3.py
  ```
- O embebe manualmente el CSS en un `<style>` antes del `</head>`.
