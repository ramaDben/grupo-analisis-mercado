"""El agendador interno de la alerta de la semana: qué le toca a cada ejecutivo y cuándo.

Material interno del bot de Telegram (spec 2026-10-18-alerta-semana-ejecutivos). No es del reloj de
sucesos (`reloj_gi.py` solo prepara y jamás envía) ni va a WhatsApp: **este módulo no importa nada del
envío a WhatsApp**, y un test lo impone. Lo mueve un hilo del bot que late cada minuto y decide con la
hora de Santiago.

Cinco decisiones lo sostienen:

1. **La hora manda en Santiago y la ventana de gracia es solo hacia adelante.** El mapa sale el lunes
   de 07:45 a 08:15; la víspera, de 16:00 a 16:30 del día hábil anterior a un dato de tier 1. Disparar
   antes de la hora sería avisar de algo que aún no toca.
2. **Idempotencia por ejecutivo, en disco.** Reiniciar el bot no repite un aviso; el envío a uno no
   marca al otro. Solo se anota un envío confirmado: uno que falló sigue pendiente en el siguiente latido.
3. **Tope de 2 por ejecutivo por día, ganan los de menor tier.** Si todo es alerta, ignoran todo.
4. **Un calendario caído no se disfraza.** No se manda una agenda vieja: se avisa una vez al director y
   el siguiente latido reintenta. «Vacía» (el calendario respondió y no hay datos fuertes) sí se envía.
5. **Se mide lo que Telegram deja medir.** No informa lecturas, así que cada aviso guarda clics del botón,
   votos Útil / No me sirve y si el ejecutivo pidió después `/oportunidad` del mismo activo.
"""
from __future__ import annotations

import hashlib
import json
import threading
import traceback
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from analista import RAIZ
from analista import agenda as ag
from analista import registro_semanal as rg
from analista import semana as sm

RUTA = RAIZ / "data" / "semanal" / "avisos_semana.json"
RUTA_FERIADOS_CHILE = RAIZ / "config" / "feriados_chile.json"
TOPE_DIARIO = 2
TIER_VISPERA = 1
MAPA = (7 * 60 + 45, 8 * 60 + 15)        # minutos desde la medianoche, [desde, hasta)
VISPERA = (16 * 60, 16 * 60 + 30)
HORAS_OPORTUNIDAD = 24
PLAZO_MAPA_PERDIDO = 105   # minutos tras cerrar la ventana del mapa en que aún se avisa al director
LECTURA_TTL = timedelta(minutes=10)
TIPOS = ("mapa", "vispera")
CLIC_REBOTE = 5            # segundos: toques repetidos del botón dentro de esta ventana se consideran rebote



def feriados_chile(ruta: Path = RUTA_FERIADOS_CHILE) -> frozenset[date]:
    """Carga los feriados oficiales de Chile desde el archivo de configuración.

    Devuelve un conjunto inmutable de fechas. Si el archivo no existe o está dañado,
    devuelve un frozenset vacío para no interrumpir el agendador.
    """
    if not ruta.exists():
        return frozenset()
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return frozenset()
    fechas = datos.get("feriados") or datos.get("chile") or []
    resultado = set()
    for f in fechas:
        try:
            resultado.add(date.fromisoformat(f))
        except (ValueError, TypeError):
            continue
    return frozenset(resultado)


@dataclass(frozen=True)
class Aviso:
    tipo: str            # "mapa" | "vispera"
    fecha: str           # día del envío (Santiago)
    evento: str          # "mapa" o «dato|fecha del dato»
    tier: int
    texto: str
    activo: str | None   # el símbolo que pide el botón de la víspera
    id: str


def _id(tipo: str, fecha: str, evento: str) -> str:
    return hashlib.sha1(f"{tipo}|{fecha}|{evento}".encode()).hexdigest()[:10]


