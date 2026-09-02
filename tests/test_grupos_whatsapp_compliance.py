"""Tests de conformidad y contrato entre las descripciones de grupos de WhatsApp y los workflows/pipelines.

Verifica que lo prometido en cada grupo (tickers, digits, formatos, fotos de perfil,
reglas de formato de mensajes y enrutamiento modular) se cumpla estrictamente en el código.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import sys
import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

GRUPOS_DIR = RAIZ / "docs" / "grupos_whatsapp"
ACTIVOS_JSON = RAIZ / "config" / "activos.json"

GRUPOS_ESPERADOS = [
    "01_macro_y_apertura",
    "02_forex_divisas",
    "03_commodities_materias_primas",
    "04_indices_bursatiles",
    "05_acciones_etfs",
    "06_criptoactivos",
    "07_oportunidades_cuantitativas",
]


def test_existen_todas_las_carpetas_y_archivos_de_grupos():
    assert GRUPOS_DIR.is_dir(), "Directorio docs/grupos_whatsapp debe existir"
    for grupo in GRUPOS_ESPERADOS:
        g_dir = GRUPOS_DIR / grupo
        assert g_dir.is_dir(), f"Carpeta {grupo} debe existir"
        assert (g_dir / "foto_perfil.jpg").is_file(), f"Falta foto_perfil.jpg en {grupo}"
        assert (g_dir / "info_grupo.txt").is_file(), f"Falta info_grupo.txt en {grupo}"


def test_las_descripciones_no_contienen_guiones_largos_prohibidos():
    """Regla canónica de redacción para el cliente: prohibido el guion largo '—' y medio '–' en textos."""
    for grupo in GRUPOS_ESPERADOS:
        txt = (GRUPOS_DIR / grupo / "info_grupo.txt").read_text(encoding="utf-8")
        # Extraer solo la sección de descripción
        if "[3] DESCRIPCIÓN OFICIAL" in txt:
            desc = txt.split("[3] DESCRIPCIÓN OFICIAL")[1]
            # No debe contener guiones largos como inciso en el cuerpo (permitiendo encabezados de separadores === o ---)
            for linea in desc.splitlines():
                if linea.startswith("=") or linea.startswith("-"):
                    continue
                assert "—" not in linea, f"Guion largo encontrado en {grupo}: {linea}"
                assert "–" not in linea, f"Guion medio encontrado en {grupo}: {linea}"


def test_todos_los_activos_mencionados_existen_en_catalogo_con_sus_digits():
    """Verifica que los tickers mencionados en los grupos existan en config/activos.json y coincidan sus decimales."""
    import screener_gi as sc

    universo = {a["ticker"]: a for a in sc.cargar_universo(solo_renderizables=False)}

    # Mapeos explícitos declarados en las descripciones
    declaraciones = [
        ("USDCLP", 2),
        ("EURUSD", 5),
        ("USDJPY", 3),
        ("GBPUSD", 5),
        ("XAUUSD", 2),
        ("XAGUSD", 3),
        ("WTI.spot", 3),
        ("COPPER", 1),
        ("US100.spot", 2),
        ("US500.spot", 2),
        ("US30.spot", 2),
        ("BTCUSD", 2),
        ("ETHUSD", 2),
        ("SOLUSD", 2),
        ("LTCUSD", 2),
        ("ADAUSD", 4),
        ("DOGUSD", 4),
        ("QQQ.US", 2),
        ("SPY.US", 2),
        ("SOXX.US", 2),
        ("IWM.US", 2),
        ("GLD.US", 2),
        ("#AAPL", 2),
        ("#MSFT", 2),
        ("#NVDA", 2),
        ("#AMZN", 2),
        ("#MELI", 2),
    ]

    for ticker, digits_esperados in declaraciones:
        assert ticker in universo, f"Ticker {ticker} prometido en los grupos no existe en el catálogo"
        assert universo[ticker]["digits"] == digits_esperados, (
            f"Digits de {ticker} ({universo[ticker]['digits']}) no coinciden con {digits_esperados}"
        )


def test_enrutamiento_completo_del_universo_hacia_los_grupos_correctos():
    """Verifica que cada activo del universo mapee determinísticamente a su grupo."""
    import pipeline_carrusel as pc
    import screener_gi as sc

    universo = sc.cargar_universo(solo_renderizables=False)
    for activo in universo:
        grupo = pc.obtener_grupo_whatsapp(activo["categoria"], activo["ticker"])
        assert grupo in GRUPOS_ESPERADOS, f"Grupo {grupo} para {activo['ticker']} no es válido"
        if activo["categoria"] == "forex":
            assert grupo == "02_forex_divisas"
        elif activo["categoria"] in ("commodity", "commodities"):
            assert grupo == "03_commodities_materias_primas"
        elif activo["categoria"] == "crypto":
            assert grupo == "06_criptoactivos"
        elif activo["categoria"] == "indice":
            assert grupo == "04_indices_bursatiles"
        elif activo["categoria"] in ("accion", "acciones", "etf", "etfs"):
            assert grupo == "05_acciones_etfs"
