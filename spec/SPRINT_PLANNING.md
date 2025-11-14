# Sprint Planning - FOQCAPAY
**Version**: 1.0
**Last Updated**: 2025-11-14
**Current Sprint**: Sprint 1.2 (Week 3-4)

## 🎯 Project Status: ACTIVE DEVELOPMENT

**Phase**: Month 1 - Foundation
**Mode**: Parallel Team Execution
**Target**: v1.0 with Multi-Pair Trading (Month 6)

---

## Team Structure

### Team Composition (25 Agents = 5 Squads)

#### 🏗️ **Squad Alpha - Infrastructure** (5 agents)
**Mission**: Build core platform foundation
**Lead**: System Architect Agent

**Team Members**:
1. System Architect - Architecture governance
2. Agent Coordinator - Orchestration
3. DevOps/Config - Environment & deployment
4. Logging & Monitoring - Observability
5. Quality Assurance - Testing framework

**Current Sprint Focus**: Event bus, agent framework, CI/CD

---

#### 💾 **Squad Data - Market Intelligence** (4 agents)
**Mission**: Real-time multi-pair market data
**Lead**: Market Data Agent

**Team Members**:
1. Market Data - Multi-pair streaming (BTC, ETH, LINK/USDC)
2. Data Validation - Quality assurance
3. CoinEx API Adapter - Exchange interface
4. Volume Analysis - Liquidity tracking

**Current Sprint Focus**: CoinEx WebSocket for 3+ pairs

---

#### 📊 **Squad Indicators - Technical Analysis** (5 agents)
**Mission**: Real-time indicator calculations
**Lead**: Signal Synthesis Agent

**Team Members**:
1. MA Indicator - Trend analysis
2. RSI Indicator - Momentum
3. MACD Indicator - Reversals
4. Bollinger Bands - Volatility
5. Trend Regime - Market classification

**Current Sprint Focus**: Parallel indicator processing

---

#### ⚡ **Squad Strategy - Trading Logic** (4 agents)
**Mission**: Multi-strategy execution engine
**Lead**: Strategy Orchestrator Agent

**Team Members**:
1. Signal Synthesis - Multi-signal aggregation
2. Strategy Orchestrator - Strategy management
3. Divergence Detection - Pattern recognition
4. Risk Management - Capital protection

**Current Sprint Focus**: First strategy (MA crossover)

---

#### 🎨 **Squad UX - User Experience** (5 agents)
**Mission**: Beautiful, functional dashboard
**Lead**: UX Design Agent

**Team Members**:
1. Product Management - Requirements & vision
2. UX Design - Design system
3. UI Development - Frontend implementation
4. Dashboard - Backend-frontend bridge
5. UX Interaction - User commands

**Current Sprint Focus**: Next.js setup, live price display

---

#### 🔐 **Squad Execution - Trade Management** (2 agents)
**Mission**: Trade execution & tracking
**Lead**: Execution Agent

**Team Members**:
1. Execution - Order placement
2. Trade Lifecycle - Position tracking

**Current Sprint Focus**: Demo mode framework

---

## Sprint Calendar - Month 1

### ✅ Sprint 1.1 (Week 1-2) - COMPLETED
**Theme**: Project Initialization & Spec Foundation

**Completed**:
- ✅ Spec Kit installation
- ✅ 25 agent definitions
- ✅ Comprehensive specifications (PROJECT_SPEC, ROADMAP, INITIATIVES, FEATURES, USER_STORIES)
- ✅ Git repository setup
- ✅ Architecture design

---

### 🚀 Sprint 1.2 (Week 3-4) - **CURRENT SPRINT**
**Theme**: Core Infrastructure & First Integration
**Dates**: Week 3-4 (Starting NOW)
**Goal**: Live multi-pair price display on dashboard

#### Sprint Objectives
1. Backend skeleton operational (FastAPI + Event Bus)
2. Frontend skeleton with live data (Next.js + ShadCN)
3. Multi-pair market data streaming (BTC, ETH, LINK/USDC)
4. First end-to-end integration working

#### Team Assignments

##### 🏗️ Squad Alpha Tasks
**Agent Coordinator & System Architect**:
- [ ] Design event bus topics for multi-pair
- [ ] Create agent base class with lifecycle
- [ ] Setup Redis Pub/Sub infrastructure
- [ ] Define message schemas

**DevOps Agent**:
- [ ] Setup backend Python environment (requirements.txt)
- [ ] Setup frontend Node.js environment (package.json)
- [ ] Create .env.example with CoinEx config
- [ ] Docker Compose for local development
- [ ] CI/CD pipeline (GitHub Actions)

**Logging Agent**:
- [ ] Implement structured logging (JSON format)
- [ ] Create log aggregation setup
- [ ] Health check endpoints

**QA Agent**:
- [ ] Setup pytest framework
- [ ] Setup Jest for frontend
- [ ] First unit tests for agent base class

