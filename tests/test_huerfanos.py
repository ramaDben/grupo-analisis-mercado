"""El detector de huérfanos: qué cuenta como justificación y qué no.

Los dos tests que de verdad importan son `test_el_detector_escanea_cmd_y_bat`, que
fija un error ya cometido (el primer barrido dio por muerto a
`generar_calculadora.py`, que corre todos los días desde una tarea de Windows), y
`test_el_detector_nunca_borra`, que impide la "mejora" natural y equivocada de
agregarle el borrado automático.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import huerfanos  # noqa: E402


def test_no_hay_modulos_injustificados():
    # Equivale a `uv run python scripts/huerfanos.py --check`. Cada archivo tiene
    # que estar llamado por algo, nombrado por la prosa operativa, o declarar su
    # invocador externo. Ninguna de las tres es un juicio de valor: son hechos.
    injustificados, _ = huerfanos.analizar()
    assert injustificados == [], (
        "sin justificación: "
        + ", ".join(injustificados)
        + " -- declararlos con `punto-de-entrada:` o borrarlos"
    )


def test_el_detector_escanea_cmd_y_bat():
    # El primer barrido no leía `.cmd` y por eso puso a `generar_calculadora.py`
    # en la lista de muertos: su invocador es `refrescar_calculadora.cmd`, que
    # dispara la tarea de Windows `GI-CalculadoraLotaje`. Borrar por esa lista
    # habría matado una publicación diaria a un sitio público.
    assert ".cmd" in huerfanos.EXTS_INDICE
    assert ".bat" in huerfanos.EXTS_INDICE
    assert ".cmd" in huerfanos.EXTS_CODIGO, "un .cmd tiene que poder justificar por sí solo"
    assert ".cmd" in huerfanos.CANDIDATOS["scripts"], "un .cmd también se juzga"


def test_el_detector_nunca_borra():
    # Su única acción es fallar. La invocación dinámica es invisible al análisis
    # de texto, así que un falso positivo tiene que costar una línea de
    # encabezado y no código perdido.
    fuente = (_SCRIPTS_DIR / "huerfanos.py").read_text(encoding="utf-8")
    for prohibido in ("unlink", "rmtree", "os.remove", "shutil.move", "git rm\"", "'rm'"):
        assert prohibido not in fuente, f"el detector no puede borrar, y menciona {prohibido}"


def test_la_propagacion_llega_al_tercer_eslabon():
    # Una cadena muerta se esconde detrás de su primer eslabón: si el detector
    # parara en la primera pasada, `medio` quedaría justificado por `raiz` y
    # `hoja` por `medio`, y nadie vería que la cadena entera está viva.
    candidatos = ["scripts/raiz.py", "scripts/medio.py", "scripts/hoja.py"]
    textos = {
        "tests/test_raiz.py": "import raiz",
        "scripts/raiz.py": "import medio",
        "scripts/medio.py": "import hoja",
        "scripts/hoja.py": "",
    }
    vivos, porque = huerfanos.marcar(candidatos, textos, declarados=set())

    assert vivos == set(candidatos), "la cadena entera es alcanzable desde el test"
    assert porque["scripts/raiz.py"].startswith("referenciado por")
    assert porque["scripts/hoja.py"] == "lo llama scripts/medio.py"


def test_dos_modulos_muertos_no_se_justifican_entre_si():
    # El caso que obliga a marcar desde raíces en vez de barrer desde el total.
    # Con el criterio "alguien lo nombra", cada uno sería la prueba de que el
    # otro se usa, y vivirían para siempre sin que nadie los llame.
    candidatos = ["scripts/a.py", "scripts/b.py"]
    textos = {"scripts/a.py": "import b", "scripts/b.py": "import a"}
    vivos, _ = huerfanos.marcar(candidatos, textos, declarados=set())

    assert vivos == set(), "a y b se referencian entre sí y nadie los alcanza"


def test_un_doc_de_diseno_no_justifica():
    # Un doc de diseño de una función retirada es la lápida, no el uso.
    # `templates/parte_postventa.txt` sobrevivió al primer filtro exactamente
    # así: lo nombraban dos docs de julio de `/postventa`, que está retirado.
    candidatos = ["scripts/retirado.py"]
    solo_diseno = {"docs/design/algo/2026-07-28-retirado-design.md": "usa retirado.py"}
    vivos, _ = huerfanos.marcar(candidatos, solo_diseno, declarados=set())
    assert vivos == set(), "un doc de diseño no puede mantener vivo a nadie"

    operativa = {"CLAUDE.md": "correr `python scripts/retirado.py` cada lunes"}
    vivos, porque = huerfanos.marcar(candidatos, operativa, declarados=set())
    assert vivos == {"scripts/retirado.py"}
    assert porque["scripts/retirado.py"] == "prosa operativa: CLAUDE.md"


def test_una_raiz_que_es_palabra_corriente_no_justifica():
    # `templates/calculadoras/instrucciones.html` aparecía justificado por
    # `README.md`, que nunca lo nombra: solo usa la palabra "instrucciones" en
    # una frase. Una plantilla se cita por su archivo, o por su raíz entre
    # comillas cuando el código la elige por nombre.
    candidatos = ["templates/calculadoras/instrucciones.html"]

    prosa_suelta = {"README.md": "seguí las instrucciones del manual"}
    vivos, _ = huerfanos.marcar(candidatos, prosa_suelta, declarados=set())
    assert vivos == set(), "la palabra suelta no es una referencia"

    por_archivo = {"CLAUDE.md": "la plantilla es `instrucciones.html`"}
    vivos, _ = huerfanos.marcar(candidatos, por_archivo, declarados=set())
    assert vivos == set(candidatos)

    entre_comillas = {"CLAUDE.md": 'se elige con plantilla="instrucciones"'}
    vivos, _ = huerfanos.marcar(candidatos, entre_comillas, declarados=set())
    assert vivos == set(candidatos)


def test_el_encabezado_exige_un_motivo(tmp_path):
    # "Declarado" sin decir quién lo llama es la misma opacidad con otro nombre.
    sin_motivo = tmp_path / "sin_motivo.py"
    sin_motivo.write_text("# punto-de-entrada:\nprint(1)\n", encoding="utf-8")
    assert not huerfanos.declara_punto_de_entrada(sin_motivo)

    con_motivo = tmp_path / "con_motivo.py"
    con_motivo.write_text(
        "# punto-de-entrada: lo corre el director a mano\nprint(1)\n", encoding="utf-8"
    )
    assert huerfanos.declara_punto_de_entrada(con_motivo)


def test_el_encabezado_solo_cuenta_en_la_cabecera(tmp_path):
    # Enterrado en la línea 300 no lo ve nadie que abra el archivo, que es la
    # mitad del valor de declararlo.
    tarde = tmp_path / "tarde.py"
    relleno = "x = 1\n" * (huerfanos.LINEAS_CABECERA + 5)
    tarde.write_text(relleno + "# punto-de-entrada: alguien\n", encoding="utf-8")
    assert not huerfanos.declara_punto_de_entrada(tarde)


def test_lo_gitignoreado_no_se_juzga():
    # `scripts/spanish_test.py` está gitignoreado a propósito en .gitignore:96.
    # Lo no rastreado es el escritorio de alguien, no el repo: juzgarlo pone la
    # suite roja en una máquina y verde en todas las demás.
    rastreados = huerfanos._rastreados_por_git()
    assert "scripts/spanish_test.py" not in rastreados
    injustificados, porque = huerfanos.analizar()
    assert not any("spanish_test" in r for r in injustificados)
    assert not any("spanish_test" in r for r in porque)
