"""
genesis_bridge.candidate_factory
Fábrica de candidatos ejecutables compatibles con Genesis (StrategyCandidate + RiskLevelsProvider).
Implementa la lógica del piloto S3 (Donchian Breakout H1 Simétrico) y adaptadores para las demás familias.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Asegurar que genesis pueda importarse si está en C:\Users\bbrav\genesis\src
GENESIS_SRC = Path("C:/Users/bbrav/genesis/src")
if GENESIS_SRC.exists() and str(GENESIS_SRC) not in sys.path:
    sys.path.insert(0, str(GENESIS_SRC))

from genesis.data.store import AnnotatedBar
from genesis.data.symbols import SymbolFigure
from genesis.strategy.contract import Direction, EntryIntent, StrategyCandidate
from genesis_bridge.catalog_schema import HypothesisSpec
from genesis_bridge.errors import CatalogValidationError


class S3DonchianBreakoutCandidate:
    """
    Candidato S3: Donchian Channel Breakout H1 Simétrico (Moskowitz et al. 2012 / Baltas & Kosowski 2013).
    Satisface StrategyCandidate y RiskLevelsProvider mediante Duck Typing.
    """

    candidate_id: str = "S3"

    def __init__(
        self,
        figure: SymbolFigure,
        reference_balance: float = 10000.0,
        lookback_donchian: int = 50,
        banda_filtro_atr_mult: float = 0.3,
        expansion_rango_atr_mult: float = 1.2,
        stop_loss_atr_mult: float = 1.5,
        trailing_chandelier_atr_mult: float = 3.0,
        risk_pct: float = 0.01,
        atr_period: int = 14,
        config_version: str = "genesis-strategy/1",
        allowed_directions: tuple[str, ...] = ("LONG", "SHORT"),
    ) -> None:
        self._figure = figure
        self._reference_balance = reference_balance
        self._lookback_donchian = lookback_donchian
        self._banda_filtro_atr_mult = banda_filtro_atr_mult
        self._expansion_rango_atr_mult = expansion_rango_atr_mult
        self._stop_loss_atr_mult = stop_loss_atr_mult
        self._trailing_chandelier_atr_mult = trailing_chandelier_atr_mult
        self._risk_pct = risk_pct
        self._atr_period = atr_period
        self._config_version = config_version
        self._allowed_directions = tuple(d.upper() for d in allowed_directions)

        # Buffers de precios para cálculo Donchian incremental
        self._highs: list[float] = []
        self._lows: list[float] = []

        # Estado ATR Wilder incremental
        self._atr_value: float | None = None
        self._atr_bars_seen: int = 0
        self._atr_last_close: float | None = None
        self._atr_warmup_sum: float = 0.0

        # Almacenamiento síncrono para risk_levels pop-on-read
        self._pending_risk_levels: tuple[float, float] | None = None

    def on_bar(self, bar: AnnotatedBar) -> list[EntryIntent]:
        """Procesa una barra ya cerrada de forma estrictamente forward-only."""
        # 1. Actualización de ATR Wilder
        self._update_atr(bar)

        # 2. Buffer para Canal Donchian
        self._highs.append(bar.high)
        self._lows.append(bar.low)
        if len(self._highs) > self._lookback_donchian + 1:
            self._highs.pop(0)
            self._lows.pop(0)

        # Filtro de sesión institucional: fuera de sesión y en la barra de cierre no se abren nuevas posiciones
        if not bar.in_session or bar.timestamp_utc >= bar.session_close_utc:
            return []

        # Se requiere warmup completo de Donchian y ATR
        if len(self._highs) < self._lookback_donchian + 1 or self._atr_value is None:
            return []

        # Donchian se calcula sobre las N barras PREVIAS (excluyendo la barra actual)
        donchian_high = max(self._highs[:-1])
        donchian_low = min(self._lows[:-1])

        atr = self._atr_value
        banda = self._banda_filtro_atr_mult * atr
        rango_actual = bar.high - bar.low

        # Filtro de expansión de rango mínimo
        expansion_ok = rango_actual >= (self._expansion_rango_atr_mult * atr)

        # Evaluación de señales
        if "LONG" in self._allowed_directions and bar.close > (donchian_high + banda) and expansion_ok:
            return [self._emit_signal(Direction.LONG, bar.close, atr)]
        elif "SHORT" in self._allowed_directions and bar.close < (donchian_low - banda) and expansion_ok:
            return [self._emit_signal(Direction.SHORT, bar.close, atr)]

        return []

    def _update_atr(self, bar: AnnotatedBar) -> None:
        last = self._atr_last_close
        if last is None:
            tr = bar.high - bar.low
        else:
            tr = max(bar.high - bar.low, abs(bar.high - last), abs(bar.low - last))
        self._atr_last_close = bar.close

        if self._atr_bars_seen < self._atr_period:
            self._atr_bars_seen += 1
            self._atr_warmup_sum += tr
            if self._atr_bars_seen == self._atr_period:
                self._atr_value = self._atr_warmup_sum / self._atr_period
        else:
            current_atr = self._atr_value
            if current_atr is not None:
                self._atr_value = ((current_atr * (self._atr_period - 1)) + tr) / self._atr_period

    def _emit_signal(self, direction: Direction, close_price: float, atr: float) -> EntryIntent:
        sl_dist = max(self._stop_loss_atr_mult * atr, self._figure.tick_value * 2)
        tp_dist = self._trailing_chandelier_atr_mult * atr

        if direction is Direction.LONG:
            stop_loss = close_price - sl_dist
            take_profit = close_price + tp_dist
        else:
            stop_loss = close_price + sl_dist
            take_profit = close_price - tp_dist

        sizing_hint = (self._risk_pct * self._reference_balance) / (sl_dist * self._figure.tick_value)
        # Limitar al step de volumen
        sizing_hint = max(self._figure.volume_step, round(sizing_hint, 2))

        self._pending_risk_levels = (stop_loss, take_profit)

        return EntryIntent(
            direction=direction,
            sizing_hint=sizing_hint,
            candidate_id=self.candidate_id,
            config_version=self._config_version,
        )

    def risk_levels(self, intent: EntryIntent) -> tuple[float, float]:
        """Implementa RiskLevelsProvider (pop-on-read)."""
        if self._pending_risk_levels is None:
            raise RuntimeError(f"risk_levels() invocado sin señal pendiente para {intent}")
        levels = self._pending_risk_levels
        self._pending_risk_levels = None
        return levels


class S2MeanReversionRSICandidate:
    """
    Hipótesis S2: Reversión a la media con oscilador RSI(14) y bandas/medias (Avellaneda & Lee 2010).
    Implementa StrategyCandidate y RiskLevelsProvider por duck typing.
    """

    candidate_id: str = "S2"

    def __init__(
        self,
        figure: SymbolFigure,
        reference_balance: float = 10000.0,
        rsi_sobreventa_umbral: float = 28.0,
        rsi_sobrecompra_umbral: float = 72.0,
        distancia_max_nivel_atr: float = 0.3,
        stop_loss_atr_mult: float = 1.5,
        risk_pct: float = 0.01,
        periodo_rsi: int = 14,
        periodo_sma: int = 20,
        config_version: str = "s2_mean_rev_rsi_v1",
        allowed_directions: Sequence[str] = ("LONG", "SHORT"),
    ) -> None:
        self._figure = figure
        self._reference_balance = reference_balance
        self._rsi_sobreventa = rsi_sobreventa_umbral
        self._rsi_sobrecompra = rsi_sobrecompra_umbral
        self._distancia_max_nivel_atr = distancia_max_nivel_atr
        self._stop_loss_atr_mult = stop_loss_atr_mult
        self._risk_pct = risk_pct
        self._periodo_rsi = periodo_rsi
        self._periodo_sma = periodo_sma
        self._config_version = config_version
        self._allowed_directions = tuple(d.upper() for d in allowed_directions)

        # Estado ATR incremental
        self._atr_value: float | None = None
        self._atr_bars_seen: int = 0
        self._atr_last_close: float | None = None
        self._atr_warmup_sum: float = 0.0

        # Estado RSI incremental (Wilder)
        self._rsi_value: float | None = None
        self._rsi_bars_seen: int = 0
        self._avg_gain: float = 0.0
        self._avg_loss: float = 0.0
        self._rsi_last_close: float | None = None

        # Estado SMA incremental
        self._closes_sma: list[float] = []

        # Risk levels pop-on-read
        self._pending_risk_levels: tuple[float, float] | None = None

    def on_bar(self, bar: AnnotatedBar) -> list[EntryIntent]:
        """Procesa una barra cerrada forward-only."""
        # 1. Actualización de indicadores
        self._update_atr(bar)
        self._update_rsi(bar)
        self._closes_sma.append(bar.close)
        if len(self._closes_sma) > self._periodo_sma:
            self._closes_sma.pop(0)

        # 2. Filtro de sesión institucional
        if not bar.in_session or bar.timestamp_utc >= bar.session_close_utc:
            return []

        # 3. Warmup
        if self._atr_value is None or self._rsi_value is None or len(self._closes_sma) < self._periodo_sma:
            return []

        sma20 = sum(self._closes_sma) / len(self._closes_sma)
        atr = self._atr_value
        rsi = self._rsi_value

        # 4. Señal de Reversión Alcista (Sobreventa extrema + giro)
        if "LONG" in self._allowed_directions:
            if rsi <= self._rsi_sobreventa and bar.close > bar.open and bar.close < sma20:
                intent = self._emit_signal(Direction.LONG, bar.close, atr, sma20)
                return [intent]

        # 5. Señal de Reversión Bajista (Sobrecompra extrema + giro)
        if "SHORT" in self._allowed_directions:
            if rsi >= self._rsi_sobrecompra and bar.close < bar.open and bar.close > sma20:
                intent = self._emit_signal(Direction.SHORT, bar.close, atr, sma20)
                return [intent]

        return []

    def _update_atr(self, bar: AnnotatedBar) -> None:
        last = self._atr_last_close
        if last is None:
            tr = bar.high - bar.low
        else:
            tr = max(bar.high - bar.low, abs(bar.high - last), abs(bar.low - last))
        self._atr_last_close = bar.close

        if self._atr_bars_seen < self._periodo_rsi:
            self._atr_bars_seen += 1
            self._atr_warmup_sum += tr
            if self._atr_bars_seen == self._periodo_rsi:
                self._atr_value = self._atr_warmup_sum / self._periodo_rsi
        else:
            cur = self._atr_value
            if cur is not None:
                self._atr_value = ((cur * (self._periodo_rsi - 1)) + tr) / self._periodo_rsi

    def _update_rsi(self, bar: AnnotatedBar) -> None:
        if self._rsi_last_close is None:
            self._rsi_last_close = bar.close
            return

        change = bar.close - self._rsi_last_close
        self._rsi_last_close = bar.close
        gain = max(change, 0.0)
        loss = max(-change, 0.0)

        if self._rsi_bars_seen < self._periodo_rsi:
            self._avg_gain += gain
            self._avg_loss += loss
            self._rsi_bars_seen += 1
            if self._rsi_bars_seen == self._periodo_rsi:
                self._avg_gain /= self._periodo_rsi
                self._avg_loss /= self._periodo_rsi
                rs = (self._avg_gain / self._avg_loss) if self._avg_loss > 0 else 100.0
                self._rsi_value = 100.0 - (100.0 / (1.0 + rs))
        else:
            self._avg_gain = ((self._avg_gain * (self._periodo_rsi - 1)) + gain) / self._periodo_rsi
            self._avg_loss = ((self._avg_loss * (self._periodo_rsi - 1)) + loss) / self._periodo_rsi
            if self._avg_loss == 0.0:
                self._rsi_value = 100.0
            else:
                rs = self._avg_gain / self._avg_loss
                self._rsi_value = 100.0 - (100.0 / (1.0 + rs))

    def _emit_signal(self, direction: Direction, close_price: float, atr: float, tp_target: float) -> EntryIntent:
        sl_dist = max(self._stop_loss_atr_mult * atr, self._figure.tick_value * 2)

        if direction is Direction.LONG:
            stop_loss = close_price - sl_dist
            take_profit = max(tp_target, close_price + sl_dist)
        else:
            stop_loss = close_price + sl_dist
            take_profit = min(tp_target, close_price - sl_dist)

        sizing_hint = (self._risk_pct * self._reference_balance) / (sl_dist * self._figure.tick_value)
        sizing_hint = max(self._figure.volume_step, round(sizing_hint, 2))

        self._pending_risk_levels = (stop_loss, take_profit)
        return EntryIntent(
            direction=direction,
            sizing_hint=sizing_hint,
            candidate_id=self.candidate_id,
            config_version=self._config_version,
        )

    def risk_levels(self, intent: EntryIntent) -> tuple[float, float]:
        if self._pending_risk_levels is None:
            raise RuntimeError(f"risk_levels() invocado sin señal pendiente para {intent}")
        levels = self._pending_risk_levels
        self._pending_risk_levels = None
        return levels


def create_candidate_from_spec(
    spec: HypothesisSpec,
    figure: SymbolFigure,
    reference_balance: float = 10000.0,
    params: Mapping[str, float] | None = None,
    allowed_directions: tuple[str, ...] = ("LONG", "SHORT"),
) -> StrategyCandidate:
    """Fábrica que instancia el candidato ejecutable a partir de una especificación normalizada."""
    p = dict(params or {})
    setup_id = spec.id_setup.upper()

    if "MEAN_REVERSION_RSI" in setup_id or "S2" in setup_id:
        return S2MeanReversionRSICandidate(
            figure=figure,
            reference_balance=reference_balance,
            rsi_sobreventa_umbral=float(p.get("rsi_sobreventa_umbral", 28.0)),
            rsi_sobrecompra_umbral=float(p.get("rsi_sobrecompra_umbral", 72.0)),
            distancia_max_nivel_atr=float(p.get("distancia_max_nivel_atr", 0.3)),
            stop_loss_atr_mult=float(p.get("stop_loss_atr_mult", 1.5)),
            risk_pct=float(p.get("risk_pct", 0.01)),
            allowed_directions=allowed_directions,
        )

    if "DONCHIAN" in setup_id or "S3" in setup_id:
        return S3DonchianBreakoutCandidate(
            figure=figure,
            reference_balance=reference_balance,
            lookback_donchian=int(p.get("lookback_donchian", 50)),
            banda_filtro_atr_mult=float(p.get("banda_filtro_atr_mult", 0.3)),
            expansion_rango_atr_mult=float(p.get("expansion_rango_atr_mult", 1.2)),
            stop_loss_atr_mult=float(p.get("stop_loss_atr_mult", 1.5)),
            trailing_chandelier_atr_mult=float(p.get("trailing_chandelier_atr_mult", 3.0)),
            risk_pct=float(p.get("risk_pct", 0.01)),
            allowed_directions=allowed_directions,
        )

    raise CatalogValidationError(f"Fábrica de candidatos aún no tiene implementación ejecutable para: {spec.id_setup}")
