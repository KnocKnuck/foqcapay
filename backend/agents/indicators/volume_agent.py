"""
Volume Indicator Agent

Agent: Volume Indicator Agent
Squad: Indicators
Sprint: 2.1 (Enhanced)

Analyzes trading volume and detects volume-based signals.

Features:
- Volume moving averages
- Volume spikes detection
- Volume trend analysis
- On-Balance Volume (OBV)
- Volume-price divergence
- Real-time WebSocket broadcasting

Agent: #12 Volume Indicator Agent
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
from dataclasses import dataclass
import numpy as np
from agents.base_agent import BaseAgent


@dataclass
class VolumeValue:
    """Volume indicator value data point."""
    pair: str
    volume: float
    volume_ma: float  # Volume moving average
    volume_ratio: float  # Current volume / MA
    obv: float  # On-Balance Volume
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "volume": self.volume,
            "volume_ma": self.volume_ma,
            "volume_ratio": self.volume_ratio,
            "obv": self.obv,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class VolumeSignal:
    """Volume signal."""
    pair: str
    signal_type: str  # 'volume_spike', 'high_volume_buy', 'high_volume_sell', 'obv_divergence_bullish', 'obv_divergence_bearish'
    volume: float
    volume_ma: float
    volume_ratio: float
    price: float
    timestamp: datetime
    strength: float  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "signal_type": self.signal_type,
            "volume": self.volume,
            "volume_ma": self.volume_ma,
            "volume_ratio": self.volume_ratio,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "strength": self.strength,
        }


class VolumeIndicatorAgent(BaseAgent):
    """
    Volume Indicator Agent.

    Analyzes trading volume patterns and generates volume-based signals.

    Responsibilities:
    - Track volume and volume moving average
    - Detect volume spikes
    - Calculate On-Balance Volume (OBV)
    - Detect volume-price divergences
    - Identify accumulation/distribution phases
    - Broadcast indicator values and signals
    """

    def __init__(self):
        super().__init__(
            agent_id="volume_indicator",
            agent_type="indicator"
        )

        # Volume MA period
        self.volume_ma_period = 20

        # Spike threshold (volume > MA * threshold)
        self.spike_threshold = 2.0

        # Data storage per pair
        self.price_history: Dict[str, deque] = {}
        self.volume_history: Dict[str, deque] = {}

        # Current values: {pair: VolumeValue}
        self.current_values: Dict[str, VolumeValue] = {}

        # Volume history for charting: {pair: deque([VolumeValue])}
        self.volume_value_history: Dict[str, deque] = {}

        # Previous values for signal detection
        self.previous_values: Dict[str, VolumeValue] = {}

        # OBV tracking
        self.obv: Dict[str, float] = {}

        # Max history length
        self.max_history = 1000

        self.logger.info(
            "Volume Indicator Agent initialized",
            volume_ma_period=self.volume_ma_period,
            spike_threshold=self.spike_threshold
        )

    async def start(self):
        """Start the Volume indicator agent."""
        await super().start()

        # Subscribe to price updates
        await self.subscribe("market.price.*", self._handle_price_update)

        # Subscribe to volume updates (if separate)
        await self.subscribe("market.volume.*", self._handle_volume_update)

        # Subscribe to historical data requests
        await self.subscribe("indicator.volume.request", self._handle_request)

        self.logger.info("Volume Indicator Agent started")

    async def _handle_price_update(self, message: Dict[str, Any]):
        """
        Handle incoming price updates.

        Args:
            message: Price update message (may include volume)
        """
        try:
            pair = message.get("pair")
            price = float(message.get("price", 0))
            volume = float(message.get("volume", 0))

            if not pair or price <= 0:
                return

            # Initialize structures for new pair
            if pair not in self.price_history:
                self.price_history[pair] = deque(maxlen=self.volume_ma_period + 100)
                self.volume_history[pair] = deque(maxlen=self.volume_ma_period + 100)
                self.volume_value_history[pair] = deque(maxlen=self.max_history)
                self.obv[pair] = 0.0

            # Add price to history
            self.price_history[pair].append(price)

            # If volume included in price update, process it
            if volume > 0:
                self.volume_history[pair].append(volume)

                if len(self.volume_history[pair]) >= self.volume_ma_period:
                    await self._calculate_volume_indicators(pair, price, volume)
                    await self._detect_signals(pair, price, volume)

        except Exception as e:
            self.logger.error(
                "Error handling price update",
                error=str(e),
                pair=message.get("pair")
            )

    async def _handle_volume_update(self, message: Dict[str, Any]):
        """
        Handle separate volume updates.

        Args:
            message: Volume update message
        """
        try:
            pair = message.get("pair")
            volume = float(message.get("volume", 0))

            if not pair or volume <= 0:
                return

            # Initialize if needed
            if pair not in self.volume_history:
                self.volume_history[pair] = deque(maxlen=self.volume_ma_period + 100)
                self.volume_value_history[pair] = deque(maxlen=self.max_history)
                self.obv[pair] = 0.0

            self.volume_history[pair].append(volume)

            # Get current price
            if pair in self.price_history and len(self.price_history[pair]) > 0:
                current_price = list(self.price_history[pair])[-1]

                if len(self.volume_history[pair]) >= self.volume_ma_period:
                    await self._calculate_volume_indicators(pair, current_price, volume)
                    await self._detect_signals(pair, current_price, volume)

        except Exception as e:
            self.logger.error(
                "Error handling volume update",
                error=str(e),
                pair=message.get("pair")
            )

    async def _calculate_volume_indicators(self, pair: str, current_price: float, current_volume: float):
        """
        Calculate volume indicators.

        Args:
            pair: Trading pair
            current_price: Current price
            current_volume: Current volume
        """
        volumes = np.array(list(self.volume_history[pair]))
        timestamp = datetime.utcnow()

        # Store previous value
        if pair in self.current_values:
            self.previous_values[pair] = self.current_values[pair]

        # Calculate volume moving average
        volume_ma = np.mean(volumes[-self.volume_ma_period:])

        # Calculate volume ratio (current volume relative to average)
        volume_ratio = current_volume / volume_ma if volume_ma > 0 else 1.0

        # Update On-Balance Volume (OBV)
        if pair in self.price_history and len(self.price_history[pair]) >= 2:
            prices = list(self.price_history[pair])
            prev_price = prices[-2]

            if current_price > prev_price:
                # Price up: add volume
                self.obv[pair] += current_volume
            elif current_price < prev_price:
                # Price down: subtract volume
                self.obv[pair] -= current_volume
            # If price unchanged, OBV unchanged

        # Create volume value
        volume_value = VolumeValue(
            pair=pair,
            volume=current_volume,
            volume_ma=volume_ma,
            volume_ratio=volume_ratio,
            obv=self.obv[pair],
            timestamp=timestamp
        )

        # Store current value
        self.current_values[pair] = volume_value

        # Add to history
        self.volume_value_history[pair].append(volume_value)

        # Broadcast current values
        await self._broadcast_values(pair, current_price)

    async def _detect_signals(self, pair: str, current_price: float, current_volume: float):
        """
        Detect volume-based signals.

        Args:
            pair: Trading pair
            current_price: Current price
            current_volume: Current volume
        """
        if pair not in self.current_values:
            return

        current = self.current_values[pair]
        timestamp = datetime.utcnow()

        # Volume spike detection
        if current.volume_ratio >= self.spike_threshold:
            strength = min(100, current.volume_ratio / self.spike_threshold * 50)

            # Determine if spike is on buy or sell
            if len(self.price_history[pair]) >= 2:
                prices = list(self.price_history[pair])
                prev_price = prices[-2]

                if current_price > prev_price:
                    # High volume on price increase (buying)
                    signal = VolumeSignal(
                        pair=pair,
                        signal_type="high_volume_buy",
                        volume=current.volume,
                        volume_ma=current.volume_ma,
                        volume_ratio=current.volume_ratio,
                        price=current_price,
                        timestamp=timestamp,
                        strength=strength
                    )

                    await self._broadcast_signal(signal)

                elif current_price < prev_price:
                    # High volume on price decrease (selling)
                    signal = VolumeSignal(
                        pair=pair,
                        signal_type="high_volume_sell",
                        volume=current.volume,
                        volume_ma=current.volume_ma,
                        volume_ratio=current.volume_ratio,
                        price=current_price,
                        timestamp=timestamp,
                        strength=strength
                    )

                    await self._broadcast_signal(signal)

                else:
                    # Generic volume spike
                    signal = VolumeSignal(
                        pair=pair,
                        signal_type="volume_spike",
                        volume=current.volume,
                        volume_ma=current.volume_ma,
                        volume_ratio=current.volume_ratio,
                        price=current_price,
                        timestamp=timestamp,
                        strength=strength
                    )

                    await self._broadcast_signal(signal)

        # OBV divergence detection
        await self._detect_obv_divergence(pair, current_price, current)

    async def _detect_obv_divergence(self, pair: str, current_price: float, current_volume: VolumeValue):
        """
        Detect OBV divergences.

        Args:
            pair: Trading pair
            current_price: Current price
            current_volume: Current volume value
        """
        # Need significant history
        if len(self.price_history[pair]) < 50 or len(self.volume_value_history[pair]) < 50:
            return

        prices = list(self.price_history[pair])
        volume_history = list(self.volume_value_history[pair])

        # Look at last 20 bars
        price_window = prices[-20:]
        obv_window = [v.obv for v in volume_history[-20:]]

        # Bullish divergence: Price lower low, OBV higher low
        price_lows = []
        obv_lows = []

        for i in range(1, len(price_window) - 1):
            if price_window[i] < price_window[i-1] and price_window[i] < price_window[i+1]:
                price_lows.append((i, price_window[i]))

            if obv_window[i] < obv_window[i-1] and obv_window[i] < obv_window[i+1]:
                obv_lows.append((i, obv_window[i]))

        if len(price_lows) >= 2 and len(obv_lows) >= 2:
            # Price making lower low
            if price_lows[-1][1] < price_lows[-2][1]:
                # OBV making higher low
                if obv_lows[-1][1] > obv_lows[-2][1]:
                    signal = VolumeSignal(
                        pair=pair,
                        signal_type="obv_divergence_bullish",
                        volume=current_volume.volume,
                        volume_ma=current_volume.volume_ma,
                        volume_ratio=current_volume.volume_ratio,
                        price=current_price,
                        timestamp=datetime.utcnow(),
                        strength=75.0
                    )

                    await self._broadcast_signal(signal)

        # Bearish divergence: Price higher high, OBV lower high
        price_highs = []
        obv_highs = []

        for i in range(1, len(price_window) - 1):
            if price_window[i] > price_window[i-1] and price_window[i] > price_window[i+1]:
                price_highs.append((i, price_window[i]))

            if obv_window[i] > obv_window[i-1] and obv_window[i] > obv_window[i+1]:
                obv_highs.append((i, obv_window[i]))

        if len(price_highs) >= 2 and len(obv_highs) >= 2:
            # Price making higher high
            if price_highs[-1][1] > price_highs[-2][1]:
                # OBV making lower high
                if obv_highs[-1][1] < obv_highs[-2][1]:
                    signal = VolumeSignal(
                        pair=pair,
                        signal_type="obv_divergence_bearish",
                        volume=current_volume.volume,
                        volume_ma=current_volume.volume_ma,
                        volume_ratio=current_volume.volume_ratio,
                        price=current_price,
                        timestamp=datetime.utcnow(),
                        strength=75.0
                    )

                    await self._broadcast_signal(signal)

    async def _broadcast_values(self, pair: str, current_price: float):
        """
        Broadcast current volume values.

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
            "volume_indicators": {
                "volume": round(current.volume, 2),
                "volume_ma": round(current.volume_ma, 2),
                "volume_ratio": round(current.volume_ratio, 2),
                "obv": round(current.obv, 2),
            }
        }

        # Broadcast to event bus
        await self.publish(
            f"indicator.volume.values.{pair}",
            {
                "type": "volume_values",
                "data": values_data
            }
        )

    async def _broadcast_signal(self, signal: VolumeSignal):
        """
        Broadcast volume signal.

        Args:
            signal: Volume signal
        """
        self.logger.info(
            "Volume signal detected",
            pair=signal.pair,
            signal_type=signal.signal_type,
            volume_ratio=signal.volume_ratio,
            strength=signal.strength
        )

        # Broadcast to event bus
        await self.publish(
            f"signal.volume.{signal.pair}",
            {
                "type": "volume_signal",
                "data": signal.to_dict()
            }
        )

        # Also broadcast to general signals topic
        await self.publish(
            "signals.all",
            {
                "type": "volume_signal",
                "indicator": "VOLUME",
                "data": signal.to_dict()
            }
        )

    async def _handle_request(self, message: Dict[str, Any]):
        """
        Handle request for volume data.

        Args:
            message: Request message
        """
        pair = message.get("pair")

        if not pair or pair not in self.current_values:
            return

        # Send current values
        current = self.current_values[pair]

        await self.publish(
            message.get("reply_to", "indicator.volume.response"),
            {
                "pair": pair,
                "volume": current.volume,
                "volume_ma": current.volume_ma,
                "volume_ratio": current.volume_ratio,
                "obv": current.obv,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def get_current_value(self, pair: str) -> Optional[VolumeValue]:
        """
        Get current volume value for a pair.

        Args:
            pair: Trading pair

        Returns:
            Current volume value
        """
        return self.current_values.get(pair)

    def get_history(self, pair: str, limit: int = 100) -> List[VolumeValue]:
        """
        Get volume history for charting.

        Args:
            pair: Trading pair
            limit: Max number of points

        Returns:
            List of volume values
        """
        if pair not in self.volume_value_history:
            return []

        history = list(self.volume_value_history[pair])
        return history[-limit:]
