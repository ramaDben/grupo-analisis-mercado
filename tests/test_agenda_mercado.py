"""La agenda de mercado como fuente unica de ventanas y momentos.

**El problema que cierra: dos relojes.** Las ventanas de sesion vivian en una
cadena de `elif` dentro de `detectar_sesion`, con los minutos escritos a mano
(`8 * 60 + 30`), y los anclajes de tanda vivian en otra tabla. El reloj de
sucesos que viene necesita sus propias ventanas, y con eso serian tres lugares
declarando el mismo hecho.

Ese es el defecto recurrente del repo: dos modulos que se hablan por nombre sin
que nada verifique que coinciden. A la segunda copia una queda atras y nadie se
entera hasta que sale una pieza mal.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for _p in (RAIZ / "scripts", RAIZ / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import agenda_mercado as ag  # noqa: E402
import screener_gi as sc  # noqa: E402

NY = ZoneInfo("America/New_York")

# Un martes cualquiera, para no caer en el fin de semana.
MARTES = datetime(2026, 8, 25, tzinfo=NY)


# ─────────────────────────────────────────────────────────────────────────────
# Las ventanas de sesion
# ─────────────────────────────────────────────────────────────────────────────
def test_las_ventanas_cubren_el_dia_entero_sin_hueco_ni_solape():
    """Cada minuto del dia habil pertenece a exactamente una sesion.

    Un hueco deja al escaner sin sesion a esa hora; un solape hace que el
    resultado dependa del orden de la tabla, que es un accidente.
    """
    for minuto in range(24 * 60):
        cuando = MARTES.replace(hour=minuto // 60, minute=minuto % 60)
        calzan = [s for s in ag.sesiones() if ag.dentro_de(s, cuando)]
        assert len(calzan) == 1, (
            f"a las {cuando:%H:%M} de Nueva York calzan {len(calzan)} sesiones: "
            f"{[s['slug'] for s in calzan]}"
        )


def test_el_fin_de_semana_tiene_su_propia_sesion():
    sabado = datetime(2026, 8, 29, 12, 0, tzinfo=NY)
    assert ag.sesion_en(sabado)["slug"] == "fin_de_semana"


def test_el_domingo_por_la_tarde_ya_es_semana_de_mercado():
    """A las 18:00 de Nueva York del domingo abre el forex."""
    assert ag.sesion_en(datetime(2026, 8, 30, 17, 0, tzinfo=NY))["slug"] == "fin_de_semana"
    assert ag.sesion_en(datetime(2026, 8, 30, 18, 30, tzinfo=NY))["slug"] == "asiatica"


def test_toda_sesion_nombra_una_tanda_que_existe():
    for s in ag.sesiones():
        assert s["tanda"] in ag.tandas(), f"{s['slug']} apunta a una tanda inexistente"


# ─────────────────────────────────────────────────────────────────────────────
# El defecto que esto cierra: un solo reloj
# ─────────────────────────────────────────────────────────────────────────────
def test_el_escaner_no_tiene_las_ventanas_escritas_en_su_codigo():
    """Si vuelven al codigo, hay dos relojes y van a divergir."""
    fuente = (RAIZ / "scripts" / "screener_gi.py").read_text(encoding="utf-8")
    for sospechoso in ("8 * 60 + 30", "12 * 60 + 30", "15 * 60 + 30", "18 * 60"):
        assert sospechoso not in fuente, (
            f"la ventana {sospechoso!r} volvio al codigo del escaner: "
            "las ventanas se declaran en config/agenda_mercado.json"
        )


def test_la_deteccion_del_escaner_sale_de_la_agenda():
    """Misma respuesta por los dos caminos, o hay dos verdades."""
    for hora in (3, 9, 13, 16, 20, 23):
        cuando = MARTES.replace(hour=hora)
        assert sc.detectar_sesion(cuando)["slug"] == ag.sesion_en(cuando)["slug"]


# ─────────────────────────────────────────────────────────────────────────────
# Los momentos: el reloj de sucesos
# ─────────────────────────────────────────────────────────────────────────────
def test_las_divisas_y_los_metales_tienen_su_momento_temprano():
    m = ag.momento("premercado_fx")
    assert m["hora"] == "08:30"
    assert "forex_commodities" in m["clases"]


def test_los_indices_y_las_acciones_tienen_el_suyo_mas_tarde():
    m = ag.momento("apertura_indices")
    assert m["hora"] > ag.momento("premercado_fx")["hora"]
    assert set(m["clases"]) == {"indices", "acciones", "etfs"}


def test_ningun_momento_reparte_la_misma_clase_dos_veces():
    """Dos momentos con la misma clase publicarian el activo dos veces."""
    vistas: set[str] = set()
    for m in ag.momentos():
        for c in m["clases"]:
            assert c not in vistas, f"{c} aparece en dos momentos"
            vistas.add(c)


def test_toda_clase_de_un_momento_existe_en_el_universo_del_escaner():
    """Contrato de nombres: una clase mal escrita deja el momento inerte."""
    reales = {a["clase"] for a in sc.cargar_universo(solo_renderizables=False)}
    for m in ag.momentos():
        for c in m["clases"]:
            assert c in reales, f"{m['slug']} nombra la clase inexistente {c!r}"


def test_toda_clase_del_universo_esta_asignada_o_declarada_pendiente():
    """Una clase sin momento y sin declararlo se queda fuera en silencio."""
    reales = {a["clase"] for a in sc.cargar_universo(solo_renderizables=False)}
    asignadas = {c for m in ag.momentos() for c in m["clases"]}
    pendientes = set(ag.clases_sin_momento())
    assert reales - asignadas == pendientes, (
        "hay clases del universo sin momento que nadie declaro pendientes: "
        f"{reales - asignadas - pendientes}"
    )


def test_cada_momento_cae_dentro_de_la_sesion_que_declara():
    """Un momento en otra sesion describe un mercado distinto al que dice."""
    for m in ag.momentos():
        h, mi = (int(x) for x in m["hora"].split(":"))
        cuando = MARTES.replace(hour=h, minute=mi)
        assert ag.sesion_en(cuando)["slug"] == m["sesion"], (
            f"{m['slug']} dice {m['sesion']} pero a las {m['hora']} de Nueva York "
            f"la sesion es {ag.sesion_en(cuando)['slug']}"
        )


def test_el_momento_activo_se_encuentra_por_hora_con_tolerancia():
    """El reloj no dispara al segundo exacto: hay una ventana de gracia."""
    a_las_830 = MARTES.replace(hour=8, minute=32)
    assert ag.momento_en(a_las_830)["slug"] == "premercado_fx"
    assert ag.momento_en(MARTES.replace(hour=11, minute=0)) is None


def test_todo_momento_explica_por_que_esta_a_esa_hora():
    """El motivo es lo que permite discutir el horario sin re-derivarlo."""
    for m in ag.momentos():
        assert len(m.get("por_que", "")) > 30, f"{m['slug']} no explica su hora"


# ─────────────────────────────────────────────────────────────────────────────
# El ancla
# ─────────────────────────────────────────────────────────────────────────────
def test_el_ancla_es_nueva_york_y_se_comunica_en_hora_de_chile():
    cfg = json.loads(
        (RAIZ / "config" / "agenda_mercado.json").read_text(encoding="utf-8")
    )
    assert cfg["zona_ancla"] == "America/New_York"


def test_el_desfase_con_chile_no_esta_escrito_en_ningun_lado():
    """Chile y EE.UU. cambian de horario en sentido opuesto: el desfase se mueve.

    Hoy es +0 h y desde el 2026-09-06 pasa a +1 h. Cualquier offset escrito a
    mano queda mal dos veces al ano, que es el error del issue #38.
    """
    cfg = (RAIZ / "config" / "agenda_mercado.json").read_text(encoding="utf-8")
    for offset in ("UTC-3", "UTC-4", "UTC-5", "GMT-3", "GMT-4"):
        assert offset not in cfg, f"hay un desfase fijo escrito: {offset}"


# ─────────────────────────────────────────────────────────────────────────────
# Cripto: medido, no supuesto
# ─────────────────────────────────────────────────────────────────────────────
def test_la_cripto_tiene_su_momento_en_la_manana_de_nueva_york():
    """Medido sobre 90 dias de H1 en BTC, ETH, SOL y LTC.

    El bloque 08-12 de Nueva York rinde entre 1,49x y 1,80x la mediana diaria de
    rango, con el maximo en 09:00-10:00 (BTC llega a 2,09x). No es una
    preferencia: es donde esta el movimiento.
    """
    m = ag.momento("cripto")
    hora = _minutos(m["hora"])
    assert _minutos("08:00") <= hora < _minutos("12:00"), (
        f"la cripto quedo a las {m['hora']} de Nueva York, fuera del bloque medido"
    )
    assert m["clases"] == ["crypto"]


def test_la_cripto_no_va_en_la_sesion_asiatica():
    """La hipotesis del rollover asiatico se midio y era falsa.

    Asia (18-02 NY) rinde entre 0,94x y 1,01x: plano. Europa (03-08) igual. Todo
    el exceso de rango esta en la manana americana.
    """
    assert ag.momento("cripto")["sesion"] != "asiatica"


def test_ninguna_clase_del_universo_quedo_sin_momento():
    """Con cripto asignada, la lista de pendientes tiene que estar vacia."""
    assert ag.clases_sin_momento() == []


def _minutos(hhmm: str) -> int:
    return ag._minutos(hhmm)
