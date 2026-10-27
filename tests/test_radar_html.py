"""Tests para el orden de filas y generación de la página HTML del radar multifractal."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.tori.radar import Evento, LecturaMarco, LineaRadar
from scripts.radar_html import Escaneo, Falla, Fila, ordenar, render, render_error

SANTIAGO = ZoneInfo("America/Santiago")


def _lectura(
    marco: str,
    eventos: tuple[Evento, ...] = (),
    direccion: str = "ALCISTA",
) -> LecturaMarco:
    return LecturaMarco(
        marco=marco,
        estado="TENDENCIA",
        direccion=direccion,
        lineas=(),
        eventos=eventos,
        avisos=(),
        vela=1700000000,
        atr=10.0,
    )


def test_las_filas_sin_eventos_no_aparecen():
    ev = Evento("H4", "seguridad", "toco", None, 0.1, 2650.0, "A+", "rebote")
    f_con_ev = Fila(
        ticker="XAUUSD",
        categoria="Metales",
        digits=2,
        marcos={"H4": _lectura("H4", (ev,))},
        cierres={"H4": datetime(2026, 10, 26, 7, 0, tzinfo=SANTIAGO)},
    )
    f_sin_ev = Fila(
        ticker="EURUSD",
        categoria="Forex",
        digits=4,
        marcos={"H4": _lectura("H4", ())},
        cierres={"H4": datetime(2026, 10, 26, 7, 0, tzinfo=SANTIAGO)},
    )

    ordenadas = ordenar([f_con_ev, f_sin_ev])
    assert len(ordenadas) == 1
    assert ordenadas[0].ticker == "XAUUSD"

    # En el HTML resultante tampoco debe aparecer la fila sin eventos en la tabla
    esc = Escaneo(
        inicio=datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO),
        duracion_s=1.2,
        cuenta=51257,
        leidos=2,
        filas=tuple(ordenadas),
        fallas=(),
        paridad=(),
    )
    html = render(esc)
    assert "XAUUSD" in html
    assert "EURUSD" not in html


def test_tres_marcos_van_antes_que_dos_y_toco_antes_que_por_tocar():
    ev_toco = Evento("H4", "seguridad", "toco", None, 0.1, 100.0, "A+", "rebote")
    ev_pt1 = Evento("H1", "seguridad", "por_tocar", 1, 0.5, 100.0, "A+", "")
    ev_pt3 = Evento("H1", "seguridad", "por_tocar", 3, 1.2, 100.0, "A+", "")

    cierre = datetime(2026, 10, 26, 7, 0, tzinfo=SANTIAGO)
    cierres = {"H1": cierre, "H4": cierre, "D1": cierre}

    # Fila 1: 3 marcos con eventos
    f1 = Fila(
        ticker="TRES_MARCOS",
        categoria="Cat",
        digits=2,
        marcos={
            "H1": _lectura("H1", (ev_pt3,)),
            "H4": _lectura("H4", (ev_pt3,)),
            "D1": _lectura("D1", (ev_pt3,)),
        },
        cierres=cierres,
    )
    # Fila 2: 2 marcos con eventos, uno es "toco"
    f2 = Fila(
        ticker="DOS_CON_TOCO",
        categoria="Cat",
        digits=2,
        marcos={
            "H1": _lectura("H1", (ev_toco,)),
            "H4": _lectura("H4", (ev_pt3,)),
        },
        cierres=cierres,
    )
    # Fila 3: 2 marcos con eventos, solo por tocar, menor velas = 1
    f3 = Fila(
        ticker="DOS_PT_1VELA",
        categoria="Cat",
        digits=2,
        marcos={
            "H1": _lectura("H1", (ev_pt1,)),
            "H4": _lectura("H4", (ev_pt3,)),
        },
        cierres=cierres,
    )
    # Fila 4: 2 marcos con eventos, solo por tocar, menor velas = 3
    f4 = Fila(
        ticker="DOS_PT_3VELAS",
        categoria="Cat",
        digits=2,
        marcos={
            "H1": _lectura("H1", (ev_pt3,)),
            "H4": _lectura("H4", (ev_pt3,)),
        },
        cierres=cierres,
    )

    ordenadas = ordenar([f4, f2, f1, f3])
    tickers = [f.ticker for f in ordenadas]
    assert tickers == ["TRES_MARCOS", "DOS_CON_TOCO", "DOS_PT_1VELA", "DOS_PT_3VELAS"]


def test_el_valor_respeta_digits_sin_truncar_ceros():
    ev = Evento("H4", "seguridad", "toco", None, 0.1, 1.5, "A+", "rebote")
    fila = Fila(
        ticker="TEST_DIGITS",
        categoria="Cat",
        digits=2,
        marcos={"H4": _lectura("H4", (ev,))},
        cierres={"H4": datetime(2026, 10, 26, 7, 0, tzinfo=SANTIAGO)},
    )
    esc = Escaneo(
        inicio=datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO),
        duracion_s=1.0,
        cuenta=51257,
        leidos=1,
        filas=(fila,),
        fallas=(),
        paridad=(),
    )
    html = render(esc)
    assert "1.50" in html


def test_mas_de_la_mitad_de_fallas_muestra_aviso_de_lectura_incompleta():
    aviso = "Lectura incompleta: no confíes en la ausencia de un activo"
    esc_alerta = Escaneo(
        inicio=datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO),
        duracion_s=1.0,
        cuenta=51257,
        leidos=10,
        filas=(),
        fallas=tuple(Falla(f"TICKER_{i}", None, "error") for i in range(6)),  # 6 de 10 > 50%
        paridad=(),
    )
    html_alerta = render(esc_alerta)
    assert aviso in html_alerta

    esc_ok = Escaneo(
        inicio=datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO),
        duracion_s=1.0,
        cuenta=51257,
        leidos=10,
        filas=(),
        fallas=tuple(Falla(f"TICKER_{i}", None, "error") for i in range(2)),  # 2 de 10 <= 50%
        paridad=(),
    )
    html_ok = render(esc_ok)
    assert aviso not in html_ok


def test_cero_actividad_dice_cuantos_se_leyeron():
    esc = Escaneo(
        inicio=datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO),
        duracion_s=2.5,
        cuenta=51257,
        leidos=137,
        filas=(),
        fallas=(),
        paridad=(),
    )
    html = render(esc)
    assert "137 leídos · 0 con actividad" in html


def test_la_celda_muestra_la_hora_de_su_vela():
    cierre_mismo_dia = datetime(2026, 10, 26, 6, 0, tzinfo=SANTIAGO)
    cierre_otro_dia = datetime(2026, 10, 25, 17, 0, tzinfo=SANTIAGO)

    ev1 = Evento("H1", "seguridad", "toco", None, 0.1, 100.0, "A+", "rebote")
    ev2 = Evento("D1", "seguridad", "toco", None, 0.1, 100.0, "A+", "rebote")

    fila = Fila(
        ticker="HORAS_TEST",
        categoria="Cat",
        digits=2,
        marcos={
            "H1": _lectura("H1", (ev1,)),
            "D1": _lectura("D1", (ev2,)),
        },
        cierres={
            "H1": cierre_mismo_dia,
            "D1": cierre_otro_dia,
        },
    )
    esc = Escaneo(
        inicio=datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO),
        duracion_s=1.0,
        cuenta=51257,
        leidos=1,
        filas=(fila,),
        fallas=(),
        paridad=(),
    )
    html = render(esc)
    assert "06:00" in html
    assert "17:00" in html
    assert "25-10" in html


def test_render_error():
    inicio = datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO)
    html = render_error("Error de cuenta", "La cuenta 12345 no coincide con la configurada", inicio)
    assert "Error de cuenta" in html
    assert "La cuenta 12345 no coincide con la configurada" in html
