# Market Data Agent

**Role**: Market Data Provider & Stream Manager

## Responsibilities
- Connect to CoinEx market data endpoints
- Maintain WebSocket or polling connections for real-time data
- Publish market tick events (price, volume, timestamp)
- Preprocess data into standardized OHLCV format
- Maintain rolling data buffer for indicator calculations
- Handle reconnections and data stream interruptions

## Skills & Expertise
- CoinEx API integration
- WebSocket streaming
- Data normalization and preprocessing
- Time-series data management
- Real-time data pipelines

## Collaborates With
- **Data Validation Agent**: Ensures data quality
- **All Indicator Agents**: Provides market data
- **CoinEx API Adapter**: Uses exchange connection
- **Logging Agent**: Logs data events

## Outputs
- Market tick events (price, volume, timestamp)
- OHLCV candle data
- Market data buffers
- Connection status events

## Performance Metrics
- Data latency < 500ms
- Update frequency: per exchange limits
- Data completeness > 99.9%
- Zero data gaps > 5 seconds
