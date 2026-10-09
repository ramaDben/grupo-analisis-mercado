"""Lo que sale de una pieza comercial: la lámina, el correo y el texto de WhatsApp.

La pieza semanal y su seguimiento no van en PDF como el resto del bot: el
ejecutivo reenvía la imagen y el texto por WhatsApp y pega el correo en
Outlook. Las tres salidas se arman desde el mismo `pieza.json` ya validado, así
las cifras coinciden entre imagen, correo y texto.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from analista import autor as au
from analista import semanal as sm

PLANTILLAS = {"semanal": "semanal.html", "seguimiento": "seguimiento.html"}


def firma(autor: au.Autor) -> str:
    """El análisis es de quien lo firma; quien lo envía va aparte (criterio 8 del plan)."""
    return f"Análisis: {autor.nombre} · {autor.cargo}"


def payload_imagen(pieza: dict[str, Any], dir_pedido: Path, autor: au.Autor) -> dict[str, Any]:
    d, ed = pieza["datos"], pieza["editorial"]
    esc = d["escenario"]
    f = esc["fmt"]
    comunes = {
        "chip": d["chip"], "datos_al": d["datos_al"], "activo": f"{d['nombre']} · {d['ticker_visible']}",
        "gatillo": f["gatillo"], "invalidacion": f["invalidacion"], "distancia": f["recorrido"],
        "pie_imagen": d["pie_imagen"], "firma": firma(autor), "aviso": sm.AVISO_CORTO,
        "chart_png": str(dir_pedido / pieza["imagenes"]["principal"]),
    }
    if pieza["orden"]["pieza"] == "semanal":
        alcista = esc["sesgo"] == "Alcista"
        return {**comunes, "titular": ed["titular"], "precio": f"{d['precio']} {d['unidad']}".strip(),
                "direccion": esc["sesgo"].upper(), "sesgo": esc["sesgo"],
                "lado": "sobre" if alcista else "bajo", "borde": "bajo" if alcista else "sobre",
                "temporalidad": d["temporalidad"]}
    ev = d["evaluacion"]
    avance = ev.get("avance_pct")
    return {**comunes, "direccion": esc["sesgo"].lower(), "sello": sm.SELLOS[ev["estado"]],
            "precio_lunes": d["precio_lunes"], "precio_hoy": d["precio_hoy"],
            "avance": f"{avance} % del recorrido de referencia" if avance is not None else "Sin activarse aún",
            "hoy": ed["hoy"]}


def rendir_imagen(pieza: dict[str, Any], dir_pedido: Path, autor: au.Autor,
                  render: Callable[..., Path] | None = None) -> Path:
    """La lámina horizontal 1920×1080 que se reenvía por WhatsApp."""
    import pipeline_avisos as pa

    if render is None:
        from story_render import render_story as render
    destino = dir_pedido / "imagen.png"
    render(payload_imagen(pieza, dir_pedido, autor), pa.DIR_PLANTILLAS / PLANTILLAS[pieza["orden"]["pieza"]],
           destino, formato="horizontal")
    return destino


def texto_whatsapp(pieza: dict[str, Any]) -> str:
    if pieza["orden"]["pieza"] == "semanal":
        return sm.mensaje_whatsapp(pieza)
    return sm.mensaje_seguimiento(pieza)


def escribir_whatsapp(pieza: dict[str, Any], dir_pedido: Path) -> tuple[Path, str]:
    """El texto validado, guardado junto a la pieza: lo que sale es lo que queda."""
    # `validar_mensaje_whatsapp` es del canal comunitario (exige el Manual y una
    # pregunta abierta): acá vale la parte genérica, guion largo y voseo.
    from validador_editorial import validar_texto

    texto = texto_whatsapp(pieza)
    errores = validar_texto(texto, campo="whatsapp")
    if errores:
        raise ValueError("; ".join(errores))
    ruta = dir_pedido / "whatsapp.txt"
    ruta.write_text(texto + "\n", encoding="utf-8")
    return ruta, texto
