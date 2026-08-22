"""
genesis_bridge.hypothesis_loader
Cargador y parser de propuesta_catalogo_estrategias_ssrn.md (v1.3.0) a modelos estructurados inmutables.
Calcula el hash criptográfico SHA-256 del documento fuente y valida contra la matriz SSOT.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping
import yaml

from genesis_bridge.catalog_schema import (
    AcademicReference,
    HumanReviewStatus,
    HypothesisProvenance,
    HypothesisSpec,
    SearchSpaceParam,
    validate_hypothesis_against_matrix,
)
from genesis_bridge.errors import CatalogValidationError

# Ruta por defecto al catálogo v1.3: la copia VERSIONADA dentro del repo.
#
# El catálogo es la fuente de verdad de toda la maquinaria de hipótesis y su
# SHA-256 (`catalogue_hash`) queda grabado en cada certificado emitido. Antes
# esta ruta apuntaba al brain cache de Antigravity, indexado por un UUID de
# sesión: si ese cache se limpiaba, se perdía el catálogo y todos los
# `catalogue_hash` emitidos quedaban inverificables para siempre.
DEFAULT_CATALOGUE_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "propuesta_catalogo_estrategias_ssrn.md"
)


def _compute_sha256(content: str | bytes) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _parse_yaml_block(block_text: str) -> dict[str, Any]:
    try:
        return yaml.safe_load(block_text) or {}
    except Exception as exc:
        raise CatalogValidationError(f"Error parseando bloque YAML del catálogo: {exc}") from exc


def _build_hypothesis_spec(raw: dict[str, Any]) -> HypothesisSpec:
    id_setup = raw.get("id_setup", "")
    familia = raw.get("familia", "")
    regimen_optimo = raw.get("regimen_macro_optimo", [])
    if isinstance(regimen_optimo, str):
        regimen_optimo = [regimen_optimo]

    estado_validacion = raw.get("estado_validacion", "CANDIDATO")

    impl = raw.get("implementacion", {})
    strategy_code_version = impl.get("strategy_code_version", "")
    data_schema_version = impl.get("data_schema_version", "")
    regime_schema_version = impl.get("regime_schema_version", "")

    proc_raw = raw.get("procedencia", {})
    tipo_proc = proc_raw.get("tipo", "SINTETICA_DERIVADA")
    derivada_de = []
    for item in proc_raw.get("derivada_de", []):
        derivada_de.append(
            AcademicReference(
                autor=item.get("autor", ""),
                paper=item.get("paper", ""),
                journal=item.get("journal", ""),
            )
        )
    transformaciones = tuple(proc_raw.get("transformaciones", []))
    mecanismo = proc_raw.get("mecanismo_preservado", "")
    auditoria_raw = str(proc_raw.get("auditoria_humana", "PENDING")).upper().strip()
    auditoria = HumanReviewStatus.APPROVED if auditoria_raw in ("APPROVED", "APROBADO") else HumanReviewStatus.PENDING

    procedencia = HypothesisProvenance(
        tipo=tipo_proc,
        derivada_de=tuple(derivada_de),
        transformaciones=transformaciones,
        mecanismo_preservado=mecanismo,
        auditoria_humana=auditoria,
    )

    unidades_val = raw.get("unidades_de_validacion", [])
    trial_ids = tuple(u.get("trial_id") for u in unidades_val if "trial_id" in u)

    dirs_raw = raw.get("direcciones_por_regimen", {})
    direcciones_por_regimen: dict[str, dict[str, tuple[str, ...]]] = {}
    for reg, sym_map in dirs_raw.items():
        direcciones_por_regimen[reg] = {}
        if isinstance(sym_map, dict):
            for sym, dirs in sym_map.items():
                direcciones_por_regimen[reg][sym] = tuple(dirs or [])

    espacio_raw = raw.get("espacio_de_busqueda_parametros", {})
    espacio_busqueda: dict[str, SearchSpaceParam] = {}
    for p_name, p_data in espacio_raw.items():
        v_base = float(p_data.get("valor_base", 0.0))
        r_permitido = tuple(float(x) for x in p_data.get("rango_permitido", [v_base, v_base]))
        p_grilla = float(p_data.get("paso_grilla", 1.0))
        espacio_busqueda[p_name] = SearchSpaceParam(
            valor_base=v_base,
            rango_permitido=r_permitido,
            paso_grilla=p_grilla,
        )

    constantes = raw.get("constantes_congeladas", {})

    return HypothesisSpec(
        id_setup=id_setup,
        familia=familia,
        regimen_macro_optimo=tuple(regimen_optimo),
        estado_validacion=estado_validacion,
        strategy_code_version=strategy_code_version,
        data_schema_version=data_schema_version,
        regime_schema_version=regime_schema_version,
        procedencia=procedencia,
        trial_ids=trial_ids,
        direcciones_por_regimen=direcciones_por_regimen,
        espacio_de_busqueda_parametros=espacio_busqueda,
        constantes_congeladas=constantes,
    )


def _get_default_catalogue_path() -> Path:
    """Ruta del catálogo versionado en el repo.

    Sin fallbacks a rutas absolutas de una máquina concreta: si el archivo no
    está donde el repo dice, `load_catalogue` levanta `CatalogValidationError`
    en vez de resolver silenciosamente a una copia distinta cuyo hash no
    coincidiría con el de los certificados ya emitidos.
    """
    return DEFAULT_CATALOGUE_PATH


def load_catalogue(
    file_path: Path | str | None = None,
) -> tuple[dict[str, HypothesisSpec], dict[str, Any], str]:
    """
    Carga el catálogo v1.3 desde Markdown, extrae bloques YAML y la matriz SSOT,
    calcula el hash SHA-256 del documento y valida cada hipótesis.
    Retorna: (mapa_hipotesis, matriz_ssot, catalogue_hash)
    """
    if file_path is not None:
        target_path = Path(file_path)
    else:
        target_path = _get_default_catalogue_path()

    if not target_path.exists():
        raise CatalogValidationError(f"Archivo de catálogo no encontrado en: {target_path}")

    content = target_path.read_text(encoding="utf-8")
    catalogue_hash = _compute_sha256(content)

    # Extraer todos los bloques de código YAML
    yaml_blocks = re.findall(r"```yaml\s*\n(.*?)\n```", content, re.DOTALL)
    if not yaml_blocks:
        raise CatalogValidationError(f"No se encontraron bloques YAML en {target_path}")

    hypotheses: dict[str, HypothesisSpec] = {}
    matrix_ssot: dict[str, Any] = {}

    for block in yaml_blocks:
        parsed = _parse_yaml_block(block)
        if "matriz_compatibilidad_y_direccion" in parsed:
            matrix_ssot = parsed["matriz_compatibilidad_y_direccion"]
        elif "id_setup" in parsed:
            spec = _build_hypothesis_spec(parsed)
            hypotheses[spec.id_setup] = spec

    if not matrix_ssot:
        raise CatalogValidationError("No se encontró la matriz_compatibilidad_y_direccion en el catálogo.")

    # Validar todas las hipótesis contra la matriz SSOT
    for setup_id, spec in hypotheses.items():
        validate_hypothesis_against_matrix(spec, matrix_ssot)

    return hypotheses, matrix_ssot, catalogue_hash


def load_hypothesis(
    setup_id: str,
    file_path: Path | str | None = None,
) -> tuple[HypothesisSpec, str]:
    """Carga una hipótesis específica por su id_setup o trial_id."""
    hypotheses, _matrix, catalogue_hash = load_catalogue(file_path)
    target = setup_id.upper()

    if target in hypotheses:
        return hypotheses[target], catalogue_hash

    # 1. Buscar coincidencia por trial_id dentro de v.trial_ids
    for k, v in hypotheses.items():
        for u_id in v.trial_ids:
            u_upper = u_id.upper()
            if target == u_upper or target in u_upper or u_upper.startswith(target) or target.startswith(u_upper.split("__")[0]):
                return v, catalogue_hash

    # 2. Buscar coincidencia por similitud de nombre
    for k, v in hypotheses.items():
        k_upper = k.upper()
        if k_upper == target or target.endswith(k_upper) or k_upper.endswith(target) or target in k_upper or k_upper in target:
            return v, catalogue_hash

    raise CatalogValidationError(
        f"Hipótesis '{setup_id}' no encontrada en el catálogo. Disponibles: {list(hypotheses.keys())}"
    )
