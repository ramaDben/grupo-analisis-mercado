"""El guardián del enchufe: fuera de `scripts/estrategia/` no se toma una decisión técnica.

Spec `docs/superpowers/specs/2026-10-09-enchufe-estrategia-design.md` §6. Hasta el enchufe,
cada pieza calculaba la dirección por su cuenta (la EMA 50 en el escáner, en Avisos, en el
informe y en el analista) y los niveles con `analizar_activo`. Sin este test, la próxima pieza
urgente vuelve a hacerlo y el sistema tiene dos lecturas a la vez.

Falla si fuera de `scripts/estrategia/` aparece:
- `direccion_tecnica` (la dirección por EMA 50 del escáner viejo);
- `ema_50` dentro de una comparación, que es usarla para decidir y no para mostrarla;
- `analizar_activo` o `get_asset_levels` importados o llamados: sus `s1`/`r1` son los niveles
  de la lectura vieja (la tool queda en el MCP como dato crudo, para auditoría y para AGY);
- un import de `_get_support_resistance`.

Mostrar una media en un manual o calcularla en el extractor no es decidir, y por eso el test
lee el AST y no busca la palabra: un `grep` obligaría a llenar la lista de excepciones, y una
excepción es la puerta por la que vuelve la lectura vieja.
"""
from __future__ import annotations

import ast
import warnings
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "scripts"

# Ruta relativa a `scripts/` -> motivo. Vacía a propósito: toda entrada necesita su motivo.
EXCEPCIONES: dict[str, str] = {}

PROHIBIDOS_NOMBRE = {"direccion_tecnica", "analizar_activo", "_get_support_resistance", "get_asset_levels"}


def _fuentes() -> list[Path]:
    return sorted(
        p for p in SCRIPTS.rglob("*.py")
        if "__pycache__" not in p.parts and (SCRIPTS / "estrategia") not in p.parents
    )


def _nombra_ema_50(nodo: ast.AST) -> bool:
    """`x["ema_50"]`, `x.get("ema_50")` o `x.ema_50`, en cualquier parte del nodo."""
    for hijo in ast.walk(nodo):
        if isinstance(hijo, ast.Constant) and hijo.value == "ema_50":
            return True
        if isinstance(hijo, ast.Attribute) and hijo.attr == "ema_50":
            return True
    return False


def decisiones_tecnicas(codigo: str) -> list[str]:
    """Las decisiones técnicas de un módulo, como `línea: qué`."""
    hallazgos: list[str] = []
    with warnings.catch_warnings():  # escapes inválidos de módulos ajenos: no son asunto de este test
        warnings.simplefilter("ignore", SyntaxWarning)
        arbol = ast.parse(codigo)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            for alias in nodo.names:
                if alias.name in PROHIBIDOS_NOMBRE:
                    hallazgos.append(f"{nodo.lineno}: importa {alias.name}")
        elif isinstance(nodo, ast.Name) and nodo.id in PROHIBIDOS_NOMBRE:
            hallazgos.append(f"{nodo.lineno}: usa {nodo.id}")
        elif isinstance(nodo, ast.Attribute) and nodo.attr in PROHIBIDOS_NOMBRE:
            hallazgos.append(f"{nodo.lineno}: usa {nodo.attr}")
        elif isinstance(nodo, ast.FunctionDef) and nodo.name in PROHIBIDOS_NOMBRE:
            hallazgos.append(f"{nodo.lineno}: define {nodo.name}")
        elif isinstance(nodo, ast.Compare) and _nombra_ema_50(nodo):
            hallazgos.append(f"{nodo.lineno}: decide con ema_50")
    return hallazgos


def test_fuera_de_la_estrategia_no_se_decide_la_direccion_ni_los_niveles():
    encontrados = []
    for ruta in _fuentes():
        rel = ruta.relative_to(SCRIPTS).as_posix()
        if rel in EXCEPCIONES:
            continue
        # `guia_usdclp/svg_artefactos_2.py` trae un BOM en la segunda línea, tras el shebang.
        for h in decisiones_tecnicas(ruta.read_text(encoding="utf-8").replace("﻿", "")):
            encontrados.append(f"scripts/{rel}:{h}")
    assert not encontrados, (
        "decisiones técnicas fuera de scripts/estrategia/ (la lectura sale de la estrategia "
        "activa: get_lectura o referencia_semanal.lectura_actual):\n" + "\n".join(encontrados)
    )


def test_toda_excepcion_trae_su_motivo_y_existe():
    for rel, motivo in EXCEPCIONES.items():
        assert (SCRIPTS / rel).exists(), f"excepción de un archivo que ya no existe: {rel}"
        assert len(motivo.strip()) > 20, f"excepción sin motivo: {rel}"


def test_el_detector_ve_cada_forma_de_la_lectura_vieja():
    """Un guardián que no detecta nada pasa siempre: se prueba contra lo que tiene que atajar."""
    casos = {
        "from screener_gi import direccion_tecnica": "importa direccion_tecnica",
        "import screener_gi as sc\nd = sc.direccion_tecnica(h1)": "usa direccion_tecnica",
        "from market_data_mcp.analisis import analizar_activo": "importa analizar_activo",
        "h1 = analizar_activo('XAUUSD', 'H1')": "usa analizar_activo",
        "from market_data_mcp.analisis import _get_support_resistance": "importa _get_support_resistance",
        "from market_data_mcp.tools.levels import get_asset_levels": "importa get_asset_levels",
        "alcista = h1['price'] > h1['ema_50']": "decide con ema_50",
        "if precio < datos.get('ema_50'):\n    pass": "decide con ema_50",
        "sesgo = 'ALCISTA' if lec.precio >= lec.ema_50 else 'BAJISTA'": "decide con ema_50",
    }
    for codigo, esperado in casos.items():
        assert any(esperado in h for h in decisiones_tecnicas(codigo)), codigo


def test_mostrar_una_media_no_es_decidir():
    """El extractor la calcula y los manuales la muestran: eso es dato, no lectura."""
    for codigo in ('fila = {"ema50": r.get("ema_50")}', 'df["ema_50"] = close.ewm(span=50).mean()'):
        assert decisiones_tecnicas(codigo) == [], codigo


def test_el_bot_de_analistas_no_trae_el_metodo_viejo():
    """La pieza semanal del #254 decidía con la EMA 50 D1 y salía con el Chandelier (spec
    oportunidad-semanal §3). Ninguna de las dos puede volver al bot."""
    hallazgos = []
    archivos = sorted((SCRIPTS / "analista").glob("*.py"))
    assert archivos, "el guardián no encontró scripts/analista"
    for ruta in archivos:
        texto = ruta.read_text(encoding="utf-8").lower()
        for prohibido in ("chandelier", "ema_50", "ema50", "ema 50"):
            if prohibido in texto:
                hallazgos.append(f"{ruta.name}: {prohibido}")
    assert hallazgos == []
