"""Las skills de AGY tienen que describir la cadena COMPLETA.

**El defecto que esto cierra.** `ecosistema-datos-macro` le decia a AGY que el
pipeline maestro era `pipeline_ingesta.py`, que es el paso 1 de 3. Los precios de
MT5 (`extractor_precios.py`) y el sesgo del Playbook (`macro_bias_engine.py`) se
quedaban atras, y el aviso de CLAUDE.md aplica entero: correr el motor sobre
precios que no se actualizaron produce un sesgo que PARECE fresco.

AGY no lee CLAUDE.md, asi que si su skill nombra un tercio de la cadena, AGY
corre un tercio de la cadena y reporta exito.
"""
from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SKILL = RAIZ / ".agents" / "skills" / "ecosistema-datos-macro" / "SKILL.md"


def test_la_skill_nombra_el_punto_de_entrada_unico_de_la_cadena():
    texto = SKILL.read_text(encoding="utf-8")
    assert "pipeline_datos.py" in texto, (
        "la skill no nombra scripts/pipeline_datos.py, que es el unico punto de "
        "entrada de la cadena de datos"
    )


def test_la_skill_no_presenta_la_ingesta_como_la_cadena_completa():
    texto = SKILL.read_text(encoding="utf-8")
    assert "pipeline maestro de ingesta" not in texto, (
        "la ingesta es el paso 1 de 3, no el pipeline maestro"
    )


def test_la_skill_nombra_los_tres_pasos():
    texto = SKILL.read_text(encoding="utf-8")
    for paso in ("pipeline_ingesta.py", "extractor_precios.py", "macro_bias_engine.py"):
        assert paso in texto, f"la skill no nombra el paso {paso}"


def test_la_skill_manda_verificar_el_estado_con_el_comando_y_no_a_ojo():
    """`--estado` lee los tres relojes y aplica el umbral del Playbook."""
    texto = SKILL.read_text(encoding="utf-8")
    assert "--estado" in texto


def test_la_skill_usa_uv_run_como_el_resto_del_repo():
    """`python` a secas corre fuera del entorno del proyecto."""
    texto = SKILL.read_text(encoding="utf-8")
    assert "uv run" in texto


def test_la_skill_avisa_del_fallback_a_yfinance():
    """Un precio de yfinance es un futuro, no el CFD del broker.

    El 2026-09-02 cinco de seis activos salieron de yfinance mientras la cadena
    reportaba datos frescos, y los stops del Playbook quedaron calculados sobre
    otro instrumento.
    """
    texto = SKILL.read_text(encoding="utf-8").lower()
    assert "yfinance" in texto


def test_los_scripts_que_la_skill_nombra_existen():
    """Un contrato por nombre que nadie verifica es el defecto recurrente."""
    base = SKILL.parent / "scripts"
    for nombre in (
        "pipeline_ingesta.py", "agenda.py", "extractor_usa.py", "extractor_chile.py",
        "extractor_europa_uk.py", "extractor_commodities.py", "extractor_japon.py",
    ):
        assert (base / nombre).exists(), f"la skill nombra {nombre} y no existe"
    for nombre in ("pipeline_datos.py", "extractor_precios.py", "macro_bias_engine.py"):
        assert (RAIZ / "scripts" / nombre).exists(), f"falta scripts/{nombre}"


TRADING = RAIZ / ".agents" / "skills" / "trading-cuantitativo-intermercado" / "SKILL.md"


def test_ante_datos_vencidos_la_skill_cuantitativa_manda_la_cadena_completa():
    """El sesgo lo produce el paso 3, asi que la ingesta sola no lo refresca."""
    texto = TRADING.read_text(encoding="utf-8")
    assert "pipeline_datos.py" in texto
    assert "scripts/pipeline_ingesta.py`." not in texto, (
        "sigue mandando solo la ingesta ante STALE_DATA"
    )


def test_ninguna_skill_de_agy_nombra_un_script_que_no_existe():
    """Contrato de nombres sobre las cuatro skills.

    Cubre las skills **del proyecto**, que son las que le dicen a AGY qué correr
    en este repo. `diagram-design` es de terceros y queda fuera a proposito: su
    SKILL.md nombra `scripts/verify-motion.py`, que no existe en ninguna parte,
    y editarla no serviria porque la proxima actualizacion del upstream lo
    revertiria. Queda reportado, no tapado.

    Una ruta se acepta relativa a la raiz del repo **o** a la carpeta de la
    propia skill, porque una skill puede traer sus scripts dentro.
    """
    import re
    base = RAIZ / ".agents" / "skills"
    nuestras = (
        "ecosistema-datos-macro",
        "trading-cuantitativo-intermercado",
        "generar-reporte-editorial",
    )
    for skill in sorted(base.glob("*/SKILL.md")):
        if skill.parent.name not in nuestras:
            continue
        texto = skill.read_text(encoding="utf-8")
        for ruta in set(re.findall(r"`[^`]*?((?:scripts/|\.agents/)[\w./-]+\.py)", texto)):
            assert (RAIZ / ruta).exists() or (skill.parent / ruta).exists(), (
                f"{skill.parent.name} nombra {ruta}, que no existe ni en la raiz "
                "ni en la carpeta de la skill"
            )
