"""Motor de render de Stories GI (issue #109; generalizado a 16:9 en el issue #119).

Único renderer del repo para Stories de marca (`data/stories/`): mapea un payload de
datos (JSON) sobre un snapshot HTML estático y produce un PNG 1920x1080 con Playwright
headless. No contiene lógica de negocio -- la recolección de datos (niveles del motor,
narrativa editorial, formateo de precios) vive en el prompt `.claude/commands/story.md`;
este módulo solo sabe payload -> HTML -> PNG (design.md D1/D2).

Mecanismo de inyección (D1 + generalización #119): tokens `{{campo}}` derivados
dinámicamente del payload, fences `<!-- IF:nombre -->...<!-- ENDIF:nombre -->` y
bloques de repetición `<!-- FOR:clave -->...<!-- ENDFOR:clave -->`, resueltos con
`re`/`str` de la stdlib (sin Jinja2 -- las llaves del CSS embebido chocarían con
`str.format`).

El import de Playwright es perezoso (dentro de `render_png`): los tests puros de
mapeo (`build_context`/`resolver_loops`/`build_html`) importan este módulo sin
necesitar Playwright instalado, igual que el patrón ya usado para `MetaTrader5` en
el MCP.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

# Fences complementarios y sus condiciones de presencia (D1). El orden es fijo dentro
# de `build_html`: primero loops, después fences, después tokens escalares, al final
# la guardia.
_FENCES = ("variacion", "vol", "chart_img", "chart_svg")

# Patrones de `resolver_loops`/`_expandir_elemento` (R4, #119). Backreference `\1`
# para anclar FOR/ENDFOR (o IF/ENDIF) a la misma clave y evitar cruces entre bloques
# distintos.
_PATRON_FOR = re.compile(
    r"<!--\s*FOR:(\w+)\s*-->(.*?)<!--\s*ENDFOR:\1\s*-->", re.DOTALL
)
_PATRON_IF_ELEMENTO = re.compile(
    r"<!--\s*IF:(\w+)\s*-->(.*?)<!--\s*ENDIF:\1\s*-->", re.DOTALL
)

_MSG_CHROMIUM_AUSENTE = (
    "No se pudo lanzar Chromium para renderizar la Story. Instala el navegador con:\n"
    "  uv sync --extra stories && python -m playwright install chromium"
)

# Formatos de lienzo soportados. El formato es **presentación**, así que viaja
# por el CLI/argumento y NUNCA por el payload -- el payload es contrato de
# contenido, y esa separación es lo que permite que el mismo payload rinda
# ambos formatos sin duplicarse. El snapshot no declara su tamaño: lo manda el
# viewport y el CSS se adapta con `@media (max-aspect-ratio: 1/1)`.
_FORMATOS: dict[str, tuple[int, int]] = {
    "horizontal": (1920, 1080),
    "vertical": (1080, 1920),
}
_FORMATO_DEFECTO = "horizontal"


def resolver_viewport(formato: str = _FORMATO_DEFECTO) -> tuple[int, int]:
    """Traduce el nombre de formato a `(ancho, alto)` del viewport.

    Un formato desconocido lanza `StoryRenderError` nombrando los válidos --
    mismo contrato de error accionable que el resto del módulo, nunca un
    `KeyError` crudo.
    """
    try:
        return _FORMATOS[formato]
    except KeyError as exc:
        validos = ", ".join(sorted(_FORMATOS))
        raise StoryRenderError(
            f"Formato de Story desconocido: {formato!r}. Válidos: {validos}."
        ) from exc


class StoryRenderError(RuntimeError):
    """Error accionable del motor de render de Stories (nunca traceback críptico)."""


def _fence_presente(nombre: str, payload: dict[str, Any]) -> bool:
    """Determina si un bloque `<!-- IF:nombre -->` debe conservarse (D1)."""
    if nombre == "variacion":
        return payload.get("variacion") is not None
    if nombre == "vol":
        return payload.get("vol_pct") is not None
    if nombre == "chart_img":
        return bool(payload.get("chart_png"))
    if nombre == "chart_svg":
        return not payload.get("chart_png")
    raise StoryRenderError(f"Fence desconocido en build_html: {nombre!r}")


def _aplicar_helper_flecha_direccion(
    contexto: dict[str, str], payload: dict[str, Any]
) -> None:
    """Helper 1 del catálogo (R5): cualquier clave top-level cuyo valor sea un
    `dict` con clave `direccion` (ej. `variacion`) deriva `{contenedor}_flecha` =
    `▲` (`alcista`) / `▼` (`bajista`) / `""` (otro valor) y además aplana los
    escalares del objeto a `{contenedor}_{sub}` -- así queda vivo `{{variacion_pct}}`
    del contrato de Alerta sin re-hardcodear el nombre `variacion`."""
    for contenedor, valor in payload.items():
        if not isinstance(valor, dict) or "direccion" not in valor:
            continue
        direccion = valor.get("direccion")
        if direccion == "alcista":
            flecha = "▲"
        elif direccion == "bajista":
            flecha = "▼"
        else:
            flecha = ""
        contexto[f"{contenedor}_flecha"] = flecha
        for sub, sub_valor in valor.items():
            if isinstance(sub_valor, dict) or isinstance(sub_valor, list):
                continue
            contexto[f"{contenedor}_{sub}"] = str(sub_valor)


def _aplicar_helper_slug_color(contexto: dict[str, str], payload: dict[str, Any]) -> None:
    """Helper 2 del catálogo (R5): `variacion.direccion` (prioridad) -> si no,
    `sesgo` -> deriva `sesgo_slug` = `str(direccion_o_sesgo).lower()` (clase CSS de
    color verde/rojo). Condicional: solo se dispara si existe alguno de los dos,
    conservando exactamente la prioridad de hoy."""
    variacion = payload.get("variacion")
    direccion = variacion.get("direccion") if isinstance(variacion, dict) else None
    sesgo = payload.get("sesgo")
    if direccion:
        contexto["sesgo_slug"] = str(direccion).lower()
    elif sesgo:
        contexto["sesgo_slug"] = str(sesgo).lower()


def _aplicar_helper_badge_impacto(contexto: dict[str, str], payload: dict[str, Any]) -> None:
    """Helper 3 del catálogo (R5): clave escalar `impacto` (`alto`/`medio`,
    case-insensitive) deriva `impacto_badge` = `"ALTO"`/`"MEDIO"`/`""` (valor no
    reconocido -> vacío, CB-5). Sin consumidor en Alerta hoy (Riesgo B); se fija ya
    para que la plantilla `calendario` de Fase C no requiera tocar el motor."""
    impacto = payload.get("impacto")
    if impacto is None:
        return
    valor = str(impacto).lower()
    if valor == "alto":
        contexto["impacto_badge"] = "ALTO"
    elif valor == "medio":
        contexto["impacto_badge"] = "MEDIO"
    else:
        contexto["impacto_badge"] = ""


def _aplicar_helper_chart_embebido(contexto: dict[str, str], payload: dict[str, Any]) -> None:
    """Helper 4 del catálogo (R5): clave `chart_png` truthy deriva `chart_src` (URI
    `file:///` de `Path(chart_png).resolve()`); valida existencia -> `StoryRenderError`
    accionable si no existe (CB-6, sin cambios respecto al CB-8 heredado). Único
    helper que toca disco -- el resto de `build_context` es puro."""
    chart_png = payload.get("chart_png")
    if not chart_png:
        return
    chart_path = Path(chart_png)
    if not chart_path.exists():
        raise StoryRenderError(
            f"chart_png apunta a una ruta inexistente: {chart_png!r}. "
            "Verifica que el PNG haya sido generado por /chart."
        )
    contexto["chart_src"] = chart_path.resolve().as_uri()


def build_context(payload: dict[str, Any]) -> dict[str, str]:
    """Deriva el dict plano de tokens `{{token}} -> valor` a partir del payload.

    Etapa A (R2/R3): recorre `payload.items()` dinámicamente -- cualquier clave
    cuyo valor no sea `dict` ni `list` se agrega como `contexto[clave] = str(valor)`,
    incluidos `None`/booleanos/números. **Matiz conocido**: `None` se convierte al
    literal `"None"` (ej. `chart_png: None` -> `contexto["chart_png"] == "None"`);
    en Alerta ese token no se referencia directo en el HTML, así que es inofensivo.
    Ya no existe noción de "campo obligatorio": una clave del payload que ningún
    `{{token}}` referencia en el HTML es un no-op silencioso (R3/CB-1) --
    `build_context` nunca valida "¿se usa esta clave en algún lado?", solo la
    guardia `_validar_sin_huerfanos` (fase 4 de `build_html`) valida la dirección
    opuesta ("¿quedó algún `{{token}}` sin resolver?").

    Etapa B (R5): aplica, en orden, el catálogo **cerrado** de 4 helpers de
    derivación (flecha de dirección, slug de color, badge de impacto, chart
    embebido) -- ver `_aplicar_helper_*` arriba.

    **Riesgo C (documentado, aceptado en el gate DESIGN->APPLY)**: al eliminar la
    lista fija `_TOKENS_ESCALARES`, un payload incompleto para una plantilla ya
    **no** falla aquí con `"Campo obligatorio ausente en el payload: X"` -- falla
    más tarde, en la guardia de `build_html`, con `"Tokens huérfanos sin resolver
    en el template: X"` (lista **tokens del HTML**, no **claves del payload**).
    Sigue siendo accionable (nombra los tokens exactos); solo cambian el mensaje y
    la etapa en la que se detecta el problema.
    """
    contexto: dict[str, str] = {}

    for clave, valor in payload.items():
        if isinstance(valor, dict) or isinstance(valor, list):
            continue
        contexto[clave] = str(valor)

    _aplicar_helper_flecha_direccion(contexto, payload)
    _aplicar_helper_slug_color(contexto, payload)
    _aplicar_helper_badge_impacto(contexto, payload)
    _aplicar_helper_chart_embebido(contexto, payload)

    return contexto


def _expandir_elemento(bloque: str, objeto: dict[str, Any]) -> str:
    """Resuelve un solo elemento de un bloque `<!-- FOR -->` (helper interno de
    `resolver_loops`, R4). Sin recursión: soporta **un solo nivel** -- un
    `<!-- FOR -->` anidado dentro de este bloque queda como texto literal (CB-4); si
    contiene `{{tokens}}` sin resolver, cae en la guardia final de `build_html`.

    Orden de resolución por elemento: fences genéricos -> tokens escalares.
    - **Fences genéricos**: `<!-- IF:clave -->...<!-- ENDIF:clave -->` se conserva
      sii `bool(objeto.get(clave))` (regla de presencia *truthy* genérica,
      **distinta** de `_fence_presente` -- ese mecanismo especializado sigue
      gobernando únicamente los 4 fences top-level de Alerta).
    - **Tokens por elemento**: por cada campo escalar del objeto, `{{campo}}` ->
      `str(valor)`.
    """

    def _reemplazo_if(match: re.Match[str]) -> str:
        clave = match.group(1)
        if bool(objeto.get(clave)):
            return match.group(2)
        return ""

    bloque = _PATRON_IF_ELEMENTO.sub(_reemplazo_if, bloque)

    for campo, valor in objeto.items():
        if isinstance(valor, dict) or isinstance(valor, list):
            continue
        bloque = bloque.replace("{{" + campo + "}}", str(valor))

    return bloque


def resolver_loops(html: str, payload: dict[str, Any]) -> str:
    """Fase 1 (nueva) de `build_html`: expande cada bloque
    `<!-- FOR:clave -->...<!-- ENDFOR:clave -->` (R4) repitiendo su contenido interno
    una vez por objeto de `payload[clave]` (array), resolviendo dentro de cada
    repetición los fences/tokens propios de ese objeto (`_expandir_elemento`).

    Soporta **un solo nivel** de anidamiento: un `<!-- FOR -->` interno a otro
    `<!-- FOR -->` no se resuelve (CB-4) -- queda como texto literal y, si contiene
    `{{tokens}}`, cae en la guardia de huérfanos al final de `build_html`. No hay
    detección explícita de anidado (aceptado, OUT del spec).

    Casos:
    - `payload[clave]` ausente o no es `list` -> `StoryRenderError` accionable
      (fail-fast, mismo criterio que la guardia).
    - `[]` (array vacío, CB-3) -> el bloque completo se reemplaza por cadena vacía
      (0 repeticiones), sin dejar contenido ni marcas `FOR`/`ENDFOR`. Los headers o
      contenedores que deban persistir sin filas van **fuera** de las marcas
      `FOR`/`ENDFOR` (convención para las plantillas de Fase C).
    - N objetos -> se concatenan N repeticiones de `_expandir_elemento`, en el
      orden del array.
    """

    def _reemplazo(match: re.Match[str]) -> str:
        clave = match.group(1)
        bloque_interno = match.group(2)
        datos = payload.get(clave)
        if not isinstance(datos, list):
            raise StoryRenderError(f"FOR:{clave} requiere un array en el payload")
        return "".join(_expandir_elemento(bloque_interno, objeto) for objeto in datos)

    return _PATRON_FOR.sub(_reemplazo, html)


def _resolver_fences(html: str, payload: dict[str, Any]) -> str:
    """Fase 1 de `build_html`: para cada fence, conserva o elimina el bloque completo."""
    for nombre in _FENCES:
        patron = re.compile(
            r"<!--\s*IF:" + re.escape(nombre) + r"\s*-->(.*?)<!--\s*ENDIF:"
            + re.escape(nombre) + r"\s*-->",
            re.DOTALL,
        )

        def _reemplazo(match: re.Match[str], _nombre: str = nombre) -> str:
            if _fence_presente(_nombre, payload):
                return match.group(1)
            return ""

        html = patron.sub(_reemplazo, html)
    return html


def _sustituir_tokens(html: str, contexto: dict[str, str]) -> str:
    """Fase 2 de `build_html`: sustitución escalar de cada `{{token}}` conocido."""
    for token, valor in contexto.items():
        html = html.replace("{{" + token + "}}", valor)
    return html


def _validar_sin_huerfanos(html: str) -> None:
    """Fase 3 (guardia) de `build_html`: cualquier `{{` restante es un error (AC2)."""
    huerfanos = sorted(set(re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", html)))
    if huerfanos:
        raise StoryRenderError(
            "Tokens huérfanos sin resolver en el template: " + ", ".join(huerfanos)
        )


def build_html(payload: dict[str, Any], template_path: Path) -> str:
    """Mapea `payload` sobre el HTML de `template_path`, orden canónico
    **loops -> fences -> tokens -> guardia** (R4, #119).

    Puro (D1/D2): no depende de Playwright ni de red. Es el objeto de AC2-AC9.
    """
    html = Path(template_path).read_text(encoding="utf-8")
    contexto = build_context(payload)

    html = resolver_loops(html, payload)
    html = _resolver_fences(html, payload)
    html = _sustituir_tokens(html, contexto)
    _validar_sin_huerfanos(html)

    return html


def render_png(
    html: str,
    output_path: Path,
    *,
    template_dir: Path,
    viewport: tuple[int, int] = _FORMATOS[_FORMATO_DEFECTO],
) -> Path:
    """Renderiza `html` a un PNG del tamaño de `viewport` con Playwright headless.

    `viewport` es `(ancho, alto)` y por defecto vale el formato horizontal
    (1920x1080), así que las llamadas existentes no cambian de comportamiento.

    El HTML resuelto se escribe a un temporal dentro de `template_dir` (para que
    los assets relativos del snapshot -- fuentes locales, CSS -- resuelvan) y se
    navega con `file://`, nunca `set_content`. El `<img>` del chart usa siempre
    una URI absoluta `file:///`, así no depende de `template_dir`.
    """
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise StoryRenderError(
            "Falta el paquete playwright. Instálalo con:\n"
            "  uv sync --extra stories && python -m playwright install chromium"
        ) from exc

    output_path = Path(output_path)
    template_dir = Path(template_dir)

    tmp_fd, tmp_name = tempfile.mkstemp(
        suffix=".html", prefix="_story_render_", dir=str(template_dir)
    )
    tmp_path = Path(tmp_name)
    try:
        with open(tmp_fd, "w", encoding="utf-8") as fh:
            fh.write(html)

        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch()
                except PlaywrightError as exc:
                    raise StoryRenderError(
                        f"{_MSG_CHROMIUM_AUSENTE}\n(detalle: {exc})"
                    ) from exc
                try:
                    ancho, alto = viewport
                    page = browser.new_page(
                        viewport={"width": ancho, "height": alto},
                        device_scale_factor=1,
                    )
                    page.goto(tmp_path.resolve().as_uri(), wait_until="networkidle")
                    page.evaluate("document.fonts.ready")
                    page.screenshot(path=str(output_path))
                finally:
                    browser.close()
        except PlaywrightError as exc:
            raise StoryRenderError(
                f"{_MSG_CHROMIUM_AUSENTE}\n(detalle: {exc})"
            ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    return output_path


def render_story(
    payload: dict[str, Any],
    template_path: Path,
    output_path: Path,
    formato: str = _FORMATO_DEFECTO,
) -> Path:
    """Orquestador público: `build_html` (puro) + `render_png` (Playwright).

    `formato` selecciona el lienzo (`horizontal` | `vertical`); el HTML que
    produce `build_html` es el mismo en ambos casos -- la diferencia es
    puramente CSS, vía `@media (max-aspect-ratio: 1/1)` en el snapshot.
    """
    template_path = Path(template_path)
    output_path = Path(output_path)

    viewport = resolver_viewport(formato)
    html = build_html(payload, template_path)
    return render_png(
        html, output_path, template_dir=template_path.parent, viewport=viewport
    )


def main(argv: list[str] | None = None) -> int:
    """CLI: payload JSON por stdin, `--template` y `--out` (design.md D4)."""
    parser = argparse.ArgumentParser(description="Render de Stories GI (#109)")
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--formato",
        default=_FORMATO_DEFECTO,
        choices=sorted(_FORMATOS),
        help="Lienzo de salida: horizontal (1920x1080) o vertical (1080x1920).",
    )
    args = parser.parse_args(argv)

    try:
        # sys.stdin no siempre es UTF-8 por defecto en Windows (usa la codepage
        # de la consola) -- leer los bytes crudos y decodificar explícito evita
        # mojibake en tildes/ñ/· del payload (ej. "técnico" -> "tÃ©cnico").
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        ruta = render_story(payload, args.template, args.out, formato=args.formato)
    except StoryRenderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Payload JSON inválido en stdin: {exc}", file=sys.stderr)
        return 1

    print(str(ruta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
