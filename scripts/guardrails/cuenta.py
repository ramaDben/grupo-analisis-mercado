"""Guardia: los precios tienen que venir de la cuenta que el director eligió.

**Por qué existe.** El 2026-09-06 la cadena de datos reportó `LISTO: relojes
frescos y el modelo ve` con el terminal conectado a la cuenta **51256**, y las
seis series se commitearon con esos precios. La cuenta del sistema es la
**51492** (decisión del director ese mismo día), y estaba escrita en tres
archivos de TEXTO: `CLAUDE.md`, `.agents/rules/proyecto.md` y una nota de
`config/activos.json`. Ninguno de los tres verificaba nada.

Es el defecto recurrente del repo, el de los contratos por nombre: dos lados que
se hablan sin que nada compruebe que coinciden. Y acá cuesta plata, porque un
stop calculado sobre otra cuenta es un stop de otro instrumento: distinto
spread, distinto tamaño de contrato, distinta moneda de resultado.

Es además el hermano del fallback a yfinance del 2026-09-02. Ese quedaba escrito
en cada archivo (`broker: YFINANCE`), así que era auditable, y **nada lo decía en
voz alta**. Costó una hora de diagnóstico. Este era peor: no quedaba escrito en
ninguna parte.

## Dos decisiones que no son obvias

**1. El guardia lee el SELLO del archivo, no el terminal en vivo.** Podría
preguntarle a MT5 en qué cuenta está, y sería la respuesta a otra pregunta. Lo
que importa no es dónde está el terminal ahora: es **qué cuenta produjo los
datos que están en disco**, que son los que el motor va a usar. Además
`pipeline_datos.py --estado` tiene que poder correr sin MT5 abierto, porque su
trabajo es leer tres relojes de JSON.

**2. Un sello ausente NO pasa.** Para un stop, "no sé de qué cuenta salió esto"
vale lo mismo que "salió de la equivocada". Tratar la ausencia como permiso
sería la puerta de atrás que este guardia existe para cerrar: bastaría con que
el extractor dejara de estampar el campo. Se cura con una reingesta, que es
justo lo que corresponde hacer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .veredicto import Veredicto, aprueba, falla

_RAIZ = Path(__file__).resolve().parent.parent.parent
CONFIG = _RAIZ / "config" / "cuenta_mt5.json"

# Centinela para distinguir "no me dijiste con que comparar" de "te digo que no
# se con que comparar". Sin el, un `None` explicito caia al config real y el
# guardia APROBABA con el config del llamador roto: fail-open justo en el caso
# que este modulo existe para cerrar. Lo encontro su propio test.
_SIN_DECIR = object()


def login_esperado(ruta: Path | None = None) -> int | None:
    """El número de cuenta que el sistema declara, o `None` si no se puede leer.

    Nunca lanza: este módulo lo consumen hooks, y un guardia que muere no
    protege. Un `None` acá se traduce arriba en un veredicto en rojo, no en un
    pase libre.
    """
    p = ruta or CONFIG
    try:
        datos = json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    login = datos.get("login")
    try:
        return int(login)
    except (TypeError, ValueError):
        return None


def cuenta_correcta(
    login_del_dato: Any, esperado: Any = _SIN_DECIR, *, ubicacion: str = ""
) -> Veredicto:
    """Compara la cuenta que produjo un dato contra la que el sistema declara.

    `login_del_dato` es el sello del archivo. `None` o ausente es **rojo**, y no
    por rigor: para un stop, no saber de qué cuenta salió el precio vale lo
    mismo que saber que salió de la equivocada.

    `esperado` omitido lee el config; `esperado=None` **explícito** significa que
    el llamador no pudo determinarlo, y entonces se niega. Los dos casos parecen
    el mismo y no lo son: confundirlos hacía que un config roto aprobara.
    """
    quiero = login_esperado() if esperado is _SIN_DECIR else esperado
    if quiero is None:
        return falla(
            "cuenta_mt5_inesperada",
            "no se puede leer config/cuenta_mt5.json, así que no hay con qué comparar",
            ubicacion,
        )
    if login_del_dato is None or login_del_dato == "":
        return falla(
            "cuenta_mt5_inesperada",
            f"el dato no dice de qué cuenta salió, y la esperada es la {quiero}",
            ubicacion,
        )
    try:
        tengo = int(login_del_dato)
    except (TypeError, ValueError):
        return falla(
            "cuenta_mt5_inesperada",
            f"el sello de cuenta no es un número: {login_del_dato!r}",
            ubicacion,
        )
    if tengo != quiero:
        return falla(
            "cuenta_mt5_inesperada",
            f"el dato salió de la cuenta {tengo} y el sistema usa la {quiero}",
            ubicacion,
        )
    return aprueba()


def revisar(sellos: dict[str, Any], esperado: Any = _SIN_DECIR) -> Veredicto:
    """Revisa varios activos a la vez. Devuelve el primer fallo, o aprueba.

    Se nombra el activo en `ubicacion` porque saber que "algo salió de otra
    cuenta" no dice qué revisar, y ese fue el problema del caso de yfinance.
    """
    from .veredicto import primer_fallo

    return primer_fallo([
        cuenta_correcta(login, esperado, ubicacion=activo)
        for activo, login in sorted(sellos.items())
    ])
