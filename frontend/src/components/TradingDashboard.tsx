/**
 * Trading Dashboard - Main Trading View
 *
 * Central dashboard showing all trading activity and results.
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: 5.1
 *
 * Features:
 * - Live positions display
 * - Trade history with filters
 * - P&L visualization
 * - Performance metrics
 * - Strategy results
 * - Real-time updates via WebSocket
 *
 * @component
 * @example
 * <TradingDashboard />
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Activity,
  Clock,
  BarChart3,
  Filter,
} from "lucide-react";

interface Position {
  id: string;
  pair: string;
  side: "buy" | "sell";
  entryPrice: number;
  currentPrice: number;
  size: number;
  unrealizedPnL: number;
  unrealizedPnLPct: number;
  stopLoss: number;
  takeProfit: number;
  strategy: string;
  entryTime: string;
}

interface Trade {
  id: string;
  pair: string;
  side: "buy" | "sell";
  entryPrice: number;
  exitPrice: number;
  size: number;
  pnl: number;
  pnlPct: number;
  strategy: string;
  entryTime: string;
  exitTime: string;
  reason: string;
}

interface PerformanceMetrics {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalPnL: number;
  avgWin: number;
  avgLoss: number;
  largestWin: number;
  largestLoss: number;
  profitFactor: number;
}

/**
 * Main trading dashboard showing positions, trades, and performance.
 *
 * This is the PRIMARY view for monitoring trading activity.
 */
