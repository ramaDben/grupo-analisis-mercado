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


# ───────────────────────────────────────────────────────────── /semanal

AHORA = datetime(2026, 10, 8, 11, 0, tzinfo=SCL)
AGENDA = [
    {"fecha": "2026-10-08", "hora": "09:30", "pais": "United States", "evento": "CPI",
     "nombre_es": "Inflación (IPC)", "explicacion": "", "consenso": "0.3%", "anterior": "0.2%",
     "actual": "0.4%", "resultado": "peor"},
    {"fecha": "2026-10-09", "hora": "10:00", "pais": "United States", "evento": "Michigan",
     "nombre_es": "Confianza del consumidor de Michigan", "explicacion": "", "consenso": "55.0",
     "anterior": "54.2", "actual": "", "resultado": ""},
    # De la semana siguiente: no entra.
    {"fecha": "2026-10-14", "hora": "09:30", "pais": "United States", "evento": "PPI",
     "nombre_es": "Precios al productor", "explicacion": "", "consenso": "", "anterior": "",
     "actual": "", "resultado": ""},
]


def _lectores_semanal(**cambios):
    from analista import preparar as pr

    df = _serie(400)
    precio = float(df["close"].iat[-1])
    graficos = []

    def grafico(ticker, nombre, digits, niveles, destino):
        graficos.append(niveles)
        destino.write_bytes(b"\x89PNG")
        return destino

    base = dict(
        d1=lambda t: _d1(precio, precio - 50, r1=precio + 30, s1=precio - 60),
        serie_d1=lambda t: df,
        contrato=lambda t, p: dict(CONTRATO),
        grafico_d1=grafico,
        catalogo=lambda t: {"ticker": t, "nombre": "Oro", "categoria": "commodity", "digits": 2,
                            "unidad": "USD", "imagen": "assets/activos/oro.jpg"},
        agenda_semana=lambda a: (list(AGENDA), []),
        curva=lambda: ({"series": {"DGS10": {"nivel_pct": 4.1, "delta_1d_bps": -3, "delta_5d_bps": -12}}}, []),
        drivers=lambda t: ["Dólar global (DXY)", "Tasas reales de EE.UU."],
        cuenta=lambda: None,
    )
    base.update(cambios)
    lec = pr.Lectores(**base)
    lec._graficos = graficos  # para inspeccionar los niveles pedidos al gráfico
    return lec


def test_semanal_se_pide_como_el_activo():
    from analista import orden as od

    universo = [{"ticker": "XAUUSD", "nombre": "Oro"}]
    assert od.interpretar("/semanal oro", universo) == od.Orden("semanal", {"ticker": "XAUUSD"})
    with pytest.raises(od.PedidoInvalido):
        od.interpretar("/semanal", universo)


def test_la_pieza_semanal_trae_escenario_simulacion_y_contexto_de_la_semana(tmp_path):
    from analista import esquema as es
    from analista import preparar as pr
    from analista.orden import Orden

    lec = _lectores_semanal()
    hecha = pr.preparar(Orden("semanal", {"ticker": "XAUUSD"}), tmp_path, AHORA, lec)
    d = hecha.pieza["datos"]
    assert d["chip"] == "ESCENARIO DE LA SEMANA · COMMODITIES"
    assert d["semana"] == "2026-10-05" and d["ticker_visible"] == "XAU/USD"
    assert d["temporalidad"] == sm.TEMPORALIDAD and d["por_que_1d"] == sm.POR_QUE_1D
    assert d["escenario"]["hay_escenario"] and d["escenario"]["estado"] == "armado"
    assert d["contrato"]["clp_unidad"] == 950.0
    assert d["simulacion_base"]["volumen"] == CONTRATO["vol_min"]
    agenda = d["contexto"]["agenda_semana"]
    assert len(agenda) == 2 and "salió 0,4%" in agenda[0] and "Michigan" in agenda[1]
    assert d["contexto"]["curva_tasas"][0][3] == "-12 pb"  # el delta a 5 días
    assert d["contexto"]["drivers_del_activo"]
    assert "variacion_semana" in d["contexto"]
    # El gráfico diario lleva los niveles del escenario con nombre.
    assert [n["rol"] for n in lec._graficos[0]] == ["SE ACTIVA", "SE ANULA"]
    assert (tmp_path / "grafico.png").exists()
    assert set(hecha.pieza["editorial"]) == set(es.CAMPOS["semanal"])


