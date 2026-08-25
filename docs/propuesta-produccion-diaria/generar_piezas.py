#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de un solo uso: arma las 7 piezas de la propuesta para Hari.

Una por clase del Heptagono, con datos REALES del motor. No vive en scripts/ a
proposito: el flujo de produccion elige por Score_GI y no por clase, y agregar un
flag de tickers curados a pipeline_carrusel seria un atajo para saltarse al
escaner. Esto es una vitrina de capacidades, no una tanda.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import screener_gi as sc
import pipeline_carrusel as pc
from serie_mt5 import obtener_serie

SALIDA = Path(__file__).resolve().parents[2] / "data" / "stories" / "_propuesta"
SALIDA.mkdir(parents=True, exist_ok=True)

# Un activo por clase, eligiendo el que tiene imagen PROPIA para que las 7 piezas
# no repitan foto: QQQ.US usa us100.jpg y GLD.US usa oro.jpg, asi que el ETF
# representativo es SOXX.US, que tiene la suya.
POR_CLASE = [
    ("Divisas", "USDCLP"),
    ("Commodities", "XAUUSD"),
    ("Criptomonedas", "BTCUSD"),
    ("Indices", "US100.spot"),
    ("ETF", "SOXX.US"),
    ("Acciones", "#MELI"),
]


def main() -> int:
    ahora = datetime.now(tz=pc.SANTIAGO)
    eventos, delta_ust, avisos = sc._contexto_macro(ahora)
    sesgos, av2 = sc._sesgos_playbook()
    avisos.extend(av2)
    avisos.extend(sc._conectar_terminal())

    catalogo = {a["ticker"]: a for a in sc.cargar_universo(solo_renderizables=False)}

    resultados = []
    for clase_label, ticker in POR_CLASE:
        activo = catalogo[ticker]
        ev = sc.evaluar_activo(activo, eventos, delta_ust, sesgos, ahora)
        if "excluido" in ev:
            resultados.append({"clase": clase_label, "ticker": ticker,
                               "estado": "EXCLUIDO", "motivo": ev["excluido"]})
            continue

        cierres, _ = obtener_serie(ticker, pc.TIMEFRAME_GRAFICO, pc.VELAS_GRAFICO)
        payload = pc.construir_payload(ev, activo, ahora, cierres)
        archivo = SALIDA / f"{clase_label.lower()}.json"
        archivo.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        resultados.append({
            "clase": clase_label, "ticker": ticker, "estado": "OK",
            "score": ev["score"], "direccion": ev["direccion"],
            "precio": payload["precio_actual"], "soporte": payload["soporte"],
            "resistencia": payload["resistencia"], "impulso": payload["vol_pct"],
            "slug": payload["activo_slug"],
            "factores": {k: v["detalle"] for k, v in ev["factores"].items()},
            "archivo": str(archivo),
        })

    # Los eventos del dia, para armar despues la pieza `calendario` de la clase
    # Macro/Tasas, que no tiene activo protagonista.
    (SALIDA / "_eventos.json").write_text(
        json.dumps({"eventos": eventos, "delta_ust_10y_bps": delta_ust},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps({"resultados": resultados, "avisos": avisos},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
