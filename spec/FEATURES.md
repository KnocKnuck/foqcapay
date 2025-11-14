# Feature Catalog - FOQCAPAY

**Version**: 1.0
**Last Updated**: 2025-11-14

## Overview

This document catalogs all features of the FOQCAPAY crypto trading bot, organized by initiative and with detailed specifications for each.

---

## Feature Matrix

| Feature ID | Feature Name | Initiative | Priority | Target Release |
|------------|--------------|------------|----------|----------------|
| F-001 | Real-Time Market Data | I1, I2 | P0 | Month 1 |
| F-002 | Technical Indicators (5x) | I1 | P0 | Month 2-3 |
| F-003 | Pre-Configured Strategies | I1 | P0 | Month 3-5 |
| F-004 | Real-Time Dashboard | I2 | P0 | Month 2 |
| F-005 | Strategy Selection UI | I2 | P1 | Month 5 |
| F-006 | Demo Mode Trading | I3 | P0 | Month 2 |
| F-007 | Live Mode Trading | I3 | P0 | Month 4 |
| F-008 | Risk Management Controls | I3 | P0 | Month 3 |
| F-009 | Event Bus Architecture | I4 | P0 | Month 1 |
| F-010 | 25-Agent System | I4 | P0 | Month 1-6 |
| F-011 | Automated Testing | I5 | P0 | Month 1-6 |
| F-012 | User Documentation | I5 | P1 | Month 6 |

**Priority Levels**: P0 (Must-have for v1.0), P1 (Should-have for v1.0), P2 (Nice-to-have)

---

## F-001: Real-Time Market Data

### Description
Integration with CoinEx exchange to fetch live market data (prices, volumes) for selected trading pairs with real-time updates.

### Initiative
Initiative 1 (Multi-Strategy Engine), Initiative 2 (Dashboard UI)

### User Story References
- US-001: Real-time market data visibility
- US-004: Clear visual feedback

### Acceptance Criteria
```gherkin
Scenario: System connects to CoinEx
  Given the application starts
  When the Market Data agent initializes
  Then connection to CoinEx is established within 5 seconds
  And market data stream begins for BTC/USDT
```

