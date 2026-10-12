"""Preparación de las piezas del bot: datos del terminal en la carpeta del pedido."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import registro_semanal as rg  # noqa: E402
from analista import esquema as es  # noqa: E402
from analista import informe_html as ih  # noqa: E402
from analista import preparar as pr  # noqa: E402
from analista.orden import Orden  # noqa: E402
from estrategia.contrato import lectura_a_dict  # noqa: E402
import referencia_semanal as rs  # noqa: E402
from test_pipeline_carrusel import ORO, _lectura_alcista, _sel  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 8, 11, 0, tzinfo=SCL)

JORNADA = [
    {"fecha": "2026-10-08", "hora": "09:30", "pais": "United States", "evento": "Initial Jobless Claims",
     "nombre_es": "Peticiones de subsidio por desempleo", "explicacion": "", "consenso": "200K",
     "anterior": "199K", "actual": "197K", "resultado": "mejor"},
    {"fecha": "2026-10-08", "hora": "14:00", "pais": "United States", "evento": "FOMC Minutes",
     "nombre_es": "Minutas de la Fed", "explicacion": "", "consenso": "", "anterior": "",
     "actual": "", "resultado": ""},
]


def _png(destino: Path) -> Path:
    destino.write_bytes(fx.PNG)
    return destino


ACTIVO = {**ORO, "clase": "forex_commodities"}
SELECCION = _sel(_lectura_alcista())
CIERRES = [4119.0, 4120.0]


def lectores(**cambios) -> pr.Lectores:
    base = dict(
        terminal=lambda t, a: {"ticker": t, "activo": ACTIVO, "seleccion": SELECCION, "cierres": CIERRES},
        grafico_tv=lambda payload, destino: _png(destino),
        jornada=lambda a: (list(JORNADA), []),
        agenda=lambda a: (list(JORNADA), []),
        movimiento=lambda t, d, a: {"desde": 951.2, "ahora": 952.1, "digits": 2, "banda": 0.1},
        activos_jornada=lambda destino: ({
            "USDCLP": {"nombre": "Dólar / Peso Chileno", "digits": 2,
                       "lectura": lectura_a_dict(_lectura_alcista()),
                       "grafico": "graficos/usdclp.png"},
        }, []),
        curva=lambda: ({"series": {"DGS2": {"nivel_pct": 3.61, "delta_1d_bps": 2, "delta_5d_bps": None}}}, []),
        cuenta=lambda: None,
    )
    base.update(cambios)
    return pr.Lectores(**base)


def test_rendir_laminas_pone_el_texto_validado(tmp_path):
    hecha = pr.preparar(Orden("calendario", {"alcance": "hoy"}), tmp_path, AHORA, lectores())
    pieza = hecha.pieza
    pieza["editorial"].update({"titular": "Empleo y Fed", "bajada": "Dos citas para el dólar",
                               "lectura": "Texto de lectura suficiente.",
                               "explicaciones": {"01": "Explicación uno larga.", "02": "Explicación dos larga."}})
    vistos = {}

    def render(tokens, plantilla, destino, formato):
        vistos.update(tokens)
        return _png(destino)

    pr.rendir_laminas(pieza, tmp_path, render=render)
    assert vistos["titulo"] == "Empleo y Fed" and vistos["subtitulo"] == "Dos citas para el dólar"
    assert (tmp_path / "calendario.png").exists()
    # La pieza completa se arma en HTML.
    assert "Empleo y Fed" in ih.armar(pieza, tmp_path, fx.ANALISTA, fx.AUTOR, AHORA.date())


def test_preparar_escribe_solo_en_la_carpeta_del_pedido(tmp_path):
    pedido = tmp_path / "pedido"
    pr.preparar(Orden("activo", {"ticker": "XAUUSD"}), pedido, AHORA, lectores())
    assert {p.relative_to(tmp_path).parts[0] for p in tmp_path.rglob("*")} == {"pedido"}


def test_no_usa_los_preparar_de_produccion():
    fuente = (RAIZ / "scripts" / "analista" / "preparar.py").read_text(encoding="utf-8")
    for prohibido in ("pc.preparar(", "pa.preparar(", "pi.preparar(", "escanear(", "registrar_uso",
                      "escribir_suplementos", "_preparar_resultado", "DIR_TRABAJO"):
        assert prohibido not in fuente, prohibido


# ───────────────────────────────────────────────────────────── la foto semanal

SEMANA = "2026-W42"
AHORA_LUNES = datetime(2026, 10, 12, 9, 30, tzinfo=SCL)


class EstrategiaFalsa:
    nombre = "tori"

    class marcos:
        operativo = "H4"
        etiquetas = {"H4": SimpleNamespace(nombre="swing", duracion="de una a dos semanas")}


def _sembrar(base, lecturas, puntajes):
    for lec in lecturas:
        rs.guardar(lec, SEMANA, "semanal", AHORA_LUNES, base=base)
    rs.guardar_manifiesto(SEMANA, {"semana": SEMANA, "elegidos": [l.ticker for l in lecturas],
                                   "puntajes": puntajes, "excluidos": []}, base=base)


def _grafico_falso(ticker, nombre, lectura, destino):
    destino.write_bytes(fx.PNG)
    return destino


def _lectores(base, filas_estado=None, **kw):
    def estado(_est, semana, _lector, _ahora, _digits, base=base):
        if filas_estado is not None:
            return filas_estado
        return [{"ticker": t, "espera_hasta": None} for t in rs.manifiesto(semana, base)["elegidos"]]
    por_defecto = dict(
        base_referencias=base, estado_semanal=estado, estrategia=lambda: EstrategiaFalsa(),
        contrato=lambda t, p: {"clp_unidad": 950.0, "vol_min": 0.01, "vol_paso": 0.01},
        grafico_lectura=_grafico_falso,
        catalogo=lambda t: {"ticker": t, "nombre": {"XAUUSD": "Oro", "COPPER": "Cobre"}[t],
                            "digits": {"XAUUSD": 2, "COPPER": 0}[t], "unidad": "USD"},
        drivers=lambda t: ["Dollar Index"], agenda=lambda a: ([], []), curva=lambda: ({}, []),
        cuenta=lambda: None)
    return pr.Lectores(**{**por_defecto, **kw})


def test_sin_analisis_semanal_no_hay_pieza(tmp_path):
    with pytest.raises(pr.SinSemanaError, match="análisis semanal"):
        pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(tmp_path / "ref"))


def test_con_una_linea_a_mas_en_prueba_espera_el_cierre(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    filas = [{"ticker": "XAUUSD", "espera_hasta": datetime(2026, 10, 12, 13, 0, tzinfo=SCL)}]
    with pytest.raises(pr.EsperaVelaError, match="13:00"):
        pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base, filas))


def test_la_foto_trae_los_activos_en_orden_de_puntaje(tmp_path):
    base = tmp_path / "ref"
    cobre = fx.lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14500.0,
                       rango=(14567.0, 14206.0), atr=85.86)
    _sembrar(base, [cobre, fx.lectura()], {"XAUUSD": 90.0, "COPPER": 5.0})
    hecha = pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base))
    activos = hecha.pieza["datos"]["activos"]
    assert [a["ticker"] for a in activos] == ["XAUUSD", "COPPER"]
    oro = activos[0]
    assert oro["escenario"]["objetivo"] == 4150.0 and oro["fmt"]["objetivo"] == "4.150,00"
    assert oro["contrato"]["clp_unidad"] == 950.0
    assert oro["temporalidad"] == "4H · swing (de una a dos semanas)"
    assert (tmp_path / "p" / oro["grafico"]).exists()
    assert hecha.pieza["anidados"] == {"titulares": ["XAUUSD", "COPPER"], "contexto": ["XAUUSD", "COPPER"]}
    assert hecha.pieza["datos"]["curva"] == []


def test_la_curva_va_sin_porcentajes(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    curva = ({"series": {"DGS2": {"nivel_pct": 3.61, "delta_1d_bps": 2, "delta_5d_bps": None}}}, [])
    hecha = pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base, curva=lambda: curva))
    filas = hecha.pieza["datos"]["curva"]
    assert filas and "%" not in json.dumps(filas, ensure_ascii=False)


def test_la_foto_no_toca_los_directorios_de_produccion(tmp_path, monkeypatch):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    antes = {p: p.stat().st_mtime for p in (RAIZ / "data").glob("carrusel/**/*") if p.is_file()}
    pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base))
    assert {p: p.stat().st_mtime for p in (RAIZ / "data").glob("carrusel/**/*") if p.is_file()} == antes


# ───────────────────────────────────────────────────────────── seguimiento


def _foto(tmp_path, base, activos):
    """Una foto ya armada en el registro, como la deja /oportunidad."""
    d = tmp_path / "foto"
    d.mkdir()
    p = es.nueva_pieza("oportunidad", {"semana": SEMANA}, {"semana": SEMANA, "activos": activos}, {},
                       extra_campos={"titulares": [a["ticker"] for a in activos],
                                     "contexto": [a["ticker"] for a in activos]})
    pr.guardar_pieza(p, d)
    rg.anotar_foto(SEMANA, d, AHORA_LUNES, [a["ticker"] for a in activos], tmp_path / "registro.json")


def _lectores_seg(tmp_path, base, velas, precio):
    def lector(ticker, marcos, extra=0):
        return {"H4": velas}, None
    lec = _lectores(base, registro=tmp_path / "registro.json", velas=lector)
    lec.lectura_del_dia = lambda est, t, d, sem, lector, base=None: rs.Diaria(
        fx.lectura(precio=precio), None, (), {"H4": velas}, fx.lectura())
    return lec


def test_seguimiento_de_un_activo_fuera_de_la_foto_lista_los_que_si(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    _foto(tmp_path, base, [fx.activo_semanal()])
    with pytest.raises(pr.FueraDeLaFotoError, match="Oro"):
        pr.preparar(Orden("seguimiento", {"ticker": "USDCLP"}), tmp_path / "s", AHORA_LUNES,
                    _lectores_seg(tmp_path, base, pd.DataFrame(), 4000.0))


def test_seguimiento_sin_foto_de_la_semana(tmp_path):
    with pytest.raises(pr.SinFotoError, match="/oportunidad"):
        pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s", AHORA_LUNES,
                    _lectores_seg(tmp_path, tmp_path / "ref", pd.DataFrame(), 4000.0))


def test_seguimiento_informa_simulacion_y_lectura_por_separado(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    oro = fx.activo_semanal()
    _foto(tmp_path, base, [oro])
    foto_vela = oro["lectura"]["vela"]
    velas = pd.DataFrame([{"time": foto_vela, "open": 1, "high": 4300, "low": 3000, "close": 1},  # anterior: no cuenta
                          {"time": foto_vela + 14400, "open": 4180, "high": 4190, "low": 4150, "close": 4160}])
    hecha = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s",
                        datetime(2026, 10, 14, 11, 0, tzinfo=SCL), _lectores_seg(tmp_path, base, velas, 4124.0))
    d = hecha.pieza["datos"]
    assert d["evaluacion"]["estado"] == "en_curso"
    assert "Simulación de la semana" in d["whatsapp"] and "Lectura técnica hoy" in d["whatsapp"]
    assert "$" not in d["whatsapp"]
