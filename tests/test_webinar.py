"""Tests para el módulo de preparación del Webinar Diario (scripts/webinar/preparar.py).

Cubre:
- Contrato de error y resiliencia de lectores inyectables (calendario, curva, lectura técnica, drivers).
- Comportamiento de deltas nulos en la curva ('sin dato', nunca '0').
- Manejo de terminal caído / fallas en lectura técnica ({'estado': 'sin_terminal'}).
- Verificación exhaustiva de config/webinar.json (5 días, sin CMF, bloques válidos, horas crecientes).
- Mapeo de días de la semana y fin de semana hacia el lunes siguiente.
- Cálculo de campos editoriales pendientes.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
import sys
from unittest.mock import MagicMock

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from webinar.preparar import (  # noqa: E402
    ACTIVOS_WEBINAR,
    CAMPOS_EDITORIALES,
    evaluar_editorial_pendiente,
    formatear_bps,
    formatear_precio,
    preparar,
)
from webinar.rendir import rendir, validar_editorial  # noqa: E402


# ───────────────────────────────────────────────────────────── 1. Configuración
def test_config_webinar_estructura_y_reglas():
    """Valida que config/webinar.json cumpla con las 5 jornadas, sin 'CMF' y con guiones coherentes."""
    ruta_cfg = RAIZ / "config" / "webinar.json"
    assert ruta_cfg.exists(), "config/webinar.json debe existir"

    contenido_raw = ruta_cfg.read_text(encoding="utf-8")
    assert "CMF" not in contenido_raw, "Regla crítica: ningún 'CMF' en config/webinar.json"

    cfg = json.loads(contenido_raw)

    # 5 días exactos en español en minúsculas
    dias_esperados = ["lunes", "martes", "miercoles", "jueves", "viernes"]
    assert list(cfg.get("dias", {}).keys()) == dias_esperados

    bloques_permitidos = {
        "portada",
        "aviso_legal",
        "agenda",
        "noticia",
        "bancos",
        "datos",
        "teoria",
        "mt5",
        "preguntas",
        "cierre",
    }

    for dia in dias_esperados:
        info_dia = cfg["dias"][dia]
        assert "titulo" in info_dia and info_dia["titulo"].strip()
        assert "hora_inicio" in info_dia and info_dia["hora_inicio"].strip()
        assert "hora_fin" in info_dia and info_dia["hora_fin"].strip()
        assert info_dia["hora_inicio"] < info_dia["hora_fin"]

        guion = info_dia.get("guion", [])
        assert len(guion) >= 3, f"{dia} debe tener al menos 3 bloques de guion"

        # Verificar primer bloque y último bloque coincidan con horario del día
        assert guion[0]["desde"] == info_dia["hora_inicio"]
        assert guion[-1]["hasta"] == info_dia["hora_fin"]

        hora_anterior = None
        for bloque in guion:
            # IDs de bloque permitidos
            assert bloque["bloque"] in bloques_permitidos, (
                f"Bloque '{bloque['bloque']}' en {dia} no es uno de {bloques_permitidos}"
            )
            assert bloque["desde"] < bloque["hasta"], f"Horas invertidas en {dia}: {bloque}"
            if hora_anterior is not None:
                assert bloque["desde"] >= hora_anterior, (
                    f"Horas no crecientes en {dia}: {bloque['desde']} < {hora_anterior}"
                )
            hora_anterior = bloque["hasta"]

    assert "disclaimer" in cfg and cfg["disclaimer"].strip()
    assert "cta" in cfg and cfg["cta"].strip()


# ───────────────────────────────────────────────────────────── 2. Calendario
def test_lector_calendario_falla_marca_sin_calendario(tmp_path):
    """Si el lector de calendario lanza excepción o devuelve error, agenda['estado'] == 'sin_calendario'."""

    def lector_que_lanza(**_kw):
        raise ConnectionResetError("Investing.com no responde")

    res = preparar(
        fecha=date(2026, 10, 26),
        dir_salida=tmp_path,
        lector_calendario=lector_que_lanza,
        lector_curva=lambda *a: {"series": {}, "spread_2s10s": {}},
        lector_lectura=lambda *a: {"estado": "sin_terminal"},
        lector_drivers=lambda *a: [],
    )

    assert res["agenda"]["estado"] == "sin_calendario"
    assert "Investing.com no responde" in res["agenda"]["motivo"]

    # Caso en que devuelve dict con error
    def lector_con_error(**_kw):
        return {"error": "NO_CALENDAR_FEEDS", "message": "Feed timeout"}

    res2 = preparar(
        fecha=date(2026, 10, 26),
        dir_salida=tmp_path,
        lector_calendario=lector_con_error,
        lector_curva=lambda *a: {"series": {}, "spread_2s10s": {}},
        lector_lectura=lambda *a: {"estado": "sin_terminal"},
        lector_drivers=lambda *a: [],
    )
    assert res2["agenda"]["estado"] == "sin_calendario"
    assert "Feed timeout" in res2["agenda"]["motivo"]


def test_lector_calendario_exito_formatea_eventos(tmp_path):
    """Eventos válidos son parseados con país traducido, horas respetadas y cifras en notación chilena."""
    mock_eventos = [
        {
            "hora_servidor": "2026-10-26 10:30",
            "pais": "United States",
            "nombre": "Nonfarm Payrolls",
            "impacto": "alto",
            "forecast": "180,000",
            "previo": "150,000",
            "actual": "195,000",
            "diccionario": {"nombre_es": "Nóminas No Agrícolas (NFP)"},
        }
    ]

    res = preparar(
        fecha=date(2026, 10, 26),
        dir_salida=tmp_path,
        lector_calendario=lambda **_kw: {"eventos": mock_eventos},
        lector_curva=lambda *a: {"series": {}, "spread_2s10s": {}},
        lector_lectura=lambda *a: {"estado": "sin_terminal"},
        lector_drivers=lambda *a: [],
    )

    assert res["agenda"]["estado"] == "ok"
    evs = res["agenda"]["eventos"]
    assert len(evs) == 1
    ev = evs[0]
    assert ev["hora"] == "10:30"
    assert ev["fecha"] == "2026-10-26"
    assert ev["pais"] == "EE.UU."
    assert ev["nombre"] == "Nóminas No Agrícolas (NFP)"
    assert ev["impacto"] == "alto"
    assert ev["anterior"] == "150.000"
    assert ev["consenso"] == "180.000"
    assert ev["actual"] == "195.000"
    assert ev["fuente"] == "Investing.com"


# ───────────────────────────────────────────────────────────── 3. Curva Soberana
def test_lector_curva_delta_null_muestra_sin_dato_nunca_cero(tmp_path):
    """Un delta null de la curva debe mostrar 'sin dato', NUNCA '0' ni '0 pb'."""
    curva_mock = {
        "as_of": "2026-10-25T12:00:00",
        "procedencia": {"fuente_tesoro": "Tesoro EE.UU.", "fuente_fed": "FRED"},
        "series": {
            "DGS2": {"nivel_pct": 4.50, "fecha_dato": "2026-10-23", "delta_5d_bps": None},
            "DGS10": {"nivel_pct": 4.80, "fecha_dato": "2026-10-23", "delta_5d_bps": None},
            "DFII10": {"nivel_pct": 2.20, "fecha_dato": "2026-10-23", "delta_5d_bps": None},
            "DFF": {"nivel_pct": 4.00, "fecha_dato": "2026-10-23", "delta_5d_bps": None},
        },
        "spread_2s10s": {
            "nivel_pct": 0.30,
            "fecha_dato": "2026-10-23",
            "delta_5d_bps": None,
        },
    }

    res = preparar(
        fecha=date(2026, 10, 26),
        dir_salida=tmp_path,
        lector_calendario=lambda **_kw: {"eventos": []},
        lector_curva=lambda *a: curva_mock,
        lector_lectura=lambda *a: {"estado": "sin_terminal"},
        lector_drivers=lambda *a: [],
    )

    datos = res["datos"]
    etiquetas_curva = [
        "Bono del Tesoro a 2 años (DGS2)",
        "Bono del Tesoro a 10 años (DGS10)",
        "Tasa real TIPS a 10 años (DFII10)",
        "Tasa de la Fed / Fondos Federales (DFF)",
        "Pendiente de la curva 2s10s",
    ]

    for eti in etiquetas_curva:
        fila = next((d for d in datos if d["etiqueta"] == eti), None)
        assert fila is not None, f"Falta fila {eti} en datos"
        assert fila["cambio_5d"] == "sin dato", (
            f"{eti}: cambio_5d debe ser 'sin dato' cuando delta es None, pero vino '{fila['cambio_5d']}'"
        )
        assert fila["cambio_5d"] != "0"
        assert fila["cambio_5d"] != "0 pb"


def test_lector_curva_con_deltas_numericos(tmp_path):
    """Valida formateo de deltas positivos y negativos en puntos base."""
    assert formatear_bps(-14.0) == "-14 pb"
    assert formatear_bps(25.0) == "+25 pb"
    assert formatear_bps(0.0) == "0 pb"
    assert formatear_bps(None) == "sin dato"
    # Formateo de precios en notación chilena
    assert formatear_precio(981.05, 2) == "981,05"
    assert formatear_precio(4145.5, 2) == "4.145,50"
    assert formatear_precio(14417.0, 0) == "14417"


# ───────────────────────────────────────────────────────────── 4. Activos / MT5
def test_lector_lectura_falla_o_lanza_excepcion_activos_sin_terminal(tmp_path):
    """Si el lector de lectura técnica lanza excepción, todos los activos quedan en {'estado': 'sin_terminal'}."""

    def lector_caido(_ticker, *_args):
        raise ConnectionError("Terminal MT5 no disponible")

    res = preparar(
        fecha=date(2026, 10, 26),
        dir_salida=tmp_path,
        lector_calendario=lambda **_kw: {"eventos": []},
        lector_curva=lambda *a: {"series": {}, "spread_2s10s": {}},
        lector_lectura=lector_caido,
        lector_drivers=lambda *a: [],
    )

    activos = res["activos"]
    assert set(activos.keys()) == set(ACTIVOS_WEBINAR)
    for ticker in ACTIVOS_WEBINAR:
        assert activos[ticker] == {"estado": "sin_terminal"}


def test_lector_lectura_exito_formatea_digits_y_campos(tmp_path):
    """Si el lector responde con éxito, se extrae direccion, estado y vigilar con notación chilena."""

    def lector_ok(ticker, *_a):
        # Dict o mock con vigilar
        vigilar_mock = MagicMock()
        precios = {"USDCLP": 981.054, "XAUUSD": 4145.5, "WTI.spot": 99.224, "US100.spot": 29330.62}
        vigilar_mock.precio = precios[ticker]

        lectura_mock = MagicMock()
        lectura_mock.direccion = "ALCISTA" if "USD" in ticker or "WTI" in ticker else "BAJISTA"
        lectura_mock.estado = "TENDENCIA"
        lectura_mock.vigilar = vigilar_mock
        return lectura_mock

    res = preparar(
        fecha=date(2026, 10, 26),
        dir_salida=tmp_path,
        lector_calendario=lambda **_kw: {"eventos": []},
        lector_curva=lambda *a: {"series": {}, "spread_2s10s": {}},
        lector_lectura=lector_ok,
        lector_drivers=lambda *a: [],
    )

    activos = res["activos"]
    assert activos["USDCLP"]["direccion"] == "ALCISTA"
    assert activos["USDCLP"]["estado"] == "TENDENCIA"
    assert activos["USDCLP"]["vigilar"] == "981,05"  # 2 decimales

    assert activos["XAUUSD"]["vigilar"] == "4.145,50"  # 2 decimales con separador de miles
    assert activos["WTI.spot"]["vigilar"] == "99,224"  # 3 decimales
    assert activos["US100.spot"]["vigilar"] == "29.330,62"  # 2 decimales con miles


# ───────────────────────────────────────────────────────────── 5. Editorial pendiente
def test_editorial_pendiente_evaluacion(tmp_path):
    """Evalúa correctamente campos faltantes según existencia de editorial.json."""
    dir_dia = tmp_path / "2026-10-26"
    dir_dia.mkdir(parents=True, exist_ok=True)
    ruta_editorial = dir_dia / "editorial.json"

    # Caso 1: Archivo no existe -> todos pendientes
    pendientes = evaluar_editorial_pendiente(ruta_editorial)
    assert pendientes == list(CAMPOS_EDITORIALES)

    # Caso 2: Archivo parcial (le falta la bajada y preguntas_chat)
    editorial_incompleto = {
        "noticia": {
            "titular": "Titular de prueba",
            "bajada": "",  # Vacío
            "url": "https://example.com",
            "fecha": "2026-10-26",
            "motivo_imagen": "oro_lingotes",
        },
        "teoria": {
            "tema": "Tema de prueba",
            "idea_central": "Idea de prueba",
            "puntos": ["Punto 1"],
            "ejemplo": "Ejemplo 1",
            "preguntas_chat": [],  # Lista vacía
        },
    }
    ruta_editorial.write_text(json.dumps(editorial_incompleto), encoding="utf-8")
    pendientes2 = evaluar_editorial_pendiente(ruta_editorial)
    assert "noticia.bajada" in pendientes2
    assert "teoria.preguntas_chat" in pendientes2
    assert "noticia.titular" not in pendientes2
    assert "teoria.puntos" not in pendientes2

    # Caso 3: Archivo completo -> 0 pendientes
    editorial_completo = {
        "noticia": {
            "titular": "Titular",
            "bajada": "Bajada informativa",
            "url": "https://example.com",
            "fecha": "2026-10-26",
            "motivo_imagen": "oro_lingotes",
        },
        "teoria": {
            "tema": "Tema",
            "idea_central": "Idea",
            "puntos": ["Punto 1"],
            "ejemplo": "Ejemplo 1",
            "preguntas_chat": ["Pregunta 1"],
        },
    }
    ruta_editorial.write_text(json.dumps(editorial_completo), encoding="utf-8")
    pendientes3 = evaluar_editorial_pendiente(ruta_editorial)
    assert pendientes3 == []


# ───────────────────────────────────────────────────────────── 6. Mapeo Fechas y Persistencia
def test_mapeo_fin_de_semana_al_lunes(tmp_path):
    """Sábado y domingo se mapean al lunes inmediatamente siguiente."""
    # Sábado 2026-10-24 -> Lunes 2026-10-26
    res_sabado = preparar(
        fecha=date(2026, 10, 24),
        dir_salida=tmp_path,
        lector_calendario=lambda **_kw: {"eventos": []},
        lector_curva=lambda *a: {"series": {}, "spread_2s10s": {}},
        lector_lectura=lambda *a: {"estado": "sin_terminal"},
        lector_drivers=lambda *a: [],
    )
    assert res_sabado["meta"]["dia"] == "lunes"
    assert res_sabado["meta"]["fecha"] == "2026-10-26"

    # Domingo 2026-10-25 -> Lunes 2026-10-26
    res_domingo = preparar(
        fecha=date(2026, 10, 25),
        dir_salida=tmp_path,
        lector_calendario=lambda **_kw: {"eventos": []},
        lector_curva=lambda *a: {"series": {}, "spread_2s10s": {}},
        lector_lectura=lambda *a: {"estado": "sin_terminal"},
        lector_drivers=lambda *a: [],
    )
    assert res_domingo["meta"]["dia"] == "lunes"
    assert res_domingo["meta"]["fecha"] == "2026-10-26"

    # Miércoles 2026-10-28 -> Miércoles 2026-10-28
    res_miercoles = preparar(
        fecha=date(2026, 10, 28),
        dir_salida=tmp_path,
        lector_calendario=lambda **_kw: {"eventos": []},
        lector_curva=lambda *a: {"series": {}, "spread_2s10s": {}},
        lector_lectura=lambda *a: {"estado": "sin_terminal"},
        lector_drivers=lambda *a: [],
    )
    assert res_miercoles["meta"]["dia"] == "miercoles"
    assert res_miercoles["meta"]["fecha"] == "2026-10-28"


def test_escritura_archivo_datos_json(tmp_path):
    """Verifica que el archivo datos.json se escriba y contenga todas las claves requeridas."""
    fecha_test = date(2026, 10, 27)
    res = preparar(
        fecha=fecha_test,
        dir_salida=tmp_path,
        lector_calendario=lambda **_kw: {"eventos": []},
        lector_curva=lambda *a: {"series": {}, "spread_2s10s": {}},
        lector_lectura=lambda *a: {"estado": "sin_terminal"},
        lector_drivers=lambda *a: [],
    )

    ruta_esperada = tmp_path / "2026-10-27" / "datos.json"
    assert ruta_esperada.exists(), f"El archivo {ruta_esperada} debe haber sido creado"

    cargado = json.loads(ruta_esperada.read_text(encoding="utf-8"))
    assert cargado == res
    for seccion in ("meta", "agenda", "datos", "activos", "editorial_pendiente"):
        assert seccion in cargado


# ───────────────────────────────────────────────────────────── 7. Fixtures para Rendir
@pytest.fixture
def editorial_valido() -> dict:
    """Fixture de editorial.json completamente válido y conforme a reglas."""
    return {
        "noticia": {
            "medio": "FXStreet",
            "fecha": "2026-10-23",
            "url": "https://www.fxstreet.com/analysis/gold-weekly-forecast-20261023",
            "titular": "El oro cerro la semana en baja: el petroleo mas caro reavivo el temor a la inflacion",
            "bajada": "Ni la caida de los rendimientos del Tesoro lo sostuvo. La reunion de la Fed definira el sesgo.",
            "motivo_imagen": "oro_lingotes",
        },
        "bancos": [
            {
                "banco": "ING",
                "fecha": "2026-10-23",
                "url": "https://think.ing.com/articles/federal-reserve-preview/",
                "resumen": "Espera que la Fed mantenga la tasa este miercoles y que la suba 0,25 puntos en diciembre.",
                "lectura": "Se podría interpretar presión sobre el oro.",
                "motivo_imagen": "banco_central",
            },
            {
                "banco": "TD Securities",
                "fecha": "2026-10-23",
                "url": "https://www.fxstreet.com/news/td-securities-october-hold",
                "resumen": "Ve la tasa sin cambios esta semana y alzas de nuevo en diciembre y marzo proximo.",
                "lectura": "Se podría interpretar presión sobre el oro.",
                "motivo_imagen": "banco_central",
            },
        ],
        "teoria": {
            "tema": "Como leer el calendario economico de la semana",
            "idea_central": "El precio no reacciona al dato en si, reacciona a la sorpresa frente al consenso.",
            "puntos": [
                "Cada evento macroeconomico trae anterior, consenso de analistas y cifra actual.",
                "Si el actual sale igual al consenso, el impacto en precio suele ser reducido.",
                "La sorpresa positiva o negativa es el catalizador real de volatilidad.",
                "En decisiones de bancos centrales, el comunicado y tono importan mas que la tasa.",
            ],
            "ejemplo": "Esta semana la Fed decide mantener en 4,75%: la clave es la conferencia de prensa posterior.",
            "preguntas_chat": [
                "Cual es el dato de mayor impacto para tu operativa esta semana?",
                "Si la inflacion sale sobre el consenso, que reaccion esperas en el dolar?",
            ],
        },
        "notas_guion": {
            "agenda": "Enfatizar PMI de manufactura y decision de tasas.",
            "mt5": "Revisar nivel 940 en USDCLP con temporalidad H1.",
        },
    }


@pytest.fixture
def datos_completos() -> dict:
    """Fixture de datos.json completo con todas las secciones."""
    return {
        "meta": {
            "fecha": "2026-10-26",
            "dia": "lunes",
            "titulo": "Que se viene esta semana: como leer los datos y las tendencias de los activos",
            "horario": "10:15 a 11:00",
            "guion": [
                {"bloque": "agenda", "desde": "10:15", "hasta": "10:25", "que": "Agenda macro"},
                {"bloque": "datos", "desde": "10:25", "hasta": "10:35", "que": "Curva y drivers"},
                {"bloque": "cierre", "desde": "10:35", "hasta": "10:45", "que": "Cierre y CTA"},
                {"bloque": "mt5", "desde": "10:45", "hasta": "11:00", "que": "Lectura MT5"},
            ],
        },
        "agenda": {
            "estado": "ok",
            "eventos": [
                {
                    "hora": "10:00",
                    "pais": "USD",
                    "nombre": "Confianza del Consumidor de The Conference Board",
                    "impacto": "alto",
                    "anterior": "98,7",
                    "consenso": "99,0",
                    "actual": "99,5",
                    "fuente": "Investing.com",
                }
            ],
        },
        "datos": [
            {"etiqueta": "Bono del Tesoro a 2 años (DGS2)", "valor": "4,15", "unidad": "%", "fecha": "2026-10-23"},
            {"etiqueta": "Bono del Tesoro a 10 años (DGS10)", "valor": "4,24", "unidad": "%", "fecha": "2026-10-23"},
            {"etiqueta": "Tasa real TIPS a 10 años (DFII10)", "valor": "1,85", "unidad": "%", "fecha": "2026-10-23"},
            {"etiqueta": "Tasa de la Fed / Fondos Federales (DFF)", "valor": "4,83", "unidad": "%", "fecha": "2026-10-23"},
            {"etiqueta": "Pendiente de la curva 2s10s", "valor": "0,09", "unidad": "%", "cambio_5d": "+9 pb", "fecha": "2026-10-23"},
            {"etiqueta": "Dollar Index (DXY)", "valor": "103,50", "unidad": "pts", "fecha": "2026-10-23"},
            {"etiqueta": "Cobre HG (Comex)", "valor": "4,35", "unidad": "USD/lb", "fecha": "2026-10-23"},
            {"etiqueta": "Petroleo WTI (Nymex)", "valor": "71,20", "unidad": "USD/bbl", "fecha": "2026-10-23"},
        ],
        "activos": {
            "USDCLP": {"direccion": "alcista", "estado": "abierto", "vigilar": "945,50"},
            "XAUUSD": {"direccion": "bajista", "estado": "abierto", "vigilar": "2.720,50"},
            "WTI.spot": {"direccion": "lateral", "estado": "abierto", "vigilar": "71,35"},
            "US100.spot": {"direccion": "alcista", "estado": "abierto", "vigilar": "20.350,25"},
        },
    }


# ───────────────────────────────────────────────────────────── 8. Validar Editorial
def test_validar_editorial_exitoso(editorial_valido):
    """El payload editorial completo y sin infracciones devuelve 0 errores."""
    errores = validar_editorial(editorial_valido)
    assert errores == []


def test_validar_editorial_detecta_faltantes_obligatorios():
    """Detecta la ausencia de campos obligatorios en noticia y teoría."""
    # Falta sección noticia entera
    assert any("noticia" in e for e in validar_editorial({}))

    # Noticia con campos vacíos o faltantes
    ed_incompleto = {
        "noticia": {
            "titular": "",
            "medio": "FXStreet",
            # falta bajada, url, fecha, motivo_imagen
        },
        "teoria": {
            "tema": "Tema",
            # falta idea_central, puntos, ejemplo, preguntas_chat
        },
    }
    errores = validar_editorial(ed_incompleto)
    assert any("noticia: falta el campo obligatorio 'titular'" in e for e in errores)
    assert any("noticia: falta el campo obligatorio 'bajada'" in e for e in errores)
    assert any("noticia: falta el campo obligatorio 'url'" in e for e in errores)
    assert any("noticia: falta el campo obligatorio 'fecha'" in e for e in errores)
    assert any("noticia: falta 'activo' o 'motivo_imagen'" in e for e in errores)
    assert any("teoria: falta el campo obligatorio 'idea_central'" in e for e in errores)
    assert any("teoria.puntos" in e for e in errores)
    assert any("teoria: falta el campo obligatorio 'ejemplo'" in e for e in errores)
    assert any("teoria.preguntas_chat" in e for e in errores)


def test_validar_editorial_detecta_fechas_invalidas(editorial_valido):
    """Detecta fechas que no cumplan el formato estricto AAAA-MM-DD."""
    fechas_malas = ["23/10/2026", "2026-10-32", "ayer", "20261023", "2026-1-1"]
    for fm in fechas_malas:
        editorial_valido["noticia"]["fecha"] = fm
        errores = validar_editorial(editorial_valido)
        assert any("noticia.fecha: formato inválido" in e for e in errores), f"Debió fallar con fecha: {fm}"

    # En bancos
    editorial_valido["noticia"]["fecha"] = "2026-10-23"
    editorial_valido["bancos"][0]["fecha"] = "invalida"
    errores_bancos = validar_editorial(editorial_valido)
    assert any("bancos[0].fecha: formato inválido" in e for e in errores_bancos)


def test_validar_editorial_detecta_urls_invalidas(editorial_valido):
    """Detecta URLs que no comiencen con http:// o https://."""
    urls_malas = ["ftp://example.com", "www.fxstreet.com", "fxstreet.com/noticia", "mailto:test@example.com"]
    for um in urls_malas:
        editorial_valido["noticia"]["url"] = um
        errores = validar_editorial(editorial_valido)
        assert any("noticia.url: la URL debe comenzar con http:// o https://" in e for e in errores), f"Debió fallar con URL: {um}"

    editorial_valido["noticia"]["url"] = "https://www.fxstreet.com"
    editorial_valido["bancos"][0]["url"] = "ftp://invalido.com"
    errores_bancos = validar_editorial(editorial_valido)
    assert any("bancos[0].url: la URL debe comenzar con http:// o https://" in e for e in errores_bancos)


