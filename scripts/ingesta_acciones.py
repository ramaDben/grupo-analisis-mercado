#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ingesta de las acciones: próxima fecha de resultados e informes de la SEC (spec 2026-10-20, Task 7).

Escribe en `data central/DATA ACCIONES/`:
  earnings_calendar.json    fecha de resultados por acción (yfinance, NO oficial)
  estados_financieros.json  últimos 10-K, 10-Q y 8-K de la SEC (sin cifras: ninguna se cita)

Dos reglas de fondo:
1. La fecha de yfinance se marca "no oficial" y NO habilita sola la publicación: lo que habilita es
   la fuente directa del ancla (un comunicado de la empresa o de la SEC), que valida `fuentes.py`.
2. Si una descarga falla, el dato queda en None. Nunca se inventa ni se rellena con la fecha anterior.

Los descargadores se inyectan (los tests no usan red). Va enganchado a `pipeline_datos.PASOS`.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

DIR_ACCIONES = RAIZ / "data central" / "DATA ACCIONES"
FUENTE_FECHA = "yfinance (no oficial)"
FORMAS = ("10-K", "10-Q", "8-K")
MAX_INFORMES = 5
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
# SEC exige un User-Agent que identifique a quien consulta. Sin correo personal: se puede reemplazar
# con la variable SEC_USER_AGENT.
USER_AGENT = os.environ.get("SEC_USER_AGENT") or "GI-analistas grupo-analisis-mercado (research; sin fines de scraping masivo)"


# ───────────────────────────────────────────────────────────── descargadores reales


def _descargar_fecha(ticker: str) -> Any:
    """La próxima fecha de resultados según yfinance. Cualquier fallo se propaga y lo trata el llamador."""
    import yfinance as yf

    cal = yf.Ticker(ticker).calendar
    fechas = cal.get("Earnings Date") if isinstance(cal, dict) else None
    return fechas[0] if fechas else None


def _descargar_sec(url: str, headers: dict[str, str]) -> dict[str, Any]:
    import requests

    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


# ───────────────────────────────────────────────────────────── funciones puras


def _como_fecha(valor: Any) -> str | None:
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    try:
        return date.fromisoformat(str(valor)[:10]).isoformat()
    except (TypeError, ValueError):
        return None


def fechas_earnings(tickers: list[str], descargar: Callable[[str], Any]) -> dict[str, dict[str, Any]]:
    """Por ticker, `{"fecha": "AAAA-MM-DD" | None, "fuente": "yfinance (no oficial)"}`."""
    salida: dict[str, dict[str, Any]] = {}
    for t in tickers:
        try:
            fecha = _como_fecha(descargar(t))
        except Exception:  # noqa: BLE001  sin dato no se inventa: queda None
            fecha = None
        salida[t] = {"fecha": fecha, "fuente": FUENTE_FECHA}
    return salida


def informes_sec(cik: str, descargar: Callable[[str, dict[str, str]], dict[str, Any]]) -> list[dict[str, Any]]:
    """Los últimos 10-K, 10-Q y 8-K del emisor, del más nuevo al más viejo. Vacío si SEC no responde."""
    cik10 = str(cik).zfill(10)
    try:
        crudo = descargar(f"https://data.sec.gov/submissions/CIK{cik10}.json",
                          {"User-Agent": USER_AGENT, "Accept": "application/json"})
        r = crudo["filings"]["recent"]
        filas = zip(r["form"], r["filingDate"], r["reportDate"], r["accessionNumber"], r["primaryDocument"])
        salida = []
        for forma, fecha, periodo, acc, doc in filas:
            if forma not in FORMAS:
                continue
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik10)}/{acc.replace('-', '')}/{doc}"
            salida.append({"forma": forma, "fecha": fecha, "periodo": periodo or None, "url": url})
        return sorted(salida, key=lambda i: i["fecha"], reverse=True)[:MAX_INFORMES]
    except Exception:  # noqa: BLE001
        return []


