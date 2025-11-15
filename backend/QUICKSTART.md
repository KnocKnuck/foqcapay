# Quick Start Guide - Trading Bot

## What This Does

When you click "Start Trading", the bot will:
1. Connect to CoinEx exchange
2. Stream real-time price data for BTC/USDC
3. Calculate moving averages every second
4. Generate BUY/SELL signals automatically
5. Open positions when BUY signals occur
6. Close positions at stop-loss (-2%) or take-profit (+4%)
7. Store all trades in the database
8. Display everything in your dashboard

**First trade typically within 60 seconds!**

## How to Run

### 1. Start Backend
```bash
cd backend
source venv/bin/activate
python main.py
```

Expected output:
```
INFO: Started server process
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 2. Start Trading

**Option A: Via Dashboard**
1. Visit http://localhost:3000
2. Click "Start Trading"
3. Select "MA Crossover" strategy
4. Watch trades execute!

**Option B: Via API**
```bash
curl -X POST http://localhost:8000/api/trading/start \
  -H "Content-Type: application/json" \
  -d '{"strategy": "ma_crossover", "pairs": ["BTC/USDC"]}'
```

Expected response:
```json
{
  "status": "success",
  "message": "Trading started with ma_crossover strategy"
}
```

### 3. Monitor Trades

**Check trading status:**
```bash
curl http://localhost:8000/api/trading/status
```

**View recent trades:**
```bash
curl http://localhost:8000/api/trades/history
```

**View open positions:**
```bash
curl http://localhost:8000/api/positions/open
```

## What to Expect

### Timeline
```
T+0s:   Trading starts
T+1s:   Connected to CoinEx
T+2s:   Price data streaming: $96,025
T+20s:  MA calculation begins (need 20 prices)
T+30s:  MAs being calculated every second
T+45s:  First signal likely generated
T+60s:  Position may open (if BUY signal)
T+5m:   Stop-loss/take-profit monitoring
T+30m:  First trade likely completes
```

### Example Trade Flow
```
1. [19:53:42] BUY SIGNAL at $96,025
   ✅ Position opened
   - Entry: $96,025
   - Size: 0.0104 BTC ($1,000)
   - Stop-loss: $94,104 (-2%)
   - Take-profit: $99,866 (+4%)

2. [19:58:15] Price monitoring
   - Current: $96,200
   - Unrealized P&L: +0.18%

3. [20:31:22] TAKE-PROFIT HIT at $99,866
   ✅ Position closed
   - Exit: $99,866
   - P&L: +$40.00 (+4.0%)
   - Duration: 38 minutes

4. Database updated
   ✅ Trade recorded in database
   ✅ Dashboard updated
```

## Demo Mode (Default)

**Safe testing with:**
- Virtual $10,000 balance
- Real market data
- Real signals
- Simulated execution
- Full feature set

**No real money at risk!**

## Database Location

**All trades stored in:**
```
backend/data/foqcapay.db
```

**Tables:**
- `trades` - Completed trades with P&L
- `positions` - Open/closed positions
- `orders` - Individual buy/sell orders
- `account_states` - Balance snapshots
- `trading_events` - Audit trail

## View Database

```bash
# Install SQLite browser (optional)
brew install sqlitebrowser

# Open database
sqlitebrowser backend/data/foqcapay.db
```

Or query directly:
```bash
cd backend
sqlite3 data/foqcapay.db

# View recent trades
SELECT pair, entry_price, exit_price, pnl, exit_reason
FROM trades
ORDER BY exit_time DESC
LIMIT 10;

# View open positions
SELECT pair, entry_price, current_price, unrealized_pnl
FROM positions
WHERE status = 'open';
```

## Stopping Trading

**Via API:**
```bash
curl -X POST http://localhost:8000/api/trading/stop \
  -H "Content-Type: application/json" \
  -d '{"close_positions": true}'
```

**Via Dashboard:**
1. Click "Stop Trading"
2. Choose whether to close open positions
3. Confirm

## Troubleshooting

### No trades opening?
**Wait longer!** Need 20 price updates (~20 seconds) before first MA calculation.

### Signals generating but no positions?
**Only BUY signals open positions.** SELL signals close existing positions or are ignored.

### Want faster testing?
Edit `services/trading_engine.py`:
```python
# Change from:
self.strategy = MAStrategy(fast_period=10, slow_period=20)

# To:
self.strategy = MAStrategy(fast_period=3, slow_period=5)
```
This will generate signals faster (but less reliable).

### Check logs
```bash
# Watch logs in real-time
tail -f backend/logs/trading.log
```

## Advanced Testing

**Run automated test:**
```bash
cd backend
source venv/bin/activate
python test_trading_engine.py
```

This runs a 90-second test that:
- Starts the engine
- Collects price data
- Generates signals
- Shows metrics
- Verifies database

## Configuration

**Environment variables** (`.env` file):
```bash
# Trading
TRADING_MODE=demo              # demo or live
TRADING_PAIRS=BTC/USDC         # Comma-separated
DEMO_STARTING_BALANCE=10000.0  # Demo balance

# Risk Management
DEFAULT_STOP_LOSS_PCT=2.0      # 2% stop-loss
DEFAULT_TAKE_PROFIT_PCT=4.0    # 4% take-profit
MAX_POSITION_SIZE_PCT=10.0     # 10% per trade

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/foqcapay.db
```

## Live Trading (When Ready)

**⚠️ WARNING: Use real API keys carefully!**

1. Create CoinEx API keys (read + trade permissions)
2. Add to `.env`:
   ```bash
   TRADING_MODE=live
   COINEX_API_KEY=your_key_here
   COINEX_API_SECRET=your_secret_here
   ```
3. Start with small amounts
4. Monitor closely

**Production safeguards:**
- Max order size: $1,000
- Daily volume limit: $10,000
- Rate limiting: 5s between orders
- Balance verification before every trade
- All trades logged for audit

## Support

**Check implementation docs:**
- `TRADING_ENGINE_README.md` - Technical details
- `IMPLEMENTATION_SUMMARY.md` - Architecture overview
- `test_trading_engine.py` - Working example

**Logs are in:**
- Console output (structured JSON)
- Database events table
- `backend/logs/` directory

## Success Indicators

**You'll know it's working when you see:**

✅ In logs:
```
INFO: TradingEngine started
INFO: Connected to CoinEx
INFO: BUY SIGNAL - Bullish MA Crossover
INFO: Position opened
```

✅ In database:
- Rows in `positions` table
- Rows in `orders` table
- Eventually rows in `trades` table

✅ In dashboard:
- Open positions showing
- Real-time P&L updating
- Trade history populating

## That's It!

The bot is now fully functional and ready to trade. Just start it and watch it work!

**Happy Trading! 📈**
