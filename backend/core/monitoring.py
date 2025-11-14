"""
Performance Monitoring System

Agent: Monitoring Agent
Squad: Alpha
Sprint: 4.2

Tracks system performance, metrics, and health in production.

Features:
- CPU, memory, disk usage
- API response times
- Order execution latency
- Agent performance metrics
- Alert thresholds
- Prometheus-compatible metrics export

Agent: #24 Monitoring Agent
"""

import time
import psutil
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance metric reading."""
    name: str
    value: float
    unit: str
    timestamp: str
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "tags": self.tags,
        }


@dataclass
class HealthStatus:
    """System health status."""
    healthy: bool
    status: str  # "healthy", "degraded", "unhealthy"
    checks: Dict[str, bool]
    message: str
    timestamp: str


class PerformanceMonitor:
    """
    Monitors system performance and health.

    Tracks:
    - System resources (CPU, memory, disk)
    - Application metrics (requests, latency)
    - Agent performance
    - Trading metrics
    - Alerts and thresholds
    """

    def __init__(self, window_size: int = 300):  # 5 minutes
        """
        Initialize performance monitor.

        Args:
            window_size: Number of samples to keep for moving averages
        """
        self.window_size = window_size

        # Metric storage (rolling windows)
        self.cpu_usage = deque(maxlen=window_size)
        self.memory_usage = deque(maxlen=window_size)
        self.disk_usage = deque(maxlen=window_size)

        # Application metrics
        self.request_latencies = deque(maxlen=window_size)
        self.order_latencies = deque(maxlen=window_size)
        self.agent_latencies: Dict[str, deque] = {}

        # Counters
        self.total_requests = 0
        self.total_orders = 0
        self.total_errors = 0

        # Alert thresholds
        self.cpu_threshold = 80.0  # %
        self.memory_threshold = 85.0  # %
        self.disk_threshold = 90.0  # %
        self.latency_threshold = 1000.0  # ms

        # Status
        self.monitoring_active = False
        self.last_health_check: Optional[datetime] = None

        logger.info("Performance Monitor initialized", window_size=window_size)

    async def start_monitoring(self):
        """Start continuous performance monitoring."""
        self.monitoring_active = True
        logger.info("Performance monitoring started")

        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self):
        """Continuous monitoring loop."""
        while self.monitoring_active:
            # Collect system metrics
            self._collect_system_metrics()

            # Sleep 1 second between collections
            await asyncio.sleep(1)

    def _collect_system_metrics(self):
        """Collect system resource metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_usage.append(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage.append(memory.percent)

        # Disk usage
        disk = psutil.disk_usage('/')
        self.disk_usage.append(disk.percent)

    def record_request_latency(self, latency_ms: float):
        """Record API request latency."""
        self.request_latencies.append(latency_ms)
        self.total_requests += 1

    def record_order_latency(self, latency_ms: float):
        """Record order execution latency."""
        self.order_latencies.append(latency_ms)
        self.total_orders += 1

    def record_agent_latency(self, agent_id: str, latency_ms: float):
        """Record agent processing latency."""
        if agent_id not in self.agent_latencies:
            self.agent_latencies[agent_id] = deque(maxlen=self.window_size)

        self.agent_latencies[agent_id].append(latency_ms)

    def record_error(self):
        """Record an error occurrence."""
        self.total_errors += 1

    def get_system_metrics(self) -> Dict[str, PerformanceMetric]:
        """Get current system metrics."""
        metrics = {}

        if self.cpu_usage:
            metrics["cpu_usage"] = PerformanceMetric(
                name="cpu_usage",
                value=sum(self.cpu_usage) / len(self.cpu_usage),
                unit="percent",
                timestamp=datetime.utcnow().isoformat(),
                tags={"type": "system"}
            )

        if self.memory_usage:
            metrics["memory_usage"] = PerformanceMetric(
                name="memory_usage",
                value=sum(self.memory_usage) / len(self.memory_usage),
                unit="percent",
                timestamp=datetime.utcnow().isoformat(),
                tags={"type": "system"}
            )

        if self.disk_usage:
            metrics["disk_usage"] = PerformanceMetric(
                name="disk_usage",
                value=sum(self.disk_usage) / len(self.disk_usage),
                unit="percent",
                timestamp=datetime.utcnow().isoformat(),
                tags={"type": "system"}
            )

        return metrics

    def get_application_metrics(self) -> Dict[str, PerformanceMetric]:
        """Get application performance metrics."""
        metrics = {}

        if self.request_latencies:
            metrics["avg_request_latency"] = PerformanceMetric(
                name="avg_request_latency",
                value=sum(self.request_latencies) / len(self.request_latencies),
                unit="ms",
                timestamp=datetime.utcnow().isoformat(),
                tags={"type": "application"}
            )

        if self.order_latencies:
            metrics["avg_order_latency"] = PerformanceMetric(
                name="avg_order_latency",
                value=sum(self.order_latencies) / len(self.order_latencies),
                unit="ms",
                timestamp=datetime.utcnow().isoformat(),
                tags={"type": "trading"}
            )

        metrics["total_requests"] = PerformanceMetric(
            name="total_requests",
            value=float(self.total_requests),
            unit="count",
            timestamp=datetime.utcnow().isoformat(),
            tags={"type": "application"}
        )

        metrics["total_orders"] = PerformanceMetric(
            name="total_orders",
            value=float(self.total_orders),
            unit="count",
            timestamp=datetime.utcnow().isoformat(),
            tags={"type": "trading"}
        )

        metrics["total_errors"] = PerformanceMetric(
            name="total_errors",
            value=float(self.total_errors),
            unit="count",
            timestamp=datetime.utcnow().isoformat(),
            tags={"type": "application"}
        )

        return metrics

    def get_agent_metrics(self) -> Dict[str, PerformanceMetric]:
        """Get agent performance metrics."""
        metrics = {}

        for agent_id, latencies in self.agent_latencies.items():
            if latencies:
                metrics[f"agent_{agent_id}_latency"] = PerformanceMetric(
                    name=f"agent_{agent_id}_latency",
                    value=sum(latencies) / len(latencies),
                    unit="ms",
                    timestamp=datetime.utcnow().isoformat(),
                    tags={"type": "agent", "agent_id": agent_id}
                )

        return metrics

    def check_health(self) -> HealthStatus:
        """
        Perform health check.

        Returns:
            HealthStatus with overall health and component statuses
        """
        checks = {}
        issues = []

        # Check CPU
        if self.cpu_usage:
            avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage)
            checks["cpu"] = avg_cpu < self.cpu_threshold
            if avg_cpu >= self.cpu_threshold:
                issues.append(f"High CPU usage: {avg_cpu:.1f}%")

        # Check memory
        if self.memory_usage:
            avg_memory = sum(self.memory_usage) / len(self.memory_usage)
            checks["memory"] = avg_memory < self.memory_threshold
            if avg_memory >= self.memory_threshold:
                issues.append(f"High memory usage: {avg_memory:.1f}%")

        # Check disk
        if self.disk_usage:
            avg_disk = sum(self.disk_usage) / len(self.disk_usage)
            checks["disk"] = avg_disk < self.disk_threshold
            if avg_disk >= self.disk_threshold:
                issues.append(f"High disk usage: {avg_disk:.1f}%")

        # Check latency
        if self.request_latencies:
            avg_latency = sum(self.request_latencies) / len(self.request_latencies)
            checks["latency"] = avg_latency < self.latency_threshold
            if avg_latency >= self.latency_threshold:
                issues.append(f"High latency: {avg_latency:.1f}ms")

        # Determine overall health
        all_healthy = all(checks.values()) if checks else True

        if all_healthy:
            status = "healthy"
            message = "All systems operational"
        elif len(issues) <= 1:
            status = "degraded"
            message = f"Degraded: {'; '.join(issues)}"
        else:
            status = "unhealthy"
            message = f"Unhealthy: {'; '.join(issues)}"

        self.last_health_check = datetime.utcnow()

        return HealthStatus(
            healthy=all_healthy,
            status=status,
            checks=checks,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics for dashboard."""
        return {
            "system": {
                name: metric.to_dict()
                for name, metric in self.get_system_metrics().items()
            },
            "application": {
                name: metric.to_dict()
                for name, metric in self.get_application_metrics().items()
            },
            "agents": {
                name: metric.to_dict()
                for name, metric in self.get_agent_metrics().items()
            },
            "health": self.check_health().__dict__,
        }

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format
        """
        lines = []

        # System metrics
        system_metrics = self.get_system_metrics()
        for name, metric in system_metrics.items():
            lines.append(f"# HELP {name} {name}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {metric.value}")

        # Application metrics
        app_metrics = self.get_application_metrics()
        for name, metric in app_metrics.items():
            lines.append(f"# HELP {name} {name}")
            type_str = "counter" if "total" in name else "gauge"
            lines.append(f"# TYPE {name} {type_str}")
            lines.append(f"{name} {metric.value}")

        return "\n".join(lines)


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
