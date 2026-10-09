"""Bot de Telegram del equipo: atiende pedidos de piezas y entrega el PDF.

Tres reglas lo definen (spec 2026-10-08-bot-telegram-analistas-design.md):

1. **Solo atiende a quien está en `config/analistas_telegram.json`**, por el id
   de la persona (no del chat: en un grupo el chat es de todos).
2. **agy solo redacta.** El pedido se traduce a una `Orden` cerrada, Python
   prepara los datos, agy rellena los textos y Python arma el HTML y lo imprime a PDF.
3. **Reusar no cuesta agy.** La pieza vigente se vuelve a entregar sin redactar.
   El informe es general e igual para todos: no se personaliza por trader.

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
from analista import bitacora as bt
from analista import comercial as cm
from analista import correo as cmo
from analista import esquema as es
from analista import informe_html as ih
from analista import orden as od
from analista import pdf as pf
from analista import preparar as pr
from analista import registro_semanal as rs

SANTIAGO = ZoneInfo("America/Santiago")
CONFIG = RAIZ / "config" / "analistas_telegram.json"
DIR_PEDIDOS = RAIZ / "data" / "informes_analistas"
ESTADO = RAIZ / "data" / ".bot_telegram_estado.json"
LOG = RAIZ / "data" / "logs" / "bot_telegram.log"
INSTANCIA = RAIZ / "data" / ".bot_analistas.lock"

AYUDA = """Bot de análisis · Grupo Inteligencia

Pide una pieza y te llega el informe en PDF, listo para entregar:

/activo oro
/calendario hoy   (o semana)
/dato ipc         (o /dato para el último)
/jornada apertura (o cierre)
/oportunidad      el foco técnico del día, para compartir con un prospecto

/semanal oro      el escenario de la semana: imagen, texto de WhatsApp y correo para Outlook
/seguimiento oro  cómo va ese escenario hoy, con su texto de actualización

El informe es un análisis general: compártelo tal cual con tu trader.

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



# El foco técnico vale menos: el precio se mueve y el plan puede cambiar de estado.
# La pieza semanal no se reusa por minutos: vale la semana y su vigencia la lleva
# `registro_semanal` (una invalidada deja de entregarse aunque sea de hace un rato).
REUSO_MINUTOS = {"activo": 30, "calendario": 30, "dato": 30, "jornada": 720, "oportunidad": 60,
                 "semanal": 0, "seguimiento": 60}


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
        if not reg or minutos <= 0:
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
    # Mensajes que van después de los archivos: el texto de WhatsApp de una pieza
    # comercial, solo, para que el ejecutivo lo copie entero.
    mensajes: list[str] = field(default_factory=list)


class FalloPedido(RuntimeError):
    """El pedido no se pudo atender; el texto va tal cual al analista."""


COMPARTIR_FOCO = "Compártelo tal cual: es análisis general, no una instrucción."


