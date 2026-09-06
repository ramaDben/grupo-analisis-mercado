"""Las partes puras del orquestador de encargos. No invoca a Antigravity.

Los dos tests que de verdad importan son `test_un_archivo_ya_sucio_que_cambia_se_detecta`,
que fija el punto sutil del diseño (acá SIEMPRE hay dieciséis JSON sucios por la ingesta
macro, así que la lista de estado sola no alcanza), y
`test_clasificar_distingue_los_fallos`, porque sin eso todo fallo se ve igual: un archivo
de salida vacío.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import agy_encargo  # noqa: E402

VALIDO = """---
titulo: Un encargo de prueba
archivos:
  - scripts/algo.py
  - tests/test_algo.py
verificar:
  - uv run ruff check scripts/algo.py
---

Escribí el módulo.
"""


def _escribir(tmp_path: Path, texto: str) -> Path:
    ruta = tmp_path / "encargo.md"
    ruta.write_text(texto, encoding="utf-8")
    return ruta


# --- el encargo: fail-closed antes de gastar siete minutos ----------------

def test_un_encargo_valido_se_parsea(tmp_path):
    encargo, problemas = agy_encargo.leer_encargo(_escribir(tmp_path, VALIDO))
    assert problemas == []
    assert encargo.titulo == "Un encargo de prueba"
    assert encargo.archivos == ("scripts/algo.py", "tests/test_algo.py")
    assert encargo.verificar == ("uv run ruff check scripts/algo.py",)
    assert "Escribí el módulo." in encargo.cuerpo


def test_sin_frontmatter_no_se_manda(tmp_path):
    encargo, problemas = agy_encargo.leer_encargo(_escribir(tmp_path, "Escribí algo.\n"))
    assert encargo is None and problemas


def test_sin_archivos_no_se_manda(tmp_path):
    # Sin ámbito declarado no se puede auditar qué tocó, que es la mitad del valor
    # de este módulo. Rechazarlo cuesta un segundo; descubrirlo después, una corrida.
    texto = VALIDO.replace("archivos:\n  - scripts/algo.py\n  - tests/test_algo.py\n", "")
    encargo, problemas = agy_encargo.leer_encargo(_escribir(tmp_path, texto))
    assert encargo is None
    assert any("archivos" in p for p in problemas)


def test_sin_verificar_no_se_manda(tmp_path):
    texto = VALIDO.replace("verificar:\n  - uv run ruff check scripts/algo.py\n", "")
    encargo, problemas = agy_encargo.leer_encargo(_escribir(tmp_path, texto))
    assert encargo is None
    assert any("verificar" in p for p in problemas)


def test_frontmatter_invalido_no_lanza(tmp_path):
    encargo, problemas = agy_encargo.leer_encargo(
        _escribir(tmp_path, "---\narchivos: [sin cerrar\n---\ncuerpo\n")
    )
    assert encargo is None and problemas


def test_el_prompt_lleva_preambulo_ambito_y_cuerpo(tmp_path):
    encargo, _ = agy_encargo.leer_encargo(_escribir(tmp_path, VALIDO))
    prompt = agy_encargo.componer(encargo)
    # El preámbulo compartido, con sus prohibiciones.
    assert "enviar_whatsapp.py" in prompt
    assert "git commit" in prompt
    # El ámbito viaja también en el texto: decírselo es más barato que medirlo después.
    assert "scripts/algo.py" in prompt and "tests/test_algo.py" in prompt
    assert "uv run ruff check scripts/algo.py" in prompt
    assert "Escribí el módulo." in prompt


# --- la medición del árbol ------------------------------------------------

def test_cambios_detecta_altas_bajas_y_modificaciones():
    antes = {"a.py": "111", "b.py": "222"}
    despues = {"a.py": "111", "b.py": "999", "c.py": "333"}
    assert agy_encargo.cambios(antes, despues) == ["b.py", "c.py"]


def test_un_archivo_ya_sucio_que_cambia_se_detecta():
    # El punto sutil del diseño. En este repo la ingesta macro deja dieciséis JSON de
    # `data central/` modificados en cada arranque de sesión, así que comparar solo la
    # LISTA de archivos sucios no vería una escritura sobre uno de ellos: su línea de
    # estado no cambia. Por eso se hashea el contenido.
    antes = {"data central/DATA USA/raw/treasury_fed_data.json": "aaa"}
    despues = {"data central/DATA USA/raw/treasury_fed_data.json": "bbb"}
    assert agy_encargo.cambios(antes, despues) == [
        "data central/DATA USA/raw/treasury_fed_data.json"
    ]


def test_fuera_de_ambito_nombra_solo_los_intrusos():
    tocados = ["scripts/algo.py", "tests/test_algo.py", "CLAUDE.md"]
    assert agy_encargo.fuera_de_ambito(
        tocados, ("scripts/algo.py", "tests/test_algo.py")
    ) == ["CLAUDE.md"]


def test_fuera_de_ambito_normaliza_los_separadores():
    # git devuelve barras normales; las rutas de este repo se escriben de las dos
    # formas. Comparar sin normalizar reportaría todo como fuera de ámbito.
    assert agy_encargo.fuera_de_ambito(["scripts/algo.py"], ("scripts\\algo.py",)) == []
    assert agy_encargo.fuera_de_ambito(["scripts/algo.py"], ("./scripts/algo.py",)) == []


def test_un_ambito_vacio_reporta_todo_como_intruso():
    # Fail-closed: si el ámbito no dice nada, nada está autorizado.
    assert agy_encargo.fuera_de_ambito(["a.py"], ()) == ["a.py"]


# --- la clasificación del fallo -------------------------------------------

def _envoltorio(**campos) -> str:
    import json

    base = {
        "conversation_id": "abc",
        "status": "SUCCESS",
        "response": "listo",
        "duration_seconds": 12.5,
        "usage": {"input_tokens": 10, "output_tokens": 2},
    }
    base.update(campos)
    return json.dumps(base)


def test_clasificar_reconoce_el_exito():
    r = agy_encargo.clasificar(0, _envoltorio(), "")
    assert r.codigo == "ok"
    assert r.conversacion == "abc" and r.segundos == 12.5
    assert r.uso["input_tokens"] == 10


def test_clasificar_distingue_los_fallos():
    # Cada código tiene una acción distinta. Confundir un timeout con un problema de
    # autenticación cuesta reintentar lo que no se arregla reintentando.
    casos = [
        ({"status": "ERROR", "error": "RESOURCE_EXHAUSTED: quota"}, "cuota"),
        ({"status": "ERROR", "error": "auth required, please sign in"}, "auth"),
        ({"status": "ERROR", "error": "timeout waiting for response"}, "timeout"),
        ({"status": "ERROR", "error": "invalid model selection"}, "error"),
    ]
    for campos, esperado in casos:
        assert agy_encargo.clasificar(1, _envoltorio(**campos), "").codigo == esperado, campos


def test_clasificar_una_salida_vacia_no_es_un_exito():
    # El modo de falla más probable: agy sale sin escribir nada. Se ve idéntico a un
    # encargo que todavía está pensando, y por eso tiene su propio código.
    assert agy_encargo.clasificar(1, "", "").codigo == "vacio"
    assert agy_encargo.clasificar(127, "", "agy: command not found").codigo == "ausente"
    assert agy_encargo.clasificar(1, "", "Error: timeout waiting").codigo == "timeout"


def test_clasificar_una_salida_que_no_es_json_no_lanza():
    r = agy_encargo.clasificar(0, "esto no es json", "")
    assert r.codigo == "error"


# --- el veredicto no colapsa en un booleano ------------------------------

def test_el_veredicto_separa_ambito_de_verificacion(tmp_path, capsys):
    # El caso interesante que un booleano esconde: la verificación en verde con un
    # archivo de más tocado. Tiene que salir 2, no 0.
    encargo, _ = agy_encargo.leer_encargo(_escribir(tmp_path, VALIDO))
    res = agy_encargo.Resultado("ok", "agy reportó SUCCESS")
    verde = [agy_encargo.Comprobacion("uv run ruff check scripts/algo.py", 0, "ok")]

    assert agy_encargo.informar(encargo, res, ["scripts/algo.py"], [], verde) == 0
    assert agy_encargo.informar(encargo, res, ["CLAUDE.md"], ["CLAUDE.md"], verde) == 2

    rojo = [agy_encargo.Comprobacion("uv run ruff check scripts/algo.py", 1, "falla")]
    assert agy_encargo.informar(encargo, res, ["scripts/algo.py"], [], rojo) == 1

    fallo = agy_encargo.Resultado("cuota", "cuota agotada")
    assert agy_encargo.informar(encargo, fallo, [], [], []) == 3
    capsys.readouterr()


def test_los_tiers_apuntan_a_modelos_con_forma_de_slug():
    # `agy models` lista slugs (`gemini-3.8-flash-high`). Un nombre para mostrar
    # también funciona con --model, pero mezclarlos hace que un typo se vea igual que
    # un modelo retirado, y headless NO cae a un modelo por defecto: sale con error.
    for rol, slug in agy_encargo.TIERS.items():
        assert slug.islower() and " " not in slug, f"{rol} -> {slug}"


def test_la_bitacora_no_se_cae_con_una_ruta_relativa():
    # El fallo del 2026-09-06: `Path.relative_to` levanta ValueError ante una ruta
    # relativa, y el encargo se invoca casi siempre así. Mató la bitácora DESPUÉS de
    # una delegación exitosa: el trabajo estaba hecho y el registro se perdió. Lo
    # último que hace el orquestador no puede ser lo que se cae.
    assert agy_encargo.ruta_relativa(Path("docs/agy/encargos/x.md")).endswith("x.md")
    assert agy_encargo.ruta_relativa(_REPO_ROOT / "docs" / "x.md") == str(
        Path("docs") / "x.md"
    )
    # Una ruta fuera del repo devuelve la absoluta en vez de lanzar.
    afuera = Path(_REPO_ROOT.anchor) / "otra-parte" / "x.md"
    assert agy_encargo.ruta_relativa(afuera)
