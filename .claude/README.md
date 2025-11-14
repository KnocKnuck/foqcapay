# Claude Agent Configuration

This directory contains the configuration and role definitions for all 25 specialized agents working on the FOQCAPAY crypto trading bot project.

## Purpose

This project uses a **multi-agent architecture** where each major system component is conceptualized as a specialized agent with specific responsibilities. This approach:

1. **Improves Modularity**: Each agent has clear boundaries and interfaces
2. **Enables Parallelism**: Agents work concurrently via event bus
3. **Simplifies Maintenance**: Changes to one agent don't affect others
4. **Mimics Professional Teams**: Like a 25-person company with specialists

## Directory Structure

```
.claude/
├── agents/              # 25 agent role definitions
│   ├── 01-coordinator.md
│   ├── 02-product-management.md
│   ├── 03-ux-design.md
│   └── ... (22 more agents)
├── commands/            # Custom slash commands (future)
├── prompts/             # Reusable prompts (future)
└── README.md            # This file
```

## Agent Categories

### 1. Coordination Layer (2 agents)
- **Agent Coordinator**: System orchestrator
- **System Architect**: Architecture governance

### 2. Product & Design Layer (3 agents)
- **Product Management**: Requirements & vision
- **UX Design**: Design system & tokens
- **UI Development**: Frontend implementation

### 3. Infrastructure Layer (2 agents)
- **DevOps/Config**: Deployment & secrets management
- **Logging & Monitoring**: Observability

### 4. Data Layer (3 agents)
- **Market Data**: Price/volume streaming from CoinEx
- **Data Validation**: Quality assurance
- **CoinEx API Adapter**: Exchange interface

### 5. Indicator Layer (5 agents)
- **Moving Average**: Trend analysis (20/50/200 MA)
- **RSI**: Momentum & overbought/oversold
- **MACD**: Momentum & reversals
- **Bollinger Bands**: Volatility & mean reversion
- **Volume Analysis**: Liquidity confirmation

### 6. Analysis Layer (2 agents)
- **Trend Regime**: Market classification (trending/ranging)
- **Divergence Detection**: Reversal pattern recognition

### 7. Strategy Layer (2 agents)
- **Signal Synthesis**: Multi-signal aggregation
- **Strategy Orchestrator**: Strategy selection & activation

### 8. Execution Layer (3 agents)
- **Risk Management**: Stop-loss, take-profit, trailing stops
- **Execution**: Order placement (demo & live)
- **Trade Lifecycle**: Position tracking & P/L

### 9. Interface Layer (2 agents)
- **Dashboard**: Backend-frontend data bridge
- **UX Interaction**: User command handling

### 10. Quality Layer (1 agent)
- **Quality Assurance**: Testing & validation

## Agent Communication

All agents communicate via an **Event Bus** (Pub/Sub pattern):

```
┌──────────┐     Event     ┌──────────────┐     Event     ┌──────────┐
│ Agent A  │────Publish───▶│  Event Bus   │────Deliver───▶│ Agent B  │
│          │               │  (Redis)     │               │          │
└──────────┘     Subscribe └──────────────┘     Subscribe └──────────┘
```

**Example Flow**:
1. Market Data Agent publishes `price_tick` event
2. All Indicator Agents subscribe to `price_tick`
3. Each indicator calculates independently (parallel)
4. Indicators publish their own events (e.g., `rsi_value`, `ma_crossover`)
5. Signal Synthesis Agent subscribes to all indicator events
6. Signal Synthesis aggregates and publishes `trade_signal`
7. Strategy Orchestrator subscribes to `trade_signal`
8. And so on...

## Agent Structure

Each agent definition includes:

- **Role**: One-line description
- **Responsibilities**: What the agent does
- **Skills & Expertise**: Required knowledge
- **Collaborates With**: Other agents it works with
- **Outputs**: Events/data the agent produces
- **Performance Metrics**: Success criteria

## Using This in Development

When implementing a feature:

1. **Identify the responsible agent(s)** from the 25 agents
2. **Read the agent's definition** to understand its role
3. **Check "Collaborates With"** to see dependencies
4. **Implement the agent** following its specification
5. **Ensure it publishes/subscribes** to the right events
6. **Test against performance metrics**

## Example: Implementing MA Crossover

To implement the MA crossover strategy:

1. **Read**: `.claude/agents/09-ma-indicator.md`
2. **Understand**: Calculates 20/50/200 MA, detects crossovers
3. **Collaborates**: Market Data (input), Signal Synthesis (output)
4. **Implement**:
   - Subscribe to `price_tick` events
   - Calculate MAs
   - Detect crossovers
   - Publish `ma_crossover` events
5. **Test**: Crossover detection accuracy 100%, latency <20ms

## Coordination Workflow

The **Agent Coordinator** orchestrates the workflow:

```
1. New price tick arrives
   ↓
2. Coordinator ensures all indicators are ready
   ↓
3. Indicator calculations happen in parallel
   ↓
4. Coordinator collects all indicator results
   ↓
5. Signal Synthesis processes results
   ↓
6. Strategy Orchestrator makes decision
   ↓
7. Execution Agent places order (if signal approved)
   ↓
8. Trade Lifecycle tracks the position
   ↓
9. Dashboard updates UI in real-time
```

## Spec-Driven Development

Each agent follows **Spec-Driven Development**:

1. **Agent spec defined first** (these files)
2. **Acceptance criteria** written (Gherkin scenarios)
3. **Implementation** follows spec
4. **Testing** validates against acceptance criteria
5. **QA Agent** automates validation

## Adding New Agents

To add a new agent (e.g., for a new exchange):

1. Create `26-binance-adapter.md` in this directory
2. Follow the template of existing agents
3. Define role, responsibilities, collaborators, outputs
4. Update the event bus to include new event types
5. Implement the agent code in `backend/agents/`
6. Write tests
7. Update documentation

## Maintenance

- **Review Quarterly**: Ensure agent definitions match implementation
- **Update on Changes**: If an agent's role changes, update the spec
- **Version Control**: Track changes to agent specs in git
- **Documentation**: Keep this aligned with actual system

## Questions?

- See [Project Spec](../spec/PROJECT_SPEC.md) for overall architecture
- See [Year Roadmap](../spec/roadmap/YEAR_ROADMAP.md) for development plan
- See individual agent files for specific details

---

**Maintained by**: Product Management Agent & System Architect Agent
**Last Updated**: 2025-11-14
**Status**: Active Development
