# 🤖 FOQCAPAY - Crypto Trading Bot & Dashboard

**A terminal-grade local multi-agent trading system for cryptocurrency markets**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

---

## 🎯 Vision

Empower active crypto traders with a **secure, local-first** trading platform that combines institutional-grade sophistication with individual accessibility. Built with **25 specialized agents** working in parallel, delivering professional trading capabilities without cloud dependencies.

## ✨ Key Features

- **🔄 Multi-Strategy Engine**: 5 proven trading strategies (MA, RSI, MACD, Bollinger, Volume)
- **📊 Real-Time Dashboard**: Beautiful charts with technical indicators, built with Next.js & ShadCN UI
- **🛡️ Comprehensive Risk Management**: Stop-loss, take-profit, trailing stops, drawdown protection
- **🎭 Demo & Live Modes**: Practice risk-free, then trade live on CoinEx
- **🏗️ Multi-Agent Architecture**: 25 specialized agents running in parallel
- **🔒 Local-First Security**: No cloud, no data sharing, full control
- **🌓 Beautiful UI**: Light/dark themes, responsive design, accessible

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **CoinEx Account** - For market data and trading (free registration)
- **Git** - Version control

### Installation

```bash
# Clone the repository
git clone https://github.com/KnocKnuck/foqcapay.git
cd foqcapay

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Configuration
cp .env.example .env
# Edit .env with your CoinEx API keys (for live trading)
```

### Run in Demo Mode

```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2: Start frontend
cd frontend
npm run dev
```

Open **http://localhost:3000** in your browser.

### Run in Live Mode

1. Create a CoinEx API key at https://www.coinex.com/apimanagement
2. Add to `.env`:
   ```
   COINEX_API_KEY=your_api_key
   COINEX_API_SECRET=your_api_secret
   ```
3. Start the application (same as demo mode)
4. Click "Switch to Live Mode" in the dashboard (⚠️ uses real funds!)

## 📚 Documentation

- **[Project Specification](./spec/PROJECT_SPEC.md)** - Complete project vision and requirements
- **[Year Roadmap](./spec/roadmap/YEAR_ROADMAP.md)** - 12-month development plan
- **[Acceptance Criteria](./spec/acceptance/ACCEPTANCE_CRITERIA.feature)** - Gherkin scenarios for all features
- **[Agent Documentation](./.claude/agents/)** - Details on all 25 agents
- **[User Guide](./docs/USER_GUIDE.md)** - How to use the system (coming soon)
- **[API Reference](./docs/API_REFERENCE.md)** - Backend API docs (coming soon)

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────┐
│     Frontend (Next.js + ShadCN)     │
│  Charts | Indicators | Controls     │
└──────────────┬──────────────────────┘
               │ WebSocket + REST
┌──────────────┴──────────────────────┐
│      Backend (FastAPI + Agents)     │
│  ┌─────────────────────────────┐   │
│  │     Event Bus (Pub/Sub)     │   │
│  └─────────────────────────────┘   │
│                                     │
│  25 Specialized Agents:             │
│  • Coordinator                      │
│  • Market Data                      │
│  • 5x Indicators (MA,RSI,MACD,BB,V) │
│  • Signal Synthesis                 │
│  • Risk Management                  │
│  • Execution                        │
│  • + 15 more...                     │
└──────────────┬──────────────────────┘
               │ REST API
