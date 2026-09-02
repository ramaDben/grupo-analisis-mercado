"""Generador de la geometría de los gráficos de las Stories.

Traduce el recorrido real de un precio (una serie de valores más los hitos de la
operación) al SVG que la plantilla `templates/stories/alerta.html` inyecta en su
token `{{grafico}}`. Es un paso **previo** al render: enriquece el payload y lo deja
listo para `story_render.py`.

    cat alerta.json \
      | uv run python scripts/story_grafico.py \
      | uv run python scripts/story_render.py --template templates/stories/alerta.html \
          --out data/stories/... --formato horizontal

Reparto de responsabilidades (mismo criterio que el resto del motor de Stories): acá
solo se calculan **coordenadas**; el color, el grosor y la tipografía viven en las
clases `.g-*` del snapshot. Por eso el SVG que se emite no lleva ni un atributo de
estilo -- si el gráfico se ve mal, se corrige en la plantilla, no acá.

Entrada (JSON por stdin): el payload de la Story más una clave `recorrido`:

    {
      "titular": "...",                    <- resto del payload, se pasa tal cual
      "recorrido": {
        "serie": [163.62, 163.80, ...],    <- precios, equiespaciados en X
        "marcadores": [
          {"indice": 6, "precio": 163.444, "clase": "origen", "rol": "ENTRADA"}
        ]
      }
    }

Salida (JSON por stdout): el mismo payload con `grafico` resuelto y `recorrido` fuera
(la plantilla no lo referencia y `build_context` lo ignoraría de todos modos).

`clase` corresponde a los estados que el snapshot sabe pintar -- `origen`,
`cumplido`, `meta`, `actual` -- y `rol` es opcional: se omite donde dos etiquetas
consecutivas quedarían demasiado juntas (el color del punto ya comunica el estado).
"""
from __future__ import annotations

import json
import sys
from typing import Any

# ---- Lienzo del SVG -----------------------------------------------------------
# El viewBox va al ratio del contenedor real (~1.10 en vertical, ~1.16 en horizontal).
# Un viewBox más ancho que su caja hace que `preserveAspectRatio` escale por el ancho
# y deje bandas vacías arriba y abajo: espacio que no comunica nada.
# Dos lienzos, porque el gráfico de línea vive en cajas de formas muy distintas:
# en `operacion` ocupa una columna alta y angosta, y en `alerta` y `recomendacion`
# una franja apaisada. `preserveAspectRatio` encoge el SVG hasta que cabe, así que
# un lienzo alto dentro de una caja ancha se convierte en una estampilla al
# centro — pasó en el primer render de las dos plantillas nuevas.
# El payload elige con `recorrido.lienzo`; por defecto, el alto.
LIENZOS = {
    "alto":  dict(vb_w=520, vb_h=400, x0=175, x1=500, y0=30, y1=370, label_x=160, guia_x=168),
    # 900x230 y no 900x300: la franja bajo la tarjeta mide ~950x210, y con un
    # lienzo 3:1 el SVG se encogia a media columna dejando bandas laterales.
    "ancho": dict(vb_w=900, vb_h=230, x0=190, x1=880, y0=18, y1=205, label_x=174, guia_x=182),
    # 900x460 para la tarjeta lateral completa de dato_macro.html
    "macro": dict(vb_w=900, vb_h=460, x0=180, x1=870, y0=40, y1=410, label_x=164, guia_x=172),
}

# Cómo se comporta el SVG dentro de su caja. `meet` conserva la proporción y deja
# bandas; `llenar` estira. Se estira sólo cuando el gráfico es ESCENARIO —fondo a
# sangre de la pieza—, nunca cuando es una tarjeta con ejes que se leen: ahí
# deformar cambiaría la pendiente que el cliente está midiendo.
AJUSTES = {"meet": "xMidYMid meet", "llenar": "none"}

_L = LIENZOS["alto"]
VB_W, VB_H = _L["vb_w"], _L["vb_h"]
PLOT_X0, PLOT_X1 = _L["x0"], _L["x1"]
PLOT_Y0, PLOT_Y1 = _L["y0"], _L["y1"]
LABEL_X = _L["label_x"]
GUIA_X = _L["guia_x"]
MARGEN_ESCALA = 0.05   # aire vertical sobre el máximo y bajo el mínimo de la serie


