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


PLAN = {
    "hay_plan": True, "sesgo": "Alcista",
    "gatillo": "Si una vela de 4 horas cierra sobre 4.131,00, se rompe la línea bajista del retroceso y la tendencia retoma.",
    "invalidacion": "El escenario se anula con un cierre bajo 4.090,10, la línea alcista de seguridad.",
    "salida": "La posición se cierra cuando una vela de 4 horas cierra al otro lado de la línea de seguridad, hoy en 4.090,10. No hay objetivo fijo.",
    "estado": "Armado: el precio todavía no cruza el gatillo.",
    "niveles": {"gatillo": 4131.0, "invalidacion": 4090.1, "vela": 1791734400},
}


def activo(dir_pedido: Path) -> dict:
    datos = {
        "chip": "NOTA DE MERCADO · COMMODITIES",
        "rotulo_referencia": "Cotización de referencia",
        "referencia": "4.110,65 USD",
        "edicion": "08/10/2026 · 09:39 hrs Chile",
        "nombre": "Oro", "ticker_visible": "XAU/USD", "ticker": "XAUUSD",
        "precio": "4.110,65", "soporte": "4.098,20", "resistencia": "4.131,00",
        "direccion": "Alcista",
        "nivel_vigilar": "4.131,00",
        "que_esperar": "sesgo comprador; sobre 4.131,00 gana camino al alza",
        "escenarios": [
            "⬆️ Sobre 4.131,00 → fuerza compradora",
            "↔️ Entre 4.098,20 y 4.131,00 → rango",
            "⬇️ Bajo 4.098,20 → presión vendedora",
        ],
        "temporalidad": "intradía · marco 1H (dentro de la jornada)",
        "por_que_temporalidad": "Por qué 1H acá: el oro se mueve lo justo para leerlo hora a hora.",
        "pie_imagen": "Oro · XAU/USD, gráfico de 1 hora con datos de MetaTrader 5",
        "plan": dict(PLAN),
    }
    p = es.nueva_pieza("activo", {"ticker": "XAUUSD"}, datos, {"principal": _imagen(dir_pedido, "alerta.png")})
    p["editorial"].update({
        "titular": "El oro sostiene el impulso comprador",
        "bajada": "La tendencia de corto plazo sigue al alza mientras respete el soporte",
        "lectura": "El oro cotiza sobre su media de 50 horas.\n\nMientras no pierda 4.098,20, el sesgo sigue comprador.",
        "empuja_alza": "• Dólar global más débil\n• Búsqueda de refugio",
        "empuja_baja": "• Rendimientos del Tesoro al alza\n• Toma de utilidades",
        "que_no_hacer": "No compres en la resistencia sin confirmación: espera el quiebre.",
    })
    return p


def oportunidad(dir_pedido: Path) -> dict:
    """El foco técnico del día: la pieza de activo para un prospecto, sin estadística."""
    base = activo(dir_pedido)
    datos = {**base["datos"], "chip": "FOCO TÉCNICO DEL DÍA · ORO",
             "plan": dict(PLAN),
             "seleccion": {"evaluados": 10, "fecha": "09-10-2026", "hora": "10:40"}}
    p = es.nueva_pieza("oportunidad", {"ticker": "XAUUSD"}, datos, base["imagenes"])
    p["editorial"].update(base["editorial"])
    return p


def calendario(dir_pedido: Path) -> dict:
    eventos = [
        {"id": "1", "hora": "09:30", "pais": "EE.UU.", "evento": "Peticiones de subsidio por desempleo",
         "anterior": "199K", "esperado": "200K", "actual": "197K", "estado": "salio"},
        {"id": "2", "hora": "14:00", "pais": "EE.UU.", "evento": "Minutas de la Fed",
         "anterior": "", "esperado": "", "actual": "", "estado": "proximo"},
    ]
    datos = {
        "chip": "CALENDARIO ECONÓMICO", "rotulo_referencia": "Datos de alto impacto", "referencia": "2",
        "edicion": "08/10/2026 · 09:39 hrs Chile", "alcance": "hoy", "eventos": eventos,
    }
    p = es.nueva_pieza("calendario", {"alcance": "hoy"}, datos, {"principal": _imagen(dir_pedido, "calendario.png")},
                       extra_campos={"explicaciones": ["1", "2"]})
    p["editorial"].update({
        "titular": "Jornada marcada por el empleo y la Fed",
        "bajada": "Dos citas que mueven al dólar",
        "lectura": "El mercado mira el empleo en la mañana y las minutas en la tarde.",
        "explicaciones": {"1": "Cuántas personas pidieron seguro de cesantía.", "2": "El acta de la última reunión de la Fed."},
    })
    return p


def dato(dir_pedido: Path) -> dict:
    datos = {
        "chip": "DATO MACRO · EE.UU.", "rotulo_referencia": "Resultado", "referencia": "197K",
        "edicion": "08/10/2026 · 09:39 hrs Chile", "modo": "resultado",
        "resumen": "Peticiones de subsidio por desempleo: 197K frente a 200K esperado. MEJOR de lo esperado.",
        "eventos": [{"id": "1", "hora": "09:30", "evento": "Peticiones de subsidio por desempleo",
                     "actual": "197K", "esperado": "200K", "anterior": "199K", "veredicto": "MEJOR"}],
        "movimientos": [{"nombre": "USD/CLP", "desde": "951,20", "ahora": "952,10", "lectura": "sube"}],
        "temporalidad": "intradía · marco 1H (dentro de la jornada)",
    }
    p = es.nueva_pieza("dato", {"busqueda": "ultimo"}, datos, {"principal": _imagen(dir_pedido, "dato.png")})
    p["editorial"].update({
        "titular": "Menos despidos de lo esperado",
        "bajada": "El empleo sigue firme y eso sostiene al dólar",
        "que_paso": "Las peticiones bajaron a 197K.",
        "que_significa": "Un mercado laboral firme le da espacio a la Fed para no apurar recortes.",
        "que_no_hacer": "No persigas el primer movimiento: espera que el precio se asiente.",
        "impacto": "• USD/CLP: presión al alza\n• Oro: freno de corto plazo",
    })
    return p


def jornada(dir_pedido: Path) -> dict:
    activos = [{"ticker": "USDCLP", "nombre": "Dólar / Peso Chileno", "precio": "951,20", "soporte": "945,00",
                "resistencia": "958,40", "direccion": "Bajista", "pie_imagen": "USD/CLP diario"}]
    datos = {
        "chip": "INFORME DE APERTURA", "rotulo_referencia": "Activos cubiertos", "referencia": "1",
        "edicion": "08/10/2026 · 09:39 hrs Chile", "momento": "apertura", "activos": activos,
        "curva": [["2 años", "3,61 %", "+2 pb", "-5 pb"]],
    }
    p = es.nueva_pieza("jornada", {"momento": "apertura"}, datos, {"USDCLP": _imagen(dir_pedido, "usdclp.png")},
                       extra_campos={"por_activo": ["USDCLP"]})
    p["editorial"].update({
        "titular": "Apertura con el dólar a la defensiva",
        "bajada": "El peso gana terreno con el cobre firme",
        "lectura": "El día parte con el dólar global débil.",
        "por_activo": {"USDCLP": "Bajo 958,40 el sesgo es vendedor."},
        "que_no_hacer": "No operes en los 15 minutos previos a un dato fuerte.",
    })
    return p


PIEZAS = {"activo": activo, "calendario": calendario, "dato": dato, "jornada": jornada}


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
