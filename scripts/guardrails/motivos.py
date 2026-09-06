"""El catálogo de motivos: un slug, su frase y si se le puede contar al cliente.

Copia el patrón que ya funciona en `suplemento_canal.CATEGORIAS`, y por la misma
razón: **un problema nuestro de datos no es contenido para el cliente**. Esa
distinción ya está resuelta ahí; inventar una segunda sería el error recurrente
del repo.

El catálogo crece por fase. Hoy declara lo que emiten los cuatro módulos puros de
la fase 1. Los de `temporal`, `estado` y `despacho` se agregan cuando esos
módulos existan, no antes: un catálogo con entradas que nadie emite es una
promesa, y el test de contrato no puede distinguir una promesa de un olvido.

Qué impide el test `test_todo_motivo_tiene_entrada`: que el sistema rechace algo
y no sepa decir por qué. Lee los módulos con `ast`, junta cada slug literal que
le pasan a `falla()` y falla si alguno no está acá.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Motivo:
    texto: str
    publicable: bool


# `publicable` responde una sola pregunta: si esto se le puede decir al cliente
# como contenido. Casi todo lo de acá es `False`, y no por conservadurismo: son
# defectos de una pieza que todavía no salió. "No pudimos escribir bien el
# precio" no es una lectura de mercado, es una excusa. El campo existe igual
# porque el gate de despacho de la fase 3a sí va a emitir motivos publicables
# (mercado cerrado, recorrido agotado), y el contrato tiene que ser el mismo.
MOTIVOS: dict[str, Motivo] = {
    # --- texto_cliente.py -------------------------------------------------
    "guion_largo": Motivo(
        "El guion largo o medio como inciso delata redacción por IA, y la pieza "
        "va firmada por un analista real. Reescribir con punto, coma o dos puntos.",
        publicable=False,
    ),
    "sigla_sin_explicar": Motivo(
        "Una sigla aparece sin su explicación en voz novata. Va al diccionario "
        "rápido, o en línea dentro de la frase si la pieza es un pie de foto.",
        publicable=False,
    ),
    "tono_catastrofico": Motivo(
        "Lenguaje extremo o dramatizado. El énfasis direccional se permite y se "
        "busca; vaticinar catástrofes o atribuirle sensaciones al mercado, no.",
        publicable=False,
    ),
    "voseo": Motivo(
        "Voseo rioplatense en texto de cliente. El registro es tuteo chileno neutro.",
        publicable=False,
    ),
    "canal_inexistente": Motivo(
        "El texto nombra un canal que no existe en WhatsApp. Ya llegó a un grupo "
        "real una pieza preguntando qué significaba el dato para un canal que "
        "nadie puede abrir.",
        publicable=False,
    ),
    # --- precios.py -------------------------------------------------------
    "decimales_incorrectos": Motivo(
        "El precio no respeta los `digits` que el broker declara para ese activo. "
        "Nunca se truncan ceros al final ni se redondea a entero salvo digits = 0.",
        publicable=False,
    ),
    "precio_literal": Motivo(
        "Un precio escrito a mano en el código (Regla 1). Todo precio se lee en "
        "tiempo de ejecución desde MT5 o el MCP market-data.",
        publicable=False,
    ),
    # --- nombres.py -------------------------------------------------------
    "ticker_desconocido": Motivo(
        "El ticker no está en el catálogo de `config/activos.json`. Para símbolos "
        "con sufijo del broker hay que usar el exacto: `US100.spot`, no `US100`.",
        publicable=False,
    ),
    "marco_no_canonico": Motivo(
        "La temporalidad no es una de las cuatro etiquetas canónicas de "
        "`pipeline_carrusel.MARCOS_CANONICOS`.",
        publicable=False,
    ),
    "alias_de_canal_desconocido": Motivo(
        "El alias de canal no resuelve contra `config/whatsapp_grupos.json`.",
        publicable=False,
    ),
    # --- shell.py ---------------------------------------------------------
    "here_string_trunca_precio": Motivo(
        "Un here-string o una cadena con comillas dobles en PowerShell: `$931` se "
        "interpreta como variable vacía y el precio desaparece del mensaje.",
        publicable=False,
    ),
    "escritura_por_consola": Motivo(
        "Escritura de texto de cliente por la consola de PowerShell. La "
        "codificación ANSI por defecto convierte tildes y eñes en `?`. Va por "
        "Python con `encoding='utf-8'`, o por here-string de comillas simples.",
        publicable=False,
    ),
    "pipeline_encadenado": Motivo(
        "Comandos encadenados con `|`: `$OutputEncoding` en US-ASCII rompe los "
        "acentos entre etapas. El puente va en Python con `subprocess` en binario.",
        publicable=False,
    ),
    # --- infraestructura --------------------------------------------------
    "error_interno": Motivo(
        "El guardrail no pudo evaluar la entrada. Fail-closed: no se aprueba lo "
        "que no se pudo revisar.",
        publicable=False,
    ),
}


def texto_de(motivo: str) -> str:
    """La frase en español de un motivo, o una que dice que no lo conocemos."""
    entrada = MOTIVOS.get(motivo)
    if entrada is not None:
        return entrada.texto
    return f"Motivo sin declarar en el catálogo: {motivo!r}."


def es_publicable(motivo: str) -> bool:
    """Si el motivo se le puede contar al cliente.

    Fail-closed ante lo desconocido: algo que nadie clasificó es, por defecto, un
    problema nuestro. Mismo criterio que `categoria_del_motivo` devolviendo `None`.
    """
    entrada = MOTIVOS.get(motivo)
    return bool(entrada and entrada.publicable)