class GraficoError(RuntimeError):
    """Error accionable del generador (nunca un traceback críptico)."""


def resolver_escala(serie: list[float], niveles: list[float] | None = None) -> tuple[float, float]:
    """Devuelve `(precio_max, precio_min)` del eje vertical.

    Los NIVELES entran en la escala junto con la serie, pero con un límite.
    Si un TP o SL está excesivamente lejos (operaciones 5:1 o posicionales),
    estirar el gráfico para que quepa aplasta la serie y hace que los precios
    cercanos colisionen. Acotamos la expansión a un máximo proporcional.
    """
    if not serie:
        raise GraficoError("recorrido.serie está vacío: no hay nada que graficar.")
    
    alto_s, bajo_s = max(serie), min(serie)
    rango_s = alto_s - bajo_s if alto_s > bajo_s else 0.1
    
    lim_alto = alto_s + (rango_s * 1.5)
    lim_bajo = bajo_s - (rango_s * 1.5)

    valores = list(serie)
    for n in (niveles or []):
        valores.append(max(lim_bajo, min(lim_alto, n)))
        
    alto, bajo = max(valores), min(valores)
    rango = alto - bajo
    margen = rango * MARGEN_ESCALA if rango else 0.1
    return alto + margen, bajo - margen


# Alto que ocupa el bloque de texto de un marcador, en unidades del viewBox: el
# precio mas su rol debajo, o solo el precio. Sale de los offsets +6 y +21 con
# que se dibujan ambas lineas, mas holgura para que no se toquen.
_ALTO_CON_ROL = 34.0
_ALTO_SIN_ROL = 19.0


def _separar_etiquetas(marcadores: list[dict], coord_y) -> dict[int, float]:
    """Y de cada bloque de texto, ya separados para que no se pisen entre si.

    Todas las etiquetas se dibujan en la misma X -pegadas al eje- asi que dos
    marcadores con precios parecidos caen en la misma altura y sus textos se
    superponen hasta volverse ilegibles. Paso en la primera prueba real: la
    entrada en 1,15038 y el precio actual en 1,15022 -16 puntos de diferencia
    sobre un rango de 1.100- salieron uno encima del otro.

    El punto y su guia horizontal se quedan SIEMPRE en la altura verdadera del
    precio; lo unico que se corre es el texto. Mover el punto seria mentir sobre
    donde ocurrio el hito.

    Se recorre de arriba hacia abajo empujando cada bloque lo justo para que no
    invada al anterior. Con dos o tres marcadores -el caso real de una operacion:
    entrada, actual y objetivo- el desplazamiento es de pocos pixeles y la
    asociacion entre texto y punto sigue siendo obvia por la guia.
    """
    orden = sorted(range(len(marcadores)), key=lambda i: coord_y(marcadores[i]["precio"]))
    y_texto: dict[int, float] = {}
    libre = float("-inf")
    for i in orden:
        y = max(coord_y(marcadores[i]["precio"]), libre)
        y_texto[i] = y
        libre = y + (_ALTO_CON_ROL if marcadores[i].get("rol") else _ALTO_SIN_ROL)
    return y_texto


