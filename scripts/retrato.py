"""Recorte circular del retrato del autor, compartido por los materiales de capacitación.

Lo usan el generador del PPTX y el de la guía rápida. Vive aparte porque el folleto no
puede importar del módulo del PPTX sin arrastrar `python-pptx`, que no está en el
entorno del proyecto (se inyecta con `uv run --with`).

Ni PowerPoint ni el PDF aplican máscaras a una imagen, así que el círculo se recorta
antes con Pillow.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

EXTENSIONES = (".png", ".jpg", ".jpeg", ".webp")

# Encuadre calibrado comparando recortes en el tamaño real de uso: con un círculo
# inscrito completo el rostro no se reconoce, y cerrando más se corta la cabeza.
ZOOM = 1.15
CENTRO_Y = 0.47


def resolver(ruta: Path | None) -> Path | None:
    """Ubica el retrato. Si la ruta exacta no existe, toma cualquier imagen de la
    carpeta: el archivo suele llegar con el nombre que le pone WhatsApp."""
    if ruta is None:
        return None
    if ruta.exists():
        return ruta
    carpeta = ruta.parent
    if not carpeta.is_dir():
        return None
    candidatas = sorted(
        archivo for archivo in carpeta.iterdir()
        if archivo.suffix.lower() in EXTENSIONES and not archivo.name.startswith(".")
    )
    if candidatas:
        print(f"  retrato: se usa {candidatas[0].name}")
        return candidatas[0]
    return None


def recortar(origen: Path, lado: int = 720, zoom: float = ZOOM,
             centro_y: float = CENTRO_Y, aro: bool = True) -> Path | None:
    """Devuelve un PNG circular temporal, con aro de acento opcional."""
    try:
        from PIL import Image, ImageDraw  # noqa: PLC0415
    except ImportError:
        print("  aviso: Pillow no disponible, la foto se omite")
        return None

    imagen = Image.open(origen).convert("RGBA")
    corto = int(min(imagen.size) / max(1.0, zoom))
    izq = max(0, (imagen.width - corto) // 2)
    arriba = max(0, min(int(imagen.height * centro_y - corto / 2),
                        imagen.height - corto))
    imagen = imagen.crop((izq, arriba, izq + corto, arriba + corto))
    imagen = imagen.resize((lado, lado), Image.LANCZOS)

    # La máscara se dibuja al cuádruple y se reduce: es la forma barata de obtener
    # un borde antialiasado en el círculo.
    mascara = Image.new("L", (lado * 4, lado * 4), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, lado * 4 - 1, lado * 4 - 1), fill=255)
    imagen.putalpha(mascara.resize((lado, lado), Image.LANCZOS))

    if aro:
        grosor = max(2, lado // 120)
        ImageDraw.Draw(imagen).ellipse(
            (grosor // 2, grosor // 2, lado - grosor // 2, lado - grosor // 2),
            outline=(0, 220, 130, 255), width=grosor)

    destino = Path(tempfile.gettempdir()) / f"gi_retrato_{origen.stem}_{lado}.png"
    imagen.save(destino, "PNG")
    return destino
