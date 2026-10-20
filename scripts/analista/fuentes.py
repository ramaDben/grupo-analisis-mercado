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
import unicodedata
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


def verificar_url(url: str, timeout: int = 10, lista: dict[str, Any] | None = None) -> str:
    """`ok`, `sin_verificar` (muro de pago o bloqueo a bots) o `muerta` (404 o dominio caído).

    `lista` es la lista cerrada con que se depura (la del segmento, si la hay): una redirección vale si
    termina en un dominio del mismo medio. Sin ella se usa la base.
    """
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
    if r.status_code >= 400:
        return "muerta"
    # La redirección se revalida: un soft-404 que lleva a la portada, o a otro dominio, responde 200
    # pero ya no es el artículo citado.
    destino = getattr(r, "url", None) or url
    if not _del_dominio(_sin_www(_host(destino)), _dominios_de(url, lista)) or not _con_ruta_de_articulo(destino):
        return "muerta"
    return "ok"


def _dominios_de(url: str, lista: dict[str, Any] | None = None) -> list[str]:
    """Los dominios de los medios de la lista que cubren la URL citada; si ninguno, su propio host sin www."""
    host = _host(url)
    try:
        medios = (lista if lista is not None else cargar_lista())["medios"].values()
    except (OSError, ValueError, KeyError):
        medios = []
    propios = [d for dominios in medios if any(_del_dominio(host, [d]) for d in dominios) for d in dominios]
    return propios or [_sin_www(host)]


def _con_lista(verificar: Callable[..., str], lista: dict[str, Any]) -> Callable[[str], str]:
    """El verificador con la lista de la depuración, si la acepta (`verificar_url` sí; un doble de test no)."""
    import inspect

    try:
        acepta = "lista" in inspect.signature(verificar).parameters
    except (TypeError, ValueError):
        acepta = False
    return (lambda url: verificar(url, lista=lista)) if acepta else verificar


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
    verificar = _con_lista(verificar, lista)
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


# ───────────────────────────────────────────── mínimo de un banco (spec 2026-10-17 §5)

INTENTO = "fuentes_intento_1.json"


def _nombres_banco(lista: dict[str, Any]) -> set[str]:
    grupos = lista.get("cuentan_como_banco") or ["bancos_de_inversion"]
    return {e for g in grupos for e in lista["entidades"].get(g, [])}