def construir_svg(
    serie: list[float],
    marcadores: list[dict[str, Any]],
    niveles: list[dict[str, Any]] | None = None,
    lienzo: str = "alto",
    ajuste: str = "meet",
) -> str:
    """Arma el SVG del recorrido: área, línea, guías, puntos y etiquetas.

    La X de la serie es equiespaciada entre `x_ini` y `x_fin`; la X de cada
    marcador sale de su `indice` en la serie y su Y del `precio` propio (que puede
    diferir del punto de la serie: el hito real de la operación manda sobre el
    muestreo del gráfico).
    """
    niveles = niveles or []
    g = LIENZOS.get(lienzo)
    if g is None:
        raise GraficoError(
            f"lienzo '{lienzo}' desconocido; usa {sorted(LIENZOS)}."
        )

    aspecto = AJUSTES.get(ajuste)
    if aspecto is None:
        raise GraficoError(
            f"ajuste '{ajuste}' desconocido; usa {sorted(AJUSTES)}."
        )

    vb_w, vb_h = g["vb_w"], g["vb_h"]
    x_ini, x_fin, y_ini, y_fin = g["x0"], g["x1"], g["y0"], g["y1"]
    label_x, guia_x = g["label_x"], g["guia_x"]

    p_max, p_min = resolver_escala(serie, [float(x["precio"]) for x in niveles])
    n = len(serie)

    def coord_y(precio: float) -> float:
        y = y_ini + (p_max - precio) / (p_max - p_min) * (y_fin - y_ini)
        # Clamp visual a los bordes para que los niveles extremos (ej. TP 5:1) 
        # que fueron acotados en resolver_escala no desaparezcan del viewBox.
        return max(y_ini, min(y_fin, y))

    def coord_x(indice: float) -> float:
        if n == 1:
            return x_ini
        return x_ini + indice / (n - 1) * (x_fin - x_ini)

    pts = [(coord_x(i), coord_y(p)) for i, p in enumerate(serie)]
    trazo = " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    partes = [
        f'<svg viewBox="0 0 {vb_w} {vb_h}" preserveAspectRatio="{aspecto}">',
        '<defs><linearGradient id="gradArea" x1="0" y1="0" x2="0" y2="1">',
        # Sin `stop-color` fijo: el color lo pone `.g-area-alto` / `.g-area-bajo`
        # en el snapshot, igual que el resto del gráfico. Estaba hardcodeado en
        # rosa, así que el área no seguía la dirección de la operación y bajo una
        # línea verde quedaba un relleno rojizo.
        '<stop class="g-area-alto" offset="0%"/>',
        '<stop class="g-area-bajo" offset="100%"/>',
        "</linearGradient></defs>",
        f'<path class="g-area" d="M {pts[0][0]:.1f},{y_fin} L {trazo} '
        f'L {pts[-1][0]:.1f},{y_fin} Z"/>',
    ]

    # Los NIVELES cruzan todo el ancho, a diferencia de la guía de un marcador
    # que solo llega hasta su punto. Es la distinción de fondo: un marcador es un
    # hecho que ocurrió en un momento -la entrada, el precio de ahora-, mientras
    # que un nivel es un precio que vale para toda la ventana -el objetivo, el
    # stop, un soporte-. Dibujar un objetivo como punto sugeriría que el precio
    # ya pasó por ahí.
    for lv in niveles:
        y = coord_y(float(lv["precio"]))
        partes.append(
            f'<line class="g-nivel g-nivel-{lv.get("clase", "nivel")}" '
            f'x1="{x_ini}" y1="{y:.1f}" x2="{x_fin}" y2="{y:.1f}"/>'
        )

    # Las guías se dibujan ANTES de la línea para que nunca la tapen.
    for m in marcadores:
        idx = m["indice"]
        y_val = serie[idx] if (0 <= idx < len(serie) and m.get("clase") == "actual") else m["precio"]
        y = coord_y(y_val)
        x = coord_x(idx)
        partes.append(
            f'<line class="g-guia" x1="{guia_x}" y1="{y:.1f}" x2="{x:.1f}" y2="{y:.1f}"/>'
        )

    partes.append(f'<path class="g-linea" d="M {trazo}"/>')

    # Niveles y marcadores escriben en la MISMA columna de etiquetas, así que la
    # separación vertical los considera juntos. Separarlos por separado dejaría
    # que un nivel y un marcador de precio parecido se pisaran igual.
    etiquetables = list(niveles) + list(marcadores)
    y_etiqueta = _separar_etiquetas(etiquetables, coord_y)

    for j, lv in enumerate(niveles):
        yt = y_etiqueta[j]
        clase = lv.get("clase", "nivel")
        partes.append(
            f'<text class="g-precio g-precio-{clase}" x="{label_x}" y="{yt + 6:.1f}" '
            f'text-anchor="end">{lv["etiqueta"]}</text>'
        )
        if lv.get("rol"):
            partes.append(
                f'<text class="g-rol" x="{label_x}" y="{yt + 21:.1f}" '
                f'text-anchor="end">{lv["rol"]}</text>'
            )

    for i, m in enumerate(marcadores):
        clase = m.get("clase", "actual")
        idx = m["indice"]
        y_val = serie[idx] if (0 <= idx < len(serie) and clase == "actual") else m["precio"]
        x, y = coord_x(idx), coord_y(y_val)
        yt = y_etiqueta[len(niveles) + i]
        if clase == "meta":
            partes.append(f'<circle class="g-halo" cx="{x:.1f}" cy="{y:.1f}" r="11"/>')
        partes.append(
            f'<circle class="g-punto g-punto-{clase}" cx="{x:.1f}" cy="{y:.1f}" r="5.5"/>'
        )
        partes.append(
            f'<text class="g-precio g-precio-{clase}" x="{label_x}" y="{yt + 6:.1f}" '
            f'text-anchor="end">{m["etiqueta"]}</text>'
        )
        if m.get("rol"):
            partes.append(
                f'<text class="g-rol" x="{label_x}" y="{yt + 21:.1f}" '
                f'text-anchor="end">{m["rol"]}</text>'
            )

    partes.append("</svg>")
    return "".join(partes)