**Story Points**: 13
**Estimate**: 2 weeks

---

##### 💾 Squad Data Tasks
**Market Data Agent**:
- [ ] **Priority**: Implement CoinEx WebSocket client
- [ ] Subscribe to multiple pairs: BTC/USDC, ETH/USDC, LINK/USDC
- [ ] Parse OHLCV data format
- [ ] Publish tick events to event bus
- [ ] Handle reconnection logic

**CoinEx API Adapter**:
- [ ] Setup CCXT integration
- [ ] Implement read-only API calls (market data)
- [ ] API key management (secure storage)
- [ ] Rate limiting logic

**Data Validation Agent**:
- [ ] Implement data quality checks
- [ ] Detect anomalies (nulls, zeros, stale data)
- [ ] Publish validation events

**Volume Analysis Agent**:
- [ ] Calculate average volume per pair
- [ ] Detect volume spikes

**Story Points**: 13
**Estimate**: 2 weeks

---

##### 📊 Squad Indicators Tasks
**MA Indicator Agent**:
- [ ] Implement SMA calculation (20, 50, 200 periods)
- [ ] Subscribe to price tick events
- [ ] Publish MA values per pair
- [ ] Unit tests with known data

**RSI Indicator Agent**:
- [ ] Implement RSI calculation (14-period)
- [ ] Subscribe to price ticks
- [ ] Publish RSI values
- [ ] Zone detection (oversold/overbought)

**MACD, Bollinger, Trend Regime**:
- [ ] Stub implementations (MVP later)

**Story Points**: 8 (MA + RSI only)
**Estimate**: 2 weeks

---

##### ⚡ Squad Strategy Tasks
**Signal Synthesis Agent**:
- [ ] Framework for receiving indicator signals
- [ ] Basic aggregation logic (collect all signals)
- [ ] Publish aggregated signal events

**Strategy Orchestrator**:
- [ ] Configuration management (which strategies active)
- [ ] Strategy selection framework

**Story Points**: 5 (framework only)
**Estimate**: 2 weeks

---

##### 🎨 Squad UX Tasks
**Product Management Agent**:
- [ ] Refine multi-pair requirements
- [ ] User flow for pair selection UI
- [ ] Define acceptance criteria for Sprint 1.2

**UX Design Agent**:
- [ ] **Priority**: Design token definitions (colors, fonts, spacing)
- [ ] Wireframe for multi-pair dashboard
- [ ] Create component design specs
- [ ] Light/dark theme variables

**UI Development Agent**:
- [ ] **Priority**: Setup Next.js 14 project with TypeScript
- [ ] Install ShadCN UI + Tailwind CSS
- [ ] Implement design tokens as CSS variables
- [ ] Create layout components (Header, Sidebar, Main)
- [ ] Multi-pair selector dropdown
- [ ] Price ticker component (updates in real-time)
- [ ] Basic candlestick chart (Recharts)

**Dashboard Agent**:
- [ ] FastAPI endpoints: GET /api/marketdata?symbol=
- [ ] WebSocket server setup
- [ ] Push price updates to frontend clients

**UX Interaction Agent**:
- [ ] Handle pair selection changes
- [ ] Configuration state management

**Story Points**: 21
**Estimate**: 2 weeks

---

##### 🔐 Squad Execution Tasks
**Execution Agent**:
- [ ] Demo mode framework (no real orders yet)
- [ ] Simulated order structure

**Trade Lifecycle Agent**:
- [ ] Position data model
- [ ] In-memory position tracking

**Story Points**: 3 (framework only)
**Estimate**: 2 weeks

---

#### Sprint 1.2 Definition of Done

**Backend**:
- ✅ FastAPI server running on http://localhost:8000
- ✅ Event bus operational (Redis)
- ✅ Market Data agent streaming 3 pairs (BTC, ETH, LINK)
- ✅ At least 2 indicator agents working (MA, RSI)
- ✅ Health check endpoint: GET /api/health
- ✅ 30% test coverage

**Frontend**:
- ✅ Next.js app running on http://localhost:3000
- ✅ Pair selector dropdown (BTC, ETH, LINK)
- ✅ Live price ticker updates <1s latency
- ✅ Basic chart showing price history
- ✅ Light/dark theme toggle working

**Integration**:
- ✅ End-to-end: CoinEx → Backend → Frontend
- ✅ Real-time price updates visible in UI
- ✅ Multi-pair switching works smoothly

**Acceptance Criteria**:
```gherkin
Scenario: Multi-pair price display
  Given the application is running
  When the user selects "BTC/USDC" from pair dropdown
  Then the price ticker shows live BTC price
  And the chart displays BTC candlesticks
  When the user switches to "ETH/USDC"
  Then the display updates to ETH data within 1 second
```

---

## Sprint 2.1 (Week 5-6) - NEXT
**Theme**: Charting & Indicators
**Goal**: Full dashboard with indicator overlays

