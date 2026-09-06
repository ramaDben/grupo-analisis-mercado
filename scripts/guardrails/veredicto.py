"""El contrato que hablan todos los guardrails: un veredicto con su motivo.

Los siete módulos de `guardrails/` son funciones puras: reciben datos, devuelven
un veredicto, no escriben nada y **nunca lanzan**. Esa última parte no es estilo.
Un guardrail vive dentro de un hook, y un hook que revienta no bloquea: la sesión
sigue y la escritura pasa sin revisar. Levantar una excepción convierte un
guardia en un permiso, que es exactamente el modo de falla silenciosa que este
sistema existe para cerrar.

De ahí las dos decisiones de este módulo:

1. **`falla()` nunca corrige el slug que le pasan.** Si alguien escribe uno que
   no está en el catálogo, el veredicto sale con ese slug tal cual: mentir sobre
   qué pasó sería peor que no saber nombrarlo. Quien lo caza es el test de
   contrato, que lee el código fuente con `ast` y falla en el commit.
2. **Un slug sin clasificar no es publicable.** `es_publicable` devuelve `False`
   ante lo desconocido, mismo criterio que `categoria_del_motivo` en
   `suplemento_canal.py`: un problema nuestro no es contenido para el cliente, y
   algo que nadie clasificó todavía es, por defecto, un problema nuestro.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import motivos as _motivos


@dataclass(frozen=True)
class Veredicto:
    """El resultado de una comprobación.

    `motivo` es un slug estable del catálogo de `motivos.py`, y el mismo slug se
    lee idéntico en un rechazo de hook, en el registro del reloj y en un fallo de
    pytest. `detalle` es la frase en español que ve la persona. `ubicacion` dice
    dónde: `"línea 12"`, `"USDCLP"`, `"02_forex_divisas"`.
    """

    ok: bool
    motivo: str = ""
    detalle: str = ""
    ubicacion: str | None = None

    def __bool__(self) -> bool:
        return self.ok

    @property
    def publicable(self) -> bool:
        """Si el motivo se le puede contar al cliente o es asunto nuestro."""
        return self.ok or _motivos.es_publicable(self.motivo)


def aprueba() -> Veredicto:
    """El veredicto positivo. No lleva motivo: no hay nada que nombrar."""
    return Veredicto(ok=True)


def falla(motivo: str, detalle: str, ubicacion: str | None = None) -> Veredicto:
    """El veredicto negativo. **Siempre** nombra su motivo.

    Igual que las exclusiones del escáner: un rechazo que no dice por qué no es
    auditable, y un sistema que rechaza sin poder explicarse termina apagado.
    """
    return Veredicto(ok=False, motivo=motivo, detalle=detalle, ubicacion=ubicacion)


def primer_fallo(veredictos: list[Veredicto]) -> Veredicto:
    """El primer negativo de la lista, o el positivo si están todos bien.

    Existe para que ningún módulo escriba su propio bucle de cortocircuito: dos
    implementaciones del mismo recorrido divergen, y la que quede atrás va a ser
    la que corre en el hook.
    """
    for v in veredictos:
        if not v.ok:
            return v
    return aprueba()