# ---- Gráfico de barras (series macro) -----------------------------------------
# Reserva abajo la banda de las etiquetas del eje X, que el gráfico de línea no
# necesita porque su eje horizontal es implícito ("las últimas N velas").
# Lienzo propio: el del grafico de linea (440x400) es alto y angosto porque vive
# en una columna lateral. Las barras ocupan el ancho de la tarjeta, y con
# `preserveAspectRatio` un lienzo vertical dentro de una caja ancha se encoge
# hasta convertirse en una estampilla al centro. Fue lo que paso en el primer
# render.
VB_W_BARRAS, VB_H_BARRAS = 900, 460
PLOT_X0_BARRAS, PLOT_X1_BARRAS = 180, 870
PLOT_Y0_BARRAS = 36
PLOT_Y1_BARRAS = 390
EJE_Y = 432
LABEL_X_BARRAS = 164
ANCHO_BARRA = 0.68   # proporción del paso entre barras; el resto es separación


def resolver_escala_barras(valores: list[float], niveles: list[float]) -> tuple[float, float]:
    """`(max, min)` del eje, incluyendo SIEMPRE el cero.

    Una barra mide desde cero por definición: si el eje arrancara en el mínimo de
    la serie, la altura de cada barra dejaría de ser proporcional a su valor y el
    gráfico mentiría sobre las diferencias. Es el error clásico del eje truncado.
    """
    todos = list(valores) + list(niveles) + [0.0]
    alto, bajo = max(todos), min(todos)
    rango = alto - bajo
    margen = rango * MARGEN_ESCALA if rango else 1.0
    return alto + margen, bajo - margen


def construir_svg_barras(
    barras: list[dict[str, Any]], niveles: list[dict[str, Any]] | None = None
) -> str:
    """SVG de una serie histórica en barras, con la última destacada.

    Pensado para datos macro: la serie de los últimos períodos de un indicador,
    y opcionalmente el consenso como línea de nivel. Ver el valor de hoy contra
    su propia historia Y contra lo que se esperaba es lo que convierte una cifra
    suelta en una lectura.

    El signo manda el color -sobre cero verde, bajo cero rojo- porque en una
    serie macro el signo ES el dato: una economía que se contrae y una que crece
    no se distinguen por la altura de la barra sino por su lado del eje.
    """
    if not barras:
        raise GraficoError("El gráfico de barras necesita al menos una barra.")

    niveles = niveles or []
    valores = [float(b["valor"]) for b in barras]
    v_max, v_min = resolver_escala_barras(valores, [float(n["valor"]) for n in niveles])
    n = len(barras)

    def coord_y(valor: float) -> float:
        return PLOT_Y0_BARRAS + (v_max - valor) / (v_max - v_min) * (
            PLOT_Y1_BARRAS - PLOT_Y0_BARRAS
        )

    paso = (PLOT_X1_BARRAS - PLOT_X0_BARRAS) / n
    ancho = paso * ANCHO_BARRA
    y_cero = coord_y(0.0)

    partes = [
        f'<svg viewBox="0 0 {VB_W_BARRAS} {VB_H_BARRAS}" preserveAspectRatio="xMidYMid meet">'
    ]

    for lv in niveles:
        y = coord_y(float(lv["valor"]))
        partes.append(
            f'<line class="gb-nivel gb-nivel-{lv.get("clase", "nivel")}" '
            f'x1="{PLOT_X0_BARRAS}" y1="{y:.1f}" x2="{PLOT_X1_BARRAS}" y2="{y:.1f}"/>'
        )
        partes.append(
            f'<text class="gb-nivel-texto gb-nivel-texto-{lv.get("clase", "nivel")}" '
            f'x="{LABEL_X_BARRAS}" y="{y + 5:.1f}" text-anchor="end">{lv["etiqueta"]}</text>'
        )
        if lv.get("rol"):
            partes.append(
                f'<text class="gb-rol" x="{LABEL_X_BARRAS}" y="{y + 20:.1f}" '
                f'text-anchor="end">{lv["rol"]}</text>'
            )

    for i, b in enumerate(barras):
        valor = float(b["valor"])
        x = PLOT_X0_BARRAS + i * paso + (paso - ancho) / 2
        y = coord_y(valor)
        alto = abs(y - y_cero)
        top = min(y, y_cero)
        signo = "pos" if valor >= 0 else "neg"
        # La última barra es el dato que se está comunicando: se destaca para que
        # el ojo la encuentre sin buscar.
        destacada = " gb-barra-destacada" if i == n - 1 else ""
        partes.append(
            f'<rect class="gb-barra gb-barra-{signo}{destacada}" x="{x:.1f}" '
            f'y="{top:.1f}" width="{ancho:.1f}" height="{max(alto, 1.5):.1f}" rx="2"/>'
        )
        if b.get("etiqueta"):
            partes.append(
                f'<text class="gb-eje" x="{x + ancho / 2:.1f}" y="{EJE_Y}" '
                f'text-anchor="middle">{b["etiqueta"]}</text>'
            )

    # El cero se dibuja al final para que ninguna barra lo tape: es la referencia
    # que hace legible el signo.
    partes.append(
        f'<line class="gb-cero" x1="{PLOT_X0_BARRAS}" y1="{y_cero:.1f}" '
        f'x2="{PLOT_X1_BARRAS}" y2="{y_cero:.1f}"/>'
    )
    partes.append("</svg>")
    return "".join(partes)


