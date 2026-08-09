# Reglas del proyecto — Grupo de Análisis de Mercado

Antigravity no lee `CLAUDE.md`, así que este archivo trae las reglas que
**cualquier** pieza tiene que cumplir. No las reemplaza: `CLAUDE.md` sigue siendo
la fuente completa y, ante cualquier duda o contradicción, manda `CLAUDE.md`.

Léelo antes de ejecutar cualquier workflow de `.agents/workflows/`.

---

## 1. Los datos no se inventan

Precios, niveles, indicadores, calendario económico y operaciones abiertas salen
**siempre** del MCP `market-data`. Nunca de tu memoria, nunca de una búsqueda web,
nunca deducidos de otro número.

Si el MCP falla, **detente y dilo**. Una pieza con un precio inventado es peor que
ninguna pieza: el cliente opera con ella.

### Qué hacer cuando el motor dice que no

El MCP devuelve `{"error": "CÓDIGO", "message": "..."}` cuando no puede darte el
dato. Ese error es una respuesta, no un obstáculo: **detente y repórtaselo al
director con el código exacto**. Él decide.

Lo que está prohibido, sin excepción:

- Completar el dato faltante con una estimación, un recuerdo o un número
  plausible. Un precio que nadie verificó dentro de una pieza que invita a
  operar es el peor resultado posible de este proyecto.
- **Modificar la configuración del proyecto para sortear el error.** Si el activo
  no está en `config/activos.json`, no lo agregues; si falta un color en
  `marca.css`, no lo inventes; si falta una imagen en
  `templates/stories/assets/`, no la descargues. Propónselo al director y espera.
  Puede que el activo no esté a propósito.

`TICKER_NOT_FOUND` merece una aclaración: el catálogo se carga cuando arranca el
servidor MCP, así que un activo agregado después aparece como inexistente hasta
reconectar. Si sospechas de eso, dilo — no lo resuelvas por tu cuenta.

### "Mejor/peor de lo esperado" exige un consenso publicado

El chip de veredicto compara un dato contra lo que el mercado **esperaba**. Solo se
puede usar cuando existe esa cifra de consenso y la tienes a la vista: la trae el
calendario económico junto al dato.

Un número sin consenso —flujos de ETFs, un volumen, una cifra de una noticia— puede
ir en la pieza como evidencia, pero **sin veredicto**. Ponerle "mejor de lo
esperado" a algo que nadie pronosticó es afirmar una comparación que no existe, y
el cliente la lee como un hecho verificado.

## 1 bis. Escribe los archivos en UTF-8

En Windows, `Set-Content` y `Out-File` de PowerShell usan por defecto la
codificación ANSI del sistema. Un payload JSON escrito así llega al renderer con
los acentos rotos, y la pieza sale con `AN?LISIS`, `inversi?n`, `?Quieres` — y
también el separador `·` de las cabeceras.

Usa siempre UTF-8 explícito:

```powershell
$json | Out-File -FilePath payload.json -Encoding utf8
```

o escribe el archivo con la herramienta de escritura del agente en vez de por
consola. **Antes de dar una pieza por buena, mira el PNG y verifica que los
acentos y los signos `¿` `¡` `·` se vean correctos.** Si aparece un `?` donde
debería haber una tilde, el problema es este y la pieza no se puede publicar.

## 2. La hora sale del reloj, no de la web

Nunca uses búsqueda web para saber la fecha o la hora. Para la hora de Chile:

```powershell
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
$now = [System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)
$now.ToString('yyyy-MM-dd HH:mm')
```

Para convertir la hora de un dato económico extranjero, usa
`scripts\hora_chile.ps1` — nunca offsets fijos, que producen desfases de una hora
cuando cambia el horario de verano.

## 3. Los decimales de cada precio están definidos

Todo precio respeta el campo `digits` de `config/activos.json` para ese activo.
Nunca truncar ceros al final ni redondear a entero.

| Activo | Digits | Correcto |
|---|---|---|
| USDCLP | 2 | $889.60 |
| USDJPY | 3 | 163.731 |
| XAUUSD | 2 | $4,539.72 |
| WTI.spot | 3 | $90.181 |
| US100.spot | 2 | 30,350.01 |
| Acciones | 2 | $192.50 |

## 4. Tono: profesional con gancho, nunca dramático

El cliente tiene que entender **hacia dónde va el activo**. Un análisis sin
dirección clara está incompleto — esa es la regla de oro.

Se toma postura direccional y se redacta para que dé ganas de operar. Lo que está
prohibido es el lenguaje extremo o coloquial:

| Evitar | Usar |
|---|---|
| "el oro se va a derrumbar" | "sesgo bajista" |
| "esto se va a disparar" | "impulso comprador" |
| "el mercado tiene una sensación pésima" | "presión vendedora" |

Toda sigla se explica en español la primera vez que aparece. Nada de jerga sin
traducir: el mensaje lo lee tanto un trader como alguien que recién empieza.

Si el texto va a un cliente, va en español chileno neutro, con tuteo. Nunca
voseo argentino.

## 5. Terminología de niveles

Siempre "soporte" y "resistencia". Nunca "techo" ni "suelo".

## 6. Nada se envía sin aprobación

Todo contenido se genera, se muestra al director y **espera su aprobación**. Al
aprobar, se guarda con `scripts\ruta_mensaje.ps1` (mensajes) o
`scripts\ruta_story.ps1` (imágenes) — nunca armes la ruta a mano.

El envío a WhatsApp lo hace el director copiando el texto. Tú no envías nada.

### La pieza se entrega completa

Varios comandos producen **imagen y texto**, no una sola cosa. `/oportunidad`
entrega la Story más el mensaje de WhatsApp que la acompaña; `/dato_macro` en
Modo resultado entrega la Story más su pie. Una imagen sin su texto llega muda al
grupo: el pie es lo único que se ve en la notificación de WhatsApp antes de abrir
el chat, y lo único legible si el cliente no descarga la imagen.

Antes de dar un comando por terminado, revisa qué entregables define su archivo
en `.claude/commands/` y confirma que produjiste **todos**, cada uno guardado con
el helper que le corresponde.

**Los nombres de archivo salen de los helpers, no de tu criterio.**
`ruta_story.ps1` devuelve la ruta completa y ya resuelve el nombre; no le agregues
sufijos como `_horizontal` ni `_v2`. Si necesitas guardar los dos formatos de una
misma pieza, pregúntale al director cómo quiere distinguirlos en vez de inventar
una convención nueva.

## 7. Color en las Stories

Si generas una imagen, los colores salen de `templates/stories/marca.css` vía
`var(--rol)`. Nunca escribas un hex.

Dos roles que no se mezclan: `--activo` es la identidad del activo (pinta el
escenario) y `--sube`/`--baja` es la dirección del mercado. Si se colapsaran, una
pieza dorada bajista se leería como alcista dorada.

Verifica con `uv run python scripts/marca_tokens.py --check`.

---

## Dónde está el resto

- `CLAUDE.md` — las reglas completas del proyecto.
- `.claude/commands/<nombre>.md` — la definición canónica de cada comando.
- `docs/architecture.md` — cómo encaja todo.
