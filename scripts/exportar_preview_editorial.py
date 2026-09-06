# punto-de-entrada: lo corre el director a mano para exportar un preview editorial
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path("C:/Users/bbrav/grupo-analisis-mercado")
tmp_html = RAIZ / "scratch" / "temp_informe_diseno.html"

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 1600}, device_scale_factor=2)
        page.goto(tmp_html.as_uri())
        page.wait_for_timeout(500)
        
        # Capture full screenshot or elements
        page_containers = page.query_selector_all(".page-container")
        print(f"Total page-containers: {len(page_containers)}")
        
        for i, container in enumerate(page_containers):
            out_img = RAIZ / "scratch" / f"editorial_preview_pagina{i+1}.png"
            container.screenshot(path=str(out_img))
            print(f"[OK] Preview container {i+1}: {out_img}")
            
        # Also screenshot flowing container
        flowing = page.query_selector(".flowing-container")
        if flowing:
            out_img = RAIZ / "scratch" / "editorial_preview_flowing.png"
            flowing.screenshot(path=str(out_img))
            print(f"[OK] Preview flowing: {out_img}")
            
        browser.close()

if __name__ == "__main__":
    main()
