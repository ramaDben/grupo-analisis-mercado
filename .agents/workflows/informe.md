# /informe

Informe de la jornada: PDF institucional en la apertura, mensaje con gráfico al cierre.

## Cómo ejecutar este comando

1. Lee `.agents/rules/proyecto.md`. Son las reglas del proyecto que aplican a
   toda pieza: tono, decimales, hora de Chile y flujo de aprobación.
2. Lee `.claude/commands/informe.md` **completo**. Ese archivo es la definición
   canónica de este comando y manda sobre cualquier resumen, incluido este.
3. Ejecuta sus pasos tal como están escritos, sin saltarte ninguno.

## Los argumentos

`.claude/commands/informe.md` está escrito para otro runner y espera sus
argumentos en un marcador llamado `$ARGUMENTS`. Acá **ese marcador no se
sustituye solo**: los argumentos son lo que el director escribió después de
`/informe` en su mensaje.

Antes de seguir los pasos del comando, toma ese texto y úsalo en todos los
lugares donde el archivo diga `$ARGUMENTS`. Si el director no escribió nada
después del comando, trata `$ARGUMENTS` como vacío — el propio comando define
qué hacer en ese caso, y normalmente es preguntarle al director en vez de
elegir por él.

Nunca inventes un argumento que no te dieron. En este proyecto elegir el activo
o el tipo de pieza por cuenta propia es decidir qué se le manda al cliente.

## Los datos

Si el comando pide datos de mercado, salen del MCP `market-data`; si pide la
hora, del reloj del sistema. Nunca los inventes ni los busques en la web — esas
dos reglas están en el archivo de reglas y valen también acá.

---
<!-- Generado por scripts/agy_workflows.py. No editar a mano: el próximo
     `--check` lo marcaría como desactualizado. Para cambiar lo que hace el
     comando, se edita `.claude/commands/informe.md`. -->
