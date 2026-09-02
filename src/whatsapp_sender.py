"""Módulo de automatización segura y robusta de WhatsApp Web con Playwright.

Proporciona el cliente WhatsAppSender con:
- Persistencia de sesión (IndexedDB/cookies en .whatsapp_session/).
- Banderas anti-detección (Stealth mode, remoción de navigator.webdriver).
- Resolución de alias canónicos de grupos oficiales (config/whatsapp_grupos.json).
- Validación estricta de doble chequeo en la cabecera activa del chat antes de enviar.
- Soporte para texto plano/formateado, imágenes (stories/gráficos) y PDFs con caption.
- Detección multi-selector de WhatsApp Web actual con confirmación asistida en setup.
- Cierre seguro de contextos para evitar corrupción de bases de datos locales.
"""
from __future__ import annotations

import json
import logging
import random
import sys
import threading
import time
from datetime import date
from pathlib import Path
from typing import Any

# Configurar encoding seguro para consola de Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("whatsapp_sender")

# Raíz del proyecto
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
CONFIG_GRUPOS_PATH = RAIZ_PROYECTO / "config" / "whatsapp_grupos.json"
DEFAULT_SESSION_DIR = RAIZ_PROYECTO / ".whatsapp_session"

# Contador de envíos, para que el ritmo no dependa de la memoria de nadie. Vive
# en disco porque cada envío es un proceso distinto: sin esto, diez llamadas
# seguidas salen en ráfaga y ese patrón es el que delata a un bot.
ESTADO_ENVIOS_PATH = RAIZ_PROYECTO / "data" / ".whatsapp_envios.json"
SEGUNDOS_ENTRE_ENVIOS = 45
MAX_ENVIOS_DIA = 40

# Selectores del DOM de WhatsApp Web
SELECTORES_QR = [
    'canvas[aria-label*="Scan"]',
    'canvas[aria-label*="código"]',
    '[data-testid="qrcode"]',
    'div[data-ref]',
]

# Medidos contra el DOM real de WhatsApp Web el 2026-09-01. Los `data-testid`
# históricos (`chat-list-search`, `send`, `msg-time`, `conversation-info-header`
# fuera del chat) ya no existen o cambiaron de nombre; los que sobreviven están
# comprobados uno por uno.
SELECTORES_AUTENTICADO = [
    'div[id="pane-side"]',
    'div[id="side"]',
    'div[data-testid="chat-list"]',
    '[aria-label="Lista de chats"]',
    '[aria-label="Chat list"]',
]

# El buscador es un <input>, no un div contenteditable: los dos selectores
# anteriores medían 0 y hacían fallar TODOS los envíos en el primer paso.
SELECTORES_BUSCADOR = [
    'input[role="textbox"][data-tab="3"]',
    '[data-testid="chat-list-search-container"] input',
    'input[aria-label*="Buscar"]',
]

# La caja de mensaje sí conserva sus selectores.
SELECTORES_CAJA_TEXTO = [
    'div[contenteditable="true"][data-tab="10"]',
    'footer div[contenteditable="true"][role="textbox"]',
    '[data-testid="conversation-compose-box-input"]',
]

# El botón de enviar perdió su testid; hoy se identifica por aria-label. En el
# modal de adjunto el rótulo lleva la cuenta ("Enviar 1 seleccionado").
SELECTORES_ENVIAR = [
    '[aria-label="Enviar"]',
    '[aria-label^="Enviar"]',
    '[data-testid="send"]',
]

SELECTORES_ADJUNTAR = [
    '[aria-label="Adjuntar"]',
    '[data-testid="attach-menu-plus"]',
]

# Extensiones que el input por defecto (accept="image/*") sí acepta. Cualquier
# otra cosa —un PDF de informe, un .txt— tiene que entrar por el menú Adjuntar.
EXTENSIONES_IMAGEN = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


# El pie de foto vive en el editor de medios, NO en el composer del chat.
SELECTORES_CAPTION = [
    '[data-testid="media-caption-input-container"]',
    'div[contenteditable="true"][aria-label="Escribe un mensaje"]:not(footer *)',
]


def _requiere_menu_documento(ruta: Path) -> bool:
    """True si el archivo no es una imagen."""
    return Path(ruta).suffix.lower() not in EXTENSIONES_IMAGEN


def _opcion_menu_adjuntar(ruta: Path) -> str:
    """Qué opción del menú Adjuntar corresponde al archivo.

    TODO adjunto pasa por este menú, imágenes incluidas. El `input[type=file]`
    que está siempre presente en el chat es el **creador de stickers**: un PNG
    empujado por ahí llega como sticker y sin pie de foto (medido el 2026-09-01,
    la lista de chats mostró "Sticker"). El input real de cada tipo lo monta
    WhatsApp recién al elegir la opción, y aparece como un file chooser nativo.
    """
    return "Documento" if _requiere_menu_documento(ruta) else "Fotos y videos"

