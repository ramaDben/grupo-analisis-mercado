"""Piezas de ejemplo del bot de analistas, válidas contra `analista.esquema`.

Se arman con `nueva_pieza` (no son JSON estáticos) para que la huella siempre
corresponda a los datos: un fixture con la huella vieja probaría el freno, no la
maqueta.
"""
from __future__ import annotations

import base64
from pathlib import Path

from analista import esquema as es
from analista.autor import Autor

# PNG de 1x1 válido.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)

ANALISTA = {"nombre": "Camila Rojas", "cargo": "Analista de mercados", "contacto": "+56 9 1111 2222"}

# Sin foto ni firma: el bloque tiene que salir completo igual.
AUTOR = Autor("Benjamín Ignacio Bravo Soza", "Dirección de Análisis Técnico", None, None,
              {"entidad": "CMV", "categoria": "Operadores", "numero": "A-32915",
               "vigente_hasta": "2028-03-31",
               "url": "https://cmvsystem.cmvchile.cl/certificados/635409A1A002"})


def _imagen(dir_pedido: Path, nombre: str) -> str:
    (dir_pedido / nombre).write_bytes(PNG)
    return nombre


from datetime import datetime as _dt  # noqa: E402
from zoneinfo import ZoneInfo as _Zi  # noqa: E402

from estrategia.contrato import Escenario as _Esc  # noqa: E402
from estrategia.contrato import Lectura, Linea, Prueba, Referencia  # noqa: E402

_ESCENARIOS = (
    _Esc("⬆️", "c", "Mientras el precio cierre sobre la línea, la tendencia alcista sigue."),
    _Esc("↔️", "c", "Si el precio vuelve a la línea y la respeta, la línea gana fuerza."),
    _Esc("⬇️", "c", "Si una vela de 4 horas cierra bajo la línea, la tendencia deja de valer."),
)


def _linea(rol: str, valor: float, tipo: str = "diagonal", calidad: str = "A+") -> Linea:
    puntos = ((1790000000, valor - 1.0), (1790500000, valor)) if tipo == "diagonal" else ((1790000000, valor),)
    return Linea(rol, tipo, puntos, "H4", 3, calidad, valor)


def lectura(ticker: str = "XAUUSD", estado: str = "TENDENCIA", direccion: str = "ALCISTA",
            precio: float = 4000.0, invalidacion: float | None = 3950.0, objetivo: float | None = 4100.0,
            atr: float = 20.0, atr_d1: float = 50.0, rango: tuple[float, float] | None = None,
            vigilar: float | None = None, tipo_rango: str = "horizontal", calidad_prueba: str = "A+",
            vela: int = 1790600000) -> Lectura:
    """Una `Lectura` mínima y válida para probar el escenario sin MT5."""
    en_prueba = None
    if estado == "RANGO":
        sup, inf = rango
        l_sup, l_inf = _linea("rango", sup, tipo_rango, ""), _linea("rango", inf, tipo_rango, "")
        arriba = vigilar is None or vigilar == sup
        vig = Referencia(sup if arriba else inf, "resistencia del rango" if arriba else "soporte del rango",
                         l_sup if arriba else l_inf)
        lineas, inv, obj = (l_sup, l_inf), None, None
    else:
        seg = _linea("seguridad", invalidacion if invalidacion is not None else precio, calidad=calidad_prueba)
        lineas = (seg,)
        vig = Referencia(vigilar if vigilar is not None else seg.valor_actual, "línea de seguridad", seg)
        inv = Referencia(invalidacion, "línea de seguridad", seg) if invalidacion is not None else None
        obj = Referencia(objetivo, "resistencia diaria") if objetivo is not None else None
        if estado == "PRUEBA":
            en_prueba = Prueba(seg, seg.valor_actual, _dt(2026, 10, 12, 13, 0, tzinfo=_Zi("America/Santiago")))
    return Lectura(ticker=ticker, marco="H4", precio=precio, direccion=direccion, estado=estado,
                   lineas=lineas, en_prueba=en_prueba, vigilar=vig, invalidacion=inv, objetivo=obj,
                   escenarios=_ESCENARIOS,
                   salida="La posición se cierra con un cierre de 4 horas al otro lado de la línea de seguridad.",
                   conceptos=(), avisos=(), metricas={"atr": atr, "atr_d1": atr_d1}, vela=vela)


