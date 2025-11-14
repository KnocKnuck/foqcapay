"""
Trades API - Trade History & Analytics

Agent: API Development Agent
Squad: Alpha
Sprint: 5.1

Provides endpoints for trade history and performance analytics.

Agent: #20 API Development Agent
"""

from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/trades", tags=["trades"])


# Mock data store (in production, this would be database)
_trade_history: List[Dict[str, Any]] = []


@router.get("/history")
async def get_trade_history(
    pair: Optional[str] = Query(None, description="Filter by trading pair"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    limit: int = Query(100, description="Max number of trades to return"),
    offset: int = Query(0, description="Offset for pagination"),
):
    """
    Get trade history with optional filters.

    Returns list of completed trades with P&L.
    """
    trades = _trade_history

    # Apply filters
    if pair:
        trades = [t for t in trades if t["pair"] == pair]

    if strategy:
        trades = [t for t in trades if t["strategy"] == strategy]

    # Sort by exit time (most recent first)
    trades = sorted(trades, key=lambda t: t["exitTime"], reverse=True)

    # Pagination
    paginated = trades[offset : offset + limit]

    return {
        "total": len(trades),
        "trades": paginated,
        "limit": limit,
        "offset": offset,
    }


@router.post("")
async def record_trade(trade: Dict[str, Any]):
    """
    Record a completed trade.

    Called by Trade Execution Agent when position closes.
    """
    trade_id = f"TRADE-{len(_trade_history):06d}"

    trade_data = {
        "id": trade_id,
        "pair": trade["pair"],
        "side": trade["side"],
        "entryPrice": trade["entryPrice"],
        "exitPrice": trade["exitPrice"],
        "size": trade["size"],
        "pnl": trade["pnl"],
        "pnlPct": trade["pnlPct"],
        "strategy": trade.get("strategy", "unknown"),
        "entryTime": trade.get("entryTime", datetime.utcnow().isoformat()),
        "exitTime": trade.get("exitTime", datetime.utcnow().isoformat()),
        "reason": trade.get("reason", "unknown"),
        "fees": trade.get("fees", 0),
    }

    _trade_history.append(trade_data)

    return {"success": True, "trade": trade_data}


@router.get("/stats/daily")
async def get_daily_stats(days: int = Query(7, description="Number of days")):
    """Get daily trading statistics."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Filter trades within timeframe
    recent_trades = [
        t
        for t in _trade_history
        if datetime.fromisoformat(t["exitTime"]) >= cutoff
    ]

    # Group by day
    daily_stats: Dict[str, Dict[str, Any]] = {}

    for trade in recent_trades:
        day = trade["exitTime"][:10]  # YYYY-MM-DD

        if day not in daily_stats:
            daily_stats[day] = {
                "date": day,
                "trades": 0,
                "winning": 0,
                "losing": 0,
                "total_pnl": 0,
                "volume": 0,
            }

        daily_stats[day]["trades"] += 1
        daily_stats[day]["total_pnl"] += trade["pnl"]
        daily_stats[day]["volume"] += trade["size"] * trade["exitPrice"]

        if trade["pnl"] > 0:
            daily_stats[day]["winning"] += 1
        else:
            daily_stats[day]["losing"] += 1

    # Convert to list and sort
    stats_list = sorted(daily_stats.values(), key=lambda x: x["date"])

    return {
        "days": days,
        "daily_stats": stats_list,
    }


@router.get("/stats/by_pair")
async def get_stats_by_pair():
    """Get performance statistics grouped by trading pair."""
    by_pair: Dict[str, Dict[str, Any]] = {}

    for trade in _trade_history:
        pair = trade["pair"]

        if pair not in by_pair:
            by_pair[pair] = {
                "pair": pair,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
                "win_rate": 0,
            }

        by_pair[pair]["total_trades"] += 1
        by_pair[pair]["total_pnl"] += trade["pnl"]

        if trade["pnl"] > 0:
            by_pair[pair]["winning_trades"] += 1
        else:
            by_pair[pair]["losing_trades"] += 1

    # Calculate averages
    for pair_stats in by_pair.values():
        if pair_stats["total_trades"] > 0:
            pair_stats["avg_pnl"] = pair_stats["total_pnl"] / pair_stats["total_trades"]
            pair_stats["win_rate"] = (
                pair_stats["winning_trades"] / pair_stats["total_trades"]
            )

    return {"pairs": list(by_pair.values())}


@router.get("/stats/by_strategy")
async def get_stats_by_strategy():
    """Get performance statistics grouped by strategy."""
    by_strategy: Dict[str, Dict[str, Any]] = {}

    for trade in _trade_history:
        strategy = trade["strategy"]

        if strategy not in by_strategy:
            by_strategy[strategy] = {
                "strategy": strategy,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
                "win_rate": 0,
                "largest_win": 0,
                "largest_loss": 0,
            }

        by_strategy[strategy]["total_trades"] += 1
        by_strategy[strategy]["total_pnl"] += trade["pnl"]

        if trade["pnl"] > 0:
            by_strategy[strategy]["winning_trades"] += 1
            by_strategy[strategy]["largest_win"] = max(
                by_strategy[strategy]["largest_win"], trade["pnl"]
            )
        else:
            by_strategy[strategy]["losing_trades"] += 1
            by_strategy[strategy]["largest_loss"] = min(
                by_strategy[strategy]["largest_loss"], trade["pnl"]
            )

    # Calculate averages
    for strategy_stats in by_strategy.values():
        if strategy_stats["total_trades"] > 0:
            strategy_stats["avg_pnl"] = (
                strategy_stats["total_pnl"] / strategy_stats["total_trades"]
            )
            strategy_stats["win_rate"] = (
                strategy_stats["winning_trades"] / strategy_stats["total_trades"]
            )

    return {"strategies": list(by_strategy.values())}
