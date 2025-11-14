"""
Trade Execution Agent

Agent: Trade Execution Agent
Squad: Execution
Sprint: 3.2

Executes trades based on approved signals from Risk Manager.
Manages order placement, fills, and position tracking.

Features:
- Multi-pair order execution
- Trailing stop-loss (BUG-055 FIX: per-pair tracking)
- Take-profit management
- Position monitoring
- Demo mode & Live mode support

Agent: #21 Trade Execution Agent
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import ccxt
from agents.base_agent import BaseAgent
from core.config import settings


class OrderSide(str, Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Position:
    """Open position with trailing stop support."""
    pair: str
    side: OrderSide
    entry_price: float
    current_price: float
    position_size: float
    stop_loss: float
    take_profit: float
    trailing_stop_enabled: bool = True
    trailing_stop_distance: float = 0.0  # Distance in price units
    highest_price: float = 0.0  # For long positions
    lowest_price: float = 0.0  # For short positions (if needed)
    unrealized_pnl: float = 0.0
    entry_time: str = ""

    def __post_init__(self):
        if not self.entry_time:
            self.entry_time = datetime.utcnow().isoformat()

        # Initialize trailing stop tracking
        if self.side == OrderSide.BUY:
            self.highest_price = self.entry_price
            # Trailing stop distance is current stop distance
            self.trailing_stop_distance = self.entry_price - self.stop_loss
        else:
            self.lowest_price = self.entry_price
            self.trailing_stop_distance = self.stop_loss - self.entry_price


@dataclass
class Order:
    """Order record."""
    order_id: str
    pair: str
    side: OrderSide
    order_type: OrderType
    price: float
    size: float
    status: OrderStatus
    filled_price: Optional[float] = None
    filled_time: Optional[str] = None
    created_time: str = ""

    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.utcnow().isoformat()


class TradeExecutionAgent(BaseAgent):
    """
    Executes trades and manages positions.

    Responsibilities:
    - Execute buy/sell orders
    - Track open positions per pair
    - Update trailing stops (BUG-055 FIX: separate tracking per pair)
    - Monitor for stop-loss / take-profit triggers
    - Handle demo mode vs live mode
    - Report fills and P&L
    """

    def __init__(self):
        super().__init__(
            agent_id="trade_execution",
            agent_type="trade_execution"
        )

        # Trading mode (demo or live)
        self.trading_mode = settings.trading_mode  # "demo" or "live"

        # Open positions - BUG-055 FIX: Each pair has independent trailing stop state
        self.positions: Dict[str, Position] = {}

        # Order history
        self.orders: List[Order] = []
        self.order_counter = 0

        # Exchange client (for live mode)
        self.exchange: Optional[ccxt.Exchange] = None

        # Metrics
        self.metrics = {
            "total_orders": 0,
            "filled_orders": 0,
            "rejected_orders": 0,
            "trailing_stops_triggered": 0,
            "take_profits_hit": 0,
        }

        self.logger.info(f"Trade Execution initialized in {self.trading_mode} mode")

    async def start(self):
        """Start the trade execution agent."""
        await super().start()

        # Initialize exchange for live mode
        if self.trading_mode == "live":
            await self._init_exchange()

        # Subscribe to approved signals from Risk Manager
        await self.subscribe("signal.approved", self._handle_approved_signal)

        # Subscribe to emergency close commands
        await self.subscribe("signal.emergency_close", self._handle_emergency_close)

        # Subscribe to market data for position monitoring
        await self.subscribe("market.*.tick", self._handle_market_tick)

        # Start position monitoring loop
        self.create_task(self._position_monitoring_loop())

        await self._publish_status()

        self.logger.info("Trade Execution started - ready to execute orders")

    async def _init_exchange(self):
        """Initialize exchange client for live trading."""
        try:
            self.exchange = ccxt.coinex({
                'apiKey': settings.coinex_api_key,
                'secret': settings.coinex_api_secret,
                'enableRateLimit': True,
            })

            # Test connection
            await self.exchange.load_markets()

            self.logger.info("Connected to CoinEx exchange for live trading")

        except Exception as e:
            self.logger.error(f"Failed to initialize exchange: {e}")
            self.logger.warning("Falling back to demo mode")
            self.trading_mode = "demo"

    async def execute_order(
        self,
        pair: str,
        side: OrderSide,
        size: float,
        price: Optional[float] = None,
        order_type: OrderType = OrderType.MARKET
    ) -> Order:
        """
        Execute a trade order.

        Args:
            pair: Trading pair
            side: Buy or sell
            size: Position size
            price: Limit price (optional)
            order_type: Market or limit

        Returns:
            Order object
        """
        self.order_counter += 1
        order_id = f"ORD-{self.order_counter:06d}"

        order = Order(
            order_id=order_id,
            pair=pair,
            side=side,
            order_type=order_type,
            price=price or 0.0,
            size=size,
            status=OrderStatus.PENDING,
        )

        self.orders.append(order)
        self.metrics["total_orders"] += 1

        # Execute based on mode
        if self.trading_mode == "demo":
            await self._execute_demo_order(order)
        else:
            await self._execute_live_order(order)

        return order

    async def _execute_demo_order(self, order: Order):
        """Execute order in demo mode (simulated)."""
        # Simulate instant fill at market price
        # In production, this would fetch current market price
        order.status = OrderStatus.FILLED
        order.filled_price = order.price
        order.filled_time = datetime.utcnow().isoformat()

        self.metrics["filled_orders"] += 1

        await self.publish(
            "order.filled",
            {
                "order_id": order.order_id,
                "pair": order.pair,
                "side": order.side.value,
                "filled_price": order.filled_price,
                "size": order.size,
                "mode": "demo",
            }
        )

        self.logger.info(
            f"[DEMO] Order filled: {order.side.value} {order.size} {order.pair} @ ${order.filled_price:.2f}"
        )

    async def _execute_live_order(self, order: Order):
        """Execute order on live exchange."""
        if not self.exchange:
            order.status = OrderStatus.REJECTED
            self.metrics["rejected_orders"] += 1
            return

        try:
            # Place order on exchange
            result = await self.exchange.create_order(
                symbol=order.pair,
                type=order.order_type.value,
                side=order.side.value,
                amount=order.size,
                price=order.price if order.order_type == OrderType.LIMIT else None,
            )

            order.status = OrderStatus.FILLED
            order.filled_price = result.get("price", order.price)
            order.filled_time = datetime.utcnow().isoformat()

            self.metrics["filled_orders"] += 1

            await self.publish("order.filled", {
                "order_id": order.order_id,
                "pair": order.pair,
                "exchange_order_id": result.get("id"),
                "filled_price": order.filled_price,
                "mode": "live",
            })

            self.logger.info(
                f"[LIVE] Order filled: {order.side.value} {order.size} {order.pair} @ ${order.filled_price:.2f}"
            )

        except Exception as e:
            order.status = OrderStatus.REJECTED
            self.metrics["rejected_orders"] += 1
            self.logger.error(f"Order execution failed: {e}")

    async def _handle_approved_signal(self, event):
        """Handle approved entry signal from Risk Manager."""
        pair = event.data.get("pair")
        side = OrderSide(event.data.get("side"))
        position_size = event.data.get("position_size")
        entry_price = event.data.get("entry_price")
        stop_loss = event.data.get("stop_loss")
        take_profit = event.data.get("take_profit")

        # Execute entry order
        order = await self.execute_order(
            pair=pair,
            side=side,
            size=position_size,
            price=entry_price,
            order_type=OrderType.MARKET,
        )

        if order.status == OrderStatus.FILLED:
            # Open position with trailing stop
            position = Position(
                pair=pair,
                side=side,
                entry_price=order.filled_price or entry_price,
                current_price=order.filled_price or entry_price,
                position_size=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                trailing_stop_enabled=True,
            )

            # BUG-055 FIX: Store position in dictionary keyed by pair
            # This ensures each pair has independent trailing stop tracking
            self.positions[pair] = position

            await self.publish(
                "position.opened",
                {
                    "pair": pair,
                    "side": side.value,
                    "entry_price": position.entry_price,
                    "position_size": position_size,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                }
            )

            self.logger.info(
                f"Position opened: {side.value} {position_size} {pair} @ ${position.entry_price:.2f}"
            )

    async def _handle_market_tick(self, event):
        """
        Update positions based on market price changes.

        BUG-055 FIX: Each pair's trailing stop is updated independently
        based on that pair's price movements.
        """
        # Extract pair from topic (e.g., "market.btcusdc.tick" -> "BTC/USDC")
        topic = event.topic
        pair_normalized = topic.split(".")[1] if "." in topic else ""

        # Convert to standard format
        if len(pair_normalized) >= 6:
            base = pair_normalized[:-4].upper()
            quote = pair_normalized[-4:].upper()
            pair = f"{base}/{quote}"

            # BUG-055 FIX: Only update if we have a position for THIS specific pair
            if pair in self.positions:
                position = self.positions[pair]
                current_price = event.data.get("price", 0)

                if current_price > 0:
                    await self._update_position_price(position, current_price)

    async def _update_position_price(self, position: Position, current_price: float):
        """
        Update position with new price and check trailing stop.

        BUG-055 FIX: Trailing stop logic isolated per position/pair.
        """
        position.current_price = current_price

        # Calculate unrealized P&L
        if position.side == OrderSide.BUY:
            price_change = current_price - position.entry_price
            position.unrealized_pnl = (price_change / position.entry_price) * position.position_size

            # Update trailing stop for long position
            if position.trailing_stop_enabled:
                # Track highest price
                if current_price > position.highest_price:
                    position.highest_price = current_price

                    # Update stop loss to trail
                    new_stop = position.highest_price - position.trailing_stop_distance

                    # Only move stop up, never down
                    if new_stop > position.stop_loss:
                        old_stop = position.stop_loss
                        position.stop_loss = new_stop

                        self.logger.info(
                            f"[{position.pair}] Trailing stop updated: "
                            f"${old_stop:.2f} -> ${new_stop:.2f} "
                            f"(price: ${current_price:.2f}, peak: ${position.highest_price:.2f})"
                        )

            # Check if stop hit
            if current_price <= position.stop_loss:
                self.metrics["trailing_stops_triggered"] += 1
                await self._close_position(position, current_price, "stop_loss")
                return

            # Check if take profit hit
            if current_price >= position.take_profit:
                self.metrics["take_profits_hit"] += 1
                await self._close_position(position, current_price, "take_profit")
                return

        else:  # Short position
            price_change = position.entry_price - current_price
            position.unrealized_pnl = (price_change / position.entry_price) * position.position_size

            # Trailing stop for short positions (optional, for future)
            # Similar logic but inverted

        # Publish position update
        await self.publish(
            "position.updated",
            {
                "pair": position.pair,
                "current_price": current_price,
                "unrealized_pnl": position.unrealized_pnl,
                "stop_loss": position.stop_loss,
            }
        )

    async def _close_position(self, position: Position, exit_price: float, reason: str):
        """Close an open position."""
        # Calculate realized P&L
        if position.side == OrderSide.BUY:
            pnl = ((exit_price - position.entry_price) / position.entry_price) * position.position_size
        else:
            pnl = ((position.entry_price - exit_price) / position.entry_price) * position.position_size

        # Execute closing order
        close_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY

        await self.execute_order(
            pair=position.pair,
            side=close_side,
            size=position.position_size,
            price=exit_price,
            order_type=OrderType.MARKET,
        )

        # Remove from open positions
        del self.positions[position.pair]

        # Publish close event
        await self.publish(
            "position.closed",
            {
                "pair": position.pair,
                "exit_price": exit_price,
                "pnl": pnl,
                "reason": reason,
                "hold_time": (
                    datetime.utcnow() - datetime.fromisoformat(position.entry_time)
                ).total_seconds(),
            }
        )

        # Publish to trade executed (for strategy manager tracking)
        await self.publish(
            "trade.executed",
            {
                "pair": position.pair,
                "pnl": pnl,
                "reason": reason,
            }
        )

        self.logger.info(
            f"Position closed: {position.pair} @ ${exit_price:.2f}, "
            f"P&L: ${pnl:.2f}, Reason: {reason}"
        )

    async def _handle_emergency_close(self, event):
        """Close all positions immediately."""
        pair = event.data.get("pair")

        if pair and pair in self.positions:
            position = self.positions[pair]
            await self._close_position(position, position.current_price, "emergency_stop")

    async def _position_monitoring_loop(self):
        """Monitor all open positions."""
        while self.running:
            # Log position status
            if self.positions:
                total_unrealized = sum(p.unrealized_pnl for p in self.positions.values())
                self.logger.debug(
                    f"Open positions: {len(self.positions)}, "
                    f"Unrealized P&L: ${total_unrealized:.2f}"
                )

            await asyncio.sleep(5)  # Check every 5 seconds

    async def _publish_status(self):
        """Publish current execution status."""
        status = {
            "trading_mode": self.trading_mode,
            "open_positions": len(self.positions),
            "positions": [
                {
                    "pair": pos.pair,
                    "side": pos.side.value,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "stop_loss": pos.stop_loss,
                    "unrealized_pnl": pos.unrealized_pnl,
                }
                for pos in self.positions.values()
            ],
            "metrics": self.metrics,
        }

        await self.publish("execution.status", status)