def _en_ventana(ahora: datetime, ventana: tuple[int, int]) -> bool:
    minuto = ahora.hour * 60 + ahora.minute
    return ventana[0] <= minuto < ventana[1]


def hay_ventana(ahora: datetime, feriados: frozenset[date] | None = None) -> bool:
    """¿Alguna ventana está abierta? Fuera de ellas no se gasta una lectura del calendario."""
    ahora = ahora.astimezone(ag.SANTIAGO)
    feriados = feriados if feriados is not None else feriados_chile()
    mapa_abierto = ahora.weekday() == 0 and _en_ventana(ahora, MAPA)
    vispera_abierta = ahora.weekday() < 5 and ahora.date() not in feriados and _en_ventana(ahora, VISPERA)
    return mapa_abierto or vispera_abierta


def _habil_anterior(dia: date, feriados: frozenset[date] | None = None) -> date:
    feriados = feriados if feriados is not None else feriados_chile()
    previo = dia - timedelta(days=1)
    while previo.weekday() >= 5 or previo in feriados:
        previo -= timedelta(days=1)
    return previo



# ───────────────────────────────────────────────────────────── estado en disco


class Estado:
    """Los avisos enviados y su interacción. Se relee del disco en cada operación: lo escriben dos hilos
    (el agendador y el que atiende los botones) y un reinicio no puede perder nada."""

    def __init__(self, ruta: Path = RUTA):
        self.ruta = ruta
        self.lock = threading.RLock()

    @property
    def datos(self) -> dict[str, Any]:
        # Bajo el mismo candado que las escrituras: en Windows `replace` sobre un archivo abierto para
        # leer falla, así que una lectura concurrente haría perder un envío, un voto o un clic.
        with self.lock:
            # Un archivo corrupto levanta `RegistroDanado`: no se trata como vacío para no pisar la historia.
            datos = rg._leer(self.ruta) if self.ruta.exists() else {}
            datos = datos if isinstance(datos, dict) else {}
            datos.setdefault("enviados", [])
            datos.setdefault("alertas", [])
            return datos

    def _mutar(self, cambio: Callable[[dict[str, Any]], Any]) -> Any:
        with self.lock:
            datos = self.datos
            res = cambio(datos)
            rg._escribir(self.ruta, datos)
            return res

    def registro(self, ejecutivo: str, id_: str) -> dict[str, Any] | None:
        return next((r for r in self.datos["enviados"] if r["ejecutivo"] == ejecutivo and r["id"] == id_), None)

    def enviado(self, ejecutivo: str, aviso: Aviso) -> bool:
        return self.registro(ejecutivo, aviso.id) is not None

    def mapa_enviado(self, ejecutivo: str, fecha: date) -> bool:
        return any(r["ejecutivo"] == ejecutivo and r["fecha"] == fecha.isoformat() and r["tipo"] == "mapa"
                   for r in self.datos["enviados"])

    def enviados_hoy(self, ejecutivo: str, fecha: date) -> int:
        return sum(1 for r in self.datos["enviados"] if r["ejecutivo"] == ejecutivo and r["fecha"] == fecha.isoformat())

    def anotar_envio(self, ejecutivo: str, aviso: Aviso, cuando: datetime, message_id: int | None) -> None:
        reg = {"id": aviso.id, "ejecutivo": ejecutivo, "tipo": aviso.tipo, "fecha": aviso.fecha,
               "evento": aviso.evento, "activo": aviso.activo, "cuando": cuando.isoformat(),
               "message_id": message_id, "clics_boton": 0, "votos": [], "oportunidad_24h": False,
               "ultimo_clic": None}
        self._mutar(lambda d: d["enviados"].append(reg))

    def anotar_clic(self, ejecutivo: str, id_: str, cuando: datetime) -> bool:
        def cambio(d):
            reg = next((r for r in d["enviados"] if r["ejecutivo"] == ejecutivo and r["id"] == id_), None)
            if reg is None:
                return False
            previo = reg.get("ultimo_clic")
            if previo is not None:
                dt = cuando - datetime.fromisoformat(previo)
                if timedelta(0) <= dt < timedelta(seconds=CLIC_REBOTE):
                    return False
            reg["clics_boton"] += 1
            reg["ultimo_clic"] = cuando.isoformat()
            return True
        return bool(self._mutar(cambio))

    def anotar_voto(self, ejecutivo: str, id_: str, voto: str, cuando: datetime) -> bool:
        """Un voto por ejecutivo y aviso: el segundo toque no cuenta. False si no se anotó."""
        def cambio(d):
            reg = next((r for r in d["enviados"] if r["ejecutivo"] == ejecutivo and r["id"] == id_), None)
            if reg is None or reg["votos"]:
                return False
            reg["votos"].append({"voto": voto, "cuando": cuando.isoformat()})
            return True
        return self._mutar(cambio)

    def marcar_oportunidad(self, ejecutivo: str, ticker: str, cuando: datetime) -> None:
        """Pidió `/oportunidad` del mismo activo dentro de 24 h del aviso. El pedido que lanza el propio
        botón no se marca acá: ese ya cuenta como clic y contarlo dos veces inflaría la medida."""
        def cambio(d):
            for r in d["enviados"]:
                if r["ejecutivo"] != ejecutivo or r.get("activo") != ticker:
                    continue
                dt = cuando - datetime.fromisoformat(r["cuando"])
                if timedelta(0) <= dt <= timedelta(hours=HORAS_OPORTUNIDAD):
                    r["oportunidad_24h"] = True
        self._mutar(cambio)

    def director_avisado(self, clave: str) -> bool:
        return clave in self.datos["alertas"]

    def anotar_alerta_director(self, clave: str) -> None:
        self._mutar(lambda d: d["alertas"].append(clave))


