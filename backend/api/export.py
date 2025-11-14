"""
Export API - Trade Data Export Functionality

Agent: API Development Agent
Squad: Alpha
Sprint: 5.2

Provides endpoints for exporting trading data to various formats (CSV, JSON).

Agent: #20 API Development Agent
"""

from fastapi import APIRouter, Depends, Response, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime
import csv
import json
import io
import structlog

from core.database import DatabaseService, get_db_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/trades/csv")
async def export_trades_csv(
    pair: Optional[str] = Query(None, description="Filter by trading pair"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: DatabaseService = Depends(get_db_service),
):
    """
    Export trade history to CSV format.

    Returns a downloadable CSV file with all trade data.
    """
    logger.info("Exporting trades to CSV", pair=pair, strategy=strategy)

    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    # Fetch trades from database
    trades = await db.get_trades(
        pair=pair,
        strategy=strategy,
        start_date=start_dt,
        end_date=end_dt,
        limit=10000,  # Export up to 10k trades
    )

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Trade ID",
        "Pair",
        "Strategy",
        "Side",
        "Entry Time",
        "Entry Price",
        "Exit Time",
        "Exit Price",
        "Size",
        "Position Value (USD)",
        "P&L (USD)",
        "P&L (%)",
        "Net P&L (USD)",
        "Fees (USD)",
        "Exit Reason",
        "Stop Loss",
        "Take Profit",
        "Duration (minutes)",
    ])

    # Write data
    for trade in trades:
        writer.writerow([
            trade.trade_id,
            trade.pair,
            trade.strategy,
            trade.side,
            trade.entry_time.isoformat(),
            trade.entry_price,
            trade.exit_time.isoformat(),
            trade.exit_price,
            trade.size,
            trade.position_value_usd,
            trade.pnl,
            trade.pnl_percent,
            trade.net_pnl,
            trade.fees,
            trade.exit_reason,
            trade.stop_loss or "",
            trade.take_profit or "",
            trade.duration_minutes or "",
        ])

    # Prepare response
    output.seek(0)

    # Generate filename
    filename_parts = ["trades"]
    if pair:
        filename_parts.append(pair.replace("/", "-"))
    if strategy:
        filename_parts.append(strategy)
    filename_parts.append(datetime.utcnow().strftime("%Y%m%d"))
    filename = "_".join(filename_parts) + ".csv"

    logger.info("CSV export complete", trades=len(trades), filename=filename)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


@router.get("/trades/json")
async def export_trades_json(
    pair: Optional[str] = Query(None, description="Filter by trading pair"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: DatabaseService = Depends(get_db_service),
):
    """
    Export trade history to JSON format.

    Returns a downloadable JSON file with all trade data.
    """
    logger.info("Exporting trades to JSON", pair=pair, strategy=strategy)

    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    # Fetch trades from database
    trades = await db.get_trades(
        pair=pair,
        strategy=strategy,
        start_date=start_dt,
        end_date=end_dt,
        limit=10000,
    )

    # Convert to dictionaries
    trade_dicts = []
    for trade in trades:
        trade_dicts.append({
            "trade_id": trade.trade_id,
            "pair": trade.pair,
            "strategy": trade.strategy,
            "side": trade.side,
            "entry_time": trade.entry_time.isoformat(),
            "entry_price": trade.entry_price,
            "exit_time": trade.exit_time.isoformat(),
            "exit_price": trade.exit_price,
            "size": trade.size,
            "position_value_usd": trade.position_value_usd,
            "pnl": trade.pnl,
            "pnl_percent": trade.pnl_percent,
            "net_pnl": trade.net_pnl,
            "fees": trade.fees,
            "exit_reason": trade.exit_reason,
            "stop_loss": trade.stop_loss,
            "take_profit": trade.take_profit,
            "duration_minutes": trade.duration_minutes,
        })

    # Create export data
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "filters": {
            "pair": pair,
            "strategy": strategy,
            "start_date": start_date,
            "end_date": end_date,
        },
        "total_trades": len(trade_dicts),
        "trades": trade_dicts,
    }

    # Generate filename
    filename_parts = ["trades"]
    if pair:
        filename_parts.append(pair.replace("/", "-"))
    if strategy:
        filename_parts.append(strategy)
    filename_parts.append(datetime.utcnow().strftime("%Y%m%d"))
    filename = "_".join(filename_parts) + ".json"

    logger.info("JSON export complete", trades=len(trades), filename=filename)

    # Convert to JSON string
    json_str = json.dumps(export_data, indent=2)

    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


