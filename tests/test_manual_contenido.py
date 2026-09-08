"""Guardias del contenido generado del manual: el caso real y las guías de lectura.

Dos secciones del manual **no las escribe una persona**: la 3.5 con los cinco
episodios de clima y la 11.1 con el caso completo. Las produce un script desde
las series, y eso las hace verificables. Lo que estos tests impiden:

1. **Que el caso publicado deje de cumplir su propio setup.** El caso del Módulo
   11.1 afirma que una vela H1 concreta cumplió las tres condiciones del rebote
   en rango. Si una reingesta cambia la serie y esa vela ya no califica, el
   manual estaría enseñando un ejemplo falso con números de aspecto correcto.
   `resolver_caso` levanta ante eso, y acá se le exige que no levante.

2. **Que el caso publique una ficha que su propio filtro rechaza.** El método
   exige riesgo/beneficio 1,0 o más. Publicar un caso que llega al final con 0,67
   sería enseñar a saltarse el filtro que el mismo manual declara obligatorio.

3. **Que el bloque del manual quede desincronizado de su generador.** Es el
   defecto recurrente del repo: dos copias de lo mismo y una queda atrás. Acá la
   copia buena es la que sale del script.

4. **Un guion largo o medio en texto de cliente.** El manual se firma con el
   nombre de un analista y ese guion es la marca reconocible de texto generado
   por IA. El punto medio `·` sí se permite: es separador del kit de marca.

Los tests que necesitan las series se saltan si no están en disco: las series
intradía y diarias están gitignoreadas y se regeneran con el extractor, así que
en un clon nuevo no existen todavía.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

MANUAL = RAIZ / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md"
OHLC = RAIZ / "data central" / "DATA PRECIOS OHLC"
CURVA_HIST = RAIZ / "data central" / "DATA USA" / "raw" / "curva_fred_historico.json"
COMM_HIST = RAIZ / "data central" / "DATA ORO Y COMMODITIES" / "raw" / "commodities_historico.json"


@pytest.fixture(scope="module")
def manual() -> str:
    return MANUAL.read_text(encoding="utf-8")


def _hay_series(*archivos: Path) -> bool:
    return all(a.exists() for a in archivos)


# ── El texto de cliente ──────────────────────────────────────────────────────

def test_el_manual_no_tiene_guion_largo_ni_medio(manual: str) -> None:
    assert "—" not in manual, "hay un guion largo (—) en el manual"
    assert "–" not in manual, "hay un guion medio (–) en el manual"


def test_las_dos_secciones_generadas_estan_en_el_manual(manual: str) -> None:
    for marca in (
        "<!-- INICIO graficos-regimenes",
        "<!-- FIN graficos-regimenes -->",
        "<!-- INICIO caso-transversal",
        "<!-- FIN caso-transversal -->",
    ):
        assert marca in manual, f"falta la marca {marca}: el bloque generado no está"


# ── El caso del Módulo 11.1 ──────────────────────────────────────────────────

@pytest.fixture(scope="module")
def caso() -> dict:
    if not _hay_series(OHLC / "USDCLP_H1.json", COMM_HIST):
        pytest.skip("faltan las series: correr el extractor de precios y --historico")
    pytest.importorskip("pandas")
    from caso_transversal import resolver_caso

    return resolver_caso()


def test_la_vela_del_caso_sigue_cumpliendo_su_setup(caso: dict) -> None:
    """`resolver_caso` levanta si alguna condición dejó de cumplirse."""
    assert all(caso["condiciones"].values()), caso["condiciones"]


def test_el_caso_publicado_pasa_el_filtro_de_riesgo_beneficio(caso: dict) -> None:
    assert caso["rr"] >= 1.0, (
        f"el caso del manual termina con R:R {caso['rr']:.2f}, bajo el mínimo de 1,0 que el "
        "propio método exige: habría que elegir otro caso, no publicar este"
    )


def test_el_caso_respeta_el_presupuesto_de_riesgo(caso: dict) -> None:
    """El lote se redondea hacia abajo, así que la pérdida queda bajo el 1 %."""
    assert 0 < caso["perdida_pct"] <= 1.0, (
        f"la pérdida del caso es el {caso['perdida_pct']:.2f} % de la cuenta"
    )


def test_la_direccion_del_caso_esta_permitida_por_el_cobre(caso: dict) -> None:
    """El desempate del Módulo 3.3: con el cobre subiendo, la compra está prohibida."""
    assert caso["habilita"] in ("rango", "solo compra"), (
        f"el cobre venía {caso['pct_cobre']:+.2f} % y eso deja al USD/CLP en "
        f"'{caso['habilita']}': el caso publica una compra que el manual prohíbe"
    )


# ── Los bloques generados contra su generador ────────────────────────────────

def test_el_caso_del_manual_esta_sincronizado_con_su_generador(manual: str, caso: dict) -> None:
    from caso_transversal import MARCA_FIN, MARCA_INICIO, bloque_markdown

    esperado = bloque_markdown(caso)
    inicio = manual.index(MARCA_INICIO)
    fin = manual.index(MARCA_FIN) + len(MARCA_FIN)

    assert manual[inicio:fin] == esperado, (
        "el bloque del caso en el manual no coincide con lo que genera el script. "
        "No lo edites a mano: corré "
        "`uv run python scripts/caso_transversal.py --escribir`"
    )


def test_los_graficos_del_manual_estan_sincronizados_con_su_generador(manual: str) -> None:
    if not _hay_series(OHLC / "XAUUSD_D1.json", CURVA_HIST, COMM_HIST):
        pytest.skip("faltan las series históricas: correr los extractores con --historico")
    from grafico_regimen_svg import MARCA_FIN, MARCA_INICIO, bloque_markdown

    esperado = bloque_markdown()
    inicio = manual.index(MARCA_INICIO)
    fin = manual.index(MARCA_FIN) + len(MARCA_FIN)

    assert manual[inicio:fin] == esperado, (
        "la sección 3.5 del manual no coincide con lo que genera el script. "
        "No la edites a mano: corré "
        "`uv run python scripts/grafico_regimen_svg.py --escribir`"
    )