export function TradingDashboard() {
  // State
  const [positions, setPositions] = useState<Position[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    totalTrades: 0,
    winningTrades: 0,
    losingTrades: 0,
    winRate: 0,
    totalPnL: 0,
    avgWin: 0,
    avgLoss: 0,
    largestWin: 0,
    largestLoss: 0,
    profitFactor: 0,
  });

  const [selectedPair, setSelectedPair] = useState<string>("all");
  const [selectedStrategy, setSelectedStrategy] = useState<string>("all");
  const [timeFilter, setTimeFilter] = useState<string>("24h");

  // WebSocket connection
  useEffect(() => {
    connectWebSocket();
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    // Fetch positions
    try {
      const posResponse = await fetch("http://localhost:8000/api/positions");
      const posData = await posResponse.json();
      setPositions(posData.positions || []);
    } catch (error) {
      console.error("Failed to fetch positions:", error);
    }

    // Fetch trades
    try {
      const tradesResponse = await fetch("http://localhost:8000/api/trades/history");
      const tradesData = await tradesResponse.json();
      setTrades(tradesData.trades || []);
    } catch (error) {
      console.error("Failed to fetch trades:", error);
    }

    // Fetch metrics
    try {
      const metricsResponse = await fetch("http://localhost:8000/api/performance/metrics");
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData);
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
    }
  };

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/ws/trading-${Date.now()}`);

    ws.onopen = () => {
      ws.send(JSON.stringify({ action: "subscribe", topic: "positions" }));
      ws.send(JSON.stringify({ action: "subscribe", topic: "trades" }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "position_update") {
        updatePosition(message.data);
      } else if (message.type === "trade_executed") {
        addTrade(message.data);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  };

  const updatePosition = (position: Position) => {
    setPositions((prev) => {
      const index = prev.findIndex((p) => p.id === position.id);
      if (index >= 0) {
        const updated = [...prev];
        updated[index] = position;
        return updated;
      }
      return [...prev, position];
    });
  };

  const addTrade = (trade: Trade) => {
    setTrades((prev) => [trade, ...prev]);

    // Update metrics
    setMetrics((prev) => {
      const newTotal = prev.totalTrades + 1;
      const isWin = trade.pnl > 0;
      const newWinning = prev.winningTrades + (isWin ? 1 : 0);
      const newLosing = prev.losingTrades + (isWin ? 0 : 1);

      return {
        ...prev,
        totalTrades: newTotal,
        winningTrades: newWinning,
        losingTrades: newLosing,
        winRate: newWinning / newTotal,
        totalPnL: prev.totalPnL + trade.pnl,
      };
    });
  };

  // Filter trades
  const filteredTrades = trades.filter((trade) => {
    if (selectedPair !== "all" && trade.pair !== selectedPair) return false;
    if (selectedStrategy !== "all" && trade.strategy !== selectedStrategy)
      return false;
    return true;
  });

  // Calculate totals
  const totalUnrealizedPnL = positions.reduce((sum, p) => sum + p.unrealizedPnL, 0);
  const totalPositionValue = positions.reduce(
    (sum, p) => sum + p.size * p.currentPrice,
    0
  );

  return (
    <div className="min-h-screen bg-bg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Trading Dashboard</h1>
          <p className="text-foreground/60 mt-1">
            Monitor positions, trades, and performance
          </p>
        </div>

        {/* Account Summary */}
        <div className="flex gap-4">
          <SummaryCard
            icon={DollarSign}
            label="Total P&L"
            value={metrics.totalPnL}
            format="currency"
            color={metrics.totalPnL >= 0 ? "success" : "danger"}
          />
          <SummaryCard
            icon={Target}
            label="Win Rate"
            value={metrics.winRate * 100}
            format="percent"
            color={metrics.winRate >= 0.55 ? "success" : "warning"}
          />
        </div>
      </div>

      {/* Performance Metrics Grid */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          label="Total Trades"
          value={metrics.totalTrades}
          icon={Activity}
        />
        <MetricCard
          label="Winning Trades"
          value={metrics.winningTrades}
          icon={TrendingUp}
          color="success"
        />
        <MetricCard
          label="Losing Trades"
          value={metrics.losingTrades}
          icon={TrendingDown}
          color="danger"
        />
        <MetricCard
          label="Profit Factor"
          value={metrics.profitFactor.toFixed(2)}
          icon={BarChart3}
          color={metrics.profitFactor >= 1.5 ? "success" : "warning"}
        />
      </div>

      {/* Open Positions */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-foreground">
            Open Positions ({positions.length})
          </h2>
          <div className="flex items-center gap-2">
            <span className="text-sm text-foreground/60">Unrealized P&L:</span>
            <span
              className={`text-lg font-bold font-mono ${
                totalUnrealizedPnL >= 0 ? "text-success" : "text-danger"
              }`}
            >
              ${totalUnrealizedPnL.toFixed(2)}
            </span>
          </div>
        </div>

        {positions.length === 0 ? (
          <div className="p-8 text-center bg-panel rounded-lg border border-border">
            <Activity className="h-12 w-12 text-foreground/30 mx-auto mb-3" />
            <p className="text-foreground/60">No open positions</p>
          </div>
        ) : (
          <div className="space-y-3">
            {positions.map((position) => (
              <PositionCard key={position.id} position={position} />
            ))}
          </div>
        )}
      </div>

      {/* Trade History */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-foreground">
            Trade History ({filteredTrades.length})
          </h2>

          {/* Filters */}
          <div className="flex gap-3">
            <select
              value={selectedPair}
              onChange={(e) => setSelectedPair(e.target.value)}
              className="px-3 py-2 bg-panel border border-border rounded-lg text-foreground text-sm"
            >
              <option value="all">All Pairs</option>
              <option value="BTC/USDC">BTC/USDC</option>
              <option value="ETH/USDC">ETH/USDC</option>
              <option value="LINK/USDC">LINK/USDC</option>
            </select>

            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="px-3 py-2 bg-panel border border-border rounded-lg text-foreground text-sm"
            >
              <option value="all">All Strategies</option>
              <option value="scalping">Scalping</option>
              <option value="intraday">Intraday</option>
              <option value="swing">Swing</option>
              <option value="ma_crossover">MA Crossover</option>
            </select>

            <select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value)}
              className="px-3 py-2 bg-panel border border-border rounded-lg text-foreground text-sm"
            >
              <option value="24h">Last 24h</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="all">All Time</option>
            </select>
          </div>
        </div>

        {filteredTrades.length === 0 ? (
          <div className="p-8 text-center bg-panel rounded-lg border border-border">
            <Clock className="h-12 w-12 text-foreground/30 mx-auto mb-3" />
            <p className="text-foreground/60">No trades yet</p>
          </div>
        ) : (
          <div className="bg-panel rounded-lg border border-border overflow-hidden">
            <table className="w-full">
              <thead className="bg-bg border-b border-border">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-foreground/70">
                    Pair
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-foreground/70">
                    Strategy
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-foreground/70">
                    Entry
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-foreground/70">
                    Exit
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-foreground/70">
                    P&L
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-foreground/70">
                    P&L %
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-foreground/70">
                    Reason
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-foreground/70">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredTrades.map((trade, index) => (
                  <TradeRow key={trade.id} trade={trade} index={index} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// Summary card component
function SummaryCard({
  icon: Icon,
  label,
  value,
  format,
  color,
}: {
  icon: any;
  label: string;
  value: number;
  format: "currency" | "percent";
  color: "success" | "danger" | "warning";
}) {
  const colorClasses = {
    success: "text-success bg-success/10 border-success",
    danger: "text-danger bg-danger/10 border-danger",
    warning: "text-warning bg-warning/10 border-warning",
  };

  const formatted =
    format === "currency"
      ? `$${value.toFixed(2)}`
      : `${value.toFixed(1)}%`;

  return (
    <div className={`px-6 py-4 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-center gap-3">
        <Icon className="h-8 w-8" />
        <div>
          <p className="text-sm text-foreground/60">{label}</p>
          <p className="text-2xl font-bold font-mono">{formatted}</p>
        </div>
      </div>
    </div>
  );
}

