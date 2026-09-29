"""Carruseles de LinkedIn: datos del terminal + visión de los bancos, en un brief para diseño.

Mismo reparto que `pipeline_carrusel` y `pipeline_informe`: el script produce los
**datos** y el comando `/linkedin` escribe el **texto**. Dos pasos:

    uv run --with MetaTrader5 python scripts/pipeline_linkedin.py --preparar --formato cita --activos USDCLP
    uv run --extra informe python scripts/pipeline_linkedin.py --rendir data/linkedin/<tanda>

La salida no es la pieza final sino el **brief** que el equipo de diseño convierte
en láminas: texto por página, copy del post y la ficha de cifras, en `.md` y `.pdf`.
Publicar en LinkedIn es manual, a propósito: automatizarlo va contra sus términos.

Por qué esto es un sistema y no un texto a mano (se hizo a mano el 2026-09-28 y
de ahí salieron los frenos):

1. **Las cifras salen del terminal y el texto no puede traer otras.** `--rendir`
   busca todo precio escrito en el texto (`$971,03`, `US$4.113,13`) y exige que
   sea una cifra medida, esté dentro de una cita registrada o esté declarado en
   `cifras_citadas` con su motivo. Un número que no se puede rastrear se detiene.
2. **Una cita de banco vieja no pasa como opinión de hoy.** Las visiones viven en
   `data/visiones_expertos.json` con fecha y URL. Más de `ANTIGUEDAD_MAX_DIAS`
   días frena el render, salvo que la pieza la acepte con motivo, y el motivo sale
   impreso en el brief. La meta de oro de J.P. Morgan que se usó ese día era de
   junio: se detectó porque se abrió la página, no porque algo lo exigiera.
3. **Los datos vencen.** El brief lleva la hora de lectura; con más de
   `FRESCURA_MAX_HORAS` el render se detiene, porque el carrusel sale publicado
   con cifras que ya no son las del mercado.
4. **Las reglas de texto de cliente se verifican, no se revisan a ojo**: ni guion
   largo ni medio como inciso, ni voseo, ni marcadores sin completar.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SANTIAGO = ZoneInfo("America/Santiago")
DIR_TRABAJO = RAIZ / "data" / "linkedin"
REGISTRO_VISIONES = RAIZ / "data" / "visiones_expertos.json"

MARCA_EDITORIAL = "[[ESCRIBIR]]"
ANTIGUEDAD_MAX_DIAS = 45
FRESCURA_MAX_HORAS = 24
DIAS_AGENDA = 7

# Los campos de nivel que el texto puede citar. Son los mismos que la ficha
# publica, así que cualquier cifra del texto se puede encontrar en la ficha.
CAMPOS_PRECIO = ("price", "s2", "s1", "r1", "r2", "ema_50", "donchian_50_high", "donchian_50_low")

# Un formato es la estructura de una referencia de LinkedIn: qué páginas tiene y
# qué campos escribe el comando en cada una. `vision` es el id de una entrada del
# registro, no una cita escrita a mano: la cita se copia del registro al rendir.
FORMATOS: dict[str, dict[str, Any]] = {
    "cita": {
        "nombre": "Cita de experto vs. dato",
        "referencia": "Tarjeta de cita (Diario Financiero / BTG): frase textual grande y firma abajo",
        "principal": True,
        "paginas": {
            "portada": ["titular", "bajada"],
            "cita_1": ["vision", "remate"],
            "cita_2": ["vision", "remate"],
            "nuestros_datos": ["titular", "texto"],
            "lectura": ["titular", "texto"],
        },
    },
    "problema_solucion": {
        "nombre": "Problema, giro y método",
        "referencia": "Gancho problema, giro, método y llamada a la acción (carrusel de consultora)",
        "principal": True,
        "paginas": {
            "gancho": ["titular", "remate"],
            "matiz": ["titular", "texto", "vision"],
            "precio_hoy": ["titular", "texto"],
            "metodo": ["titular", "texto"],
            "llamada": ["titular", "texto", "cta"],
        },
    },
    "agenda": {
        "nombre": "Agenda de la semana",
        "referencia": "Agenda (feria IACC): una página por día con hora y qué pasa",
        "principal": False,
        "paginas": {
            "portada": ["kicker", "titular", "bajada"],
            "contexto": ["texto", "vision"],
            "cierre_agenda": ["remate"],
        },
    },
}

_NOMBRE_PAGINA = {
    "portada": "Portada", "cita_1": "Cita 1", "cita_2": "Cita 2",
    "nuestros_datos": "Nuestros datos", "lectura": "Nuestra lectura",
    "gancho": "Gancho", "matiz": "El matiz", "precio_hoy": "Lo que dice el precio hoy",
    "metodo": "El método", "llamada": "Llamada a la acción",
    "contexto": "El contexto", "cierre_agenda": "Qué mirar en cada activo",
}

_TRAMOS = {
    "DGS2": "Bono del Tesoro a 2 años",
    "DGS10": "Bono del Tesoro a 10 años",
    "DGS30": "Bono del Tesoro a 30 años",
    "DFII10": "Tasa real a 10 años (TIPS)",
    "T10YIE": "Inflación esperada a 10 años",
    "DFF": "Tasa efectiva de fondos federales",
}

_DIAS_ES = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")


# ---------------------------------------------------------------- formato


def formatear(valor: float, digits: int) -> str:
    """Precio en notación chilena con los decimales del catálogo.

    Delega en `grafico_informe.formatear_precio`: dos formateadores del mismo
    precio divergen, y el cobre (`digits = 0`, sin separador de miles) es
    justamente el caso donde ya divergieron una vez.
    """
    from grafico_informe import formatear_precio

    return formatear_precio(float(valor), int(digits))


def _pct(valor: Any) -> str:
    if valor is None:
        return "sin dato"
    return f"{float(valor):+.2f}%".replace(".", ",")


def _nivel(fila: dict[str, Any], campo: str) -> str:
    """Un nivel formateado, o vacío si el terminal no lo entregó."""
    valor = fila.get(campo)
    return "" if valor is None else formatear(valor, fila["digits"])


# ---------------------------------------------------------------- preparar


def _catalogo() -> dict[str, dict[str, Any]]:
    import screener_gi as sc

    return {a["ticker"]: a for a in sc.cargar_universo(solo_renderizables=False)}


def leer_activos(tickers: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Lectura diaria de cada activo, con los avisos de lo que no se pudo leer."""
    import screener_gi as sc

    catalogo = _catalogo()
    avisos: list[str] = []
    fuera = [t for t in tickers if t not in catalogo]
    if fuera:
        raise SystemExit(f"Tickers fuera del catálogo: {', '.join(fuera)}")

    from market_data_mcp import mt5_client
    from market_data_mcp.analisis import analizar_activo

    try:
        mt5_client.connect()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"MT5 no conectó ({exc.__class__.__name__}). Sin terminal no hay cifras, "
            "y un carrusel sin cifras medidas no se prepara."
        ) from exc

    salida: dict[str, dict[str, Any]] = {}
    for ticker in tickers:
        d1 = analizar_activo(ticker, "D1")
        if d1.get("error"):
            avisos.append(f"{catalogo[ticker]['nombre']}: sin lectura ({d1['error']}).")
            continue
        fila = {"nombre": catalogo[ticker]["nombre"], "digits": catalogo[ticker]["digits"]}
        fila.update({c: d1.get(c) for c in CAMPOS_PRECIO})
        fila["change_pct"] = d1.get("change_pct")
        fila["rsi_14"] = d1.get("rsi_14")
        fila["direccion"] = sc.direccion_tecnica(d1)
        salida[ticker] = fila
    if not salida:
        raise SystemExit("Ningún activo se pudo leer del terminal: no hay carrusel que preparar.")
    return salida, avisos


