"""Piezas de la maqueta HTML que comparte la pieza semanal: escape, firma y fuentes.

Agy solo aporta textos y entran escapados: nada de lo que escribió puede convertirse en
etiqueta. No se personaliza: nadie en GI está inscrito como asesor de inversión.
"""
from __future__ import annotations

import base64
import html
import io
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

try:
    from PIL import Image
    _TIENE_PIL = True
except ImportError:
    _TIENE_PIL = False

from analista import RAIZ
from analista import autor as au

MARCA_CSS = RAIZ / "templates" / "stories" / "marca.css"
LOGO = RAIZ / "templates" / "stories" / "assets" / "LOGO Blanco.png"

FRASE_GENERAL = ("Análisis general de mercado, idéntico para todos sus destinatarios. "
                 "No es asesoría de inversión ni considera el perfil de quien lo lee.")


def e(texto: Any) -> str:
    return html.escape(str(texto), quote=True)


def slug(texto: str) -> str:
    plano = unicodedata.normalize("NFKD", texto)
    plano = "".join(c for c in plano if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "_", plano).strip("_")


def _data_uri(ruta: Path, ancho_max: int | None = None, calidad: int = 85, a_jpeg: bool = False) -> str:
    """La imagen embebida. Con `ancho_max` o `a_jpeg`, y Pillow a mano (llega con el extra `informe`), se reduce
    antes de embeberla: la foto del autor pesaba 850 KB para mostrarse a 80 px. Una imagen que no existe
    falla, como siempre: una pieza sin su imagen no sale."""
    if _TIENE_PIL and (ancho_max is not None or a_jpeg):
        try:
            with Image.open(ruta) as im:
                w, h = im.size
                if ancho_max is not None and w > ancho_max:
                    nuevo_h = max(1, round(h * ancho_max / w))
                    im = im.resize((ancho_max, nuevo_h), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                es_jpeg = a_jpeg or ruta.suffix.lower() in (".jpg", ".jpeg")
                tiene_alfa = im.mode in ("RGBA", "LA") or ("transparency" in im.info)
                if es_jpeg and not tiene_alfa:
                    if im.mode != "RGB":
                        im = im.convert("RGB")
                    im.save(buf, format="JPEG", quality=calidad, optimize=True)
                    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"
                if not tiene_alfa and im.mode == "RGB":
                    im.save(buf, format="JPEG", quality=calidad, optimize=True)
                    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"
                im.save(buf, format="PNG", optimize=True)
                return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"
        except (OSError, ValueError):  # una imagen que Pillow no sabe leer va tal cual
            pass
    tipo = "image/png" if ruta.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{tipo};base64,{base64.b64encode(ruta.read_bytes()).decode('ascii')}"


def pildora(direccion: str) -> str:
    return f'<span class="direccion {slug(direccion)}">{e(direccion.upper())}</span>'


def _fuentes() -> str:
    from guia_usdclp.estilos import caras_de_fuente

    return caras_de_fuente()


def bloque_firma(a: au.Autor, hoy: date, incluir_general: bool = True) -> str:
    """Quién firma, con la acreditación solo si sigue vigente a la fecha del pedido."""
    foto = f'<img class="firma-foto" src="{_data_uri(a.foto, ancho_max=160, calidad=85, a_jpeg=True)}" alt="{e(a.nombre)}">' if a.foto else ""
    trazo = f'<img class="firma-trazo" src="{_data_uri(a.firma)}" alt="Firma">' if a.firma else ""
    credencial = ""
    if au.vigente(a, hoy):
        ac = a.acreditacion
        hasta = date.fromisoformat(ac["vigente_hasta"]).strftime("%d-%m-%Y")
        # Sin enlace aunque el config traiga uno: el de la CMV no reconocía el certificado.
        credencial = (
            f'<p class="firma-credencial">Acreditación {e(ac["entidad"])} · Categoría {e(ac["categoria"])}'
            f' · N° {e(ac["numero"])} · Vigente hasta el {hasta}</p>'
        )
    general = f'<p class="firma-general">{e(FRASE_GENERAL)}</p>' if incluir_general else ""
    return (
        f'<section class="firma">{foto}<div class="firma-texto">{trazo}'
        f'<p class="firma-nombre">{e(a.nombre)}</p>'
        f'<p class="firma-cargo">{e(a.cargo)} · Grupo Inteligencia</p>{credencial}'
        f'{general}</div></section>'
    )
