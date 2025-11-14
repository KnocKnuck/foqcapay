"""
Strategy Manager Agent - Multi-Strategy Framework

Agent: Strategy Manager Agent
Squad: Strategy
Sprint: 3.1

Manages multiple trading strategies running simultaneously.
Allows switching between strategies, comparing performance,
and running strategies in parallel for different pairs.

Features:
- Run multiple strategies (scalping, intraday, swing) simultaneously
- Per-pair strategy assignment
- Strategy performance comparison
- Strategy enable/disable controls
- Aggregate P&L across all active strategies

Agent: #18 Strategy Manager Agent
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from agents.base_agent import BaseAgent


class StrategyType(str, Enum):
    """Available strategy types."""
    SCALPING = "scalping"
    INTRADAY = "intraday"
    SWING = "swing"
    MA_CROSSOVER = "ma_crossover"


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy."""
    strategy_name: str
    enabled: bool = True
    trades_executed: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "enabled": self.enabled,
            "trades_executed": self.trades_executed,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_pnl": self.total_pnl,
            "win_rate": self.win_rate,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
        }


@dataclass
class PairStrategyAssignment:
    """Maps a trading pair to a strategy."""
    pair: str
    strategy_type: StrategyType
    enabled: bool = True
    performance: StrategyPerformance = field(default_factory=lambda: StrategyPerformance(""))


