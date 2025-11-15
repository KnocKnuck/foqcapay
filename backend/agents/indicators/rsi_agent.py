"""
RSI Indicator Agent

Agent: RSI Indicator Agent
Squad: Indicators
Sprint: 2.1 (Enhanced)

Calculates and broadcasts Relative Strength Index (RSI) for technical analysis.

Features:
- RSI calculation with multiple periods (5, 14, 21)
- Overbought/oversold signal generation
- Divergence detection
- Real-time WebSocket broadcasting
- Historical value storage

Agent: #9 RSI Indicator Agent
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
from dataclasses import dataclass
import numpy as np
from agents.base_agent import BaseAgent


@dataclass
class RSIValue:
    """RSI value data point."""
    pair: str
    period: int
    value: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "period": self.period,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class RSISignal:
    """RSI signal."""
    pair: str
    signal_type: str  # 'overbought', 'oversold', 'divergence_bullish', 'divergence_bearish'
    rsi_value: float
    price: float
    timestamp: datetime
    strength: float  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "signal_type": self.signal_type,
            "rsi_value": self.rsi_value,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "strength": self.strength,
        }


class RSIIndicatorAgent(BaseAgent):
    """
    RSI Indicator Agent.

    Calculates Relative Strength Index and detects overbought/oversold conditions.

    Responsibilities:
    - Calculate RSI for multiple periods (5, 14, 21)
    - Detect overbought (>70) and oversold (<30) conditions
    - Detect bullish/bearish divergences
    - Broadcast indicator values and signals
    - Store historical data for charting
    """

    def __init__(self):
        super().__init__(
            agent_id="rsi_indicator",
            agent_type="indicator"
        )

        # RSI periods to calculate
        self.periods = [5, 14, 21]

        # Price history per pair: {pair: deque([prices])}
        self.price_history: Dict[str, deque] = {}

        # Current RSI values: {pair: {period: value}}
        self.current_values: Dict[str, Dict[int, float]] = {}

        # RSI history for charting: {pair: {period: deque([RSIValue])}}
        self.rsi_history: Dict[str, Dict[int, deque]] = {}

        # Previous RSI values for divergence detection
        self.previous_values: Dict[str, Dict[int, float]] = {}

        # Thresholds
        self.overbought_threshold = 70
        self.oversold_threshold = 30

        # Max history length
        self.max_history = 1000

        self.logger.info(
            "RSI Indicator Agent initialized",
            periods=self.periods,
            overbought=self.overbought_threshold,
            oversold=self.oversold_threshold
        )

    async def start(self):
        """Start the RSI indicator agent."""
        await super().start()

        # Subscribe to price updates
        await self.subscribe("market.price.*", self._handle_price_update)

        # Subscribe to historical data requests
        await self.subscribe("indicator.rsi.request", self._handle_request)

        self.logger.info("RSI Indicator Agent started")

    async def _handle_price_update(self, message: Dict[str, Any]):
        """
        Handle incoming price updates.

        Args:
            message: Price update message
        """
        try:
            pair = message.get("pair")
            price = float(message.get("price", 0))

            if not pair or price <= 0:
                return

            # Initialize structures for new pair
            if pair not in self.price_history:
                self.price_history[pair] = deque(maxlen=max(self.periods) + 100)
                self.current_values[pair] = {}
                self.previous_values[pair] = {}
                self.rsi_history[pair] = {
                    p: deque(maxlen=self.max_history) for p in self.periods
                }

            # Add price to history
            self.price_history[pair].append(price)

            # Calculate RSI if we have enough data
            if len(self.price_history[pair]) >= min(self.periods) + 1:
                await self._calculate_rsi(pair, price)
                await self._detect_signals(pair, price)

        except Exception as e:
            self.logger.error(
                "Error handling price update",
                error=str(e),
                pair=message.get("pair")
            )

    async def _calculate_rsi(self, pair: str, current_price: float):
        """
        Calculate RSI for all periods.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        prices = np.array(list(self.price_history[pair]))
        timestamp = datetime.utcnow()

        # Calculate price changes
        if len(prices) < 2:
            return

        # Store previous values
        for period in self.periods:
            if period in self.current_values[pair]:
                self.previous_values[pair][period] = self.current_values[pair][period]

        # Calculate RSI for each period
        for period in self.periods:
            if len(prices) >= period + 1:
                rsi_value = self._calculate_rsi_value(prices, period)

                self.current_values[pair][period] = rsi_value

                rsi_data = RSIValue(
                    pair=pair,
                    period=period,
                    value=rsi_value,
                    timestamp=timestamp
                )
                self.rsi_history[pair][period].append(rsi_data)

        # Broadcast current values
        await self._broadcast_values(pair, current_price)

    def _calculate_rsi_value(self, prices: np.ndarray, period: int) -> float:
        """
        Calculate RSI value.

        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss

        Args:
            prices: Price array
            period: RSI period

        Returns:
            RSI value (0-100)
        """
        # Calculate price changes
        deltas = np.diff(prices)

        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Calculate initial averages using SMA
        if len(gains) < period:
            return 50.0  # Neutral

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        # Calculate subsequent averages using Wilder's smoothing
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        # Calculate RS and RSI
        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    async def _detect_signals(self, pair: str, current_price: float):
        """
        Detect RSI signals (overbought/oversold).

        Args:
            pair: Trading pair
            current_price: Current price
        """
        timestamp = datetime.utcnow()

        # Use RSI-14 as primary signal
        if 14 not in self.current_values[pair]:
            return

        rsi_14 = self.current_values[pair][14]

        # Overbought condition (RSI > 70)
        if rsi_14 > self.overbought_threshold:
            # Check if just crossed into overbought
            if 14 in self.previous_values[pair]:
                prev_rsi = self.previous_values[pair][14]

                if prev_rsi <= self.overbought_threshold:
                    strength = min(100, (rsi_14 - self.overbought_threshold) / 30 * 100)

                    signal = RSISignal(
                        pair=pair,
                        signal_type="overbought",
                        rsi_value=rsi_14,
                        price=current_price,
                        timestamp=timestamp,
                        strength=strength
                    )

                    await self._broadcast_signal(signal)

        # Oversold condition (RSI < 30)
        elif rsi_14 < self.oversold_threshold:
            # Check if just crossed into oversold
            if 14 in self.previous_values[pair]:
                prev_rsi = self.previous_values[pair][14]

                if prev_rsi >= self.oversold_threshold:
                    strength = min(100, (self.oversold_threshold - rsi_14) / 30 * 100)

                    signal = RSISignal(
                        pair=pair,
                        signal_type="oversold",
                        rsi_value=rsi_14,
                        price=current_price,
                        timestamp=timestamp,
                        strength=strength
                    )

                    await self._broadcast_signal(signal)

        # Divergence detection (simplified)
        await self._detect_divergence(pair, current_price, rsi_14)

    async def _detect_divergence(self, pair: str, current_price: float, rsi_value: float):
        """
        Detect bullish/bearish divergences.

        Args:
            pair: Trading pair
            current_price: Current price
            rsi_value: Current RSI value
        """
        # Need significant history for divergence
        if len(self.price_history[pair]) < 50:
            return

        prices = list(self.price_history[pair])
        rsi_history = list(self.rsi_history[pair][14])

        if len(rsi_history) < 50:
            return

        # Bullish divergence: Price makes lower low, RSI makes higher low
        # (simplified check - looking at last 20 bars)
        price_window = prices[-20:]
        rsi_window = [r.value for r in rsi_history[-20:]]

        price_low_idx = price_window.index(min(price_window))
        rsi_low_idx = rsi_window.index(min(rsi_window))

        # Bullish divergence pattern
        if price_low_idx > 10 and rsi_low_idx < 10:
            if rsi_value < 40:  # Only in lower RSI range
                signal = RSISignal(
                    pair=pair,
                    signal_type="divergence_bullish",
                    rsi_value=rsi_value,
                    price=current_price,
                    timestamp=datetime.utcnow(),
                    strength=60.0
                )

                await self._broadcast_signal(signal)

        # Bearish divergence: Price makes higher high, RSI makes lower high
        price_high_idx = price_window.index(max(price_window))
        rsi_high_idx = rsi_window.index(max(rsi_window))

        if price_high_idx > 10 and rsi_high_idx < 10:
            if rsi_value > 60:  # Only in higher RSI range
                signal = RSISignal(
                    pair=pair,
                    signal_type="divergence_bearish",
                    rsi_value=rsi_value,
                    price=current_price,
                    timestamp=datetime.utcnow(),
                    strength=60.0
                )

                await self._broadcast_signal(signal)

    async def _broadcast_values(self, pair: str, current_price: float):
        """
        Broadcast current RSI values.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        values_data = {
            "pair": pair,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "rsi": {}
        }

        for period in self.periods:
            if period in self.current_values[pair]:
                values_data["rsi"][period] = round(
                    self.current_values[pair][period], 2
                )

        # Broadcast to event bus
        await self.publish(
            f"indicator.rsi.values.{pair}",
            {
                "type": "rsi_values",
                "data": values_data
            }
        )

    async def _broadcast_signal(self, signal: RSISignal):
        """
        Broadcast RSI signal.

        Args:
            signal: RSI signal
        """
        self.logger.info(
            "RSI signal detected",
            pair=signal.pair,
            signal_type=signal.signal_type,
            rsi=signal.rsi_value,
            strength=signal.strength
        )

        # Broadcast to event bus
        await self.publish(
            f"signal.rsi.{signal.pair}",
            {
                "type": "rsi_signal",
                "data": signal.to_dict()
            }
        )

        # Also broadcast to general signals topic
        await self.publish(
            "signals.all",
            {
                "type": "rsi_signal",
                "indicator": "RSI",
                "data": signal.to_dict()
            }
        )

    async def _handle_request(self, message: Dict[str, Any]):
        """
        Handle request for RSI data.

        Args:
            message: Request message
        """
        pair = message.get("pair")
        period = message.get("period", 14)

        if not pair:
            return

        # Send current values
        if pair in self.current_values and period in self.current_values[pair]:
            await self.publish(
                message.get("reply_to", "indicator.rsi.response"),
                {
                    "pair": pair,
                    "period": period,
                    "value": self.current_values[pair][period],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    def get_current_value(self, pair: str, period: int = 14) -> Optional[float]:
        """
        Get current RSI value for a pair.

        Args:
            pair: Trading pair
            period: RSI period

        Returns:
            Current RSI value
        """
        if pair in self.current_values and period in self.current_values[pair]:
            return self.current_values[pair][period]
        return None

    def get_history(self, pair: str, period: int = 14, limit: int = 100) -> List[RSIValue]:
        """
        Get RSI history for charting.

        Args:
            pair: Trading pair
            period: RSI period
            limit: Max number of points

        Returns:
            List of RSI values
        """
        if pair not in self.rsi_history or period not in self.rsi_history[pair]:
            return []

        history = list(self.rsi_history[pair][period])
        return history[-limit:]
