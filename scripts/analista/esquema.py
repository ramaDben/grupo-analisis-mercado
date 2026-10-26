"""La pieza que agy rellena: datos del terminal congelados y huecos de texto.

`pieza.json` tiene cuatro partes: `orden` (qué se pidió), `datos` (lo que salió
del terminal y del calendario), `imagenes` (los PNG de WhatsApp ya rendidos) y
`editorial` (los únicos campos que agy escribe). Las tres primeras van selladas
con una huella: si agy las toca, la pieza no sale.

agy no decide la maqueta. Por eso el texto no puede traer HTML, y por la Regla 1
tampoco cifras que no estén en `datos`: un número inventado en un párrafo es un
precio escrito a mano, aunque lo haya escrito un modelo.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

from pipeline_linkedin import MARCA_EDITORIAL as MARCA
from pipeline_linkedin import validar_textos

from analista import fuentes as fu

# Campos de texto plano por pieza. Los que dependen de los datos (un titular y un
# contexto por activo) se declaran al preparar, en `anidados`.
CAMPOS: dict[str, tuple[str, ...]] = {
    # El análisis de un activo: portada, un titular y un contexto anidados por activo, y las voces
    # de bancos y prensa que agy encontró en la web (lista de objetos, ver `fuentes.py`).
    # `noticia` es la noticia de apertura del correo (spec 2026-10-24): un objeto que valida y depura
    # `noticia.py`, opcional (una pieza anterior no la trae) y que puede quedar en `None`.
    "oportunidad": ("titular", "bajada", "fuentes", "noticia"),
    # El seguimiento no pasa por agy, pero su `pieza.json` usa el mismo sello.
    "seguimiento": (),
    # Tres mensajes independientes con noticias y análisis técnico para abrir conversación.
    "contexto": ("noticia_1", "noticia_2", "tecnico"),
}

# Campos que una pieza puede no traer: las anteriores al spec 2026-10-24 no tienen noticia,
# y la pieza contexto admite dejar tarjetas en None cuando no hay material.
OPCIONALES: tuple[str, ...] = ("noticia", "noticia_1", "noticia_2", "tecnico")

# El titular y la bajada también van impresos dentro de las láminas de WhatsApp,
# que tienen el espacio medido: un titular largo se corta en la imagen.
LARGO_MAXIMO = {"titular": 70, "bajada": 160}
LARGO_MAXIMO_ANIDADO = {"titulares": 70, "dias_clave": 420}
# El contexto nombra el estado real de al menos dos drivers medidos (o del único que haya), con su
# cifra tal como viene en `datos.hechos` (spec 2026-10-17 §5). La corrida del oro del 17/10 pasaba
# todos los controles sin una sola cifra: el validador prohibía inventar, pero no exigía citar.
MINIMO_HECHOS = 2

# El informe es análisis general: nadie en GI está inscrito como asesor de
# inversión. Se prohíben FRASES y no palabras sueltas, porque "compra" o
# "entrar" aparecen en texto legítimo ("gerentes de compra (PMI)", "vuelve a
# entrar") y un candado que bloquea eso termina desactivado. Se comparan sin
# tildes y en minúsculas; las que van en `_PALABRA_EXACTA` exigen borde al final
# ("lote" no puede atrapar "lotería"), el resto también atrapa sus derivadas.
FRASES_PROHIBIDAS: tuple[str, ...] = (
    "compra ya", "vende ya", "es momento de comprar", "es momento de vender",
    "entra al mercado", "abre una posicion", "cierra tu posicion", "toma ganancias",
    "debes comprar", "debes vender", "deberias comprar", "deberias vender",
    "recomendamos", "te recomiendo", "te conviene", "senal de compra", "senal de venta",
    # Riesgo y apalancamiento solo en su forma de instrucción: "el apalancamiento
    # amplifica las pérdidas" o "no conviene arriesgar más de lo previsto" son la
    # advertencia natural de "Qué NO hacer" y tienen que pasar.
    "lote", "lotes", "de tu capital", "arriesga tu", "arriesga el", "arriesga un",
    "apalancate", "usa apalancamiento",
)
# Lo que le resta crédito al dato que se cita (correo de Caterpillar, 2026-10-26: "resultados previstos
# para el jueves según datos de mercado no oficiales"). Un dato sin fuente que se pueda nombrar no va.
FRASES_SIN_FUENTE: tuple[str, ...] = ("no oficial", "según fuentes de mercado")
_PALABRA_EXACTA = {"lote", "lotes"}

# La pieza semanal la comparte ventas con un prospecto: además no puede
# empujar a entrar ni hablar de cuánto acierta. La estadística se sacó de la
# pieza a propósito (sin su línea base, "53 %" insinúa una ventaja que no hay),
# y un porcentaje en el texto la traería de vuelta por la puerta de atrás.
FRASES_PROHIBIDAS_SEMANAL: tuple[str, ...] = (
    "no te lo pierdas", "oportunidad", "aprovecha", "asegurad", "ganancia segura",
    "acierta", "efectividad", "de las veces", "tasa de exito",
)

# El informe no nombra a la CMF (decisión del director, 2026-10-08), tampoco en
# el texto de agy.
_CMF = re.compile(r"\bcmf\b", re.IGNORECASE)

_HTML = re.compile(r"<\s*[a-zA-Z/!]")
_NUMERO = re.compile(r"\d[\d.,]*\d|\d")


def _plano(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


# La pieza no invita a operar: por regulación invita a revisar la plataforma (director, 2026-10-16).
# Reemplaza la regla del 2026-10-12, que exigía invitar a operar el escenario.
_OPERAR = re.compile(r"\bopera(s|r|rlo|rla|rse|ble|bles|mos)?\b|\boperes\b")
# Tampoco invita a comprar, vender ni entrar (fix final 2026-10-17). Acotado al infinitivo, sus
# formas con objeto y «puede/conviene + verbo»: "gerentes de compra", "presión compradora", "los
# vendedores" o "entra en vigor" son texto legítimo y no caen.
_INVITACION = re.compile(r"\b(comprar|comprarlo|comprarla|vender|venderlo|venderla|entrar|aprovech\w*)\b"
                         r"|\b(puede|pueden|conviene)\s+(comprar|vender)")


def frases_prohibidas(texto: str, frases: tuple[str, ...] = FRASES_PROHIBIDAS) -> list[str]:
    """Las frases de instrucción o recomendación que trae `texto`."""
    plano = _plano(texto)
    return [
        f for f in frases
        if re.search(rf"\b{re.escape(f)}" + (r"\b" if f in _PALABRA_EXACTA else ""), plano)
    ]


def _huella(pieza: dict[str, Any]) -> str:
    sellado = {k: pieza.get(k) for k in ("orden", "datos", "imagenes", "anidados", "laminas")}
    crudo = json.dumps(sellado, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def nueva_pieza(
    pieza: str,
    args: dict[str, Any],
    datos: dict[str, Any],
    imagenes: dict[str, str],
    extra_campos: dict[str, list[str]] | None = None,
    laminas: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Pieza recién preparada: todo sellado y cada campo editorial sin escribir.

    `laminas` son las imágenes de WhatsApp que llevan texto adentro (la agenda
    del día): se guardan como payload y se rinden después de validar el texto.
    """
    anidados = {campo: [str(i) for i in ids] for campo, ids in (extra_campos or {}).items()}
    editorial: dict[str, Any] = {campo: MARCA for campo in CAMPOS[pieza]}
    for campo, ids in anidados.items():
        editorial[campo] = {i: MARCA for i in ids}
    p = {
        "orden": {"pieza": pieza, "args": args},
        "datos": datos,
        "imagenes": imagenes,
        "anidados": anidados,
        "laminas": laminas or {},
        "editorial": editorial,
    }
    p["huella"] = _huella(p)
    return p


