#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Informe de la jornada: PDF institucional en la apertura, chat-first al cierre.

**Por qué un solo PDF al día y no dos.** El plan de producción pedía informe en
apertura y en cierre, los dos en PDF. La skill `generar-reporte-editorial`
reserva el PDF "estrictamente" para hitos de alta densidad, y su propio criterio
de canal manda formato chat-first para piezas tácticas, por fatiga de descargas.
Decisión del director: la apertura sí va en PDF, porque es densa y se lee antes
de operar; el cierre pasa a mensaje con gráfico adjunto.

**Mismo reparto que el carrusel**: este script arma los DATOS del informe (curva
del Tesoro, calendario del día, régimen y sesgo del Playbook, lotaje por riesgo)
y deja la narrativa en blanco. El análisis lo escribe quien tiene criterio
editorial, no un script.

**La regla de frescura no es negociable en silencio.** El informe de apertura
depende de `macro_bias_output.json`, que produce `macro_bias_engine.py` sobre lo
que ingiere `pipeline_ingesta.py`. Si ese dato está viejo, el informe **no se
emite** salvo que se pida explícitamente con `--con-datos-viejos`, y en ese caso
la antigüedad va estampada en la portada. Un PDF institucional con datos de dos
días hábiles atrás y sin decirlo es peor que no emitirlo: el lector lo cita como
si fuera de hoy.

Uso:
    uv run python scripts/pipeline_informe.py --tipo apertura --preparar
    uv run python scripts/pipeline_informe.py --tipo apertura --rendir <dir>
    uv run python scripts/pipeline_informe.py --tipo cierre --preparar
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SANTIAGO = ZoneInfo("America/Santiago")
DIR_TRABAJO = RAIZ / "data" / "informes"
GENERADOR_PDF = RAIZ / ".agents" / "skills" / "generar-reporte-editorial" / "scripts" / "generar_pdf.py"

# Los tramos de la curva que entran al informe. El resto de las series existen en
# `get_curva_tasas` pero no son parte del marco de apertura: DFF es política
# ejecutada y T10YIE es expectativa, y las dos merecen su propia lectura.
TRAMOS_CURVA = ("DGS2", "DGS10", "DGS30", "DFII10")

MARCA_EDITORIAL = "[[ESCRIBIR]]"

# El lector de la curva devuelve el nombre que usa FRED, en inglés. El informe lo
# lee un cliente en español, así que cada tramo se nombra acá. No se traduce en
# `curva_reader` porque ahí el nombre es el de la fuente, y cambiarlo haría que la
# tool devuelva algo distinto de lo que el organismo publica.
_TRAMOS_ES = {
    "DGS2": "Bono del Tesoro a 2 años",
    "DGS10": "Bono del Tesoro a 10 años",
    "DGS30": "Bono del Tesoro a 30 años",
    "DFII10": "Tasa real a 10 años (TIPS)",
    "DFF": "Tasa efectiva de fondos federales",
    "T10YIE": "Inflación esperada a 10 años",
}


def _curva() -> tuple[dict[str, Any], list[str]]:
    from market_data_mcp.curva_reader import cargar_curva_tasas

    res = cargar_curva_tasas(serie="ALL")
    if "error" in res:
        return {}, [f"curva del Tesoro no disponible ({res['error']}): {res.get('message', '')}"]
    return res, []


def _calendario(ahora: datetime) -> tuple[list[dict[str, Any]], list[str]]:
    from market_data_mcp.tools.calendar import cargar_calendario

    res = cargar_calendario(solo_hoy=True, min_impact="medium", ahora=ahora)
    if "error" in res:
        return [], [f"calendario no disponible ({res['error']})"]
    return res.get("eventos", []), []


def _playbook() -> tuple[dict[str, Any], list[str]]:
    """Régimen, sesgo y parámetros de riesgo de los 5 activos con ficha."""
    from market_data_mcp.bias_reader import cargar_macro_bias

    res = cargar_macro_bias("ALL")
    if "error" in res:
        return {}, [
            f"sesgo del Playbook no disponible ({res['error']}): {res.get('message', '')}"
        ]
    return res, []


def _pct_es(valor: Any) -> str:
    """Un porcentaje en notación chilena y con dos decimales siempre.

    La fuente entrega 4.7 y 4.24 indistintamente. En una columna, "4.7%" al lado
    de "4.24%" se lee como si uno tuviera menos precisión que el otro, cuando en
    realidad son la misma medida. Y el separador decimal en Chile es la coma.
    """
    try:
        return f"{float(valor):.2f}".replace(".", ",") + "%"
    except (TypeError, ValueError):
        return "sin dato"


