"""
Positions API - Trading Positions Management

Agent: API Development Agent
Squad: Alpha
Sprint: 5.1

Provides endpoints for managing and viewing trading positions.

Agent: #20 API Development Agent
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/positions", tags=["positions"])


# Mock data store (in production, this would be database)
_open_positions: Dict[str, Dict[str, Any]] = {}


@router.get("")
async def get_positions():
    """
    Get all open positions.

    Returns list of currently open trading positions with
    real-time P&L calculations.
    """
    positions_list = list(_open_positions.values())

    return {
        "total": len(positions_list),
        "positions": positions_list,
        "total_unrealized_pnl": sum(p.get("unrealizedPnL", 0) for p in positions_list),
    }


@router.get("/{position_id}")
async def get_position(position_id: str):
    """Get specific position by ID."""
    if position_id not in _open_positions:
        raise HTTPException(status_code=404, detail="Position not found")

    return _open_positions[position_id]


@router.post("")
async def open_position(position: Dict[str, Any]):
    """
    Open a new position.

    Called by Trade Execution Agent when position is opened.
    """
    position_id = position.get("id") or f"POS-{len(_open_positions):06d}"

    position_data = {
        "id": position_id,
        "pair": position["pair"],
        "side": position["side"],
        "entryPrice": position["entryPrice"],
        "currentPrice": position["entryPrice"],
        "size": position["size"],
        "unrealizedPnL": 0.0,
        "unrealizedPnLPct": 0.0,
        "stopLoss": position.get("stopLoss", 0),
        "takeProfit": position.get("takeProfit", 0),
        "strategy": position.get("strategy", "unknown"),
        "entryTime": datetime.utcnow().isoformat(),
    }

    _open_positions[position_id] = position_data

    return {"success": True, "position": position_data}


@router.patch("/{position_id}")
async def update_position(position_id: str, updates: Dict[str, Any]):
    """
    Update position (price, P&L, etc.).

    Called by Market Data Agent when prices change.
    """
    if position_id not in _open_positions:
        raise HTTPException(status_code=404, detail="Position not found")

    position = _open_positions[position_id]

    # Update current price
    if "currentPrice" in updates:
        position["currentPrice"] = updates["currentPrice"]

        # Recalculate P&L
        entry = position["entryPrice"]
        current = position["currentPrice"]
        side = position["side"]

        if side == "buy":
            pnl = (current - entry) * position["size"]
            pnl_pct = ((current - entry) / entry) * 100
        else:
            pnl = (entry - current) * position["size"]
            pnl_pct = ((entry - current) / entry) * 100

        position["unrealizedPnL"] = pnl
        position["unrealizedPnLPct"] = pnl_pct

    # Update other fields
    for key, value in updates.items():
        if key != "currentPrice":
            position[key] = value

    return {"success": True, "position": position}


@router.delete("/{position_id}")
async def close_position(position_id: str):
    """
    Close a position.

    Called by Trade Execution Agent when position is closed.
    """
    if position_id not in _open_positions:
        raise HTTPException(status_code=404, detail="Position not found")

    position = _open_positions.pop(position_id)

    return {
        "success": True,
        "closed_position": position,
    }


@router.get("/summary/stats")
async def get_position_stats():
    """Get summary statistics for all open positions."""
    positions = list(_open_positions.values())

    if not positions:
        return {
            "total_positions": 0,
            "total_value": 0,
            "total_unrealized_pnl": 0,
            "avg_pnl_pct": 0,
            "by_pair": {},
            "by_strategy": {},
        }

    total_value = sum(p["size"] * p["currentPrice"] for p in positions)
    total_pnl = sum(p["unrealizedPnL"] for p in positions)
    avg_pnl_pct = sum(p["unrealizedPnLPct"] for p in positions) / len(positions)

    # Group by pair
    by_pair: Dict[str, Dict[str, Any]] = {}
    for pos in positions:
        pair = pos["pair"]
        if pair not in by_pair:
            by_pair[pair] = {"count": 0, "total_pnl": 0}
        by_pair[pair]["count"] += 1
        by_pair[pair]["total_pnl"] += pos["unrealizedPnL"]

    # Group by strategy
    by_strategy: Dict[str, Dict[str, Any]] = {}
    for pos in positions:
        strategy = pos["strategy"]
        if strategy not in by_strategy:
            by_strategy[strategy] = {"count": 0, "total_pnl": 0}
        by_strategy[strategy]["count"] += 1
        by_strategy[strategy]["total_pnl"] += pos["unrealizedPnL"]

    return {
        "total_positions": len(positions),
        "total_value": total_value,
        "total_unrealized_pnl": total_pnl,
        "avg_pnl_pct": avg_pnl_pct,
        "by_pair": by_pair,
        "by_strategy": by_strategy,
    }
