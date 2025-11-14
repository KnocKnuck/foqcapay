"""
Tests for Trade Execution Agent

Agent: Bug & Resolution Agent
Squad: Execution
Sprint: 3.2

Tests Cover:
- Order execution (demo & live modes)
- Position opening and closing
- Trailing stop-loss (BUG-055 fix verification)
- Multi-pair position tracking
- Stop-loss and take-profit triggers

Run:
    pytest tests/test_trade_execution.py -v
"""

import pytest
import asyncio
from agents.trade_execution import (
    TradeExecutionAgent,
    Position,
    Order,
    OrderSide,
    OrderType,
    OrderStatus,
)


@pytest.mark.asyncio
async def test_trade_execution_initialization():
    """Test trade execution agent initializes in demo mode."""
    te = TradeExecutionAgent()

    assert te.trading_mode == "demo"
    assert len(te.positions) == 0
    assert len(te.orders) == 0
    assert te.metrics["total_orders"] == 0


@pytest.mark.asyncio
async def test_demo_order_execution():
    """Test order execution in demo mode."""
    te = TradeExecutionAgent()
    await te.connect()

    order = await te.execute_order(
        pair="BTC/USDC",
        side=OrderSide.BUY,
        size=100.0,
        price=30000.0,
        order_type=OrderType.MARKET,
    )

    assert order.status == OrderStatus.FILLED
    assert order.filled_price == 30000.0
    assert te.metrics["total_orders"] == 1
    assert te.metrics["filled_orders"] == 1

    await te.disconnect()


@pytest.mark.asyncio
async def test_position_creation():
    """Test position is created correctly."""
    position = Position(
        pair="BTC/USDC",
        side=OrderSide.BUY,
        entry_price=30000.0,
        current_price=30000.0,
        position_size=100.0,
        stop_loss=29000.0,
        take_profit=31000.0,
    )

    assert position.pair == "BTC/USDC"
    assert position.entry_price == 30000.0
    assert position.trailing_stop_enabled is True
    assert position.highest_price == 30000.0
    assert position.trailing_stop_distance == 1000.0  # 30000 - 29000


@pytest.mark.asyncio
async def test_bug_055_fix_multi_pair_trailing_stops():
    """
    BUG-055 FIX VERIFICATION: Multi-pair trailing stops.

    Verify that trailing stops are tracked independently per pair.
    Each pair should have its own highest_price and stop_loss tracking.
    """
    te = TradeExecutionAgent()
    await te.connect()

    # Create positions for BTC and ETH
    btc_position = Position(
        pair="BTC/USDC",
        side=OrderSide.BUY,
        entry_price=30000.0,
        current_price=30000.0,
        position_size=100.0,
        stop_loss=29000.0,
        take_profit=32000.0,
    )

    eth_position = Position(
        pair="ETH/USDC",
        side=OrderSide.BUY,
        entry_price=2000.0,
        current_price=2000.0,
        position_size=100.0,
        stop_loss=1900.0,
        take_profit=2200.0,
    )

    te.positions["BTC/USDC"] = btc_position
    te.positions["ETH/USDC"] = eth_position

    # Update BTC price to 31000 (up 1000)
    await te._update_position_price(btc_position, 31000.0)

    # BTC trailing stop should update
    assert btc_position.highest_price == 31000.0
    assert btc_position.stop_loss == 30000.0  # Trailed up by 1000

    # ETH trailing stop should NOT be affected (independent tracking)
    assert eth_position.highest_price == 2000.0  # Unchanged
    assert eth_position.stop_loss == 1900.0  # Unchanged

    # Now update ETH price to 2100 (up 100)
    await te._update_position_price(eth_position, 2100.0)

    # ETH trailing stop should update
    assert eth_position.highest_price == 2100.0
    assert eth_position.stop_loss == 2000.0  # Trailed up by 100

    # BTC should still be at previous values (independent)
    assert btc_position.highest_price == 31000.0
    assert btc_position.stop_loss == 30000.0

    await te.disconnect()


@pytest.mark.asyncio
async def test_trailing_stop_updates_on_price_increase():
    """Test trailing stop updates when price increases."""
    te = TradeExecutionAgent()
    await te.connect()

    position = Position(
        pair="BTC/USDC",
        side=OrderSide.BUY,
        entry_price=30000.0,
        current_price=30000.0,
        position_size=100.0,
        stop_loss=29000.0,
        take_profit=32000.0,
    )

    te.positions["BTC/USDC"] = position

    # Price goes up to 31000
    await te._update_position_price(position, 31000.0)

    # Stop should trail up
    assert position.highest_price == 31000.0
    assert position.stop_loss == 30000.0  # Trailed from 29000 to 30000

    # Price goes up to 32000
    await te._update_position_price(position, 32000.0)

    # Stop should trail up again
    assert position.highest_price == 32000.0
    assert position.stop_loss == 31000.0  # Trailed from 30000 to 31000

    await te.disconnect()


