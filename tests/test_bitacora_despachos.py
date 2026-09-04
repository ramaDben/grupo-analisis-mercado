"""La bitacora de despachos: que salio, para no mandarlo dos veces.

El contador `data/.whatsapp_envios.json` dice cuantos mensajes salieron hoy y
nada mas. Con el despacho pieza por pieza (2026-09-03), un abort a mitad de canal
deja el estado indeterminado y `--desde N`, que cuenta canales, reenvia la primera
pieza del canal que fallo.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import bitacora_despachos as bd  # noqa: E402

TANDA = "2026-09-04_10-12_apertura_ny"
AHORA = datetime(2026, 9, 4, 10, 17)


@pytest.fixture
def libro(tmp_path) -> Path:
    return tmp_path / "historial_despachos.json"


def test_una_bitacora_ausente_se_lee_vacia_y_no_revienta(libro):
    """Primera corrida en un clon nuevo: no hay archivo y eso no es un error."""
    assert bd.cargar(libro) == []


def test_una_bitacora_corrupta_se_lee_vacia(libro):
    """Fallar aca detendria un despacho por un JSON roto. Se prefiere reenviar de
    menos que bloquear la tanda: el guardia de entrega sigue en pie."""
    libro.write_text("{ esto no es json", encoding="utf-8")
    assert bd.cargar(libro) == []


def test_lo_registrado_queda_marcado_como_despachado(libro):
    bd.registrar(TANDA, "05_acciones_etfs", "2_qqqus", activo="QQQ.US",
                 huella="abc", ahora=AHORA, ruta=libro)
    hist = bd.cargar(libro)
    assert bd.ya_despachada(hist, TANDA, "05_acciones_etfs", "2_qqqus")


def test_una_pieza_distinta_del_mismo_canal_no_queda_marcada(libro):
    """Es lo que rompia `--desde`: retomar un canal reenviaba sus primeras piezas."""
    bd.registrar(TANDA, "05_acciones_etfs", "2_qqqus", ahora=AHORA, ruta=libro)
    hist = bd.cargar(libro)
    assert not bd.ya_despachada(hist, TANDA, "05_acciones_etfs", "3_iwmus")


def test_la_misma_pieza_en_otra_tanda_si_se_puede_volver_a_publicar(libro):
    """Una tanda nueva del mismo activo es contenido legitimo: niveles nuevos,
    hora nueva. Lo que no se repite es la misma pieza de la misma tanda."""
    bd.registrar(TANDA, "06_criptoactivos", "1_solusd", ahora=AHORA, ruta=libro)
    hist = bd.cargar(libro)
    assert not bd.ya_despachada(
        hist, "2026-09-04_14-30_tarde_ny", "06_criptoactivos", "1_solusd"
    )


def test_la_misma_pieza_en_otro_canal_tampoco_se_confunde(libro):
    bd.registrar(TANDA, "06_criptoactivos", "1_solusd", ahora=AHORA, ruta=libro)
    hist = bd.cargar(libro)
    assert not bd.ya_despachada(hist, TANDA, "02_forex_divisas", "1_solusd")


def test_la_entrada_guarda_fecha_hora_activo_y_huella(libro):
    """La huella es la del texto enviado: permite ver despues si lo que salio es
    lo que el archivo dice hoy, sin duplicar el mensaje entero."""
    bd.registrar(TANDA, "05_acciones_etfs", "2_qqqus", activo="QQQ.US",
                 huella="h1u3ll4", ahora=AHORA, ruta=libro)
    entrada = json.loads(libro.read_text(encoding="utf-8"))[0]
    assert entrada == {
        "fecha": "2026-09-04", "hora": "10:17", "tanda": TANDA,
        "canal": "05_acciones_etfs", "pieza": "2_qqqus",
        "activo": "QQQ.US", "huella": "h1u3ll4",
    }


def test_registrar_acumula_sin_perder_lo_anterior(libro):
    for pieza in ("2_qqqus", "3_iwmus", "0_contexto_macro"):
        bd.registrar(TANDA, "05_acciones_etfs", pieza, ahora=AHORA, ruta=libro)
    assert len(bd.cargar(libro)) == 3


# ─────────────────────────────────────────────────────────────────────────────
# La reanudacion: `despachar` no repite una pieza que ya salio
# ─────────────────────────────────────────────────────────────────────────────
import pipeline_carrusel as pc  # noqa: E402


class SenderFalso:
    """Un sender que anota lo que le piden enviar y puede fallar en la pieza N.

    Reproduce el contrato que importa: `enviar_lote` llama `al_entregar` DENTRO
    del bucle, tras confirmar cada pieza, y levanta si una falla.
    """

    def __init__(self, falla_en: int | None = None):
        self.enviadas: list[str] = []
        self.falla_en = falla_en

    def enviar_lote(self, destinatario, piezas, dry_run=False, al_entregar=None):
        if dry_run:
            # Fiel al contrato real: `enviar_lote` devuelve ANTES del bucle, asi
            # que no entrega nada y no llama al callback. Si el falso no lo
            # modelara, el test de dry run probaria el falso y no el codigo.
            return {"status": "simulado", "piezas": len(piezas)}
        for i, pieza in enumerate(piezas, 1):
            if self.falla_en is not None and i == self.falla_en:
                raise RuntimeError("el adjunto no aparecio en la conversacion")
            self.enviadas.append(Path(pieza.adjunto).stem)
            if al_entregar is not None:
                al_entregar(pieza)
        return {"status": "enviado", "piezas": len(piezas)}

    def enviar(self, *a, **k):        # pragma: no cover - no se usa aca
        return {"status": "enviado"}


@pytest.fixture
def tanda_con_tres_piezas(tmp_path, monkeypatch, libro):
    """Una tanda de un canal con tres piezas listas, y la bitacora en tmp."""
    monkeypatch.setattr(bd, "HISTORIAL_PATH", libro)
    tanda = tmp_path / "2026-09-04_10-12_apertura_ny"
    canal = tanda / "05_acciones_etfs"
    canal.mkdir(parents=True)
    for nombre in ("1_qqqus", "2_iwmus", "3_spyus"):
        (canal / f"{nombre}.png").write_bytes(b"png")
        (canal / f"{nombre}_mensaje.txt").write_text(f"pie de {nombre}", encoding="utf-8")
    # El refresco pide MT5 y estas piezas no tienen `_procedencia.ticker`, asi que
    # se saltan solas; se neutraliza igual para que el test no dependa del terminal.
    monkeypatch.setattr(pc, "_refrescar_y_rendir", lambda d: [])
    return tanda


def _despachar_con(sender, tanda, monkeypatch):
    import whatsapp_sender
    monkeypatch.setattr(whatsapp_sender, "WhatsAppSender", lambda **k: sender)
    return pc.despachar(tanda, headless=True)


def test_un_despacho_interrumpido_deja_anotado_solo_lo_que_salio(
    tanda_con_tres_piezas, libro, monkeypatch
):
    """`enviar_lote` levanta y su `return` no ocurre. Si la bitacora se escribiera
    al final, se perderia el registro de las piezas que SI salieron, que es
    exactamente la informacion por la que existe."""
    sender = SenderFalso(falla_en=3)
    with pytest.raises(RuntimeError):
        _despachar_con(sender, tanda_con_tres_piezas, monkeypatch)

    assert sender.enviadas == ["1_qqqus", "2_iwmus"]
    anotadas = [e["pieza"] for e in bd.cargar(libro)]
    assert anotadas == ["1_qqqus", "2_iwmus"]


def test_la_reanudacion_no_repite_ninguna_pieza(
    tanda_con_tres_piezas, libro, monkeypatch
):
    """El defecto que `--desde N` no podia resolver: cuenta canales mientras el
    envio cuenta piezas, asi que retomar el canal reenviaba sus dos primeras."""
    with pytest.raises(RuntimeError):
        _despachar_con(SenderFalso(falla_en=3), tanda_con_tres_piezas, monkeypatch)

    segundo = SenderFalso()
    _despachar_con(segundo, tanda_con_tres_piezas, monkeypatch)

    assert segundo.enviadas == ["3_spyus"]
    assert [e["pieza"] for e in bd.cargar(libro)] == ["1_qqqus", "2_iwmus", "3_spyus"]


def test_un_canal_ya_despachado_completo_se_omite(
    tanda_con_tres_piezas, libro, monkeypatch
):
    primero = SenderFalso()
    _despachar_con(primero, tanda_con_tres_piezas, monkeypatch)
    assert len(primero.enviadas) == 3

    segundo = SenderFalso()
    res = _despachar_con(segundo, tanda_con_tres_piezas, monkeypatch)
    assert segundo.enviadas == []
    assert res["grupos"][0]["status"] == "ya_despachado"


def test_un_dry_run_no_ensucia_la_bitacora(
    tanda_con_tres_piezas, libro, monkeypatch
):
    """Simular no es enviar. Si el dry run anotara, el despacho real se saltaria
    la tanda entera creyendola ya entregada."""
    import whatsapp_sender
    sender = SenderFalso()
    monkeypatch.setattr(whatsapp_sender, "WhatsAppSender", lambda **k: sender)
    pc.despachar(tanda_con_tres_piezas, dry_run=True, headless=True)
    assert bd.cargar(libro) == []


def test_el_sender_real_no_anota_en_un_dry_run(tmp_path):
    """El contrato del que depende el test de arriba, probado sobre el sender de
    verdad: un dry run no llega al bucle de piezas, asi que no puede anotar.

    Si esto se rompiera, un dry run dejaria la tanda marcada como entregada y el
    despacho real la saltaria entera."""
    from whatsapp_sender import Pieza, WhatsAppSender

    png = tmp_path / "1_prueba.png"
    png.write_bytes(b"png")          # `_validar_lote` exige que el adjunto exista

    entregadas = []
    sender = WhatsAppSender(headless=True)
    res = sender.enviar_lote(
        "banco de pruebas",
        [Pieza(adjunto=png, mensaje="pie")],
        dry_run=True,
        al_entregar=entregadas.append,
    )
    assert res["status"] == "simulado"
    assert entregadas == []