@router.get("/performance/report")
async def export_performance_report(
    pair: Optional[str] = Query(None),
    strategy: Optional[str] = Query(None),
    days: int = Query(30, description="Number of days for analysis"),
    db: DatabaseService = Depends(get_db_service),
):
    """
    Export comprehensive performance report as JSON.

    Includes detailed statistics and metrics.
    """
    logger.info("Generating performance report", pair=pair, strategy=strategy)

    # Get performance stats from database
    stats = await db.get_performance_stats(pair=pair, strategy=strategy, days=days)

    # Fetch trades for detailed analysis
    trades = await db.get_trades(pair=pair, strategy=strategy, limit=10000)

    # Calculate additional metrics
    trade_dicts = []
    for trade in trades:
        trade_dicts.append({
            "trade_id": trade.trade_id,
            "pair": trade.pair,
            "strategy": trade.strategy,
            "entry_time": trade.entry_time.isoformat(),
            "exit_time": trade.exit_time.isoformat(),
            "pnl": trade.pnl,
            "pnl_percent": trade.pnl_percent,
        })

    # Create comprehensive report
    report = {
        "report_date": datetime.utcnow().isoformat(),
        "analysis_period_days": days,
        "filters": {
            "pair": pair,
            "strategy": strategy,
        },
        "summary": {
            "total_trades": stats["total_trades"],
            "winning_trades": stats["winning_trades"],
            "losing_trades": stats["losing_trades"],
            "win_rate": round(stats["win_rate"] * 100, 2),
            "total_pnl": round(stats["total_pnl"], 2),
            "avg_win": round(stats["avg_win"], 2),
            "avg_loss": round(stats["avg_loss"], 2),
            "largest_win": round(stats["largest_win"], 2),
            "largest_loss": round(stats["largest_loss"], 2),
            "profit_factor": round(stats["profit_factor"], 2),
            "expectancy": round(stats["expectancy"], 2),
        },
        "trades": trade_dicts,
    }

    # Generate filename
    filename = f"performance_report_{datetime.utcnow().strftime('%Y%m%d')}.json"

    logger.info("Performance report generated", trades=len(trades))

    json_str = json.dumps(report, indent=2)

    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


@router.get("/backtest/{backtest_id}/csv")
async def export_backtest_csv(backtest_id: str):
    """
    Export backtest results to CSV.

    Returns backtest trades in CSV format.
    """
    # TODO: Implement backtest export from stored results
    from api.backtest import _backtest_results
    from fastapi import HTTPException

    if backtest_id not in _backtest_results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    results = _backtest_results[backtest_id]

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Entry Time",
        "Exit Time",
        "Pair",
        "Side",
        "Entry Price",
        "Exit Price",
        "Size",
        "P&L (USD)",
        "P&L (%)",
        "Exit Reason",
        "Duration (minutes)",
        "Commission",
    ])

    # Write trades
    for trade in results.trades:
        writer.writerow([
            trade.entry_time.isoformat(),
            trade.exit_time.isoformat(),
            trade.pair,
            trade.side,
            trade.entry_price,
            trade.exit_price,
            trade.size,
            trade.pnl,
            trade.pnl_pct,
            trade.exit_reason,
            trade.duration_minutes,
            trade.commission,
        ])

    output.seek(0)
    filename = f"backtest_{backtest_id}_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    logger.info("Backtest CSV export complete", backtest_id=backtest_id)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
