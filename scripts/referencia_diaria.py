"""La referencia intradía por día: el plan 1H que fija el día (espejo de referencia_semanal).

Estructura en disco: `data/referencias_diarias/<AAAA-MM-DD>/<ticker>.json` (fecha en America/Santiago).
Semántica: la primera lectura 1H del día se guarda y las siguientes del mismo día la reutilizan,
para que el plan de hoy no cambie en cada /seguimiento.
Caducidad: caduca al cambiar el día calendario en America/Santiago (otra ruta) o si corresponde
reemplazarla por ruptura por cierre o cambio de estructura (misma regla que la semanal:
`debe_reemplazar`).
Mercado cerrado: si el mercado no cotiza (`velas_mt5` no entrega vela en curso),
no se inventa referencia: devuelve None y el llamador lo informa.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from estrategia.contrato import SCL, Lectura, Marcos, VelaEnCurso, lectura_a_dict, lectura_de_dict
from referencia_semanal import debe_reemplazar, slug

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "data" / "referencias_diarias"
EXTRA = 60
Lector = Callable[[str, Marcos, int], tuple[dict[str, pd.DataFrame], VelaEnCurso | None]]


def fecha_de(ahora: datetime) -> str:
    """El día calendario en America/Santiago (AAAA-MM-DD)."""
    if ahora.tzinfo is None:
        ahora = ahora.replace(tzinfo=SCL)
    return ahora.astimezone(SCL).date().isoformat()


def ruta(fecha: str, ticker: str, base: Path = DIR) -> Path:
    """Ruta en disco para la referencia diaria de un activo."""
    return base / fecha / f"{slug(ticker)}.json"


def guardar(fecha: str, ticker: str, lectura: Lectura, base: Path = DIR, motivo: str = "diaria",
            ahora: datetime | None = None) -> Path:
    """Guarda la referencia diaria en disco en formato JSON."""
    if lectura.estado == "PRUEBA":
        raise ValueError(f"{lectura.ticker}: una referencia no se guarda en PRUEBA; se lee con en_curso=None")
    if ahora is None:
        ahora = datetime.now(SCL)
    elif ahora.tzinfo is None:
        ahora = ahora.replace(tzinfo=SCL)

    destino = ruta(fecha, ticker, base)
    destino.parent.mkdir(parents=True, exist_ok=True)
    datos = {
        "ticker": ticker,
        "fecha": fecha,
        "motivo": motivo,
        "guardada": ahora.astimezone(SCL).isoformat(timespec="minutes"),
        "lectura": lectura_a_dict(lectura),
    }
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def cargar(fecha: str, ticker: str, base: Path = DIR) -> Lectura | None:
    """Carga la referencia diaria si existe; de lo contrario devuelve None."""
    origen = ruta(fecha, ticker, base)
    if not origen.exists():
        return None
    datos = json.loads(origen.read_text(encoding="utf-8"))
    return lectura_de_dict(datos["lectura"])


def referencia_del_dia(
    estrategia: Any,
    ticker: str,
    digits: int,
    ahora: datetime,
    lector: Lector | None = None,
    base: Path = DIR,
    velas: dict[str, pd.DataFrame] | None = None,
    en_curso: VelaEnCurso | None = None,
) -> Lectura | None:
    """Obtiene la referencia intradía de hoy, creándola si es la primera vez o reutilizándola.

    Si el mercado no cotiza (sin vela en curso), devuelve None sin inventar referencia.
    Si ya existía una referencia para hoy, se evalúa contra las velas actuales: si hubo ruptura
    por cierre o cambio de estructura (`debe_reemplazar`), se actualiza la referencia guardada.
    """
    if ahora.tzinfo is None:
        ahora = ahora.replace(tzinfo=SCL)
    fec = fecha_de(ahora)
    guardada = cargar(fec, ticker, base=base)

    if velas is None:
        if lector is not None:
            velas, en_curso = lector(ticker, estrategia.marcos, EXTRA)
        else:
            from estrategia.fuente import velas_mt5
            velas, en_curso = velas_mt5(ticker, estrategia.marcos, EXTRA)

    if guardada is None:
        # Primera consulta del día: sin vela en curso el mercado no cotiza (`velas_mt5` la entrega
        # solo si cotiza), y fijar el plan de hoy sobre el cierre de ayer sería inventarlo.
        if en_curso is None:
            return None
        nueva = estrategia.leer(ticker, velas, digits, en_curso=None)
        guardar(fec, ticker, nueva, base=base, motivo="primera_del_dia", ahora=ahora)
        return nueva

    # Reutilización / seguimiento de la referencia existente del día
    try:
        actual = estrategia.seguir(guardada, velas, digits, en_curso)
    except ValueError:
        nueva = estrategia.leer(ticker, velas, digits, en_curso=None)
        guardar(fec, ticker, nueva, base=base, motivo="reemplazo_error_seguir", ahora=ahora)
        return nueva

    if debe_reemplazar(guardada, actual):
        nueva = estrategia.leer(ticker, velas, digits, en_curso=None)
        guardar(fec, ticker, nueva, base=base, motivo="reemplazo_ruptura_o_estructura", ahora=ahora)
        return nueva

    return guardada

