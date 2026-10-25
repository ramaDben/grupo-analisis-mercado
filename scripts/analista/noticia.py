"""La noticia de apertura del correo de `/oportunidad`: agy la encuentra y la redacta, Python la depura.

Spec 2026-10-24 §1. Lo que no pasa se descarta con su motivo y la pieza sigue (mismo criterio que
`descartar_tesis_rotas`): una noticia rota no puede tirar 7 a 25 minutos de agy ni el cupo cobrado.

Las cifras son la excepción a la Regla 1 y por eso el freno es más duro que el del resto de la
pieza: una cifra solo vale si Python **leyó la nota** y la encontró en su texto. El `extracto` que
trae agy no cuenta, porque lo escribe el mismo agy que escribe el titular, y no hay revisión del
director antes del envío. Con muro de pago (`sin_verificar`) el titular y la bajada van sin cifras
(director, 2026-10-24, opción 1a).
"""
from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from analista import RAIZ
from analista import esquema as es
from analista import fuentes as fu

CAMPOS = ("medio", "fecha", "url", "titular_original", "extracto", "titular", "bajada", "motivo")
VENTANA_DIAS = 3
LARGOS = {"titular": 90, "bajada": 200}
_ETIQUETA = re.compile(r"<(script|style)\b.*?</\1>|<[^>]+>", re.IGNORECASE | re.DOTALL)


def leer_texto(url: str, timeout: int = 10) -> str | None:
    """El texto visible de la nota, sin etiquetas; `None` si no responde."""
    import requests

    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; GI-analistas)"})
    except requests.RequestException:
        return None
    if r.status_code >= 400:
        return None
    return html.unescape(_ETIQUETA.sub(" ", r.text))


def _fecha(n: dict[str, Any]) -> date | None:
    try:
        return datetime.strptime(str(n.get("fecha", "")), "%Y-%m-%d").date()
    except ValueError:
        return None


def vigente(n: dict[str, Any], hoy: date) -> bool:
    """Dentro de la ventana de 3 días. Pasada, la noticia sale igual con su fecha en palabras (opción 2b)."""
    f = _fecha(n)
    return f is not None and 0 <= (hoy - f).days <= VENTANA_DIAS


_ES = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?")
_EN = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")


def _valores(token: str, convenciones: tuple[str, ...]) -> set[float]:
    """Los valores que puede significar una cifra: «4.200» es 4200 en Chile y 4,2 en inglés.

    Comparar dígitos sin la coma daría por buena «4.200 dólares» contra «$42.00 per gram».
    """
    salida = set()
    if "es" in convenciones and _ES.fullmatch(token):
        salida.add(float(token.replace(".", "").replace(",", ".")))
    if "en" in convenciones and _EN.fullmatch(token):
        salida.add(float(token.replace(",", "")))
    return salida


def _cifras_del_texto(texto: str) -> list[str]:
    """Todas las cifras, también las de uno o dos dígitos: «8 %» y «50 puntos base» son las que más importan."""
    return es._NUMERO.findall(texto)


def _cifras_ausentes(citadas: list[str], pagina: str) -> list[str]:
    en_pagina: set[float] = set()
    for t in es._NUMERO.findall(pagina):
        en_pagina |= _valores(t, ("es", "en"))
    return [t for t in citadas if not (_valores(t, ("es",)) & en_pagina)]


def _motivo(n: Any, hoy: date, lista: dict[str, Any], verificar: Callable[[str], str],
            leer: Callable[[str], str | None]) -> str | None:
    """El motivo por el que la noticia no sale; `None` si pasa."""
    if not isinstance(n, dict) or any(not isinstance(n.get(c), str) or not n[c].strip() for c in CAMPOS):
        return f"viene incompleta (campos: {', '.join(CAMPOS)})"
    from analista import ilustracion

    if n["motivo"] not in ilustracion.motivos():
        return f"el motivo de imagen «{n['motivo']}» no está en el catálogo"
    for campo, tope in LARGOS.items():
        if len(n[campo]) > tope:
            return f"el {campo} tiene {len(n[campo])} caracteres y el máximo es {tope}"
    for campo in ("titular", "bajada"):
        errs = es.errores_texto_noticia(f"noticia.{campo}", n[campo])
        if errs:
            return errs[0].split(": ", 1)[-1]
    dominios = lista["medios"].get(n["medio"])
    if dominios is None:
        return f"el medio {n['medio']} no está en la lista"
    if not n["url"].startswith("https://") or not fu._del_dominio(fu._host(n["url"]), dominios):
        return f"la URL no es del dominio de {n['medio']}"
    if not fu._con_ruta_de_articulo(n["url"]):
        return "la URL es una portada y no un artículo"
    f = _fecha(n)
    if f is None:
        return f"la fecha {n['fecha']!r} no es AAAA-MM-DD"
    if not vigente(n, hoy):
        return f"la fecha {n['fecha']} está fuera de la ventana de {VENTANA_DIAS} días"
    estado = verificar(n["url"])
    if estado == "muerta":
        return "la URL no responde"
    citadas = _cifras_del_texto(n["titular"] + " " + n["bajada"])
    if not citadas:
        return None
    texto = leer(n["url"]) if estado == "ok" else None
    if texto is None:
        return "trae cifras y no pude leer la nota para comprobarlas (muro de pago o página ilegible)"
    ausentes = _cifras_ausentes(citadas, texto)
    if ausentes:
        return f"la cifra {', '.join(dict.fromkeys(ausentes))} no aparece en la nota"
    return None


