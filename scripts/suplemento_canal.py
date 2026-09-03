#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""El suplemento de un canal que quedó sin activos publicables.

**El motivo por el que un canal queda vacío ya es contenido.** El 2026-09-03 a
las 12:11 el canal de divisas quedó en cero porque sus cuatro activos habían
consumido su recorrido del día, con el USD/JPY al 290 %. Eso es una lectura de
mercado, no un premio de consuelo, y explica algo que el cliente necesita
entender: que no operar también es una decisión.

**Por qué sale de las exclusiones y no de un generador de contenido.** El manual
del comando prohíbe el relleno con estas palabras: *"una tanda de 2 piezas bien
elegidas es mejor que una de 3 con un relleno"*. Un suplemento genérico sería
exactamente ese relleno. El que sale de acá se apoya en cifras que el escáner ya
midió y escribió, así que se gana el lugar en vez de ocuparlo.

**Y hay una razón estructural para que esto haga falta.** El recorrido disponible
es `ATR − rango_hoy`: una función que **solo baja** a medida que avanza el día.
Por construcción, un sistema cuyo criterio de selección exige espacio disponible
tiene su mejor momento al abrir y se apaga solo. A las 10:24 de ese día el canal
de divisas tenía cuatro activos entre 93 % y 290 %; a las 12:11 había quince
excluidos en todo el universo. No es un defecto del gate: es la métrica haciendo
lo que mide. La tarde necesita otro eje de contenido, y este es el primero.

**Lo que NO hace:** no promete niveles. El cierre canónico de tres escenarios
necesita soporte y resistencia, y este mensaje no los tiene; prometerlos sería
inventarlos. Cierra con el CTA al analista.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
MAPA_CONCEPTOS = RAIZ / "data" / "mapa_conceptos.json"
HISTORIAL = RAIZ / "data" / "historial_suplementos.json"

# Cuantos dias tiene que pasar un concepto sin repetirse en el MISMO canal.
#
# Dos semanas es la ventana porque hay seis conceptos tecnicos aplicables: con
# menos, un canal que se vacia seguido agota el repertorio y vuelve al primero
# antes de que nadie lo haya olvidado. Con mas, la mayoria de los canales
# quedaria sin parte educativa la mayor parte del tiempo.
VENTANA_CONCEPTO_DIAS = 14

# ─────────────────────────────────────────────────────────────────────────────
# Los motivos del escáner, traducidos a categoría y concepto
# ─────────────────────────────────────────────────────────────────────────────
# El concepto lo elige **el motivo**, no el azar: si todo el canal gastó su rango
# del día, el concepto que lo explica es la volatilidad. Eso hace que la parte
# educativa esté pegada a lo que de verdad pasó, en vez de ser una cápsula
# suelta que el ojo aprende a saltar.
#
# `publicable: False` es tan importante como el concepto. La confianza baja del
# modelo y un fallo del analizador son problemas de **nuestra** tubería, no
# lecturas de mercado: publicar "no pudimos leer el activo" no le sirve a nadie
# y suena a excusa. Esos canales quedan sin suplemento, que es la respuesta
# honesta.
CATEGORIAS: dict[str, dict[str, Any]] = {
    "ATR diario consumido": {
        "categoria": "recorrido_agotado",
        "concepto": "volatilidad-atr",
        "publicable": True,
    },
    "blackout por": {
        "categoria": "dato_en_curso",
        "concepto": "precio-descontado",
        "publicable": True,
    },
    "el Playbook prohibe": {
        "categoria": "setup_prohibido",
        "concepto": "riesgo",
        "publicable": True,
    },
    "feriado de": {
        "categoria": "mercado_cerrado",
        "concepto": "temporalidades",
        "publicable": True,
    },
    # Problemas nuestros, no del mercado.
    "el snapshot no declara la confianza": {
        "categoria": "modelo_sin_vista",
        "concepto": None,
        "publicable": False,
    },
    "la confianza del modelo": {
        "categoria": "modelo_sin_vista",
        "concepto": None,
        "publicable": False,
    },
}

# Los nombres de canal en voz de cliente. El slug es interno.
NOMBRE_CANAL = {
    "02_forex_divisas": "divisas",
    "03_commodities_materias_primas": "metales y energía",
    "04_indices_bursatiles": "índices",
    "05_acciones_etfs": "acciones y ETF",
    "06_criptoactivos": "criptomonedas",
}


def categoria_del_motivo(motivo: str) -> dict[str, Any] | None:
    """La categoría de un motivo de exclusión, o `None` si nadie la clasificó.

    Fail-closed: un gate nuevo sin categoría deja al canal sin suplemento, que es
    preferible a un concepto que no explica nada. El contrato
    `test_todo_gate_del_escaner_tiene_categoria_o_esta_declarado_no_publicable`
    lee los motivos del código del escáner y falla si aparece uno sin clasificar.
    """
    texto = (motivo or "").strip()
    if not texto:
        return None
    for prefijo, datos in CATEGORIAS.items():
        if prefijo.lower() in texto.lower():
            return dict(datos)
    return None


