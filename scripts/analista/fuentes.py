"""Las voces de bancos y prensa que agy cita: Python valida, agy solo las encuentra.

agy busca en la web (spec 2026-10-16 §7) y escribe `editorial.fuentes[]`. Nada de lo que trae se
cree: la entidad tiene que estar en `config/fuentes_prestigio.json`, el dominio de la URL tiene
que ser el del medio, la fecha tiene que ser fresca y la URL tiene que responder. Lo que no pasa
se descarta con su motivo; ninguna fuente se inventa ni se rellena.

La discrepancia con nuestra lectura la calcula Python con la `postura`, no la declara agy: un
modelo tiende a alinearse con el titular que encontró.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from analista import RAIZ

CONFIG = RAIZ / "config" / "fuentes_prestigio.json"
CAMPOS = ("entidad", "medio", "fecha", "url", "postura", "tesis")
POSTURAS = ("alcista", "bajista", "neutral")
TESIS_MAX = 260
_MARCADO = re.compile(r"[<>]")


def cargar_lista(ruta: Path = CONFIG) -> dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def _entidades(lista: dict[str, Any]) -> set[str]:
    return {e for grupo in lista["entidades"].values() for e in grupo}


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _del_dominio(host: str, dominios: list[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in dominios)


def _con_ruta_de_articulo(url: str) -> bool:
    ruta = urlparse(url).path.strip("/")
    return bool(ruta) and ruta.lower() not in {"index", "index.html", "index.php"}


def verificar_url(url: str, timeout: int = 10) -> str:
    """`ok`, `sin_verificar` (muro de pago o bloqueo a bots) o `muerta` (404 o dominio caído)."""
    import requests

    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True, stream=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; GI-analistas)"})
        r.close()
    except requests.Timeout:
        return "sin_verificar"
    except requests.RequestException:
        return "muerta"
    if r.status_code in (401, 403, 429):
        return "sin_verificar"
    return "ok" if r.status_code < 400 else "muerta"


def _motivo_de_descarte(f: Any, hoy: date, lista: dict[str, Any], verificar: Callable[[str], str]
                        ) -> tuple[str | None, str]:
    """(motivo, verificacion). Motivo None = la fuente pasa."""
    if not isinstance(f, dict) or any(not isinstance(f.get(c), str) or not f[c].strip() for c in CAMPOS):
        return "una fuente viene incompleta", ""
    nombre = f["entidad"]
    if any(_MARCADO.search(f[c]) for c in CAMPOS):
        return f"{nombre}: trae marcado en sus campos", ""
    if nombre not in _entidades(lista):
        return f"{nombre}: la entidad no está en la lista de fuentes de prestigio", ""
    if f["postura"] not in POSTURAS:
        return f"{nombre}: la postura «{f['postura']}» no es alcista, bajista ni neutral", ""
    if len(f["tesis"]) > TESIS_MAX:
        return f"{nombre}: la tesis es demasiado larga", ""
    dominios = lista["medios"].get(f["medio"])
    if dominios is None:
        return f"{nombre}: el medio {f['medio']} no está en la lista", ""
    if not f["url"].startswith("https://"):
        return f"{nombre}: la URL no es https", ""
    if not _del_dominio(_host(f["url"]), dominios):
        return f"{nombre}: el dominio de la URL no es el de {f['medio']}", ""
    if not _con_ruta_de_articulo(f["url"]):
        return f"{nombre}: la URL es una portada y no un artículo", ""
    try:
        dias = (hoy - datetime.strptime(f["fecha"], "%Y-%m-%d").date()).days
    except ValueError:
        return f"{nombre}: la fecha {f['fecha']!r} no es AAAA-MM-DD", ""
    if dias < 0 or dias > int(lista.get("frescura_dias", 14)):
        return f"{nombre}: la fecha {f['fecha']} está fuera de la ventana de {lista.get('frescura_dias', 14)} días", ""
    estado = verificar(f["url"])
    if estado == "muerta":
        return f"{nombre}: la URL no responde", ""
    return None, estado


def depurar(crudas: Any, hoy: date, lista: dict[str, Any] | None = None,
            verificar: Callable[[str], str] = verificar_url) -> tuple[list[dict[str, Any]], list[str]]:
    """Las fuentes que pasan (con su `verificacion`) y el motivo de cada descarte."""
    lista = lista or cargar_lista()
    validas: list[dict[str, Any]] = []
    descartes: list[str] = []
    vistas: set[str] = set()
    for f in crudas if isinstance(crudas, list) else []:
        motivo, estado = _motivo_de_descarte(f, hoy, lista, verificar)
        if motivo is None and f["url"] in vistas:
            motivo = f"{f['entidad']}: la URL ya estaba citada"
        if motivo:
            descartes.append(motivo)
            continue
        vistas.add(f["url"])
        validas.append({**{c: f[c].strip() for c in CAMPOS}, "verificacion": estado})
    return validas, descartes


def depurar_pieza(pieza: dict[str, Any], hoy: date, lista: dict[str, Any] | None = None,
                  verificar: Callable[[str], str] = verificar_url) -> tuple[dict[str, Any], list[str]]:
    """Deja en `editorial.fuentes` solo las válidas. Sin lista de agy, queda vacía y se avisa."""
    crudas = pieza["editorial"].get("fuentes")
    validas, descartes = depurar(crudas, hoy, lista, verificar)
    if not isinstance(crudas, list):
        descartes.append("agy no entregó la lista de fuentes")
    pieza["editorial"]["fuentes"] = validas
    return pieza, descartes


# Qué postura de una fuente equivale a cada dirección de nuestra lectura.
_POSTURA_DE_LA_LECTURA = {"ALCISTA": "alcista", "BAJISTA": "bajista", "LATERAL": "neutral"}


def discrepa(fuente: dict[str, Any], direccion: str) -> bool:
    """La fuente ve distinto que nuestra lectura (alcista/bajista/lateral contra su postura)."""
    return _POSTURA_DE_LA_LECTURA.get(direccion.upper(), "neutral") != fuente["postura"]
