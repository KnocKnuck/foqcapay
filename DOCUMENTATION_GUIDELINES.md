# Documentation Guidelines - FOQCAPAY

**For All 25 Agents/Teams**
**Version**: 1.0
**Last Updated**: 2025-11-14

---

## 📚 Purpose

**Every agent MUST document their work**. Good documentation ensures:
- ✅ Future team members (or AI agents) can understand the code
- ✅ Users can set up and use the system easily
- ✅ Bugs can be debugged faster
- ✅ The system remains maintainable as it grows

---

## 🎯 Documentation Rules

### Rule 1: **Document as You Code**
- Don't wait until the end of sprint
- Write docs alongside implementation
- Update docs when code changes

### Rule 2: **Keep It Simple**
- Use plain language
- Avoid jargon unless necessary
- Include examples

### Rule 3: **Update Existing Docs**
- If you change how something works, update the docs!
- Mark deprecated features clearly
- Remove outdated information

### Rule 4: **Review Before Committing**
- Check that your docs are accurate
- Test any code examples
- Ensure links work

---

## 📝 What Each Agent Must Document

### 1. **Agent Specification** (Already done in `.claude/agents/`)

Each agent has a spec file. Keep it updated!

**Update when**:
- Responsibilities change
- New collaborators added
- Performance metrics change
- New outputs added

**Example**: If MA Indicator Agent adds EMA support, update `.claude/agents/09-ma-indicator.md`

---

### 2. **Code Documentation** (Inline)

#### Python (Backend)
```python
"""
Market Data Agent - Multi-pair price streaming from CoinEx.

This agent connects to CoinEx WebSocket API and streams real-time
price data for multiple trading pairs (BTC/USDC, ETH/USDC, etc.).

Agent: Market Data Agent
Collaborates With: Data Validation, All Indicator Agents
Publishes: market.{pair}.tick events
"""

class MarketDataAgent:
    """
    Streams real-time market data for multiple pairs.

    Attributes:
        pairs (List[str]): Trading pairs to monitor
        ws_client: WebSocket client connection
        event_bus: Event bus for publishing ticks

    Example:
        agent = MarketDataAgent(["BTC/USDC", "ETH/USDC"])
        await agent.start()
    """

    async def subscribe_to_pair(self, pair: str):
        """
        Subscribe to real-time data for a trading pair.

        Args:
            pair: Trading pair (e.g., "BTC/USDC")

        Raises:
            ConnectionError: If WebSocket connection fails

        Publishes:
            Event to topic "market.{pair}.tick" with price data
        """
        # Implementation...
```

#### TypeScript (Frontend)
```typescript
/**
 * PairSelector Component
 *
 * Dropdown for selecting trading pairs (BTC/USDC, ETH/USDC, etc.)
 *
 * @component
 * @example
 * <PairSelector
 *   pairs={["BTC/USDC", "ETH/USDC"]}
 *   onPairChange={(pair) => console.log(pair)}
 * />
 */
export function PairSelector({ pairs, onPairChange }: PairSelectorProps) {
  // Implementation...
}
```

---

### 3. **API Documentation**

**For Backend Endpoints** (Squad Dashboard)

Document in the code AND in `docs/API_REFERENCE.md`:

```python
@router.get("/marketdata")
async def get_market_data(
    symbol: str = Query(..., description="Trading pair (e.g., BTC/USDC)")
):
    """
    Get current market data for a trading pair.

    Args:
        symbol: Trading pair in format "BASE/QUOTE" (e.g., "BTC/USDC")

    Returns:
        MarketDataResponse: Current price, volume, and indicator values

    Example Request:
        GET /api/marketdata?symbol=BTC/USDC

    Example Response:
        {
          "symbol": "BTC/USDC",
          "price": 30125.50,
          "volume_24h": 1234567.89,
          "indicators": {
            "ma_20": 30050.00,
            "rsi_14": 68.5
          }
        }

    Errors:
        404: Pair not found or not configured
        500: Exchange API error
    """
```

---

### 4. **Configuration Documentation**

**When you add new config options**, document in `.env.example` AND code:

```bash
# .env.example

# Trading Pairs (comma-separated)
# Add or remove pairs as needed. System supports unlimited pairs.
# Format: BASE/QUOTE (e.g., BTC/USDC, ETH/USDC)
TRADING_PAIRS=BTC/USDC,ETH/USDC,LINK/USDC
```

---

### 5. **Testing Documentation**

**For each test file**, add a header explaining what's being tested:

```python
"""
Tests for Market Data Agent.

Covers:
- WebSocket connection to CoinEx
- Multi-pair subscription
- Event publishing
- Reconnection logic on disconnect
- Error handling for invalid pairs

Run:
    pytest tests/agents/test_market_data.py -v
"""

def test_subscribe_to_multiple_pairs():
    """Test that agent can subscribe to 3+ pairs simultaneously."""
    # Test implementation...
```

---

### 6. **User-Facing Documentation**

**Squad UX / Product Management**: Maintain these files:

#### `QUICK_START.md`
- 5-10 minute setup guide
- For new users who want to run the bot ASAP
- Screenshots if helpful