def test_validar_editorial_detecta_motivo_inexistente(editorial_valido):
    """Detecta motivos de imagen no catalogados en config/motivos_imagen.json."""
    editorial_valido["noticia"]["motivo_imagen"] = "motivo_inexistente_xyz"
    errores = validar_editorial(editorial_valido)
    assert any("noticia.motivo_imagen: motivo 'motivo_inexistente_xyz' no existe" in e for e in errores)

    editorial_valido["noticia"]["motivo_imagen"] = "oro_lingotes"
    editorial_valido["bancos"][0]["motivo_imagen"] = "banco_fantasma"
    errores_bancos = validar_editorial(editorial_valido)
    assert any("bancos[0].motivo_imagen: motivo 'banco_fantasma' no existe" in e for e in errores_bancos)


def test_validar_editorial_detecta_guiones_largos(editorial_valido):
    """Regla de estilo: CERO guiones largos (U+2014 '—' o U+2013 '–') en ningún campo de texto."""
    # Guion largo em-dash U+2014 en titular
    editorial_valido["noticia"]["titular"] = "Oro en baja \u2014 petroleo reaviva temor inflacionario"
    errores = validar_editorial(editorial_valido)
    assert any("guion largo prohibido" in e and "noticia.titular" in e for e in errores)

    # Guion corto en-dash U+2013 en bajada
    editorial_valido["noticia"]["titular"] = "Oro en baja: petroleo reaviva temor inflacionario"
    editorial_valido["noticia"]["bajada"] = "Sesion de alta volatilidad \u2013 Fed define tasas."
    errores2 = validar_editorial(editorial_valido)
    assert any("guion largo prohibido" in e and "noticia.bajada" in e for e in errores2)

    # En puntos de teoria
    editorial_valido["noticia"]["bajada"] = "Sesion de alta volatilidad. Fed define tasas."
    editorial_valido["teoria"]["puntos"][0] = "Punto 1 con guion \u2014 prohibido"
    errores3 = validar_editorial(editorial_valido)
    assert any("guion largo prohibido" in e and "teoria.puntos[0]" in e for e in errores3)