def resumen_interaccion(desde: date, hasta: date, estado: Estado) -> dict[str, dict[str, int]]:
    """Por tipo de aviso: enviados, clics, votos y pedidos posteriores. No identifica al ejecutivo."""
    salida = {t: {"enviados": 0, "clics": 0, "util": 0, "no_sirve": 0, "oportunidad": 0} for t in TIPOS}
    for r in estado.datos["enviados"]:
        if not desde <= date.fromisoformat(r["fecha"]) <= hasta or r["tipo"] not in salida:
            continue
        s = salida[r["tipo"]]
        s["enviados"] += 1
        s["clics"] += r["clics_boton"]
        s["oportunidad"] += 1 if r["oportunidad_24h"] else 0
        for v in r["votos"]:
            s[v["voto"]] += 1
    return salida


# ───────────────────────────────────────────────────────────── qué toca


def _avisos_posibles(ahora: datetime, eventos: list[dict[str, Any]],
                     feriados: frozenset[date] | None = None,
                     parcial: bool = False) -> list[Aviso]:
    feriados = feriados if feriados is not None else feriados_chile()
    fecha = ahora.date().isoformat()
    avisos: list[Aviso] = []
    if ahora.weekday() == 0 and _en_ventana(ahora, MAPA):
        cubierto_hasta = None
        if parcial and eventos:
            fechas = [ag._cuando(e) for e in eventos if ag._cuando(e)]
            cubierto_hasta = max(fechas) if fechas else None
        avisos.append(Aviso("mapa", fecha, "mapa", 0, sm.armar_mapa(eventos, ahora, cubierto_hasta=cubierto_hasta), None, _id("mapa", fecha, "mapa")))
    if ahora.weekday() < 5 and ahora.date() not in feriados and _en_ventana(ahora, VISPERA):
        vistos: set[tuple] = set()
        del_tema = [e for e in eventos if sm.tipo_de_evento(e) and sm._tier(e) <= TIER_VISPERA and ag._cuando(e)]
        for ev in sorted(del_tema, key=sm._clave_de_tema):
            cuando = ag._cuando(ev)
            if cuando <= ahora or _habil_anterior(cuando.date(), feriados=feriados) != ahora.date():
                continue
            if sm.momento(ev) in vistos:   # un informe es una sola víspera: no se gasta el cupo en dos
                continue
            vistos.add(sm.momento(ev))
            tipo, pais, dia = sm.momento(ev)
            clave = f"{tipo}|{pais}|{dia.isoformat()}"
            avisos.append(Aviso("vispera", fecha, clave, sm._tier(ev), sm.armar_vispera(ev, ahora),
                                sm.activo_mas_afectado(ev), _id("vispera", fecha, clave)))
    return avisos


