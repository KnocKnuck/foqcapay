# Crypto Trading Bot - Acceptance Criteria
# Gherkin-style scenarios for all user stories and features

Feature: Unified Dashboard UI
  As a trader
  I want to see real-time market data and technical indicators on a single dashboard
  So that I can quickly assess market conditions and bot status without using multiple tools

  Background:
    Given the application is connected to CoinEx
    And the backend agents are running
    And the event bus is operational

  Scenario: Dashboard displays live price data
    Given the user opens the dashboard
    When the Market Data agent fetches new price updates for BTC/USDT
    Then the price chart updates within 1 second
    And the current price is displayed prominently
    And the timestamp shows the latest update time

  Scenario: Dashboard displays multiple technical indicators
    Given the dashboard is displaying BTC/USDT chart
    When all indicator agents publish their values
    Then the chart shows 20, 50, and 200 period moving average lines
    And the RSI subchart shows the current RSI value
    And the MACD chart shows MACD line, signal line, and histogram
    And the Bollinger Bands overlay shows upper, middle, and lower bands
    And volume bars are displayed below the price chart

  Scenario: Indicator values update in real-time
    Given the application is connected to CoinEx in Demo mode with a network connection
    When the Market Data agent fetches new price updates for the selected trading pair
    Then the Dashboard UI chart updates within 1 second with the latest price candle
    And all active indicator overlays (MA, RSI, MACD, Bollinger, Volume) recalculate and render their new values
    And the current values of indicators are displayed in the UI's indicator panel
    And the indicators show their status (e.g., "RSI: 68 (neutral)")

  Scenario: Theme toggle switches between light and dark modes
    Given the dashboard is currently displayed in light theme
    When the user toggles the theme switch in the UI
    Then the application applies the dark theme design tokens instantly across all components
    And background color changes to dark (#121212)
    And text color changes to light (#E4E4E4)
    And all UI elements remain clearly visible and accessible
    And charts switch to dark style with bright grid and text
    And the user's theme preference is saved locally
    And on app restart, the dark theme is remembered

  Scenario: Responsive design adapts to screen size
    Given the dashboard is open on a desktop (1920x1080)
    When the user resizes the window to tablet size (768x1024)
    Then the layout adjusts to fit the smaller screen
    And all critical information remains visible
    And charts resize proportionally
    And panels stack vertically if needed
    And no horizontal scrolling is required

  Scenario: Compact view mode for dense data display
    Given the dashboard is in normal view mode
    When the user toggles compact view
    Then font sizes reduce slightly
    And spacing between elements decreases
    And more data fits on screen
    And readability remains acceptable
    And the setting is remembered

---

Feature: Live Market Data Integration
  As a trader
  I need real-time market data from CoinEx
  So that my trading decisions are based on current market conditions

  Scenario: System connects to CoinEx market data
    Given the application starts
    And CoinEx API credentials are configured
    When the Market Data agent initializes
    Then a connection to CoinEx WebSocket is established
    And market data stream starts for the configured trading pair
    And the connection status shows "Connected" in the UI

  Scenario: Market data updates flow to indicators
    Given the Market Data agent is streaming BTC/USDT data
    When a new price tick arrives from CoinEx
    Then the Market Data agent publishes a tick event to the event bus
    And all indicator agents receive the tick within 50ms
    And indicators begin recalculation immediately

  Scenario: Data validation catches corrupt data
    Given the system is receiving normal market data
    When the Market Data agent receives a price of zero or null
    Then the Data Validation agent detects the anomaly
    And publishes a data quality alert event
    And the Dashboard shows "Data feed error" within 2 seconds
    And no trading signals are generated during the error
    And the system attempts to reconnect

  Scenario: Automatic reconnection on network failure
    Given the system is running and receiving data normally
    When the CoinEx API becomes unreachable or returns an error
    Then the Data Validation agent detects missing updates and flags an error event
    And the Dashboard UI's status bar shows an alert within 2 seconds
    And the system automatically retries the connection using exponential backoff
    And no trades are executed during the outage
    And once data resumes, normal operation continues

  Scenario: Multiple timeframe support
    Given the dashboard is showing 1-hour candles
    When the user selects "5 minute" timeframe
    Then the chart reloads with 5-minute candles
    And indicators recalculate for the 5-minute timeframe
    And the chart displays at least 100 candles of history

---

Feature: Multi-Strategy Trading Engine
  As a trader
  I want multiple proven strategies running simultaneously
  So that I can capitalize on different market opportunities automatically

  Scenario: Moving Average crossover generates buy signal
    Given the bot is running in Demo mode
    And currently not in any position for BTC/USDT
    And the 50-period MA has just crossed above the 200-period MA
    When the MA Indicator agent detects the crossover
    Then it publishes a "Golden Cross Buy Signal" event
    And the signal includes the cross price and timestamp
    And the signal is displayed on the dashboard chart

  Scenario: RSI oversold generates buy signal
    Given the bot is in Demo mode with no open BTC/USDT position
    And the 14-period RSI drops below 30
    When the RSI Indicator agent detects oversold condition
    Then it publishes an "RSI Oversold Buy Signal" event
    And the signal includes the RSI value
    And the signal is shown in the dashboard's signals panel

  Scenario: MACD crossover generates buy signal
    Given the bot is monitoring BTC/USDT
    And the MACD line crosses above the signal line
    When the MACD Indicator agent detects the crossover
    Then it publishes a "MACD Bullish Crossover" event
    And the crossover point is marked on the MACD chart

  Scenario: Bollinger Band touch generates mean reversion signal
    Given BTC/USDT price is falling
    When the price touches or drops below the lower Bollinger Band
    Then the Bollinger Bands agent publishes a "Lower Band Touch - Oversold" signal
    And the event includes the band value and price

  Scenario: Volume spike confirms breakout
    Given a price breakout is detected by MA strategy
    When the Volume Analysis agent detects volume >2x average
    Then it publishes a "High Volume Confirmation" event
    And the volume confirmation is factored into signal confidence

---

Feature: Signal Synthesis & Decision Logic
  As a trader
  I want intelligent signal aggregation from multiple indicators
  So that trades are based on strong, confirmed signals

  Scenario: Multiple strategies agree on buy signal
    Given the bot is running in Demo mode and currently not in any position
    And the market conditions meet the Moving Average crossover strategy's criteria for a buy
    And the RSI is below 40 (supporting oversold)
    And volume is above average
    When the Signal Synthesis agent receives signals from MA, RSI, and Volume agents
    And no conflicting signals exist
    Then the Signal Synthesis agent publishes a "Strong Buy" signal with confidence score >80
    And the signal reasoning includes "MA Golden Cross + RSI Oversold + High Volume"

  Scenario: Conflicting signals are resolved
    Given the MA strategy signals "Buy"
    And the RSI strategy signals "Sell" (overbought)
    When the Signal Synthesis agent receives both signals
    Then it calculates a weighted decision based on configuration
    And if weights are equal, it publishes "Hold" (no action)
    And the conflict is logged with reasoning

  Scenario: Divergence warning overrides signal
    Given the MA and RSI agents signal "Buy"
    But the Divergence Detection agent detects a bearish divergence
    When the Signal Synthesis agent evaluates all inputs
    Then it downgrades the confidence score significantly
    Or publishes a "Caution" event instead of "Buy"
    And the divergence warning is shown in the dashboard

  Scenario: Trend regime filters inappropriate strategies
    Given the Trend Regime agent classifies the market as "Strong Trend"
    And a Bollinger Band mean-reversion signal occurs
    When the Strategy Orchestrator evaluates the signal
    Then it suppresses the mean-reversion signal
    And logs "Mean reversion disabled in trending regime"
    And only trend-following strategies are active

---

Feature: Automated Trade Execution - Demo Mode
  As a trader
  I want to practice strategies in a risk-free environment
  So that I can validate the system before risking real money

  Scenario: Demo mode executes simulated trade
    Given the bot is running in Demo mode and currently not in any position
    And the market conditions meet the Moving Average crossover strategy's criteria for a buy
    When the Signal Synthesis agent receives a "Buy" event from the MA Strategy agent
    And no conflicting signals exist
    Then the Strategy Orchestrator approves the signal
    And the Execution agent creates a simulated buy order for 100 USDT worth of BTC
    And the Trade Lifecycle agent logs the trade as open
    And the dashboard immediately marks the trade on the chart with a green arrow at the execution price
    And the portfolio panel shows the new open position with entry price and P/L = 0
    And no real order is sent to CoinEx
    And funds remain unchanged in the real account

  Scenario: Demo mode tracks position P/L
    Given a demo buy trade was executed at $30,000 BTC
    And the position size is 0.5 BTC
    When the price moves to $30,600 (2% gain)
    Then the Trade Lifecycle agent calculates unrealized P/L = +$300
    And the dashboard shows "+$300 (+2.00%)" for the position
    And the P/L updates in real-time as price changes

  Scenario: Demo mode executes stop-loss
    Given a demo long position exists (entry $30,000, size 0.5 BTC)
    And stop-loss is set at $28,500 (-5%)
    When the price falls to $28,500
    Then the Risk Management agent detects stop-loss hit
    And signals the Execution agent to close the position
    And the Execution agent simulates a sell at $28,500
    And the Trade Lifecycle marks the trade as closed with -$750 loss
    And the dashboard shows the closed trade in red with "Stopped Out -5%"

---

Feature: Automated Trade Execution - Live Mode
  As a trader
  I want the system to execute real trades on CoinEx
  So that I can profit from automated strategies

  Scenario: User switches from demo to live mode
    Given the bot is in Demo mode
    And CoinEx API keys are configured correctly
    When the user clicks "Switch to Live Mode" in the UI
    And confirms the warning dialog
    Then the UX Interaction agent sends mode change event
    And the Execution agent validates API credentials
    And the system switches to Production mode
    And the UI displays "LIVE TRADING" indicator prominently
    And a confirmation message shows "Live trading enabled"

  Scenario: Live mode executes real trade
    Given the bot is in Production mode
    And account balance is sufficient (>100 USDT)
    And a strong buy signal is generated
    When the Strategy Orchestrator approves the trade
    Then the Execution agent sends a market buy order to CoinEx via API Adapter
    And waits for order confirmation from CoinEx
    And receives fill confirmation with actual fill price
    And the Trade Lifecycle records the actual fill price and quantity
    And the dashboard shows the live trade with "LIVE" badge

  Scenario: Live mode handles insufficient balance
    Given the bot is in Production mode
    And account balance is 50 USDT
    And a buy signal for 100 USDT occurs
    When the Execution agent validates the trade
    Then it detects insufficient funds
    And rejects the trade with "Insufficient balance" error
    And logs the rejection
    And alerts the user in the dashboard

  Scenario: Live mode retries failed API call
    Given the bot is in Production mode
    And a sell signal is approved
    When the Execution agent calls CoinEx API
    And the API returns a timeout error
    Then the Execution agent waits 2 seconds
    And retries the order
    And on success, logs "Order executed after retry"
    And if all retries fail (max 3), logs critical error and alerts user

---

Feature: Risk Management Controls
  As a trader
  I want comprehensive risk controls on every trade
  So that my downside is protected and profits are locked in automatically

  Scenario: Stop-loss triggers on live trade
    Given the bot is in Production mode and holds an open position (long 0.5 BTC)
    And a stop-loss is set 5% below the entry price at $28,500
    And the market price falls to $28,500
    When the Risk Management agent detects the price has hit the stop-loss for that position
    Then the Execution agent immediately sends a sell order to CoinEx for 0.5 BTC at market price
    And the Trade Lifecycle agent marks the trade as closed with status "Stopped Out"
    And records the final loss amount
    Then the Dashboard UI updates to show no open position (position size back to 0)
    And the closed trade appears in Trade History with red indicator and "-5%" annotation

  Scenario: Take-profit executes at target
    Given an open long position with entry at $30,000
    And take-profit target set at $31,500 (+5%)
    When price reaches $31,500
    Then the Risk Management agent triggers exit
    And the Execution agent sells the position
    And the trade closes with +5% profit
    And the dashboard shows "Take Profit +5%" in green

  Scenario: Trailing stop locks in profits
    Given a long position entered at $30,000
    And trailing stop configured at 3% below peak
    When price rises to $32,000 (new peak)
    Then the Risk Management agent adjusts stop to $31,040 (3% below $32,000)
    And the new stop level is displayed in the dashboard
    When price later falls to $31,040
    Then the position is sold, locking in ~3.5% profit

  Scenario: Position size limit is enforced
    Given maximum position size is set to 50% of capital
    And account has $1,000 USDT
    When a buy signal occurs for $600 USDT worth
    Then the Execution agent caps the order at $500 (50% of $1,000)
    And logs "Position size capped at 50% limit"
    And executes the reduced order

  Scenario: Maximum drawdown protection halts trading
    Given maximum drawdown is set to 10%
    And starting capital was $1,000
    When total losses reach $100 (10% drawdown)
    Then the Risk Management agent publishes "Max Drawdown Reached" event
    And the Strategy Orchestrator pauses all new trades
    And the dashboard shows "Trading Halted - Max Drawdown" alert
    And the user must manually resume trading

---

Feature: Trade Lifecycle Management
  As a trader
  I want complete tracking of all positions from open to close
  So that I have a full history and accurate performance metrics

  Scenario: New position is tracked
    Given a buy order is executed at $30,000 for 0.5 BTC
    When the Trade Lifecycle agent receives the execution event
    Then it creates a new open position record
    With entry_time, entry_price ($30,000), size (0.5 BTC), strategy ("MA Crossover")
    And adds it to the open positions list
    And initializes unrealized P/L at 0

  Scenario: Open position P/L updates in real-time
    Given an open long position (entry $30,000, size 0.5 BTC)
    When price updates to $30,600
    Then the Trade Lifecycle agent recalculates unrealized P/L
    And updates the record: unrealized_pnl = $300, unrealized_pnl_percent = 2%
    And publishes position update event
    And the dashboard reflects the new P/L immediately

  Scenario: Position closure is recorded
    Given an open position (entry $30,000, size 0.5 BTC)
    When the position is sold at $31,200
    Then the Trade Lifecycle agent marks the position as closed
    And records exit_time, exit_price ($31,200)
    And calculates realized P/L = $600 (2%)
    And removes from open positions
    And adds to closed trades history
    And updates portfolio total P/L

  Scenario: Portfolio statistics are calculated
    Given 10 closed trades exist
    With 7 wins and 3 losses
    When the user views the performance dashboard
    Then the Trade Lifecycle agent provides:
      | Metric | Value |
      | Total Trades | 10 |
      | Win Rate | 70% |
      | Total P/L | $1,250 |
      | Average Win | $250 |
      | Average Loss | $100 |
    And these metrics are displayed in the UI

---

Feature: Logging & Monitoring
  As a trader
  I want complete transparency into system actions
  So that I can understand, trust, and debug the trading bot

  Scenario: Trade signals are logged with reasoning
    Given a buy signal is generated by MA strategy
    When the Signal Synthesis agent processes it
    Then a log entry is created:
      """
      [2025-11-14 10:23:45] INFO: BUY Signal Generated
      Pair: BTC/USDT, Price: $30,000
      Strategy: MA Crossover (50/200 Golden Cross)
      Confidence: 85
      Supporting: Volume +50%, RSI Neutral (55)
      """
    And the log is stored persistently
    And appears in the dashboard log viewer

  Scenario: Trade execution is logged
    Given a buy order is executed
    When the Execution agent receives confirmation
    Then a log entry is created:
      """
      [2025-11-14 10:24:01] INFO: Trade Executed
      Mode: DEMO, Side: BUY, Pair: BTC/USDT
      Quantity: 0.5 BTC, Price: $30,000
      Order ID: DEMO_12345, Status: Filled
      """

  Scenario: Errors are logged and alerted
    Given the CoinEx API call fails with error 500
    When the CoinEx API Adapter receives the error
    Then a log entry is created:
      """
      [2025-11-14 10:25:00] ERROR: API Call Failed
      Endpoint: /order/market, Method: POST
      Error: 500 Internal Server Error
      Action: Retry 1/3
      """
    And an error alert is shown in the dashboard
    And the Logging agent flags for review

  Scenario: Agent health is monitored
    Given all 25 agents are running normally
    When the RSI Indicator agent stops publishing (crashes)
    Then the Logging & Monitoring agent detects silence (no heartbeat)
    And logs "RSI Indicator agent unresponsive"
    And notifies the Agent Coordinator
    And the Coordinator attempts to restart the RSI agent
    And the dashboard shows "RSI indicator offline - restarting"

---

Feature: User Configuration & Control
  As a trader
  I want to customize strategies and parameters from the UI
  So that I have control over the bot's behavior

  Scenario: User toggles a strategy off
    Given the RSI strategy is currently active
    When the user clicks "Disable" next to RSI strategy in the UI
    Then the UX Interaction agent sends disable_strategy event
    And the Strategy Orchestrator updates configuration
    And stops routing RSI signals to execution
    And the UI shows RSI as "Inactive" with grayed-out indicator
    And a confirmation message appears "RSI strategy disabled"

  Scenario: User adjusts risk parameters
    Given default stop-loss is 5%
    When the user changes stop-loss to 3% in settings
    And clicks "Save"
    Then the UX Interaction agent publishes config_update event
    And the Risk Management agent loads new 3% stop-loss
    And all new trades use 3% stop-loss
    And the setting is persisted locally

  Scenario: User changes trading pair
    Given the dashboard is showing BTC/USDT
    When the user selects "ETH/USDT" from the pair dropdown
    Then the Market Data agent switches to ETH/USDT stream
    And all indicators reset and recalculate for ETH
    And the chart reloads with ETH/USDT data
    And any open BTC positions are unaffected (multi-pair support pending)

---

Feature: Multi-Agent Architecture Performance
  As a system
  I must handle 25 concurrent agents efficiently
  So that trading decisions are fast and reliable

  Scenario: Agents process market tick in parallel
    Given all 25 agents are running
    When a new market tick arrives
    Then the Market Data agent publishes the tick to the event bus within 50ms
    And all 5 indicator agents receive the tick simultaneously
    And all indicators complete calculation within 100ms total (parallel)
    And the Signal Synthesis receives all results within 150ms
    And a trading decision is made within 200ms total

  Scenario: Event bus handles high message volume
    Given the system is running with live data
    When the market is highly active (10 ticks/second)
    Then the event bus processes 250+ messages/second (25 agents x 10 ticks)
    And message delivery latency remains <10ms
    And no messages are dropped
    And agents remain synchronized

  Scenario: Agent failure doesn't crash system
    Given all agents are running
    When the MACD Indicator agent encounters an exception and crashes
    Then the Agent Coordinator detects the failure
    And isolates the error (other agents continue)
    And attempts to restart the MACD agent
    And logs the failure and restart
    And the dashboard shows "MACD temporarily offline"
    And trading continues without MACD signals

  Scenario: Graceful shutdown saves state
    Given the system is running with open positions
    When the user initiates shutdown
    Then the System Architect agent coordinates shutdown
    And all agents finish processing current events
    And open positions are saved to database
    And configuration is persisted
    And all connections are closed gracefully
    And the shutdown completes within 5 seconds
    And on restart, open positions are restored

---

Feature: Security & Privacy
  As a trader
  I need my API keys and trading data to be secure
  So that I can trade safely without risk of credential theft

  Scenario: API keys are encrypted at rest
    Given the user enters CoinEx API key and secret
    When the DevOps agent stores the credentials
    Then the credentials are encrypted using AES-256
    And stored in a local secure file
    And never logged or displayed in plain text

  Scenario: API keys are not exposed in logs
    Given the system is executing trades
    When any agent logs events
    Then API keys and secrets are never included in logs
    And only masked versions appear (e.g., "***abc123")
    And log file review confirms no credential leaks

  Scenario: UI prevents credential injection
    Given the user enters configuration in the UI
    When malicious input like "<script>alert('xss')</script>" is entered
    Then the input is sanitized before processing
    And no script execution occurs
    And the input is safely escaped in display

  Scenario: Local-only architecture verified
    Given the application is running
    When network traffic is monitored
    Then the only external connections are to CoinEx API
    And no data is sent to third-party services
    And no analytics or telemetry is transmitted
    And all processing occurs locally

---

Feature: Quality Assurance Agent
  As a development system
  I need automated testing of acceptance criteria
  So that quality is maintained continuously

  Scenario: QA agent runs Gherkin scenarios
    Given the QA agent is invoked
    When it executes all Gherkin scenarios
    Then it runs simulations for each scenario
    And validates expected outcomes against actual results
    And generates a test report showing pass/fail for each scenario
    And reports overall acceptance criteria pass rate

  Scenario: QA agent validates indicator calculations
    Given known historical price data with expected indicator values
    When the QA agent tests the MA Indicator agent
    Then it feeds the known data to the agent
    And compares calculated MA values with expected values
    And asserts accuracy within 0.01% tolerance
    And reports "MA Indicator: PASS" if accurate

  Scenario: QA agent detects regressions
    Given all tests passed previously
    When code changes are made
    And the QA agent runs tests again
    And a previously passing test now fails
    Then the QA agent flags a regression
    And logs detailed failure information
    And alerts developers via the dashboard

---

Feature: Documentation & Onboarding
  As a new user
  I need clear documentation and guidance
  So that I can set up and use the system successfully

  Scenario: User accesses setup guide
    Given a new user has downloaded the application
    When they open the README
    Then clear setup instructions are provided
    With prerequisites (Python 3.11+, Node.js 18+)
    And step-by-step installation commands
    And configuration instructions
    And expected completion time (15 minutes)

  Scenario: In-app help is available
    Given the user is in the dashboard
    When they click the "Help" icon
    Then a help panel opens
    With explanations of each UI element
    And links to detailed documentation
    And common troubleshooting tips

  Scenario: Strategy explanations are clear
    Given the user views the strategies panel
    When they hover over "MA Crossover" strategy
    Then a tooltip appears explaining:
      "Trend-following strategy using moving average crossovers.
       Buy when fast MA crosses above slow MA (golden cross).
       Best in trending markets."
    And similar explanations exist for all strategies

---

# End of Acceptance Criteria
# These scenarios serve as the "Definition of Done" for each feature
# All scenarios should pass before v1.0 release
# Target: 90%+ pass rate by Month 6
