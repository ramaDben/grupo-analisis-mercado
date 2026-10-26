#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""preparar.py — Preparación de datos para el Lienzo del Webinar Diario.

Lee configuración, agenda económica, curva soberana, drivers macroeconómicos y
lecturas técnicas de los activos principales (USDCLP, XAUUSD, WTI, US100).
Persiste el resultado en `data/webinar/<fecha>/datos.json`.

CLI:
    uv run --with MetaTrader5 python scripts/webinar/preparar.py [--fecha AAAA-MM-DD]
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Callable
from zoneinfo import ZoneInfo

# Asegurar src/ y scripts/ en sys.path
RAIZ = Path(__file__).resolve().parents[2]
for _p in (RAIZ / "src", RAIZ / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

SANTIAGO = ZoneInfo("America/Santiago")

DIAS_MAP: dict[int, str] = {
    0: "lunes",
    1: "martes",
    2: "miercoles",
    3: "jueves",
    4: "viernes",
}

ACTIVOS_WEBINAR = ("USDCLP", "XAUUSD", "WTI.spot", "US100.spot")

CAMPOS_EDITORIALES = [
    "noticia.titular",
    "noticia.bajada",
    "noticia.url",
    "noticia.fecha",
    "noticia.motivo_imagen",
    "teoria.tema",
    "teoria.idea_central",
    "teoria.puntos",
    "teoria.ejemplo",
    "teoria.preguntas_chat",
]

# Eventos que el glosario no distingue (los tres de la Fed salían como «Comité de mercado abierto
# de la Fed») o que engancha mal (la decisión del BCE salía con la explicación de la TPM de Chile).
NOMBRES_ES: dict[str, str] = {
    "Chile:Interest Rate Decision": "Decisión de tasa del Banco Central de Chile (TPM)",
    "Chile:Unemployment Rate": "Tasa de desempleo de Chile",
    "Chile:Copper Production": "Producción de cobre de Chile",
    "Chile:Chilean Manufacturing Production": "Producción manufacturera de Chile",
    "Chile:Retail Sales": "Ventas minoristas de Chile",
    "Chile:Economic Activity": "Imacec (actividad económica de Chile)",
    "Chile:CPI": "IPC de Chile",
    "Fed Interest Rate Decision": "Decisión de tasas de la Fed",
    "FOMC Statement": "Comunicado de la Fed",
    "FOMC Press Conference": "Conferencia de prensa de la Fed",
    "FOMC Economic Projections": "Proyecciones económicas de la Fed",
    "ECB Interest Rate Decision": "Decisión de tasas del BCE",
    "Deposit Facility Rate": "Tasa de depósito del BCE",
    "ECB Press Conference": "Conferencia de prensa del BCE",
    "Manufacturing PMI": "PMI manufacturero",
    "Chicago PMI": "PMI de Chicago",
}

PAISES: dict[str, str] = {
    "United States": "EE.UU.",
    "Chile": "Chile",
    "China": "China",
    "Euro Zone": "Zona Euro",
    "Euro Area": "Zona Euro",
    "Zona Euro": "Zona Euro",
    "Switzerland": "Suiza",
    "Japan": "Japón",
    "United Kingdom": "Reino Unido",
    "Germany": "Alemania",
}


def formatear_precio(valor: float, digits: int) -> str:
    """Precio en notación chilena con los decimales indicados."""
    if digits == 0:
        return f"{valor:.0f}"
    return f"{valor:,.{digits}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def formatear_bps(delta: float | None) -> str:
    """Variación en puntos base. Un delta None se muestra 'sin dato', nunca 0."""
    if delta is None:
        return "sin dato"
    try:
        val = float(delta)
    except (ValueError, TypeError):
        return "sin dato"
    if val == 0:
        return "0 pb"
    return f"{val:+.0f} pb"


def _cifra_es(valor: str) -> str:
    """Intercambia punto y coma para notación chilena."""
    if not valor:
        return ""
    return valor.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def obtener_digits_activos(ruta_activos: Path | None = None) -> dict[str, int]:
    """Carga los decimales definidos en config/activos.json."""
    ruta = ruta_activos or (RAIZ / "config" / "activos.json")
    if ruta.exists():
        try:
            from market_data_mcp.catalog import load_valid_tickers

            return load_valid_tickers()
        except Exception:
            pass
    return {"USDCLP": 2, "XAUUSD": 2, "WTI.spot": 3, "US100.spot": 2}


def _formatear_evento_agenda(ev: dict[str, Any]) -> dict[str, Any]:
    """Adapta un evento del calendario Investing al formato requerido."""
    pais_raw = str(ev.get("pais", ""))
    pais = PAISES.get(pais_raw, pais_raw)

    diccionario = ev.get("diccionario") or {}
    # El glosario a veces engancha la entrada de otro país (la decisión del BCE salía con la
    # explicación de la TPM de Chile): si su país no es el del evento, va el nombre original.
    pais_glosario = diccionario.get("pais")
    propio = not pais_glosario or pais_glosario == pais_raw
    original = ev.get("nombre", "")
    base = original.split(" (")[0].strip()
    nombre = (NOMBRES_ES.get(f"{pais_raw}:{base}") or NOMBRES_ES.get(base)
              or (diccionario.get("nombre_es") if propio else None) or original)

    hora_raw = str(ev.get("hora") or ev.get("hora_servidor", ""))
    if " " in hora_raw:
        partes = hora_raw.split(" ", 1)
        fecha_ev = partes[0]
        hora_ev = partes[1]
    else:
        fecha_ev = str(ev.get("fecha", ""))
        hora_ev = hora_raw

    ant_val = ev.get("anterior") if "anterior" in ev else ev.get("previo", "")
    con_val = ev.get("consenso") if "consenso" in ev else ev.get("forecast", "")
    act_val = ev.get("actual", "")

    anterior = _cifra_es(str(ant_val or "").strip())
    consenso = _cifra_es(str(con_val or "").strip())
    actual = _cifra_es(str(act_val or "").strip())

    return {
        "fecha": fecha_ev,
        "hora": hora_ev,
        "pais": pais,
        "nombre": nombre,
        "impacto": ev.get("impacto", "medio"),
        "anterior": anterior,
        "consenso": consenso,
        "actual": actual,
        "fuente": "Investing.com",
    }


def evaluar_editorial_pendiente(ruta_editorial: Path) -> list[str]:
    """Verifica qué campos obligatorios del editorial faltan en el JSON."""
    if not ruta_editorial.exists():
        return list(CAMPOS_EDITORIALES)
    try:
        data = json.loads(ruta_editorial.read_text(encoding="utf-8"))
    except Exception:
        return list(CAMPOS_EDITORIALES)

    pendientes: list[str] = []
    for campo in CAMPOS_EDITORIALES:
        seccion, subcampo = campo.split(".", 1)
        nodo = data.get(seccion)
        if not isinstance(nodo, dict):
            pendientes.append(campo)
            continue
        val = nodo.get(subcampo)
        if val is None:
            pendientes.append(campo)
        elif isinstance(val, str) and not val.strip():
            pendientes.append(campo)
        elif isinstance(val, (list, tuple, dict)) and len(val) == 0:
            pendientes.append(campo)
    return pendientes


def _leer_ohlc_fallback(simbolo: str) -> list[tuple[date, float]]:
    """Lee cierres diarios desde data central/DATA PRECIOS OHLC como respaldo."""
    ruta = RAIZ / "data central" / "DATA PRECIOS OHLC" / f"{simbolo}_D1.json"
    if not ruta.exists():
        return []
    try:
        filas = json.loads(ruta.read_text(encoding="utf-8")).get("rows", [])
        puntos: list[tuple[date, float]] = []
        for r in filas[-7:]:
            d = datetime.fromisoformat(r["time"]).date()
            puntos.append((d, float(r["close"])))
        return puntos
    except Exception:
        return []


def obtener_drivers_default(hoy: date) -> list[dict[str, Any]]:
    """Mide los drivers macro principales (DXY, Cobre, WTI) reutilizando analista.hechos."""
    from analista import hechos as hc

    drivers_salida: list[dict[str, Any]] = []
    mapeo = [
        ("dxy", "USDIDX"),
        ("cobre", "COPPER"),
        ("petroleo", "WTI.spot"),
    ]

    for medible, sim_mt5 in mapeo:
        puntos: list[tuple[date, float]] = []
        fuente = f"MT5 ({sim_mt5})"
        try:
            puntos = hc.leer_d1_mt5(sim_mt5, 7)
        except Exception:
            puntos = []

        if len(puntos) < 6:
            # Fallback
            sim_archivo = "WTI" if sim_mt5 == "WTI.spot" else sim_mt5
            puntos = _leer_ohlc_fallback(sim_archivo)
            fuente = f"data central ({sim_archivo})"

        if len(puntos) >= 6:
            try:
                h = hc._de_serie(medible, puntos, fuente, hoy)
                if h is not None:
                    drivers_salida.append({
                        "etiqueta": h["driver"],
                        "valor": h["nivel"],
                        "unidad": h["unidad_cambio"],
                        "fecha": str(h["fecha"]),
                        "fuente": h["fuente"],
                        # hechos entrega la magnitud sin signo y el sentido aparte.
                        "cambio_5d": (f'estable ({h["cambio_5d"]} {h["unidad_cambio"]})' if h["sentido"] == "estable"
                                      else f'{h["sentido"]} {h["cambio_5d"]} {h["unidad_cambio"]}'),
                    })
            except Exception:
                continue

    return drivers_salida


def _leer_activo(
    ticker: str,
    digits: int,
    ahora: datetime,
    lector_lectura: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Obtiene la lectura técnica de un activo o {'estado': 'sin_terminal'} ante fallas."""
    if lector_lectura is not None:
        try:
            sig = inspect.signature(lector_lectura)
            params = len(sig.parameters)
            if params >= 2:
                res = lector_lectura(ticker, ahora)
            elif params == 1:
                res = lector_lectura(ticker)
            else:
                res = lector_lectura()
        except TypeError:
            try:
                res = lector_lectura(ticker)
            except Exception:
                return {"estado": "sin_terminal"}
        except Exception:
            return {"estado": "sin_terminal"}
    else:
        try:
            from estrategia import registro
            import referencia_semanal as rs
            from estrategia.fuente import velas_mt5

            est = registro.activa()
            res, _ = rs.lectura_actual(est, ticker, digits, velas_mt5, ahora)
        except Exception:
            return {"estado": "sin_terminal"}

    if res is None:
        return {"estado": "sin_terminal"}

    if isinstance(res, dict):
        if res.get("estado") == "sin_terminal" or "error" in res:
            return {"estado": "sin_terminal"}
        lec = res.get("lectura", res)
        direccion = lec.get("direccion")
        estado = lec.get("estado")
        vigilar = lec.get("vigilar")
        if estado == "sin_terminal" or not direccion or not estado:
            return {"estado": "sin_terminal"}
        if isinstance(vigilar, (int, float)):
            vigilar_str = formatear_precio(float(vigilar), digits)
        elif isinstance(vigilar, dict) and "precio" in vigilar:
            vigilar_str = formatear_precio(float(vigilar["precio"]), digits)
        elif hasattr(vigilar, "precio"):
            vigilar_str = formatear_precio(float(vigilar.precio), digits)
        elif isinstance(vigilar, str):
            vigilar_str = vigilar
        else:
            vigilar_str = "sin dato"
        return {
            "direccion": str(direccion),
            "estado": str(estado),
            "vigilar": vigilar_str,
        }

    try:
        direccion = getattr(res, "direccion", None)
        estado = getattr(res, "estado", None)
        vigilar = getattr(res, "vigilar", None)
        if not direccion or not estado or not vigilar:
            return {"estado": "sin_terminal"}
        precio = getattr(vigilar, "precio", None)
        vigilar_str = "sin dato" if precio is None else formatear_precio(float(precio), digits)
        return {
            "direccion": str(direccion),
            "estado": str(estado),
            "vigilar": vigilar_str,
        }
    except Exception:
        return {"estado": "sin_terminal"}


def preparar(
    fecha: date | None = None,
    *,
    lector_calendario: Callable[..., Any] | None = None,
    lector_curva: Callable[..., Any] | None = None,
    lector_lectura: Callable[..., Any] | None = None,
    lector_drivers: Callable[..., Any] | None = None,
    ruta_config: Path | None = None,
    dir_salida: Path | None = None,
) -> dict[str, Any]:
    """Prepara y persiste los datos del webinar diario."""
    if fecha is None:
        ahora_scl = datetime.now(SANTIAGO)
        fecha = ahora_scl.date()

    # Si es fin de semana (sábado=5, domingo=6), mapear al lunes siguiente
    if fecha.weekday() >= 5:
        dias_hasta_lunes = 7 - fecha.weekday()
        fecha = fecha + timedelta(days=dias_hasta_lunes)

    dia = DIAS_MAP[fecha.weekday()]

    cfg_path = ruta_config or (RAIZ / "config" / "webinar.json")
    if not cfg_path.exists():
        raise FileNotFoundError(f"Configuración de webinar no encontrada en {cfg_path}")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    dia_cfg = cfg.get("dias", {}).get(dia)
    if not dia_cfg:
        raise ValueError(f"Día '{dia}' no configurado en {cfg_path}")

    # 1. Metadatos
    meta = {
        "fecha": fecha.isoformat(),
        "dia": dia,
        "titulo": dia_cfg.get("titulo", ""),
        "horario": f"{dia_cfg.get('hora_inicio', '')} a {dia_cfg.get('hora_fin', '')}",
        "guion": dia_cfg.get("guion", []),
        "generado": datetime.now(SANTIAGO).isoformat(),
        "disclaimer": cfg.get("disclaimer", ""),
        "cta": cfg.get("cta", ""),
    }

    # 2. Agenda
    agenda: dict[str, Any]
    try:
        if lector_calendario is None:
            from market_data_mcp.tools.calendar import cargar_calendario

            lector_cal = cargar_calendario
        else:
            lector_cal = lector_calendario

        ahora_ref = datetime.combine(fecha, datetime.min.time(), tzinfo=SANTIAGO)
        if dia == "lunes":
            try:
                res_cal = lector_cal(solo_hoy=False, pestanas=("thisWeek",), ahora=ahora_ref, min_impact="low")
            except TypeError:
                try:
                    res_cal = lector_cal(solo_hoy=False, pestanas=("thisWeek",))
                except TypeError:
                    try:
                        res_cal = lector_cal(solo_hoy=False)
                    except TypeError:
                        res_cal = lector_cal()
        else:
            try:
                res_cal = lector_cal(solo_hoy=True, ahora=ahora_ref, min_impact="low")
            except TypeError:
                try:
                    res_cal = lector_cal(solo_hoy=True)
                except TypeError:
                    res_cal = lector_cal()

        if isinstance(res_cal, dict) and "error" in res_cal:
            agenda = {
                "estado": "sin_calendario",
                "motivo": str(res_cal.get("message") or res_cal["error"]),
            }
        else:
            raw_eventos = (
                res_cal.get("eventos", [])
                if isinstance(res_cal, dict)
                else (res_cal if isinstance(res_cal, list) else [])
            )
            eventos_formateados = [_formatear_evento_agenda(ev) for ev in raw_eventos]
            agenda = {"estado": "ok", "eventos": eventos_formateados}
    except Exception as exc:
        agenda = {"estado": "sin_calendario", "motivo": str(exc)}

    # 3. Datos macroeconómicos (Curva soberana + Drivers)
    datos_lista: list[dict[str, Any]] = []

    # Curva soberana
    try:
        if lector_curva is None:
            from market_data_mcp.curva_reader import cargar_curva_tasas

            curva_raw = cargar_curva_tasas()
        else:
            try:
                curva_raw = lector_curva("ALL")
            except TypeError:
                curva_raw = lector_curva()

        if isinstance(curva_raw, dict) and "error" not in curva_raw:
            series = curva_raw.get("series", {})
            spread = curva_raw.get("spread_2s10s", {})
            procedencia = curva_raw.get("procedencia", {})
            fuente_curva = (
                procedencia.get("fuente_tesoro")
                or procedencia.get("fuente_fed")
                or "Tesoro de EE.UU. / FRED"
            )

            def _fmt_pct(val: Any) -> str:
                if val is None:
                    return "sin dato"
                try:
                    return f"{float(val):.2f}".replace(".", ",")
                except (ValueError, TypeError):
                    return "sin dato"

            s2 = series.get("DGS2") or {}
            datos_lista.append({
                "etiqueta": "Bono del Tesoro a 2 años (DGS2)",
                "valor": _fmt_pct(s2.get("nivel_pct")),
                "unidad": "%",
                "fecha": str(s2.get("fecha_dato") or "sin dato"),
                "fuente": fuente_curva,
                "cambio_5d": formatear_bps(s2.get("delta_5d_bps")),
            })

            s10 = series.get("DGS10") or {}
            datos_lista.append({
                "etiqueta": "Bono del Tesoro a 10 años (DGS10)",
                "valor": _fmt_pct(s10.get("nivel_pct")),
                "unidad": "%",
                "fecha": str(s10.get("fecha_dato") or "sin dato"),
                "fuente": fuente_curva,
                "cambio_5d": formatear_bps(s10.get("delta_5d_bps")),
            })

            stips = series.get("DFII10") or {}
            datos_lista.append({
                "etiqueta": "Tasa real TIPS a 10 años (DFII10)",
                "valor": _fmt_pct(stips.get("nivel_pct")),
                "unidad": "%",
                "fecha": str(stips.get("fecha_dato") or "sin dato"),
                "fuente": fuente_curva,
                "cambio_5d": formatear_bps(stips.get("delta_5d_bps")),
            })

            sfed = series.get("DFF") or {}
            datos_lista.append({
                "etiqueta": "Tasa de la Fed / Fondos Federales (DFF)",
                "valor": _fmt_pct(sfed.get("nivel_pct")),
                "unidad": "%",
                "fecha": str(sfed.get("fecha_dato") or "sin dato"),
                "fuente": procedencia.get("fuente_fed") or "FRED",
                "cambio_5d": formatear_bps(sfed.get("delta_5d_bps")),
            })

            datos_lista.append({
                "etiqueta": "Pendiente de la curva 2s10s",
                "valor": _fmt_pct(spread.get("nivel_pct")),
                "unidad": "%",
                "fecha": str(spread.get("fecha_dato") or "sin dato"),
                "fuente": fuente_curva,
                "cambio_5d": formatear_bps(spread.get("delta_5d_bps")),
            })
        else:
            for eti in (
                "Bono del Tesoro a 2 años (DGS2)",
                "Bono del Tesoro a 10 años (DGS10)",
                "Tasa real TIPS a 10 años (DFII10)",
                "Tasa de la Fed / Fondos Federales (DFF)",
                "Pendiente de la curva 2s10s",
            ):
                datos_lista.append({
                    "etiqueta": eti,
                    "valor": "sin dato",
                    "unidad": "%",
                    "fecha": "sin dato",
                    "fuente": "FRED / Tesoro de EE.UU.",
                    "cambio_5d": "sin dato",
                })
    except Exception:
        for eti in (
            "Bono del Tesoro a 2 años (DGS2)",
            "Bono del Tesoro a 10 años (DGS10)",
            "Tasa real TIPS a 10 años (DFII10)",
            "Tasa de la Fed / Fondos Federales (DFF)",
            "Pendiente de la curva 2s10s",
        ):
            datos_lista.append({
                "etiqueta": eti,
                "valor": "sin dato",
                "unidad": "%",
                "fecha": "sin dato",
                "fuente": "FRED / Tesoro de EE.UU.",
                "cambio_5d": "sin dato",
            })

    # Drivers macroeconómicos
    try:
        if lector_drivers is not None:
            try:
                sig = inspect.signature(lector_drivers)
                if len(sig.parameters) >= 1:
                    drivers_raw = lector_drivers(fecha)
                else:
                    drivers_raw = lector_drivers()
            except Exception:
                drivers_raw = []
        else:
            drivers_raw = obtener_drivers_default(fecha)

        for drv in drivers_raw:
            if isinstance(drv, dict):
                eti = drv.get("etiqueta") or drv.get("driver", "")
                val = drv.get("valor") or drv.get("nivel", "sin dato")
                uni = drv.get("unidad") or drv.get("unidad_cambio", "")
                fec = drv.get("fecha", "sin dato")
                fue = drv.get("fuente", "")
                c5d = drv.get("cambio_5d")
                c5d_str = "sin dato" if c5d is None else str(c5d)
                datos_lista.append({
                    "etiqueta": str(eti),
                    "valor": str(val),
                    "unidad": str(uni),
                    "fecha": str(fec),
                    "fuente": str(fue),
                    "cambio_5d": c5d_str,
                })
    except Exception:
        pass

    # 4. Activos
    activos: dict[str, Any] = {}
    digits_map = obtener_digits_activos()
    ahora_dt = datetime.combine(fecha, datetime.min.time(), tzinfo=SANTIAGO)

    for ticker in ACTIVOS_WEBINAR:
        d = digits_map.get(ticker, 2)
        activos[ticker] = _leer_activo(ticker, d, ahora_dt, lector_lectura)

    # 5. Editorial pendiente
    fecha_str = fecha.isoformat()
    if dir_salida is None:
        carpeta = RAIZ / "data" / "webinar" / fecha_str
    else:
        carpeta = dir_salida if dir_salida.name == fecha_str else (dir_salida / fecha_str)

    ruta_editorial = carpeta / "editorial.json"
    editorial_pendiente = evaluar_editorial_pendiente(ruta_editorial)

    salida: dict[str, Any] = {
        "meta": meta,
        "agenda": agenda,
        "datos": datos_lista,
        "activos": activos,
        "editorial_pendiente": editorial_pendiente,
    }

    carpeta.mkdir(parents=True, exist_ok=True)
    ruta_datos = carpeta / "datos.json"
    ruta_datos.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")

    return salida


def main() -> None:
    """Punto de entrada CLI."""
    parser = argparse.ArgumentParser(description="Prepara los datos del webinar diario.")
    parser.add_argument("--fecha", type=str, default=None, help="Fecha en formato AAAA-MM-DD")
    args = parser.parse_args()

    fecha = date.fromisoformat(args.fecha) if args.fecha else None
    res = preparar(fecha=fecha)
    meta = res.get("meta", {})
    print(f"Webinar preparado para {meta.get('fecha')} ({meta.get('dia')})")
    print(f"Agenda: {res.get('agenda', {}).get('estado')}")
    print(f"Activos: {len(res.get('activos', {}))} activos leídos")
    print(f"Datos macro: {len(res.get('datos', []))} filas")
    print(f"Editorial pendiente: {len(res.get('editorial_pendiente', []))} campos")


if __name__ == "__main__":
    main()