def test_sin_escenario_la_pieza_semanal_no_se_arma(tmp_path):
    from analista import preparar as pr
    from analista.orden import Orden

    df = _serie(400)
    precio = float(df["close"].iat[-1])
    lec = _lectores_semanal(d1=lambda t: _d1(precio, precio - 50, r1=precio + 30, s1=precio - 60, origen="atr"))
    with pytest.raises(pr.SinEscenarioError):
        pr.preparar(Orden("semanal", {"ticker": "XAUUSD"}), tmp_path, AHORA, lec)


def test_el_texto_semanal_no_puede_recomendar_ni_prometer(tmp_path):
    from analista import esquema as es
    from analista import preparar as pr
    from analista.orden import Orden

    pieza = pr.preparar(Orden("semanal", {"ticker": "XAUUSD"}), tmp_path, AHORA, _lectores_semanal()).pieza
    pieza["editorial"] = {
        "titular": "El oro llega a la semana con impulso",
        "bajada": "La inflación de Estados Unidos marcó el tono.",
        "contexto_semana": "Es una oportunidad que no se repite.",
        "que_lo_mueve": "La acción recomendada por el equipo.",
        "whatsapp": "Si hubieras entrado el lunes ya ganarías.",
    }
    errores = " ".join(es.errores(pieza))
    assert "oportunidad" in errores and "recomendad" in errores and "si hubieras" in errores


# ───────────────────────────────────────────────────────────── seguimiento

ESC_ALZA = {"sesgo": "Alcista", "estado": "armado", "precio": 4000.0, "entrada": 4030.0,
            "gatillo": 4030.0, "invalidacion": 3880.0, "recorrido": 60.0, "vela": "2026-10-09 00:00:00",
            "fmt": {"precio": "4.000,00", "gatillo": "4.030,00", "invalidacion": "3.880,00", "recorrido": "60,00"}}


def _velas(*filas):
    return pd.DataFrame([{"time": pd.Timestamp("2026-10-12") + pd.Timedelta(days=i),
                          "open": c, "high": h, "low": l, "close": c} for i, (c, h, l) in enumerate(filas)])


def test_sin_cierre_sobre_el_gatillo_el_escenario_sigue_vigente():
    ev = sm.evaluar(ESC_ALZA, _velas((4020, 4029, 4000)), 4025.0)
    assert ev["estado"] == "vigente" and ev["avance_pct"] is None


def test_un_cierre_sobre_el_gatillo_lo_activa_y_mide_el_avance_desde_ahi():
    ev = sm.evaluar(ESC_ALZA, _velas((4040, 4045, 4010)), 4060.0)
    assert ev["estado"] == "avanzando" and ev["entrada"] == 4030.0
    assert ev["avance_pct"] == 50  # 30 de 60


def test_tocar_el_recorrido_completa_el_escenario():
    ev = sm.evaluar(ESC_ALZA, _velas((4040, 4045, 4010), (4080, 4095, 4050)), 4085.0)
    assert ev["estado"] == "completado" and ev["avance_pct"] == 100


def test_un_cierre_bajo_la_invalidacion_lo_anula_aunque_no_se_haya_activado():
    ev = sm.evaluar(ESC_ALZA, _velas((3870, 3990, 3860)), 3875.0)
    assert ev["estado"] == "invalidado"


def test_empate_en_la_misma_vela_cuenta_como_invalidacion():
    esc = {**ESC_ALZA, "estado": "activado", "entrada": 4000.0}
    # Toca el recorrido (4.060) y cierra bajo la invalidación en la misma vela.
    ev = sm.evaluar(esc, _velas((3870, 4070, 3860)), 3875.0)
    assert ev["estado"] == "invalidado"


def test_el_precio_de_ahora_puede_completar_el_escenario_activado():
    esc = {**ESC_ALZA, "estado": "activado", "entrada": 4000.0}
    assert sm.evaluar(esc, _velas(), 4061.0)["estado"] == "completado"


def test_bajista_es_el_espejo():
    esc = {"sesgo": "Bajista", "estado": "armado", "precio": 4000.0, "entrada": 3970.0, "gatillo": 3970.0,
           "invalidacion": 4120.0, "recorrido": 60.0}
    assert sm.evaluar(esc, _velas((3960, 3990, 3955)), 3940.0)["avance_pct"] == 50
    assert sm.evaluar(esc, _velas((4130, 4140, 3990)), 4130.0)["estado"] == "invalidado"


