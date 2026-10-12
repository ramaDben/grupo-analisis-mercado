#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contenido del informe de cierre semanal: lo fijo y el contrato de lo editorial.

Separado de la maqueta (`compilar_informe_cierre_semanal.py`) y de los datos
(`cierre_semanal_datos.py`) por el mismo criterio que la capacitación en PPTX:
editar un texto no debe obligar a tocar el dibujo, ni al revés.

**Acá solo vive lo que no cambia de semana a semana** (aviso legal, encabezados,
reparto de páginas). El texto de la semana se escribe en el `editorial.json` que
deja `--preparar`, y `--rendir` se detiene si falta un campo. Hasta el 2026-10-12
este archivo traía la narrativa entera de la semana del 11 de septiembre (título,
resumen, escenarios, radar y las capas por activo, con cifras escritas a mano y
frases del Playbook retirado), así que cada cierre posterior la republicaba con
la fecha del día.

**Las cifras de precio NO se escriben a mano.** En las capas "qué pasó" se usan
`{previo}`, `{actual}` y `{var}`, que llegan del terminal (regla 1).

Reglas de texto de cliente que el validador impone: sin guion largo como inciso
y sin campos vacíos. Las demás (notación chilena, español chileno neutro, toda
sigla explicada la primera vez) son de quien redacta.
"""

from __future__ import annotations

from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Portada
# ─────────────────────────────────────────────────────────────────────────────
KICKER = "RESEARCH INTERMERCADO · EDICIÓN CIERRE DE SEMANA"
NOTA_CURVA_REZAGO = (
    "Los niveles de la curva son del dato oficial más reciente publicado por la "
    "Reserva Federal, con la fecha indicada en la última columna. La variación de "
    "cinco días es la que corresponde a la semana."
)

# ─────────────────────────────────────────────────────────────────────────────
# El texto de la semana: plantilla vacía y validación
# ─────────────────────────────────────────────────────────────────────────────
# Los tres escenarios van siempre, en este orden. El emoji sigue el código visual
# del proyecto (flechas y no colores, director 2026-09-29), así que no es editorial.
ESCENARIOS_FIJOS = (
    ("pos", "⬆️", "ESCENARIO POSITIVO"),
    ("base", "↔️", "ESCENARIO BASE"),
    ("risk", "⚠️", "ESCENARIO DE RIESGO"),
)
VINETAS_POR_ESCENARIO = 3
FILAS_RADAR = 3
GUIONES_PROHIBIDOS = ("—", "–")


def plantilla_editorial(datos: dict[str, Any]) -> dict[str, Any]:
    """El `editorial.json` vacío de una semana, con una entrada por activo y por serie.

    Las claves salen de los datos reunidos, no de una lista escrita acá: si mañana
    entra un activo al cierre, su ficha aparece en la plantilla sin tocar este módulo.
    """
    return {
        "_instrucciones": (
            "Llenar todos los campos vacíos. En 'pasando' usar {previo}, {actual} y "
            "{var} para las cifras de precio; toda otra cifra sale de una fuente "
            "verificada esa semana. Sin guion largo. 'prob' es un entero y los tres "
            "suman 100. 'titulo' de cada escenario es el remate tras el rótulo fijo."
        ),
        "portada": {"titulo": "", "titulo_acento": "", "bajada": "", "resumen_ejecutivo": ""},
        "notas_portada": {a["slug"]: "" for a in datos["activos"]},
        "curva": {
            "intro": "",
            "diagnostico": {f["codigo"]: "" for f in datos["filas_curva"]},
        },
        "activos": {a["slug"]: {"pasando": "", "prohibido": ""} for a in datos["activos"]},
        "escenarios": [
            {"clase": clase, "titulo": "", "prob": None, "bullets": [""] * VINETAS_POR_ESCENARIO}
            for clase, _, _ in ESCENARIOS_FIJOS
        ],
        "radar": [
            {"cuando": "", "evento": "", "fuente": "", "impacto": ""}
            for _ in range(FILAS_RADAR)
        ],
        "aviso_horario": "",
    }


def _textos(nodo: Any, ruta: str):
    """Recorre el editorial y entrega (ruta, valor) de cada hoja."""
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            if not k.startswith("_"):
                yield from _textos(v, f"{ruta}.{k}" if ruta else k)
    elif isinstance(nodo, list):
        for i, v in enumerate(nodo):
            yield from _textos(v, f"{ruta}[{i}]")
    else:
        yield ruta, nodo


def problemas_editorial(editorial: dict[str, Any], datos: dict[str, Any]) -> list[str]:
    """Todo lo que impide rendir, nombrado campo por campo. Lista vacía = se puede.

    Se juntan todos en vez de cortar en el primero: arreglar de a uno obligaría a
    correr el render tantas veces como huecos haya.
    """
    problemas: list[str] = []
    esperado = plantilla_editorial(datos)
    for seccion in ("portada", "curva"):
        for clave in esperado[seccion]:
            if clave not in (editorial.get(seccion) or {}):
                problemas.append(f"{seccion}.{clave}: falta la clave")
    for slug in esperado["activos"]:
        if slug not in (editorial.get("activos") or {}):
            problemas.append(f"activos.{slug}: falta la ficha")
    for slug in esperado["notas_portada"]:
        if slug not in (editorial.get("notas_portada") or {}):
            problemas.append(f"notas_portada.{slug}: falta la nota")
    for codigo in esperado["curva"]["diagnostico"]:
        if codigo not in ((editorial.get("curva") or {}).get("diagnostico") or {}):
            problemas.append(f"curva.diagnostico.{codigo}: falta el diagnóstico")

    for ruta, valor in _textos(editorial, ""):
        if ruta.endswith(".prob"):
            continue
        if not isinstance(valor, str) or not valor.strip():
            problemas.append(f"{ruta}: vacío")
        elif any(g in valor for g in GUIONES_PROHIBIDOS):
            problemas.append(f"{ruta}: trae guion largo")

    escenarios = editorial.get("escenarios") or []
    clases = [e.get("clase") for e in escenarios]
    if clases != [c for c, _, _ in ESCENARIOS_FIJOS]:
        problemas.append(f"escenarios: deben ser pos, base y risk en ese orden (hay {clases})")
    probs = [e.get("prob") for e in escenarios]
    if not all(isinstance(p, int) and 0 < p < 100 for p in probs):
        problemas.append(f"escenarios.prob: cada una es un entero entre 1 y 99 (hay {probs})")
    elif sum(probs) != 100:
        problemas.append(f"escenarios.prob: suman {sum(probs)} y deben sumar 100")
    if not editorial.get("radar"):
        problemas.append("radar: sin eventos")

    for slug, capas in (editorial.get("activos") or {}).items():
        for clave in ("pasando", "prohibido"):
            try:
                str(capas.get(clave, "")).format(previo="", actual="", var="")
            except (KeyError, IndexError, ValueError) as exc:
                problemas.append(f"activos.{slug}.{clave}: marcador inválido ({exc})")
    return problemas


def exigir_editorial(editorial: dict[str, Any], datos: dict[str, Any]) -> None:
    """Lanza con la lista completa si el editorial no se puede rendir."""
    problemas = problemas_editorial(editorial, datos)
    if problemas:
        raise ValueError(
            "El texto de la semana está incompleto y el informe no sale a medias:\n  - "
            + "\n  - ".join(problemas)
        )

AVISO_LEGAL = (
    "Este informe ha sido elaborado exclusivamente con fines informativos y "
    "formativos por el Área de Research de Grupo Inteligencia, a partir de datos "
    "oficiales del terminal MetaTrader 5, la Reserva Federal de Estados Unidos "
    "(FRED), la Administración de Información Energética (EIA) y el calendario "
    "económico de Investing.com. No constituye una oferta ni una recomendación de "
    "compra o venta de instrumentos financieros o contratos por diferencia. Las "
    "operaciones apalancadas conllevan un riesgo sustancial para el capital."
)

# Encabezado de cada página, por índice de página (2 a 5).
ENCABEZADOS = {
    2: "RESEARCH INTERMERCADO · CURVA SOBERANA & FX",
    3: "RESEARCH INTERMERCADO · METALES",
    4: "RESEARCH INTERMERCADO · ENERGÍA",
    5: "RESEARCH INTERMERCADO · EQUITY & FX GLOBAL",
    6: "RESEARCH INTERMERCADO · ESCENARIOS & MARCO LEGAL",
}

# Reparto de fichas por página: **dos fichas por página como máximo**.
#
# El primer armado puso cuatro en la página 4 y la del yen se perdió entera:
# las páginas son fijas de 1123 px con `overflow: hidden`, así que el contenido
# que no cabe desaparece sin aviso y el informe se lee como completo. El control
# de "cinco páginas" no lo detectó porque el desborde fue DENTRO de una página,
# y por eso el compilador ahora mide el alto de cada una.
PAGINAS_ACTIVOS = {
    2: ("usdclp",),
    3: ("xauusd", "copper"),
    4: ("wti", "brent"),
    5: ("us100", "usdjpy"),
}


def significa_de(lectura, digits: int) -> str:
    """La capa "qué significa para ti", escrita solo con la lectura de la estrategia.

    Frase técnica, nivel a vigilar con su etiqueta y, si la hay, la invalidación: bajo
    ella si la lectura es alcista, sobre ella si es bajista. En rango se nombran el
    soporte y la resistencia que publica el carrusel.
    """
    import pipeline_carrusel as pc
    import pipeline_informe as pi

    def p(valor: float) -> str:
        return pc.formatear_precio(float(valor), digits)

    marco = pi.MARCO_LEGIBLE.get(lectura.marco, lectura.marco)
    frases = [f"{pi._frase_tecnica(lectura)}."]
    frases.append(f"El nivel a vigilar es {p(lectura.vigilar.precio)} ({lectura.vigilar.etiqueta}).")
    if lectura.estado == "RANGO":
        soporte, resistencia = pc.niveles_publicados(lectura)
        if soporte is not None and resistencia is not None:
            frases.append(f"El rango tiene soporte en {p(soporte)} y resistencia en {p(resistencia)}.")
        elif soporte is not None:
            frases.append(f"El soporte del rango está en {p(soporte)}.")
        elif resistencia is not None:
            frases.append(f"La resistencia del rango está en {p(resistencia)}.")
    lado = {"ALCISTA": "bajo", "BAJISTA": "sobre"}.get(lectura.direccion)
    if lectura.invalidacion is not None and lado:
        frases.append(
            f"La lectura deja de valer con un cierre de {marco} {lado} {p(lectura.invalidacion.precio)}."
        )
    return " ".join(frases)


def capas_de(
    slug: str, activo: dict[str, Any], lectura, editorial: dict[str, Any]
) -> dict[str, str]:
    """Rellena las tres capas de un activo con sus cifras reales.

    "Qué pasa" y "qué NO hacer" salen del `editorial.json` de la semana, con las
    cifras de precio interpoladas; "qué significa" sale entera de la `Lectura`
    (acepta el objeto o su dict). Lanza si falta el texto, con la misma política del
    resto del pipeline: una ficha a medias que sale sin avisar llega al cliente.
    """
    if isinstance(lectura, dict):
        from estrategia.contrato import lectura_de_dict

        lectura = lectura_de_dict(lectura)
    contexto = {
        "previo": activo["previo_txt"],
        "actual": activo["actual_txt"],
        "var": activo["var_txt"],
    }
    plantilla = (editorial.get("activos") or {}).get(slug) or {}
    if not all(str(plantilla.get(k, "")).strip() for k in ("pasando", "prohibido")):
        raise KeyError(f"{slug}: falta el texto editorial de la ficha en editorial.json")
    capas = {k: plantilla[k].format(**contexto) for k in ("pasando", "prohibido")}
    return {
        "pasando": capas["pasando"],
        "significa": significa_de(lectura, activo["digits"]),
        "prohibido": capas["prohibido"],
    }
