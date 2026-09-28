#!/usr/bin/env python
# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
"""Abre Google Chrome en tu pantalla para iniciar sesión en Facebook e inspeccionar Grupo Inteligencia.

Uso:
    uv run python scripts/login_facebook.py
"""

import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent
SESION_DIR = RAIZ / ".facebook_session"
SESION_DIR.mkdir(parents=True, exist_ok=True)
SALIDA_DATA = RAIZ / "data"
SALIDA_DATA.mkdir(parents=True, exist_ok=True)

def main():
    print("\n" + "="*60)
    print("  INICIANDO GOOGLE CHROME VISIBLE PARA FACEBOOK  ")
    print("="*60 + "\n")
    
    with sync_playwright() as p:
        # Usa el ejecutable real de Google Chrome instalado en Windows
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESION_DIR),
            headless=False,
            channel="chrome",
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ],
            no_viewport=True
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        target_url = "https://web.facebook.com/search/top?q=grupo%20inteligencia"
        print(f"Cargando: {target_url}...")
        try:
            page.goto(target_url, timeout=45000)
        except Exception as e:
            print(f"Nota de carga: {e}")
            
        print("\n" + "#"*60)
        print("  VENTANA DE CHROME ABIERTA EN TU ESCRITORIO")
        print("  1. Inicia sesión en Facebook.")
        print("  2. Busca o haz clic en la página de Grupo Inteligencia.")
        print("  3. Cuando estés viendo la página de Grupo Inteligencia:")
        print("     Vuelve a esta consola y presiona [ENTER].")
        print("#"*60 + "\n")
        
        input(">>> Presiona [ENTER] aquí en la consola cuando estés listo... ")
        
        print("\nExtrayendo datos de la página actual...")
        current_url = page.url
        title = page.title()
        print(f"URL detectada: {current_url}")
        print(f"Título detectado: {title}")
        
        # Guarda screenshot
        screenshot_path = SALIDA_DATA / "facebook_grupo_inteligencia.png"
        page.screenshot(path=str(screenshot_path))
        print(f"Captura guardada en: {screenshot_path}")
        
        # Guarda estado de sesión / cookies
        state_path = SALIDA_DATA / "facebook_storage_state.json"
        context.storage_state(path=str(state_path))
        print(f"Sesión guardada en: {state_path}")
        
        # Extrae contenido visible
        page_info = page.evaluate('''() => {
            const h1 = document.querySelector('h1') ? document.querySelector('h1').innerText.trim() : '';
            const allText = document.body.innerText;
            const lines = allText.split('\\n').map(l => l.trim()).filter(l => l.length > 15);
            
            const links = Array.from(document.querySelectorAll('a'))
                .map(a => ({ text: a.innerText.trim(), href: a.href }))
                .filter(a => a.text.length > 2 && !a.href.includes('/messages/'));
                
            return {
                title: document.title,
                url: window.location.href,
                h1: h1,
                textLines: lines.slice(0, 60),
                links: links.slice(0, 30)
            };
        }''')
        
        json_path = SALIDA_DATA / "facebook_grupo_inteligencia.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(page_info, f, indent=2, ensure_ascii=False)
        print(f"Datos guardados en: {json_path}")
        
        print("\n¡Extracción exitosa! Cerrando navegador...")
        context.close()

if __name__ == "__main__":
    main()
