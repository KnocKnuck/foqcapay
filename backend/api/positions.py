"""
Positions API - Trading Positions Management with Database Persistence

Agent: API Development Agent
Squad: Alpha
Sprint: 4.3 (Updated from 5.1)

Provides endpoints for managing and viewing trading positions.
NOW WITH DATABASE PERSISTENCE - all positions stored in SQLite.

Agent: #20 API Development Agent
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import structlog

from core.database import DatabaseService, get_db_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/positions", tags=["positions"])


# Pydantic models for request validation
class PositionCreate(BaseModel):
    """Model for opening a new position."""

    pair: str
    side: str  # buy or sell
    entry_price: float
    size: float
    strategy: str = "unknown"
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None


class PositionUpdate(BaseModel):
    """Model for updating a position."""

    current_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    trailing_stop_activation: Optional[float] = None


@router.get("")
async def get_positions(
    pair: Optional[str] = None,
    strategy: Optional[str] = None,
    db: DatabaseService = Depends(get_db_service),
):
    """
    Get all open positions from database.

    Returns list of currently open trading positions with
    real-time P&L calculations.
    """
    logger.info("Fetching open positions", pair=pair, strategy=strategy)

    # Fetch open positions from database
    positions = await db.get_open_positions(pair=pair, strategy=strategy)

    # Convert to dict format
    positions_list = []
    total_unrealized_pnl = 0.0

    for pos in positions:
        pos_dict = {
            "id": pos.position_id,
            "pair": pos.pair,
            "side": pos.side,
            "strategy": pos.strategy,
            "entryPrice": pos.entry_price,
            "currentPrice": pos.current_price or pos.entry_price,
            "size": pos.size,
            "unrealizedPnL": pos.unrealized_pnl,
            "unrealizedPnLPct": pos.unrealized_pnl_percent,
            "stopLoss": pos.stop_loss,
            "takeProfit": pos.take_profit,
            "trailingStop": pos.trailing_stop,
            "entryTime": pos.entry_time.isoformat(),
            "status": pos.status,
        }
        positions_list.append(pos_dict)
        total_unrealized_pnl += pos.unrealized_pnl

    logger.info(
        "Open positions fetched",
        count=len(positions_list),
        total_pnl=total_unrealized_pnl,
    )

    return {
        "total": len(positions_list),
        "positions": positions_list,
        "total_unrealized_pnl": total_unrealized_pnl,
    }


@router.get("/{position_id}")
async def get_position(
    position_id: str,
    db: DatabaseService = Depends(get_db_service),
):
    """Get specific position by ID from database."""
    logger.info("Fetching position", position_id=position_id)

    position = await db.get_position(position_id)

    if not position:
        logger.warning("Position not found", position_id=position_id)
        raise HTTPException(status_code=404, detail="Position not found")

    return {
        "id": position.position_id,
        "pair": position.pair,
        "side": position.side,
        "strategy": position.strategy,
        "entryPrice": position.entry_price,
        "currentPrice": position.current_price or position.entry_price,
        "size": position.size,
        "unrealizedPnL": position.unrealized_pnl,
        "unrealizedPnLPct": position.unrealized_pnl_percent,
        "stopLoss": position.stop_loss,
        "takeProfit": position.take_profit,
        "trailingStop": position.trailing_stop,
        "entryTime": position.entry_time.isoformat(),
        "status": position.status,
    }


@router.post("")
async def open_position(
    position: PositionCreate,
    db: DatabaseService = Depends(get_db_service),
):
    """
    Open a new position and save to database.

    Called by Trade Execution Agent when position is opened.
    """
    logger.info(
        "Opening position",
        pair=position.pair,
        side=position.side,
        size=position.size,
    )

    # Generate unique position ID
    position_id = f"POS-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    # Calculate position value
    position_value_usd = position.size * position.entry_price

    # Prepare position data
    position_data = {
        "position_id": position_id,
        "pair": position.pair,
        "side": position.side,
        "strategy": position.strategy,
        "entry_time": datetime.utcnow(),
        "entry_price": position.entry_price,
        "size": position.size,
        "position_value_usd": position_value_usd,
        "current_price": position.entry_price,
        "unrealized_pnl": 0.0,
        "unrealized_pnl_percent": 0.0,
        "stop_loss": position.stop_loss,
        "take_profit": position.take_profit,
        "trailing_stop": position.trailing_stop,
        "status": "open",
    }

    # Save to database
    saved_position = await db.create_position(position_data)

    logger.info(
        "Position opened and saved to database",
        position_id=saved_position.position_id,
    )

    return {
        "success": True,
        "position": {
            "id": saved_position.position_id,
            "pair": saved_position.pair,
            "entryPrice": saved_position.entry_price,
            "size": saved_position.size,
        },
    }


@router.patch("/{position_id}")
async def update_position(
    position_id: str,
    updates: PositionUpdate,
    db: DatabaseService = Depends(get_db_service),
):
    """
    Update position (price, P&L, etc.) in database.

    Called by Market Data Agent when prices change.
    """
    logger.debug("Updating position", position_id=position_id)

    # Get existing position
    position = await db.get_position(position_id)

    if not position:
        logger.warning("Position not found for update", position_id=position_id)
        raise HTTPException(status_code=404, detail="Position not found")

    # Prepare updates dictionary
    update_data = {}

    # Update current price and recalculate P&L
    if updates.current_price is not None:
        update_data["current_price"] = updates.current_price

        # Recalculate P&L
        entry = position.entry_price
        current = updates.current_price
        side = position.side
        size = position.size

        if side == "buy":
            pnl = (current - entry) * size
            pnl_pct = ((current - entry) / entry) * 100
        else:
            pnl = (entry - current) * size
            pnl_pct = ((entry - current) / entry) * 100

        update_data["unrealized_pnl"] = pnl
        update_data["unrealized_pnl_percent"] = pnl_pct

    # Update risk parameters
    if updates.stop_loss is not None:
        update_data["stop_loss"] = updates.stop_loss

    if updates.take_profit is not None:
        update_data["take_profit"] = updates.take_profit

    if updates.trailing_stop is not None:
        update_data["trailing_stop"] = updates.trailing_stop

    if updates.trailing_stop_activation is not None:
        update_data["trailing_stop_activation"] = updates.trailing_stop_activation

    # Update in database
    updated_position = await db.update_position(position_id, update_data)

    if not updated_position:
        raise HTTPException(status_code=500, detail="Failed to update position")

    logger.debug(
        "Position updated in database",
        position_id=position_id,
        unrealized_pnl=updated_position.unrealized_pnl,
    )

    return {
        "success": True,
        "position": {
            "id": updated_position.position_id,
            "currentPrice": updated_position.current_price,
            "unrealizedPnL": updated_position.unrealized_pnl,
            "unrealizedPnLPct": updated_position.unrealized_pnl_percent,
        },
    }


@router.delete("/{position_id}")
async def close_position(
    position_id: str,
    closed_by: str = "manual",
    db: DatabaseService = Depends(get_db_service),
):
    """
    Close a position in database.

    Called by Trade Execution Agent when position is closed.
    """
    logger.info("Closing position", position_id=position_id, closed_by=closed_by)

    # Get position
    position = await db.get_position(position_id)

    if not position:
        logger.warning("Position not found for closing", position_id=position_id)
        raise HTTPException(status_code=404, detail="Position not found")

    # Calculate realized P&L
    realized_pnl = position.unrealized_pnl

    # Close position in database
    closed_position = await db.close_position(
        position_id=position_id,
        closed_by=closed_by,
        realized_pnl=realized_pnl,
    )

    if not closed_position:
        raise HTTPException(status_code=500, detail="Failed to close position")

    logger.info(
        "Position closed in database",
        position_id=position_id,
        realized_pnl=realized_pnl,
    )

    return {
        "success": True,
        "closed_position": {
            "id": closed_position.position_id,
            "pair": closed_position.pair,
            "realized_pnl": closed_position.realized_pnl,
            "closed_at": closed_position.closed_at.isoformat() if closed_position.closed_at else None,
        },
    }


@router.get("/summary/stats")
async def get_position_stats(
    db: DatabaseService = Depends(get_db_service),
):
    """Get summary statistics for all open positions from database."""
    logger.info("Fetching position summary stats")

    # Get all open positions
    positions = await db.get_open_positions()

    if not positions:
        return {
            "total_positions": 0,
            "total_value": 0,
            "total_unrealized_pnl": 0,
            "avg_pnl_pct": 0,
            "by_pair": {},
            "by_strategy": {},
        }

    # Calculate aggregates
    total_value = sum(pos.position_value_usd for pos in positions)
    total_pnl = sum(pos.unrealized_pnl for pos in positions)
    avg_pnl_pct = sum(pos.unrealized_pnl_percent for pos in positions) / len(positions)

    # Group by pair
    by_pair: Dict[str, Dict[str, Any]] = {}
    for pos in positions:
        pair = pos.pair
        if pair not in by_pair:
            by_pair[pair] = {"count": 0, "total_pnl": 0.0, "total_value": 0.0}
        by_pair[pair]["count"] += 1
        by_pair[pair]["total_pnl"] += pos.unrealized_pnl
        by_pair[pair]["total_value"] += pos.position_value_usd

    # Group by strategy
    by_strategy: Dict[str, Dict[str, Any]] = {}
    for pos in positions:
        strategy = pos.strategy
        if strategy not in by_strategy:
            by_strategy[strategy] = {"count": 0, "total_pnl": 0.0, "total_value": 0.0}
        by_strategy[strategy]["count"] += 1
        by_strategy[strategy]["total_pnl"] += pos.unrealized_pnl
        by_strategy[strategy]["total_value"] += pos.position_value_usd

    logger.info(
        "Position summary stats calculated",
        total_positions=len(positions),
        total_pnl=total_pnl,
    )

    return {
        "total_positions": len(positions),
        "total_value": total_value,
        "total_unrealized_pnl": total_pnl,
        "avg_pnl_pct": avg_pnl_pct,
        "by_pair": by_pair,
        "by_strategy": by_strategy,
    }
