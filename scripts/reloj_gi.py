#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""El reloj de sucesos: latido del sistema operativo, decisión en Python.

**La trampa que esto evita.** Task Scheduler dispara en hora **local**. Una tarea
a las 08:30 de Chile es 08:30 de Nueva York hoy, y 06:30 de Nueva York en
noviembre: dos horas antes del dato que justifica la hora. La tarea seguiría
corriendo puntual y publicando el cierre de ayer. Por eso el agendador es un
**latido** que no sabe nada de mercados, y quien decide es este módulo, que lee
la agenda y convierte en el momento.

**Anclado al mercado, con el cambio narrado** (decisión del director, 2026-09-04).
La hora sigue al mercado y la hora chilena drifta; cuando el desfase cambia, se
avisa al canal. La alternativa era anclar a hora chilena fija, y se descartó
midiéndola: la pieza de índices habría salido en noviembre a las 08:00 de Nueva
York, hora y media antes de la campana, publicando el cierre de ayer con fecha de
hoy. El desfase se mueve cuatro veces al año y llega a dos horas.

**Este módulo no envía nada.** Prepara y avisa. Que un proceso automático pueda
publicar en un canal es justamente lo que el flujo de aprobación prohíbe, y hay
un test que falla si alguien conecta el envío acá.

Uso:
    uv run python scripts/reloj_gi.py --verificar    # qué haría, sin efectos
    uv run python scripts/reloj_gi.py --ejecutar     # prepara el momento vencido
    uv run python scripts/reloj_gi.py --estado       # el libro y el desfase
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import agenda_mercado as agenda  # noqa: E402

LIBRO = RAIZ / "data" / ".reloj_disparos.json"
CHILE = ZoneInfo("America/Santiago")

# Cuántos días de disparos se conservan. El libro es estado generado, no
# historia editorial: solo tiene que responder "¿ya salió hoy?". Un archivo que
# nada más crece termina siendo el problema.
DIAS_DE_LIBRO = 14


# ─────────────────────────────────────────────────────────────────────────────
# El desfase: se calcula, nunca se escribe
# ─────────────────────────────────────────────────────────────────────────────
def desfase_horas(cuando: datetime) -> int:
    """Cuántas horas va Chile por delante del ancla, en ese instante.

    **No hay ningún offset escrito acá y no debe haberlo.** Chile y EE.UU.
    cambian de horario en sentido opuesto, así que el desfase se mueve cuatro
    veces al año: escribirlo a mano queda mal dos de esas cuatro, que es el error
    de ±1 h del issue #38. Lo calcula el calendario.
    """
    ancla = cuando.astimezone(agenda.zona_ancla())
    delta = ancla.astimezone(CHILE).utcoffset() - ancla.utcoffset()
    return round(delta.total_seconds() / 3600)


def instante_del_momento(m: dict[str, Any], dia: datetime) -> datetime:
    """El instante exacto de un momento, ese día. Una sola implementación."""
    return agenda.instante(m, dia)


def zona_del_momento(m: dict[str, Any]) -> ZoneInfo:
    return agenda.zona_del_momento(m)


def hora_chile_del_momento(m: dict[str, Any], dia: datetime) -> str:
    """La hora del momento en el reloj del cliente, que es la que se comunica."""
    return instante_del_momento(m, dia).astimezone(CHILE).strftime("%H:%M")


# ─────────────────────────────────────────────────────────────────────────────
# El libro de disparos
# ─────────────────────────────────────────────────────────────────────────────
def cargar_libro(ruta: Path | None = None) -> dict[str, Any]:
    """El libro, o uno vacío. **No crea el archivo**: consultar no es escribir."""
    p = ruta or LIBRO
    if not p.exists():
        return {"disparos": {}}
    try:
        datos = json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        # Un libro corrupto no puede voltear el latido. Lo peor que pasa es que
        # un momento se repita una vez, y eso lo ve el director; que el reloj se
        # caiga en silencio no lo ve nadie.
        return {"disparos": {}}
    if not isinstance(datos, dict):
        return {"disparos": {}}
    datos.setdefault("disparos", {})
    return datos


def _clave_dia(cuando: datetime) -> str:
    """La fecha del ancla. El libro se indexa por un solo reloj, siempre el mismo.

    Indexarlo por la zona de cada momento haría que dos momentos de la misma
    jornada cayeran en días distintos cuatro meses al año.
    """
    return cuando.astimezone(agenda.zona_ancla()).strftime("%Y-%m-%d")