def _vigencia_real(pieza: dict[str, Any], ahora: datetime) -> bool:
    from analista import foco

    return foco.sigue_vigente(pieza, ahora)


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
    rendir_laminas: Callable[..., None] = pr.rendir_laminas
    reloj: Callable[[], datetime] = lambda: datetime.now(SANTIAGO)
    dir_pedidos: Path = DIR_PEDIDOS
    bitacora: Path = bt.RUTA
    # El foco técnico solo se reusa si su plan sigue igual: se vuelve a leer el activo.
    vigencia: Callable[[dict[str, Any], datetime], bool] = _vigencia_real
    # Lo que circula es el PDF: Drive no muestra HTML y un documento firmado no se
    # entrega editable. El HTML queda junto a la pieza como su fuente.
    a_pdf: Callable[[Path], Path] = pf.rendir
    registro_semanal: Path = rs.RUTA
    rendir_imagen: Callable[..., Path] = cm.rendir_imagen

    def analista(self, usuario: str) -> dict[str, Any]:
        return self.config["analistas"][usuario]

    def _pieza_base(self, pedido: Pedido, ahora: datetime) -> tuple[Path, dict[str, Any], list[str], bool]:
        o = pedido.orden
        minutos = int(self.config["reuso_minutos"].get(o.pieza, 30))
        previa = self.estado.vigente(o.clave_base(), ahora, minutos)
        if previa:
            pieza_previa = pr.cargar_pieza(previa)
            if o.pieza != "oportunidad" or self.vigencia(pieza_previa, ahora):
                return previa, pieza_previa, [], True

        cupo = int(self.analista(pedido.usuario).get("cupo_diario", 10))
        if self.estado.usados(pedido.usuario, ahora) >= cupo:
            raise FalloPedido(
                f"Completaste tu cupo de {cupo} piezas nuevas por hoy. "
                "Las que ya existen siguen disponibles."
            )
        arg = ih.slug(str(next(iter(o.args.values()), "") or "auto"))
        dir_pedido = self.dir_pedidos / ahora.strftime("%Y-%m-%d") / f"{ahora:%H%M%S}_{o.pieza}_{arg}"
        try:
            hecha = self.preparar(o, dir_pedido, ahora)
        except (pr.SinFocoError, pr.MercadoIlegibleError, pr.SinEscenarioError, pr.SinPiezaSemanalError) as exc:
            # No es una falla del pedido: es la respuesta. Va tal cual, sin gastar agy ni cupo.
            raise FalloPedido(str(exc)) from exc
        except pr.PreparacionFallida as exc:
            raise FalloPedido(f"No pude leer los datos: {exc}") from exc

        res = self.redactar(dir_pedido / "pieza.json", self.config["tier"])
        if getattr(res, "codigo", "ok") != "ok":
            raise FalloPedido(f"La redacción no terminó ({res.codigo}: {res.detalle}). No gasté tu cupo.")
        pieza = pr.cargar_pieza(dir_pedido)
        errores = es.errores(pieza)
        if errores:
            raise FalloPedido("El texto no pasó los controles y no lo entrego así:\n• " + "\n• ".join(errores[:6]))
        self.rendir_laminas(pieza, dir_pedido)
        fija = o.pieza == "dato" and pieza["datos"].get("modo") == "resultado"
        self.estado.registrar_pieza(o.clave_base(), dir_pedido, ahora, fija)
        self.estado.consumir(pedido.usuario, ahora)
        self.estado.guardar()
        return dir_pedido, pieza, hecha.avisos, False

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

    def _a_drive_semanal(self, archivos: dict[Path, str], lunes: str, activo: str) -> str:
        """`GI Semanal/<lunes>/<activo>/`: la carpeta que el ejecutivo comparte desde Drive."""
        raiz = self.config.get("ruta_drive") or ""
        if not raiz:
            return "Drive no está configurado: los archivos van solo por acá."
        relativa = f"GI Semanal/{lunes}/{activo}"
        try:
            destino = Path(raiz) / relativa
            destino.mkdir(parents=True, exist_ok=True)
            for origen, nombre in archivos.items():
                shutil.copy2(origen, destino / nombre)
        except OSError as exc:
            return f"No pude copiarlo a Drive ({exc.__class__.__name__}): los archivos van solo por acá."
        return f"Guardado en Drive: {relativa}"

    def _atender_comercial(self, pedido: Pedido, ahora: datetime) -> Respuesta:
        """La pieza semanal y su seguimiento: imagen y texto de WhatsApp, y el correo del lunes.

        La semanal se reusa toda la semana desde `registro_semanal` (una sola
        redacción por activo y semana, sin gastar cupo); el seguimiento, una hora.
        El correo se arma para cada ejecutivo porque lleva su nombre en la
        simulación, y armarlo no cuesta agy.
        """
        from analista import semanal as sm

        o = pedido.orden
        tematica = o.args.get("tematica")
        semana = sm.lunes_de(ahora).isoformat()
        previa = None
        if o.pieza == "semanal":
            previa = (rs.vigente_tematica(semana, tematica, self.registro_semanal) if tematica
                      else rs.vigente(semana, o.args["ticker"], self.registro_semanal))
        if previa:
            dir_pedido, pieza, avisos, reusada = Path(previa["dir"]), pr.cargar_pieza(Path(previa["dir"])), [], True
        else:
            dir_pedido, pieza, avisos, reusada = self._pieza_base(pedido, ahora)
        d = pieza["datos"]
        ticker = d["ticker"]
        ejecutivo = self.analista(pedido.usuario)
        try:
            imagen = dir_pedido / "imagen.png"
            if not (reusada and imagen.exists()):
                imagen = self.rendir_imagen(pieza, dir_pedido, self.autor)
            whatsapp, texto = cm.escribir_whatsapp(pieza, dir_pedido)
        except Exception as exc:  # noqa: BLE001
            raise FalloPedido(f"No pude armar la imagen o el texto: {exc}") from exc

        # La carpeta de Drive de una temática no cambia de nombre aunque cambie su activo.
        activo = tematica or ih.slug(d["nombre"])
        if o.pieza == "semanal":
            if not reusada:
                esc = d["escenario"]
                rs.anotar({"semana": semana, "ticker": ticker, "tematica": tematica, "dir": str(dir_pedido),
                           "analista": pedido.usuario,
                           "creada": ahora.isoformat(),
                           "escenario": {k: esc[k] for k in ("sesgo", "estado", "precio", "entrada", "gatillo",
                                                            "invalidacion", "recorrido", "vela")}},
                          self.registro_semanal)
            correo = cmo.guardar(pieza, dir_pedido, ejecutivo, self.autor,
                                 f"correo_{activo}_{ih.slug(ejecutivo.get('nombre', pedido.usuario))}.html")
            base = f"{activo}_semana_{semana}"
            archivos = [imagen, correo]
            drive = self._a_drive_semanal({imagen: f"{base}.png", whatsapp: f"{base}_whatsapp.txt",
                                           correo: correo.name}, semana, activo)
        else:
            ev = d["evaluacion"]
            if not reusada:
                rs.anotar_seguimiento(semana, ticker, d["version"],
                                      {"cuando": ahora.isoformat(), "estado": ev["estado"],
                                       "avance_pct": ev.get("avance_pct"), "precio": d["precio_hoy"],
                                       "pedido_por": pedido.usuario, "dir": str(dir_pedido)},
                                      self.registro_semanal)
                if ev["estado"] == "invalidado":
                    # La pieza de la semana deja de entregarse; la próxima /semanal arma la versión 2.
                    rs.marcar(semana, ticker, d["version"], "invalidada", self.registro_semanal)
            base = f"seguimiento_{ahora:%Y-%m-%d_%H%M}"
            archivos = [imagen]
            drive = self._a_drive_semanal({imagen: f"{base}.png", whatsapp: f"{base}.txt"}, semana, activo)

        lineas = [f"✅ {pieza['editorial'].get('titular') or d['chip']}", f"{d['chip']} · {d['edicion']}"]
        if reusada:
            lineas.append("Es la pieza vigente de la semana: no se volvió a redactar." if o.pieza == "semanal"
                          else "Es el seguimiento de hace un rato: no se volvió a medir.")
        if o.pieza == "semanal":
            lineas.append("Abre el correo en el navegador, completa tu simulación y cópialo a Outlook.")
        elif d["evaluacion"]["estado"] == "invalidado":
            lineas.append("El escenario se invalidó: la pieza de la semana quedó retirada. "
                          f"La próxima /semanal arma la versión {d['version'] + 1}.")
        lineas += [f"⚠️ {a}" for a in [*avisos, *au.avisos(self.autor, ahora.date())]]
        lineas.append(drive)
        lineas.append("El texto para WhatsApp va en el mensaje siguiente.")
        return Respuesta(pedido.chat, "\n".join(lineas), archivos, [texto])

    def atender(self, pedido: Pedido) -> Respuesta:
        ahora = self.reloj()
        if pedido.orden.pieza in ("semanal", "seguimiento"):
            return self._atender_comercial(pedido, ahora)
        dir_pedido, pieza, avisos, reusada = self._pieza_base(pedido, ahora)
        o = pedido.orden
        arg = ih.slug(str(next(iter(pieza["orden"]["args"].values()), "") or "auto"))
        # El archivo viaja al prospecto: su nombre tampoco dice "oportunidad".
        prefijo = "foco-tecnico" if o.pieza == "oportunidad" else o.pieza
        nombre_base = f"{prefijo}_{arg}_{dir_pedido.name[:4]}"
        try:
            ruta = ih.guardar(pieza, dir_pedido, self.analista(pedido.usuario), self.autor,
                              ahora.date(), nombre_base)
        except ih.InformeInvalido as exc:
            raise FalloPedido(f"No pude armar el informe: {exc}") from exc
        # Una pieza reusada es el mismo plan: se anota una sola vez.
        if o.pieza in ("activo", "oportunidad") and not reusada:
            bt.anotar(pieza, ruta, pedido.usuario, ahora, self.bitacora)
        try:
            entregable = self.a_pdf(ruta)
        except pf.PdfFallido as exc:
            # La pieza no se pierde, pero Drive no recibe un archivo que no puede mostrar.
            entregable = None
            avisos = [*avisos, f"No pude generar el PDF ({exc}): va el HTML, ábrelo en el navegador."]
        drive = (self._a_drive([entregable], ahora) if entregable
                 else "El HTML no se guarda en Drive: va solo por acá.")
        lineas = [f"✅ {pieza['editorial']['titular']}",
                  f"{pieza['datos']['chip']} · {pieza['datos']['edicion']}"]
        if reusada and o.pieza == "oportunidad":
            lineas.append(f"Ya está: es el foco de las {pieza['datos']['seleccion']['hora']}.")
        elif reusada:
            lineas.append("Es la pieza vigente: no se volvió a redactar.")
        if o.pieza == "oportunidad":
            lineas.append(COMPARTIR_FOCO)
        lineas += [f"⚠️ {a}" for a in [*avisos, *au.avisos(self.autor, ahora.date())]]
        lineas.append(drive)
        return Respuesta(pedido.chat, "\n".join(lineas), [entregable or ruta])


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
            tipo = "application/pdf" if ruta.suffix == ".pdf" else "text/html"
            self._post("sendDocument", data={"chat_id": chat}, files={"document": (ruta.name, f, tipo)})

    def foto(self, chat: int, ruta: Path) -> None:
        # Como foto y no como documento: así se reenvía a WhatsApp con un toque.
        with ruta.open("rb") as f:
            self._post("sendPhoto", data={"chat_id": chat}, files={"photo": (ruta.name, f, "image/png")})

    def soy(self) -> dict[str, Any]:
        return self._post("getMe")


def entregar(tg: Any, r: Respuesta) -> None:
    if r.texto:
        tg.mensaje(r.chat, r.texto)
    for ruta in r.archivos:
        if ruta.suffix.lower() == ".png":
            tg.foto(r.chat, ruta)
        else:
            tg.documento(r.chat, ruta)
    for texto in r.mensajes:
        tg.mensaje(r.chat, texto)


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
