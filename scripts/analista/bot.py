"""Bot de Telegram del equipo: entrega el análisis de un activo y su seguimiento.

Tres reglas lo definen (specs 2026-10-12-oportunidad-semanal y 2026-10-16-oportunidad-por-activo):

1. **Solo atiende a quien está en `config/analistas_telegram.json`**, por el id
   de la persona (no del chat: en un grupo el chat es de todos).
2. **agy solo redacta.** `/oportunidad <activo>` arma el análisis de un activo, vigente 7 días: Python prepara
   los datos, agy rellena los textos una sola vez y Python arma el HTML (herramienta interna
   con panel de simulación). `/seguimiento` no usa agy: lámina PNG y texto de WhatsApp.
3. **Reusar no cuesta agy.** El análisis vale 7 días y el seguimiento 30 minutos.

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
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import IO, Any, Callable
from zoneinfo import ZoneInfo

from analista import RAIZ
from analista import autor as au
from analista import comercial as cm
from analista import esquema as es
from analista import fuentes as fu
from analista import informe_html as ih
from analista import macro_seguimiento as mac
from analista import oportunidad_html as oh
from analista import orden as od
from analista import preparar as pr
from analista import registro_semanal as rg
from analista import seguimiento as sg
from analista import simbolos as sm
from analista import vigencia as vg

SANTIAGO = ZoneInfo("America/Santiago")
CONFIG = RAIZ / "config" / "analistas_telegram.json"
DIR_PEDIDOS = RAIZ / "data" / "informes_analistas"
ESTADO = RAIZ / "data" / ".bot_telegram_estado.json"
LOG = RAIZ / "data" / "logs" / "bot_telegram.log"
INSTANCIA = RAIZ / "data" / ".bot_analistas.lock"

AYUDA = """Bot de análisis · Grupo Inteligencia

1) Análisis completo de un activo (técnico, fundamental y voces de bancos), para abrir en tu navegador:
/oportunidad oro
Con el nombre de tu cliente: /oportunidad oro Juan
Vale 7 días: si ya existe uno vigente, te lo entrego al tiro.

