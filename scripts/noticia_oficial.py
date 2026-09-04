#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""La noticia de fuente oficial que puede suplementar a un canal vacío.

**Lo que este módulo hace de verdad es descartar.** Bajar un feed es trivial; lo
que decide si esto sirve o estorba es el filtro, y la medición del 2026-09-03 lo
dejó claro: ese día la EIA publicó *"Weekly average load in ERCOT continues near
record high"*. Carga eléctrica en Texas. Oficial, fresca, y sin ninguna relación
con el petróleo. Un filtro de frescura sin filtro de relevancia la habría mandado
al canal de metales y energía justo el día en que ese canal quedó vacío.

**Las fuentes oficiales son autorizadas pero escasas.** Medido sobre el último
mes: la EIA publica unas 3 notas por semana y solo 3 de 12 tocaban el crudo; el
BCE publica unas 4 por semana, casi todas discursos de su directorio; la Fed
saca 2 piezas de política monetaria al mes y el resto de su feed son sanciones y
aprobaciones bancarias, que no le importan a nadie acá. Sumadas, el flujo
relevante es de una nota cada dos o tres días. **Esto no cubre el canal todos los
días, y no pretende hacerlo**: el piso confiable sigue siendo el suplemento de
estado más concepto de `suplemento_canal`. Esta pieza es estrictamente aditiva.

Tres fuentes más quedaron fuera porque no se pueden leer: el Tesoro de EE.UU.
responde 404, y la BLS y la OPEP responden 403 al bot. El Banco Central de Chile
devuelve HTML en la ruta de su RSS.

