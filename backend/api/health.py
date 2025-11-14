"""
Health check endpoints.

Agent: Logging & Monitoring Agent
"""

from fastapi import APIRouter
from datetime import datetime
from core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    System health check.

    Returns:
        dict: Health status of all components
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0-alpha",
        "mode": settings.trading_mode,
        "components": {
            "event_bus": "operational",
            "market_data": "initializing",
            "indicators": "initializing",
            "strategies": "initializing"
        }
    }


@router.get("/status")
async def system_status():
    """
    Detailed system status.

    Returns:
        dict: Detailed status of all agents and components
    """
    return {
        "sprint": "1.2",
        "mode": settings.trading_mode,
        "trading_pairs": settings.trading_pairs,
        "agents": {
            "total": 25,
            "operational": 2,  # Will update as agents are implemented
            "initializing": 23
        },
        "strategies": {
            "scalping": settings.enable_scalping,
            "intraday": settings.enable_intraday,
            "swing": settings.enable_swing
        }
    }
