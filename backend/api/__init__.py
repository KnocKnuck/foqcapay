"""
FastAPI routes for the FOQCAPAY trading bot.

Agent: Dashboard Agent (provides data to frontend)
Sprint: Through 5.2
"""

from fastapi import APIRouter

router = APIRouter()

# Import route modules
from . import market_data, health

# Sprint 4.2 - Monitoring
try:
    from . import monitoring, websocket
    router.include_router(monitoring.router)
    router.include_router(websocket.router)
except ImportError:
    pass

# Sprint 5.1 - Trading Dashboard APIs
try:
    from . import trades, positions, performance
    router.include_router(trades.router)
    router.include_router(positions.router)
    router.include_router(performance.router)
except ImportError:
    pass

# Sprint 5.2 - Backtesting & Export
try:
    from . import backtest, export
    router.include_router(backtest.router)
    router.include_router(export.router)
except ImportError:
    pass

__all__ = ["router"]
