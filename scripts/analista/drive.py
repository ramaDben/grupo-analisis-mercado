"""Drive ordenado por sector, activo y fecha: GI Informes/<Sector>/<Nombre (TICKER)>/<AAAA-MM-DD>."""
from __future__ import annotations

import re
import shutil
from datetime import date
from pathlib import Path

from analista import segmentos

SECTORES = {"fx": "Divisas", "commodities": "Commodities", "indices": "Índices",
            "acciones": "Acciones", "etfs": "ETF", "cripto": "Cripto"}
OTROS = "Otros"
_PROHIBIDOS = re.compile(r'[<>:"/\|?*]')


def _limpio(texto: str) -> str:
    return _PROHIBIDOS.sub("", texto).strip()


def _sector(ticker: str) -> str:
    try:
        resuelto = segmentos.segmento_y_ancla(ticker)
    except Exception:  # noqa: BLE001  sin catálogo legible el archivo igual se guarda
        resuelto = None
    return SECTORES.get(resuelto[0], OTROS) if resuelto else OTROS


def carpeta(raiz: Path, ticker: str, nombre: str, dia: date) -> Path:
    return Path(raiz) / "GI Informes" / _sector(ticker) / f"{_limpio(nombre)} ({_limpio(ticker)})" / dia.isoformat()


def copiar(rutas: list[tuple[Path, str]], destino: Path) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    for origen, nombre in rutas:
        tamano = Path(origen).stat().st_size
        base, sufijo = Path(nombre).stem, Path(nombre).suffix
        meta, n = destino / nombre, 1
        while meta.exists():
            if meta.stat().st_size == tamano:
                break
            n += 1
            meta = destino / f"{base}_{n}{sufijo}"
        else:
            shutil.copy2(origen, meta)
