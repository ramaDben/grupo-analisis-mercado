"""Registro de análisis por activo: quién lo generó, cuánto vale y qué se hizo con él.

Se versiona, como la bitácora de despachos: es historia de lo que el equipo comercial le mandó a
sus clientes. Cumple dos funciones (spec 2026-10-16 §2 y §5):

1. **Reúso.** Un análisis vale 7 días corridos desde que se creó. Mientras esté vigente, cualquiera
   que pida ese activo recibe el mismo, sin gastar agy ni cupo. Puede caducar antes si la lectura
   se rompe (`caducar`); el análisis caducado queda como historia, con su motivo.
2. **El análisis contra el que se mide `/seguimiento`.**

Las entradas del formato antiguo (una por semana, con `semana` y sin `ticker`) se conservan en el
archivo y se ignoran: son historia de solo lectura.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from analista import RAIZ

RUTA = RAIZ / "data" / "semanal" / "registro.json"
VIGENCIA = timedelta(days=7)


class RegistroDanado(ValueError):
    """El registro no se puede leer: no se sigue, para no pisarlo."""


def _leer(ruta: Path) -> list[dict[str, Any]]:
    """Solo un archivo ausente es un registro vacío. Un JSON corrupto levanta: si se
    tratara como vacío, la próxima escritura borraría toda la historia."""
    try:
        texto = ruta.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        raise RegistroDanado(f"registro semanal corrupto, no se sobrescribe: {ruta}") from e


def _escribir(ruta: Path, entradas: list[dict[str, Any]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(entradas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(ruta)


def _ultima(entradas: list[dict[str, Any]], ticker: str) -> dict[str, Any] | None:
    """La entrada más reciente del activo: la que manda. Las del formato antiguo no tienen `ticker`."""
    return next((e for e in reversed(entradas) if e.get("ticker") == ticker), None)


def anterior(ticker: str, ruta: Path = RUTA) -> dict[str, Any] | None:
    """La lectura del análisis previo del activo, vigente o no, para contar el cambio de lectura.

    Devuelve `direccion`, `creada` (datetime) y `motivo` (por qué caducó antes de los 7 días, o "" si
    simplemente venció). Sin análisis previo o sin dirección anotada, None.
    """
    e = _ultima(_leer(ruta), ticker)
    if e is None or not e.get("direccion"):
        return None
    return {"direccion": e["direccion"], "creada": datetime.fromisoformat(e["creada"]),
            "motivo": (e.get("caducada") or {}).get("motivo", "")}


def vigente(ticker: str, ahora: datetime, ruta: Path = RUTA) -> dict[str, Any] | None:
    """El análisis vigente del activo, si existe, no caducó, no venció y su carpeta sigue en disco."""
    e = _ultima(_leer(ruta), ticker)
    if e is None or e.get("caducada"):
        return None
    if datetime.fromisoformat(e["vence"]) <= ahora:
        return None
    return e if _completo(Path(e["dir"])) else None


def vigentes(ahora: datetime, ruta: Path = RUTA) -> list[str]:
    """Los activos que hoy tienen un análisis vigente, en el orden en que aparecen en el registro."""
    tickers = list(dict.fromkeys(e["ticker"] for e in _leer(ruta) if e.get("ticker")))
    return [t for t in tickers if vigente(t, ahora, ruta) is not None]


def _completo(dir_pedido: Path) -> bool:
    """`pieza.json` y las imágenes que declara (el gráfico que la ficha incrusta) siguen en disco.

    Sin el gráfico, la ficha falla en cada pedido durante los 7 días: mejor rehacer el análisis.
    """
    try:
        pieza = json.loads((dir_pedido / "pieza.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    imagenes = pieza.get("imagenes") if isinstance(pieza, dict) else None
    return all((dir_pedido / str(n)).exists() for n in (imagenes or {}).values())


def anotar(ticker: str, dir_pedido: Path, creada: datetime, direccion: str,
           creado_por: dict[str, str], ruta: Path = RUTA) -> dict[str, Any]:
    entradas = _leer(ruta)
    nueva = {"ticker": ticker, "dir": str(dir_pedido), "creada": creada.isoformat(),
             "vence": (creada + VIGENCIA).isoformat(), "direccion": direccion,
             "creado_por": creado_por, "reusos": [], "seguimientos": [], "caducada": None}
    entradas.append(nueva)
    _escribir(ruta, entradas)
    return nueva


def _modificar(ticker: str, ruta: Path, cambio) -> None:
    entradas = _leer(ruta)
    e = _ultima(entradas, ticker)
    if e is not None:
        cambio(e)
        _escribir(ruta, entradas)


def anotar_reuso(ticker: str, quien: dict[str, str], cuando: datetime, ruta: Path = RUTA) -> None:
    _modificar(ticker, ruta, lambda e: e.setdefault("reusos", []).append({**quien, "cuando": cuando.isoformat()}))


def caducar(ticker: str, motivo: str, cuando: datetime, ruta: Path = RUTA) -> None:
    """El análisis deja de valer antes de los 7 días; queda en el registro con su motivo."""
    _modificar(ticker, ruta, lambda e: e.update(caducada={"motivo": motivo, "cuando": cuando.isoformat()}))


def anotar_seguimiento(ticker: str, seguimiento: dict[str, Any], ruta: Path = RUTA) -> None:
    """Suma un seguimiento al análisis del activo: qué se informó, a quién y cuándo."""
    _modificar(ticker, ruta, lambda e: e.setdefault("seguimientos", []).append(seguimiento))