def depurar_noticia(pieza: dict[str, Any], hoy: date, lista: dict[str, Any] | None = None,
                    verificar: Callable[[str], str] = fu.verificar_url,
                    leer: Callable[[str], str | None] = leer_texto) -> tuple[dict[str, Any], list[str]]:
    """Deja `editorial.noticia` válida o en `None`, con el motivo de la caída."""
    editorial = pieza.get("editorial", {})
    if "noticia" not in editorial:
        return pieza, []
    n = editorial["noticia"]
    if n is None or n == es.MARCA:
        editorial["noticia"] = None
        return pieza, []
    lista = lista or fu.cargar_lista()
    motivo = _motivo(n, hoy, lista, fu._con_lista(verificar, lista), leer)
    if motivo:
        editorial["noticia"] = None
        return pieza, [f"Noticia de apertura: {motivo}"]
    editorial["noticia"] = {c: n[c].strip() for c in CAMPOS}
    return pieza, []


# ── Candidatas de FXStreet (director, 2026-10-25) ──
# La búsqueda web de agy volvió vacía un domingo: la noticia no puede depender de ella. Python lee el RSS
# en español y sella las notas del activo en `datos.noticias_candidatas`; agy elige una y la redacta, y la
# depuración de arriba la valida igual que a cualquier otra. `es.fxstreet.com` responde 403: va `www.fxstreet.es`.

FEEDS_FX = ("https://www.fxstreet.es/rss/news", "https://www.fxstreet.es/rss/analysis")
PATRONES_FX = RAIZ / "config" / "noticias_fxstreet.json"
MAX_CANDIDATAS = 5
SANTIAGO = ZoneInfo("America/Santiago")


def leer_feed(url: str, timeout: int = 15) -> str:
    import requests

    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (compatible; GI-analistas)"})
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text


def _items(xml: str) -> list[dict[str, Any]]:
    """Título, link y fecha de cada nota; un feed que no es RSS (una página de bloqueo) no trae ninguna."""
    try:
        canal = ET.fromstring(xml.strip().encode("utf-8"))
    except ET.ParseError:
        return []
    salida = []
    for it in canal.iter("item"):
        titulo, link, pub = (it.findtext(k) or "" for k in ("title", "link", "pubDate"))
        try:
            momento = parsedate_to_datetime(pub)
        except (TypeError, ValueError):
            continue
        if titulo.strip() and link.strip().startswith("https://") and momento.tzinfo is not None:
            salida.append({"titulo": titulo.strip(), "url": link.strip(), "momento": momento})
    return salida


def _patrones(ticker: str, nombre: str, ruta: Path) -> list[re.Pattern[str]]:
    try:
        propios = json.loads(ruta.read_text(encoding="utf-8"))["patrones"].get(ticker)
    except (OSError, ValueError, KeyError):
        propios = None
    return [re.compile(p, re.IGNORECASE) for p in (propios or [rf"\b{re.escape(nombre)}\b"])]


def candidatas_fxstreet(ticker: str, nombre: str, ahora: datetime, leer: Callable[[str], str] = leer_feed,
                        ruta_patrones: Path = PATRONES_FX) -> tuple[list[dict[str, Any]], str | None]:
    """Las notas del activo de los últimos 3 días, la más reciente primero, y un aviso si FXStreet no respondió.

    Sin la descripción del RSS: trae precios y porcentajes en notación inglesa, y agy abre la nota igual.
    """
    patrones = _patrones(ticker, nombre, ruta_patrones)
    hoy = ahora.astimezone(SANTIAGO).date()
    vistas: dict[str, dict[str, Any]] = {}
    caidos = 0
    for feed in FEEDS_FX:
        try:
            items = _items(leer(feed))
        except Exception:  # noqa: BLE001  un feed caído no bota la pieza: agy busca en la web
            caidos += 1
            continue
        for it in items:
            fecha = it["momento"].astimezone(SANTIAGO).date()
            if 0 <= (hoy - fecha).days <= VENTANA_DIAS and any(p.search(it["titulo"]) for p in patrones):
                vistas.setdefault(it["url"], {**it, "fecha": fecha})
    orden = sorted(vistas.values(), key=lambda it: it["momento"], reverse=True)[:MAX_CANDIDATAS]
    lista = [{"medio": "FXStreet", "fecha": it["fecha"].isoformat(), "url": it["url"],
              "titular_original": it["titulo"]} for it in orden]
    aviso = ("No pude leer FXStreet: agy buscó la noticia de apertura en la web." if caidos == len(FEEDS_FX)
             else None)
    return lista, aviso
