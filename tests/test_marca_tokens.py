"""La paleta vive en marca.css y ninguna plantilla escribe un hex a mano."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import marca_tokens  # noqa: E402

MARCA_CSS = _REPO_ROOT / "templates" / "stories" / "marca.css"


def test_marca_css_declara_un_color_por_activo():
    css = MARCA_CSS.read_text(encoding="utf-8")

    for token in (
        "--activo-oro",
        "--activo-wti",
        "--activo-us100",
        "--activo-usdclp",
        "--activo-bitcoin",
    ):
        assert token in css, f"falta {token} en marca.css"


def test_marca_css_cascadea_el_rol_activo_por_clase():
    css = MARCA_CSS.read_text(encoding="utf-8")

    assert "body.activo-oro" in css
    assert "--activo: var(--activo-oro)" in css


def test_todo_color_de_activo_declarado_tiene_rol_en_el_mapa():
    """Sin esto, una plantilla que hardcodee un color de activo recibiría
    "hex huérfano" en vez de la sugerencia del token correcto.

    La lista NO se escribe acá: se lee de `marca.css`. La versión anterior
    enumeraba cinco hex a mano y sobrevivió al cambio de paleta afirmando que
    `#C9743A` tenía rol cuando ya nadie lo declaraba. Un test que repite el dato
    que debería estar verificando solo comprueba que dos copias coinciden.
    """
    css = MARCA_CSS.read_text(encoding="utf-8")
    mapa = marca_tokens.cargar_mapa()

    declarados = {
        hex_.upper(): rol
        for rol, hex_ in marca_tokens.PATRON_DECLARACION.findall(css)
        if rol.startswith("activo-")
    }
    assert declarados, "marca.css no declara ningún --activo-* con hex propio"

    for hex_activo, rol in declarados.items():
        assert mapa.get(hex_activo) is not None, f"{hex_activo} ({rol}) sin rol asignado"


def test_ninguna_plantilla_de_produccion_hardcodea_color():
    """Se mira el CSS propio de cada plantilla, no la paleta que trae embebida.

    El bloque embebido es una copia literal de `marca.css`, o sea el único lugar
    donde escribir un hex es correcto. Contarlo ahí reportaba la paleta entera
    como veinte colores hardcodeados de `alerta.html`.
    """
    for plantilla in sorted((_REPO_ROOT / "templates" / "stories").glob("*.html")):
        html = marca_tokens.quitar_css_embebido(
            plantilla.read_text(encoding="utf-8")
        )
        _, _, huerfanos = marca_tokens._tokenizar(html)
        assert not huerfanos, f"{plantilla.name} trae hex sin token: {huerfanos}"


def test_el_gate_cubre_las_hojas_propias():
    hojas = [p.name for p in marca_tokens._hojas()]

    assert "piel.css" in hojas, "el gate no está escaneando piel.css"
    # marca.css es la fuente de los hex: escanearla la reportaría entera como
    # infracción.
    assert "marca.css" not in hojas


def test_ninguna_hoja_propia_hardcodea_color():
    for hoja in marca_tokens._hojas():
        css = hoja.read_text(encoding="utf-8")
        _, n, huerfanos = marca_tokens._tokenizar(css)
        assert not n and not huerfanos, f"{hoja.name} trae color a mano: {huerfanos or n}"


def _snapshot(css_propio: str) -> str:
    """HTML minimo con la estructura real: paleta embebida + <style> propio."""
    return (
        "<style>\n"
        f"  {marca_tokens.MARCADOR_MARCA}\n"
        "  :root { --acento: #50C0A8; --fondo: #000000; }\n"
        "</style>\n"
        "<style>\n"
        f"{css_propio}\n"
        "</style>\n"
    )


def test_la_paleta_embebida_no_cuenta_como_color_hardcodeado():
    """Es el falso positivo que tuvo el gate roto durante semanas: reportaba los
    veinte hex de `marca.css` como si `alerta.html` los hubiera escrito."""
    limpio = _snapshot("  .chip { color: var(--acento); }")
    _, _, huerfanos = marca_tokens._tokenizar(
        marca_tokens.quitar_css_embebido(limpio)
    )
    assert huerfanos == []


def test_un_hex_en_el_css_propio_si_se_detecta():
    """La otra mitad, y la que importa: sin esto el guardia pasaría por no mirar."""
    sucio = _snapshot("  .chip { color: #AB12CD; }")
    _, _, huerfanos = marca_tokens._tokenizar(
        marca_tokens.quitar_css_embebido(sucio)
    )
    assert huerfanos == ["#AB12CD"]


def test_un_hex_de_la_paleta_escrito_a_mano_se_sugiere_como_rol():
    """No es huérfano: tiene rol, y el gate debe nombrarlo para que se corrija."""
    sucio = _snapshot("  .chip { color: #50C0A8; }")
    nuevo, n, huerfanos = marca_tokens._tokenizar(
        marca_tokens.quitar_css_embebido(sucio)
    )
    assert (n, huerfanos) == (1, [])
    assert "var(--acento)" in nuevo


def test_migrar_no_toca_la_paleta_embebida():
    """El modo migración reescribe el archivo. Si tokenizara el bloque embebido
    dejaría `--acento: var(--acento);`: una variable que se referencia a sí misma
    y no resuelve a ningún color. La pieza no falla al renderizar, sale sin
    paleta, y el defecto viaja hasta que alguien mira un PNG.

    Estuvo a salvo por accidente mientras el mapa estaba desactualizado: ninguno
    de esos hex tenía rol, así que el migrador se negaba a escribir. Arreglar el
    mapa quitó esa protección sin que nada lo dijera.
    """
    entrada = _snapshot("  .chip { color: var(--acento); }")
    salida, n, huerfanos = marca_tokens._tokenizar_respetando_paleta(
        entrada, marca_tokens.cargar_mapa()
    )
    assert (salida, n, huerfanos) == (entrada, 0, [])
    assert "--acento: #50C0A8;" in salida


def test_migrar_si_tokeniza_fuera_del_bloque():
    """La contraparte: fuera de la paleta, migrar sigue haciendo su trabajo."""
    entrada = _snapshot("  .chip { color: #50C0A8; }")
    salida, n, huerfanos = marca_tokens._tokenizar_respetando_paleta(
        entrada, marca_tokens.cargar_mapa()
    )
    assert (n, huerfanos) == (1, [])
    assert ".chip { color: var(--acento); }" in salida
    assert "--acento: #50C0A8;" in salida


def test_la_migracion_es_no_op_sobre_las_plantillas_de_produccion():
    """Correr el migrador hoy no debe cambiar ni un byte: ya están migradas.
    Si cambia algo, o la paleta se desincronizó o el migrador está mordiendo
    donde no debe."""
    mapa = marca_tokens.cargar_mapa()
    for ruta in marca_tokens._plantillas():
        html = ruta.read_text(encoding="utf-8")
        salida, _, _ = marca_tokens._tokenizar_respetando_paleta(html, mapa)
        assert salida == html, f"migrar modificaría {ruta.name}"

