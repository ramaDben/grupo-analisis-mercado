"""Velas sintéticas para probar el trazado de Tori con geometría conocida."""
from __future__ import annotations

import pandas as pd

T0 = 1_735_689_600  # 2025-01-01 00:00 UTC


def desde_vertices(vertices: list[float], velas_por_tramo: int, paso: int = 4 * 3600,
                   mecha: float = 0.2, t0: int = T0) -> pd.DataFrame:
    """Une los vértices con tramos rectos. La vela i abre en p_i y cierra en p_{i+1}."""
    camino = [vertices[0]]
    for a, b in zip(vertices, vertices[1:]):
        camino += [a + (b - a) * (k + 1) / velas_por_tramo for k in range(velas_por_tramo)]
    filas = []
    for i, (o, c) in enumerate(zip(camino, camino[1:])):
        filas.append({"time": t0 + i * paso, "open": o, "close": c,
                      "high": max(o, c) + mecha, "low": min(o, c) - mecha})
    return pd.DataFrame(filas)


def agregar(df: pd.DataFrame, cada: int) -> pd.DataFrame:
    """Junta `cada` velas en una (de H4 a D1 con 6, de H4 a W1 con 30)."""
    grupos = df.groupby(df.index // cada)
    return pd.DataFrame({
        "time": grupos["time"].first(), "open": grupos["open"].first(),
        "high": grupos["high"].max(), "low": grupos["low"].min(), "close": grupos["close"].last(),
    }).reset_index(drop=True)
