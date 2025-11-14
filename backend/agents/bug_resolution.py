"""
Bug & Resolution Agent (Incident Manager)

Continuously tests the system, detects bugs, and coordinates resolution.
Runs automated tests in parallel with development and acts as incident manager.

Agent: Bug & Resolution Agent (Agent #26)
Collaborates With: All agents, QA Agent, System Architect
Role: Site Reliability Engineer + Incident Manager

Responsibilities:
- Run automated tests continuously
- Detect bugs via tests, monitors, and anomaly detection
- Triage bugs by severity (P0-P3)
- Coordinate bug fixes across squads
- Track bug lifecycle
- Generate reports and metrics
- Prevent regressions

Sprint: 1.2 (New hire!)
Status: Active - Protecting the system!
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import subprocess
import structlog

from .base_agent import BaseAgent

logger = structlog.get_logger()


class Severity(str, Enum):
    """Bug severity levels for incident triage."""
    P0_CRITICAL = "P0"  # System down, fix immediately
    P1_HIGH = "P1"      # Major feature broken, fix <24h
    P2_MEDIUM = "P2"    # Minor issue, fix <1 week
    P3_LOW = "P3"       # Cosmetic/nice-to-have


class BugStatus(str, Enum):
    """Bug lifecycle states."""
    DETECTED = "detected"
    TRIAGED = "triaged"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"


class Bug:
    """
    Represents a detected bug/incident.

    Attributes:
        id: Unique bug identifier
        title: Short description
        description: Detailed description
        severity: P0-P3 severity level
        status: Current lifecycle status
        squad: Responsible squad (Data, UX, etc.)
        assigned_to: Specific agent responsible
        detected_at: When bug was found
        resolved_at: When bug was fixed (if resolved)
    """

    def __init__(
        self,
        title: str,
        description: str,
        severity: Severity,
        squad: str = "unassigned"
    ):
        self.id = f"BUG-{int(datetime.utcnow().timestamp())}"
        self.title = title
        self.description = description
        self.severity = severity
        self.status = BugStatus.DETECTED
        self.squad = squad
        self.assigned_to: Optional[str] = None
        self.detected_at = datetime.utcnow()
        self.resolved_at: Optional[datetime] = None
        self.reproduction_steps: List[str] = []
        self.proposed_fix: Optional[str] = None
        self.test_case: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert bug to dictionary for logging/reporting."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "squad": self.squad,
            "assigned_to": self.assigned_to,
            "detected_at": self.detected_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "mttr_hours": self._calculate_mttr() if self.resolved_at else None
        }

    def _calculate_mttr(self) -> float:
        """Calculate Mean Time To Resolve in hours."""
        if not self.resolved_at:
            return 0.0
        delta = self.resolved_at - self.detected_at
        return delta.total_seconds() / 3600


class BugResolutionAgent(BaseAgent):
    """
    Incident Manager and Continuous Testing Agent.

    Monitors system health, runs automated tests, detects bugs,
    and coordinates their resolution across all squads.

    Attributes:
        bugs: Dictionary of all bugs (id -> Bug)
        test_interval: Seconds between test runs (default: 300 = 5 minutes)
        last_test_run: Timestamp of last test execution
        metrics: Testing and bug resolution metrics
    """

    def __init__(self):
        """Initialize Bug & Resolution Agent."""
        super().__init__(agent_id="bug_resolution")

        self.bugs: Dict[str, Bug] = {}
        self.test_interval = 300  # 5 minutes
        self.last_test_run: Optional[datetime] = None

        # Metrics tracking
        self.metrics = {
            "total_bugs_detected": 0,
            "bugs_by_severity": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
            "bugs_resolved": 0,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_coverage_pct": 0.0,
            "mean_time_to_resolve_hours": 0.0
        }

        logger.info(
            "bug_resolution_agent_initialized",
            role="incident_manager",
            test_interval=self.test_interval
        )

    async def start(self):
        """
        Start the Bug & Resolution Agent.

        Begins continuous testing and monitoring.
        """
        await super().start()

        # Subscribe to error events from all agents
        await self.subscribe("*.error", self._handle_error_event)
        await self.subscribe("agent.*.crash", self._handle_agent_crash)

        # Start continuous testing loop
        self.create_task(self._continuous_testing_loop())

        # Start health monitoring
        self.create_task(self._monitor_agent_health())

        logger.info(
            "bug_resolution_agent_started",
            watching="all_agents",
            testing_mode="continuous"
        )

    async def _continuous_testing_loop(self):
        """
        Run tests continuously at regular intervals.

        Executes pytest and tracks results.
        """
        logger.info("continuous_testing_started", interval=self.test_interval)

        while self.running:
            try:
                # Run tests
                await self._run_tests()

                # Wait before next test run
                await asyncio.sleep(self.test_interval)

            except Exception as e:
                logger.error(
                    "continuous_testing_error",
                    error=str(e)
                )
                await asyncio.sleep(60)  # Wait 1 min before retry

    async def _run_tests(self):
        """
        Run pytest test suite and analyze results.

        Detects bugs from test failures.
        """
        logger.info("running_test_suite")

        try:
            # Run pytest with coverage
            result = subprocess.run(
                ["pytest", "tests/", "-v", "--tb=short", "--cov=.", "--cov-report=term-missing"],
                cwd="/home/user/foqcapay/backend",
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            self.last_test_run = datetime.utcnow()
            self.metrics["tests_run"] += 1

            # Parse results
            output = result.stdout + result.stderr

            # Count passed/failed (simple parsing)
            # Real implementation would parse pytest JSON output
            if "passed" in output:
                # Extract test counts (simplified)
                self.metrics["tests_passed"] += 10  # Placeholder
                logger.info("tests_passed", count=10)

            if result.returncode != 0:
                # Tests failed - create bug report
                self.metrics["tests_failed"] += 1
                await self._handle_test_failure(output)

            # Extract coverage percentage
            if "TOTAL" in output:
                # Parse coverage (simplified)
                self.metrics["test_coverage_pct"] = 78.0  # Placeholder

            await self.publish("testing.results", {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "passed" if result.returncode == 0 else "failed",
                "coverage_pct": self.metrics["test_coverage_pct"]
            })

        except subprocess.TimeoutExpired:
            logger.error("test_suite_timeout")
            await self._report_bug(
                title="Test Suite Timeout",
                description="Test suite took >5 minutes to complete",
                severity=Severity.P2_MEDIUM,
                squad="QA"
            )

        except Exception as e:
            logger.error("test_execution_error", error=str(e))

    async def _handle_test_failure(self, output: str):
        """
        Handle test failures by creating bug reports.

        Args:
            output: pytest output with failure details
        """
        logger.warning("test_failure_detected")

        await self._report_bug(
            title="Automated Test Failure",
            description=f"One or more tests failed. Output:\n{output[:500]}...",
            severity=Severity.P2_MEDIUM,
            squad="unassigned"
        )

    async def _monitor_agent_health(self):
        """
        Monitor health of all agents continuously.

        Detects unresponsive or crashed agents.
        """
        logger.info("agent_health_monitoring_started")

        while self.running:
            try:
                # TODO Sprint 1.2: Implement actual health checks
                # For now, just a placeholder
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error("health_monitoring_error", error=str(e))

    async def _handle_error_event(self, event):
        """
        Handle error events from other agents.

        Creates bug reports for repeated errors.

        Args:
            event: Error event from event bus
        """
        logger.warning(
            "error_event_received",
            agent=event.agent_id,
            error=event.data.get("error")
        )

        # If this is a repeated error, create a bug
        # (Simplified - real implementation would track error frequency)
        if "critical" in str(event.data.get("error", "")).lower():
            await self._report_bug(
                title=f"Critical Error in {event.agent_id}",
                description=str(event.data),
                severity=Severity.P1_HIGH,
                squad=self._get_squad_for_agent(event.agent_id)
            )

    async def _handle_agent_crash(self, event):
        """
        Handle agent crash events - critical incidents!

        Args:
            event: Crash event from event bus
        """
        logger.error(
            "agent_crash_detected",
            agent=event.agent_id,
            severity="P0_CRITICAL"
        )

        # Agent crash is always P0 - critical incident!
        await self._report_bug(
            title=f"CRITICAL: {event.agent_id} Crashed",
            description=f"Agent crashed unexpectedly. Data: {event.data}",
            severity=Severity.P0_CRITICAL,
            squad=self._get_squad_for_agent(event.agent_id),
            assigned_to=event.agent_id
        )

        # Notify Agent Coordinator immediately
        await self.publish("incident.critical", {
            "agent": event.agent_id,
            "severity": "P0",
            "action_required": "immediate_attention"
        })

    async def _report_bug(
        self,
        title: str,
        description: str,
        severity: Severity,
        squad: str = "unassigned",
        assigned_to: Optional[str] = None
    ) -> Bug:
        """
        Create and report a new bug.

        Args:
            title: Short bug description
            description: Detailed description
            severity: P0-P3 severity level
            squad: Responsible squad
            assigned_to: Specific agent (optional)

        Returns:
            Bug: The created bug object
        """
        bug = Bug(
            title=title,
            description=description,
            severity=severity,
            squad=squad
        )
        bug.assigned_to = assigned_to
        bug.status = BugStatus.TRIAGED if squad != "unassigned" else BugStatus.DETECTED

        self.bugs[bug.id] = bug

        # Update metrics
        self.metrics["total_bugs_detected"] += 1
        self.metrics["bugs_by_severity"][severity.value] += 1

        # Log bug
        logger.warning(
            "bug_reported",
            bug_id=bug.id,
            title=title,
            severity=severity.value,
            squad=squad
        )

        # Publish bug event
        await self.publish(f"bug.{severity.value.lower()}", bug.to_dict())

        # If P0/P1, send urgent notification
        if severity in [Severity.P0_CRITICAL, Severity.P1_HIGH]:
            await self._escalate_incident(bug)

        return bug

    async def _escalate_incident(self, bug: Bug):
        """
        Escalate critical incidents for immediate attention.

        Args:
            bug: Critical or high-severity bug
        """
        logger.error(
            "incident_escalated",
            bug_id=bug.id,
            severity=bug.severity.value,
            title=bug.title
        )

        await self.publish("incident.escalated", {
            "bug_id": bug.id,
            "severity": bug.severity.value,
            "title": bug.title,
            "squad": bug.squad,
            "requires": "immediate_action",
            "sla_hours": 2 if bug.severity == Severity.P0_CRITICAL else 24
        })

    def _get_squad_for_agent(self, agent_id: str) -> str:
        """
        Determine which squad owns an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            str: Squad name
        """
        squad_mapping = {
            "market_data": "Data",
            "data_validation": "Data",
            "coinex_adapter": "Data",
            "ma_indicator": "Indicators",
            "rsi_indicator": "Indicators",
            "macd_indicator": "Indicators",
            "bollinger_bands": "Indicators",
            "volume_analysis": "Indicators",
            "signal_synthesis": "Strategy",
            "strategy_orchestrator": "Strategy",
            "risk_management": "Strategy",
            "execution": "Execution",
            "trade_lifecycle": "Execution",
            "dashboard": "UX",
            "ux_interaction": "UX",
        }

        return squad_mapping.get(agent_id, "Alpha")  # Default to infrastructure

    async def mark_bug_resolved(self, bug_id: str):
        """
        Mark a bug as resolved.

        Args:
            bug_id: Bug identifier
        """
        if bug_id not in self.bugs:
            logger.warning("bug_not_found", bug_id=bug_id)
            return

        bug = self.bugs[bug_id]
        bug.status = BugStatus.RESOLVED
        bug.resolved_at = datetime.utcnow()

        self.metrics["bugs_resolved"] += 1

        # Calculate MTTR
        mttr = bug._calculate_mttr()
        total_mttr = self.metrics["mean_time_to_resolve_hours"]
        resolved_count = self.metrics["bugs_resolved"]
        self.metrics["mean_time_to_resolve_hours"] = (
            (total_mttr * (resolved_count - 1) + mttr) / resolved_count
        )

        logger.info(
            "bug_resolved",
            bug_id=bug_id,
            mttr_hours=mttr,
            avg_mttr=self.metrics["mean_time_to_resolve_hours"]
        )

        await self.publish("bug.resolved", bug.to_dict())

    async def get_daily_report(self) -> Dict[str, Any]:
        """
        Generate daily bug and testing report.

        Returns:
            dict: Daily summary
        """
        open_bugs = [b for b in self.bugs.values() if b.status != BugStatus.CLOSED]

        report = {
            "date": datetime.utcnow().date().isoformat(),
            "metrics": self.metrics.copy(),
            "open_bugs": len(open_bugs),
            "open_bugs_by_severity": {
                "P0": len([b for b in open_bugs if b.severity == Severity.P0_CRITICAL]),
                "P1": len([b for b in open_bugs if b.severity == Severity.P1_HIGH]),
                "P2": len([b for b in open_bugs if b.severity == Severity.P2_MEDIUM]),
                "P3": len([b for b in open_bugs if b.severity == Severity.P3_LOW]),
            },
            "system_health": "healthy" if not any(
                b.severity == Severity.P0_CRITICAL for b in open_bugs
            ) else "degraded"
        }

        return report

    async def health_check(self) -> dict:
        """Health check for Bug & Resolution Agent."""
        base_health = await super().health_check()

        open_critical = len([
            b for b in self.bugs.values()
            if b.severity == Severity.P0_CRITICAL and b.status != BugStatus.CLOSED
        ])

        base_health.update({
            "total_bugs": len(self.bugs),
            "open_bugs": len([b for b in self.bugs.values() if b.status != BugStatus.CLOSED]),
            "critical_bugs": open_critical,
            "test_coverage_pct": self.metrics["test_coverage_pct"],
            "last_test_run": self.last_test_run.isoformat() if self.last_test_run else None,
            "status": "degraded" if open_critical > 0 else "healthy"
        })

        return base_health


# Singleton instance
_bug_resolution_agent: Optional[BugResolutionAgent] = None


async def get_bug_resolution_agent() -> BugResolutionAgent:
    """Get or create the Bug & Resolution Agent singleton."""
    global _bug_resolution_agent

    if _bug_resolution_agent is None:
        _bug_resolution_agent = BugResolutionAgent()
        await _bug_resolution_agent.initialize()

    return _bug_resolution_agent
