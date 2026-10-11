"""Trazado de Tori (doctrina §2.1 y §4, reglas 2, 3 y 6)."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori.lineas import _recorrer, seguimiento, trazar  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402
from estrategia.tori.pivotes import serie_de  # noqa: E402

# Mínimos 100, 106 y 112 alineados (pendiente 0,25 por vela), y un retroceso al final.
ALCISTA = [100, 112, 106, 118, 112, 124, 119]
# Espejo: máximos 124, 118 y 112 alineados, y un tramo final que rompe hacia arriba.
BAJISTA_ROTA = [124, 112, 118, 106, 112, 100]
# Mínimos 100-104-108 alineados, después 116-124 más empinados.
ACELERA = [100, 112, 104, 116, 108, 128, 116, 136, 124]


def _respeta(s, t, tol):
    fin = t.i_ruptura if t.i_ruptura is not None else len(s)
    for i in range(t.i_a, fin):
        if t.sentido == "alcista":
            assert s.lows[i] >= t.valor(i) - tol - 1e-9, f"la vela {i} cruza la línea"
        else:
            assert s.highs[i] <= t.valor(i) + tol + 1e-9, f"la vela {i} cruza la línea"


def test_la_alcista_se_ancla_en_el_minimo_y_junta_los_tres_toques():
    s = serie_de(vs.desde_vertices([130, *ALCISTA], 12))  # el tramo previo confirma el mínimo
    t = trazar(s, "alcista", P)
    assert t is not None and t.i_a == 12 and abs(t.p_a - 99.8) < 1e-9
    assert len(t.toques) >= 3 and t.vigente
    assert abs(t.pendiente - 0.25) < 1e-9
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)


def test_ninguna_vela_cruza_la_linea_elegida_ni_con_una_mecha_suelta():
    df = vs.desde_vertices(ALCISTA, 12)
    # La mecha cae en la vela del tercer toque de la línea limpia (48) y la perfora de
    # verdad: esa línea (0 a 24) debe descartarse y la elegida ya no es la limpia.
    df.loc[48, "low"] = df.loc[48, "low"] - 4.0
    s = serie_de(df)
    t = trazar(s, "alcista", P)
    assert t is not None
    assert t.i_b != 24, "la línea limpia cruzada por la mecha no se descartó"
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)
    assert t.vigente, "una mecha no es ruptura"


def test_el_cierre_al_otro_lado_es_ruptura():
    df = vs.desde_vertices([100, *BAJISTA_ROTA], 12)
    subida = vs.desde_vertices([100, 118], 6, t0=int(df["time"].iloc[-1]) + 4 * 3600)
    s = serie_de(pd.concat([df, subida], ignore_index=True))
    t = trazar(s, "bajista", P)
    assert t is not None and t.i_a == 12 and t.i_ruptura is not None
    assert s.closes[t.i_ruptura] > t.valor(t.i_ruptura)
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)


def test_sin_segundo_punto_no_hay_linea():
    s = serie_de(vs.desde_vertices([120, 100], 24))  # el mínimo es la última vela
    assert trazar(s, "alcista", P) is None


def test_una_linea_plana_no_es_diagonal():
    s = serie_de(vs.desde_vertices([100, 110, 100, 110, 100, 110], 10))
    assert trazar(s, "alcista", P) is None
    assert trazar(s, "bajista", P) is None


def test_el_abanico_arranca_en_el_ultimo_toque_y_es_mas_empinado():
    s = serie_de(vs.desde_vertices(ACELERA, 12))
    principal = trazar(s, "alcista", P)
    assert principal is not None
    seg = seguimiento(s, principal, P)
    assert seg is not None
    assert seg.i_a == principal.toques[-1]  # encadenar: el último toque es el nuevo Punto A
    assert seg.pendiente > principal.pendiente and seg.vigente


def test_sin_aceleracion_no_hay_linea_de_seguimiento():
    # Una principal ya empinada (su Punto B se subió a mano: con velas reales una candidata
    # menos empinada cruzaría la principal) frente a la candidata de ACELERA (0,32).
    s = serie_de(vs.desde_vertices(ACELERA, 12))
    real = trazar(s, "alcista", P)
    principal = replace(real, p_b=real.p_a + 0.5 * (real.i_b - real.i_a))
    cand = trazar(s, "alcista", P, ancla=principal.toques[-1])
    assert cand is not None and cand.vigente
    assert abs(cand.pendiente) <= abs(principal.pendiente)  # la causa es la pendiente
    assert seguimiento(s, principal, P) is None


def test_la_principal_rota_no_tiene_seguimiento():
    s = serie_de(vs.desde_vertices(ACELERA, 12))
    principal = replace(trazar(s, "alcista", P), i_ruptura=100)  # ruptura marcada a mano
    assert not principal.vigente
    cand = trazar(s, "alcista", P, ancla=principal.toques[-1])
    assert cand is not None and cand.vigente  # sin la guarda sí habría línea
    assert seguimiento(s, principal, P) is None


def test_la_secundaria_rota_se_borra():
    df = vs.desde_vertices(ACELERA, 12)
    caida = vs.desde_vertices([124, 119], 4, t0=int(df["time"].iloc[-1]) + 4 * 3600)
    s = serie_de(pd.concat([df, caida], ignore_index=True))
    principal = trazar(s, "alcista", P)
    assert principal is not None and principal.vigente  # cae bajo la de seguimiento, no bajo la principal
    cand = trazar(s, "alcista", P, ancla=principal.toques[-1])
    assert cand is not None and not cand.vigente
    assert seguimiento(s, principal, P) is None


def test_el_toque_se_anota_en_el_extremo_y_no_en_la_primera_vela():
    s = serie_de(vs.desde_vertices([120, *ACELERA], 12))
    principal = trazar(s, "alcista", P)
    assert principal is not None
    assert principal.i_b in principal.toques
    assert principal.toques == (12, 36, 60)  # los mínimos reales, no la vela de entrada (35, 59)


def test_un_toque_partido_en_dos_velas_ancla_el_seguimiento_en_el_extremo():
    df = vs.desde_vertices(ACELERA, 12)
    s0 = serie_de(df)
    base = trazar(s0, "alcista", P)
    # Último toque en dos velas: la 47 entra sobre la línea y la 48 la perfora dentro de la tolerancia.
    df.loc[47, "low"] = base.valor(47) + 0.2 * s0.atr
    df.loc[48, "low"] = base.valor(48) - 0.2 * s0.atr
    s = serie_de(df)
    principal = trazar(s, "alcista", P)
    assert principal is not None and principal.toques[-1] == 48
    seg = seguimiento(s, principal, P)
    assert seg is not None
    assert seg.i_a == 48


def test_la_separacion_de_toques_debe_superar_a_la_tolerancia():
    import pytest
    with pytest.raises(ValueError):
        replace(P, separacion_toque_atr=P.tolerancia_toque_atr)
    with pytest.raises(ValueError):
        replace(P, separacion_toque_atr=P.tolerancia_toque_atr / 2)


# _recorrer directo: con velas sintéticas la mecha que perfora suele ser ella misma un pivote
# del zigzag, y `trazar` la elegiría como B aunque _recorrer descartara la línea original.
def test_la_mecha_que_perfora_despues_de_b_mueve_el_punto_b():
    df = vs.desde_vertices(ALCISTA, 12)
    base = trazar(serie_de(df), "alcista", P, ancla=0)
    assert base.i_b == 24
    df.loc[60, "low"] = base.valor(60) - 4.0  # perfora más que la tolerancia y cierra adentro
    s = serie_de(df)
    t = _recorrer(s, "alcista", 0, 24, P)
    assert t is not None and t.vigente, "una mecha no es ruptura: la línea no desaparece"
    assert t.i_a == 0 and t.i_b == 60 and t.p_b == s.lows[60]
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)


def test_la_mecha_bajista_despues_de_b_mueve_el_punto_b():
    df = vs.desde_vertices(BAJISTA_ROTA[:-1], 12)
    s0 = serie_de(df)
    base = trazar(s0, "bajista", P, ancla=0)
    assert base is not None and base.i_a == 0
    j = len(df) - 2
    df.loc[j, "high"] = base.valor(j) + 4.0
    s = serie_de(df)
    t = _recorrer(s, "bajista", 0, base.i_b, P)
    assert t is not None and t.vigente
    assert t.i_b == j and t.p_b == s.highs[j]
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)


def test_la_mecha_que_deja_a_b_sin_pendiente_deja_sin_linea():
    df = vs.desde_vertices(ALCISTA, 12)
    base = trazar(serie_de(df), "alcista", P, ancla=0)
    # El low de la vela 60 queda por debajo de A: con ese B la pendiente se invierte.
    df.loc[60, "low"] = base.p_a - 1.0
    assert _recorrer(serie_de(df), "alcista", 0, 24, P) is None


def test_la_vela_que_perfora_y_cierra_afuera_sigue_siendo_ruptura():
    df = vs.desde_vertices(ALCISTA, 12)
    base = trazar(serie_de(df), "alcista", P, ancla=0)
    k = 60
    df.loc[k, ["low", "close"]] = base.valor(k) - 4.0
    t = _recorrer(serie_de(df), "alcista", 0, 24, P)
    assert t is not None and not t.vigente and t.i_ruptura == k


def test_la_mecha_que_perfora_antes_de_b_sigue_invalidando():
    df = vs.desde_vertices(ALCISTA, 12)
    base = trazar(serie_de(df), "alcista", P, ancla=0)
    df.loc[12, "low"] = base.valor(12) - 4.0  # antes de B (24)
    assert _recorrer(serie_de(df), "alcista", 0, 24, P) is None


# Gate del director (2026-10-11) sobre los PNG de S3: USDCLP con alcista evidente y sin
# ninguna diagonal, USDJPY con una ruptura de ~155 velas, WTI con el ancla en el borde.

def test_el_doble_piso_pasa_el_ancla_al_segundo_minimo():
    # Mínimos 100 y 100,2 casi iguales: desde el primero la línea es plana (o el segundo la
    # cruza). Encadenar (doctrina 2.3): la diagonal arranca en el segundo piso.
    s = serie_de(vs.desde_vertices([130, 100, 112, 100.2, 116, 108.5, 124, 116.5, 130, 125], 12))
    t = trazar(s, "alcista", P)
    assert t is not None and t.vigente
    assert abs(t.p_a - 100.0) < 1e-9 and t.i_a in (35, 36)
    assert len(t.toques) >= 3
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)


def test_la_linea_rota_rota_al_extremo_posterior_a_la_ruptura():
    # La alcista 100-106-112 se rompe; después el precio arma otra alcista 104-110-116.
    s = serie_de(vs.desde_vertices([130, 100, 112, 106, 118, 112, 124, 104, 116, 110, 122, 116, 126],
                                   12))
    t = trazar(s, "alcista", P)
    assert t is not None and t.vigente, "la estructura nueva reemplaza a la línea rota (V13)"
    assert abs(t.p_a - 103.8) < 1e-9
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)


def test_la_linea_rota_sin_estructura_nueva_se_conserva():
    s = serie_de(vs.desde_vertices([130, 100, 112, 106, 118, 112, 124, 103], 12))
    t = trazar(s, "alcista", P)
    assert t is not None and not t.vigente and abs(t.p_a - 99.8) < 1e-9


def test_el_ancla_no_cae_en_el_borde_de_la_ventana():
    # El mínimo es la primera vela: no se ve de dónde venía el precio, así que no es un
    # extremo visible (gate del director, WTI).
    s = serie_de(vs.desde_vertices([100, 112, 106, 118, 112, 124, 119], 12))
    t = trazar(s, "alcista", P)
    assert t is None or t.i_a > 1
