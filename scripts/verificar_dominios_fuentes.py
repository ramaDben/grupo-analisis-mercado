"""Verifica que cada dominio (y cada ruta propia) declarado en los segmentos y en los anclas responda.

punto-de-entrada: CLI de red que corre el director a mano al editar los segmentos; no lo llama nada

Uso: `uv run python scripts/verificar_dominios_fuentes.py`. Hace red, por eso no corre en la suite.
Clasifica cada dominio: `ok`, `sin_verificar` (401/403/429/timeout: muro o bloqueo a bots) o `muerta`
(error de conexion o 4xx/5xx). Sale con codigo 1 si alguno esta muerto.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from analista import fuentes  # noqa: E402
from analista.segmentos import ACTIVOS, _entradas  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (compatible; GI-analistas)"}


def dominios_declarados() -> set[str]:
    cfg = fuentes.cargar_segmentos()
    dominios: set[str] = set()
    for seg in cfg.values():
        if not isinstance(seg, dict):
            continue
        for ds in (seg.get("medios") or {}).values():
            dominios.update(ds)
        for divisa in (seg.get("divisas") or {}).values():
            dominios.update(divisa.get("dominios", []))
    try:
        catalogo = json.loads(ACTIVOS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        catalogo = {}
    for entry in _entradas(catalogo):
        ancla = entry.get("ancla")
        if isinstance(ancla, dict):
            dominios.update(ancla.get("dominios", []))
            dominios.update(ancla.get("rutas_propias", []))  # host/ruta: se prueba igual
    return dominios


def verificar_dominio(dominio: str, timeout: int = 10) -> str:
    """Estado del dominio; si el apex no responde se prueba con `www.` (varios sitios oficiales solo viven ahi)."""
    estado = _estado_de(dominio, timeout)
    if estado == "muerta" and not dominio.startswith("www."):
        estado = _estado_de(f"www.{dominio}", timeout)
    return estado


def _estado_de(dominio: str, timeout: int) -> str:
    import requests

    try:
        r = requests.get(f"https://{dominio}", timeout=timeout, allow_redirects=True, stream=True, headers=UA)
        r.close()
    except requests.Timeout:
        return "sin_verificar"
    except requests.RequestException:
        return "muerta"
    if r.status_code in (401, 403, 429):
        return "sin_verificar"
    return "muerta" if r.status_code >= 400 else "ok"


def main() -> int:
    muertas = 0
    for d in sorted(dominios_declarados()):
        estado = verificar_dominio(d)
        muertas += estado == "muerta"
        print(f"{estado:14} {d}")
    print(f"{muertas} muerta(s)")
    return 1 if muertas else 0


if __name__ == "__main__":
    raise SystemExit(main())
