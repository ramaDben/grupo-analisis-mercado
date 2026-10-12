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

**Desde S8 del enchufe solo lo disparan el blackout y el feriado.** Nació con el
gate de agotamiento del ATR, que vaciaba los canales por la tarde, y ese gate se
borró: el ranking y las exclusiones técnicas son de la estrategia, y la cobertura
fija garantiza una pieza en cada canal cubierto.

**Lo que NO hace:** no promete niveles. El cierre canónico de tres escenarios
necesita soporte y resistencia, y este mensaje no los tiene; prometerlos sería
inventarlos. Cierra con el CTA al analista.
"""

from __future__ import annotations

import json
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
# `publicable: False` es tan importante como el concepto. Un fallo del
# analizador es un problema de **nuestra** tubería, no una lectura de mercado:
# publicar "no pudimos leer el activo" no le sirve a nadie y suena a excusa. Esos canales quedan sin suplemento, que es la respuesta
# honesta.
CATEGORIAS: dict[str, dict[str, Any]] = {
    # El activo ya se publicó hoy: el canal tuvo su pieza, y decirle al cliente que
    # el mercado agotó su rango sería inventar el motivo. Hasta S8 caía en la
    # categoría del ATR consumido, que salió con ese gate.
    "ya salio en una corrida anterior": {"categoria": "ya_publicado", "concepto": None, "publicable": False},
    "blackout por": {
        "categoria": "dato_en_curso",
        "concepto": "precio-descontado",
        "publicable": True,
    },
    "feriado de": {
        "categoria": "mercado_cerrado",
        "concepto": "temporalidades",
        "publicable": True,
    },
    # Exclusiones de la estrategia activa (enchufe, fase 2). No se publican como
    # suplemento: son motivos técnicos y no una lectura para el cliente, y la
    # cobertura fija ya garantiza una pieza por canal cubierto.
    "sin líneas trazables": {"categoria": "sin_estructura", "concepto": None, "publicable": False},
    "va contra la secuencia": {"categoria": "contra_secuencia", "concepto": None, "publicable": False},
    "está en prueba": {"categoria": "en_prueba", "concepto": None, "publicable": False},
    # Un activo que no se pudo leer es un problema nuestro de datos, no contenido.
    "no se pudo leer": {"categoria": "sin_datos", "concepto": None, "publicable": False},
}

ACTIVOS_ANCLA_CANAL: dict[str, dict[str, Any]] = {
    "02_forex_divisas": {
        "ticker": "USDCLP",
        "nombre": "Dólar / Peso Chileno",
        "rotulo": "USD/CLP",
        "categoria": "DIVISAS",
    },
    "03_commodities_materias_primas": {
        "ticker": "XAUUSD",
        "nombre": "Oro",
        "rotulo": "XAU/USD",
        "categoria": "COMMODITIES",
    },
    "04_indices_bursatiles": {
        "ticker": "US100.spot",
        "nombre": "Nasdaq 100",
        "rotulo": "US100 (Nasdaq)",
        "categoria": "ÍNDICES",
    },
    "05_acciones_etfs": {
        "ticker": "#NVDA",
        "nombre": "NVIDIA",
        "rotulo": "NVDA",
        "categoria": "ACCIONES",
    },
    "06_criptoactivos": {
        "ticker": "BTCUSD",
        "nombre": "Bitcoin",
        "rotulo": "BTC/USD",
        "categoria": "CRIPTOMONEDAS",
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

ENCUESTAS_CIERRE_CANAL: dict[str, dict[str, Any]] = {
    "02_forex_divisas": {
        "pregunta": "¿Cómo proyectas la apertura del dólar (USD/CLP) mañana?",
        "opciones": ["🟢 Apertura alcista", "🟡 En rango / neutral", "🔴 Corrección a la baja"],
        "permitir_multiples": False,
    },
    "03_commodities_materias_primas": {
        "pregunta": "¿Qué dirección esperas para el Oro (XAU/USD) en la sesión asiática?",
        "opciones": ["📈 Rebote comprador", "➡️ Consolidación lateral", "📉 Presión vendedora"],
        "permitir_multiples": False,
    },
    "04_indices_bursatiles": {
        "pregunta": "Cerramos Wall Street: ¿cómo evalúas la jornada bursátil de hoy?",
        "opciones": ["🔥 Sesión compradora sólida", "⚖️ Toma de ganancias / mixta", "⚠️ Mayor cautela"],
        "permitir_multiples": False,
    },
    "05_acciones_etfs": {
        "pregunta": "Tras el cierre de sesión: ¿qué sector ves con mayor atractivo para mañana?",
        "opciones": ["💻 Tecnológicas y Semiconductores", "🏭 Industriales y Financieras", "🛡️ Defensivas y Renta Fija"],
        "permitir_multiples": False,
    },
    "06_criptoactivos": {
        "pregunta": "¿Logrará Bitcoin defender sus soportes durante la noche?",
        "opciones": ["🛡️ Sí, defenderá el nivel", "⚠️ Quiebre correctivo", "➡️ Rango sin tendencia"],
        "permitir_multiples": False,
    },
}


def encuesta_cierre(canal: str) -> dict[str, Any] | None:
    """La encuesta nativa de cierre correspondiente al canal, si tiene configurada."""
    enc = ENCUESTAS_CIERRE_CANAL.get(canal)
    if not enc:
        return None
    return {
        "pregunta": enc["pregunta"],
        "opciones": list(enc["opciones"]),
        "permitir_multiples": enc.get("permitir_multiples", False),
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

    return {
        "categoria": dominante,
        "concepto": delgrupo[0][0]["concepto"],
        "activos": len(delgrupo),
        "tickers": [ex.get("ticker") for _, ex in delgrupo],
    }


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
    mismo motivo.
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
    ancla_base = ACTIVOS_ANCLA_CANAL.get(canal, {
        "ticker": "USDCLP",
        "nombre": "Dólar / Peso Chileno",
        "rotulo": "USD/CLP",
        "categoria": "DIVISAS",
    })
    activo_ancla = dict(ancla_base)
    for ex in excluidos or []:
        if ex.get("ticker") == ancla_base["ticker"]:
            activo_ancla["nombre"] = ex.get("nombre", ancla_base["nombre"])
            break

    return {
        "canal": canal,
        "canal_es": NOMBRE_CANAL.get(canal, "este mercado"),
        "resumen": resumen,
        "concepto": ({"clave": resumen["concepto"], **ficha} if ficha else None),
        "activo_ancla": activo_ancla,
    }


# ─────────────────────────────────────────────────────────────────────────────
# El mensaje
# ─────────────────────────────────────────────────────────────────────────────
_ESTADO = {
    "dato_en_curso": (
        "El mercado de {canal} asimila en este momento la publicación de catalizadores macroeconómicos de alto impacto, "
        "por lo que los niveles técnicos se encuentran en proceso de reajuste y confirmación institucional."
    ),
    "mercado_cerrado": (
        "La sesión oficial de {canal} se encuentra cerrada por feriado de mercado, "
        "manteniendo la estructura técnica previa a la espera de la reapertura de operaciones."
    ),
}


def construir_mensaje_suplemento(sup: dict[str, Any], es_cierre: bool = False) -> str:
    """El mensaje de WhatsApp del suplemento o balance de sesión.

    En cierre presenta un balance en tres tiempos comentando qué pasó, qué está pasando
    ahora y qué vigilar para la próxima apertura, anclado a un activo representativo.
    """
    r = sup["resumen"]
    canal = sup["canal_es"]

    if es_cierre:
        ancla = sup.get("activo_ancla") or {}
        rotulo_ancla = ancla.get("rotulo") or ancla.get("nombre") or canal.title()

        lineas = [
            f"📊 *{canal.upper()} · Balance de Cierre de Jornada*",
            f"🎯 *Activo en foco*: *{rotulo_ancla}*",
            "━━━━━━━━━━━━━━━━━━━",
            "1️⃣ *QUÉ PASÓ EN LA JORNADA*",
        ]
        if r["categoria"] == "dato_en_curso":
            lineas.append(
                f"Cerramos la jornada de {canal} tras asimilar el impacto de los datos macroeconómicos del día."
            )
        elif r["categoria"] == "mercado_cerrado":
            lineas.append(
                f"Jornada sin actividad operativa en {canal} debido al feriado de mercado."
            )
        else:
            lineas.append(
                f"Cerramos la jornada en {canal} con el mercado consolidando posiciones sin rupturas de rango."
            )

        lineas.extend([
            "",
            "2️⃣ *QUÉ ESTÁ PASANDO AHORA*",
            f"El cierre de sesión deja a {rotulo_ancla} con su estructura a la vista: "
            "las líneas que importan para la próxima apertura están en el gráfico.",
            "",
            "3️⃣ *QUÉ VIGILAR PARA LA PRÓXIMA APERTURA*",
            "El cierre de sesión es momento de evaluar la estructura del precio para anticipar "
            "la apertura del siguiente ciclo sin forzar entradas innecesarias.",
            "━━━━━━━━━━━━━━━━━━━",
            "💡 *En la imagen adjunta encuentras el gráfico TradingView™ con los niveles de la jornada.*",
            "━━━━━━━━━━━━━━━━━━━",
            "A continuación abrimos la encuesta de la jornada para conocer la visión de la comunidad 👇",
        ])
        return "\n".join(lineas)

    plantilla = _ESTADO.get(r["categoria"])
    estado = plantilla.format(canal=canal, n=r["activos"]) if plantilla else (
        f"El mercado de {canal} se encuentra en zona de balance institucional."
    )

    lineas = [
        f"📊 *{canal.upper()} · Contexto Operativo y Zonas de Balance*",
        "━━━━━━━━━━━━━━━━━━━",
        estado,
    ]

    if sup.get("concepto"):
        c = sup["concepto"]
        texto = c.get("explicacion") or c.get("glosario") or ""
        lineas += [
            "━━━━━━━━━━━━━━━━━━━",
            f"📚 *{c['nombre']}*",
            texto,
        ]

    canal_slug = sup.get("canal", "")
    if "forex" in canal_slug or "divisa" in canal_slug:
        modulos = "Módulo 5 y Módulo 8"
    elif "commodit" in canal_slug:
        modulos = "Módulo 7 y Módulo 10"
    elif "indice" in canal_slug or "bursatil" in canal_slug:
        modulos = "Módulo 4 y Módulo 9"
    elif "accion" in canal_slug:
        modulos = "Módulo 4 y Módulo 9"
    elif "cripto" in canal_slug or "crypto" in canal_slug:
        modulos = "Módulo 6 y Módulo 10"
    else:
        modulos = "Módulo 7 y Módulo 10"

    lineas += [
        "━━━━━━━━━━━━━━━━━━━",
        "💬 *Te compartimos nuestra lectura: ¿cuál es tu visión para la sesión?*",
        "No operar cuando los rangos están comprimidos o a la espera de volumen también es una decisión estratégica que protege el capital. ¿Prefieres esperar la definición de rango o buscas entradas en los extremos? ¡Coméntanos en el grupo cómo lo ves o consúltalo con tu analista en el chat!",
        "",
        f"📖 *Para profundizar en la gestión del riesgo y cómo dimensionar tus posiciones en fases de compresión, consulta el {modulos} de nuestro Manual de Operaciones.*",
    ]
    return "\n".join(lineas)