def _tabla_curva(curva: dict[str, Any]) -> str:
    """La curva como tabla, en lenguaje de cliente.

    Tres cosas que NO se escriben acá aunque sean el estándar del oficio:
    `Δ` como encabezado de columna, `bps` como abreviatura, y "2s10s" como nombre
    de la pendiente. Las tres son taquigrafía de mesa de dinero: quien las conoce
    no las necesita, y quien no, se detiene en ellas antes de llegar al número.

    La fecha del dato va en la tabla y no al pie. FRED publica con rezago, así que
    el dato "de hoy" puede ser de anteayer, y quien va a citar la cifra tiene
    derecho a verlo junto a ella.
    """
    def puntos_base(valor: Any) -> str:
        # `null` y `0` son afirmaciones distintas: cero es "no se movió", null es
        # "no se pudo calcular". Mostrar 0 donde no hay dato sería inventar una
        # quietud que nadie midió.
        if valor is None:
            return "sin dato"
        return f"{valor:+.0f} puntos base"

    filas = [
        "| Tramo | Nivel | Cambio en 1 día | Cambio en 5 días | Fecha del dato |",
        "|---|---|---|---|---|",
    ]

    series = curva.get("series", {})
    for clave in TRAMOS_CURVA:
        s = series.get(clave)
        if not s:
            continue
        filas.append(
            f"| {_TRAMOS_ES.get(clave, s.get('nombre', clave))} | {_pct_es(s.get('nivel_pct'))} "
            f"| {puntos_base(s.get('delta_1d_bps'))} | {puntos_base(s.get('delta_5d_bps'))} "
            f"| {s.get('fecha_dato', '?')} |"
        )

    spread = curva.get("spread_2s10s")
    if spread:
        filas.append(
            f"| Diferencia entre 10 y 2 años | {_pct_es(spread.get('nivel_pct'))} "
            f"| {puntos_base(spread.get('delta_1d_bps'))} | {puntos_base(spread.get('delta_5d_bps'))} "
            f"| {spread.get('fecha_dato', '?')} |"
        )

    # Una tabla con solo el encabezado se lee como "no se movió nada". Si no hay
    # series, se dice que no hay dato: la ausencia declarada es información, la
    # tabla vacía es una afirmación falsa.
    if len(filas) == 2:
        return (
            "_Curva no disponible en esta corrida. Correr `pipeline_ingesta.py` "
            "para refrescar las series del Tesoro._"
        )

    return "\n".join(filas)


# La fuente publica en inglés y el informe lo lee un cliente en español. Es la
# misma regla que ya rige los mensajes: el indicador se nombra en español y la
# sigla original va entre paréntesis una sola vez. Traducir el país es el mínimo.
_PAISES_ES = {
    "United States": "EE.UU.",
    "Chile": "Chile",
    "China": "China",
    "Euro Zone": "Zona Euro",
    "Japan": "Japón",
    "United Kingdom": "Reino Unido",
    "Germany": "Alemania",
}


_MESES_ES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def _fecha_es(momento: datetime) -> str:
    """La fecha en español. `strftime('%B')` devuelve el mes según el locale del
    sistema, que acá es inglés: la portada salía "25 de August de 2026"."""
    return f"{momento.day} de {_MESES_ES[momento.month - 1]} de {momento.year}"


def _momento_snapshot(as_of_utc: str | None) -> str:
    """La marca de tiempo del motor, en hora de Chile y legible.

    El campo viene en ISO con microsegundos y en UTC
    (`2026-08-25T21:55:42.222379+00:00`). Citado tal cual en un informe obliga al
    lector a hacer dos conversiones mentales para saber si el dato es de hoy.
    """
    if not as_of_utc:
        return "no disponible"
    try:
        momento = datetime.fromisoformat(as_of_utc).astimezone(SANTIAGO)
    except (TypeError, ValueError):
        return str(as_of_utc)
    return f"{_fecha_es(momento)}, {momento.strftime('%H:%M')} hora de Chile"


# Sufijos que la fuente pega al nombre del indicador. Sin traducir, la agenda de
# un informe en español termina diciendo "S&P/CS HPI Composite - 20 n.s.a. (YoY)
# (Jun)", que para un cliente es ruido con el que tiene que lidiar antes de llegar
# a la hora y al impacto, que es lo único que iba a mirar.
_SUFIJOS_ES = {
    "YoY": "variación anual",
    "MoM": "variación mensual",
    "QoQ": "variación trimestral",
    "WoW": "variación semanal",
}
_MESES_CORTOS = {
    "Jan": "enero", "Feb": "febrero", "Mar": "marzo", "Apr": "abril",
    "May": "mayo", "Jun": "junio", "Jul": "julio", "Aug": "agosto",
    "Sep": "septiembre", "Oct": "octubre", "Nov": "noviembre", "Dec": "diciembre",
}
_TRIMESTRES = {"Q1": "primer", "Q2": "segundo", "Q3": "tercer", "Q4": "cuarto"}
_PLAZOS = {"Year": "años", "Month": "meses", "Week": "semanas"}


