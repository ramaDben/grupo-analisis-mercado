"""La única llamada a agy del bot: redactar los textos de una pieza ya preparada.

El prompt es fijo y solo lleva la ruta de la pieza. Nada de lo que el analista
escribió en Telegram llega acá.
"""
from __future__ import annotations

from pathlib import Path

from analista import RAIZ

DIR_PEDIDOS = RAIZ / "data" / "informes_analistas"

# Un encargo real de agy tarda de 5 a 7 minutos (medido el 2026-09-06). Con búsqueda web de 3 a 5
# fuentes medimos 424 s y 652 s el 2026-10-16; el techo deja el doble más la validación. Los hechos
# del día no suman búsquedas: los mide Python (spec 2026-10-17 §8).
TIMEOUT = "25m"
# El segundo intento solo busca fuentes de bancos (spec 2026-10-17 §5).
TIMEOUT_REINTENTO = "15m"


class RutaFueraDePedidos(ValueError):
    pass


def escribir_textos(ruta_pieza: Path, tier: str = "flash", timeout: str = TIMEOUT):
    """Lanza `/analista <ruta>` y devuelve el `Resultado` de `agy_encargo`."""
    from agy_encargo import invocar

    ruta = Path(ruta_pieza).resolve()
    if DIR_PEDIDOS.resolve() not in ruta.parents or ruta.name != "pieza.json":
        raise RutaFueraDePedidos(f"{ruta} no es una pieza de data/informes_analistas/")
    relativa = ruta.relative_to(RAIZ.resolve()).as_posix()
    return invocar(f"/analista {relativa}", tier, timeout)
