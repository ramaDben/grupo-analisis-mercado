# -*- coding: utf-8 -*-
# punto-de-entrada: lo corre el director a mano; genera las Instrucciones del Simulador GI en PDF y HTML para post-venta
"""Genera las Instrucciones de uso del Simulador GI, en PDF A4 y en HTML autónomo.

Reemplaza al README.md que acompañaba la planilla: el destinatario es el equipo de
post-venta, no un desarrollador, y un .md se abre en el Bloc de notas sin formato.

Dos salidas del mismo HTML:

- **PDF A4** para imprimir o adjuntar al correo.
- **HTML autónomo**, con las fuentes y el logo incrustados en base64, así el archivo
  funciona solo. Bajo 820 px de ancho las hojas A4 se rompen en una columna, para
  consultarlo en el teléfono sin hacer zoom.

Los umbrales de margen del broker se leen de la cuenta MT5 (margin_so_call y
margin_so_so) en vez de escribirse a mano, igual que en el generador de la planilla.
Si el terminal no está disponible cae a los valores conocidos y avisa.

La escala del HTML está calibrada al alto útil de una A4 (1123 px a 96 dpi). Al agregar
contenido hay que MEDIR, no estimar: si una hoja se pasa, Chromium la parte en dos y el
PDF duplica páginas. La medición va incluida en este script y falla si eso ocurre.

    uv run --extra stories --with MetaTrader5 --with tzdata \
        python scripts/instrucciones_simulador.py
"""
import base64
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "templates" / "calculadoras" / "instrucciones.html"
FUENTES = RAIZ / "templates" / "stories" / "fonts"
SALIDA = RAIZ / "calculadoras excel"
LOGO = SALIDA / "assets" / "logo_gi.png"

# DM Sans para títulos y cuerpo; Space Grotesk solo para cifras y siglas, donde
# importa el alineado tabular. Syne queda fuera a propósito: en peso 800 sus
# contraformas se cierran y en un documento de consulta cansa la vista.
CATALOGO = [
    ("dm-sans-400.woff2", "DM Sans", 400),
    ("dm-sans-700.woff2", "DM Sans", 700),
    ("space-grotesk-600.woff2", "Space Grotesk", 600),
]

# alto útil de una A4 a 96 dpi, con holgura de 2 px por el redondeo del layout
ALTO_A4 = 1123 + 2


def bloque_fuentes() -> str:
    reglas = []
    for archivo, familia, peso in CATALOGO:
        ruta = FUENTES / archivo
        if not ruta.exists():
            print("  aviso: falta %s, se usará la tipografía de sistema" % archivo)
            continue
        datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
        reglas.append(
            '@font-face{font-family:"%s";font-weight:%d;font-style:normal;'
            'font-display:swap;src:url(data:font/woff2;base64,%s) format("woff2")}'
            % (familia, peso, datos)
        )
    return "\n".join(reglas)


def bloque_logo() -> str:
    if not LOGO.exists():
        print("  aviso: sin logo en %s" % LOGO)
        return ""
    datos = base64.b64encode(LOGO.read_bytes()).decode("ascii")
    return '<img src="data:image/png;base64,%s" alt="GI">' % datos


def umbrales_broker() -> tuple[float, float]:
    """Llamada a margen y cierre forzado, leídos de la cuenta."""
    try:
        import MetaTrader5 as mt5  # noqa: PLC0415
        if mt5.initialize():
            cuenta = mt5.account_info()
            mt5.shutdown()
            if cuenta:
                return cuenta.margin_so_call, cuenta.margin_so_so
    except Exception as e:                                   # noqa: BLE001
        print("  aviso: sin terminal (%s)" % e)
    print("  aviso: umbrales por defecto, verificar con el broker")
    return 90.0, 50.0


def construir_html() -> str:
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    llamada, cierre = umbrales_broker()
    ahora = datetime.now(ZoneInfo("America/Santiago"))
    for marcador in ("/*FUENTES*/", "{{LOGO}}", "{{LLAMADA}}", "{{CIERRE}}", "{{FECHA}}"):
        if marcador not in plantilla:
            raise SystemExit("la plantilla no tiene el marcador %s" % marcador)
    return (plantilla
            .replace("/*FUENTES*/", bloque_fuentes())
            .replace("{{LOGO}}", bloque_logo())
            .replace("{{LLAMADA}}", "%g" % llamada)
            .replace("{{CIERRE}}", "%g" % cierre)
            .replace("{{FECHA}}", ahora.strftime("%d-%m-%Y")))


def escribir_pdf(html: Path, destino: Path) -> None:
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page()
        pagina.goto(html.as_uri())
        pagina.emulate_media(media="print")
        pagina.wait_for_timeout(400)  # que terminen de aplicarse las fuentes

        # medir antes de exportar: una hoja que se pasa del alto de la A4 se parte en
        # dos y el PDF duplica páginas sin avisar
        altos = pagina.evaluate(
            "Array.from(document.querySelectorAll('section.hoja'))"
            ".map(s => s.getBoundingClientRect().height)")
        for i, alto in enumerate(altos, start=1):
            estado = "ok" if alto <= ALTO_A4 else "SE PASA"
            print("  hoja %d: %.0f px de %d  ->  %s" % (i, alto, ALTO_A4, estado))
        excedidas = [i for i, a in enumerate(altos, start=1) if a > ALTO_A4]

        pagina.pdf(path=str(destino), format="A4", print_background=True,
                   margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        navegador.close()

    if excedidas:
        raise SystemExit("hojas que se pasan del alto A4: %s. Hay que recortar contenido "
                         "o ajustar la escala antes de entregar el PDF." % excedidas)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta_html = SALIDA / "Instrucciones de uso.html"
    ruta_html.write_text(construir_html(), encoding="utf-8")
    print("HTML -> %s (%.0f KB)"
          % (ruta_html.name, ruta_html.stat().st_size / 1024))

    ruta_pdf = SALIDA / "Instrucciones de uso.pdf"
    escribir_pdf(ruta_html, ruta_pdf)
    print("PDF  -> %s (%.0f KB)"
          % (ruta_pdf.name, ruta_pdf.stat().st_size / 1024))


if __name__ == "__main__":
    main()
