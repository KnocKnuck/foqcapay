"""
MACD Indicator Agent

Agent: MACD Indicator Agent
Squad: Indicators
Sprint: 2.1 (Enhanced)

Calculates and broadcasts MACD (Moving Average Convergence Divergence) indicator.

Features:
- MACD line, signal line, and histogram
- Crossover signal detection
- Divergence detection
- Real-time WebSocket broadcasting
- Historical value storage

Agent: #10 MACD Indicator Agent
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import deque
from dataclasses import dataclass
import numpy as np
from agents.base_agent import BaseAgent


@dataclass
class MACDValue:
    """MACD value data point."""
    pair: str
    macd_line: float
    signal_line: float
    histogram: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "macd_line": self.macd_line,
            "signal_line": self.signal_line,
            "histogram": self.histogram,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MACDSignal:
    """MACD signal."""
    pair: str
    signal_type: str  # 'bullish_crossover', 'bearish_crossover', 'divergence_bullish', 'divergence_bearish'
    macd_line: float
    signal_line: float
    histogram: float
    price: float
    timestamp: datetime
    strength: float  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "signal_type": self.signal_type,
            "macd_line": self.macd_line,
            "signal_line": self.signal_line,
            "histogram": self.histogram,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "strength": self.strength,
        }


class MACDIndicatorAgent(BaseAgent):
    """
    MACD Indicator Agent.

    Calculates MACD indicator and detects crossover signals.

    MACD = 12-period EMA - 26-period EMA
    Signal Line = 9-period EMA of MACD
    Histogram = MACD - Signal Line

    Responsibilities:
    - Calculate MACD, signal line, and histogram
    - Detect bullish/bearish crossovers
    - Detect divergences
    - Broadcast indicator values and signals
    - Store historical data for charting
    """

    def __init__(self):
        super().__init__(
            agent_id="macd_indicator",
            agent_type="indicator"
        )

        # MACD parameters
        self.fast_period = 12
        self.slow_period = 26
        self.signal_period = 9

        # Price history per pair: {pair: deque([prices])}
        self.price_history: Dict[str, deque] = {}

        # Current MACD values: {pair: MACDValue}
        self.current_values: Dict[str, MACDValue] = {}

        # MACD history for charting: {pair: deque([MACDValue])}
        self.macd_history: Dict[str, deque] = {}

        # Previous values for crossover detection
        self.previous_values: Dict[str, MACDValue] = {}

        # Max history length
        self.max_history = 1000

        self.logger.info(
            "MACD Indicator Agent initialized",
            fast=self.fast_period,
            slow=self.slow_period,
            signal=self.signal_period
        )

    async def start(self):
        """Start the MACD indicator agent."""
        await super().start()

        # Subscribe to price updates
        await self.subscribe("market.price.*", self._handle_price_update)

        # Subscribe to historical data requests
        await self.subscribe("indicator.macd.request", self._handle_request)

        self.logger.info("MACD Indicator Agent started")

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
                self.price_history[pair] = deque(maxlen=self.slow_period + 100)
                self.macd_history[pair] = deque(maxlen=self.max_history)

            # Add price to history
            self.price_history[pair].append(price)

            # Calculate MACD if we have enough data
            if len(self.price_history[pair]) >= self.slow_period + self.signal_period:
                await self._calculate_macd(pair, price)
                await self._detect_signals(pair, price)

        except Exception as e:
            self.logger.error(
                "Error handling price update",
                error=str(e),
                pair=message.get("pair")
            )

    async def _calculate_macd(self, pair: str, current_price: float):
        """
        Calculate MACD indicator.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        prices = np.array(list(self.price_history[pair]))
        timestamp = datetime.utcnow()

        # Store previous value
        if pair in self.current_values:
            self.previous_values[pair] = self.current_values[pair]

        # Calculate 12-period EMA
        ema_12 = self._calculate_ema(prices, self.fast_period)

        # Calculate 26-period EMA
        ema_26 = self._calculate_ema(prices, self.slow_period)

        # MACD Line = Fast EMA - Slow EMA
        macd_line = ema_12 - ema_26

        # Calculate signal line (9-period EMA of MACD)
        # Need MACD history for this
        if len(self.macd_history[pair]) >= self.signal_period:
            macd_values = [v.macd_line for v in list(self.macd_history[pair])[-self.signal_period:]]
            macd_values.append(macd_line)
            signal_line = self._calculate_ema(np.array(macd_values), self.signal_period)
        else:
            # Not enough history, use MACD as signal
            signal_line = macd_line

        # Histogram = MACD - Signal
        histogram = macd_line - signal_line

        # Create MACD value
        macd_value = MACDValue(
            pair=pair,
            macd_line=macd_line,
            signal_line=signal_line,
            histogram=histogram,
            timestamp=timestamp
        )

        # Store current value
        self.current_values[pair] = macd_value

        # Add to history
        self.macd_history[pair].append(macd_value)

        # Broadcast current values
        await self._broadcast_values(pair, current_price)

    def _calculate_ema(self, values: np.ndarray, period: int) -> float:
        """
        Calculate Exponential Moving Average.

        Args:
            values: Value array
            period: EMA period

        Returns:
            EMA value
        """
        if len(values) < period:
            return np.mean(values)

        multiplier = 2 / (period + 1)
        ema = np.mean(values[:period])  # Start with SMA

        for value in values[period:]:
            ema = (value * multiplier) + (ema * (1 - multiplier))

        return ema

    async def _detect_signals(self, pair: str, current_price: float):
        """
        Detect MACD crossover signals.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        if pair not in self.current_values or pair not in self.previous_values:
            return

        current = self.current_values[pair]
        previous = self.previous_values[pair]

        timestamp = datetime.utcnow()

        # Bullish crossover: MACD crosses above signal line
        if previous.macd_line <= previous.signal_line and current.macd_line > current.signal_line:
            # Strength based on histogram size
            strength = min(100, abs(current.histogram) / current_price * 10000)

            signal = MACDSignal(
                pair=pair,
                signal_type="bullish_crossover",
                macd_line=current.macd_line,
                signal_line=current.signal_line,
                histogram=current.histogram,
                price=current_price,
                timestamp=timestamp,
                strength=strength
            )

            await self._broadcast_signal(signal)

        # Bearish crossover: MACD crosses below signal line
        elif previous.macd_line >= previous.signal_line and current.macd_line < current.signal_line:
            strength = min(100, abs(current.histogram) / current_price * 10000)

            signal = MACDSignal(
                pair=pair,
                signal_type="bearish_crossover",
                macd_line=current.macd_line,
                signal_line=current.signal_line,
                histogram=current.histogram,
                price=current_price,
                timestamp=timestamp,
                strength=strength
            )

            await self._broadcast_signal(signal)

        # Divergence detection
        await self._detect_divergence(pair, current_price, current)

    async def _detect_divergence(self, pair: str, current_price: float, current_macd: MACDValue):
        """
        Detect bullish/bearish divergences.

        Args:
            pair: Trading pair
            current_price: Current price
            current_macd: Current MACD value
        """
        # Need significant history
        if len(self.price_history[pair]) < 50 or len(self.macd_history[pair]) < 50:
            return

        prices = list(self.price_history[pair])
        macd_history = list(self.macd_history[pair])

        # Look at last 20 bars for divergence
        price_window = prices[-20:]
        macd_window = macd_history[-20:]

        # Bullish divergence: Price lower low, MACD higher low
        price_lows = []
        macd_lows = []

        for i in range(1, len(price_window) - 1):
            if price_window[i] < price_window[i-1] and price_window[i] < price_window[i+1]:
                price_lows.append((i, price_window[i]))

            if macd_window[i].macd_line < macd_window[i-1].macd_line and \
               macd_window[i].macd_line < macd_window[i+1].macd_line:
                macd_lows.append((i, macd_window[i].macd_line))

        # Check for divergence pattern
        if len(price_lows) >= 2 and len(macd_lows) >= 2:
            # Price making lower low
            if price_lows[-1][1] < price_lows[-2][1]:
                # MACD making higher low
                if macd_lows[-1][1] > macd_lows[-2][1]:
                    signal = MACDSignal(
                        pair=pair,
                        signal_type="divergence_bullish",
                        macd_line=current_macd.macd_line,
                        signal_line=current_macd.signal_line,
                        histogram=current_macd.histogram,
                        price=current_price,
                        timestamp=datetime.utcnow(),
                        strength=70.0
                    )

                    await self._broadcast_signal(signal)

        # Bearish divergence: Price higher high, MACD lower high
        price_highs = []
        macd_highs = []

        for i in range(1, len(price_window) - 1):
            if price_window[i] > price_window[i-1] and price_window[i] > price_window[i+1]:
                price_highs.append((i, price_window[i]))

            if macd_window[i].macd_line > macd_window[i-1].macd_line and \
               macd_window[i].macd_line > macd_window[i+1].macd_line:
                macd_highs.append((i, macd_window[i].macd_line))

        if len(price_highs) >= 2 and len(macd_highs) >= 2:
            # Price making higher high
            if price_highs[-1][1] > price_highs[-2][1]:
                # MACD making lower high
                if macd_highs[-1][1] < macd_highs[-2][1]:
                    signal = MACDSignal(
                        pair=pair,
                        signal_type="divergence_bearish",
                        macd_line=current_macd.macd_line,
                        signal_line=current_macd.signal_line,
                        histogram=current_macd.histogram,
                        price=current_price,
                        timestamp=datetime.utcnow(),
                        strength=70.0
                    )

                    await self._broadcast_signal(signal)

    async def _broadcast_values(self, pair: str, current_price: float):
        """
        Broadcast current MACD values.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        if pair not in self.current_values:
            return

        current = self.current_values[pair]

        values_data = {
            "pair": pair,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "macd": {
                "macd_line": round(current.macd_line, 4),
                "signal_line": round(current.signal_line, 4),
                "histogram": round(current.histogram, 4),
            }
        }

        # Broadcast to event bus
        await self.publish(
            f"indicator.macd.values.{pair}",
            {
                "type": "macd_values",
                "data": values_data
            }
        )

    async def _broadcast_signal(self, signal: MACDSignal):
        """
        Broadcast MACD signal.

        Args:
            signal: MACD signal
        """
        self.logger.info(
            "MACD signal detected",
            pair=signal.pair,
            signal_type=signal.signal_type,
            histogram=signal.histogram,
            strength=signal.strength
        )

        # Broadcast to event bus
        await self.publish(
            f"signal.macd.{signal.pair}",
            {
                "type": "macd_signal",
                "data": signal.to_dict()
            }
        )

        # Also broadcast to general signals topic
        await self.publish(
            "signals.all",
            {
                "type": "macd_signal",
                "indicator": "MACD",
                "data": signal.to_dict()
            }
        )

    async def _handle_request(self, message: Dict[str, Any]):
        """
        Handle request for MACD data.

        Args:
            message: Request message
        """
        pair = message.get("pair")

        if not pair or pair not in self.current_values:
            return

        # Send current values
        current = self.current_values[pair]

        await self.publish(
            message.get("reply_to", "indicator.macd.response"),
            {
                "pair": pair,
                "macd_line": current.macd_line,
                "signal_line": current.signal_line,
                "histogram": current.histogram,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def get_current_value(self, pair: str) -> Optional[MACDValue]:
        """
        Get current MACD value for a pair.

        Args:
            pair: Trading pair

        Returns:
            Current MACD value
        """
        return self.current_values.get(pair)

    def get_history(self, pair: str, limit: int = 100) -> List[MACDValue]:
        """
        Get MACD history for charting.

        Args:
            pair: Trading pair
            limit: Max number of points

        Returns:
            List of MACD values
        """
        if pair not in self.macd_history:
            return []

        history = list(self.macd_history[pair])
        return history[-limit:]