def _pct(motivo: str) -> int | None:
    """El porcentaje que trae el motivo de agotamiento, si lo trae.

    Sí, esto lee un número de un mensaje que escribimos nosotros, y ese
    acoplamiento es el que el contrato de arriba protege. La alternativa era que
    los gates devolvieran datos estructurados, que es mejor pero cambia la firma
    de los cinco: queda para su propio cambio.
    """
    m = re.search(r"(\d+)\s*%", motivo or "")
    return int(m.group(1)) if m else None


def resumen_del_canal(excluidos: list[dict[str, Any]]) -> dict[str, Any] | None:
    """La categoría dominante del canal y sus cifras, o `None` si no hay qué decir.

    Domina la que más activos explica. Si el canal quedó vacío por dos motivos
    distintos, el que afecta a más activos es el que describe la jornada.
    """
    clasificados = []
    for ex in excluidos or []:
        cat = categoria_del_motivo(str(ex.get("excluido") or ""))
        if cat and cat["publicable"]:
            clasificados.append((cat, ex))

    if not clasificados:
        return None

    conteo = Counter(cat["categoria"] for cat, _ in clasificados)
    dominante = conteo.most_common(1)[0][0]
    delgrupo = [(cat, ex) for cat, ex in clasificados if cat["categoria"] == dominante]

    porcentajes = [(_pct(str(ex.get("excluido"))), ex) for _, ex in delgrupo]
    con_pct = [(p, ex) for p, ex in porcentajes if p is not None]

    resumen: dict[str, Any] = {
        "categoria": dominante,
        "concepto": delgrupo[0][0]["concepto"],
        "activos": len(delgrupo),
        "tickers": [ex.get("ticker") for _, ex in delgrupo],
        "minimo_pct": None,
        "maximo_pct": None,
        "peor_activo": None,
    }
    if con_pct:
        con_pct.sort(key=lambda x: x[0])
        resumen["minimo_pct"] = con_pct[0][0]
        resumen["maximo_pct"] = con_pct[-1][0]
        resumen["peor_activo"] = con_pct[-1][1].get("nombre")
    return resumen


def _concepto(clave: str | None) -> dict[str, Any] | None:
    """La ficha del concepto desde `data/mapa_conceptos.json`."""
    if not clave or not MAPA_CONCEPTOS.exists():
        return None
    mapa = json.loads(MAPA_CONCEPTOS.read_text(encoding="utf-8"))
    return (mapa.get("conceptos") or {}).get(clave)


def cargar_historial(ruta: Path | None = None) -> list[dict[str, Any]]:
    """Lo que ya se publicó como suplemento, para no repetirlo.

    Se **versiona** a propósito, igual que `historial_senales.json`: es historia
    editorial de lo que el cliente ya leyó, no un archivo generado que se pueda
    regenerar. Sin él, la ventana anti repetición no sobrevive a un clon nuevo.
    """
    p = ruta or HISTORIAL
    if not p.exists():
        return []
    try:
        datos = json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    return datos if isinstance(datos, list) else (datos.get("suplementos") or [])


