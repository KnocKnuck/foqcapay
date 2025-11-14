# User Stories - FOQCAPAY

**Version**: 1.0
**Last Updated**: 2025-11-14

## Overview

User stories capture the needs of our two primary personas: **Alex** (experienced trader) and **Nina** (cautious learner). Each story follows the format:

> **As a** [persona]
> **I want** [feature/capability]
> **So that** [benefit/value]

Stories are prioritized using MoSCoW: **Must**, **Should**, **Could**, **Won't** (for v1.0)

---

## Story Index

| ID | Title | Persona | Priority | Sprint | Status |
|----|-------|---------|----------|--------|--------|
| US-001 | Real-time market dashboard | Both | Must | 1.2 | Planned |
| US-002 | Automated strategy execution | Both | Must | 2.2 | Planned |
| US-003 | Risk-free demo mode | Nina | Must | 2.2 | Planned |
| US-004 | Clear trade signals | Both | Must | 2.1 | Planned |
| US-005 | Easy mode switching | Both | Must | 4.1 | Planned |
| US-006 | Automatic risk management | Alex | Must | 3.2 | Planned |
| US-007 | Strategy customization | Alex | Should | 5.2 | Planned |
| US-008 | Customizable UI | Both | Should | 5.1 | Planned |
| US-009 | Select trading style | Both | Must | 5.1 | Planned |
| US-010 | Understand strategy performance | Nina | Should | 5.2 | Planned |
| US-011 | Multi-pair trading | Alex | Could | 12.1 | Future |
| US-012 | Mobile access | Both | Won't | - | v2.0 |

---

## US-001: Real-Time Market Dashboard

**As a** trader (Alex or Nina)
**I want to** see real-time market data and technical indicators on a single dashboard
**So that** I can quickly assess market conditions and my bot's status without using multiple tools

### Persona
Both Alex and Nina

### Priority
**Must Have** (Core feature for v1.0)

### Related Features
- F-001: Real-Time Market Data
- F-002: Technical Indicators
- F-004: Real-Time Dashboard

### Acceptance Criteria

```gherkin
Scenario: Dashboard displays live price data
  Given the user opens the dashboard
  When the Market Data agent fetches new price updates for BTC/USDT
  Then the price chart updates within 1 second
  And the current price is displayed prominently
  And the timestamp shows the latest update time

Scenario: Dashboard displays all technical indicators
  Given the dashboard is showing BTC/USDT chart
  When all indicator agents publish their values
  Then the chart shows 20, 50, and 200 period moving average lines
  And the RSI subchart shows the current RSI value (e.g., "RSI: 68")
  And the MACD chart shows MACD line, signal line, and histogram
  And the Bollinger Bands overlay shows upper, middle, and lower bands
  And volume bars are displayed below the price chart
  And all values update in real-time (<1s latency)
```

### Tasks
- [ ] Setup Next.js frontend with ShadCN UI
- [ ] Integrate Recharts for candlestick charting
- [ ] Implement WebSocket client for real-time updates
- [ ] Create indicator overlay components
- [ ] Add current price ticker
- [ ] Test with live CoinEx data
- [ ] Performance optimization (60fps rendering)

### Estimate
13 story points (Sprint 1.2 + 2.1)

### Target Sprint
Sprint 1.2 (basic), Sprint 2.1 (complete)

### Status
Planned

---

## US-002: Automated Strategy Execution

**As a** trader
**I want** the system to execute trades automatically based on proven strategies
**So that** I can capitalize on opportunities 24/7, even when I'm not actively trading

### Persona
Both Alex and Nina

### Priority
**Must Have**

### Related Features
- F-003: Pre-Configured Strategies
- F-006: Demo Mode Trading
- F-007: Live Mode Trading

### Acceptance Criteria

```gherkin
Scenario: MA crossover strategy generates buy signal
  Given the bot is running in Demo mode
  And currently not in any position for BTC/USDT
  And the 50-period MA has just crossed above the 200-period MA
  When the MA Indicator agent detects the golden cross
  And the Signal Synthesis agent confirms the signal
  Then the Strategy Orchestrator approves the trade
  And the Execution agent creates a simulated buy order
  And the dashboard shows a green arrow at the entry point
  And the position is tracked in "Open Positions"

Scenario: Multiple strategies run simultaneously
  Given Scalping and Swing strategies are both active
  When both generate signals for different pairs
  Then the system executes both trades independently
  And tracks each position separately
  And shows which strategy triggered each trade
```