#### `docs/USER_GUIDE.md` (Coming soon)
- Complete user manual
- How to configure strategies
- How to interpret charts
- Risk management best practices

#### `docs/TROUBLESHOOTING.md` (Coming soon)
- Common errors and solutions
- FAQ
- How to get help

---

### 7. **Architecture Decisions**

**Squad Alpha / System Architect**: Document major decisions in `docs/ADR/`

**Architecture Decision Record (ADR)** format:

```markdown
# ADR-001: Use Redis for Event Bus

## Status
Accepted

## Context
Need event bus for 25 agents to communicate. Options: Redis, RabbitMQ, Kafka.

## Decision
Use Redis Pub/Sub for event bus.

## Rationale
- Simple setup (single dependency)
- Low latency (<10ms)
- Sufficient throughput (1000+ msg/sec)
- Good Python async support
- Familiar to team

## Consequences
**Positive**:
- Fast development
- Easy local testing
- Low resource usage

**Negative**:
- No message persistence by default (not needed for real-time ticks)
- Limited to single Redis instance (can add cluster later if needed)

## Alternatives Considered
- RabbitMQ: More complex, overkill for our use case
- Kafka: High throughput but complex setup, unnecessary for v1.0
```

Save as `docs/ADR/001-redis-event-bus.md`

---

## 📂 Documentation Structure

```
foqcapay/
├── README.md                    # ✅ Project overview (already great!)
├── QUICK_START.md              # 🆕 YOU'LL CREATE THIS
├── CONTRIBUTING.md             # Coming in Sprint 6
├── .claude/
│   ├── README.md               # ✅ Agent coordination guide
│   └── agents/                 # ✅ Agent specifications (keep updated!)
├── spec/                        # ✅ All specs (keep updated!)
│   ├── PROJECT_SPEC.md
│   ├── SPRINT_PLANNING.md      # Update weekly!
│   └── ...
├── docs/
│   ├── API_REFERENCE.md        # 🆕 Squad Dashboard will create
│   ├── USER_GUIDE.md           # 🆕 Squad UX will create (Sprint 6)
│   ├── TROUBLESHOOTING.md      # 🆕 Squad UX will create (Sprint 6)
│   ├── DEVELOPMENT.md          # 🆕 Squad Alpha will create
│   ├── DESIGN_SYSTEM.md        # 🆕 Squad UX will create
│   └── ADR/                    # Architecture decision records
│       ├── 001-redis-event-bus.md
│       ├── 002-multi-pair-support.md
│       └── ...
├── backend/
│   ├── README.md               # 🆕 Backend setup guide
│   └── [All files have docstrings!]
└── frontend/
    ├── README.md               # 🆕 Frontend setup guide
    └── [All components have JSDoc!]
```

---

## 🔄 Documentation Update Workflow

### When You Make a Change:

1. **Update inline docs** (docstrings, comments)
2. **Update relevant spec files** (if agent responsibilities changed)
3. **Update API docs** (if endpoints changed)
4. **Update SPRINT_PLANNING.md** (mark tasks complete)
5. **Create ADR** (if architecture decision made)
6. **Update QUICK_START.md** (if setup process changed)

### Weekly (Friday):

**Squad Leads Review**:
- Is documentation up to date?
- Are there broken links?
- Are examples still accurate?
- Do we need new docs?

**Product Management Agent** tracks documentation gaps in backlog.

---

## ✅ Documentation Checklist

Before marking a task "Done", verify:

- [ ] Code has docstrings/JSDoc comments
- [ ] Complex logic has inline comments explaining "why"
- [ ] Agent spec file updated (if needed)
- [ ] API docs updated (if endpoint changed)
- [ ] Tests documented (what they test, how to run)
- [ ] SPRINT_PLANNING.md task marked complete
- [ ] README or QUICK_START updated (if setup changed)
- [ ] ADR created (if architecture decision)
- [ ] Examples tested and work

---

## 📊 Documentation Quality Metrics

**Target by v1.0**:
- ✅ 100% of public functions have docstrings
- ✅ 100% of API endpoints documented
- ✅ 100% of agents have up-to-date spec files
- ✅ User guide complete
- ✅ Quick start tested by new user (<15 min setup)

**Quality Assurance Agent** will monitor these metrics.

---

## 🎓 Examples of Good Documentation

### Example 1: Function with Clear Docs
```python
async def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI) for a price series.

    RSI is a momentum oscillator ranging from 0-100. Values above 70
    indicate overbought conditions, below 30 indicate oversold.

    Args:
        prices: List of closing prices (oldest first)
        period: Number of periods for calculation (default: 14)

    Returns:
        float: RSI value between 0 and 100

    Raises:
        ValueError: If prices has fewer than (period + 1) elements

    Example:
        >>> prices = [30000, 30100, 30050, 30150, ...]
        >>> rsi = await calculate_rsi(prices, period=14)
        >>> print(f"RSI: {rsi:.2f}")
        RSI: 68.50

    Reference:
        https://www.investopedia.com/terms/r/rsi.asp
    """
```