SELECTORES_SINCRONIZANDO = [
    "progress",
    '[data-testid="intro-md-beta-logo-dark"]',
    'div[role="progressbar"]',
    'text="Descargando mensajes"',
    'text="Organizando mensajes"',
]


class WhatsAppError(RuntimeError):
    """Excepción base para errores de automatización de WhatsApp."""


class SesionNoIniciadaError(WhatsAppError):
    """La sesión no está autenticada o requiere escanear código QR."""


class DestinatarioInvalidoError(WhatsAppError):
    """El destinatario no existe o la validación de cabecera activa falló."""


class EnvioMensajeError(WhatsAppError):
    """Fallo durante el proceso de tipeo, adjunto o confirmación de envío."""


class LimiteEnviosError(WhatsAppError):
    """Se alcanzó el cupo diario de envíos.

    Automatizar WhatsApp Web va contra sus términos de servicio y la cuenta del
    proyecto es la del negocio. El cupo no es una cortesía: es el freno que evita
    que un bucle mal escrito mande cien mensajes y se lleve el número por delante.
    """


class WhatsAppConfig:
    """Carga y valida la configuración de canales de WhatsApp."""

    def __init__(self, config_path: Path | str | None = None) -> None:
        self.path = Path(config_path) if config_path else CONFIG_GRUPOS_PATH
        self.grupos: dict[str, dict[str, Any]] = {}
        self.seguridad: dict[str, Any] = {}
        self.cargar()

    def cargar(self) -> None:
        if not self.path.exists():
            logger.warning("No se encontró archivo de configuración en %s. Usando valores por defecto.", self.path)
            self.grupos = {}
            self.seguridad = {
                "session_dir": str(DEFAULT_SESSION_DIR),
                "timeout_busqueda_ms": 15000,
                "timeout_envio_ms": 30000,
                "min_jitter_ms": 800,
                "max_jitter_ms": 2000,
            }
            return

        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.grupos = data.get("grupos", {})
        self.seguridad = data.get("seguridad", {})

    def resolver_nombre_oficial(self, alias_o_nombre: str) -> str:
        """Resuelve un alias o slug (ej. 'forex', '02_forex_divisas') al nombre oficial de WhatsApp."""
        busqueda = alias_o_nombre.strip().lower()

        # 1. Coincidencia exacta con slug de clave (ej. '02_forex_divisas')
        if busqueda in self.grupos:
            return str(self.grupos[busqueda].get("nombre_oficial", busqueda))

        # 2. Coincidencia en la lista de alias
        for slug, info in self.grupos.items():
            if busqueda == slug.lower():
                return str(info.get("nombre_oficial", slug))
            aliases = [str(a).lower() for a in info.get("alias", [])]
            if busqueda in aliases:
                return str(info.get("nombre_oficial", slug))
            if busqueda == str(info.get("nombre_oficial", "")).lower():
                return str(info.get("nombre_oficial", slug))

        # 3. Si no coincide con ningún alias configurado, devuelve el nombre tal cual
        return alias_o_nombre.strip()


