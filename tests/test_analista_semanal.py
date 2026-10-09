"""La pieza semanal comercial: escenario en diario, simulación y texto de WhatsApp."""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import semanal as sm  # noqa: E402

SCL = ZoneInfo("America/Santiago")


def _serie(n: int = 60, base: float = 4000.0, paso: float = 2.0) -> pd.DataFrame:
    """Velas diarias en alza suave, con rango fijo: ATR conocido."""
    filas = []
    for i in range(n):
        c = base + paso * i
        filas.append({"time": pd.Timestamp("2026-06-01") + pd.Timedelta(days=i),
                      "open": c - 1, "high": c + 10, "low": c - 10, "close": c})
    return pd.DataFrame(filas)


def _d1(precio: float, ema50: float, r1: float, s1: float, origen: str = "swing") -> dict:
    return {"price": precio, "ema_50": ema50, "r1": r1, "s1": s1, "atr_14": 40.0,
            "niveles_origen": {"r1": origen, "s1": origen}}


# ───────────────────────────────────────────────────────────── semana


def test_la_semana_se_ancla_al_lunes_en_hora_de_chile():
    # Domingo 23:30 en Chile sigue siendo la semana que empezó el lunes anterior.
    assert sm.lunes_de(datetime(2026, 10, 18, 23, 30, tzinfo=SCL)) == date(2026, 10, 12)
    assert sm.lunes_de(datetime(2026, 10, 14, 9, 0, tzinfo=SCL)) == date(2026, 10, 12)
    assert sm.lunes_de(datetime(2026, 10, 19, 0, 5, tzinfo=SCL)) == date(2026, 10, 19)


# ───────────────────────────────────────────────────────────── escenario


def test_escenario_armado_usa_la_resistencia_diaria_y_un_chandelier_de_22_dias():
    df = _serie()
    precio = float(df["close"].iat[-1])
    esc = sm.escenario(_d1(precio, precio - 50, r1=precio + 30, s1=precio - 60), df, 2)
    assert esc["hay_escenario"] and esc["sesgo"] == "Alcista" and esc["estado"] == "armado"
    assert esc["gatillo"] == pytest.approx(precio + 30)
    hh22 = float(df["high"].tail(22).max())
    assert esc["invalidacion"] < hh22  # Chandelier: el máximo de 22 días menos 3 ATR
    assert esc["recorrido"] == pytest.approx(60.0)  # 1,5 × ATR14 diario
    # Armado: la simulación entra en el gatillo, no en el precio de ahora.
    assert esc["entrada"] == esc["gatillo"]
    assert "cierre diario sobre" in esc["textos"]["gatillo"]
    assert "no un objetivo" in esc["textos"]["recorrido"]


def test_escenario_activado_esta_semana_toma_el_nivel_roto_y_entra_al_precio():
    df = _serie()
    precio = float(df["close"].iat[-1])
    esc = sm.escenario(_d1(precio, precio - 50, r1=precio + 30, s1=precio - 60), df, 2,
                       ruptura=(precio - 8, len(df) - 2))
    assert esc["estado"] == "activado"
    assert esc["gatillo"] == pytest.approx(precio - 8)
    assert esc["entrada"] == pytest.approx(precio)


def test_una_ruptura_de_hace_mas_de_una_semana_no_cuenta_como_activacion():
    df = _serie()
    precio = float(df["close"].iat[-1])
    esc = sm.escenario(_d1(precio, precio - 50, r1=precio + 30, s1=precio - 60), df, 2,
                       ruptura=(precio - 80, len(df) - 9))
    assert esc["estado"] == "armado" and esc["gatillo"] == pytest.approx(precio + 30)


def test_bajo_la_media_de_50_dias_el_escenario_es_bajista_y_usa_el_soporte():
    df = _serie(paso=-2.0)
    precio = float(df["close"].iat[-1])
    esc = sm.escenario(_d1(precio, precio + 50, r1=precio + 60, s1=precio - 30), df, 2)
    assert esc["sesgo"] == "Bajista" and esc["gatillo"] == pytest.approx(precio - 30)
    assert esc["invalidacion"] > precio
    assert "cierre diario bajo" in esc["textos"]["gatillo"]


def test_sin_nivel_medido_no_hay_escenario_que_proponer():
    df = _serie()
    precio = float(df["close"].iat[-1])
    esc = sm.escenario(_d1(precio, precio - 50, r1=precio + 30, s1=precio - 60, origen="atr"), df, 2)
    assert esc["hay_escenario"] is False and esc["motivo"]


# ───────────────────────────────────────────────────────────── simulación

CONTRATO = {"clp_unidad": 950.0, "margen_lote": 380_000.0, "contrato": 100.0,
            "vol_min": 0.01, "vol_paso": 0.01, "moneda": "CLP"}
ESC = {"precio": 4000.0, "entrada": 4000.0, "invalidacion": 3880.0, "recorrido": 60.0}


def test_la_simulacion_muestra_la_perdida_y_el_recorrido_en_pesos():
    s = sm.simular(CONTRATO, ESC, monto=1_000_000, volumen=0.10)
    assert s["valor_punto"] == 95  # 950 CLP por punto y lote × 0,10
    assert s["perdida_invalidacion"] == 11_400  # 120 puntos × 95
    assert s["valor_recorrido"] == 5_700  # 60 puntos × 95
    assert s["margen"] == 38_000
    assert s["nocional"] == 380_000
    assert s["apalancamiento"] == pytest.approx(0.38)
    assert s["uno_pct_contra"] == 3_800


