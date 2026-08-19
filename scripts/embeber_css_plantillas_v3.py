#!/usr/bin/env python3
"""Embebe CSS de manera más robusta, manejando variaciones de espaciado."""
import re
from pathlib import Path

STORIES_DIR = Path("templates/stories")

# Leer CSS
marca_css = (STORIES_DIR / "marca.css").read_text(encoding="utf-8")
piel_css = (STORIES_DIR / "piel.css").read_text(encoding="utf-8")

# Extraer solo reglas (sin comentarios largos)
def extraer_css_reglas(css_texto: str) -> str:
    lineas = []
    en_comentario_largo = False
    for linea in css_texto.split("\n"):
        if "/*" in linea and "/*" == linea.strip()[:2]:
            en_comentario_largo = True
        if "*/" in linea:
            en_comentario_largo = False
            if len(linea) < 80:
                lineas.append(linea)
            continue
        if not en_comentario_largo:
            lineas.append(linea)
    return "\n".join(lineas)

marca_reglas = extraer_css_reglas(marca_css)
piel_reglas = extraer_css_reglas(piel_css)

styles_marca_piel = f"""  /* ════ marca.css embebido ════ */
{marca_reglas}

  /* ════ piel.css embebido ════ */
{piel_reglas}"""

styles_solo_marca = f"""  /* ════ marca.css embebido ════ */
{marca_reglas}"""

# Plantillas y su configuración
plantillas_config = {
    "oportunidad.html": (True, False),
    "alerta.html": (True, False),
    "recomendacion.html": (True, False),
    "operacion.html": (False, False),
    "quote.html": (True, True),
    "breaking.html": (True, True),
    "encuesta.html": (True, True),
    "edu.html": (True, True),
    "flash.html": (True, True),
    "postventa.html": (True, True),
    "dato_macro.html": (True, True),
    "calendario.html": (False, False),
}

for plantilla_nombre, (tiene_piel, necesita_update) in plantillas_config.items():
    plantilla_path = STORIES_DIR / plantilla_nombre

    if not plantilla_path.exists():
        print(f"[SKIP] {plantilla_nombre} no existe")
        continue

    contenido = plantilla_path.read_text(encoding="utf-8")

    if "marca.css embebido" in contenido:
        print(f"[OK]   {plantilla_nombre} ya tiene CSS embebido")
        continue

    if not necesita_update:
        print(f"[SKIP] {plantilla_nombre} (no necesita update)")
        continue

    styles_a_insertar = styles_marca_piel if tiene_piel else styles_solo_marca

    # Patrón flexible: permite cualquier espaciado
    if tiene_piel:
        # marca + piel
        patron = r'<link\s+rel="stylesheet"\s+href="marca\.css"\s*>\s*\n\s*<link\s+rel="stylesheet"\s+href="piel\.css"\s*>\s*\n\s*<style>'
    else:
        # solo marca
        patron = r'<link\s+rel="stylesheet"\s+href="marca\.css"\s*>\s*\n\s*<style>'

    if not re.search(patron, contenido):
        # Si aún no coincide, intentar detectar manualmente
        if '<link rel="stylesheet" href="marca.css">' in contenido and '<style>' in contenido:
            # Hacer reemplazo simple
            nuevo_contenido = contenido.replace(
                '<link rel="stylesheet" href="marca.css">\n<style>',
                f'<style>\n{styles_a_insertar}\n</style>\n<style>'
            )
            if nuevo_contenido == contenido:
                # Intentar sin \n
                nuevo_contenido = contenido.replace(
                    '<link rel="stylesheet" href="marca.css">\n<link rel="stylesheet" href="piel.css">\n<style>',
                    f'<style>\n{styles_a_insertar}\n</style>\n<style>'
                )
        else:
            print(f"[FAIL] {plantilla_nombre}")
            continue
    else:
        nuevo_contenido = re.sub(
            patron,
            f"<style>\n{styles_a_insertar}\n</style>\n<style>",
            contenido
        )

    if nuevo_contenido != contenido:
        plantilla_path.write_text(nuevo_contenido, encoding="utf-8")
        print(f"[DONE] {plantilla_nombre}")
    else:
        print(f"[FAIL] {plantilla_nombre} (no se realizó cambio)")

print("\n=== Verificacion final ===")
for plantilla_nombre in plantillas_config.keys():
    plantilla_path = STORIES_DIR / plantilla_nombre
    if plantilla_path.exists():
        contenido = plantilla_path.read_text(encoding="utf-8")
        tiene_embebido = "marca.css embebido" in contenido
        if tiene_embebido:
            print(f"[OK] {plantilla_nombre}")
        else:
            print(f"[TODO] {plantilla_nombre}")