def enriquecer(payload: dict[str, Any]) -> dict[str, Any]:
    """Reemplaza la clave `recorrido` del payload por el token `grafico` resuelto.

    Un solo punto de entrada para los dos tipos de gráfico, y el despacho sale de
    la forma del dato: `serie` es una línea de precios, `barras` es una serie
    histórica. Así ni el renderer ni `rendir_todas.py` tienen que saber qué
    gráfico lleva cada plantilla.
    """
    recorrido = payload.pop("recorrido", None)
    if not isinstance(recorrido, dict):
        raise GraficoError(
            "El payload no trae la clave 'recorrido' con {serie, marcadores} o {barras}."
        )

    if "barras" in recorrido:
        payload["grafico"] = construir_svg_barras(
            recorrido["barras"], recorrido.get("niveles")
        )
        return payload

    serie = recorrido.get("serie")
    if not isinstance(serie, list):
        raise GraficoError("recorrido.serie debe ser un array de precios.")

    niveles = recorrido.get("niveles") or []
    for lv in niveles:
        if "precio" not in lv:
            raise GraficoError(f"Nivel sin 'precio': {lv!r}")
        lv.setdefault("etiqueta", str(lv["precio"]))

    marcadores = recorrido.get("marcadores") or []
    for m in marcadores:
        faltantes = {"indice", "precio"} - set(m)
        if faltantes:
            raise GraficoError(
                f"Marcador incompleto (faltan {sorted(faltantes)}): {m!r}"
            )
        if not 0 <= m["indice"] <= len(serie) - 1:
            raise GraficoError(
                f"indice {m['indice']} fuera de la serie (0..{len(serie) - 1})."
            )
        # La etiqueta visible respeta los `digits` del activo, así que la trae el
        # payload ya formateada; si falta, se cae al precio crudo.
        m.setdefault("etiqueta", str(m["precio"]))

    payload["grafico"] = construir_svg(
        [float(p) for p in serie], marcadores, niveles,
        lienzo=recorrido.get("lienzo", "alto"),
        ajuste=recorrido.get("ajuste", "meet"),
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    """CLI: payload JSON por stdin, payload enriquecido por stdout."""
    try:
        # stdin no siempre es UTF-8 en Windows (usa la codepage de la consola):
        # leer bytes y decodificar explícito evita mojibake en tildes y ñ.
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        salida = enriquecer(payload)
    except GraficoError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Payload JSON inválido en stdin: {exc}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(
        (json.dumps(salida, ensure_ascii=False) + "\n").encode("utf-8")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
