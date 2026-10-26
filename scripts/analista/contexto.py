"""La pieza de contexto: preparar, depurar, sustituir marcas y tarjetas.

Entrega tres mensajes de WhatsApp independientes (Noticia 1, Noticia 2 y Análisis técnico)
asociados a un seguimiento. Python prepara las noticias candidatas y los datos del terminal;
agy redacta los textos con marcas; Python depura, reemplaza marcas por precios y arma las tarjetas.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from analista import esquema as es
from analista import fuentes as fu
from analista import noticia as nt
from analista import noticias_contexto as nctx
from analista import preparar as pr
from analista import seguimiento as sg

MARCAS: dict[str, str] = {
    "[[NIVEL]]": "nivel",
    "[[OBJETIVO]]": "objetivo",
    "[[SIGUIENTE]]": "siguiente",
}


@dataclass
class Tarjeta:
    """Un mensaje listo para copiar. `texto` es el mensaje entero; `cuerpo`, `pregunta` y `pie` son sus partes,
    para que el ejecutivo meta su comentario entre la noticia y la pregunta con que cierra."""
    titulo: str
    texto: str | None
    motivo: str = ""
    medio: str = ""
    fecha: str = ""
    url: str = ""
    cuerpo: str = ""
    pregunta: str = ""
    pie: str = ""


# Palabras con que agy abre el mensaje después del saludo. Tras «Hola Juan,» van en minúscula; un nombre
# propio («FXStreet», «Powell») no está acá y conserva su mayúscula.
_MINUSCULA_TRAS_SALUDO = frozenset("""
    a al ante aunque ayer como con de del desde durante el en entre esta este esto hoy la las lo los mientras
    mira nuestra nuestro para por quería quiero se según si sin sobre su sus te tras un una ya
    mantenemos vigilamos seguimos tenemos comparto
