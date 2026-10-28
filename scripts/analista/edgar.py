"""Lector de hechos esenciales 8-K de la SEC vía EDGAR Atom feeds (spec 2026-10-28, Task 2).

Consulta el feed Atom de la SEC para un CIK dado, filtra eventos dentro de
la ventana de días definida (por defecto 45) y resuelve los titulares en español
según el ítem de mayor prioridad del 8-K.
"""
from __future__ import annotations

import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import datetime, timedelta

ENV_CONTACTO: str = "GI_EDGAR_CONTACTO"

ITEMS: dict[str, str] = {
    "2.02": "Resultados del trimestre",
    "5.02": "Cambios en la directiva",
    "1.01": "Acuerdo relevante",
    "2.01": "Compra o venta de activos",
    "7.01": "Aviso de la empresa",
    "8.01": "Aviso de la empresa",
}

PRIORIDAD_ITEMS: list[str] = ["2.02", "5.02", "1.01", "2.01", "7.01", "8.01"]


def _tag_local(elem: ET.Element) -> str:
    """Extrae el nombre local del tag ignorando el XML namespace."""
    tag = elem.tag
    return tag.split("}")[-1] if "}" in tag else tag


def parsear_8k(xml: str) -> list[dict]:
    """Parsea el feed Atom de reportes 8-K de la SEC.

    Devuelve una lista de dicts con:
        - fecha: datetime con zona horaria
        - url: enlace al reporte index.htm
        - items: lista de códigos de ítems extraídos del summary (ej. ["2.02", "7.01"])
    Si una entrada tiene <updated> ilegible o fecha malformada, se ignora esa entrada.
    """
    root = ET.fromstring(xml)
    if _tag_local(root) != "feed":
        raise ValueError(f"XML no es un feed Atom válido (root tag: {root.tag})")

    entradas: list[dict] = []
    for elem in root.iter():
        if _tag_local(elem) != "entry":
            continue

        updated_str = None
        for child in elem:
            if _tag_local(child) == "updated" and child.text:
                updated_str = child.text.strip()
                break

        if not updated_str:
            continue

        try:
            fecha = datetime.fromisoformat(updated_str)
        except Exception:
            continue

        url = ""
        primer_link = ""
        for child in elem:
            if _tag_local(child) == "link":
                href = child.get("href", "").strip()
                if not primer_link and href:
                    primer_link = href
                if child.get("rel") == "alternate" and href:
                    url = href
                    break
        if not url:
            url = primer_link

        summary_str = ""
        for child in elem:
            if _tag_local(child) == "summary" and child.text:
                summary_str = child.text
                break

        items = re.findall(r"Item\s+([0-9]+\.[0-9]+)", summary_str, re.IGNORECASE)

        entradas.append({
            "fecha": fecha,
            "url": url,
            "items": items,
        })

    return entradas


def titular_de(items: list[str]) -> str | None:
    """Devuelve el titular en español del ítem con mayor prioridad presente en items.

    Si ninguno de los ítems está en la lista de items permitidos, devuelve None.
    """
    for item_prio in PRIORIDAD_ITEMS:
        if item_prio in items:
            return ITEMS[item_prio]
    return None


def construir_pedido(url: str, contacto: str) -> urllib.request.Request:
    """Construye un urllib.request.Request con User-Agent conforme a la política de la SEC."""
    user_agent = f"GrupoInteligencia/1.0 ({contacto})"
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/atom+xml, application/xml, text/xml, */*",
    }
    return urllib.request.Request(url, headers=headers)


def _descargar_defecto(url: str, contacto: str) -> str:
    """Descargador por defecto con urllib."""
    req = construir_pedido(url, contacto)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def candidatas_8k(
    cik: str,
    organismo: str,
    ahora: datetime,
    descargar: Callable[[str], str] | None = None,
    ventana_dias: int = 45,
) -> tuple[list[dict], str | None]:
    """Obtiene y procesa las publicaciones 8-K de un CIK en la ventana definida.

    Retorna:
        (lista_candidatas, aviso)
    """
    contacto = os.environ.get(ENV_CONTACTO, "").strip()
    if not contacto:
        return [], "No hay correo de contacto configurado en GI_EDGAR_CONTACTO para consultar EDGAR"

    url = (
        f"https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&CIK={cik}&type=8-K&owner=include&count=10&output=atom"
    )

    if descargar is None:
        def fn_descargar(u: str) -> str:
            return _descargar_defecto(u, contacto)
    else:
        fn_descargar = descargar

    try:
        xml = fn_descargar(url)
        entradas = parsear_8k(xml)
    except Exception as exc:
        return [], f"Error consultando EDGAR para {organismo}: {exc}"

    candidatas: list[dict] = []
    for entrada in entradas:
        titular = titular_de(entrada["items"])
        if titular is None:
            continue

        fecha_entrada = entrada["fecha"]
        if ahora.tzinfo is not None:
            if fecha_entrada.tzinfo is None:
                fecha_cmp = fecha_entrada.replace(tzinfo=ahora.tzinfo)
            else:
                fecha_cmp = fecha_entrada
            ahora_cmp = ahora
        else:
            if fecha_entrada.tzinfo is not None:
                fecha_cmp = fecha_entrada.replace(tzinfo=None)
            else:
                fecha_cmp = fecha_entrada
            ahora_cmp = ahora

        diff = ahora_cmp - fecha_cmp
        if not (timedelta(0) <= diff <= timedelta(days=ventana_dias)):
            continue

        candidatas.append({
            "medio": "SEC EDGAR",
            "fecha": fecha_entrada.strftime("%Y-%m-%d"),
            "url": entrada["url"],
            "titular_original": titular,
            "titular_es": titular,
            "escalon": "oficial",
            "organismo": organismo,
        })

    return candidatas, None
