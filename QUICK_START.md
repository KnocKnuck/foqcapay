# 🚀 Quick Start Guide - FOQCAPAY Trading Bot

**Get up and running in under 5 minutes with Docker!**

This guide provides TWO ways to run the FOQCAPAY crypto trading bot:
1. **🐳 Docker** (Recommended - Easiest & Fastest!)
2. **🔧 Manual Setup** (For development)

**Current Sprint**: 5.2 - Advanced Features (Backtesting + Export)
**Status**: 77% Complete, Production-Ready Database Persistence

---

## 🎯 Choose Your Path

### **Option A: Docker Setup** (Recommended for Quick Start)
✅ No Python/Node installation needed
✅ Redis included automatically
✅ Production-ready configuration
✅ One command to start
⏱️ **Time**: 3-5 minutes

[Jump to Docker Setup](#-option-a-docker-setup-recommended)

### **Option B: Manual Setup** (For Development)
🔧 Full control over environment
🔨 Best for contributors/developers
📚 Learn the internals
⏱️ **Time**: 10-15 minutes

[Jump to Manual Setup](#-option-b-manual-setup-development)

---

# 🐳 Option A: Docker Setup (Recommended)

## Prerequisites

- **Docker** & **Docker Compose** - [Get Docker](https://docs.docker.com/get-docker/)
- **Git** - [Download](https://git-scm.com/downloads)

**Check your installation:**
```bash
docker --version          # Should be 20.10+
docker-compose --version  # Should be 2.0+
```

---

## Step 1: Clone & Configure

```bash
# Clone repository
git clone https://github.com/KnocKnuck/foqcapay.git
cd foqcapay

# Create environment file from template
cp .env.example .env

# (Optional) Edit .env for your preferences
# Default values work great for demo mode!
nano .env  # or use any text editor
```

### Quick .env Configuration

For **DEMO MODE** (no API keys needed):
```bash
TRADING_MODE=demo
TRADING_PAIRS=BTC/USDC,ETH/USDC,LINK/USDC
```

For **LIVE TRADING** (⚠️ real money!):
```bash
TRADING_MODE=live
COINEX_API_KEY=your_api_key_here
COINEX_API_SECRET=your_api_secret_here
ENCRYPTION_PASSWORD=your_strong_password_min_32_chars
```

---

## Step 2: Start Everything

```bash
# Start all services with one command!
docker-compose up -d

# Check status
docker-compose ps
```

You should see:
```
NAME                 STATUS              PORTS
foqcapay-backend     Up 10 seconds      0.0.0.0:8000->8000/tcp
foqcapay-redis       Up 11 seconds      0.0.0.0:6379->6379/tcp
```

---

## Step 3: Verify Installation

### Check Backend API
Open **http://localhost:8000** in your browser:

```json
{
  "name": "FOQCAPAY Trading Bot",
  "version": "0.5.0-beta",
  "status": "operational",
  "mode": "demo",
  "trading_pairs": ["BTC/USDC", "ETH/USDC", "LINK/USDC"],
  "sprint": "5.2 - Advanced Features",
  "database": "connected"
}
```

### Check Health
**http://localhost:8000/health**

```json
{
  "status": "healthy",
  "mode": "demo",
  "database": "connected",
  "redis": "connected",
  "agents": "operational"
}
```

### View Logs
```bash
# View backend logs
docker-compose logs -f backend

# View all logs
docker-compose logs -f
```

---

## ✅ You're Running!

### What's Available Now:

**API Endpoints** - http://localhost:8000/docs (Swagger UI)
- ✅ `/api/trades/*` - Trade history & management
- ✅ `/api/positions/*` - Position tracking
- ✅ `/api/performance/*` - Performance metrics
- ✅ `/api/backtest/*` - Strategy backtesting
- ✅ `/api/export/*` - Data export (CSV/JSON)
- ✅ `/api/monitoring/*` - System monitoring
- ✅ `/ws/*` - WebSocket real-time updates

**Features**:
- ✅ Multi-pair trading (BTC, ETH, LINK/USDC)
- ✅ 4 trading strategies (Scalping, Intraday, Swing, MA Crossover)
- ✅ Risk management (stop-loss, take-profit, trailing stops)
- ✅ **Database persistence** (all data survives restarts!)
- ✅ **Backtesting engine** (test strategies on historical data!)
- ✅ **Export to CSV/JSON** (analyze your trades!)
- ✅ Real-time monitoring
- ✅ Production-ready logging

---

## Docker Commands Cheat Sheet

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps

# Update to latest code
git pull
docker-compose build
docker-compose up -d

# Stop and remove everything (including data!)
docker-compose down -v  # ⚠️ This deletes database!

# Access backend shell
docker-compose exec backend bash

# Run tests
docker-compose exec backend pytest
```

---

## 🎮 Using the Trading Dashboard

### Overview
The Trading Dashboard provides full control over your trading bot with an intuitive interface for:
- Starting/stopping trading
- Switching between trading strategies
- Toggling Demo vs Live mode
- Monitoring real-time prices
- Viewing active positions and trade history

### Trading Controls

#### Start Trading
1. Select a trading strategy from the dropdown:
   - **Scalping**: Fast trades, 1-5 minute timeframes, quick profits
   - **Intraday**: Trade within the day, 15m-1h timeframes
   - **Swing**: Multi-day positions, 4h-1d timeframes
   - **MA Crossover**: Moving average crossover strategy

2. Choose your mode:
   - **Demo Mode**: Paper trading with virtual funds (safe for testing)
   - **Live Mode**: Real trading with actual funds (requires API keys)

3. Click **"Start Trading"** button
   - Bot begins executing the selected strategy
   - Real-time updates appear in the dashboard
   - Price ticker shows current market prices

#### Stop Trading
1. Click **"Stop Trading"** button
2. Bot stops opening new positions
3. Option to close existing positions or leave them open
4. Trading status updates to "Stopped"

#### Change Strategy (Hot-Swap)
- Select a new strategy from the dropdown
- Click **"Change Strategy"** button
- Strategy switches immediately (even while trading is active)
- Existing positions remain open
- New signals use the new strategy

#### Switch Trading Mode
- Toggle between Demo and Live mode
- **Important**: Recommended to stop trading before switching modes
- Demo mode requires no API keys
- Live mode requires CoinEx API credentials

### Pair Selector & Price Ticker
- **Pair Selector**: Choose which trading pair to view (BTC/USDC, ETH/USDC, LINK/USDC)
- **Price Ticker**: Real-time price updates for selected pair
- Updates automatically via WebSocket connection
- Shows current market price with 2 decimal precision

### Dashboard Features

#### Active Positions
- View all open positions in real-time
- Shows: pair, side (long/short), entry price, current P&L
- Auto-updates via WebSocket

#### Recent Trades
- Complete trade history
- Filters by pair, date range, strategy
- Shows: timestamp, pair, side, price, quantity, P&L
- Export to CSV/JSON for analysis

#### Performance Metrics
- Total P&L (profit/loss)
- Win rate percentage
- Sharpe ratio (risk-adjusted returns)
- Maximum drawdown
- Daily/weekly/monthly performance charts

---

## 🎯 Try It Out!

### 1. Run a Backtest

```bash
curl -X POST "http://localhost:8000/api/backtest/run" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "MA_Crossover",
    "pair": "BTC/USDC",
    "timeframe": "1h",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-01T00:00:00",
    "initial_capital": 10000,
    "position_size_pct": 10,
    "stop_loss_pct": 2,
    "take_profit_pct": 5
  }'
```

### 2. Export Trades to CSV

Visit: http://localhost:8000/api/export/trades/csv

Downloads: `trades_20251114.csv`

### 3. View API Documentation

Visit: http://localhost:8000/docs

Interactive Swagger UI with all endpoints!

---

## 🐛 Troubleshooting Docker

### Issue: "port is already allocated"

```bash
# Find what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Either kill that process or change port in docker-compose.yml
```

### Issue: "Cannot connect to Docker daemon"

```bash
# Start Docker Desktop (Mac/Windows)
# Or start Docker service (Linux):
sudo systemctl start docker
```

### Issue: Containers keep restarting

```bash
# Check logs for errors
docker-compose logs backend

# Common fixes:
# 1. Check .env file exists and is valid
# 2. Ensure Redis is healthy: docker-compose logs redis
# 3. Rebuild: docker-compose build --no-cache
```

### Issue: Database not persisting

```bash
# Check data volume
docker volume ls | grep foqcapay

# Data is in: ./data/foqcapay.db (mapped from container)
ls -la data/

# Ensure volume is mounted (check docker-compose.yml)
```

---

# 🔧 Option B: Manual Setup (Development)

For developers who want full control.

## Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/) (for frontend, coming soon)
- **Redis** - Event bus
- **Git** - Version control

```bash
python --version  # 3.11+
node --version    # v18+
git --version
```

---

## Step 1: Clone Repository

```bash
git clone https://github.com/KnocKnuck/foqcapay.git
cd foqcapay
```

---

## Step 2: Install Redis

### macOS (Homebrew)
```bash
brew install redis
brew services start redis
redis-cli ping  # Should return: PONG
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
redis-cli ping  # Should return: PONG
```

### Windows
Download from [tporadowski/redis](https://github.com/tporadowski/redis/releases)
Run `redis-server.exe`

### Docker (Quick Alternative)
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

---

## Step 3: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows

# Install dependencies (~2 minutes)
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env as needed (defaults work for demo!)
```

---

## Step 4: Start Backend

```bash
cd backend
source venv/bin/activate  # If not already active

# Run the server
python main.py
```

Expected output:
```
INFO:     application_starting version="0.5.0-beta" mode="demo"
INFO:     database_initialized path="sqlite+aiosqlite:///data/foqcapay.db"
INFO:     event_bus_initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ Backend is running on **http://localhost:8000**

---

## Step 5: Verify

Visit: http://localhost:8000

You should see the API status JSON.

Visit: http://localhost:8000/docs

Interactive API documentation!

---

## 📊 What's Working (Sprint 5.2 - 77% Complete)

### ✅ Completed Features:

**Infrastructure** (Sprints 1-2):
- ✅ FastAPI backend
- ✅ Redis event bus
- ✅ Multi-pair support (BTC, ETH, LINK)
- ✅ 5 technical indicators (MA, RSI, MACD, BB, Volume)

**Trading** (Sprints 3-4):
- ✅ 4 trading strategies
- ✅ Risk management (stop-loss, take-profit, drawdown protection)
- ✅ Live trading mode (CoinEx integration)
- ✅ Demo mode (paper trading)
- ✅ Production safeguards ($5K order limit, $20K daily limit)

**Monitoring** (Sprint 4.2):
- ✅ Performance monitoring
- ✅ WebSocket real-time updates
- ✅ Admin dashboard
- ✅ Health checks

**Data Persistence** (Sprint 4.3 - CRITICAL!):
- ✅ SQLite database
- ✅ Trade history persistence
- ✅ Position tracking
- ✅ Account state snapshots
- ✅ Complete audit trail
- ✅ Data survives restarts!

**Dashboard** (Sprint 5.1):
- ✅ Trading dashboard (positions, trades, P&L)
- ✅ Performance charts (equity curve, daily P&L)
- ✅ Real-time WebSocket updates

**Advanced Features** (Sprint 5.2 - 64% Complete):
- ✅ **Backtesting engine** (test strategies on historical data!)
- ✅ **Export to CSV/JSON** (download trade history!)
- ✅ Performance metrics (Sharpe, Sortino, drawdown)
- ✅ Strategy comparison
- 🔨 Notifications (Telegram, email) - In Progress

---

## 🎯 Try the New Features!

### 1. Backtest a Strategy

```python
# Using Python requests
import requests

response = requests.post("http://localhost:8000/api/backtest/run", json={
    "strategy_name": "MA_Crossover",
    "pair": "BTC/USDC",
    "timeframe": "1h",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-01T00:00:00",
    "initial_capital": 10000,
    "position_size_pct": 10,
    "stop_loss_pct": 2,
    "take_profit_pct": 5
})

print(response.json())
# Returns: backtest_id, total_return_pct, win_rate, sharpe_ratio, etc.
```

### 2. Export Your Trades

Visit in browser:
- CSV: http://localhost:8000/api/export/trades/csv
- JSON: http://localhost:8000/api/export/trades/json

Or with curl:
```bash
curl "http://localhost:8000/api/export/trades/csv?pair=BTC/USDC" > my_trades.csv
```

### 3. View Backtest Results

```bash
# List all backtests
curl http://localhost:8000/api/backtest/list

# Get specific backtest details
curl http://localhost:8000/api/backtest/results/{backtest_id}

# Get equity curve data
curl http://localhost:8000/api/backtest/results/{backtest_id}/equity_curve
```

---

## 📚 Next Steps

### 1. Explore the API
- Visit http://localhost:8000/docs
- Try out different endpoints
- Run backtests with different parameters

### 2. Read the Documentation
- [Sprint Progress Report](./spec/SPRINT_PROGRESS_REPORT.md) - See what's done
- [Live Trading Guide](./LIVE_TRADING_GUIDE.md) - When you're ready for real trading
- [Project Specification](./spec/PROJECT_SPEC.md) - Full vision

### 3. Try Live Trading (When Ready!)
- Get CoinEx API keys
- Update `.env` with your keys
- Set `TRADING_MODE=live`
- **Start with small amounts!**

### 4. Contribute
- Report bugs on GitHub
- Suggest features
- Submit pull requests
- Star the repo! ⭐

---

## 🔐 Security Best Practices

### For Demo Mode
- ✅ No API keys needed
- ✅ No real money at risk
- ✅ Safe to experiment

### For Live Trading
- ⚠️ **NEVER commit API keys to git!**
- ⚠️ Use strong `ENCRYPTION_PASSWORD`
- ⚠️ Keep `.env` file secure (it's git-ignored)
- ⚠️ Start with small amounts
- ⚠️ Enable 2FA on your CoinEx account
- ⚠️ Use IP whitelisting on API keys
- ⚠️ Monitor your trades regularly

### Data Security
- ✅ API keys encrypted in database (PBKDF2HMAC)
- ✅ Database at `data/foqcapay.db` (backup regularly!)
- ✅ Logs at `logs/` (check for sensitive data)
- ✅ All sensitive files in `.gitignore`

---

## 🐛 Troubleshooting

### Redis Connection Issues

```bash
# Check if Redis is running
redis-cli ping  # Should return: PONG

# If not, start it
brew services start redis  # macOS
sudo systemctl start redis  # Linux
# Or restart Docker container
```

### Import Errors

```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Must be 3.11+
```

### Database Issues

```bash
# Check if database file exists
ls -la data/foqcapay.db

# If missing, it will be created on first run
# Delete and recreate if corrupted:
rm data/foqcapay.db
python main.py  # Will create fresh database
```

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in .env:
PORT=8001
```

---

## 📊 Project Status

**Version**: 0.5.0-beta
**Sprint**: 5.2 - Advanced Features
**Progress**: 77% Complete (10/13 sprints)
**Lines of Code**: ~13,100+
**API Endpoints**: 46+
**Database Models**: 5
**Test Coverage**: 31 tests passing

**Production Ready**:
- ✅ Database persistence
- ✅ Live trading
- ✅ Risk management
- ✅ Monitoring
- ✅ Backtesting
- ✅ Export functionality
- 🔨 Notifications (in progress)

---

## 🤝 Getting Help

### Resources
- **API Docs**: http://localhost:8000/docs
- **GitHub Issues**: [Report bugs](https://github.com/KnocKnuck/foqcapay/issues)
- **Documentation**: See `spec/` folder
- **Logs**: Check terminal output and `logs/` directory

### Common Questions

**Q: Can I trade with real money?**
A: Yes! Set `TRADING_MODE=live` and add your CoinEx API keys. Start small!

**Q: How do I add more trading pairs?**
A: Edit `.env` → `TRADING_PAIRS=BTC/USDC,ETH/USDC,YOUR/PAIR`

**Q: Where is my data stored?**
A: Database at `data/foqcapay.db`, logs at `logs/`, both git-ignored.

**Q: How do I backup my data?**
A: Copy `data/foqcapay.db` file. For Docker: `docker cp foqcapay-backend:/app/data ./backup`

**Q: Can I run multiple strategies at once?**
A: Yes! The system supports multi-strategy execution on multiple pairs simultaneously.

---

## 🎉 Success Checklist

- [ ] Docker installed (Option A) OR Python 3.11+ (Option B)
- [ ] Repository cloned
- [ ] `.env` file created and configured
- [ ] Services started (Docker: `docker-compose up -d` / Manual: `python main.py`)
- [ ] Backend accessible at http://localhost:8000
- [ ] API docs showing at http://localhost:8000/docs
- [ ] Health check shows "healthy"
- [ ] Database connected
- [ ] Redis connected

**Completion Time**:
- Docker: 3-5 minutes ✅
- Manual: 10-15 minutes ✅

---

## 🚀 You're Ready!

**Welcome to FOQCAPAY!** 🤖💰

You now have a production-ready crypto trading bot with:
- Multi-pair trading
- Multiple strategies
- Backtesting capabilities
- Data export
- Complete persistence
- Real-time monitoring

**Start exploring and happy trading!** 📈

---

**Last Updated**: 2025-11-14
**Status**: Sprint 5.2 (Advanced Features) - 77% Complete
**Next Sprint**: 5.2 Completion → Notifications + Testing
**v1.0 Target**: Month 6
