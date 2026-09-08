"""Tool obtener_calendario_macro — calendario económico vía Investing.com.

Fuente única: endpoint AJAX getCalendarFilteredData de Investing.com (issue #91).
Pedimos las horas en UTC (timeZone=55) y convertimos a America/Santiago con
zoneinfo — nunca offsets fijos. Incluye el resultado real (`actual`) una vez
publicado el dato, clasificado como mejor/peor/en_linea vs el consenso.
Reemplaza el triple feed Fair Economy (sin `actual` y sin cobertura de Chile).
MT5 queda exclusivamente para precios y niveles técnicos (get_asset_levels).
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

_URL = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
_REFERER = "https://www.investing.com/economic-calendar/"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36"
_TIMEZONE_UTC = "55"  # ID Investing.com para GMT/UTC (verificado contra CPI 12:30 UTC)
_SANTIAGO = ZoneInfo("America/Santiago")

# Países del mandato del director: Chile, EE.UU., China, Zona Euro
_PAISES: dict[str, int] = {
    "Chile": 27,
    "Estados Unidos": 5,
    "China": 37,
    "Zona Euro": 72,
}

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "cache"
_CACHE_TTL = 3600  # 1 hora en segundos

_IMPACTO_RANK_EN: dict[str, int] = {"low": 0, "medium": 1, "high": 2}
_IMPACTO_RANK_ES: dict[str, int] = {"bajo": 0, "medio": 1, "alto": 2}
# El título de la celda de sentimiento indica la volatilidad esperada
_VOLATILIDAD_ES: dict[str, str] = {
    "Low Volatility Expected": "bajo",
    "Moderate Volatility Expected": "medio",
    "High Volatility Expected": "alto",
}

_GLOSARIO_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "glosario_siglas.json"
)

# ── regex de parseo de filas del calendario ───────────────────────────────────
_RE_ROW = re.compile(
    r'<tr id="eventRowId_(?P<row_id>\d+)"[^>]*'
    r'data-event-datetime="(?P<dt>[\d/]+ [\d:]+)"[^>]*>(?P<body>.*?)</tr>',
    re.S,
)
_RE_FLAG = re.compile(
    r'<span title="(?P<pais>[^"]*)"[^>]*>(?:&nbsp;)?</span>\s*(?P<divisa>[A-Z]{3})'
)
_RE_SENTIMENT = re.compile(r'class="left textNum sentiment noWrap" title="(?P<vol>[^"]*)"')
_RE_EVENT = re.compile(r'<td class="left event"[^>]*>\s*(?:<a[^>]*>)?\s*(?P<nombre>[^<]+)')
_RE_ACTUAL = re.compile(
    r'<td class="[^"]*\bact\b[^"]*"\s*title="(?P<titulo>[^"]*)"\s*id="eventActual_\d+">(?P<valor>[^<]*)<'
)
_RE_FORECAST = re.compile(r'id="eventForecast_\d+">(?P<valor>[^<]*)<')
_RE_PREVIOUS = re.compile(r'id="eventPrevious_\d+">(?:<span[^>]*>)?(?P<valor>[^<]*)<')


def _cargar_glosario() -> dict[str, Any]:
    if not _GLOSARIO_PATH.exists():
        return {}
    return json.loads(_GLOSARIO_PATH.read_text(encoding="utf-8"))


def _cache_path(tab: str) -> Path:
    return _CACHE_DIR / f"investing_calendar_{tab}.html"


def _cache_valid(path: Path) -> bool:
    return path.exists() and (time.time() - path.stat().st_mtime) < _CACHE_TTL


def _fetch_calendario(tab: str) -> str:
    """POST getCalendarFilteredData con horas en UTC. Caché local de 1 hora.

    Retorna el HTML de las filas, o "" ante cualquier falla sin caché de respaldo.
    """
    cached = _cache_path(tab)
    if _cache_valid(cached):
        try:
            return cached.read_text(encoding="utf-8")
        except Exception:  # nosec B110 — caché ilegible: se sigue al fetch remoto
            pass

    params = [("country[]", str(pid)) for pid in _PAISES.values()]
    params += [
        ("timeZone", _TIMEZONE_UTC),
        ("timeFilter", "timeOnly"),
        ("currentTab", tab),
        ("limit_from", "0"),
    ]
    try:
        req = urllib.request.Request(
            _URL,
            data=urllib.parse.urlencode(params).encode("ascii"),
            headers={
                "User-Agent": _UA,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": _REFERER,
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310  # nosec B310 — URL https fija de Investing.com
            payload = json.loads(resp.read().decode("utf-8"))
        html = payload.get("data", "")
        if html:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cached.write_text(html, encoding="utf-8")
        return html
    except Exception:
        if cached.exists():
            try:
                return cached.read_text(encoding="utf-8")
            except Exception:  # nosec B110 — sin caché legible se retorna "" (contrato de error aguas arriba)
                pass
        return ""


def _utc_a_santiago(dt_str: str) -> str:
    """Convierte 'YYYY/MM/DD HH:MM:SS' UTC a America/Santiago 'YYYY-MM-DD HH:MM'."""
    dt = datetime.strptime(dt_str, "%Y/%m/%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return dt.astimezone(_SANTIAGO).strftime("%Y-%m-%d %H:%M")


def _limpiar_celda(valor: str) -> str:
    return valor.replace("&nbsp;", "").strip()


def _clasificar_resultado(titulo_actual: str, actual: str, forecast: str) -> str | None:
    """Clasifica el resultado publicado vs consenso usando el título de la celda."""
    if not actual:
        return None
    if "Better Than Expected" in titulo_actual:
        return "mejor"
    if "Worse Than Expected" in titulo_actual:
        return "peor"
    return "en_linea" if forecast else None


def _parsear_filas(html: str) -> list[dict]:
    """Extrae eventos del HTML de filas del calendario Investing.com."""
    eventos: list[dict] = []
    for m in _RE_ROW.finditer(html):
        body = m.group("body")
        flag = _RE_FLAG.search(body)
        nombre = _RE_EVENT.search(body)
        if not flag or not nombre:
            continue  # filas sin evento (festivos, separadores)
        sentiment = _RE_SENTIMENT.search(body)
        actual_m = _RE_ACTUAL.search(body)
        forecast_m = _RE_FORECAST.search(body)
        previous_m = _RE_PREVIOUS.search(body)

        actual = _limpiar_celda(actual_m.group("valor")) if actual_m else ""
        forecast = _limpiar_celda(forecast_m.group("valor")) if forecast_m else ""
        try:
            hora = _utc_a_santiago(m.group("dt"))
        except ValueError:
            continue

        ev: dict[str, Any] = {
            "nombre": " ".join(nombre.group("nombre").split()),
            "divisa": flag.group("divisa"),
            "pais": flag.group("pais"),
            "impacto": _VOLATILIDAD_ES.get(
                sentiment.group("vol") if sentiment else "", "bajo"
            ),
            "hora_servidor": hora,
            "forecast": forecast,
            "previo": _limpiar_celda(previous_m.group("valor")) if previous_m else "",
            "actual": actual,
            "fuente": "investing",
        }
        resultado = _clasificar_resultado(
            actual_m.group("titulo") if actual_m else "", actual, forecast
        )
        if resultado:
            ev["resultado"] = resultado
        eventos.append(ev)
    return eventos


def _enganchar_glosario(
    nombre: str, glosario: dict, pais: str = ""
) -> dict | None:
    """Busca entrada del glosario para un nombre de evento, del pais del evento.

    Gana la entrada cuya clave o alias coincide con el tramo **más largo** del
    título, y no la que aparece primero en el JSON. La versión anterior devolvía
    el primer match, así que el resultado dependía del orden del archivo: la
    entrada "Cushing Crude Oil Inventories" quedaba inalcanzable porque "Crude
    Oil Inventories" estaba escrita unas líneas antes, y el evento de Cushing
    salía nombrado como el inventario nacional.

    Un match más largo es siempre más específico, así que el criterio no puede
    empeorar un enganche que ya funcionaba: solo desempata entre varios.

    **Una entrada de otro pais no engancha, y eso es lo que evita publicar el
    signo al reves.** El IPC de Chile se titula "CPI (MoM)" igual que el de
    EE.UU., porque la fuente publica en ingles, asi que sin este filtro
    enganchaba la entrada `CPI` de EE.UU. y viajaba con su mapeo direccional:
    `usdclp: "sube"`. Para un IPC chileno es exactamente al contrario, porque
    mas inflacion local le quita espacio al Banco Central para bajar la tasa y
    eso sostiene al peso. `clasificacion_macro.clasificar` ya tenia esta regla;
    este modulo era la mitad que no la tenia, y las dos se hablan por el mismo
    glosario.

    Una entrada sin `pais` sigue enganchando cualquier evento, y un evento sin
    pais sigue enganchando cualquier entrada: el filtro solo descarta cuando los
    dos estan declarados y se contradicen.

    Retorna None si no hay match, y el evento queda marcado `glosario_pendiente`.
    """
    nombre_upper = nombre.upper()
    pais_evento = str(pais or "").strip()
    mejor: dict | None = None
    mejor_largo = -1
    for key, entry in glosario.items():
        if key.startswith("_") or key.isdigit():
            continue
        pais_entrada = str(entry.get("pais") or "").strip()
        if pais_evento and pais_entrada and pais_evento != pais_entrada:
            continue
        for candidato in (key, *entry.get("titulos_ff", [])):
            if candidato.upper() in nombre_upper and len(candidato) > mejor_largo:
                mejor, mejor_largo = entry, len(candidato)
    return mejor


def _sobrevive_al_umbral(ev: dict[str, Any], umbral: int) -> bool:
    """Pasa el filtro de impacto, o lo pasa por ser tier 1 nuestro.

    **`impacto` es la opinion de la fuente y `tier` es la nuestra, y la que
    gobierna nuestras decisiones es la nuestra** (mismo criterio que
    `test_el_tier_es_nuestro_y_no_el_impacto_de_investing`). Investing marca
    impacto **bajo** al IPC de Chile y a la decision de tasas del Banco Central
    de Chile, asi que con el umbral en `medium` los dos desaparecian del
    calendario: no salian en la agenda de ningun canal y, lo mas grave, el gate
    de blackout del escaner **nunca podia activarse**, porque el evento que lo
    dispara no llegaba a la lista. Las reglas de blackout de Chile estaban
    escritas y correctas, y aun asi inertes.

    Solo rescata tier 1, que es el que reprecia todo. Tier 2 y 3 siguen
    obedeciendo a la fuente: rescatarlos importaba eventos enganchados por
    alias flojos (el NFIB calza con la entrada del ISM) y eso llenaria la
    agenda de ruido.
    """
    if _IMPACTO_RANK_ES.get(ev.get("impacto", ""), 0) >= umbral:
        return True
    return (ev.get("diccionario") or {}).get("tier") == 1


def cargar_calendario(
    solo_hoy: bool = True,
    min_impact: str = "medium",
    ahora: datetime | None = None,
) -> dict[str, Any]:
    """Calendario económico de Investing.com, como función y no solo como tool.

    Existe por la misma razón que `market_data_mcp.analisis.analizar_activo`: el
    cuerpo vivía dentro del closure de `register(mcp)` y solo se podía obtener
    hablando MCP. El escáner de tandas necesita el calendario para su gate de
    blackout, y un script no puede llamar a una tool.

    Se queda en este módulo en vez de mudarse a uno nuevo porque los ayudantes de
    descarga, caché y parseo son casi 200 líneas que nadie más usa: moverlos sería
    churn sin beneficio.

    `ahora` se inyecta para poder testear el filtro `solo_hoy` sin depender del
    reloj de la máquina.
    """
    if min_impact not in _IMPACTO_RANK_EN:
        return {
            "error": "INVALID_IMPACT",
            "message": (
                f"min_impact '{min_impact}' inválido. "
                f"Opciones: {list(_IMPACTO_RANK_EN)}"
            ),
        }

    html = _fetch_calendario("thisWeek")
    if not html:
        return {
            "error": "NO_CALENDAR_FEEDS",
            "message": (
                "Investing.com no respondió y no hay caché local. "
                "Usar WebSearch investing.com como fallback."
            ),
        }

    todos = _parsear_filas(html)
    umbral = _IMPACTO_RANK_EN[min_impact]
    hoy = (ahora or datetime.now(tz=_SANTIAGO)).date()
    glosario = _cargar_glosario()

    # El glosario se engancha ANTES del umbral, porque el `tier` propio puede
    # rescatar un evento que la fuente subestimo. Ver `_sobrevive_al_umbral`.
    eventos: list[dict[str, Any]] = []
    for ev in todos:
        if solo_hoy:
            fecha_ev = datetime.strptime(
                ev["hora_servidor"], "%Y-%m-%d %H:%M"
            ).date()
            if fecha_ev != hoy:
                continue
        ev = dict(ev)
        entrada = _enganchar_glosario(ev["nombre"], glosario, ev.get("pais", ""))
        if entrada:
            ev["diccionario"] = entrada
        else:
            ev["glosario_pendiente"] = True
        if not _sobrevive_al_umbral(ev, umbral):
            continue
        eventos.append(ev)

    resultado: dict[str, Any] = {"source": "investing"}
    if not eventos:
        resultado["eventos"] = []
        resultado["info"] = "sin eventos sobre el umbral de impacto ni de tier 1 hoy"
        return resultado

    resultado["eventos"] = eventos
    return resultado


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def obtener_calendario_macro(
        solo_hoy: bool = True,
        min_impact: str = "medium",
    ) -> dict[str, Any]:
        """Calendario económico vía Investing.com (Chile + EE.UU. + China + Zona Euro).

        Incluye el resultado real (`actual`) una vez publicado el dato, con
        clasificación `resultado` = mejor | peor | en_linea vs el consenso.
        Hora en America/Santiago. Si Investing.com no responde, retorna error
        NO_CALENDAR_FEEDS → el comando debe caer a WebSearch como fallback.

        Args:
            solo_hoy: si True, solo eventos de hoy en Santiago (default True).
            min_impact: umbral mínimo — 'low' | 'medium' | 'high' (default 'medium').

        Returns:
            {"eventos": [...], "source": "investing", ...}
            o {"error": CÓDIGO, "message": "..."} si la fuente falla.
        """
        return cargar_calendario(solo_hoy=solo_hoy, min_impact=min_impact)
