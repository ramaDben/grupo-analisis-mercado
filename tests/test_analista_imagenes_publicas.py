"""Las imágenes del correo en una URL pública: nombre por contenido, sin subir dos veces, sin fallar callado."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from analista import imagenes_publicas as ip  # noqa: E402


def _png(tmp_path, nombre="a.png", contenido=b"PNG-uno"):
    ruta = tmp_path / nombre
    ruta.write_bytes(contenido)
    return ruta


def test_el_nombre_sale_del_contenido_no_del_archivo(tmp_path):
    a, b = _png(tmp_path, "a.png"), _png(tmp_path, "b.png")
    c = _png(tmp_path, "c.png", b"PNG-otro")
    assert ip.url_publica(a) == ip.url_publica(b) != ip.url_publica(c)
    assert ip.url_publica(a).startswith("https://ramadben.github.io/") and ip.url_publica(a).endswith(".png")


def test_una_imagen_ya_publicada_no_se_vuelve_a_subir(tmp_path, monkeypatch):
    monkeypatch.setattr(ip, "_responde", lambda url: True)
    monkeypatch.setattr(ip, "_subir", lambda *a: pytest.fail("no deba subir"))
    ruta = _png(tmp_path)
    assert ip.publicar(ruta) == ip.url_publica(ruta)


def test_una_imagen_nueva_se_sube_y_se_espera_a_que_la_url_responda(tmp_path, monkeypatch):
    respuestas = iter([False, False, True])
    subidas = []
    monkeypatch.setattr(ip, "_responde", lambda url: next(respuestas))
    monkeypatch.setattr(ip, "_subir", lambda ruta, nombre: subidas.append(nombre))
    monkeypatch.setattr(ip.time, "sleep", lambda s: None)
    ruta = _png(tmp_path)
    assert ip.publicar(ruta) == ip.url_publica(ruta)
    assert subidas == [ip.nombre_publico(ruta)]


def test_si_la_url_nunca_responde_falla_en_voz_alta(tmp_path, monkeypatch):
    monkeypatch.setattr(ip, "_responde", lambda url: False)
    monkeypatch.setattr(ip, "_subir", lambda *a: None)
    monkeypatch.setattr(ip, "ESPERA_PAGES_S", 0)
    with pytest.raises(ip.ImagenNoPublicada):
        ip.publicar(_png(tmp_path))
