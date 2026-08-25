#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pieza `calendario` para la clase Macro/Tasas del Heptagono.

Es la septima clase y la unica sin activo protagonista: lo que se comunica es la
curva y la agenda, no un precio. La plantilla `calendario` existe justamente para
eso, asi que cae al acento de marca en vez de a un color por activo.

Seleccion EDITORIAL de 5 de los 9 eventos del dia, no un volcado: los dos de alto
impacto mas los tres que le hablan a un activo del catalogo. Un calendario
completo no es una pieza, es una tabla.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parents[2] / "data" / "stories" / "_propuesta"
SANTIAGO = ZoneInfo("America/Santiago")

datos = json.loads((BASE / "_eventos.json").read_text(encoding="utf-8"))
eventos = datos["eventos"]
delta_ust = datos["delta_ust_10y_bps"]

glosario = json.loads(
    Path(__file__).resolve().parents[2] / "data" / "glosario_siglas.json".read_text(encoding="utf-8")
)


def nombre_es(ev: dict) -> str:
    dic = ev.get("diccionario") or {}
    if dic.get("nombre_es"):
        return dic["nombre_es"]
    # El evento no traia enganche porque el glosario se amplio despues de la
    # corrida: se resuelve contra los titulos_ff recien agregados.
    for entrada in glosario.values():
        if not isinstance(entrada, dict):
            continue
        for titulo in entrada.get("titulos_ff", []):
            if titulo.lower() in ev["nombre"].lower():
                return entrada["nombre_es"]
    return ev["nombre"]


# Los 5 elegidos, en orden de hora.
ELEGIDOS = [
    "CB Consumer Confidence",
    "New Home Sales (Jul)",
    "ADP Employment Change Weekly",
    "API Weekly Crude Oil Stock",
    "2-Year Note Auction",
]

# A qué activo del catálogo le habla cada uno. Es lo que convierte una agenda en
# una pieza: el cliente no necesita saber que hay un dato, necesita saber qué
# activo suyo se mueve con él.
ACTIVO_QUE_MIRA = {
    "CB Consumer Confidence": "US100 · Oro",
    "New Home Sales (Jul)": "US100",
    "ADP Employment Change Weekly": "Oro · USD/CLP",
    "API Weekly Crude Oil Stock": "WTI",
    "2-Year Note Auction": "Oro · US100",
}

seleccion = []
for clave in ELEGIDOS:
    ev = next((e for e in eventos if clave in e["nombre"]), None)
    if ev:
        seleccion.append(ev)
seleccion.sort(key=lambda e: e["hora_servidor"])

hoy = datetime.strptime(seleccion[0]["hora_servidor"], "%Y-%m-%d %H:%M")
DIAS = ("LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO")
MESES = ("ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO",
         "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE")

filas = []
for i, ev in enumerate(seleccion, 1):
    clave = next(k for k in ELEGIDOS if k in ev["nombre"])
    impacto = ev.get("impacto", "medio")
    filas.append({
        "numero": f"{i:02d}",
        "dia": ACTIVO_QUE_MIRA[clave],
        "hora": ev["hora_servidor"][-5:] + " CLT",
        "evento": nombre_es(ev),
        "pais": "EE.UU. · USD",
        "impacto": f"{impacto.capitalize()} impacto",
        "impacto_slug": impacto,
        # Los campos de la fuente son `previo` y `forecast`, no `anterior` ni
        # `previsto`: la primera version dejaba la columna ANTES vacia en las
        # cinco filas, que se lee como "no habia dato previo" y es falso.
        "anterior": ev.get("previo") or "—",
        "esperado": ev.get("forecast") or "—",
        "tiene_esperado": bool(ev.get("forecast")),
    })

payload = {
    "plantilla": "calendario",
    "sello": "AGENDA DEL DÍA · GI",
    "fecha_hora": f"{DIAS[hoy.weekday()]} {hoy.day} DE {MESES[hoy.month - 1]}",
    "titulo": "Lo que mueve la jornada",
    "subtitulo": (
        f"Los 5 datos de mayor impacto del día y el activo al que le hablan. "
        f"La tasa del Tesoro a 10 años se movió {delta_ust:+.0f} puntos base."
        if delta_ust is not None else
        "Los 5 datos de mayor impacto del día y el activo al que le hablan."
    ),
    "eventos": filas,
    "cta": "¿Quieres seguir la jornada en detalle?",
    "cta_sub": "Habla hoy con tu analista",
}

destino = BASE / "macro.json"
destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print("ok ->", destino)
for f in filas:
    print(f"  {f['numero']} {f['hora']:<10} {f['impacto_slug']:<6} {f['evento'][:50]:<52} mira: {f['dia']}")
