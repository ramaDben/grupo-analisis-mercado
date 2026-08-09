# /oportunidad

Genera la pieza que invita a operar: imagen más mensaje de WhatsApp. No es una señal: sin entrada, TP ni SL.

## Cómo ejecutar este comando

1. Lee `.agents/rules/proyecto.md`. Son las reglas del proyecto que aplican a
   toda pieza: tono, decimales, hora de Chile y flujo de aprobación.
2. Lee `.claude/commands/oportunidad.md` **completo**. Ese archivo es la definición
   canónica de este comando y manda sobre cualquier resumen, incluido este.
3. Ejecuta sus pasos tal como están escritos, sin saltarte ninguno.

Si el comando pide datos de mercado, salen del MCP `market-data`; si pide la
hora, del reloj del sistema. Nunca los inventes ni los busques en la web — esas
dos reglas están en el archivo de reglas y valen también acá.

---
<!-- Generado por scripts/agy_workflows.py. No editar a mano: el próximo
     `--check` lo marcaría como desactualizado. Para cambiar lo que hace el
     comando, se edita `.claude/commands/oportunidad.md`. -->
