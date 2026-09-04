"""El reloj de sucesos: latido del sistema operativo, decision en Python.

**La trampa que esto evita.** Task Scheduler dispara en hora LOCAL. Una tarea a
las 08:30 de Chile es 08:30 de Nueva York hoy, y 06:30 de Nueva York en
noviembre: dos horas antes del dato que justifica la hora. La tarea seguiria
corriendo puntual y publicando el cierre de ayer.

Por eso el agendador es un latido que no sabe nada de mercados, y quien decide
es un decisor en Python que lee la agenda y convierte en el momento.

**Anclado al mercado, con el cambio narrado.** Decision del director el
2026-09-04: la hora sigue al mercado y la hora chilena drifta; cuando el desfase
cambia se avisa al canal. Anclar a hora chilena fija habria puesto la pieza de
indices en noviembre a las 08:00 de Nueva York, hora y media antes de la
campana.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for _p in (RAIZ / "scripts", RAIZ / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import agenda_mercado as ag  # noqa: E402
import reloj_gi as reloj  # noqa: E402

NY = ZoneInfo("America/New_York")
CL = ZoneInfo("America/Santiago")

# Las cuatro fechas del ano con desfase distinto, medidas.
DESFASE_0 = datetime(2026, 9, 4, tzinfo=NY)     # Chile y Nueva York coinciden
DESFASE_1 = datetime(2026, 9, 8, tzinfo=NY)     # Chile entro en horario de verano
DESFASE_2 = datetime(2026, 11, 2, tzinfo=NY)    # EE.UU. salio del suyo


# ─────────────────────────────────────────────────────────────────────────────
# El desfase se calcula, nunca se escribe
# ─────────────────────────────────────────────────────────────────────────────
def test_el_desfase_sale_del_calendario_y_cambia_cuatro_veces_al_ano():
    assert reloj.desfase_horas(DESFASE_0) == 0
    assert reloj.desfase_horas(DESFASE_1) == 1
    assert reloj.desfase_horas(DESFASE_2) == 2


def test_ningun_desfase_esta_escrito_en_el_codigo_del_reloj():
    """El error del issue #38: un offset a mano queda mal dos veces al ano."""
    fuente = (RAIZ / "scripts" / "reloj_gi.py").read_text(encoding="utf-8")
    for prohibido in ("UTC-3", "UTC-4", "UTC-5", "GMT-3", "timedelta(hours=1)"):
        assert prohibido not in fuente, f"hay un desfase fijo escrito: {prohibido}"


# ─────────────────────────────────────────────────────────────────────────────
# El latido: idempotencia por momento y por dia
# ─────────────────────────────────────────────────────────────────────────────
def test_el_momento_esta_pendiente_dentro_de_su_tolerancia():
    ahora = DESFASE_0.replace(hour=8, minute=35)
    m = reloj.momento_pendiente(ahora, libro={})
    assert m is not None and m["slug"] == "premercado_fx"


def test_pasada_la_tolerancia_el_momento_ya_no_dispara():
    """Un momento que salio una hora tarde publica niveles de otro mercado."""
    assert reloj.momento_pendiente(DESFASE_0.replace(hour=9, minute=55), libro={}) is None


def test_un_momento_ya_disparado_hoy_no_vuelve_a_disparar():
    """El latido pasa cuatro veces por la tolerancia; la pieza sale una sola vez."""
    libro = {"disparos": {"2026-09-04": ["premercado_fx"]}}
    assert reloj.momento_pendiente(DESFASE_0.replace(hour=8, minute=35), libro) is None


def test_el_mismo_momento_vuelve_a_estar_pendiente_al_dia_siguiente():
    libro = {"disparos": {"2026-09-04": ["premercado_fx"]}}
    manana = datetime(2026, 9, 7, 8, 35, tzinfo=NY)
    m = reloj.momento_pendiente(manana, libro)
    assert m is not None and m["slug"] == "premercado_fx"


def test_el_libro_se_anota_por_dia_y_momento(tmp_path):
    p = tmp_path / "disparos.json"
    reloj.anotar_disparo("premercado_fx", DESFASE_0, ruta=p)
    reloj.anotar_disparo("cripto", DESFASE_0, ruta=p)
    libro = reloj.cargar_libro(p)
    assert set(libro["disparos"]["2026-09-04"]) == {"premercado_fx", "cripto"}


def test_un_libro_corrupto_no_voltea_el_latido(tmp_path):
    p = tmp_path / "roto.json"
    p.write_text("{esto no es json", encoding="utf-8")
    assert reloj.cargar_libro(p) == {"disparos": {}}


def test_el_libro_no_crece_para_siempre(tmp_path):
    """Un archivo que solo crece termina siendo el problema."""
    p = tmp_path / "disparos.json"
    for dia in range(1, 40):
        reloj.anotar_disparo("cripto", datetime(2026, 7, dia % 28 + 1, tzinfo=NY), ruta=p)
    assert len(reloj.cargar_libro(p)["disparos"]) <= reloj.DIAS_DE_LIBRO