def _nombre_indicador(ev: dict[str, Any]) -> str:
    """El indicador en español, con su período, para un lector no especializado.

    No se traduce a mano: `obtener_calendario_macro` ya engancha
    `data/glosario_siglas.json` y devuelve `diccionario.nombre_es`. Lo que se hace
    acá es quedarse con ese nombre y **descartar el de la fuente**, conservando
    solo los sufijos que aportan información real: el período que mide y el mes al
    que corresponde. Sin eso, dos filas del mismo indicador se leerían idénticas.

    Cuando el indicador no está en el glosario se devuelve el nombre de la fuente
    tal cual y el evento viene marcado `glosario_pendiente`, que es la señal de
    que hay una sigla nueva por agregar al JSON.
    """
    nombre_fuente = ev.get("nombre", "?")
    entrada = ev.get("diccionario") or {}
    nombre_es = entrada.get("nombre_es")
    if not nombre_es:
        return nombre_fuente

    # El orden no es cosmético: primero lo que cambia QUÉ se mide, después cómo
    # se mide y al final a qué período corresponde. Al revés, el lector llega al
    # dato distintivo cuando ya decidió que la fila es igual a la anterior.
    matices: list[str] = []

    # `Core` es el caso que más duplicados produce. El glosario engancha por
    # sigla (PCE, GDP), así que "Core PCE" y "PCE" caen los dos en la misma
    # entrada y salen dos filas idénticas en la tabla. La distinción no es
    # menor: el subyacente excluye alimentos y energía, y es el que mira la Fed.
    if re.search(r"\bCore\b", nombre_fuente, re.IGNORECASE):
        matices.append("subyacente")

    # Mismo problema entre un agregado y su deflactor: "GDP" y "GDP Price Index"
    # comparten la sigla y miden cosas distintas (cuánto se produjo contra
    # cuánto subieron los precios de lo producido).
    if re.search(r"\bPrices?(\s+Index)?\b", nombre_fuente, re.IGNORECASE) \
            and "precio" not in nombre_es.lower():
        matices.append("índice de precios")

    # El plazo de una subasta o de un bono: "2-Year Note Auction" y "5-Year Note
    # Auction" son la misma entrada del glosario y dos eventos distintos.
    plazo = re.search(r"\b(\d+)[-\s](Year|Month|Week)\b", nombre_fuente, re.IGNORECASE)
    if plazo:
        matices.append(f"a {plazo.group(1)} {_PLAZOS[plazo.group(2).capitalize()]}")

    for sufijo, traduccion in _SUFIJOS_ES.items():
        if f"({sufijo})" in nombre_fuente:
            matices.append(traduccion)
    # Solo el nombre del período. "dato de julio" son trece caracteres en la
    # columna que decide el alto de toda la fila, y la palabra "dato" no agrega
    # nada que la columna Cifras no diga al lado.
    for mes_en, mes_es in _MESES_CORTOS.items():
        if f"({mes_en})" in nombre_fuente:
            matices.append(mes_es)
    for trimestre, orden in _TRIMESTRES.items():
        if f"({trimestre})" in nombre_fuente:
            matices.append(f"{orden} trimestre")

    if not matices:
        return nombre_es
    return f"{nombre_es} · {', '.join(matices)}"


CALENDARIO_URL = "https://es.investing.com/economic-calendar/"


def _cifra_es(valor: str) -> str:
    """La cifra de la fuente en notación chilena.

    Investing publica en notación estadounidense: el punto es el separador
    decimal y la coma el de miles. Copiada tal cual a un informe chileno,
    `1.600M` se lee como mil seiscientos millones cuando son un millón seiscientos
    mil, y `216,000` como doscientos dieciséis. Se intercambian los dos
    separadores en un solo paso para no pisar el trabajo del anterior.
    """
    if not valor:
        return ""
    return valor.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _estado_evento(ev: dict[str, Any], ahora: datetime) -> str:
    """Si el dato ya salió, si falta, o si pasó la hora y no trajo cifra.

    El testigo de que un dato se publicó es su valor (`actual`), no el reloj: la
    fuente publica con retraso más seguido de lo que uno querría, y un informe
    que dice "ya salió" porque pasó la hora obliga al lector a desmentirlo.

    El tercer estado no es un caso de borde: las subastas del Tesoro, las
    intervenciones de gobernadores y los feriados nunca traen cifra. Marcarlos
    "pendiente" para siempre haría que la tabla del cierre mienta todas las
    tardes.
    """
    if str(ev.get("actual") or "").strip():
        return "Publicado"
    try:
        momento = datetime.strptime(
            str(ev.get("hora_servidor", "")), "%Y-%m-%d %H:%M"
        ).replace(tzinfo=SANTIAGO)
    except ValueError:
        return "Pendiente"
    return "Pendiente" if momento > ahora else "Sin cifra"


def _cifras_evento(ev: dict[str, Any]) -> str:
    """Las dos cifras que importan, que dependen de si el dato salió o no.

    Antes de publicarse, lo que informa es el consenso; después, el valor real
    contra ese consenso. El anterior solo entra cuando es lo único que hay
    (subastas, series sin consenso publicado): así la columna nunca lleva tres
    números ni queda vacía teniendo algo que decir.
    """
    actual = _cifra_es(str(ev.get("actual") or "").strip())
    consenso = _cifra_es(str(ev.get("forecast") or "").strip())
    previo = _cifra_es(str(ev.get("previo") or "").strip())

    # El salto de linea es explicito y no decorativo. Con seis columnas esta
    # queda en unos 100 px, y `0,2% · esperado 0,1%` en una sola linea se parte
    # donde el navegador quiera: la primera version dejaba el separador colgando
    # al final de la linea (`0,2% ·`) y la celda en tres o cuatro lineas, que es
    # lo que hacia que la tabla de quince filas no cupiera en la pagina.
    if actual and consenso:
        return f"**{actual}**<br>esperado {consenso}"
    if actual:
        return f"**{actual}**<br>sin consenso"
    if consenso:
        return f"esperado {consenso}"
    if previo:
        return f"anterior {previo}"
    return "—"


