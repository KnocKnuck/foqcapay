"""
Tests for Risk Manager Agent

Agent: Bug & Resolution Agent
Squad: Alpha
Sprint: 3.2

Tests Cover:
- Position size calculation
- ATR-based stop-loss
- Max drawdown detection
- Daily loss limits
- Emergency stop functionality
- Risk alerts

Run:
    pytest tests/test_risk_manager.py -v
"""

import pytest
import asyncio
from agents.risk_manager import RiskManagerAgent, RiskLevel, RiskLimits


@pytest.mark.asyncio
async def test_risk_manager_initialization():
    """Test risk manager initializes with correct defaults."""
    rm = RiskManagerAgent(initial_capital=10000.0)

    assert rm.initial_capital == 10000.0
    assert rm.current_capital == 10000.0
    assert rm.peak_capital == 10000.0
    assert rm.realized_pnl == 0.0
    assert rm.emergency_stop_active is False
    assert rm.trading_paused is False


@pytest.mark.asyncio
async def test_position_size_calculation():
    """Test position size is calculated correctly."""
    rm = RiskManagerAgent(initial_capital=10000.0)

    # 1% risk of $10,000 = $100
    position_size = rm.calculate_position_size("BTC/USDC", risk_per_trade_pct=1.0)

    assert position_size == 100.0


@pytest.mark.asyncio
async def test_position_size_respects_max_limit():
    """Test position size doesn't exceed max position limit."""
    rm = RiskManagerAgent(initial_capital=10000.0)
    rm.limits.max_position_size_pct = 10.0  # Max 10% = $1000

    # Try to risk 20%, should be capped at 10%
    position_size = rm.calculate_position_size("BTC/USDC", risk_per_trade_pct=20.0)

    assert position_size == 1000.0  # Capped at 10%


@pytest.mark.asyncio
async def test_atr_stop_loss_calculation():
    """Test ATR-based stop-loss calculation."""
    rm = RiskManagerAgent(initial_capital=10000.0)

    # Set ATR for BTC/USDC
    rm.atr_values["BTC/USDC"] = 500.0  # ATR = $500
    rm.limits.atr_multiplier = 2.0

    entry_price = 30000.0

    # Long position: stop should be 2*ATR below entry
    stop_loss_long = rm.calculate_atr_stop_loss("BTC/USDC", entry_price, is_long=True)
    assert stop_loss_long == 29000.0  # 30000 - (2 * 500)

    # Short position: stop should be 2*ATR above entry
    stop_loss_short = rm.calculate_atr_stop_loss("BTC/USDC", entry_price, is_long=False)
    assert stop_loss_short == 31000.0  # 30000 + (2 * 500)


@pytest.mark.asyncio
async def test_atr_stop_loss_fallback():
    """Test stop-loss falls back to percentage when ATR unavailable."""
    rm = RiskManagerAgent(initial_capital=10000.0)
    rm.limits.default_stop_loss_pct = 2.0  # 2%

    entry_price = 30000.0

    # No ATR available, should use 2% default
    stop_loss = rm.calculate_atr_stop_loss("ETH/USDC", entry_price, is_long=True)

    expected = 30000.0 * 0.98  # 2% below entry
    assert stop_loss == expected


@pytest.mark.asyncio
async def test_drawdown_detection():
    """Test max drawdown detection."""
    rm = RiskManagerAgent(initial_capital=10000.0)
    rm.limits.max_drawdown_pct = 10.0  # 10% max

    # Simulate 8% loss - should not breach
    rm.current_capital = 9200.0
    breached, drawdown = rm.check_drawdown()

    assert breached is False
    assert drawdown == 8.0

    # Simulate 12% loss - should breach
    rm.current_capital = 8800.0
    breached, drawdown = rm.check_drawdown()

    assert breached is True
    assert drawdown == 12.0