def textos(pieza: dict[str, Any]) -> list[tuple[str, str]]:
    salida: list[tuple[str, str]] = []
    for campo, valor in pieza.get("editorial", {}).items():
        if campo in OPCIONALES:  # la noticia tiene sus propios controles (`noticia.py`)
            continue
        if isinstance(valor, dict):
            salida.extend((f"{campo}.{k}", str(v)) for k, v in valor.items())
        elif isinstance(valor, list):  # `fuentes`: solo la tesis es texto de agy; lo demás lo valida `fuentes.py`
            salida.extend((f"{campo}.{i}.tesis", str(f.get("tesis", ""))) for i, f in enumerate(valor)
                          if isinstance(f, dict))
        else:
            salida.append((campo, str(valor)))
    return salida


def _plano_numero(token: str) -> str:
    return token.replace(".", "").replace(",", "")


def _significativo(token: str) -> bool:
    return any(c in token for c in ".,") or len(token) >= 3


def cifras_ajenas(texto: str, datos: Any, fuentes: list[dict[str, Any]] | tuple = ()) -> list[str]:
    """Las cifras del texto que no están en `datos`.

    Única excepción (spec 2026-10-16 §7): la cifra de un tercero que aparece en la `tesis` de una
    fuente validada y se atribuye a ella en la misma frase («Goldman Sachs ve el oro en 4.800»).
    """
    volcado = json.dumps(datos, ensure_ascii=False)
    permitidas = {_plano_numero(t) for t in _NUMERO.findall(volcado)}
    ajenas: list[str] = []
    for frase in re.split(r"(?<=[.!?])\s+|\n+", texto):
        plano = _plano(frase)
        de_terceros = {_plano_numero(t) for f in fuentes
                       if re.search(rf"\b{re.escape(_plano(f['entidad']))}\b", plano)
                       for t in _NUMERO.findall(f["tesis"])}
        ajenas += [t for t in _NUMERO.findall(frase)
                   if _significativo(t) and _plano_numero(t) not in permitidas
                   and _plano_numero(t) not in de_terceros]
    return ajenas


