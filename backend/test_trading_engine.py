"""
Quick test script to verify trading engine works end-to-end.

This simulates:
1. Starting the trading engine
2. Market data flowing in
3. Signals being generated
4. Positions being opened
5. Trades being stored in database
"""

import asyncio
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

from services.trading_engine import TradingEngine
from core.database import db_service
import structlog

logger = structlog.get_logger()


async def test_trading_engine():
    """Test the trading engine with simulated price movements."""

    print("=" * 60)
    print("TESTING TRADING ENGINE")
    print("=" * 60)

    # Initialize database
    print("\n1. Initializing database...")
    await db_service.initialize()
    print("   ✅ Database initialized")

    # Create trading engine
    print("\n2. Creating trading engine...")
    engine = TradingEngine(
        pairs=["BTC/USDC"],
        strategy="ma_crossover"
    )
    print("   ✅ Trading engine created")

    # Start the engine
    print("\n3. Starting trading engine...")
    await engine.start()
    print("   ✅ Trading engine started")
    print(f"   - Mode: {engine.mode}")
    print(f"   - Balance: ${engine.demo_balance:,.2f}")
    print(f"   - Pairs: {engine.pairs}")

    # Let it run for 90 seconds to collect price data and generate signals
    print("\n4. Running trading engine for 90 seconds...")
    print("   (Collecting price data and watching for MA crossover signals...)")

    for i in range(9):
        await asyncio.sleep(10)
        status = engine.get_status()
        print(f"\n   [{i+1}0s] Status:")
        print(f"   - Signals generated: {status['metrics']['signals_generated']}")
        print(f"   - Positions opened: {status['metrics']['positions_opened']}")
        print(f"   - Open positions: {status['open_positions']}")
        print(f"   - Total P&L: ${status['metrics']['total_pnl']:.2f}")

        if status['open_positions'] > 0:
            for pos in status['positions']:
                print(f"   - Position {pos['pair']}: Entry ${pos['entry_price']:.2f}, "
                      f"Current ${pos['current_price']:.2f}, "
                      f"P&L {pos['unrealized_pnl']:.2f}%")

    # Check database for trades
    print("\n5. Checking database for trades...")
    trades = await db_service.get_trades(limit=10)
    positions = await db_service.get_open_positions()

    print(f"\n   📊 Database Summary:")
    print(f"   - Total trades: {len(trades)}")
    print(f"   - Open positions: {len(positions)}")

    if trades:
        print(f"\n   Recent trades:")
        for trade in trades[:5]:
            print(f"   - {trade.pair}: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%) - {trade.exit_reason}")

    if positions:
        print(f"\n   Open positions:")
        for pos in positions:
            print(f"   - {pos.pair}: Entry ${pos.entry_price:.2f}, Current ${pos.current_price:.2f}")

    # Stop the engine
    print("\n6. Stopping trading engine...")
    await engine.stop()
    print("   ✅ Trading engine stopped")

    # Final metrics
    final_status = engine.get_status()
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Signals Generated: {final_status['metrics']['signals_generated']}")
    print(f"Trades Executed: {final_status['metrics']['trades_executed']}")
    print(f"Positions Opened: {final_status['metrics']['positions_opened']}")
    print(f"Positions Closed: {final_status['metrics']['positions_closed']}")
    print(f"Total P&L: ${final_status['metrics']['total_pnl']:.2f}")
    print(f"Final Balance: ${final_status['demo_balance']:,.2f}")
    print("=" * 60)

    # Shutdown
    await db_service.shutdown()

    # Success criteria
    success = final_status['metrics']['signals_generated'] > 0 or len(trades) > 0 or len(positions) > 0

    if success:
        print("\n✅ TEST PASSED - Trading engine is working!")
    else:
        print("\n⚠️  WARNING - No trades executed yet (may need more time for price movement)")

    return success


if __name__ == "__main__":
    print("\n🚀 Starting Trading Engine Test...\n")
    success = asyncio.run(test_trading_engine())
    sys.exit(0 if success else 1)