def anotar_disparo(
    slug: str, cuando: datetime, ruta: Path | None = None
) -> None:
    """Anota que este momento ya salió hoy, y poda lo viejo."""
    p = ruta or LIBRO
    libro = cargar_libro(p)
    dia = _clave_dia(cuando)
    del_dia = set(libro["disparos"].get(dia) or [])
    del_dia.add(slug)
    libro["disparos"][dia] = sorted(del_dia)
    libro["disparos"] = {
        d: libro["disparos"][d]
        for d in sorted(libro["disparos"])[-DIAS_DE_LIBRO:]
    }
    libro["desfase"] = desfase_horas(cuando)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(libro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ya_disparo(slug: str, cuando: datetime, libro: dict[str, Any]) -> bool:
    return slug in ((libro.get("disparos") or {}).get(_clave_dia(cuando)) or [])


# ─────────────────────────────────────────────────────────────────────────────
# La decisión
# ─────────────────────────────────────────────────────────────────────────────
def momento_pendiente(
    cuando: datetime, libro: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """El momento que le toca ahora y todavía no salió, o `None`.

    `None` es la respuesta normal: el latido pasa 96 veces al día y hay tres
    momentos. La idempotencia por día es lo que hace segura la tolerancia: el
    latido puede pasar cuatro veces por la misma ventana de gracia y la pieza
    sale una sola vez.

    Y es lo que hace **recuperable** la noche del cambio de hora chileno, donde
    una hora local simplemente no existe: una tarea anclada a esa hora no
    dispararía nunca, y acá el momento sale en el siguiente latido.
    """
    sesion = agenda.sesion_en(cuando)
    if sesion.get("dias") == "finde":
        return None
    m = agenda.momento_en(cuando)
    if m is None:
        return None
    if ya_disparo(m["slug"], cuando, libro or {}):
        return None
    return m


def canales_del_momento(m: dict[str, Any]) -> list[str]:
    """Los canales que cubre un momento, por el mapeo REAL de activo a canal.

    No hay una segunda lista de canales por momento: se recorre el universo del
    escáner y se pregunta por el mismo mapeo que usan las piezas. Una lista
    aparte sería otro contrato por nombre de los que ya costaron caro.
    """
    from pipeline_carrusel import obtener_grupo_whatsapp
    from screener_gi import cargar_universo

    clases = set(m.get("clases") or [])
    canales = {
        obtener_grupo_whatsapp(a["clase"], a["ticker"])
        for a in cargar_universo(solo_renderizables=False)
        if a["clase"] in clases
    }
    return sorted(canales)


# ─────────────────────────────────────────────────────────────────────────────
# La narración del cambio de horario
# ─────────────────────────────────────────────────────────────────────────────
def quien_cambio(cuando: datetime, dias: int = 7) -> str | None:
    """Cuál de los dos países movió su reloj, o `None` si ninguno.

    **Importa para no publicar una explicación falsa.** El cambio de septiembre
    es Chile entrando en su horario de verano; el de noviembre es Estados Unidos
    saliendo del suyo. Decir "horario de verano de Chile" en noviembre sería
    contarle al cliente algo que no pasó.

    Se deduce comparando el desplazamiento de cada zona con el de una semana
    antes. Una semana porque los cambios caen en domingo y nunca hay dos en
    siete días.
    """
    antes = cuando - timedelta(days=dias)
    for pais, zona in (("Chile", CHILE), ("Estados Unidos", agenda.zona_ancla())):
        if cuando.astimezone(zona).utcoffset() != antes.astimezone(zona).utcoffset():
            return pais
    return None


def _mensaje_cambio(cuando: datetime, anterior: int, nuevo: int) -> str:
    """El aviso al canal cuando la hora de entrega se mueve.

    Convierte un corrimiento confuso en un cambio comunicado, y lo dispara el
    dato en vez de la memoria del director. Cuatro veces al año.

    Lo lee el cliente, así que se le aplican las reglas de texto de cliente:
    nombres acentuados, negrita de WhatsApp, sin guion largo, sin cifras de
    precio, y los momentos en orden de reloj y no en el del archivo.
    """
    horas = sorted(
        (hora_chile_del_momento(m, cuando), m["nombre"]) for m in agenda.momentos()
    )
    detalle = "\n".join(f"• {nombre}: *{hora}*" for hora, nombre in horas)
    verbo = "más tarde" if nuevo > anterior else "más temprano"
    pais = quien_cambio(cuando)
    causa = (
        f"Lo que cambió es el reloj de {pais} por el cambio de horario de verano"
        if pais else "Lo que cambió es el reloj, no el mercado"
    )
    return "\n".join([
        "🕐 *Cambio de horario de entrega*",
        "━━━━━━━━━━━━━━━━━━━",
        f"Desde hoy los análisis del día llegan una hora {verbo}:",
        detalle,
        "━━━━━━━━━━━━━━━━━━━",
        "Los horarios están atados a la apertura de Nueva York, que es cuando el "
        f"mercado se mueve de verdad. {causa}, así que el análisis sigue llegando "
        "en el mismo momento del mercado.",
    ])


def aviso_de_desfase(
    cuando: datetime, libro: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """El aviso de que la hora de entrega se movió, o `None` si no se movió.

    **La primera corrida no narra nada.** Sin desfase anterior registrado no
    hubo cambio que contar: anunciar uno inventado el día que se instala el reloj
    sería peor que callarse.
    """
    libro = libro or {}
    anterior = libro.get("desfase")
    if anterior is None:
        return None
    nuevo = desfase_horas(cuando)
    if int(anterior) == nuevo:
        return None
    return {
        "desfase_anterior": int(anterior),
        "desfase_nuevo": nuevo,
        "mensaje": _mensaje_cambio(cuando, int(anterior), nuevo),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Estado y ejecución
# ─────────────────────────────────────────────────────────────────────────────
def estado(
    cuando: datetime | None = None, ruta_libro: Path | None = None
) -> dict[str, Any]:
    """Qué haría el reloj ahora mismo, **sin efectos**."""
    ahora = cuando or datetime.now(tz=agenda.zona_ancla())
    libro = cargar_libro(ruta_libro)
    m = momento_pendiente(ahora, libro)
    aviso = aviso_de_desfase(ahora, libro)
    return {
        "hora_ancla": ahora.astimezone(agenda.zona_ancla()).strftime("%Y-%m-%d %H:%M"),
        "hora_chile": ahora.astimezone(CHILE).strftime("%Y-%m-%d %H:%M"),
        "desfase": desfase_horas(ahora),
        "sesion": agenda.sesion_en(ahora)["slug"],
        "momento": m["slug"] if m else None,
        "canales": canales_del_momento(m) if m else [],
        "hora_chile_del_momento": hora_chile_del_momento(m, ahora) if m else None,
        "cambio_de_horario": aviso,
        "ya_disparados_hoy": (libro.get("disparos") or {}).get(_clave_dia(ahora), []),
    }


def _correr_preparar(canal: str) -> dict[str, Any]:
    """Una corrida de `pipeline_carrusel.py --preparar` para un canal."""
    cmd = [
        sys.executable, str(RAIZ / "scripts" / "pipeline_carrusel.py"),
        "--preparar", "--grupo", canal,
    ]
    r = subprocess.run(cmd, cwd=str(RAIZ), capture_output=True, text=True)
    return {
        "canal": canal,
        "codigo": r.returncode,
        "salida": (r.stdout or "")[-1500:],
        "error": (r.stderr or "")[-500:],
    }


def ejecutar(
    cuando: datetime | None = None,
    correr: Any = None,
    ruta_libro: Path | None = None,
) -> dict[str, Any]:
    """Prepara la tanda del momento vencido, canal por canal.

    **Solo prepara.** El despacho sigue siendo del director, después de revisar.

    **Un momento que falló sigue pendiente.** MT5 puede no estar conectado en ese
    latido, y anotar el disparo igual perdería la pieza por el día entero. Sin
    anotar, el siguiente latido reintenta dentro de la tolerancia, que es
    justamente para lo que existe la ventana de gracia.
    """
    ahora = cuando or datetime.now(tz=agenda.zona_ancla())
    est = estado(ahora, ruta_libro)
    if not est["momento"]:
        return {**est, "corridas": [], "nota": "no hay momento vencido"}

    hacer = correr or _correr_preparar
    corridas = [hacer(canal) for canal in est["canales"]]

    if any(c["codigo"] == 0 for c in corridas):
        anotar_disparo(est["momento"], ahora, ruta=ruta_libro)
        nota = None
    else:
        nota = ("ninguna corrida termino bien: el momento sigue pendiente y el "
                "siguiente latido lo reintenta")
    return {**est, "corridas": corridas, "nota": nota}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--verificar", action="store_true",
                   help="qué haría ahora, sin efectos (default)")
    g.add_argument("--ejecutar", action="store_true",
                   help="prepara la tanda del momento vencido")
    g.add_argument("--estado", action="store_true", help="el libro y el desfase")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    args = ap.parse_args()

    res = ejecutar() if args.ejecutar else estado()
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    print(f"ancla {res['hora_ancla']}  |  Chile {res['hora_chile']}  "
          f"|  desfase +{res['desfase']}h  |  sesion {res['sesion']}")
    if res["momento"]:
        print(f"momento vencido: {res['momento']} "
              f"({res['hora_chile_del_momento']} hora de Chile) "
              f"-> canales {', '.join(res['canales'])}")
    else:
        print("sin momento vencido")
    if res["ya_disparados_hoy"]:
        print(f"ya salieron hoy: {', '.join(res['ya_disparados_hoy'])}")
    if res["cambio_de_horario"]:
        c = res["cambio_de_horario"]
        print(f"\n*** CAMBIO DE HORARIO: +{c['desfase_anterior']}h -> "
              f"+{c['desfase_nuevo']}h ***")
        print("Aviso listo para revisar y mandar a los canales:\n")
        print(c["mensaje"])
    for c in res.get("corridas", []):
        print(f"\n[{c['canal']}] codigo {c['codigo']}")
        print(c["salida"] or c["error"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