### Example 2: Component with Props Documented
```typescript
interface PairSelectorProps {
  /** List of available trading pairs */
  pairs: string[];

  /** Currently selected pair */
  selectedPair?: string;

  /** Callback when user selects a different pair */
  onPairChange: (pair: string) => void;

  /** Optional CSS class name */
  className?: string;
}

/**
 * Dropdown selector for choosing trading pairs.
 *
 * Displays available pairs with visual badges and allows
 * switching between them. Updates are handled via callback.
 */
export function PairSelector({
  pairs,
  selectedPair,
  onPairChange,
  className
}: PairSelectorProps) {
  // ...
}
```

---

## 🚫 Documentation Anti-Patterns (Avoid These!)

### ❌ BAD: Obvious Comments
```python
# Increment i by 1
i = i + 1
```

### ✅ GOOD: Explaining "Why"
```python
# Skip first price as RSI requires at least 2 periods for gain/loss
i = i + 1
```

---

### ❌ BAD: Outdated Docs
```python
def process_data(data):
    """Processes BTC data only."""  # WRONG! Now handles multiple pairs
    for pair in data.keys():
        # ...
```

### ✅ GOOD: Accurate Docs
```python
def process_data(data):
    """
    Process market data for all configured trading pairs.

    Handles BTC/USDC, ETH/USDC, LINK/USDC, and any future pairs.
    """
```

---

### ❌ BAD: No Examples
```python
def configure_strategy(name, params):
    """Configure a trading strategy."""
```

### ✅ GOOD: With Examples
```python
def configure_strategy(name: str, params: dict) -> Strategy:
    """
    Configure a trading strategy with parameters.

    Example:
        >>> strategy = configure_strategy("scalping", {
        ...     "timeframe": "1m",
        ...     "stop_loss_pct": 0.3,
        ...     "take_profit_pct": 0.5
        ... })
    """
```

---

## 🎯 Action Items for Each Squad

### 🏗️ Squad Alpha (Infrastructure)
- [ ] Create `docs/DEVELOPMENT.md` - Developer setup guide
- [ ] Create ADR for event bus decision
- [ ] Create ADR for multi-pair architecture
- [ ] Document agent base class thoroughly

### 💾 Squad Data (Market Intelligence)
- [ ] Document CoinEx API integration in code
- [ ] Create ADR for WebSocket vs REST choice
- [ ] Add examples to Market Data Agent spec

### 📊 Squad Indicators (Technical Analysis)
- [ ] Document all indicator calculations with formulas
- [ ] Add references to Investopedia or TA-Lib docs
- [ ] Include example inputs/outputs in tests

### ⚡ Squad Strategy (Trading Logic)
- [ ] Document strategy selection logic clearly
- [ ] Explain conflict resolution algorithm
- [ ] Document each pre-configured strategy fully

### 🎨 Squad UX (User Experience)
- [ ] Create `docs/DESIGN_SYSTEM.md` - Design tokens & components
- [ ] Document all React components with examples
- [ ] Keep QUICK_START.md updated with UI changes
- [ ] Create USER_GUIDE.md (Sprint 6)

### 🔐 Squad Execution (Trade Management)
- [ ] Document order execution flow with diagrams
- [ ] Explain demo vs live mode clearly
- [ ] Document all risk management rules

---

## 📅 Documentation Milestones

**Sprint 1.2** (Current):
- ✅ DOCUMENTATION_GUIDELINES.md (this file)
- ✅ QUICK_START.md
- ✅ Inline docs for all new code

**Sprint 2-3**:
- API_REFERENCE.md (Dashboard Agent)
- DEVELOPMENT.md (System Architect)
- ADRs for major decisions

**Sprint 6** (v1.0):
- USER_GUIDE.md complete
- TROUBLESHOOTING.md
- Video tutorials (optional)

---

## 💡 Tips for Great Documentation

1. **Write for your future self** - You'll forget why you did something!
2. **Use diagrams** - A picture is worth 1000 words
3. **Link to related docs** - Help readers navigate
4. **Keep it DRY** - Don't repeat yourself across docs
5. **Test your examples** - Broken examples are worse than no examples
6. **Get feedback** - Ask someone to try your QUICK_START

---

## 🤝 Documentation Review Process

**Before Pull Request**:
1. Author self-reviews documentation
2. Runs documentation checklist
3. Tests any code examples

**During Code Review**:
- Reviewer checks documentation quality
- Confirms examples work
- Suggests improvements

**Product Management Agent** ensures docs meet user needs.

---

## 📞 Questions?

If you're unsure what to document:
1. Check this guide first
2. Look at examples from other agents
3. Ask in team standup
4. When in doubt, **document it!** (better to have too much than too little)

---

**Remember**: Good documentation is a sign of professional software.
**Let's make FOQCAPAY's docs world-class!** 📚✨

---

**Document Owner**: Product Management Agent, System Architect Agent
**Maintained By**: All 25 Agents
**Last Updated**: 2025-11-14 (Sprint 1.2)
**Status**: 📚 **ACTIVE - All teams must follow**