def hechos_citados(texto: str, hechos: list[dict[str, Any]]) -> list[str]:
    """Los `id` de los hechos medidos cuya cifra (nivel o cambio) aparece en el texto.

    Solo cuentan las cifras significativas del propio hecho: citar el precio del activo u otra cifra
    de `datos` no cumple, y "14 pb" (dos dígitos) no alcanza a distinguirse de una fecha.
    """
    del_texto = {_plano_numero(t) for t in _NUMERO.findall(texto) if _significativo(t)}
    citados: list[str] = []
    for h in hechos:
        propias = {_plano_numero(t) for campo in ("nivel", "cambio_1d", "cambio_5d")
                   for t in _NUMERO.findall(str(h.get(campo) or "")) if _significativo(t)}
        if propias & del_texto:
            citados.append(str(h.get("id")))
    return citados


def _errores_de_desarrollo(pieza: dict[str, Any]) -> list[str]:
    """El contexto cita los hechos del día y los días clave nombran un día de la agenda."""
    datos = pieza.get("datos") or {}
    editorial = pieza.get("editorial") or {}
    errs: list[str] = []
    hechos = [h for h in datos.get("hechos") or [] if isinstance(h, dict)]
    # Un hecho sin cifra significativa propia (todo de un dígito) no se puede citar: no cuenta.
    citables = [h for h in hechos if any(_significativo(t) for campo in ("nivel", "cambio_1d", "cambio_5d")
                                         for t in _NUMERO.findall(str(h.get(campo) or "")))]
    exigidos = min(MINIMO_HECHOS, len(citables))
    contexto = editorial.get("contexto")
    for t, texto in (contexto.items() if isinstance(contexto, dict) else []):
        if exigidos and texto != MARCA and len(hechos_citados(str(texto), citables)) < exigidos:
            ejemplos = ", ".join(f"{h.get('driver')} {h.get('nivel')}" for h in hechos[:4])
            errs.append(f"contexto.{t}: tiene que nombrar el estado de hoy de al menos {exigidos} de los drivers "
                        f"medidos (datos.hechos), citando su cifra tal como viene: {ejemplos}")
    # El correo muestra solo 2 drivers (director, 2026-10-19): el texto no puede nombrar un tercero que la
    # tabla no tiene. Los 2 los elige la maqueta con una regla determinista; el import va adentro porque
    # oportunidad_html importa este módulo.
    if len(citables) > MINIMO_HECHOS:
        from analista import oportunidad_html as oh
        elegidos = oh.seleccionar_drivers_correo(hechos)[0]
        ids_ok = {str(h.get("id")) for h in elegidos}
        nombres = " y ".join(str(h.get("driver")) for h in elegidos)
        for t, texto in (contexto.items() if isinstance(contexto, dict) else []):
            if texto == MARCA:
                continue
            de_mas = [i for i in hechos_citados(str(texto), citables) if i not in ids_ok]
            if de_mas:
                errs.append(f"contexto.{t}: el correo muestra solo 2 drivers ({nombres}); quita la cifra de "
                            f"{', '.join(de_mas)} y deja el resto del texto")
    agenda = datos.get("agenda") if isinstance(datos.get("agenda"), dict) else {}
    dias = [str(e["dia"]) for e in agenda.get("eventos") or [] if isinstance(e, dict) and e.get("dia")]
    dias_clave = editorial.get("dias_clave")
    for t, texto in (dias_clave.items() if isinstance(dias_clave, dict) else []):
        if dias and texto != MARCA and not any(_plano(d) in _plano(str(texto)) for d in dias):
            errs.append(f"dias_clave.{t}: tiene que nombrar al menos un día de la agenda tal como viene en "
                        f"datos.agenda ({', '.join(dict.fromkeys(dias[:4]))})")
    return errs


