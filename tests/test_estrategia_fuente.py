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


def test_la_hora_de_cierre_respeta_la_vuelta_al_horario_de_invierno_en_abril():
    # Chile vuelve de UTC-3 a UTC-4 el domingo 2027-04-04 a las 03:00 UTC (zoneinfo: el reloj
    # pasa de 00:00 a 23:00 del sábado). Servidor en UTC+3: la vela de 4H que abre a las
    # 12:00 del servidor abre 09:00 UTC y cierra 13:00 UTC.
    # Sábado 3: 13:00 UTC - 3 h = 10:00 en Chile. Lunes 5: 13:00 UTC - 4 h = 09:00 en Chile.
    antes = cierre_santiago(_ts(2027, 4, 3, 12, 0), "H4", 3 * 3600)  # Chile en UTC-3
    despues = cierre_santiago(_ts(2027, 4, 5, 12, 0), "H4", 3 * 3600)  # Chile en UTC-4
    assert antes.strftime("%H:%M") == "10:00"
    assert despues.strftime("%H:%M") == "09:00"


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


def test_el_atr_es_el_promedio_del_rango_verdadero():
    import pandas as pd
    from estrategia.fuente import atr
    df = pd.DataFrame({"time": [1, 2, 3], "open": [10, 11, 12], "high": [11, 13, 13],
                       "low": [9, 10, 11], "close": [10, 12, 12]})
    # Rangos verdaderos: 2, max(3, |13-10|, |10-10|)=3, max(2, |13-12|, |11-12|)=2
    assert atr(df, n=3) == (2 + 3 + 2) / 3
    assert atr(df, n=2) == (3 + 2) / 2