# ─────────────────────────────────────────────────────────────────────────────
# La hora del fin de semana no dispara nada
# ─────────────────────────────────────────────────────────────────────────────
def test_el_sabado_no_hay_momento_que_disparar():
    sabado = datetime(2026, 8, 29, 8, 35, tzinfo=NY)
    assert reloj.momento_pendiente(sabado, libro={}) is None


# ─────────────────────────────────────────────────────────────────────────────
# La narracion del cambio de desfase
# ─────────────────────────────────────────────────────────────────────────────
def test_el_cambio_de_desfase_levanta_aviso_con_la_hora_nueva():
    libro = {"disparos": {}, "desfase": 0}
    aviso = reloj.aviso_de_desfase(DESFASE_1, libro)
    assert aviso is not None
    assert aviso["desfase_anterior"] == 0 and aviso["desfase_nuevo"] == 1
    assert "09:30" in aviso["mensaje"], "tiene que decir la hora nueva de Chile"


def test_sin_cambio_de_desfase_no_hay_aviso():
    assert reloj.aviso_de_desfase(DESFASE_0, {"disparos": {}, "desfase": 0}) is None


def test_la_primera_corrida_no_narra_un_cambio_que_nadie_vio():
    """Sin desfase anterior no hubo cambio: solo se registra el actual."""
    assert reloj.aviso_de_desfase(DESFASE_1, {"disparos": {}}) is None


def test_el_mensaje_del_cambio_explica_que_el_ancla_es_el_mercado():
    aviso = reloj.aviso_de_desfase(DESFASE_1, {"disparos": {}, "desfase": 0})
    texto = aviso["mensaje"].lower()
    assert "nueva york" in texto
    assert "—" not in aviso["mensaje"] and "–" not in aviso["mensaje"]


def test_el_mensaje_del_cambio_no_trae_precios():
    """Regla 1: los precios salen del terminal, y esta pieza no los necesita."""
    aviso = reloj.aviso_de_desfase(DESFASE_2, {"disparos": {}, "desfase": 1})
    assert "$" not in aviso["mensaje"]


# ─────────────────────────────────────────────────────────────────────────────
# El reloj NO envia
# ─────────────────────────────────────────────────────────────────────────────
def test_el_reloj_no_puede_enviar_nada_a_whatsapp():
    """Nada sale al canal sin aprobacion explicita del director.

    El reloj prepara y avisa. Que un proceso automatico pueda publicar es
    justamente lo que el flujo de aprobacion prohibe.
    """
    fuente = (RAIZ / "scripts" / "reloj_gi.py").read_text(encoding="utf-8")
    for prohibido in ("enviar_whatsapp", "whatsapp_sender", "--despachar", "despachar("):
        assert prohibido not in fuente, f"el reloj toca el envio: {prohibido}"


def test_el_reloj_solo_prepara():
    assert "--preparar" in (RAIZ / "scripts" / "reloj_gi.py").read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# De momento a canales, por el mapeo real
# ─────────────────────────────────────────────────────────────────────────────
def test_el_momento_de_indices_cubre_indices_y_acciones():
    canales = reloj.canales_del_momento(ag.momento("apertura_indices"))
    assert set(canales) == {"04_indices_bursatiles", "05_acciones_etfs"}


def test_el_momento_de_cripto_cubre_solo_su_canal():
    assert reloj.canales_del_momento(ag.momento("cripto")) == ["06_criptoactivos"]


def test_todo_momento_llega_a_algun_canal():
    """Un momento sin canal no publicaria nada: seria un disparo al vacio."""
    for m in ag.momentos():
        assert reloj.canales_del_momento(m), f"{m['slug']} no mapea a ningun canal"


# ─────────────────────────────────────────────────────────────────────────────
# El invariante que permite que convivan dos anclas
# ─────────────────────────────────────────────────────────────────────────────
def test_ningun_par_de_momentos_se_pisa_en_ningun_desfase_del_ano():
    """Con `zona` por momento, dos anclas distintas pueden acercarse al drift.

    Si dos momentos caen dentro de la tolerancia uno del otro, el decisor
    dispararia solo uno y el otro se perderia en silencio. Se verifica en las
    tres configuraciones de desfase del ano.
    """
    tol = ag.tolerancia_minutos()
    for dia in (DESFASE_0, DESFASE_1, DESFASE_2):
        instantes = sorted(
            (reloj.instante_del_momento(m, dia), m["slug"]) for m in ag.momentos()
        )
        for (t1, s1), (t2, s2) in zip(instantes, instantes[1:]):
            gap = (t2 - t1).total_seconds() / 60
            assert gap > tol, (
                f"el {dia:%Y-%m-%d} (desfase {reloj.desfase_horas(dia)}) "
                f"{s1} y {s2} quedan a {gap:.0f} min, dentro de la tolerancia de {tol}"
            )