# Palabras con las que la fuente distingue dos eventos que el glosario mete en
# la misma entrada. No es un traductor: es la lista corta de las que aparecen
# seguido en un calendario de cuatro países. Lo que no está acá pasa tal cual,
# que para un nombre propio como Cushing es justamente lo correcto.
_CALIFICADORES_ES = {
    "manufacturing": "manufacturero",
    "services": "servicios",
    "composite": "compuesto",
    "preliminary": "preliminar",
    "prelim": "preliminar",
    "flash": "preliminar",
    "revised": "revisado",
    "final": "final",
    "excluding": "excluyendo",
    "ex": "excluyendo",
    "transportation": "transporte",
    "defense": "defensa",
    "continuing": "continuas",
    "initial": "iniciales",
}

# Ruido que la fuente pega al nombre y que `_nombre_indicador` ya tradujo o
# descartó. Si entrara al desempate, dos filas se "distinguirían" por la palabra
# que tienen en común.
_RUIDO_FUENTE = {
    "mom", "yoy", "qoq", "wow", "sa", "nsa", "n", "s", "a",
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "sept",
    "oct", "nov", "dec", "q1", "q2", "q3", "q4", "index", "core",
}


def _palabras_fuente(nombre: str) -> list[str]:
    """Las palabras del nombre de la fuente que pueden diferenciar dos filas."""
    crudas = re.findall(r"[A-Za-z][A-Za-z&/\.-]*", nombre)
    return [p for p in crudas if p.lower().strip(".") not in _RUIDO_FUENTE]


def _distinguir(nombres: list[str], eventos: list[dict[str, Any]]) -> list[str]:
    """Ninguna fila de la tabla puede leerse igual que otra.

    Dos filas idénticas no son un defecto cosmético: el lector no puede saber
    cuál de las dos cifras corresponde a cuál indicador, y la tabla deja de
    servir para lo único que sirve una tabla.

    `_nombre_indicador` cubre los matices que ya conocemos (subyacente, índice
    de precios, plazo, período). Esta es la red para el que aparezca mañana, y
    cita **solo la palabra que diferencia** en vez del nombre completo de la
    fuente: entre "Crude Oil Inventories" y "Cushing Crude Oil Inventories" la
    diferencia es Cushing, y pegar los dos nombres en inglés para decir eso
    metería en un informe en español seis palabras que el lector no necesita.

    La fila que no tiene ninguna palabra propia es la general del grupo, y se
    dice así: es la lectura nacional frente a la de un punto de entrega, o el
    agregado frente a uno de sus componentes.
    """
    repetidos = {n for n in nombres if nombres.count(n) > 1}
    if not repetidos:
        return nombres

    distinguidos: list[str] = []
    for nombre, ev in zip(nombres, eventos):
        if nombre not in repetidos:
            distinguidos.append(nombre)
            continue

        grupo = [e for n, e in zip(nombres, eventos) if n == nombre]
        comunes = set.intersection(*(
            {p.lower() for p in _palabras_fuente(e.get("nombre", ""))} for e in grupo
        ))
        propias = [
            _CALIFICADORES_ES.get(p.lower(), p)
            for p in _palabras_fuente(ev.get("nombre", ""))
            if p.lower() not in comunes
        ]
        distinguidos.append(f"{nombre} ({', '.join(propias) if propias else 'general'})")
    return distinguidos


def _tabla_calendario(
    eventos: list[dict[str, Any]], ahora: datetime | None = None
) -> str:
    """La agenda del día, con el estado de cada dato y sus cifras.

    Seis columnas y no ocho: el anterior, el consenso y el dato real no caben
    los tres, y tampoco hacen falta los tres a la vez (ver `_cifras_evento`).
    Con la escala tipográfica del informe de cliente, una columna más deja el
    nombre del indicador en tres líneas y el bloque no cabe en la página.
    """
    if not eventos:
        return (
            "_Sin eventos de impacto medio o alto en la jornada._\n\n"
            f"Agenda completa: [calendario económico]({CALENDARIO_URL})"
        )

    ahora = ahora or datetime.now(tz=SANTIAGO)
    nombres = _distinguir([_nombre_indicador(ev) for ev in eventos], eventos)

    filas = ["| Estado | Hora | País | Indicador | Impacto | Cifras |",
             "|---|---|---|---|---|---|"]
    for ev, nombre in zip(eventos, nombres):
        hora = str(ev.get("hora_servidor", "?")).split(" ")[-1]
        pais = ev.get("pais", "?")
        filas.append(
            f"| {_estado_evento(ev, ahora)} | {hora} | {_PAISES_ES.get(pais, pais)} | "
            f"{nombre} | {str(ev.get('impacto', '?')).capitalize()} | "
            f"{_cifras_evento(ev)} |"
        )

    publicados = sum(1 for ev in eventos if _estado_evento(ev, ahora) == "Publicado")
    pie = (
        f"Horas en hora de Chile. {publicados} de {len(eventos)} eventos ya "
        f"publicados al momento de emitir este informe. "
        f"Agenda completa y actualizada: [calendario económico]({CALENDARIO_URL})"
    )
    return "\n".join(filas) + "\n\n" + pie