@pytest.mark.asyncio
async def test_trailing_stop_does_not_move_down():
    """Test trailing stop never moves down."""
    te = TradeExecutionAgent()
    await te.connect()

    position = Position(
        pair="BTC/USDC",
        side=OrderSide.BUY,
        entry_price=30000.0,
        current_price=30000.0,
        position_size=100.0,
        stop_loss=29000.0,
        take_profit=32000.0,
    )

    te.positions["BTC/USDC"] = position

    # Price goes up to 31000
    await te._update_position_price(position, 31000.0)
    assert position.stop_loss == 30000.0

    # Price drops to 30500
    await te._update_position_price(position, 30500.0)

    # Stop should NOT move down
    assert position.stop_loss == 30000.0  # Still at 30000
    assert position.highest_price == 31000.0  # Peak still at 31000

    await te.disconnect()


@pytest.mark.asyncio
async def test_stop_loss_trigger():
    """Test position closes when stop-loss is hit."""
    te = TradeExecutionAgent()
    await te.connect()

    position = Position(
        pair="BTC/USDC",
        side=OrderSide.BUY,
        entry_price=30000.0,
        current_price=30000.0,
        position_size=100.0,
        stop_loss=29000.0,
        take_profit=32000.0,
    )

    te.positions["BTC/USDC"] = position

    # Price drops to stop level
    await te._update_position_price(position, 29000.0)

    # Position should be closed
    assert "BTC/USDC" not in te.positions
    assert te.metrics["trailing_stops_triggered"] == 1

    await te.disconnect()


@pytest.mark.asyncio
async def test_take_profit_trigger():
    """Test position closes when take-profit is hit."""
    te = TradeExecutionAgent()
    await te.connect()

    position = Position(
        pair="BTC/USDC",
        side=OrderSide.BUY,
        entry_price=30000.0,
        current_price=30000.0,
        position_size=100.0,
        stop_loss=29000.0,
        take_profit=31500.0,
    )

    te.positions["BTC/USDC"] = position

    # Price rises to take-profit level
    await te._update_position_price(position, 31500.0)

    # Position should be closed
    assert "BTC/USDC" not in te.positions
    assert te.metrics["take_profits_hit"] == 1

    await te.disconnect()


@pytest.mark.asyncio
async def test_unrealized_pnl_calculation():
    """Test unrealized P&L is calculated correctly."""
    te = TradeExecutionAgent()

    position = Position(
        pair="BTC/USDC",
        side=OrderSide.BUY,
        entry_price=30000.0,
        current_price=30000.0,
        position_size=100.0,
        stop_loss=29000.0,
        take_profit=32000.0,
    )

    te.positions["BTC/USDC"] = position

    # Price goes up 10% (30000 -> 33000)
    await te._update_position_price(position, 33000.0)

    # P&L should be 10% of position size = 10
    expected_pnl = (3000 / 30000) * 100  # 10.0
    assert abs(position.unrealized_pnl - expected_pnl) < 0.01


@pytest.mark.asyncio
async def test_multiple_pairs_independent_tracking():
    """Test multiple pairs are tracked independently."""
    te = TradeExecutionAgent()
    await te.connect()

    # Create 3 different positions
    pairs = ["BTC/USDC", "ETH/USDC", "LINK/USDC"]
    entry_prices = [30000.0, 2000.0, 15.0]

    for pair, entry_price in zip(pairs, entry_prices):
        position = Position(
            pair=pair,
            side=OrderSide.BUY,
            entry_price=entry_price,
            current_price=entry_price,
            position_size=100.0,
            stop_loss=entry_price * 0.95,
            take_profit=entry_price * 1.05,
        )
        te.positions[pair] = position

    # Verify all 3 are tracked
    assert len(te.positions) == 3

    # Update each independently
    await te._update_position_price(te.positions["BTC/USDC"], 31000.0)
    await te._update_position_price(te.positions["ETH/USDC"], 2100.0)
    await te._update_position_price(te.positions["LINK/USDC"], 16.0)

    # Verify each has correct values
    assert te.positions["BTC/USDC"].current_price == 31000.0
    assert te.positions["ETH/USDC"].current_price == 2100.0
    assert te.positions["LINK/USDC"].current_price == 16.0

    await te.disconnect()
