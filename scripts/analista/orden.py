"""Gramática del pedido: lo único que el analista puede pedirle al bot.

El texto del usuario nunca llega a agy. Este módulo lo traduce a una `Orden` con
campos cerrados (pieza y argumentos de una lista conocida) y rechaza todo lo
demás con un motivo que el analista pueda corregir.

El informe es general e igual para todos: ya no se personaliza por trader
(spec 2026-10-08-informe-general-firmado-y-plan-design.md).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any


class PedidoInvalido(ValueError):
    """El pedido no calza con la gramática; el mensaje se le muestra al analista."""


PIEZAS = ("oportunidad", "seguimiento")
# Solo el director (config `admins`): rehace el análisis de un activo, o de todos los vigentes.
RECREAR = "recrear"
TODAS = "todas"
# Retirados el 2026-10-12 (spec oportunidad-semanal §2): responden con la ayuda.
RETIRADOS = ("activo", "calendario", "dato", "jornada")
SERVICIO = ("start", "ayuda", "id", "estado")

# Nombres en español que el equipo usa a diario. Los tickers del broker se
# resuelven solos (ver `_formas`); acá van solo los que no se parecen al ticker.
# Un test verifica que cada destino exista en el catálogo real.
ALIAS: dict[str, str] = {
    "dolar": "USDCLP",
    "peso": "USDCLP",
    "oro": "XAUUSD",
    "xau": "XAUUSD",
    "plata": "XAGUSD",
    "petroleo": "WTI.spot",
    "wti": "WTI.spot",
    "brent": "BRENT.spot",
    "cobre": "COPPER",
    "nasdaq": "US100.spot",
    "sp500": "US500.spot",
    "dowjones": "US30.spot",
    "dow": "US30.spot",
    "yen": "USDJPY",
    "euro": "EURUSD",
    "libra": "GBPUSD",
    "bitcoin": "BTCUSD",
    "ethereum": "ETHUSD",
}

PERSONALIZACION_RETIRADA = (
    "Los informes ya no se personalizan: son un análisis general que puedes "
    "compartir tal cual. Pide de nuevo sin «para …», por ejemplo /seguimiento oro."
)


@dataclass(frozen=True)
class Orden:
    pieza: str
    args: dict[str, Any] = field(default_factory=dict)
    # Cómo se dirige el ejecutivo a su cliente en el texto de WhatsApp. No entra en `clave_base`: la
    # pieza se reusa entre ejecutivos y el saludo se aplica al responder, no al preparar.
    saludo: str = ""

    def clave_base(self) -> str:
        """Identidad de la pieza para reusarla mientras está vigente."""
        partes = [self.pieza] + [f"{k}={self.args[k]}" for k in sorted(self.args)]
        return "|".join(partes)


def _plano(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower()


def _formas(ticker: str) -> set[str]:
    base = _plano(ticker)
    sin_sufijo = base.replace(".spot", "").replace(".us", "")
    return {base, sin_sufijo, sin_sufijo.lstrip("#"), sin_sufijo.replace("/", "")}


def resolver_activo(texto: str, universo: list[dict[str, Any]]) -> str:
    clave = re.sub(r"[\s/&]", "", _plano(texto))
    if clave in ALIAS:
        return ALIAS[clave]
    for activo in universo:
        formas = _formas(activo["ticker"]) | {re.sub(r"[\s/&]", "", _plano(activo.get("nombre", "")))}
        if clave in {re.sub(r"[\s/]", "", f) for f in formas}:
            return activo["ticker"]
    raise PedidoInvalido(f"No encontré el activo '{texto}'. Prueba con: oro, dolar, cobre, petroleo, brent, nasdaq o bitcoin.")


SALUDO_MAX = 60


_SIMBOLO = re.compile(r"^[A-Za-z#][A-Za-z0-9#._]{1,19}$")


def _activo_y_saludo(cuerpo: str, universo: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    """El activo es el prefijo más largo que se resuelve en el catálogo; lo que sigue es el saludo.

    Un activo que el catálogo no conoce no se rechaza acá: el terminal manda (spec 2026-10-16 §3).
    La primera palabra pasa como símbolo `libre` y el bot la canoniza contra MT5 al atender, para
    no tocar el terminal desde el hilo que escucha Telegram.
    """
    palabras = cuerpo.split()
    for n in range(len(palabras), 0, -1):
        try:
            ticker = resolver_activo(" ".join(palabras[:n]), universo)
        except PedidoInvalido:
            continue
        return {"ticker": ticker}, _limpiar_saludo(" ".join(palabras[n:]))
    if _SIMBOLO.match(palabras[0]):
        return {"ticker": palabras[0], "libre": True}, _limpiar_saludo(" ".join(palabras[1:]))
    resolver_activo(cuerpo, universo)  # levanta el error de siempre
    raise PedidoInvalido(f"No encontré el activo '{cuerpo}'.")  # inalcanzable


def _limpiar_saludo(texto: str) -> str:
    """Una línea corta y sin guiones largos: es texto de cliente (CLAUDE.md)."""
    limpio = " ".join(texto.replace("—", " ").replace("–", " ").split())
    if len(limpio) > SALUDO_MAX:
        raise PedidoInvalido(f"El saludo es muy largo (máximo {SALUDO_MAX} letras). Ejemplo: /seguimiento oro Juan")
    return limpio


def interpretar(texto: str, universo: list[dict[str, Any]] | None = None) -> Orden:
    texto = (texto or "").strip()
    if not texto.startswith("/"):
        raise PedidoInvalido("Escribe un comando, por ejemplo /seguimiento oro. Si no sabes cuál, escribe /ayuda.")

    cabeza, _, resto = texto.partition(" ")
    comando = cabeza[1:].split("@", 1)[0].lower()
    if comando in SERVICIO or comando in RETIRADOS:
        return Orden(pieza="ayuda" if comando in RETIRADOS else comando)
    if comando == RECREAR:
        cuerpo = resto.strip()
        if not cuerpo:
            raise PedidoInvalido("Falta el activo. Escribe por ejemplo: /recrear oro, o /recrear todas")
        if _plano(cuerpo) in (TODAS, "todos"):
            return Orden(pieza=RECREAR, args={"ticker": TODAS})
        if universo is None:
            import screener_gi as sc

            universo = sc.cargar_universo(solo_renderizables=False)
        args, _ = _activo_y_saludo(cuerpo, universo)
        return Orden(pieza=RECREAR, args=args)
    if comando not in PIEZAS:
        raise PedidoInvalido("Ese comando no existe. Escribe /ayuda y te muestro los que sí.")

    cuerpo = resto.strip()
    if re.search(r"(?:^|\s)para\s+\S", cuerpo, flags=re.IGNORECASE):
        raise PedidoInvalido(PERSONALIZACION_RETIRADA)

    entrada = None
    if comando == "seguimiento":
        cuerpo, entrada = _extraer_entrada(cuerpo)
    if not cuerpo:
        raise PedidoInvalido(f"Falta el activo. Escribe por ejemplo: /{comando} oro")
    if universo is None:
        import screener_gi as sc

        universo = sc.cargar_universo(solo_renderizables=False)
    args, saludo = _activo_y_saludo(cuerpo, universo)
    if entrada is not None:
        args["entrada"] = entrada
    return Orden(pieza=comando, args=args, saludo=saludo)


_ENTRADA = re.compile(r"(?:^|\s)entrada\s*[=:]\s*(\S+)", flags=re.IGNORECASE)


def _extraer_entrada(cuerpo: str) -> tuple[str, float | None]:
    """El precio al que entró el ejecutivo (`entrada=4062.5`), sacado del pedido antes de leer el saludo.

    Solo dígitos con un separador decimal (punto o coma), sin separador de miles: «4.062» sería
    ambiguo entre 4062 y 4,062.
    """
    m = _ENTRADA.search(cuerpo)
    if m is None:
        return cuerpo, None
    valor = m.group(1).replace(",", ".")
    if not re.fullmatch(r"\d+(?:\.\d+)?", valor) or float(valor) <= 0:
        raise PedidoInvalido("La entrada va como número, sin separador de miles. Ejemplo: /seguimiento oro entrada=4062.5")
    return (cuerpo[:m.start()] + " " + cuerpo[m.end():]).strip(), float(valor)