def bancos(fuentes: Any, lista: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Las fuentes cuya entidad cuenta como banco (`cuentan_como_banco` de la lista cerrada)."""
    nombres = _nombres_banco(lista or cargar_lista())
    return [f for f in (fuentes if isinstance(fuentes, list) else [])
            if isinstance(f, dict) and f.get("entidad") in nombres]


def seleccionar_bancos_correo(
    fuentes: list[dict[str, Any]],
    direccion: str,
    lista: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """El banco del correo: uno solo, el más reciente que respalda nuestra lectura (director, 2026-10-19).

    El correo va a un prospecto que lo lee en segundos: la voz externa es una confirmación de la
    lectura, no un contrapunto. Los bancos que ven distinto no se muestran. Sin un banco que la
    respalde el bloque no sale: no se rellena con uno que contradice ni con un organismo.
    """
    a_favor = [b for b in bancos(fuentes, lista) if not discrepa(b, direccion)]
    a_favor.sort(key=lambda b: str(b.get("fecha", "")), reverse=True)
    return a_favor[:1]


# ───────────────────────────────────────────── fuente directa por segmento (spec 2026-10-20)

SEGMENTOS = ("fx", "commodities", "acciones", "etfs", "indices", "cripto")
CONFIG_SEGMENTOS = RAIZ / "config" / "segmentos_fuentes.json"


def _plano(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def cargar_segmentos(ruta: Path = CONFIG_SEGMENTOS) -> dict[str, Any]:
    """El config de segmentos; sin archivo, vacío. Un JSON corrupto propaga: no se publica a ciegas."""
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def lista_del_segmento(segmento: str, base: dict[str, Any] | None = None,
                       segmentos: dict[str, Any] | None = None) -> dict[str, Any]:
    """La lista cerrada extendida con las entidades y los medios propios del segmento."""
    if segmento not in SEGMENTOS:
        raise ValueError(f"segmento desconocido: {segmento!r}")
    base = base if base is not None else cargar_lista()
    segmentos = segmentos if segmentos is not None else cargar_segmentos()
    extra = segmentos.get(segmento) or {}
    entidades = {g: list(v) for g, v in base["entidades"].items()}
    if extra.get("entidades"):
        entidades[f"segmento_{segmento}"] = list(extra["entidades"])
    medios = {m: list(d) for m, d in base["medios"].items()}
    for medio, dominios in (extra.get("medios") or {}).items():
        medios[medio] = list(dict.fromkeys([*medios.get(medio, []), *dominios]))
    return {**base, "entidades": entidades, "medios": medios}


def nombra_ancla(fuente: dict[str, Any], ancla: dict[str, Any]) -> bool:
    """Algún término del ancla aparece en la tesis o en la ruta de la URL (sin tildes ni mayúsculas).

    Antes se borran los `terminos_excluidos` del ancla: un nombre que contiene al término sin ser el ancla
    («S&P Dow Jones Indices» contiene «Dow Jones» y no es el Dow).
    """
    texto = _plano(f"{fuente.get('tesis', '')} {urlparse(str(fuente.get('url', ''))).path}")
    for excluido in ancla.get("terminos_excluidos", []):
        texto = re.sub(rf"(?<!\w){re.escape(_plano(excluido))}(?!\w)", " ", texto)
    return any(re.search(rf"(?<!\w){re.escape(_plano(t))}(?!\w)", texto)
               for t in ancla.get("terminos_ancla", []))


def _sin_www(host: str) -> str:
    return host[4:] if host.startswith("www.") else host


def _ruta_propia(ruta: str) -> tuple[str, str]:
    """`host/ruta` a (host sin www, `/ruta` o vacío si es el host entero)."""
    host, _, resto = ruta.lower().partition("/")
    return _sin_www(host), f"/{resto.strip('/')}" if resto.strip("/") else ""


def _en_rutas_propias(url: str, ancla: dict[str, Any]) -> bool:
    """False si la URL cae en un sitio acotado del ancla y fuera de sus `rutas_propias`.

    Una ruta propia es `host/ruta` (p. ej. `goldmansachs.com/investor-relations`). Un sitio queda acotado
    cuando alguna ruta propia vive bajo el mismo dominio del ancla: ahí solo cuentan esas secciones
    (relaciones con inversionistas, prensa), no el research ni el catálogo. Los demás dominios, sin acotar.
    """
    rutas = [_ruta_propia(r) for r in ancla.get("rutas_propias") or []]
    if not rutas:
        return True
    p = urlparse(url)
    host, ruta = _sin_www((p.hostname or "").lower()), p.path.lower()
    acotado = any(_del_dominio(host, [d]) and any(_del_dominio(h, [d]) for h, _ in rutas)
                  for d in ancla.get("dominios", []))
    return not acotado or any(host == h and (not r or ruta == r or ruta.startswith(r + "/")) for h, r in rutas)


# Por segmento, el grupo de entidades de la lista cerrada que no habilita por su nombre: en acciones, una
# voz de banco de inversión es research aunque el banco sea la empresa del ancla (#GS, #MS, #BAC).
# Esa empresa cuenta solo por su comunicado propio (dominio del ancla, dentro de sus rutas propias).
_ENTIDAD_NO_HABILITA = {"acciones": "bancos_de_inversion"}


def fuentes_directas(fuentes: Any, segmento: str, ancla: dict[str, Any],
                     lista: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Las fuentes del ancla misma (su entidad o su dominio) que además la nombran. No mira la postura."""
    lista = lista or lista_del_segmento(segmento)
    sin_nombre = set(lista["entidades"].get(_ENTIDAD_NO_HABILITA.get(segmento, ""), []))

    def propia(f: dict[str, Any]) -> bool:
        url = str(f.get("url", ""))
        por_entidad = f.get("entidad") in ancla.get("entidades", []) and f.get("entidad") not in sin_nombre
        por_dominio = _del_dominio(_host(url), ancla.get("dominios", []))
        return (por_entidad or por_dominio) and _en_rutas_propias(url, ancla) and nombra_ancla(f, ancla)

    entidades = _entidades(lista)
    return [f for f in (fuentes if isinstance(fuentes, list) else [])
            if isinstance(f, dict) and propia(f) and f.get("entidad") in entidades]


def falta_fuente_directa(pieza: dict[str, Any], segmento: str, ancla: dict[str, Any],
                         lista: dict[str, Any] | None = None) -> list[str]:
    """El error de `--validar` si no hay fuente directa; vacío si la hay o si `fuentes` aún no es lista."""
    fuentes = (pieza.get("editorial") or {}).get("fuentes")
    if not isinstance(fuentes, list):
        return []  # `esquema.errores` ya dice que falta la lista
    lista = lista or lista_del_segmento(segmento)
    if fuentes_directas(fuentes, segmento, ancla, lista):
        return []
    return [f"fuentes: falta una fuente directa de {ancla['nombre']} ({', '.join(ancla.get('entidades', []))}) "
            f"con una nota de los últimos {lista.get('frescura_dias', 14)} días que nombre {ancla['nombre']}"]


def directa_de(pieza: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    """(segmento, ancla) del sello `datos.fuente_directa`, o None si la pieza no lo trae."""
    sello = (pieza.get("datos") or {}).get("fuente_directa")
    if isinstance(sello, dict) and sello.get("segmento") and isinstance(sello.get("ancla"), dict):
        return sello["segmento"], sello["ancla"]
    return None


def guardar_intento(dir_pedido: Path, validas: list[dict[str, Any]], descartes: list[str], crudas: Any) -> Path:
    """Lo que dejó el primer intento, para que el segundo no repita URLs caídas (spec 2026-10-17 §5)."""
    urls_validas = {f.get("url") for f in validas if isinstance(f, dict)}
    descartadas = [f["url"] for f in (crudas if isinstance(crudas, list) else [])
                   if isinstance(f, dict) and isinstance(f.get("url"), str) and f["url"] not in urls_validas]
    ruta = Path(dir_pedido) / INTENTO
    ruta.write_text(json.dumps({"validas": list(validas), "descartadas": descartadas, "motivos": list(descartes)},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta
