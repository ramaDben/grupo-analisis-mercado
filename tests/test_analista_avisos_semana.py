"""El agendador interno del bot: qué toca y cuándo, sin repetir, con tope, y qué mide de la interacción."""
from __future__ import annotations

import ast
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from analista import avisos_semana as av  # noqa: E402
from market_data_mcp.tools.calendar import _cargar_glosario, _enganchar_glosario  # noqa: E402

SCL = ZoneInfo("America/Santiago")
GLOSARIO = _cargar_glosario()


def a(dia, h, m=0):
    return datetime(2026, 10, dia, h, m, tzinfo=SCL)


def ev(nombre, hora, pais="United States"):
    e = {"nombre": nombre, "pais": pais, "impacto": "alto", "hora_servidor": hora, "forecast": "", "previo": "",
         "actual": ""}
    e["diccionario"] = _enganchar_glosario(nombre, GLOSARIO)
    return e


CPI = ev("CPI (MoM) (Sep)", "2026-10-21 09:30")          # miércoles
NFP = ev("Nonfarm Payrolls (Sep)", "2026-10-21 09:30")    # miércoles, mismo día
FOMC = ev("Fed Interest Rate Decision", "2026-10-21 15:00")
PMI = ev("ISM Manufacturing PMI (Sep)", "2026-10-21 11:00")  # tier 2: no tiene víspera
LUNES_0745 = a(19, 7, 45)
MARTES_1600 = a(20, 16, 0)


@pytest.fixture
def estado(tmp_path):
    return av.Estado(tmp_path / "avisos_semana.json")


# ───────────────────────────────────────────── ventanas


@pytest.mark.parametrize("ahora,tipos", [
    (a(19, 7, 44), []), (a(19, 7, 45), ["mapa"]), (a(19, 8, 14), ["mapa"]), (a(19, 8, 15), []),
    (a(20, 7, 45), []),                    # el martes no hay mapa
    (a(20, 15, 59), []), (MARTES_1600, ["vispera"]), (a(20, 16, 29), ["vispera"]), (a(20, 16, 30), []),
    (a(21, 16, 0), []),                    # el miércoles el dato ya salió: no hay víspera de nada
])
def test_ventanas(estado, ahora, tipos):
    assert [x.tipo for x in av.que_toca(ahora, [CPI], estado, "1")] == tipos


def test_la_vispera_de_un_dato_del_lunes_sale_el_viernes_a_las_16():
    lunes = ev("CPI (MoM) (Sep)", "2026-10-26 09:30")
    assert [x.tipo for x in av.que_toca(a(23, 16, 0), [lunes], av.Estado(Path("x")), "1")] == ["vispera"]
    assert av.que_toca(a(25, 16, 0), [lunes], av.Estado(Path("x")), "1") == []   # domingo: no es día hábil


def test_solo_tier_uno_tiene_vispera(estado):
    assert av.que_toca(MARTES_1600, [PMI], estado, "1") == []


def test_la_vispera_no_repite_el_mismo_dato_del_mismo_dia(estado):
    fomc2 = ev("FOMC Statement", "2026-10-21 15:00")
    avisos = av.que_toca(MARTES_1600, [FOMC, fomc2], estado, "1")
    assert len(avisos) == 1


# ───────────────────────────────────────────── una vez, y tras reinicio


def test_un_aviso_enviado_no_se_repite_ni_tras_reiniciar(estado, tmp_path):
    aviso = av.que_toca(LUNES_0745, [CPI], estado, "1")[0]
    estado.anotar_envio("1", aviso, LUNES_0745, 77)
    assert av.que_toca(a(19, 8, 0), [CPI], estado, "1") == []
    reiniciado = av.Estado(tmp_path / "avisos_semana.json")
    assert av.que_toca(a(19, 8, 0), [CPI], reiniciado, "1") == []


def test_el_envio_a_un_ejecutivo_no_marca_a_otro(estado):
    aviso = av.que_toca(LUNES_0745, [CPI], estado, "1")[0]
    estado.anotar_envio("1", aviso, LUNES_0745, 1)
    assert len(av.que_toca(LUNES_0745, [CPI], estado, "2")) == 1


def test_tope_de_dos_por_ejecutivo_por_dia_y_gana_el_mayor_tier(estado):
    # Martes 16:00: víspera de CPI (tier 1), NFP (tier 1) y FOMC (tier 1) del miércoles; mapa no aplica.
    avisos = av.que_toca(MARTES_1600, [FOMC, CPI, NFP], estado, "1")
    assert len(avisos) == 2
    estado.anotar_envio("1", avisos[0], MARTES_1600, 1)
    estado.anotar_envio("1", avisos[1], MARTES_1600, 2)
    assert av.que_toca(a(20, 16, 10), [FOMC, CPI, NFP], estado, "1") == []   # el resto queda en el mapa


