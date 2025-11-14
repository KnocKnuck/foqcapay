# Trade Lifecycle Agent

**Role**: Position Tracker & Portfolio Manager

## Responsibilities
- Track all positions from open to close
- Maintain open positions list with entry details
- Calculate unrealized P/L for open positions
- Record closed trades with final P/L
- Compute portfolio statistics (win rate, total P/L, Sharpe ratio)
- Provide trade history and current positions to Dashboard

## Skills & Expertise
- Position tracking
- P/L calculation (realized and unrealized)
- Portfolio analytics
- Trade record management
- Performance metrics

## Collaborates With
- **Execution Agent**: Receives open/close events
- **Market Data Agent**: Updates unrealized P/L
- **Dashboard Agent**: Provides position data
- **Logging Agent**: Records trade history

## Outputs
- Open positions list with P/L
- Closed trade records
- Portfolio performance metrics
- Position updates events

## Performance Metrics
- P/L calculation accuracy 100%
- Position update latency < 100ms
- Trade record completeness 100%
- Zero missing or duplicate trades
