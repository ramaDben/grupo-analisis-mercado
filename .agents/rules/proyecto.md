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
