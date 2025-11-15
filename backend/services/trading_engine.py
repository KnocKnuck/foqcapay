"""
Trading Engine - Complete Trade Execution Pipeline

Agent: Trade Execution Agent
Squad: Execution
Sprint: 5.2

The MISSING LINK that connects market data to actual trade execution.

This service:
1. Fetches real-time market data
2. Calculates indicators (MA crossover)
3. Generates BUY/SELL signals
4. Executes trades (demo mode)
5. Stores trades in database
6. Updates positions

Agent: #21 Trade Execution Agent
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid
import structlog

from core.config import settings
from core.database import db_service
from agents.market_data import MarketDataAgent

logger = structlog.get_logger(__name__)


@dataclass
class Indicator:
    """Market indicator data."""
    name: str
    value: float
    timestamp: datetime


@dataclass
class Signal:
    """Trading signal."""
    pair: str
    signal_type: str  # "BUY" or "SELL"
    price: float
    timestamp: datetime
    strategy: str
    confidence: float = 0.8
    indicators: Dict[str, float] = field(default_factory=dict)


@dataclass
class ActivePosition:
    """Active trading position (in-memory tracking)."""
    position_id: str
    pair: str
    side: str
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0

    def update_pnl(self, current_price: float):
        """Update unrealized P&L based on current price."""
        self.current_price = current_price

        if self.side == "buy":
            price_change = current_price - self.entry_price
            self.unrealized_pnl = (price_change / self.entry_price) * 100  # Percent
        else:
            price_change = self.entry_price - current_price
            self.unrealized_pnl = (price_change / self.entry_price) * 100


class MAStrategy:
    """
    Simple Moving Average Crossover Strategy.

    BUY: When fast MA crosses above slow MA
    SELL: When fast MA crosses below slow MA
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 20):
        self.fast_period = fast_period
        self.slow_period = slow_period

        # Store price history per pair
        self.price_history: Dict[str, List[float]] = {}

        # Track previous MA values to detect crossovers
        self.prev_fast_ma: Dict[str, float] = {}
        self.prev_slow_ma: Dict[str, float] = {}

        logger.info(
            "MA Strategy initialized",
            fast_period=fast_period,
            slow_period=slow_period
        )

    def update(self, pair: str, price: float) -> Optional[Signal]:
        """
        Update strategy with new price and check for signals.

        Args:
            pair: Trading pair
            price: Current price

        Returns:
            Signal if generated, else None
        """
        # Initialize price history for new pairs
        if pair not in self.price_history:
            self.price_history[pair] = []

        # Add new price
        self.price_history[pair].append(price)

        # Keep only necessary history (slow_period + buffer)
        max_history = self.slow_period + 5
        if len(self.price_history[pair]) > max_history:
            self.price_history[pair] = self.price_history[pair][-max_history:]

        # Need enough data for slow MA
        if len(self.price_history[pair]) < self.slow_period:
            logger.debug(
                "Insufficient price history",
                pair=pair,
                have=len(self.price_history[pair]),
                need=self.slow_period
            )
            return None

        # Calculate MAs
        prices = self.price_history[pair]
        fast_ma = sum(prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(prices[-self.slow_period:]) / self.slow_period

        # Get previous MAs
        prev_fast = self.prev_fast_ma.get(pair)
        prev_slow = self.prev_slow_ma.get(pair)

        # Store current MAs for next iteration
        self.prev_fast_ma[pair] = fast_ma
        self.prev_slow_ma[pair] = slow_ma

        # Need previous values to detect crossover
        if prev_fast is None or prev_slow is None:
            logger.debug(
                "First MA calculation",
                pair=pair,
                fast_ma=fast_ma,
                slow_ma=slow_ma
            )
            return None

        # Detect crossovers
        signal = None

        # Bullish crossover: fast MA crosses above slow MA
        if prev_fast <= prev_slow and fast_ma > slow_ma:
            signal = Signal(
                pair=pair,
                signal_type="BUY",
                price=price,
                timestamp=datetime.utcnow(),
                strategy="ma_crossover",
                confidence=0.85,
                indicators={
                    "fast_ma": fast_ma,
                    "slow_ma": slow_ma,
                    "price": price
                }
            )
            logger.info(
                "🔔 BUY SIGNAL - Bullish MA Crossover",
                pair=pair,
                price=price,
                fast_ma=fast_ma,
                slow_ma=slow_ma
            )

        # Bearish crossover: fast MA crosses below slow MA
        elif prev_fast >= prev_slow and fast_ma < slow_ma:
            signal = Signal(
                pair=pair,
                signal_type="SELL",
                price=price,
                timestamp=datetime.utcnow(),
                strategy="ma_crossover",
                confidence=0.85,
                indicators={
                    "fast_ma": fast_ma,
                    "slow_ma": slow_ma,
                    "price": price
                }
            )
            logger.info(
                "🔔 SELL SIGNAL - Bearish MA Crossover",
                pair=pair,
                price=price,
                fast_ma=fast_ma,
                slow_ma=slow_ma
            )

        return signal


class TradingEngine:
    """
    Complete trading pipeline: Market Data → Signals → Execution → Database.

    This is the CORE engine that makes trading actually happen.
    """

    def __init__(self, pairs: List[str], strategy: str = "ma_crossover"):
        """
        Initialize trading engine.

        Args:
            pairs: List of trading pairs to monitor
            strategy: Strategy name (currently only ma_crossover)
        """
        self.pairs = pairs
        self.strategy_name = strategy

        # Market data agent
        self.market_agent: Optional[MarketDataAgent] = None

        # Strategy
        self.strategy = MAStrategy(fast_period=10, slow_period=20)

        # Active positions (in-memory tracking)
        self.positions: Dict[str, ActivePosition] = {}

        # Trading mode
        self.mode = settings.trading_mode

        # Demo account balance
        self.demo_balance = settings.demo_starting_balance

        # Running state
        self.running = False
        self.tasks: List[asyncio.Task] = []

        # Metrics
        self.metrics = {
            "signals_generated": 0,
            "trades_executed": 0,
            "positions_opened": 0,
            "positions_closed": 0,
            "total_pnl": 0.0
        }

        logger.info(
            "TradingEngine initialized",
            pairs=pairs,
            strategy=strategy,
            mode=self.mode,
            demo_balance=self.demo_balance
        )

    async def start(self):
        """Start the trading engine."""
        if self.running:
            logger.warning("TradingEngine already running")
            return

        logger.info("🚀 Starting TradingEngine...")

        self.running = True

        # Initialize database
        if not db_service._initialized:
            await db_service.initialize()

        # Initialize market data agent
        self.market_agent = MarketDataAgent(pairs=self.pairs)
        await self.market_agent.start()

        # Start trading loop for each pair
        for pair in self.pairs:
            task = asyncio.create_task(self._trading_loop(pair))
            self.tasks.append(task)

        # Start position monitoring
        task = asyncio.create_task(self._monitor_positions())
        self.tasks.append(task)

        logger.info(
            "✅ TradingEngine started",
            pairs=self.pairs,
            loops=len(self.tasks)
        )

    async def stop(self):
        """Stop the trading engine."""
        if not self.running:
            return

        logger.info("🛑 Stopping TradingEngine...")

        self.running = False

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)

        # Stop market data agent
        if self.market_agent:
            await self.market_agent.stop()

        # Close all open positions
        await self._close_all_positions("trading_stopped")

        logger.info("✅ TradingEngine stopped")

    async def _trading_loop(self, pair: str):
        """
        Main trading loop for a specific pair.

        Continuously:
        1. Fetch latest price
        2. Update strategy
        3. Check for signals
        4. Execute trades
        """
        logger.info(f"Trading loop started for {pair}")

        while self.running:
            try:
                # Get latest market data
                data = await self.market_agent.get_latest_data(pair)

                if not data:
                    await asyncio.sleep(1)
                    continue

                price = data["price"]

                # Update strategy and check for signals
                signal = self.strategy.update(pair, price)

                if signal:
                    self.metrics["signals_generated"] += 1
                    await self._handle_signal(signal)

                # Update open positions for this pair
                if pair in self.positions:
                    await self._update_position(pair, price)

                # Wait before next iteration (1 second)
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(
                    "Error in trading loop",
                    pair=pair,
                    error=str(e)
                )
                await asyncio.sleep(5)

    async def _handle_signal(self, signal: Signal):
        """
        Handle a trading signal by executing a trade.

        Args:
            signal: Trading signal
        """
        logger.info(
            f"📊 Handling {signal.signal_type} signal",
            pair=signal.pair,
            price=signal.price
        )

        # Check if we already have a position for this pair
        if signal.pair in self.positions:
            position = self.positions[signal.pair]

            # If signal is opposite to our position, close it
            if (signal.signal_type == "SELL" and position.side == "buy") or \
               (signal.signal_type == "BUY" and position.side == "sell"):
                await self._close_position(signal.pair, signal.price, "signal")
            else:
                logger.debug(
                    "Ignoring signal - same direction as open position",
                    pair=signal.pair,
                    signal=signal.signal_type,
                    position_side=position.side
                )
            return

        # Open new position for BUY or SELL signals
        if signal.signal_type == "BUY":
            await self._open_position(signal)
        elif signal.signal_type == "SELL":
            # For now, treat SELL signals as SHORT positions in demo mode
            # In production, this would short on the exchange
            await self._open_position(signal)

    async def _open_position(self, signal: Signal):
        """
        Open a new position based on signal.

        Args:
            signal: Trading signal
        """
        # Calculate position size (use 10% of balance per trade)
        position_value_usd = self.demo_balance * 0.10
        size = position_value_usd / signal.price

        # Calculate stop loss and take profit
        # Stop loss: 2% below entry
        # Take profit: 4% above entry
        stop_loss = signal.price * 0.98
        take_profit = signal.price * 1.04

        # Generate position ID
        position_id = f"POS-{uuid.uuid4().hex[:8].upper()}"

        # Determine position side based on signal
        position_side = "buy" if signal.signal_type == "BUY" else "sell"

        # For SELL/SHORT positions, reverse stop-loss and take-profit
        if position_side == "sell":
            stop_loss = signal.price * 1.02  # 2% above entry (loss when price rises)
            take_profit = signal.price * 0.96  # 4% below entry (profit when price falls)

        # Create position object
        position = ActivePosition(
            position_id=position_id,
            pair=signal.pair,
            side=position_side,
            entry_price=signal.price,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=datetime.utcnow(),
            current_price=signal.price
        )

        # Store in memory
        self.positions[signal.pair] = position

        # Store in database
        await db_service.create_position({
            "position_id": position_id,
            "pair": signal.pair,
            "strategy": signal.strategy,
            "side": position_side,  # Use correct side from signal
            "entry_time": position.entry_time,
            "entry_price": signal.price,
            "size": size,
            "position_value_usd": position_value_usd,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "status": "open"
        })

        # Create order record
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        await db_service.create_order({
            "order_id": order_id,
            "pair": signal.pair,
            "order_type": "market",
            "side": "buy",
            "price": signal.price,
            "size": size,
            "status": "filled",
            "filled_price": signal.price,
            "filled_size": size,
            "filled_at": datetime.utcnow(),
            "position_id": position_id
        })

        # Log event
        await db_service.log_event({
            "event_type": "position",
            "event_category": "entry",
            "severity": "info",
            "message": f"Position opened: {signal.signal_type} {signal.pair} @ ${signal.price:.2f}",
            "pair": signal.pair,
            "strategy": signal.strategy,
            "position_id": position_id,
            "order_id": order_id,
            "agent_name": "TradingEngine"
        })

        self.metrics["positions_opened"] += 1
        self.metrics["trades_executed"] += 1

        logger.warning(
            "✅ POSITION OPENED",
            position_id=position_id,
            pair=signal.pair,
            side="buy",
            price=signal.price,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

    async def _update_position(self, pair: str, current_price: float):
        """
        Update position with current price and check exit conditions.

        Args:
            pair: Trading pair
            current_price: Current market price
        """
        position = self.positions[pair]
        position.update_pnl(current_price)

        # Update position in database
        await db_service.update_position(
            position.position_id,
            {
                "current_price": current_price,
                "unrealized_pnl": position.unrealized_pnl
            }
        )

        # Check stop loss
        if current_price <= position.stop_loss:
            logger.warning(
                "🛑 STOP LOSS HIT",
                pair=pair,
                price=current_price,
                stop_loss=position.stop_loss
            )
            await self._close_position(pair, current_price, "stop_loss")
            return

        # Check take profit
        if current_price >= position.take_profit:
            logger.warning(
                "🎯 TAKE PROFIT HIT",
                pair=pair,
                price=current_price,
                take_profit=position.take_profit
            )
            await self._close_position(pair, current_price, "take_profit")
            return

    async def _close_position(self, pair: str, exit_price: float, reason: str):
        """
        Close an open position.

        Args:
            pair: Trading pair
            exit_price: Exit price
            reason: Reason for closing (stop_loss, take_profit, signal)
        """
        if pair not in self.positions:
            logger.warning(f"Cannot close position - no position for {pair}")
            return

        position = self.positions[pair]

        # Calculate P&L
        exit_time = datetime.utcnow()
        duration_minutes = int((exit_time - position.entry_time).total_seconds() / 60)

        # P&L calculation
        price_change = exit_price - position.entry_price
        pnl_percent = (price_change / position.entry_price) * 100
        pnl_usd = (price_change / position.entry_price) * (position.size * position.entry_price)

        # Simulate fees (0.1%)
        fees = (position.size * position.entry_price * 0.001) + (position.size * exit_price * 0.001)
        net_pnl = pnl_usd - fees

        # Update demo balance
        self.demo_balance += net_pnl

        # Update metrics
        self.metrics["positions_closed"] += 1
        self.metrics["total_pnl"] += net_pnl

        # Close position in database
        await db_service.update_position(
            position.position_id,
            {
                "status": "closed",
                "closed_at": exit_time,
                "closed_by": reason,
                "realized_pnl": net_pnl,
                "realized_pnl_percent": pnl_percent
            }
        )

        # Create exit order
        exit_order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        await db_service.create_order({
            "order_id": exit_order_id,
            "pair": pair,
            "order_type": "market",
            "side": "sell",
            "price": exit_price,
            "size": position.size,
            "status": "filled",
            "filled_price": exit_price,
            "filled_size": position.size,
            "filled_at": exit_time,
            "position_id": position.position_id
        })

        # Create completed trade record
        trade_id = f"TRD-{uuid.uuid4().hex[:8].upper()}"
        await db_service.create_trade({
            "trade_id": trade_id,
            "pair": pair,
            "strategy": "ma_crossover",
            "side": "buy",
            "entry_time": position.entry_time,
            "entry_price": position.entry_price,
            "entry_order_id": f"ORD-{position.position_id[-8:]}",
            "exit_time": exit_time,
            "exit_price": exit_price,
            "exit_order_id": exit_order_id,
            "exit_reason": reason,
            "size": position.size,
            "position_value_usd": position.size * position.entry_price,
            "pnl": pnl_usd,
            "pnl_percent": pnl_percent,
            "fees": fees,
            "net_pnl": net_pnl,
            "stop_loss": position.stop_loss,
            "take_profit": position.take_profit,
            "duration_minutes": duration_minutes
        })

        # Log event
        await db_service.log_event({
            "event_type": "position",
            "event_category": "exit",
            "severity": "info",
            "message": f"Position closed: {pair} @ ${exit_price:.2f}, P&L: ${net_pnl:.2f} ({pnl_percent:.2f}%)",
            "pair": pair,
            "strategy": "ma_crossover",
            "position_id": position.position_id,
            "trade_id": trade_id,
            "agent_name": "TradingEngine"
        })

        # Remove from active positions
        del self.positions[pair]

        logger.warning(
            "✅ POSITION CLOSED",
            position_id=position.position_id,
            trade_id=trade_id,
            pair=pair,
            entry_price=position.entry_price,
            exit_price=exit_price,
            pnl_usd=net_pnl,
            pnl_percent=pnl_percent,
            reason=reason,
            duration_min=duration_minutes
        )

    async def _close_all_positions(self, reason: str):
        """Close all open positions."""
        pairs_to_close = list(self.positions.keys())

        for pair in pairs_to_close:
            # Get current price
            data = await self.market_agent.get_latest_data(pair)
            if data:
                current_price = data["price"]
                await self._close_position(pair, current_price, reason)

    async def _monitor_positions(self):
        """Monitor and log position status periodically."""
        while self.running:
            try:
                if self.positions:
                    total_unrealized = sum(p.unrealized_pnl for p in self.positions.values())

                    logger.info(
                        "📈 Position Status",
                        open_positions=len(self.positions),
                        total_unrealized_pnl_pct=total_unrealized,
                        demo_balance=self.demo_balance,
                        total_pnl=self.metrics["total_pnl"]
                    )

                # Update account state every 30 seconds
                await db_service.save_account_state({
                    "mode": self.mode,
                    "total_balance": self.demo_balance,
                    "available_balance": self.demo_balance,
                    "total_pnl": self.metrics["total_pnl"],
                    "open_positions": len(self.positions)
                })

                await asyncio.sleep(30)

            except Exception as e:
                logger.error("Error in position monitoring", error=str(e))
                await asyncio.sleep(30)

    def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        return {
            "running": self.running,
            "pairs": self.pairs,
            "strategy": self.strategy_name,
            "mode": self.mode,
            "demo_balance": self.demo_balance,
            "open_positions": len(self.positions),
            "positions": [
                {
                    "position_id": pos.position_id,
                    "pair": pos.pair,
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "stop_loss": pos.stop_loss,
                    "take_profit": pos.take_profit
                }
                for pos in self.positions.values()
            ],
            "metrics": self.metrics
        }


# Global trading engine instance
_trading_engine: Optional[TradingEngine] = None


async def get_trading_engine() -> Optional[TradingEngine]:
    """Get the active trading engine instance."""
    return _trading_engine


async def start_trading_engine(pairs: List[str], strategy: str = "ma_crossover") -> TradingEngine:
    """
    Start a new trading engine.

    Args:
        pairs: List of trading pairs
        strategy: Strategy name

    Returns:
        TradingEngine instance
    """
    global _trading_engine

    if _trading_engine and _trading_engine.running:
        logger.warning("Trading engine already running - stopping previous instance")
        await _trading_engine.stop()

    _trading_engine = TradingEngine(pairs=pairs, strategy=strategy)
    await _trading_engine.start()

    return _trading_engine


async def stop_trading_engine():
    """Stop the active trading engine."""
    global _trading_engine

    if _trading_engine:
        await _trading_engine.stop()
        _trading_engine = None
