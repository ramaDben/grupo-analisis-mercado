"""Tests del catálogo de motivos y banco de imágenes ilustrativas del correo."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import ilustracion  # noqa: E402
from analista.generador_imagen import ImagenNoGenerada  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64

MOTIVOS_ESPERADOS = {
    "oro_lingotes",
    "banco_central",
    "billetes_dolar",
    "peso_chileno",
    "cobre",
    "petroleo",
    "bolsa_pantallas",
    "tecnologia",
    "acciones_generico",
}


def test_prompt_lleva_las_prohibiciones():
    prompt = ilustracion.prompt_de("oro_lingotes")
    assert "Sin logos" in prompt


def test_motivo_desconocido_levanta(tmp_path: Path):
    with pytest.raises(KeyError):
        ilustracion.prompt_de("bandera_chile")

    with pytest.raises(KeyError):
        ilustracion.elegir("bandera_chile", hoy=date(2026, 10, 24), generar=None, banco=tmp_path)


def test_catalogo_tiene_los_nueve_motivos():
    assert set(ilustracion.motivos().keys()) == MOTIVOS_ESPERADOS


def test_ningun_prompt_pide_marca_ni_texto():
    prohibidas = ("logo de", "marca de", "texto que diga", "bandera de")
    for id_motivo, info in ilustracion.motivos().items():
        prompt_bajo = info["prompt"].lower()
        for frase in prohibidas:
            assert frase not in prompt_bajo, f"Motivo {id_motivo} contiene '{frase}' en su prompt"


def test_elige_una_sin_uso_reciente(tmp_path: Path):
    dir_oro = tmp_path / "oro_lingotes"
    dir_oro.mkdir(parents=True, exist_ok=True)
    img_a = dir_oro / "a.png"
    img_b = dir_oro / "b.png"
    img_a.write_bytes(PNG)
    img_b.write_bytes(PNG)

    hoy = date(2026, 10, 24)
    usos = {
        "oro_lingotes/a.png": (hoy - timedelta(days=2)).isoformat(),
        "oro_lingotes/b.png": (hoy - timedelta(days=9)).isoformat(),
    }
    (tmp_path / "uso.json").write_text(json.dumps(usos, ensure_ascii=False, indent=2), encoding="utf-8")

    ruta, aviso = ilustracion.elegir("oro_lingotes", hoy=hoy, generar=None, banco=tmp_path)
    assert ruta == img_b
    assert aviso is None

    nuevo_uso = json.loads((tmp_path / "uso.json").read_text(encoding="utf-8"))
    assert nuevo_uso["oro_lingotes/b.png"] == hoy.isoformat()
    assert nuevo_uso["oro_lingotes/a.png"] == (hoy - timedelta(days=2)).isoformat()


def test_prefiere_la_nunca_usada(tmp_path: Path):
    dir_oro = tmp_path / "oro_lingotes"
    dir_oro.mkdir(parents=True, exist_ok=True)
    img_a = dir_oro / "a.png"
    img_c = dir_oro / "c.png"
    img_a.write_bytes(PNG)
    img_c.write_bytes(PNG)

    hoy = date(2026, 10, 24)
    usos = {
        "oro_lingotes/a.png": (hoy - timedelta(days=9)).isoformat(),
    }
    (tmp_path / "uso.json").write_text(json.dumps(usos, ensure_ascii=False, indent=2), encoding="utf-8")

    ruta, aviso = ilustracion.elegir("oro_lingotes", hoy=hoy, generar=None, banco=tmp_path)
    assert ruta == img_c
    assert aviso is None

    nuevo_uso = json.loads((tmp_path / "uso.json").read_text(encoding="utf-8"))
    assert nuevo_uso["oro_lingotes/c.png"] == hoy.isoformat()


def test_genera_si_todas_estan_en_cooldown(tmp_path: Path):
    dir_oro = tmp_path / "oro_lingotes"
    dir_oro.mkdir(parents=True, exist_ok=True)
    img_a = dir_oro / "a.png"
    img_b = dir_oro / "b.png"
    img_a.write_bytes(PNG)
    img_b.write_bytes(PNG)

    hoy = date(2026, 10, 24)
    usos = {
        "oro_lingotes/a.png": (hoy - timedelta(days=1)).isoformat(),
        "oro_lingotes/b.png": (hoy - timedelta(days=1)).isoformat(),
    }
    (tmp_path / "uso.json").write_text(json.dumps(usos, ensure_ascii=False, indent=2), encoding="utf-8")

    recibido: list[tuple[str, Path]] = []

    def doble_generar(prompt: str, destino: Path) -> Path:
        recibido.append((prompt, destino))
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(PNG)
        return destino

    ahora = datetime(2026, 10, 24, 15, 30, 0)
    ruta, aviso = ilustracion.elegir("oro_lingotes", hoy=hoy, generar=doble_generar, banco=tmp_path, ahora=ahora)
    assert ruta == dir_oro / "20261024-153000.png"
    assert aviso is None
    assert len(recibido) == 1
    assert "Sin logos" in recibido[0][0]

    nuevo_uso = json.loads((tmp_path / "uso.json").read_text(encoding="utf-8"))
    assert nuevo_uso["oro_lingotes/20261024-153000.png"] == hoy.isoformat()


def test_si_falla_la_generacion_usa_la_mas_antigua(tmp_path: Path):
    dir_oro = tmp_path / "oro_lingotes"
    dir_oro.mkdir(parents=True, exist_ok=True)
    img_a = dir_oro / "a.png"
    img_b = dir_oro / "b.png"
    img_a.write_bytes(PNG)
    img_b.write_bytes(PNG)

    hoy = date(2026, 10, 24)
    usos = {
        "oro_lingotes/a.png": (hoy - timedelta(days=1)).isoformat(),
        "oro_lingotes/b.png": (hoy - timedelta(days=3)).isoformat(),
    }
    (tmp_path / "uso.json").write_text(json.dumps(usos, ensure_ascii=False, indent=2), encoding="utf-8")

    def doble_falla(prompt: str, destino: Path) -> Path:
        raise ImagenNoGenerada("simulacion de error de agy")

    ruta, aviso = ilustracion.elegir("oro_lingotes", hoy=hoy, generar=doble_falla, banco=tmp_path)
    assert ruta == img_b
    assert aviso is not None
    assert len(aviso) > 0

    nuevo_uso = json.loads((tmp_path / "uso.json").read_text(encoding="utf-8"))
    assert nuevo_uso["oro_lingotes/b.png"] == hoy.isoformat()


def test_sin_banco_ni_generador_devuelve_none(tmp_path: Path):
    hoy = date(2026, 10, 24)
    ruta, aviso = ilustracion.elegir("oro_lingotes", hoy=hoy, generar=None, banco=tmp_path)
    assert ruta is None
    assert aviso is not None
    assert len(aviso) > 0


def test_uso_ilegible_cuenta_como_vacio(tmp_path: Path):
    dir_oro = tmp_path / "oro_lingotes"
    dir_oro.mkdir(parents=True, exist_ok=True)
    img_a = dir_oro / "a.png"
    img_a.write_bytes(PNG)

    hoy = date(2026, 10, 24)
    (tmp_path / "uso.json").write_text("{roto", encoding="utf-8")

    ruta, aviso = ilustracion.elegir("oro_lingotes", hoy=hoy, generar=None, banco=tmp_path)
    assert ruta == img_a
    assert aviso is None

    nuevo_uso = json.loads((tmp_path / "uso.json").read_text(encoding="utf-8"))
    assert nuevo_uso["oro_lingotes/a.png"] == hoy.isoformat()


def test_generador_none_con_imagenes_en_cooldown_reutiliza_la_mas_antigua(tmp_path: Path):
    dir_oro = tmp_path / "oro_lingotes"
    dir_oro.mkdir(parents=True, exist_ok=True)
    img_a = dir_oro / "a.png"
    img_b = dir_oro / "b.png"
    img_a.write_bytes(PNG)
    img_b.write_bytes(PNG)

    hoy = date(2026, 10, 24)
    usos = {
        "oro_lingotes/a.png": (hoy - timedelta(days=2)).isoformat(),
        "oro_lingotes/b.png": (hoy - timedelta(days=4)).isoformat(),
    }
    (tmp_path / "uso.json").write_text(json.dumps(usos, ensure_ascii=False, indent=2), encoding="utf-8")

    ruta, aviso = ilustracion.elegir("oro_lingotes", hoy=hoy, generar=None, banco=tmp_path)
    assert ruta == img_b
    assert aviso is not None
    assert len(aviso) > 0


def test_ningun_motivo_pide_pantallas_ni_graficos():
    """La excepción de la Regla 0 excluye gráficos y pantallas: un gráfico generado se leería como el real."""
    for m in ilustracion.motivos().values():
        texto = m["prompt"].lower()
        assert "velas" not in texto and "monitores" not in texto and "pantallas múltiples" not in texto