def leer_curva(ahora: datetime, vivo: dict[str, dict[str, Any]] | None = None) -> tuple[dict[str, Any], list[str]]:
    """La curva de `data central/`, con el rendimiento del día donde lo hay.

    FRED publica con días de rezago: el 2026-09-28 el archivo decía 5,18% (dato
    del 24) mientras el 10 años cotizaba 5,27%. Un carrusel que se publica hoy no
    puede traer la tasa de la semana pasada, así que se usa `rendimientos_en_vivo`,
    la misma fuente que el carrusel de WhatsApp, y solo si la cotización es de hoy.
    La variación a 5 días sigue siendo la del archivo y la ficha lo dice.
    """
    from market_data_mcp.curva_reader import cargar_curva_tasas

    res = cargar_curva_tasas(serie="ALL")
    if "error" in res:
        return {}, [f"curva del Tesoro no disponible ({res['error']})"]
    if vivo is None:
        try:
            from market_data_mcp.tasas_en_vivo import rendimientos_en_vivo

            vivo = rendimientos_en_vivo(tuple(_TRAMOS))
        except ImportError:
            vivo = {}
    series = res.get("series", {})
    curva: dict[str, Any] = {}
    for codigo, nombre in _TRAMOS.items():
        if codigo not in series:
            continue
        fila = {
            "nombre": nombre,
            "nivel_pct": series[codigo].get("nivel_pct"),
            "delta_5d_bps": series[codigo].get("delta_5d_bps"),
            "fecha_dato": series[codigo].get("fecha_dato"),
            "fuente": "FRED / Tesoro (archivo)",
        }
        cotizacion = vivo.get(codigo)
        if cotizacion and cotizacion["momento"].astimezone(SANTIAGO).date() == ahora.date():
            fila.update(nivel_pct=cotizacion["valor"], fecha_dato=cotizacion["fecha"],
                        fuente=cotizacion.get("fuente", "en vivo"))
        curva[codigo] = fila
    return curva, []


