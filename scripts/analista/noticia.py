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
import re
from datetime import date, datetime
from typing import Any, Callable

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


def _cifras(texto: str) -> set[str]:
    return {es._plano_numero(t) for t in es._NUMERO.findall(texto) if es._significativo(t)}


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
    citadas = _cifras(n["titular"] + " " + n["bajada"])
    if not citadas:
        return None
    texto = leer(n["url"]) if estado == "ok" else None
    if texto is None:
        return "trae cifras y no pude leer la nota para comprobarlas (muro de pago o página ilegible)"
    ausentes = sorted(citadas - _cifras(texto))
    if ausentes:
        originales = [t for t in es._NUMERO.findall(n["titular"] + " " + n["bajada"])
                      if es._plano_numero(t) in ausentes]
        return f"la cifra {', '.join(originales)} no aparece en la nota"
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