@pytest.mark.parametrize("estado", sm.ESTADOS)
def test_los_cuatro_estados_se_cuentan_igual_y_ninguno_vende(estado):
    ev = {"estado": estado, "avance_pct": 50 if estado == "avanzando" else None}
    t = sm.textos_seguimiento(ESC_ALZA, ev, 4060.0, 2, "XAUUSD", "2026-10-14")
    assert sm.SELLOS[estado] in t["estado"] and "*4.060,00*" in t["estado"]
    plano = t["estado"].lower()
    assert not any(f in plano for f in ("hubieras", "ganar", "ganancia", "oportunidad"))


def _lectores_seguimiento(tmp_path, precio=4060.0, **cambios):
    base_dir = tmp_path / "lunes"
    base_dir.mkdir()
    (base_dir / "pieza.json").write_text(json.dumps({
        "datos": {"escenario": ESC_ALZA, "digits": 2, "ticker_visible": "XAU/USD", "nombre": "Oro"},
        "editorial": {"contexto_semana": "La semana gira en torno a la inflación de EE.UU."},
    }), encoding="utf-8")
    graficos = []

    def grafico(ticker, nombre, digits, niveles, destino):
        graficos.append(niveles)
        destino.write_bytes(b"\x89PNG")
        return destino

    lec = _lectores_semanal(**{
        "semanal_vigente": lambda s, t: {"dir": str(base_dir), "version": 1, "ticker": t} if t == "XAUUSD" else None,
        "serie_d1": lambda t: _velas((4040, 4045, 4010)),
        "precio_vivo": lambda t: precio,
        "grafico_h1": grafico,
        "jornada": lambda a: ([AGENDA[1]], []),
        **cambios,
    })
    lec._graficos = graficos
    return lec


def test_el_seguimiento_mide_contra_la_foto_del_lunes_y_trae_lo_de_hoy(tmp_path):
    from analista import esquema as es
    from analista import preparar as pr
    from analista.orden import Orden

    lec = _lectores_seguimiento(tmp_path)
    pieza = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA, lec).pieza
    d = pieza["datos"]
    assert d["evaluacion"]["estado"] == "avanzando"
    assert d["chip"] == "SEGUIMIENTO · AVANZANDO"
    assert d["precio_lunes"] == "4.000,00" and d["precio_hoy"] == "4.060,00"
    assert d["contexto"]["agenda_hoy"] and "Michigan" in d["contexto"]["agenda_hoy"][0]
    assert d["contexto"]["curva_tasas"][0][2] == "-3 pb"  # el cambio de hoy, no el de la semana
    assert d["contexto"]["contexto_lunes"].startswith("La semana gira")
    assert set(pieza["editorial"]) == set(es.CAMPOS["seguimiento"])


def test_sin_pieza_de_la_semana_el_seguimiento_dice_como_pedirla(tmp_path):
    from analista import preparar as pr
    from analista.orden import Orden

    lec = _lectores_seguimiento(tmp_path, semanal_vigente=lambda s, t: None)
    with pytest.raises(pr.SinPiezaSemanalError, match="/semanal xauusd"):
        pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA, lec)


def test_el_mensaje_de_seguimiento_lleva_estado_lo_de_hoy_y_aviso(tmp_path):
    from analista import preparar as pr
    from analista.orden import Orden

    pieza = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA,
                        _lectores_seguimiento(tmp_path)).pieza
    pieza["editorial"]["hoy"] = "Hoy se espera la confianza del consumidor de Michigan."
    texto = sm.mensaje_seguimiento(pieza)
    assert "*AVANZANDO*" in texto and "Michigan" in texto and "*4.000,00*" in texto
    assert "no constituye recomendación" in texto.lower()


# ───────────────────────────────────────────────────────────── correo

TEXTOS_SEMANAL = {
    "titular": "El oro llega a la semana con la tendencia diaria a favor",
    "bajada": "La inflación de Estados Unidos marcó el tono de los primeros días.",
    "contexto_semana": "La inflación de Estados Unidos salió 0,4%, sobre lo esperado.\n\n"
                       "El viernes llega la confianza del consumidor de Michigan.",
    "que_lo_mueve": "• Tasas reales: el bono a 10 años cae 12 pb en la semana y eso sostiene al oro.\n"
                    "• Dólar global: si se fortalece, el oro tiende a ceder.",
    "whatsapp": "El oro empieza la semana sostenido por la baja de las tasas reales.",
}


