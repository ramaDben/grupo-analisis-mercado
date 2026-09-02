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
        ("macro", "Grupo Inteligencia | Comunidad de Traders 📈"),
        ("apertura", "Grupo Inteligencia | Comunidad de Traders 📈"),
        ("01_macro_y_apertura", "Grupo Inteligencia | Comunidad de Traders 📈"),
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
    mock_page.evaluate.return_value = {
        "texto": "PDF | informe.pdf | 11 paginas | PRUEBA PDF de auditoria",
        "media": True,
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


def test_el_pie_de_cada_pieza_se_escribe_en_su_propia_miniatura(tmp_path):
    """Cada imagen conserva su pie: hay que seleccionar su miniatura antes.

    Sin el clic en la miniatura, los cuatro pies se apilarían en la primera
    imagen y las otras tres saldrían mudas.
    """
    from whatsapp_sender import Pieza

    piezas = []
    for i in range(3):
        p = tmp_path / f"{i}.png"
        p.write_bytes(b"x")
        piezas.append(Pieza(adjunto=p, mensaje=f"pie {i}"))

    sender = WhatsAppSender()
    orden: list[str] = []

    mini = MagicMock()
    mini.click.side_effect = lambda *a, **k: orden.append("miniatura")
    mini.bounding_box.return_value = {"x": 0, "y": 900, "width": 52, "height": 52}

    caja = MagicMock()
    caja.inner_text.return_value = "algo"
    caja.click.side_effect = lambda *a, **k: orden.append("caja")

    page = MagicMock()
    page.locator.return_value = MagicMock(count=MagicMock(return_value=3), nth=lambda i: mini)
    sender._primer_locator = lambda p, s: caja           # type: ignore[assignment]
    sender._escribir_multilinea = staticmethod(          # type: ignore[assignment]
        lambda p, t: orden.append(f"texto:{t}")
    )
    sender._pausa_humana = lambda factor=1.0: None       # type: ignore[assignment]

    sender._escribir_pies_del_lote(page, piezas)

    textos = [o for o in orden if o.startswith("texto:")]
    assert textos == ["texto:pie 0", "texto:pie 1", "texto:pie 2"]
    # Antes de cada pie, su miniatura
    assert orden.count("miniatura") >= 2, "no cambió de miniatura entre pies"


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
