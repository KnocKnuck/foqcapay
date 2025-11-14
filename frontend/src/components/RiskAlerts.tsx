/**
 * Risk Alerts Component
 *
 * Displays risk alerts and warnings from the Risk Manager Agent.
 * Shows current risk level, drawdown, daily P&L, and active alerts.
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: 3.2
 *
 * Features:
 * - Real-time risk level indicator (LOW/MEDIUM/HIGH/CRITICAL)
 * - Max drawdown monitor
 * - Daily loss limit tracker
 * - Active alerts list
 * - Emergency stop button
 *
 * @component
 * @example
 * <RiskAlerts
 *   riskLevel="high"
 *   drawdown={8.5}
 *   dailyPnL={-450}
 *   maxDrawdown={10}
 *   dailyLossLimit={5}
 *   tradingPaused={false}
 * />
 */

"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  AlertCircle,
  Info,
  XCircle,
  TrendingDown,
  DollarSign,
  StopCircle,
} from "lucide-react";
import { formatCurrency, formatPercentage } from "@/lib/utils";

interface Alert {
  id: string;
  level: "low" | "medium" | "high" | "critical";
  message: string;
  timestamp: string;
}

interface RiskAlertsProps {
  /** Current risk level */
  riskLevel: "low" | "medium" | "high" | "critical";

  /** Current drawdown percentage */
  drawdown: number;

  /** Daily P&L in dollars */
  dailyPnL: number;

  /** Max drawdown limit */
  maxDrawdown: number;

  /** Daily loss limit percentage */
  dailyLossLimit: number;

  /** Is trading currently paused */
  tradingPaused: boolean;

  /** Active alerts */
  alerts?: Alert[];

  /** Callback for emergency stop */
  onEmergencyStop?: () => void;
}

/**
 * Risk monitoring and alerts display.
 *
 * Shows real-time risk metrics and active warnings.
 */