def test_el_volumen_se_ajusta_al_minimo_y_al_paso_del_broker():
    assert sm.simular(CONTRATO, ESC, 1_000_000, 0.004)["volumen"] == 0.01
    assert sm.simular(CONTRATO, ESC, 1_000_000, 0.237)["volumen"] == pytest.approx(0.23)


def test_un_monto_cero_no_rompe_la_simulacion():
    assert sm.simular(CONTRATO, ESC, 0, 0.10)["apalancamiento"] is None


# ───────────────────────────────────────────────────────────── WhatsApp


def _pieza_whatsapp() -> dict:
    return {
        "datos": {"nombre": "Oro", "ticker_visible": "XAU/USD", "precio": "4.000,00",
                  "direccion": "Alcista", "temporalidad": sm.TEMPORALIDAD, "datos_al": "lunes 12-10 · 09:30 CLT",
                  "escenario": {"fmt": {"gatillo": "4.030,00", "invalidacion": "3.880,00", "recorrido": "60,00"},
                                "sesgo": "Alcista"}},
        "editorial": {"whatsapp": "El oro empieza la semana sostenido por la baja de las tasas reales."},
    }


def test_el_mensaje_de_whatsapp_destaca_en_negrita_precio_y_niveles():
    texto = sm.mensaje_whatsapp(_pieza_whatsapp())
    for cifra in ("4.000,00", "4.030,00", "3.880,00", "60,00"):
        assert f"*{cifra}*" in texto
    assert "El oro empieza la semana" in texto
    assert sm.TEMPORALIDAD in texto
    assert "lunes 12-10" in texto
    assert "—" not in texto and "–" not in texto


def test_el_mensaje_de_whatsapp_lleva_el_aviso_y_no_recomienda():
    texto = sm.mensaje_whatsapp(_pieza_whatsapp()).lower()
    assert "no constituye recomendación" in texto
    assert "recomend" not in texto.replace("no constituye recomendación", "")


# ───────────────────────────────────────────────────────────── gráfico


def test_el_grafico_dibuja_los_niveles_del_escenario():
    pytest.importorskip("PIL")  # el módulo del gráfico lo importa; viene con el extra `informe`
    from tradingview_grafico import calcular_indicadores, construir_html_tradingview

    filas = [{"time": 1_760_000_000 + i * 86_400, "open": 4000 + i, "high": 4010 + i,
              "low": 3990 + i, "close": 4000 + i, "tick_volume": 1} for i in range(80)]
    html = construir_html_tradingview(
        calcular_indicadores(filas), "Oro", "D1", 2,
        niveles=[{"precio": 4100.0, "rol": "SE ACTIVA", "color": "#00DC82"},
                 {"precio": 3950.0, "rol": "SE ANULA", "color": "#E84040"}],
    )
    datos = json.loads(re.search(r"const D = (\{.*?\});", html, re.S).group(1).replace("<\\/", "</"))
    assert [n["rol"] for n in datos["niveles"]] == ["SE ACTIVA", "SE ANULA"]
    assert "D.niveles.forEach" in html


# ───────────────────────────────────────────────────────────── registro


def _entrada(dir_pedido: Path, ticker: str = "XAUUSD", semana: str = "2026-10-12") -> dict:
    (dir_pedido / "pieza.json").parent.mkdir(parents=True, exist_ok=True)
    (dir_pedido / "pieza.json").write_text("{}", encoding="utf-8")
    return {"semana": semana, "ticker": ticker, "dir": str(dir_pedido), "analista": "111",
            "creada": "2026-10-12T09:30:00-03:00",
            "escenario": {"sesgo": "Alcista", "gatillo": 4030.0, "invalidacion": 3880.0,
                          "recorrido": 60.0, "precio": 4000.0, "vela": "2026-10-09 00:00:00"}}


def test_la_pieza_de_la_semana_se_reusa_por_activo(tmp_path):
    from analista import registro_semanal as rs

    ruta = tmp_path / "registro.json"
    assert rs.vigente("2026-10-12", "XAUUSD", ruta) is None
    rs.anotar(_entrada(tmp_path / "p1"), ruta)
    vig = rs.vigente("2026-10-12", "XAUUSD", ruta)
    assert vig["version"] == 1 and vig["estado"] == "vigente"
    assert rs.vigente("2026-10-12", "USDCLP", ruta) is None
    # La semana siguiente es otra pieza.
    assert rs.vigente("2026-10-19", "XAUUSD", ruta) is None


def test_una_pieza_invalidada_deja_de_entregarse_y_la_siguiente_es_version_2(tmp_path):
    from analista import registro_semanal as rs

    ruta = tmp_path / "registro.json"
    rs.anotar(_entrada(tmp_path / "p1"), ruta)
    rs.marcar("2026-10-12", "XAUUSD", 1, "invalidada", ruta)
    assert rs.vigente("2026-10-12", "XAUUSD", ruta) is None
    rs.anotar(_entrada(tmp_path / "p2"), ruta)
    assert rs.vigente("2026-10-12", "XAUUSD", ruta)["version"] == 2
    # El registro conserva las dos: es historia de lo que circuló.
    assert len(json.loads(ruta.read_text(encoding="utf-8"))) == 2


def test_una_carpeta_borrada_no_se_entrega_como_vigente(tmp_path):
    from analista import registro_semanal as rs

    ruta = tmp_path / "registro.json"
    rs.anotar(_entrada(tmp_path / "p1"), ruta)
    (tmp_path / "p1" / "pieza.json").unlink()
    assert rs.vigente("2026-10-12", "XAUUSD", ruta) is None
