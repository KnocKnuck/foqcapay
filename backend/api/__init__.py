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
except ImportError as e:
    import structlog
    logger = structlog.get_logger(__name__)
    logger.warning("failed_to_import_sprint_5_1_apis", error=str(e))

# Trading Control API (separate from others - no dependencies)
try:
    from . import trading_control
    router.include_router(trading_control.router)
except ImportError as e:
    import structlog
    logger = structlog.get_logger(__name__)
    logger.warning("failed_to_import_trading_control_api", error=str(e))

# Sprint 5.2 - Backtesting & Export
try:
    from . import backtest, export
    router.include_router(backtest.router)
    router.include_router(export.router)
except ImportError:
    pass

__all__ = ["router"]
