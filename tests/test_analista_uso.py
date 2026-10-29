"""La bitácora de uso del bot y su panel."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import uso  # noqa: E402
import uso_bot  # noqa: E402

AHORA = datetime(2026, 10, 28, 11, 0, tzinfo=ZoneInfo("America/Santiago"))


def test_registrar_y_leer(tmp_path):
    ruta = tmp_path / "uso.jsonl"
    uso.registrar(uso.MENSAJE, "1", ahora=AHORA, ruta=ruta, clase="pedido", pieza="oportunidad", ticker="GS", texto="x" * 500)
    (e,) = uso.leer(ruta)
    assert e["usuario"] == "1" and e["ts"].startswith("2026-10-28T11:00") and len(e["texto"]) == uso.MAX_TEXTO


def test_registrar_no_bota_si_no_puede_escribir(tmp_path):
    uso.registrar(uso.MENSAJE, "1", ruta=tmp_path)  # un directorio no se puede abrir como archivo


def test_leer_ignora_linea_cortada(tmp_path):
    ruta = tmp_path / "uso.jsonl"
    ruta.write_text('{"ts":"2026-10-28T10:00:00-03:00","tipo":"mensaje","usuario":"1"}\n{"ts":"2026', encoding="utf-8")
    assert len(uso.leer(ruta)) == 1


def test_log_viejo_solo_aporta_lo_anterior_a_la_bitacora(tmp_path):
    log = tmp_path / "bot.log"
    log.write_text(
        "2026-10-26 20:06:58 pedido 7: oportunidad|ticker=US500.spot\n"
        "2026-10-28 10:49:23 pedido 7: seguimiento|ticker=XAGUSD\n"
        "2026-10-28 11:00:00 desconocido 9: 'hola'\n"
        "  File \"x.py\", line 1\n", encoding="utf-8")
    sin_corte = uso.desde_log(log)
    assert [(e["usuario"], e.get("ticker"), e["clase"]) for e in sin_corte] == [
        ("7", "US500.spot", "pedido"), ("7", "XAGUSD", "pedido"), ("9", None, "no_autorizado")]
    assert len(uso.desde_log(log, antes_de="2026-10-28T10:00:00-03:00")) == 1


def test_panel_resuelve_nombres_y_no_deja_cerrar_el_script(tmp_path):
    cfg = tmp_path / "a.json"
    cfg.write_text(json.dumps({"analistas": {"7": {"nombre": "Camila Jofré", "cargo": "Analista", "rol": "analista"}}}), encoding="utf-8")
    ev = [{"ts": "2026-10-28T10:00:00-03:00", "tipo": "mensaje", "usuario": "9", "clase": "no_autorizado", "texto": "</script><b>"}]
    html = uso_bot.armar(ev, uso_bot.equipo(cfg), AHORA)
    assert "Camila Jofré" in html
    assert "</script><b>" not in html
    assert uso_bot.equipo(tmp_path / "no_existe.json") == {}