def _pieza_semanal_redactada(tmp_path):
    from analista import esquema as es
    from analista import preparar as pr
    from analista.orden import Orden

    pieza = pr.preparar(Orden("semanal", {"ticker": "XAUUSD"}), tmp_path, AHORA, _lectores_semanal()).pieza
    pieza["editorial"] = dict(TEXTOS_SEMANAL)
    assert es.errores(pieza) == []
    return pieza


def test_el_correo_es_de_tablas_en_linea_y_destaca_las_cifras(tmp_path):
    import analista_fixtures as fx
    from analista import correo as co

    pieza = _pieza_semanal_redactada(tmp_path)
    html = co.armar(pieza, tmp_path, fx.ANALISTA, fx.AUTOR)
    correo = html[html.index('<table id="email-root"'):html.index('<script id="simulador">')]
    assert "<link" not in html and "var(--" not in correo and "{{" not in html
    assert 'width="640"' in correo
    f = pieza["datos"]["escenario"]["fmt"]
    for cifra in (pieza["datos"]["precio"], f["gatillo"], f["invalidacion"], f["recorrido"]):
        assert re.search(rf"<strong[^>]*>{re.escape(cifra)}", correo), cifra
    # La línea de marca: Goldman en titulares y cifras, Jakarta en el cuerpo, escritas en cada elemento.
    assert "font-family:'Goldman'" in correo and "font-family:'Plus Jakarta Sans'" in correo
    assert "data:font/woff2;base64," in html[:html.index("<body")]
    assert 'id="v-perdida"' in correo and 'id="v-recorrido"' in correo
    assert "Simulación realizada por Camila Rojas" in correo
    assert "Análisis de Benjamín" in correo and "Te lo envía" in correo
    assert "no constituye" in correo.lower()
    assert sm.TEMPORALIDAD in correo and "Por qué 1D" in correo
    assert "data:image/png;base64," in correo  # logo y gráfico van adentro


def test_la_simulacion_del_panel_calcula_igual_que_python(tmp_path):
    import shutil
    import subprocess

    import analista_fixtures as fx
    from analista import correo as co

    node = shutil.which("node")
    if not node:
        pytest.skip("sin node para correr el JavaScript del panel")
    pieza = _pieza_semanal_redactada(tmp_path)
    html = co.armar(pieza, tmp_path, fx.ANALISTA, fx.AUTOR)
    js = re.search(r'<script id="simulador">(.*?)</script>', html, re.S).group(1)
    esc, contrato = pieza["datos"]["escenario"], pieza["datos"]["contrato"]
    for monto, volumen in ((1_000_000, 0.10), (250_000, 0.237), (0, 0.004)):
        llamada = (f"console.log(JSON.stringify(simular({json.dumps(contrato)}, {json.dumps(esc)}, "
                   f"{monto}, {volumen})))")
        salida = subprocess.run([node, "-e", js + "\n" + llamada], capture_output=True, text=True, check=True)
        assert json.loads(salida.stdout) == sm.simular(contrato, esc, monto, volumen)


# ───────────────────────────────────────────────────────────── el bot


class _TgFalso:
    def __init__(self):
        self.enviados = []

    def mensaje(self, chat, texto):
        self.enviados.append(("mensaje", texto))

    def documento(self, chat, ruta):
        self.enviados.append(("documento", Path(ruta).name))

    def foto(self, chat, ruta):
        self.enviados.append(("foto", Path(ruta).name))


def _atendedor(tmp_path, lectores=None, textos=None):
    import analista_fixtures as fx
    from analista import bot as b
    from analista import preparar as pr

    llamadas = []
    estado = {"lec": lectores or _lectores_semanal()}

    def preparar(orden, dir_pedido, ahora):
        return pr.preparar(orden, dir_pedido, ahora, estado["lec"])

    def redactar(ruta, tier):
        llamadas.append(ruta)
        pieza = pr.cargar_pieza(ruta.parent)
        if pieza["orden"]["pieza"] == "semanal":
            pieza["editorial"] = dict(textos or TEXTOS_SEMANAL)
        else:
            pieza["editorial"] = {"hoy": "Hoy el mercado espera la confianza del consumidor de Michigan."}
        pr.guardar_pieza(pieza, ruta.parent)
        return type("R", (), {"codigo": "ok"})()

    def imagen(pieza, dir_pedido, autor):
        (dir_pedido / "imagen.png").write_bytes(fx.PNG)
        return dir_pedido / "imagen.png"

    config = {"analistas": {"111": {**fx.ANALISTA, "cupo_diario": 5}}, "reuso_minutos": dict(b.REUSO_MINUTOS),
              "tier": "flash", "ruta_drive": str(tmp_path / "drive")}
    at = b.Atendedor(config, b.Estado.cargar(tmp_path / "estado.json"), autor=fx.AUTOR, preparar=preparar,
                     redactar=redactar, reloj=lambda: AHORA, dir_pedidos=tmp_path / "pedidos",
                     bitacora=tmp_path / "bitacora.json", registro_semanal=tmp_path / "registro.json",
                     rendir_imagen=imagen)
    return at, llamadas, estado


