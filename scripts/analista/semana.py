"""La semana tiene un tema: el mapa del lunes y la víspera de un dato fuerte, para el ejecutivo.

Material interno del bot de Telegram (spec 2026-10-18-alerta-semana-ejecutivos): no es contenido para
clientes. Dos reglas lo sostienen:

1. **Todo sale de lo que ya existe y nada lo redacta un modelo.** Eventos y hora, del calendario ya en
   Santiago (no se reconvierte, issue #38); activos y sentido, del glosario (`tier`,
   `si_sale_sobre_consenso`); lo que se conversa y lo que no se dice, de `config/guia_eventos.json`.
   Si el glosario no declara el efecto, el evento sale sin línea de efecto: callarse es más honesto.
2. **Escenarios y no órdenes.** Nunca «compra» ni «el dólar va a subir»: se dice «tiende a» y se invita
   a revisar la exposición.

Funciones puras: no leen la red ni el reloj.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any

from analista import RAIZ
from analista import agenda as ag
from analista import macro_seguimiento as mac

RUTA_GUIA = RAIZ / "config" / "guia_eventos.json"
AVISO_RIESGO = ("⚠️ Operar con CFD conlleva riesgo: el apalancamiento amplifica tanto las ganancias como "
                "las pérdidas.")

# Del más fuerte al más débil: desempata el tema cuando dos datos tienen el mismo tier.
TIPOS = ("tasas", "inflacion", "empleo", "actividad", "petroleo")
PATRONES = {
    "tasas": r"INTEREST RATE DECISION|\bFOMC\b|MONETARY POLICY MEETING",
    "inflacion": r"\bCPI\b|\bPCE\b|\bPPI\b|INFLATION",
    "empleo": r"PAYROLLS|UNEMPLOYMENT|JOBLESS|JOB OPENINGS|JOLTS|\bADP\b|AVERAGE HOURLY EARNINGS|EMPLOYMENT CHANGE",
    "actividad": r"\bPMI\b|\bISM\b|\bGDP\b|IMACEC|GROSS DOMESTIC",
    "petroleo": r"CRUDE OIL INVENTORIES|\bOPEC\b",
}
# Actas y discursos enganchan con la entrada del banco central (la sigla está en el título) pero no
# deciden nada ni tienen consenso: anunciarlos como decisión de tasas sería falso.
NO_ES_DATO = r"MINUTES|SPEAKS|SPEECH|TESTIFIES"
# El glosario describe a EE.UU. y a Chile: el tier de un dato de otro país no se presta.
PAISES_DEL_TEMA = ("United States", "Chile")
# Entre datos del mismo tipo y día, el que da el nombre al informe (el de empleo es Nóminas, no la tasa).
PRINCIPALES = r"PAYROLLS|INTEREST RATE DECISION|\bCPI\b|\bPCE\b|\bGDP\b|\bPMI\b|IMACEC"
TIER_ALTO = 2          # tier 1 y 2 del glosario pueden ser el tema; el 3 es contexto
MAXIMO_MAPA = 5
# Series que salen todas las semanas: son contexto del calendario, no el tema. Solo mandan si no hay otra cosa.
SEMANALES = r"JOBLESS CLAIMS|UNEMPLOYMENT CLAIMS|CRUDE OIL INVENTORIES"

ACTIVOS = {"dolar": ("dólar", "el dólar", "tiende"), "oro": ("oro", "el oro", "tiende"),
           "indices": ("índices", "los índices", "tienden"), "usdclp": ("USD/CLP", "el USD/CLP", "tiende"),
           "petroleo": ("petróleo", "el petróleo", "tiende")}
# El activo que el botón de la víspera pide: petróleo manda en su dato; luego el dólar chileno, que es
# el que más miran nuestros clientes; luego oro e índices.
ACTIVO_DEL_BOTON = (("petroleo", "WTI.spot"), ("usdclp", "USDCLP"), ("oro", "XAUUSD"), ("indices", "US100.spot"))
# Nombres que el glosario trae sin su sigla explicada o sin decir qué decide.
NOMBRES = {"Comité de mercado abierto de la Fed": "Decisión de tasas de la Reserva Federal (Fed) de EE.UU."}


def guia() -> dict[str, dict[str, Any]]:
    datos = json.loads(RUTA_GUIA.read_text(encoding="utf-8"))
    return {k: v for k, v in datos.items() if not k.startswith("_")}


# ───────────────────────────────────────────────────────────── clasificar


def _dic(ev: dict[str, Any]) -> dict[str, Any]:
    return ev.get("diccionario") or {}


def _tier(ev: dict[str, Any]) -> int:
    try:
        return int(_dic(ev).get("tier") or 9)
    except (TypeError, ValueError):
        return 9


def tipo_de_evento(ev: dict[str, Any]) -> str | None:
    """El tipo de la guía al que pertenece el evento; None si el glosario no lo conoce o no es del tema."""
    if not _dic(ev).get("tier") or ev.get("pais") not in PAISES_DEL_TEMA:
        return None
    nombre = str(ev.get("nombre", "")).upper()
    if re.search(NO_ES_DATO, nombre):
        return None
    return next((t for t in TIPOS if re.search(PATRONES[t], nombre)), None)


def _efectos(ev: dict[str, Any]) -> dict[str, str]:
    """Qué hace el dato con cada activo, según el glosario. Vacío si no lo declara o no aplica al país.

    Las entradas del glosario describen datos de EE.UU., salvo las chilenas, que declaran neutro al dólar
    global. «CPI» en Chile engancha con la entrada de EE.UU. (el dólar sube) y el PIB de China con la
    estadounidense: esa lectura no vale para ellos, y afirmarla sería inventar el efecto.
    """
    efecto = {k: v for k, v in (_dic(ev).get("si_sale_sobre_consenso") or {}).items() if k in ACTIVOS}
    pais = ev.get("pais")
    if pais == "United States" or (pais == "Chile" and efecto.get("dolar") == "neutro"):
        return efecto
    return {}


def _fuerte(ev: dict[str, Any]) -> bool:
    return tipo_de_evento(ev) is not None and _tier(ev) <= TIER_ALTO


def _clave_de_tema(ev: dict[str, Any]) -> tuple:
    cuando = ag._cuando(ev)
    semanal = bool(re.search(SEMANALES, str(ev.get("nombre", "")).upper()))
    principal = not re.search(PRINCIPALES, str(ev.get("nombre", "")).upper())
    return (semanal, _tier(ev), TIPOS.index(tipo_de_evento(ev)), principal,
            cuando.timestamp() if cuando else float("inf"))


def tema_de_la_semana(eventos: list[dict[str, Any]]) -> dict[str, Any]:
    """Manda el dato de menor tier; en empate, tasas sobre inflación, empleo, actividad y petróleo."""
    fuertes = [e for e in eventos if _fuerte(e)]
    if not fuertes:
        return {"tipo": None, "titular": "Semana tranquila", "tranquila": True, "evento": None}
    elegido = min(fuertes, key=_clave_de_tema)
    tipo = tipo_de_evento(elegido)
    return {"tipo": tipo, "titular": guia()[tipo]["titular"], "tranquila": False, "evento": elegido}


def activo_mas_afectado(ev: dict[str, Any]) -> str | None:
    """El símbolo MT5 que el botón de la víspera le pide al bot, o None si el glosario no declara efecto."""
    efecto = _efectos(ev)
    return next((ticker for clave, ticker in ACTIVO_DEL_BOTON if efecto.get(clave) in ("sube", "baja")), None)


# ───────────────────────────────────────────────────────────── redactar


def _nombre(ev: dict[str, Any]) -> str:
    base = str(_dic(ev).get("nombre_es") or ev.get("nombre", ""))
    if base in NOMBRES:
        return NOMBRES[base]
    return f"{base} {mac.PAISES.get(ev.get('pais', ''), 'de ' + str(ev.get('pais', '')))}"


def _cuando_txt(ev: dict[str, Any]) -> str:
    cuando = ag._cuando(ev)
    return f"{ag.dia_corto(cuando)} · {ag._hora(cuando)}"


def _linea(ev: dict[str, Any]) -> str:
    activos = [ACTIVOS[k][0] for k, v in _efectos(ev).items() if v in ("sube", "baja", "mixto")]
    return f"• {_cuando_txt(ev)} · {_nombre(ev)}" + (f" · mueve: {', '.join(activos)}" if activos else "")


def momento(ev: dict[str, Any]) -> tuple:
    """Un informe es un solo lugar: Nóminas, tasa de desempleo y salarios salen juntos y cuentan una vez."""
    return (tipo_de_evento(ev), ev.get("pais"), ag._cuando(ev).date())


def _elegidos(eventos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Hasta cinco datos fuertes, uno por tipo, país y día, en orden de reloj."""
    vistos: set[tuple] = set()
    unicos = []
    for ev in sorted((e for e in eventos if _fuerte(e) and ag._cuando(e)), key=_clave_de_tema):
        if momento(ev) not in vistos:
            vistos.add(momento(ev))
            unicos.append(ev)
    return sorted(unicos[:MAXIMO_MAPA], key=lambda e: ag._cuando(e))


