# Referencia de comandos

Seis comandos, expuestos por igual a Claude Code y a Antigravity. La producción diaria se rige
por **el carrusel y el informe**; el resto son piezas puntuales y utilidades.

El catálogo era de veintiocho. Se retiró todo lo que orquestaban los comandos de día
(`/lunes` … `/domingo`, `/apertura`, `/alerta`, `/dato_macro`, `/noticia`, `/actualizacion`,
`/accion`, `/earnings`, `/señal`), lo educativo satélite (`/concepto`, `/pregunta`,
`/respuesta`, `/curriculo`), `/chart`, y los internos `/ventas` y `/postventa`. Sus definiciones
siguen en la historia de git si alguna vez hacen falta.

---

## `/carrusel` — la producción diaria

Escanea el universo, elige objetivamente qué comunicar y arma las piezas por canal.

```bash
/carrusel                      # Top 3 de la sesión activa
/carrusel --grupo metales      # un canal concreto
/carrusel --matriz             # Top 1 de cada uno de los 5 canales de mercado
```

`scripts/screener_gi.py` detecta la sesión (Asiática, Europea, Apertura Wall Street, Rotación de
Tarde, Cierre o Fin de Semana) y puntúa cada activo con el `Score_GI` sobre 100: técnico 35 +
catalizador macro 25 + espacio ADC/ATR 20 + momentum 20. Antes de puntuar aplica cuatro
**gates**, que son prohibiciones y no puntos: feriado de la bolsa, blackout por calendario,
prohibición del Playbook y agotamiento del ATR diario.

Cada canal recibe además **su propia lectura macro**: `contexto_macro_grupos.py` arma la agenda
del día filtrada para ese canal, la curva soberana y el mecanismo que explica por qué le importa,
más una Story de dato macro. Todo derivado de las series oficiales de `data central/`.

`--grupo` acepta los alias de `config/whatsapp_grupos.json` (`metales`, `oro`, `forex`,
`indices`, `acciones`, `cripto`, `senales`, `macro`, o el nombre del canal). **Un alias que no se
reconoce aborta**: antes caía en silencio al canal macro y publicaba en el grupo equivocado.

> **No corras `--preparar` de prueba.** El escáner lee las corridas anteriores del día para no
> repetir activos, así que un ensayo los excluye de la corrida real.

## `/informe [apertura|cierre]` — el informe de la jornada

- **Apertura**: PDF institucional A4 con banners por activo a 300 DPI, curva soberana y agenda.
- **Cierre**: chat-first, mensaje con gráfico y **sin PDF**. Un PDF al día, no dos: la fatiga de
  descargas es real.

La apertura **no se emite con el sesgo del motor vencido**, salvo `--con-datos-viejos`, que
estampa el aviso en la primera página.

## `/story [tipo]` — una pieza suelta

Para cuando hace falta algo fuera de la tanda. **No pregunta nada**: el tipo, el activo y la
temporalidad van como argumentos, y si falta alguno se detiene.

| tipo | qué es | datos |
|---|---|---|
| `alerta` | niveles del día de un activo | `get_asset_levels` |
| `dato_macro` | un dato que ya publicó, con su veredicto | calendario + `data central/` |
| `breaking` | noticia urgente, 100% editorial | ninguno |
| `calendario` | 3 a 6 eventos macro de la semana | `obtener_calendario_macro` |

Son las cuatro plantillas que existen en `templates/stories/`. Un tipo sin plantilla se rechaza:
el estándar de diseño lo comanda ahora el brand kit (`brand_atomic_system/`).

## `/encuesta [tipo] [activo]` — sentimiento del canal

Tres tipos: `posicion`, `tendencia`, `movimiento`. Sin precios ni contenido educativo dentro.

Regla de oro: **antes de la encuesta, el canal tiene que haber recibido contexto** para votar
informado. En la práctica, el contexto macro que publica el carrusel esa mañana.

## `/rencuesta` — el desarrollo didáctico

Toma el tema de una encuesta y lo explica, construyendo la malla de conceptos.
`/rencuesta` (la última), `/rencuesta [tema]`, `/rencuesta mapa` (vista de repaso).

## `/estado` — diagnóstico

Dashboard del sistema: si la sesión de WhatsApp sigue vinculada, cuántos envíos van hoy contra el
cupo, frescura del sesgo del motor y estado de los MCPs. **No envía nada.**

---

## Flujo de aprobación (aplica a todos)

1. El comando genera el contenido y lo muestra.
2. El director aprueba o pide ajustes.
3. **Al aprobar**: se guarda con `scripts\ruta_mensaje.ps1` o `scripts\ruta_story.ps1` — nunca se
   arma la ruta a mano.
4. Se envía. La tanda completa, canal por canal:
   `scripts/pipeline_carrusel.py --despachar data/carrusel/<tanda>` (`--desde N` retoma).
   Una pieza o un canal suelto:
   `scripts/enviar_whatsapp.py --grupo <alias> [--lote <carpeta> | --adjunto ... --mensaje-archivo ...]`

**Cada canal sale en una sola acción con todas sus piezas.** El editor de medios acepta
varias imágenes y cada una conserva su propio pie, así que una tanda de cinco canales son
cinco acciones y no veinte. Y cada canal se rinde **justo antes** de salir: si el precio
cruzó un nivel que el texto daba por vigente, esa pieza no se envía y el despacho lo dice.

Un lote tiene que ser del mismo tipo: el menú Adjuntar entra por "Fotos y videos" o por
"Documento", no por ambas.

**Nunca se envía nada sin la aprobación explícita del director.**

El envío verifica que la pieza aparezca en la conversación antes de reportar éxito, y compara la
cabecera del chat contra el destinatario de forma exacta. **Si aborta, no se envió**: revisa si
llegó antes de reintentar, porque repetir a ciegas duplica la pieza.

Automatizar WhatsApp Web va contra sus términos de servicio: el comando impone 45 s mínimos entre
acciones de envío y un cupo de 40 mensajes al día, y espera cuando toca. Un lote es una acción
pero N mensajes: la cadencia se aplica una vez, el cupo se descuenta por pieza.

**Un solo dueño de la sesión a la vez.** El perfil de Chromium admite un proceso; Claude Code y
Antigravity abriéndolo a la vez crean un perfil paralelo, y eso desvinculó la sesión el
2026-09-01 y el 2026-09-02.

## Tipos de archivo guardado

`niveles`, `dato_macro`, `alerta`, `encuesta`, `cierre` — la carpeta `<tipo>` dentro de
`data/mensajes/<fecha>/<activo>/`. Sin activo protagonista, cae en `_general/`.
