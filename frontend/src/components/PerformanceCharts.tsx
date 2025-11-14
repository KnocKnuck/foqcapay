/**
 * Performance Charts - Visual Analytics
 *
 * Charts and visualizations for trading performance analysis.
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: 5.1
 *
 * Features:
 * - Equity curve (cumulative P&L over time)
 * - Daily P&L bar chart
 * - Win/loss distribution
 * - Strategy comparison
 * - Pair performance comparison
 *
 * @component
 * @example
 * <PerformanceCharts />
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp, PieChart as PieChartIcon, BarChart3 } from "lucide-react";

interface EquityPoint {
  timestamp: string;
  equity: number;
  trade_id: string;
  pnl: number;
}

interface DailyStat {
  date: string;
  trades: number;
  winning: number;
  losing: number;
  total_pnl: number;
  volume: number;
}

interface StrategyPerformance {
  strategy: string;
  total_trades: number;
  winning_trades: number;
  total_pnl: number;
  win_rate: number;
}

/**
 * Performance charts and analytics visualizations.
 */
export function PerformanceCharts() {
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([]);
  const [dailyStats, setDailyStats] = useState<DailyStat[]>([]);
  const [strategyPerf, setStrategyPerf] = useState<StrategyPerformance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchChartData();

    // Refresh every 30 seconds
    const interval = setInterval(fetchChartData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchChartData = async () => {
    try {
      // Fetch equity curve
      const equityRes = await fetch("http://localhost:8000/api/performance/equity_curve");
      const equityData = await equityRes.json();
      setEquityCurve(equityData.points || []);

      // Fetch daily stats
      const dailyRes = await fetch("http://localhost:8000/api/trades/stats/daily?days=30");
      const dailyData = await dailyRes.json();
      setDailyStats(dailyData.daily_stats || []);

      // Fetch strategy performance
      const strategyRes = await fetch("http://localhost:8000/api/trades/stats/by_strategy");
      const strategyData = await strategyRes.json();
      setStrategyPerf(strategyData.strategies || []);

      setLoading(false);
    } catch (error) {
      console.error("Failed to fetch chart data:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <TrendingUp className="h-12 w-12 animate-pulse text-primary mx-auto mb-4" />
          <p className="text-foreground/70">Loading charts...</p>
        </div>
      </div>
    );
  }

  // Prepare data for charts
  const equityChartData = equityCurve.map((point) => ({
    time: new Date(point.timestamp).toLocaleDateString(),
    equity: point.equity,
    pnl: point.pnl,
  }));

  const dailyPnLData = dailyStats.map((stat) => ({
    date: new Date(stat.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    pnl: stat.total_pnl,
    winning: stat.winning,
    losing: stat.losing,
  }));

  const strategyPieData = strategyPerf.map((strat) => ({
    name: strat.strategy.replace("_", " ").toUpperCase(),
    value: strat.total_pnl,
    trades: strat.total_trades,
  }));

  const COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"];

  return (
    <div className="space-y-6">
      {/* Equity Curve */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <TrendingUp className="h-6 w-6 text-primary" />
          <h2 className="text-xl font-semibold text-foreground">Equity Curve</h2>
          <span className="text-sm text-foreground/60">
            Cumulative P&L over time
          </span>
        </div>

        <div className="p-6 bg-panel rounded-lg border border-border">
          {equityChartData.length === 0 ? (
            <p className="text-center text-foreground/60 py-12">
              No trading data yet. Start trading to see your equity curve.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
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
                  formatter={(value: number) => `$${value.toFixed(2)}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="equity"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={false}
                  name="Equity"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Daily P&L */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="h-6 w-6 text-primary" />
          <h2 className="text-xl font-semibold text-foreground">Daily P&L</h2>
          <span className="text-sm text-foreground/60">Last 30 days</span>
        </div>

        <div className="p-6 bg-panel rounded-lg border border-border">
          {dailyPnLData.length === 0 ? (
            <p className="text-center text-foreground/60 py-12">
              No daily trading data available yet.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dailyPnLData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="date"
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
                  formatter={(value: number) => `$${value.toFixed(2)}`}
                />
                <Legend />
                <Bar
                  dataKey="pnl"
                  fill="#3B82F6"
                  name="P&L"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Strategy Performance */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <PieChartIcon className="h-6 w-6 text-primary" />
          <h2 className="text-xl font-semibold text-foreground">
            Strategy Performance
          </h2>
          <span className="text-sm text-foreground/60">
            P&L by strategy
          </span>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Pie Chart */}
          <div className="p-6 bg-panel rounded-lg border border-border">
            {strategyPieData.length === 0 ? (
              <p className="text-center text-foreground/60 py-12">
                No strategy data available.
              </p>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={strategyPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {strategyPieData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1a1a",
                      border: "1px solid #333",
                      borderRadius: "8px",
                    }}
                    formatter={(value: number) => `$${value.toFixed(2)}`}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Strategy Stats Table */}
          <div className="p-6 bg-panel rounded-lg border border-border">
            {strategyPerf.length === 0 ? (
              <p className="text-center text-foreground/60 py-12">
                No strategy statistics available.
              </p>
            ) : (
              <div className="space-y-3">
                {strategyPerf.map((strat, index) => (
                  <div
                    key={strat.strategy}
                    className="p-4 bg-bg rounded-lg border border-border"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="font-semibold text-foreground capitalize">
                          {strat.strategy.replace("_", " ")}
                        </span>
                      </div>
                      <span
                        className={`font-bold font-mono ${
                          strat.total_pnl >= 0 ? "text-success" : "text-danger"
                        }`}
                      >
                        ${strat.total_pnl.toFixed(2)}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-foreground/60">Trades</p>
                        <p className="font-mono text-foreground">
                          {strat.total_trades}
                        </p>
                      </div>
                      <div>
                        <p className="text-foreground/60">Wins</p>
                        <p className="font-mono text-success">
                          {strat.winning_trades}
                        </p>
                      </div>
                      <div>
                        <p className="text-foreground/60">Win Rate</p>
                        <p className="font-mono text-foreground">
                          {(strat.win_rate * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