┌──────────────┴──────────────────────┐
│      CoinEx Exchange API            │
└─────────────────────────────────────┘
```

### 25-Agent Team

Our system uses a **multi-agent architecture** where each agent is a specialist:

| Layer | Agents | Responsibility |
|-------|--------|----------------|
| **Coordination** | Coordinator, System Architect | Orchestration, governance |
| **Product & Design** | Product Mgmt, UX Design, UI Dev | Requirements, design, frontend |
| **Infrastructure** | DevOps, Logging & Monitoring | Config, observability |
| **Data** | Market Data, Validation, CoinEx Adapter | Data ingestion, quality |
| **Indicators** | MA, RSI, MACD, Bollinger, Volume | Technical analysis |
| **Analysis** | Trend Regime, Divergence Detection | Market classification |
| **Strategy** | Signal Synthesis, Strategy Orchestrator | Decision making |
| **Execution** | Risk Mgmt, Execution, Trade Lifecycle | Order placement, tracking |
| **Interface** | Dashboard, UX Interaction | User interface |
| **Quality** | QA Agent | Testing, validation |

See [.claude/agents/](./.claude/agents/) for detailed agent documentation.

## 🎓 For Traders

### Personas

**Alex - The Experienced Trader**
- Runs multiple strategies simultaneously
- Values transparency and control
- Uses live mode on dedicated hardware

**Nina - The Cautious Learner**
- Learns strategies in demo mode
- Needs clear explanations
- Builds confidence before going live

### Strategies Explained

1. **Moving Average Crossover** 🌊
   - Trend-following strategy
   - Buy: 50 MA crosses above 200 MA (golden cross)
   - Best in: Trending markets

2. **RSI Oscillator** 📉
   - Momentum/reversal strategy
   - Buy: RSI < 30 (oversold)
   - Best in: Ranging markets

3. **MACD Momentum** ⚡
   - Trend reversal detection
   - Buy: MACD line crosses above signal line
   - Best in: All market conditions

4. **Bollinger Bands** 📊
   - Mean reversion strategy
   - Buy: Price touches lower band
   - Best in: Low volatility, ranging

5. **Volume Confirmation** 🔊
   - Validates other signals
   - High volume = strong signal
   - Works with: All strategies

## 🛠️ Development

### Project Structure

```
foqcapay/
├── .claude/              # Agent definitions & Claude AI config
│   └── agents/          # 25 agent specification files
├── spec/                # Project specifications
│   ├── PROJECT_SPEC.md
│   ├── roadmap/
│   └── acceptance/
├── backend/             # Python FastAPI backend
│   ├── agents/         # Agent implementations
│   ├── core/           # Event bus, base classes
│   ├── api/            # REST API endpoints
│   ├── strategies/     # Trading strategies
│   └── indicators/     # Technical indicators
├── frontend/            # Next.js frontend
│   └── src/
│       ├── app/        # Next.js app router
│       ├── components/ # React components (ShadCN)
│       └── lib/        # Utilities
└── docs/                # Documentation
```

### Technology Stack

**Backend**: FastAPI, Python 3.11+, NumPy, Pandas, TA-Lib, CCXT, Redis
**Frontend**: Next.js 14, React 18, TypeScript, ShadCN UI, Tailwind, Recharts
**Testing**: Pytest, Jest, Playwright
**DevOps**: Docker, Docker Compose

### Spec-Driven Development

This project follows **Spec-Driven Development** using [Spec Kit](https://github.com/github/spec-kit):

1. ✅ **Specifications First** - Comprehensive specs before code
2. ✅ **Agent-Based Development** - 25 specialized agents
3. ✅ **Acceptance Criteria** - Gherkin scenarios as "Definition of Done"
4. ✅ **Iterative Delivery** - Phased roadmap with clear milestones

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=agents --cov=core

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 📅 Roadmap

### Q1 2025: Foundation & MVP (Months 1-3)
- ✅ Month 1: Infrastructure setup, event bus, basic UI
- ✅ Month 2: First strategy end-to-end (MA crossover in demo)
- ✅ Month 3: Multi-strategy, risk management

**Milestone**: MVP with demo mode fully functional

### Q2 2025: Production Ready (Months 4-6)
- Month 4: Live trading on CoinEx
- Month 5: UX polish, advanced features
- Month 6: Testing, documentation, beta release

**Milestone**: v1.0 Production Release 🎉

### Q3-Q4 2025: Optimization & Growth
- Performance optimization
- Advanced analytics
- Backtesting engine
- Multi-exchange support (Binance)
- ML strategy framework

See [YEAR_ROADMAP.md](./spec/roadmap/YEAR_ROADMAP.md) for full details.

## 🔒 Security & Privacy

- **Local-First**: All processing on your machine
- **No Cloud**: Zero external dependencies (except CoinEx API)
- **Encrypted Credentials**: AES-256 encryption for API keys
- **No Tracking**: No analytics, no telemetry
- **Open Source**: Full transparency, audit the code

## ⚖️ Legal & Disclaimer

**⚠️ Trading cryptocurrencies involves substantial risk of loss.**

- This software is provided "AS IS" without warranty
- Not financial advice
- Use at your own risk
- You are responsible for regulatory compliance
- Past performance ≠ future results
- The authors are not liable for trading losses

**Recommended**: Start with demo mode, test thoroughly, trade small amounts initially.

## 🤝 Contributing

We welcome contributions! This is a community-driven project.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow spec-driven development (write specs first!)
4. Ensure tests pass (`pytest` and `npm test`)
5. Submit a pull request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for details (coming soon).

## 📞 Support

- **Documentation**: [./docs](./docs)
- **Issues**: [GitHub Issues](https://github.com/KnocKnuck/foqcapay/issues)
- **Discussions**: [GitHub Discussions](https://github.com/KnocKnuck/foqcapay/discussions)
- **Email**: support@foqcapay.dev (coming soon)

## 📜 License

[MIT License](./LICENSE) - See LICENSE file for details.

## 🙏 Acknowledgments

- **CoinEx** - Exchange API
- **ShadCN UI** - Beautiful UI components
- **Spec Kit** - Spec-driven development framework
- **TA-Lib** - Technical analysis library
- **CCXT** - Cryptocurrency exchange integration
- **Open Source Community** - For amazing tools

---

**Built with ❤️ by the FOQCAPAY team**

**Current Version**: v0.1.0-alpha
**Status**: In Development (Month 1)
**Last Updated**: 2025-11-14

---

## 🌟 Star Us!

If you find this project useful, please ⭐ star the repository!

**Ready to start?** → [Quick Start](#-quick-start)
