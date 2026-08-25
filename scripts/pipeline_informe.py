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


def _tabla_curva(curva: dict[str, Any]) -> str:
    """La curva como tabla, con el delta en puntos base y la fecha del dato.

    La fecha va en la tabla y no al pie: FRED publica con rezago, así que el dato
    "de hoy" puede ser de anteayer y el lector tiene derecho a verlo junto a la
    cifra que va a citar.
    """
    def bps(valor: Any) -> str:
        # `null` y `0` son afirmaciones distintas: cero es "no se movió", null es
        # "no se pudo calcular". Mostrar 0 donde no hay dato sería inventar una
        # quietud que nadie midió.
        return "sin dato" if valor is None else f"{valor:+.1f} bps"

    filas = ["| Tramo | Nivel | Δ 1 día | Δ 5 días | Fecha del dato |",
             "|---|---|---|---|---|"]

    series = curva.get("series", {})
    for clave in TRAMOS_CURVA:
        s = series.get(clave)
        if not s:
            continue
        filas.append(
            f"| {s.get('nombre', clave)} | {s.get('nivel_pct', '?')}% "
            f"| {bps(s.get('delta_1d_bps'))} | {bps(s.get('delta_5d_bps'))} "
            f"| {s.get('fecha_dato', '?')} |"
        )

    spread = curva.get("spread_2s10s")
    if spread:
        filas.append(
            f"| Pendiente 2s10s | {spread.get('nivel_pct', '?')}% "
            f"| {bps(spread.get('delta_1d_bps'))} | {bps(spread.get('delta_5d_bps'))} "
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


def _nombre_indicador(ev: dict[str, Any]) -> str:
    """El indicador en español, con su sigla original entre paréntesis.

    No traduce a mano: `obtener_calendario_macro` ya engancha
    `data/glosario_siglas.json` y devuelve `diccionario.nombre_es` cuando el
    evento está en el glosario. Cuando no está, queda el nombre de la fuente y el
    evento viene marcado con `glosario_pendiente`, que es la señal de que hay una
    sigla nueva por agregar al JSON.
    """
    nombre_fuente = ev.get("nombre", "?")
    entrada = ev.get("diccionario") or {}
    nombre_es = entrada.get("nombre_es")
    if not nombre_es:
        return nombre_fuente
    # Varias entradas del glosario ya traen su sigla entre paréntesis
    # ("Confianza del consumidor (The Conference Board)"). Agregar el nombre de la
    # fuente detrás produce paréntesis anidados ilegibles, y la regla del proyecto
    # es explicar la sigla UNA sola vez.
    if "(" in nombre_es:
        return nombre_es
    return f"{nombre_es} ({nombre_fuente})"


def _tabla_calendario(eventos: list[dict[str, Any]]) -> str:
    if not eventos:
        return "_Sin eventos de impacto medio o alto en la jornada._"
    filas = ["| Hora Chile | País | Indicador | Impacto |", "|---|---|---|---|"]
    for ev in eventos:
        hora = str(ev.get("hora_servidor", "?")).split(" ")[-1]
        pais = ev.get("pais", "?")
        filas.append(
            f"| {hora} | {_PAISES_ES.get(pais, pais)} | {_nombre_indicador(ev)} | "
            f"{ev.get('impacto', '?')} |"
        )
    return "\n".join(filas)


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
    fecha_dato = playbook.get("as_of_utc", "no disponible") if playbook else "no disponible"

    encabezado = [
        f"## 01. Marco de la jornada",
        "",
        f"{MARCA_EDITORIAL} Dos parrafos: que deja la sesion anterior y con que abre esta.",
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

    secciones = [
        "\n".join(encabezado),
        "## 02. Regimen macro y sesgo por activo\n\n"
        + (f"**Regimen vigente:** {regimen.get('codigo', 'no disponible')} — "
           f"{regimen.get('nombre', '')}\n\n" if regimen else "")
        + _tabla_playbook(playbook) + "\n\n"
        + f"{MARCA_EDITORIAL} Una lectura de que significa este regimen para la jornada.",
        "## 03. Curva soberana de EE.UU.\n\n"
        + _tabla_curva(curva) + "\n\n"
        + f"{MARCA_EDITORIAL} Que dice el movimiento de tasas sobre el dolar, el oro y el Nasdaq.",
        "## 04. Agenda del dia\n\n"
        + _tabla_calendario(eventos) + "\n\n"
        + f"{MARCA_EDITORIAL} Cual de estos eventos puede mover la jornada y por que.",
        "## 05. Fuentes consultadas\n\n"
        + "- Curva soberana y tasa real: Reserva Federal (FRED), via `data central/`.\n"
        + "- Calendario economico: Investing.com.\n"
        + "- Precios y niveles: terminal MetaTrader 5, cuenta Grupo Inteligencia SpA.\n"
        + (f"- Sesgo cuantitativo: Motor GI, snapshot del {fecha_dato}.\n" if playbook else ""),
    ]

    md = destino / f"informe_{tipo}.md"
    md.write_text("\n\n".join(secciones) + "\n", encoding="utf-8")

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
        "canal": "PDF institucional A4" if tipo == "apertura" else "chat-first (mensaje + grafico)",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Paso 2: rendir
# ─────────────────────────────────────────────────────────────────────────────
def rendir(directorio: Path, tipo: str) -> dict[str, Any]:
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
         "--title", "Marco de Apertura",
         "--tag", "INFORME DE APERTURA",
         "--subtitle", "Regimen macro, curva soberana y agenda del dia para la sesion de hoy.",
         "--header-left", "MARCO DE APERTURA",
         "--header-right", _fecha_es(datetime.now(tz=SANTIAGO)).upper(),
         "--date", _fecha_es(datetime.now(tz=SANTIAGO)),
         "--theme", "verde"],
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

    res = rendir(args.rendir, args.tipo)
    print(f"\nINFORME DE {res['tipo'].upper()} - canal: {res['canal']}")
    if res.get("pdf"):
        print(f"PDF: {res['pdf']}")
    if res.get("nota"):
        print(res["nota"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