### Tasks
- [ ] Implement MA Indicator Agent
- [ ] Implement Signal Synthesis Agent
- [ ] Implement Strategy Orchestrator
- [ ] Implement Execution Agent (demo mode)
- [ ] Create trade tracking in UI
- [ ] Add strategy attribution to trades
- [ ] Test multi-strategy scenarios

### Estimate
21 story points (Sprints 2.2, 3.1, 3.2)

### Target Sprint
Sprint 2.2 (first strategy), Sprint 3.1 (multi-strategy)

### Status
Planned

---

## US-003: Risk-Free Demo Mode

**As a** cautious learner (Nina)
**I want to** run the system in a demo/simulated mode initially
**So that** I can test strategies and confirm everything works correctly without risking real money

### Persona
Nina (primary), also valuable for Alex

### Priority
**Must Have**

### Related Features
- F-006: Demo Mode Trading

### Acceptance Criteria

```gherkin
Scenario: Demo mode executes simulated trades
  Given the bot is in Demo mode
  And virtual balance is $10,000
  When a buy signal is generated for BTC at $30,000
  Then a simulated order is created for $1,000 worth (0.0333 BTC)
  And the virtual balance decreases to $9,000
  And the position shows in "Open Positions"
  And no real API call is made to CoinEx
  And no real funds are affected

Scenario: Demo mode badge is visible
  Given the bot is in Demo mode
  When the user views the dashboard
  Then a "DEMO MODE" badge is prominently displayed
  And the virtual balance shows "Virtual: $10,000"
  And all trades have a "DEMO" indicator

Scenario: Reset virtual portfolio
  Given the bot is in Demo mode
  And virtual balance is $8,500 (after some trades)
  When the user clicks "Reset Virtual Portfolio"
  Then the balance resets to $10,000
  And all demo trade history is cleared
  And a confirmation message appears
```

### Tasks
- [ ] Implement simulated order execution logic
- [ ] Create virtual portfolio management
- [ ] Add demo mode badge to UI
- [ ] Implement portfolio reset functionality
- [ ] Prevent real API calls in demo mode
- [ ] Add demo trade history view

### Estimate
8 story points

### Target Sprint
Sprint 2.2

### Status
Planned

---

## US-004: Clear Trade Signals

**As a** trader
**I want** clear visual feedback on the dashboard when a trade signal occurs
**So that** I know which strategy triggered and why, helping me trust and understand the bot's decisions

### Persona
Both (especially Nina for learning)

### Priority
**Must Have**

### Related Features
- F-004: Real-Time Dashboard

### Acceptance Criteria

```gherkin
Scenario: Buy signal is marked on chart
  Given a buy signal is generated by RSI strategy
  When the signal is approved by Strategy Orchestrator
  Then a green upward arrow appears on the chart at the signal price
  And a tooltip shows: "RSI Buy Signal: RSI = 28 (Oversold)"
  And the signal appears in the "Signals" log panel
  And the entry includes timestamp and strategy name

Scenario: Trade reasoning is explained
  Given a trade was executed 5 minutes ago
  When the user clicks on the trade marker on the chart
  Then a popup shows:
    """
    Trade: BUY 0.5 BTC at $30,000
    Strategy: Intraday
    Reasoning:
    - MA 20 crossed above MA 50 (Golden Cross)
    - RSI: 55 (Neutral, momentum building)
    - Volume: +25% above average (Confirmation)
    - MACD: Positive histogram (Bullish)
    """
  And the user understands why the trade was made
```

### Tasks
- [ ] Implement signal markers on chart
- [ ] Create signal log panel
- [ ] Add trade reasoning display
- [ ] Design tooltip components
- [ ] Color-code signals (green=buy, red=sell)
- [ ] Add strategy attribution

### Estimate
5 story points

### Target Sprint
Sprint 2.1

### Status
Planned

---

## US-005: Easy Mode Switching

**As a** trader
**I want to** easily switch between demo mode and live trading mode
**So that** once I'm confident, I can start real trades, and similarly pause real trading if needed with minimal friction

### Persona
Both Alex and Nina

### Priority
**Must Have**

### Related Features
- F-006: Demo Mode
- F-007: Live Mode

### Acceptance Criteria

