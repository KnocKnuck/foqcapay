"""
Backtesting API - Strategy Performance Testing Endpoints

Agent: API Development Agent
Squad: Alpha
Sprint: 5.2

Provides endpoints for running backtests and viewing results.

Agent: #20 API Development Agent
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import structlog

from backend.services.backtesting import (
    BacktestEngine,
    BacktestConfig,
    BacktestResults,
    BacktestStatus,
)
from backend.core.database import DatabaseService, get_db_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


# Pydantic models
class BacktestRequest(BaseModel):
    """Request to run a backtest."""

    strategy_name: str
    pair: str
    timeframe: str = "1h"
    start_date: str  # ISO format
    end_date: str  # ISO format
    initial_capital: float = 10000.0
    position_size_pct: float = 10.0
    max_positions: int = 3
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 5.0
    trailing_stop_pct: Optional[float] = None
    commission_pct: float = 0.1
    slippage_pct: float = 0.05
    use_trailing_stop: bool = False


class BacktestSummary(BaseModel):
    """Summary of backtest results."""

    backtest_id: str
    strategy_name: str
    pair: str
    start_date: str
    end_date: str
    status: str
    total_return_pct: float
    win_rate: float
    total_trades: int
    sharpe_ratio: float
    max_drawdown_pct: float


# In-memory storage for backtest results (TODO: move to database)
_backtest_results: Dict[str, BacktestResults] = {}


@router.post("/run")
async def run_backtest(
    request: BacktestRequest,
    db: DatabaseService = Depends(get_db_service),
):
    """
    Run a backtest on historical data.

    Simulates strategy execution and returns comprehensive results.
    """
    logger.info(
        "Starting backtest",
        strategy=request.strategy_name,
        pair=request.pair,
        start=request.start_date,
        end=request.end_date,
    )

    # Parse dates
    start_date = datetime.fromisoformat(request.start_date)
    end_date = datetime.fromisoformat(request.end_date)

    # Create config
    config = BacktestConfig(
        strategy_name=request.strategy_name,
        pair=request.pair,
        timeframe=request.timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_capital=request.initial_capital,
        position_size_pct=request.position_size_pct,
        max_positions=request.max_positions,
        stop_loss_pct=request.stop_loss_pct,
        take_profit_pct=request.take_profit_pct,
        trailing_stop_pct=request.trailing_stop_pct,
        commission_pct=request.commission_pct,
        slippage_pct=request.slippage_pct,
        use_trailing_stop=request.use_trailing_stop,
    )

    # Get historical data from database
    # For now, generate synthetic data (TODO: use real historical data)
    historical_data = await _generate_historical_data(
        request.pair, start_date, end_date, request.timeframe
    )

    if not historical_data:
        raise HTTPException(
            status_code=400,
            detail=f"No historical data available for {request.pair} from {start_date} to {end_date}",
        )

    logger.info("Historical data loaded", bars=len(historical_data))

    # Run backtest
    engine = BacktestEngine(config)
    results = engine.run(historical_data)

    # Store results
    _backtest_results[results.backtest_id] = results

    logger.info(
        "Backtest completed",
        backtest_id=results.backtest_id,
        return_pct=results.total_return_pct,
        trades=results.total_trades,
    )

    # Return summary
    return {
        "success": True,
        "backtest_id": results.backtest_id,
        "summary": {
            "strategy": results.strategy_name,
            "pair": results.pair,
            "total_return_pct": round(results.total_return_pct, 2),
            "total_trades": results.total_trades,
            "win_rate": round(results.win_rate * 100, 2),
            "profit_factor": round(results.profit_factor, 2),
            "sharpe_ratio": round(results.sharpe_ratio, 2),
            "max_drawdown_pct": round(results.max_drawdown_pct, 2),
            "execution_time": round(results.execution_time_seconds, 2),
        },
    }


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: str):
    """Get detailed results for a specific backtest."""
    if backtest_id not in _backtest_results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    results = _backtest_results[backtest_id]

    return {
        "backtest_id": results.backtest_id,
        "strategy_name": results.strategy_name,
        "pair": results.pair,
        "start_date": results.start_date.isoformat(),
        "end_date": results.end_date.isoformat(),
        "status": results.status,
        # Capital
        "initial_capital": results.initial_capital,
        "final_capital": results.final_capital,
        "total_return": results.total_return,
        "total_return_pct": results.total_return_pct,
        # Trades
        "total_trades": results.total_trades,
        "winning_trades": results.winning_trades,
        "losing_trades": results.losing_trades,
        # Performance
        "win_rate": results.win_rate,
        "profit_factor": results.profit_factor,
        "avg_win": results.avg_win,
        "avg_loss": results.avg_loss,
        "largest_win": results.largest_win,
        "largest_loss": results.largest_loss,
        "expectancy": results.expectancy,
        # Risk
        "max_drawdown": results.max_drawdown,
        "max_drawdown_pct": results.max_drawdown_pct,
        "sharpe_ratio": results.sharpe_ratio,
        "sortino_ratio": results.sortino_ratio,
        "calmar_ratio": results.calmar_ratio,
        # Execution
        "execution_time_seconds": results.execution_time_seconds,
    }


@router.get("/results/{backtest_id}/trades")
async def get_backtest_trades(
    backtest_id: str,
    limit: int = Query(100, description="Max trades to return"),
    offset: int = Query(0, description="Offset for pagination"),
):
    """Get trade history from a backtest."""
    if backtest_id not in _backtest_results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    results = _backtest_results[backtest_id]
    trades = results.trades[offset : offset + limit]

    trade_dicts = []
    for trade in trades:
        trade_dicts.append(
            {
                "entry_time": trade.entry_time.isoformat(),
                "exit_time": trade.exit_time.isoformat(),
                "pair": trade.pair,
                "side": trade.side,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "size": trade.size,
                "pnl": trade.pnl,
                "pnl_pct": trade.pnl_pct,
                "exit_reason": trade.exit_reason,
                "duration_minutes": trade.duration_minutes,
                "commission": trade.commission,
            }
        )

    return {
        "backtest_id": backtest_id,
        "total": len(results.trades),
        "trades": trade_dicts,
        "limit": limit,
        "offset": offset,
    }


@router.get("/results/{backtest_id}/equity_curve")
async def get_equity_curve(backtest_id: str):
    """Get equity curve data for charting."""
    if backtest_id not in _backtest_results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    results = _backtest_results[backtest_id]

    equity_data = []
    for point in results.equity_curve:
        equity_data.append(
            {
                "timestamp": point["timestamp"].isoformat(),
                "equity": point["equity"],
                "drawdown": point["drawdown"],
            }
        )

    return {
        "backtest_id": backtest_id,
        "equity_curve": equity_data,
    }


@router.get("/list")
async def list_backtests():
    """List all backtests."""
    summaries = []

    for backtest_id, results in _backtest_results.items():
        summaries.append(
            {
                "backtest_id": backtest_id,
                "strategy_name": results.strategy_name,
                "pair": results.pair,
                "start_date": results.start_date.isoformat(),
                "end_date": results.end_date.isoformat(),
                "status": results.status,
                "total_return_pct": results.total_return_pct,
                "win_rate": results.win_rate,
                "total_trades": results.total_trades,
                "sharpe_ratio": results.sharpe_ratio,
                "max_drawdown_pct": results.max_drawdown_pct,
            }
        )

    # Sort by most recent
    summaries = sorted(summaries, key=lambda x: x["backtest_id"], reverse=True)

    return {"backtests": summaries, "total": len(summaries)}


@router.delete("/results/{backtest_id}")
async def delete_backtest(backtest_id: str):
    """Delete a backtest."""
    if backtest_id not in _backtest_results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    del _backtest_results[backtest_id]

    logger.info("Backtest deleted", backtest_id=backtest_id)

    return {"success": True, "message": "Backtest deleted"}


@router.post("/compare")
async def compare_backtests(backtest_ids: List[str]):
    """Compare multiple backtests side-by-side."""
    if len(backtest_ids) < 2:
        raise HTTPException(
            status_code=400, detail="At least 2 backtests required for comparison"
        )

    comparison = []

    for backtest_id in backtest_ids:
        if backtest_id not in _backtest_results:
            raise HTTPException(
                status_code=404, detail=f"Backtest {backtest_id} not found"
            )

        results = _backtest_results[backtest_id]
        comparison.append(
            {
                "backtest_id": backtest_id,
                "strategy_name": results.strategy_name,
                "pair": results.pair,
                "total_return_pct": results.total_return_pct,
                "win_rate": results.win_rate,
                "total_trades": results.total_trades,
                "profit_factor": results.profit_factor,
                "sharpe_ratio": results.sharpe_ratio,
                "max_drawdown_pct": results.max_drawdown_pct,
                "expectancy": results.expectancy,
            }
        )

    return {"comparison": comparison}


# Helper function to generate synthetic historical data
async def _generate_historical_data(
    pair: str, start_date: datetime, end_date: datetime, timeframe: str
) -> List[Dict[str, Any]]:
    """
    Generate synthetic historical data for backtesting.

    TODO: Replace with actual historical data from database or API.
    """
    import numpy as np

    # Determine number of bars based on timeframe
    if timeframe == "1m":
        minutes = 1
    elif timeframe == "5m":
        minutes = 5
    elif timeframe == "15m":
        minutes = 15
    elif timeframe == "1h":
        minutes = 60
    elif timeframe == "4h":
        minutes = 240
    elif timeframe == "1d":
        minutes = 1440
    else:
        minutes = 60  # Default to 1h

    # Generate timestamps
    total_minutes = int((end_date - start_date).total_seconds() / 60)
    num_bars = total_minutes // minutes

    if num_bars > 10000:
        num_bars = 10000  # Limit to 10k bars

    logger.info(f"Generating {num_bars} synthetic bars for {pair}")

    # Generate price data (random walk with trend)
    np.random.seed(42)  # For reproducibility

    # Starting price
    base_price = 30000.0 if "BTC" in pair else 2000.0 if "ETH" in pair else 100.0

    # Generate returns (with slight upward trend)
    returns = np.random.normal(0.0001, 0.02, num_bars)
    prices = base_price * np.exp(np.cumsum(returns))

    # Generate OHLCV data
    bars = []
    current_time = start_date

    for i, close in enumerate(prices):
        # Add some volatility for high/low
        volatility = close * 0.01
        high = close + abs(np.random.normal(0, volatility))
        low = close - abs(np.random.normal(0, volatility))
        open_price = (
            prices[i - 1] if i > 0 else close
        )  # Previous close is this open

        # Ensure OHLC consistency
        high = max(high, open_price, close)
        low = min(low, open_price, close)

        bars.append(
            {
                "timestamp": current_time,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": np.random.uniform(100, 1000),
            }
        )

        current_time += timedelta(minutes=minutes)

    return bars