def leer_agenda(ahora: datetime) -> tuple[list[dict[str, Any]], list[str]]:
    """Eventos de impacto alto de los próximos días, ya en hora de Chile.

    `cargar_calendario` entrega la hora en America/Santiago: convertirla otra vez
    es el desfase de ±1 h del issue #38.
    """
    from market_data_mcp.tools.calendar import cargar_calendario

    res = cargar_calendario(solo_hoy=False, min_impact="high", ahora=ahora)
    if "error" in res:
        return [], [f"calendario no disponible ({res['error']})"]
    limite = ahora + timedelta(days=DIAS_AGENDA)
    eventos: list[dict[str, Any]] = []
    for ev in res.get("eventos", []):
        try:
            momento = datetime.strptime(ev["hora_servidor"], "%Y-%m-%d %H:%M").replace(tzinfo=SANTIAGO)
        except (KeyError, ValueError):
            continue
        if not (ahora <= momento <= limite):
            continue
        eventos.append({
            "fecha": momento.strftime("%Y-%m-%d"),
            "hora": momento.strftime("%H:%M"),
            "pais": ev.get("pais", ""),
            "evento": ev.get("nombre", ""),
            "nombre_es": (ev.get("diccionario") or {}).get("nombre_es", ""),
            "consenso": ev.get("forecast", ""),
            "anterior": ev.get("previo", ""),
        })
    return eventos, []


def esqueleto_editorial(formato: str) -> dict[str, Any]:
    paginas = {
        pagina: {campo: MARCA_EDITORIAL for campo in campos}
        for pagina, campos in FORMATOS[formato]["paginas"].items()
    }
    editorial: dict[str, Any] = {
        "paginas": paginas,
        "copy": MARCA_EDITORIAL,
        "hashtags": MARCA_EDITORIAL,
        "cifras_citadas": {},
        "aceptar_antiguas": {},
    }
    if formato == "agenda":
        editorial["remates_dia"] = {}
    return editorial


def armar_payload(
    formato: str,
    activos: dict[str, dict[str, Any]],
    curva: dict[str, Any],
    agenda: list[dict[str, Any]],
    avisos: list[str],
    ahora: datetime,
    principal: str | None,
) -> dict[str, Any]:
    """El payload sin tocar disco ni terminal, para que los tests lo armen igual."""
    if formato not in FORMATOS:
        raise SystemExit(f"Formato desconocido: {formato}. Opciones: {', '.join(FORMATOS)}")
    if FORMATOS[formato]["principal"]:
        principal = principal or next(iter(activos))
        if principal not in activos:
            raise SystemExit(f"El activo principal {principal} no tiene lectura.")
    else:
        principal = None
    editorial = esqueleto_editorial(formato)
    if formato == "agenda":
        editorial["remates_dia"] = {f: MARCA_EDITORIAL for f in sorted({e["fecha"] for e in agenda})}
    return {
        "version": 1,
        "formato": formato,
        "activo_principal": principal,
        "datos": {
            "leido_en": ahora.isoformat(timespec="minutes"),
            "activos": activos,
            "curva": curva,
            "agenda": agenda,
            "avisos": avisos,
        },
        "editorial": editorial,
        "_pendiente_editorial": True,
    }


def preparar(formato: str, tickers: list[str], principal: str | None) -> Path:
    ahora = datetime.now(SANTIAGO)
    activos, av1 = leer_activos(tickers)
    curva, av2 = leer_curva(ahora)
    agenda, av3 = leer_agenda(ahora) if formato == "agenda" else ([], [])
    payload = armar_payload(formato, activos, curva, agenda, av1 + av2 + av3, ahora, principal)
    destino = DIR_TRABAJO / f"{ahora:%Y-%m-%d_%H-%M}_{formato}"
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / "payload.json"
    ruta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


