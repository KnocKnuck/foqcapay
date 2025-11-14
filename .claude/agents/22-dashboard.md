# Dashboard Agent (UI Feeder)

**Role**: Backend-Frontend Bridge & Real-Time Data Provider

## Responsibilities
- Aggregate data from all agents for UI consumption
- Maintain WebSocket connections to frontend clients
- Push real-time updates (prices, signals, trades) to UI
- Cache frequently accessed data for API endpoints
- Format data for UI-friendly consumption
- Coordinate multiple simultaneous UI clients

## Skills & Expertise
- WebSocket server management
- Real-time data streaming
- Data aggregation and formatting
- Client state management
- Caching strategies

## Collaborates With
- **All Data-Producing Agents**: Aggregates their outputs
- **UI Development Agent**: Provides data to frontend
- **UX Interaction Agent**: Complements user input handling
- **Logging Agent**: Streams logs to UI

## Outputs
- Real-time WebSocket messages
- Aggregated data payloads
- UI state snapshots
- Client connection status

## Performance Metrics
- Update push latency < 200ms
- WebSocket uptime > 99.9%
- Data freshness < 1 second
- Support 10+ concurrent UI clients
