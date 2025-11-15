"""
Moving Average Indicator Agent

Agent: MA Indicator Agent
Squad: Indicators
Sprint: 2.1 (Enhanced)

Calculates and broadcasts moving average indicators for technical analysis.

Features:
- Multiple MA types (SMA, EMA, WMA)
- Multiple timeframes (9, 20, 50, 100, 200)
- Real-time calculation on price updates
- Signal generation (golden cross, death cross)
- WebSocket broadcasting
- Historical value storage

Agent: #8 MA Indicator Agent
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
import numpy as np
from agents.base_agent import BaseAgent


@dataclass
class MAValue:
    """Moving average value data point."""
    pair: str
    ma_type: str  # 'SMA', 'EMA', 'WMA'
    period: int
    value: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "ma_type": self.ma_type,
            "period": self.period,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MASignal:
    """Moving average crossover signal."""
    pair: str
    signal_type: str  # 'golden_cross', 'death_cross', 'price_cross_up', 'price_cross_down'
    fast_ma: int
    slow_ma: int
    price: float
    timestamp: datetime
    strength: float  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "signal_type": self.signal_type,
            "fast_ma": self.fast_ma,
            "slow_ma": self.slow_ma,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "strength": self.strength,
        }


class MAIndicatorAgent(BaseAgent):
    """
    Moving Average Indicator Agent.

    Calculates moving averages and detects crossover signals.

    Responsibilities:
    - Calculate SMA, EMA, WMA for multiple periods
    - Detect golden cross (bullish) and death cross (bearish)
    - Detect price crossing above/below MAs
    - Broadcast indicator values and signals
    - Store historical data for charting
    """

    def __init__(self):
        super().__init__(
            agent_id="ma_indicator",
            agent_type="indicator"
        )

        # Moving average periods to calculate
        self.periods = [9, 20, 50, 100, 200]

        # Price history per pair: {pair: deque([prices])}
        self.price_history: Dict[str, deque] = {}

        # Current MA values: {pair: {ma_type: {period: value}}}
        self.current_values: Dict[str, Dict[str, Dict[int, float]]] = {}

        # MA history for charting: {pair: {ma_type: {period: deque([MAValue])}}}
        self.ma_history: Dict[str, Dict[str, Dict[int, deque]]] = {}

        # Previous values for crossover detection
        self.previous_values: Dict[str, Dict[str, Dict[int, float]]] = {}

        # Max history length
        self.max_history = 1000

        self.logger.info(
            "MA Indicator Agent initialized",
            periods=self.periods
        )

    async def start(self):
        """Start the MA indicator agent."""
        await super().start()

        # Subscribe to price updates
        await self.subscribe("market.price.*", self._handle_price_update)

        # Subscribe to historical data requests
        await self.subscribe("indicator.ma.request", self._handle_request)

        self.logger.info("MA Indicator Agent started")

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
                self.current_values[pair] = {"SMA": {}, "EMA": {}, "WMA": {}}
                self.previous_values[pair] = {"SMA": {}, "EMA": {}, "WMA": {}}
                self.ma_history[pair] = {
                    "SMA": {p: deque(maxlen=self.max_history) for p in self.periods},
                    "EMA": {p: deque(maxlen=self.max_history) for p in self.periods},
                    "WMA": {p: deque(maxlen=self.max_history) for p in self.periods},
                }

            # Add price to history
            self.price_history[pair].append(price)

            # Calculate MAs if we have enough data
            if len(self.price_history[pair]) >= min(self.periods):
                await self._calculate_mas(pair, price)
                await self._detect_crossovers(pair, price)

        except Exception as e:
            self.logger.error(
                "Error handling price update",
                error=str(e),
                pair=message.get("pair")
            )

    async def _calculate_mas(self, pair: str, current_price: float):
        """
        Calculate all moving averages for a pair.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        prices = list(self.price_history[pair])
        timestamp = datetime.utcnow()

        # Store previous values for crossover detection
        for ma_type in ["SMA", "EMA", "WMA"]:
            for period in self.periods:
                if period in self.current_values[pair][ma_type]:
                    self.previous_values[pair][ma_type][period] = \
                        self.current_values[pair][ma_type][period]

        # Calculate each MA type
        for period in self.periods:
            if len(prices) >= period:
                # Simple Moving Average (SMA)
                sma = np.mean(prices[-period:])
                self.current_values[pair]["SMA"][period] = sma

                ma_value = MAValue(
                    pair=pair,
                    ma_type="SMA",
                    period=period,
                    value=sma,
                    timestamp=timestamp
                )
                self.ma_history[pair]["SMA"][period].append(ma_value)

                # Exponential Moving Average (EMA)
                ema = self._calculate_ema(prices, period)
                self.current_values[pair]["EMA"][period] = ema

                ema_value = MAValue(
                    pair=pair,
                    ma_type="EMA",
                    period=period,
                    value=ema,
                    timestamp=timestamp
                )
                self.ma_history[pair]["EMA"][period].append(ema_value)

                # Weighted Moving Average (WMA)
                wma = self._calculate_wma(prices[-period:])
                self.current_values[pair]["WMA"][period] = wma

                wma_value = MAValue(
                    pair=pair,
                    ma_type="WMA",
                    period=period,
                    value=wma,
                    timestamp=timestamp
                )
                self.ma_history[pair]["WMA"][period].append(wma_value)

        # Broadcast current values
        await self._broadcast_values(pair, current_price)

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """
        Calculate Exponential Moving Average.

        Args:
            prices: Price history
            period: EMA period

        Returns:
            EMA value
        """
        if len(prices) < period:
            return np.mean(prices)

        multiplier = 2 / (period + 1)
        ema = np.mean(prices[:period])  # Start with SMA

        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _calculate_wma(self, prices: List[float]) -> float:
        """
        Calculate Weighted Moving Average.

        Args:
            prices: Price window

        Returns:
            WMA value
        """
        weights = np.arange(1, len(prices) + 1)
        wma = np.average(prices, weights=weights)
        return wma

    async def _detect_crossovers(self, pair: str, current_price: float):
        """
        Detect MA crossovers and generate signals.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        timestamp = datetime.utcnow()

        # Check golden cross (50 crosses above 200) and death cross (50 crosses below 200)
        if 50 in self.current_values[pair]["SMA"] and 200 in self.current_values[pair]["SMA"]:
            ma_50_current = self.current_values[pair]["SMA"][50]
            ma_200_current = self.current_values[pair]["SMA"][200]

            if 50 in self.previous_values[pair]["SMA"] and 200 in self.previous_values[pair]["SMA"]:
                ma_50_prev = self.previous_values[pair]["SMA"][50]
                ma_200_prev = self.previous_values[pair]["SMA"][200]

                # Golden Cross: 50 crosses above 200
                if ma_50_prev <= ma_200_prev and ma_50_current > ma_200_current:
                    strength = min(100, abs((ma_50_current - ma_200_current) / ma_200_current) * 1000)

                    signal = MASignal(
                        pair=pair,
                        signal_type="golden_cross",
                        fast_ma=50,
                        slow_ma=200,
                        price=current_price,
                        timestamp=timestamp,
                        strength=strength
                    )

                    await self._broadcast_signal(signal)

                # Death Cross: 50 crosses below 200
                elif ma_50_prev >= ma_200_prev and ma_50_current < ma_200_current:
                    strength = min(100, abs((ma_50_current - ma_200_current) / ma_200_current) * 1000)

                    signal = MASignal(
                        pair=pair,
                        signal_type="death_cross",
                        fast_ma=50,
                        slow_ma=200,
                        price=current_price,
                        timestamp=timestamp,
                        strength=strength
                    )

                    await self._broadcast_signal(signal)

        # Check price crossing 20 MA (common trading signal)
        if 20 in self.current_values[pair]["EMA"]:
            ma_20 = self.current_values[pair]["EMA"][20]

            if 20 in self.previous_values[pair]["EMA"]:
                ma_20_prev = self.previous_values[pair]["EMA"][20]

                # Price crosses above MA (bullish)
                if current_price > ma_20 and len(self.price_history[pair]) > 1:
                    prev_price = list(self.price_history[pair])[-2]

                    if prev_price <= ma_20_prev:
                        strength = min(100, abs((current_price - ma_20) / ma_20) * 500)

                        signal = MASignal(
                            pair=pair,
                            signal_type="price_cross_up",
                            fast_ma=0,  # 0 indicates price
                            slow_ma=20,
                            price=current_price,
                            timestamp=timestamp,
                            strength=strength
                        )

                        await self._broadcast_signal(signal)

    async def _broadcast_values(self, pair: str, current_price: float):
        """
        Broadcast current MA values.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        # Prepare data for broadcast
        values_data = {
            "pair": pair,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "mas": {}
        }

        for ma_type in ["SMA", "EMA", "WMA"]:
            values_data["mas"][ma_type] = {}
            for period in self.periods:
                if period in self.current_values[pair][ma_type]:
                    values_data["mas"][ma_type][period] = round(
                        self.current_values[pair][ma_type][period], 2
                    )

        # Broadcast to event bus
        await self.publish(
            f"indicator.ma.values.{pair}",
            {
                "type": "ma_values",
                "data": values_data
            }
        )

    async def _broadcast_signal(self, signal: MASignal):
        """
        Broadcast MA crossover signal.

        Args:
            signal: MA signal
        """
        self.logger.info(
            "MA signal detected",
            pair=signal.pair,
            signal_type=signal.signal_type,
            strength=signal.strength
        )

        # Broadcast to event bus
        await self.publish(
            f"signal.ma.{signal.pair}",
            {
                "type": "ma_signal",
                "data": signal.to_dict()
            }
        )

        # Also broadcast to general signals topic
        await self.publish(
            "signals.all",
            {
                "type": "ma_signal",
                "indicator": "MA",
                "data": signal.to_dict()
            }
        )

    async def _handle_request(self, message: Dict[str, Any]):
        """
        Handle request for MA data.

        Args:
            message: Request message
        """
        pair = message.get("pair")
        ma_type = message.get("ma_type", "EMA")
        period = message.get("period", 20)

        if not pair:
            return

        # Send current values
        if pair in self.current_values and ma_type in self.current_values[pair]:
            if period in self.current_values[pair][ma_type]:
                await self.publish(
                    message.get("reply_to", "indicator.ma.response"),
                    {
                        "pair": pair,
                        "ma_type": ma_type,
                        "period": period,
                        "value": self.current_values[pair][ma_type][period],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

    def get_current_values(self, pair: str) -> Optional[Dict[str, Dict[int, float]]]:
        """
        Get current MA values for a pair.

        Args:
            pair: Trading pair

        Returns:
            Current MA values
        """
        return self.current_values.get(pair)

    def get_history(self, pair: str, ma_type: str = "EMA", period: int = 20,
                    limit: int = 100) -> List[MAValue]:
        """
        Get MA history for charting.

        Args:
            pair: Trading pair
            ma_type: MA type
            period: MA period
            limit: Max number of points

        Returns:
            List of MA values
        """
        if pair not in self.ma_history:
            return []

        if ma_type not in self.ma_history[pair]:
            return []

        if period not in self.ma_history[pair][ma_type]:
            return []

        history = list(self.ma_history[pair][ma_type][period])
        return history[-limit:]
