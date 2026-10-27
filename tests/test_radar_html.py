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


def test_una_falla_en_varios_marcos_cuenta_como_un_simbolo():
    aviso = "Lectura incompleta: no confíes en la ausencia de un activo"
    fallas = (
        Falla("A", "H1", "error"),
        Falla("A", "H4", "error"),
        Falla("A", "D1", "error"),
        Falla("B", "H1", "error"),
        Falla("B", "H4", "error"),
        Falla("B", "D1", "error"),
    )  # 2 simbolos de 10, aunque haya 6 fallas (> 5)
    esc = Escaneo(
        inicio=datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO),
        duracion_s=1.0,
        cuenta=51257,
        leidos=10,
        filas=(),
        fallas=fallas,
        paridad=(),
    )
    assert aviso not in render(esc)


def test_el_texto_visible_dice_control_y_no_seguridad():
    ev = Evento("H4", "seguridad", "toco", None, 0.1, 1.5, "A+", "rebote")
    ev2 = Evento("H1", "seguridad", "por_tocar", 2, 0.5, 1.5, "A+", "")
    fila = Fila(
        ticker="T",
        categoria="Cat",
        digits=2,
        marcos={"H4": _lectura("H4", (ev,)), "H1": _lectura("H1", (ev2,))},
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
    html = render(esc).lower()
    assert "seguridad" not in html
    assert "tocó control" in html
    assert "control a 2 velas" in html
    assert "línea de control" in html


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


# --- lo que la página distingue (spec §2, §5, §6) -------------------------------------------

def _esc(filas=(), fallas=(), paridad=(), avisos=(), leidos=1) -> Escaneo:
    return Escaneo(inicio=datetime(2026, 10, 26, 7, 30, tzinfo=SANTIAGO), duracion_s=1.0,
                   cuenta=51257, leidos=leidos, filas=tuple(filas), fallas=tuple(fallas),
                   paridad=tuple(paridad), avisos=tuple(avisos))


def _celdas(html: str) -> list[str]:
    """Las tres celdas de marco (1H, 4H, 1D) de la única fila de la tabla."""
    fila = html.split("<tr>")[2]
    return fila.split("</td>")[2:5]


def test_el_aviso_de_salto_se_ve_en_su_celda_aunque_no_haya_eventos():
    from estrategia.tori.lectura import AVISO_SALTO
    ev = Evento("H1", "seguridad", "toco", None, 0.1, 100.0, "A+", "rebote")
    aviso = AVISO_SALTO.format(marco="H4")
    h4 = LecturaMarco("H4", "TENDENCIA", "ALCISTA", (), (), (aviso,), 1700000000, 10.0)
    fila = Fila("X", "Forex", 2, {"H1": _lectura("H1", (ev,)), "H4": h4, "D1": _lectura("D1")}, {})
    h1, c4, d1 = _celdas(render(_esc([fila])))
    assert aviso in c4 and 'class="c"' in c4 and "avm" in c4
    assert aviso not in h1
    assert d1.strip().endswith(">·")  # leído y sin nada: el punto de siempre


def test_un_marco_que_no_se_pudo_leer_dice_sin_lectura_y_no_punto():
    ev = Evento("H1", "seguridad", "toco", None, 0.1, 100.0, "A+", "rebote")
    fila = Fila("X", "Forex", 2, {"H1": _lectura("H1", (ev,)), "D1": _lectura("D1")}, {})
    _h1, c4, d1 = _celdas(render(_esc([fila], fallas=[Falla("X", "H4", "H4: 10 velas de 180")])))
    assert "sin lectura" in c4 and "sinlec" in c4
    assert "sin lectura" not in d1 and d1.strip().endswith(">·")


def test_el_evento_muestra_la_distancia_en_atr():
    toco = Evento("H1", "seguridad", "toco", None, 0.1234, 100.0, "A+", "rebote")
    pt = Evento("H4", "accion", "por_tocar", 2, 1.5, 100.0, "B", "")
    fila = Fila("X", "Forex", 2, {"H1": _lectura("H1", (toco,)), "H4": _lectura("H4", (pt,)),
                                  "D1": _lectura("D1")}, {})
    html = render(_esc([fila]))
    assert "✅ tocó control · 100.00 · 0.12 ATR" in html
    assert "acción a 2 velas · 100.00 · 1.50 ATR" in html


def test_las_fallas_se_cuentan_por_activo_y_no_por_marco():
    fallas = [Falla("A", m, "error") for m in ("H1", "H4", "D1")] + [Falla("B", None, "error")]
    html = render(_esc(fallas=fallas, leidos=10))
    assert "2 no se pudieron leer" in html and "4 no se pudieron leer" not in html
    assert "No se pudieron leer (2):" in html
    assert "1 no se pudo leer" in render(_esc(fallas=fallas[:3], leidos=10))


def test_los_avisos_del_escaneo_van_en_el_encabezado_y_no_en_la_paridad():
    aviso = "no se pudo medir el reloj del servidor: las horas de cierre no se muestran"
    html = render(_esc(avisos=[aviso], paridad=["paridad: 1 gráfico comparado, 0 diferencias"]))
    assert html.index(aviso) < html.index("<table>")
    assert html.index(aviso) < html.index("Control de paridad")
    assert "Control de paridad:</b><br>paridad: 1 gráfico comparado, 0 diferencias" in html
