#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lee las últimas burbujas de una conversación de WhatsApp. **Solo lectura.**

**Por qué existe.** El flujo de aprobación del director pasó a ser: la pieza se
manda al banco de pruebas y él responde **ahí** si la aprueba (decisión del
2026-09-04). El sender solo sabía escribir, así que la mitad del lazo no se podía
cerrar: había que preguntarle por otra vía justamente lo que él pidió no
preguntar por otra vía.

**Este script no puede enviar nada.** No escribe en el cuadro de conversación, no
toca el botón de enviar y no adjunta archivos. Hay un test que falla si aparece
cualquiera de esas cosas acá. Un lector que además pueda publicar no es un lector.

Reutiliza la sesión y los selectores de `WhatsAppSender`, que están medidos contra
el DOM real: reimplementarlos sería la segunda copia que después queda atrás.

Uso:
    uv run python scripts/leer_respuesta.py --grupo "GI · Banco de Pruebas"
    uv run python scripts/leer_respuesta.py --grupo pruebas --n 6 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

from whatsapp_sender import WhatsAppError, WhatsAppSender  # noqa: E402

# Las clases con que WhatsApp Web marca de quién es cada burbuja. Están medidas
# contra el DOM real, igual que el resto de los selectores del sender.
_JS_BURBUJAS = """
(n) => {
  const filas = Array.from(document.querySelectorAll('#main div[role=row]'));
  const texto = (nodo) => {
    // Los emoji se rinden como <img> con el caracter en `alt`: `innerText` los
    // pierde. Mismo motivo por el que el sender tiene `_texto_con_emojis`.
    const salida = [];
    const recorrer = (el) => {
      for (const hijo of el.childNodes) {
        if (hijo.nodeType === 3) { salida.push(hijo.nodeValue); continue; }
        if (hijo.nodeType !== 1) continue;
        const t = hijo.tagName;
        if (t === 'SCRIPT' || t === 'STYLE' || t === 'SVG' || t === 'TITLE') continue;
        if (hijo.getAttribute && hijo.getAttribute('aria-hidden') === 'true') continue;
        // Los iconos de estado (visto, reloj, silenciado) traen su nombre de
        // clase como texto y se cuelan al final de la burbuja: el mismo defecto
        // que hacia que el sender leyera "tail-out" como primera linea.
        if (hijo.hasAttribute && hijo.hasAttribute('data-icon')) continue;
        if (t === 'IMG') { salida.push(hijo.getAttribute('alt') || ''); continue; }
        if (t === 'BR') { salida.push('\\n'); continue; }
        recorrer(hijo);
      }
    };
    recorrer(nodo);
    return salida.join('');
  };
  return filas.slice(-n).map((r) => {
    const clases = r.className || '';
    const entrante = /message-in/.test(r.innerHTML) || /message-in/.test(clases);
    const saliente = /message-out/.test(r.innerHTML) || /message-out/.test(clases);
    const media = Array.from(r.querySelectorAll('img'))
      .some((i) => (i.src || '').startsWith('blob:'))
      || !!r.querySelector('audio, video');
    return {
      de: entrante ? 'ellos' : (saliente ? 'nosotros' : 'indeterminado'),
      media: media,
      texto: texto(r).trim(),
    };
  });
}
"""


def leer(
    destinatario: str, n: int = 5, headless: bool = True
) -> list[dict[str, Any]]:
    """Las últimas `n` burbujas de esa conversación, más nuevas al final."""
    sender = WhatsAppSender(headless=headless)
    nombre = sender.config.resolver_nombre_oficial(destinatario)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        contexto = sender._crear_contexto(pw, headless=headless)
        try:
            page = contexto.new_page()
            page.goto(sender.URL_WHATSAPP, wait_until="domcontentloaded")
            sender._verificar_autenticacion(page)
            sender._cerrar_modales_emergentes(page)
            sender._buscar_y_abrir_chat(page, nombre)
            burbujas = page.evaluate(_JS_BURBUJAS, n) or []
        finally:
            contexto.close()

    return [b for b in burbujas if isinstance(b, dict)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-g", "--grupo", "--destinatario", dest="destinatario",
                    required=True, help="alias, slug o nombre del chat a leer")
    ap.add_argument("-n", type=int, default=5, help="cuántas burbujas leer")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    ap.add_argument("--visible", action="store_false", dest="headless",
                    help="muestra la ventana del navegador")
    args = ap.parse_args()

    try:
        burbujas = leer(args.destinatario, n=args.n, headless=args.headless)
    except WhatsAppError as e:
        print(f"[ERROR] {e}")
        return 1

    if args.json:
        print(json.dumps(burbujas, ensure_ascii=False, indent=2))
        return 0

    if not burbujas:
        print("La conversación no devolvió burbujas.")
        return 0

    for b in burbujas:
        quien = {"ellos": "ELLOS", "nosotros": "NOSOTROS"}.get(b["de"], "?")
        marca = " [media]" if b.get("media") else ""
        primera, *resto = (b["texto"] or "").splitlines() or [""]
        print(f"[{quien}]{marca} {primera}")
        for linea in resto:
            print(f"           {linea}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