2) Cómo va un activo, con lámina y texto listos para WhatsApp:
/seguimiento oro (con nombre: /seguimiento oro Juan)
Activos: oro, dolar, cobre, petroleo, brent, nasdaq, bitcoin o el símbolo exacto de MT5
Tus pedidos de hoy: /estado"""

# El menú que Telegram muestra al tocar «/»: los ejecutivos no tienen que recordar nada.
MENU = [
    ("oportunidad", "Análisis de un activo (ej: /oportunidad oro)"),
    ("seguimiento", "Cómo va un activo (ej: /seguimiento oro)"),
    ("estado", "Tus pedidos de hoy"),
    ("ayuda", "Cómo se usa"),
]


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



# El análisis se reusa 7 días (registro); el seguimiento vale menos: el precio se mueve.
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
    aparte: str = ""  # un aviso para el ejecutivo, en otro mensaje: no se reenvía al cliente


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
    calendario: Callable[[datetime], list[dict[str, Any]]] = mac.eventos_de_la_semana
    verificar_vigencia: Callable[[dict[str, Any], datetime], tuple[str | None, str | None]] = vg.verificar
    simbolo: Callable[[str], dict[str, Any] | None] = sm.buscar
    verificar_url: Callable[[str], str] = fu.verificar_url

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
        except (pr.SinAnalisisError,) as exc:
            raise FalloPedido(str(exc)) from exc  # es la respuesta, no una falla
        except pr.PreparacionFallida as exc:
            extra = (" El análisis vigente sigue disponible con /oportunidad."
                     if orden.pieza == "seguimiento" else "")
            raise FalloPedido(f"No pude leer los datos: {exc}.{extra}".replace("..", ".")) from exc

    def _canonica(self, orden: od.Orden) -> od.Orden:
        """Un símbolo `libre` se confirma contra el terminal y queda con su nombre exacto."""
        if not orden.args.get("libre"):
            return orden
        crudo = orden.args["ticker"]
        try:
            info = self.simbolo(crudo)
        except sm.TerminalNoDisponible as exc:
            raise FalloPedido(f"No pude consultar el terminal para confirmar «{crudo}»: {exc}. Intenta de nuevo.") from exc
        if info is None:
            raise FalloPedido(f"No encontré el símbolo «{crudo}» en el terminal MT5. Revisa el nombre exacto, "
                              "por ejemplo oro, dolar, cobre o AAPL.US.")
        return od.Orden(orden.pieza, {"ticker": info["ticker"]}, orden.saludo)

    def _redactar_y_validar(self, dir_pedido: Path, hoy) -> tuple[dict[str, Any], list[str]]:
        res = self.redactar(dir_pedido / "pieza.json", self.config["tier"])
        if getattr(res, "codigo", "ok") != "ok":
            raise FalloPedido(f"La redacción no terminó ({res.codigo}: {res.detalle}). No gasté tu cupo.")
        pieza = pr.cargar_pieza(dir_pedido)
        pieza, descartes = fu.depurar_pieza(pieza, hoy, verificar=self.verificar_url)
        # Una tesis con un defecto de texto descarta solo esa voz, no la pieza (spec §9).
        pieza, rotas = es.descartar_tesis_rotas(pieza)
        descartes += rotas
        pr.guardar_pieza(pieza, dir_pedido)
        errores = es.errores(pieza)
        if errores:
            raise FalloPedido("El texto no pasó los controles y no lo entrego así:\n• " + "\n• ".join(errores[:6]))
        return pieza, descartes

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
        try:
            orden = self._canonica(pedido.orden)
            pedido = replace(pedido, orden=orden)
            if orden.pieza == "oportunidad":
                return self._oportunidad(pedido, ahora)
            return self._seguimiento(pedido, ahora)
        except rg.RegistroDanado as exc:
            raise FalloPedido("El registro de análisis está dañado y no sigo para no pisarlo: "
                              "avisa al director.") from exc

    def _oportunidad(self, pedido: Pedido, ahora: datetime) -> Respuesta:
        ticker = pedido.orden.args["ticker"]
        ejecutivo = self.analista(pedido.usuario)
        quien = {"nombre": ejecutivo["nombre"], "id": pedido.usuario}
        previa = rg.vigente(ticker, ahora, self.registro)  # un registro corrupto levanta: no es "sin análisis"
        avisos: list[str] = []
        if previa is not None:
            motivo, aviso = self.verificar_vigencia(pr.cargar_pieza(Path(previa["dir"])), ahora)
            if motivo:
                rg.caducar(ticker, motivo, ahora, self.registro)
                avisos.append(f"El análisis anterior de {ticker} caducó ({motivo}): rehíce uno con la lectura de hoy.")
                previa = None
            elif aviso:
                avisos.append(aviso)
        reusada = previa is not None
        if reusada:
            dir_pedido, pieza = Path(previa["dir"]), pr.cargar_pieza(Path(previa["dir"]))
            if (previa.get("creado_por") or {}).get("id") != pedido.usuario:  # el reúso propio no cuenta
                rg.anotar_reuso(ticker, quien, ahora, self.registro)
        else:
            self._exigir_cupo(pedido.usuario, ahora)
            dir_pedido = self.dir_pedidos / ahora.strftime("%Y-%m-%d") / f"{ahora:%H%M%S}_oportunidad_{ih.slug(ticker)}"
            hecha = self._preparar(pedido.orden, dir_pedido, ahora)
            pieza, descartes = self._redactar_y_validar(dir_pedido, ahora.date())
            a = pieza["datos"]["activos"][0]
            # La lámina se rinde antes del HTML: sin ella no hay botón «Descargar lámina».
            self.rendir_lamina(
                cm.payload_semanal(a, pieza["editorial"]["titulares"][ticker], pieza["datos"]["edicion"],
                                   self.autor, dir_pedido / a["grafico"]),
                "semanal", dir_pedido / cm.nombre_lamina(ticker))
            rg.anotar(ticker, dir_pedido, ahora, a["lectura"]["direccion"], quien, self.registro)
            self.estado.consumir(pedido.usuario, ahora)
            self.estado.guardar()
            avisos += [*hecha.avisos, *[f"Descarté una fuente: {d}" for d in descartes]]
            if not pieza["editorial"]["fuentes"]:
                avisos.append("Sin voces de bancos o prensa atingentes esta vez: el análisis sale con nuestra lectura.")
        try:
            ruta = oh.guardar(pieza, dir_pedido, ejecutivo, self.autor, ahora.date())
        except oh.InformeInvalido as exc:
            raise FalloPedido(f"No pude armar la pieza: {exc}") from exc
        entrada = rg.vigente(ticker, ahora, self.registro) or {}
        creador = (entrada.get("creado_por") or quien)["nombre"]
        nombre = pieza["datos"]["activos"][0]["nombre"]
        aparte = [f"✅ {pieza['editorial']['titular']}",
                  f"Análisis de {nombre} creado por {creador} · vigente hasta el {pieza['datos']['vigencia']['hasta']}"]
        if reusada:
            aparte.append("Ya existía uno vigente: te lo entrego tal cual, sin gastar tu cupo.")
        aparte.append("Ábrelo en el navegador: marca lo que quieres incluir, escribe la pérdida aceptable y copia el correo.")
        aparte += [f"⚠️ {x}" for x in [*avisos, *au.avisos(self.autor, ahora.date())]]
        aparte.append(self._a_drive([ruta], ahora))
        return Respuesta(pedido.chat, cm.texto_acompanamiento(nombre, pedido.orden.saludo), [ruta], "\n".join(aparte))

    def _seguimiento(self, pedido: Pedido, ahora: datetime) -> Respuesta:
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
            if rg.vigente(o.args["ticker"], ahora, self.registro) is not None:
                rg.anotar_seguimiento(o.args["ticker"],
                                      {"ticker": o.args["ticker"], "estado": d["evaluacion"]["estado"],
                                       "ejecutivo": pedido.usuario, "cuando": ahora.isoformat()}, self.registro)
            self.estado.registrar_pieza(o.clave_base(), dir_pedido, ahora, fija=False)
            self.estado.consumir(pedido.usuario, ahora)
            self.estado.guardar()
        pieza = pr.cargar_pieza(dir_pedido)
        datos = pieza["datos"]
        # El texto se arma ahora y no al preparar: la pieza se reusa 30 minutos y puede venir de una
        # versión anterior del bot; así sale siempre al día, con el saludo de quien pide y el dato macro.
        try:
            eventos = self.calendario(ahora)
        except Exception:  # noqa: BLE001  el calendario es un extra
            eventos = []
        ctx = mac.contexto(datos["ticker"], ahora, eventos)
        try:
            texto, aparte = sg.redactar(datos, o.saludo, ctx, ahora)
        except (KeyError, TypeError, ValueError):  # pieza vieja sin todos los datos
            texto, aparte = sg.con_saludo(datos["whatsapp"], o.saludo), ""
        return Respuesta(pedido.chat, texto, [dir_pedido / "lamina.png"], aparte)


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

    def registrar_menu(self) -> None:
        self._post("setMyCommands", json={"commands": [{"command": c, "description": d} for c, d in MENU]})


def entregar(tg: Any, r: Respuesta) -> None:
    if r.texto:
        tg.mensaje(r.chat, r.texto)
    for ruta in r.archivos:
        tg.documento(r.chat, ruta)
    if r.aparte:
        tg.mensaje(r.chat, r.aparte)


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
    generando: set[str] = field(default_factory=set)
    candado: threading.Lock = field(default_factory=threading.Lock, repr=False)

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

        if orden.pieza == "oportunidad":
            clave = orden.clave_base().lower()
            with self.candado:
                if clave in self.generando:
                    return [Respuesta(chat, f"Ya se está generando el análisis de {orden.args['ticker']}. Pídelo de "
                                            "nuevo en unos minutos y te llega al tiro.")]
                self.generando.add(clave)

        en_cola = self.cola.qsize() + (1 if self.ocupado.is_set() else 0)
        self.cola.put(Pedido(usuario, chat, orden))
        _log(f"pedido {usuario}: {orden.clave_base()}")
        if en_cola:
            return [Respuesta(chat, f"Recibido. Hay {en_cola} pedido(s) antes que el tuyo.")]
        if orden.pieza == "oportunidad":
            return [Respuesta(chat, f"Recibido. Armando el análisis de {orden.args['ticker']}: si ya hay uno "
                                    "vigente te lo entrego al tiro; si no, tarda unos minutos.")]
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
            if pedido.orden.pieza == "oportunidad":
                with self.candado:
                    self.generando.discard(pedido.orden.clave_base().lower())

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

        try:
            self.tg.registrar_menu()
        except Exception:  # noqa: BLE001  el menú es comodidad: nunca impide arrancar
            _log(f"no se pudo registrar el menú: {traceback.format_exc()}")

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
