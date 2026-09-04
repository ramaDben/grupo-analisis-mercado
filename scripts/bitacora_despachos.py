# -*- coding: utf-8 -*-
"""Bitacora de lo que se despacho, pieza por pieza.

`data/.whatsapp_envios.json` es un CONTADOR: `{fecha, enviados, ultimo_ts}`. Sirve
para el cupo y la cadencia y no para nada mas. Despues de un despacho abortado a
mitad de canal, nadie sabe **que** salio salvo abriendo WhatsApp.

Eso importo el 2026-09-03, cuando el despacho paso a **una pieza por accion** para
que el pie de foto no llegue mutilado. Desde entonces `--desde N` quedo midiendo en
la unidad equivocada: cuenta canales mientras el envio cuenta piezas, asi que
retomar un canal que fallo en su segunda de tres piezas **reenvia la primera**. Y
duplicar un mensaje en un canal de clientes es justo el patron por el que marcan
una cuenta.

Tres decisiones:

1. **Se anota DESPUES de que el envio se confirma contra el DOM**, y desde dentro
   del bucle de piezas. `enviar_lote` levanta ante un fallo y su `return` no
   ocurre, asi que anotar al final perderia exactamente la informacion por la que
   existe la bitacora.
2. **La identidad de una pieza es (tanda, canal, pieza)**, no el activo. Una tanda
   nueva del mismo activo es contenido legitimo con niveles nuevos; la misma pieza
   de la misma tanda es una repeticion.
3. **Se versiona**, igual que `historial_senales.json` y `historial_suplementos.json`.
   `data/.reloj_disparos.json` es el mecanismo mas parecido y esta gitignoreado,
   pero evita volver a *preparar*, que es barato y reversible. Esto evita volver a
   *enviar a un cliente*, que no lo es. Un clon nuevo sin bitacora reenviaria la
   tanda del dia.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
HISTORIAL_PATH = RAIZ / "data" / "historial_despachos.json"


def cargar(ruta: Path | None = None) -> list[dict[str, Any]]:
    """Lo ya despachado. Una bitacora ausente o ilegible se lee como vacia."""
    destino = ruta or HISTORIAL_PATH
    try:
        datos = json.loads(destino.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return datos if isinstance(datos, list) else []


def clave(tanda: str, canal: str, pieza: str) -> str:
    return f"{tanda}|{canal}|{pieza}"


def ya_despachada(
    historial: list[dict[str, Any]], tanda: str, canal: str, pieza: str
) -> bool:
    """Si esa pieza exacta de esa tanda exacta ya salio."""
    objetivo = clave(tanda, canal, pieza)
    return any(
        clave(e.get("tanda", ""), e.get("canal", ""), e.get("pieza", "")) == objetivo
        for e in historial
    )


def registrar(
    tanda: str,
    canal: str,
    pieza: str,
    activo: str = "",
    huella: str = "",
    ahora: datetime | None = None,
    ruta: Path | None = None,
) -> dict[str, Any]:
    """Anota una pieza entregada y devuelve la entrada escrita.

    La `huella` es la del texto enviado, la misma que calcula
    `whatsapp_sender._huella`: permite ver despues si lo que salio es lo que el
    archivo dice hoy, sin guardar el mensaje entero por duplicado.
    """
    destino = ruta or HISTORIAL_PATH
    momento = ahora or datetime.now()
    entrada = {
        "fecha": momento.strftime("%Y-%m-%d"),
        "hora": momento.strftime("%H:%M"),
        "tanda": tanda,
        "canal": canal,
        "pieza": pieza,
        "activo": activo,
        "huella": huella,
    }
    historial = cargar(destino)
    historial.append(entrada)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(historial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return entrada