def que_toca(ahora: datetime, eventos: list[dict[str, Any]], estado: Estado, ejecutivo: str,
             feriados: frozenset[date] | None = None,
             parcial: bool = False) -> list[Aviso]:
    """Los avisos que le corresponden ahora a este ejecutivo: sin repetir y con el tope diario."""
    ahora = ahora.astimezone(ag.SANTIAGO)
    pendientes = [a for a in _avisos_posibles(ahora, eventos, feriados=feriados, parcial=parcial) if not estado.enviado(ejecutivo, a)]
    cupo = max(TOPE_DIARIO - estado.enviados_hoy(ejecutivo, ahora.date()), 0)
    return pendientes[:cupo]   # el mapa va primero (tier 0), luego los de menor tier


def leer_eventos(ahora: datetime, cargar: Callable[..., dict[str, Any]] | None = None) -> tuple[str, list[dict[str, Any]]]:
    """`("ok"|"parcial"|"vacia"|"sin_calendario", eventos)`: la misma distinción que `agenda.py`."""
    altos, _avisos, fallidas, _limite = ag.ventana_cruda(ahora, cargar)
    eventos = [ev for _, ev in altos]
    if eventos:
        return ("parcial" if fallidas > 0 else "ok"), eventos
    return ("sin_calendario" if fallidas else "vacia"), []


# ───────────────────────────────────────────────────────────── el agendador


def destinatarios(config: dict[str, Any]) -> list[str]:
    """Primera semana en modo prueba: solo el director. Después, todos los registrados."""
    todos = config.get("analistas", {})
    if (config.get("avisos_semana") or {}).get("modo", "prueba") == "todos":
        return list(todos)
    return [i for i, a in todos.items() if a.get("rol") == "director"]