def test_validar_editorial_rangos_puntos_y_preguntas(editorial_valido):
    """Puntos deben ser de 3 a 5 y preguntas_chat de 2 a 3."""
    # Puntos < 3
    editorial_valido["teoria"]["puntos"] = ["Punto 1", "Punto 2"]
    errores = validar_editorial(editorial_valido)
    assert any("teoria.puntos: debe ser una lista de 3 a 5" in e for e in errores)

    # Puntos > 5
    editorial_valido["teoria"]["puntos"] = [f"Punto {i}" for i in range(1, 7)]
    errores2 = validar_editorial(editorial_valido)
    assert any("teoria.puntos: debe ser una lista de 3 a 5" in e for e in errores2)

    # Preguntas < 2
    editorial_valido["teoria"]["puntos"] = ["Punto 1", "Punto 2", "Punto 3"]
    editorial_valido["teoria"]["preguntas_chat"] = ["Solo una pregunta?"]
    errores3 = validar_editorial(editorial_valido)
    assert any("teoria.preguntas_chat: debe ser una lista de 2 a 3" in e for e in errores3)

    # Preguntas > 3
    editorial_valido["teoria"]["preguntas_chat"] = ["P1?", "P2?", "P3?", "P4?"]
    errores4 = validar_editorial(editorial_valido)
    assert any("teoria.preguntas_chat: debe ser una lista de 2 a 3" in e for e in errores4)

    # Bancos > 4
    editorial_valido["teoria"]["preguntas_chat"] = ["P1?", "P2?"]
    editorial_valido["bancos"] = [
        {"banco": f"B{i}", "fecha": "2026-10-23", "url": "https://b.com", "resumen": "R", "motivo_imagen": "banco_central"}
        for i in range(5)
    ]
    errores5 = validar_editorial(editorial_valido)
    assert any("bancos: debe contener entre 0 y 4 elementos" in e for e in errores5)


