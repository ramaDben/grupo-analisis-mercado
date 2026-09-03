#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""La clasificación propia de los datos macro, independiente del juicio de Investing.

**Por qué existe.** `obtener_calendario_macro` devuelve `resultado: peor | mejor |
en_linea`, que es un **juicio económico**: si el dato salió por encima o por
debajo del consenso. Lo que la pieza necesita es otra cosa, la **dirección de
mercado**, y no coinciden.

El caso del 2026-09-03 lo muestra entero: las peticiones de subsidio salieron
206K contra 205K esperado, o sea `peor`. El dólar cedió 0,65 % y el oro subió
0,93 %. **"Peor" para la economía fue alcista para el oro**, porque un empleo más
débil acerca los recortes de tasa de la Fed. Una pieza que tradujera `peor` como
`bajista` habría dicho lo contrario de lo que pasó.

Ese mapeo no lo puede dar Investing y no es su trabajo. Vive acá.

**Tres decisiones de diseño que conviene no revertir:**

1. **La clasificación vive en `data/glosario_siglas.json`, no en un archivo
   nuevo.** El MCP del calendario ya adjunta la entrada de ese glosario en el
   campo `diccionario` de cada evento, así que extenderlo hace que la
   clasificación llegue sola a las piezas. Un archivo paralelo sería el defecto
   recurrente de este repo: dos fuentes para lo mismo.

2. **El `pais` es obligatorio y no es cosmético.** El glosario tiene `CPI` e
   `IPC` como "índice de precios al consumidor" sin distinguir país, y el signo
   **depende del país**: un IPC caliente de EE.UU. sube al dólar, uno de Chile
   baja al USD/CLP. Misma sigla, signo opuesto. Los indicadores cuyo país es
   ambiguo quedan sin clasificar a propósito: fail-closed le gana a un signo
   equivocado publicado a un canal.

3. **`tier` es nuestro; `impacto` es de Investing.** Dos campos con dueños
   distintos. El que gobierna nuestras decisiones es el nuestro, porque el de la
   fuente marca "alto" a las peticiones semanales de subsidio igual que a un
   FOMC.

El efecto direccional está declarado de **primer orden** y es subordinado al
régimen. El 2026-09-03 acertó en dólar y oro y falló en índices: debían subir
por la expectativa de recortes y bajaron, porque el ISM de precios salió
caliente y el régimen era R3 estanflación. El Playbook manda sobre el dato, y
esa jerarquía ya existe en `macro_bias_engine`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
GLOSARIO = RAIZ / "data" / "glosario_siglas.json"

# La escala es de tres y no más. Un cuarto tier sería una gradación que nadie
# puede aplicar de forma consistente.
TIERS = {
    1: "reprecia toda la curva",
    2: "mueve su clase de activo",
    3: "contexto",
}


def cargar_glosario(ruta: Path | None = None) -> dict[str, Any]:
    """El glosario completo, incluidas las entradas sin clasificar."""
    p = ruta or GLOSARIO
    if not p.exists():
        return {}
    datos = json.loads(p.read_text(encoding="utf-8"))
    return {k: v for k, v in datos.items() if not k.startswith("_")}


def cargar_clasificacion(ruta: Path | None = None) -> dict[str, Any]:
    """Solo las entradas que **están** clasificadas, o sea las que traen `tier`.

    Una entrada del glosario sin `tier` sigue sirviendo para explicar la sigla;
    lo que no puede es gobernar una decisión de publicación.
    """
    return {
        clave: entrada
        for clave, entrada in cargar_glosario(ruta).items()
        if isinstance(entrada, dict) and "tier" in entrada
    }


def _candidatas(nombre_evento: str, clasificadas: dict[str, Any]) -> list[str]:
    """Las claves del glosario que calzan con el nombre del evento, la mejor primero.

    Se ordena por el largo de **lo que calzó**, no por el largo de la clave:
    `TPM` calza con "Chile Interest Rate Decision" por su título de fuente
    `Interest Rate Decision` (22 caracteres), y `FOMC` calza con "Fed Interest
    Rate Decision" por `Fed Interest Rate Decision` (26). Ordenar por el largo
    de la clave daría `FOMC` (4) sobre `TPM` (3) sin mirar qué calzó, y bastaría
    un título más específico en la otra para invertirlo sin querer.

    El desempate es alfabético y no arbitrario: dos indicadores que calzan con
    lo mismo tienen que resolverse siempre igual, o la pieza cambia de un día
    para otro sin que nadie toque nada.
    """
    texto = nombre_evento.lower()
    calzan: list[tuple[int, str]] = []
    for clave, entrada in clasificadas.items():
        alternativas = [clave] + list(entrada.get("titulos_ff") or [])
        largos = [len(alt) for alt in alternativas if alt.lower() in texto]
        if largos:
            calzan.append((max(largos), clave))
    calzan.sort(key=lambda x: (-x[0], x[1]))
    return [clave for _, clave in calzan]


