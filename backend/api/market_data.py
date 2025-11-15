"""
Market data API endpoints.

Agent: Dashboard Agent
Provides: Real-time market data to frontend
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
import random
import structlog

router = APIRouter()

logger = structlog.get_logger(__name__)


def _generate_mock_ticker_data(pair: str) -> dict:
    """
    Generate mock ticker data for a trading pair.

    Args:
        pair: Trading pair (e.g., BTC/USDC)

    Returns:
        dict: Mock market data with realistic values
    """
    # Base prices for different pairs
    base_prices = {
        "BTC/USDC": 43500.00,
        "ETH/USDC": 2280.00,
        "LINK/USDC": 14.50,
        "SOL/USDC": 98.75,
        "AVAX/USDC": 36.20,
    }

    # Get base price or use default
    base_price = base_prices.get(pair, 100.00)

    # Add some randomness to make it realistic
    price_variance = random.uniform(-0.02, 0.02)  # +/- 2%
    current_price = base_price * (1 + price_variance)

    # Calculate other values based on current price
    high_24h = current_price * random.uniform(1.01, 1.05)
    low_24h = current_price * random.uniform(0.95, 0.99)
    change_24h = random.uniform(-5.0, 5.0)

    # Volume based on asset
    volume_multiplier = 1000000 if "BTC" in pair else 500000
    volume_24h = volume_multiplier * random.uniform(0.8, 1.2)

    # RSI - Random but realistic (30-70 range mostly)
    rsi = random.uniform(35, 75)

    # MACD values - correlated with price movement
    macd_line = random.uniform(-50, 50)
    signal_line = macd_line * random.uniform(0.8, 1.2)
    histogram = macd_line - signal_line

    # Moving averages
    ma20 = current_price * random.uniform(0.98, 1.02)
    ma50 = current_price * random.uniform(0.96, 1.04)
    ma200 = current_price * random.uniform(0.92, 1.08)

    return {
        "pair": pair,
        "price": round(current_price, 2),
        "change_24h": round(change_24h, 2),
        "volume_24h": round(volume_24h, 2),
        "high_24h": round(high_24h, 2),
        "low_24h": round(low_24h, 2),
        "rsi": round(rsi, 2),
        "macd": {
            "macd": round(macd_line, 2),
            "signal": round(signal_line, 2),
            "histogram": round(histogram, 2)
        },
        "ma": {
            "ma20": round(ma20, 2),
            "ma50": round(ma50, 2),
            "ma200": round(ma200, 2)
        },
        "timestamp": datetime.utcnow().isoformat(),
        "status": "mock_data"
    }


@router.get("/market/ticker")
async def get_ticker(
    pair: str = Query(..., description="Trading pair (e.g., BTC/USDC)")
):
    """
    Get real-time ticker data for a trading pair.

    Args:
        pair: Trading pair (BTC/USDC, ETH/USDC, etc.)

    Returns:
        dict: Real-time market data including price, volume, and technical indicators

    Example:
        GET /api/market/ticker?pair=BTC/USDC

    Response:
        {
            "pair": "BTC/USDC",
            "price": 43500.50,
            "change_24h": 2.34,
            "volume_24h": 1234567.89,
            "high_24h": 44000.00,
            "low_24h": 42800.00,
            "timestamp": "2025-11-15T10:30:00Z",
            "status": "live"
        }
    """
    logger.info("ticker_request", pair=pair)

    # Validate pair format
    if "/" not in pair:
        raise HTTPException(
            status_code=400,
            detail="Invalid pair format. Expected format: BASE/QUOTE (e.g., BTC/USDC)"
        )

    # Try to get REAL live data from CoinEx
    try:
        import ccxt.async_support as ccxt

        # Create CoinEx exchange instance
        exchange = ccxt.coinex({
            "enableRateLimit": True,
            "timeout": 10000,
        })

        # Fetch real ticker data
        ticker = await exchange.fetch_ticker(pair)
        await exchange.close()

        # Return real live data
        ticker_data = {
            "pair": pair,
            "price": ticker.get("last", 0),
            "change_24h": ticker.get("percentage", 0),
            "volume_24h": ticker.get("quoteVolume", 0),
            "high_24h": ticker.get("high", 0),
            "low_24h": ticker.get("low", 0),
            "bid": ticker.get("bid"),
            "ask": ticker.get("ask"),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "live"  # REAL LIVE DATA
        }

        logger.info(
            "live_ticker_fetched",
            pair=pair,
            price=ticker_data["price"],
            status="live"
        )

        return ticker_data

    except Exception as e:
        logger.error(
            "failed_to_fetch_live_data",
            pair=pair,
            error=str(e)
        )

        # Fallback to mock data if CoinEx fails
        ticker_data = _generate_mock_ticker_data(pair)
        ticker_data["status"] = "mock_data"
        ticker_data["error"] = str(e)

        return ticker_data


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
