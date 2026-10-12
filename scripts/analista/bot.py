"""Bot de Telegram del equipo: entrega la pieza semanal y el seguimiento de un activo.

Tres reglas lo definen (spec 2026-10-12-oportunidad-semanal-design.md):

1. **Solo atiende a quien está en `config/analistas_telegram.json`**, por el id
   de la persona (no del chat: en un grupo el chat es de todos).
2. **agy solo redacta.** `/oportunidad` arma la foto de la semana: Python prepara los datos,
   agy rellena los textos una sola vez por semana y Python arma el HTML (herramienta interna
   con panel de simulación). `/seguimiento` no usa agy: lámina PNG y texto de WhatsApp.
3. **Reusar no cuesta agy.** La foto vale toda la semana y el seguimiento 30 minutos.

No publica en ningún canal de WhatsApp ni toca la bitácora de despachos: es una
herramienta interna del equipo, y un test lo impone.
"""
from __future__ import annotations

import json
import queue
import shutil
import sys
import threading
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import IO, Any, Callable
from zoneinfo import ZoneInfo

from analista import RAIZ
from analista import autor as au
from analista import comercial as cm
from analista import esquema as es
from analista import informe_html as ih
from analista import oportunidad_html as oh
from analista import orden as od
from analista import preparar as pr
from analista import registro_semanal as rg

SANTIAGO = ZoneInfo("America/Santiago")
CONFIG = RAIZ / "config" / "analistas_telegram.json"
DIR_PEDIDOS = RAIZ / "data" / "informes_analistas"
ESTADO = RAIZ / "data" / ".bot_telegram_estado.json"
LOG = RAIZ / "data" / "logs" / "bot_telegram.log"
INSTANCIA = RAIZ / "data" / ".bot_analistas.lock"

AYUDA = """Bot de análisis · Grupo Inteligencia

/oportunidad          el análisis técnico de la semana, con los 6 activos y tu panel de simulación
/seguimiento oro      cómo va un activo de la semana: la simulación y la lectura de hoy

/estado muestra tu cupo del día. /id muestra tu número de usuario."""


# ───────────────────────────────────────────────────────────── configuración y estado


