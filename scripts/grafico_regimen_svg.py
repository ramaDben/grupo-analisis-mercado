#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Dibuja, con datos reales, el gráfico de un episodio de régimen del manual.

**Por qué se genera y no se dibuja a mano.** El manual enseña los cinco climas
con sus umbrales y el miembro necesita ver cuándo pasó cada uno. Un gráfico con
la serie escrita a mano tendría aspecto institucional y números que nadie midió,
que es el defecto de `generar_graficos_drivers.py` y lo que prohíbe la regla de
precios del proyecto. Acá cada punto sale de la misma serie que alimenta al
motor, y los episodios salen de `scripts/regimenes_historicos.py`, que corre el
clasificador del motor sobre la historia.

**Dos líneas con su propia escala, no un índice base 100.** El driver y el
activo se miden en unidades distintas (dólares por libra, dólares por onza,
puntos porcentuales), así que cada línea se escala a su propio máximo y mínimo
de la ventana y **lleva anotado su valor real en las dos puntas**. Lo que el
lector tiene que comparar es la FORMA, y un eje común los aplastaría; un índice
base 100 escondería el nivel, que en una tasa es justamente el dato.

**La elección del episodio es editorial; los números, medidos.** Cada clima
tiene decenas de episodios y se elige uno por criterio de enseñanza (reciente,
con datos de los activos y con el movimiento claro). Esa elección está declarada
en `EPISODIOS` con su motivo. Ninguna cifra se escribe acá.

Uso:
    uv run python scripts/grafico_regimen_svg.py                  # imprime el bloque
    uv run python scripts/grafico_regimen_svg.py --escribir       # lo inserta en el manual