export function RiskAlerts({
  riskLevel,
  drawdown,
  dailyPnL,
  maxDrawdown,
  dailyLossLimit,
  tradingPaused,
  alerts = [],
  onEmergencyStop,
}: RiskAlertsProps) {
  const [showEmergencyConfirm, setShowEmergencyConfirm] = useState(false);

  // Calculate daily P&L percentage (assuming $10k capital for demo)
  const dailyPnLPct = (dailyPnL / 10000) * 100;

  // Risk level styles
  const riskLevelConfig = {
    low: {
      color: "text-success",
      bg: "bg-success/10",
      icon: Info,
      label: "LOW",
    },
    medium: {
      color: "text-warning",
      bg: "bg-warning/10",
      icon: AlertCircle,
      label: "MEDIUM",
    },
    high: {
      color: "text-danger",
      bg: "bg-danger/10",
      icon: AlertTriangle,
      label: "HIGH",
    },
    critical: {
      color: "text-danger",
      bg: "bg-danger/20",
      icon: XCircle,
      label: "CRITICAL",
    },
  };

  const config = riskLevelConfig[riskLevel];
  const RiskIcon = config.icon;

  // Drawdown progress (percentage of limit)
  const drawdownProgress = (drawdown / maxDrawdown) * 100;

  // Daily loss progress (percentage of limit)
  const dailyLossProgress = (Math.abs(dailyPnLPct) / dailyLossLimit) * 100;

  const handleEmergencyStop = () => {
    if (onEmergencyStop) {
      onEmergencyStop();
      setShowEmergencyConfirm(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Risk Level Header */}
      <div
        className={`flex items-center gap-3 p-4 rounded-lg border ${config.bg} ${
          riskLevel === "critical" ? "border-danger" : "border-border"
        }`}
      >
        <RiskIcon className={`h-6 w-6 ${config.color}`} />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground/70">
              Risk Level:
            </span>
            <span className={`text-lg font-bold ${config.color}`}>
              {config.label}
            </span>
          </div>
          {tradingPaused && (
            <div className="flex items-center gap-2 mt-1">
              <StopCircle className="h-4 w-4 text-danger" />
              <span className="text-sm font-semibold text-danger">
                Trading Paused
              </span>
            </div>
          )}
        </div>

        {/* Emergency Stop Button */}
        {!showEmergencyConfirm ? (
          <button
            onClick={() => setShowEmergencyConfirm(true)}
            className="px-4 py-2 bg-danger text-white rounded-lg hover:bg-danger/90 transition-colors font-semibold text-sm"
          >
            Emergency Stop
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={handleEmergencyStop}
              className="px-3 py-1 bg-danger text-white rounded text-xs font-semibold"
            >
              Confirm
            </button>
            <button
              onClick={() => setShowEmergencyConfirm(false)}
              className="px-3 py-1 bg-panel text-foreground rounded text-xs"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Risk Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Drawdown Monitor */}
        <div className="p-4 bg-panel rounded-lg border border-border">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="h-4 w-4 text-foreground/60" />
            <span className="text-sm font-medium text-foreground/70">
              Drawdown
            </span>
          </div>

          <div className="space-y-2">
            <div className="flex items-baseline gap-2">
              <span
                className={`text-2xl font-bold font-mono ${
                  drawdown >= maxDrawdown * 0.8 ? "text-danger" : "text-foreground"
                }`}
              >
                {formatPercentage(drawdown)}
              </span>
              <span className="text-sm text-foreground/60">
                / {formatPercentage(maxDrawdown)} limit
              </span>
            </div>

            {/* Progress Bar */}
            <div className="h-2 bg-border rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  drawdownProgress >= 100
                    ? "bg-danger"
                    : drawdownProgress >= 80
                    ? "bg-warning"
                    : "bg-success"
                }`}
                style={{ width: `${Math.min(drawdownProgress, 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Daily P&L Monitor */}
        <div className="p-4 bg-panel rounded-lg border border-border">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="h-4 w-4 text-foreground/60" />
            <span className="text-sm font-medium text-foreground/70">
              Daily P&L
            </span>
          </div>

          <div className="space-y-2">
            <div className="flex items-baseline gap-2">
              <span
                className={`text-2xl font-bold font-mono ${
                  dailyPnL < 0 ? "text-danger" : "text-success"
                }`}
              >
                {formatCurrency(dailyPnL)}
              </span>
              <span
                className={`text-sm ${
                  dailyPnL < 0 ? "text-danger" : "text-success"
                }`}
              >
                ({formatPercentage(dailyPnLPct)})
              </span>
            </div>

            {/* Progress Bar */}
            <div className="h-2 bg-border rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  dailyLossProgress >= 100
                    ? "bg-danger"
                    : dailyLossProgress >= 80
                    ? "bg-warning"
                    : "bg-success"
                }`}
                style={{ width: `${Math.min(dailyLossProgress, 100)}%` }}
              />
            </div>
            <div className="text-xs text-foreground/60">
              Limit: -{formatPercentage(dailyLossLimit)} (
              {formatCurrency(-(10000 * dailyLossLimit) / 100)})
            </div>
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-foreground/70">
            Active Alerts ({alerts.length})
          </h3>

          <div className="space-y-2 max-h-48 overflow-y-auto">
            {alerts.map((alert) => {
              const alertConfig = riskLevelConfig[alert.level];
              const AlertIcon = alertConfig.icon;

              return (
                <div
                  key={alert.id}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${alertConfig.bg}`}
                >
                  <AlertIcon
                    className={`h-4 w-4 ${alertConfig.color} flex-shrink-0 mt-0.5`}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground">{alert.message}</p>
                    <p className="text-xs text-foreground/60 mt-1">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Info Footer */}
      <div className="text-xs text-foreground/60 p-3 bg-panel rounded border border-border">
        <strong>Risk Protection Active:</strong> Max drawdown{" "}
        {formatPercentage(maxDrawdown)} • Daily loss limit{" "}
        {formatPercentage(dailyLossLimit)} • ATR-based stops enabled
      </div>
    </div>
  );
}
