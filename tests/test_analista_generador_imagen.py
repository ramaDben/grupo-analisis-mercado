"""El generador de imágenes ilustrativas: agy genera, Python comprueba que el archivo quedó."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from agy_encargo import Resultado  # noqa: E402
from analista import generador_imagen as gi  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_generar_levanta_si_no_queda_el_archivo(tmp_path: Path):
    destino = tmp_path / "oro.png"
    with pytest.raises(gi.ImagenNoGenerada):
        gi.generar_con_agy("lingotes", destino, invocar=lambda *a: Resultado("ok", "SUCCESS"))


def test_generar_levanta_si_agy_no_termina(tmp_path: Path):
    destino = tmp_path / "oro.png"

    def invocar(*a):
        destino.write_bytes(PNG)
        return Resultado("timeout", "se cortó")

    with pytest.raises(gi.ImagenNoGenerada):
        gi.generar_con_agy("lingotes", destino, invocar=invocar)


def test_generar_levanta_si_el_archivo_no_es_imagen(tmp_path: Path):
    destino = tmp_path / "oro.png"

    def invocar(*a):
        destino.write_text("ERROR: no pude", encoding="utf-8")
        return Resultado("ok", "SUCCESS")

    with pytest.raises(gi.ImagenNoGenerada):
        gi.generar_con_agy("lingotes", destino, invocar=invocar)


def test_generar_devuelve_el_destino(tmp_path: Path):
    destino = tmp_path / "sub" / "oro.png"
    vistos: list[str] = []

    def invocar(prompt, tier, timeout):
        vistos.append(prompt)
        destino.write_bytes(PNG)
        return Resultado("ok", "SUCCESS")

    assert gi.generar_con_agy("lingotes de oro", destino, invocar=invocar) == destino
    assert "lingotes de oro" in vistos[0] and destino.as_posix() in vistos[0]
