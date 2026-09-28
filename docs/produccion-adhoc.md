# Producción y Despacho Ad-hoc / Extraordinario

Para eventos imprevistos, noticias de última hora, subastas soberanas (ej. UST 10Y/20Y/30Y), fe de erratas o análisis extraordinarios, **está estrictamente prohibido crear scripts `.py` desechables de un solo uso** (como `despacho_<evento>.py` o `generar_textos_<evento>.py`).

Toda producción ad-hoc se sistematiza mediante un **manifiesto declarativo JSON** y se procesa exclusivamente con `scripts/produccion_adhoc.py`.

## Formato del Manifiesto JSON

Se guarda en `data/stories/<tanda>_manifest.json` o dentro de su carpeta:

```json
{
  "tanda": "2026-09-16_ventas_minoristas_fomc",
  "descripcion": "Despacho de Ventas Minoristas EE.UU., Inflación y Decisión FOMC",
  "story": {
    "plantilla": "dato_macro.html",
    "salida_png": "data/stories/2026-09-16_ventas_minoristas_fomc_macro.png",
    "payload": {
      "plantilla": "dato_macro",
      "chip_pais": "EE.UU.",
      "fecha_hora": "16 SEP 2026 · 09:30 CLT",
      "indicador": "Ventas Minoristas (MoM)",
      "periodo": "Agosto 2026 · U.S. Census Bureau",
      "titular": "Consumo repunta a +1,2% mensual...",
      "veredicto": "Sobre Consenso",
      "veredicto_slug": "mejor",
      "actual": "+1,2%",
      "esperado": "+0,8%",
      "anterior": "-0,5%",
      "recorrido": {
        "barras": [
          {"valor": 0.6, "etiqueta": "Abr", "valor_etiqueta": "+0,6%", "signo": "pos"},
          {"valor": 1.2, "etiqueta": "Ago", "valor_etiqueta": "+1,2%", "signo": "pos"}
        ],
        "niveles": [
          {"valor": 0.8, "etiqueta": "0,8%", "rol": "ESPERADO", "clase": "esperado"}
        ]
      },
      "activos": [
        {"nombre": "DÓLAR / CLP", "direccion": "sube", "etiqueta": "ALCISTA", "porque": "..."}
      ]
    }
  },
  "despachos": [
    {
      "canal": "01_macro_y_apertura",
      "alias": "avisos",
      "pieza": "ventas_minoristas_macro",
      "activo": "MACRO_USA",
      "adjunto": "data/stories/2026-09-16_ventas_minoristas_fomc_macro.png",
      "mensaje_texto": "📊 *Ventas Minoristas en EE.UU....* ...",
      "archivo_txt": "data/stories/2026-09-16_ventas_minoristas_macro.txt"
    }
  ]
}
```

## Comandos del CLI

```bash
# 1. Generar imágenes PNG y escribir archivos TXT en UTF-8 garantizado:
python scripts/produccion_adhoc.py --generar data/stories/<tanda>_manifest.json

# 2. Auditar guardrails de cliente, precios/decimales y existencia de artefactos:
python scripts/produccion_adhoc.py --auditar data/stories/<tanda>_manifest.json

# 3. Despachar a WhatsApp con bitácora anti-baneo y cadencia de 45s:
python scripts/produccion_adhoc.py --despachar data/stories/<tanda>_manifest.json [--dry-run]

# 4. Pipeline completo encadenado (generar + auditar + despachar):
python scripts/produccion_adhoc.py --todo data/stories/<tanda>_manifest.json [--dry-run]
```
