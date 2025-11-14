"""
Tests for Configuration Management.

Agent: Bug & Resolution Agent
Squad: Alpha
Sprint: 1.2

Tests Cover:
- Loading settings from environment
- Default values
- Multi-pair configuration
- Trading mode validation

Run:
    pytest tests/test_config.py -v
"""

import pytest
from core.config import Settings


def test_default_settings():
    """Test that default settings load correctly."""
    settings = Settings()

    assert settings.app_env == "development"
    assert settings.debug is True
    assert settings.trading_mode in ["demo", "live"]


def test_trading_pairs_parsing():
    """Test that trading pairs are parsed from comma-separated string."""
    settings = Settings()

    pairs = settings.trading_pairs
    assert isinstance(pairs, list)
    assert len(pairs) >= 3  # At least BTC, ETH, LINK
    assert "BTC/USDC" in pairs or "BTCUSDC" in "".join(pairs)


def test_redis_url_construction():
    """Test Redis URL is constructed correctly."""
    settings = Settings()

    redis_url = settings.redis_url
    assert redis_url.startswith("redis://")
    assert str(settings.redis_port) in redis_url


def test_invalid_trading_mode():
    """Test that invalid trading mode raises error."""
    with pytest.raises(ValueError, match="Trading mode must be"):
        Settings(trading_mode="invalid")


def test_risk_management_defaults():
    """Test that risk management defaults are reasonable."""
    settings = Settings()

    assert 0 < settings.default_stop_loss_pct < 10
    assert 0 < settings.default_take_profit_pct < 20
    assert 0 < settings.max_position_size_pct <= 100
    assert settings.max_drawdown_pct > 0
