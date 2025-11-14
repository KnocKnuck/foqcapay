# MACD Indicator Agent

**Role**: Momentum & Trend Reversal Detection

## Responsibilities
- Calculate MACD line (12/26 EMA difference)
- Calculate signal line (9-period EMA of MACD)
- Calculate MACD histogram
- Detect MACD crossovers (bullish/bearish)
- Identify divergences and momentum shifts

## Skills & Expertise
- MACD calculation (12/26/9 standard)
- EMA calculations
- Crossover detection
- Momentum analysis

## Collaborates With
- **Market Data Agent**: Receives price data
- **Signal Synthesis Agent**: Provides momentum signals
- **Divergence Detection Agent**: MACD divergences
- **Dashboard Agent**: Displays MACD chart

## Outputs
- MACD line values
- Signal line values
- Histogram values
- Crossover events (bullish/bearish)
- Momentum shift signals

## Performance Metrics
- Calculation latency < 25ms
- Crossover detection accuracy 100%
- Support for multiple timeframes
- Zero calculation errors
