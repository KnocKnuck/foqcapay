"""
Backtesting Engine - Strategy Performance Testing on Historical Data

Agent: Strategy Manager Agent + System Architect Agent
Squad: Alpha + Strategy
Sprint: 5.2

Provides comprehensive backtesting capabilities for trading strategies
using historical market data stored in the database.

Features:
- Historical data replay
- Strategy signal generation simulation
- Position and trade tracking
- Performance metrics calculation (Sharpe, Sortino, drawdown, etc.)
- Multi-strategy comparison
- Monte Carlo simulation support

Agent: #18 Strategy Manager Agent, #25 System Architect Agent
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class BacktestStatus(str, Enum):
    """Backtest execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""

    # Strategy Configuration
    strategy_name: str
    pair: str
    timeframe: str = "1h"  # 1m, 5m, 15m, 1h, 4h, 1d

    # Time Range
    start_date: datetime = None
    end_date: datetime = None

    # Initial Capital
    initial_capital: float = 10000.0

    # Risk Parameters
    position_size_pct: float = 10.0  # % of capital per trade
    max_positions: int = 3
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 5.0
    trailing_stop_pct: Optional[float] = None

    # Fees
    commission_pct: float = 0.1  # 0.1% per trade
    slippage_pct: float = 0.05  # 0.05% slippage

    # Advanced
    use_trailing_stop: bool = False
    allow_pyramiding: bool = False  # Multiple positions in same direction
    max_pyramiding: int = 1


@dataclass
class BacktestTrade:
    """A single trade from backtest."""

    entry_time: datetime
    exit_time: datetime
    pair: str
    side: str  # buy or sell
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float
    exit_reason: str  # stop_loss, take_profit, signal
    duration_minutes: int
    commission: float


@dataclass
class BacktestResults:
    """Complete backtest results with performance metrics."""

    # Backtest Info
    backtest_id: str
    strategy_name: str
    pair: str
    start_date: datetime
    end_date: datetime
    status: BacktestStatus

    # Capital & Equity
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float

    # Trades
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    trades: List[BacktestTrade] = field(default_factory=list)

    # Performance Metrics
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    expectancy: float = 0.0

    # Risk Metrics
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Equity Curve
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)

    # Execution Time
    execution_time_seconds: float = 0.0