def test_semanal_entrega_imagen_como_foto_correo_y_el_texto_aparte(tmp_path):
    from analista import bot as b
    from analista.orden import Orden

    at, llamadas, _ = _atendedor(tmp_path)
    r = at.atender(b.Pedido("111", 9, Orden("semanal", {"ticker": "XAUUSD"})))
    assert [p.suffix for p in r.archivos] == [".png", ".html"]
    assert len(r.mensajes) == 1 and "*" in r.mensajes[0] and "Escenario de la semana" in r.mensajes[0]
    tg = _TgFalso()
    b.entregar(tg, r)
    assert [t for t, _ in tg.enviados] == ["mensaje", "foto", "documento", "mensaje"]
    # Drive: la carpeta de la semana y el activo, con las tres salidas.
    carpeta = tmp_path / "drive" / "GI Semanal" / "2026-10-05" / "oro"
    assert sorted(p.suffix for p in carpeta.iterdir()) == [".html", ".png", ".txt"]
    # Segunda petición en la semana: se reusa sin redactar ni gastar cupo.
    r2 = at.atender(b.Pedido("111", 9, Orden("semanal", {"ticker": "XAUUSD"})))
    assert len(llamadas) == 1 and "vigente de la semana" in r2.texto
    assert at.estado.usados("111", AHORA) == 1


