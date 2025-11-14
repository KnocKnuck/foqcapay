"""
Performance API - Trading Performance Metrics

Agent: API Development Agent
Squad: Alpha
Sprint: 5.1

Provides endpoints for performance analytics and metrics.

Agent: #20 API Development Agent
"""

from fastapi import APIRouter
from typing import Dict, Any
from api.trades import _trade_history

router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("/metrics")
async def get_performance_metrics():
    """
    Get overall performance metrics.

    Returns comprehensive trading performance statistics.
    """
    if not _trade_history:
        return {
            "totalTrades": 0,
            "winningTrades": 0,
            "losingTrades": 0,
            "winRate": 0,
            "totalPnL": 0,
            "avgWin": 0,
            "avgLoss": 0,
            "largestWin": 0,
            "largestLoss": 0,
            "profitFactor": 0,
            "avgTrade": 0,
            "expectancy": 0,
        }

    # Calculate metrics
    total_trades = len(_trade_history)
    winning_trades = [t for t in _trade_history if t["pnl"] > 0]
    losing_trades = [t for t in _trade_history if t["pnl"] <= 0]

    total_wins = len(winning_trades)
    total_losses = len(losing_trades)

    total_pnl = sum(t["pnl"] for t in _trade_history)
    total_win_amount = sum(t["pnl"] for t in winning_trades) if winning_trades else 0
    total_loss_amount = (
        sum(t["pnl"] for t in losing_trades) if losing_trades else 0
    )

    avg_win = total_win_amount / total_wins if total_wins > 0 else 0
    avg_loss = total_loss_amount / total_losses if total_losses > 0 else 0

    largest_win = max((t["pnl"] for t in winning_trades), default=0)
    largest_loss = min((t["pnl"] for t in losing_trades), default=0)

    win_rate = total_wins / total_trades if total_trades > 0 else 0

    # Profit factor = total wins / abs(total losses)
    profit_factor = (
        total_win_amount / abs(total_loss_amount)
        if total_loss_amount != 0
        else (float("inf") if total_win_amount > 0 else 0)
    )

    # Expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))

    avg_trade = total_pnl / total_trades if total_trades > 0 else 0

    return {
        "totalTrades": total_trades,
        "winningTrades": total_wins,
        "losingTrades": total_losses,
        "winRate": win_rate,
        "totalPnL": total_pnl,
        "avgWin": avg_win,
        "avgLoss": avg_loss,
        "largestWin": largest_win,
        "largestLoss": largest_loss,
        "profitFactor": profit_factor if profit_factor != float("inf") else 999,
        "avgTrade": avg_trade,
        "expectancy": expectancy,
    }


@router.get("/equity_curve")
async def get_equity_curve():
    """
    Get equity curve data for charting.

    Returns cumulative P&L over time.
    """
    if not _trade_history:
        return {"points": []}

    # Sort trades by exit time
    sorted_trades = sorted(_trade_history, key=lambda t: t["exitTime"])

    # Calculate cumulative P&L
    equity_points = []
    cumulative_pnl = 0

    for trade in sorted_trades:
        cumulative_pnl += trade["pnl"]
        equity_points.append({
            "timestamp": trade["exitTime"],
            "equity": cumulative_pnl,
            "trade_id": trade["id"],
            "pnl": trade["pnl"],
        })

    return {"points": equity_points}


@router.get("/drawdown")
async def get_drawdown_analysis():
    """
    Calculate drawdown analysis.

    Returns peak drawdown and recovery information.
    """
    if not _trade_history:
        return {
            "current_drawdown": 0,
            "max_drawdown": 0,
            "max_drawdown_duration": 0,
            "in_drawdown": False,
        }

    # Sort trades by exit time
    sorted_trades = sorted(_trade_history, key=lambda t: t["exitTime"])

    # Calculate equity curve
    cumulative_pnl = 0
    peak_equity = 0
    max_drawdown = 0
    current_drawdown = 0

    for trade in sorted_trades:
        cumulative_pnl += trade["pnl"]

        # Update peak
        if cumulative_pnl > peak_equity:
            peak_equity = cumulative_pnl

        # Calculate current drawdown
        if peak_equity > 0:
            current_drawdown = ((peak_equity - cumulative_pnl) / peak_equity) * 100
        else:
            current_drawdown = 0

        # Update max drawdown
        max_drawdown = max(max_drawdown, current_drawdown)

    in_drawdown = current_drawdown > 0

    return {
        "current_drawdown": current_drawdown,
        "max_drawdown": max_drawdown,
        "max_drawdown_duration": 0,  # Would need time-based calculation
        "in_drawdown": in_drawdown,
        "peak_equity": peak_equity,
        "current_equity": cumulative_pnl,
    }
