"""
Trading Control API - Start/Stop trading and manage strategies

Handles:
- Starting/stopping demo/live trading
- Strategy selection
- Mode switching (Demo ↔ Live)
- Trading status monitoring

Agent: Dashboard Agent
Squad: UX
Sprint: 5.1
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
import structlog

from core.config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/trading", tags=["trading_control"])

# Global state (in production, this would be in Redis or database)
trading_state = {
    "is_trading": False,
    "active_strategy": None,
    "mode": settings.trading_mode,  # "demo" or "live"
    "started_at": None,
    "stopped_at": None,
}


class StartTradingRequest(BaseModel):
    """Request to start trading"""
    strategy: Literal["scalping", "intraday", "swing", "ma_crossover"]
    mode: Optional[Literal["demo", "live"]] = None


class StopTradingRequest(BaseModel):
    """Request to stop trading"""
    close_positions: bool = True


class StrategyChangeRequest(BaseModel):
    """Request to change active strategy"""
    strategy: Literal["scalping", "intraday", "swing", "ma_crossover"]


class ModeChangeRequest(BaseModel):
    """Request to change trading mode"""
    mode: Literal["demo", "live"]
    close_positions: bool = True


@router.get("/status")
async def get_trading_status():
    """
    Get current trading status

    Returns:
        - is_trading: Whether trading is currently active
        - active_strategy: Current strategy name
        - mode: Trading mode (demo/live)
        - started_at: When trading was started (if active)
    """
    return {
        "status": "success",
        "data": trading_state
    }


@router.post("/start")
async def start_trading(request: StartTradingRequest):
    """
    Start trading with specified strategy

    In demo mode:
    - Simulates trades without real funds
    - Uses virtual portfolio

    In live mode:
    - Places real orders on CoinEx
    - Requires API credentials

    Args:
        request: Trading configuration (strategy, mode)

    Returns:
        Success message with trading status

    Raises:
        400: If trading is already active
        403: If live mode requires API keys
    """
    if trading_state["is_trading"]:
        raise HTTPException(
            status_code=400,
            detail="Trading is already active. Stop trading first."
        )

    # Use requested mode or default to current mode
    mode = request.mode or trading_state["mode"]

    # Validate live mode requirements
    if mode == "live":
        # TODO: Check for API credentials
        logger.warning(
            "live_trading_start_requested",
            strategy=request.strategy,
            warning="Live trading requires API credentials"
        )

    # Update state
    import datetime
    trading_state["is_trading"] = True
    trading_state["active_strategy"] = request.strategy
    trading_state["mode"] = mode
    trading_state["started_at"] = datetime.datetime.utcnow().isoformat()
    trading_state["stopped_at"] = None

    logger.info(
        "trading_started",
        strategy=request.strategy,
        mode=mode
    )

    # TODO Sprint 5.1: Actually start trading agents
    # - Initialize Strategy Orchestrator with selected strategy
    # - Start Market Data Agent
    # - Start Indicator Agents
    # - Start Signal Synthesis
    # - Start Execution Agent

    return {
        "status": "success",
        "message": f"Trading started with {request.strategy} strategy in {mode} mode",
        "data": trading_state
    }


@router.post("/stop")
async def stop_trading(request: StopTradingRequest):
    """
    Stop trading and optionally close positions

    Args:
        request: Stop configuration (close_positions flag)

    Returns:
        Success message

    Raises:
        400: If trading is not active
    """
    if not trading_state["is_trading"]:
        raise HTTPException(
            status_code=400,
            detail="Trading is not active"
        )

    logger.info(
        "trading_stopping",
        close_positions=request.close_positions
    )

    # TODO: Close positions if requested
    if request.close_positions:
        # Close all open positions
        logger.info("closing_all_positions")

    # Update state
    import datetime
    trading_state["is_trading"] = False
    trading_state["stopped_at"] = datetime.datetime.utcnow().isoformat()

    logger.info("trading_stopped")

    return {
        "status": "success",
        "message": "Trading stopped",
        "data": trading_state
    }


@router.post("/strategy")
async def change_strategy(request: StrategyChangeRequest):
    """
    Change active trading strategy

    Can be changed while trading is active (hot-swap).

    Args:
        request: New strategy name

    Returns:
        Success message
    """
    old_strategy = trading_state["active_strategy"]
    trading_state["active_strategy"] = request.strategy

    logger.info(
        "strategy_changed",
        old_strategy=old_strategy,
        new_strategy=request.strategy,
        is_trading=trading_state["is_trading"]
    )

    # TODO: Hot-swap strategy if trading is active

    return {
        "status": "success",
        "message": f"Strategy changed to {request.strategy}",
        "data": trading_state
    }


@router.post("/mode")
async def change_mode(request: ModeChangeRequest):
    """
    Switch between demo and live trading modes

    Important:
    - Switching to live mode requires API credentials
    - It's recommended to close positions before switching

    Args:
        request: New mode and close_positions flag

    Returns:
        Success message

    Raises:
        400: If switching to live without proper setup
    """
    old_mode = trading_state["mode"]

    # Validate live mode switch
    if request.mode == "live":
        # TODO: Validate API credentials exist
        logger.warning(
            "mode_switch_to_live",
            warning="Ensure API credentials are configured"
        )

    # Close positions if requested
    if request.close_positions and trading_state["is_trading"]:
        logger.info("closing_positions_before_mode_switch")
        # TODO: Close all positions

    # Update mode
    trading_state["mode"] = request.mode

    logger.info(
        "mode_changed",
        old_mode=old_mode,
        new_mode=request.mode
    )

    return {
        "status": "success",
        "message": f"Switched from {old_mode} to {request.mode} mode",
        "data": trading_state
    }
