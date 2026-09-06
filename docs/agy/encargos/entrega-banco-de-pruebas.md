---
titulo: Entrega real al banco de pruebas
archivos:
  - data/.whatsapp_envios.json
verificar:
  - uv run python scripts/enviar_whatsapp.py --status
---

Entrega **real** al canal interno de pruebas. Esto mide el ultimo tramo del flujo, que
es el unico que sale al mundo, y por eso se hace contra el banco y nunca contra un canal
de clientes.

## Que hay que hacer

Toma la pieza de Solana que ya existe y entregala al banco de pruebas:

- texto: `data/carrusel/2026-09-06_14-48_fin_de_semana/06_criptoactivos/2_solusd_mensaje.txt`
- imagen: `data/carrusel/2026-09-06_14-48_fin_de_semana/06_criptoactivos/2_solusd.png`

## Reglas de esta entrega, y no son negociables

**El destino se nombra con el flag `--pruebas` de `scripts/enviar_whatsapp.py`.** No
existe otra forma: `--grupo banco_de_pruebas` **no resuelve**, porque el banco vive fuera
del mapa de canales a proposito y el sender devuelve el literal, que WhatsApp no
encuentra. El flag no toma un destino, lo resuelve del config.

**NO uses `--dry-run`.** Una corrida anterior simulo y por eso no midio nada. Esta
entrega tiene que salir de verdad.

**NO regeneres la pieza ni actualices los precios.** Los niveles son de las 14:48 y eso
esta bien: el banco existe para medir contra el DOM de WhatsApp Web, no es un canal de
clientes, y regenerar cambiaria lo que se esta midiendo.

**Un solo envio.** Texto y adjunto van en la misma accion, que es como lo hace el
proyecto: el texto se escribe primero y el adjunto despues, para que el pie no quede
sujeto al tope de 1.024 caracteres del editor de medios.

**Cualquier otro canal esta prohibido.** Un hook del sistema niega todo destino que no
sea el banco y limita esta prueba a dos envios. Si te lo niega, informa el motivo exacto
y detente: no busques otra via, la negacion es la respuesta.

## Que reportar

En pocas lineas: el comando exacto, que dijo el sender sobre la entrega, y como quedo
`data/.whatsapp_envios.json` (fecha y cuenta) antes y despues.
