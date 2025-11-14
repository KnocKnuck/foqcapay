"""
Risk Manager Agent - Comprehensive Risk Controls

Agent: Risk Manager Agent
Squad: Execution
Sprint: 3.2

Implements comprehensive risk management:
- Max drawdown protection
- Daily loss limits
- ATR-based stop-loss (volatility-adjusted)
- Position sizing
- Risk alerts
- Emergency stop functionality

Agent: #22 Risk Manager Agent
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from agents.base_agent import BaseAgent


class RiskLevel(str, Enum):
    """Risk level severity."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskLimits:
    """Risk limit configuration."""
    max_drawdown_pct: float = 10.0  # Max 10% drawdown
    daily_loss_limit_pct: float = 5.0  # Max 5% daily loss
    max_position_size_pct: float = 20.0  # Max 20% portfolio per position
    max_open_positions: int = 5
    default_stop_loss_pct: float = 2.0
    default_take_profit_pct: float = 3.0
    atr_multiplier: float = 2.0  # ATR-based stop: 2x ATR


@dataclass
class PositionRisk:
    """Risk metrics for an open position."""
    pair: str
    entry_price: float
    current_price: float
    position_size: float
    stop_loss: float
    take_profit: float
    unrealized_pnl: float
    risk_amount: float
    risk_reward_ratio: float