def concepto_en_cooldown(
    canal: str,
    clave: str | None,
    hoy: date,
    historial: list[dict[str, Any]] | None = None,
) -> bool:
    """¿Este concepto ya se publicó en este canal hace poco?

    **La ventana es por canal**, porque cada uno tiene su propia audiencia: que
    divisas haya visto la volatilidad no significa que cripto la haya visto.

    El riesgo que cierra es real y estaba en producción: el 2026-09-03 tres
    canales recibieron el **mismo** concepto porque los tres se vaciaron por el
    mismo motivo. Y va a pasar seguido, porque el recorrido disponible solo baja
    con el día y las tardes vacías no son la excepción.
    """
    if not clave:
        return False
    for entrada in historial if historial is not None else cargar_historial():
        if entrada.get("canal") != canal or entrada.get("clave") != clave:
            continue
        try:
            cuando = datetime.strptime(str(entrada.get("fecha")), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            continue
        if (hoy - cuando).days < VENTANA_CONCEPTO_DIAS:
            return True
    return False


def registrar_suplemento(
    sup: dict[str, Any] | None,
    hoy: date | None = None,
    ruta: Path | None = None,
) -> None:
    """Anota el concepto publicado, para que la ventana lo tome en cuenta.

    **Un suplemento sin concepto no se anota.** Si el concepto ya estaba en
    cooldown, no hay nada nuevo que registrar: anotarlo otra vez extendería la
    ventana sola, indefinidamente, y el concepto no volvería nunca.

    Se registra al **preparar** y no al despachar. Una tanda preparada y
    descartada gasta la ventana igual, y ese error va hacia el lado seguro:
    repetir de menos, no de más.
    """
    if not sup or not sup.get("concepto"):
        return
    p = ruta or HISTORIAL
    historial = cargar_historial(p)
    historial.append({
        "fecha": (hoy or date.today()).isoformat(),
        "canal": sup["canal"],
        "tipo": "concepto",
        "clave": sup["concepto"]["clave"],
        "categoria": sup["resumen"]["categoria"],
    })
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(historial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def suplemento(
    canal: str,
    excluidos: list[dict[str, Any]],
    hoy: date | None = None,
    historial: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """El suplemento de un canal, o `None` si no se lo gana.

    Devuelve datos, no texto: el mensaje se arma aparte, igual que en el resto
    del repo.

    **Si el concepto está en cooldown se cae el concepto, no la pieza.** La cifra
    del estado ES la novedad: hoy el USD/JPY al 290 % y mañana otra. Lo que se
    gasta con la repetición es la parte educativa.
    """
    resumen = resumen_del_canal(excluidos)
    if resumen is None:
        return None

    if concepto_en_cooldown(canal, resumen["concepto"], hoy or date.today(), historial):
        resumen = {**resumen, "concepto": None}

    ficha = _concepto(resumen["concepto"])
    return {
        "canal": canal,
        "canal_es": NOMBRE_CANAL.get(canal, "este mercado"),
        "resumen": resumen,
        "concepto": ({"clave": resumen["concepto"], **ficha} if ficha else None),
    }


# ─────────────────────────────────────────────────────────────────────────────
# El mensaje
# ─────────────────────────────────────────────────────────────────────────────
_ESTADO = {
    "recorrido_agotado": (
        "Hoy no hay niveles que valga la pena mirar en {canal}, y el motivo es "
        "información en sí mismo: *los {n} activos del canal ya recorrieron lo "
        "que suelen moverse en un día completo*."
    ),
    "dato_en_curso": (
        "Hoy no publicamos niveles de {canal} porque hay un dato de alto impacto "
        "en curso: el precio se está reacomodando y cualquier nivel que diéramos "
        "quedaría viejo en minutos."
    ),
    "setup_prohibido": (
        "Hoy no hay operativa que comunicar en {canal}: el escenario de fondo "
        "deja fuera justamente las jugadas que la lectura técnica sugeriría."
    ),
    "mercado_cerrado": (
        "Hoy el mercado de {canal} está cerrado por feriado, así que no hay "
        "precio que leer."
    ),
}


def construir_mensaje_suplemento(sup: dict[str, Any]) -> str:
    """El mensaje de WhatsApp del suplemento.

    No lleva el cierre canónico de tres escenarios porque no tiene niveles con
    que armarlo. Cierra con el CTA al analista, que es lo que corresponde a una
    pieza sin operativa.
    """
    r = sup["resumen"]
    canal = sup["canal_es"]

    plantilla = _ESTADO.get(r["categoria"])
    estado = plantilla.format(canal=canal, n=r["activos"]) if plantilla else (
        f"Hoy no hay niveles publicables en {canal}."
    )

    lineas = [
        f"📊 *{canal.upper()} · hoy no hay niveles, y el motivo importa*",
        "━━━━━━━━━━━━━━━━━━━",
        estado,
    ]

    if r["maximo_pct"] is not None and r["peor_activo"]:
        # La coma se aplica SOLO al numero. Un `replace` sobre la frase entera
        # corrompe cualquier nombre con punto, y el catalogo tiene varios
        # (`US100.spot`, `GLD.US`, `WTI.spot`).
        veces = f"{r['maximo_pct'] / 100:.1f}".replace(".", ",")
        detalle = (
            f"El caso extremo es {r['peor_activo']}, que se movió "
            f"{veces} veces su rango habitual"
        )
        if r["minimo_pct"] is not None:
            detalle += f". El que menos, un {r['minimo_pct']}%"
        lineas.append(detalle + ".")

    if sup.get("concepto"):
        c = sup["concepto"]
        # `explicacion` antes que `glosario`: el segundo es la linea del mensaje
        # fijado del grupo, y ahi una linea es lo correcto. Acá hace falta un
        # parrafo que ensene, y el de volatilidad decia "clave en USD/CLP", que
        # salio publicado en el canal de indices donde no aplica.
        texto = c.get("explicacion") or c.get("glosario") or ""
        lineas += [
            "━━━━━━━━━━━━━━━━━━━",
            f"📚 *{c['nombre']}*",
            texto,
        ]

    lineas += [
        "━━━━━━━━━━━━━━━━━━━",
        "No operar cuando no hay espacio también es una decisión, y es la que "
        "protege la cuenta. ¿Dudas? Consulta a tu analista.",
    ]
    return "\n".join(lineas)
