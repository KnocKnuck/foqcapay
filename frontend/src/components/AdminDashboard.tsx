/**
 * Admin/Monitoring Dashboard
 *
 * Real-time system monitoring and performance metrics.
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: 4.2
 *
 * Features:
 * - System resource monitoring (CPU, memory, disk)
 * - Application performance metrics
 * - Agent performance tracking
 * - Real-time WebSocket updates
 * - Health status indicators
 * - Active alerts
 *
 * @component
 * @example
 * <AdminDashboard />
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  Cpu,
  HardDrive,
  MemoryStick,
  Zap,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Users,
  Clock,
} from "lucide-react";

interface SystemMetric {
  name: string;
  value: number;
  unit: string;
  timestamp: string;
}

interface HealthCheck {
  healthy: boolean;
  status: string;
  checks: Record<string, boolean>;
  message: string;
  timestamp: string;
}

interface Metrics {
  system: Record<string, SystemMetric>;
  application: Record<string, SystemMetric>;
  agents: Record<string, SystemMetric>;
  health: HealthCheck;
}

/**
 * Admin dashboard for system monitoring.
 *
 * Displays real-time metrics and health status.
 */
export function AdminDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch initial metrics
  useEffect(() => {
    fetchMetrics();

    // Refresh every 5 seconds
    const interval = setInterval(fetchMetrics, 5000);

    return () => clearInterval(interval);
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    connectWebSocket();
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/monitoring/metrics");
      const data = await response.json();
      setMetrics(data);
      setLoading(false);
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
    }
  };

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/ws/admin-${Date.now()}`);

    ws.onopen = () => {
      setWsConnected(true);
      // Subscribe to metrics topic
      ws.send(JSON.stringify({ action: "subscribe", topic: "metrics" }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "metrics_update") {
        setMetrics(message.data);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  };

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Activity className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-foreground/70">Loading metrics...</p>
        </div>
      </div>
    );
  }

  const { system, application, agents, health } = metrics;

  // Extract metrics
  const cpuUsage = system.cpu_usage?.value || 0;
  const memoryUsage = system.memory_usage?.value || 0;
  const diskUsage = system.disk_usage?.value || 0;

  const totalRequests = application.total_requests?.value || 0;
  const totalOrders = application.total_orders?.value || 0;
  const totalErrors = application.total_errors?.value || 0;
  const avgLatency = application.avg_request_latency?.value || 0;

  // Health status
  const isHealthy = health.healthy;
  const healthStatus = health.status;

  return (
    <div className="min-h-screen bg-bg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">
            System Monitoring
          </h1>
          <p className="text-foreground/60 mt-1">
            Real-time performance and health metrics
          </p>
        </div>

        {/* Connection Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {wsConnected ? (
              <>
                <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
                <span className="text-sm text-foreground/70">Live</span>
              </>
            ) : (
              <>
                <div className="h-2 w-2 rounded-full bg-danger" />
                <span className="text-sm text-foreground/70">Disconnected</span>
              </>
            )}
          </div>

          {/* Health Indicator */}
          <div
            className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
              isHealthy
                ? "bg-success/10 border border-success"
                : "bg-danger/10 border border-danger"
            }`}
          >
            {isHealthy ? (
              <CheckCircle2 className="h-5 w-5 text-success" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-danger" />
            )}
            <span
              className={`font-semibold font-mono ${
                isHealthy ? "text-success" : "text-danger"
              }`}
            >
              {healthStatus.toUpperCase()}
            </span>
          </div>
        </div>
      </div>

      {/* System Resources */}
      <div>
        <h2 className="text-xl font-semibold text-foreground mb-4">
          System Resources
        </h2>
        <div className="grid grid-cols-3 gap-4">
          {/* CPU */}
          <MetricCard
            icon={Cpu}
            label="CPU Usage"
            value={cpuUsage.toFixed(1)}
            unit="%"
            color={cpuUsage > 80 ? "danger" : cpuUsage > 60 ? "warning" : "success"}
            progress={cpuUsage}
          />

          {/* Memory */}
          <MetricCard
            icon={MemoryStick}
            label="Memory Usage"
            value={memoryUsage.toFixed(1)}
            unit="%"
            color={memoryUsage > 85 ? "danger" : memoryUsage > 70 ? "warning" : "success"}
            progress={memoryUsage}
          />

          {/* Disk */}
          <MetricCard
            icon={HardDrive}
            label="Disk Usage"
            value={diskUsage.toFixed(1)}
            unit="%"
            color={diskUsage > 90 ? "danger" : diskUsage > 75 ? "warning" : "success"}
            progress={diskUsage}
          />
        </div>
      </div>

      {/* Application Metrics */}
      <div>
        <h2 className="text-xl font-semibold text-foreground mb-4">
          Application Performance
        </h2>
        <div className="grid grid-cols-4 gap-4">
          <StatCard
            icon={TrendingUp}
            label="Total Requests"
            value={totalRequests.toFixed(0)}
            color="primary"
          />

          <StatCard
            icon={Zap}
            label="Total Orders"
            value={totalOrders.toFixed(0)}
            color="success"
          />

          <StatCard
            icon={Clock}
            label="Avg Latency"
            value={avgLatency.toFixed(1)}
            unit="ms"
            color="primary"
          />

          <StatCard
            icon={AlertTriangle}
            label="Total Errors"
            value={totalErrors.toFixed(0)}
            color={totalErrors > 0 ? "danger" : "success"}
          />
        </div>
      </div>

      {/* Agent Performance */}
      {Object.keys(agents).length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-4">
            Agent Performance
          </h2>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(agents).map(([name, metric]) => {
              const agentId = name.replace("agent_", "").replace("_latency", "");
              return (
                <div
                  key={name}
                  className="p-4 bg-panel rounded-lg border border-border"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-foreground/60">{agentId}</p>
                      <p className="text-2xl font-bold font-mono text-foreground mt-1">
                        {metric.value.toFixed(1)}
                        <span className="text-sm text-foreground/60 ml-1">ms</span>
                      </p>
                    </div>
                    <Activity className="h-8 w-8 text-primary" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Health Details */}
      {!isHealthy && (
        <div className="p-4 bg-danger/10 border border-danger rounded-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-6 w-6 text-danger flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-semibold text-danger">
                System Health Issues
              </h3>
              <p className="text-foreground/70 mt-1">{health.message}</p>

              <div className="mt-3 space-y-2">
                {Object.entries(health.checks).map(([check, passed]) => (
                  <div key={check} className="flex items-center gap-2">
                    {passed ? (
                      <CheckCircle2 className="h-4 w-4 text-success" />
                    ) : (
                      <XCircle className="h-4 w-4 text-danger" />
                    )}
                    <span className="text-sm text-foreground/70 capitalize">
                      {check}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Metric card with progress bar
function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  color,
  progress,
}: {
  icon: any;
  label: string;
  value: string;
  unit: string;
  color: "success" | "warning" | "danger";
  progress: number;
}) {
  const colorClasses = {
    success: "text-success bg-success/10 border-success",
    warning: "text-warning bg-warning/10 border-warning",
    danger: "text-danger bg-danger/10 border-danger",
  };

  const progressColors = {
    success: "bg-success",
    warning: "bg-warning",
    danger: "bg-danger",
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-sm text-foreground/60">{label}</p>
          <p className="text-3xl font-bold font-mono mt-1">
            {value}
            <span className="text-sm text-foreground/60 ml-1">{unit}</span>
          </p>
        </div>
        <Icon className="h-8 w-8" />
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-border rounded-full overflow-hidden">
        <div
          className={`h-full transition-all ${progressColors[color]}`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
    </div>
  );
}

// Stat card
function StatCard({
  icon: Icon,
  label,
  value,
  unit,
  color,
}: {
  icon: any;
  label: string;
  value: string;
  unit?: string;
  color: "primary" | "success" | "danger";
}) {
  const colorClasses = {
    primary: "text-primary",
    success: "text-success",
    danger: "text-danger",
  };

  return (
    <div className="p-4 bg-panel rounded-lg border border-border">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-foreground/60">{label}</p>
          <p className="text-2xl font-bold font-mono text-foreground mt-1">
            {value}
            {unit && <span className="text-sm text-foreground/60 ml-1">{unit}</span>}
          </p>
        </div>
        <Icon className={`h-8 w-8 ${colorClasses[color]}`} />
      </div>
    </div>
  );
}