# ---------------------------------------------------------------- visiones


def cargar_visiones(ruta: Path = REGISTRO_VISIONES) -> dict[str, dict[str, Any]]:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return {v["id"]: v for v in datos.get("visiones", [])}


def validar_vision(vision: dict[str, Any], hoy: date, motivo_antigua: str | None) -> list[str]:
    """Lo que una visión necesita para citarse: quién, qué, cuándo y dónde."""
    vid = vision.get("id", "?")
    errores = [
        f"visión {vid}: falta {campo}"
        for campo in ("quien", "institucion", "cita", "fecha", "url")
        if not str(vision.get(campo, "")).strip()
    ]
    if errores:
        return errores
    if not str(vision["url"]).startswith(("http://", "https://")):
        errores.append(f"visión {vid}: la URL no es un enlace ({vision['url']})")
    try:
        fecha = date.fromisoformat(str(vision["fecha"]))
    except ValueError:
        return errores + [f"visión {vid}: fecha ilegible ({vision['fecha']}); va AAAA-MM-DD"]
    # Un día de margen: una nota de Tokio o Sídney ya lleva la fecha de mañana
    # cuando en Santiago todavía es hoy.
    if (fecha - hoy).days > 1:
        errores.append(f"visión {vid}: fecha futura ({fecha})")
    edad = (hoy - fecha).days
    if edad > ANTIGUEDAD_MAX_DIAS and not (motivo_antigua or "").strip():
        errores.append(
            f"visión {vid}: tiene {edad} días (máximo {ANTIGUEDAD_MAX_DIAS}). "
            "Busca una más reciente o acéptala en `aceptar_antiguas` con el motivo."
        )
    return errores


# ---------------------------------------------------------------- validar


def leido_en(payload: dict[str, Any]) -> datetime:
    """La hora de lectura de los datos, en Santiago si el payload perdió la zona.

    Un payload editado a mano puede quedar con `2026-09-28T12:18` sin offset, y
    restar un datetime sin zona de uno con zona lanza TypeError en vez de avisar.
    """
    leido = datetime.fromisoformat(payload["datos"]["leido_en"])
    return leido if leido.tzinfo else leido.replace(tzinfo=SANTIAGO)


# Miles con punto solo en grupos de tres, para que el punto final de una frase
# ("llegó a $971.") no quede pegado a la cifra.
_PRECIO = re.compile(r"(?:US\$|\$)\s?(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)")

# Toda cifra, con o sin moneda. No se exige que calce exacto (fallarían "50
# días" o "0,24 puntos"): se usa para el freno por cercanía, más abajo.
_NUMERO = re.compile(r"(?<![\d.,])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)(?![\d.,]*\d)(?!\s?%)")

# Qué tan cerca de un precio medido tiene que estar una cifra para leerse como
# ese precio. 3% cubre la cifra de ayer o la de hace unas horas sin alcanzar
# a los niveles vecinos de activos distintos.
CERCANIA_PRECIO = 0.03


def _a_float(cifra: str) -> float:
    return float(cifra.replace(".", "").replace(",", "."))


def cifras_parecidas_no_medidas(texto: str, payload: dict[str, Any], permitidas: set[str]) -> list[str]:
    """Cifras sin `$` que se parecen a un precio medido pero no son ese precio.

    `_PRECIO` solo ve lo que lleva `$`, y un nivel de índice nunca lo lleva
    (30.379,37), ni un "USD 971". Exigir que toda cifra del texto calce fallaría
    con "50 días" o "0,24 puntos". Así que se busca el caso que de verdad se
    escapa: una cifra a menos de `CERCANIA_PRECIO` de un precio del terminal que
    no coincide con ninguno. Es la cifra de ayer copiada, o un nivel redondeado.
    """
    referencias = [
        float(fila[c])
        for fila in payload["datos"]["activos"].values()
        for c in CAMPOS_PRECIO
        if fila.get(c) not in (None, 0)
    ]
    dudosas: list[str] = []
    for cifra in _NUMERO.findall(texto):
        if cifra in permitidas:
            continue
        valor = _a_float(cifra)
        if 1900 <= valor <= 2100 and "," not in cifra and "." not in cifra:
            continue  # un año
        if any(abs(valor - ref) / ref <= CERCANIA_PRECIO for ref in referencias):
            dudosas.append(cifra)
    return dudosas