def tomar_instancia(ruta: Path = INSTANCIA) -> IO[bytes] | None:
    """Toma el candado de bot único; `None` si otro proceso ya lo tiene.

    Dos bots con el mismo token se reparten los pedidos al azar. Pasó al reiniciar la
    tarea: `Stop-ScheduledTask` cierra solo `conhost`, el bot viejo quedó vivo y sin
    consola, y no podía lanzar Chromium. El candado es del sistema operativo, no de
    antigüedad: lo suelta al morir el proceso, así que nunca queda huérfano. Quien lo
    toma tiene que mantener el archivo abierto mientras escucha.
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    archivo = open(ruta, "a+b")  # noqa: SIM115 - vive lo que vive el proceso
    try:
        if sys.platform == "win32":
            import msvcrt

            archivo.seek(0)
            msvcrt.locking(archivo.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(archivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        archivo.close()
        return None
    return archivo



# La foto semanal se reusa por semana (registro); el seguimiento vale menos: el precio se mueve.
REUSO_MINUTOS = {"seguimiento": 30}


def cargar_config(ruta: Path = CONFIG) -> dict[str, Any]:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos.setdefault("analistas", {})
    # Una pieza nueva no puede quedar con la ventana genérica porque el config es anterior a ella.
    datos["reuso_minutos"] = {**REUSO_MINUTOS, **datos.get("reuso_minutos", {})}
    datos.setdefault("tier", "flash")
    return datos


@dataclass
class Estado:
    """Offset de Telegram, cupo del día y piezas vigentes.

    Lo escriben dos hilos (el que escucha y el que trabaja), así que toda
    lectura que muta y toda escritura a disco pasan por `lock`.
    """

    ruta: Path = ESTADO
    datos: dict[str, Any] = field(default_factory=dict)
    lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    @classmethod
    def cargar(cls, ruta: Path = ESTADO) -> "Estado":
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            datos = {}
        for k, v in (("offset", 0), ("uso", {}), ("piezas", {}), ("avisados", [])):
            datos.setdefault(k, v)
        return cls(ruta, datos)

    def guardar(self) -> None:
        with self.lock:
            crudo = json.dumps(self.datos, ensure_ascii=False, indent=1)
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.ruta.with_suffix(".tmp")
            tmp.write_text(crudo, encoding="utf-8")
            tmp.replace(self.ruta)

    def usados(self, usuario: str, ahora: datetime) -> int:
        return self.datos["uso"].get(ahora.strftime("%Y-%m-%d"), {}).get(usuario, 0)

    def consumir(self, usuario: str, ahora: datetime) -> None:
        with self.lock:
            dia = self.datos["uso"].setdefault(ahora.strftime("%Y-%m-%d"), {})
            dia[usuario] = dia.get(usuario, 0) + 1
            # Solo se guarda el día en curso: el cupo es diario y no es historia.
            self.datos["uso"] = {ahora.strftime("%Y-%m-%d"): dia}

    def vigente(self, clave: str, ahora: datetime, minutos: int) -> Path | None:
        reg = self.datos["piezas"].get(clave)
        if not reg:
            return None
        creada = datetime.fromisoformat(reg["creada"])
        mismo_dia = creada.astimezone(SANTIAGO).date() == ahora.astimezone(SANTIAGO).date()
        fija = reg.get("fija") and mismo_dia
        if not fija and ahora - creada > timedelta(minutes=minutos):
            return None
        ruta = Path(reg["dir"])
        return ruta if (ruta / "pieza.json").exists() else None

    def registrar_pieza(self, clave: str, dir_pedido: Path, ahora: datetime, fija: bool) -> None:
        with self.lock:
            self.datos["piezas"][clave] = {"dir": str(dir_pedido), "creada": ahora.isoformat(), "fija": fija}


# ───────────────────────────────────────────────────────────── el trabajo


@dataclass
class Pedido:
    usuario: str
    chat: int
    orden: od.Orden


@dataclass
class Respuesta:
    chat: int
    texto: str = ""
    archivos: list[Path] = field(default_factory=list)


class FalloPedido(RuntimeError):
    """El pedido no se pudo atender; el texto va tal cual al analista."""


def _agy_real(ruta_pieza: Path, tier: str):
    from analista.agy import escribir_textos

    return escribir_textos(ruta_pieza, tier)


@dataclass
class Atendedor:
    """Convierte un pedido en archivos. Todo lo externo se inyecta."""

    config: dict[str, Any]
    estado: Estado
    autor: au.Autor
    preparar: Callable[..., pr.Preparada] = pr.preparar
    redactar: Callable[[Path, str], Any] = _agy_real
    rendir_lamina: Callable[..., Path] = cm.rendir
    reloj: Callable[[], datetime] = lambda: datetime.now(SANTIAGO)
    dir_pedidos: Path = DIR_PEDIDOS
    registro: Path = rg.RUTA

    def analista(self, usuario: str) -> dict[str, Any]:
        return self.config["analistas"][usuario]

    def _exigir_cupo(self, usuario: str, ahora: datetime) -> None:
        cupo = int(self.analista(usuario).get("cupo_diario", 10))
        if self.estado.usados(usuario, ahora) >= cupo:
            raise FalloPedido(f"Completaste tu cupo de {cupo} piezas nuevas por hoy. "
                              "Las que ya existen siguen disponibles.")

    def _preparar(self, orden: od.Orden, dir_pedido: Path, ahora: datetime) -> pr.Preparada:
        try:
            # El registro del bot y no el real: con uno inyectado, preparar miraba otro archivo.
            return self.preparar(orden, dir_pedido, ahora, registro=self.registro)
        except (pr.SinSemanaError, pr.EsperaVelaError, pr.SinFotoError, pr.FueraDeLaFotoError,
                pr.FotoVaciaError) as exc:
            raise FalloPedido(str(exc)) from exc  # es la respuesta, no una falla
        except pr.PreparacionFallida as exc:
            raise FalloPedido(f"No pude leer los datos: {exc}") from exc

    def _redactar_y_validar(self, dir_pedido: Path) -> dict[str, Any]:
        res = self.redactar(dir_pedido / "pieza.json", self.config["tier"])
        if getattr(res, "codigo", "ok") != "ok":
            raise FalloPedido(f"La redacción no terminó ({res.codigo}: {res.detalle}). No gasté tu cupo.")
        pieza = pr.cargar_pieza(dir_pedido)
        errores = es.errores(pieza)
        if errores:
            raise FalloPedido("El texto no pasó los controles y no lo entrego así:\n• " + "\n• ".join(errores[:6]))
        return pieza

    def _a_drive(self, rutas: list[Path], ahora: datetime) -> str:
        destino_raiz = self.config.get("ruta_drive") or ""
        if not destino_raiz:
            return "Drive no está configurado: el archivo va solo por acá."
        destino = Path(destino_raiz) / "GI Informes" / ahora.strftime("%Y-%m-%d")
        try:
            destino.mkdir(parents=True, exist_ok=True)
            for r in rutas:
                shutil.copy2(r, destino / r.name)
        except OSError as exc:
            return f"No pude copiarlo a Drive ({exc.__class__.__name__}): el archivo va solo por acá."
        url = self.config.get("url_carpeta_drive")
        return f"Guardado en Drive: GI Informes/{ahora:%Y-%m-%d}" + (f"\n{url}" if url else "")

    def atender(self, pedido: Pedido) -> Respuesta:
        ahora = self.reloj()
        if pedido.orden.pieza == "oportunidad":
            return self._oportunidad(pedido, ahora)
        return self._seguimiento(pedido, ahora)

    def _oportunidad(self, pedido: Pedido, ahora: datetime) -> Respuesta:
        import referencia_semanal as rs

        semana = rs.semana_de(ahora)
        previa = rg.foto(semana, self.registro)  # un registro corrupto levanta: no es "sin foto"
        reusada = previa is not None
        if reusada:
            dir_pedido, avisos = Path(previa["dir"]), []
            pieza = pr.cargar_pieza(dir_pedido)
        else:
            self._exigir_cupo(pedido.usuario, ahora)
            dir_pedido = self.dir_pedidos / ahora.strftime("%Y-%m-%d") / f"{ahora:%H%M%S}_semanal_{semana}"
            hecha = self._preparar(pedido.orden, dir_pedido, ahora)
            pieza = self._redactar_y_validar(dir_pedido)
            # Las láminas se rinden antes del HTML: sin ellas no hay botón «Descargar lámina».
            for a in pieza["datos"]["activos"]:
                t = a["ticker"]
                self.rendir_lamina(
                    cm.payload_semanal(a, pieza["editorial"]["titulares"][t], pieza["datos"]["edicion"],
                                       self.autor, dir_pedido / a["grafico"]),
                    "semanal", dir_pedido / cm.nombre_lamina(t))
            rg.anotar_foto(semana, dir_pedido, ahora, [a["ticker"] for a in pieza["datos"]["activos"]],
                           self.registro)
            self.estado.consumir(pedido.usuario, ahora)
            self.estado.guardar()
            avisos = hecha.avisos
        try:
            ruta = oh.guardar(pieza, dir_pedido, self.analista(pedido.usuario), self.autor, ahora.date())
        except oh.InformeInvalido as exc:
            raise FalloPedido(f"No pude armar la pieza: {exc}") from exc
        lineas = [f"✅ {pieza['editorial']['titular']}",
                  f"Semana {pieza['datos']['semana']} · foto del {pieza['datos']['edicion']}"]
        if reusada:
            lineas.append("Ya está: es la foto de esta semana. Para ver cómo va un activo, usa /seguimiento <activo>.")
        lineas.append("Ábrelo en el navegador: marca los activos, escribe la pérdida aceptable y copia el correo.")
        lineas += [f"⚠️ {a}" for a in [*avisos, *au.avisos(self.autor, ahora.date())]]
        lineas.append(self._a_drive([ruta], ahora))
        return Respuesta(pedido.chat, "\n".join(lineas), [ruta])

    def _seguimiento(self, pedido: Pedido, ahora: datetime) -> Respuesta:
        import referencia_semanal as rs

        o = pedido.orden
        minutos = int(self.config["reuso_minutos"].get("seguimiento", 30))
        dir_pedido = self.estado.vigente(o.clave_base(), ahora, minutos)
        if dir_pedido is None:
            self._exigir_cupo(pedido.usuario, ahora)
            dir_pedido = (self.dir_pedidos / ahora.strftime("%Y-%m-%d")
                          / f"{ahora:%H%M%S}_seguimiento_{ih.slug(o.args['ticker'])}")
            self._preparar(o, dir_pedido, ahora)
            d = pr.cargar_pieza(dir_pedido)["datos"]
            self.rendir_lamina(
                cm.payload_seguimiento(d["activo"], d["evaluacion"], d["precio_vivo"], d["lectura_hoy"],
                                       d["edicion"], self.autor, dir_pedido / "grafico.png"),
                "seguimiento", dir_pedido / "lamina.png")
            semana = rs.semana_de(ahora)
            if rg.foto(semana, self.registro) is not None:
                rg.anotar_seguimiento(semana, o.args["ticker"],
                                      {"estado": d["evaluacion"]["estado"], "ejecutivo": pedido.usuario,
                                       "cuando": ahora.isoformat()}, self.registro)
            self.estado.registrar_pieza(o.clave_base(), dir_pedido, ahora, fija=False)
            self.estado.consumir(pedido.usuario, ahora)
            self.estado.guardar()
        pieza = pr.cargar_pieza(dir_pedido)
        return Respuesta(pedido.chat, pieza["datos"]["whatsapp"], [dir_pedido / "lamina.png"])


# ───────────────────────────────────────────────────────────── Telegram


class Telegram:
    def __init__(self, token: str):
        self.base = f"https://api.telegram.org/bot{token}"

    def _post(self, metodo: str, **kw):
        import requests

        r = requests.post(f"{self.base}/{metodo}", timeout=60, **kw)
        datos = r.json()
        if not datos.get("ok"):
            raise RuntimeError(f"Telegram rechazó {metodo}: {datos.get('description')}")
        return datos["result"]

    def actualizaciones(self, offset: int) -> list[dict[str, Any]]:
        import requests

        r = requests.get(f"{self.base}/getUpdates", params={"offset": offset, "timeout": 25}, timeout=35)
        return r.json().get("result", [])

    def mensaje(self, chat: int, texto: str) -> None:
        # Sin parse_mode a propósito: un "_" o "*" en un nombre rompía el Markdown
        # y Telegram descartaba la respuesta entera.
        self._post("sendMessage", json={"chat_id": chat, "text": texto[:4000]})

    def documento(self, chat: int, ruta: Path) -> None:
        with ruta.open("rb") as f:
            tipo = {".pdf": "application/pdf", ".png": "image/png"}.get(ruta.suffix, "text/html")
            self._post("sendDocument", data={"chat_id": chat}, files={"document": (ruta.name, f, tipo)})

    def soy(self) -> dict[str, Any]:
        return self._post("getMe")


def entregar(tg: Any, r: Respuesta) -> None:
    if r.texto:
        tg.mensaje(r.chat, r.texto)
    for ruta in r.archivos:
        tg.documento(r.chat, ruta)


def _log(texto: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now(SANTIAGO):%Y-%m-%d %H:%M:%S} {texto}\n")


@dataclass
class Bot:
    tg: Any
    atendedor: Atendedor
    cola: "queue.Queue[Pedido]" = field(default_factory=queue.Queue)
    ocupado: threading.Event = field(default_factory=threading.Event)

    @property
    def config(self) -> dict[str, Any]:
        return self.atendedor.config

    @property
    def estado(self) -> Estado:
        return self.atendedor.estado

    def recibir(self, update: dict[str, Any]) -> list[Respuesta]:
        """Respuestas inmediatas; los pedidos de pieza quedan en la cola."""
        msg = update.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        usuario = str((msg.get("from") or {}).get("id", ""))
        texto = (msg.get("text") or "").strip()
        if not chat or not usuario or not texto:
            return []

        if usuario not in self.config["analistas"]:
            with self.estado.lock:
                if usuario in self.estado.datos["avisados"]:
                    return []
                self.estado.datos["avisados"].append(usuario)
            self.estado.guardar()
            _log(f"desconocido {usuario}: {texto[:60]!r}")
            return [Respuesta(chat, f"No estás autorizado para usar este bot. Tu número de usuario es {usuario}: "
                                    "pásaselo al director para que te dé acceso.")]

        try:
            orden = od.interpretar(texto)
        except od.PedidoInvalido as exc:
            return [Respuesta(chat, str(exc))]

        if orden.pieza in ("start", "ayuda"):
            return [Respuesta(chat, AYUDA)]
        if orden.pieza == "id":
            return [Respuesta(chat, f"Tu número de usuario es {usuario}.")]
        if orden.pieza == "estado":
            cupo = self.config["analistas"][usuario].get("cupo_diario", 10)
            usados = self.estado.usados(usuario, self.atendedor.reloj())
            return [Respuesta(chat, f"Piezas nuevas hoy: {usados} de {cupo}. En cola: {self.cola.qsize()}.")]

        en_cola = self.cola.qsize() + (1 if self.ocupado.is_set() else 0)
        self.cola.put(Pedido(usuario, chat, orden))
        _log(f"pedido {usuario}: {orden.clave_base()}")
        if en_cola:
            return [Respuesta(chat, f"Recibido. Hay {en_cola} pedido(s) antes que el tuyo.")]
        return [Respuesta(chat, "Recibido. Preparo la pieza: una nueva tarda unos minutos.")]

    def procesar_uno(self, pedido: Pedido) -> Respuesta:
        self.ocupado.set()
        try:
            return self.atendedor.atender(pedido)
        except FalloPedido as exc:
            return Respuesta(pedido.chat, f"❌ {exc}")
        except Exception as exc:  # noqa: BLE001
            _log(f"error {pedido.orden.clave_base()}: {traceback.format_exc()}")
            return Respuesta(pedido.chat, f"❌ Falló algo inesperado ({exc.__class__.__name__}). Quedó registrado.")
        finally:
            self.ocupado.clear()

    def trabajador(self) -> None:
        while True:
            pedido = self.cola.get()
            respuesta = self.procesar_uno(pedido)
            try:
                entregar(self.tg, respuesta)
            except Exception:  # noqa: BLE001
                _log(f"no se pudo entregar a {pedido.chat}: {traceback.format_exc()}")

    def escuchar(self) -> None:
        threading.Thread(target=self.trabajador, daemon=True).start()
        import time

        while True:
            try:
                for update in self.tg.actualizaciones(self.estado.datos["offset"]):
                    with self.estado.lock:
                        self.estado.datos["offset"] = update["update_id"] + 1
                    self.estado.guardar()
                    for r in self.recibir(update):
                        entregar(self.tg, r)
            except Exception:  # noqa: BLE001
                _log(f"polling: {traceback.format_exc()}")
                time.sleep(5)