// Metric card
function MetricCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number | string;
  icon: any;
  color?: "success" | "danger" | "warning";
}) {
  const textColor = color
    ? color === "success"
      ? "text-success"
      : color === "danger"
      ? "text-danger"
      : "text-warning"
    : "text-foreground";

  return (
    <div className="p-4 bg-panel rounded-lg border border-border">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-foreground/60">{label}</p>
          <p className={`text-2xl font-bold font-mono mt-1 ${textColor}`}>
            {value}
          </p>
        </div>
        <Icon className={`h-8 w-8 ${textColor}`} />
      </div>
    </div>
  );
}

// Position card component
function PositionCard({ position }: { position: Position }) {
  const isProfit = position.unrealizedPnL >= 0;

  return (
    <div className="p-4 bg-panel rounded-lg border border-border hover:border-primary/50 transition-colors">
      <div className="flex items-center justify-between">
        {/* Pair & Strategy */}
        <div>
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-bold font-mono text-foreground">
              {position.pair}
            </h3>
            <span
              className={`px-2 py-1 rounded text-xs font-semibold ${
                position.side === "buy"
                  ? "bg-success/20 text-success"
                  : "bg-danger/20 text-danger"
              }`}
            >
              {position.side.toUpperCase()}
            </span>
            <span className="text-sm text-foreground/60">
              {position.strategy}
            </span>
          </div>
        </div>

        {/* P&L */}
        <div className="text-right">
          <p className="text-sm text-foreground/60">Unrealized P&L</p>
          <p
            className={`text-2xl font-bold font-mono ${
              isProfit ? "text-success" : "text-danger"
            }`}
          >
            ${position.unrealizedPnL.toFixed(2)}
            <span className="text-sm ml-2">
              ({isProfit ? "+" : ""}
              {position.unrealizedPnLPct.toFixed(2)}%)
            </span>
          </p>
        </div>
      </div>

      {/* Details */}
      <div className="grid grid-cols-5 gap-4 mt-4 pt-4 border-t border-border">
        <div>
          <p className="text-xs text-foreground/60">Entry</p>
          <p className="text-sm font-mono text-foreground">
            ${position.entryPrice.toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-xs text-foreground/60">Current</p>
          <p className="text-sm font-mono text-foreground">
            ${position.currentPrice.toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-xs text-foreground/60">Stop Loss</p>
          <p className="text-sm font-mono text-danger">
            ${position.stopLoss.toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-xs text-foreground/60">Take Profit</p>
          <p className="text-sm font-mono text-success">
            ${position.takeProfit.toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-xs text-foreground/60">Size</p>
          <p className="text-sm font-mono text-foreground">
            ${position.size.toFixed(2)}
          </p>
        </div>
      </div>
    </div>
  );
}

// Trade row component
function TradeRow({ trade, index }: { trade: Trade; index: number }) {
  const isProfit = trade.pnl >= 0;
  const bgColor = index % 2 === 0 ? "bg-bg/50" : "bg-transparent";

  return (
    <tr className={`${bgColor} hover:bg-primary/5`}>
      <td className="px-4 py-3 text-sm font-mono text-foreground">
        {trade.pair}
      </td>
      <td className="px-4 py-3 text-sm text-foreground/70 capitalize">
        {trade.strategy.replace("_", " ")}
      </td>
      <td className="px-4 py-3 text-sm font-mono text-right text-foreground">
        ${trade.entryPrice.toFixed(2)}
      </td>
      <td className="px-4 py-3 text-sm font-mono text-right text-foreground">
        ${trade.exitPrice.toFixed(2)}
      </td>
      <td
        className={`px-4 py-3 text-sm font-mono text-right font-semibold ${
          isProfit ? "text-success" : "text-danger"
        }`}
      >
        ${trade.pnl.toFixed(2)}
      </td>
      <td
        className={`px-4 py-3 text-sm font-mono text-right ${
          isProfit ? "text-success" : "text-danger"
        }`}
      >
        {isProfit ? "+" : ""}
        {trade.pnlPct.toFixed(2)}%
      </td>
      <td className="px-4 py-3 text-sm text-foreground/70 capitalize">
        {trade.reason.replace("_", " ")}
      </td>
      <td className="px-4 py-3 text-sm text-foreground/60">
        {new Date(trade.exitTime).toLocaleString()}
      </td>
    </tr>
  );
}