class WhatsAppSender:
    """Cliente de automatización para WhatsApp Web usando Playwright."""

    URL_WHATSAPP = "https://web.whatsapp.com"

    def __init__(
        self,
        session_dir: Path | str | None = None,
        config_path: Path | str | None = None,
        headless: bool = True,
    ) -> None:
        self.config = WhatsAppConfig(config_path)
        # `session_dir` viene relativo en el config. Anclarlo a la raíz del repo y no
        # al directorio de trabajo: si no, ejecutar desde otro cwd apunta a una
        # carpeta vacía, reporta "sesión expirada" con la sesión intacta, y un
        # `--login` ahí vincularía un perfil distinto del que usan los envíos.
        cruda = Path(session_dir) if session_dir else Path(
            self.config.seguridad.get("session_dir", DEFAULT_SESSION_DIR)
        )
        self.session_dir = cruda if cruda.is_absolute() else (RAIZ_PROYECTO / cruda)
        self.headless = headless
        self.timeout_busqueda_ms = int(self.config.seguridad.get("timeout_busqueda_ms", 15000))
        self.timeout_envio_ms = int(self.config.seguridad.get("timeout_envio_ms", 30000))
        self.min_jitter_ms = int(self.config.seguridad.get("min_jitter_ms", 800))
        self.max_jitter_ms = int(self.config.seguridad.get("max_jitter_ms", 2000))
        self.segundos_entre_envios = int(
            self.config.seguridad.get("segundos_entre_envios", SEGUNDOS_ENTRE_ENVIOS)
        )
        self.max_envios_dia = int(self.config.seguridad.get("max_envios_dia", MAX_ENVIOS_DIA))

    @staticmethod
    def _leer_estado_envios() -> dict[str, Any]:
        """Contador del día: {fecha, enviados, ultimo_ts}."""
        hoy = date.today().isoformat()
        try:
            datos = json.loads(ESTADO_ENVIOS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"fecha": hoy, "enviados": 0, "ultimo_ts": 0.0}
        if datos.get("fecha") != hoy:
            return {"fecha": hoy, "enviados": 0, "ultimo_ts": 0.0}
        return {
            "fecha": hoy,
            "enviados": int(datos.get("enviados", 0)),
            "ultimo_ts": float(datos.get("ultimo_ts", 0.0)),
        }

    def _registrar_envio(self) -> None:
        estado = self._leer_estado_envios()
        estado["enviados"] += 1
        estado["ultimo_ts"] = time.time()
        try:
            ESTADO_ENVIOS_PATH.parent.mkdir(parents=True, exist_ok=True)
            ESTADO_ENVIOS_PATH.write_text(json.dumps(estado), encoding="utf-8")
        except OSError as exc:  # noqa: BLE001
            logger.warning("No se pudo registrar el envío (%s); el freno queda ciego.", exc)

    def _esperar_turno(self) -> None:
        """Impone el cupo diario y la cadencia mínima entre envíos."""
        estado = self._leer_estado_envios()

        if estado["enviados"] >= self.max_envios_dia:
            raise LimiteEnviosError(
                f"Se alcanzó el cupo de {self.max_envios_dia} envíos para hoy "
                f"({estado['enviados']} hechos). Se detiene a propósito: pasar de ahí "
                "es lo que hace que WhatsApp marque la cuenta. Retoma mañana o sube "
                "'max_envios_dia' en config/whatsapp_grupos.json sabiendo el riesgo."
            )

        transcurrido = time.time() - estado["ultimo_ts"]
        if estado["ultimo_ts"] and transcurrido < self.segundos_entre_envios:
            espera = self.segundos_entre_envios - transcurrido
            logger.info("Cadencia anti-baneo: esperando %.0fs antes del próximo envío.", espera)
            print(
                f"[RITMO] Esperando {espera:.0f}s para no enviar en ráfaga "
                f"(mínimo {self.segundos_entre_envios}s entre mensajes).",
                flush=True,
            )
            time.sleep(espera)

    def _pausa_humana(self, factor: float = 1.0) -> None:
        """Introduce una pausa aleatoria para emular comportamiento humano."""
        delay_ms = random.randint(self.min_jitter_ms, self.max_jitter_ms) * factor
        time.sleep(delay_ms / 1000.0)

    def _aplicar_stealth(self, context: Any) -> None:
        """Inyecta scripts para ocultar la firma de automatización de Chromium."""
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-419', 'es', 'en-US', 'en']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

    def _crear_contexto(self, playwright_instance: Any, headless: bool):
        """Lanza el contexto de navegador persistente."""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        user_agent = self.config.seguridad.get(
            "user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )

        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-infobars",
        ]

        context = playwright_instance.chromium.launch_persistent_context(
            user_data_dir=str(self.session_dir),
            headless=headless,
            user_agent=user_agent,
            # El editor de medios necesita alto para montar su campo de pie de
            # foto; a 1280x800 queda apretado contra la barra inferior.
            viewport={"width": 1600, "height": 1000},
            ignore_default_args=["--enable-automation"],
            args=args,
        )
        self._aplicar_stealth(context)
        return context

    def _hay_qr_visible(self, page: Any) -> bool:
        """Verifica si en la página actual se muestra el código QR."""
        for selector in SELECTORES_QR:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except Exception:
                pass
        return False

    def _esta_autenticado(self, page: Any) -> bool:
        """Verifica si el panel principal o lista de chats ya está renderizada."""
        for selector in SELECTORES_AUTENTICADO:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    def _primer_locator(page: Any, selectores: list[str]) -> Any | None:
        """El primer selector de la lista que exista en la página."""
        for selector in selectores:
            try:
                loc = page.locator(selector).first
                if loc.count() > 0:
                    return loc
            except Exception:
                continue
        return None

    @staticmethod
    def _header_coincide(nombre_oficial: str, texto_header: str) -> bool:
        """Compara el destinatario con la cabecera del chat abierto, EXACTO.

        La comparación era por substring, y con los nombres reales eso es un
        agujero: "Grupo Inteligencia" está contenido en los otros seis canales,
        así que pedir el grupo padre y aterrizar en Dólar & FX pasaba la
        validación. Se compara contra la PRIMERA línea de la cabecera, que es el
        nombre del chat; las siguientes traen el subtítulo (miembros, estado).
        """
        primera = (texto_header or "").strip().splitlines()
        if not primera:
            return False
        return primera[0].strip().casefold() == nombre_oficial.strip().casefold()

    def _esta_sincronizando(self, page: Any) -> bool:
        """Verifica si WhatsApp Web está en pantalla de descarga/organización de mensajes."""
        for selector in SELECTORES_SINCRONIZANDO:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except Exception:
                pass
        return False

    def ejecutar_login_interactivo(self, timeout_s: int = 120) -> bool:
        """Abre Chromium visible para vincular la sesión con código QR y confirmación dual."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as err:
            raise WhatsAppError("Playwright no está instalado. Ejecute: uv sync --extra stories") from err

        print("\n=======================================================")
        print("          [WHATSAPP SETUP - VINCULACIÓN DE SESIÓN]")
        print("=======================================================")
        print(f"• Carpeta de sesión : {self.session_dir.resolve()}")
        print(f"• Tiempo límite     : {timeout_s} segundos")
        print("\n👉 Abre WhatsApp en tu celular > Dispositivos vinculados > Vincular un dispositivo.")
        print("👉 Escanea el código QR que aparecerá en la ventana del navegador.")
        print("👉 (Opcional) Cuando veas tus chats en pantalla, presiona [ENTER] en esta consola para confirmar inmediatamente.\n")

        # Evento para confirmación manual por teclado en consola
        confirmacion_manual = threading.Event()

        def escuchar_enter():
            try:
                sys.stdin.readline()
                confirmacion_manual.set()
            except Exception:
                pass

        hilo_teclado = threading.Thread(target=escuchar_enter, daemon=True)
        hilo_teclado.start()

        with sync_playwright() as p:
            context = self._crear_contexto(p, headless=False)
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(self.URL_WHATSAPP, wait_until="domcontentloaded")

                inicio = time.time()
                qr_detectado = False
                autenticado = False

                while time.time() - inicio < timeout_s:
                    # 1. Si el usuario presionó ENTER en la consola
                    if confirmacion_manual.is_set():
                        print("\n[WHATSAPP SETUP] Confirmación manual recibida por teclado.")
                        autenticado = True
                        break

                    # 2. Detección de presencia de QR
                    if self._hay_qr_visible(page):
                        if not qr_detectado:
                            print("[WHATSAPP SETUP] Código QR detectado en pantalla. Esperando escaneo...")
                            qr_detectado = True

                    # 3. Detección de autenticación automática
                    if self._esta_autenticado(page):
                        print("\n[WHATSAPP SETUP] ¡Panel de chats detectado automáticamente!")
                        autenticado = True
                        break

                    # 4. Detección de pantalla de sincronización tras escaneo
                    if qr_detectado and not self._hay_qr_visible(page):
                        if self._esta_sincronizando(page):
                            print("[WHATSAPP SETUP] Código escaneado. WhatsApp Web está sincronizando chats...", end="\r")

                    time.sleep(1.0)

                if autenticado:
                    print("\n[WHATSAPP SETUP] Guardando estado de sesión en disco...")
                    page.wait_for_timeout(3500)  # Asegura flush completo de IndexedDB a disco
                    print("[WHATSAPP SETUP] ¡Excelente! Sesión vinculada y guardada con éxito.")
                    return True
                else:
                    print("\n[WHATSAPP SETUP] Tiempo de espera agotado sin detectar inicio de sesión.")
                    return False
            finally:
                context.close()

    def _verificar_autenticacion(self, page: Any, timeout_s: int = 30) -> None:
        """Valida que la página esté en estado autenticado y lista para interactuar."""
        inicio = time.time()
        while time.time() - inicio < timeout_s:
            # Si aparece el canvas del QR
            if self._hay_qr_visible(page):
                raise SesionNoIniciadaError(
                    "La sesión de WhatsApp Web no está vinculada o expiró. "
                    "Ejecuta: python scripts/enviar_whatsapp.py --login"
                )

            # Si el panel de chats ya está visible
            if self._esta_autenticado(page):
                return

            time.sleep(0.5)

        if page.locator('text="Sin conexión"').count() > 0:
            raise WhatsAppError("WhatsApp Web indica falta de conexión a Internet.")

        raise WhatsAppError("No se pudo verificar la carga del panel principal de WhatsApp Web.")

    def verificar_estado_sesion(self) -> dict[str, Any]:
        """Realiza un chequeo rápido en segundo plano para certificar si la sesión está viva."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as err:
            raise WhatsAppError("Playwright no está instalado. Ejecute: uv sync --extra stories") from err

        with sync_playwright() as p:
            context = self._crear_contexto(p, headless=True)
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(self.URL_WHATSAPP, wait_until="domcontentloaded")
                
                inicio = time.time()
                while time.time() - inicio < 20.0:
                    if self._hay_qr_visible(page):
                        return {
                            "autenticado": False,
                            "estado": "requiere_login",
                            "mensaje": f"Se detectó código QR: la sesión expiró o no está vinculada ({self.session_dir}).",
                        }
                    if self._esta_autenticado(page):
                        return {
                            "autenticado": True,
                            "estado": "activa",
                            "mensaje": f"Sesión activa y lista para enviar ({self.session_dir}).",
                        }
                    time.sleep(1.0)

                return {
                    "autenticado": False,
                    "estado": "timeout",
                    "mensaje": "No se pudo determinar el estado en el tiempo esperado.",
                }
            finally:
                context.close()

    def _buscar_y_abrir_chat(self, page: Any, nombre_oficial: str) -> None:
        """Busca el chat por nombre y valida la cabecera activa (Double Check)."""
        # 1. Localizar la barra de búsqueda de chats
        buscador = self._primer_locator(page, SELECTORES_BUSCADOR)
        if buscador is None:
            raise EnvioMensajeError(
                "No se encontró la barra de búsqueda de chats en WhatsApp Web. "
                "El DOM pudo haber cambiado: revisa SELECTORES_BUSCADOR."
            )

        buscador.click()
        self._pausa_humana(0.5)

        # `fill` y no `type`: el tipeo carácter a carácter parte los pares
        # suplentes de los emoji, y hay un canal cuyo nombre lleva uno.
        buscador.fill("")
        buscador.fill(nombre_oficial)
        self._pausa_humana(1.2)

        # 2. Localizar el resultado en la lista
        resultado = page.locator(f'span[title="{nombre_oficial}"]')
        if resultado.count() == 0:
            resultado = page.locator(f'[data-testid="cell-frame-title"]:has-text("{nombre_oficial}")')

        if resultado.count() == 0:
            raise DestinatarioInvalidoError(
                f'No se encontró el grupo o contacto "{nombre_oficial}" en WhatsApp Web. '
                "Verifique que la cuenta esté añadida a dicho grupo."
            )

        resultado.first.click()
        try:
            page.wait_for_selector("div#main", timeout=self.timeout_busqueda_ms)
        except Exception as exc:  # noqa: BLE001
            raise DestinatarioInvalidoError(
                f'No se llegó a abrir la conversación con "{nombre_oficial}": {exc}'
            ) from exc
        self._pausa_humana(1.0)

        # 3. DOBLE CHEQUEO DE SEGURIDAD (Active Header Check)
        # El fallback NO puede ser `header` a secas: el primero de la página es
        # el del panel izquierdo ("Actualizaciones en Estados"), no el del chat.
        header_locator = self._primer_locator(
            page, ['[data-testid="conversation-info-header"]', "div#main header"]
        )
        texto_header = header_locator.inner_text() if header_locator is not None else ""

        if not self._header_coincide(nombre_oficial, texto_header):
            raise DestinatarioInvalidoError(
                f'FALLO DE SEGURIDAD: El chat activo visible en pantalla '
                f'("{texto_header.strip().splitlines()[0] if texto_header.strip() else "sin cabecera"}") '
                f'no coincide con el destinatario solicitado ("{nombre_oficial}"). Abortando envío.'
            )

    def _insertar_texto(self, page: Any, texto: str) -> None:
        """Escribe el texto en la caja de conversación respetando saltos de línea."""
        caja = self._primer_locator(page, SELECTORES_CAJA_TEXTO)
        if caja is None:
            raise EnvioMensajeError("No se encontró la caja de texto para escribir el mensaje.")

        caja.click()
        self._pausa_humana(0.4)
        # Un borrador olvidado de una corrida anterior se enviaría pegado a este
        # mensaje. Se limpia siempre antes de escribir.
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        self._pausa_humana(0.3)
        self._escribir_multilinea(page, texto)
        self._pausa_humana(0.8)

    @staticmethod
    def _escribir_multilinea(page: Any, texto: str) -> None:
        """Escribe respetando los saltos de línea (Shift+Enter, nunca Enter solo)."""
        lineas = texto.splitlines()
        for i, linea in enumerate(lineas):
            if linea:
                page.keyboard.insert_text(linea)
            if i < len(lineas) - 1:
                page.keyboard.down("Shift")
                page.keyboard.press("Enter")
                page.keyboard.up("Shift")
                time.sleep(0.05)

    def _adjuntar_archivo(self, page: Any, ruta_archivo: Path, caption: str = "") -> None:
        """Adjunta por el menú Adjuntar y escribe el pie dentro del editor."""
        ruta_archivo = Path(ruta_archivo)
        if not ruta_archivo.exists():
            raise FileNotFoundError(f"El archivo adjunto no existe: {ruta_archivo}")

        boton = self._primer_locator(page, SELECTORES_ADJUNTAR)
        if boton is None:
            raise EnvioMensajeError(
                'No se encontró el botón "Adjuntar". Es la única vía correcta: el '
                "campo de archivo suelto del chat es el creador de stickers."
            )
        boton.click()
        self._pausa_humana(0.8)

        opcion = _opcion_menu_adjuntar(ruta_archivo)
        try:
            with page.expect_file_chooser(timeout=self.timeout_envio_ms) as selector_archivo:
                page.get_by_text(opcion, exact=True).first.click()
            selector_archivo.value.set_files(str(ruta_archivo.resolve()))
        except Exception as exc:  # noqa: BLE001
            raise EnvioMensajeError(
                f'No se pudo adjuntar {ruta_archivo.name} por "{opcion}": {exc}'
            ) from exc

        # El editor está listo cuando aparece su botón de enviar.
        try:
            page.wait_for_selector('[aria-label^="Enviar"]', timeout=self.timeout_envio_ms)
        except Exception as exc:  # noqa: BLE001
            raise EnvioMensajeError(
                f"El editor de medios no terminó de abrirse para {ruta_archivo.name}: {exc}"
            ) from exc
        self._pausa_humana(2.0)

        if not caption.strip():
            return

        caja_caption = self._primer_locator(page, SELECTORES_CAPTION)
        if caja_caption is None:
            raise EnvioMensajeError(
                "No apareció el campo de pie de foto del editor. Se aborta para no "
                "mandar la pieza muda ni dejar el texto como borrador en el chat."
            )
        # `click()` sobre el contenedor: el <p> del placeholder intercepta el
        # puntero, así que se enfoca el editor por su propio nodo.
        try:
            caja_caption.click(timeout=8000)
        except Exception:  # noqa: BLE001
            caja_caption.click(timeout=8000, force=True)
        self._pausa_humana(0.5)
        self._escribir_multilinea(page, caption.strip())
        self._pausa_humana(0.8)

        # El pie tiene que haber quedado DENTRO del editor. Si terminó en el
        # composer del chat, enviar mandaría el texto suelto y tiraría la imagen.
        try:
            texto_pie = caja_caption.inner_text().strip()
        except Exception:  # noqa: BLE001
            texto_pie = ""
        if not texto_pie:
            raise EnvioMensajeError(
                "El pie de foto no quedó en el editor de medios. Se aborta antes de "
                "enviar para no publicar la imagen sin texto."
            )

    @staticmethod
    def _contar_mensajes(page: Any) -> int:
        """Burbujas en la conversación abierta.

        Se cuenta `div[role="row"]`: las clases `message-out` / `message-in` ya
        no existen en el DOM actual (medido: 0 coincidencias) y los `data-id` ya
        no traen el prefijo `true_`/`false_` que distinguía las salientes.
        """
        try:
            return page.locator('#main div[role="row"]').count()
        except Exception:  # noqa: BLE001
            return -1

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Solo letras, dígitos y espacios, en minúsculas.

        WhatsApp renderiza los emoji como `<img>`, así que `innerText` los
        devuelve como un espacio en blanco: un testigo que conserve el emoji no
        coincide nunca con lo que se ve en pantalla (falso negativo medido el
        2026-09-01 sobre un envío que sí había llegado). De paso caen los
        asteriscos de negrita y los separadores decorativos del kit.
        """
        limpio = "".join(
            c if (c.isalnum() or c.isspace()) else " " for c in (texto or "")
        )
        return " ".join(limpio.split()).casefold()

    @staticmethod
    def _testigo(mensaje: str) -> str:
        """Un fragmento normalizado del mensaje, para reconocerlo ya enviado."""
        for linea in (mensaje or "").splitlines():
            limpia = WhatsAppSender._normalizar(linea)
            if len(limpia) >= 8:
                return limpia[:40]
        return ""

    @staticmethod
    def _texto_ultimas_filas(page: Any, n: int = 4) -> str:
        """El texto de las últimas burbujas de la conversación."""
        try:
            return page.evaluate(
                "(n) => Array.from(document.querySelectorAll('#main div[role=row]'))"
                ".slice(-n).map(r => r.innerText || '').join(' ')",
                n,
            ) or ""
        except Exception:  # noqa: BLE001
            return ""

    @staticmethod
    def _boton_enviar(page: Any, fuera_del_footer: bool = False) -> Any | None:
        """El control de enviar; opcionalmente el del editor de medios.

        Con el editor abierto hay DOS candidatos con `aria-label` que empieza por
        "Enviar": el del composer (dentro de `footer`, aparece en cuanto el
        composer tiene texto) y el del editor ("Enviar 1 seleccionado", fuera del
        footer). Clicar el del composer lo intercepta el overlay del editor, y el
        respaldo con Enter termina mandando el pie como mensaje de texto y
        descartando la imagen. Medido el 2026-09-01.
        """
        try:
            candidatos = page.locator('[aria-label^="Enviar"]')
            total = candidatos.count()
        except Exception:  # noqa: BLE001
            return None
        for i in range(total):
            cand = candidatos.nth(i)
            if not fuera_del_footer:
                return cand
            try:
                if not cand.evaluate("e => !!e.closest('footer')"):
                    return cand
            except Exception:  # noqa: BLE001
                continue
        return None

    @staticmethod
    def _ultima_burbuja(page: Any) -> dict[str, Any]:
        """Texto y tipo de la ÚLTIMA burbuja de la conversación.

        Se mira solo la última y no "las tres últimas": con esa ventana, un PDF
        que no salió se daba por enviado porque el chequeo veía la foto de un
        envío anterior (medido el 2026-09-01).
        """
        try:
            datos = page.evaluate(
                "() => {"
                " const filas = Array.from(document.querySelectorAll('#main div[role=row]'));"
                " const r = filas[filas.length - 1];"
                " if (!r) return {texto: '', media: false};"
                " const texto = r.innerText || '';"
                " const media = Array.from(r.querySelectorAll('img'))"
                "   .some(i => (i.src || '').startsWith('blob:'))"
                "   || !!r.querySelector('audio, video')"
                "   || /\bPDF\b|\bDOCX?\b|\bXLSX?\b|p\u00e1ginas/i.test(texto);"
                " return {texto, media};"
                "}"
            )
        except Exception:  # noqa: BLE001
            return {"texto": "", "media": False}
        return datos if isinstance(datos, dict) else {"texto": "", "media": False}

    def _adjunto_confirmado(self, page: Any, testigo: str) -> bool:
        """La última burbuja es el adjunto recién enviado, con su pie."""
        burbuja = self._ultima_burbuja(page)
        if not burbuja.get("media"):
            return False
        if not testigo:
            return True
        return testigo in self._normalizar(str(burbuja.get("texto", "")))

    def _clic_enviar_y_confirmar(
        self,
        page: Any,
        mensajes_antes: int,
        testigo: str = "",
        con_adjunto: bool = False,
        timeout_s: float = 25.0,
    ) -> None:
        """Envía y verifica que la burbuja nueva efectivamente apareció.

        La versión anterior esperaba a que `status-upload` y `msg-time` valieran
        0; ambos son testids muertos, así que la condición se cumplía en la
        primera vuelta y la función devolvía éxito sin comprobar nada. Ahora el
        testigo es el DOM de la conversación: si no aparece una fila nueva, el
        envío no ocurrió y hay que decirlo.
        """
        boton = self._boton_enviar(page, fuera_del_footer=con_adjunto)

        if con_adjunto:
            # Sin respaldo con Enter: acá Enter manda el pie como texto suelto y
            # tira la imagen, que es exactamente el fallo que se está corrigiendo.
            if boton is None:
                raise EnvioMensajeError(
                    "No se encontró el botón de enviar del editor de medios. Se aborta "
                    "en vez de usar Enter, que mandaría el pie de foto sin la imagen."
                )
            try:
                boton.click(timeout=10000)
            except Exception:  # noqa: BLE001
                # El <span> del ícono intercepta el puntero; el clic forzado va al
                # elemento correcto y el chequeo de media de abajo lo confirma.
                boton.click(timeout=10000, force=True)
        else:
            clic_ok = False
            if boton is not None:
                try:
                    boton.click(timeout=8000)
                    clic_ok = True
                except Exception as exc:  # noqa: BLE001
                    logger.warning("El clic en enviar falló (%s); se intenta con Enter.", exc)
            if not clic_ok:
                page.keyboard.press("Enter")

        inicio = time.time()
        while time.time() - inicio < timeout_s:
            # Testigo principal: ver el texto ya publicado en la conversación.
            # El conteo de filas NO sirve solo: WhatsApp virtualiza la lista y al
            # entrar un mensaje abajo descarta otro arriba, así que el total puede
            # quedar idéntico después de un envío correcto (falso negativo medido
            # el 2026-09-01 con un envío que sí había llegado).
            if con_adjunto:
                # El testigo de texto NO alcanza: si el pie viaja como mensaje
                # suelto también aparece, y la imagen se quedó sin enviar. Se
                # exige que la burbuja NUEVA sea el adjunto y lleve ese pie.
                if self._adjunto_confirmado(page, testigo):
                    self._pausa_humana(0.6)
                    return
            elif testigo:
                texto = self._normalizar(self._texto_ultimas_filas(page))
                if testigo in texto:
                    self._pausa_humana(0.6)
                    return
            else:
                ahora = self._contar_mensajes(page)
                if ahora < 0 or ahora > mensajes_antes:
                    self._pausa_humana(0.6)
                    return
            time.sleep(0.5)

        if con_adjunto:
            raise EnvioMensajeError(
                "El adjunto no apareció en la conversación después de presionar enviar "
                f"({timeout_s:.0f}s de espera). Revisa si llegó el pie de foto sin la "
                "imagen antes de reintentar, para no duplicar el mensaje."
            )
        raise EnvioMensajeError(
            "El mensaje no apareció en la conversación después de presionar enviar "
            f"({timeout_s:.0f}s de espera). No se puede dar el envío por bueno."
        )

    def enviar(
        self,
        destinatario: str,
        mensaje: str = "",
        adjunto: Path | str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Ejecuta el ciclo completo de envío a un grupo o contacto."""
        nombre_oficial = self.config.resolver_nombre_oficial(destinatario)
        ruta_adjunto = Path(adjunto) if adjunto else None

        if not mensaje.strip() and not ruta_adjunto:
            raise ValueError("Debe proporcionar al menos un mensaje de texto o un archivo adjunto.")

        if dry_run:
            print(f'[DRY RUN] Simulación de envío a: "{nombre_oficial}"')
            if ruta_adjunto:
                print(f"[DRY RUN] Archivo adjunto: {ruta_adjunto} (Existe: {ruta_adjunto.exists()})")
            if mensaje:
                print(f"[DRY RUN] Mensaje / Caption:\n{mensaje}")
            return {
                "status": "simulado",
                "destinatario": nombre_oficial,
                "adjunto": str(ruta_adjunto) if ruta_adjunto else None,
                "mensaje_len": len(mensaje),
            }

        # Playwright se importa acá y no al entrar: es un extra opcional
        # (`uv sync --extra stories`), y pedirlo antes dejaba sin funcionar el
        # dry-run y las validaciones, que no tocan el navegador.
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as err:
            raise WhatsAppError(
                "Playwright no está instalado. Ejecute: uv sync --extra stories"
            ) from err

        # El freno va ANTES de abrir el navegador: así la espera no deja una
        # sesión de WhatsApp Web colgando y sin actividad.
        self._esperar_turno()

        with sync_playwright() as p:
            context = self._crear_contexto(p, headless=self.headless)
            page = None
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(self.URL_WHATSAPP, wait_until="domcontentloaded")

                # 1. Verificar sesión
                self._verificar_autenticacion(page)

                # 2. Abrir chat y verificar cabecera
                self._buscar_y_abrir_chat(page, nombre_oficial)

                # 3. Fotografiar el estado del chat ANTES de tocar nada: es el
                #    punto de comparación que confirma que el envío ocurrió.
                mensajes_antes = self._contar_mensajes(page)

                # 4. Adjuntar o escribir texto
                if ruta_adjunto:
                    self._adjuntar_archivo(page, ruta_adjunto, caption=mensaje)
                else:
                    self._insertar_texto(page, mensaje)

                # 5. Enviar y confirmar contra el DOM
                self._clic_enviar_y_confirmar(
                    page,
                    mensajes_antes,
                    testigo=self._testigo(mensaje),
                    con_adjunto=ruta_adjunto is not None,
                )
                self._pausa_humana(1.0)
                self._registrar_envio()

                return {
                    "status": "enviado",
                    "destinatario": nombre_oficial,
                    "adjunto": str(ruta_adjunto) if ruta_adjunto else None,
                    "mensaje_len": len(mensaje),
                }
            except Exception as e:
                # `page` puede no existir si falló al abrir la pestaña: sin este
                # guard, el NameError enmascaraba el error real.
                if page is not None:
                    try:
                        debug_png = RAIZ_PROYECTO / "scratch" / f"whatsapp_error_{int(time.time())}.png"
                        debug_png.parent.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(debug_png))
                        logger.error("Captura de error guardada en %s", debug_png)
                    except Exception:  # noqa: BLE001
                        pass
                raise e
            finally:
                context.close()