class StrategyManagerAgent(BaseAgent):
    """
    Manages multiple trading strategies running in parallel.

    Responsibilities:
    - Enable/disable strategies per pair
    - Track performance of each strategy
    - Compare strategy performance
    - Route signals to appropriate strategy
    - Aggregate P&L across all strategies
    """

    def __init__(self):
        super().__init__(
            agent_id="strategy_manager",
            agent_type="strategy_manager"
        )

        # Strategy assignments per pair
        self.pair_strategies: Dict[str, PairStrategyAssignment] = {}

        # Global strategy performance tracking
        self.strategy_performance: Dict[str, StrategyPerformance] = {
            StrategyType.SCALPING.value: StrategyPerformance("scalping"),
            StrategyType.INTRADAY.value: StrategyPerformance("intraday"),
            StrategyType.SWING.value: StrategyPerformance("swing"),
            StrategyType.MA_CROSSOVER.value: StrategyPerformance("ma_crossover"),
        }

        # Available strategies registry
        self.available_strategies = {
            StrategyType.SCALPING: {
                "name": "Scalping",
                "timeframe": "1m",
                "description": "High-frequency 1-5min trades",
                "indicators": ["EMA_9", "EMA_21", "RSI_5", "VOLUME"],
                "target_profit": 0.5,
                "stop_loss": 0.3,
            },
            StrategyType.INTRADAY: {
                "name": "Intraday",
                "timeframe": "15m",
                "description": "Medium-frequency intraday trades",
                "indicators": ["MA_20", "MA_50", "RSI_14", "MACD"],
                "target_profit": 1.5,
                "stop_loss": 1.0,
            },
            StrategyType.SWING: {
                "name": "Swing",
                "timeframe": "4h",
                "description": "Multi-day swing trades",
                "indicators": ["MA_50", "MA_200", "RSI_14", "BB"],
                "target_profit": 5.0,
                "stop_loss": 3.0,
            },
            StrategyType.MA_CROSSOVER: {
                "name": "MA Crossover",
                "timeframe": "1h",
                "description": "Moving average crossover strategy (Sprint 2.2)",
                "indicators": ["MA_20", "MA_50"],
                "target_profit": 2.0,
                "stop_loss": 1.5,
            },
        }

        self.logger.info("Strategy Manager initialized with 4 available strategies")

    async def start(self):
        """Start the strategy manager agent."""
        await super().start()

        # Subscribe to strategy control commands
        await self.subscribe("strategy.control.*", self._handle_control_command)

        # Subscribe to trade execution results
        await self.subscribe("trade.executed", self._handle_trade_executed)

        # Subscribe to strategy performance updates
        await self.subscribe("strategy.*.performance", self._handle_performance_update)

        # Publish initial strategy status
        await self._publish_status()

        self.logger.info("Strategy Manager started - ready for multi-strategy trading")

    async def assign_strategy(self, pair: str, strategy_type: StrategyType):
        """
        Assign a strategy to a trading pair.

        Args:
            pair: Trading pair (e.g., "BTC/USDC")
            strategy_type: Strategy to assign
        """
        assignment = PairStrategyAssignment(
            pair=pair,
            strategy_type=strategy_type,
            performance=StrategyPerformance(strategy_type.value)
        )

        self.pair_strategies[pair] = assignment

        await self.publish(
            "strategy.assigned",
            {
                "pair": pair,
                "strategy": strategy_type.value,
                "config": self.available_strategies[strategy_type],
            }
        )

        self.logger.info(f"Assigned {strategy_type.value} strategy to {pair}")

    async def enable_strategy(self, pair: str, enabled: bool = True):
        """Enable or disable strategy for a pair."""
        if pair in self.pair_strategies:
            self.pair_strategies[pair].enabled = enabled
            action = "enabled" if enabled else "disabled"

            await self.publish(
                f"strategy.{action}",
                {"pair": pair, "strategy": self.pair_strategies[pair].strategy_type.value}
            )

            self.logger.info(f"{action.capitalize()} strategy for {pair}")

    async def get_strategy_comparison(self) -> Dict[str, Any]:
        """
        Compare performance across all strategies.

        Returns:
            Dictionary with strategy comparison metrics
        """
        comparison = {
            "timestamp": datetime.utcnow().isoformat(),
            "strategies": {},
            "best_performer": None,
            "total_pnl": 0.0,
        }

        best_pnl = float('-inf')

        for strategy_name, perf in self.strategy_performance.items():
            comparison["strategies"][strategy_name] = perf.to_dict()
            comparison["total_pnl"] += perf.total_pnl

            if perf.total_pnl > best_pnl:
                best_pnl = perf.total_pnl
                comparison["best_performer"] = strategy_name

        return comparison

    async def _handle_control_command(self, event):
        """Handle strategy control commands."""
        command = event.data.get("command")
        pair = event.data.get("pair")
        strategy = event.data.get("strategy")

        if command == "assign":
            strategy_type = StrategyType(strategy)
            await self.assign_strategy(pair, strategy_type)

        elif command == "enable":
            await self.enable_strategy(pair, enabled=True)

        elif command == "disable":
            await self.enable_strategy(pair, enabled=False)

        elif command == "compare":
            comparison = await self.get_strategy_comparison()
            await self.publish("strategy.comparison", comparison)

    async def _handle_trade_executed(self, event):
        """Update strategy performance when a trade is executed."""
        pair = event.data.get("pair")
        pnl = event.data.get("pnl", 0.0)

        if pair in self.pair_strategies:
            assignment = self.pair_strategies[pair]
            strategy_name = assignment.strategy_type.value
            perf = self.strategy_performance[strategy_name]

            # Update metrics
            perf.trades_executed += 1
            perf.total_pnl += pnl

            if pnl > 0:
                perf.winning_trades += 1
                perf.avg_win = (
                    (perf.avg_win * (perf.winning_trades - 1) + pnl) / perf.winning_trades
                )
            else:
                perf.losing_trades += 1
                perf.avg_loss = (
                    (perf.avg_loss * (perf.losing_trades - 1) + pnl) / perf.losing_trades
                )

            # Calculate win rate
            if perf.trades_executed > 0:
                perf.win_rate = perf.winning_trades / perf.trades_executed

            self.logger.info(
                f"Updated {strategy_name} performance: {perf.trades_executed} trades, "
                f"{perf.win_rate:.1%} win rate, ${perf.total_pnl:.2f} P&L"
            )

    async def _handle_performance_update(self, event):
        """Handle performance metric updates from individual strategies."""
        strategy_name = event.data.get("strategy")
        metrics = event.data.get("metrics", {})

        if strategy_name in self.strategy_performance:
            perf = self.strategy_performance[strategy_name]

            # Update advanced metrics
            perf.sharpe_ratio = metrics.get("sharpe_ratio", perf.sharpe_ratio)
            perf.max_drawdown = metrics.get("max_drawdown", perf.max_drawdown)

    async def _publish_status(self):
        """Publish current strategy manager status."""
        status = {
            "active_pairs": len(self.pair_strategies),
            "pair_assignments": {
                pair: {
                    "strategy": assignment.strategy_type.value,
                    "enabled": assignment.enabled,
                }
                for pair, assignment in self.pair_strategies.items()
            },
            "available_strategies": list(self.available_strategies.keys()),
            "global_performance": {
                name: perf.to_dict()
                for name, perf in self.strategy_performance.items()
            },
        }

        await self.publish("strategy.manager.status", status)
