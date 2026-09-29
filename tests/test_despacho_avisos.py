"""El despacho de las tandas de Avisos (spec 2026-09-28-carruseles-avisos-design.md, 3.7 y §13)."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pipeline_avisos as pa  # noqa: E402
import pipeline_carrusel as pc  # noqa: E402
from test_pipeline_avisos_jornada import CONFIANZA, JOLTS, preparar  # noqa: E402

SIETE_45 = datetime(2026, 9, 29, 7, 45, tzinfo=pa.SANTIAGO)
ONCE_10 = datetime(2026, 9, 29, 11, 10, tzinfo=pa.SANTIAGO)


class _Config:
    destino_de_pruebas = "GI · Banco de Pruebas"


def _sender(envios: list, cupo: int = 40):
    class Sender:
        def __init__(self, headless=True):
            self.config = _Config()

        def cupo_restante(self):
            return cupo

        def enviar_lote(self, destinatario, piezas, dry_run=False, al_entregar=None):
            envios.append((destinatario, [Path(pz.adjunto).name for pz in piezas]))
            return {"destinatario": destinatario, "piezas": len(piezas), "status": "enviado"}

    return Sender


@pytest.fixture
def entorno(monkeypatch):
    """Sin navegador, sin bitácora real y con un render que solo escribe el PNG."""
    monkeypatch.setattr("story_render.render_story",
                        lambda tokens, plantilla, salida, formato="horizontal": Path(salida).write_bytes(b"png"))
    monkeypatch.setattr("bitacora_despachos.registrar", lambda *a, **k: None)
    monkeypatch.setattr("bitacora_despachos.cargar", lambda *a, **k: [])
    monkeypatch.setattr(pc, "falta_metatrader5", lambda: True)


def _escribir(ruta: Path, textos: dict[str, dict]) -> None:
    for stem, payload in pa.leer_laminas(ruta):
        payload.update(textos.get(stem, {}))
        (ruta / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


TEXTOS_AGENDA = {
    "1_portada": {"kicker": "Martes", "titular": "Un día que se juega en el empleo",
                  "parrafo": "Dos datos a las 11:00.", "claves": [{"texto": "Empleo"}] * 3,
                  "pie": "Hoy manda el empleo de EE.UU."},
    "2_dia": {"titular": "Lo que mueve la jornada", "parrafo": "Dos datos de EE.UU. a las 11:00."},
    "3_lectura": {"titular": "Cómo leer estos datos", "parrafo": "Antes de un dato fuerte el precio se mueve poco."},
}


def test_la_agenda_del_dia_sale_con_sus_tres_laminas_en_orden(tmp_path, entorno, monkeypatch):
    ruta = preparar(tmp_path, "avisos_agenda", datetime.now(pa.SANTIAGO).replace(hour=7, minute=45),
                    [dict(CONFIANZA, fecha=datetime.now(pa.SANTIAGO).date().isoformat())])
    _escribir(ruta, TEXTOS_AGENDA)
    envios: list = []
    monkeypatch.setattr("whatsapp_sender.WhatsAppSender", _sender(envios))
    pc.despachar(ruta.parent, pruebas=True)
    assert envios == [("GI · Banco de Pruebas", ["1_portada.png", "2_dia.png", "3_lectura.png"])]
    assert "Hoy manda el empleo de EE.UU." in (ruta / "1_portada_mensaje.txt").read_text(encoding="utf-8")


def test_un_carrusel_sin_escribir_no_sale_ninguna_lamina(tmp_path, entorno, monkeypatch):
    ruta = preparar(tmp_path, "avisos_agenda", SIETE_45, [CONFIANZA])
    envios: list = []
    monkeypatch.setattr("whatsapp_sender.WhatsAppSender", _sender(envios))
    res = pc.despachar(ruta.parent, pruebas=True)
    assert envios == []
    assert res["grupos"] == [{"grupo": pa.CANAL, "status": "frenado"}]


def test_si_el_cupo_no_alcanza_el_carrusel_no_empieza(tmp_path, entorno, monkeypatch):
    ruta = preparar(tmp_path, "avisos_agenda", datetime.now(pa.SANTIAGO).replace(hour=7, minute=45),
                    [dict(CONFIANZA, fecha=datetime.now(pa.SANTIAGO).date().isoformat())])
    _escribir(ruta, TEXTOS_AGENDA)
    envios: list = []
    monkeypatch.setattr("whatsapp_sender.WhatsAppSender", _sender(envios, cupo=2))
    pc.despachar(ruta.parent, pruebas=True)
    assert envios == []


def test_un_resultado_que_dio_vuelta_no_se_despacha(tmp_path, entorno, monkeypatch):
    hoy = datetime.now(pa.SANTIAGO)
    publicados = [dict(CONFIANZA, fecha=hoy.date().isoformat(), actual="81.9", resultado="peor"),
                  dict(JOLTS, fecha=hoy.date().isoformat(), actual="7.079M", resultado="peor")]
    ruta = preparar(tmp_path, "avisos_resultado", hoy.replace(hour=11, minute=10), publicados)
    _escribir(ruta, {"1_resultado": {"parrafo": "Un empleo que se enfría le resta fuerza al dólar."}})
    monkeypatch.setattr(pc, "falta_metatrader5", lambda: False)
    monkeypatch.setattr(pa, "leer_movimiento", lambda t, d, a: {"desde": 970.80, "ahora": 972.10, "digits": 2})
    envios: list = []
    monkeypatch.setattr("whatsapp_sender.WhatsAppSender", _sender(envios))
    pc.despachar(ruta.parent, pruebas=True)
    assert envios == []


def test_una_tanda_sin_avisos_json_sigue_el_camino_del_carrusel(tmp_path, entorno, monkeypatch):
    grupo = tmp_path / "02_forex_divisas"
    grupo.mkdir()
    (grupo / "1_test.png").write_bytes(b"png")
    (grupo / "1_test_mensaje.txt").write_text("Mensaje", encoding="utf-8")
    llamados: list = []
    monkeypatch.setattr(pc, "_refrescar_y_rendir", lambda d: llamados.append(d) or [])
    monkeypatch.setattr(pc, "_refrescar_y_rendir_avisos", lambda *a: pytest.fail("no es de Avisos"))
    envios: list = []
    monkeypatch.setattr("whatsapp_sender.WhatsAppSender", _sender(envios))
    pc.despachar(tmp_path, pruebas=True)
    assert llamados == [grupo] and envios == [("GI · Banco de Pruebas", ["1_test.png"])]


def test_el_sender_informa_el_cupo_sin_descontarlo(tmp_path, monkeypatch):
    import whatsapp_sender as ws

    estado = tmp_path / "envios.json"
    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", estado)
    from datetime import date

    estado.write_text(json.dumps({"fecha": date.today().isoformat(), "enviados": 31, "ultimo_ts": 0}),
                      encoding="utf-8")
    sender = ws.WhatsAppSender.__new__(ws.WhatsAppSender)
    sender.max_envios_dia = 40
    assert sender.cupo_restante() == 9
    assert json.loads(estado.read_text(encoding="utf-8"))["enviados"] == 31
