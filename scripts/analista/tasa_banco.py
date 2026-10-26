"""El dato de tasas del banco central que mueve al activo, para el correo de `/oportunidad`.

Spec 2026-10-24 §3. Lo lee Python de `data central/` y se sella en `datos.tasa` al preparar. Se
muestra con el nombre real de la serie y la fecha del dato, sin la fecha de la última decisión: no
está en los datos, y deducirla de la serie (DFF cambia un día después del anuncio, BCE_DFR tiene
huecos) le llevaría una fecha errada al cliente.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analista import RAIZ

CONFIG = RAIZ / "config" / "tasa_por_activo.json"


def cargar_config(ruta: Path = CONFIG) -> dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def banco_de(ticker: str, clase: str, cfg: dict[str, Any]) -> str | None:
    return cfg["por_ticker"].get(ticker) or cfg["por_clase"].get(clase)


def leer(ticker: str, clase: str, ahora: datetime, raiz: Path = RAIZ,
         config: Path = CONFIG) -> tuple[dict[str, Any] | None, str | None]:
    """`(tasa, None)`, `(None, aviso)` si el dato no está o venció, o `(None, None)` sin banco mapeado."""
    from market_data_mcp.frescura import validar_staleness

    cfg = cargar_config(config)
    clave = banco_de(ticker, clase, cfg)
    if clave is None:
        return None, None
    b = cfg["bancos"][clave]
    try:
        crudo = json.loads((raiz / b["archivo"]).read_text(encoding="utf-8"))
        serie = crudo
        for paso in b["ruta"]:
            serie = serie[paso]
        fecha, valor = max(serie["historico"].items())
    except (OSError, ValueError, KeyError, TypeError):
        return None, f"No encontré la tasa de {b['nombre']}: el correo sale sin el dato de tasas."
    fresco, horas, _, _ = validar_staleness(crudo.get("as_of"), now_dt=ahora)
    if not fresco:
        return None, (f"La tasa de {b['nombre']} tiene {horas:.0f} h sin actualizar: "
                      "el correo sale sin el dato de tasas.")
    dia = datetime.strptime(fecha, "%Y-%m-%d")
    linea = (b.get("lineas_por_clase") or {}).get(clase) or b["linea"]
    return {"banco": clave, "nombre": b["nombre"], "serie": b["serie"],
            "valor": f"{float(valor):.2f}".replace(".", ","), "fecha": f"{dia:%d/%m}",
            "linea": linea, "motivo_imagen": "banco_central"}, None
