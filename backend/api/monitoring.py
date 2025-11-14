"""
Monitoring API Endpoints

Agent: API Development Agent
Squad: Alpha
Sprint: 4.2

Provides HTTP endpoints for monitoring and metrics.

Agent: #20 API Development Agent
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from core.monitoring import get_performance_monitor
from api.websocket import get_connection_manager

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns health status of all system components.
    """
    monitor = get_performance_monitor()
    health = monitor.check_health()

    return {
        "healthy": health.healthy,
        "status": health.status,
        "checks": health.checks,
        "message": health.message,
        "timestamp": health.timestamp
    }


@router.get("/metrics")
async def get_metrics():
    """
    Get all performance metrics.

    Returns system, application, and agent metrics.
    """
    monitor = get_performance_monitor()
    return monitor.get_all_metrics()


@router.get("/metrics/system")
async def get_system_metrics():
    """Get system resource metrics (CPU, memory, disk)."""
    monitor = get_performance_monitor()
    metrics = monitor.get_system_metrics()

    return {
        name: metric.to_dict()
        for name, metric in metrics.items()
    }


@router.get("/metrics/application")
async def get_application_metrics():
    """Get application performance metrics."""
    monitor = get_performance_monitor()
    metrics = monitor.get_application_metrics()

    return {
        name: metric.to_dict()
        for name, metric in metrics.items()
    }


@router.get("/metrics/agents")
async def get_agent_metrics():
    """Get agent performance metrics."""
    monitor = get_performance_monitor()
    metrics = monitor.get_agent_metrics()

    return {
        name: metric.to_dict()
        for name, metric in metrics.items()
    }


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """
    Get metrics in Prometheus format.

    For integration with Prometheus monitoring.
    """
    monitor = get_performance_monitor()
    prometheus_text = monitor.export_prometheus()

    return {
        "metrics": prometheus_text
    }


@router.get("/websocket/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    manager = get_connection_manager()
    return manager.get_stats()


@router.get("/alerts")
async def get_active_alerts():
    """
    Get all active alerts.

    Returns list of current system alerts.
    """
    monitor = get_performance_monitor()
    health = monitor.check_health()

    alerts = []

    # Check for unhealthy components
    for check_name, is_healthy in health.checks.items():
        if not is_healthy:
            alerts.append({
                "severity": "high" if health.status == "unhealthy" else "medium",
                "component": check_name,
                "message": f"{check_name} check failed",
                "timestamp": health.timestamp
            })

    return {
        "total": len(alerts),
        "alerts": alerts
    }