def activo_semanal(rango: bool = False, ticker: str | None = None) -> dict:
    """Una entrada de `datos.activos` como la deja `preparar_oportunidad`.

    `ticker` cambia solo el símbolo (para probar los que llevan punto, como `WTI.spot`).
    """
    from estrategia.contrato import lectura_a_dict

    from analista import oportunidad as op

    if rango:
        lec = lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14500.0,
                      rango=(14567.0, 14206.0), atr=85.86)
        fmt = {"precio": "14500", "vigilar": "14567", "invalidacion": "", "objetivo_tori": "",
               "entrada": "14567", "stop": "14610", "objetivo": "14438",
               "borde_superior": "14567", "borde_inferior": "14206"}
        nombre, visible, digits, unidad = "Cobre", "COPPER", 0, "USD/t"
    else:
        lec = lectura(ticker=ticker or "XAUUSD", direccion="BAJISTA", precio=4186.17, invalidacion=4227.32,
                      objetivo=4149.96)
        fmt = {"precio": "4.186,17", "vigilar": "4.227,32", "invalidacion": "4.227,32",
               "objetivo_tori": "4.149,96", "entrada": "4.186,17", "stop": "4.227,32",
               "objetivo": "4.062,72", "borde_superior": "", "borde_inferior": ""}
        nombre, visible, digits, unidad = "Oro", "XAU/USD", 2, "USD"
    return {"ticker": lec.ticker, "nombre": nombre, "ticker_visible": visible, "digits": digits,
            "unidad": unidad, "puntaje": 90.0,
            "foto": {"guardada": "2026-10-12T09:05:00-03:00", "fecha": "lunes 12-10", "precio": lec.precio},
            "lectura": lectura_a_dict(lec), "escenario": op.escenario(lec, digits).a_dict(), "fmt": fmt,
            "contrato": {"clp_unidad": 950.0, "vol_min": 0.01, "vol_paso": 0.01},
            "temporalidad": "4H · swing (de una a dos semanas)",
            "grafico": f"grafico_{lec.ticker.lower().replace('.', '_')}.png"}


FUENTES_EJEMPLO = [{
    "entidad": "Goldman Sachs", "medio": "Reuters", "fecha": "2026-10-14",
    "url": "https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/",
    "postura": "alcista", "tesis": "Goldman Sachs ve el oro en 4.800 dólares por la demanda de bancos centrales.",
    "verificacion": "ok"}]


def pieza_oportunidad(dir_pedido: Path, laminas: bool = False, wti: bool = False, rango: bool = False,
                      fuentes: list | None = None) -> dict:
    """El análisis de un activo con su texto ya escrito (por defecto el oro; `rango` es el cobre).

    Escribe el gráfico en `dir_pedido`; con `laminas=True` también la lámina, que en el bot se
    rinde antes del HTML (así el botón «Descargar lámina» aparece).
    """
    a = activo_semanal(rango=rango, ticker="WTI.spot" if wti else None)
    _imagen(dir_pedido, a["grafico"])
    if laminas:
        _imagen(dir_pedido, {"WTI.spot": "lamina_wti_spot.png"}.get(a["ticker"], f"lamina_{a['ticker'].lower()}.png"))
    t = a["ticker"]
    p = es.nueva_pieza("oportunidad", {"ticker": t},
                       {"ticker": t, "chip": "ANÁLISIS TÉCNICO Y FUNDAMENTAL", "edicion": "lunes 12/10 · 09:30",
                        "vigencia": {"desde": "lunes 12/10", "hasta": "lunes 19/10"},
                        "activos": [a], "drivers": {t: ["Dollar Index"]}, "agenda_semana": [], "curva": [],
                        "fundamental": {"fuera_catalogo": False, "sin_drivers": False, "referencia": "semanal"}},
                       {t: a["grafico"]}, extra_campos={"titulares": [t], "contexto": [t]})
    p["editorial"] = {"titular": f"{a['nombre']}: lectura técnica y fundamental",
                      "bajada": "Lectura de nuestros sistemas, drivers y voces de bancos.",
                      "titulares": {t: f"Titular de {t}"},
                      "contexto": {t: f"Contexto de {t}. La lectura se mantiene mientras el precio respete la línea."},
                      "fuentes": [dict(f) for f in (FUENTES_EJEMPLO if fuentes is None else fuentes)]}
    return p


def pieza_seguimiento(dir_pedido: Path) -> dict:
    """Un seguimiento del oro como lo deja `preparar_seguimiento`, con el texto de WhatsApp."""
    a = activo_semanal()
    _imagen(dir_pedido, "grafico.png")
    datos = {"semana": "2026-W42", "ticker": a["ticker"], "nombre": a["nombre"],
             "evaluacion": {"estado": "en_curso", "avance_pct": 40},
             "precio_vivo": 4150.0, "lectura_hoy": "La lectura de hoy sigue igual.", "reemplazada": False,
             "whatsapp": "[[SALUDO]] te cuento cómo va el oro: la simulación de esta semana avanza a favor.",
             "edicion": "miércoles 14-10 · 11:00", "activo": a}
    return es.nueva_pieza("seguimiento", {"ticker": a["ticker"]}, datos, {"principal": "grafico.png"})
