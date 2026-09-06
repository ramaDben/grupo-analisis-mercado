"""Tests unitarios y de seguridad para el módulo whatsapp_sender."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from unittest.mock import MagicMock

from whatsapp_sender import (
    WhatsAppConfig,
    WhatsAppSender,
    WhatsAppError,
    SesionNoIniciadaError,
    DestinatarioInvalidoError,
)

RAIZ = Path(__file__).resolve().parent.parent


def test_carga_configuracion_correcta():
    """Verifica que la configuración cargue los 7 grupos oficiales y parámetros de seguridad."""
    config = WhatsAppConfig()
    assert len(config.grupos) == 7
    assert "01_macro_y_apertura" in config.grupos
    assert "02_forex_divisas" in config.grupos
    assert "03_commodities_materias_primas" in config.grupos
    assert "04_indices_bursatiles" in config.grupos
    assert "05_acciones_etfs" in config.grupos
    assert "06_criptoactivos" in config.grupos
    assert "07_oportunidades_cuantitativas" in config.grupos

    assert "session_dir" in config.seguridad
    assert "timeout_busqueda_ms" in config.seguridad


def test_resolucion_alias_a_nombres_oficiales():
    """Verifica que los alias semánticos resuelvan al nombre oficial exacto."""
    config = WhatsAppConfig()

    casos = [
        ("macro", "Grupo Inteligencia | Comunidad de Traders"),
        ("apertura", "Grupo Inteligencia | Comunidad de Traders"),
        ("01_macro_y_apertura", "Grupo Inteligencia | Comunidad de Traders"),
        ("forex", "Grupo Inteligencia | Dólar & FX"),
        ("usdclp", "Grupo Inteligencia | Dólar & FX"),
        ("dolar", "Grupo Inteligencia | Dólar & FX"),
        ("commodities", "Grupo Inteligencia | Metales & Energía"),
        ("oro", "Grupo Inteligencia | Metales & Energía"),
        ("cobre", "Grupo Inteligencia | Metales & Energía"),
        ("indices", "Grupo Inteligencia | Wall Street & Índices"),
        ("nasdaq", "Grupo Inteligencia | Wall Street & Índices"),
        ("sp500", "Grupo Inteligencia | Wall Street & Índices"),
        ("acciones", "Grupo Inteligencia | Acciones & ETFs"),
        ("etfs", "Grupo Inteligencia | Acciones & ETFs"),
        ("cripto", "Grupo Inteligencia | Criptomercados"),
        ("btc", "Grupo Inteligencia | Criptomercados"),
        ("cuantitativo", "Grupo Inteligencia | Señales De Trading"),
        ("playbook", "Grupo Inteligencia | Señales De Trading"),
    ]

    for alias, esperado in casos:
        resultado = config.resolver_nombre_oficial(alias)
        assert resultado == esperado, f"Alias '{alias}' resolvió a '{resultado}', se esperaba '{esperado}'"


def test_todos_los_grupos_configurados_coinciden_con_docs():
    """Verifica conformidad total entre config/whatsapp_grupos.json y docs/grupos_whatsapp/."""
    config = WhatsAppConfig()
    docs_grupos = RAIZ / "docs" / "grupos_whatsapp"

    for clave, info in config.grupos.items():
        dir_grupo = docs_grupos / clave
        assert dir_grupo.is_dir(), f"Directorio de documentación no encontrado para {clave}"
        assert (dir_grupo / "info_grupo.txt").is_file(), f"Falta info_grupo.txt en {clave}"
        
        # Verificar que el nombre oficial esté presente en el info_grupo.txt
        info_txt = (dir_grupo / "info_grupo.txt").read_text(encoding="utf-8")
        assert info["nombre_oficial"] in info_txt, (
            f"El nombre oficial '{info['nombre_oficial']}' no está en {dir_grupo / 'info_grupo.txt'}"
        )


def test_session_dir_esta_en_gitignore():
    """Verifica que la carpeta de sesión de WhatsApp esté protegida en .gitignore."""
    gitignore = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert ".whatsapp_session/" in gitignore, ".whatsapp_session/ debe estar en .gitignore"


def test_dry_run_ejecuta_sin_errores():
    """Verifica que el modo dry_run simule el envío correctamente sin abrir Chromium."""
    sender = WhatsAppSender()
    resultado = sender.enviar(
        destinatario="forex",
        mensaje="Alerta de prueba",
        dry_run=True,
    )
    assert resultado["status"] == "simulado"
    assert resultado["destinatario"] == "Grupo Inteligencia | Dólar & FX"
    assert resultado["mensaje_len"] == len("Alerta de prueba")
    assert resultado["adjunto"] is None


def test_validacion_mensaje_y_adjunto_vacio_lanza_error():
    """Verifica que intentar enviar sin texto ni adjunto lance ValueError."""
    sender = WhatsAppSender()
    with pytest.raises(ValueError, match="al menos un mensaje de texto o un archivo adjunto"):
        sender.enviar(destinatario="forex", mensaje="", adjunto=None)


def test_adjunto_inexistente_lanza_file_not_found():
    """Verifica que un archivo adjunto inexistente lance FileNotFoundError."""
    sender = WhatsAppSender()
    archivo_falso = RAIZ / "data" / "no_existe_archivo_12345.png"
    with pytest.raises(FileNotFoundError):
        sender._adjuntar_archivo(MagicMock(), archivo_falso)


def test_double_check_header_mismatch_lanza_error():
    """Verifica que el Active Header Check aborte si el chat activo no coincide con el destinatario."""
    sender = WhatsAppSender()
    mock_page = MagicMock()

    # Simular que el buscador funciona (selector real, medido contra el DOM)
    mock_search = MagicMock()
    mock_search.count.return_value = 1
    mock_search.first = mock_search

    mock_cell = MagicMock()
    mock_cell.count.return_value = 1
    mock_cell.first = mock_cell

    # Simular que en pantalla se abrió un chat con otro nombre
    mock_header = MagicMock()
    mock_header.count.return_value = 1
    mock_header.first = mock_header
    mock_header.inner_text.return_value = "Chat Familiar Personal"

    def locator_mock(selector: str):
        if selector == 'input[role="textbox"][data-tab="3"]':
            return mock_search
        if "Grupo Inteligencia | Dólar & FX" in selector:
            return mock_cell
        if selector == '[data-testid="conversation-info-header"]':
            return mock_header
        m = MagicMock()
        m.count.return_value = 0
        m.first = m
        return m

    mock_page.locator.side_effect = locator_mock

    with pytest.raises(DestinatarioInvalidoError, match="FALLO DE SEGURIDAD"):
        sender._buscar_y_abrir_chat(mock_page, "Grupo Inteligencia | Dólar & FX")



# ---------------------------------------------------------------------------
# Selectores y guardas verificados contra el DOM real de WhatsApp Web (2026-09)
# ---------------------------------------------------------------------------

def test_el_buscador_apunta_al_input_real_y_no_al_contenteditable():
    """El buscador es un <input>, no un div contenteditable: los viejos daban 0."""
    from whatsapp_sender import SELECTORES_BUSCADOR
    assert 'input[role="textbox"][data-tab="3"]' in SELECTORES_BUSCADOR


def test_autenticado_no_se_conforma_con_un_header_con_imagen():
    """'header img' y el nav aparecen antes de que cargue la lista de chats."""
    from whatsapp_sender import SELECTORES_AUTENTICADO
    assert "header img" not in SELECTORES_AUTENTICADO
    assert 'div[role="navigation"]' not in SELECTORES_AUTENTICADO
    assert 'div[id="pane-side"]' in SELECTORES_AUTENTICADO


def test_el_nombre_del_grupo_padre_no_valida_contra_un_canal_tematico():
    """'Grupo Inteligencia' es prefijo de los otros seis: la comparación debe ser exacta."""
    sender = WhatsAppSender()
    assert not sender._header_coincide("Grupo Inteligencia", "Grupo Inteligencia | Dólar & FX")
    assert sender._header_coincide("Grupo Inteligencia", "Grupo Inteligencia")
    assert sender._header_coincide(
        "Grupo Inteligencia | Dólar & FX",
        "Grupo Inteligencia | Dólar & FX\nGrupo · 214 miembros",
    )


def test_un_pdf_exige_el_menu_de_documentos():
    """El único input disponible acepta image/*: un PDF por ahí no llega."""
    from whatsapp_sender import _requiere_menu_documento
    assert _requiere_menu_documento(Path("informe.pdf")) is True
    assert _requiere_menu_documento(Path("story.png")) is False
    assert _requiere_menu_documento(Path("grafico.JPG")) is False
    assert _requiere_menu_documento(Path("cierre.txt")) is True


def test_el_envio_falla_si_el_mensaje_no_aparece_en_la_conversacion():
    """Confirmar el envío exige ver la burbuja nueva, no solo haber hecho clic.

    El bucle anterior esperaba a que dos `data-testid` inexistentes valieran 0,
    así que rompía en la primera vuelta y devolvía "enviado" sin comprobar nada.
    """
    from whatsapp_sender import EnvioMensajeError

    sender = WhatsAppSender()
    mock_page = MagicMock()
    fila = MagicMock()
    fila.count.return_value = 7          # mismas filas antes y después: nada salió
    boton = MagicMock()
    boton.count.return_value = 1
    boton.first = boton

    def locator_mock(selector: str):
        if 'role="row"' in selector:
            return fila
        return boton

    mock_page.locator.side_effect = locator_mock
    sender.min_jitter_ms = sender.max_jitter_ms = 1

    mock_page.evaluate.return_value = "otra cosa distinta"
    with pytest.raises(EnvioMensajeError, match="no apareció"):
        sender._clic_enviar_y_confirmar(
            mock_page, mensajes_antes=7, testigo=WhatsAppSender._testigo("PRUEBA DE AUDITORIA"), timeout_s=1.0
        )


def test_sin_testigo_el_envio_se_confirma_con_una_burbuja_nueva():
    """Camino de respaldo: un adjunto sin pie de foto no deja texto que buscar,
    así que ahí el conteo de filas sigue siendo el único indicio disponible."""
    sender = WhatsAppSender()
    mock_page = MagicMock()
    fila = MagicMock()
    fila.count.return_value = 8          # una fila más que antes
    boton = MagicMock()
    boton.count.return_value = 1
    boton.first = boton

    def locator_mock(selector: str):
        if 'role="row"' in selector:
            return fila
        return boton

    mock_page.locator.side_effect = locator_mock
    sender.min_jitter_ms = sender.max_jitter_ms = 1

    sender._clic_enviar_y_confirmar(mock_page, mensajes_antes=7, testigo="", timeout_s=2.0)


def test_el_testigo_confirma_el_envio_aunque_el_conteo_de_filas_no_cambie():
    """WhatsApp virtualiza la lista: al entrar un mensaje puede descartar otro
    arriba y el conteo queda igual. El testigo real es ver el texto enviado."""
    sender = WhatsAppSender()
    mock_page = MagicMock()
    fila = MagicMock()
    fila.count.return_value = 7          # mismas filas: la virtualizacion las recicla
    boton = MagicMock()
    boton.count.return_value = 1
    boton.first = boton
    mock_page.locator.side_effect = lambda sel: fila if 'role="row"' in sel else boton
    mock_page.evaluate.return_value = "...PRUEBA DE AUDITORIA GI... 18:55"
    sender.min_jitter_ms = sender.max_jitter_ms = 1

    sender._clic_enviar_y_confirmar(
        mock_page,
        mensajes_antes=7,
        testigo=WhatsAppSender._testigo("*PRUEBA DE AUDITORIA GI*"),
        timeout_s=2.0,
    )


def test_el_testigo_ignora_negritas_emojis_y_separadores():
    """WhatsApp renderiza los emoji como <img>: `innerText` los devuelve como un
    espacio, y *negrita* pierde los asteriscos. Un testigo que los conserve nunca
    coincide con lo que se ve en pantalla."""
    assert WhatsAppSender._testigo("*PRUEBA DE AUDITORIA GI*" + chr(10) + "segunda") == "prueba de auditoria gi"
    assert WhatsAppSender._testigo("") == ""


def test_el_testigo_coincide_con_el_texto_ya_renderizado_por_whatsapp():
    """Caso real medido: se envió con emoji y la burbuja lo devuelve sin él."""
    enviado = "📊 *VERIFICACION FINAL GI* · segunda prueba" + chr(10) + "Si esta imagen llego"
    renderizado = " VERIFICACION FINAL GI · segunda prueba |  | Si esta imagen llego con su pie"
    testigo = WhatsAppSender._testigo(enviado)
    assert testigo
    assert testigo in WhatsAppSender._normalizar(renderizado)


def test_con_adjunto_nunca_se_cae_a_enter():
    """Con el editor de medios abierto, Enter envía el pie como texto suelto y
    descarta la imagen. Si no está el botón del editor hay que abortar."""
    from whatsapp_sender import EnvioMensajeError

    sender = WhatsAppSender()
    vacio = MagicMock()
    vacio.count.return_value = 0
    vacio.first = vacio
    mock_page = MagicMock()
    mock_page.locator.return_value = vacio
    sender.min_jitter_ms = sender.max_jitter_ms = 1

    with pytest.raises(EnvioMensajeError, match="botón de enviar del editor"):
        sender._clic_enviar_y_confirmar(
            mock_page, mensajes_antes=7, testigo="algo", con_adjunto=True, timeout_s=1.0
        )
    mock_page.keyboard.press.assert_not_called()


def test_con_adjunto_la_confirmacion_exige_media_y_no_solo_el_texto_del_pie():
    """El fallo real del 2026-09-01: llegó el pie como mensaje de texto y la
    verificación lo dio por bueno porque encontró el testigo."""
    from whatsapp_sender import EnvioMensajeError

    sender = WhatsAppSender()
    boton = MagicMock()
    boton.count.return_value = 1
    boton.first = boton
    boton.nth.return_value = boton
    boton.evaluate.return_value = False        # el boton NO esta en el footer
    mock_page = MagicMock()
    mock_page.locator.return_value = boton
    mock_page.evaluate.return_value = False    # no hay media en las ultimas burbujas
    sender.min_jitter_ms = sender.max_jitter_ms = 1

    with pytest.raises(EnvioMensajeError, match="sin la imagen"):
        sender._clic_enviar_y_confirmar(
            mock_page, mensajes_antes=7, testigo="algo", con_adjunto=True, timeout_s=1.0
        )


def test_toda_imagen_pasa_por_el_menu_adjuntar_y_no_por_el_input_suelto():
    """El `input[type=file]` siempre presente es el CREADOR DE STICKERS.

    Un PNG enviado por ahí llega como sticker, sin pie de foto (medido el
    2026-09-01: la lista de chats mostró "Sticker"). La ruta correcta para una
    foto es Adjuntar > Fotos y videos, igual que para un documento.
    """
    from whatsapp_sender import _opcion_menu_adjuntar
    assert _opcion_menu_adjuntar(Path("story.png")) == "Fotos y videos"
    assert _opcion_menu_adjuntar(Path("grafico.JPG")) == "Fotos y videos"
    assert _opcion_menu_adjuntar(Path("informe.pdf")) == "Documento"
    assert _opcion_menu_adjuntar(Path("cierre.txt")) == "Documento"


def test_el_selector_del_pie_de_foto_es_el_del_editor_de_medios():
    from whatsapp_sender import SELECTORES_CAPTION
    assert '[data-testid="media-caption-input-container"]' in SELECTORES_CAPTION


def test_el_texto_limpia_cualquier_borrador_previo_del_composer():
    """Un borrador olvidado de una corrida anterior se enviaría pegado al mensaje."""
    sender = WhatsAppSender()
    caja = MagicMock()
    caja.count.return_value = 1
    caja.first = caja
    mock_page = MagicMock()
    mock_page.locator.return_value = caja
    sender.min_jitter_ms = sender.max_jitter_ms = 1

    sender._insertar_texto(mock_page, "hola")

    teclas = [c.args[0] for c in mock_page.keyboard.press.call_args_list]
    assert "Control+A" in teclas
    assert "Backspace" in teclas


# ---------------------------------------------------------------------------
# Frenos anti-baneo: el sistema no puede comportarse como un bot
# ---------------------------------------------------------------------------

def test_el_cupo_diario_de_envios_se_respeta(tmp_path, monkeypatch):
    """Pasado el cupo del día, el envío se rechaza en vez de seguir insistiendo."""
    import whatsapp_sender as ws

    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", tmp_path / "envios.json")
    sender = WhatsAppSender()
    sender.max_envios_dia = 3
    sender.segundos_entre_envios = 0

    for _ in range(3):
        sender._registrar_envio()

    with pytest.raises(ws.LimiteEnviosError, match="cupo"):
        sender._esperar_turno()


def test_el_cupo_se_reinicia_al_cambiar_el_dia(tmp_path, monkeypatch):
    import json as _json
    import whatsapp_sender as ws

    ruta = tmp_path / "envios.json"
    ruta.write_text(_json.dumps({"fecha": "2020-01-01", "enviados": 99, "ultimo_ts": 0}), encoding="utf-8")
    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", ruta)

    sender = WhatsAppSender()
    sender.max_envios_dia = 3
    sender.segundos_entre_envios = 0
    sender._esperar_turno()          # no debe levantar: es otro día


def test_entre_dos_envios_se_espera_el_minimo(tmp_path, monkeypatch):
    """Dos envíos seguidos sin pausa son el patrón que delata a un bot."""
    import whatsapp_sender as ws

    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", tmp_path / "envios.json")
    dormido = []
    monkeypatch.setattr(ws.time, "sleep", lambda s: dormido.append(s))

    sender = WhatsAppSender()
    sender.max_envios_dia = 50
    sender.segundos_entre_envios = 45

    sender._registrar_envio()
    sender._esperar_turno()

    assert dormido, "no esperó nada entre dos envíos consecutivos"
    assert 0 < sum(dormido) <= 45


def test_el_estado_de_envios_esta_en_gitignore():
    gitignore = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert ".whatsapp_envios.json" in gitignore


def test_la_confirmacion_del_adjunto_mira_la_ultima_burbuja_y_no_las_anteriores():
    """Mirar 'las ultimas 3 filas' daba por bueno un PDF que no salió, porque
    veía las fotos de envíos previos. El testigo es la burbuja nueva."""
    from whatsapp_sender import EnvioMensajeError

    sender = WhatsAppSender()
    boton = MagicMock()
    boton.count.return_value = 1
    boton.first = boton
    boton.nth.return_value = boton
    boton.evaluate.return_value = False
    mock_page = MagicMock()
    mock_page.locator.return_value = boton
    # La ultima burbuja NO es el adjunto: es un mensaje viejo cualquiera.
    mock_page.evaluate.return_value = {"texto": "un mensaje anterior", "media": False}
    sender.min_jitter_ms = sender.max_jitter_ms = 1

    with pytest.raises(EnvioMensajeError, match="sin la imagen"):
        sender._clic_enviar_y_confirmar(
            mock_page,
            mensajes_antes=7,
            testigo=WhatsAppSender._testigo("PRUEBA PDF de auditoria"),
            con_adjunto=True,
            timeout_s=1.0,
        )


def test_el_adjunto_se_confirma_cuando_la_ultima_burbuja_lo_trae_con_su_pie():
    sender = WhatsAppSender()
    boton = MagicMock()
    boton.count.return_value = 1
    boton.first = boton
    boton.nth.return_value = boton
    boton.evaluate.return_value = False
    mock_page = MagicMock()
    mock_page.locator.return_value = boton
    # `entregado` es el tic: sin el, la burbuja solo esta PINTADA y la subida
    # puede fallar despues. Es el hueco por el que un PDF de 2 MB se reporto
    # entregado el 2026-09-04 sin llegar al canal.
    mock_page.evaluate.return_value = {
        "texto": "PDF | informe.pdf | 11 paginas | PRUEBA PDF de auditoria",
        "media": True,
        "etiquetas": ["Tu  Nombre del documento: informe.pdf  17:38 Enviado  "],
    }
    sender.min_jitter_ms = sender.max_jitter_ms = 1

    sender._clic_enviar_y_confirmar(
        mock_page,
        mensajes_antes=7,
        testigo=WhatsAppSender._testigo("PRUEBA PDF de auditoria"),
        con_adjunto=True,
        timeout_s=2.0,
    )


def test_el_dry_run_y_las_validaciones_no_necesitan_playwright(monkeypatch):
    """Playwright es un extra opcional (`uv sync --extra stories`). Pedirlo para
    simular un envío deja la suite sin correr donde no está instalado, que es
    justo lo que le pasó a CI el 2026-09-01."""
    import builtins

    importar_real = builtins.__import__

    def sin_playwright(nombre, *args, **kwargs):
        if nombre.startswith("playwright"):
            raise ModuleNotFoundError("No module named 'playwright'")
        return importar_real(nombre, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", sin_playwright)
    sender = WhatsAppSender()

    resultado = sender.enviar(destinatario="forex", mensaje="prueba", dry_run=True)
    assert resultado["status"] == "simulado"

    with pytest.raises(ValueError):
        sender.enviar(destinatario="forex", mensaje="", adjunto=None)


def test_la_sesion_no_depende_del_directorio_desde_el_que_se_ejecute(tmp_path, monkeypatch):
    """`session_dir` viene relativo en el config. Sin anclarlo a la raíz del repo,
    ejecutar desde otro cwd apunta a una carpeta vacía y reporta "sesión expirada"
    con la sesión intacta — y un `--login` ahí vincularía OTRO perfil."""
    monkeypatch.chdir(tmp_path)
    sender = WhatsAppSender()
    assert sender.session_dir.resolve() == (RAIZ / ".whatsapp_session").resolve()


def test_el_login_no_da_por_vinculada_una_sesion_sin_comprobarla():
    """Presionar ENTER en la consola confirmaba la vinculación a ciegas. Si el QR
    no se llegó a escanear, `--login` reportaba éxito y el primer envío moría."""
    sender = WhatsAppSender()
    page_con_qr = MagicMock()

    def locator_qr(selector: str):
        m = MagicMock()
        m.count.return_value = 1 if "canvas" in selector else 0
        m.first = m
        return m

    page_con_qr.locator.side_effect = locator_qr
    assert sender._hay_qr_visible(page_con_qr) is True
    assert sender._esta_autenticado(page_con_qr) is False
    # Con QR en pantalla, la confirmación manual no puede valer como vinculación.
    assert sender._confirmacion_valida(page_con_qr) is False

    page_ok = MagicMock()

    def locator_ok(selector: str):
        m = MagicMock()
        m.count.return_value = 1 if "pane-side" in selector else 0
        m.first = m
        return m

    page_ok.locator.side_effect = locator_ok
    assert sender._confirmacion_valida(page_ok) is True


def test_sin_teclado_interactivo_no_se_simula_un_enter():
    """`readline()` sobre un stdin no interactivo devuelve "" al instante. Tomar
    eso por un ENTER hacía que el aviso se repitiera decenas de veces por segundo
    durante todo el --login (observado el 2026-09-02)."""
    import io

    from whatsapp_sender import _hubo_enter

    assert _hubo_enter(io.StringIO("")) is False          # EOF: no hay teclado
    assert _hubo_enter(io.StringIO("\n")) is True         # ENTER de verdad
    assert _hubo_enter(io.StringIO("listo\n")) is True


# ---------------------------------------------------------------------------
# Despacho por lote: varias piezas al mismo canal en una sola acción.
#
# Medido contra el DOM real el 2026-09-02: el selector de archivos acepta
# múltiples (`is_multiple() == True`), cada imagen conserva SU PROPIO pie
# (se escribió en la 1, se cambió a la 2, se volvió a la 1 y el pie seguía
# ahí) y el botón queda etiquetado "Enviar 2 seleccionados".
# ---------------------------------------------------------------------------


def test_un_lote_vacio_se_rechaza():
    from whatsapp_sender import LoteInvalidoError

    sender = WhatsAppSender()
    with pytest.raises(LoteInvalidoError, match="vacío"):
        sender.enviar_lote("macro", [], dry_run=True)


def test_un_lote_que_mezcla_imagen_y_pdf_se_rechaza(tmp_path):
    """El menú Adjuntar tiene una entrada por tipo: un lote mixto no cabe."""
    from whatsapp_sender import LoteInvalidoError, Pieza

    png = tmp_path / "a.png"
    png.write_bytes(b"x")
    pdf = tmp_path / "b.pdf"
    pdf.write_bytes(b"x")

    sender = WhatsAppSender()
    with pytest.raises(LoteInvalidoError, match="mismo tipo"):
        sender.enviar_lote(
            "macro",
            [Pieza(adjunto=png, mensaje="uno"), Pieza(adjunto=pdf, mensaje="dos")],
            dry_run=True,
        )


def test_un_lote_con_un_archivo_inexistente_se_rechaza(tmp_path):
    from whatsapp_sender import Pieza

    png = tmp_path / "a.png"
    png.write_bytes(b"x")

    sender = WhatsAppSender()
    with pytest.raises(FileNotFoundError):
        sender.enviar_lote(
            "macro",
            [Pieza(adjunto=png, mensaje="uno"), Pieza(adjunto=tmp_path / "no.png", mensaje="dos")],
            dry_run=True,
        )


def test_el_dry_run_del_lote_enumera_todas_las_piezas(tmp_path, capsys):
    from whatsapp_sender import Pieza

    piezas = []
    for i in range(3):
        p = tmp_path / f"{i}.png"
        p.write_bytes(b"x")
        piezas.append(Pieza(adjunto=p, mensaje=f"pie {i}"))

    sender = WhatsAppSender()
    res = sender.enviar_lote("macro", piezas, dry_run=True)

    assert res["status"] == "simulado"
    assert res["piezas"] == 3
    salida = capsys.readouterr().out
    for i in range(3):
        assert f"pie {i}" in salida


def test_el_lote_descuenta_del_cupo_una_vez_por_pieza(tmp_path, monkeypatch):
    """Un lote es UNA acción pero N mensajes entregados.

    Contar el lote como un solo envío relajaría el freno por la puerta de
    atrás: el cupo diario existe para limitar mensajes, no clics.
    """
    import whatsapp_sender as ws

    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", tmp_path / "envios.json")
    sender = WhatsAppSender()
    sender._registrar_envio(4)

    assert sender._leer_estado_envios()["enviados"] == 4


def test_un_lote_que_desborda_el_cupo_se_rechaza_antes_de_abrir_el_navegador(tmp_path, monkeypatch):
    import whatsapp_sender as ws

    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", tmp_path / "envios.json")
    sender = WhatsAppSender()
    sender.max_envios_dia = 5
    sender.segundos_entre_envios = 0
    sender._registrar_envio(3)

    with pytest.raises(ws.LimiteEnviosError, match="cupo"):
        sender._esperar_turno(piezas=4)      # 3 + 4 = 7 > 5


def test_el_lote_espera_la_cadencia_una_sola_vez(tmp_path, monkeypatch):
    """Cuatro piezas en un lote no son cuatro esperas de 45 s."""
    import whatsapp_sender as ws

    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", tmp_path / "envios.json")
    dormido = []
    monkeypatch.setattr(ws.time, "sleep", lambda s: dormido.append(s))

    sender = WhatsAppSender()
    sender.max_envios_dia = 50
    sender.segundos_entre_envios = 45

    sender._registrar_envio(1)
    sender._esperar_turno(piezas=4)

    assert len(dormido) == 1, f"esperó {len(dormido)} veces en vez de una"
    assert 0 < dormido[0] <= 45


def test_el_texto_va_antes_del_adjunto_y_no_al_reves():
    """El defecto que mutiló el mensaje del canal el 2026-09-03.

    El campo de pie del editor de medios tope en **1.024 caracteres**, y una
    línea que no cabe se rechaza ENTERA mientras el salto de línea que la sigue
    sí entra. El resultado no es un texto cortado al final: son renglones que
    desaparecen dejando su espacio en blanco, con las líneas cortas posteriores
    intactas porque todavía cabían. El canal recibió el contexto macro sin la
    línea del Imacec ni las dos de tasas, pero con el link del BCCh que iba en
    medio, y el despacho reportó éxito.

    Medido contra el DOM real ese día con un texto de 2.016 caracteres:
    adjuntando primero entraron 1.029; escribiendo primero en el cuadro de
    conversación, 2.042 (completo).

    Se verifica el ORDEN en el código y no el resultado, porque el resultado
    solo se ve contra WhatsApp Web. Es el mismo criterio del test de la reserva
    de cupo.
    """
    import inspect

    fuente = inspect.getsource(WhatsAppSender._adjuntar_archivo)
    pos_texto = fuente.index("_insertar_texto")
    pos_editor = fuente.index("_abrir_editor_de_medios(page, ruta_archivo, caption)\n        except")

    assert pos_texto < pos_editor, (
        "el editor de medios se abre antes de escribir el texto: ese es exactamente "
        "el orden que tope en 1.024 caracteres y mutila el mensaje"
    )
    # Y el adjunto de verdad vive en el otro metodo, no duplicado aca.
    assert "expect_file_chooser" not in fuente


def test_un_pie_incompleto_aborta_en_vez_de_enviarse_a_medias():
    """El guardia que faltaba. El anterior solo preguntaba si había ALGO escrito,
    y un mensaje al que le faltan renglones se lee como completo: nadie lo nota
    desde afuera, así que el defecto viaja al cliente sin dejar rastro."""
    from whatsapp_sender import EnvioMensajeError

    sender = WhatsAppSender()
    esperado = "linea uno\n" + "x" * 2000
    caja = MagicMock()
    caja.inner_text.return_value = "linea uno\n" + "x" * 900

    with pytest.raises(EnvioMensajeError, match="incompleto"):
        sender._verificar_pie_completo(caja, esperado, Path("contexto_macro.png"))


def test_un_pie_completo_pasa_aunque_el_editor_cuente_distinto_los_saltos():
    """El contenteditable devolvió 2.042 caracteres para un texto de 2.016: los
    saltos de línea los cuenta a su manera. Comparar largos crudos daría un
    falso negativo, así que se compara la huella sin espacios."""
    sender = WhatsAppSender()
    esperado = "una linea\notra linea\ntercera"
    caja = MagicMock()
    caja.inner_text.return_value = "una linea\n\notra linea\n\n\ntercera\n"

    sender._verificar_pie_completo(caja, esperado, Path("story.png"))


def test_un_pie_vacio_sigue_abortando():
    """El texto que termina en el composer en vez del editor: enviar mandaría el
    párrafo suelto y tiraría la imagen."""
    from whatsapp_sender import EnvioMensajeError

    sender = WhatsAppSender()
    caja = MagicMock()
    caja.inner_text.return_value = "   "

    with pytest.raises(EnvioMensajeError, match="no quedó en el editor"):
        sender._verificar_pie_completo(caja, "un pie cualquiera", Path("story.png"))


def test_el_lote_manda_una_pieza_por_accion_y_reserva_cupo_en_cada_una():
    """La decisión del director del 2026-09-03, que revierte el despacho por lote.

    Mandar todas las piezas en una acción es incompatible con el pie completo:
    escribir en el cuadro antes de adjuntar solo llena el pie de UNA imagen, la
    que el editor abre seleccionada. Las demás vuelven al editor y se cortan.

    Se paga con una espera de cadencia por pieza. Lo que se compra es que el
    mensaje llegue entero.
    """
    import inspect

    fuente = inspect.getsource(WhatsAppSender.enviar_lote)
    pos_bucle = fuente.index("for indice, pieza in enumerate(piezas")
    pos_reserva = fuente.index("_reservar_turno")
    pos_adjuntar = fuente.index("_adjuntar_archivo")

    assert pos_bucle < pos_reserva, (
        "la reserva quedó fuera del bucle: la cadencia no se aplicaría entre piezas"
    )
    assert pos_reserva < pos_adjuntar, "el cupo se anota después de intentar"
    assert "_adjuntar_lote" not in fuente, (
        "sigue usando el adjunto por lote, que escribe los pies dentro del editor"
    )


def test_el_adjunto_por_lote_ya_no_existe():
    """Se eliminó en vez de dejarse como referencia: era el orden equivocado,
    escrito y a mano para el próximo que pasara por ahí."""
    for muerto in ("_adjuntar_lote", "_escribir_pies_del_lote", "_miniaturas_del_lote"):
        assert not hasattr(WhatsAppSender, muerto), (
            f"{muerto} volvió: adjunta antes de escribir el pie"
        )


def test_el_cli_expone_el_lote_y_lo_hace_excluyente_con_el_adjunto_suelto():
    """`--lote` manda una carpeta entera; `--adjunto` manda un archivo.

    Aceptar ambos dejaría sin definir qué se envía y en qué orden.
    """
    import sys as _sys
    _sys.path.insert(0, str(RAIZ / "scripts"))
    from enviar_whatsapp import construir_parser

    parser = construir_parser()
    args = parser.parse_args(["--grupo", "forex", "--lote", "data/carrusel/x/02_forex_divisas"])
    assert args.lote == Path("data/carrusel/x/02_forex_divisas")

    with pytest.raises(SystemExit):
        parser.parse_args(["--grupo", "forex", "--lote", "x", "--adjunto", "y.png"])


# ─────────────────────────────────────────────────────────────────────────────
# El cupo se RESERVA antes de enviar, no se anota despues
# ─────────────────────────────────────────────────────────────────────────────

def test_reservar_turno_descuenta_el_cupo_antes_del_envio(tmp_path, monkeypatch):
    """El freno tiene que quedar aplicado ANTES de tocar el boton de enviar.

    El orden era: esperar turno -> enviar -> anotar. Si el proceso muere, lo
    interrumpen con Ctrl+C, o `_clic_enviar_y_confirmar` falla DESPUES de que
    WhatsApp acepto el mensaje (una verificacion que expira con la subida
    lenta), las piezas salieron y el contador no registro nada.

    Sobrecontar cuesta una pieza de cupo. Subcontar cuesta la cuenta.
    """
    import whatsapp_sender as ws

    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", tmp_path / "envios.json")
    monkeypatch.setattr(ws.time, "sleep", lambda s: None)

    sender = WhatsAppSender()
    sender.max_envios_dia = 50
    sender.segundos_entre_envios = 45

    sender._reservar_turno(piezas=3)

    assert sender._leer_estado_envios()["enviados"] == 3


def test_reservar_turno_sella_la_hora_para_que_un_fallo_no_permita_rafaga(tmp_path, monkeypatch):
    """`ultimo_ts` vivia solo en `_registrar_envio`, que corria despues del envio.

    Un fallo lo dejaba sin sellar, asi que la llamada siguiente encontraba la
    cadencia ya cumplida y disparaba de inmediato. Rafaga es exactamente el
    patron que hace que marquen una cuenta.
    """
    import whatsapp_sender as ws

    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", tmp_path / "envios.json")
    monkeypatch.setattr(ws.time, "sleep", lambda s: None)

    sender = WhatsAppSender()
    sender.max_envios_dia = 50
    sender.segundos_entre_envios = 45

    antes = sender._leer_estado_envios().get("ultimo_ts", 0.0)
    sender._reservar_turno(piezas=1)
    assert sender._leer_estado_envios()["ultimo_ts"] > antes


def test_reservar_turno_rechaza_el_desborde_sin_descontar(tmp_path, monkeypatch):
    """La reserva no puede consumir cupo cuando el lote ni siquiera cabe."""
    import whatsapp_sender as ws

    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", tmp_path / "envios.json")
    sender = WhatsAppSender()
    sender.max_envios_dia = 5
    sender.segundos_entre_envios = 0
    sender._registrar_envio(3)

    with pytest.raises(ws.LimiteEnviosError, match="cupo"):
        sender._reservar_turno(piezas=4)

    assert sender._leer_estado_envios()["enviados"] == 3


@pytest.mark.parametrize("metodo", ["enviar", "enviar_lote"])
def test_las_dos_rutas_reservan_antes_de_pulsar_enviar(metodo):
    """El contrato de orden, leido del codigo de cada ruta.

    Sin este test la regresion es invisible: mover `_registrar_envio` de vuelta
    despues del envio no rompe ninguna asercion de comportamiento, y el sintoma
    (cupo desbordado, rafaga) solo aparece cuando algo ya falló en produccion.
    """
    import inspect

    fuente = inspect.getsource(getattr(WhatsAppSender, metodo))

    assert "_reservar_turno" in fuente, f"{metodo} no reserva el turno"
    assert "_registrar_envio" not in fuente, (
        f"{metodo} anota el envio por su cuenta: el descuento tiene que venir de "
        "la reserva, o vuelve a quedar despues del envio"
    )
    assert fuente.index("_reservar_turno") < fuente.index("_clic_enviar_y_confirmar"), (
        f"{metodo} reserva despues de pulsar enviar"
    )


def test_la_previsualizacion_de_enlace_se_cierra_antes_de_abrir_adjuntar():
    """El segundo defecto del orden nuevo, y mato el despacho de las 12:26.

    Casi todos los mensajes del proyecto llevan enlaces (Investing, BCCh, FRED).
    Al dejar el texto en el cuadro, WhatsApp despliega una tarjeta de
    previsualizacion que ocupa el area donde se abre el menu Adjuntar, y el clic
    en "Fotos y videos" espera 30 s a un elemento tapado.

    Se verifica el ORDEN: la tarjeta se cierra antes de tocar el boton Adjuntar.
    """
    import inspect

    fuente = inspect.getsource(WhatsAppSender._adjuntar_archivo)
    pos_cerrar = fuente.index("_cerrar_previsualizacion_enlace")
    pos_editor = fuente.index("_abrir_editor_de_medios(page, ruta_archivo, caption)\n        except")

    assert pos_cerrar < pos_editor, (
        "el menu Adjuntar se abre antes de cerrar la previsualizacion: la tarjeta "
        "tapa la opcion 'Fotos y videos' y el envio muere esperandola"
    )


def test_sin_previsualizacion_el_cierre_no_hace_nada_y_no_falla():
    """Un mensaje sin URLs no despliega tarjeta. El paso tiene que ser inocuo,
    no un requisito: la mayoria de las piezas de activo no llevan enlace."""
    sender = WhatsAppSender()
    vacio = MagicMock()
    vacio.count.return_value = 0
    page = MagicMock()
    page.locator.return_value = vacio

    assert sender._cerrar_previsualizacion_enlace(page) is False
    vacio.first.click.assert_not_called()


def test_si_la_tarjeta_no_se_puede_cerrar_el_envio_sigue():
    """Fail-open a proposito, y es la excepcion a la regla del proyecto: acá el
    guardia que importa es el del pie completo, que corre despues. Abortar por
    no poder cerrar una tarjeta que quiza no estorba dejaria la tanda detenida
    por un adorno."""
    sender = WhatsAppSender()
    tarjeta = MagicMock()
    tarjeta.count.return_value = 1
    tarjeta.first.click.side_effect = RuntimeError("no se pudo")
    page = MagicMock()
    page.locator.return_value = tarjeta

    assert sender._cerrar_previsualizacion_enlace(page) is False


def test_un_fallo_al_adjuntar_no_deja_el_texto_de_borrador_en_el_chat():
    """El riesgo que se materializo el 2026-09-03 y hubo que limpiar a mano.

    Con el texto escrito antes de adjuntar, cualquier fallo posterior lo deja de
    borrador VIVO en el chat del cliente: quedaron 1.451 caracteres del contexto
    macro en el cuadro de Metales & Energia, y un Enter de cualquiera los publica
    sin su imagen. Se descubrio porque el error dejo captura; sin ella, el texto
    seguiria ahi.
    """
    import inspect

    fuente = inspect.getsource(WhatsAppSender._adjuntar_archivo)
    assert "_descartar_borrador" in fuente, (
        "el camino de error no limpia el cuadro: el texto queda publicable"
    )
    pos_except = fuente.index("except Exception:")
    pos_descartar = fuente.index("_descartar_borrador")
    pos_raise = fuente.index("raise", pos_descartar)
    assert pos_except < pos_descartar < pos_raise, (
        "el descarte tiene que ir dentro del manejo de error y antes de re-lanzar"
    )


def test_descartar_el_borrador_nunca_lanza():
    """Se llama desde el camino de error: una excepcion aca taparia la causa real
    del fallo con una secundaria."""
    sender = WhatsAppSender()
    page = MagicMock()
    page.locator.side_effect = RuntimeError("la pagina se murio")

    sender._descartar_borrador(page)          # no debe lanzar


def test_sin_pie_no_hay_borrador_que_descartar():
    """Una pieza sin texto no escribe nada en el cuadro, asi que el camino corto
    va directo al editor y no necesita limpieza."""
    import inspect

    fuente = inspect.getsource(WhatsAppSender._adjuntar_archivo)
    pos_corto = fuente.index("if not caption.strip():")
    pos_insertar = fuente.index("_insertar_texto")
    assert pos_corto < pos_insertar, (
        "el atajo sin pie tiene que resolverse antes de tocar el cuadro del chat"
    )


def test_la_cabecera_se_lee_con_sus_emojis_y_no_sin_ellos():
    """El envio correcto que la verificacion aborto el 2026-09-03.

    `inner_text()` no devuelve los emoji: WhatsApp los dibuja como <img> y el
    caracter vive en su `alt`. El grupo padre se llamaba "...Comunidad de
    Traders 📈" y la cabecera devolvia el nombre SIN el emoji, asi que la
    verificacion no reconocio su propio destino y abortó.

    Se resolvio quitandole el emoji al grupo, que arregla el caso y no la causa:
    cualquier canal que gane uno vuelve a romper el envio.
    """
    import inspect

    fuente = inspect.getsource(WhatsAppSender._buscar_y_abrir_chat)
    assert "_texto_con_emojis" in fuente, (
        "la cabecera se sigue leyendo con inner_text, que come los emoji"
    )
    assert "header_locator.inner_text()" not in fuente


def test_el_lector_de_cabecera_sustituye_cada_imagen_por_su_alt():
    """El contrato del reemplazo: el emoji sale del atributo `alt` del <img>."""
    import inspect

    fuente = inspect.getsource(WhatsAppSender._texto_con_emojis)
    assert "getAttribute('alt')" in fuente
    assert "IMG" in fuente
    # Y los saltos de linea se preservan: `_header_coincide` compara contra la
    # PRIMERA linea, asi que sin ellos el nombre quedaria pegado al subtitulo.
    assert "BR" in fuente


def test_sin_evaluate_el_lector_cae_a_inner_text_y_no_revienta():
    """Degradar es aceptable; quedarse sin verificacion no. El fallback devuelve
    el texto sin emoji, que es lo que habia antes: peor, nunca menos estricto."""
    locator = MagicMock()
    locator.evaluate.side_effect = RuntimeError("sin evaluate")
    locator.inner_text.return_value = "Grupo Inteligencia | Metales & Energía"

    assert WhatsAppSender._texto_con_emojis(locator) == "Grupo Inteligencia | Metales & Energía"
    assert WhatsAppSender._texto_con_emojis(None) == ""


def test_un_nombre_con_emoji_calza_cuando_la_cabecera_lo_devuelve():
    """La consecuencia practica: con el emoji reconstruido, el destino calza."""
    sender = WhatsAppSender()
    nombre = "Grupo Inteligencia | Comunidad de Traders \U0001F4C8"

    assert sender._header_coincide(nombre, nombre + "\nSolo los administradores")
    # Y sin el emoji NO calza, que es lo que pasaba y por eso abortaba.
    assert not sender._header_coincide(nombre, "Grupo Inteligencia | Comunidad de Traders ")


def test_el_lector_de_cabecera_ignora_lo_invisible_y_los_svg():
    """`inner_text` descarta lo oculto y el texto de los SVG, y hace bien.

    Sin esos filtros el recorrido se traia el <title> de los iconos: medido el
    2026-09-03, una burbuja devolvia "tail-out" (el icono de la cola del globo)
    como su PRIMERA linea. La cabecera se compara justo contra la primera linea,
    asi que eso abortaria un envio legitimo por un adorno.
    """
    import inspect

    fuente = inspect.getsource(WhatsAppSender._texto_con_emojis)
    for filtro in ("SVG", "TITLE", "aria-hidden", "display === 'none'", "visibility === 'hidden'"):
        assert filtro in fuente, f"el recorrido no filtra {filtro}"


def test_el_destino_de_pruebas_existe_y_no_es_un_canal_de_clientes():
    """Durante todo el 2026-09-03 los diagnosticos contra el DOM improvisaron el
    destino en scripts sueltos, con el numero escrito a mano en cada uno."""
    config = WhatsAppConfig()

    destino = config.destino_de_pruebas
    assert destino, "no hay destino de pruebas configurado"

    nombres_de_canales = {g["nombre_oficial"] for g in config.grupos.values()}
    assert destino not in nombres_de_canales, (
        "el destino de pruebas es un canal de clientes: medir ahi publica"
    )


def test_el_banco_de_pruebas_no_entra_al_mapa_de_canales():
    """`grupos` es el mapa de canales de clientes y su contrato son siete. Un
    octavo ahi seria un destino de publicacion accidental esperando a que alguien
    resuelva un alias con un typo, que es el defecto que el sender ya arreglo
    para los alias no reconocidos."""
    config = WhatsAppConfig()

    assert len(config.grupos) == 7
    assert "banco_de_pruebas" not in config.grupos
    assert config.banco_de_pruebas, "el banco de pruebas no se cargo"

    # Y no se puede alcanzar resolviendo un alias.
    for intento in ("pruebas", "banco_de_pruebas", "test", "prueba"):
        assert config.resolver_nombre_oficial(intento) not in {
            g["nombre_oficial"] for g in config.grupos.values()
        }


def test_sin_destino_configurado_se_niega_en_vez_de_elegir_uno():
    """Fail-closed: caer a un canal de clientes por defecto es exactamente lo que
    no debe pasar cuando falta configuracion."""
    from whatsapp_sender import WhatsAppError

    config = WhatsAppConfig()
    config.banco_de_pruebas = {}

    with pytest.raises(WhatsAppError, match="destino de pruebas"):
        _ = config.destino_de_pruebas


# ─────────────────────────────────────────────────────────────────────────────
# El falso "enviado" del 2026-09-04
#
# Un PDF de 2 MB se reporto ENTREGADO y no llego al canal. `_adjunto_confirmado`
# con el testigo vacio devolvia True apenas la ultima burbuja tenia `media`, y
# `media` se decide con un regex sobre el texto (`/\bPDF\b/`), que da verdadero
# en cuanto WhatsApp pinta la burbuja **antes de terminar la subida**. Con un PNG
# de 500 KB la subida es instantanea y nunca se noto.
# ─────────────────────────────────────────────────────────────────────────────
def test_un_adjunto_sin_pie_no_se_confirma_solo_porque_haya_media():
    """Sin pie, el unico testigo posible es el archivo: hay que exigirlo."""
    sender = WhatsAppSender()
    mock_page = MagicMock()
    # Una burbuja de documento CUALQUIERA, que no es la que se acaba de mandar.
    mock_page.evaluate.return_value = {"texto": "otro_informe.pdf 1 MB PDF", "media": True}

    assert not sender._adjunto_confirmado(
        mock_page, testigo="", nombre_archivo="informe_cierre_semanal_20260904_GI.pdf"
    )


def test_un_adjunto_sin_pie_se_confirma_con_el_nombre_del_archivo():
    sender = WhatsAppSender()
    mock_page = MagicMock()
    mock_page.evaluate.return_value = {
        "texto": "informe_cierre_semanal_20260904_GI.pdf 2 MB PDF", "media": True,
        "etiquetas": ["Tu  Nombre del documento  20:08 Enviado  "],
    }

    assert sender._adjunto_confirmado(
        mock_page, testigo="", nombre_archivo="informe_cierre_semanal_20260904_GI.pdf"
    )


def test_la_burbuja_pintada_sin_terminar_la_subida_no_cuenta_como_entregada():
    """WhatsApp pinta la burbuja al instante y sube en segundo plano. El tic de
    enviado es lo unico que dice que el servidor la recibio."""
    sender = WhatsAppSender()
    mock_page = MagicMock()
    # "Pendiente" es el estado real del PDF que nunca salio al canal.
    mock_page.evaluate.return_value = {
        "texto": "informe.pdf 2 MB PDF", "media": True,
        "etiquetas": ["Tu  Nombre del documento  17:38 Pendiente  "],
    }

    assert not sender._adjunto_confirmado(
        mock_page, testigo="", nombre_archivo="informe.pdf"
    )


# ─────────────────────────────────────────────────────────────────────────────
# El falso NEGATIVO del 2026-09-04, que es el que de verdad duplica
#
# El PDF de 2 MB SI llego al canal a las 17:38, pero el sender lo dio por fallido
# a los 25 s de espera fija. El director no lo vio, lo mando a mano un minuto
# despues, y el canal quedo con dos copias. Un falso negativo induce el reenvio,
# asi que hace el mismo dano que un falso positivo.
# ─────────────────────────────────────────────────────────────────────────────
def test_la_espera_de_confirmacion_crece_con_el_tamano_del_archivo():
    from whatsapp_sender import espera_confirmacion_s

    chico = espera_confirmacion_s(0)                 # texto suelto
    png = espera_confirmacion_s(500 * 1024)          # una Story tipica
    pdf = espera_confirmacion_s(2 * 1024 * 1024)     # el informe semanal

    assert chico < png < pdf, "la espera tiene que escalar con el peso"
    assert pdf >= 60, "2 MB tardaron mas de 25 s en subir el 2026-09-04"


def test_la_espera_tiene_techo_para_no_colgar_el_despacho():
    from whatsapp_sender import espera_confirmacion_s

    assert espera_confirmacion_s(500 * 1024 * 1024) <= 180


# ─────────────────────────────────────────────────────────────────────────────
# El estado de entrega vive en el aria-label, no en un data-icon
#
# Medido contra el DOM real el 2026-09-04: una burbuja de documento ENTREGADA
# trae `iconos: ['document-PDF-icon']` y ningun `msg-check`. El estado esta en el
# aria-label ("... 20:08 Enviado"). Buscar el tic como data-icon deja al sender
# abortando envios que si llegaron, y un falso negativo induce el reenvio manual:
# es lo que dejo dos PDF en el canal de clientes ese mismo dia.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "aria, entregado",
    [
        ("Tu  Nombre del documento: x.pdf. 6 paginas 20:08 Enviado  ", True),
        ("Tu  Nombre del documento: x.pdf. 2 MB  19:48 Entregado  ", True),
        ("Tu  mensaje  10:16 Leido  ", True),
        # El caso real del PDF que NUNCA salio al canal de clientes.
        ("Tu  Nombre del documento: x.pdf. 6 paginas 17:38 Pendiente  ", False),
        ("Tu  Nombre del documento: x.pdf.", False),
        ("", False),
    ],
)
def test_el_estado_de_entrega_se_lee_del_aria_label(aria, entregado):
    from whatsapp_sender import burbuja_entregada

    assert burbuja_entregada([aria]) is entregado


def test_pendiente_gana_sobre_cualquier_otra_marca():
    """Si una etiqueta dice Pendiente, la burbuja no salio, sin importar el resto."""
    from whatsapp_sender import burbuja_entregada

    assert burbuja_entregada(["algo Enviado", "estado: Pendiente"]) is False


def test_el_cli_puede_alcanzar_el_banco_de_pruebas():
    """Un canal de pruebas al que no se puede enviar no sirve de nada.

    Hasta el 2026-09-06 `destino_de_pruebas` existia, estaba testeado y **ningun
    camino del CLI lo llamaba**: `--grupo banco_de_pruebas` cae en el paso 3 de
    `resolver_nombre_oficial` (devolver el nombre tal cual) y WhatsApp Web no
    encuentra ningun chat con ese literal. El efecto real era que el mecanismo de
    entrega se verificaba contra canales de clientes, o no se verificaba.

    Lo resuelve el flag `--pruebas`, que **no toma un destino**: lo resuelve del
    config. Esa es la parte que importa, y por eso se testea la firma y no solo el
    resultado. Un flag que aceptara un destino podria apuntar a un canal de
    clientes con un typo, que es justo lo que los dos tests de arriba impiden.
    """
    import runpy

    ruta = Path(__file__).resolve().parent.parent / "scripts" / "enviar_whatsapp.py"
    modulo = runpy.run_path(str(ruta), run_name="_no_es_main_")
    parser = modulo["construir_parser"]()

    args = parser.parse_args(["--pruebas", "-m", "x"])
    assert args.pruebas is True
    assert args.destinatario is None, "--pruebas no puede tomar un destino"

    # El destino sale del config, no del argumento, y no es un canal de clientes.
    config = WhatsAppConfig()
    assert config.destino_de_pruebas not in {
        g["nombre_oficial"] for g in config.grupos.values()
    }
