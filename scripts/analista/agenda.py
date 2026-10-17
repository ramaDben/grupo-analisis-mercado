"""Los días clave de un análisis: el calendario económico de sus 7 días de vigencia.

Un análisis vale 7 días corridos (spec 2026-10-16 §2), así que su agenda es la de esos 7 días y no
la de la semana calendario. Investing.com entrega la semana en curso y la siguiente en pestañas
distintas (`thisWeek`, `nextWeek`, de domingo a sábado): pedir solo la primera dejaba la agenda
vacía cada sábado (oro, 2026-10-17). Spec 2026-10-17 §3.

Tres estados, porque se dicen distinto: `ok` (hay datos de alto impacto en la ventana), `vacia`
(el calendario respondió y no hay ninguno) y `sin_calendario` (no respondió, o entregó una copia
vieja: su respaldo de caché no avisa, así que se reconoce por las fechas).

El efecto sobre el activo sale del glosario (`si_sale_sobre_consenso`), como en el seguimiento:
nunca de la redacción.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Callable
from zoneinfo import ZoneInfo

SANTIAGO = ZoneInfo("America/Santiago")
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
VENTANA_DIAS = 7
MAXIMO_LAMINA = 6
URL_CALENDARIO = "https://es.investing.com/economic-calendar/"
PAISES = {"United States": "EE.UU.", "Chile": "Chile", "China": "China", "Euro Zone": "Zona Euro",
          "Euro Area": "Zona Euro", "Zona Euro": "Zona Euro"}


def dia_corto(momento: date | datetime) -> str:
    """«sábado 17/10», el mismo formato que `preparar.fecha_corta`."""
    if isinstance(momento, datetime):
        momento = momento.astimezone(SANTIAGO)
    return f"{DIAS[momento.weekday()]} {momento:%d/%m}"


def texto_vacia(agenda: dict[str, Any]) -> str:
    """La ventana sin datos de alto impacto, con sus fechas (decisión 2 del director, 2026-10-17)."""
    return (f"Sin datos de alto impacto entre el {agenda['desde']} y el {agenda['hasta']} en el calendario "
            "de EE.UU., Chile, China y la Zona Euro.")


def _domingo(d: date) -> date:
    """El domingo que abre la semana de Investing.com que contiene `d`."""
    return d - timedelta(days=(d.weekday() + 1) % 7)


def _cuando(ev: dict[str, Any]) -> datetime | None:
    """`cargar_calendario` ya entrega la hora en Santiago: no se reconvierte (issue #38)."""
    try:
        return datetime.strptime(ev["hora_servidor"], "%Y-%m-%d %H:%M").replace(tzinfo=SANTIAGO)
    except (KeyError, TypeError, ValueError):
        return None


def _hora(cuando: datetime) -> str:
    return f"{cuando:%H:%M} {'CLST' if cuando.dst() else 'CLT'}"


def _cifra(valor: Any) -> str:
    from pipeline_informe import _cifra_es

    return _cifra_es(str(valor or "").strip())


def _efecto(ev: dict[str, Any], ticker: str, nombre: str) -> str:
    from analista import macro_seguimiento as mac

    clave = mac.CLAVE_DEL_ACTIVO.get(ticker)
    verbo = ((ev.get("diccionario") or {}).get("si_sale_sobre_consenso") or {}).get(clave) if clave else None
    if verbo not in ("sube", "baja"):
        return ""
    return (f"Si sale sobre lo esperado, {mac._el(clave, nombre)} tiende a "
            f"{'subir' if verbo == 'sube' else 'bajar'}; si sale bajo lo esperado, lo contrario.")


def fila(ev: dict[str, Any], ticker: str, nombre: str) -> dict[str, Any]:
    cuando = _cuando(ev)
    dic = ev.get("diccionario") or {}
    efecto = _efecto(ev, ticker, nombre)
    return {"fecha": f"{cuando:%Y-%m-%d}", "dia": dia_corto(cuando), "hora": _hora(cuando),
            "evento": dic.get("nombre_es") or ev.get("nombre", ""), "fuente_nombre": ev.get("nombre", ""),
            "pais": PAISES.get(ev.get("pais", ""), ev.get("pais", "")),
            "anterior": _cifra(ev.get("previo")), "esperado": _cifra(ev.get("forecast")),
            "explicacion": dic.get("explicacion", ""), "efecto": efecto, "mueve_al_activo": bool(efecto)}


@dataclass
class Agenda:
    desde: str
    hasta: str
    estado: str  # "ok" | "vacia" | "sin_calendario"
    eventos: list[dict[str, Any]] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def a_dict(self) -> dict[str, Any]:
        return {"desde": self.desde, "hasta": self.hasta, "estado": self.estado,
                "eventos": [dict(e) for e in self.eventos], "url": URL_CALENDARIO}


def leer_ventana(ahora: datetime, ticker: str, nombre: str, cargar: Callable[..., dict[str, Any]] | None = None,
                 dias: int = VENTANA_DIAS) -> Agenda:
    """Los datos de alto impacto entre `ahora` y `ahora + dias`, de las dos pestañas que la cubren."""
    if cargar is None:
        from market_data_mcp.tools.calendar import cargar_calendario as cargar
    ahora = ahora.astimezone(SANTIAGO)
    limite = ahora + timedelta(days=dias)
    domingo = _domingo(ahora.date())
    crudos: list[dict[str, Any]] = []
    avisos: list[str] = []
    fallidas = 0
    for tab, inicio in (("thisWeek", domingo), ("nextWeek", domingo + timedelta(days=7))):
        if inicio > limite.date():
            continue
        try:
            # Todo el calendario (impacto bajo en adelante): sin filas no se puede reconocer la copia vieja.
            res = cargar(solo_hoy=False, min_impact="low", ahora=ahora, pestanas=(tab,))
        except Exception as exc:  # noqa: BLE001  el calendario es un insumo: su falla se dice, no tumba la pieza
            avisos.append(f"el calendario falló ({exc.__class__.__name__})")
            fallidas += 1
            continue
        if "error" in res:
            avisos.append(f"el calendario no respondió ({res['error']})")
            fallidas += 1
            continue
        eventos = list(res.get("eventos") or [])
        fechas = [c for c in map(_cuando, eventos) if c]
        if fechas and max(fechas).date() < inicio:
            avisos.append(f"el calendario entregó una copia vieja (su último dato es del {dia_corto(max(fechas))})")
            fallidas += 1
            continue
        crudos += eventos
    filas = []
    for ev in crudos:
        cuando = _cuando(ev)
        if ev.get("impacto") == "alto" and cuando and ahora <= cuando <= limite:
            filas.append((cuando, fila(ev, ticker, nombre)))
    filas.sort(key=lambda par: par[0])
    eventos = [f for _, f in filas]
    estado = "ok" if eventos else ("sin_calendario" if fallidas else "vacia")
    return Agenda(dia_corto(ahora), dia_corto(limite), estado, eventos, avisos)


def payload_lamina(agenda: dict[str, Any]) -> dict[str, Any]:
    """La lámina del calendario (plantilla `calendario` de Stories): todo su texto es de Python.

    Hasta 6 eventos, primero los que mueven al activo según el glosario, y después en orden de reloj.
    """
    eventos = agenda["eventos"]
    elegidos = ([e for e in eventos if e.get("mueve_al_activo")]
                + [e for e in eventos if not e.get("mueve_al_activo")])[:MAXIMO_LAMINA]
    elegidos.sort(key=lambda e: (e["fecha"], e["hora"]))
    return {
        "plantilla": "calendario",
        "sello": "CALENDARIO ECONÓMICO · GI",
        "fecha_hora": f"DEL {agenda['desde'].upper()} AL {agenda['hasta'].upper()}",
        "titulo": "Los días clave de este análisis",
        "subtitulo": "Datos de alto impacto de los próximos 7 días, en hora de Chile. Fuente: calendario de Investing.com.",
        "eventos": [{"numero": f"{i:02d}", "dia": e["dia"].upper(), "hora": e["hora"], "evento": e["evento"],
                     "pais": e["pais"], "impacto": "Alto impacto", "impacto_slug": "alto",
                     "anterior": e["anterior"], "esperado": e["esperado"], "tiene_esperado": bool(e["esperado"])}
                    for i, e in enumerate(elegidos, 1)],
        "cta": "Lo revisamos juntos en la plataforma MT5",
        "cta_sub": "Grupo Inteligencia",
    }