class BacktestEngine:
    """
    Core backtesting engine for strategy performance testing.

    Simulates strategy execution on historical data and calculates
    comprehensive performance metrics.
    """

    def __init__(self, config: BacktestConfig):
        """
        Initialize backtesting engine.

        Args:
            config: Backtest configuration
        """
        self.config = config
        self.logger = logger.bind(
            strategy=config.strategy_name,
            pair=config.pair,
        )

        # State
        self.capital = config.initial_capital
        self.equity = config.initial_capital
        self.peak_equity = config.initial_capital
        self.open_positions: List[Dict[str, Any]] = []
        self.closed_trades: List[BacktestTrade] = []
        self.equity_history: List[Dict[str, Any]] = []

        self.logger.info("Backtest engine initialized", initial_capital=self.capital)

    def run(self, historical_data: List[Dict[str, Any]]) -> BacktestResults:
        """
        Run backtest on historical data.

        Args:
            historical_data: List of OHLCV candles with timestamps

        Returns:
            BacktestResults with comprehensive performance metrics
        """
        start_time = datetime.utcnow()

        self.logger.info(
            "Starting backtest",
            bars=len(historical_data),
            start=historical_data[0]["timestamp"] if historical_data else None,
            end=historical_data[-1]["timestamp"] if historical_data else None,
        )

        # Process each bar
        for i, bar in enumerate(historical_data):
            self._process_bar(bar, i, historical_data)

        # Close any remaining open positions at end
        if historical_data:
            final_bar = historical_data[-1]
            self._close_all_positions(final_bar, "backtest_end")

        # Calculate final metrics
        results = self._calculate_results(start_time)

        self.logger.info(
            "Backtest complete",
            trades=results.total_trades,
            return_pct=results.total_return_pct,
            win_rate=results.win_rate,
            sharpe=results.sharpe_ratio,
        )

        return results

    def _process_bar(
        self, bar: Dict[str, Any], index: int, all_bars: List[Dict[str, Any]]
    ):
        """
        Process a single price bar.

        Args:
            bar: Current OHLCV bar
            index: Index in historical data
            all_bars: All historical bars (for lookback)
        """
        timestamp = bar["timestamp"]
        current_price = bar["close"]

        # Update position P&L
        self._update_positions(current_price)

        # Check for stop-loss / take-profit triggers
        self._check_exits(bar)

        # Generate trading signals
        signal = self._generate_signal(bar, index, all_bars)

        # Execute signal if conditions met
        if signal:
            self._execute_signal(signal, bar)

        # Record equity
        self._record_equity(timestamp)

    def _update_positions(self, current_price: float):
        """Update unrealized P&L for open positions."""
        self.equity = self.capital

        for pos in self.open_positions:
            if pos["side"] == "buy":
                pos["unrealized_pnl"] = (current_price - pos["entry_price"]) * pos[
                    "size"
                ]
            else:
                pos["unrealized_pnl"] = (pos["entry_price"] - current_price) * pos[
                    "size"
                ]

            self.equity += pos["unrealized_pnl"]

        # Update peak for drawdown calculation
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity

    def _check_exits(self, bar: Dict[str, Any]):
        """Check if any positions should be closed."""
        current_price = bar["close"]
        high = bar["high"]
        low = bar["low"]

        positions_to_close = []

        for pos in self.open_positions:
            exit_reason = None

            # Check stop-loss
            if pos.get("stop_loss"):
                if pos["side"] == "buy" and low <= pos["stop_loss"]:
                    exit_reason = "stop_loss"
                    exit_price = pos["stop_loss"]
                elif pos["side"] == "sell" and high >= pos["stop_loss"]:
                    exit_reason = "stop_loss"
                    exit_price = pos["stop_loss"]

            # Check take-profit
            if not exit_reason and pos.get("take_profit"):
                if pos["side"] == "buy" and high >= pos["take_profit"]:
                    exit_reason = "take_profit"
                    exit_price = pos["take_profit"]
                elif pos["side"] == "sell" and low <= pos["take_profit"]:
                    exit_reason = "take_profit"
                    exit_price = pos["take_profit"]

            # Update trailing stop
            if not exit_reason and self.config.use_trailing_stop:
                self._update_trailing_stop(pos, current_price)

            if exit_reason:
                positions_to_close.append((pos, exit_reason, exit_price, bar))

        # Close positions
        for pos, reason, price, bar_data in positions_to_close:
            self._close_position(pos, price, bar_data["timestamp"], reason)

    def _update_trailing_stop(self, position: Dict[str, Any], current_price: float):
        """Update trailing stop for position."""
        if not self.config.trailing_stop_pct:
            return

        trail_distance = current_price * (self.config.trailing_stop_pct / 100)

        if position["side"] == "buy":
            new_stop = current_price - trail_distance
            if "stop_loss" not in position or new_stop > position["stop_loss"]:
                position["stop_loss"] = new_stop
        else:
            new_stop = current_price + trail_distance
            if "stop_loss" not in position or new_stop < position["stop_loss"]:
                position["stop_loss"] = new_stop

    def _generate_signal(
        self, bar: Dict[str, Any], index: int, all_bars: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Generate trading signal for current bar.

        This is a simplified example - real strategies would implement
        complex indicator-based logic here.

        Returns:
            "buy", "sell", or None
        """
        # Simple MA crossover example
        if index < 50:
            return None

        # Calculate fast and slow MAs
        fast_period = 20
        slow_period = 50

        fast_ma = np.mean([b["close"] for b in all_bars[index - fast_period : index]])
        slow_ma = np.mean([b["close"] for b in all_bars[index - slow_period : index]])

        prev_fast_ma = np.mean(
            [b["close"] for b in all_bars[index - fast_period - 1 : index - 1]]
        )
        prev_slow_ma = np.mean(
            [b["close"] for b in all_bars[index - slow_period - 1 : index - 1]]
        )

        # Bullish crossover
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma:
            return "buy"

        # Bearish crossover
        if prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma:
            return "sell"

        return None

    def _execute_signal(self, signal: str, bar: Dict[str, Any]):
        """Execute trading signal."""
        # Check position limits
        if len(self.open_positions) >= self.config.max_positions:
            return

        entry_price = bar["close"]
        position_size_usd = self.capital * (self.config.position_size_pct / 100)

        # Account for slippage
        if signal == "buy":
            entry_price *= 1 + (self.config.slippage_pct / 100)
        else:
            entry_price *= 1 - (self.config.slippage_pct / 100)

        size = position_size_usd / entry_price

        # Calculate stop-loss and take-profit
        if signal == "buy":
            stop_loss = entry_price * (1 - self.config.stop_loss_pct / 100)
            take_profit = entry_price * (1 + self.config.take_profit_pct / 100)
        else:
            stop_loss = entry_price * (1 + self.config.stop_loss_pct / 100)
            take_profit = entry_price * (1 - self.config.take_profit_pct / 100)

        # Create position
        position = {
            "entry_time": bar["timestamp"],
            "entry_price": entry_price,
            "side": signal,
            "size": size,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "unrealized_pnl": 0.0,
        }

        self.open_positions.append(position)

        self.logger.debug(
            "Position opened",
            side=signal,
            price=entry_price,
            size=size,
            timestamp=bar["timestamp"],
        )

    def _close_position(
        self,
        position: Dict[str, Any],
        exit_price: float,
        exit_time: datetime,
        exit_reason: str,
    ):
        """Close position and record trade."""
        # Calculate P&L
        if position["side"] == "buy":
            pnl = (exit_price - position["entry_price"]) * position["size"]
        else:
            pnl = (position["entry_price"] - exit_price) * position["size"]

        # Deduct commission
        commission = (
            position["entry_price"] * position["size"] * self.config.commission_pct / 100
        )
        commission += exit_price * position["size"] * self.config.commission_pct / 100
        net_pnl = pnl - commission

        # Update capital
        self.capital += net_pnl

        # Calculate duration
        duration = (exit_time - position["entry_time"]).total_seconds() / 60

        # Record trade
        trade = BacktestTrade(
            entry_time=position["entry_time"],
            exit_time=exit_time,
            pair=self.config.pair,
            side=position["side"],
            entry_price=position["entry_price"],
            exit_price=exit_price,
            size=position["size"],
            pnl=net_pnl,
            pnl_pct=(net_pnl / (position["entry_price"] * position["size"])) * 100,
            exit_reason=exit_reason,
            duration_minutes=int(duration),
            commission=commission,
        )

        self.closed_trades.append(trade)

        # Remove from open positions
        self.open_positions.remove(position)

        self.logger.debug(
            "Position closed",
            pnl=net_pnl,
            reason=exit_reason,
            timestamp=exit_time,
        )

    def _close_all_positions(self, final_bar: Dict[str, Any], reason: str):
        """Close all remaining positions."""
        for pos in list(self.open_positions):
            self._close_position(
                pos, final_bar["close"], final_bar["timestamp"], reason
            )

    def _record_equity(self, timestamp: datetime):
        """Record current equity for equity curve."""
        self.equity_history.append(
            {
                "timestamp": timestamp,
                "equity": self.equity,
                "drawdown": (
                    ((self.peak_equity - self.equity) / self.peak_equity) * 100
                    if self.peak_equity > 0
                    else 0
                ),
            }
        )

    def _calculate_results(self, start_time: datetime) -> BacktestResults:
        """Calculate final backtest results."""
        # Basic metrics
        total_trades = len(self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl <= 0]

        total_return = self.capital - self.config.initial_capital
        total_return_pct = (total_return / self.config.initial_capital) * 100

        # Win/loss metrics
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))

        profit_factor = (
            total_wins / total_losses
            if total_losses > 0
            else float("inf") if total_wins > 0 else 0
        )

        avg_win = total_wins / len(winning_trades) if winning_trades else 0
        avg_loss = total_losses / len(losing_trades) if losing_trades else 0
        largest_win = max([t.pnl for t in winning_trades], default=0)
        largest_loss = min([t.pnl for t in losing_trades], default=0)

        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        # Risk metrics
        max_dd, max_dd_pct = self._calculate_max_drawdown()
        sharpe = self._calculate_sharpe_ratio()
        sortino = self._calculate_sortino_ratio()
        calmar = total_return_pct / max_dd_pct if max_dd_pct > 0 else 0

        # Execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()

        return BacktestResults(
            backtest_id=f"BT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            strategy_name=self.config.strategy_name,
            pair=self.config.pair,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            status=BacktestStatus.COMPLETED,
            initial_capital=self.config.initial_capital,
            final_capital=self.capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            trades=self.closed_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            expectancy=expectancy,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            equity_curve=self.equity_history,
            execution_time_seconds=execution_time,
        )

    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum drawdown."""
        if not self.equity_history:
            return 0.0, 0.0

        max_dd_pct = max([h["drawdown"] for h in self.equity_history], default=0)
        max_dd_usd = self.peak_equity * (max_dd_pct / 100)

        return max_dd_usd, max_dd_pct

    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio (annualized)."""
        if len(self.closed_trades) < 2:
            return 0.0

        returns = [t.pnl_pct for t in self.closed_trades]
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        # Annualize (assuming daily returns)
        sharpe = (mean_return - risk_free_rate) / std_return * np.sqrt(252)

        return sharpe

    def _calculate_sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside deviation)."""
        if len(self.closed_trades) < 2:
            return 0.0

        returns = [t.pnl_pct for t in self.closed_trades]
        mean_return = np.mean(returns)

        # Downside deviation (only negative returns)
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            return 0.0

        downside_std = np.std(negative_returns)

        if downside_std == 0:
            return 0.0

        sortino = (mean_return - risk_free_rate) / downside_std * np.sqrt(252)

        return sortino
