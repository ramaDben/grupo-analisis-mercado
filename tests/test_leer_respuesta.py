"""El lector del banco de pruebas: solo lectura, sin excepciones.

El flujo de aprobacion paso a ser "la pieza va al banco de pruebas y el director
responde ahi" (decision del 2026-09-04). El sender solo sabia escribir, asi que
la mitad del lazo no se podia cerrar.

Un lector que ademas pueda publicar no es un lector, y en este repo un envio no
aprobado es el peor error posible: por eso el contrato es de codigo.
"""
from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LECTOR = RAIZ / "scripts" / "leer_respuesta.py"


def test_el_lector_no_puede_enviar_nada():
    fuente = LECTOR.read_text(encoding="utf-8")
    prohibidos = (
        "_insertar_texto",
        "_escribir_multilinea",
        "_adjuntar_archivo",
        "_abrir_editor_de_medios",
        "_boton_enviar",
        "enviar(",
        "enviar_lote",
        "set_input_files",
    )
    for p in prohibidos:
        assert p not in fuente, f"el lector toca el envio: {p}"


def test_el_lector_no_escribe_en_el_cuadro_de_conversacion():
    fuente = LECTOR.read_text(encoding="utf-8")
    for p in (".type(", ".fill(", "press(\"Enter\")", "insert_text"):
        assert p not in fuente, f"el lector escribe en la pagina: {p}"


def test_el_lector_reutiliza_los_selectores_medidos_del_sender():
    """Reimplementarlos seria la segunda copia que despues queda atras."""
    fuente = LECTOR.read_text(encoding="utf-8")
    assert "_buscar_y_abrir_chat" in fuente
    assert "_crear_contexto" in fuente
    assert "resolver_nombre_oficial" in fuente


def test_el_lector_distingue_quien_escribio_cada_burbuja():
    """Sin eso, la aprobacion del director no se distingue de nuestro propio envio."""
    fuente = LECTOR.read_text(encoding="utf-8")
    assert "message-in" in fuente and "message-out" in fuente


def test_el_lector_recupera_los_emoji():
    """`innerText` no devuelve emoji: se rinden como <img> con el caracter en alt.

    Un "ok" con visto bueno emoji se leeria vacio, que es peor que no leer.
    """
    fuente = LECTOR.read_text(encoding="utf-8")
    assert "alt" in fuente and "IMG" in fuente


def test_el_lector_cierra_el_contexto_siempre():
    """El perfil de Chromium admite un proceso: dejarlo abierto bloquea el envio."""
    fuente = LECTOR.read_text(encoding="utf-8")
    assert "finally:" in fuente and "contexto.close()" in fuente


def test_el_lector_ignora_los_iconos_de_estado():
    """Los iconos traen su nombre de clase como texto y se cuelan a la burbuja.

    Medido: la lectura terminaba en `wds-ic-read`, que es el visto. Es el mismo
    defecto que hacia que el sender leyera `tail-out` como primera linea.
    """
    fuente = LECTOR.read_text(encoding="utf-8")
    assert "data-icon" in fuente
