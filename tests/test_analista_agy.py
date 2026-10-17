"""El techo de espera de agy para redactar una pieza."""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import agy  # noqa: E402


def test_el_timeout_alcanza_para_la_busqueda_web():
    minutos = int(re.fullmatch(r"(\d+)m", agy.TIMEOUT).group(1))
    assert minutos >= 12  # nunca bajo lo que ya medía un encargo real


def _minutos(t):
    return int(re.fullmatch(r"(\d+)m", t).group(1))


def test_el_reintento_de_fuentes_tiene_su_propio_techo_menor():
    assert 10 <= _minutos(agy.TIMEOUT_REINTENTO) < _minutos(agy.TIMEOUT)


def test_escribir_textos_pasa_el_timeout_pedido(monkeypatch, tmp_path):
    import agy_encargo

    pedidos = tmp_path / "data" / "informes_analistas"
    (pedidos / "p").mkdir(parents=True)
    (pedidos / "p" / "pieza.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(agy, "RAIZ", tmp_path)
    monkeypatch.setattr(agy, "DIR_PEDIDOS", pedidos)
    vistos = []
    monkeypatch.setattr(agy_encargo, "invocar", lambda prompt, tier, timeout: vistos.append((prompt, timeout)))
    agy.escribir_textos(pedidos / "p" / "pieza.json", "flash", agy.TIMEOUT_REINTENTO)
    agy.escribir_textos(pedidos / "p" / "pieza.json")
    assert vistos == [("/analista data/informes_analistas/p/pieza.json", agy.TIMEOUT_REINTENTO),
                      ("/analista data/informes_analistas/p/pieza.json", agy.TIMEOUT)]
