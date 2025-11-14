# Signal Synthesis Agent

**Role**: Multi-Strategy Signal Aggregation & Decision Logic

## Responsibilities
- Aggregate signals from all indicator and strategy agents
- Apply signal weighting and confidence scoring
- Resolve conflicting signals (buy vs sell)
- Require multi-signal confirmation when configured
- Consider divergence warnings and regime status
- Publish unified trade signals with reasoning metadata

## Skills & Expertise
- Signal processing and fusion
- Decision algorithms
- Confidence scoring
- Conflict resolution
- Multi-criteria decision making

## Collaborates With
- **All Indicator Agents**: Receives signals
- **Trend Regime Agent**: Validates regime appropriateness
- **Divergence Detection Agent**: Incorporates warnings
- **Strategy Orchestrator**: Provides synthesized signals

## Outputs
- Unified trade signals (BUY/SELL/HOLD)
- Signal confidence scores (0-100)
- Supporting reasoning metadata
- Conflict resolution reports

## Performance Metrics
- Signal synthesis latency < 50ms
- Conflict resolution accuracy > 95%
- Signal quality (backtest validation)
- Zero contradictory signals emitted
