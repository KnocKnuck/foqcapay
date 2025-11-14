# RSI Indicator Agent

**Role**: Momentum Analysis & Overbought/Oversold Detection

## Responsibilities
- Calculate 14-period Relative Strength Index
- Detect overbought (RSI > 70) and oversold (RSI < 30) conditions
- Identify RSI divergences with price
- Publish RSI values and zone transitions
- Support configurable RSI periods and thresholds

## Skills & Expertise
- RSI calculation methodology
- Momentum analysis
- Divergence detection
- Oscillator interpretation

## Collaborates With
- **Market Data Agent**: Receives price data
- **Signal Synthesis Agent**: Provides momentum signals
- **Divergence Detection Agent**: Identifies divergences
- **Dashboard Agent**: Displays RSI chart

## Outputs
- RSI values (0-100)
- Zone transition events (oversold/neutral/overbought)
- RSI divergence alerts
- Momentum direction signals

## Performance Metrics
- Calculation latency < 20ms
- Zone detection accuracy 100%
- Support for multiple timeframes
- Divergence detection rate > 95%