def errores(pieza: dict[str, Any]) -> list[str]:
    """Todo lo que impide armar el HTML; lista vacía si la pieza puede salir."""
    errs: list[str] = []
    tipo = pieza.get("orden", {}).get("pieza")
    if tipo not in CAMPOS:
        return [f"pieza desconocida: {tipo!r}"]

    if pieza.get("huella") != _huella(pieza):
        errs.append("los datos, las imágenes o la orden cambiaron después de preparar: la pieza no es confiable")

    editorial = pieza.get("editorial", {})
    anidados = pieza.get("anidados", {})
    esperados = set(CAMPOS[tipo]) | set(anidados)
    for faltante in sorted(esperados - set(editorial) - set(OPCIONALES)):
        errs.append(f"{faltante}: falta el campo")
    for sobrante in sorted(set(editorial) - esperados):
        errs.append(f"{sobrante}: campo no previsto")
    for campo, ids in anidados.items():
        valor = editorial.get(campo)
        if not isinstance(valor, dict) or set(valor) != set(ids):
            errs.append(f"{campo}: tiene que traer exactamente {', '.join(ids) or 'ningún elemento'}")

    noticia = editorial.get("noticia")
    if tipo == "oportunidad" and noticia not in (None, MARCA) and not isinstance(noticia, dict):
        errs.append("noticia: tiene que ser un objeto o null")

    if tipo == "contexto":
        for campo in ("noticia_1", "noticia_2", "tecnico"):
            val = editorial.get(campo)
            if val == MARCA:
                errs.append(f"{campo}: quedó sin escribir")
            elif val is not None:
                if campo in ("noticia_1", "noticia_2") and not isinstance(val, dict):
                    errs.append(f"{campo}: tiene que ser un objeto o null")
                elif campo == "tecnico" and not isinstance(val, str):
                    errs.append(f"{campo}: tiene que ser un texto o null")

    fuentes = editorial.get("fuentes") if tipo == "oportunidad" else None
    if tipo == "oportunidad" and fuentes != MARCA:
        if not isinstance(fuentes, list):
            errs.append("fuentes: tiene que ser una lista (vacía si no hay voces atingentes)")
            fuentes = []
        else:
            for i, f in enumerate(fuentes):
                if not isinstance(f, dict) or any(not isinstance(f.get(c), str) or not f[c].strip() for c in fu.CAMPOS):
                    errs.append(f"fuentes.{i}: le faltan campos ({', '.join(fu.CAMPOS)})")
                elif f["postura"] not in fu.POSTURAS:
                    errs.append(f"fuentes.{i}: la postura {f['postura']!r} no es alcista, bajista ni neutral")
    fuentes_ok = [f for f in (fuentes or []) if isinstance(f, dict) and all(isinstance(f.get(c), str) for c in fu.CAMPOS)]
    if tipo == "oportunidad" and fuentes != MARCA:
        activos = (pieza.get("datos") or {}).get("activos") or [{}]
        direccion = (activos[0].get("lectura") or {}).get("direccion", "") if isinstance(activos[0], dict) else ""
        bs = fu.bancos(fuentes_ok)
        a_favor = [b for b in bs if not fu.discrepa(b, direccion)]
        en_contra = [b for b in bs if fu.discrepa(b, direccion)]
        if len(a_favor) > 1:
            errs.append("fuentes: máximo 1 banco a favor de nuestra lectura")
        if len(en_contra) > 1:
            errs.append("fuentes: máximo 1 banco en contra de nuestra lectura")

    pares = textos(pieza)
    for campo, tope in LARGO_MAXIMO.items():
        largo = len(str(editorial.get(campo, "")))
        if largo > tope:
            errs.append(f"{campo}: tiene {largo} caracteres y el máximo es {tope}")
    for campo, tope in LARGO_MAXIMO_ANIDADO.items():
        for clave, texto in (editorial.get(campo) or {}).items():
            if len(str(texto)) > tope:
                errs.append(f"{campo}.{clave}: tiene {len(str(texto))} caracteres y el máximo es {tope}")
    for donde, texto in pares:
        errs.extend(_errores_de_texto(donde, texto, tipo, pieza.get("datos"), fuentes_ok))
    if tipo == "oportunidad":
        errs.extend(_errores_de_desarrollo(pieza))
    return errs


