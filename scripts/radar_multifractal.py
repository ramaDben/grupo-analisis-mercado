"""Radar multifractal: qué líneas tocó cada activo y cuáles va a tocar, en 1H, 4H y 1D.

Spec `docs/superpowers/specs/2026-10-26-radar-multifractal-design.md` §4, §6 y §8. Es el
orquestador: arma el universo, verifica la cuenta, lee las velas, le pide al motor la
lectura de cada marco (`estrategia.tori.radar.leer_marco`) y escribe una página HTML.
No traza nada propio: toda la técnica vive en `scripts/estrategia/`.

Es una herramienta interna del director. **No publica ni manda nada a ningún canal**:
su única salida es un archivo en `data/radar/` (gitignoreado).

    uv run --with MetaTrader5 python scripts/radar_multifractal.py
    uv run --with MetaTrader5 python scripts/radar_multifractal.py --simbolos XAUUSD,USDCLP --sin-abrir

Tres decisiones que conviene no revertir:

1. **La cuenta se verifica antes de leer.** El radar lee en vivo y no tiene sello en
   archivo, así que compara `account_info().login` con `config/cuenta_mt5.json`. Si no
   coincide no escanea: una matriz leída sobre otra cuenta es la de otro instrumento.
2. **Observación de Mercado se registra antes y se restaura en un `finally`.**
   `mt5_client.get_rates` hace `symbol_select(True)` para poder leer, y el radar recorre
   todo el universo: sin restaurar, el terminal del director quedaría con 137 símbolos
   abiertos.
3. **Una falla es de un marco o de un símbolo, nunca del escaneo.** Cada una queda en la
   página con su motivo; un radar que descarta en silencio no se puede auditar.
"""
from __future__ import annotations

import argparse
import sys
import time
import webbrowser
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

_RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(_RAIZ / "src"), str(_RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from estrategia.fuente import DURACION, RELOJ, cierre_santiago, offset_servidor, velas_mt5  # noqa: E402
from estrategia.tori.parametros import PARAMETROS  # noqa: E402
from estrategia.tori.radar import MARCOS_RADAR, RADAR_MARCOS, LecturaMarco, leer_marco  # noqa: E402
from guardrails.cuenta import cuenta_correcta  # noqa: E402
from market_data_mcp import mt5_client  # noqa: E402
from radar_html import Escaneo, Falla, Fila, render, render_error  # noqa: E402
from radar_paridad import comparar, leer_objetos, ruta_objetos  # noqa: E402

SANTIAGO = ZoneInfo("America/Santiago")
SALIDA = _RAIZ / "data" / "radar"


@dataclass(frozen=True)
class Simbolo:
    ticker: str
    digits: int
    categoria: str            # primer tramo de symbol_info.path ("Forex", "Stocks"...)
    visible: bool             # estaba en Observación de Mercado antes de empezar


def _ahora_santiago() -> datetime:
    return datetime.now(SANTIAGO)


def _terminal():
    """El módulo MetaTrader5. Va en una función para que los tests le pongan uno falso."""
    import MetaTrader5 as mt5

    return mt5


def universo(mt5) -> list[Simbolo]:
    """Los símbolos operables del terminal: `trade_mode` FULL, como `simulador_gi.py`.

    Un símbolo en solo cierre o deshabilitado no tiene a quién avisarle que toca una
    línea. La visibilidad se toma acá, antes de cualquier lectura, porque leer lo
    selecciona y después ya no se sabe cómo estaba.
    """
    full = mt5.SYMBOL_TRADE_MODE_FULL
    return [
        Simbolo(s.name, int(s.digits), str(s.path or "").split("\\")[0], bool(s.visible))
        for s in (mt5.symbols_get() or ())
        if s.trade_mode == full
    ]


def _cuenta(mt5) -> int:
    info = mt5.account_info()
    try:
        return int(info.login)
    except (AttributeError, TypeError, ValueError):
        return 0


AVISO_SIN_RELOJ = "no se pudo medir el reloj del servidor: las horas de cierre no se muestran"
AVISO_RELOJ_SUSTITUTO = "reloj del servidor medido con {ticker}: revisa las horas"
# Ningún huso horario va más de 14 h adelante o atrás de UTC. Un desfase mayor medido con
# un símbolo cualquiera es un tick viejo (un mercado cerrado desde hace días), no un reloj.
DESFASE_MAX_S = 14 * 3600


class SinUniverso(Exception):
    """No hay símbolos que leer: la página lo dice en vez de mostrar una matriz vacía."""


def _offset(tick, utc: Callable[[], float] = time.time) -> int | None:
    """El desfase del servidor contra UTC a partir de un tick, o None si no hay tick."""
    return offset_servidor(int(tick.time), utc()) if tick is not None else None


def _offset_sustituto(tick, utc: Callable[[], float] = time.time) -> int | None:
    """El desfase medido con un símbolo que no es el reloj, o None si no es creíble."""
    offset = _offset(tick, utc)
    return offset if offset is not None and abs(offset) <= DESFASE_MAX_S else None


# Medido en vivo el 2026-10-26 (#AAL, #ABT, #AXP, #NVDA): un símbolo que no estaba en
# Observación de Mercado, recién seleccionado, entrega en la primera lectura las velas de
# la caché local del terminal (una H1 de mayo), y 1,5 s después las de hoy. Sin esta
# espera el radar dibuja líneas de hace meses como sucesos frescos: la matriz falsa y
# convincente que la spec prohíbe.
# En la corrida completa del mismo día (146 símbolos, 5 min 37 s, cuatro intentos por
# oculto en serie), 33 marcos con cachés de 7 a 9 días siguieron viejos tras 4,5 s: a
# algunos símbolos la sincronización les toma más que eso. Por eso los ocultos se
# preseleccionan todos juntos (sincronizan en paralelo) y lo que siga viejo se relee al
# final, minutos después. Con eso basta un reintento por símbolo: más esperas en serie
# solo alargaban el escaneo sin rescatar a los lentos.
INTENTOS_SINCRONIZACION = 2
ESPERA_SINCRONIZACION_S = 1.5
# Holgura sobre la duración del marco: cubre el fin de semana y los feriados largos (una
# acción el lunes a las 07:30 tiene como última vela la del viernes).
HOLGURA_FRESCURA_S = 4 * 86400
AVISO_VELAS_VIEJAS = "velas desactualizadas en MT5: la última vela cerrada es del {cuando}"


def _vencida(vela: int, marco: str, ahora_servidor: int) -> bool:
    """La última vela cerrada terminó hace más de un marco y la holgura de feriados."""
    return ahora_servidor - (vela + DURACION[marco]) > DURACION[marco] + HOLGURA_FRESCURA_S


def _vela_mas_nueva(mt5, ticker: str, marco: str) -> int | None:
    """La apertura (hora del servidor) de la vela más nueva que MT5 tiene, en curso incluida.

    `copy_rates_from_pos` crudo entrega `time` en segundos, sin la conversión a datetime de
    `mt5_client.get_rates`. None si MT5 no la entrega: la prueba se salta.
    """
    try:
        velas = mt5.copy_rates_from_pos(ticker, getattr(mt5, f"TIMEFRAME_{marco}"), 0, 1)
    except Exception:  # noqa: BLE001 - sin la vela no se prueba; la lectura dirá lo suyo
        return None
    if velas is None or len(velas) == 0:
        return None
    return int(velas[-1]["time"])


def _sin_sincronizar(mt5, ticker: str, tick) -> list[str]:
    """Los marcos cuya vela más nueva no contiene el último tick del símbolo.

    Es la prueba exacta de que la caché local está al día, sin calendario: si MT5 tiene
    la vela donde cae el tick, tiene todo lo anterior. Un mercado cerrado la pasa (el
    tick del viernes 16:59 cae en la H1 de las 16:00), y el lunes también (la D1 en curso
    del lunes contiene el tick del lunes), que es donde comparar el tick con las velas
    cerradas daba falsos «desactualizadas». Sin tick, ningún marco se marca: queda la
    guarda de cuatro días. Tick y vela van en hora del servidor.
    """
    if tick is None:
        return []
    t = int(tick.time)
    marcos = []
    for marco in RADAR_MARCOS:
        nueva = _vela_mas_nueva(mt5, ticker, marco)
        if nueva is not None and not nueva <= t < nueva + DURACION[marco]:
            marcos.append(marco)
    return marcos


def _ultimas_velas(velas: dict) -> dict[str, int]:
    """La apertura de la última vela cerrada de cada marco del radar, tal como llegó.

    Se mira la serie cruda y no la lectura del motor: una caché corta (historia
    insuficiente en todos los marcos) también tiene que reconocerse como vieja.
    """
    return {m: int(velas[m]["time"].iloc[-1]) for m in RADAR_MARCOS
            if m in velas and len(velas[m])}


def _cuando(vela: int, marco: str, offset: int | None) -> str:
    """El cierre de la vela en Santiago; sin desfase medido, en hora del servidor y dicho."""
    if offset is not None:
        return cierre_santiago(vela, marco, offset).strftime("%d-%m %H:%M")
    cierre = datetime.fromtimestamp(vela + DURACION[marco], tz=timezone.utc)
    return cierre.strftime("%d-%m %H:%M") + " (hora del servidor)"


def _abrir_reloj(mt5) -> bool:
    """Deja el reloj del servidor en Observación de Mercado. Devuelve si hay que cerrarlo.

    Un símbolo fuera de Observación de Mercado no recibe ticks, así que el reloj se
    selecciona antes de pedir su cotización y se restaura con el resto del universo.
    """
    info = mt5.symbol_info(RELOJ)
    if info is None or info.visible:
        return False
    mt5.symbol_select(RELOJ, True)
    return True


def _leer_simbolo(sim: Simbolo, velas: dict) -> tuple[dict[str, LecturaMarco], list[Falla]]:
    """La lectura de cada marco de un símbolo; un marco que el motor rechaza es su falla."""
    marcos: dict[str, LecturaMarco] = {}
    fallas: list[Falla] = []
    for marco in RADAR_MARCOS:
        try:
            marcos[marco] = leer_marco(velas, marco, sim.digits, PARAMETROS)
        except KeyError as exc:
            fallas.append(Falla(sim.ticker, marco, f"MT5 no entregó velas de {exc}"))
        except ValueError as exc:  # incluye HistoriaInsuficiente
            fallas.append(Falla(sim.ticker, marco, str(exc)))
    return marcos, fallas


def escanear(simbolos: list[Simbolo], mt5, leer_velas=velas_mt5,
             ahora: Callable[[], datetime] = _ahora_santiago,
             cuenta: int | None = None,
             dormir: Callable[[float], None] = time.sleep,
             utc: Callable[[], float] = time.time) -> Escaneo:
    """Lee cada símbolo en los marcos del radar y junta filas y fallas.

    Una sola lectura de velas por símbolo (W1/D1/H4/H1 cerradas; la vela en curso la
    separa `velas_mt5` y no entra). Una excepción de la lectura es falla del símbolo; una
    del motor (historia insuficiente, marco ausente, ATR 0) es falla de ese marco, y los
    demás marcos y símbolos se leen igual. La paridad la agrega `main`.

    El desfase del servidor se mide una vez con el reloj (`RELOJ`). Si el reloj no
    cotiza, se usa el tick del primer símbolo leído que dé un desfase creíble (a lo
    sumo 14 h), la misma idea de `velas_mt5`, y el encabezado avisa con qué símbolo se
    midió. Sin ninguno, las horas de cierre no se muestran y queda un aviso en
    `avisos`: no es la falla de ningún símbolo ni de la paridad, y no se cuenta como tal.

    `cuenta` es el login que `main` ya verificó; si no viene, se lee del terminal.

    **Frescura (siempre activa).** Un marco cuya última vela cerrada terminó hace más de
    un marco y cuatro días (`_vencida`) es falla «velas desactualizadas», no una celda.
    La hora del servidor es `utc() + offset`; sin desfase, `utc() − DESFASE_MAX_S`, la más
    temprana posible, y no el tick del símbolo, que puede ser tan viejo como su caché.
    Un símbolo que estaba fuera de Observación de Mercado se prueba además antes de cada
    lectura (`_sin_sincronizar`): la vela más nueva de cada marco, en curso incluida, tiene
    que contener su último tick. Si no, MT5 sigue con la caché local, aunque sea de ayer
    (el radar deselecciona al terminar, así que mañana la caché tendrá un día). Si algún
    marco no sincronizó o salió vencido, se vuelve a intentar hasta
    `INTENTOS_SINCRONIZACION` veces con `ESPERA_SINCRONIZACION_S` entre intentos. Uno
    visible se lee una sola vez. La guarda de cuatro días se juzga sobre las velas crudas,
    así que una caché demasiado corta para el motor también se reintenta, y si no se
    repone su falla es «velas desactualizadas», no la historia.

    **Preselección y segunda pasada.** Todos los ocultos se seleccionan juntos antes de
    leer el primero, así sincronizan en paralelo mientras se leen los anteriores. Al
    final, tras una sola espera, todo símbolo con algún marco viejo (oculto o visible) se
    relee una vez: ya tuvo el escaneo entero para ponerse al día. Si esa lectura sale fresca
    reemplaza a la primera; si no, queda la primera con sus fallas.

    Presupuesto: en el peor caso, (INTENTOS − 1) × ESPERA = 1,5 s por oculto que siga
    viejo, más una espera y una lectura por símbolo viejo en la segunda pasada. `dormir` y `utc` se
    inyectan para los tests.
    """
    inicio = ahora()
    t0 = time.monotonic()
    restaurar = [s.ticker for s in simbolos if not s.visible]
    offset: int | None = None
    medido_con: str | None = None   # el símbolo que reemplazó al reloj, si hizo falta

    def leer(sim: Simbolo, intentos: int) -> tuple[dict[str, LecturaMarco], list[Falla], bool]:
        """Lee un símbolo hasta `intentos` veces mientras salga viejo. El bool: quedó viejo."""
        nonlocal offset, medido_con
        marcos: dict[str, LecturaMarco] = {}
        fallas_sim: list[Falla] = []
        for intento in range(intentos):
            if intento:
                dormir(ESPERA_SINCRONIZACION_S)
            ultimo = intento == intentos - 1
            # Cada intento reemplaza entero al anterior: ni lecturas ni fallas se suman.
            marcos, fallas_sim = {}, []
            # El símbolo ya está seleccionado (preselección) y su tick existe si cotiza.
            tick = mt5.symbol_info_tick(sim.ticker)
            # Un oculto se prueba ANTES de leer: así la lectura sigue a una caché al día, y
            # una que todavía no sincroniza no gasta la lectura completa.
            sin_sinc = [] if sim.visible else _sin_sincronizar(mt5, sim.ticker, tick)
            if sin_sinc and not ultimo:
                continue
            try:
                velas, _en_curso = leer_velas(sim.ticker, MARCOS_RADAR)
            except Exception as exc:  # noqa: BLE001 - un símbolo no corta el escaneo
                return {}, [Falla(sim.ticker, None, str(exc) or type(exc).__name__)], False
            if offset is None:
                # Uno rechazado deja el desfase en None y el siguiente símbolo lo intenta.
                offset = _offset_sustituto(tick, utc)
                if offset is not None:
                    medido_con = sim.ticker
            marcos, fallas_sim = _leer_simbolo(sim, velas)
            # Sin desfase, la hora del servidor más temprana posible: el tick del propio
            # símbolo puede ser tan viejo como su caché y aprobarla.
            ahora_servidor = int(utc()) + (offset if offset is not None else -DESFASE_MAX_S)
            ultimas = _ultimas_velas(velas)
            viejos = [m for m, vela in ultimas.items()
                      if _vencida(vela, m, ahora_servidor) or m in sin_sinc]
            if not viejos:
                return marcos, fallas_sim, False
            if ultimo:
                for m in viejos:
                    # La falla del motor (historia corta de una caché) cede su lugar.
                    marcos.pop(m, None)
                    fallas_sim = [f for f in fallas_sim if f.marco != m]
                    fallas_sim.append(Falla(sim.ticker, m, AVISO_VELAS_VIEJAS.format(
                        cuando=_cuando(ultimas[m], m, offset))))
        return marcos, fallas_sim, True

    resultados: dict[str, tuple[Simbolo, dict[str, LecturaMarco], list[Falla], bool]] = {}
    try:
        if _abrir_reloj(mt5) and RELOJ not in restaurar:
            restaurar.append(RELOJ)
        offset = _offset(mt5.symbol_info_tick(RELOJ), utc)
        # Todos los ocultos se seleccionan de una vez, antes de leer el primero: el terminal
        # los sincroniza en paralelo mientras se leen los anteriores. Ya están en
        # `restaurar`, así que el `finally` los vuelve a cerrar pase lo que pase.
        for sim in simbolos:
            if not sim.visible:
                mt5.symbol_select(sim.ticker, True)
        for sim in simbolos:
            intentos = 1 if sim.visible else INTENTOS_SINCRONIZACION
            resultados[sim.ticker] = (sim, *leer(sim, intentos))
        # Segunda pasada: lo que quedó viejo ya tuvo el escaneo entero para sincronizar.
        # Se relee una vez, y solo una lectura fresca reemplaza a la primera. Una espera
        # antes, si hay algo que releer: los últimos de la primera pasada recién llegaron.
        if any(v for *_r, v in resultados.values()):
            dormir(ESPERA_SINCRONIZACION_S)
        for ticker, (sim, _m, _f, viejo) in list(resultados.items()):
            if viejo:
                marcos, fallas_sim, sigue_viejo = leer(sim, 1)
                if not sigue_viejo and not any(f.marco is None for f in fallas_sim):
                    resultados[ticker] = (sim, marcos, fallas_sim, False)
    finally:
        # Lo que el director no tenía abierto vuelve a cerrarse, pase lo que pase.
        for ticker in restaurar:
            try:
                mt5.symbol_select(ticker, False)
            except Exception:  # noqa: BLE001 - restaurar uno no impide restaurar el resto
                pass
    fallas = [f for _s, _m, fallas_sim, _v in resultados.values() for f in fallas_sim]
    leidos = [(sim, marcos) for sim, marcos, _f, _v in resultados.values() if marcos]
    # Las horas se calculan al final: el desfase puede haberse medido con un símbolo
    # posterior, y los anteriores también llevan su hora de cierre.
    filas = tuple(
        Fila(sim.ticker, sim.categoria, sim.digits, marcos,
             {} if offset is None else
             {m: cierre_santiago(lm.vela, m, offset) for m, lm in marcos.items()})
        for sim, marcos in leidos
    )
    return Escaneo(inicio=inicio, duracion_s=time.monotonic() - t0,
                   cuenta=_cuenta(mt5) if cuenta is None else cuenta,
                   leidos=len(simbolos), filas=filas, fallas=tuple(fallas), paridad=(),
                   avisos=(AVISO_SIN_RELOJ,) if offset is None else
                   (AVISO_RELOJ_SUSTITUTO.format(ticker=medido_con),) if medido_con else ())


def _paridad(e: Escaneo) -> tuple[str, ...]:
    """El resumen y las diferencias contra el indicador de MT5. Nunca mata el escaneo.

    Con el archivo fresco la primera línea es siempre el resumen de `comparar`, también
    cuando no hay diferencias: la paridad nunca se omite en silencio (spec §7). Un JSON
    del exportador mal formado puede lanzar dentro de `leer_objetos` o de
    `comparar`; eso es una línea más de la página, no una corrida perdida.
    """
    try:
        objetos = leer_objetos(ruta_objetos(), e.inicio)
        if isinstance(objetos, str):
            return (objetos,)
        lecturas = {(f.ticker, m): lm for f in e.filas for m, lm in f.marcos.items()}
        digits = {f.ticker: f.digits for f in e.filas}
        return tuple(comparar(objetos, lecturas, digits, PARAMETROS))
    except Exception as exc:  # noqa: BLE001
        return (f"no se pudo verificar la paridad: {exc}",)


def _escribir(html: str, raiz: Path, inicio: datetime) -> Path:
    """La página del día y la copia en `ultimo.html`, siempre en UTF-8."""
    destino = raiz / inicio.strftime("%Y-%m-%d") / f"radar_{inicio.strftime('%H-%M')}.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    (raiz / "ultimo.html").write_text(html, encoding="utf-8")
    return destino


def _args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Radar multifractal: qué mirar hoy en 1H, 4H y 1D.")
    ap.add_argument("--simbolos", help="lista separada por comas, para una prueba acotada")
    ap.add_argument("--sin-abrir", action="store_true", help="no abrir la página al terminar")
    ap.add_argument("--salida", type=Path, default=SALIDA,
                    help="carpeta raíz de las páginas (por defecto data/radar)")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _args(argv)
    inicio = _ahora_santiago()

    def terminar(html: str, codigo: int) -> int:
        destino = _escribir(html, args.salida, inicio)
        if not args.sin_abrir:
            webbrowser.open(destino.resolve().as_uri())
        print(destino)
        return codigo

    try:
        mt5 = _terminal()
        mt5_client.connect()
    except Exception as exc:  # noqa: BLE001 - incluye el paquete MetaTrader5 ausente
        return terminar(render_error("MT5 no responde", str(exc) or type(exc).__name__, inicio), 1)

    info = mt5.account_info()
    veredicto = cuenta_correcta(getattr(info, "login", None))
    if not veredicto.ok:
        detalle = getattr(veredicto, "detalle", "") or getattr(veredicto, "motivo", "")
        return terminar(render_error("Cuenta MT5 inesperada", detalle, inicio), 1)

    try:
        html = _matriz(mt5, int(info.login), args.simbolos, inicio)
    except SinUniverso as exc:
        # Una matriz vacía se lee como «nada que mirar hoy»; acá no se leyó nada.
        return terminar(render_error("MT5 no entregó el universo", str(exc), inicio), 1)
    except Exception as exc:  # noqa: BLE001
        # Sin esto, una falla inesperada deja el `ultimo.html` de ayer con cara de hoy.
        return terminar(render_error("El radar falló", f"{type(exc).__name__}: {exc}", inicio), 1)
    return terminar(html, 0)


def _matriz(mt5, login: int, pedidos_txt: str | None, inicio: datetime) -> str:
    """El escaneo completo ya con la cuenta verificada: universo, lectura, paridad y HTML."""
    simbolos = universo(mt5)
    if not simbolos:
        raise SinUniverso("symbols_get() no devolvió ningún símbolo operable: "
                          "no hay nada que leer, y una matriz vacía no significaría nada")
    fuera: list[Falla] = []
    if pedidos_txt:
        pedidos = [t.strip() for t in pedidos_txt.split(",") if t.strip()]
        por_ticker = {s.ticker: s for s in simbolos}
        simbolos = [por_ticker[t] for t in pedidos if t in por_ticker]
        fuera = [Falla(t, None, "no está entre los símbolos operables del terminal")
                 for t in pedidos if t not in por_ticker]
        if not simbolos:
            raise SinUniverso("ninguno de los símbolos pedidos con --simbolos está entre los "
                              f"operables del terminal: {', '.join(pedidos) or '(lista vacía)'}")

    # `velas_mt5` se pasa explícito para leer el nombre del módulo en el momento.
    e = escanear(simbolos, mt5, leer_velas=velas_mt5, ahora=lambda: inicio, cuenta=login)
    e = replace(e, leidos=e.leidos + len(fuera), fallas=tuple(fuera) + e.fallas,
                paridad=e.paridad + _paridad(e))
    return render(e)

if __name__ == "__main__":
    raise SystemExit(main())
