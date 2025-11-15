/**
 * Error Log Viewer
 *
 * Administrative panel for viewing detailed system errors and logs.
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: Enhancement Phase
 *
 * Features:
 * - Real-time error streaming
 * - Error severity levels
 * - Stack traces
 * - Filter by level, category, time
 * - Search functionality
 * - Export logs
 * - Clear logs
 *
 * @component
 * @example
 * <ErrorLog />
 */

"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  AlertCircle,
  XCircle,
  AlertTriangle,
  Info,
  Search,
  Download,
  Trash2,
  Filter,
  RefreshCw,
} from "lucide-react";

interface LogEntry {
  id: string;
  level: "error" | "warning" | "info" | "debug";
  category: string; // 'api', 'agent', 'database', 'exchange', 'system'
  message: string;
  timestamp: string;
  agent_id?: string;
  error?: string;
  stack_trace?: string;
  context?: any;
}

/**
 * Error log viewer for administrators.
 */
export function ErrorLog() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filterLevel, setFilterLevel] = useState<string>("all");
  const [filterCategory, setFilterCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [expandedLog, setExpandedLog] = useState<string | null>(null);

  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load recent logs from API
    fetchRecentLogs();

    // Connect to WebSocket for real-time logs
    connectWebSocket();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const fetchRecentLogs = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/logs?limit=100");
      const data = await response.json();

      if (data.logs) {
        setLogs(data.logs);
      }
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    }
  };

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/ws/logs-${Date.now()}`);

    ws.onopen = () => {
      setWsConnected(true);
      // Subscribe to log topics
      ws.send(JSON.stringify({ action: "subscribe", topic: "logs.*" }));
      ws.send(JSON.stringify({ action: "subscribe", topic: "error.*" }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "log" || message.type === "error") {
        const logEntry: LogEntry = {
          id: `log-${Date.now()}-${Math.random()}`,
          level: message.level || (message.type === "error" ? "error" : "info"),
          category: message.category || "system",
          message: message.message || message.error || "Unknown error",
          timestamp: message.timestamp || new Date().toISOString(),
          agent_id: message.agent_id,
          error: message.error,
          stack_trace: message.stack_trace || message.traceback,
          context: message.context || message.data,
        };

        setLogs((prev) => [...prev, logEntry].slice(-1000)); // Keep last 1000
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      setTimeout(connectWebSocket, 3000);
    };
  };

  // Filter and search logs
  const filteredLogs = logs.filter((log) => {
    if (filterLevel !== "all" && log.level !== filterLevel) return false;
    if (filterCategory !== "all" && log.category !== filterCategory) return false;
    if (
      searchQuery &&
      !log.message.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !log.category.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  // Export logs
  const exportLogs = () => {
    const csv = [
      ["Timestamp", "Level", "Category", "Message", "Agent", "Error"].join(","),
      ...filteredLogs.map((log) =>
        [
          log.timestamp,
          log.level,
          log.category,
          `"${log.message.replace(/"/g, '""')}"`,
          log.agent_id || "",
          `"${(log.error || "").replace(/"/g, '""')}"`,
        ].join(",")
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `error_log_${new Date().toISOString().split("T")[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // Clear logs
  const clearLogs = () => {
    if (confirm("Clear all logs?")) {
      setLogs([]);
    }
  };

  // Get level config
  const getLevelConfig = (level: string) => {
    const configs: Record<string, { icon: any; color: string; bg: string }> = {
      error: {
        icon: XCircle,
        color: "text-danger",
        bg: "bg-danger/10",
      },
      warning: {
        icon: AlertTriangle,
        color: "text-warning",
        bg: "bg-warning/10",
      },
      info: {
        icon: Info,
        color: "text-primary",
        bg: "bg-primary/10",
      },
      debug: {
        icon: AlertCircle,
        color: "text-foreground/60",
        bg: "bg-foreground/5",
      },
    };

    return configs[level] || configs.info;
  };

  // Count by level
  const errorCount = logs.filter((l) => l.level === "error").length;
  const warningCount = logs.filter((l) => l.level === "warning").length;

  return (
    <div className="h-full flex flex-col bg-bg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Error Log</h2>
          <p className="text-sm text-foreground/60">
            {errorCount} errors • {warningCount} warnings • {logs.length} total
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Connection Status */}
          {wsConnected ? (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
              <span className="text-xs text-foreground/60">Live</span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-danger" />
              <span className="text-xs text-foreground/60">Disconnected</span>
            </div>
          )}

          {/* Refresh */}
          <button
            onClick={fetchRecentLogs}
            className="px-3 py-2 text-foreground/70 hover:text-foreground transition-colors"
            title="Refresh logs"
          >
            <RefreshCw className="h-4 w-4" />
          </button>

          {/* Export */}
          <button
            onClick={exportLogs}
            className="px-3 py-2 text-foreground/70 hover:text-foreground transition-colors"
            title="Export logs"
          >
            <Download className="h-4 w-4" />
          </button>

          {/* Clear */}
          <button
            onClick={clearLogs}
            className="px-3 py-2 text-danger/70 hover:text-danger transition-colors"
            title="Clear logs"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 p-4 border-b border-border bg-panel">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground/60" />
          <input
            type="text"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-bg border border-border rounded-lg text-foreground text-sm focus:outline-none focus:border-primary"
          />
        </div>

        {/* Level Filter */}
        <select
          value={filterLevel}
          onChange={(e) => setFilterLevel(e.target.value)}
          className="px-3 py-2 bg-bg border border-border rounded-lg text-foreground text-sm"
        >
          <option value="all">All Levels</option>
          <option value="error">Errors</option>
          <option value="warning">Warnings</option>
          <option value="info">Info</option>
          <option value="debug">Debug</option>
        </select>

        {/* Category Filter */}
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="px-3 py-2 bg-bg border border-border rounded-lg text-foreground text-sm"
        >
          <option value="all">All Categories</option>
          <option value="api">API</option>
          <option value="agent">Agent</option>
          <option value="database">Database</option>
          <option value="exchange">Exchange</option>
          <option value="system">System</option>
        </select>

        {/* Auto-scroll */}
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
            className="rounded"
          />
          <span className="text-sm text-foreground/70">Auto-scroll</span>
        </label>
      </div>

      {/* Log List */}
      <div
        ref={logContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-1 font-mono text-sm"
      >
        {filteredLogs.length === 0 ? (
          <div className="text-center py-12">
            <Info className="h-12 w-12 text-foreground/30 mx-auto mb-3" />
            <p className="text-foreground/60">No logs to display</p>
          </div>
        ) : (
          filteredLogs.map((log) => (
            <LogEntry
              key={log.id}
              log={log}
              expanded={expandedLog === log.id}
              onToggle={() =>
                setExpandedLog(expandedLog === log.id ? null : log.id)
              }
              getLevelConfig={getLevelConfig}
            />
          ))
        )}
      </div>
    </div>
  );
}

// Individual log entry
function LogEntry({
  log,
  expanded,
  onToggle,
  getLevelConfig,
}: {
  log: LogEntry;
  expanded: boolean;
  onToggle: () => void;
  getLevelConfig: (level: string) => any;
}) {
  const config = getLevelConfig(log.level);
  const Icon = config.icon;

  return (
    <div
      className={`p-3 rounded border transition-colors cursor-pointer ${
        config.bg
      } ${
        expanded ? "border-primary" : "border-border hover:border-primary/50"
      }`}
      onClick={onToggle}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <Icon className={`h-4 w-4 ${config.color} flex-shrink-0 mt-0.5`} />

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between mb-1">
            <div className="flex items-center gap-2">
              <span className={`text-xs font-semibold uppercase ${config.color}`}>
                {log.level}
              </span>
              <span className="text-xs text-foreground/60">{log.category}</span>
              {log.agent_id && (
                <span className="text-xs text-foreground/60">
                  [{log.agent_id}]
                </span>
              )}
            </div>
            <span className="text-xs text-foreground/60">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
          </div>

          <p className="text-sm text-foreground break-words">{log.message}</p>

          {/* Expanded Details */}
          {expanded && (
            <div className="mt-3 space-y-2">
              {log.error && log.error !== log.message && (
                <div>
                  <p className="text-xs text-foreground/60 mb-1">Error:</p>
                  <p className="text-xs text-danger bg-danger/5 p-2 rounded">
                    {log.error}
                  </p>
                </div>
              )}

              {log.stack_trace && (
                <div>
                  <p className="text-xs text-foreground/60 mb-1">Stack Trace:</p>
                  <pre className="text-xs text-foreground/70 bg-bg p-2 rounded overflow-x-auto">
                    {log.stack_trace}
                  </pre>
                </div>
              )}

              {log.context && (
                <div>
                  <p className="text-xs text-foreground/60 mb-1">Context:</p>
                  <pre className="text-xs text-foreground/70 bg-bg p-2 rounded overflow-x-auto">
                    {JSON.stringify(log.context, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
