"""Infraestructura de velas: vela abierta y hora de cierre en Chile."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.fuente import cierre_santiago, offset_servidor, separar_vela_abierta  # noqa: E402

H4 = 4 * 3600


def _ts(*args) -> int:
    return int(datetime(*args, tzinfo=timezone.utc).timestamp())


def test_offset_del_servidor_en_la_grilla_de_media_hora():
    assert offset_servidor(_ts(2026, 10, 9, 15, 2), _ts(2026, 10, 9, 12, 0)) == 3 * 3600


def test_la_ultima_vela_esta_abierta_si_no_termino_su_duracion():
    df = pd.DataFrame({"time": [0, H4, 2 * H4], "open": [1] * 3, "high": [1] * 3, "low": [1] * 3,
                       "close": [1] * 3})
    cerradas, abierta = separar_vela_abierta(df, "H4", ahora_servidor=2 * H4 + 60)
    assert len(cerradas) == 2 and int(abierta["time"]) == 2 * H4
    cerradas, abierta = separar_vela_abierta(df, "H4", ahora_servidor=3 * H4)
    assert len(cerradas) == 3 and abierta is None


def test_la_hora_de_cierre_respeta_el_cambio_de_horario_de_chile():
    # Servidor en UTC+3. Vela de 4H que abre 12:00 del servidor = 09:00 UTC y cierra 13:00 UTC.
    antes = cierre_santiago(_ts(2026, 9, 5, 12, 0), "H4", 3 * 3600)  # Chile en UTC-4
    despues = cierre_santiago(_ts(2026, 9, 7, 12, 0), "H4", 3 * 3600)  # Chile en UTC-3
    assert antes.strftime("%H:%M") == "09:00"
    assert despues.strftime("%H:%M") == "10:00"


def test_la_revision_registra_la_falla_de_un_activo_y_sigue(tmp_path, monkeypatch, capsys):
    import json

    import tori_revision

    def sin_datos(ticker, marcos, extra=0):
        raise RuntimeError("MT5 sin datos")

    monkeypatch.setattr(tori_revision, "RAIZ", tmp_path)
    monkeypatch.setattr(tori_revision, "velas_mt5", sin_datos)
    code = tori_revision.main(["--tickers", "USDCLP", "NO_EXISTE"])
    assert code == 1
    resumen = json.loads(next(tmp_path.rglob("resumen.json")).read_text(encoding="utf-8"))
    assert [r["ticker"] for r in resumen] == ["USDCLP", "NO_EXISTE"]
    assert "MT5 sin datos" in resumen[0]["error"] and "catalogo" in resumen[1]["error"]