class RiskManagerAgent(BaseAgent):
    """
    Manages all risk controls for the trading system.

    Responsibilities:
    - Enforce max drawdown limits
    - Enforce daily loss limits
    - Calculate ATR-based stop-loss levels
    - Monitor position sizes
    - Send risk alerts
    - Execute emergency stops
    - Track realized & unrealized P&L
    """

    def __init__(self, initial_capital: float = 10000.0):
        super().__init__(
            agent_id="risk_manager",
            agent_type="risk_manager"
        )

        # Risk configuration
        self.limits = RiskLimits()

        # Capital tracking
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital

        # P&L tracking
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.daily_pnl = 0.0
        self.daily_reset_time = datetime.utcnow().replace(hour=0, minute=0, second=0)

        # Position tracking
        self.open_positions: Dict[str, PositionRisk] = {}

        # Risk state
        self.emergency_stop_active = False
        self.trading_paused = False
        self.current_risk_level = RiskLevel.LOW

        # ATR cache (from technical indicator agents)
        self.atr_values: Dict[str, float] = {}

        # Metrics
        self.metrics = {
            "max_drawdown_hit": 0,
            "daily_limit_hit": 0,
            "risk_alerts_sent": 0,
            "emergency_stops": 0,
            "positions_rejected": 0,
        }

        self.logger.info(f"Risk Manager initialized with ${initial_capital:.2f} capital")

    async def start(self):
        """Start the risk manager agent."""
        await super().start()

        # Subscribe to trade signals
        await self.subscribe("signal.entry", self._handle_entry_signal)
        await self.subscribe("signal.exit", self._handle_exit_signal)

        # Subscribe to position updates
        await self.subscribe("position.opened", self._handle_position_opened)
        await self.subscribe("position.closed", self._handle_position_closed)
        await self.subscribe("position.updated", self._handle_position_updated)

        # Subscribe to market data for unrealized P&L
        await self.subscribe("market.*.tick", self._handle_market_tick)

        # Subscribe to ATR updates
        await self.subscribe("indicator.atr", self._handle_atr_update)

        # Subscribe to emergency commands
        await self.subscribe("risk.emergency_stop", self._handle_emergency_stop)

        # Start monitoring loop
        self.create_task(self._risk_monitoring_loop())

        # Start daily reset loop
        self.create_task(self._daily_reset_loop())

        await self._publish_status()

        self.logger.info("Risk Manager started - all protection systems active")

    def calculate_position_size(self, pair: str, risk_per_trade_pct: float = 1.0) -> float:
        """
        Calculate position size based on risk percentage.

        Args:
            pair: Trading pair
            risk_per_trade_pct: % of capital to risk (default 1%)

        Returns:
            Position size in base currency
        """
        risk_amount = self.current_capital * (risk_per_trade_pct / 100)

        # Apply max position size limit
        max_position = self.current_capital * (self.limits.max_position_size_pct / 100)

        position_size = min(risk_amount, max_position)

        return position_size

    def calculate_atr_stop_loss(self, pair: str, entry_price: float, is_long: bool = True) -> float:
        """
        Calculate ATR-based stop-loss level.

        Args:
            pair: Trading pair
            entry_price: Entry price
            is_long: True for long, False for short

        Returns:
            Stop-loss price
        """
        atr = self.atr_values.get(pair, 0)

        if atr == 0:
            # Fallback to default percentage if ATR not available
            stop_distance = entry_price * (self.limits.default_stop_loss_pct / 100)
        else:
            # ATR-based: 2x ATR
            stop_distance = atr * self.limits.atr_multiplier

        if is_long:
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance

        return stop_loss

    def check_drawdown(self) -> tuple[bool, float]:
        """
        Check if max drawdown limit is breached.

        Returns:
            (is_breached, current_drawdown_pct)
        """
        drawdown = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
        is_breached = drawdown >= self.limits.max_drawdown_pct

        return is_breached, drawdown

    def check_daily_loss(self) -> tuple[bool, float]:
        """
        Check if daily loss limit is breached.

        Returns:
            (is_breached, daily_loss_pct)
        """
        daily_loss_pct = (self.daily_pnl / self.initial_capital) * 100
        is_breached = daily_loss_pct <= -self.limits.daily_loss_limit_pct

        return is_breached, daily_loss_pct

    async def _handle_entry_signal(self, event):
        """Validate entry signals against risk limits."""
        pair = event.data.get("pair")
        entry_price = event.data.get("price")
        is_long = event.data.get("side") == "buy"

        # Check if trading is paused
        if self.trading_paused or self.emergency_stop_active:
            self.metrics["positions_rejected"] += 1
            await self._send_alert(
                RiskLevel.CRITICAL,
                f"Entry signal rejected for {pair} - trading paused"
            )
            return

        # Check max positions
        if len(self.open_positions) >= self.limits.max_open_positions:
            self.metrics["positions_rejected"] += 1
            await self._send_alert(
                RiskLevel.HIGH,
                f"Entry signal rejected for {pair} - max positions ({self.limits.max_open_positions}) reached"
            )
            return

        # Check drawdown
        drawdown_breached, drawdown = self.check_drawdown()
        if drawdown_breached:
            self.metrics["positions_rejected"] += 1
            self.metrics["max_drawdown_hit"] += 1
            await self._send_alert(
                RiskLevel.CRITICAL,
                f"Entry signal rejected for {pair} - max drawdown ({drawdown:.2f}%) exceeded"
            )
            await self._pause_trading()
            return

        # Check daily loss
        daily_loss_breached, daily_loss = self.check_daily_loss()
        if daily_loss_breached:
            self.metrics["positions_rejected"] += 1
            self.metrics["daily_limit_hit"] += 1
            await self._send_alert(
                RiskLevel.CRITICAL,
                f"Entry signal rejected for {pair} - daily loss limit ({daily_loss:.2f}%) exceeded"
            )
            await self._pause_trading()
            return

        # Calculate risk parameters
        position_size = self.calculate_position_size(pair, risk_per_trade_pct=1.0)
        stop_loss = self.calculate_atr_stop_loss(pair, entry_price, is_long)

        # Calculate take profit (default 1.5:1 risk/reward)
        risk_distance = abs(entry_price - stop_loss)
        if is_long:
            take_profit = entry_price + (risk_distance * 1.5)
        else:
            take_profit = entry_price - (risk_distance * 1.5)

        # Approve signal with risk parameters
        await self.publish(
            "signal.approved",
            {
                "pair": pair,
                "entry_price": entry_price,
                "side": "buy" if is_long else "sell",
                "position_size": position_size,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_amount": position_size * (risk_distance / entry_price),
                "risk_reward_ratio": 1.5,
            }
        )

        self.logger.info(f"Approved entry for {pair} with ATR-based SL: ${stop_loss:.2f}")

    async def _handle_position_opened(self, event):
        """Track opened position."""
        pair = event.data.get("pair")
        entry_price = event.data.get("entry_price")
        position_size = event.data.get("position_size")
        stop_loss = event.data.get("stop_loss")
        take_profit = event.data.get("take_profit")

        position_risk = PositionRisk(
            pair=pair,
            entry_price=entry_price,
            current_price=entry_price,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            unrealized_pnl=0.0,
            risk_amount=position_size * abs(entry_price - stop_loss) / entry_price,
            risk_reward_ratio=abs(take_profit - entry_price) / abs(entry_price - stop_loss)
        )

        self.open_positions[pair] = position_risk

        self.logger.info(f"Tracking position: {pair} @ ${entry_price:.2f}, R:R = {position_risk.risk_reward_ratio:.2f}")

    async def _handle_position_closed(self, event):
        """Update P&L when position closes."""
        pair = event.data.get("pair")
        pnl = event.data.get("pnl", 0.0)

        # Update realized P&L
        self.realized_pnl += pnl
        self.daily_pnl += pnl
        self.current_capital += pnl

        # Update peak capital
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        # Remove from open positions
        if pair in self.open_positions:
            del self.open_positions[pair]

        self.logger.info(f"Position closed: {pair}, P&L: ${pnl:.2f}, Capital: ${self.current_capital:.2f}")

    async def _handle_position_updated(self, event):
        """Update unrealized P&L for open positions."""
        pair = event.data.get("pair")
        current_price = event.data.get("current_price")
        unrealized_pnl = event.data.get("unrealized_pnl")

        if pair in self.open_positions:
            position = self.open_positions[pair]
            position.current_price = current_price
            position.unrealized_pnl = unrealized_pnl

            # NOTE: BUG-056 FIX - Do NOT include unrealized P&L in drawdown calculation
            # Drawdown should only use realized capital, not unrealized

    async def _handle_market_tick(self, event):
        """Update current prices for risk calculations."""
        # Extract pair from topic (e.g., "market.btcusdc.tick" -> "BTC/USDC")
        topic = event.topic
        pair_normalized = topic.split(".")[1] if "." in topic else ""

        # Convert back to standard format (e.g., "btcusdc" -> "BTC/USDC")
        if len(pair_normalized) >= 6:
            base = pair_normalized[:-4].upper()
            quote = pair_normalized[-4:].upper()
            pair = f"{base}/{quote}"

            if pair in self.open_positions:
                current_price = event.data.get("price", 0)
                position = self.open_positions[pair]

                # Calculate unrealized P&L
                price_change = current_price - position.entry_price
                position.unrealized_pnl = position.position_size * price_change / position.entry_price
                position.current_price = current_price

    async def _handle_atr_update(self, event):
        """Store ATR values for stop-loss calculation."""
        pair = event.data.get("pair")
        atr = event.data.get("atr")

        if pair and atr:
            self.atr_values[pair] = atr

    async def _handle_emergency_stop(self, event):
        """Execute emergency stop - close all positions immediately."""
        self.emergency_stop_active = True
        self.metrics["emergency_stops"] += 1

        await self._send_alert(
            RiskLevel.CRITICAL,
            f"🚨 EMERGENCY STOP ACTIVATED - Closing all {len(self.open_positions)} positions"
        )

        # Send close signals for all open positions
        for pair in list(self.open_positions.keys()):
            await self.publish(
                "signal.emergency_close",
                {
                    "pair": pair,
                    "reason": "emergency_stop",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        self.logger.critical("Emergency stop executed - all positions closing")

    async def _pause_trading(self):
        """Pause all trading due to risk breach."""
        self.trading_paused = True

        await self.publish(
            "risk.trading_paused",
            {
                "reason": "risk_limit_breached",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        self.logger.warning("Trading paused due to risk limit breach")

    async def _send_alert(self, level: RiskLevel, message: str):
        """Send risk alert."""
        self.metrics["risk_alerts_sent"] += 1

        await self.publish(
            f"risk.alert.{level.value}",
            {
                "level": level.value,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "current_capital": self.current_capital,
                "daily_pnl": self.daily_pnl,
            }
        )

        self.logger.warning(f"[{level.value.upper()}] {message}")

    async def _risk_monitoring_loop(self):
        """Continuously monitor risk levels."""
        while self.running:
            # Check drawdown
            drawdown_breached, drawdown = self.check_drawdown()

            if drawdown_breached and not self.trading_paused:
                await self._send_alert(
                    RiskLevel.CRITICAL,
                    f"Max drawdown breached: {drawdown:.2f}% (limit: {self.limits.max_drawdown_pct}%)"
                )
                await self._pause_trading()
            elif drawdown >= self.limits.max_drawdown_pct * 0.8:
                # Warning at 80% of limit
                self.current_risk_level = RiskLevel.HIGH
                await self._send_alert(
                    RiskLevel.HIGH,
                    f"Approaching max drawdown: {drawdown:.2f}% (limit: {self.limits.max_drawdown_pct}%)"
                )

            # Check daily loss
            daily_loss_breached, daily_loss_pct = self.check_daily_loss()

            if daily_loss_breached and not self.trading_paused:
                await self._send_alert(
                    RiskLevel.CRITICAL,
                    f"Daily loss limit breached: {daily_loss_pct:.2f}% (limit: -{self.limits.daily_loss_limit_pct}%)"
                )
                await self._pause_trading()
            elif daily_loss_pct <= -self.limits.daily_loss_limit_pct * 0.8:
                # Warning at 80% of limit
                self.current_risk_level = RiskLevel.HIGH
                await self._send_alert(
                    RiskLevel.HIGH,
                    f"Approaching daily loss limit: {daily_loss_pct:.2f}% (limit: -{self.limits.daily_loss_limit_pct}%)"
                )

            await asyncio.sleep(10)  # Check every 10 seconds

    async def _daily_reset_loop(self):
        """Reset daily metrics at midnight."""
        while self.running:
            now = datetime.utcnow()

            # Check if we've passed midnight
            if now >= self.daily_reset_time + timedelta(days=1):
                self.daily_pnl = 0.0
                self.daily_reset_time = now.replace(hour=0, minute=0, second=0)

                # Reset trading pause if it was due to daily limit
                if self.trading_paused and not self.check_drawdown()[0]:
                    self.trading_paused = False
                    await self.publish("risk.trading_resumed", {"reason": "daily_reset"})
                    self.logger.info("Trading resumed after daily reset")

                self.logger.info("Daily P&L reset")

            await asyncio.sleep(60)  # Check every minute

    async def _publish_status(self):
        """Publish current risk status."""
        drawdown_breached, drawdown = self.check_drawdown()
        daily_loss_breached, daily_loss = self.check_daily_loss()

        # Calculate total unrealized P&L
        total_unrealized = sum(pos.unrealized_pnl for pos in self.open_positions.values())

        status = {
            "capital": {
                "initial": self.initial_capital,
                "current": self.current_capital,
                "peak": self.peak_capital,
            },
            "pnl": {
                "realized": self.realized_pnl,
                "unrealized": total_unrealized,
                "daily": self.daily_pnl,
            },
            "risk": {
                "level": self.current_risk_level.value,
                "drawdown_pct": drawdown,
                "daily_loss_pct": daily_loss,
                "trading_paused": self.trading_paused,
                "emergency_stop": self.emergency_stop_active,
            },
            "positions": {
                "open": len(self.open_positions),
                "max": self.limits.max_open_positions,
                "details": [
                    {
                        "pair": pos.pair,
                        "unrealized_pnl": pos.unrealized_pnl,
                        "risk_amount": pos.risk_amount,
                    }
                    for pos in self.open_positions.values()
                ],
            },
            "limits": {
                "max_drawdown_pct": self.limits.max_drawdown_pct,
                "daily_loss_limit_pct": self.limits.daily_loss_limit_pct,
                "max_position_size_pct": self.limits.max_position_size_pct,
            },
            "metrics": self.metrics,
        }

        await self.publish("risk.manager.status", status)