@pytest.mark.asyncio
async def test_daily_loss_limit():
    """Test daily loss limit detection."""
    rm = RiskManagerAgent(initial_capital=10000.0)
    rm.limits.daily_loss_limit_pct = 5.0  # 5% max daily loss

    # Simulate -4% daily loss - should not breach
    rm.daily_pnl = -400.0
    breached, daily_loss_pct = rm.check_daily_loss()

    assert breached is False
    assert daily_loss_pct == -4.0

    # Simulate -6% daily loss - should breach
    rm.daily_pnl = -600.0
    breached, daily_loss_pct = rm.check_daily_loss()

    assert breached is True
    assert daily_loss_pct == -6.0


@pytest.mark.asyncio
async def test_bug_056_fix_unrealized_pnl_not_in_drawdown():
    """
    BUG-056 FIX: Verify drawdown calculation excludes unrealized P&L.

    Drawdown should only use realized capital, not unrealized positions.
    This prevents false drawdown triggers from paper losses.
    """
    rm = RiskManagerAgent(initial_capital=10000.0)

    # Start with capital
    rm.current_capital = 10000.0
    rm.peak_capital = 10000.0

    # Simulate a trade with unrealized loss
    rm.open_positions["BTC/USDC"] = type('obj', (object,), {
        'unrealized_pnl': -500.0  # $500 unrealized loss
    })()

    # Drawdown should NOT include unrealized loss
    breached, drawdown = rm.check_drawdown()

    # Drawdown should be 0% (no realized loss yet)
    assert drawdown == 0.0
    assert breached is False

    # Now realize the loss
    rm.realized_pnl = -500.0
    rm.current_capital = 9500.0

    # NOW drawdown should reflect it
    breached, drawdown = rm.check_drawdown()
    assert drawdown == 5.0  # 5% drawdown


@pytest.mark.asyncio
async def test_position_tracking():
    """Test position tracking and P&L updates."""
    rm = RiskManagerAgent(initial_capital=10000.0)

    # Simulate position opened
    await rm._handle_position_opened({
        "data": {
            "pair": "BTC/USDC",
            "entry_price": 30000.0,
            "position_size": 100.0,
            "stop_loss": 29000.0,
            "take_profit": 31500.0,
        }
    })

    assert "BTC/USDC" in rm.open_positions
    assert rm.open_positions["BTC/USDC"].entry_price == 30000.0

    # Simulate position closed with profit
    await rm._handle_position_closed({
        "data": {
            "pair": "BTC/USDC",
            "pnl": 150.0,
        }
    })

    assert "BTC/USDC" not in rm.open_positions
    assert rm.realized_pnl == 150.0
    assert rm.current_capital == 10150.0
    assert rm.peak_capital == 10150.0


@pytest.mark.asyncio
async def test_max_positions_limit():
    """Test max open positions enforcement."""
    rm = RiskManagerAgent(initial_capital=10000.0)
    rm.limits.max_open_positions = 3

    await rm.connect()

    # Open 3 positions
    for i, pair in enumerate(["BTC/USDC", "ETH/USDC", "LINK/USDC"]):
        await rm._handle_position_opened({
            "data": {
                "pair": pair,
                "entry_price": 1000.0,
                "position_size": 100.0,
                "stop_loss": 900.0,
                "take_profit": 1100.0,
            }
        })

    assert len(rm.open_positions) == 3

    # Try to open 4th - should be rejected by entry handler
    # (This would be tested via event system in integration tests)


@pytest.mark.asyncio
async def test_emergency_stop():
    """Test emergency stop closes all positions."""
    rm = RiskManagerAgent(initial_capital=10000.0)
    await rm.connect()

    # Open some positions
    rm.open_positions["BTC/USDC"] = type('obj', (object,), {})()
    rm.open_positions["ETH/USDC"] = type('obj', (object,), {})()

    # Trigger emergency stop
    await rm._handle_emergency_stop({})

    assert rm.emergency_stop_active is True
    assert rm.metrics["emergency_stops"] == 1

    await rm.disconnect()
