"""Motor de render de Stories GI (issue #109).

Único renderer del repo para Stories de marca (`data/stories/`): mapea un payload de
datos (JSON) sobre un snapshot HTML estático y produce un PNG 1080x1920 con Playwright
headless. No contiene lógica de negocio -- la recolección de datos (niveles del motor,
narrativa editorial, formateo de precios) vive en el prompt `.claude/commands/story.md`;
este módulo solo sabe payload -> HTML -> PNG (design.md D1/D2).

Mecanismo de inyección (D1): tokens `{{campo}}` + fences
`<!-- IF:nombre -->...<!-- ENDIF:nombre -->`, resueltos con `re`/`str` de la stdlib
(sin Jinja2 -- las llaves del CSS embebido chocarían con `str.format`).

El import de Playwright es perezoso (dentro de `render_png`): los tests puros de
mapeo (`build_context`/`build_html`) importan este módulo sin necesitar Playwright
instalado, igual que el patrón ya usado para `MetaTrader5` en el MCP.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

# Fences complementarios y sus condiciones de presencia (D1). El orden es fijo:
# primero se resuelven fences, después tokens escalares, al final la guardia.
_FENCES = ("variacion", "vol", "chart_img", "chart_svg")

# Tokens escalares siempre presentes en el payload (D1). `sesgo_slug` es derivado,
# no viene literal en el payload -- se calcula en `build_context`.
_TOKENS_ESCALARES = (
    "chip_categoria",
    "fecha_hora",
    "titular",
    "parrafo",
    "rotulo_activo",
    "tag_riesgo",
    "precio_actual",
    "soporte",
    "resistencia",
    "rotulo_grafico",
    "fuente",
    "sesgo_slug",
)

_MSG_CHROMIUM_AUSENTE = (
    "No se pudo lanzar Chromium para renderizar la Story. Instala el navegador con:\n"
    "  uv sync --extra stories && python -m playwright install chromium"
)


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


def build_context(payload: dict[str, Any]) -> dict[str, str]:
    """Deriva el dict plano de tokens `{{token}} -> valor` a partir del payload.

    Puro: no toca disco salvo para validar que `chart_png` (si viene) exista --
    CB-8, nunca renderiza con una imagen rota. Deriva `variacion_flecha`,
    `sesgo_slug` y `chart_src` (URI `file:///`).
    """
    contexto: dict[str, str] = {}

    for token in _TOKENS_ESCALARES:
        if token == "sesgo_slug":
            continue
        valor = payload.get(token)
        if valor is None:
            raise StoryRenderError(
                f"Campo obligatorio ausente en el payload: {token!r}"
            )
        contexto[token] = str(valor)

    variacion = payload.get("variacion")
    if variacion is not None:
        direccion = variacion.get("direccion", "")
        contexto["variacion_pct"] = str(variacion.get("pct", ""))
        contexto["variacion_flecha"] = "▲" if direccion == "alcista" else "▼"

    vol_pct = payload.get("vol_pct")
    if vol_pct is not None:
        contexto["vol_pct"] = str(vol_pct)

    # sesgo_slug: prioriza variacion.direccion (presentación), si no cae a sesgo.
    if variacion is not None and variacion.get("direccion"):
        contexto["sesgo_slug"] = str(variacion["direccion"]).lower()
    else:
        contexto["sesgo_slug"] = str(payload.get("sesgo", "")).lower()

    chart_png = payload.get("chart_png")
    if chart_png:
        chart_path = Path(chart_png)
        if not chart_path.exists():
            raise StoryRenderError(
                f"chart_png apunta a una ruta inexistente: {chart_png!r}. "
                "Verifica que el PNG haya sido generado por /chart."
            )
        contexto["chart_src"] = chart_path.resolve().as_uri()

    return contexto


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
    """Mapea `payload` sobre el HTML de `template_path` (fences -> tokens -> guardia).

    Puro (D1/D2): no depende de Playwright ni de red. Es el objeto de AC2/AC9.
    """
    html = Path(template_path).read_text(encoding="utf-8")
    contexto = build_context(payload)

    html = _resolver_fences(html, payload)
    html = _sustituir_tokens(html, contexto)
    _validar_sin_huerfanos(html)

    return html


def render_png(html: str, output_path: Path, *, template_dir: Path) -> Path:
    """Renderiza `html` a un PNG 1080x1920 con Playwright headless (AC3, D3).

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
                    page = browser.new_page(
                        viewport={"width": 1080, "height": 1920},
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


def render_story(payload: dict[str, Any], template_path: Path, output_path: Path) -> Path:
    """Orquestador público: `build_html` (puro) + `render_png` (Playwright)."""
    template_path = Path(template_path)
    output_path = Path(output_path)

    html = build_html(payload, template_path)
    return render_png(html, output_path, template_dir=template_path.parent)


def main(argv: list[str] | None = None) -> int:
    """CLI: payload JSON por stdin, `--template` y `--out` (design.md D4)."""
    parser = argparse.ArgumentParser(description="Render de Stories GI (#109)")
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        # sys.stdin no siempre es UTF-8 por defecto en Windows (usa la codepage
        # de la consola) -- leer los bytes crudos y decodificar explícito evita
        # mojibake en tildes/ñ/· del payload (ej. "técnico" -> "tÃ©cnico").
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        ruta = render_story(payload, args.template, args.out)
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
