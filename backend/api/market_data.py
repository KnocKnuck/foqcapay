"""
Market data API endpoints.

Agent: Dashboard Agent
Provides: Real-time market data to frontend
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.get("/marketdata")
async def get_market_data(
    symbol: str = Query(..., description="Trading pair (e.g., BTC/USDC)")
):
    """
    Get current market data for a trading pair.

    Args:
        symbol: Trading pair (BTC/USDC, ETH/USDC, etc.)

    Returns:
        dict: Current price, volume, and indicator values

    Example:
        GET /api/marketdata?symbol=BTC/USDC
    """
    # TODO Sprint 1.2: Connect to Market Data Agent
    # For now, return mock data

    return {
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat(),
        "price": 30125.50,
        "volume_24h": 1234567.89,
        "high_24h": 30500.00,
        "low_24h": 29800.00,
        "change_24h_pct": 2.34,
        "indicators": {
            "ma_20": 30050.00,
            "ma_50": 29900.00,
            "ma_200": 28500.00,
            "rsi_14": 68.5,
            "macd": None,  # Not implemented yet
            "bollinger_upper": None,
            "bollinger_lower": None
        },
        "status": "mock_data"  # Will be "live" once Market Data agent is connected
    }


@router.get("/pairs")
async def get_trading_pairs():
    """
    Get list of available trading pairs.

    Returns:
        dict: List of configured trading pairs
    """
    from core.config import settings

    return {
        "pairs": settings.trading_pairs,
        "count": len(settings.trading_pairs),
        "default": settings.trading_pairs[0] if settings.trading_pairs else None
    }
