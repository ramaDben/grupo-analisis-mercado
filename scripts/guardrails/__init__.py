"""Guardrails: funciones puras que deciden si algo puede salir.

Las ejecutan **dos mitades** del sistema: los hooks, que solo viven mientras hay
una sesión de Claude Code abierta, y `reloj_gi.py`, que corre 24/7 bajo el
Programador de tareas. El riesgo obvio es que cada mitad desarrolle su propio
criterio, que es el defecto recurrente del repo (`TPM_CHILE` contra `TPM`, los
`digits` del cobre con tres valores distintos, `exigir_texto_editorial` en una
ruta de render y no en la otra).

La respuesta es este módulo compartido, y tests de contrato que fallan si alguna
mitad deja de llamarlo.

Ninguno de estos módulos reimplementa lo que ya existe: `temporal` y `estado`
(fases siguientes) son envoltorios. Una segunda regla de vencimiento o una
segunda fórmula de anacronismo serían el mismo error que tener dos fórmulas de ATR.
"""

from .veredicto import Veredicto, aprueba, falla, primer_fallo

__all__ = ["Veredicto", "aprueba", "falla", "primer_fallo"]