def _errores_de_texto(donde: str, texto: str, tipo: str, datos: Any,
                      fuentes: list[dict[str, Any]] | tuple = (), cifras: bool = True,
                      porcentaje: bool = True) -> list[str]:
    """Los controles de texto de un campo. La `tesis` de una fuente no pasa por el de cifras:
    la cifra es del tercero citado. La noticia de apertura apaga el de cifras y el de `%`
    (`cifras=False, porcentaje=False`): sus cifras las contrasta `noticia.py` con la nota."""
    errs = list(validar_textos([(donde, texto)]))
    if _HTML.search(texto):
        errs.append(f"{donde}: trae HTML; la maqueta la pone la plantilla, no el texto")
    if _CMF.search(texto):
        errs.append(f"{donde}: nombra a la CMF, y el informe no la menciona")
    for frase in frases_prohibidas(texto):
        errs.append(f"{donde}: «{frase}» es una instrucción de operar o una recomendación; "
                    "el informe es análisis general")
    for frase in frases_prohibidas(texto, FRASES_SIN_FUENTE):
        errs.append(f"{donde}: «{frase}» le resta crédito al dato; si no tiene una fuente que se pueda "
                    "nombrar, no se cita")
    if tipo == "oportunidad":
        for frase in frases_prohibidas(texto, FRASES_PROHIBIDAS_SEMANAL):
            errs.append(f"{donde}: «{frase}» empuja a entrar o habla de cuánto acierta; "
                        "la pieza semanal describe un escenario")
        if porcentaje and "%" in texto:
            errs.append(f"{donde}: trae un porcentaje, y la pieza semanal no muestra ninguno")
        plano = _plano(texto)
        if _OPERAR.search(plano):
            errs.append(f"{donde}: invita a operar; por regulación la pieza invita a revisar la plataforma, "
                        "no a operar")
        m = _INVITACION.search(plano)
        if m:
            errs.append(f"{donde}: «{m.group(0)}» invita a comprar, vender o entrar; la pieza describe "
                        "un escenario, no invita a operar")
    if cifras and not donde.endswith(".tesis"):
        for cifra in cifras_ajenas(texto, datos, fuentes):
            errs.append(f"{donde}: la cifra {cifra} no está en los datos del terminal")
    return errs


def errores_tesis(tesis: str) -> list[str]:
    """Los controles de texto que rompe la `tesis` de una fuente (los mismos del resto de la pieza)."""
    return _errores_de_texto("fuentes.tesis", tesis, "oportunidad", None)


def errores_texto_noticia(donde: str, texto: str) -> list[str]:
    """Los controles de texto de la noticia de apertura, sin el de cifras ni el de `%` (spec 2026-10-24 §1)."""
    return _errores_de_texto(donde, texto, "oportunidad", None, cifras=False, porcentaje=False)


def descartar_tesis_rotas(pieza: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Saca de `editorial.fuentes` las voces cuya tesis rompe un control de texto, con su motivo.

    Un defecto en la paráfrasis de una sola fuente no bota la pieza entera (spec 2026-10-16 §9):
    esa voz se descarta y el análisis sigue, igual que una fuente que no pasa `fuentes.depurar`.
    """
    fuentes = pieza.get("editorial", {}).get("fuentes")
    if not isinstance(fuentes, list):
        return pieza, []
    quedan: list[Any] = []
    descartes: list[str] = []
    for f in fuentes:
        errs = errores_tesis(str(f.get("tesis", ""))) if isinstance(f, dict) else []
        if errs:
            motivo = errs[0].split(": ", 1)[-1]
            descartes.append(f"{f.get('entidad', 'una fuente')}: la tesis no pasó los controles de texto ({motivo})")
        else:
            quedan.append(f)
    pieza["editorial"]["fuentes"] = quedan
    return pieza, descartes
