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
    "gatillo": "El escenario alcista se activa con un cierre de vela de 1 hora sobre 4.131,00.",
    "invalidacion": "El escenario se anula bajo 4.090,10. Es una salida por volatilidad.",
    "recorrido": "Recorrido de referencia: 1,5 veces la volatilidad típica de una hora, unos 12,00.",
    "estadistica": "Desde el 2025-01-27, esta condición se dio 313 veces en Oro.",
    "estado": "Armado: el precio todavía no cruza el gatillo.",
    "niveles": {"gatillo": 4131.0, "invalidacion": 4090.1, "recorrido": 12.0, "vela": "2026-10-08 09:00:00"},
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
