"""El guardrail de consola, y sobre todo lo que NO tiene que detener.

La mitad de estos tests fijan falsos positivos. No es simetría decorativa: un
guardia que grita sobre un `| head -5` se apaga a la semana, y un guardia apagado
no protege de nada. Los falsos positivos son la vía por la que estos sistemas
mueren, no los falsos negativos.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from guardrails import shell  # noqa: E402


# --- el $ que se come el precio ------------------------------------------

def test_here_string_doble_con_precio_falla():
    v = shell.sin_here_string_peligroso('Set-Content x.txt @"\nEntrada: $931.44\n"@')
    assert not v.ok and v.motivo == "here_string_trunca_precio"


def test_cadena_doble_con_precio_falla():
    v = shell.sin_here_string_peligroso('Write-Output "el oro cerro en $4539.72"')
    assert not v.ok and v.motivo == "here_string_trunca_precio"


def test_here_string_simple_con_precio_pasa():
    # El caso que importa: `@'...'@` es literal y es la salida que el proyecto
    # recomienda. Si esto fallara, el guardia estaria prohibiendo la solucion.
    assert shell.sin_here_string_peligroso("Set-Content x.txt @'\nEntrada: $931.44\n'@").ok


def test_variable_de_powershell_normal_pasa():
    # `$now` es una variable legitima. Solo `$<digito>` es un precio perdido.
    assert shell.sin_here_string_peligroso('Write-Output "son las $now"').ok


# --- la codificacion que se come las tildes -------------------------------

def test_set_content_a_ruta_de_cliente_sin_encoding_falla():
    v = shell.sin_escritura_de_texto_por_consola(
        "Set-Content data/mensajes/2026-09-06/usdclp/niveles/09-01_niveles.txt $t"
    )
    assert not v.ok and v.motivo == "escritura_por_consola"


def test_set_content_con_encoding_utf8_pasa():
    assert shell.sin_escritura_de_texto_por_consola(
        "Set-Content data/mensajes/x.txt $t -Encoding utf8"
    ).ok


def test_encoding_utf8bom_y_mayusculas_tambien_pasan():
    for variante in ("-Encoding UTF8", "-Encoding utf8BOM", "-encoding utf-8"):
        assert shell.sin_escritura_de_texto_por_consola(
            f"Out-File data/stories/x.json {variante}"
        ).ok, variante


def test_escritura_fuera_de_ruta_de_cliente_pasa():
    # `data/logs/` puede salir en ANSI sin que a nadie le importe. Juzgarlo seria
    # friccion diaria sin ninguna falla documentada detras.
    assert shell.sin_escritura_de_texto_por_consola("Set-Content data/logs/x.txt $t").ok


def test_ruta_con_separador_de_windows_tambien_se_juzga():
    # La mitad de las rutas de este repo llegan con barra invertida.
    v = shell.sin_escritura_de_texto_por_consola(r"Set-Content data\mensajes\x.txt $t")
    assert not v.ok and v.motivo == "escritura_por_consola"


# --- la tuberia que se come los acentos entre etapas ----------------------

def test_dos_etapas_encadenadas_falla():
    v = shell.sin_pipeline_encadenado(
        "python scripts/serie_mt5.py | python scripts/story_grafico.py"
    )
    assert not v.ok and v.motivo == "pipeline_encadenado"


def test_una_sola_etapa_con_head_pasa():
    # Inspeccion, no puente de datos. Es el falso positivo mas probable de todos.
    assert shell.sin_pipeline_encadenado("python scripts/story_render.py | head -5").ok


def test_una_sola_etapa_con_jq_pasa():
    assert shell.sin_pipeline_encadenado("python scripts/pipeline_informe.py | jq .").ok


def test_comando_sin_tuberia_pasa():
    assert shell.sin_pipeline_encadenado("python scripts/serie_mt5.py").ok


# --- el compuesto ---------------------------------------------------------

def test_revisar_devuelve_el_primero_en_orden():
    # Un comando que infringe dos reglas reporta la del `$`, que va primera.
    v = shell.revisar('Set-Content data/mensajes/x.txt @"\n$931.44\n"@')
    assert not v.ok and v.motivo == "here_string_trunca_precio"


def test_revisar_aprueba_un_comando_limpio():
    assert shell.revisar("uv run pytest tests/ -q").ok


def test_ninguna_funcion_lanza_ante_entrada_vacia():
    # Un hook que revienta no bloquea: la escritura pasa sin revisar.
    for entrada in ("", None):
        assert shell.revisar(entrada).ok
