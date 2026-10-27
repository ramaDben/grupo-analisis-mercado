"""Imágenes del correo en una URL pública: Gmail no muestra las que van embebidas en el HTML.

Titan (el correo de GoDaddy) convierte las imágenes pegadas en referencias `cid:` y al enviar no adjunta
los archivos, así que el cliente recibe huecos. Con una URL `https://` el correo las lleva tal cual y se
ven en cualquier cliente. Viven en el sitio público de GitHub Pages de la calculadora, en `correos/`.

El nombre sale del contenido (hash): la misma imagen es siempre la misma URL, una imagen nueva nunca pisa a
una anterior y los correos ya enviados siguen mostrando la suya.
"""
from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = "ramaDben/gi-calculadora-lotaje"
CARPETA = "correos"
BASE = f"https://ramadben.github.io/gi-calculadora-lotaje/{CARPETA}/"
ESPERA_PAGES_S = 240  # GitHub Pages tarda en servir un archivo recién subido
SONDEO_S = 5


class ImagenNoPublicada(RuntimeError):
    """No se pudo dejar la imagen en la URL pública: el correo no se vería en Gmail."""


def nombre_publico(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:24] + ruta.suffix.lower()


def url_publica(ruta: Path) -> str:
    return BASE + nombre_publico(ruta)


def _responde(url: str) -> bool:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=15) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _subir(ruta: Path, nombre: str) -> None:
    cuerpo = json.dumps({"message": f"correo: imagen {nombre}",
                         "content": base64.b64encode(ruta.read_bytes()).decode("ascii")}).encode("utf-8")
    try:
        res = subprocess.run(["gh", "api", "-X", "PUT", f"repos/{REPO}/contents/{CARPETA}/{nombre}", "--input", "-"],
                             input=cuerpo, capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ImagenNoPublicada(f"no pude correr gh para subir {ruta.name}: {exc}") from exc
    if res.returncode != 0 and b"already exists" not in res.stderr + res.stdout:
        raise ImagenNoPublicada(f"GitHub rechazó {ruta.name}: {res.stderr.decode('utf-8', 'replace').strip()[:200]}")


class Publicador:
    """Publica las imágenes de un correo en lote: sube todas primero y espera a Pages una sola vez.

    Se pasa como `publicar(ruta) -> url` y devuelve la URL apenas GitHub confirma la subida, sin esperar a
    que Pages la sirva: el nombre sale del contenido, así que esa URL es la definitiva. Esperar imagen por
    imagen hacía que un build lento (368 s el 2026-10-27) agotara la espera en la primera, que las demás no
    se subieran nunca y que el correo saliera entero sin imágenes. `confirmar()` hace la espera al final y
    devuelve las URLs que Pages todavía no sirve, para avisarlo; una subida rechazada sí falla en el acto.
    """

    def __init__(self) -> None:
        self._urls: dict[str, str] = {}
        self._pendientes: list[str] = []

    def __call__(self, ruta: Path) -> str:
        if not ruta.exists():
            raise ImagenNoPublicada(f"no existe {ruta}")
        nombre, url = nombre_publico(ruta), url_publica(ruta)
        if nombre not in self._urls:
            if not _responde(url):
                _subir(ruta, nombre)
                self._pendientes.append(url)
            self._urls[nombre] = url
        return url

    def confirmar(self) -> list[str]:
        """Espera a que Pages sirva lo subido y devuelve las URLs que siguen sin responder."""
        limite = time.monotonic() + ESPERA_PAGES_S
        while self._pendientes:
            self._pendientes = [u for u in self._pendientes if not _responde(u)]
            if not self._pendientes or time.monotonic() >= limite:
                break
            time.sleep(SONDEO_S)
        return list(self._pendientes)
