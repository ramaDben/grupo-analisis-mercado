"""La única llamada a agy del bot: redactar los textos de una pieza ya preparada.

El prompt es fijo y solo lleva la ruta de la pieza. Nada de lo que el analista
escribió en Telegram llega acá.
"""
from __future__ import annotations

from pathlib import Path

from analista import RAIZ

DIR_PEDIDOS = RAIZ / "data" / "informes_analistas"

# Un encargo real de agy tarda de 5 a 7 minutos (medido el 2026-09-06). Redactar
# una pieza es menos trabajo, pero el techo deja margen para la validación.
TIMEOUT = "12m"


class RutaFueraDePedidos(ValueError):
    pass


def escribir_textos(ruta_pieza: Path, tier: str = "flash"):
    """Lanza `/analista <ruta>` y devuelve el `Resultado` de `agy_encargo`."""
    from agy_encargo import invocar

    ruta = Path(ruta_pieza).resolve()
    if DIR_PEDIDOS.resolve() not in ruta.parents or ruta.name != "pieza.json":
        raise RutaFueraDePedidos(f"{ruta} no es una pieza de data/informes_analistas/")
    relativa = ruta.relative_to(RAIZ.resolve()).as_posix()
    return invocar(f"/analista {relativa}", tier, TIMEOUT)
