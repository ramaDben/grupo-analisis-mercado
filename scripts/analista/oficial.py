"""Resolutor de fuentes oficiales por activo (spec 2026-10-28, Task 1).

Para cada activo resuelve si tiene fuente oficial propia (escalón 0):
- Acciones de EE.UU.: vía SEC EDGAR 8-K, si su ancla en el catálogo declara CIK.
- Materias primas y divisas: vía feeds oficiales declarados en noticia_oficial.FUENTES.
- El piso entrega el organismo y la URL oficial de prensa si existe la fuente.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

import noticia_oficial
from analista import edgar, segmentos

VENTANA_OFICIAL_DIAS: int = 45


def fuente_de(ticker: str) -> dict[str, Any] | None:
    """Resuelve la fuente oficial de un activo.

    Devuelve un diccionario con claves:
        - organismo: str
        - pagina_prensa: str
        - lector: Literal["edgar_8k", "feed_oficial"]
        - cik: str (si lector == "edgar_8k") o fuente: str (si lector == "feed_oficial")
    O None si el activo no tiene fuente oficial declarada.
    """
    t_norm = ticker.removesuffix(".spot")

    # 1. Acciones del catálogo con ancla y CIK
    resuelto = segmentos.segmento_y_ancla(ticker) or segmentos.segmento_y_ancla(t_norm)
    if resuelto is not None:
        _, ancla = resuelto
        if isinstance(ancla, dict) and ancla.get("cik"):
            return {
                "organismo": ancla["nombre"],
                "pagina_prensa": ancla["sitio_ir"],
                "lector": "edgar_8k",
                "cik": ancla["cik"],
            }

    # 2. Feeds oficiales (EIA, BCE, Fed)
    for nombre_fuente, datos in noticia_oficial.FUENTES.items():
        if t_norm in datos.get("activos", ()):
            return {
                "organismo": datos["organismo"],
                "pagina_prensa": datos["pagina_prensa"],
                "lector": "feed_oficial",
                "fuente": nombre_fuente,
            }

    return None


def piso(ticker: str) -> dict[str, str] | None:
    """Devuelve organismo y página de prensa de la fuente oficial, o None si no tiene."""
    f = fuente_de(ticker)
    if f is None:
        return None
    return {
        "organismo": f["organismo"],
        "pagina_prensa": f["pagina_prensa"],
    }


def candidatas(
    ticker: str,
    ahora: datetime,
    descargar: Callable[[str], str] | None = None,
) -> tuple[list[dict], str | None]:
    """Obtiene noticias candidatas de fuentes oficiales (EDGAR 8-K o feeds de BC/EIA)."""
    f = fuente_de(ticker)
    if f is None:
        return [], None

    lector = f.get("lector")
    if lector == "edgar_8k":
        return edgar.candidatas_8k(
            cik=f["cik"],
            organismo=f["organismo"],
            ahora=ahora,
            descargar=descargar,
            ventana_dias=VENTANA_OFICIAL_DIAS,
        )

    if lector == "feed_oficial":
        fn_descargar = noticia_oficial.descargar_con_cache(
            descargar or noticia_oficial.descargar
        )
        url_feed = noticia_oficial.FUENTES[f["fuente"]]["url"]
        try:
            xml = fn_descargar(url_feed)
        except Exception as exc:
            return [], f"Error consultando feed {f['fuente']}: {exc}"

        items = noticia_oficial.parsear_feed(xml)
        candidatas_lista: list[dict] = []
        clave_del_activo = ticker.removesuffix(".spot")

        for item in items:
            relevante = clave_del_activo in noticia_oficial.activos_del_titular(item["titulo"])
            ahora_cmp = ahora if ahora.tzinfo else ahora.replace(tzinfo=item["fecha"].tzinfo)
            fresca = noticia_oficial.es_fresca(
                item["fecha"],
                ahora_cmp,
                VENTANA_OFICIAL_DIAS * 24,
            )
            if relevante and fresca:
                medio = {"eia": "EIA", "bce": "BCE", "fed": "Fed"}.get(
                    f["fuente"], f["fuente"].upper()
                )
                candidata = {
                    "medio": medio,
                    "fecha": item["fecha"].strftime("%Y-%m-%d"),
                    "url": item["url"],
                    "titular_original": item["titulo"],
                    "escalon": "oficial",
                    "organismo": f["organismo"],
                }
                candidatas_lista.append(candidata)

        candidatas_lista.sort(key=lambda c: c["fecha"], reverse=True)
        return candidatas_lista, None

    return [], None

