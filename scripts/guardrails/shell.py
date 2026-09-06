"""Las tres formas en que la consola de PowerShell rompe texto de cliente.

Las tres están medidas y las tres llegaron al canal. No son teóricas:

1. **El `$` se come el precio.** Dentro de comillas dobles o de un here-string
   `@"..."@`, PowerShell interpreta `$931` como la variable `$9` seguida de `31`.
   La variable no existe, expande a vacío, y el precio **desaparece** del mensaje.
   El here-string de comillas simples `@'...'@` es literal y es la salida correcta.
2. **La codificación se come las tildes.** `Set-Content` y `Out-File` escriben en
   la codificación ANSI del sistema salvo que se les diga otra cosa, así que la
   pieza se publica con `AN?LISIS` e `inversi?n`.
3. **La tubería se come los acentos entre etapas.** Encadenar dos scripts con `|`
   convierte los bytes en strings con `$OutputEncoding` en US-ASCII.

Lo que las tres comparten es el motivo por el que hace falta un guardia y no basta
la regla escrita: **el resultado se lee como correcto desde afuera**. Un mensaje al
que le falta el precio no se ve incompleto, tiene un espacio donde iba la cifra.

El módulo se calibró tanto por lo que NO tiene que detener como por lo que sí. Un
guardia que grita sobre un `| head -5` se apaga a la semana, y entonces no protege
de nada: los falsos positivos son la vía por la que estos sistemas mueren.
"""

from __future__ import annotations

import re

from .veredicto import Veredicto, aprueba, falla, primer_fallo

# `$` seguido de dígito. No hace falta más: no existe una variable de PowerShell
# que empiece con un número, así que todo `$<dígito>` dentro de comillas dobles es
# un precio que se va a perder.
_DOLAR_CIFRA = re.compile(r"\$\d")

# Un here-string de comillas dobles, y una cadena de comillas dobles corriente.
# El de comillas simples (`@'...'@`) no está acá a propósito: es literal.
_HERE_DOBLE = re.compile(r'@"(.*?)"@', re.DOTALL)
_CADENA_DOBLE = re.compile(r'"([^"\n]*)"')

# Los comandos que escriben un archivo desde la consola.
_ESCRITORES = re.compile(
    r"\b(Set-Content|Add-Content|Out-File)\b|(?<![|>])>{1,2}(?!\s*[&|])",
    re.IGNORECASE,
)
_ENCODING_UTF8 = re.compile(r"-Encoding\s+utf-?8(bom)?\b", re.IGNORECASE)

# Las carpetas donde vive el texto que lee un cliente. La lista es corta a
# propósito: `data/logs/` o un `.json` de trabajo pueden salir en ANSI sin que
# nadie se entere ni le importe.
_RUTAS_DE_CLIENTE = ("data/mensajes", r"data\mensajes", "data/stories", r"data\stories",
                     "templates/stories", r"templates\stories")

# Los scripts que se pasan datos entre sí. Encadenar DOS de estos con `|` es un
# puente de datos; uno solo seguido de `head` o `jq` es inspección.
_ETAPAS = ("serie_mt5", "story_grafico", "story_render", "pipeline_carrusel",
           "pipeline_informe", "generar_pdf")


def sin_here_string_peligroso(comando: str) -> Veredicto:
    """Prohíbe el `$` seguido de dígito dentro de comillas dobles."""
    for patron in (_HERE_DOBLE, _CADENA_DOBLE):
        for m in patron.finditer(comando or ""):
            if _DOLAR_CIFRA.search(m.group(1)):
                trozo = _DOLAR_CIFRA.search(m.group(1)).group(0)
                return falla(
                    "here_string_trunca_precio",
                    f"El texto trae {trozo!r} dentro de comillas dobles: PowerShell lo "
                    "lee como variable y el precio sale vacío. Usá un here-string de "
                    "comillas simples (@'...'@) o escribí el archivo desde Python.",
                    ubicacion=trozo,
                )
    return aprueba()


def sin_escritura_de_texto_por_consola(comando: str) -> Veredicto:
    """Prohíbe escribir texto de cliente sin declarar UTF-8.

    Solo mira las rutas de cliente. Cualquier otra escritura puede salir en ANSI
    sin consecuencias, y hacerla fallar sería la fricción que apaga el guardia.
    """
    texto = comando or ""
    ruta = next((r for r in _RUTAS_DE_CLIENTE if r in texto), None)
    if ruta is None:
        return aprueba()
    if not _ESCRITORES.search(texto):
        return aprueba()
    if _ENCODING_UTF8.search(texto):
        return aprueba()
    return falla(
        "escritura_por_consola",
        "Escritura de texto de cliente desde la consola sin `-Encoding utf8`: la "
        "codificación ANSI convierte tildes y eñes en `?`. Escribilo desde Python "
        "con encoding='utf-8'.",
        ubicacion=ruta,
    )


def sin_pipeline_encadenado(comando: str) -> Veredicto:
    """Prohíbe encadenar dos etapas del pipeline de piezas con `|`."""
    texto = comando or ""
    if "|" not in texto:
        return aprueba()
    tramos = texto.split("|")
    con_etapa = [t for t in tramos if any(e in t for e in _ETAPAS)]
    if len(con_etapa) < 2:
        return aprueba()
    return falla(
        "pipeline_encadenado",
        "Dos etapas del pipeline encadenadas con `|`: $OutputEncoding en US-ASCII "
        "rompe los acentos entre una y otra. El puente va en Python, con subprocess "
        "en binario.",
        ubicacion=" | ".join(t.strip()[:30] for t in con_etapa[:2]),
    )


def revisar(comando: str) -> Veredicto:
    """Las tres comprobaciones, cortocircuitando en la primera que falle."""
    return primer_fallo([
        sin_here_string_peligroso(comando),
        sin_escritura_de_texto_por_consola(comando),
        sin_pipeline_encadenado(comando),
    ])