### Technical Specifications
- **API**: CoinEx WebSocket API (wss://socket.coinex.com/)
- **Data Format**: OHLCV (Open, High, Low, Close, Volume) candles
- **Update Frequency**: Real-time ticks (as provided by exchange)
- **Timeframes**: 1m, 5m, 15m, 1h, 4h, 1d
- **Latency SLA**: <500ms from exchange to UI
- **Backup**: REST API polling if WebSocket fails

### Responsible Agents
- **Market Data Agent**: Primary data ingestion
- **Data Validation Agent**: Quality assurance
- **CoinEx API Adapter**: Exchange interface

### Dependencies
- CoinEx API access
- Network connectivity
- Event bus operational

### Target Release
Month 1, Sprint 1.2

---

## F-002: Technical Indicators (5x)

### Description
Five technical indicators calculated in real-time and displayed on charts to support trading strategies.

### Sub-Features

#### F-002a: Moving Averages (MA)
- **Periods**: 20, 50, 200 (configurable)
- **Types**: SMA (Simple) and EMA (Exponential)
- **Output**: MA values, crossover events (golden cross, death cross)
- **Agent**: MA Indicator Agent

#### F-002b: Relative Strength Index (RSI)
- **Period**: 14 (configurable)
- **Range**: 0-100
- **Zones**: Oversold (<30), Neutral (30-70), Overbought (>70)
- **Output**: RSI value, zone transitions
- **Agent**: RSI Indicator Agent

#### F-002c: MACD (Moving Average Convergence Divergence)
- **Configuration**: 12/26/9 (fast/slow/signal)
- **Components**: MACD line, Signal line, Histogram
- **Output**: Values, crossover events (bullish/bearish)
- **Agent**: MACD Indicator Agent

#### F-002d: Bollinger Bands
- **Period**: 20 (configurable)
- **Standard Deviations**: 2
- **Bands**: Upper, Middle (SMA), Lower
- **Output**: Band values, price position, squeeze/expansion events
- **Agent**: Bollinger Bands Agent

#### F-002e: Volume Analysis
- **Metrics**: Current volume, average volume (20-period)
- **Patterns**: Volume spikes, low liquidity warnings
- **Output**: Volume values, spike events, confirmation signals
- **Agent**: Volume Analysis Agent

### Performance Requirements
- **Calculation Latency**: <25ms per indicator
- **Accuracy**: 100% (validated against TA-Lib)
- **Parallel Processing**: All indicators calculate simultaneously

### UI Integration
- Indicators overlaid on price chart
- Separate subcharts for RSI and MACD
- Indicator panel showing current values
- Color-coded status (green/yellow/red)

### Target Release
Month 2-3

---

## F-003: Pre-Configured Trading Strategies

### Description
Three ready-to-use trading strategies optimized for different trading styles: Scalping, Intraday, and Swing.

### Sub-Features

#### F-003a: Scalping Strategy ⚡
**Trading Style**: Ultra-short-term, quick in-and-out

**Timeframe**: 1-5 minutes

**Indicators Used**:
- EMA (9/21 fast crossover)
- RSI (5-period for quick momentum)
- Volume confirmation

**Entry Rules**:
- EMA 9 crosses above EMA 21 (bullish)
- RSI > 50 (momentum confirmation)
- Volume > 1.5x average (liquidity confirmation)
- Trend Regime: Any (works in both trending and ranging)

**Exit Rules**:
- **Take Profit**: +0.5% to +1% (quick gains)
- **Stop Loss**: -0.3% (tight stop)
- **Trailing Stop**: Yes, 0.2% trail once +0.3% profit
- **Time-based**: Exit after 15 minutes if not hit TP/SL

**Risk Parameters**:
- Max position size: 10% of capital per trade
- Max concurrent positions: 3
- Max daily trades: 20

**Best For**:
- High-frequency opportunities
- Highly liquid markets (BTC, ETH)
- Active monitoring (not set-and-forget)

**Agent Configuration**:
```json
{
  "strategy_name": "scalping",
  "timeframe": "1m",
  "indicators": ["ema_9", "ema_21", "rsi_5", "volume"],
  "entry": {
    "ema_cross": "9_above_21",
    "rsi_threshold": ">50",
    "volume_multiplier": 1.5
  },
  "exit": {
    "take_profit_pct": 0.5,
    "stop_loss_pct": 0.3,
    "trailing_stop_pct": 0.2,
    "max_hold_minutes": 15
  },
  "risk": {
    "position_size_pct": 10,
    "max_positions": 3,
    "max_daily_trades": 20
  }
}
```

---

#### F-003b: Intraday Strategy 📊
**Trading Style**: Same-day trades, hold for hours

**Timeframe**: 5-60 minutes (primarily 15m)

**Indicators Used**:
- MA (20/50 crossover)
- RSI (14-period)
- MACD (12/26/9)
- Volume confirmation

**Entry Rules**:
- MA 20 crosses above MA 50 (trend confirmation)
- RSI between 40-70 (not overbought/oversold)
- MACD histogram positive and increasing
- Volume > average (confirmation)
- Trend Regime: Trending preferred

**Exit Rules**:
- **Take Profit**: +2% to +4%
- **Stop Loss**: -1.5%
- **Trailing Stop**: Yes, 1% trail once +2% profit
- **Time-based**: Exit by end of trading day (if 24/7 market, exit after 8 hours)

**Risk Parameters**:
- Max position size: 20% of capital per trade
- Max concurrent positions: 5
- Max daily trades: 10

**Best For**:
- Capturing intraday trends
- Balanced risk/reward
- Alex (experienced trader)

**Agent Configuration**:
```json
{
  "strategy_name": "intraday",
  "timeframe": "15m",
  "indicators": ["ma_20", "ma_50", "rsi_14", "macd", "volume"],
  "entry": {
    "ma_cross": "20_above_50",
    "rsi_range": [40, 70],
    "macd_histogram": "positive_increasing",
    "volume_multiplier": 1.2,
    "regime_filter": "trending"
  },
  "exit": {
    "take_profit_pct": 3.0,
    "stop_loss_pct": 1.5,
    "trailing_stop_pct": 1.0,
    "max_hold_hours": 8
  },
  "risk": {
    "position_size_pct": 20,
    "max_positions": 5,
    "max_daily_trades": 10
  }
}
```

---

#### F-003c: Swing Strategy 🌊
**Trading Style**: Multi-day positions, catch larger moves

**Timeframe**: 4-hour to daily (primarily 4h)

**Indicators Used**:
- MA (50/200 golden cross)
- RSI (14-period for divergences)
- MACD (standard 12/26/9)
- Bollinger Bands (mean reversion opportunities)
- Volume trends

**Entry Rules**:
- MA 50 crosses above MA 200 (major trend change)
- OR Price bounces off lower Bollinger Band + RSI <30
- MACD confirms direction
- Volume increasing on entry
- Trend Regime: Strong trend or regime transition

**Exit Rules**:
- **Take Profit**: +8% to +15%
- **Stop Loss**: -4%
- **Trailing Stop**: Yes, 3% trail once +5% profit
- **Time-based**: Hold for days/weeks (no forced exit)

**Risk Parameters**:
- Max position size: 30% of capital per trade
- Max concurrent positions: 3
- Max trades per week: 5

**Best For**:
- Capturing major trends
- Longer-term outlook
- Less frequent monitoring
- Nina (learning) and Alex (portfolio diversity)

**Agent Configuration**:
```json
{
  "strategy_name": "swing",
  "timeframe": "4h",
  "indicators": ["ma_50", "ma_200", "rsi_14", "macd", "bollinger_20", "volume"],
  "entry": {
    "conditions": [
      {
        "type": "ma_golden_cross",
        "ma_cross": "50_above_200"
      },
      {
        "type": "mean_reversion",
        "bollinger_touch": "lower",
        "rsi_threshold": "<30"
      }
    ],
    "macd_confirm": true,
    "volume_trend": "increasing",
    "regime_filter": ["strong_trend", "transition"]
  },
  "exit": {
    "take_profit_pct": 10.0,
    "stop_loss_pct": 4.0,
    "trailing_stop_pct": 3.0,
    "max_hold_days": null
  },
  "risk": {
    "position_size_pct": 30,
    "max_positions": 3,
    "max_weekly_trades": 5
  }
}
```

---

### Strategy Selection UI

**Location**: Dashboard settings panel

**Components**:
1. **Strategy Selector Dropdown**
   - Options: "Scalping", "Intraday", "Swing", "Custom"
   - Visual badges showing style (⚡ 🔄 🌊)

2. **Strategy Preview Card**
   - Timeframe
   - Typical hold time
   - Win rate (backtested)
   - Risk level (Low/Medium/High)
   - Best for: description

3. **Quick Configuration**
   - Adjust risk parameters (sliders)
   - Enable/disable specific indicators
   - Set max position size

4. **Strategy Performance**
   - Backtest results summary
   - Recent trade history for this strategy
   - P/L chart

### Responsible Agents
- **Strategy Orchestrator**: Manages active strategy
- **Signal Synthesis**: Combines strategy signals
- **Product Management**: Defines strategy rules
- **UX Design**: Strategy selection interface

### Target Release
- Month 3: Basic strategy framework
- Month 5: All 3 pre-configured strategies with UI

---

## F-004: Real-Time Dashboard

### Description
Web-based dashboard providing real-time visualization of market data, indicators, trades, and bot status.

### Key Components

#### Dashboard Layout
```
┌────────────────────────────────────────────────────────────┐
│  FOQCAPAY                    BTC/USDT $30,125 ▲ 2.3%      │
│  ☰ Menu   Strategy: Intraday   Mode: [DEMO] [LIVE]   🌓   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                Price Chart + Indicators               │ │
│  │  [Candlesticks with MA overlays, buy/sell markers]   │ │
│  │                                                       │ │
│  │  Height: 60% of viewport                             │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌────────────────────┐ ┌─────────────────────────────┐  │
│  │   RSI Chart        │ │    MACD Chart               │  │
│  │   [RSI line]       │ │    [MACD, Signal, Histogram]│  │
│  └────────────────────┘ └─────────────────────────────┘  │
├────────────────────────────────────────────────────────────┤
│  Open Positions (2) │ Performance │ Signals │ Logs        │
├────────────────────────────────────────────────────────────┤
│  BTC/USDT Long      Entry: $29,800  P/L: +$162.50 (+1.09%)│
│  ETH/USDT Long      Entry: $1,850   P/L: -$22.00 (-0.59%) │
└────────────────────────────────────────────────────────────┘
```

#### Chart Features
- Candlestick visualization (green/red)
- Indicator overlays (MA lines, Bollinger Bands)
- Buy/sell signal markers (↑ green, ↓ red)
- Volume bars below price
- Crosshair and tooltips
- Zoom and pan controls
- Timeframe selector (1m, 5m, 15m, 1h, 4h, 1d)

#### Indicator Panels
- Current values displayed
- Color-coded status (green=bullish, red=bearish, yellow=neutral)
- Mini charts for RSI and MACD
- Bollinger Band width indicator

#### Position Tracking
- Open positions table: Pair, Side, Entry, Current, P/L, Actions
- Real-time P/L updates
- Click to view position details
- Quick close button

#### Performance Metrics
- Total P/L (session, day, week, all-time)
- Win rate %
- Number of trades (wins/losses)
- Sharpe ratio (if >30 trades)
- Best/worst trade

### Technology Stack
- **Framework**: Next.js 14 (React 18)
- **UI Library**: ShadCN UI + Radix UI
- **Styling**: Tailwind CSS
- **Charts**: Recharts or Lightweight Charts
- **State**: Zustand
- **Real-time**: WebSocket client

### Performance Requirements
- Initial load: <3 seconds
- Chart update latency: <200ms
- Frame rate: 60fps (16ms per frame)
- Bundle size: <500KB gzipped

### Responsible Agents
- **UI Development Agent**: Implementation
- **UX Design Agent**: Design and layout
- **Dashboard Agent**: Backend data provider

### Target Release
Month 2 (basic), Month 5 (complete)

---

## F-005: Strategy Selection UI

### Description
User interface for selecting, configuring, and managing trading strategies.

### Features
1. **Pre-Set Strategy Selection**
   - Dropdown or card-based selector
   - Visual previews of each strategy
   - Tooltips explaining when to use each

2. **Custom Strategy Builder** (v1.1+)
   - Drag-and-drop indicator selection
   - Configure entry/exit rules
   - Test on historical data

3. **Strategy Configuration Panel**
   - Risk parameter sliders (stop-loss %, take-profit %)
   - Position size control
   - Enable/disable specific indicators within strategy

4. **Multi-Strategy Mode**
   - Run multiple strategies simultaneously
   - Allocate capital % to each
   - View performance per strategy

5. **Strategy Performance Dashboard**
   - Backtest results
   - Live performance metrics
   - Comparison table (side-by-side)

### UX Flow
```
1. User clicks "Change Strategy" button
   ↓
2. Modal opens with 3 options: Scalping, Intraday, Swing
   ↓
3. User clicks "Intraday" card
   ↓
4. Preview shown: "Best for capturing trends over hours.
   Typical hold: 2-8 hours. Win rate: 62% (backtested)"
   ↓
5. User adjusts stop-loss from 1.5% to 2%
   ↓
6. User clicks "Activate Strategy"
   ↓
7. Confirmation: "Intraday strategy activated. Bot will use
   15-minute timeframe and 2% stop-loss."
   ↓
8. Dashboard updates to show active strategy badge
```

### Responsible Agents
- **UX Design Agent**: Interface design
- **UI Development Agent**: Implementation
- **Product Management Agent**: Strategy definitions
- **UX Interaction Agent**: Handle user commands

### Target Release
Month 5

---

## F-006: Demo Mode Trading

### Description
Paper trading mode that simulates real trades without risking actual funds, perfect for learning and testing.

### Features
1. **Simulated Order Execution**
   - Instant fills at current market price
   - Realistic slippage simulation (optional)
   - No real API calls to exchange

2. **Virtual Portfolio**
   - Starting balance: $10,000 (configurable)
   - Track virtual positions and P/L
   - Reset portfolio anytime

3. **Full Trade Lifecycle**
   - Entry, monitoring, exit
   - Stop-loss and take-profit execution
   - Trade history logging

4. **Learning Features**
   - Trade annotations: "Why this trade?"
   - Strategy explanations
   - Mistakes highlighted

5. **Performance Tracking**
   - Virtual P/L dashboard
   - Strategy effectiveness
   - Preparedness score before going live

### UI Indicators
- **Badge**: "DEMO MODE" in yellow/orange
- **Balance**: "Virtual: $10,234.56"
- **Disclaimer**: "No real funds at risk"

### Responsible Agents
- **Execution Agent**: Simulated execution logic
- **Trade Lifecycle Agent**: Tracking
- **Risk Management Agent**: Simulated stop-loss triggers

### Target Release
Month 2

---

## F-007: Live Mode Trading

### Description
Real trading on CoinEx exchange with actual funds.

### Features
1. **Real Order Execution**
   - Market orders via CoinEx API
   - Order status monitoring
   - Fill confirmations

2. **Fund Management**
   - Real balance checks
   - Position size calculations
   - Insufficient funds handling

3. **Safety Mechanisms**
   - Confirmation required to switch to live mode
   - Warning: "You are about to trade with real funds"
   - Emergency stop button

4. **Order Reliability**
   - Retry logic (exponential backoff)
   - Timeout handling
   - Error recovery

### Mode Switching
```
Demo → Live:
1. User clicks "Switch to Live Mode"
2. Warning dialog: "Real funds will be used. Continue?"
3. API key validation
4. If valid → Live mode enabled
5. UI changes: Badge to "LIVE TRADING" (red)

Live → Demo:
1. User clicks "Switch to Demo Mode"
2. Closes all open positions first (optional)
3. Switches to demo mode
4. UI changes: Badge to "DEMO MODE" (yellow)
```

### Responsible Agents
- **Execution Agent**: Live order placement
- **CoinEx API Adapter**: Exchange communication
- **Risk Management Agent**: Pre-trade validation

### Target Release
Month 4

---

## F-008: Risk Management Controls

### Description
Comprehensive risk management system to protect capital and manage positions.

### Position-Level Controls

**Stop-Loss**
- Types: Percentage-based, ATR-based, Support/resistance
- Execution: Immediate market order when triggered
- Customizable per trade or strategy default

**Take-Profit**
- Fixed % targets
- Multiple targets (scale out: 50% at +3%, 50% at +6%)
- Trail to breakeven after first target

**Trailing Stop**
- Activates after X% profit
- Trails by Y% below peak price
- Locks in profits automatically

### Portfolio-Level Controls

**Max Drawdown Protection**
- Monitor total portfolio drawdown
- Auto-pause trading if threshold hit (e.g., -10%)
- Requires manual resume

**Position Sizing**
- Kelly criterion (advanced)
- Fixed % of capital (simple)
- Risk-based (% of capital at risk per trade)

**Exposure Limits**
- Max concurrent positions: 5 (default)
- Max capital allocation: 80% (20% reserved)
- Per-pair limits (e.g., max 30% in BTC)

### Anomaly Detection

**Divergence Warnings**
- Bearish divergence: Override buy signals
- Bullish divergence: Override sell signals
- Alert user in dashboard

**Data Quality Gates**
- No trades on missing/stale data
- No trades during exchange maintenance
- Volume/liquidity checks before entry

**Volatility Protection**
- Detect extreme volatility (e.g., >10% move in 5 min)
- Widen stops or pause trading
- Alert user

### Responsible Agents
- **Risk Management Agent**: Primary
- **Divergence Detection Agent**: Anomaly detection
- **Data Validation Agent**: Quality gates

### Target Release
Month 3 (basic), Month 7 (advanced)

---

## F-009: Event Bus Architecture

### Description
Redis-based pub/sub messaging system enabling 25 agents to communicate efficiently.

### Technical Specs
- **Technology**: Redis Pub/Sub
- **Message Format**: JSON
- **Topics**: Hierarchical (e.g., `market.btcusdt.tick`, `signal.ma.crossover`)
- **Delivery**: At-least-once
- **Persistence**: Optional (for replay)

### Performance Requirements
- Throughput: >1000 messages/sec
- Latency: <10ms message delivery
- Scalability: 25+ concurrent agents

### Responsible Agents
- **Agent Coordinator**: Orchestration
- **System Architect**: Design
- **DevOps Agent**: Setup and monitoring

### Target Release
Month 1, Sprint 1.2

---

## F-010: 25-Agent System

### Description
Full implementation of all 25 specialized agents working in parallel.

### Agent Categories
(See `.claude/agents/` for full details)

- Coordination (2)
- Product & Design (3)
- Infrastructure (2)
- Data (3)
- Indicators (5)
- Analysis (2)
- Strategy (2)
- Execution (3)
- Interface (2)
- Quality (1)

### Integration Requirements
- All agents implement base agent interface
- Subscribe/publish via event bus
- Health monitoring and heartbeats
- Graceful error handling

### Target Release
Month 1-6 (progressive rollout)

---

## F-011: Automated Testing

### Description
Comprehensive test suite ensuring system reliability.

### Test Types

**Unit Tests** (>80% coverage)
- Test each agent independently
- Mock dependencies
- Fast execution (<1 min total)

**Integration Tests**
- Test agent communication
- Event bus workflows
- End-to-end scenarios

**Acceptance Tests**
- Automated Gherkin scenarios
- QA Agent execution
- Regression detection

**Performance Tests**
- Load testing (1000 msg/sec)
- Latency measurement
- Resource usage monitoring

### Responsible Agents
- **Quality Assurance Agent**: Primary
- **All Development Agents**: Write unit tests

### Target Release
Month 1-6 (ongoing)

---

## F-012: User Documentation

### Description
Comprehensive documentation for users and developers.

### Documentation Types

**User Guide**
- Getting started (15-min setup)
- Strategy selection guide
- Risk management best practices
- Troubleshooting

**API Reference**
- REST endpoints
- WebSocket messages
- Agent interfaces

**Design System Docs**
- Design tokens
- Component library
- Accessibility guidelines

**Video Tutorials**
- Setup walkthrough
- Strategy explanation
- Demo to live transition

### Responsible Agents
- **Product Management Agent**: User guide
- **System Architect Agent**: API docs
- **UX Design Agent**: Design system docs

### Target Release
Month 6 (v1.0 documentation complete)

---

## Feature Dependency Graph

```
F-009 (Event Bus)
  ↓
F-010 (25 Agents) ← F-011 (Testing)
  ↓
F-001 (Market Data) → F-002 (Indicators)
  ↓                      ↓
F-003 (Strategies) ← F-008 (Risk Mgmt)
  ↓                      ↓
F-006 (Demo Mode) → F-007 (Live Mode)
  ↓                      ↓
F-004 (Dashboard) ← F-005 (Strategy UI)
  ↓
F-012 (Documentation)
```

---

**Document Owner**: Product Management Agent
**Contributors**: All 25 Agents
**Last Review**: 2025-11-14
**Status**: Active Development 🚀
