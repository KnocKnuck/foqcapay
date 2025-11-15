/**
 * Signal Feed - Real-Time Trading Signals
 *
 * Displays live trading signals from all indicator agents.
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: Enhancement Phase
 *
 * Features:
 * - Real-time signal stream via WebSocket
 * - Signal filtering by indicator type
 * - Signal filtering by pair
 * - Strength-based coloring
 * - Auto-scroll with pause option
 * - Signal history with timestamps
 * - Click to see signal details
 *
 * @component
 * @example
 * <SignalFeed />
 */

"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Filter,
  Zap,
  AlertCircle,
  BarChart3,
  Pause,
  Play,
} from "lucide-react";

interface Signal {
  id: string;
  indicator: string; // 'MA', 'RSI', 'MACD', 'BB', 'VOLUME'
  signal_type: string;
  pair: string;
  price: number;
  strength: number; // 0-100
  timestamp: string;
  data: any; // Indicator-specific data
}

/**
 * Real-time signal feed component.
 *
 * Displays all trading signals as they occur with filtering options.
 */
export function SignalFeed() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [selectedIndicator, setSelectedIndicator] = useState<string>("all");
  const [selectedPair, setSelectedPair] = useState<string>("all");
  const [isPaused, setIsPaused] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  const signalListRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // WebSocket connection
  useEffect(() => {
    connectWebSocket();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && signalListRef.current) {
      signalListRef.current.scrollTop = signalListRef.current.scrollHeight;
    }
  }, [signals, autoScroll]);

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/ws/signals-${Date.now()}`);

    ws.onopen = () => {
      setWsConnected(true);
      // Subscribe to all signal topics
      ws.send(JSON.stringify({ action: "subscribe", topic: "signals.all" }));
      ws.send(JSON.stringify({ action: "subscribe", topic: "signal.*" }));
    };

    ws.onmessage = (event) => {
      if (isPaused) return;

      const message = JSON.parse(event.data);

      if (message.type?.includes("signal")) {
        const signal: Signal = {
          id: `${message.data.pair}-${message.data.timestamp}-${Math.random()}`,
          indicator: message.indicator || "UNKNOWN",
          signal_type: message.data.signal_type,
          pair: message.data.pair,
          price: message.data.price,
          strength: message.data.strength || 50,
          timestamp: message.data.timestamp,
          data: message.data,
        };

        setSignals((prev) => [signal, ...prev].slice(0, 200)); // Keep last 200
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

  // Filter signals
  const filteredSignals = signals.filter((signal) => {
    if (selectedIndicator !== "all" && signal.indicator !== selectedIndicator) {
      return false;
    }
    if (selectedPair !== "all" && signal.pair !== selectedPair) {
      return false;
    }
    return true;
  });

  // Signal type display configuration
  const getSignalConfig = (signalType: string) => {
    const configs: Record<string, { icon: any; color: string; label: string }> = {
      golden_cross: {
        icon: TrendingUp,
        color: "text-success",
        label: "Golden Cross",
      },
      death_cross: {
        icon: TrendingDown,
        color: "text-danger",
        label: "Death Cross",
      },
      price_cross_up: {
        icon: TrendingUp,
        color: "text-success",
        label: "Price Cross Up",
      },
      overbought: {
        icon: AlertCircle,
        color: "text-warning",
        label: "Overbought",
      },
      oversold: {
        icon: AlertCircle,
        color: "text-success",
        label: "Oversold",
      },
      bullish_crossover: {
        icon: TrendingUp,
        color: "text-success",
        label: "Bullish Cross",
      },
      bearish_crossover: {
        icon: TrendingDown,
        color: "text-danger",
        label: "Bearish Cross",
      },
      upper_touch: {
        icon: AlertCircle,
        color: "text-warning",
        label: "Upper Band",
      },
      lower_touch: {
        icon: AlertCircle,
        color: "text-success",
        label: "Lower Band",
      },
      squeeze: {
        icon: BarChart3,
        color: "text-primary",
        label: "Squeeze",
      },
      expansion: {
        icon: BarChart3,
        color: "text-warning",
        label: "Expansion",
      },
      high_volume_buy: {
        icon: Zap,
        color: "text-success",
        label: "High Vol Buy",
      },
      high_volume_sell: {
        icon: Zap,
        color: "text-danger",
        label: "High Vol Sell",
      },
      volume_spike: {
        icon: Zap,
        color: "text-warning",
        label: "Volume Spike",
      },
    };

    return (
      configs[signalType] || {
        icon: Activity,
        color: "text-foreground",
        label: signalType.replace(/_/g, " "),
      }
    );
  };

  // Get indicator badge color
  const getIndicatorColor = (indicator: string) => {
    const colors: Record<string, string> = {
      MA: "bg-blue-500/20 text-blue-400 border-blue-500",
      RSI: "bg-purple-500/20 text-purple-400 border-purple-500",
      MACD: "bg-green-500/20 text-green-400 border-green-500",
      BB: "bg-orange-500/20 text-orange-400 border-orange-500",
      VOLUME: "bg-pink-500/20 text-pink-400 border-pink-500",
    };

    return colors[indicator] || "bg-gray-500/20 text-gray-400 border-gray-500";
  };

  return (
    <div className="h-full flex flex-col bg-bg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <Zap className="h-6 w-6 text-primary" />
          <div>
            <h2 className="text-xl font-semibold text-foreground">Signal Feed</h2>
            <p className="text-sm text-foreground/60">
              Real-time trading signals ({filteredSignals.length})
            </p>
          </div>
        </div>

        {/* Connection Status */}
        <div className="flex items-center gap-3">
          {wsConnected ? (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
              <span className="text-sm text-foreground/70">Live</span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-danger" />
              <span className="text-sm text-foreground/70">Disconnected</span>
            </div>
          )}

          {/* Pause/Play */}
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`px-3 py-2 rounded-lg border transition-colors ${
              isPaused
                ? "bg-warning/10 border-warning text-warning"
                : "bg-panel border-border text-foreground hover:border-primary"
            }`}
            title={isPaused ? "Resume signals" : "Pause signals"}
          >
            {isPaused ? (
              <Play className="h-4 w-4" />
            ) : (
              <Pause className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 p-4 border-b border-border bg-panel">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-foreground/60" />
          <span className="text-sm text-foreground/70">Filter:</span>
        </div>

        {/* Indicator Filter */}
        <select
          value={selectedIndicator}
          onChange={(e) => setSelectedIndicator(e.target.value)}
          className="px-3 py-1.5 bg-bg border border-border rounded-lg text-foreground text-sm"
        >
          <option value="all">All Indicators</option>
          <option value="MA">MA (Moving Average)</option>
          <option value="RSI">RSI (Overbought/Oversold)</option>
          <option value="MACD">MACD (Trend)</option>
          <option value="BB">BB (Volatility)</option>
          <option value="VOLUME">Volume</option>
        </select>

        {/* Pair Filter */}
        <select
          value={selectedPair}
          onChange={(e) => setSelectedPair(e.target.value)}
          className="px-3 py-1.5 bg-bg border border-border rounded-lg text-foreground text-sm"
        >
          <option value="all">All Pairs</option>
          <option value="BTC/USDC">BTC/USDC</option>
          <option value="ETH/USDC">ETH/USDC</option>
          <option value="LINK/USDC">LINK/USDC</option>
        </select>

        {/* Auto-scroll Toggle */}
        <label className="flex items-center gap-2 ml-auto">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
            className="rounded"
          />
          <span className="text-sm text-foreground/70">Auto-scroll</span>
        </label>
      </div>

      {/* Signal List */}
      <div
        ref={signalListRef}
        className="flex-1 overflow-y-auto p-4 space-y-2"
        style={{ maxHeight: "600px" }}
      >
        {filteredSignals.length === 0 ? (
          <div className="text-center py-12">
            <Activity className="h-12 w-12 text-foreground/30 mx-auto mb-3" />
            <p className="text-foreground/60">
              {isPaused
                ? "Signal feed paused"
                : "No signals yet. Waiting for trading signals..."}
            </p>
          </div>
        ) : (
          filteredSignals.map((signal) => (
            <SignalCard key={signal.id} signal={signal} getSignalConfig={getSignalConfig} getIndicatorColor={getIndicatorColor} />
          ))
        )}
      </div>
    </div>
  );
}

// Individual signal card
function SignalCard({
  signal,
  getSignalConfig,
  getIndicatorColor,
}: {
  signal: Signal;
  getSignalConfig: (type: string) => any;
  getIndicatorColor: (indicator: string) => string;
}) {
  const config = getSignalConfig(signal.signal_type);
  const Icon = config.icon;

  // Strength-based opacity
  const strengthOpacity = Math.max(0.6, signal.strength / 100);

  return (
    <div
      className="p-3 bg-panel rounded-lg border border-border hover:border-primary/50 transition-colors"
      style={{ opacity: strengthOpacity }}
    >
      <div className="flex items-center justify-between mb-2">
        {/* Signal Type & Indicator */}
        <div className="flex items-center gap-2">
          <Icon className={`h-5 w-5 ${config.color}`} />
          <span className={`text-sm font-semibold ${config.color}`}>
            {config.label}
          </span>
          <span
            className={`px-2 py-0.5 rounded text-xs font-mono border ${getIndicatorColor(
              signal.indicator
            )}`}
          >
            {signal.indicator}
          </span>
        </div>

        {/* Timestamp */}
        <span className="text-xs text-foreground/60">
          {new Date(signal.timestamp).toLocaleTimeString()}
        </span>
      </div>

      {/* Signal Details */}
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div>
          <p className="text-foreground/60 text-xs">Pair</p>
          <p className="font-mono font-semibold text-foreground">{signal.pair}</p>
        </div>
        <div>
          <p className="text-foreground/60 text-xs">Price</p>
          <p className="font-mono text-foreground">${signal.price.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-foreground/60 text-xs">Strength</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-border rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  signal.strength >= 70
                    ? "bg-success"
                    : signal.strength >= 40
                    ? "bg-warning"
                    : "bg-danger"
                }`}
                style={{ width: `${signal.strength}%` }}
              />
            </div>
            <span className="text-xs font-mono text-foreground/70">
              {signal.strength.toFixed(0)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
