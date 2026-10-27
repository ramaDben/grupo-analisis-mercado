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


# ── El lote: subir todo primero y esperar una sola vez (2026-10-27) ──
# Un build de Pages tardó 368 s: la primera imagen agotó la espera, el bot abandonó las demás sin subirlas y
# el correo salió entero sin imágenes, aunque la que se subió quedó servida minutos después.

def test_el_lote_sube_todas_antes_de_esperar(tmp_path, monkeypatch):
    eventos = []
    monkeypatch.setattr(ip, "_responde", lambda url: eventos.append(("sondeo", url)) or len(eventos) > 4)
    monkeypatch.setattr(ip, "_subir", lambda ruta, nombre: eventos.append(("sube", nombre)))
    monkeypatch.setattr(ip.time, "sleep", lambda s: None)
    a, b = _png(tmp_path, "a.png", b"uno"), _png(tmp_path, "b.png", b"dos")
    pub = ip.Publicador()
    assert pub(a) == ip.url_publica(a) and pub(b) == ip.url_publica(b)
    assert [e for e in eventos if e[0] == "sube"] == [("sube", ip.nombre_publico(a)), ("sube", ip.nombre_publico(b))]
    assert pub.confirmar() == []


def test_la_misma_imagen_no_se_sube_dos_veces_en_el_lote(tmp_path, monkeypatch):
    subidas = []
    monkeypatch.setattr(ip, "_responde", lambda url: False)
    monkeypatch.setattr(ip, "_subir", lambda ruta, nombre: subidas.append(nombre))
    pub = ip.Publicador()
    ruta = _png(tmp_path)
    pub(ruta), pub(ruta)
    assert subidas == [ip.nombre_publico(ruta)]


def test_una_subida_confirmada_conserva_su_url_aunque_pages_tarde(tmp_path, monkeypatch):
    monkeypatch.setattr(ip, "_responde", lambda url: False)
    monkeypatch.setattr(ip, "_subir", lambda *a: None)
    monkeypatch.setattr(ip, "ESPERA_PAGES_S", 0)
    ruta = _png(tmp_path)
    pub = ip.Publicador()
    assert pub(ruta) == ip.url_publica(ruta)
    assert pub.confirmar() == [ip.url_publica(ruta)]


def test_si_github_rechaza_la_subida_el_lote_falla_en_voz_alta(tmp_path, monkeypatch):
    def rechaza(*a):
        raise ip.ImagenNoPublicada("GitHub rechazó a.png")
    monkeypatch.setattr(ip, "_responde", lambda url: False)
    monkeypatch.setattr(ip, "_subir", rechaza)
    with pytest.raises(ip.ImagenNoPublicada):
        ip.Publicador()(_png(tmp_path))


def test_las_ya_servidas_no_se_sondean_al_confirmar(tmp_path, monkeypatch):
    monkeypatch.setattr(ip, "_responde", lambda url: True)
    monkeypatch.setattr(ip, "_subir", lambda *a: pytest.fail("no deba subir"))
    pub = ip.Publicador()
    pub(_png(tmp_path))
    monkeypatch.setattr(ip, "_responde", lambda url: pytest.fail("no deba sondear"))
    assert pub.confirmar() == []
