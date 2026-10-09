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


PIEZAS = ("activo", "calendario", "dato", "jornada", "oportunidad", "semanal", "seguimiento")
SERVICIO = ("start", "ayuda", "id", "estado")

# Nombres en español que el equipo usa a diario. Los tickers del broker se
# resuelven solos (ver `_formas`); acá van solo los que no se parecen al ticker.
# Un test verifica que cada destino exista en el catálogo real.
ALIAS: dict[str, str] = {
    "dolar": "USDCLP",
    "peso": "USDCLP",
    "oro": "XAUUSD",
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
    "compartir tal cual. Pide de nuevo sin «para …», por ejemplo /activo oro."
)
_BUSQUEDA_DATO = re.compile(r"^[a-z0-9 ]{2,40}$")


@dataclass(frozen=True)
class Orden:
    pieza: str
    args: dict[str, Any] = field(default_factory=dict)

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
    raise PedidoInvalido(f"No reconozco el activo «{texto}». Prueba con el ticker, por ejemplo /activo usdclp.")


def interpretar(texto: str, universo: list[dict[str, Any]] | None = None) -> Orden:
    texto = (texto or "").strip()
    if not texto.startswith("/"):
        raise PedidoInvalido("Los pedidos empiezan con un comando. Escribe /ayuda para ver cuáles hay.")

    cabeza, _, resto = texto.partition(" ")
    comando = cabeza[1:].split("@", 1)[0].lower()
    if comando in SERVICIO:
        return Orden(pieza=comando)
    if comando not in PIEZAS:
        raise PedidoInvalido(f"No existe el comando /{comando}. Escribe /ayuda para ver cuáles hay.")

    cuerpo = resto.strip()
    if re.search(r"(?:^|\s)para\s+\S", cuerpo, flags=re.IGNORECASE):
        raise PedidoInvalido(PERSONALIZACION_RETIRADA)

    if comando in ("activo", "semanal", "seguimiento"):
        if not cuerpo:
            raise PedidoInvalido(f"Falta el activo. Ejemplo: /{comando} oro")
        if universo is None:
            import screener_gi as sc

            universo = sc.cargar_universo(solo_renderizables=False)
        args: dict[str, Any] = {"ticker": resolver_activo(cuerpo, universo)}
    elif comando == "oportunidad":
        # Sin argumentos: el foco lo elige el escáner, no quien lo pide.
        args = {}
    elif comando == "calendario":
        alcance = _plano(cuerpo) or "hoy"
        if alcance not in ("hoy", "semana"):
            raise PedidoInvalido("El calendario es /calendario hoy o /calendario semana.")
        args = {"alcance": alcance}
    elif comando == "dato":
        busqueda = _plano(cuerpo) or "ultimo"
        if not _BUSQUEDA_DATO.match(busqueda):
            raise PedidoInvalido("Nombra el dato con letras y números, por ejemplo /dato ipc.")
        args = {"busqueda": busqueda}
    else:
        momento = _plano(cuerpo) or None
        if momento not in (None, "apertura", "cierre"):
            raise PedidoInvalido("La jornada es /jornada apertura o /jornada cierre.")
        args = {"momento": momento}

    return Orden(pieza=comando, args=args)