def _escribir(ruta: Path, datos: dict[str, Any]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def ingestar(anclas: dict[str, tuple[str, dict[str, Any]]], destino: Path = DIR_ACCIONES, *,
             ahora: datetime | None = None, descargar_fecha: Callable[[str], Any] = _descargar_fecha,
             descargar_sec: Callable[..., dict[str, Any]] = _descargar_sec) -> dict[str, Any]:
    """Descarga y escribe los dos archivos. `anclas` es `{ticker_mt5: (segmento, ancla)}` de las acciones."""
    sello = (ahora or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    fechas = fechas_earnings([a["ticker"] for _, a in anclas.values()], descargar_fecha)
    calendario: dict[str, Any] = {}
    estados: dict[str, Any] = {}
    for mt5, (_, ancla) in anclas.items():
        calendario[mt5] = fechas[ancla["ticker"]]
        estados[mt5] = {"cik": ancla["cik"], "informes": informes_sec(ancla["cik"], descargar_sec)}
    _escribir(destino / "earnings_calendar.json", {"ingesta": sello, "acciones": calendario})
    _escribir(destino / "estados_financieros.json", {"ingesta": sello, "acciones": estados})
    return {"fechas": sum(1 for v in calendario.values() if v["fecha"]),
            "con_informes": sum(1 for v in estados.values() if v["informes"]), "total": len(anclas)}


def _falla(mensaje: str):
    from analista.preparar import PreparacionFallida

    return PreparacionFallida(mensaje)


def leer_empresa(ticker: str, base: Path = DIR_ACCIONES, *, ahora: datetime | None = None) -> dict[str, Any]:
    """Lo que el análisis sabe de la empresa. Levanta `PreparacionFallida` sin ingesta o vencida."""
    from market_data_mcp.frescura import validar_staleness

    ahora = ahora or datetime.now(timezone.utc)
    try:
        cal = json.loads((base / "earnings_calendar.json").read_text(encoding="utf-8"))
        est = json.loads((base / "estados_financieros.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise _falla(f"No hay ingesta de acciones para {ticker} ({exc.__class__.__name__}): corre "
                     "`uv run python scripts/pipeline_datos.py` y vuelve a pedir. No gasté tu cupo.") from exc
    fresco, horas, _umbral, motivo = validar_staleness(min(cal.get("ingesta") or "", est.get("ingesta") or "")
                                                       or None, now_dt=ahora)
    if not fresco:
        raise _falla(f"La ingesta de acciones está vencida ({horas:.0f} h) o sin sello ({motivo}): corre "
                     "`uv run python scripts/pipeline_datos.py` y vuelve a pedir. No gasté tu cupo.")
    fila = (cal.get("acciones") or {}).get(ticker) or {}
    proxima = None
    fecha = _como_fecha(fila.get("fecha")) if fila.get("fecha") else None
    hoy = ahora.astimezone(ZoneInfo("America/Santiago")).date()
    if fecha and date.fromisoformat(fecha) >= hoy:
        d = date.fromisoformat(fecha)
        proxima = f"{DIAS[d.weekday()]} {d:%d/%m}"
    informes = ((est.get("acciones") or {}).get(ticker) or {}).get("informes") or []
    return {"proxima_earnings": proxima, "fuente_fecha": fila.get("fuente", FUENTE_FECHA),
            "ultimo_informe": informes[0] if informes else None}


def main() -> int:
    from analista import segmentos

    anclas = {t: sa for t, sa in segmentos.anclas_del_catalogo().items() if sa[0] == "acciones"}
    if not anclas:
        print("No hay acciones con ancla en el catálogo.")
        return 1
    r = ingestar(anclas)
    print(f"acciones: {r['total']} · fechas de resultados {r['fechas']} · con informes SEC {r['con_informes']}")
    return 0 if (r["fechas"] or r["con_informes"]) else 1


if __name__ == "__main__":
    sys.exit(main())