"""

from __future__ import annotations

import argparse
import json
import sys
from bisect import bisect_left, bisect_right
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURVA_HIST = RAIZ / "data central" / "DATA USA" / "raw" / "curva_fred_historico.json"
COMM_HIST = RAIZ / "data central" / "DATA ORO Y COMMODITIES" / "raw" / "commodities_historico.json"
OHLC = RAIZ / "data central" / "DATA PRECIOS OHLC"
MANUAL = RAIZ / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md"
EPISODIOS_JSON = RAIZ / "data" / "regimenes_historicos.json"

MARCA_INICIO = "<!-- INICIO graficos-regimenes (generado por scripts/grafico_regimen_svg.py) -->"
MARCA_FIN = "<!-- FIN graficos-regimenes -->"

ACENTO = "#50C0A8"
SUBE = "#10B981"
BAJA = "#E84040"
TINTA = "#0B1916"
GRIS = "#64748B"
TRAMA = "#E2E8F0"

# Un episodio por clima. El criterio de elección va escrito porque es editorial:
# reciente (para que el lector lo reconozca), con datos del activo que ilustra, y
# con el movimiento del clima visible en las dos líneas.
EPISODIOS = [
    {
        "regimen": "R3_ESTANFLACION_SHOCK",
        "clima": "Tormenta",
        "emoji": "🌪️",
        "inicio": "2022-06-01",
        "driver": ("PETROLEO_WTI", "Petróleo WTI", "US$/barril"),
        "activo": ("XAUUSD", "Oro", "US$/onza"),
        "motivo": "el caso de manual: el crudo en rally con las tasas subiendo",
    },
    {
        "regimen": "R1_SHOCK_INFLACIONARIO",
        "clima": "Inflación",
        "emoji": "🛒",
        "inicio": "2022-10-14",
        "driver": ("T10YIE", "Inflación esperada a 10 años", "%"),
        "activo": ("XAUUSD", "Oro", "US$/onza"),
        "motivo": "es el clima que explica por qué se compra Oro con la inflación subiendo",
    },
    {
        "regimen": "R4_RECESION_VUELO_CALIDAD",
        "clima": "Recesión",
        "emoji": "📉",
        "inicio": "2024-07-17",
        "driver": ("COBRE_COMEX", "Cobre", "US$/libra"),
        "activo": ("US100", "Nasdaq 100", "puntos"),
        "motivo": "el cobre cayendo con la bolsa detrás, y con datos de los cuatro activos",
    },
    {
        "regimen": "R2_GOLDILOCKS_EXPANSION",
        "clima": "Día bueno",
        "emoji": "☀️",
        "inicio": "2025-12-19",
        "driver": ("COBRE_COMEX", "Cobre", "US$/libra"),
        "activo": ("USDCLP", "USD/CLP", "pesos"),
        "motivo": "muestra la relación inversa del cobre con el dólar en Chile",
    },
    {
        "regimen": "R0_CALMA_RANGO",
        "clima": "Calma",
        "emoji": "🏖️",
        "inicio": "2024-11-11",
        "driver": ("COBRE_COMEX", "Cobre", "US$/libra"),
        "activo": ("USDCLP", "USD/CLP", "pesos"),
        "motivo": "19 días hábiles y el activo termina donde empezó: el clima más frecuente",
    },
]

VENTANA_CONTEXTO = 12   # días hábiles a cada lado del episodio


MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
MESES_CORTOS = ("ene", "feb", "mar", "abr", "may", "jun",
                "jul", "ago", "sep", "oct", "nov", "dic")


def _fecha_larga(iso: str) -> str:
    """`2022-06-01` -> `1 de junio de 2022`.

    En ISO la fuente del manual dibuja el guion como un trazo largo, asi que
    `2022-06-01` se lee como si llevara guiones de inciso, que es justo lo que el
    proyecto prohibe en texto de cliente. Y en castellano la fecha larga se lee
    sin traducir mentalmente.
    """
    a, m, d = iso.split("-")
    return f"{int(d)} de {MESES[int(m) - 1]} de {a}"


def _rango_fechas(inicio: str, fin: str) -> str:
    """`del 1 al 10 de junio de 2022`, sin repetir mes ni ano cuando coinciden."""
    a1, m1, d1 = inicio.split("-")
    a2, m2, d2 = fin.split("-")
    if a1 == a2 and m1 == m2:
        return f"del {int(d1)} al {int(d2)} de {MESES[int(m1) - 1]} de {a1}"
    if a1 == a2:
        return (f"del {int(d1)} de {MESES[int(m1) - 1]} al "
                f"{int(d2)} de {MESES[int(m2) - 1]} de {a1}")
    return f"del {_fecha_larga(inicio)} al {_fecha_larga(fin)}"


def _fecha_corta(iso: str) -> str:
    """`2022-06-01` -> `1 jun 2022`, para el eje de tiempo del grafico."""
    a, m, d = iso.split("-")
    return f"{int(d)} {MESES_CORTOS[int(m) - 1]} {a}"


def _serie(nombre: str) -> list[tuple[str, float]]:
    """Serie cronológica del driver o del activo, según de dónde viva."""
    if nombre in ("T10YIE", "DFII10", "DGS10", "DGS2"):
        datos = json.loads(CURVA_HIST.read_text(encoding="utf-8"))["series"]
        hist = datos[nombre]["historico"]
    elif nombre in ("COBRE_COMEX", "PETROLEO_WTI", "PETROLEO_BRENT"):
        datos = json.loads(COMM_HIST.read_text(encoding="utf-8"))["commodities"]
        hist = datos[nombre]["historico"]
    else:
        filas = json.loads((OHLC / f"{nombre}_D1.json").read_text(encoding="utf-8"))["rows"]
        return [(f["time"][:10], float(f["close"])) for f in filas]
    return sorted((f, float(v)) for f, v in hist.items() if v is not None)


def _recorte(serie: list[tuple[str, float]], desde: str, hasta: str) -> list[tuple[str, float]]:
    fechas = [f for f, _ in serie]
    return serie[bisect_left(fechas, desde):bisect_right(fechas, hasta)]


def _decimales(nombre: str) -> int:
    return {"USDCLP": 2, "XAUUSD": 2, "US100": 2, "COBRE_COMEX": 4, "PETROLEO_WTI": 2}.get(nombre, 2)


def _numero(valor: float, dec: int) -> str:
    """Notación chilena: punto de miles, coma decimal."""
    entero, _, frac = f"{valor:,.{dec}f}".partition(".")
    entero = entero.replace(",", ".")
    return f"{entero},{frac}" if frac else entero


def _ruta(puntos: list[tuple[str, float]], x0: float, x1: float, y0: float, y1: float) -> str:
    """Traza la serie escalada a su propio máximo y mínimo de la ventana."""
    valores = [v for _, v in puntos]
    lo, hi = min(valores), max(valores)
    rango = (hi - lo) or 1.0
    n = len(puntos) - 1 or 1
    trozos = []
    for i, (_, v) in enumerate(puntos):
        x = x0 + (x1 - x0) * i / n
        y = y1 - (y1 - y0) * (v - lo) / rango
        trozos.append(f"{'M' if i == 0 else 'L'} {x:.1f} {y:.1f}")
    return " ".join(trozos)


def _indice_de_fecha(puntos: list[tuple[str, float]], fecha: str) -> int:
    return bisect_left([f for f, _ in puntos], fecha)


def hitos(ep: dict, episodio: dict) -> dict:
    """Valores medidos del episodio que la guía de lectura necesita nombrar.

    **Existe por un error concreto que conviene no repetir.** La revisión
    pedagógica del 2026-09-07 propuso guías de lectura excelentes en estructura
    y con dos precios inventados: leyó las etiquetas de los EXTREMOS del gráfico,
    que son de la ventana de contexto, y las escribió como si fueran del
    episodio. Así el crudo "arrancaba en 110" cuando el episodio abre en 115,26,
    y el Oro tenía un "soporte en 1.653" que es el borde izquierdo del dibujo y
    no el mínimo del tramo, que fue 1.625,62.

    De ahí que la guía no lleve ningún número escrito a mano: los toma de acá, y
    acá salen de la serie recortada al episodio.
    """
    driver_id = ep["driver"][0]
    activo_id = ep["activo"][0]
    inicio, fin = episodio["inicio"], episodio["fin"]

    def tramo(nombre: str, dec: int) -> dict:
        puntos = _recorte(_serie(nombre), inicio, fin)
        if not puntos:
            raise SystemExit(f"Sin datos de {nombre} en {inicio}..{fin}")
        valores = [v for _, v in puntos]
        return {
            "abre": _numero(valores[0], dec),
            "cierra": _numero(valores[-1], dec),
            "minimo": _numero(min(valores), dec),
            "maximo": _numero(max(valores), dec),
        }

    return {
        "driver": tramo(driver_id, _decimales(driver_id)),
        "activo": tramo(activo_id, _decimales(activo_id)),
        "dias": episodio["dias"],
        "unidad_driver": ep["driver"][2],
        "unidad_activo": ep["activo"][2],
    }


def guia_de_lectura(ep: dict, episodio: dict, h: dict) -> list[str]:
    """Los tres bloques que enseñan a leer el gráfico, uno por clima.

    La prosa es editorial y se escribe una vez por clima; las cifras se
    interpolan desde `hitos`. Estructura tomada de la revisión pedagógica: qué
    mirar y en qué orden, la conclusión en una frase que el lector pueda
    repetir, y qué significa la franja.
    """
    d, a = h["driver"], h["activo"]
    dd = episodio["deltas_inicio"]
    va = episodio["variacion_activos_pct"]
    ud, ua = h["unidad_driver"], h["unidad_activo"]

    if ep["regimen"] == "R3_ESTANFLACION_SHOCK":
        pasos = [
            f"**1. Empieza por el tramo verde a la izquierda de la franja.** Ahí está el "
            f"gatillo: en los cinco días previos el petróleo subió {_pct(dd.get('oil_signed_pct_5d'))} "
            f"y el bono a 10 años sumó {_bps(dd.get('dgs10_diff_5d'))}. Las dos cosas juntas son "
            f"lo que define este clima, y los umbrales están en el Anexo A2.",
            f"**2. Ahora la franja.** El crudo entra en {d['abre']} {ud} y sale en "
            f"{d['cierra']} {ud}, tocando {d['maximo']} en el camino. El shock no se agotó "
            f"al confirmarse el clima: siguió.",
            f"**3. Recién ahora mira la línea gris de abajo, el Oro.** Va de {a['abre']} a "
            f"{a['cierra']} {ua}. Fíjate en lo raro: las tasas de los bonos subieron, y por el "
            f"Módulo 2.2 eso debería castigar al Oro. No lo castigó.",
        ]
        conclusion = (
            "En Tormenta el Oro aguanta aunque las tasas suban, porque lo que lo mueve en ese "
            "momento no es el costo de oportunidad sino la búsqueda de refugio. Por eso el "
            "método prohíbe apostar a su baja en este clima."
        )
    elif ep["regimen"] == "R1_SHOCK_INFLACIONARIO":
        pasos = [
            f"**1. Mira la línea verde antes de la franja.** Es la inflación que el mercado "
            f"descuenta para los próximos 10 años, leída de los bonos. En los cinco días previos "
            f"subió {_bps(dd.get('breakeven_diff_5d'))}. Y en los mismos días la tasa real se "
            f"movió {_bps(dd.get('tips10y_diff_5d'))}: prácticamente nada.",
            "**2. Esa diferencia es todo el caso.** Los precios esperados subieron y lo que paga "
            "el bono descontada la inflación no las siguió. Es exactamente la rama verde del "
            "Módulo 2.2: la Reserva Federal todavía no había respondido.",
            f"**3. Ahora la línea gris, el Oro.** Entra en {a['abre']} y sale en {a['cierra']} "
            f"{ua}, con un mínimo de {a['minimo']} dentro del tramo. Venía de meses de caídas y "
            f"acá se dio vuelta.",
        ]
        conclusion = (
            "El Oro no sube porque suba la inflación: sube cuando la inflación esperada le gana "
            "a la tasa real. Si la Reserva Federal hubiera subido su tasa más rápido, este mismo "
            "gráfico se vería al revés."
        )
    elif ep["regimen"] == "R4_RECESION_VUELO_CALIDAD":
        pasos = [
            f"**1. El gatillo está en el cobre, la línea verde antes de la franja.** Cayó "
            f"{_pct(dd.get('copper_pct_5d'))} en cinco días. El cobre es el termómetro de la "
            f"industria del mundo: si las fábricas compran menos cobre, es porque esperan "
            f"producir menos.",
            f"**2. Dentro de la franja el cobre sigue.** De {d['abre']} a {d['cierra']} {ud}. "
            f"No fue un día raro: fueron {h['dias']} días hábiles en la misma dirección.",
            f"**3. Ahora la línea gris, el Nasdaq 100.** De {a['abre']} a {a['cierra']} {ua}, "
            f"un {_pct(va.get('US100'))}. La bolsa está descontando las mismas ganancias más "
            f"chicas que anticipa el cobre.",
        ]
        conclusion = (
            f"En Recesión el cobre avisa antes que la bolsa, y a Chile le llega por el bolsillo: "
            f"si el mundo compra menos cobre, entran menos dólares al país y el dólar sube. En "
            f"estos días el USD/CLP hizo {_pct(va.get('USDCLP'))}."
        )
    elif ep["regimen"] == "R2_GOLDILOCKS_EXPANSION":
        pasos = [
            f"**1. El gatillo, en el cobre antes de la franja.** Subió "
            f"{_pct(dd.get('copper_pct_5d'))} en cinco días, y esta vez con las tasas quietas: "
            f"el bono a 10 años se movió {_bps(dd.get('dgs10_diff_5d'))}. Esa quietud es la "
            f"condición que separa este clima de los dos anteriores.",
            f"**2. Fíjate en que las dos líneas van al revés.** El cobre va de {d['abre']} a "
            f"{d['cierra']} {ud} mientras el USD/CLP baja de {a['abre']} a {a['cierra']} {ua}. "
            f"No es casualidad ni coincidencia: es el mismo hecho visto de dos lados.",
            "**3. La cadena, en una línea.** El cobre sube, Chile lo exporta, entran más "
            "dólares al país, y con más dólares ofrecidos el dólar vale menos pesos. Es la "
            "verdulería del Módulo 2.4.",
        ]
        conclusion = (
            "Cuando el cobre sube con las tasas tranquilas, el peso chileno se fortalece y el "
            "dólar baja. Es el único clima donde el sesgo del USD/CLP es a la baja."
        )
    else:  # R0_CALMA_RANGO
        pasos = [
            f"**1. Acá no hay gatillo que buscar, y eso es lo que hay que ver.** A la Calma no "
            f"la activa ningún umbral: es donde queda el mercado cuando ningún otro clima "
            f"califica. El cobre venía cayendo {_pct(dd.get('copper_pct_5d'))}, pero la curva de "
            f"bonos no acompañó, así que no llegó a ser Recesión.",
            f"**2. Mira la línea gris dentro de la franja.** El USD/CLP entra en {a['abre']} y "
            f"sale en {a['cierra']} {ua}, un {_pct(va.get('USDCLP'))} en {h['dias']} días "
            f"hábiles. Entremedio se movió entre {a['minimo']} y {a['maximo']}.",
            "**3. Eso es un rango, no una tendencia.** El precio va y vuelve entre dos niveles. "
            "Perseguir una ruptura acá es comprar arriba justo antes de que el precio vuelva "
            "al medio, y por eso este clima lo prohíbe.",
        ]
        conclusion = (
            "La Calma es el clima más frecuente: son 6 de cada 10 días. No es un clima de espera "
            "sin nada que hacer, es el único donde se opera el rebote entre soporte y "
            "resistencia, que es el setup del Módulo 5.3."
        )

    lineas = ["**Cómo leer este gráfico, en orden:**", ""]
    for paso in pasos:           # renglón en blanco entre pasos: sin él markdown
        lineas += [paso, ""]     # los pega en un solo párrafo corrido
    lineas += [
        "",
        f"**La conclusión, en una frase.** {conclusion}",
        "",
        f"**Qué es la franja sombreada.** Son los {h['dias']} días hábiles en que el clima "
        f"estuvo confirmado por la regla de los dos días. Lo que pasa **antes** de la franja es "
        f"lo que lo activó; lo que pasa **dentro** es lo que tenías permitido y prohibido operar.",
        "",
    ]
    return lineas


def dibujar(ep: dict, episodio: dict) -> str:
    """Devuelve el SVG del episodio, con las dos series y la franja del clima."""
    driver_id, driver_nom, driver_uni = ep["driver"]
    activo_id, activo_nom, activo_uni = ep["activo"]
    inicio, fin = episodio["inicio"], episodio["fin"]

    eje = [f for f, _ in _serie("COBRE_COMEX")]
    i_ini, i_fin = bisect_left(eje, inicio), bisect_right(eje, fin)
    desde = eje[max(0, i_ini - VENTANA_CONTEXTO)]
    hasta = eje[min(len(eje) - 1, i_fin + VENTANA_CONTEXTO)]

    serie_driver = _recorte(_serie(driver_id), desde, hasta)
    serie_activo = _recorte(_serie(activo_id), desde, hasta)
    if len(serie_driver) < 3 or len(serie_activo) < 3:
        raise SystemExit(f"Sin datos suficientes para {ep['regimen']} en {inicio}")

    X0, X1 = 148.0, 610.0
    ALTO = 200

    # la franja del clima, ubicada sobre el eje del driver
    n = len(serie_driver) - 1 or 1
    fx = lambda i: X0 + (X1 - X0) * i / n  # noqa: E731
    banda_x0 = fx(_indice_de_fecha(serie_driver, inicio))
    banda_x1 = fx(min(_indice_de_fecha(serie_driver, fin), n))

    dec_d, dec_a = _decimales(driver_id), _decimales(activo_id)
    d_ini, d_fin = serie_driver[0][1], serie_driver[-1][1]
    a_ini, a_fin = serie_activo[0][1], serie_activo[-1][1]

    partes = [
        f'<svg viewBox="0 0 720 {ALTO}" width="100%" height="{ALTO}" xmlns="http://www.w3.org/2000/svg" '
        f'style="background:#FFFFFF; border:1px solid {TRAMA}; border-radius:8px; '
        "font-family:'Plus Jakarta Sans', sans-serif;\">",
        f'<rect x="{banda_x0:.1f}" y="42" width="{max(banda_x1 - banda_x0, 2):.1f}" height="118" '
        f'fill="{ACENTO}" opacity="0.12"/>',
        f'<text x="{(banda_x0 + banda_x1) / 2:.1f}" y="36" font-family="\'Goldman\', sans-serif" '
        f'font-size="9" font-weight="700" fill="#065F46" text-anchor="middle">'
        f'CLIMA {ep["clima"].upper()}: {episodio["dias"]} DÍAS</text>',
        f'<path d="{_ruta(serie_driver, X0, X1, 52, 100)}" stroke="{ACENTO}" stroke-width="2.5" fill="none"/>',
        f'<path d="{_ruta(serie_activo, X0, X1, 108, 156)}" stroke="{GRIS}" stroke-width="2.5" fill="none"/>',
        # rotulos de cada linea, con su valor real en las dos puntas
        f'<text x="{X0 - 10:.0f}" y="70" font-size="9.5" font-weight="700" fill="#065F46" '
        f'text-anchor="end">{driver_nom}</text>',
        f'<text x="{X0 - 10:.0f}" y="83" font-size="9" font-weight="600" fill="{GRIS}" '
        f'text-anchor="end">{_numero(d_ini, dec_d)} {driver_uni}</text>',
        f'<text x="{X1 + 10:.0f}" y="78" font-size="9" font-weight="700" fill="#065F46" '
        f'text-anchor="start">{_numero(d_fin, dec_d)} {driver_uni}</text>',
        f'<text x="{X0 - 10:.0f}" y="126" font-size="9.5" font-weight="700" fill="{TINTA}" '
        f'text-anchor="end">{activo_nom}</text>',
        f'<text x="{X0 - 10:.0f}" y="139" font-size="9" font-weight="600" fill="{GRIS}" '
        f'text-anchor="end">{_numero(a_ini, dec_a)} {activo_uni}</text>',
        f'<text x="{X1 + 10:.0f}" y="134" font-size="9" font-weight="700" fill="{TINTA}" '
        f'text-anchor="start">{_numero(a_fin, dec_a)} {activo_uni}</text>',
        # eje de tiempo
        f'<line x1="{X0:.0f}" y1="168" x2="{X1:.0f}" y2="168" stroke="{TRAMA}" stroke-width="1"/>',
        f'<text x="{X0:.0f}" y="182" font-size="8.5" font-weight="600" fill="{GRIS}">{_fecha_corta(desde)}</text>',
        f'<text x="{X1:.0f}" y="182" font-size="8.5" font-weight="600" fill="{GRIS}" '
        f'text-anchor="end">{_fecha_corta(hasta)}</text>',
        f'<text x="{X0 - 10:.0f}" y="26" font-family="\'Goldman\', sans-serif" font-size="10" '
        f'font-weight="700" fill="{TINTA}" text-anchor="end">{ep["emoji"]} {ep["clima"]}</text>',
        "</svg>",
    ]
    return "\n".join(partes)


def _pct(valor: float | None) -> str:
    if valor is None:
        return "sin dato"
    return f"{valor:+.2f} %".replace(".", ",")


def _bps(pp: float | None) -> str:
    if pp is None:
        return "sin dato"
    return f"{pp * 100:+.0f} pb".replace(".", ",")


def bloque_markdown() -> str:
    """Arma la sección completa del manual: texto, gráfico y cifras medidas."""
    datos = json.loads(EPISODIOS_JSON.read_text(encoding="utf-8"))
    por_clave = {(e["regimen"], e["inicio"]): e for e in datos["episodios"]}

    lineas = [
        MARCA_INICIO,
        "",
        "## 3.5 · Cuándo pasó cada clima, de verdad",
        "",
        "Los cinco climas no son categorías teóricas. Se pueden fechar, porque el mismo "
        "clasificador que corre hoy se puede aplicar a la historia. Abajo hay un episodio real "
        "de cada uno, con las cifras que lo activaron y lo que hicieron los activos en esos días.",
        "",
        "**Cómo leer los gráficos**: cada uno tiene dos líneas, el driver arriba en verde y el "
        "activo abajo en gris, y la franja sombreada marca los días en que el clima estuvo "
        "confirmado. Cada línea tiene su propia escala y lleva su valor real en las dos puntas: "
        "lo que se compara es la forma, no la altura.",
        "",
        f"> **De dónde salen estos números.** El clasificador del motor se corrió sobre "
        f"{datos['dias_clasificados']:,} días hábiles".replace(",", "."),
        f"> (de {_fecha_larga(datos['generado_desde'])} a {_fecha_larga(datos['generado_hasta'])}), con las mismas series que "
        f"alimentan la clasificación de hoy. El límite es la tasa real de EE.UU., que se publica "
        f"desde 2003. Ninguna cifra de esta sección está escrita a mano.",
        "",
    ]

    for ep in EPISODIOS:
        clave = (ep["regimen"], ep["inicio"])
        if clave not in por_clave:
            raise SystemExit(f"No hay episodio {clave} en {EPISODIOS_JSON.name}")
        episodio = por_clave[clave]
        d = episodio["deltas_inicio"]
        v = episodio["variacion_activos_pct"]
        _, driver_nom, _ = ep["driver"]

        lineas += [
            f"### {ep['emoji']} {ep['clima']} · "
            f"{_rango_fechas(episodio['inicio'], episodio['fin'])}",
            "",
            '<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">',
            dibujar(ep, episodio),
            "</div>",
            "",
        ]
        lineas += guia_de_lectura(ep, episodio, hitos(ep, episodio))
        # El bloque de cifras va DESPUÉS de la guía y comprimido: la guía ya
        # nombra las que enseñan algo, y esto queda como referencia para quien
        # quiera verificar la clasificación por su cuenta.
        lineas += [
            # A la Calma no la activa ningún umbral, así que rotular sus cifras
            # "lo que lo activó" las haría leer como el gatillo que no son.
            (
                "**Los drivers de esos días** (variación en los 5 previos al primero): "
                if ep["regimen"] == "R0_CALMA_RANGO"
                else "**Lo que lo activó** (variación en los 5 días previos al primero): "
            )
            + f"cobre {_pct(d.get('copper_pct_5d'))}, petróleo {_pct(d.get('oil_signed_pct_5d'))}, "
            f"bono a 10 años {_bps(d.get('dgs10_diff_5d'))}, "
            f"tasa real {_bps(d.get('tips10y_diff_5d'))}, "
            f"inflación esperada {_bps(d.get('breakeven_diff_5d'))}.",
            "",
            f"**Los activos en esos {episodio['dias']} días hábiles**: "
            + ", ".join(
                f"{rotulo} {_pct(v[clave])}"
                for clave, rotulo in (
                    ("XAUUSD", "Oro"), ("USDCLP", "USD/CLP"),
                    ("WTI", "WTI"), ("US100", "Nasdaq 100"),
                )
                if v.get(clave) is not None
            )
            + ".",
            "",
        ]

    lineas += [
        "> [!NOTE]",
        "> **Un episodio no es una promesa.** Estos son casos de un clima, no el "
        "comportamiento garantizado de todos. Sirven para reconocer la forma del escenario, "
        "no para esperar el mismo porcentaje. El clima te dice qué dirección tienes "
        "permitida; el tamaño del movimiento no lo decide nadie.",
        "",
        MARCA_FIN,
    ]
    return "\n".join(lineas)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--escribir", action="store_true", help="inserta el bloque en el manual")
    args = ap.parse_args()

    bloque = bloque_markdown()
    if not args.escribir:
        print(bloque)
        return 0

    texto = MANUAL.read_text(encoding="utf-8")
    if MARCA_INICIO in texto and MARCA_FIN in texto:
        antes = texto[: texto.index(MARCA_INICIO)]
        despues = texto[texto.index(MARCA_FIN) + len(MARCA_FIN):]
        MANUAL.write_text(antes + bloque + despues, encoding="utf-8")
        print(f"Sección regenerada en {MANUAL.name}")
        return 0

    # primera inserción: al final del Módulo 3, antes del separador del Módulo 4
    ancla = "\n---\n\n# 🎫 MÓDULO 4 · Tu ficha de operación"
    if ancla not in texto:
        raise SystemExit("No encontré dónde insertar: revisá el ancla del Módulo 4")
    MANUAL.write_text(texto.replace(ancla, "\n" + bloque + ancla, 1), encoding="utf-8")
    print(f"Sección insertada en {MANUAL.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