**Planned Work**:
- Complete all 5 indicator agents
- Indicator overlays on charts (MA lines, Bollinger Bands)
- RSI and MACD subcharts
- Volume bars
- Enhanced UI (performance metrics panel)

---

## Sprint 2.2 (Week 7-8)
**Theme**: First Strategy End-to-End
**Goal**: Execute first demo trade with MA crossover

**Planned Work**:
- Signal Synthesis logic
- MA crossover strategy implementation
- Demo mode execution
- Trade markers on chart
- Position tracking display

---

## Daily Standup Format

**What did your squad complete yesterday?**
**What will your squad work on today?**
**Any blockers?**

**Example**:
```
Squad Data (Market Data Agent reporting):
✅ Yesterday: Implemented CoinEx WebSocket connection for BTC/USDC
🎯 Today: Add ETH/USDC and LINK/USDC subscriptions
🚧 Blocker: None
```

---

## Team Communication

### Squads Collaborate Via Event Bus
- Squads publish events, others subscribe
- Loose coupling = parallel work
- Example: Data Squad publishes `market.btcusdc.tick`, Indicators Squad subscribes

### Weekly Sync
- **Every Friday**: All squad leads (5 leads) sync progress
- Review metrics: Story points completed, test coverage, blockers
- Plan next sprint

### Documentation
- Each agent documents their interface in `.claude/agents/`
- API contracts in code comments
- Architecture decisions in `docs/ADR/`

---

## Metrics Dashboard

### Sprint 1.2 Progress (Real-Time)

| Squad | Story Points | Completed | In Progress | Blocked |
|-------|--------------|-----------|-------------|---------|
| Alpha | 13 | 0 | 0 | 0 |
| Data | 13 | 0 | 0 | 0 |
| Indicators | 8 | 0 | 0 | 0 |
| Strategy | 5 | 0 | 0 | 0 |
| UX | 21 | 0 | 0 | 0 |
| Execution | 3 | 0 | 0 | 0 |
| **Total** | **63** | **0** | **0** | **0** |

**Target**: 63 points in 2 weeks (Sprint 1.2)
**Velocity**: TBD (first sprint with actual dev)

---

## Risk Register

| Risk | Squad | Probability | Impact | Mitigation |
|------|-------|-------------|--------|------------|
| CoinEx API rate limits | Data | Medium | High | Implement caching, request throttling |
| WebSocket disconnects | Data | High | Medium | Auto-reconnect with exponential backoff |
| Chart performance (multi-pair) | UX | Medium | Medium | Virtualization, debouncing, React.memo |
| Event bus bottleneck | Alpha | Low | High | Load testing early, Redis benchmarking |
| Multi-pair complexity | All | Medium | Medium | Start with 3 pairs, scale gradually |

---

## Multi-Pair Architecture Decisions

### Pair Management
**Decision**: Support 3 pairs in Sprint 1.2, scale to 10+ by Sprint 5
**Rationale**: Prove multi-pair works early, avoid over-engineering

### Data Structure
```typescript
// Event format for multi-pair
{
  "topic": "market.tick",
  "pair": "BTC/USDC",
  "timestamp": 1700000000,
  "data": {
    "price": 30125.50,
    "volume": 1234.56,
    "open": 30100.00,
    "high": 30150.00,
    "low": 30050.00,
    "close": 30125.50
  }
}
```

### Capital Allocation (Multi-Pair)
**Sprint 1.2**: Display only (no trading yet)
**Sprint 4+**: Equal weight (33% each for 3 pairs) or custom allocation via UI

### UI Layout (Multi-Pair)
**Option A**: Tabs (one chart at a time) ← **Chosen for v1.0**
**Option B**: Grid (multiple mini charts) ← v1.1 enhancement

---

## Backlog Grooming

### Sprint 3 Preview (Week 9-10)
- MACD, Bollinger, Volume agents completed
- Multi-strategy framework
- Risk management (stop-loss, take-profit)
- Demo mode trading execution

### Sprint 4 Preview (Week 13-14)
- Live trading mode
- CoinEx order execution
- Multi-pair position tracking
- Emergency stop button

---

## Team Motivation 🚀

**We're building something amazing together!**

- **25 specialized agents** = 25x the productivity
- **Parallel execution** = Faster delivery
- **Multi-pair from day one** = Professional-grade
- **Spec-driven** = Clear direction, less confusion
- **Target**: v1.0 in 6 months with REAL multi-pair trading

**LET'S SHIP IT!** 🔥

---

**Sprint Master**: Agent Coordinator
**Product Owner**: Product Management Agent
**Scrum Master**: System Architect Agent
**Last Updated**: 2025-11-14 (Sprint 1.2 Kickoff)
**Status**: 🚀 **ACTIVE DEVELOPMENT - TEAMS WORKING IN PARALLEL**