def _textos(editorial: dict[str, Any]) -> list[tuple[str, str]]:
    """Todo texto de cliente del payload, con su ubicación para el mensaje de error."""
    salida: list[tuple[str, str]] = []
    for pagina, campos in editorial.get("paginas", {}).items():
        for campo, valor in campos.items():
            if campo != "vision":
                salida.append((f"{pagina}.{campo}", str(valor)))
    for fecha, valor in editorial.get("remates_dia", {}).items():
        salida.append((f"remate {fecha}", str(valor)))
    salida.append(("copy", str(editorial.get("copy", ""))))
    salida.append(("hashtags", str(editorial.get("hashtags", ""))))
    return salida


def cifras_permitidas(payload: dict[str, Any], visiones: list[dict[str, Any]]) -> set[str]:
    permitidas: set[str] = set()
    for fila in payload["datos"]["activos"].values():
        for campo in CAMPOS_PRECIO:
            if fila.get(campo) is not None:
                permitidas.add(formatear(fila[campo], fila["digits"]))
    for vision in visiones:
        permitidas.update(_PRECIO.findall(str(vision.get("cita", ""))))
    for cifra in payload["editorial"].get("cifras_citadas", {}):
        permitidas.update(_PRECIO.findall(cifra) or [cifra.strip()])
    return permitidas


def validar(payload: dict[str, Any], registro: dict[str, dict[str, Any]], ahora: datetime,
            aceptar_datos_viejos: bool = False) -> list[str]:
    """Todos los motivos por los que el brief no puede salir. Vacío = puede salir.

    Junta todos los errores en vez de cortar al primero: el comando corrige de una
    vez en vez de ir descubriendo los huecos uno por uno.
    """
    from validador_editorial import validar_texto

    editorial = payload["editorial"]
    errores: list[str] = []

    for donde, texto in _textos(editorial):
        if MARCA_EDITORIAL in texto or not texto.strip():
            errores.append(f"{donde}: sin escribir")
            continue
        if "–" in texto or "—" in texto:
            errores.append(f"{donde}: guion largo o medio como inciso; reescribe con punto, coma o dos puntos")
        errores.extend(e for e in validar_texto(texto, campo=donde) if "guion largo" not in e)

    usadas: list[dict[str, Any]] = []
    aceptadas = editorial.get("aceptar_antiguas", {})
    hoy = ahora.date()
    for pagina, campos in editorial.get("paginas", {}).items():
        vid = campos.get("vision")
        if vid is None:
            continue
        if vid == MARCA_EDITORIAL or not str(vid).strip():
            errores.append(f"{pagina}.vision: sin elegir")
            continue
        if vid not in registro:
            errores.append(f"{pagina}.vision: `{vid}` no está en {REGISTRO_VISIONES.name}")
            continue
        usadas.append(registro[vid])
        errores.extend(validar_vision(registro[vid], hoy, aceptadas.get(vid)))

    permitidas = cifras_permitidas(payload, usadas)
    for donde, texto in _textos(editorial):
        con_moneda = _PRECIO.findall(texto)
        for cifra in con_moneda:
            if cifra not in permitidas:
                errores.append(
                    f"{donde}: la cifra ${cifra} no sale del terminal ni de una cita registrada. "
                    "Usa la medida o declárala en `cifras_citadas` con su motivo."
                )
        for cifra in cifras_parecidas_no_medidas(texto, payload, permitidas):
            if cifra not in con_moneda:
                errores.append(
                    f"{donde}: {cifra} se parece a un precio medido pero no es ninguno. "
                    "Usa la cifra exacta del terminal o declárala en `cifras_citadas`."
                )

    leido = leido_en(payload)
    horas = (ahora - leido).total_seconds() / 3600
    if horas > FRESCURA_MAX_HORAS and not aceptar_datos_viejos:
        errores.append(
            f"los datos se leyeron hace {horas:.0f} h (máximo {FRESCURA_MAX_HORAS}). "
            "Vuelve a correr --preparar."
        )
    return errores


# ---------------------------------------------------------------- brief


def mapa_niveles(fila: dict[str, Any]) -> list[str]:
    """El cierre canónico de tres escenarios, armado con cifras medidas."""
    if any(fila.get(c) is None for c in ("s1", "r1", "r2", "s2")):
        return ["Mapa no disponible: el terminal no entregó soporte o resistencia. No inventarlo."]
    s1, r1, r2, s2 = (_nivel(fila, c) for c in ("s1", "r1", "r2", "s2"))
    return [
        f"🟢 Sobre **{r1}** → fuerza compradora; siguiente nivel **{r2}**",
        f"🟡 Entre **{s1}** y **{r1}** → rango: si rompe un borde y vuelve a entrar, "
        "el objetivo pasa a ser el borde contrario",
        f"🔴 Bajo **{s1}** → presión vendedora; siguiente nivel **{s2}**",
    ]