def clasificar(evento: dict[str, Any], ruta: Path | None = None) -> dict[str, Any] | None:
    """La clasificación de un evento del calendario, o `None` si no la tiene.

    Devuelve `None` en tres casos, y los tres son deliberados:

    - el indicador no está en el diccionario
    - está pero sin `tier`, o sea sin clasificar
    - está clasificado para otro país que el del evento

    El último es el que importa: aplicar el mapeo de EE.UU. a un dato de Chile
    publicaría el signo al revés. La pieza dice "sin clasificar" en vez de
    adivinar.
    """
    nombre = str(evento.get("nombre") or "").strip()
    if not nombre:
        return None

    clasificadas = cargar_clasificacion(ruta)
    for clave in _candidatas(nombre, clasificadas):
        entrada = clasificadas[clave]
        pais_evento = str(evento.get("pais") or "").strip()
        pais_entrada = str(entrada.get("pais") or "").strip()
        if pais_evento and pais_entrada and pais_evento != pais_entrada:
            continue
        return {**entrada, "_clave": clave}
    return None


def _tiene_consenso(evento: dict[str, Any]) -> bool:
    """¿El evento trae consenso publicado?

    Sin consenso no se puede juzgar si salió mejor o peor, así que no da pieza:
    el modo anticipación necesita algo contra qué comparar y el de resultado
    necesita un veredicto. Hoy esto descarta solo el lote de las 08:30 a un
    único candidato.
    """
    return bool(str(evento.get("forecast") or "").strip())


def dato_que_manda(
    eventos: list[dict[str, Any]],
    canal: str,
    ruta: Path | None = None,
) -> dict[str, Any] | None:
    """El único dato del lote que gobierna el momento de un canal, o `None`.

    **Las 08:30 no son un dato, son siete.** El 2026-09-03 el lote de EE.UU.
    traía peticiones de subsidio, subsidios continuados, exportaciones,
    importaciones, balanza comercial, productividad, costo laboral unitario y un
    discurso de Waller. Publicar eso es spam.

    La regla, en orden: que el indicador esté clasificado **para ese canal**, que
    traiga consenso, y de ahí el de **tier más bajo** (1 manda sobre 3). A igual
    tier, el que publica primero.

    Con el lote de ese día la regla selecciona exactamente uno: las peticiones de
    subsidio. Es el único de tier 2 con consenso que toca el canal de divisas.
    """
    candidatos = []
    for evento in eventos:
        if not _tiene_consenso(evento):
            continue
        clase = clasificar(evento, ruta)
        if clase is None:
            continue
        # **Una entrada sin mapeo direccional no puede ganar un momento.** Si no
        # puede decir qué le hace al mercado, la pieza no tendría qué escribir.
        # Encontrado contra el calendario real: "Atlanta Fed GDPNow" calzaba con
        # la entrada `Fed` (discursos y hoja de balance), que no lleva efecto
        # porque un discurso no tiene dirección, y así ganaba el momento de
        # cripto y reventaba al consumidor.
        if not clase.get("si_sale_sobre_consenso"):
            continue
        if canal not in (clase.get("canales") or []):
            continue
        candidatos.append((clase["tier"], str(evento.get("hora_servidor") or ""), evento))

    if not candidatos:
        return None
    candidatos.sort(key=lambda x: (x[0], x[1]))
    return candidatos[0][2]


def efecto_direccional(
    evento: dict[str, Any],
    ruta: Path | None = None,
) -> dict[str, Any] | None:
    """Qué le hace este dato al mercado si sale por encima del consenso.

    Es de **primer orden** y subordinado al régimen del Playbook, que es quien
    decide la dirección final. Ver el docstring del módulo.
    """
    clase = clasificar(evento, ruta)
    if clase is None:
        return None
    return clase.get("si_sale_sobre_consenso")


def puede_disparar_momento(evento: dict[str, Any], ruta: Path | None = None) -> bool:
    """¿Se puede programar un momento alrededor de este dato?

    El ISM y los PMI dicen **no**: son de organizaciones privadas que licencian
    su distribución, no están en FRED (medido el 2026-09-03: `NAPM` y `NMFCI`
    devuelven no disponible) y por tanto su hora de llegada depende de un tercero
    que no controlamos. Su pieza sale cuando el número **está**, no cuando el
    reloj dice.
    """
    clase = clasificar(evento, ruta)
    return bool(clase and clase.get("puede_disparar_momento"))