```gherkin
Scenario: User switches from demo to live mode
  Given the bot is in Demo mode
  And CoinEx API keys are configured
  When the user clicks "Switch to Live Mode"
  And confirms the warning "You will trade with real funds. Continue?"
  Then the system validates API credentials
  And if valid, switches to Production mode
  And the UI displays "LIVE TRADING" badge in red
  And a confirmation message appears: "Live trading enabled. Be careful!"
  And the balance now shows real CoinEx balance

Scenario: User switches from live to demo mode
  Given the bot is in Live mode
  And has 2 open positions
  When the user clicks "Switch to Demo Mode"
  Then the system asks: "Close open positions first? (Recommended)"
  And if user confirms, closes all positions
  And switches to Demo mode
  And UI displays "DEMO MODE" badge in yellow
  And balance shows virtual balance
```

### Tasks
- [ ] Implement mode switching logic in UX Interaction Agent
- [ ] Create confirmation dialogs
- [ ] Validate API credentials on live mode activation
- [ ] Add mode indicator badge to UI
- [ ] Handle open positions on mode switch
- [ ] Update balance display based on mode

### Estimate
8 story points

### Target Sprint
Sprint 4.1

### Status
Planned

---

## US-006: Automatic Risk Management

**As an** experienced trader (Alex)
**I want** the system to manage risk automatically (stops, take-profit, trailing stops)
**So that** my downside is protected and profits are locked in without manual intervention

### Persona
Alex (primary), also protects Nina

### Priority
**Must Have**

### Related Features
- F-008: Risk Management Controls

### Acceptance Criteria

```gherkin
Scenario: Stop-loss triggers automatically
  Given an open long position: BTC at $30,000, size 0.5 BTC
  And stop-loss set at -5% = $28,500
  When the price falls to $28,500
  Then the Risk Management agent detects the trigger
  And the Execution agent immediately sends a sell order
  And the position is closed at ~$28,500
  And the trade history shows "Stopped Out -5%"
  And the loss is recorded as -$750

Scenario: Trailing stop locks in profits
  Given an open long position: entry $30,000, trailing stop 3%
  When the price rises to $31,500 (new peak)
  Then the trailing stop adjusts to $30,555 (3% below peak)
  And the new stop level is displayed on chart and position panel
  When the price later falls to $30,555
  Then the position is automatically closed
  And the profit is locked in: ~$277.50 (+1.85%)

Scenario: Max drawdown protection activates
  Given the starting capital was $10,000
  And max drawdown is set to 10%
  When total losses reach $1,000 (10% drawdown)
  Then the Risk Management agent emits "Max Drawdown Reached" event
  And the Strategy Orchestrator pauses all new trades
  And the UI shows alert: "Trading Halted - Max Drawdown (10%) Reached"
  And the user must manually resume trading after reviewing
```

### Tasks
- [ ] Implement Risk Management Agent
- [ ] Add stop-loss monitoring and execution
- [ ] Implement trailing stop logic
- [ ] Add take-profit targets
- [ ] Implement max drawdown tracking
- [ ] Create risk alerts in UI
- [ ] Add manual trading resume after halt

### Estimate
13 story points

### Target Sprint
Sprint 3.2

### Status
Planned

---

## US-007: Strategy Customization

**As an** experienced trader (Alex)
**I want to** customize or toggle strategies from the UI (e.g., turn off a strategy or adjust a threshold)
**So that** I have control over the bot's behavior and can experiment with different approaches in real time

### Persona
Alex (advanced feature)

### Priority
**Should Have**

### Related Features
- F-005: Strategy Selection UI

### Acceptance Criteria

```gherkin
Scenario: User disables a specific strategy
  Given the RSI strategy is currently active
  When the user navigates to Strategy Settings
  And toggles RSI strategy to "Off"
  Then the Strategy Orchestrator stops routing RSI signals
  And the RSI indicator grays out in the UI
  And a message shows: "RSI strategy disabled"
  And no RSI-based trades are executed

Scenario: User adjusts stop-loss percentage
  Given the current stop-loss default is 2%
  When the user changes it to 3% in Risk Settings
  And clicks "Save"
  Then the Risk Management agent updates the parameter
  And all new trades use 3% stop-loss
  And existing trades remain with their original stop-loss
  And the setting is persisted locally
```

### Tasks
- [ ] Create Strategy Settings UI panel
- [ ] Implement enable/disable toggle for each strategy
- [ ] Add risk parameter adjustment controls (sliders)
- [ ] Persist settings to local storage
- [ ] Propagate config changes to agents via event bus
- [ ] Add confirmation for significant changes

