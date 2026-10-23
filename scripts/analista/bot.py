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
from analista import avisos_semana as av
from analista import comercial as cm
from analista import drive as dv
from analista import esquema as es
from analista import fuentes as fu
from analista import informe_html as ih
from analista import macro_seguimiento as mac
from analista import imagenes_publicas as ip
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

AYUDA = """📚 Bot de análisis · Grupo Inteligencia

1) /oportunidad oro
El análisis completo del activo (técnico, fundamental y qué dicen los bancos), en un archivo que abres en tu navegador.
Con tu cliente: /oportunidad oro Juan
Dura 7 días: si ya hay uno vigente, te llega al tiro. El primero de un activo demora unos minutos.

2) /seguimiento oro
Cómo va el activo hoy: lámina y texto listos para WhatsApp.
Con tu cliente: /seguimiento oro Juan
Si ya entraste: /seguimiento oro Juan entrada=4062.5 (mide el avance desde tu precio).
Incluye la oportunidad de hoy; si la lectura cambió de lado, avisa que lo anterior queda invalidado.
Antes debe existir el /oportunidad de ese activo. Dura 30 minutos.

Activos: oro, dolar, cobre, petroleo, brent, nasdaq, bitcoin o el símbolo exacto de MT5.

Tienes 10 pedidos al día, que se renuevan cada día. Mira cuántos te quedan con /estado.
Tu identificador de Telegram: /id

El bot funciona en jornada hábil chilena y depende de que el equipo del director esté encendido. Si no responde o algo falla, escríbele al director.

Material educativo y de análisis general. No constituye asesoría financiera personalizada ni recomendación de inversión."""

SIN_COMANDO = "Ese comando no existe. Escribe /ayuda y te muestro los que sí."

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
    forzar: bool = False  # /recrear del director: ignora el análisis vigente y no gasta cupo


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


def _agy_fuentes_real(ruta_pieza: Path, tier: str):
    """El segundo intento: solo `fuentes` sigue por escribir, con un techo menor (spec 2026-10-17 §5)."""
    from analista.agy import TIMEOUT_REINTENTO, escribir_textos

    return escribir_textos(ruta_pieza, tier, TIMEOUT_REINTENTO)


SIN_NOTICIA_DIRECTA = ("No encontré ninguna noticia directa de {voz} con su nota vigente (de los últimos {dias} días) "
                       "sobre {nombre}, ni en un segundo intento, y sin ella el análisis no sale. No gasté tu cupo: "
                       "vuelve a pedirlo más tarde, cada pedido hace una búsqueda nueva.")


def _guardar_salida_agy(dir_pedido: Path, res: Any, intento: int) -> None:
    """Lo que respondió agy, para auditar si buscó (spec 2026-10-17 §5.4). Nunca bota el pedido."""
    datos = {"intento": intento, "codigo": getattr(res, "codigo", "ok"), "segundos": getattr(res, "segundos", None),
             "respuesta": str(getattr(res, "respuesta", "") or "")[:20000]}
    try:
        (dir_pedido / f"agy_salida_{intento}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2),
                                                                encoding="utf-8")
    except OSError:
        pass


def _agenda_pasada(pieza: dict[str, Any], ahora: datetime) -> str | None:
    """Motivo de caducidad si algún dato de la agenda sellada ya quedó en el pasado (fecha de Chile).

    La agenda va redactada en modo anticipación («sale el miércoles»): pasado el día, reusarla anuncia como
    pendiente lo que ya salió. Una pieza anterior a la agenda estructurada, o con la ventana vacía o sin
    calendario, no tiene eventos y conserva la regla simple de los 7 días.
    """
    hoy = ahora.astimezone(SANTIAGO).date().isoformat()
    eventos = ((pieza.get("datos") or {}).get("agenda") or {}).get("eventos") or []
    return "ya pasó uno de los días clave de su agenda" if any(e.get("fecha", hoy) < hoy for e in eventos) else None