# ───────────────────────────────────────────────────────────── 9. Rendir
def test_rendir_aborta_con_systemexit_si_editorial_incompleto(tmp_path, datos_completos):
    """Si editorial.json tiene campos faltantes o infracciones, rendir lanza SystemExit nombrando faltantes."""
    fecha_test = date(2026, 10, 26)
    dir_fecha = tmp_path / "data" / "webinar" / str(fecha_test)
    dir_fecha.mkdir(parents=True, exist_ok=True)

    # Escribir datos.json válido
    (dir_fecha / "datos.json").write_text(json.dumps(datos_completos), encoding="utf-8")

    # Escribir editorial.json incompleto (falta bajada y url)
    editorial_roto = {
        "noticia": {
            "titular": "Titular",
            "fecha": "2026-10-23",
            "medio": "FXStreet",
            "motivo_imagen": "oro_lingotes",
        },
        "teoria": {
            "tema": "Tema",
            "idea_central": "Idea",
            "puntos": ["P1", "P2", "P3"],
            "ejemplo": "Ejemplo",
            "preguntas_chat": ["Q1", "Q2"],
        },
    }
    (dir_fecha / "editorial.json").write_text(json.dumps(editorial_roto), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        rendir(fecha=fecha_test, dir_base=tmp_path)

    mensaje = str(exc_info.value)
    assert "noticia: falta el campo obligatorio 'bajada'" in mensaje
    assert "noticia: falta el campo obligatorio 'url'" in mensaje


def test_rendir_falla_si_falta_datos_json(tmp_path, editorial_valido):
    """Si falta datos.json, lanza FileNotFoundError."""
    fecha_test = date(2026, 10, 26)
    dir_fecha = tmp_path / "data" / "webinar" / str(fecha_test)
    dir_fecha.mkdir(parents=True, exist_ok=True)

    (dir_fecha / "editorial.json").write_text(json.dumps(editorial_valido), encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        rendir(fecha=fecha_test, dir_base=tmp_path)


def test_rendir_exitoso_autonomo_sin_referencias_externas(tmp_path, editorial_valido, datos_completos):
    """Genera lienzo.html autónomo con todos los bloques y cero referencias externas en script/link/img."""
    fecha_test = date(2026, 10, 26)
    dir_fecha = tmp_path / "data" / "webinar" / str(fecha_test)
    dir_fecha.mkdir(parents=True, exist_ok=True)

    (dir_fecha / "datos.json").write_text(json.dumps(datos_completos), encoding="utf-8")
    (dir_fecha / "editorial.json").write_text(json.dumps(editorial_valido), encoding="utf-8")

    # Copiar o asegurar plantillas y configs necesarios en tmp_path si aplica
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    cfg_src = RAIZ / "config" / "webinar.json"
    if cfg_src.exists():
        (tmp_path / "config" / "webinar.json").write_text(cfg_src.read_text(encoding="utf-8"), encoding="utf-8")
    motivos_src = RAIZ / "config" / "motivos_imagen.json"
    if motivos_src.exists():
        (tmp_path / "config" / "motivos_imagen.json").write_text(motivos_src.read_text(encoding="utf-8"), encoding="utf-8")

    # Directorio de plantillas
    plantilla_dir = tmp_path / "templates" / "webinar"
    plantilla_dir.mkdir(parents=True, exist_ok=True)
    plantilla_src = RAIZ / "templates" / "webinar" / "lienzo.html"
    plantilla_dir.joinpath("lienzo.html").write_text(plantilla_src.read_text(encoding="utf-8"), encoding="utf-8")

    # Ejecutar render autónomo
    salida_html = rendir(fecha=fecha_test, exportar_pdf=False, dir_base=tmp_path)
    assert salida_html.exists()
    assert salida_html.name == "lienzo.html"

    contenido_html = salida_html.read_text(encoding="utf-8")
    assert len(contenido_html) > 1000

    # 1. Verificar presencia de los 10 bloques requeridos
    bloques_esperados = [
        "bloque-portada",
        "bloque-aviso_legal",
        "bloque-agenda",
        "bloque-noticia",
        "bloque-bancos",
        "bloque-datos",
        "bloque-teoria",
        "bloque-mt5",
        "bloque-preguntas",
        "bloque-cierre",
    ]
    for b_id in bloques_esperados:
        assert f'id="{b_id}"' in contenido_html, f"Falta el bloque requerido: {b_id}"

    # 2. CERO guiones largos en el HTML generado
    assert "\u2014" not in contenido_html, "Infracción: em-dash encontrado en el HTML generado"
    assert "\u2013" not in contenido_html, "Infracción: en-dash encontrado en el HTML generado"

    # 3. Cero referencias http/https externas en src/href de script, link e img
    patron_externo = re.compile(r'<(script|link|img)[^>]*(src|href)\s*=\s*["\']https?://', re.IGNORECASE)
    coincidencias = patron_externo.findall(contenido_html)
    assert not coincidencias, f"Se encontraron referencias externas prohibidas en tags multimedia: {coincidencias}"


def test_rendir_sin_terminal_ni_datos_lo_dice(tmp_path, editorial_valido):
    """Con todo caído el lienzo sale igual, dice lo que falta y no rellena nada.

    Corre en tmp_path: antes escribía en data/webinar/ del repo y pisaba el datos.json real.
    """
    fecha_ref = date(2026, 10, 26)
    dir_fecha = tmp_path / "data" / "webinar" / str(fecha_ref)
    preparar(
        fecha=fecha_ref,
        lector_calendario=lambda **_kw: {"eventos": []},
        lector_curva=lambda *a: {"series": {}, "spread_2s10s": {}},
        lector_lectura=lambda *a: {"estado": "sin_terminal"},
        lector_drivers=lambda *a: [],
        dir_salida=dir_fecha,
    )
    (dir_fecha / "editorial.json").write_text(json.dumps(editorial_valido), encoding="utf-8")
    for rel in ("config/webinar.json", "config/motivos_imagen.json", "templates/webinar/lienzo.html"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text((RAIZ / rel).read_text(encoding="utf-8"), encoding="utf-8")

    html = rendir(fecha=fecha_ref, exportar_pdf=False, dir_base=tmp_path).read_text(encoding="utf-8")
    assert "sin terminal" in html
    assert "no trae eventos" in html
    assert "—" not in html and "–" not in html


def test_rendir_no_tiene_cifras_de_respaldo():
    """Regla 1: el render no lleva precios escritos a mano como respaldo de un dato ausente."""
    fuente = (RAIZ / "scripts" / "webinar" / "rendir.py").read_text(encoding="utf-8")
    assert not re.search(r"\d+[.,]\d+\s*(pts|USD|%|bps)", fuente), "rendir.py tiene una cifra escrita a mano"


def test_rendir_no_gasta_el_enfriamiento_del_correo(tmp_path):
    """Elegir imagen para el lienzo no escribe uso.json, que es el enfriamiento del correo."""
    from webinar.rendir import resolver_imagen_motivo

    motivo = tmp_path / "data" / "imagenes_ilustrativas" / "oro_lingotes"
    motivo.mkdir(parents=True)
    (motivo / "a.png").write_bytes(bytes([137, 80, 78, 71]))
    assert resolver_imagen_motivo("oro_lingotes", date(2026, 10, 26), tmp_path).startswith("data:image/png")
    assert not (motivo.parent / "uso.json").exists()
    assert resolver_imagen_motivo("banco_central", date(2026, 10, 26), tmp_path) is None


def test_guion_de_cada_dia_recorre_los_bloques_con_contenido():
    """Cada día pasa por portada, aviso legal, teoría, MT5 y cierre: lo que el director pidió tener listo."""
    cfg = json.loads((RAIZ / "config" / "webinar.json").read_text(encoding="utf-8"))
    for dia, d in cfg["dias"].items():
        ids = [p["bloque"] for p in d["guion"]]
        for requerido in ("portada", "aviso_legal", "teoria", "mt5", "cierre"):
            assert requerido in ids, f"{dia}: el guion no pasa por {requerido}"


def test_rendir_exportar_pdf(tmp_path, editorial_valido, datos_completos):
    """Verifica que con exportar_pdf=True se genere lienzo.pdf usando Playwright."""
    fecha_test = date(2026, 10, 26)
    dir_fecha = tmp_path / "data" / "webinar" / str(fecha_test)
    dir_fecha.mkdir(parents=True, exist_ok=True)

    (dir_fecha / "datos.json").write_text(json.dumps(datos_completos), encoding="utf-8")
    (dir_fecha / "editorial.json").write_text(json.dumps(editorial_valido), encoding="utf-8")

    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    cfg_src = RAIZ / "config" / "webinar.json"
    if cfg_src.exists():
        (tmp_path / "config" / "webinar.json").write_text(cfg_src.read_text(encoding="utf-8"), encoding="utf-8")
    motivos_src = RAIZ / "config" / "motivos_imagen.json"
    if motivos_src.exists():
        (tmp_path / "config" / "motivos_imagen.json").write_text(motivos_src.read_text(encoding="utf-8"), encoding="utf-8")

    plantilla_dir = tmp_path / "templates" / "webinar"
    plantilla_dir.mkdir(parents=True, exist_ok=True)
    plantilla_src = RAIZ / "templates" / "webinar" / "lienzo.html"
    plantilla_dir.joinpath("lienzo.html").write_text(plantilla_src.read_text(encoding="utf-8"), encoding="utf-8")

    salida_html = rendir(fecha=fecha_test, exportar_pdf=True, dir_base=tmp_path)
    salida_pdf = salida_html.with_suffix(".pdf")

    assert salida_html.exists()
    assert salida_pdf.exists()
    assert salida_pdf.stat().st_size > 1000
