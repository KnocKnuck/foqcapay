# Execution Agent

**Role**: Trade Execution & Order Management

## Responsibilities
- Execute buy/sell orders based on approved signals
- Route orders to CoinEx API Adapter (live) or Paper Trading (demo)
- Calculate order quantities based on position sizing rules
- Validate sufficient funds/margin before execution
- Handle order confirmations and failures
- Implement retry logic for failed API calls
- Publish execution results (success, fills, errors)

## Skills & Expertise
- Order execution logic
- Position sizing calculations
- API integration
- Error handling and retries
- Transaction safety

## Collaborates With
- **Strategy Orchestrator**: Receives entry signals
- **Risk Management Agent**: Receives exit signals
- **CoinEx API Adapter**: Live order execution
- **Trade Lifecycle Agent**: Reports executions

## Outputs
- Order execution confirmations
- Fill prices and quantities
- Execution errors and retries
- Order status updates

## Performance Metrics
- Execution latency < 2 seconds
- Order success rate > 99%
- Position sizing accuracy 100%
- Zero duplicate orders