def test_un_seguimiento_invalidado_retira_la_pieza_y_la_siguiente_es_version_2(tmp_path):
    from analista import bot as b
    from analista import registro_semanal as rs
    from analista.orden import Orden

    registro = tmp_path / "registro.json"
    at, _, estado = _atendedor(tmp_path)
    at.atender(b.Pedido("111", 9, Orden("semanal", {"ticker": "XAUUSD"})))
    vig = rs.vigente("2026-10-05", "XAUUSD", registro)
    inval = vig["escenario"]["invalidacion"]
    vela = pd.Timestamp(vig["escenario"]["vela"]) + pd.Timedelta(days=1)
    caida = pd.DataFrame([{"time": vela, "open": inval, "high": inval + 1, "low": inval - 20, "close": inval - 10}])

    def grafico(ticker, nombre, digits, niveles, destino):
        destino.write_bytes(b"\x89PNG")
        return destino

    estado["lec"] = _lectores_semanal(semanal_vigente=lambda s, t: rs.vigente(s, t, registro),
                                      serie_d1=lambda t: caida, precio_vivo=lambda t: inval - 10,
                                      grafico_h1=grafico, jornada=lambda a: ([], []))
    r = at.atender(b.Pedido("111", 9, Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert "*INVALIDADO*" in r.mensajes[0] and "versión 2" in r.texto
    assert rs.vigente("2026-10-05", "XAUUSD", registro) is None
    historia = json.loads(registro.read_text(encoding="utf-8"))[0]
    assert historia["estado"] == "invalidada" and historia["seguimientos"][0]["estado"] == "invalidado"


def test_un_texto_que_vende_no_se_entrega(tmp_path):
    from analista import bot as b
    from analista.orden import Orden

    at, _, _ = _atendedor(tmp_path, textos={**TEXTOS_SEMANAL, "whatsapp": "Una oportunidad para la semana."})
    with pytest.raises(b.FalloPedido, match="oportunidad"):
        at.atender(b.Pedido("111", 9, Orden("semanal", {"ticker": "XAUUSD"})))


# ───────────────────────────────────────────────────────────── temáticas del lunes


def test_indices_etf_y_acciones_se_piden_como_tematica():
    from analista import orden as od

    assert od.interpretar("/semanal etf", []) == od.Orden("semanal", {"tematica": "etf"})
    assert od.interpretar("/semanal Índices", []) == od.Orden("semanal", {"tematica": "indices"})
    assert od.interpretar("/seguimiento acciones", []) == od.Orden("seguimiento", {"tematica": "acciones"})


def test_la_tematica_elige_el_escenario_mas_claro_y_salta_los_que_no_tienen():
    df = _serie(400)
    precio = float(df["close"].iat[-1])
    base = {"ema_20": precio - 5, "ema_100": precio - 80, "adx_14": 30, "rsi_14": 60, "macd_hist": 1.0}
    lecturas = {
        # Sin estructura medible: no compite.
        "SPY.US": {**_d1(precio, precio - 50, r1=precio + 30, s1=precio - 60, origen="atr"), **base},
        # Con escenario, pero sin momentum (ADX bajo): menos puntos.
        "QQQ.US": {**_d1(precio, precio - 50, r1=precio + 10, s1=precio - 60), **base, "adx_14": 10},
        "GLD.US": {**_d1(precio, precio - 50, r1=precio + 30, s1=precio - 60), **base},
        "IWM.US": "rompe",  # datos rotos: se salta sin tumbar a los demás
    }

    def leer_d1(t):
        if lecturas[t] == "rompe":
            raise RuntimeError("sin datos")
        return lecturas[t]

    universo = [{"ticker": t, "digits": 2} for t in lecturas]
    elegido = sm.elegir(universo, leer_d1, lambda t: df)
    assert elegido["ticker"] == "GLD.US" and elegido["evaluados"] == 4
    assert sm.elegir(universo[:1], leer_d1, lambda t: df) is None


def test_la_pieza_de_una_tematica_se_arma_con_la_lectura_que_la_eligio(tmp_path):
    from analista import preparar as pr
    from analista.orden import Orden

    df = _serie(400)
    precio = float(df["close"].iat[-1])
    d1 = _d1(precio, precio - 50, r1=precio + 30, s1=precio - 60)
    lec = _lectores_semanal(
        foco_semanal=lambda tem, ahora: {"ticker": "GLD.US", "d1": d1, "serie": df, "evaluados": 5},
        d1=lambda t: pytest.fail("no se vuelve a leer el activo elegido"),
        catalogo=lambda t: {"ticker": t, "nombre": "ETF de oro", "categoria": "etf", "digits": 2, "unidad": "USD"},
    )
    pieza = pr.preparar(Orden("semanal", {"tematica": "etf"}), tmp_path, AHORA, lec).pieza
    d = pieza["datos"]
    assert d["ticker"] == "GLD.US" and d["chip"] == "ESCENARIO DE LA SEMANA · ETF"
    assert "Elegido entre 5 ETF" in d["seleccion"]["texto"]

    sin = _lectores_semanal(foco_semanal=lambda tem, ahora: None)
    with pytest.raises(pr.SinEscenarioError, match="ETF"):
        pr.preparar(Orden("semanal", {"tematica": "etf"}), tmp_path / "x", AHORA, sin)


def test_la_tematica_se_reusa_en_la_semana_aunque_no_se_sepa_su_activo(tmp_path):
    from analista import bot as b
    from analista import registro_semanal as rs
    from analista.orden import Orden

    df = _serie(400)
    precio = float(df["close"].iat[-1])
    d1 = _d1(precio, precio - 50, r1=precio + 30, s1=precio - 60)
    lec = _lectores_semanal(
        foco_semanal=lambda tem, ahora: {"ticker": "GLD.US", "d1": d1, "serie": df, "evaluados": 5},
        catalogo=lambda t: {"ticker": t, "nombre": "ETF de oro", "categoria": "etf", "digits": 2, "unidad": "USD"},
    )
    at, llamadas, _ = _atendedor(tmp_path, lectores=lec)
    r = at.atender(b.Pedido("111", 9, Orden("semanal", {"tematica": "etf"})))
    assert (tmp_path / "drive" / "GI Semanal" / "2026-10-05" / "etf").is_dir()
    assert rs.vigente_tematica("2026-10-05", "etf", tmp_path / "registro.json")["ticker"] == "GLD.US"
    r2 = at.atender(b.Pedido("111", 9, Orden("semanal", {"tematica": "etf"})))
    assert len(llamadas) == 1 and "vigente de la semana" in r2.texto
    assert "Elegido entre 5 ETF" in r.archivos[1].read_text(encoding="utf-8")