**Lo que NO hace:** no toma cifras de la noticia. Los precios y niveles salen del
terminal (regla 1), siempre. Y no traduce: el titular en español es un campo
editorial que escribe el comando al rendir, con el mismo contrato que el resto
del pipeline, porque `--preparar` es Python puro y no tiene modelo que traduzca.
"""

from __future__ import annotations

import email.utils
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

RAIZ = Path(__file__).resolve().parent.parent

# Tres días. Con la fecha a la vista, "lo último que publicó la fuente oficial"
# sigue siendo honesto a 48 o 72 horas; a una semana ya no es noticia y decirlo
# igual gasta la credibilidad que la fuente oficial venía a aportar.
VENTANA_FRESCURA_HORAS = 72

_UA = "Mozilla/5.0 (compatible; GrupoInteligencia/1.0)"

# ─────────────────────────────────────────────────────────────────────────────
# A qué canal va cada activo
# ─────────────────────────────────────────────────────────────────────────────
# Los canales de las fuentes se DERIVAN de acá, no se escriben aparte. Dos
# listas del mismo hecho es el defecto recurrente del repo: a la segunda copia
# una queda atrás y nadie se entera hasta que sale una pieza al canal equivocado.
CANAL_DE_ACTIVO: dict[str, str] = {
    "WTI": "03_commodities_materias_primas",
    "BRENT": "03_commodities_materias_primas",
    "XAUUSD": "03_commodities_materias_primas",
    "EURUSD": "02_forex_divisas",
    "USDCLP": "02_forex_divisas",
    "US100": "04_indices_bursatiles",
}

# ─────────────────────────────────────────────────────────────────────────────
# El vocabulario que decide la relevancia
# ─────────────────────────────────────────────────────────────────────────────
# Se busca en el TITULAR y no en el cuerpo. La descripción de casi cualquier
# nota trae una línea de contexto donde cabe la palabra "oil" o "inflation", y
# buscar ahí deja pasar todo: el filtro se vuelve decorativo.
#
# En los bancos centrales la relevancia la da **quién habla**, no un commodity.
# Un discurso de Lagarde mueve el euro aunque el titular no diga "euro".
VOCABULARIO: dict[str, tuple[str, ...]] = {
    "WTI": (
        "crude oil", "petroleum", "wti", "opec", "oil production", "oil demand",
        "oil price", "refinery", "refineries", "gasoline", "distillate",
    ),
    "BRENT": (
        "crude oil", "petroleum", "brent", "opec", "oil production", "oil demand",
        "oil price", "refinery", "refineries",
    ),
    "XAUUSD": (
        "fomc", "federal open market", "monetary policy", "interest rate",
        "powell", "gold",
    ),
    "EURUSD": (
        "lagarde", "schnabel", "cipollone", "philip r. lane", "euro area",
        "monetary policy", "governing council", "euro short-term rate",
    ),
    "USDCLP": (
        "fomc", "federal open market", "monetary policy", "interest rate",
        "powell", "waller", "dollar",
    ),
    "US100": (
        "fomc", "federal open market", "monetary policy", "interest rate",
        "powell",
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Las fuentes que responden
# ─────────────────────────────────────────────────────────────────────────────
_FUENTES_BASE: dict[str, dict[str, Any]] = {
    "eia": {
        "organismo": "EIA (agencia de energía de Estados Unidos)",
        "url": "https://www.eia.gov/rss/todayinenergy.xml",
        "activos": ("WTI", "BRENT"),
    },
    "bce": {
        "organismo": "BCE (Banco Central Europeo)",
        "url": "https://www.ecb.europa.eu/rss/press.html",
        "activos": ("EURUSD",),
    },
    "fed": {
        # El feed general de la Fed trae sanciones y aprobaciones bancarias, que
        # no le sirven a nadie acá. Este es el de política monetaria.
        "organismo": "Fed (Reserva Federal de Estados Unidos)",
        "url": "https://www.federalreserve.gov/feeds/press_monetary.xml",
        "activos": ("USDCLP", "US100", "XAUUSD"),
    },
}

FUENTES: dict[str, dict[str, Any]] = {
    nombre: {**datos, "canales": sorted({
        CANAL_DE_ACTIVO[a] for a in datos["activos"]
    })}
    for nombre, datos in _FUENTES_BASE.items()
}

_MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


# ─────────────────────────────────────────────────────────────────────────────
# Leer
# ─────────────────────────────────────────────────────────────────────────────
def descargar(url: str, timeout: int = 20) -> str:
    """Baja un feed. Se inyecta en los tests: la suite nunca toca la red."""
    pedido = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(pedido, timeout=timeout) as r:  # noqa: S310
        return r.read().decode("utf-8", errors="replace")


def descargar_con_cache(
    bajar: Callable[[str], str] = descargar
) -> Callable[[str], str]:
    """Un descargador que baja cada feed una sola vez por corrida.

    Sin esto el prepare se vuelve lento de forma tonta: el feed de la Fed sirve
    a divisas y a índices, así que se bajaría dos veces, y cada canal vacío
    repite las consultas de su fuente. Un timeout de red multiplicado por cinco
    canales bloquea la tanda entera.
    """
    memo: dict[str, str] = {}

    def _bajar(url: str) -> str:
        if url not in memo:
            memo[url] = bajar(url)
        return memo[url]

    return _bajar


def parsear_feed(xml: str) -> list[dict[str, Any]]:
    """Los items de un RSS, con fecha ya convertida a `datetime` con zona.

    Un feed ilegible devuelve lista vacía y no lanza: una fuente caída no puede
    voltear la tanda entera.
    """
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError:
        return []

    items: list[dict[str, Any]] = []
    for it in raiz.findall(".//item"):
        titulo = (it.findtext("title") or "").strip()
        url = (it.findtext("link") or "").strip()
        crudo = (it.findtext("pubDate") or "").strip()
        if not titulo or not url:
            continue
        try:
            # `parsedate_to_datetime` tolera el doble espacio que trae el feed
            # real de la EIA (`Mon, 24 Aug 2026  09:00:00 EST`) y traduce las
            # zonas obsoletas tipo EST al offset que les corresponde.
            fecha = email.utils.parsedate_to_datetime(crudo)
        except (TypeError, ValueError):
            continue
        if fecha is None or fecha.tzinfo is None:
            continue
        items.append({
            "titulo": titulo,
            "url": url,
            "fecha": fecha,
            "resumen": " ".join((it.findtext("description") or "").split()),
        })
    return items


# ─────────────────────────────────────────────────────────────────────────────
# Descartar
# ─────────────────────────────────────────────────────────────────────────────
def activos_del_titular(titulo: str) -> list[str]:
    """Los activos que el titular menciona, según el vocabulario.

    Vacío significa *no publicable*, y ese es el caso normal: la mayoría de lo
    que publica un organismo oficial no toca ningún activo que cubramos.
    """
    texto = (titulo or "").lower()
    return sorted(
        activo for activo, terminos in VOCABULARIO.items()
        if any(t in texto for t in terminos)
    )


def es_fresca(
    fecha: datetime, ahora: datetime, horas: int = VENTANA_FRESCURA_HORAS
) -> bool:
    """¿Se publicó dentro de la ventana? Una nota vieja no es noticia."""
    return timedelta(0) <= (ahora - fecha) <= timedelta(hours=horas)


def ya_publicada(url: str, historial: list[dict[str, Any]] | None) -> bool:
    """¿Ya mandamos esta nota?

    **El URL no tiene ventana, a diferencia de los conceptos.** Que un concepto
    vuelva a las dos semanas es refuerzo; que vuelva la misma noticia es un
    error visible desde afuera.
    """
    for entrada in historial or []:
        if entrada.get("tipo") == "noticia" and entrada.get("clave") == url:
            return True
    return False


def noticia_para_canal(
    canal: str,
    ahora: datetime,
    historial: list[dict[str, Any]] | None = None,
    descargar: Callable[[str], str] = descargar,
) -> dict[str, Any] | None:
    """La nota oficial más reciente que sirve a este canal, o `None`.

    `None` es el resultado esperado la mayoría de las veces, y no es una falla:
    el canal se queda con el suplemento de estado, que siempre funciona.
    """
    candidatas: list[dict[str, Any]] = []

    for nombre, fuente in FUENTES.items():
        if canal not in fuente["canales"]:
            continue
        # Los activos de ESTA fuente que además pertenecen a ESTE canal. Sin este
        # cruce, la Fed le mandaría al canal de índices una nota que solo mapea
        # al oro.
        del_canal = {
            a for a in fuente["activos"] if CANAL_DE_ACTIVO.get(a) == canal
        }
        if not del_canal:
            continue
        try:
            items = parsear_feed(descargar(fuente["url"]))
        except Exception:  # noqa: BLE001  (red caída, DNS, 403, timeout)
            continue

        for it in items:
            if not es_fresca(it["fecha"], ahora):
                continue
            tocados = del_canal.intersection(activos_del_titular(it["titulo"]))
            if not tocados:
                continue
            if ya_publicada(it["url"], historial):
                continue
            candidatas.append({
                **it,
                "fuente": nombre,
                "organismo": fuente["organismo"],
                "canal": canal,
                "activos": sorted(tocados),
            })

    if not candidatas:
        return None
    candidatas.sort(key=lambda c: c["fecha"], reverse=True)
    return candidatas[0]


# ─────────────────────────────────────────────────────────────────────────────
# El bloque de texto
# ─────────────────────────────────────────────────────────────────────────────
def _cuando(fecha: datetime, hoy: date | None = None) -> str:
    """La fecha en voz de cliente, siempre visible.

    Que la fecha se vea es lo que hace honesto publicar algo de anteayer.
    """
    dia = fecha.date()
    referencia = hoy or date.today()
    if dia == referencia:
        return "hoy"
    if (referencia - dia).days == 1:
        return "ayer"
    return f"el {dia.day} de {_MESES[dia.month - 1]}"


def bloque_noticia(
    noticia: dict[str, Any], titular_es: str, hoy: date | None = None
) -> str:
    """El bloque de WhatsApp de la noticia, con el titular ya traducido.

    `titular_es` es un **campo editorial**: lo escribe el comando al rendir,
    porque `--preparar` es Python puro. Vacío detiene la pieza, con el mismo
    criterio que el resto del pipeline: una pieza a medias que sale sin avisar
    llega al cliente.
    """
    if not (titular_es or "").strip():
        raise ValueError(
            "el titular en español está vacío: el bloque de noticia no se arma "
            "sin él (lo escribe el comando al rendir)"
        )

    cuando = _cuando(noticia["fecha"], hoy)
    return "\n".join([
        "📰 *LO ÚLTIMO DE LA FUENTE OFICIAL*",
        "━━━━━━━━━━━━━━━━━━━",
        f"La {noticia['organismo']} publicó {cuando}:",
        f"*{titular_es.strip()}*",
        "Es contexto de fondo para entender el activo, no una señal de entrada. "
        "Los niveles siguen saliendo del terminal.",
        f"🔗 {noticia['url']}",
    ])


def registrar_noticia(
    noticia: dict[str, Any] | None,
    hoy: date | None = None,
    ruta: Path | None = None,
) -> None:
    """Anota el URL publicado para no repetirlo nunca.

    Comparte archivo con los conceptos (`data/historial_suplementos.json`), que
    es historia editorial de lo que el cliente ya leyó y por eso se versiona.
    """
    if not noticia:
        return
    from suplemento_canal import HISTORIAL, cargar_historial

    import json

    p = ruta or HISTORIAL
    historial = cargar_historial(p)
    historial.append({
        "fecha": (hoy or date.today()).isoformat(),
        "canal": noticia["canal"],
        "tipo": "noticia",
        "clave": noticia["url"],
        "fuente": noticia["fuente"],
    })
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(historial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