### Estimate
8 story points

### Target Sprint
Sprint 5.2

### Status
Planned

---

## US-008: Customizable UI

**As a** trader
**I want** the interface to be customizable (themes, layout density) and responsive
**So that** I can comfortably use it in different environments (bright office, dark home setup, small laptop screen) without straining

### Persona
Both Alex and Nina

### Priority
**Should Have**

### Related Features
- F-004: Real-Time Dashboard

### Acceptance Criteria

```gherkin
Scenario: User switches to dark theme
  Given the dashboard is in light theme
  When the user clicks the theme toggle (moon icon)
  Then the UI instantly switches to dark theme
  And all components use dark design tokens
  And charts switch to dark backgrounds with light text
  And the preference is saved locally
  And on next login, dark theme is remembered

Scenario: User enables compact mode
  Given the dashboard is in normal density mode
  When the user toggles "Compact Mode" in settings
  Then font sizes reduce slightly
  And padding/spacing decreases
  And more data fits on screen
  And readability remains acceptable
```

### Tasks
- [ ] Implement theme toggle (light/dark)
- [ ] Define dark theme design tokens
- [ ] Create compact mode CSS adjustments
- [ ] Persist theme preference in localStorage
- [ ] Test accessibility in both themes
- [ ] Ensure chart themes switch correctly

### Estimate
5 story points

### Target Sprint
Sprint 5.1

### Status
Planned

---

## US-009: Select Trading Style

**As a** trader
**I want to** select a pre-configured trading style (Scalping, Intraday, Swing)
**So that** the bot trades according to my preferred timeframe and risk tolerance without complex configuration

### Persona
Both Alex and Nina

### Priority
**Must Have** (Differentiating feature)

### Related Features
- F-003: Pre-Configured Strategies
- F-005: Strategy Selection UI

### Acceptance Criteria

```gherkin
Scenario: User selects Scalping strategy
  Given the user opens Strategy Selection
  When they click on "Scalping ⚡" card
  Then a preview shows:
    """
    Scalping Strategy
    Timeframe: 1-5 minutes
    Typical hold: 5-15 minutes
    Target: +0.5% to +1%
    Stop-loss: -0.3%
    Best for: Quick trades, high liquidity pairs
    Risk: Medium-High (frequent trades)
    Backtested win rate: 58%
    """
  And the user clicks "Activate"
  And the bot switches to 1-minute timeframe
  And uses EMA 9/21 with tight stops
  And the dashboard shows "Active: Scalping ⚡"

Scenario: User compares strategy performance
  Given the user has historical data for all 3 strategies
  When they view the Strategy Comparison panel
  Then they see a table:
    | Strategy | Trades | Win Rate | Avg Profit | Max DD |
    | Scalping |   145  |   58%    |  +0.6%     | -2.1%  |
    | Intraday |    42  |   64%    |  +2.3%     | -4.5%  |
    | Swing    |    12  |   67%    |  +8.1%     | -6.2%  |
  And they can make an informed decision
```

### Tasks
- [ ] Define strategy configurations (Scalping, Intraday, Swing)
- [ ] Create strategy selection UI (cards or dropdown)
- [ ] Implement strategy preview with details
- [ ] Add strategy activation logic
- [ ] Create strategy comparison dashboard
- [ ] Backtest each strategy and display results
- [ ] Add strategy badge to main dashboard

### Estimate
13 story points

### Target Sprint
Sprint 5.1 (UI), Sprint 5.2 (strategies implemented)

### Status
Planned

---

## US-010: Understand Strategy Performance

**As a** cautious learner (Nina)
**I want to** see explanations of why a strategy performed well or poorly
**So that** I can learn trading principles and build confidence before risking real money

### Persona
Nina (primary), educational value

### Priority
**Should Have**

### Related Features
- F-003: Strategies
- F-004: Dashboard

### Acceptance Criteria

