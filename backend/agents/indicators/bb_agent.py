"""
Bollinger Bands Indicator Agent

Agent: Bollinger Bands Indicator Agent
Squad: Indicators
Sprint: 2.1 (Enhanced)

Calculates and broadcasts Bollinger Bands for volatility analysis.

Features:
- Upper band, middle band (SMA), lower band
- Bandwidth and %B calculations
- Squeeze and expansion signals
- Band touch/breakout signals
- Real-time WebSocket broadcasting

Agent: #11 Bollinger Bands Indicator Agent
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
from dataclasses import dataclass
import numpy as np
from agents.base_agent import BaseAgent


@dataclass
class BBValue:
    """Bollinger Bands value data point."""
    pair: str
    period: int
    upper_band: float
    middle_band: float
    lower_band: float
    bandwidth: float
    percent_b: float  # Current price position relative to bands (0-1)
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "period": self.period,
            "upper_band": self.upper_band,
            "middle_band": self.middle_band,
            "lower_band": self.lower_band,
            "bandwidth": self.bandwidth,
            "percent_b": self.percent_b,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BBSignal:
    """Bollinger Bands signal."""
    pair: str
    signal_type: str  # 'upper_touch', 'lower_touch', 'squeeze', 'expansion', 'breakout_up', 'breakout_down'
    price: float
    upper_band: float
    lower_band: float
    bandwidth: float
    timestamp: datetime
    strength: float  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "signal_type": self.signal_type,
            "price": self.price,
            "upper_band": self.upper_band,
            "lower_band": self.lower_band,
            "bandwidth": self.bandwidth,
            "timestamp": self.timestamp.isoformat(),
            "strength": self.strength,
        }


class BollingerBandsAgent(BaseAgent):
    """
    Bollinger Bands Indicator Agent.

    Calculates Bollinger Bands and detects volatility signals.

    BB = SMA ± (K × StdDev)
    where K is typically 2

    Responsibilities:
    - Calculate upper, middle, lower bands
    - Calculate bandwidth and %B
    - Detect squeezes (low volatility)
    - Detect expansions (high volatility)
    - Detect band touches and breakouts
    - Broadcast indicator values and signals
    """

    def __init__(self):
        super().__init__(
            agent_id="bb_indicator",
            agent_type="indicator"
        )

        # BB parameters
        self.periods = [20]  # Standard is 20
        self.std_multiplier = 2  # Standard is 2

        # Price history per pair: {pair: deque([prices])}
        self.price_history: Dict[str, deque] = {}

        # Current BB values: {pair: {period: BBValue}}
        self.current_values: Dict[str, Dict[int, BBValue]] = {}

        # BB history for charting: {pair: {period: deque([BBValue])}}
        self.bb_history: Dict[str, Dict[int, deque]] = {}

        # Previous values for signal detection
        self.previous_values: Dict[str, Dict[int, BBValue]] = {}

        # Max history length
        self.max_history = 1000

        self.logger.info(
            "Bollinger Bands Indicator Agent initialized",
            periods=self.periods,
            std_multiplier=self.std_multiplier
        )

    async def start(self):
        """Start the Bollinger Bands agent."""
        await super().start()

        # Subscribe to price updates
        await self.subscribe("market.price.*", self._handle_price_update)

        # Subscribe to historical data requests
        await self.subscribe("indicator.bb.request", self._handle_request)

        self.logger.info("Bollinger Bands Indicator Agent started")

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
                self.bb_history[pair] = {
                    p: deque(maxlen=self.max_history) for p in self.periods
                }

            # Add price to history
            self.price_history[pair].append(price)

            # Calculate BB if we have enough data
            if len(self.price_history[pair]) >= min(self.periods):
                await self._calculate_bb(pair, price)
                await self._detect_signals(pair, price)

        except Exception as e:
            self.logger.error(
                "Error handling price update",
                error=str(e),
                pair=message.get("pair")
            )

    async def _calculate_bb(self, pair: str, current_price: float):
        """
        Calculate Bollinger Bands.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        prices = np.array(list(self.price_history[pair]))
        timestamp = datetime.utcnow()

        for period in self.periods:
            if len(prices) < period:
                continue

            # Store previous value
            if period in self.current_values[pair]:
                self.previous_values[pair][period] = self.current_values[pair][period]

            # Calculate middle band (SMA)
            middle_band = np.mean(prices[-period:])

            # Calculate standard deviation
            std_dev = np.std(prices[-period:])

            # Calculate upper and lower bands
            upper_band = middle_band + (self.std_multiplier * std_dev)
            lower_band = middle_band - (self.std_multiplier * std_dev)

            # Calculate bandwidth (volatility measure)
            bandwidth = (upper_band - lower_band) / middle_band * 100

            # Calculate %B (price position within bands)
            if upper_band != lower_band:
                percent_b = (current_price - lower_band) / (upper_band - lower_band)
            else:
                percent_b = 0.5

            # Create BB value
            bb_value = BBValue(
                pair=pair,
                period=period,
                upper_band=upper_band,
                middle_band=middle_band,
                lower_band=lower_band,
                bandwidth=bandwidth,
                percent_b=percent_b,
                timestamp=timestamp
            )

            # Store current value
            self.current_values[pair][period] = bb_value

            # Add to history
            self.bb_history[pair][period].append(bb_value)

        # Broadcast current values
        await self._broadcast_values(pair, current_price)

    async def _detect_signals(self, pair: str, current_price: float):
        """
        Detect Bollinger Bands signals.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        # Use 20-period as primary
        if 20 not in self.current_values[pair]:
            return

        current = self.current_values[pair][20]
        timestamp = datetime.utcnow()

        # Band touch signals
        # Price touching upper band (potential reversal down)
        if current_price >= current.upper_band * 0.998:  # Within 0.2%
            strength = min(100, (current_price - current.upper_band) / current.upper_band * 500)

            signal = BBSignal(
                pair=pair,
                signal_type="upper_touch",
                price=current_price,
                upper_band=current.upper_band,
                lower_band=current.lower_band,
                bandwidth=current.bandwidth,
                timestamp=timestamp,
                strength=max(50, strength)
            )

            await self._broadcast_signal(signal)

        # Price touching lower band (potential reversal up)
        elif current_price <= current.lower_band * 1.002:  # Within 0.2%
            strength = min(100, (current.lower_band - current_price) / current.lower_band * 500)

            signal = BBSignal(
                pair=pair,
                signal_type="lower_touch",
                price=current_price,
                upper_band=current.upper_band,
                lower_band=current.lower_band,
                bandwidth=current.bandwidth,
                timestamp=timestamp,
                strength=max(50, strength)
            )

            await self._broadcast_signal(signal)

        # Squeeze detection (low volatility)
        if 20 in self.previous_values[pair]:
            previous = self.previous_values[pair][20]

            # Bandwidth shrinking significantly
            if current.bandwidth < 5 and previous.bandwidth >= 5:
                signal = BBSignal(
                    pair=pair,
                    signal_type="squeeze",
                    price=current_price,
                    upper_band=current.upper_band,
                    lower_band=current.lower_band,
                    bandwidth=current.bandwidth,
                    timestamp=timestamp,
                    strength=80.0
                )

                await self._broadcast_signal(signal)

            # Expansion (volatility increasing)
            elif current.bandwidth > previous.bandwidth * 1.5 and current.bandwidth > 10:
                signal = BBSignal(
                    pair=pair,
                    signal_type="expansion",
                    price=current_price,
                    upper_band=current.upper_band,
                    lower_band=current.lower_band,
                    bandwidth=current.bandwidth,
                    timestamp=timestamp,
                    strength=75.0
                )

                await self._broadcast_signal(signal)

        # Breakout signals
        if len(self.price_history[pair]) >= 2:
            prices = list(self.price_history[pair])
            prev_price = prices[-2]

            # Breakout above upper band
            if prev_price <= current.upper_band and current_price > current.upper_band:
                strength = min(100, (current_price - current.upper_band) / current.upper_band * 300)

                signal = BBSignal(
                    pair=pair,
                    signal_type="breakout_up",
                    price=current_price,
                    upper_band=current.upper_band,
                    lower_band=current.lower_band,
                    bandwidth=current.bandwidth,
                    timestamp=timestamp,
                    strength=max(60, strength)
                )

                await self._broadcast_signal(signal)

            # Breakout below lower band
            elif prev_price >= current.lower_band and current_price < current.lower_band:
                strength = min(100, (current.lower_band - current_price) / current.lower_band * 300)

                signal = BBSignal(
                    pair=pair,
                    signal_type="breakout_down",
                    price=current_price,
                    upper_band=current.upper_band,
                    lower_band=current.lower_band,
                    bandwidth=current.bandwidth,
                    timestamp=timestamp,
                    strength=max(60, strength)
                )

                await self._broadcast_signal(signal)

    async def _broadcast_values(self, pair: str, current_price: float):
        """
        Broadcast current BB values.

        Args:
            pair: Trading pair
            current_price: Current price
        """
        values_data = {
            "pair": pair,
            "price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "bb": {}
        }

        for period in self.periods:
            if period in self.current_values[pair]:
                bb = self.current_values[pair][period]
                values_data["bb"][period] = {
                    "upper_band": round(bb.upper_band, 2),
                    "middle_band": round(bb.middle_band, 2),
                    "lower_band": round(bb.lower_band, 2),
                    "bandwidth": round(bb.bandwidth, 2),
                    "percent_b": round(bb.percent_b, 3),
                }

        # Broadcast to event bus
        await self.publish(
            f"indicator.bb.values.{pair}",
            {
                "type": "bb_values",
                "data": values_data
            }
        )

    async def _broadcast_signal(self, signal: BBSignal):
        """
        Broadcast BB signal.

        Args:
            signal: BB signal
        """
        self.logger.info(
            "Bollinger Bands signal detected",
            pair=signal.pair,
            signal_type=signal.signal_type,
            bandwidth=signal.bandwidth,
            strength=signal.strength
        )

        # Broadcast to event bus
        await self.publish(
            f"signal.bb.{signal.pair}",
            {
                "type": "bb_signal",
                "data": signal.to_dict()
            }
        )

        # Also broadcast to general signals topic
        await self.publish(
            "signals.all",
            {
                "type": "bb_signal",
                "indicator": "BB",
                "data": signal.to_dict()
            }
        )

    async def _handle_request(self, message: Dict[str, Any]):
        """
        Handle request for BB data.

        Args:
            message: Request message
        """
        pair = message.get("pair")
        period = message.get("period", 20)

        if not pair:
            return

        # Send current values
        if pair in self.current_values and period in self.current_values[pair]:
            bb = self.current_values[pair][period]

            await self.publish(
                message.get("reply_to", "indicator.bb.response"),
                {
                    "pair": pair,
                    "period": period,
                    "upper_band": bb.upper_band,
                    "middle_band": bb.middle_band,
                    "lower_band": bb.lower_band,
                    "bandwidth": bb.bandwidth,
                    "percent_b": bb.percent_b,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    def get_current_value(self, pair: str, period: int = 20) -> Optional[BBValue]:
        """
        Get current BB value for a pair.

        Args:
            pair: Trading pair
            period: BB period

        Returns:
            Current BB value
        """
        if pair in self.current_values and period in self.current_values[pair]:
            return self.current_values[pair][period]
        return None

    def get_history(self, pair: str, period: int = 20, limit: int = 100) -> List[BBValue]:
        """
        Get BB history for charting.

        Args:
            pair: Trading pair
            period: BB period
            limit: Max number of points

        Returns:
            List of BB values
        """
        if pair not in self.bb_history or period not in self.bb_history[pair]:
            return []

        history = list(self.bb_history[pair][period])
        return history[-limit:]
