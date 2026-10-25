"""Las imágenes ilustrativas del correo las genera agy; Python solo comprueba que el archivo quedó.

Medido el 2026-10-24: agy headless (Flash) generó un PNG de 1376×768 en 76 s y lo dejó en la ruta
pedida. El prompt lo arma `ilustracion.prompt_de` (con las prohibiciones fijas), nunca agy. Un
"SUCCESS" de agy no prueba nada: vale el archivo en disco y su firma de imagen.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

Generador = Callable[[str, Path], Path]

TIMEOUT = "10m"
_FIRMAS = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")


class ImagenNoGenerada(RuntimeError):
    """agy no dejó una imagen válida en la ruta pedida."""


def _invocar_real(prompt: str, tier: str, timeout: str) -> Any:
    from agy_encargo import invocar

    return invocar(prompt, tier, timeout)


def generar_con_agy(prompt: str, destino: Path, tier: str = "flash", timeout: str = TIMEOUT,
                    invocar: Callable[[str, str, str], Any] = _invocar_real) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    encargo = (
        "Usa tu herramienta de generación de imágenes (generate_image) para crear esta imagen: "
        f"{prompt} Guarda el archivo resultante exactamente en {destino.as_posix()} (cópialo ahí si la "
        "herramienta lo deja en otra carpeta). No modifiques ningún otro archivo. "
        "Responde solo la ruta final o ERROR: <motivo>."
    )
    res = invocar(encargo, tier, timeout)
    if getattr(res, "codigo", "ok") != "ok":
        raise ImagenNoGenerada(f"agy no terminó ({res.codigo}: {res.detalle})")
    if not destino.exists():
        raise ImagenNoGenerada(f"agy no dejó la imagen en {destino.name}")
    if not destino.read_bytes()[:8].startswith(_FIRMAS):
        raise ImagenNoGenerada(f"{destino.name} no es un PNG ni un JPEG")
    return destino
