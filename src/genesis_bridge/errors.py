"""
genesis_bridge.errors
Jerarquía tipada de excepciones para el puente de validación cuantitativa entre el catálogo y Genesis.
"""

from __future__ import annotations


class GenesisBridgeError(Exception):
    """Excepción base para todos los errores del puente de integración con Genesis."""


class CatalogValidationError(GenesisBridgeError):
    """El catálogo v1.3 contiene esquemas inválidos, campos ambiguos o discrepancias con la matriz SSOT."""


class RegimeLeakageError(GenesisBridgeError):
    """Intento de acceso a un régimen futuro o violación del invariante Point-in-Time."""


class PromotionGateError(GenesisBridgeError):
    """Intento de promover una estrategia sin cumplir estrictamente los gates o sin hashes verificables."""


class UncertifiedStrategyError(GenesisBridgeError):
    """Intento de ejecutar u operar una estrategia sin certificado válido o sin estado APROBADO_LIMITADO."""
