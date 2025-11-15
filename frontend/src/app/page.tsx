"use client";

import { useEffect, useState } from "react";
import { TradingDashboard } from "@/components/TradingDashboard";
import { PairSelector } from "@/components/PairSelector";
import { PriceTicker } from "@/components/PriceTicker";
import { PerformanceCharts } from "@/components/PerformanceCharts";
import { Play, Square } from "lucide-react";

type Strategy = "scalping" | "intraday" | "swing" | "ma_crossover";
type Mode = "demo" | "live";

interface TradingStatus {
  is_trading: boolean;
  active_strategy: Strategy | null;
  mode: Mode;
  started_at: string | null;
  stopped_at: string | null;
}

interface MarketData {
  pair: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  // Technical indicators
  rsi?: number;
  macd?: {
    macd: number;
    signal: number;
    histogram: number;
  };
  ma?: {
    ma20: number;
    ma50: number;
    ma200: number;
  };
}

export default function Home() {
  const [apiStatus, setApiStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Trading controls state
  const [tradingStatus, setTradingStatus] = useState<TradingStatus>({
    is_trading: false,
    active_strategy: null,
    mode: "demo",
    started_at: null,
    stopped_at: null,
  });
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy>("intraday");

  // Market data state
  const [selectedPair, setSelectedPair] = useState<string>("BTC/USDC");
  const [marketData, setMarketData] = useState<MarketData>({
    pair: "BTC/USDC",
    price: 0,
    change24h: 0,
    volume24h: 0,
    high24h: 0,
    low24h: 0,
  });
  const [marketDataLoading, setMarketDataLoading] = useState(true);

  const pairs = ["BTC/USDC", "ETH/USDC", "LINK/USDC"];

  // Fetch trading status
  const fetchTradingStatus = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/trading/status");
      const data = await res.json();
      if (data.status === "success") {
        setTradingStatus(data.data);
        if (data.data.active_strategy) {
          setSelectedStrategy(data.data.active_strategy);
        }
      }
    } catch (err) {
      console.error("Failed to fetch trading status:", err);
    }
  };

  // Fetch market data for selected pair
  const fetchMarketData = async (pair: string) => {
    try {
      setMarketDataLoading(true);
      const res = await fetch(`http://localhost:8000/api/market/ticker?pair=${pair}`);
      const data = await res.json();

      if (data) {
        setMarketData({
          pair: data.pair || pair,
          price: data.price || 0,
          change24h: data.change_24h || 0,
          volume24h: data.volume_24h || 0,
          high24h: data.high_24h || 0,
          low24h: data.low_24h || 0,
          rsi: data.rsi,
          macd: data.macd,
          ma: data.ma,
        });
      }
    } catch (err) {
      console.error("Failed to fetch market data:", err);
      // Set mock data for now
      setMarketData({
        pair,
        price: pair.includes("BTC") ? 43250.75 : pair.includes("ETH") ? 2280.40 : 14.85,
        change24h: 2.34,
        volume24h: 1234567.89,
        high24h: 0,
        low24h: 0,
        rsi: 58.5,
        macd: { macd: 125.5, signal: 110.2, histogram: 15.3 },
        ma: { ma20: 43100, ma50: 42800, ma200: 41500 },
      });
    } finally {
      setMarketDataLoading(false);
    }
  };

  useEffect(() => {
    // Fetch backend status
    fetch("http://localhost:8000/")
      .then((res) => res.json())
      .then((data) => {
        setApiStatus(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to connect to backend:", err);
        setLoading(false);
      });

    // Fetch trading status
    fetchTradingStatus();

    // Fetch initial market data
    fetchMarketData(selectedPair);

    // Poll trading status every 2 seconds
    const statusInterval = setInterval(fetchTradingStatus, 2000);

    // Poll market data every 5 seconds
    const marketInterval = setInterval(() => fetchMarketData(selectedPair), 5000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(marketInterval);
    };
  }, [selectedPair]);

  // Start trading
  const handleStartTrading = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/trading/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy: selectedStrategy,
          mode: tradingStatus.mode,
        }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setTradingStatus(data.data);
      } else {
        alert(`Failed to start trading: ${data.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Failed to start trading:", err);
      alert("Failed to start trading");
    }
  };

  // Stop trading
  const handleStopTrading = async () => {
    if (!confirm("Stop trading? This will close all open positions.")) {
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/api/trading/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ close_positions: true }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setTradingStatus(data.data);
      } else {
        alert(`Failed to stop trading: ${data.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Failed to stop trading:", err);
      alert("Failed to stop trading");
    }
  };

  // Change strategy
  const handleStrategyChange = async (strategy: Strategy) => {
    setSelectedStrategy(strategy);

    // If trading is active, update backend
    if (tradingStatus.is_trading) {
      try {
        const res = await fetch("http://localhost:8000/api/trading/strategy", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ strategy }),
        });
        const data = await res.json();
        if (data.status === "success") {
          setTradingStatus(data.data);
        }
      } catch (err) {
        console.error("Failed to change strategy:", err);
      }
    }
  };

  // Toggle mode
  const handleModeToggle = async () => {
    const newMode = tradingStatus.mode === "demo" ? "live" : "demo";

    // Warn about live mode
    if (newMode === "live") {
      if (
        !confirm(
          "⚠️ WARNING: You are about to switch to LIVE TRADING mode!\n\n" +
            "Real funds will be used for trades.\n\n" +
            "Make sure you have:\n" +
            "1. Configured your CoinEx API keys\n" +
            "2. Tested thoroughly in demo mode\n" +
            "3. Set appropriate risk limits\n\n" +
            "Continue?"
        )
      ) {
        return;
      }
    }

    try {
      const res = await fetch("http://localhost:8000/api/trading/mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: newMode, close_positions: true }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setTradingStatus(data.data);
      } else {
        alert(`Failed to switch mode: ${data.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Failed to switch mode:", err);
      alert("Failed to switch mode");
    }
  };

  // Handle pair change
  const handlePairChange = (pair: string) => {
    setSelectedPair(pair);
    fetchMarketData(pair);
  };

  // Strategy labels with emojis
  const strategyLabels: Record<Strategy, string> = {
    scalping: "⚡ Scalping",
    intraday: "📊 Intraday",
    swing: "🌊 Swing",
    ma_crossover: "📈 MA Crossover",
  };

  // Show loading state
  if (loading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-4">
            🤖 FOQCAPAY Trading Bot
          </h1>
          <p className="text-xl text-foreground/70">Connecting to backend...</p>
        </div>
      </main>
    );
  }

  // Show error state if backend is not connected
  if (!apiStatus) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
        <div className="max-w-5xl w-full space-y-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-4">
              🤖 FOQCAPAY Trading Bot
            </h1>
            <p className="text-xl text-foreground/70">
              Multi-Agent Crypto Trading System
            </p>
          </div>

          <div className="bg-panel p-8 rounded-lg border border-border">
            <h2 className="text-2xl font-semibold mb-4">System Status</h2>
            <div className="text-danger">
              <p>❌ Failed to connect to backend</p>
              <p className="text-sm mt-2 text-foreground/60">
                Make sure the backend is running on http://localhost:8000
              </p>
            </div>
          </div>
        </div>
      </main>
    );
  }

  // Show trading dashboard
  return (
    <main className="min-h-screen bg-background">
      {/* Header with Trading Controls */}
      <div className="bg-panel border-b border-border px-6 py-4">
        <div className="max-w-7xl mx-auto space-y-4">
          {/* Top row: Title, status, system info */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">🤖 FOQCAPAY Trading Bot</h1>
              <p className="text-sm text-foreground/70">
                Multi-Agent Crypto Trading System
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm font-medium">
                  System:{" "}
                  <span className="uppercase font-mono bg-primary/10 px-2 py-1 rounded text-xs">
                    {apiStatus.mode}
                  </span>
                </div>
                <div className="text-xs text-foreground/60">
                  {apiStatus.version} • {apiStatus.sprint}
                </div>
              </div>
              <div
                className={`w-3 h-3 rounded-full ${
                  apiStatus.status === "operational"
                    ? "bg-success animate-pulse"
                    : "bg-danger"
                }`}
                title={apiStatus.status}
              />
            </div>
          </div>

          {/* Market Data Row: Pair selector + Price Ticker + Indicators */}
          <div className="flex items-center gap-6 flex-wrap pb-4 border-b border-border">
            <PairSelector
              pairs={pairs}
              selectedPair={selectedPair}
              onPairChange={handlePairChange}
            />

            <PriceTicker
              pair={marketData.pair}
              price={marketData.price}
              change24h={marketData.change24h}
              volume24h={marketData.volume24h}
              loading={marketDataLoading}
            />

            {/* Technical Indicators */}
            {marketData.rsi !== undefined && (
              <div className="flex items-center gap-4 ml-auto">
                <div className="flex flex-col">
                  <span className="text-xs text-foreground/60">RSI(14)</span>
                  <span className={`text-lg font-bold font-mono ${
                    marketData.rsi > 70 ? 'text-danger' :
                    marketData.rsi < 30 ? 'text-success' : 'text-foreground'
                  }`}>
                    {marketData.rsi.toFixed(1)}
                  </span>
                </div>

                {marketData.macd && (
                  <div className="flex flex-col">
                    <span className="text-xs text-foreground/60">MACD</span>
                    <span className={`text-sm font-mono ${
                      marketData.macd.histogram > 0 ? 'text-success' : 'text-danger'
                    }`}>
                      {marketData.macd.histogram.toFixed(2)}
                    </span>
                  </div>
                )}

                {marketData.ma && (
                  <div className="flex flex-col">
                    <span className="text-xs text-foreground/60">MA20/50</span>
                    <span className={`text-sm font-mono ${
                      marketData.ma.ma20 > marketData.ma.ma50 ? 'text-success' : 'text-danger'
                    }`}>
                      {(marketData.ma.ma20 / marketData.ma.ma50 * 100 - 100).toFixed(2)}%
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Trading Controls Row */}
          <div className="flex items-center gap-4 flex-wrap">
            {/* Strategy Selector */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Strategy:</label>
              <select
                value={selectedStrategy}
                onChange={(e) =>
                  handleStrategyChange(e.target.value as Strategy)
                }
                disabled={tradingStatus.is_trading}
                className="px-3 py-1.5 rounded border border-border bg-background text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option value="scalping">⚡ Scalping (1-5min)</option>
                <option value="intraday">📊 Intraday (15min-1h)</option>
                <option value="swing">🌊 Swing (4h-1d)</option>
                <option value="ma_crossover">📈 MA Crossover</option>
              </select>
            </div>

            {/* Mode Toggle */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Mode:</label>
              <button
                onClick={handleModeToggle}
                disabled={tradingStatus.is_trading}
                className={`px-3 py-1.5 rounded border font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                  tradingStatus.mode === "demo"
                    ? "bg-yellow-500/10 border-yellow-500/30 text-yellow-600 dark:text-yellow-400"
                    : "bg-red-500/10 border-red-500/30 text-red-600 dark:text-red-400"
                }`}
              >
                {tradingStatus.mode === "demo" ? "🎮 DEMO" : "🔴 LIVE"}
              </button>
            </div>

            {/* Start/Stop Button */}
            <div className="flex items-center gap-2 ml-auto">
              {!tradingStatus.is_trading ? (
                <button
                  onClick={handleStartTrading}
                  className="flex items-center gap-2 px-4 py-1.5 bg-success hover:bg-success/90 text-white rounded font-medium text-sm transition-colors"
                >
                  <Play size={16} />
                  Start Trading
                </button>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
                    <span className="font-medium">
                      Trading Active - {strategyLabels[tradingStatus.active_strategy || "intraday"]}
                    </span>
                  </div>
                  <button
                    onClick={handleStopTrading}
                    className="flex items-center gap-2 px-4 py-1.5 bg-danger hover:bg-danger/90 text-white rounded font-medium text-sm transition-colors"
                  >
                    <Square size={16} />
                    Stop Trading
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Trading Dashboard and Charts */}
      <div className="p-6 space-y-6">
        <div className="max-w-7xl mx-auto">
          {/* Performance Charts */}
          <div className="mb-6">
            <PerformanceCharts />
          </div>

          {/* Trading Dashboard - Positions, Trades, Metrics */}
          <TradingDashboard />
        </div>
      </div>
    </main>
  );
}
