"""
Trades API - Trade History & Analytics with Database Persistence

Agent: API Development Agent
Squad: Alpha
Sprint: 4.3 (Updated from 5.1)

Provides endpoints for trade history and performance analytics.
NOW WITH DATABASE PERSISTENCE - all trades stored in SQLite.

Agent: #20 API Development Agent
"""

from fastapi import APIRouter, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import structlog

from backend.core.database import DatabaseService, get_db_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/trades", tags=["trades"])


# Pydantic models for request validation
class TradeCreate(BaseModel):
    """Model for creating a new trade."""

    pair: str
    side: str  # buy or sell
    strategy: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_percent: float
    entry_time: str  # ISO format
    exit_time: str  # ISO format
    exit_reason: str = "unknown"
    fees: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None


@router.get("/history")
async def get_trade_history(
    pair: Optional[str] = Query(None, description="Filter by trading pair"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    limit: int = Query(100, description="Max number of trades to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: DatabaseService = Depends(get_db_service),
):
    """
    Get trade history with optional filters.

    Returns list of completed trades with P&L from database.
    """
    logger.info("Fetching trade history", pair=pair, strategy=strategy, limit=limit)

    # Fetch trades from database
    trades = await db.get_trades(
        pair=pair,
        strategy=strategy,
        limit=limit,
        offset=offset,
    )

    # Get total count for pagination
    total = await db.get_trade_count(pair=pair, strategy=strategy)

    # Convert SQLAlchemy models to dicts
    trade_dicts = []
    for trade in trades:
        trade_dicts.append(
            {
                "id": trade.trade_id,
                "pair": trade.pair,
                "side": trade.side,
                "strategy": trade.strategy,
                "entryPrice": trade.entry_price,
                "exitPrice": trade.exit_price,
                "size": trade.size,
                "pnl": trade.pnl,
                "pnlPct": trade.pnl_percent,
                "netPnl": trade.net_pnl,
                "fees": trade.fees,
                "entryTime": trade.entry_time.isoformat(),
                "exitTime": trade.exit_time.isoformat(),
                "reason": trade.exit_reason,
                "stopLoss": trade.stop_loss,
                "takeProfit": trade.take_profit,
                "durationMinutes": trade.duration_minutes,
            }
        )

    logger.info("Trade history fetched", count=len(trade_dicts), total=total)

    return {
        "total": total,
        "trades": trade_dicts,
        "limit": limit,
        "offset": offset,
    }


@router.post("")
async def record_trade(
    trade: TradeCreate,
    db: DatabaseService = Depends(get_db_service),
):
    """
    Record a completed trade to database.

    Called by Trade Execution Agent when position closes.
    """
    logger.info(
        "Recording trade",
        pair=trade.pair,
        pnl=trade.pnl,
        strategy=trade.strategy,
    )

    # Generate unique trade ID
    trade_count = await db.get_trade_count()
    trade_id = f"TRADE-{trade_count + 1:06d}"

    # Parse datetime strings
    entry_time = datetime.fromisoformat(trade.entry_time)
    exit_time = datetime.fromisoformat(trade.exit_time)

    # Calculate duration
    duration_minutes = int((exit_time - entry_time).total_seconds() / 60)

    # Calculate net P&L
    net_pnl = trade.pnl - trade.fees

    # Prepare trade data for database
    trade_data = {
        "trade_id": trade_id,
        "pair": trade.pair,
        "side": trade.side,
        "strategy": trade.strategy,
        "entry_time": entry_time,
        "entry_price": trade.entry_price,
        "exit_time": exit_time,
        "exit_price": trade.exit_price,
        "exit_reason": trade.exit_reason,
        "size": trade.size,
        "position_value_usd": trade.size * trade.entry_price,
        "pnl": trade.pnl,
        "pnl_percent": trade.pnl_percent,
        "fees": trade.fees,
        "net_pnl": net_pnl,
        "stop_loss": trade.stop_loss,
        "take_profit": trade.take_profit,
        "duration_minutes": duration_minutes,
        "notes": trade.notes,
    }

    # Save to database
    saved_trade = await db.create_trade(trade_data)

    logger.info(
        "Trade recorded to database",
        trade_id=saved_trade.trade_id,
        pnl=saved_trade.pnl,
    )

    # Return formatted response
    return {
        "success": True,
        "trade": {
            "id": saved_trade.trade_id,
            "pair": saved_trade.pair,
            "pnl": saved_trade.pnl,
            "exitTime": saved_trade.exit_time.isoformat(),
        },
    }


@router.get("/stats/daily")
async def get_daily_stats(
    days: int = Query(7, description="Number of days"),
    db: DatabaseService = Depends(get_db_service),
):
    """Get daily trading statistics from database."""
    logger.info("Fetching daily stats", days=days)

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Fetch trades from database
    trades = await db.get_trades(start_date=start_date, end_date=end_date, limit=10000)

    # Group by day
    daily_stats: Dict[str, Dict[str, Any]] = {}

    for trade in trades:
        day = trade.exit_time.strftime("%Y-%m-%d")

        if day not in daily_stats:
            daily_stats[day] = {
                "date": day,
                "trades": 0,
                "winning": 0,
                "losing": 0,
                "total_pnl": 0.0,
                "volume": 0.0,
            }

        daily_stats[day]["trades"] += 1
        daily_stats[day]["total_pnl"] += trade.pnl
        daily_stats[day]["volume"] += trade.position_value_usd

        if trade.pnl > 0:
            daily_stats[day]["winning"] += 1
        else:
            daily_stats[day]["losing"] += 1

    # Convert to list and sort
    stats_list = sorted(daily_stats.values(), key=lambda x: x["date"])

    logger.info("Daily stats calculated", days_with_data=len(stats_list))

    return {
        "days": days,
        "daily_stats": stats_list,
    }


@router.get("/stats/by_pair")
async def get_stats_by_pair(
    db: DatabaseService = Depends(get_db_service),
):
    """Get performance statistics grouped by trading pair."""
    logger.info("Fetching stats by pair")

    # Fetch all trades from database
    trades = await db.get_trades(limit=10000)

    # Group by pair
    by_pair: Dict[str, Dict[str, Any]] = {}

    for trade in trades:
        pair = trade.pair

        if pair not in by_pair:
            by_pair[pair] = {
                "pair": pair,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "win_rate": 0.0,
            }

        by_pair[pair]["total_trades"] += 1
        by_pair[pair]["total_pnl"] += trade.pnl

        if trade.pnl > 0:
            by_pair[pair]["winning_trades"] += 1
        else:
            by_pair[pair]["losing_trades"] += 1

    # Calculate averages and win rates
    for pair_stats in by_pair.values():
        if pair_stats["total_trades"] > 0:
            pair_stats["avg_pnl"] = (
                pair_stats["total_pnl"] / pair_stats["total_trades"]
            )
            pair_stats["win_rate"] = (
                pair_stats["winning_trades"] / pair_stats["total_trades"]
            )

    logger.info("Stats by pair calculated", pairs=len(by_pair))

    return {"pairs": list(by_pair.values())}


@router.get("/stats/by_strategy")
async def get_stats_by_strategy(
    db: DatabaseService = Depends(get_db_service),
):
    """Get performance statistics grouped by strategy."""
    logger.info("Fetching stats by strategy")

    # Fetch all trades from database
    trades = await db.get_trades(limit=10000)

    # Group by strategy
    by_strategy: Dict[str, Dict[str, Any]] = {}

    for trade in trades:
        strategy = trade.strategy

        if strategy not in by_strategy:
            by_strategy[strategy] = {
                "strategy": strategy,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "win_rate": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
            }

        by_strategy[strategy]["total_trades"] += 1
        by_strategy[strategy]["total_pnl"] += trade.pnl

        if trade.pnl > 0:
            by_strategy[strategy]["winning_trades"] += 1
            by_strategy[strategy]["largest_win"] = max(
                by_strategy[strategy]["largest_win"], trade.pnl
            )
        else:
            by_strategy[strategy]["losing_trades"] += 1
            by_strategy[strategy]["largest_loss"] = min(
                by_strategy[strategy]["largest_loss"], trade.pnl
            )

    # Calculate averages and win rates
    for strategy_stats in by_strategy.values():
        if strategy_stats["total_trades"] > 0:
            strategy_stats["avg_pnl"] = (
                strategy_stats["total_pnl"] / strategy_stats["total_trades"]
            )
            strategy_stats["win_rate"] = (
                strategy_stats["winning_trades"] / strategy_stats["total_trades"]
            )

    logger.info("Stats by strategy calculated", strategies=len(by_strategy))

    return {"strategies": list(by_strategy.values())}