class Agendador:
    """`enviar(chat, aviso) -> message_id` y `avisar_director(chat, texto)` los pone el bot."""

    def __init__(self, config: dict[str, Any], estado: Estado, enviar: Callable[[str, Aviso], int | None],
                 avisar_director: Callable[[str, str], None], reloj: Callable[[], datetime],
                 leer: Callable[[datetime], tuple[str, list[dict[str, Any]]]] = leer_eventos,
                 log: Callable[[str], None] = lambda texto: None,
                 feriados: frozenset[date] | None = None):
        self.config, self.estado, self.enviar = config, estado, enviar
        self.avisar_director, self.reloj, self.leer, self.log = avisar_director, reloj, leer, log
        self.feriados = feriados
        self._hechos: set[tuple[str, str]] = set()   # enviados en este proceso, anotados o no
        self._cache_lectura: tuple[str, list[dict[str, Any]]] | None = None
        self._cache_cuando: datetime | None = None

    def _leer_con_cache(self, ahora: datetime) -> tuple[str, list[dict[str, Any]]]:
        if (self._cache_cuando is not None and self._cache_lectura is not None
                and self._cache_cuando.date() == ahora.date()
                and timedelta(0) <= ahora - self._cache_cuando < LECTURA_TTL):
            return self._cache_lectura
        situacion, eventos = self.leer(ahora)
        if situacion != "sin_calendario":
            self._cache_cuando = ahora
            self._cache_lectura = (situacion, eventos)
        else:
            self._cache_cuando = None
            self._cache_lectura = None
        return situacion, eventos

    def _calendario_caido(self, ahora: datetime) -> None:
        clave = f"{ahora.date().isoformat()}|{'mapa' if ahora.weekday() == 0 and _en_ventana(ahora, MAPA) else 'vispera'}"
        if self.estado.director_avisado(clave):
            return
        directores = [i for i, a in self.config.get("analistas", {}).items() if a.get("rol") == "director"]
        texto = ("No pude leer el calendario, así que no mandé el aviso de la semana. "
                 "Lo intento de nuevo en el siguiente latido mientras siga abierta la ventana.")
        enviado = False
        for d in directores:
            try:
                self.avisar_director(d, texto)
                enviado = True
            except Exception:  # noqa: BLE001
                self.log(f"no pude avisar al director {d}: {traceback.format_exc()}")
        if enviado:
            self.estado.anotar_alerta_director(clave)

    def _mapa_perdido(self, ahora: datetime) -> None:
        """El lunes pasada la ventana sin que el mapa saliera (bot apagado): se le dice al director, una vez.

        Si el calendario estaba caído ya se avisó por esa vía. La ventana no se reabre: mandar tarde un mapa
        que nadie pidió es decisión del director."""
        minuto = ahora.hour * 60 + ahora.minute
        dia = ahora.date()
        if not (ahora.weekday() == 0 and MAPA[1] <= minuto < MAPA[1] + PLAZO_MAPA_PERDIDO):
            return
        clave = f"{dia.isoformat()}|mapa_perdido"
        if self.estado.director_avisado(clave) or self.estado.director_avisado(f"{dia.isoformat()}|mapa"):
            return
        if all(self.estado.mapa_enviado(e, dia) for e in destinatarios(self.config)):
            return
        directores = [i for i, a in self.config.get("analistas", {}).items() if a.get("rol") == "director"]
        texto = ("El mapa de la semana no salió en su ventana (de 07:45 a 08:15), probablemente porque el bot "
                 "estaba apagado. Los ejecutivos no lo recibieron esta semana.")
        enviado = False
        for d in directores:
            try:
                self.avisar_director(d, texto)
                enviado = True
            except Exception:  # noqa: BLE001
                self.log(f"no pude avisar al director {d}: {traceback.format_exc()}")
        if enviado:
            self.estado.anotar_alerta_director(clave)

    def latido(self) -> None:
        ahora = self.reloj().astimezone(ag.SANTIAGO)
        self._mapa_perdido(ahora)
        fer = self.feriados if self.feriados is not None else feriados_chile()
        if not hay_ventana(ahora, feriados=fer):
            return
        situacion, eventos = self._leer_con_cache(ahora)
        if situacion == "sin_calendario":
            self._calendario_caido(ahora)
            return
        for ejecutivo in destinatarios(self.config):
            for aviso in que_toca(ahora, eventos, self.estado, ejecutivo, feriados=fer, parcial=(situacion == "parcial")):
                if (ejecutivo, aviso.id) in self._hechos:
                    continue   # salió pero no se pudo anotar: reenviarlo cada minuto sería peor que perder el registro
                try:
                    message_id = self.enviar(ejecutivo, aviso)
                except Exception:  # noqa: BLE001  un envío caído sigue pendiente: no se anota
                    self.log(f"aviso {aviso.tipo} a {ejecutivo} falló: {traceback.format_exc()}")
                    continue
                self._hechos.add((ejecutivo, aviso.id))
                try:
                    self.estado.anotar_envio(ejecutivo, aviso, ahora, message_id)
                except Exception:  # noqa: BLE001  no debe cortar a los ejecutivos que faltan
                    self.log(f"aviso {aviso.tipo} a {ejecutivo} salió pero no se anotó: {traceback.format_exc()}")

