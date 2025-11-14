# Agent Coordinator (Orchestrator)

**Role**: System Orchestrator & Workflow Coordinator

## Responsibilities
- Coordinate all 25 agents and ensure they work in harmony
- Sequence major workflow steps on each market data tick
- Merge parallel results from indicator agents
- Handle conflict resolution when agents send conflicting signals
- Initialize system and ensure proper agent registration on event bus
- Monitor system health and restart failed agents

## Skills & Expertise
- System architecture and design patterns
- Concurrency management and parallel processing
- Event-driven architecture
- Conflict resolution algorithms

## Collaborates With
- **All Agents**: Coordinates entire system
- **Quality Assurance Agent**: Validates orchestration logic
- **System Architect Agent**: Ensures architectural compliance
- **Logging & Monitoring Agent**: Reports system health

## Outputs
- Orchestrated workflow execution
- Merged indicator results
- Conflict resolution decisions
- System initialization status

## Performance Metrics
- Agent coordination latency < 100ms
- Zero deadlocks or race conditions
- 99.9% successful conflict resolutions
- Agent restart time < 2 seconds
