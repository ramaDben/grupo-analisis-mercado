"""La noticia de apertura baja por escalones hasta encontrar de qué hablar (spec 2026-10-28).

0. Lo último que publicó la fuente oficial del activo (`oficial.candidatas`).
1. Una nota que nombra al activo, de FXStreet o de Investing.com (`noticias_contexto.candidatas`).
2. Si no hay ninguna, una nota de su sector (`config/noticias_sector.json`), validada en el titular.
3. Si tampoco, el evento central de la semana del calendario que la pieza ya trae, en modo anticipación.

El primero que encuentra algo gana. Cada candidata lleva su `escalon`, y el correo lo rotula: el cliente
tiene que saber si lee una nota oficial, una nota del activo, una del sector o la agenda.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from analista import RAIZ
from analista import noticia as nt
from analista import noticias_contexto as nc
from analista import oficial

RUTA_SECTORES = RAIZ / "config" / "noticias_sector.json"
MAX_CANDIDATAS = 5
SANTIAGO = ZoneInfo("America/Santiago")


def patrones_sector(ticker: str, ruta: Path = RUTA_SECTORES) -> tuple[str, list[re.Pattern[str]]]:
    """El nombre del sector del activo y sus patrones; ("", []) si no tiene sector declarado."""
    try:
        sectores = json.loads(ruta.read_text(encoding="utf-8"))["sectores"]
    except (OSError, ValueError, KeyError):
        return "", []
    for s in sectores.values():
        if ticker in s.get("tickers", []):
            return s["nombre"], [re.compile(p, re.IGNORECASE) for p in s["patrones"]]
    return "", []


def candidatas(ticker: str, nombre: str, ahora: datetime, leer: Callable[[str], str] = nt.leer_feed,
               ruta_patrones: Path = nt.PATRONES_FX,
               ruta_sectores: Path = RUTA_SECTORES,
               oficial_fn: Callable = oficial.candidatas) -> tuple[list[dict[str, Any]], str | None]:
    """Las candidatas del primer escalón con notas (oficial, activo, después sector) y un aviso si algún medio no respondió."""
    cands_oficial: list[dict[str, Any]] = []
    aviso_oficial: str | None = None
    try:
        cands_oficial, aviso_oficial = oficial_fn(ticker, ahora)
    except Exception as exc:
        aviso_oficial = str(exc)

    if cands_oficial:
        return [{**c, "escalon": "oficial"} for c in cands_oficial[:MAX_CANDIDATAS]], aviso_oficial

    propias, avisos = nc.candidatas(ticker, nombre, ahora, leer=leer, ruta_patrones=ruta_patrones)
    todos_avisos: list[str] = []
    if aviso_oficial:
        todos_avisos.append(aviso_oficial)
    todos_avisos.extend(avisos)
    aviso = " ".join(todos_avisos) or None

    if propias:
        return [{**c, "escalon": "activo"} for c in propias[:MAX_CANDIDATAS]], aviso
    sector, patrones = patrones_sector(ticker, ruta_sectores)
    if not patrones:
        return [], aviso
    vistas: dict[str, dict[str, Any]] = {}
    for feeds, medio in ((nt.FEEDS_FX, "FXStreet"), (nc.FEEDS_INVESTING, "Investing.com")):
        lista, _ = nt.candidatas_de_feeds(feeds, medio, ticker, nombre, ahora, leer=leer, patrones=patrones)
        for c in lista:
            vistas.setdefault(c["url"], {**c, "escalon": "sector", "sector": sector})
    orden = sorted(vistas.values(), key=lambda c: c["fecha"], reverse=True)
    return orden[:MAX_CANDIDATAS], aviso


# ── Escalón 3 ──
# Solo un evento fuerte abre el correo: una decisión de tasas del país del activo, o un dato que la mueve
# (inflación, empleo, crecimiento). Una encuesta de confianza no es "lo que mueve al mercado esta semana".
_DECISION = re.compile(r"interest rate decision", re.IGNORECASE)
_DATO_FUERTE = re.compile(r"\b(CPI|PCE|nonfarm|payrolls|GDP|unemployment rate)\b", re.IGNORECASE)
_PAISES = {"USDCLP": ("Chile", "EE.UU."), "EURUSD": ("Zona Euro", "EE.UU."), "GER40.spot": ("Zona Euro", "EE.UU."),
           "COPPER": ("China", "EE.UU.")}


def momento(ev: dict[str, Any]) -> datetime | None:
    m = re.match(r"(\d{1,2}):(\d{2})", str(ev.get("hora", "")))
    try:
        dia = datetime.strptime(str(ev.get("fecha", "")), "%Y-%m-%d")
    except ValueError:
        return None
    return dia.replace(hour=int(m[1]) if m else 23, minute=int(m[2]) if m else 59, tzinfo=SANTIAGO)


def evento_central(eventos: list[dict[str, Any]], ticker: str, ahora: datetime) -> dict[str, Any] | None:
    """El evento que abre el correo cuando no hay notas: la decisión de tasas antes que los datos, y el más próximo."""
    paises = _PAISES.get(ticker, ("EE.UU.",))
    candidatos = []
    for ev in eventos:
        cuando = momento(ev)
        if cuando is None or cuando <= ahora or ev.get("pais") not in paises:
            continue
        nombre = str(ev.get("fuente_nombre", ""))
        if _DECISION.search(nombre):
            rango = 0
        elif _DATO_FUERTE.search(nombre):
            rango = 1
        else:
            continue
        candidatos.append((rango, paises.index(ev["pais"]), cuando, ev))
    if not candidatos:
        return None
    return dict(min(candidatos, key=lambda c: c[:3])[3])


def escalon_de(noticia: dict[str, Any], datos: dict[str, Any]) -> str:
    """De qué escalón es la noticia elegida: lo dice la candidata, no agy. La buscada en la web es del activo."""
    if noticia.get("escalon") in ("agenda", "oficial"):
        return str(noticia["escalon"])
    for c in datos.get("noticias_candidatas") or []:
        if c.get("url") == noticia.get("url"):
            return str(c.get("escalon", "activo"))
    return "activo"