""".split())


def preparar(
    ticker: str,
    dir_pedido: Path,
    ahora: datetime,
    seg: dict[str, Any],
    candidatas: Callable[[str, str, datetime], tuple[list[dict[str, Any]], list[str]]] = nctx.candidatas,
) -> pr.Preparada:
    """Prepara la pieza de contexto sellando candidatas, hechos técnicos y huecos editoriales.

    `seg` son los `datos` de la pieza de seguimiento.
    """
    dir_pedido.mkdir(parents=True, exist_ok=True)
    activo = seg.get("activo") or {}
    nombre = seg.get("nombre") or activo.get("nombre", ticker)
    digits = int(activo.get("digits", 2))
    suceso = seg.get("suceso") or {}

    cand_lista, avisos = candidatas(ticker, nombre, ahora)

    tecnico_datos = {
        "nombre": nombre,
        "sentido": suceso.get("sentido"),
        "estado": suceso.get("estado"),
        "nivel": suceso.get("nivel"),
        "objetivo": suceso.get("objetivo"),
        "siguiente": suceso.get("siguiente"),
        "calidad": suceso.get("calidad", ""),
        "digits": digits,
    }

    estado = suceso.get("estado")
    if estado == "cerrado":
        tecnico_motivo = "El mercado está cerrado."
    elif estado == "sin_direccion":
        tecnico_motivo = "Hoy la lectura técnica no marca dirección clara."
    else:
        tecnico_motivo = ""

    datos = {
        "ticker": ticker,
        "nombre": nombre,
        "noticias_candidatas": cand_lista,
        "tecnico": tecnico_datos,
        "tecnico_motivo": tecnico_motivo,
    }

    pieza = es.nueva_pieza("contexto", {"ticker": ticker}, datos, {})
    editorial = pieza["editorial"]

    if not cand_lista:
        editorial["noticia_1"] = None
        editorial["noticia_2"] = None

    if estado in ("sin_direccion", "cerrado"):
        editorial["tecnico"] = None

    pieza["huella"] = es._huella(pieza)
    pr.guardar_pieza(pieza, dir_pedido)
    return pr.Preparada(pieza, avisos)


def depurar(
    pieza: dict[str, Any],
    hoy: date,
    lista: dict[str, Any] | None = None,
    verificar: Callable[[str], str] = fu.verificar_url,
    leer: Callable[[str], str | None] = nt.leer_texto,
) -> tuple[dict[str, Any], list[str]]:
    """Deja cada campo de editorial válido o en None, y guarda los motivos en pieza['motivos'].

    Reglas en orden:
    1. Un campo en es.MARCA pasa a None con su motivo.
    2. La URL de una noticia debe estar en datos.noticias_candidatas y su titular original coincidir.
    3. La noticia 2 cae si repite la URL de la 1.
    4. Cada noticia pasa por noticia.motivo_de_contexto.
    5. tecnico: debe empezar con [[SALUDO]], sin números significativos fuera de marcas,
       y solo marcas con valor no nulo en datos.tecnico.
    """
    editorial = pieza.get("editorial", {})
    datos = pieza.get("datos", {})
    candidatas = datos.get("noticias_candidatas") or []
    tecnico_datos = datos.get("tecnico") or {}
    motivos: dict[str, str] = {}
    avisos: list[str] = []

    # Regla 1: Un campo en es.MARCA pasa a None con su motivo.
    for campo in ("noticia_1", "noticia_2", "tecnico"):
        if editorial.get(campo) == es.MARCA:
            editorial[campo] = None
            motivos[campo] = "No alcancé a redactar este mensaje: vuelve a pedir el contexto."

    lista = lista or fu.cargar_lista()
    verificar_fn = fu._con_lista(verificar, lista)

    for campo in ("noticia_1", "noticia_2"):
        n = editorial.get(campo)
        if n is None:
            if campo not in motivos:
                motivos[campo] = _sin_noticia(campo, datos)
            continue
        if not isinstance(n, dict):
            editorial[campo] = None
            motivos[campo] = "la noticia debe ser un objeto"
            continue

        # Regla 2: URL debe estar en candidatas y titular_original coincidir
        cand = next((c for c in candidatas if c.get("url") == n.get("url")), None)
        if cand is None:
            editorial[campo] = None
            motivos[campo] = "la URL no está en las noticias candidatas"
            continue
        if cand.get("titular_original") != n.get("titular_original"):
            editorial[campo] = None
            motivos[campo] = "el titular original no coincide con el de la candidata"
            continue

        # Regla 3: noticia 2 cae si repite la URL de la 1
        if campo == "noticia_2":
            n1 = editorial.get("noticia_1")
            url_1 = n1.get("url") if isinstance(n1, dict) else None
            if url_1 and n.get("url") == url_1:
                editorial["noticia_2"] = None
                motivos["noticia_2"] = "repite la URL de la primera noticia"
                continue

        # Regla 4: cada noticia pasa por motivo_de_contexto
        mot = nt.motivo_de_contexto(n, hoy, lista, verificar_fn, leer)
        if mot:
            editorial[campo] = None
            motivos[campo] = mot
            avisos.append(f"{campo}: {mot}")
            continue

        editorial[campo] = {c: str(n.get(c, "")).strip() for c in nt.CAMPOS_CONTEXTO}

    # Regla 5: técnico
    t_texto = editorial.get("tecnico")
    if t_texto is None:
        if "tecnico" not in motivos:
            motivos["tecnico"] = datos.get("tecnico_motivo") or "sin análisis técnico"
    elif not isinstance(t_texto, str):
        editorial["tecnico"] = None
        motivos["tecnico"] = "el texto técnico debe ser un string"
    else:
        t_strip = t_texto.strip()
        if not t_strip.startswith(sg.MARCA_SALUDO):
            editorial["tecnico"] = None
            motivos["tecnico"] = f"el texto técnico debe empezar con {sg.MARCA_SALUDO}"
        else:
            # Sin números significativos fuera de marcas
            texto_sin_marcas = t_strip
            for m in MARCAS:
                texto_sin_marcas = texto_sin_marcas.replace(m, " ")
            texto_sin_marcas = texto_sin_marcas.replace(sg.MARCA_SALUDO, " ")

            numeros = es._NUMERO.findall(texto_sin_marcas)
            significativos = [num for num in numeros if es._significativo(num)]
            if significativos:
                editorial["tecnico"] = None
                motivos["tecnico"] = f"trae un precio o cifra escrita ({', '.join(significativos)})"
            else:
                # Solo marcas con valor no nulo en datos.tecnico
                marcas_invalidas = [
                    m for m, clave in MARCAS.items()
                    if m in t_strip and tecnico_datos.get(clave) is None
                ]
                if marcas_invalidas:
                    editorial["tecnico"] = None
                    motivos["tecnico"] = f"usa la marca {', '.join(marcas_invalidas)} sin valor en los datos"
                else:
                    errs = es._errores_de_texto("tecnico", t_strip, "contexto", datos, cifras=False)
                    if errs:
                        editorial["tecnico"] = None
                        motivos["tecnico"] = errs[0].split(": ", 1)[-1]
                    else:
                        editorial["tecnico"] = t_strip

    pieza["motivos"] = motivos
    return pieza, avisos


def _sin_noticia(campo: str, datos: dict[str, Any]) -> str:
    """Por qué la tarjeta de noticia sale vacía, en palabras del ejecutivo (lo lee él, no el cliente)."""
    _, del_activo = sg._activo_con_articulo(datos.get("nombre") or datos.get("ticker", ""))
    if not datos.get("noticias_candidatas"):
        return f"Hoy no encontré noticias {del_activo} en FXStreet ni en Investing.com."
    otra = "otra noticia" if campo == "noticia_2" else "ninguna de las noticias"
    return f"No hay {otra} de los últimos {nt.VENTANA_DIAS} días que trate {del_activo}."


def _con_saludo(texto: str, saludo: str) -> str:
    """El saludo del ejecutivo, y la palabra que lo sigue en minúscula si el saludo cierra con coma.

    agy escribe la frase como si empezara sola («Según FXStreet…»), y quedaba «Hola, Según FXStreet».
    """
    resto = texto.strip()
    if resto.startswith(sg.MARCA_SALUDO):
        resto = resto[len(sg.MARCA_SALUDO):].lstrip()
        abre = sg.saludo_de(saludo)
        palabra = resto.split(" ", 1)[0]
        if abre.endswith(",") and palabra.lower().strip(",:;") in _MINUSCULA_TRAS_SALUDO:
            resto = resto[0].lower() + resto[1:]
        return f"{abre} {resto}"
    return sg.con_saludo(resto, saludo)


def _partes(texto: str) -> tuple[str, str]:
    """(cuerpo, pregunta): la pregunta con que cierra el mensaje, si cierra con una."""
    inicio = texto.rfind("¿")
    if not texto.rstrip().endswith("?") or inicio <= 0:
        return texto, ""
    return texto[:inicio].rstrip(), texto[inicio:].strip()


def _tarjeta(titulo: str, texto: str, pie: str = "", **meta: str) -> Tarjeta:
    cuerpo, pregunta = _partes(texto)
    completo = f"{texto}\n\n{pie}" if pie else texto
    return Tarjeta(titulo=titulo, texto=completo, cuerpo=cuerpo, pregunta=pregunta, pie=pie, **meta)


def sustituir_marcas(texto: str, tecnico: dict[str, Any]) -> str:
    """Reemplaza cada marca con seguimiento._fmt(valor, tecnico['digits'])."""
    digits = int(tecnico.get("digits", 2))
    salida = texto
    for marca, clave in MARCAS.items():
        valor = tecnico.get(clave)
        if valor is not None:
            fmt_valor = sg._fmt(float(valor), digits)
            salida = salida.replace(marca, fmt_valor)
    return salida


def _formato_dd_mm(fecha_str: str) -> str:
    """Convierte AAAA-MM-DD a dd-mm."""
    try:
        f = date.fromisoformat(fecha_str)
        return f"{f.day:02d}-{f.month:02d}"
    except (ValueError, TypeError):
        partes = str(fecha_str).split("-")
        if len(partes) == 3:
            return f"{partes[2]}-{partes[1]}"
        return fecha_str


def tarjetas(pieza: dict[str, Any], saludo: str = "") -> list[Tarjeta]:
    """Genera las tres tarjetas (Noticia 1, Noticia 2, Análisis técnico).

    El texto final aplica con_saludo; en las noticias agrega al final una línea
    'Fuente: <medio>, <dd-mm>'; en el técnico aplica sustituir_marcas.
    Una tarjeta vacía lleva texto=None y su motivo.
    """
    editorial = pieza.get("editorial", {})
    datos = pieza.get("datos", {})
    motivos = pieza.get("motivos", {})
    tecnico_datos = datos.get("tecnico", {})

    salida: list[Tarjeta] = []

    for campo, titulo in (("noticia_1", "Noticia 1"), ("noticia_2", "Noticia 2")):
        n = editorial.get(campo)
        if isinstance(n, dict):
            medio = n.get("medio", "")
            pie = f"Fuente: {medio}, {_formato_dd_mm(n.get('fecha', ''))}"
            salida.append(_tarjeta(titulo, _con_saludo(n.get("mensaje", ""), saludo), pie,
                                   medio=medio, fecha=n.get("fecha", ""), url=n.get("url", "")))
        else:
            salida.append(Tarjeta(titulo=titulo, texto=None, motivo=motivos.get(campo, "")))

    tec_txt = editorial.get("tecnico")
    if isinstance(tec_txt, str):
        con_precios = sustituir_marcas(tec_txt, tecnico_datos)
        salida.append(_tarjeta("Análisis técnico", _con_saludo(con_precios, saludo)))
    else:
        salida.append(Tarjeta(titulo="Análisis técnico", texto=None, motivo=motivos.get("tecnico", "")))

    return salida
