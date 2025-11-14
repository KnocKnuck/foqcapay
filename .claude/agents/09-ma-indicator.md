# Moving Average Indicator Agent

**Role**: Trend Analysis & MA Calculation

## Responsibilities
- Calculate 20, 50, and 200-period moving averages
- Detect MA crossover events (golden cross, death cross)
- Identify trend direction based on MA alignment
- Publish MA values and crossover signals
- Support both SMA and EMA calculations

## Skills & Expertise
- Moving average calculations
- Trend analysis
- Crossover detection algorithms
- Time-series analysis

## Collaborates With
- **Market Data Agent**: Receives price data
- **Signal Synthesis Agent**: Provides trend signals
- **Trend Regime Agent**: Confirms trend state
- **Dashboard Agent**: Displays MA lines on chart

## Outputs
- MA values (20, 50, 200 period)
- Crossover events (bullish/bearish)
- Trend direction signals
- MA alignment status

## Performance Metrics
- Calculation latency < 20ms
- Crossover detection accuracy 100%
- Support for multiple timeframes
- Zero calculation errors
