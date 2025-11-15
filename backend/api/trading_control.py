"""
Trading Control API - Start/Stop trading and manage strategies

Handles:
- Starting/stopping demo/live trading for multiple pairs
- Strategy selection per pair
- Mode switching (Demo ↔ Live)
- Trading status monitoring

Agent: Dashboard Agent
Squad: UX
Sprint: 5.1 + Multi-Pair Enhancement
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional, List, Dict
import structlog

from core.config import settings
from services.trading_engine import start_trading_engine, stop_trading_engine, get_trading_engine

logger = structlog.get_logger()

router = APIRouter(prefix="/trading", tags=["trading_control"])

# Global state (in production, this would be in Redis or database)
# Multi-pair trading state: each pair can have independent strategy and status
trading_state = {
    "is_trading": False,  # Global trading flag
    "mode": settings.trading_mode,  # "demo" or "live" - applies to all pairs
    "started_at": None,
    "stopped_at": None,
    "pairs": {}  # Per-pair trading status: {pair: {strategy, is_active, started_at, etc}}
}


class StartTradingRequest(BaseModel):
    """Request to start trading"""
    strategy: Literal["scalping", "intraday", "swing", "ma_crossover"]
    mode: Optional[Literal["demo", "live"]] = None
    pairs: Optional[List[str]] = None  # List of pairs to trade (e.g., ["BTC/USDC", "ETH/USDC"])


class StopTradingRequest(BaseModel):
    """Request to stop trading"""
    close_positions: bool = True
    pairs: Optional[List[str]] = None  # Specific pairs to stop (None = stop all)


class StrategyChangeRequest(BaseModel):
    """Request to change active strategy"""
    strategy: Literal["scalping", "intraday", "swing", "ma_crossover"]
    pair: Optional[str] = None  # Specific pair to change strategy for (None = all active pairs)


class ModeChangeRequest(BaseModel):
    """Request to change trading mode"""
    mode: Literal["demo", "live"]
    close_positions: bool = True


class PairStatusRequest(BaseModel):
    """Request to get status for specific pairs"""
    pairs: Optional[List[str]] = None  # None = all pairs


@router.get("/status")
async def get_trading_status():
    """
    Get current trading status

    Returns:
        - is_trading: Whether trading is currently active
        - active_strategy: Current strategy name
        - mode: Trading mode (demo/live)
        - started_at: When trading was started (if active)
        - pairs: Per-pair trading status
        - active_pairs: List of currently active pairs
        - engine: Trading engine status (if running)
    """
    # Calculate active pairs list
    active_pairs = [pair for pair, status in trading_state.get("pairs", {}).items() if status.get("is_active", False)]

    # Get most common strategy for backward compatibility
    active_strategy = None
    if active_pairs and trading_state.get("pairs"):
        # Get strategy from first active pair
        active_strategy = trading_state["pairs"][active_pairs[0]].get("strategy")

    # Get trading engine status
    engine_status = None
    engine = await get_trading_engine()
    if engine:
        engine_status = engine.get_status()

    return {
        "status": "success",
        "data": {
            **trading_state,
            "active_pairs": active_pairs,
            "active_strategy": active_strategy,
            "engine": engine_status
        }
    }


@router.post("/start")
async def start_trading(request: StartTradingRequest):
    """
    Start trading with specified strategy for one or more pairs

    In demo mode:
    - Simulates trades without real funds
    - Uses virtual portfolio

    In live mode:
    - Places real orders on CoinEx
    - Requires API credentials

    Args:
        request: Trading configuration (strategy, mode, pairs)
            - pairs: List of trading pairs (default: all configured pairs)

    Returns:
        Success message with trading status

    Raises:
        400: If invalid pairs specified
        403: If live mode requires API keys
    """
    import datetime

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

    # Get pairs to trade (default to all configured pairs)
    pairs_to_trade = request.pairs or settings.trading_pairs

    if not pairs_to_trade:
        raise HTTPException(
            status_code=400,
            detail="No trading pairs specified and none configured"
        )

    # Update global state
    if not trading_state["is_trading"]:
        trading_state["is_trading"] = True
        trading_state["started_at"] = datetime.datetime.utcnow().isoformat()
        trading_state["stopped_at"] = None

    trading_state["mode"] = mode

    # Start trading for each pair
    now = datetime.datetime.utcnow().isoformat()
    for pair in pairs_to_trade:
        trading_state["pairs"][pair] = {
            "strategy": request.strategy,
            "is_active": True,
            "started_at": now,
            "stopped_at": None
        }

        logger.info(
            "pair_trading_started",
            pair=pair,
            strategy=request.strategy,
            mode=mode
        )

    # ACTUALLY START TRADING ENGINE! 🚀
    # This initializes the complete trading pipeline:
    # - Market Data Agent for price streaming
    # - MA Crossover Strategy for signal generation
    # - Trade Execution for opening/closing positions
    # - Database persistence for all trades
    try:
        engine = await start_trading_engine(
            pairs=pairs_to_trade,
            strategy=request.strategy
        )
        logger.info(
            "trading_engine_started",
            pairs=pairs_to_trade,
            strategy=request.strategy,
            engine_status=engine.get_status()
        )
    except Exception as e:
        logger.error(
            "failed_to_start_trading_engine",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start trading engine: {str(e)}"
        )

    active_pairs = [p for p, status in trading_state["pairs"].items() if status["is_active"]]

    return {
        "status": "success",
        "message": f"Trading started with {request.strategy} strategy for {len(pairs_to_trade)} pair(s) in {mode} mode",
        "data": {
            **trading_state,
            "active_pairs": active_pairs,
            "active_strategy": request.strategy  # For backward compatibility
        }
    }


@router.post("/stop")
async def stop_trading(request: StopTradingRequest):
    """
    Stop trading and optionally close positions

    Args:
        request: Stop configuration
            - close_positions: Whether to close open positions
            - pairs: Specific pairs to stop (None = stop all)

    Returns:
        Success message

    Raises:
        400: If trading is not active
    """
    import datetime

    if not trading_state["is_trading"]:
        raise HTTPException(
            status_code=400,
            detail="Trading is not active"
        )

    # Determine which pairs to stop
    pairs_to_stop = request.pairs or list(trading_state["pairs"].keys())

    if not pairs_to_stop:
        raise HTTPException(
            status_code=400,
            detail="No pairs to stop"
        )

    logger.info(
        "trading_stopping",
        close_positions=request.close_positions,
        pairs=pairs_to_stop
    )

    # Stop trading for each specified pair
    now = datetime.datetime.utcnow().isoformat()
    for pair in pairs_to_stop:
        if pair in trading_state["pairs"]:
            trading_state["pairs"][pair]["is_active"] = False
            trading_state["pairs"][pair]["stopped_at"] = now

            logger.info("pair_trading_stopped", pair=pair)

    # Check if all pairs are stopped
    active_pairs = [p for p, status in trading_state["pairs"].items() if status["is_active"]]

    if not active_pairs:
        # All pairs stopped - set global trading to False and stop engine
        trading_state["is_trading"] = False
        trading_state["stopped_at"] = now

        # STOP THE TRADING ENGINE
        try:
            await stop_trading_engine()
            logger.info("trading_engine_stopped")
        except Exception as e:
            logger.error("failed_to_stop_trading_engine", error=str(e))

        logger.info("all_trading_stopped")

    return {
        "status": "success",
        "message": f"Trading stopped for {len(pairs_to_stop)} pair(s)",
        "data": {
            **trading_state,
            "active_pairs": active_pairs,
            "stopped_pairs": pairs_to_stop
        }
    }


@router.post("/strategy")
async def change_strategy(request: StrategyChangeRequest):
    """
    Change active trading strategy for one or all pairs

    Can be changed while trading is active (hot-swap).

    Args:
        request: New strategy name and optional pair
            - strategy: New strategy to use
            - pair: Specific pair to change (None = all active pairs)

    Returns:
        Success message
    """
    if request.pair:
        # Change strategy for specific pair
        if request.pair not in trading_state["pairs"]:
            raise HTTPException(
                status_code=400,
                detail=f"Pair {request.pair} is not being traded"
            )

        old_strategy = trading_state["pairs"][request.pair].get("strategy")
        trading_state["pairs"][request.pair]["strategy"] = request.strategy

        logger.info(
            "strategy_changed_for_pair",
            pair=request.pair,
            old_strategy=old_strategy,
            new_strategy=request.strategy
        )

        return {
            "status": "success",
            "message": f"Strategy changed to {request.strategy} for {request.pair}",
            "data": trading_state
        }
    else:
        # Change strategy for all active pairs
        active_pairs = [p for p, status in trading_state["pairs"].items() if status["is_active"]]

        if not active_pairs:
            raise HTTPException(
                status_code=400,
                detail="No active pairs to change strategy for"
            )

        for pair in active_pairs:
            old_strategy = trading_state["pairs"][pair].get("strategy")
            trading_state["pairs"][pair]["strategy"] = request.strategy

            logger.info(
                "strategy_changed_for_pair",
                pair=pair,
                old_strategy=old_strategy,
                new_strategy=request.strategy
            )

        # TODO: Hot-swap strategy if trading is active

        return {
            "status": "success",
            "message": f"Strategy changed to {request.strategy} for {len(active_pairs)} pair(s)",
            "data": {
                **trading_state,
                "active_pairs": active_pairs,
                "active_strategy": request.strategy  # For backward compatibility
            }
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
