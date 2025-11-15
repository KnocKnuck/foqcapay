/**
 * Backtest Results Viewer
 *
 * Displays comprehensive backtesting results with visualizations.
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: Enhancement Phase
 *
 * Features:
 * - Backtest summary metrics
 * - Equity curve visualization
 * - Trade list with details
 * - Performance statistics
 * - Comparison with other backtests
 * - Export results
 *
 * @component
 * @example
 * <BacktestResults backtestId="abc123" />
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Download,
  Calendar,
  DollarSign,
  Target,
  AlertCircle,
  BarChart3,
} from "lucide-react";

interface BacktestSummary {
  backtest_id: string;
  strategy_name: string;
  pair: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_capital: number;
  total_pnl: number;
  total_pnl_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  max_drawdown_pct: number;
}

interface BacktestTrade {
  trade_id: string;
  entry_time: string;
  exit_time: string;
  side: string;
  entry_price: number;
  exit_price: number;
  size: number;
  pnl: number;
  pnl_pct: number;
  exit_reason: string;
}

interface EquityPoint {
  timestamp: string;
  equity: number;
  trade_id: string;
}

interface BacktestResultsProps {
  backtestId: string;
}

/**
 * Backtest results viewer with comprehensive analytics.
 */
export function BacktestResults({ backtestId }: BacktestResultsProps) {
  const [summary, setSummary] = useState<BacktestSummary | null>(null);
  const [trades, setTrades] = useState<BacktestTrade[]>([]);
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "trades" | "equity">("overview");

  useEffect(() => {
    fetchBacktestResults();
  }, [backtestId]);

  const fetchBacktestResults = async () => {
    try {
      // Fetch summary
      const summaryRes = await fetch(`http://localhost:8000/api/backtest/results/${backtestId}`);
      const summaryData = await summaryRes.json();

      if (summaryData.success) {
        setSummary(summaryData.summary);
      }

      // Fetch trades
      const tradesRes = await fetch(`http://localhost:8000/api/backtest/results/${backtestId}/trades`);
      const tradesData = await tradesRes.json();

      if (tradesData.success) {
        setTrades(tradesData.trades);
      }

      // Fetch equity curve
      const equityRes = await fetch(`http://localhost:8000/api/backtest/results/${backtestId}/equity_curve`);
      const equityData = await equityRes.json();

      if (equityData.success) {
        setEquityCurve(equityData.equity_curve);
      }

      setLoading(false);
    } catch (error) {
      console.error("Failed to fetch backtest results:", error);
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/export/backtest/${backtestId}/csv`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `backtest_${backtestId}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (error) {
      console.error("Failed to export backtest:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Activity className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-foreground/70">Loading backtest results...</p>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="p-8 text-center bg-panel rounded-lg border border-border">
        <AlertCircle className="h-12 w-12 text-foreground/30 mx-auto mb-3" />
        <p className="text-foreground/60">Backtest results not found</p>
      </div>
    );
  }

  // Prepare equity curve data for chart
  const equityChartData = equityCurve.map((point) => ({
    time: new Date(point.timestamp).toLocaleDateString(),
    equity: point.equity,
  }));

  // Calculate daily returns for distribution
  const dailyReturns = trades.map((trade) => ({
    date: new Date(trade.exit_time).toLocaleDateString(),
    pnl: trade.pnl,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Backtest Results</h2>
          <p className="text-foreground/60 mt-1">
            {summary.strategy_name} • {summary.pair} • {summary.timeframe}
          </p>
        </div>

        <button
          onClick={handleExport}
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <SummaryCard
          icon={DollarSign}
          label="Total P&L"
          value={`$${summary.total_pnl.toFixed(2)}`}
          subValue={`${summary.total_pnl_pct >= 0 ? "+" : ""}${summary.total_pnl_pct.toFixed(2)}%`}
          color={summary.total_pnl >= 0 ? "success" : "danger"}
        />

        <SummaryCard
          icon={Target}
          label="Win Rate"
          value={`${(summary.win_rate * 100).toFixed(1)}%`}
          subValue={`${summary.winning_trades}W / ${summary.losing_trades}L`}
          color={summary.win_rate >= 0.5 ? "success" : "warning"}
        />

        <SummaryCard
          icon={BarChart3}
          label="Profit Factor"
          value={summary.profit_factor.toFixed(2)}
          subValue={summary.total_trades + " trades"}
          color={summary.profit_factor >= 1.5 ? "success" : "warning"}
        />

        <SummaryCard
          icon={TrendingDown}
          label="Max Drawdown"
          value={`${summary.max_drawdown_pct.toFixed(2)}%`}
          subValue={`$${summary.max_drawdown.toFixed(2)}`}
          color={summary.max_drawdown_pct <= 10 ? "success" : "danger"}
        />
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 border-b-2 transition-colors ${
              activeTab === "overview"
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-foreground/60 hover:text-foreground"
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab("equity")}
            className={`px-4 py-2 border-b-2 transition-colors ${
              activeTab === "equity"
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-foreground/60 hover:text-foreground"
            }`}
          >
            Equity Curve
          </button>
          <button
            onClick={() => setActiveTab("trades")}
            className={`px-4 py-2 border-b-2 transition-colors ${
              activeTab === "trades"
                ? "border-primary text-primary font-semibold"
                : "border-transparent text-foreground/60 hover:text-foreground"
            }`}
          >
            Trade List ({trades.length})
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-2 gap-6">
          {/* Performance Metrics */}
          <div className="p-6 bg-panel rounded-lg border border-border">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Performance Metrics
            </h3>

            <div className="space-y-3">
              <MetricRow label="Initial Capital" value={`$${summary.initial_capital.toFixed(2)}`} />
              <MetricRow label="Final Capital" value={`$${summary.final_capital.toFixed(2)}`} />
              <MetricRow label="Sharpe Ratio" value={summary.sharpe_ratio.toFixed(2)} />
              <MetricRow label="Total Trades" value={summary.total_trades.toString()} />
              <MetricRow
                label="Period"
                value={`${new Date(summary.start_date).toLocaleDateString()} - ${new Date(summary.end_date).toLocaleDateString()}`}
              />
            </div>
          </div>

          {/* Daily Returns Distribution */}
          <div className="p-6 bg-panel rounded-lg border border-border">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Daily P&L Distribution
            </h3>

            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={dailyReturns.slice(-30)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="date"
                  stroke="#888"
                  style={{ fontSize: "10px" }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis stroke="#888" style={{ fontSize: "12px" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a1a1a",
                    border: "1px solid #333",
                    borderRadius: "8px",
                  }}
                  formatter={(value: number) => [`$${value.toFixed(2)}`, "P&L"]}
                />
                <Bar
                  dataKey="pnl"
                  fill="#3B82F6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {activeTab === "equity" && (
        <div className="p-6 bg-panel rounded-lg border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">Equity Curve</h3>

          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={equityChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="time"
                stroke="#888"
                style={{ fontSize: "12px" }}
              />
              <YAxis stroke="#888" style={{ fontSize: "12px" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #333",
                  borderRadius: "8px",
                }}
                formatter={(value: number) => [`$${value.toFixed(2)}`, "Equity"]}
              />
              <Line
                type="monotone"
                dataKey="equity"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {activeTab === "trades" && (
        <div className="bg-panel rounded-lg border border-border overflow-hidden">
          <table className="w-full">
            <thead className="bg-bg border-b border-border">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-foreground/70">
                  Entry Time
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-foreground/70">
                  Exit Time
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-foreground/70">
                  Side
                </th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-foreground/70">
                  Entry Price
                </th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-foreground/70">
                  Exit Price
                </th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-foreground/70">
                  P&L
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-foreground/70">
                  Exit Reason
                </th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade, index) => (
                <TradeRow key={trade.trade_id} trade={trade} index={index} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// Summary card component
function SummaryCard({
  icon: Icon,
  label,
  value,
  subValue,
  color,
}: {
  icon: any;
  label: string;
  value: string;
  subValue: string;
  color: "success" | "danger" | "warning";
}) {
  const colorClasses = {
    success: "text-success bg-success/10 border-success",
    danger: "text-danger bg-danger/10 border-danger",
    warning: "text-warning bg-warning/10 border-warning",
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-start justify-between mb-2">
        <p className="text-sm text-foreground/60">{label}</p>
        <Icon className="h-5 w-5" />
      </div>
      <p className="text-2xl font-bold font-mono mb-1">{value}</p>
      <p className="text-xs text-foreground/60">{subValue}</p>
    </div>
  );
}

// Metric row
function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <span className="text-sm text-foreground/60">{label}</span>
      <span className="text-sm font-mono text-foreground">{value}</span>
    </div>
  );
}

// Trade row
function TradeRow({ trade, index }: { trade: BacktestTrade; index: number }) {
  const isProfit = trade.pnl >= 0;
  const bgColor = index % 2 === 0 ? "bg-bg/50" : "bg-transparent";

  return (
    <tr className={`${bgColor} hover:bg-primary/5`}>
      <td className="px-4 py-3 text-sm text-foreground/70">
        {new Date(trade.entry_time).toLocaleString()}
      </td>
      <td className="px-4 py-3 text-sm text-foreground/70">
        {new Date(trade.exit_time).toLocaleString()}
      </td>
      <td className="px-4 py-3">
        <span
          className={`px-2 py-1 rounded text-xs font-semibold ${
            trade.side === "buy"
              ? "bg-success/20 text-success"
              : "bg-danger/20 text-danger"
          }`}
        >
          {trade.side.toUpperCase()}
        </span>
      </td>
      <td className="px-4 py-3 text-sm font-mono text-right text-foreground">
        ${trade.entry_price.toFixed(2)}
      </td>
      <td className="px-4 py-3 text-sm font-mono text-right text-foreground">
        ${trade.exit_price.toFixed(2)}
      </td>
      <td
        className={`px-4 py-3 text-sm font-mono text-right font-semibold ${
          isProfit ? "text-success" : "text-danger"
        }`}
      >
        ${trade.pnl.toFixed(2)} ({isProfit ? "+" : ""}
        {trade.pnl_pct.toFixed(2)}%)
      </td>
      <td className="px-4 py-3 text-sm text-foreground/70 capitalize">
        {trade.exit_reason.replace("_", " ")}
      </td>
    </tr>
  );
}
