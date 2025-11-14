# 🚀 Quick Start Guide - FOQCAPAY Trading Bot

**Get up and running in 10 minutes!**

This guide will help you set up and run the FOQCAPAY crypto trading bot locally on your machine.

---

## ✅ Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Redis** - Event bus for agent communication
- **Git** - Version control
- **CoinEx Account** (optional for demo mode) - [Sign up](https://www.coinex.com/)

**Check your versions:**
```bash
python --version    # Should be 3.11 or higher
node --version      # Should be v18 or higher
git --version       # Any recent version
```

---

## 📦 Step 1: Clone the Repository

```bash
git clone https://github.com/KnocKnuck/foqcapay.git
cd foqcapay
```

---

## 🔧 Step 2: Install Redis (Event Bus)

The bot uses Redis for inter-agent communication.

### macOS (Homebrew)
```bash
brew install redis
brew services start redis

# Verify it's running
redis-cli ping
# Should return: PONG
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Verify
redis-cli ping
# Should return: PONG
```

### Windows
1. Download Redis from [tporadowski/redis](https://github.com/tporadowski/redis/releases)
2. Extract and run `redis-server.exe`
3. In another terminal: `redis-cli.exe ping` should return PONG

### Docker (Cross-platform)
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

---

## 🐍 Step 3: Setup Backend (Python/FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies (takes ~2 minutes)
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

### Configure Environment (Optional for Demo)

Edit `backend/.env`:

```bash
# For DEMO mode (default) - No API keys needed!
TRADING_MODE=demo
DEMO_STARTING_BALANCE=10000.0

# Trading Pairs (multi-pair support!)
TRADING_PAIRS=BTC/USDC,ETH/USDC,LINK/USDC

# For LIVE trading (real money!) - Add your CoinEx API keys
# Get keys from: https://www.coinex.com/apimanagement
# COINEX_API_KEY=your_key_here
# COINEX_API_SECRET=your_secret_here
# TRADING_MODE=live  # ONLY when ready!
```

**⚠️ Start with demo mode!** No API keys needed for practice.

---

## 🎨 Step 4: Setup Frontend (Next.js/React)

Open a **new terminal** (keep backend terminal open):

```bash
cd frontend

# Install dependencies (takes ~3 minutes)
npm install

# Create environment file
cp .env.example .env.local

# (Optional) Customize settings
# Edit .env.local if needed - defaults work fine!
```

---

## 🚀 Step 5: Start the Application

### Terminal 1: Start Backend

```bash
cd backend
source venv/bin/activate  # If not already activated
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ Backend is running on **http://localhost:8000**

### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

You should see:
```
▲ Next.js 14.0.4
- Local:        http://localhost:3000
- Ready in 2.5s
```

✅ Frontend is running on **http://localhost:3000**

---

## 🎉 Step 6: Verify Installation

### Open Your Browser

Go to **http://localhost:3000**

You should see:
- ✅ **System Status**: "operational"
- ✅ **Version**: 0.1.0-alpha
- ✅ **Mode**: DEMO (or LIVE if configured)
- ✅ **Trading Pairs**: BTC/USDC, ETH/USDC, LINK/USDC badges
- ✅ **Sprint**: 1.2 - Infrastructure Setup

### Test Backend API

Open **http://localhost:8000** in another tab.

You should see:
```json
{
  "name": "FOQCAPAY Trading Bot",
  "version": "0.1.0-alpha",
  "status": "operational",
  "mode": "demo",
  "trading_pairs": ["BTC/USDC", "ETH/USDC", "LINK/USDC"],
  "sprint": "1.2 - Infrastructure Setup"
}
```

### Test Health Endpoint

http://localhost:8000/health

```json
{
  "status": "healthy",
  "mode": "demo",
  "redis": "connected",
  "agents": "initializing"
}
```

---

## 🎯 What's Working Now (Sprint 1.2)

✅ **Backend API** serving requests
✅ **Event Bus** (Redis) operational
✅ **Frontend** displaying system status
✅ **Multi-pair** configuration (BTC, ETH, LINK)
✅ **Demo mode** ready

### Coming Soon (Sprint 1.2 completion - Week 4):
- 🔨 Live market data from CoinEx
- 🔨 Price charts with candle sticks
- 🔨 Trading pair selector dropdown
- 🔨 Real-time price updates

---

## 🐛 Troubleshooting

### Issue: "redis-cli: command not found"

**Solution**: Redis not installed. Go back to Step 2.

---

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution**: Virtual environment not activated or dependencies not installed.

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

---

### Issue: Backend shows "Connection refused" for Redis

**Solution**: Redis not running.

```bash
# Check if Redis is running
redis-cli ping

# If not, start it
# macOS: brew services start redis
# Ubuntu: sudo systemctl start redis
# Windows: Run redis-server.exe
# Docker: docker start redis
```

---

### Issue: Frontend shows "Failed to connect to backend"

**Solution**: Backend not running or wrong URL.

1. Ensure backend is running: `http://localhost:8000`
2. Check `frontend/.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. Restart frontend: `npm run dev`

---

### Issue: "Port 8000 already in use"

**Solution**: Another process using port 8000.

```bash
# Find process
# macOS/Linux:
lsof -i :8000
kill -9 <PID>

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change port in backend/.env:
PORT=8001
```

---

### Issue: npm install fails

**Solution**: Node version too old or network issues.

```bash
# Check Node version
node --version  # Must be v18+

# Clear npm cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

---

## 📚 Next Steps

### 1. **Explore the Dashboard**
- View system status
- See configured trading pairs
- Check backend connection

### 2. **Read the Documentation**
- [Project Specification](./spec/PROJECT_SPEC.md) - Full vision
- [Sprint Planning](./spec/SPRINT_PLANNING.md) - Current development
- [Agent Documentation](./.claude/agents/) - How agents work

### 3. **Try Demo Trading** (Coming in Sprint 2.2)
- Strategies will execute automatically
- Virtual $10,000 balance
- No real money risk!

### 4. **Monitor Progress**
- Check [Sprint Planning](./spec/SPRINT_PLANNING.md) for latest updates
- Follow commits on GitHub
- Star the repo! ⭐

---

## 🎓 Learn More

### Understanding the System
- **25 Agents**: Each agent is a specialist (Market Data, Indicators, Strategy, etc.)
- **Event Bus**: Agents communicate via Redis Pub/Sub
- **Multi-Pair**: Trade BTC, ETH, LINK (and more) simultaneously
- **Strategies**: Pre-configured Scalping, Intraday, Swing strategies

### Key Files
- `backend/main.py` - Application entry point
- `backend/core/event_bus.py` - Agent communication
- `frontend/src/app/page.tsx` - Dashboard UI
- `spec/SPRINT_PLANNING.md` - Development roadmap

---

## 🔐 Security Notes

### For Demo Mode
- ✅ No API keys needed
- ✅ No real money at risk
- ✅ Safe to experiment

### For Live Trading (When Ready)
- ⚠️ **Never commit API keys to git!**
- ⚠️ Keys are in `.env` (which is git-ignored)
- ⚠️ Start with small amounts
- ⚠️ Understand risks before going live

---

## 🤝 Getting Help

### Something not working?

1. **Check this guide** - Most issues covered above
2. **Check logs**:
   - Backend: Terminal 1 output
   - Frontend: Terminal 2 output and browser console (F12)
3. **Check Redis**: `redis-cli ping` should return PONG
4. **GitHub Issues**: [Report a bug](https://github.com/KnocKnuck/foqcapay/issues)
5. **Discord** (coming soon): Community support

---

## 🎉 Success!

If you see the dashboard and system status shows "operational", you're ready! 🚀

**What's Next**:
- Wait for Sprint 1.2 completion (live charts coming!)
- Read the [User Stories](./spec/USER_STORIES.md) to understand features
- Follow along with development
- Consider contributing!

---

## ⏱️ Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Redis installed and running (`redis-cli ping` = PONG)
- [ ] Repository cloned
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend `.env` file created from `.env.example`
- [ ] Frontend `.env.local` file created from `.env.example`
- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Dashboard shows "operational" status
- [ ] Trading pairs (BTC, ETH, LINK) displayed

**Completion Time**: 10-15 minutes ✅

---

**Welcome to FOQCAPAY!** 🤖💰

**Status**: Sprint 1.2 - Infrastructure Ready
**Next Update**: Sprint 1.2 completion (live charts!)
**Last Updated**: 2025-11-14
