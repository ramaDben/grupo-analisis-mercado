"""Tests del pipeline de carruseles de LinkedIn (scripts/pipeline_linkedin.py).

Ninguno toca el terminal ni la red: el payload se arma con `armar_payload` sobre
datos de fixture, igual que lo haría `--preparar` con lo que devuelve MT5.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "src"))

import pipeline_linkedin as pl  # noqa: E402

AHORA = datetime(2026, 9, 28, 12, 0, tzinfo=pl.SANTIAGO)

from estrategia.contrato import Escenario, Lectura, Linea, Referencia  # noqa: E402


def _lectura(ticker, precio, vigilar, invalidacion, objetivo, direccion="ALCISTA", estado="TENDENCIA"):
    """Una `Lectura` real de la estrategia, como la que devuelve `rs.lectura_actual`."""
    lin = Linea("seguridad", "diagonal", ((100, vigilar - 1), (200, vigilar)), "H4", 3, "A+", vigilar)
    ref = Referencia(vigilar, f"línea {direccion.lower()} de control", lin)
    inv = Referencia(invalidacion, "invalida la lectura") if invalidacion is not None else None
    obj = Referencia(objetivo, "objetivo") if objetivo is not None else None
    esc = tuple(Escenario(f, "c", "t") for f in ("⬆️", "↔️", "⬇️"))
    return Lectura(
        ticker=ticker, marco="H4", precio=precio, direccion=direccion, estado=estado,
        lineas=(lin,), en_prueba=None, vigilar=ref, invalidacion=inv, objetivo=obj,
        escenarios=esc, salida="s", conceptos=(), avisos=(), metricas={}, vela=200)


# Soporte 960,90 (invalida) y resistencia 974,50 (vigilar); objetivo 977,30.
USDCLP = pl.fila_de_lectura("USD/CLP", 2, _lectura("USDCLP", 971.03, 974.5, 960.9, 977.3))
# Soporte 14089 (vigilar) y resistencia 14508 (objetivo).
COBRE = pl.fila_de_lectura("Cobre", 0, _lectura("COPPER", 14395, 14089, 13903, 14508))

REGISTRO = {
    "reciente": {"id": "reciente", "quien": "Ana", "institucion": "Banco X", "tipo": "textual",
                 "cita": "El dólar debería volver a $940.", "fecha": "2026-09-20",
                 "fuente": "Medio", "url": "https://ejemplo.cl/nota"},
    "vieja": {"id": "vieja", "quien": "Luis", "institucion": "Banco Y", "tipo": "parafrasis",
              "cita": "Oro en US$6.000.", "fecha": "2026-06-09", "fuente": "Medio",
              "url": "https://ejemplo.com/oro"},
}


def _payload(formato: str = "cita") -> dict:
    return pl.armar_payload(formato, {"USDCLP": dict(USDCLP), "COPPER": dict(COBRE)},
                            {}, [], [], AHORA, "USDCLP")


def _completo() -> dict:
    p = _payload()
    ed = p["editorial"]
    ed["paginas"] = {
        "portada": {"titular": "El dólar llegó a $971,03.", "bajada": "Esto es lo que cambió."},
        "cita_1": {"vision": "reciente", "remate": "Hoy está en $971,03."},
        "cita_2": {"vision": "reciente", "remate": "La resistencia está en $974,50."},
        "nuestros_datos": {"titular": "Lo que dice el gráfico", "texto": "Tendencia alcista."},
        "lectura": {"titular": "Nuestra lectura", "texto": "Manda la Fed."},
    }
    ed["copy"] = "El dólar tocó su techo."
    ed["hashtags"] = "#DólarChile #GrupoInteligencia"
    return p


# ------------------------------------------------------------ formato


def test_formatear_respeta_digits_y_notacion_chilena():
    assert pl.formatear(4113.13, 2) == "4.113,13"
    assert pl.formatear(98.436, 3) == "98,436"
    assert pl.formatear(889.6, 2) == "889,60"


def test_formatear_cobre_sin_separador_de_miles():
    assert pl.formatear(14395, 0) == "14395"


# ------------------------------------------------------------ preparar


def test_esqueleto_marca_todo_campo_de_cada_formato():
    for formato, spec in pl.FORMATOS.items():
        ed = pl.esqueleto_editorial(formato)
        assert set(ed["paginas"]) == set(spec["paginas"])
        for pagina, campos in spec["paginas"].items():
            assert all(ed["paginas"][pagina][c] == pl.MARCA_EDITORIAL for c in campos)


def test_formato_desconocido_se_detiene():
    with pytest.raises(SystemExit):
        pl.armar_payload("inventado", {"USDCLP": USDCLP}, {}, [], [], AHORA, None)


def test_agenda_crea_un_remate_por_dia_con_eventos():
    agenda = [
        {"fecha": "2026-09-30", "hora": "09:30", "pais": "United States", "evento": "PCE",
         "nombre_es": "Gasto en consumo personal", "consenso": "3.4%", "anterior": "3.3%"},
        {"fecha": "2026-10-02", "hora": "09:30", "pais": "United States", "evento": "NFP",
         "nombre_es": "Nóminas no agrícolas", "consenso": "98K", "anterior": "162K"},
    ]
    p = pl.armar_payload("agenda", {"USDCLP": USDCLP}, {}, agenda, [], AHORA, None)
    assert set(p["editorial"]["remates_dia"]) == {"2026-09-30", "2026-10-02"}
    assert p["activo_principal"] is None


# ------------------------------------------------------------ validar


def test_payload_recien_preparado_no_puede_salir():
    errores = pl.validar(_payload(), REGISTRO, AHORA)
    assert any("sin escribir" in e for e in errores)
    assert any("vision: sin elegir" in e for e in errores)


def test_payload_completo_sale():
    assert pl.validar(_completo(), REGISTRO, AHORA) == []


@pytest.mark.parametrize("guion", ["—", "–"])
def test_guion_largo_o_medio_se_detiene(guion):
    p = _completo()
    p["editorial"]["copy"] = f"El dólar subió {guion} y mucho."
    assert any("guion" in e for e in pl.validar(p, REGISTRO, AHORA))


def test_voseo_se_detiene():
    p = _completo()
    p["editorial"]["copy"] = "Si tenés dudas, escribinos."
    assert any("voseo" in e for e in pl.validar(p, REGISTRO, AHORA))


def test_cifra_que_no_sale_del_terminal_se_detiene():
    p = _completo()
    p["editorial"]["paginas"]["lectura"]["texto"] = "El objetivo es $990,00."
    errores = pl.validar(p, REGISTRO, AHORA)
    assert any("$990,00" in e for e in errores)


def test_cifra_de_una_cita_usada_se_acepta():
    p = _completo()
    p["editorial"]["paginas"]["lectura"]["texto"] = "Hace dos semanas se hablaba de $940."
    assert pl.validar(p, REGISTRO, AHORA) == []


def test_cifra_redondeada_se_acepta_solo_declarada():
    p = _completo()
    p["editorial"]["paginas"]["portada"]["titular"] = "El dólar llegó a $971."
    assert any("$971" in e for e in pl.validar(p, REGISTRO, AHORA))
    p["editorial"]["cifras_citadas"] = {"$971": "redondeo de 971,03 para el titular"}
    assert pl.validar(p, REGISTRO, AHORA) == []


def test_cobre_se_cita_entero():
    p = _completo()
    p["editorial"]["paginas"]["lectura"]["texto"] = "El cobre está en $14395 USD/t."
    assert pl.validar(p, REGISTRO, AHORA) == []


def test_vision_inexistente_se_detiene():
    p = _completo()
    p["editorial"]["paginas"]["cita_1"]["vision"] = "no-existe"
    assert any("no está" in e for e in pl.validar(p, REGISTRO, AHORA))


def test_vision_vieja_se_detiene_salvo_aceptada_con_motivo():
    p = _completo()
    p["editorial"]["paginas"]["cita_2"]["vision"] = "vieja"
    assert any("días" in e for e in pl.validar(p, REGISTRO, AHORA))
    p["editorial"]["aceptar_antiguas"] = {"vieja": "es la última revisión publicada"}
    assert pl.validar(p, REGISTRO, AHORA) == []


def test_vision_sin_url_o_fecha_futura_se_detiene():
    hoy = AHORA.date()
    sin_url = dict(REGISTRO["reciente"], url="")
    futura = dict(REGISTRO["reciente"], fecha="2026-12-01")
    assert pl.validar_vision(sin_url, hoy, None)
    assert any("futura" in e for e in pl.validar_vision(futura, hoy, None))


def test_datos_viejos_se_detienen_salvo_aceptados():
    p = _completo()
    tarde = AHORA + timedelta(hours=pl.FRESCURA_MAX_HORAS + 1)
    assert any("se leyeron hace" in e for e in pl.validar(p, REGISTRO, tarde))
    assert pl.validar(p, REGISTRO, tarde, aceptar_datos_viejos=True) == []


@pytest.mark.parametrize("texto", [
    "El dólar está en 968,42 pesos.",      # una cifra de otra lectura, sin $
    "Cotiza cerca de USD 969.",            # otra moneda escrita
    "El precio llegó a US$ 971,0.",        # con espacio y un decimal
])
def test_cifra_sin_signo_parecida_a_un_precio_se_detiene(texto):
    p = _completo()
    p["editorial"]["paginas"]["lectura"]["texto"] = texto
    assert pl.validar(p, REGISTRO, AHORA), texto


@pytest.mark.parametrize("texto", [
    "Mira los 50 días y los 0,24 puntos de la tasa.",
    "La Fed está en 3,75%-4,00% y la TPM en 4,50%.",
    "Resistencia en 974,50 y soporte en 960,90.",
    "Pasó en 2026 y el cobre cotiza 14395 USD/t.",
])
def test_cifras_legitimas_sin_signo_no_frenan(texto):
    p = _completo()
    p["editorial"]["paginas"]["lectura"]["texto"] = texto
    assert pl.validar(p, REGISTRO, AHORA) == []


def test_nivel_de_indice_distinto_al_medido_se_detiene():
    p = _completo()
    p["datos"]["activos"]["US100.spot"] = pl.fila_de_lectura(
        "Nasdaq 100", 2, _lectura("US100.spot", 30165.57, 30379.37, 29604.49, 30724.16))
    p["editorial"]["paginas"]["lectura"]["texto"] = "El Nasdaq vigila 30.400,00."
    assert any("30.400,00" in e for e in pl.validar(p, REGISTRO, AHORA))
    p["editorial"]["paginas"]["lectura"]["texto"] = "El Nasdaq vigila 30.379,37."
    assert pl.validar(p, REGISTRO, AHORA) == []


def test_leido_en_sin_zona_se_lee_en_santiago():
    p = _completo()
    p["datos"]["leido_en"] = "2026-09-28T12:00"
    assert pl.validar(p, REGISTRO, AHORA) == []


def test_vision_con_fecha_de_manana_se_acepta_por_husos():
    manana = dict(REGISTRO["reciente"], fecha="2026-09-29")
    assert pl.validar_vision(manana, AHORA.date(), None) == []


def test_brief_no_se_rompe_con_niveles_ausentes():
    p = _completo()
    p["datos"]["activos"]["USDCLP"]["soporte"] = None
    p["datos"]["activos"]["USDCLP"]["objetivo"] = None
    brief = pl.construir_brief(p, REGISTRO)
    assert "Mapa no disponible" in brief and "sin dato" in brief


def test_curva_usa_la_cotizacion_de_hoy_y_no_la_de_otro_dia(monkeypatch):
    import market_data_mcp.curva_reader as cr

    monkeypatch.setattr(cr, "cargar_curva_tasas", lambda serie="ALL": {"series": {
        "DGS10": {"nivel_pct": 5.18, "delta_5d_bps": 24, "fecha_dato": "2026-09-24"},
        "DGS2": {"nivel_pct": 4.87, "delta_5d_bps": 20, "fecha_dato": "2026-09-24"},
    }})
    vivo = {
        "DGS10": {"valor": 5.27, "fecha": "2026-09-28", "momento": AHORA, "fuente": "CNBC"},
        "DGS2": {"valor": 4.95, "fecha": "2026-09-25", "momento": AHORA - timedelta(days=3), "fuente": "CNBC"},
    }
    curva, _ = pl.leer_curva(AHORA, vivo=vivo)
    assert curva["DGS10"]["nivel_pct"] == 5.27 and curva["DGS10"]["fuente"] == "CNBC"
    assert curva["DGS2"]["nivel_pct"] == 4.87, "una cotización de otro día no reemplaza al archivo"


# ------------------------------------------------------------ lectura de la estrategia


def test_fila_sale_de_la_lectura_de_la_estrategia():
    assert USDCLP["price"] == 971.03
    assert USDCLP["vigilar"] == 974.5 and USDCLP["invalidacion"] == 960.9
    assert USDCLP["objetivo"] == 977.3
    assert (USDCLP["soporte"], USDCLP["resistencia"]) == (960.9, 974.5)
    assert USDCLP["direccion"] == "ALCISTA" and USDCLP["estado"] == "TENDENCIA"
    assert USDCLP["lectura"]["vigilar"]["precio"] == 974.5
    # Nada de la lectura vieja de `analizar_activo`: ni s1/r1, ni media, ni RSI.
    for viejo in ("s1", "r1", "s2", "r2", "ema_50", "donchian_50_high", "rsi_14", "change_pct"):
        assert viejo not in USDCLP


def test_fila_sin_invalidacion_ni_objetivo_los_deja_vacios():
    fila = pl.fila_de_lectura("Oro", 2, _lectura("XAUUSD", 4000.0, 3990.0, None, None, "LATERAL", "RANGO"))
    assert fila["invalidacion"] is None and fila["objetivo"] is None
    assert fila["direccion"] == "LATERAL"


def test_campos_precio_son_los_de_la_lectura():
    assert pl.CAMPOS_PRECIO == ("price", "vigilar", "invalidacion", "objetivo", "soporte", "resistencia")


def _parchar_lectura(monkeypatch, catalogo, falsa):
    import referencia_semanal as rs
    from estrategia import registro
    from market_data_mcp import mt5_client

    monkeypatch.setattr(pl, "_catalogo", lambda: catalogo)
    monkeypatch.setattr(mt5_client, "connect", lambda *a, **k: None)
    monkeypatch.setattr(registro, "activa", lambda: "tori")
    monkeypatch.setattr(rs, "lectura_actual", falsa)


def test_leer_activos_lee_con_la_estrategia_activa(monkeypatch):
    llamadas = []

    def falsa(estrategia, ticker, digits, lector, ahora, base=None, referencia=None):
        llamadas.append((estrategia, ticker, digits))
        return _lectura(ticker, 971.03, 974.5, 960.9, 977.3), None

    _parchar_lectura(monkeypatch, {"USDCLP": {"nombre": "USD/CLP", "digits": 2}}, falsa)
    activos, avisos = pl.leer_activos(["USDCLP"])
    assert llamadas == [("tori", "USDCLP", 2)]
    assert activos["USDCLP"]["vigilar"] == 974.5 and avisos == []


def test_leer_activos_avisa_el_activo_sin_lectura(monkeypatch):
    def falsa(estrategia, ticker, digits, lector, ahora, base=None, referencia=None):
        if ticker == "COPPER":
            raise RuntimeError("sin velas")
        return _lectura(ticker, 971.03, 974.5, 960.9, 977.3), None

    _parchar_lectura(monkeypatch, {"USDCLP": {"nombre": "USD/CLP", "digits": 2},
                                   "COPPER": {"nombre": "Cobre", "digits": 0}}, falsa)
    activos, avisos = pl.leer_activos(["USDCLP", "COPPER"])
    assert set(activos) == {"USDCLP"}
    assert any("Cobre" in a for a in avisos)


def test_el_modulo_no_decide_con_la_media_ni_con_s1_r1():
    fuente = (RAIZ / "scripts" / "pipeline_linkedin.py").read_text(encoding="utf-8")
    assert "direccion_tecnica" not in fuente
    assert "analizar_activo" not in fuente


def test_mapa_de_niveles_usa_soporte_y_resistencia_de_la_lectura():
    mapa = " ".join(pl.mapa_niveles(USDCLP))
    assert "974,50" in mapa and "960,90" in mapa
    assert "—" not in mapa and "–" not in mapa


def test_agenda_nombra_el_nivel_a_vigilar_de_la_lectura():
    bajista = pl.fila_de_lectura("Oro", 2, _lectura("XAUUSD", 4000.0, 4012.5, 4030.0, 3950.0, "BAJISTA"))
    p = pl.armar_payload("agenda", {"XAUUSD": bajista}, {}, [], [], AHORA, None)
    p["editorial"]["paginas"]["contexto"]["vision"] = "reciente"
    brief = pl.construir_brief(p, REGISTRO)
    assert "| Oro | Bajista | 4.012,50 |" in brief


def test_ficha_trae_las_columnas_de_la_lectura():
    brief = pl.construir_brief(_completo(), REGISTRO)
    assert "A vigilar" in brief and "Invalida" in brief and "Objetivo" in brief
    assert "977,30" in brief and "Tendencia" in brief
    assert "RSI" not in brief and "Media 50" not in brief


# ------------------------------------------------------------ brief


def test_brief_trae_mapa_de_niveles_medido_y_fuentes():
    brief = pl.construir_brief(_completo(), REGISTRO)
    assert "974,50" in brief and "960,90" in brief
    assert "⬆️" in brief and "↔️" in brief and "⬇️" in brief
    assert "https://ejemplo.cl/nota" in brief
    assert "12:00" in brief


def test_brief_imprime_el_motivo_de_una_cita_vieja():
    p = _completo()
    p["editorial"]["paginas"]["cita_2"]["vision"] = "vieja"
    p["editorial"]["aceptar_antiguas"] = {"vieja": "última revisión publicada"}
    assert "última revisión publicada" in pl.construir_brief(p, REGISTRO)


def test_rendir_sin_pdf_escribe_brief_y_quita_la_marca(tmp_path, monkeypatch):
    p = _completo()
    p["datos"]["leido_en"] = datetime.now(pl.SANTIAGO).isoformat(timespec="minutes")
    (tmp_path / "payload.json").write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(pl, "cargar_visiones", lambda *a, **k: REGISTRO)
    salida = pl.rendir(tmp_path, sin_pdf=True)
    assert salida.name == "brief.md"
    assert "_pendiente_editorial" not in json.loads((tmp_path / "payload.json").read_text(encoding="utf-8"))


def test_rendir_se_detiene_con_huecos(tmp_path, monkeypatch):
    (tmp_path / "payload.json").write_text(json.dumps(_payload(), ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(pl, "cargar_visiones", lambda *a, **k: REGISTRO)
    with pytest.raises(SystemExit):
        pl.rendir(tmp_path, sin_pdf=True)
    assert not (tmp_path / "brief.md").exists()


def test_normalizar_separa_listas_pegadas_y_escapa_hashtags():
    markdown = pytest.importorskip("markdown")  # extra `informe`, ausente en CI

    texto = "**Pág. 1 · Portada**\n- Titular: Hola\n- Bajada: Chao\n\n> Copy\n> #Inversiones #GI"
    html = markdown.markdown(pl.normalizar_markdown(texto), extensions=["tables", "sane_lists"])
    assert "<li>Titular: Hola</li>" in html
    assert "<h1>" not in html

    texto = "- Titular: Tres claves\n1. **Primera:** algo\n2. **Segunda:** otra"
    html = markdown.markdown(pl.normalizar_markdown(texto), extensions=["tables", "sane_lists"])
    assert "<ol>" in html and html.count("<li>") == 3


# ------------------------------------------------------------ contratos


def test_registro_real_es_valido_y_sin_ids_repetidos():
    datos = json.loads(pl.REGISTRO_VISIONES.read_text(encoding="utf-8"))
    ids = [v["id"] for v in datos["visiones"]]
    assert len(ids) == len(set(ids))
    # El registro es real y crece cada día: se valida contra el día de hoy, no
    # contra `AHORA`, o toda visión cargada después de esa fecha saldría "futura".
    hoy = datetime.now(pl.SANTIAGO).date()
    for v in datos["visiones"]:
        assert v.get("tipo") in {"textual", "traduccion", "parafrasis"}
        errores = [e for e in pl.validar_vision(v, hoy, "test") if "días" not in e]
        assert errores == [], errores


def test_el_comando_documenta_todos_los_formatos():
    comando = (RAIZ / ".claude" / "commands" / "linkedin.md").read_text(encoding="utf-8")
    for formato in pl.FORMATOS:
        assert f"`{formato}`" in comando, f"el formato {formato} no está documentado en linkedin.md"


# ─────────────────────────────────────────────────────────────────────────────
# Frenos públicos (los comparte pipeline_avisos)
# ─────────────────────────────────────────────────────────────────────────────
ACTIVOS_FRENO = {"USDCLP": {"nombre": "Dólar", "digits": 2, "price": 936.32, "soporte": 930.0, "resistencia": 942.5}}


def test_validar_textos_marca_vacio_y_guion():
    err = pl.validar_textos([("a", "[[ESCRIBIR]]"), ("b", "  "), ("c", "El dólar sube — fuerte")])
    assert "a: sin escribir" in err
    assert "b: sin escribir" in err
    assert any(e.startswith("c: guion largo") for e in err)


def test_validar_textos_texto_sano_pasa():
    assert pl.validar_textos([("a", "El dólar mantiene su sesgo alcista sobre su promedio de 50 horas.")]) == []


def test_validar_cifras_con_moneda_sin_respaldo():
    err = pl.validar_cifras([("t", "El dólar va a $951,00 hoy.")], ACTIVOS_FRENO, [], {})
    assert any("$951,00" in e for e in err)


def test_validar_cifras_medidas_pasan():
    texto = "El soporte está en $930,00 y el precio en $936,32."
    assert pl.validar_cifras([("t", texto)], ACTIVOS_FRENO, [], {}) == []


def test_validar_cifras_parecida_no_medida():
    err = pl.validar_cifras([("t", "Cotiza cerca de 935,10.")], ACTIVOS_FRENO, [], {})
    assert any("935,10" in e for e in err)


def test_validar_cifras_acepta_campos_extra():
    activos = {"USDCLP": {**ACTIVOS_FRENO["USDCLP"], "soporte_publicado": 928.4}}
    campos = pl.CAMPOS_PRECIO + ("soporte_publicado",)
    assert pl.validar_cifras([("t", "Soporte en $928,40.")], activos, [], {}, campos=campos) == []


def test_validar_cifras_vision_y_citadas():
    vision = {"cita": "El dólar llegaría a $970."}
    assert pl.validar_cifras([("t", "El banco ve $970 al cierre.")], ACTIVOS_FRENO, [vision], {}) == []
    citadas = {"$955": "máximo de ayer"}
    assert pl.validar_cifras([("t", "Ayer tocó $955.")], ACTIVOS_FRENO, [], citadas) == []


def test_validar_frescura_en_el_borde():
    ahora = datetime(2026, 9, 29, 12, 0, tzinfo=pl.SANTIAGO)
    assert pl.validar_frescura(ahora - timedelta(minutes=119), ahora, 2) == []
    err = pl.validar_frescura(ahora - timedelta(minutes=121), ahora, 2, remedio="Corre --refrescar.")
    assert err and "se leyeron hace 121 min" in err[0] and "Corre --refrescar." in err[0]


def test_validar_frescura_acepta_hora_sin_zona():
    ahora = datetime(2026, 9, 29, 12, 0, tzinfo=pl.SANTIAGO)
    assert pl.validar_frescura(datetime(2026, 9, 29, 11, 30), ahora, 2) == []