```gherkin
Scenario: View trade post-mortem
  Given a trade was closed with -2% loss
  When Nina clicks on the trade in Trade History
  Then a detailed view shows:
    """
    Trade Analysis: SELL 0.5 BTC at $29,400 (Loss: -$300, -2%)

    Entry Reasoning:
    - MA 50 crossed above MA 200 (Golden Cross) ✓
    - RSI: 52 (Neutral) ✓
    - Volume: +15% above average ✓

    What Went Wrong:
    - Bearish divergence appeared shortly after entry
      (Price made higher high, RSI made lower high)
    - Market regime shifted from Trending to Choppy
    - Stop-loss hit at -2% as planned (risk managed)

    Lesson: Watch for divergences before entry. Consider
    waiting for MACD confirmation in addition to MA cross.
    """
  And Nina learns from the experience

Scenario: View strategy learning curve
  Given Nina has been using Swing strategy in demo mode for 2 weeks
  When she views "My Progress" dashboard
  Then she sees:
    - Win rate trend (45% → 58% over time)
    - Common mistakes identified
    - Suggested improvements
    - "Readiness Score" for live trading: 72/100
```

### Tasks
- [ ] Create trade post-mortem analysis feature
- [ ] Implement "What went wrong" logic
- [ ] Add learning curve tracking
- [ ] Create "My Progress" dashboard for Nina
- [ ] Compute readiness score
- [ ] Add educational tooltips throughout UI

### Estimate
13 story points (nice-to-have enhancements)

### Target Sprint
Sprint 6.1+ (post-v1.0 polish)

### Status
Planned (Could defer to v1.1)

---

## US-011: Multi-Pair Trading

**As an** experienced trader (Alex)
**I want to** trade multiple cryptocurrency pairs simultaneously
**So that** I can diversify my portfolio and capitalize on opportunities across different markets

### Persona
Alex (advanced feature)

### Priority
**Could Have** (v1.1 or later)

### Related Features
- F-003: Strategies (multi-pair support)

### Acceptance Criteria

```gherkin
Scenario: Monitor multiple pairs
  Given Alex has activated multi-pair mode
  When he selects BTC/USDT, ETH/USDT, and SOL/USDT
  Then the dashboard shows 3 mini charts
  And each pair has independent strategy execution
  And capital is allocated per pair (e.g., 33% each)

Scenario: Independent risk management per pair
  Given Alex is trading BTC and ETH simultaneously
  When BTC position hits stop-loss
  Then only BTC position is closed
  And ETH position continues independently
  And max drawdown is calculated across both
```

### Tasks
- [ ] Extend Market Data agent for multiple pairs
- [ ] Update Strategy Orchestrator for multi-pair logic
- [ ] Create multi-chart UI layout
- [ ] Implement per-pair capital allocation
- [ ] Aggregate risk metrics across pairs

### Estimate
21 story points

### Target Sprint
Sprint 12.1 (Q4 2025)

### Status
Future (v1.1 or v2.0)

---

## US-012: Mobile Access

**As a** trader on the go
**I want to** access the dashboard and monitor trades from my mobile device
**So that** I can stay informed even when away from my computer

### Persona
Both Alex and Nina

### Priority
**Won't Have** (v1.0) → v2.0 consideration

### Rationale
- v1.0 focuses on desktop/laptop experience
- Mobile responsive design included, but native app deferred
- Progressive Web App (PWA) could be interim solution in v1.2

### Target Sprint
v2.0 roadmap

### Status
Deferred

---

## Story Prioritization Summary

### Must Have (v1.0)
- US-001: Real-time market dashboard ✓
- US-002: Automated strategy execution ✓
- US-003: Risk-free demo mode ✓
- US-004: Clear trade signals ✓
- US-005: Easy mode switching ✓
- US-006: Automatic risk management ✓
- US-009: Select trading style ✓

**Total**: 7 must-have stories

### Should Have (v1.0 or v1.1)
- US-007: Strategy customization
- US-008: Customizable UI
- US-010: Understand strategy performance

**Total**: 3 should-have stories

### Could Have (v1.1+)
- US-011: Multi-pair trading

### Won't Have (v1.0)
- US-012: Mobile access (v2.0)

---

## Story Dependencies

```
US-001 (Dashboard)
  ↓
US-004 (Signals) → US-002 (Strategies) → US-009 (Trading Styles)
  ↓                     ↓
US-003 (Demo) → US-005 (Mode Switch) → US-007 (Customization)
  ↓                     ↓
US-006 (Risk Mgmt) → US-008 (UI Customization)
  ↓
US-010 (Performance Understanding)
  ↓
US-011 (Multi-Pair) [v1.1]
```

---

**Document Owner**: Product Management Agent
**Contributors**: UX Design, UI Development, All Agents
**Last Review**: 2025-11-14
**Status**: Active Sprint Planning 🚀
