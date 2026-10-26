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
    "plata",
    "cripto",
}


def test_prompt_lleva_las_prohibiciones():
    prompt = ilustracion.prompt_de("oro_lingotes")
    assert "Sin logos" in prompt


def test_motivo_desconocido_levanta(tmp_path: Path):
    with pytest.raises(KeyError):
        ilustracion.prompt_de("bandera_chile")

    with pytest.raises(KeyError):
        ilustracion.elegir("bandera_chile", hoy=date(2026, 10, 24), generar=None, banco=tmp_path)


def test_catalogo_tiene_los_once_motivos():
    assert set(ilustracion.motivos().keys()) == MOTIVOS_ESPERADOS


def test_ningun_prompt_pide_marca_ni_texto():
    prohibidas = ("logo de", "marca de", "texto que diga", "bandera de")
    for id_motivo, info in ilustracion.motivos().items():
        for prompt_bajo in (v.lower() for v in info["variantes"]):
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
    # Con dos imágenes en el banco se genera la tercera variante, no otra copia de la primera.
    assert ilustracion.motivos()["oro_lingotes"]["variantes"][2] in recibido[0][0]

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
        texto = " ".join(m["variantes"]).lower()
        assert "velas" not in texto and "monitores" not in texto and "pantallas múltiples" not in texto


def _banco(tmp_path: Path, motivo: str, n: int, hoy: date, dias: int = 1) -> list[Path]:
    d = tmp_path / motivo
    d.mkdir(parents=True, exist_ok=True)
    rutas = []
    usos = {}
    for i in range(n):
        r = d / f"{i}.png"
        r.write_bytes(PNG)
        rutas.append(r)
        usos[f"{motivo}/{r.name}"] = (hoy - timedelta(days=dias + i)).isoformat()
    (tmp_path / "uso.json").write_text(json.dumps(usos), encoding="utf-8")
    return rutas


def test_cada_motivo_tiene_al_menos_tres_variantes():
    """Un solo prompt por motivo producía la misma foto cada vez: seis fachadas idénticas (2026-10-26)."""
    for id_motivo, info in ilustracion.motivos().items():
        assert len(info["variantes"]) >= 3, id_motivo
        assert len(set(info["variantes"])) == len(info["variantes"]), id_motivo


def test_el_prompt_lleva_el_estilo_de_marca_y_la_variante():
    v = ilustracion.motivos()["plata"]["variantes"]
    p0, p1 = ilustracion.prompt_de("plata", 0), ilustracion.prompt_de("plata", 1)
    assert v[0] in p0 and v[1] in p1 and p0 != p1
    estilo = ilustracion.estilo()
    assert estilo and estilo in p0 and "Sin logos" in p0


def test_banco_completo_en_enfriamiento_reutiliza_sin_generar(tmp_path: Path):
    """Con una imagen por variante ya en disco, generar otra solo repetiría una foto que ya existe."""
    hoy = date(2026, 10, 24)
    n = len(ilustracion.motivos()["oro_lingotes"]["variantes"])
    rutas = _banco(tmp_path, "oro_lingotes", n, hoy)
    llamadas = []
    ruta, aviso = ilustracion.elegir("oro_lingotes", hoy=hoy, generar=lambda p, d: llamadas.append(d),
                                     banco=tmp_path)
    assert llamadas == [] and aviso is None
    assert ruta == rutas[-1]  # la de uso más antiguo


@pytest.mark.parametrize("motivo, ticker, esperado", [
    ("oro_lingotes", "XAGUSD", "plata"),       # el caso del 2026-10-26: noticia de plata con lingotes de oro
    ("plata", "XAUUSD", "oro_lingotes"),
    ("oro_lingotes", "XAUUSD", "oro_lingotes"),
    ("petroleo", "BRENT.spot", "petroleo"),
    ("cobre", "BTCUSD", "cripto"),
    ("banco_central", "XAGUSD", "banco_central"),  # un motivo sin dueño vale para cualquier activo
    ("billetes_dolar", "XAUUSD", "billetes_dolar"),
    ("oro_lingotes", "US100.spot", "banco_central"),  # materia prima ajena y el activo sin motivo propio
])
def test_motivo_para_no_pone_la_materia_prima_de_otro_activo(motivo, ticker, esperado):
    assert ilustracion.motivo_para(motivo, ticker) == esperado


def test_faltantes_lista_las_variantes_sin_imagen(tmp_path: Path):
    _banco(tmp_path, "plata", 1, date(2026, 10, 24))
    falta = ilustracion.faltantes(tmp_path)
    n_plata = len(ilustracion.motivos()["plata"]["variantes"])
    assert [i for m, i in falta if m == "plata"] == list(range(1, n_plata))
    assert ("oro_lingotes", 0) in falta
    assert len(falta) == sum(len(v["variantes"]) for v in ilustracion.motivos().values()) - 1