def armar_mapa(eventos: list[dict[str, Any]], ahora: datetime) -> str:
    """El mensaje del lunes: el tema, los datos fuertes con su hora de Chile y una línea para conversar."""
    ahora = ahora.astimezone(ag.SANTIAGO)
    tema = tema_de_la_semana(eventos)
    if tema["tranquila"]:
        cuerpo = ["Ningún dato de los próximos 7 días marca la semana con claridad (calendario de EE.UU., "
                  "Chile, China y la Zona Euro).", "",
                  "💬 Qué conversar: es una buena semana para ponerte al día con tus clientes y revisar cómo "
                  "viene su cartera."]
    else:
        cuerpo = ["Lo que viene, en hora de Chile:", *[_linea(e) for e in _elegidos(eventos)], "",
                  f"💬 Qué conversar: {guia()[tema['tipo']]['conversar']}"]
    desde, hasta = ag.dia_corto(ahora), ag.dia_corto(ahora + timedelta(days=ag.VENTANA_DIAS))
    return "\n".join([f"📅 {tema['titular']}", f"Del {desde} al {hasta}.", "", *cuerpo, "", AVISO_RIESGO])


def _frase_de_efecto(ev: dict[str, Any]) -> str:
    partes = []
    for clave, verbo in _efectos(ev).items():
        if verbo in ("sube", "baja"):
            _, art, tiende = ACTIVOS[clave]
            partes.append(f"{art} {tiende} a {'subir' if verbo == 'sube' else 'bajar'}")
    if not partes:
        return ""
    unidas = partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + " y " + partes[-1]
    return f"📊 Si sale sobre lo esperado, {unidas}; si sale bajo lo esperado, lo contrario."


def armar_vispera(ev: dict[str, Any], ahora: datetime) -> str:
    """Cinco líneas como máximo: cuándo sale, qué suele hacer, qué conversar, qué no decir y el aviso."""
    tipo = tipo_de_evento(ev)
    if tipo is None:
        raise ValueError(f"el evento {ev.get('nombre')!r} no es del tema de la semana")
    ahora = ahora.astimezone(ag.SANTIAGO)
    cuando = ag._cuando(ev)
    dia = "Mañana" if (cuando.date() - ahora.date()).days == 1 else f"El {ag.dia_corto(cuando)}"
    nombre = _nombre(ev)
    lineas = [f"📍 {dia} a las {ag._hora(cuando)} sale {nombre}{'' if nombre.endswith('.') else '.'}",
              _frase_de_efecto(ev),
              f"💬 Qué conversar: {guia()[tipo]['conversar']}", f"🚫 Qué no decir: {guia()[tipo]['no_decir']}",
              AVISO_RIESGO]
    return "\n".join(x for x in lineas if x)