def test_el_momento_respeta_su_propia_zona():
    """Un momento anclado a Santiago se mide con el reloj chileno, no con el de NY."""
    ny = ag.momento("apertura_indices")
    assert reloj.zona_del_momento(ny).key == "America/New_York"
    # El mecanismo tiene que servir para una zona distinta del ancla.
    santiago = {"slug": "prueba", "hora": "08:00", "zona": "America/Santiago",
                "sesion": "apertura_ny", "clases": []}
    inst = reloj.instante_del_momento(santiago, DESFASE_2)
    assert inst.astimezone(CL).strftime("%H:%M") == "08:00"


# ─────────────────────────────────────────────────────────────────────────────
# El libro es estado generado, no historia editorial
# ─────────────────────────────────────────────────────────────────────────────
def test_el_libro_de_disparos_esta_gitignoreado():
    ignore = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert ".reloj_disparos.json" in ignore


def test_el_estado_del_reloj_se_puede_consultar_sin_efectos(tmp_path):
    """`--verificar` responde que haria, y no anota nada."""
    p = tmp_path / "disparos.json"
    est = reloj.estado(DESFASE_0.replace(hour=8, minute=35), ruta_libro=p)
    assert est["momento"] == "premercado_fx"
    assert est["desfase"] == 0
    assert not p.exists(), "verificar no puede escribir el libro"
    assert json.dumps(est)          # serializable, para el dashboard


# ─────────────────────────────────────────────────────────────────────────────
# El aviso lo lee el cliente, asi que se le aplican las reglas de cliente
# ─────────────────────────────────────────────────────────────────────────────
def test_el_aviso_lista_los_momentos_en_orden_de_reloj():
    """Cripto va a las 09:00 y en el config esta tercera: el orden es por hora."""
    aviso = reloj.aviso_de_desfase(DESFASE_1, {"disparos": {}, "desfase": 0})
    lineas = [l for l in aviso["mensaje"].splitlines() if l.startswith("•")]
    horas = [l.rsplit("*", 2)[-2] for l in lineas]
    assert horas == sorted(horas), f"el aviso lista las horas desordenadas: {horas}"


def test_el_aviso_nombra_al_pais_que_de_verdad_cambio_de_horario():
    """En septiembre cambia Chile; en noviembre cambia Estados Unidos.

    Decir "horario de verano de Chile" en noviembre seria falso: ese cambio es
    la salida de EE.UU. del suyo.
    """
    sept = reloj.aviso_de_desfase(DESFASE_1, {"disparos": {}, "desfase": 0})["mensaje"]
    assert "Chile" in sept and "Estados Unidos" not in sept

    nov = reloj.aviso_de_desfase(DESFASE_2, {"disparos": {}, "desfase": 1})["mensaje"]
    assert "Estados Unidos" in nov


def test_quien_cambio_se_deduce_del_calendario():
    assert reloj.quien_cambio(DESFASE_1) == "Chile"
    assert reloj.quien_cambio(DESFASE_2) == "Estados Unidos"
    assert reloj.quien_cambio(DESFASE_0) is None


def test_los_nombres_de_momento_van_acentuados_porque_los_lee_el_cliente():
    """El aviso publica el nombre del momento tal cual sale del config."""
    faltas = ("energia", "indices", "Criptoactivos ")
    for m in ag.momentos():
        for falta in faltas[:2]:
            assert falta not in m["nombre"], (
                f"{m['slug']} tiene {falta!r} sin acento y ese nombre sale al canal"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Un momento que fallo sigue pendiente
# ─────────────────────────────────────────────────────────────────────────────
def test_un_momento_que_fallo_no_queda_anotado_como_disparado(tmp_path):
    """Si se anota igual, el momento se pierde por el dia entero.

    MT5 puede no estar conectado en ese latido. Dejarlo pendiente hace que el
    siguiente latido reintente dentro de la tolerancia, que es justamente para
    lo que existe la ventana de gracia.
    """
    p = tmp_path / "disparos.json"
    ahora = DESFASE_0.replace(hour=8, minute=32)
    res = reloj.ejecutar(
        ahora, correr=lambda canal: {"canal": canal, "codigo": 1,
                                     "salida": "", "error": "MT5 no conectado"},
        ruta_libro=p,
    )
    assert res["momento"] == "premercado_fx"
    assert not reloj.ya_disparo("premercado_fx", ahora, reloj.cargar_libro(p))


def test_un_momento_que_salio_bien_si_queda_anotado(tmp_path):
    p = tmp_path / "disparos.json"
    ahora = DESFASE_0.replace(hour=8, minute=32)
    reloj.ejecutar(
        ahora, correr=lambda canal: {"canal": canal, "codigo": 0,
                                     "salida": "ok", "error": ""},
        ruta_libro=p,
    )
    assert reloj.ya_disparo("premercado_fx", ahora, reloj.cargar_libro(p))