def _tabla_playbook(playbook: dict[str, Any]) -> str:
    activos = playbook.get("activos", {})
    if not activos:
        return "_Sesgo del Playbook no disponible en esta corrida._"
    filas = ["| Activo | Sesgo | Score | Setups permitidos | Prohibidos |",
             "|---|---|---|---|---|"]
    for ticker, a in activos.items():
        filas.append(
            f"| {ticker} | {a.get('sesgo_etiqueta', '?')} | {a.get('sesgo_score', '?')} | "
            f"{', '.join(a.get('setups_permitidos') or []) or '—'} | "
            f"{', '.join(a.get('setups_prohibidos') or []) or '—'} |"
        )
    return "\n".join(filas)


# ─────────────────────────────────────────────────────────────────────────────
# El traductor del motor: ningún token interno llega al cliente
# ─────────────────────────────────────────────────────────────────────────────
_GLOSARIO_MOTOR = RAIZ / "data" / "glosario_motor.json"


def cargar_glosario_motor() -> dict[str, Any]:
    """`data/glosario_motor.json`, o vacío si falta (el guard lo detecta igual)."""
    try:
        return json.loads(_GLOSARIO_MOTOR.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _traducir_setup(token: str, glosario: dict[str, Any]) -> str:
    """Un setup del motor, en lenguaje de cliente.

    Si el token no está en el glosario se devuelve tal cual, y ahí lo caza el
    test: preferimos que falle la suite a que `FADE_TOP_RESISTANCE` llegue a un
    documento que lee un cliente.
    """
    return (glosario.get("setups") or {}).get(token, token)


def _frase_sesgo(a: dict[str, Any], glosario: dict[str, Any]) -> str:
    """El sesgo de un activo en una frase de cliente, sin punto final.

    Vive aparte porque la usan dos consumidores: la prosa de la seccion y el
    subtitulo del grafico. Si cada uno la derivara por su cuenta, el dia que
    cambie la traduccion de un matiz la imagen y el texto dirian cosas
    distintas sobre el mismo activo, en la misma pagina.
    """
    sesgos = glosario.get("sesgos") or {}
    matices_es = glosario.get("matices") or {}
    etiqueta = str(a.get("sesgo_etiqueta", ""))
    primera = etiqueta.split()[0] if etiqueta else ""
    direccion = sesgos.get(primera, primera.lower())
    matiz_crudo = etiqueta[len(primera):].strip(" /").strip()
    matiz = matices_es.get(matiz_crudo.upper(), "")
    if not matiz and matiz_crudo:
        # Los rangos vienen como "RANGO (912 - 925)": se deja el numero, que
        # es lo unico que el cliente necesita de ahi.
        numeros = re.search(r"\(([^)]+)\)", matiz_crudo)
        matiz = ("entre " + numeros.group(1).replace(" - ", " y ")) if numeros else matiz_crudo.lower()
    frase = f"Hoy lo vemos {direccion}"
    if matiz:
        frase += f", {matiz}"
    return frase


def generar_graficos_activos(
    playbook: dict[str, Any], glosario: dict[str, Any], destino: Path
) -> tuple[dict[str, str], list[str]]:
    """Un grafico por activo del Playbook, con la serie real del terminal.

    Devuelve `{simbolo_playbook: ruta_relativa}` y los avisos de lo que no se
    pudo dibujar. **Nunca lanza**: un informe sin graficos sigue siendo un
    informe, mientras que uno que se cae por una imagen deja al director sin
    nada a las ocho de la manana. Cada ausencia queda dicha en los avisos, que
    es lo que la hace auditable en vez de invisible.

    Brent no tiene grafico y no es un olvido: el broker no lo ofrece, asi que no
    hay serie que pedir. Como comparte lectura con WTI, el bloque agrupado se
    queda con el grafico del WTI.
    """
    avisos: list[str] = []
    activos = (playbook or {}).get("activos") or {}
    if not activos:
        return {}, avisos

    try:
        sys.path.insert(0, str(RAIZ / "scripts"))
        from grafico_informe import GraficoError, construir_grafico
        from market_data_mcp import mt5_client
        from market_data_mcp.analisis import analizar_activo
        from market_data_mcp.bias_reader import TICKER_MT5
    except ImportError as exc:
        return {}, [
            f"informe sin gráficos: no se pudo importar el generador ({exc}). "
            "Instalar con `uv sync --extra informe` y correr con `--with MetaTrader5`."
        ]

    # `analizar_activo` no abre la conexion por su cuenta: sin esto responde
    # MT5_UNAVAILABLE y los niveles saldrian vacios sin que se note.
    try:
        mt5_client.connect()
    except Exception as exc:  # noqa: BLE001
        return {}, [f"informe sin gráficos: MT5 no conectó ({exc.__class__.__name__})."]

    salida: dict[str, str] = {}
    for simbolo, a in activos.items():
        ticker = TICKER_MT5.get(simbolo)
        if not ticker:
            avisos.append(f"{simbolo} sin gráfico: el broker no ofrece el símbolo.")
            continue
        niveles = analizar_activo(ticker, "D1")
        if niveles.get("error"):
            avisos.append(f"{simbolo}: niveles no disponibles ({niveles['error']}).")
            niveles = {}
        nombre = a.get("nombre", simbolo)
        relativa = f"graficos/{simbolo.lower()}.png"
        try:
            construir_grafico(
                ticker, nombre, destino / relativa,
                timeframe="D1", tema="claro",
                subtitulo=_frase_sesgo(a, glosario),
                niveles=niveles,
            )
        except GraficoError as exc:
            avisos.append(f"{simbolo} sin gráfico: {exc}")
            continue
        salida[simbolo] = relativa
    return salida, avisos


def _lectura_por_activo(
    playbook: dict[str, Any],
    glosario: dict[str, Any],
    graficos: dict[str, str] | None = None,
) -> str:
    """El sesgo por activo en prosa, no en una matriz de cinco columnas.

    Sigue el ritmo pedagógico que la skill de reporte editorial exige y que el
    informe del Motor GI ya usa: qué pasa, qué significa para ti, y qué NO vamos
    a hacer hoy. La versión anterior era una tabla con `setups_permitidos` y
    `setups_prohibidos` volcados del JSON: nombres de variable del motor, en
    inglés y en mayúsculas, que un cliente lee como ruido.

    Tres decisiones de redacción que se tomaron mirando el resultado:

    - **El porqué de las prohibiciones va una sola vez, al final.** Repetirlo bajo
      cada activo lo convertía en relleno que el ojo aprende a saltar, y con eso
      se pierde justo lo que había que comunicar.
    - **Los activos con lectura idéntica se agrupan.** WTI y Brent salían como dos
      bloques palabra por palabra iguales: para un cliente eso no es más
      información, es la misma dos veces.
    - **El matiz del sesgo se traduce.** Sin eso la frase quedaba colgando: "lo
      vemos con más probabilidad de subir, moderado".
    """
    activos = playbook.get("activos", {})
    if not activos:
        return "_Lectura por activo no disponible en esta corrida._"

    def descripcion(a: dict[str, Any]) -> tuple[str, list[str], list[str]]:
        return _frase_sesgo(a, glosario) + ".", (
            [_traducir_setup(s, glosario) for s in (a.get("setups_permitidos") or [])]
        ), (
            [_traducir_setup(s, glosario) for s in (a.get("setups_prohibidos") or [])]
        )

    # Agrupar los activos cuya lectura es identica palabra por palabra.
    grupos: dict[tuple, list[tuple[str, str]]] = {}
    for ticker, a in activos.items():
        clave = descripcion(a)
        clave_hash = (clave[0], tuple(clave[1]), tuple(clave[2]))
        grupos.setdefault(clave_hash, []).append((ticker, a.get("nombre", ticker)))

    bloques: list[str] = []
    hubo_prohibiciones = False
    graficos = graficos or {}
    for (frase, permitidos, prohibidos), miembros in grupos.items():
        nombres = [n for _, n in miembros]
        titulo = nombres[0] if len(nombres) == 1 else " y ".join(
            [", ".join(nombres[:-1]), nombres[-1]]
        )
        bloque = f"### {titulo}\n\n**{frase}**"
        if permitidos:
            bloque += "\n\nQué estamos mirando: " + "; ".join(
                p[0].lower() + p[1:] for p in permitidos
            ) + "."
        if prohibidos:
            hubo_prohibiciones = True
            bloque += "\n\n**Lo que hoy no hacemos:** " + "; ".join(prohibidos) + "."
        # El grafico cierra el bloque: primero se dice que pasa y despues se
        # muestra. Al reves, el cliente mira la imagen sin saber que buscar.
        for simbolo, nombre in miembros:
            ruta = graficos.get(simbolo)
            if ruta:
                bloque += f"\n\n![{nombre}: precio de los últimos meses]({ruta})"
        bloques.append(bloque)

    texto = "\n\n".join(bloques)
    if hubo_prohibiciones:
        texto += (
            "\n\n> **Sobre lo que no hacemos.** No es una opinión sobre esos activos "
            "ni una predicción de que vayan a moverse al revés. Son jugadas que, en el "
            "escenario de mercado de hoy, ofrecen poco a favor y mucho en contra. "
            "Cuando el escenario cambia, la lista cambia con él."
        )
    return texto


def _bloque_regimen(regimen: dict[str, Any], glosario: dict[str, Any]) -> str:
    """El régimen macro explicado, sin su código interno.

    `R2_GOLDILOCKS_EXPANSION` es un identificador para que el motor compare
    estados entre sí. En un informe de cliente no aporta nada y resta: parece
    jerga que hay que descifrar antes de llegar al contenido.
    """
    codigo = regimen.get("codigo")
    entrada = (glosario.get("regimenes") or {}).get(codigo)
    if not entrada:
        return ""
    return (
        f"**El escenario de fondo: {entrada['nombre'].lower()}.** "
        f"{entrada['explicacion']} {entrada['que_implica']}"
    )


def _diccionario(glosario: dict[str, Any], texto: str) -> str:
    """Las pocas expresiones técnicas que sobreviven, explicadas una vez.

    Regla del proyecto: ninguna abreviatura queda sin explicación en español. Se
    incluyen solo las que de verdad aparecen en el documento, para que el bloque
    no sea una lista muerta que nadie lee.
    """
    conceptos = glosario.get("conceptos") or {}
    presentes = [(k, v) for k, v in conceptos.items() if k.lower() in texto.lower()]
    if not presentes:
        return ""
    filas = [f"- **{k.capitalize()}.** {v}" for k, v in presentes]
    return "## Diccionario rápido\n\n" + "\n".join(filas)


# ─────────────────────────────────────────────────────────────────────────────
# Paso 1: preparar
# ─────────────────────────────────────────────────────────────────────────────
def preparar(tipo: str, con_datos_viejos: bool = False) -> dict[str, Any]:
    """Arma el markdown del informe con los datos resueltos y la prosa en blanco."""
    ahora = datetime.now(tz=SANTIAGO)
    avisos: list[str] = []

    curva, av = _curva()
    avisos.extend(av)
    eventos, av = _calendario(ahora)
    avisos.extend(av)
    playbook, av = _playbook()
    avisos.extend(av)

    # La regla de frescura: sin sesgo del Playbook, el informe de apertura pierde
    # su columna vertebral (régimen, sesgo y riesgo por activo).
    if tipo == "apertura" and not playbook and not con_datos_viejos:
        raise SystemExit(
            "El informe de apertura NO se emite: el sesgo del Playbook no esta "
            "disponible.\n  " + "\n  ".join(avisos) + "\n\n"
            "Un PDF institucional sin regimen ni sesgo, o con datos de dias atras y "
            "sin decirlo, se cita despues como si fuera de hoy.\n"
            "Remedio: correr pipeline_ingesta.py y despues macro_bias_engine.py.\n"
            "Para emitirlo igual, con la antiguedad estampada en la portada: "
            "--con-datos-viejos"
        )

    destino = DIR_TRABAJO / f"{ahora.strftime('%Y-%m-%d')}_{tipo}"
    destino.mkdir(parents=True, exist_ok=True)

    regimen = (playbook.get("regimen_macro_global") or {}) if playbook else {}
    fecha_dato = _momento_snapshot(playbook.get("as_of_utc")) if playbook else "no disponible"

    encabezado = [
        f"## 01. Marco de la jornada",
        "",
        f"{MARCA_EDITORIAL} Dos párrafos: qué deja la sesión anterior y con qué abre esta.",
        "",
    ]
    if not playbook or con_datos_viejos:
        # Dos avisos distintos, porque son situaciones distintas: emitir con un
        # snapshot viejo no es lo mismo que emitir sin sesgo. Un aviso que dijera
        # "snapshot del no disponible" no informa nada.
        if playbook:
            aviso = (
                f"> **Aviso de frescura.** El sesgo cuantitativo de este informe "
                f"corresponde al snapshot del {fecha_dato}, no al momento de emisión. "
                f"Los niveles y la curva llevan su propia fecha en cada tabla."
            )
        else:
            aviso = (
                "> **Aviso de frescura.** Este informe se emite **sin el sesgo "
                "cuantitativo del Motor GI**: el snapshot estaba vencido al momento de "
                "generarlo. Las secciones de régimen y sesgo por activo van vacías a "
                "propósito, y ninguna cifra de este documento debe leerse como lectura "
                "del motor."
            )
        encabezado.insert(0, "")
        encabezado.insert(0, aviso)

    glosario = cargar_glosario_motor()

    # Los graficos se dibujan antes de componer el texto porque la seccion
    # los referencia. Si el terminal no responde, `generar_graficos_activos`
    # devuelve el diccionario vacio y sus motivos: el informe sale sin
    # imagenes en vez de no salir.
    graficos, av = generar_graficos_activos(playbook, glosario, destino)
    avisos.extend(av)

    secciones = [
        "\n".join(encabezado),
        "## 02. El escenario de hoy\n\n"
        + (_bloque_regimen(regimen, glosario) + "\n\n" if regimen else "")
        + f"{MARCA_EDITORIAL} Una o dos frases sobre cómo se traduce ese escenario "
          "en la jornada de hoy.\n\n"
        + _lectura_por_activo(playbook, glosario, graficos),
        "## 03. Qué están haciendo las tasas en EE.UU.\n\n"
        + f"{MARCA_EDITORIAL} Una frase de entrada: hacia dónde se movieron las tasas "
          "y por qué le importa a alguien que no opera bonos.\n\n"
        + _tabla_curva(curva) + "\n\n"
        + f"{MARCA_EDITORIAL} Qué implica para el oro, para las acciones tecnológicas "
          "y para el dólar. Una viñeta por activo, en frases cortas.",
        "## 04. La agenda del día\n\n"
        + _tabla_calendario(eventos, ahora) + "\n\n"
        + f"{MARCA_EDITORIAL} Cuál de estos datos puede mover la jornada, qué mide y "
          "qué pasa si sale mejor o peor de lo esperado.",
        "## 05. De dónde salen estos datos\n\n"
        + "- Tasas de los bonos e inflación esperada: Reserva Federal de Estados Unidos (FRED).\n"
        + "- Calendario económico y consensos de mercado: Investing.com.\n"
        + "- Precios y niveles de los activos: terminal MetaTrader 5, cuenta Grupo Inteligencia SpA.\n"
        + (f"- Lectura cuantitativa de escenario: Motor GI, cálculo del {fecha_dato}.\n" if playbook else ""),
    ]

    cuerpo = "\n\n".join(secciones)
    diccionario = _diccionario(glosario, cuerpo)
    if diccionario:
        cuerpo += "\n\n" + diccionario

    md = destino / f"informe_{tipo}.md"
    md.write_text(cuerpo + "\n", encoding="utf-8")

    (destino / "_datos.json").write_text(
        json.dumps(
            {"curva": curva, "eventos": eventos, "playbook": playbook, "avisos": avisos},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "tipo": tipo,
        "directorio": str(destino),
        "markdown": str(md),
        "avisos": avisos,
        "secciones_por_escribir": md.read_text(encoding="utf-8").count(MARCA_EDITORIAL),
        "graficos": len(graficos),
        "canal": "PDF institucional A4" if tipo == "apertura" else "chat-first (mensaje + grafico)",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Paso 2: rendir
# ─────────────────────────────────────────────────────────────────────────────
def rendir(
    directorio: Path,
    tipo: str,
    titulo: str = "Flash de Mercado",
    tag: str = "APERTURA DE NUEVA YORK",
) -> dict[str, Any]:
    """Compila el PDF de apertura. El cierre no lleva PDF por decision de canal."""
    md = directorio / f"informe_{tipo}.md"
    if not md.is_file():
        raise SystemExit(f"No encuentro {md}. Correr antes --preparar.")

    texto = md.read_text(encoding="utf-8")
    if MARCA_EDITORIAL in texto:
        pendientes = texto.count(MARCA_EDITORIAL)
        raise SystemExit(
            f"El informe tiene {pendientes} seccion(es) sin escribir (busca "
            f"{MARCA_EDITORIAL} en {md}).\n"
            "Las tablas de datos ya estan; falta el analisis, que es lo que un "
            "script no puede redactar."
        )

    if tipo == "cierre":
        return {
            "tipo": tipo,
            "canal": "chat-first",
            "markdown": str(md),
            "nota": (
                "El cierre no genera PDF: por criterio de canal va como mensaje con "
                "grafico adjunto. Usar el markdown como guion del mensaje."
            ),
        }

    salida = directorio / f"informe_{tipo}_GI.pdf"
    proceso = subprocess.run(
        # Los flags son los de generar_pdf.py, no inventados: --pdf y no --out,
        # --title y no --titulo. La primera version usaba los nombres castellanos
        # de sus parametros internos y argparse los rechazaba.
        [sys.executable, str(GENERADOR_PDF),
         "--md", str(md),
         "--pdf", str(salida),
         "--title", titulo,
         "--tag", tag.upper(),
         "--subtitle", "Regimen macro, curva soberana y agenda del dia para la sesion de hoy.",
         "--header-left", f"{titulo.upper()} • {tag.upper()}",
         "--header-right", _fecha_es(datetime.now(tz=SANTIAGO)).upper(),
         "--date", _fecha_es(datetime.now(tz=SANTIAGO)),
         "--theme", "verde",
         # El informe de apertura lo lee un cliente. El maquetador trae el cuerpo
         # en 7,5-7,9 pt, bajo el piso de legibilidad impresa; esta escala lo deja
         # cerca de 11 pt, que es donde se calibro el folleto del repo por la misma
         # razon. Los informes internos no la pasan y conservan su tamano.
         "--escala", "1.4"],
        capture_output=True, text=True, cwd=str(RAIZ),
    )
    if proceso.returncode != 0:
        raise SystemExit(
            "generar_pdf.py fallo. Requiere playwright, markdown y pypdf:\n"
            f"{proceso.stderr.strip() or proceso.stdout.strip()}"
        )

    return {"tipo": tipo, "canal": "PDF", "pdf": str(salida), "salida": proceso.stdout.strip()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Informe de la jornada (apertura o cierre)")
    parser.add_argument("--tipo", required=True, choices=("apertura", "cierre"))
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--preparar", action="store_true")
    grupo.add_argument("--rendir", type=Path, metavar="DIR")
    parser.add_argument(
        "--titulo", default="Flash de Mercado",
        help="titulo principal de la portada del PDF",
    )
    parser.add_argument(
        "--tag", default="APERTURA DE NUEVA YORK",
        help="pretitulo o tag superior de la portada del PDF",
    )
    parser.add_argument(
        "--con-datos-viejos", action="store_true",
        help="emite la apertura aunque el sesgo este vencido, estampando la antiguedad",
    )
    args = parser.parse_args(argv)

    if args.preparar:
        res = preparar(args.tipo, con_datos_viejos=args.con_datos_viejos)
        print(f"\nINFORME DE {res['tipo'].upper()} - canal: {res['canal']}")
        print(f"Markdown: {res['markdown']}")
        print(f"Secciones por escribir: {res['secciones_por_escribir']} (marcadas {MARCA_EDITORIAL})")
        if res["avisos"]:
            print("\nAVISOS")
            for a in res["avisos"]:
                print(f"  - {a}")
        print(f"\nDespues: --tipo {res['tipo']} --rendir {res['directorio']}")
        return 0

    res = rendir(args.rendir, args.tipo, titulo=args.titulo, tag=args.tag)
    print(f"\nINFORME DE {res['tipo'].upper()} - canal: {res['canal']}")
    if res.get("pdf"):
        print(f"PDF: {res['pdf']}")
    if res.get("nota"):
        print(res["nota"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
