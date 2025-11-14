# Bollinger Bands Agent

**Role**: Volatility Analysis & Mean Reversion Detection

## Responsibilities
- Calculate 20-period Bollinger Bands (2 standard deviations)
- Detect price interaction with bands (touches, breakouts)
- Identify volatility expansion/contraction (band squeeze)
- Publish band values and price position events
- Support configurable periods and standard deviations

## Skills & Expertise
- Bollinger Bands calculation
- Standard deviation analysis
- Volatility measurement
- Mean reversion detection

## Collaborates With
- **Market Data Agent**: Receives price data
- **Signal Synthesis Agent**: Mean reversion signals
- **Trend Regime Agent**: Validates regime for mean reversion
- **Dashboard Agent**: Displays bands on chart

## Outputs
- Upper, middle, lower band values
- Band width (volatility measure)
- Price position events (above/below/inside bands)
- Squeeze/expansion signals

## Performance Metrics
- Calculation latency < 25ms
- Band touch detection accuracy 100%
- Support for multiple timeframes
- Volatility measurement precision