@dataclass
class Atendedor:
    """Convierte un pedido en archivos. Todo lo externo se inyecta."""

    config: dict[str, Any]
    estado: Estado
    autor: au.Autor
    preparar: Callable[..., pr.Preparada] = pr.preparar
    redactar: Callable[[Path, str], Any] = _agy_real
    redactar_fuentes: Callable[[Path, str], Any] = _agy_fuentes_real
    rendir_lamina: Callable[..., Path] = cm.rendir
    reloj: Callable[[], datetime] = lambda: datetime.now(SANTIAGO)
    dir_pedidos: Path = DIR_PEDIDOS
    registro: Path = rg.RUTA
    calendario: Callable[[datetime], list[dict[str, Any]]] = mac.eventos_de_la_semana
    verificar_vigencia: Callable[[dict[str, Any], datetime], tuple[str | None, str | None]] = vg.verificar
    simbolo: Callable[[str], dict[str, Any] | None] = sm.buscar
    verificar_url: Callable[[str], str] = fu.verificar_url
    publicar_imagen: Callable[[Path], str] | None = ip.publicar  # None: el correo lleva las imágenes embebidas

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
        except (pr.SinAnalisisError, pr.AvisoAlPedir) as exc:
            raise FalloPedido(str(exc)) from exc  # es la respuesta, no una falla de lectura
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

    def _redactar_y_validar(self, dir_pedido: Path, hoy, redactar: Callable[[Path, str], Any] | None = None,
                            intento: int = 1) -> tuple[dict[str, Any], list[str], list[Any]]:
        res = (redactar or self.redactar)(dir_pedido / "pieza.json", self.config["tier"])
        _guardar_salida_agy(dir_pedido, res, intento)
        if getattr(res, "codigo", "ok") != "ok":
            raise FalloPedido(f"La redacción no terminó ({res.codigo}: {res.detalle}). No gasté tu cupo.")
        pieza = pr.cargar_pieza(dir_pedido)
        crudas = pieza["editorial"].get("fuentes")
        crudas = list(crudas) if isinstance(crudas, list) else []
        directa = fu.directa_de(pieza)
        lista = fu.lista_del_segmento(directa[0]) if directa else None
        pieza, descartes = fu.depurar_pieza(pieza, hoy, lista=lista, verificar=self.verificar_url)
        # Una tesis con un defecto de texto descarta solo esa voz, no la pieza (spec §9).
        pieza, rotas = es.descartar_tesis_rotas(pieza)
        descartes += rotas
        pr.guardar_pieza(pieza, dir_pedido)
        errores = es.errores(pieza)
        if errores:
            raise FalloPedido("El texto no pasó los controles y no lo entrego así:\n• " + "\n• ".join(errores[:6]))
        return pieza, descartes, crudas

    def _con_fuente_directa(self, dir_pedido: Path, hoy) -> tuple[dict[str, Any], list[str], bool]:
        """La pieza con al menos una fuente directa válida; si el primer intento no la trae, un segundo solo de fuentes.

        Spec 2026-10-20: un análisis sin noticia directa del activo no se publica. El segundo intento reabre
        solo `fuentes` (los demás textos ya pasaron los controles) y deja escrito qué se descartó. Una pieza
        sin sello `datos.fuente_directa` (anterior al spec) no exige directa.
        """
        pieza, descartes, crudas = self._redactar_y_validar(dir_pedido, hoy)
        directa = fu.directa_de(pieza)
        if directa is None or fu.fuentes_directas(pieza["editorial"]["fuentes"], *directa):
            return pieza, descartes, False
        fu.guardar_intento(dir_pedido, pieza["editorial"]["fuentes"], descartes, crudas)
        pieza["editorial"]["fuentes"] = es.MARCA
        pr.guardar_pieza(pieza, dir_pedido)
        pieza, descartes2, _ = self._redactar_y_validar(dir_pedido, hoy, self.redactar_fuentes, intento=2)
        if fu.fuentes_directas(pieza["editorial"]["fuentes"], *directa):
            return pieza, descartes + descartes2, True
        motivos = [*descartes, *descartes2][:4]
        texto = SIN_NOTICIA_DIRECTA.format(voz=directa[1]["nombre"],
                                           dias=fu.cargar_lista().get("frescura_dias", 14),
                                           nombre=pieza["datos"]["activos"][0]["nombre"])
        raise FalloPedido(texto + ("\nLo que descarté:\n• " + "\n• ".join(motivos) if motivos else ""))

    def _a_drive(self, rutas: list[tuple[Path, str]], ahora: datetime, ticker: str, nombre: str) -> str:
        destino_raiz = self.config.get("ruta_drive") or ""
        if not destino_raiz:
            return "Drive no está configurado: el archivo va solo por acá."
        destino = dv.carpeta(Path(destino_raiz), ticker, nombre, ahora.date())
        try:
            dv.copiar(rutas, destino)
        except OSError as exc:
            return f"No pude copiarlo a Drive ({exc.__class__.__name__}): el archivo va solo por acá."
        url = self.config.get("url_carpeta_drive")
        relativa = destino.relative_to(destino_raiz).as_posix()
        return f"Guardado en Drive: {relativa}" + (f"{chr(10)}{url}" if url else "")

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
        if pedido.forzar and previa is not None:
            rg.caducar(ticker, "recreado por el director", ahora, self.registro)
            previa = None
        if previa is not None:
            pieza_previa = pr.cargar_pieza(Path(previa["dir"]))
            motivo, aviso = self.verificar_vigencia(pieza_previa, ahora)
            motivo = motivo or _agenda_pasada(pieza_previa, ahora)
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
            if not pedido.forzar:
                self._exigir_cupo(pedido.usuario, ahora)
            dir_pedido = self.dir_pedidos / ahora.strftime("%Y-%m-%d") / f"{ahora:%H%M%S}_oportunidad_{ih.slug(ticker)}"
            hecha = self._preparar(pedido.orden, dir_pedido, ahora)
            pieza, descartes, reintento = self._con_fuente_directa(dir_pedido, ahora.date())
            a = pieza["datos"]["activos"][0]
            # La lámina se rinde antes del HTML: sin ella no hay botón «Descargar lámina».
            self.rendir_lamina(
                cm.payload_semanal(a, pieza["editorial"]["titulares"][ticker], pieza["datos"]["edicion"],
                                   self.autor, dir_pedido / a["grafico"]),
                "semanal", dir_pedido / cm.nombre_lamina(ticker))
            rg.anotar(ticker, dir_pedido, ahora, a["lectura"]["direccion"], quien, self.registro)
            if not pedido.forzar:
                self.estado.consumir(pedido.usuario, ahora)
            self.estado.guardar()
            avisos += [*hecha.avisos, *[f"Descarté una fuente: {d}" for d in descartes]]
            if reintento:
                avisos.append("La primera búsqueda no trajo ninguna noticia directa: hice un segundo intento y ese sí la trajo.")
        try:
            try:
                ruta = oh.guardar(pieza, dir_pedido, ejecutivo, self.autor, ahora.date(), self.publicar_imagen)
            except ip.ImagenNoPublicada as exc:
                # Sin URL pública el correo se arma igual, pero Gmail no mostraría sus imágenes: se avisa.
                avisos.append(f"No pude publicar las imágenes del correo ({exc}): en Gmail se verá sin imágenes.")
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
        aparte.append(self._a_drive([(ruta, ruta.name)], ahora, ticker, nombre))
        return Respuesta(pedido.chat, cm.texto_acompanamiento(nombre, pedido.orden.saludo), [ruta], "\n".join(aparte))

    def _seguimiento(self, pedido: Pedido, ahora: datetime) -> Respuesta:
        o = pedido.orden
        minutos = int(self.config["reuso_minutos"].get("seguimiento", 30))
        dir_pedido = self.estado.vigente(o.clave_base(), ahora, minutos)
        if dir_pedido is not None:
            pieza_existente = pr.cargar_pieza(dir_pedido)
            if "suceso" not in pieza_existente.get("datos", {}):
                dir_pedido = None
        if dir_pedido is None:
            self._exigir_cupo(pedido.usuario, ahora)
            dir_pedido = (self.dir_pedidos / ahora.strftime("%Y-%m-%d")
                          / f"{ahora:%H%M%S}_seguimiento_{ih.slug(o.args['ticker'])}")
            self._preparar(o, dir_pedido, ahora)
            d = pr.cargar_pieza(dir_pedido)["datos"]
            self.rendir_lamina(
                cm.payload_suceso(d["activo"], d["suceso"], d["edicion"], self.autor, dir_pedido / "grafico.png"),
                "seguimiento_dia", dir_pedido / "lamina.png")
            if rg.vigente(o.args["ticker"], ahora, self.registro) is not None:
                rg.anotar_seguimiento(o.args["ticker"],
                                      {"ticker": o.args["ticker"], "estado": d["evaluacion"]["estado"],
                                       "ejecutivo": pedido.usuario, "cuando": ahora.isoformat()}, self.registro)
            self.estado.registrar_pieza(o.clave_base(), dir_pedido, ahora, fija=False)
            self.estado.consumir(pedido.usuario, ahora)
            self.estado.guardar()
            # Solo la lámina recién rendida: reusarla 30 minutos no debe duplicarla en Drive con otra hora.
            self._a_drive([(dir_pedido / "lamina.png", f"seguimiento_{ih.slug(o.args['ticker'])}_{ahora:%H%M}.png")],
                          ahora, o.args["ticker"], d["activo"]["nombre"])
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

    def mensaje_con_teclado(self, chat: int, texto: str, teclado: dict[str, Any]) -> int:
        """Un mensaje con botones en línea; devuelve su id para poder quitarle el teclado después."""
        res = self._post("sendMessage", json={"chat_id": chat, "text": texto[:4000], "reply_markup": teclado})
        return int(res["message_id"])

    def quitar_teclado(self, chat: int, message_id: int) -> None:
        self._post("editMessageReplyMarkup",
                   json={"chat_id": chat, "message_id": message_id, "reply_markup": {"inline_keyboard": []}})

    def responder_callback(self, id_: str, texto: str = "") -> None:
        """Telegram deja el botón girando hasta que se responde el toque."""
        self._post("answerCallbackQuery", json={"callback_query_id": id_, "text": texto})

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
    por_confirmar: set[str] = field(default_factory=set)  # directores con un /recrear todas esperando el «sí»
    candado: threading.Lock = field(default_factory=threading.Lock, repr=False)
    avisos: av.Estado | None = None        # la alerta semanal: sin él, el bot no mide ni agenda nada
    agendador: Any = None
    parar: threading.Event = field(default_factory=threading.Event, repr=False)

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

        if usuario in self.por_confirmar:
            self.por_confirmar.discard(usuario)
            if od._plano(texto).strip(" .!") in ("si", "sip", "dale", "ok"):
                return self._recrear_todas(usuario, chat)
            return [Respuesta(chat, "Listo, no recreé nada.")]

        try:
            orden = od.interpretar(texto)
        except od.PedidoInvalido as exc:
            if texto.lower().startswith("/recrear") and usuario not in self._admins():
                return [Respuesta(chat, SIN_COMANDO)]
            return [Respuesta(chat, str(exc))]

        if orden.pieza == od.RECREAR:
            if usuario not in self._admins():
                return [Respuesta(chat, SIN_COMANDO)]  # para el ejecutivo el comando no existe
            return self._recrear(usuario, chat, orden)

        if orden.pieza in ("start", "ayuda"):
            return [Respuesta(chat, AYUDA)]
        if orden.pieza == "id":
            return [Respuesta(chat, f"Tu número de usuario es {usuario}.")]
        if orden.pieza == "estado":
            cupo = self.config["analistas"][usuario].get("cupo_diario", 10)
            usados = self.estado.usados(usuario, self.atendedor.reloj())
            return [Respuesta(chat, f"Piezas nuevas hoy: {usados} de {cupo}. En cola: {self.cola.qsize()}.")]

        if orden.pieza == "oportunidad" and self.avisos is not None:
            try:
                self.avisos.marcar_oportunidad(usuario, orden.args["ticker"], self.atendedor.reloj())
            except Exception:  # noqa: BLE001  la medición es un extra: nunca bota el pedido del ejecutivo
                _log(f"no pude anotar la oportunidad en la medición: {traceback.format_exc()}")
        return self._encolar(usuario, chat, orden)

    def _admins(self) -> set[str]:
        return {str(x) for x in self.config.get("admins", [])}

    def _recrear(self, usuario: str, chat: int, orden: od.Orden) -> list[Respuesta]:
        ticker = orden.args["ticker"]
        if ticker == od.TODAS:
            vigentes = rg.vigentes(self.atendedor.reloj(), self.atendedor.registro)
            if not vigentes:
                return [Respuesta(chat, "No hay análisis vigentes que recrear.")]
            self.por_confirmar.add(usuario)
            return [Respuesta(chat, f"Voy a rehacer {len(vigentes)} análisis ({', '.join(vigentes)}) y reemplazan "
                                    "lo que reciben los ejecutivos desde ahora. Gasta agy y tarda unos minutos por "
                                    "activo. Responde «sí» para empezar.")]
        return self._encolar(usuario, chat, od.Orden("oportunidad", {"ticker": ticker}), forzar=True)

    def _recrear_todas(self, usuario: str, chat: int) -> list[Respuesta]:
        vigentes = rg.vigentes(self.atendedor.reloj(), self.atendedor.registro)
        if not vigentes:
            return [Respuesta(chat, "No hay análisis vigentes que recrear.")]
        respuestas = [Respuesta(chat, f"Empiezo a rehacer {len(vigentes)} análisis. Cada uno te llega cuando termina.")]
        for t in vigentes:
            orden = od.Orden("oportunidad", {"ticker": t})
            with self.candado:
                ocupada = orden.clave_base().lower() in self.generando
            r = self._encolar(usuario, chat, orden, forzar=True)
            if ocupada:  # ya venía armándose: se avisa; los «Recibido» sobran con el aviso de arriba
                respuestas += r
        return respuestas

    def _encolar(self, usuario: str, chat: int, orden: od.Orden, forzar: bool = False) -> list[Respuesta]:
        if orden.pieza == "oportunidad":
            clave = orden.clave_base().lower()
            with self.candado:
                if clave in self.generando:
                    return [Respuesta(chat, f"Ya se está generando el análisis de {orden.args['ticker']}. Pídelo de "
                                            "nuevo en unos minutos y te llega al tiro.")]
                self.generando.add(clave)

        en_cola = self.cola.qsize() + (1 if self.ocupado.is_set() else 0)
        self.cola.put(Pedido(usuario, chat, orden, forzar))
        _log(f"pedido {usuario}: {orden.clave_base()}")
        if en_cola:
            return [Respuesta(chat, f"Recibido. Hay {en_cola} pedido(s) antes que el tuyo.")]
        if orden.pieza == "oportunidad":
            return [Respuesta(chat, f"Recibido. Armando el análisis de {orden.args['ticker']}: si ya hay uno "
                                    "vigente te lo entrego al tiro; si no, tarda unos minutos.")]
        return [Respuesta(chat, "Recibido. Preparo la pieza: una nueva tarda unos minutos.")]

    # ───────────────────────────────────────── la alerta semanal (spec 2026-10-18)

    def enviar_aviso(self, ejecutivo: str, aviso: av.Aviso) -> int | None:
        """Manda el aviso por Telegram con su teclado y devuelve el id del mensaje (None si va sin botones)."""
        chat = int(ejecutivo)
        if aviso.tipo == "mapa":
            teclado = {"inline_keyboard": [[{"text": "👍 Útil", "callback_data": f"sw:util:{aviso.id}"},
                                            {"text": "👎 No me sirve", "callback_data": f"sw:no:{aviso.id}"}]]}
        elif aviso.activo:
            alias = mac.ALIAS_DEL_BOT.get(aviso.activo, aviso.activo.lower())
            alias = {"dolar": "dólar", "petroleo": "petróleo"}.get(alias, alias)   # lo que lee el ejecutivo
            teclado = {"inline_keyboard": [[{"text": f"📊 Ver análisis de {alias}",
                                             "callback_data": f"sw:ped:{aviso.id}"}]]}
        else:
            self.tg.mensaje(chat, aviso.texto)
            return None
        return self.tg.mensaje_con_teclado(chat, aviso.texto, teclado)

    def activar_avisos(self, reloj: Callable[[], datetime] | None = None) -> None:
        """Enciende la alerta semanal: el estado en disco y el agendador que lo alimenta."""
        self.avisos = av.Estado()
        self.agendador = av.Agendador(self.config, self.avisos, self.enviar_aviso,
                                      lambda chat, texto: self.tg.mensaje(int(chat), texto),
                                      reloj or self.atendedor.reloj, log=_log)

    def iniciar_avisos(self, pausa: float = 60.0) -> threading.Thread | None:
        """El hilo que late cada minuto. Un error del latido se registra y nunca tumba el polling."""
        if self.agendador is None:
            return None

        def latir() -> None:
            while True:
                try:
                    self.agendador.latido()
                except Exception:  # noqa: BLE001
                    _log(f"avisos de la semana: {traceback.format_exc()}")
                if self.parar.wait(pausa):
                    return

        hilo = threading.Thread(target=latir, daemon=True)
        hilo.start()
        return hilo

    def recibir_callback(self, update: dict[str, Any]) -> list[Respuesta]:
        """Los toques de los botones de la alerta: voto Útil / No me sirve y el pedido de la víspera.

        Garantiza que todo callback_query con id y prefijo 'sw:' se responda exactamente una vez
        para que Telegram no deje el botón girando (Menor 13). Callbacks de otro prefijo no se tocan.
        """
        cb = update.get("callback_query") or {}
        cb_id = cb.get("id")
        data = str(cb.get("data") or "")
        if not cb_id or not data.startswith("sw:"):
            return []
        texto_cb, respuestas = self._procesar_callback_sw(cb)
        self._responder_callback(cb_id, texto_cb)
        return respuestas

    def _procesar_callback_sw(self, cb: dict[str, Any]) -> tuple[str, list[Respuesta]]:
        """Procesa la lógica de negocio del callback 'sw:' y devuelve (texto_a_responder, respuestas)."""
        usuario = str((cb.get("from") or {}).get("id", ""))
        if self.avisos is None or usuario not in self.config["analistas"]:
            return "", []

        msg = cb.get("message") or {}
        chat, message_id = (msg.get("chat") or {}).get("id"), msg.get("message_id")
        if not chat:
            return "", []

        partes = str(cb.get("data", "")).split(":")
        if len(partes) != 3 or partes[0] != "sw" or partes[1] not in ("util", "no", "ped"):
            return "", []

        _, accion, id_ = partes
        registro = self.avisos.registro(usuario, id_)
        if registro is None:
            return "Ese aviso ya no está disponible", []

        ahora = self.atendedor.reloj()
        if accion == "ped":
            if not registro.get("activo"):
                return "", []
            self.avisos.anotar_clic(usuario, id_, ahora)
            # El pedido del botón no pasa por `recibir`: ya cuenta como clic y no como pedido propio.
            return "Armando el análisis", self._encolar(
                usuario, chat, od.Orden("oportunidad", {"ticker": registro["activo"]})
            )

        voto = "util" if accion == "util" else "no_sirve"
        if self.avisos.anotar_voto(usuario, id_, voto, ahora):
            try:
                self.tg.quitar_teclado(chat, message_id)
            except Exception:  # noqa: BLE001  el teclado que queda no daña: el voto ya está anotado
                _log(f"no pude quitar el teclado: {traceback.format_exc()}")
            return "¡Gracias!", []

        return "Ya votaste este aviso", []

    def _responder_callback(self, id_: str | None, texto: str) -> None:
        try:
            self.tg.responder_callback(id_, texto)
        except Exception:  # noqa: BLE001
            _log(f"no pude responder el callback: {traceback.format_exc()}")

    def atender_update(self, update: dict[str, Any]) -> None:
        """Un mensaje o el toque de un botón; lo que haya que contestar se entrega acá."""
        respuestas = self.recibir_callback(update) if "callback_query" in update else self.recibir(update)
        for r in respuestas:
            entregar(self.tg, r)

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
        self.iniciar_avisos()
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
                    self.atender_update(update)
            except Exception:  # noqa: BLE001
                _log(f"polling: {traceback.format_exc()}")
                time.sleep(5)