def _bloque_vision(vision: dict[str, Any], motivo: str | None) -> list[str]:
    tipo = vision.get("tipo", "textual")
    cita = vision["cita"] if tipo == "parafrasis" else f"\"{vision['cita']}\""
    etiqueta = {"textual": "Cita", "traduccion": "Cita (traducción nuestra)", "parafrasis": "Lo que proyecta"}
    lineas = [
        f"- {etiqueta.get(tipo, 'Cita')}: {cita}",
        f"- Firma: {vision['quien']} · {vision['institucion']} · {vision.get('fuente', '')}, {vision['fecha']}",
    ]
    if motivo:
        lineas.append(f"- ⚠️ Cita de más de {ANTIGUEDAD_MAX_DIAS} días, aceptada: {motivo}")
    return lineas


def _tabla_activos(activos: dict[str, dict[str, Any]]) -> list[str]:
    filas = [
        "| Activo | Precio | Var. día | Dirección | S2 | S1 | R1 | R2 | Media 50 días | RSI 14 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for f in activos.values():
        n = {c: _nivel(f, c) for c in CAMPOS_PRECIO}
        filas.append(
            f"| {f['nombre']} | {n['price']} | {_pct(f['change_pct'])} | {f['direccion'].capitalize()} "
            f"| {n['s2']} | {n['s1']} | {n['r1']} | {n['r2']} | {n['ema_50']} | {f.get('rsi_14', '')} |"
        )
    return filas


def _agenda_por_dia(agenda: list[dict[str, Any]], remates: dict[str, str]) -> list[str]:
    lineas: list[str] = []
    for fecha in sorted({e["fecha"] for e in agenda}):
        dia = date.fromisoformat(fecha)
        lineas += ["", f"### {_DIAS_ES[dia.weekday()]} {dia.day:02d}", ""]
        for e in (x for x in agenda if x["fecha"] == fecha):
            nombre = e["nombre_es"] or e["evento"]
            cifras = f"esperado {e['consenso']}" if e["consenso"] else ""
            if e["anterior"]:
                cifras += f"{' · ' if cifras else ''}anterior {e['anterior']}"
            lineas.append(f"- {e['hora']} · **{nombre}** ({e['pais']}, {e['evento']}){': ' + cifras if cifras else ''}")
        if remates.get(fecha):
            lineas.append(f"- Remate: {remates[fecha]}")
    return lineas


def construir_brief(payload: dict[str, Any], registro: dict[str, dict[str, Any]]) -> str:
    formato = FORMATOS[payload["formato"]]
    editorial = payload["editorial"]
    datos = payload["datos"]
    aceptadas = editorial.get("aceptar_antiguas", {})
    leido = leido_en(payload)
    principal = payload.get("activo_principal")

    md: list[str] = [
        f"# Carrusel LinkedIn · {formato['nombre']}",
        "",
        "**Para:** equipo de diseño  ",
        f"**Formato de referencia:** {formato['referencia']}  ",
        f"**Páginas:** {len(formato['paginas']) + (len({e['fecha'] for e in datos['agenda']}) if payload['formato'] == 'agenda' else 0)}",
        "",
        f"> ⚠️ **Cifras leídas del terminal MT5 el {leido:%d-%m-%Y} a las {leido:%H:%M} hora Chile.** "
        "Si el carrusel sale otro día, se vuelve a correr `--preparar`.",
        "",
    ]
    for aviso in datos.get("avisos", []):
        md.append(f"> Aviso de datos: {aviso}")
    md.append("")

    n = 0
    for pagina, campos in editorial["paginas"].items():
        if pagina == "cierre_agenda":
            continue
        n += 1
        md += [f"### Pág. {n} · {_NOMBRE_PAGINA.get(pagina, pagina)}", ""]
        for campo, valor in campos.items():
            if campo == "vision":
                md += _bloque_vision(registro[valor], aceptadas.get(valor))
            else:
                md.append(f"- {campo.capitalize()}: {valor}")
        if pagina in ("nuestros_datos", "precio_hoy") and principal:
            md += ["- Mapa de niveles (cifras del terminal, no editar):"]
            md += [f"    - {linea}" for linea in mapa_niveles(datos["activos"][principal])]
        md.append("")

    if payload["formato"] == "agenda":
        md += _agenda_por_dia(datos["agenda"], editorial.get("remates_dia", {}))
        n += len({e["fecha"] for e in datos["agenda"]}) + 1
        md += ["", f"### Pág. {n} · Qué mirar en cada activo", "",
               "| Activo | Dirección | Nivel a vigilar |", "| --- | --- | --- |"]
        for f in datos["activos"].values():
            nivel = _nivel(f, "r1" if f["direccion"] == "ALCISTA" else "s1")
            md.append(f"| {f['nombre']} | {f['direccion'].capitalize()} | {nivel} |")
        md += ["", f"- Remate: {editorial['paginas']['cierre_agenda']['remate']}", ""]

    md += ["### Copy del post", ""]
    md += [f"> {linea}" if linea.strip() else ">" for linea in str(editorial["copy"]).splitlines()]
    md += [">", f"> {str(editorial['hashtags']).replace('#', chr(92) + '#', 1)}", ""]

    md += ["---", "", "## Ficha de datos para diseño", ""]
    md += _tabla_activos(datos["activos"])
    md += ["", "Decimales según el broker (`digits` del catálogo). La dirección es precio contra la media de 50 días.", ""]
    if datos.get("curva"):
        md += ["| Tasa | Nivel | Cambio 5 días (archivo) | Fecha del dato | Fuente del nivel |",
               "| --- | --- | --- | --- | --- |"]
        for c in datos["curva"].values():
            nivel = f"{c['nivel_pct']:.2f}%".replace(".", ",") if c.get("nivel_pct") is not None else ""
            delta = c.get("delta_5d_bps")
            cambio = "sin dato" if delta is None else f"{delta / 100:+.2f} puntos".replace(".", ",")
            md.append(f"| {c['nombre']} | {nivel} | {cambio} | {c.get('fecha_dato', '')} | {c.get('fuente', '')} |")
        md.append("")
    md += ["Todo nivel citado en el texto va dibujado en el gráfico. Las series salen del terminal "
           "(`scripts/serie_mt5.py`, `scripts/tradingview_grafico.py`), nunca a mano.", ""]

    citadas = editorial.get("cifras_citadas", {})
    if citadas:
        md += ["**Cifras del texto que no son del terminal**", ""]
        md += [f"- {cifra}: {motivo}" for cifra, motivo in citadas.items()]
        md.append("")

    usadas = [c["vision"] for c in editorial["paginas"].values() if c.get("vision")]
    if usadas:
        md += ["## Fuentes", "", "| Quién | Fecha | Fuente |", "| --- | --- | --- |"]
        for vid in dict.fromkeys(usadas):
            v = registro[vid]
            md.append(f"| {v['quien']}, {v['institucion']} | {v['fecha']} | [{v.get('fuente') or 'enlace'}]({v['url']}) |")
        md.append("")

    md += ["**Antes de publicar**", "",
           "- [ ] Si sale otro día, volver a preparar los datos.",
           "- [ ] Confirmar la frase textual de cada cita en su fuente.",
           "- [ ] Mirar el PDF final y verificar tildes, eñes, ¿ y ¡.", ""]
    return "\n".join(md)


_CSS = """
@page { size: A4; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #1d2a30; line-height: 1.45; }
h1 { font-size: 19pt; color: #0f3b40; border-bottom: 3px solid #50C0A8; padding-bottom: 6px; }
h2 { font-size: 14pt; color: #0f3b40; margin-top: 20px; border-left: 5px solid #50C0A8; padding-left: 8px; page-break-after: avoid; }
h3 { font-size: 11pt; color: #0f3b40; margin-bottom: 4px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 8.6pt; page-break-inside: avoid; }
th { background: #0f3b40; color: #fff; text-align: left; padding: 4px 6px; }
td { border-bottom: 1px solid #d5dfe0; padding: 4px 6px; vertical-align: top; }
blockquote { background: #eef7f5; border-left: 4px solid #50C0A8; margin: 8px 0; padding: 6px 12px; page-break-inside: avoid; }
hr { border: none; page-break-after: always; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #f1f4f5; padding: 0 3px; }
li { margin: 2px 0; }
"""


_INICIO_LISTA = ("- ", "|", "1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ", "9. ")


def normalizar_markdown(texto: str) -> str:
    """Corrige lo que el markdown escrito a mano rompe al convertirse.

    Dos defectos medidos el 2026-09-28 en el primer PDF: una lista pegada a la
    línea anterior (`**Pág. 1**` y en la siguiente `- Titular`) sale como un solo
    párrafo, y una línea de cita que empieza con `#` (`> #Inversiones`) sale como
    título gigante. Un brief ilegible llega a diseño igual.
    """
    lineas: list[str] = []
    for linea in texto.splitlines():
        if linea.startswith("  - "):
            linea = "    " + linea[2:]
        if linea.startswith("> #"):
            linea = "> \\#" + linea[3:]
        limpia = linea.strip()
        if lineas and limpia.startswith(_INICIO_LISTA) and not linea.startswith("    "):
            previa = lineas[-1].strip()
            # También cuando cambia el tipo de lista: un "1." pegado a una lista
            # de "-" se lee como continuación del último punto.
            cambia_tipo = previa.startswith("- ") != limpia.startswith("- ")
            if previa and (not previa.startswith(_INICIO_LISTA) or cambia_tipo):
                lineas.append("")
        lineas.append(linea)
    return "\n".join(lineas)


def brief_a_pdf(markdown_texto: str, destino: Path, titulo: str) -> None:
    """Markdown → HTML → PDF con el Chromium de Playwright, que dibuja tildes y emoji."""
    import markdown
    from playwright.sync_api import sync_playwright

    cuerpo = markdown.markdown(normalizar_markdown(markdown_texto),
                               extensions=["tables", "sane_lists"]).replace("[ ]", "☐")
    html = (f"<!doctype html><html lang='es'><head><meta charset='utf-8'><style>{_CSS}</style>"
            f"</head><body>{cuerpo}</body></html>")
    pie = ("<div style='font-size:8px;width:100%;text-align:center;color:#777'>Grupo Inteligencia · "
           f"{titulo} · <span class='pageNumber'></span>/<span class='totalPages'></span></div>")
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page()
        pagina.set_content(html, wait_until="load")
        pagina.pdf(path=str(destino), format="A4", print_background=True,
                   display_header_footer=True, header_template="<span></span>", footer_template=pie,
                   margin={"top": "16mm", "bottom": "18mm", "left": "14mm", "right": "14mm"})
        navegador.close()


def rendir(directorio: Path, aceptar_datos_viejos: bool = False, sin_pdf: bool = False) -> Path:
    ruta = directorio / "payload.json"
    payload = json.loads(ruta.read_text(encoding="utf-8"))
    registro = cargar_visiones()
    errores = validar(payload, registro, datetime.now(SANTIAGO), aceptar_datos_viejos)
    if errores:
        raise SystemExit(
            "El brief no sale. Un carrusel a medias o con una cifra sin respaldo llega "
            "publicado igual:\n  " + "\n  ".join(errores)
        )
    payload.pop("_pendiente_editorial", None)
    ruta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    texto = construir_brief(payload, registro)
    md = directorio / "brief.md"
    md.write_text(texto, encoding="utf-8")
    if sin_pdf:
        return md
    pdf = directorio / "brief.pdf"
    brief_a_pdf(texto, pdf, f"Carrusel LinkedIn {directorio.name}")
    return pdf


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--preparar", action="store_true", help="lee el terminal y deja el payload con los huecos editoriales")
    modo.add_argument("--rendir", type=Path, metavar="DIR", help="valida el payload y produce brief.md y brief.pdf")
    modo.add_argument("--validar", type=Path, metavar="DIR", help="solo informa qué falta, no escribe nada")
    parser.add_argument("--formato", choices=sorted(FORMATOS))
    parser.add_argument("--activos", help="tickers del catálogo separados por coma (el primero es el principal)")
    parser.add_argument("--principal", help="activo protagonista, si no es el primero de --activos")
    parser.add_argument("--aceptar-datos-viejos", action="store_true",
                        help="rinde con datos de más de 24 h; el brief lo dice igual")
    parser.add_argument("--sin-pdf", action="store_true", help="solo brief.md")
    args = parser.parse_args(argv)

    if args.preparar:
        if not args.formato or not args.activos:
            parser.error("--preparar necesita --formato y --activos")
        tickers = [t.strip() for t in args.activos.split(",") if t.strip()]
        print(preparar(args.formato, tickers, args.principal))
        return 0
    if args.validar:
        payload = json.loads((args.validar / "payload.json").read_text(encoding="utf-8"))
        errores = validar(payload, cargar_visiones(), datetime.now(SANTIAGO), args.aceptar_datos_viejos)
        print("\n".join(errores) if errores else "ok: el brief puede salir")
        return 1 if errores else 0
    print(rendir(args.rendir, args.aceptar_datos_viejos, args.sin_pdf))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
