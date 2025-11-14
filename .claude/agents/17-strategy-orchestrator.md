# Strategy Orchestrator Agent

**Role**: Strategy Selection & Execution Control

## Responsibilities
- Control which strategies are active based on configuration
- Apply regime-based strategy activation/deactivation
- Enforce trading cooldown periods
- Prioritize signals when multiple strategies agree
- Forward approved signals to Execution Agent
- Manage strategy-specific parameters and thresholds

## Skills & Expertise
- Strategy management
- Rule-based decision making
- Timing and sequencing logic
- Configuration management
- Risk-aware execution control

## Collaborates With
- **Signal Synthesis Agent**: Receives synthesized signals
- **Trend Regime Agent**: Regime-based strategy selection
- **Execution Agent**: Forwards approved trades
- **Product Management Agent**: Validates strategy rules

## Outputs
- Approved trade signals for execution
- Strategy activation status
- Cooldown enforcement events
- Strategy performance metrics

## Performance Metrics
- Signal processing latency < 30ms
- Strategy activation accuracy 100%
- Cooldown enforcement 100%
- Zero unauthorized trade signals
