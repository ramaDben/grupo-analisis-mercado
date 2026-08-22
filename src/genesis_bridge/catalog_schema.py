"""
genesis_bridge.catalog_schema
Modelos estructurados y validadores estrictos para el Catálogo Maestro de Hipótesis Candidatas v1.3.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping, Sequence

from genesis_bridge.errors import CatalogValidationError


class PromotionState(StrEnum):
    CANDIDATO = "CANDIDATO"
    GATE_ESTADISTICO_APROBADO = "GATE_ESTADISTICO_APROBADO"
    VALIDADO_GENESIS = "VALIDADO_GENESIS"
    INCUBACION_PAPER = "INCUBACION_PAPER"
    APROBADO_LIMITADO = "APROBADO_LIMITADO"


class TerminalState(StrEnum):
    RECHAZADO = "RECHAZADO"
    DEPRECADO = "DEPRECADO"


class OperationalStatus(StrEnum):
    BLOQUEADO = "BLOQUEADO"
    PAPER_ONLY = "PAPER_ONLY"
    LIVE_LIMITED = "LIVE_LIMITED"


class HumanReviewStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class SearchSpaceParam:
    """Definición de un parámetro en el espacio de búsqueda formal."""
    valor_base: float
    rango_permitido: tuple[float, float] | tuple[float, ...]
    paso_grilla: float

    def grid_values(self) -> list[float]:
        """Genera los valores discretos de la grilla combinatoria."""
        if len(self.rango_permitido) > 2 and self.paso_grilla == 1.0:
            return [float(x) for x in self.rango_permitido]
        start, end = self.rango_permitido[0], self.rango_permitido[1]
        step = self.paso_grilla
        if step <= 0:
            return [start]
        values = []
        current = start
        while current <= end + (step / 1000.0):
            values.append(round(current, 6))
            current += step
        return values


@dataclass(frozen=True, slots=True)
class AcademicReference:
    autor: str
    paper: str
    journal: str


@dataclass(frozen=True, slots=True)
class HypothesisProvenance:
    tipo: str
    derivada_de: tuple[AcademicReference, ...]
    transformaciones: tuple[str, ...]
    mecanismo_preservado: str
    auditoria_humana: HumanReviewStatus = HumanReviewStatus.PENDING


@dataclass(frozen=True, slots=True)
class HypothesisSpec:
    """Especificación normalizada e inmutable de una hipótesis candidata del catálogo."""
    id_setup: str
    familia: str
    regimen_macro_optimo: tuple[str, ...]
    estado_validacion: str
    strategy_code_version: str
    data_schema_version: str
    regime_schema_version: str
    procedencia: HypothesisProvenance
    trial_ids: tuple[str, ...]
    direcciones_por_regimen: Mapping[str, Mapping[str, tuple[str, ...]]]
    espacio_de_busqueda_parametros: Mapping[str, SearchSpaceParam]
    constantes_congeladas: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.estado_validacion not in (PromotionState.CANDIDATO.value, PromotionState.GATE_ESTADISTICO_APROBADO.value, PromotionState.VALIDADO_GENESIS.value):
            if self.estado_validacion not in (TerminalState.RECHAZADO.value, TerminalState.DEPRECADO.value):
                raise CatalogValidationError(
                    f"Hipótesis '{self.id_setup}' tiene estado_validacion inválido: '{self.estado_validacion}'."
                )
        if not self.trial_ids:
            raise CatalogValidationError(f"Hipótesis '{self.id_setup}' debe declarar al menos un trial_id.")


def validate_hypothesis_against_matrix(
    hypothesis: HypothesisSpec,
    matrix: Mapping[str, Mapping[str, Mapping[str, Any]]]
) -> None:
    """
    Valida la consistencia estricta entre la ficha de la hipótesis y la matriz SSOT.
    Aplica la regla 'fail-closed': ante cualquier discrepancia, lanza CatalogValidationError.
    """
    setup_key = hypothesis.id_setup
    for regimen, setups_en_regimen in matrix.items():
        # Si la matriz lista la estrategia para este régimen
        matrix_setup_entry = setups_en_regimen.get(setup_key)
        if matrix_setup_entry is None:
            # Buscar posible clave con prefijo (ej. S3_BREAKOUT_DONCHIAN_H1)
            for k, v in setups_en_regimen.items():
                if k.endswith(setup_key) or setup_key.endswith(k):
                    matrix_setup_entry = v
                    break

        if matrix_setup_entry is not None:
            estado_matriz = matrix_setup_entry.get("estado")
            direcciones_matriz = matrix_setup_entry.get("direcciones", {})
            direcciones_ficha = hypothesis.direcciones_por_regimen.get(regimen, {})

            # Si es PROHIBIDA en la matriz, en la ficha no debe tener direcciones
            if estado_matriz == "PROHIBIDA":
                for symbol, dirs in direcciones_ficha.items():
                    if len(dirs) > 0:
                        raise CatalogValidationError(
                            f"Discrepancia SSOT en {hypothesis.id_setup} para {regimen}: "
                            f"Matriz declara PROHIBIDA pero ficha tiene direcciones {dirs} en {symbol}."
                        )
            elif estado_matriz in ("OPTIMA", "SECUNDARIA", "PERMITIDA"):
                for symbol, dirs_matriz in direcciones_matriz.items():
                    dirs_ficha = list(direcciones_ficha.get(symbol, []))
                    if sorted(dirs_ficha) != sorted(dirs_matriz):
                        raise CatalogValidationError(
                            f"Discrepancia SSOT en {hypothesis.id_setup} para {regimen} en {symbol}: "
                            f"Matriz declara {dirs_matriz} vs Ficha declara {dirs_ficha}."
                        )