def test_el_mapa_cuenta_para_el_tope(estado):
    mapa = av.que_toca(LUNES_0745, [CPI], estado, "1")[0]
    estado.anotar_envio("1", mapa, LUNES_0745, 1)
    # Ese mismo lunes a las 16:00 hay víspera del martes: es el segundo aviso, cabe.
    martes = ev("CPI (MoM) (Sep)", "2026-10-20 09:30")
    assert len(av.que_toca(a(19, 16, 0), [martes], estado, "1")) == 1


# ───────────────────────────────────────────── el agendador


class Envios:
    def __init__(self, falla=False):
        self.enviados, self.falla = [], falla
        self.n = 0

    def __call__(self, chat, aviso):
        if self.falla:
            raise RuntimeError("Telegram caído")
        self.enviados.append((chat, aviso.tipo))
        self.n += 1
        return 100 + self.n

    def director(self, chat, texto):
        self.enviados.append((chat, "director:" + texto[:20]))


CONFIG = {"analistas": {"10": {"nombre": "Dora", "rol": "director"}, "20": {"nombre": "Eli", "rol": "analista"}}}


def agendador(estado, envios, ahora, leer, modo="todos"):
    cfg = {**CONFIG, "avisos_semana": {"modo": modo}}
    return av.Agendador(cfg, estado, envios, envios.director, lambda: ahora[0], leer)


def test_el_agendador_dispara_una_vez_y_anota_solo_lo_confirmado(estado):
    envios, ahora = Envios(), [LUNES_0745]
    ag_ = agendador(estado, envios, ahora, lambda t: ("ok", [CPI]))
    ag_.latido()
    ag_.latido()
    assert sorted(envios.enviados) == [("10", "mapa"), ("20", "mapa")]


def test_un_envio_que_falla_sigue_pendiente_y_sale_en_el_siguiente_latido(estado):
    envios, ahora = Envios(falla=True), [LUNES_0745]
    ag_ = agendador(estado, envios, ahora, lambda t: ("ok", [CPI]))
    ag_.latido()
    assert envios.enviados == [] and estado.datos["enviados"] == []
    envios.falla = False
    ag_.latido()
    assert len(envios.enviados) == 2


def test_modo_prueba_manda_solo_al_director(estado):
    envios, ahora = Envios(), [LUNES_0745]
    agendador(estado, envios, ahora, lambda t: ("ok", [CPI]), modo="prueba").latido()
    assert envios.enviados == [("10", "mapa")]


def test_fuera_de_ventana_ni_siquiera_lee_el_calendario(estado):
    llamadas = []
    envios, ahora = Envios(), [a(21, 12, 0)]
    agendador(estado, envios, ahora, lambda t: llamadas.append(t) or ("ok", [])).latido()
    assert llamadas == [] and envios.enviados == []


def test_calendario_caido_no_envia_avisa_al_director_una_vez_y_reintenta(estado):
    envios, ahora = Envios(), [LUNES_0745]
    estado_cal = ["sin_calendario"]
    ag_ = agendador(estado, envios, ahora, lambda t: (estado_cal[0], [CPI] if estado_cal[0] == "ok" else []))
    ag_.latido()
    ag_.latido()
    assert [e for e in envios.enviados if not e[1].startswith("director")] == []
    assert len([e for e in envios.enviados if e[1].startswith("director")]) == 1
    estado_cal[0] = "ok"
    ahora[0] = a(19, 8, 0)
    ag_.latido()
    assert sorted(e for e in envios.enviados if e[1] == "mapa") == [("10", "mapa"), ("20", "mapa")]


def test_semana_sin_eventos_fuertes_si_se_envia_cuando_el_calendario_respondio(estado):
    envios, ahora = Envios(), [LUNES_0745]
    agendador(estado, envios, ahora, lambda t: ("vacia", [])).latido()
    assert len(envios.enviados) == 2


# ───────────────────────────────────────────── interacción (tarea 5b)


def _enviar_mapa_y_vispera(estado):
    mapa = av.que_toca(LUNES_0745, [CPI], estado, "1")[0]
    estado.anotar_envio("1", mapa, LUNES_0745, 11)
    vispera = av.que_toca(MARTES_1600, [CPI], estado, "1")[0]
    estado.anotar_envio("1", vispera, MARTES_1600, 12)
    return mapa, vispera


