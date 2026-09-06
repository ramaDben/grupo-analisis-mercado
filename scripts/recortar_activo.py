# punto-de-entrada: lo corre el director a mano al sumar la foto de un activo nuevo
"""Recorta el fondo de una foto de activo y deja un PNG con transparencia.

Existe porque el equipo no tiene Photoshop ni un diseñador disponible, y las
fotos utilizables de los bancos libres casi siempre vienen sobre fondo claro de
estudio — que es justo lo que no sirve para una pieza de fondo negro.

Método: separa por SATURACIÓN, no por color ni por luminancia. Los fondos de
estudio son grises o beige (saturación baja) mientras el objeto —oro, cobre,
crudo— es cromático (saturación alta). Un umbral de luminancia fallaría con los
reflejos claros del metal; uno de croma los conserva.

Los reflejos especulares casi blancos sí tienen saturación baja y abrirían
agujeros dentro del objeto, así que la máscara se cierra morfológicamente
(MaxFilter y luego MinFilter) antes de suavizar el borde.

    uv run --with pillow python scripts/recortar_activo.py entrada.jpg salida.png
    uv run --with pillow python scripts/recortar_activo.py entrada.jpg salida.png --umbral 40

Si el recorte no convence, la alternativa es `rembg` (modelo local de segmentación,
~176 MB la primera vez) o la función "quitar fondo" de Canva. Este script cubre el
caso común —objeto cromático sobre fondo neutro— sin descargar nada.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageFilter


def construir_alfa(im: Image.Image, umbral: int, suavizado: float, umbral_luz: int = 118) -> Image.Image:
    """Canal alfa cruzando croma y luminancia.

    Es fondo lo que cumple las DOS condiciones: poco saturado **y** claro. Con
    croma solo, un beige de estudio sobrevive —tiene algo de saturación— y deja
    un halo alrededor del objeto. Con luminancia sola, los reflejos del metal se
    borran. El cruce respeta además las sombras propias del objeto, que son
    oscuras y desaturadas: caen del lado "objeto" y por eso se conservan.

    `umbral` es la saturación bajo la cual un píxel es candidato a fondo;
    `umbral_luz`, el valor sobre el cual se considera claro.
    """
    hsv = im.convert("HSV")
    saturacion, valor = hsv.getchannel("S"), hsv.getchannel("V")

    # Rampa en vez de corte duro: un borde binario se ve dentado sobre el negro.
    ancho_rampa = 26
    por_croma = saturacion.point(
        lambda s: 0 if s < umbral else min(255, int((s - umbral) * 255 / ancho_rampa))
    )
    # Lo oscuro es objeto aunque no tenga color (sombras propias, cantos).
    por_luz = valor.point(lambda v: 255 if v < umbral_luz else 0)

    alfa = Image.new("L", im.size)
    alfa.paste(por_croma)
    alfa.paste(255, mask=por_luz)

    # Cierre morfológico: tapa los agujeros que dejan los reflejos especulares
    # (casi blancos, saturación baja) dentro del objeto.
    alfa = alfa.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))

    return alfa.filter(ImageFilter.GaussianBlur(suavizado))


def recortar(entrada: Path, salida: Path, umbral: int, suavizado: float, ancho: int,
             umbral_luz: int = 118) -> Path:
    im = Image.open(entrada).convert("RGB")
    if ancho and im.width > ancho:
        im.thumbnail((ancho, ancho * 4))

    im.putalpha(construir_alfa(im, umbral, suavizado, umbral_luz))

    # Recorta el lienzo al contenido: el aire sobrante descuadra el encuadre en
    # la plantilla, que centra la imagen por su caja.
    caja = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if caja:
        im = im.crop(caja)

    salida.parent.mkdir(parents=True, exist_ok=True)
    im.save(salida)
    return salida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--umbral", type=int, default=34, help="saturación mínima del objeto (0-255)")
    parser.add_argument("--suavizado", type=float, default=1.4, help="desenfoque del borde, en píxeles")
    parser.add_argument("--ancho", type=int, default=1600, help="ancho máximo de salida")
    parser.add_argument("--umbral-luz", type=int, default=118, help="valor sobre el cual un píxel desaturado es fondo")
    args = parser.parse_args(argv)

    if not args.entrada.exists():
        print(f"ERROR: no existe {args.entrada}", file=sys.stderr)
        return 1

    ruta = recortar(args.entrada, args.salida, args.umbral, args.suavizado, args.ancho, args.umbral_luz)
    im = Image.open(ruta)
    print(f"{ruta}  {im.width}x{im.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
