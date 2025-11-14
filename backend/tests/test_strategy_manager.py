"""
Tests for Strategy Manager Agent

Agent: Bug & Resolution Agent
Squad: Strategy
Sprint: 3.1

Tests Cover:
- Strategy assignment to pairs
- Multi-strategy execution
- Strategy enable/disable
- Performance tracking
- Strategy comparison

Run:
    pytest tests/test_strategy_manager.py -v
"""

import pytest
import asyncio
from agents.strategy_manager import StrategyManagerAgent, StrategyType


@pytest.mark.asyncio
async def test_strategy_manager_initialization():
    """Test strategy manager initializes with all strategies."""
    sm = StrategyManagerAgent()

    assert len(sm.available_strategies) == 4
    assert StrategyType.SCALPING in sm.available_strategies
    assert StrategyType.INTRADAY in sm.available_strategies
    assert StrategyType.SWING in sm.available_strategies
    assert StrategyType.MA_CROSSOVER in sm.available_strategies


@pytest.mark.asyncio
async def test_assign_strategy_to_pair():
    """Test assigning a strategy to a trading pair."""
    sm = StrategyManagerAgent()
    await sm.connect()

    # Assign scalping strategy to BTC/USDC
    await sm.assign_strategy("BTC/USDC", StrategyType.SCALPING)

    assert "BTC/USDC" in sm.pair_strategies
    assert sm.pair_strategies["BTC/USDC"].strategy_type == StrategyType.SCALPING
    assert sm.pair_strategies["BTC/USDC"].enabled is True

    await sm.disconnect()


@pytest.mark.asyncio
async def test_multi_pair_multi_strategy():
    """Test different strategies assigned to different pairs."""
    sm = StrategyManagerAgent()
    await sm.connect()

    # Assign different strategies to different pairs
    await sm.assign_strategy("BTC/USDC", StrategyType.SCALPING)
    await sm.assign_strategy("ETH/USDC", StrategyType.INTRADAY)
    await sm.assign_strategy("LINK/USDC", StrategyType.SWING)

    assert len(sm.pair_strategies) == 3
    assert sm.pair_strategies["BTC/USDC"].strategy_type == StrategyType.SCALPING
    assert sm.pair_strategies["ETH/USDC"].strategy_type == StrategyType.INTRADAY
    assert sm.pair_strategies["LINK/USDC"].strategy_type == StrategyType.SWING

    await sm.disconnect()


@pytest.mark.asyncio
async def test_enable_disable_strategy():
    """Test enabling and disabling strategies."""
    sm = StrategyManagerAgent()
    await sm.connect()

    await sm.assign_strategy("BTC/USDC", StrategyType.SCALPING)

    # Initially enabled
    assert sm.pair_strategies["BTC/USDC"].enabled is True

    # Disable
    await sm.enable_strategy("BTC/USDC", enabled=False)
    assert sm.pair_strategies["BTC/USDC"].enabled is False

    # Re-enable
    await sm.enable_strategy("BTC/USDC", enabled=True)
    assert sm.pair_strategies["BTC/USDC"].enabled is True

    await sm.disconnect()


@pytest.mark.asyncio
async def test_strategy_performance_tracking():
    """Test strategy performance is tracked correctly."""
    sm = StrategyManagerAgent()
    await sm.connect()

    await sm.assign_strategy("BTC/USDC", StrategyType.SCALPING)

    # Simulate winning trade
    await sm._handle_trade_executed({
        "data": {
            "pair": "BTC/USDC",
            "pnl": 50.0,
        }
    })

    perf = sm.strategy_performance[StrategyType.SCALPING.value]
    assert perf.trades_executed == 1
    assert perf.winning_trades == 1
    assert perf.losing_trades == 0
    assert perf.total_pnl == 50.0
    assert perf.win_rate == 1.0

    # Simulate losing trade
    await sm._handle_trade_executed({
        "data": {
            "pair": "BTC/USDC",
            "pnl": -30.0,
        }
    })

    assert perf.trades_executed == 2
    assert perf.winning_trades == 1
    assert perf.losing_trades == 1
    assert perf.total_pnl == 20.0
    assert perf.win_rate == 0.5

    await sm.disconnect()


@pytest.mark.asyncio
async def test_strategy_comparison():
    """Test comparing performance across multiple strategies."""
    sm = StrategyManagerAgent()
    await sm.connect()

    # Assign and trade with multiple strategies
    await sm.assign_strategy("BTC/USDC", StrategyType.SCALPING)
    await sm.assign_strategy("ETH/USDC", StrategyType.INTRADAY)

    # Scalping wins $100
    await sm._handle_trade_executed({
        "data": {"pair": "BTC/USDC", "pnl": 100.0}
    })

    # Intraday wins $200
    await sm._handle_trade_executed({
        "data": {"pair": "ETH/USDC", "pnl": 200.0}
    })

    # Get comparison
    comparison = await sm.get_strategy_comparison()

    assert comparison["total_pnl"] == 300.0
    assert comparison["best_performer"] == StrategyType.INTRADAY.value
    assert comparison["strategies"][StrategyType.SCALPING.value]["total_pnl"] == 100.0
    assert comparison["strategies"][StrategyType.INTRADAY.value]["total_pnl"] == 200.0

    await sm.disconnect()


@pytest.mark.asyncio
async def test_strategy_configs():
    """Test each strategy has correct configuration."""
    sm = StrategyManagerAgent()

    # Scalping config
    scalping = sm.available_strategies[StrategyType.SCALPING]
    assert scalping["timeframe"] == "1m"
    assert scalping["target_profit"] == 0.5
    assert "EMA_9" in scalping["indicators"]

    # Intraday config
    intraday = sm.available_strategies[StrategyType.INTRADAY]
    assert intraday["timeframe"] == "15m"
    assert intraday["target_profit"] == 1.5
    assert "MA_20" in intraday["indicators"]

    # Swing config
    swing = sm.available_strategies[StrategyType.SWING]
    assert swing["timeframe"] == "4h"
    assert swing["target_profit"] == 5.0
    assert "MA_200" in swing["indicators"]