def test_un_voto_por_ejecutivo_y_aviso(estado):
    mapa, _ = _enviar_mapa_y_vispera(estado)
    assert estado.anotar_voto("1", mapa.id, "util", a(19, 9, 0)) is True
    assert estado.anotar_voto("1", mapa.id, "no_sirve", a(19, 9, 5)) is False
    reg = estado.registro("1", mapa.id)
    assert reg["votos"] == [{"voto": "util", "cuando": a(19, 9, 0).isoformat()}]


def test_los_clics_del_boton_se_cuentan_todos(estado):
    _, vispera = _enviar_mapa_y_vispera(estado)
    estado.anotar_clic("1", vispera.id, a(20, 16, 5))
    estado.anotar_clic("1", vispera.id, a(20, 16, 6))
    assert estado.registro("1", vispera.id)["clics_boton"] == 2


def test_oportunidad_24h_solo_cuenta_el_mismo_activo_y_dentro_de_la_ventana(estado):
    _, vispera = _enviar_mapa_y_vispera(estado)
    assert vispera.activo == "USDCLP"
    estado.marcar_oportunidad("1", "XAUUSD", a(20, 17, 0))      # otro activo
    assert estado.registro("1", vispera.id)["oportunidad_24h"] is False
    estado.marcar_oportunidad("1", "USDCLP", a(21, 16, 1))      # pasaron más de 24 h
    assert estado.registro("1", vispera.id)["oportunidad_24h"] is False
    estado.marcar_oportunidad("2", "USDCLP", a(20, 17, 0))      # otro ejecutivo
    assert estado.registro("1", vispera.id)["oportunidad_24h"] is False
    estado.marcar_oportunidad("1", "USDCLP", a(21, 15, 59))
    assert estado.registro("1", vispera.id)["oportunidad_24h"] is True


def test_el_resumen_suma_dos_ejecutivos_y_dos_semanas_sin_identificarlos(estado):
    for ejecutivo in ("1", "2"):
        for dia_lunes, dia_martes in ((19, 20), (26, 27)):
            m = av.que_toca(a(dia_lunes, 7, 45), [CPI], av.Estado(Path("x")), ejecutivo)[0]
            estado.anotar_envio(ejecutivo, m, a(dia_lunes, 7, 45), 1)
            estado.anotar_voto(ejecutivo, m.id, "util" if ejecutivo == "1" else "no_sirve", a(dia_lunes, 9))
    v = av.que_toca(MARTES_1600, [CPI], av.Estado(Path("x")), "1")[0]
    estado.anotar_envio("1", v, MARTES_1600, 2)
    estado.anotar_clic("1", v.id, a(20, 16, 5))
    estado.marcar_oportunidad("1", "USDCLP", a(20, 17, 0))
    r = av.resumen_interaccion(date(2026, 10, 19), date(2026, 10, 30), estado)
    assert r["mapa"] == {"enviados": 4, "clics": 0, "util": 2, "no_sirve": 2, "oportunidad": 0}
    assert r["vispera"] == {"enviados": 1, "clics": 1, "util": 0, "no_sirve": 0, "oportunidad": 1}
    assert set(r) == {"mapa", "vispera"}  # por tipo de aviso: ningún ejecutivo aparece en el resumen
    acotado = av.resumen_interaccion(date(2026, 10, 26), date(2026, 10, 30), estado)
    assert acotado["mapa"]["enviados"] == 2


def test_reiniciar_el_bot_no_pierde_los_registros(estado, tmp_path):
    mapa, _ = _enviar_mapa_y_vispera(estado)
    estado.anotar_voto("1", mapa.id, "util", a(19, 9))
    otro = av.Estado(tmp_path / "avisos_semana.json")
    assert otro.registro("1", mapa.id)["votos"][0]["voto"] == "util"


# ───────────────────────────────────────────── contrato: nada de WhatsApp


def test_el_agendador_no_importa_el_envio_de_whatsapp():
    fuente = (Path(__file__).resolve().parent.parent / "scripts" / "analista" / "avisos_semana.py").read_text(
        encoding="utf-8")
    importados = set()
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import):
            importados |= {n.name for n in nodo.names}
        elif isinstance(nodo, ast.ImportFrom):
            importados |= {nodo.module or ""} | {n.name for n in nodo.names}
    assert not any("whatsapp" in i.lower() for i in importados), importados
