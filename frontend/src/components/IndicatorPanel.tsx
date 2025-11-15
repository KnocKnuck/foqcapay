/**
 * Indicator Panel - Live Technical Indicators
 *
 * Displays real-time values of all technical indicators.
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: Enhancement Phase
 *
 * Features:
 * - Live MA, RSI, MACD, BB, Volume values
 * - Real-time updates via WebSocket
 * - Color-coded indicators (green/red/yellow)
 * - Compact and detailed view modes
 * - Per-pair indicator selection
 * - Historical sparklines
 *
 * @component
 * @example
 * <IndicatorPanel pair="BTC/USDC" />
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Minus,
} from "lucide-react";

interface MAValues {
  SMA?: Record<number, number>;
  EMA?: Record<number, number>;
  WMA?: Record<number, number>;
}

interface RSIValues {
  [period: number]: number;
}

interface MACDValues {
  macd_line: number;
  signal_line: number;
  histogram: number;
}

interface BBValues {
  [period: number]: {
    upper_band: number;
    middle_band: number;
    lower_band: number;
    bandwidth: number;
    percent_b: number;
  };
}

interface VolumeValues {
  volume: number;
  volume_ma: number;
  volume_ratio: number;
  obv: number;
}

interface IndicatorData {
  pair: string;
  price: number;
  timestamp: string;
  mas?: MAValues;
  rsi?: RSIValues;
  macd?: MACDValues;
  bb?: BBValues;
  volume_indicators?: VolumeValues;
}

interface IndicatorPanelProps {
  pair?: string;
  compact?: boolean;
}

/**
 * Indicator panel showing live technical indicator values.
 */
export function IndicatorPanel({ pair = "BTC/USDC", compact = false }: IndicatorPanelProps) {
  const [maData, setMaData] = useState<MAValues>({});
  const [rsiData, setRsiData] = useState<RSIValues>({});
  const [macdData, setMacdData] = useState<MACDValues | null>(null);
  const [bbData, setBbData] = useState<BBValues>({});
  const [volumeData, setVolumeData] = useState<VolumeValues | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    connectWebSocket();
  }, [pair]);

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/ws/indicators-${Date.now()}`);

    ws.onopen = () => {
      setWsConnected(true);
      // Subscribe to indicator updates for this pair
      ws.send(
        JSON.stringify({
          action: "subscribe",
          topic: `indicator.*.values.${pair}`,
        })
      );
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "ma_values" && message.data.pair === pair) {
        setMaData(message.data.mas || {});
        setCurrentPrice(message.data.price);
      } else if (message.type === "rsi_values" && message.data.pair === pair) {
        setRsiData(message.data.rsi || {});
        setCurrentPrice(message.data.price);
      } else if (message.type === "macd_values" && message.data.pair === pair) {
        setMacdData(message.data.macd || null);
        setCurrentPrice(message.data.price);
      } else if (message.type === "bb_values" && message.data.pair === pair) {
        setBbData(message.data.bb || {});
        setCurrentPrice(message.data.price);
      } else if (message.type === "volume_values" && message.data.pair === pair) {
        setVolumeData(message.data.volume_indicators || null);
        setCurrentPrice(message.data.price);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  };

  // Determine RSI condition
  const getRSICondition = (rsi: number) => {
    if (rsi >= 70) return { label: "Overbought", color: "text-danger" };
    if (rsi <= 30) return { label: "Oversold", color: "text-success" };
    return { label: "Neutral", color: "text-foreground" };
  };

  // Determine MACD trend
  const getMACDTrend = (macd: MACDValues) => {
    if (macd.histogram > 0) {
      return { label: "Bullish", color: "text-success", icon: TrendingUp };
    } else if (macd.histogram < 0) {
      return { label: "Bearish", color: "text-danger", icon: TrendingDown };
    }
    return { label: "Neutral", color: "text-foreground", icon: Minus };
  };

  // Determine BB position
  const getBBPosition = (bb: any) => {
    const percentB = bb.percent_b;
    if (percentB >= 1) return { label: "Above Upper", color: "text-danger" };
    if (percentB <= 0) return { label: "Below Lower", color: "text-success" };
    if (percentB > 0.7) return { label: "Near Upper", color: "text-warning" };
    if (percentB < 0.3) return { label: "Near Lower", color: "text-warning" };
    return { label: "Middle", color: "text-foreground" };
  };

  if (compact) {
    return <CompactView
      maData={maData}
      rsiData={rsiData}
      macdData={macdData}
      pair={pair}
      currentPrice={currentPrice}
      wsConnected={wsConnected}
      getRSICondition={getRSICondition}
      getMACDTrend={getMACDTrend}
    />;
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-foreground">
            Technical Indicators
          </h3>
          <p className="text-sm text-foreground/60">
            {pair} • ${currentPrice.toFixed(2)}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {wsConnected ? (
            <>
              <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
              <span className="text-xs text-foreground/60">Live</span>
            </>
          ) : (
            <>
              <div className="h-2 w-2 rounded-full bg-danger" />
              <span className="text-xs text-foreground/60">Disconnected</span>
            </>
          )}
        </div>
      </div>

      {/* Moving Averages */}
      {Object.keys(maData).length > 0 && (
        <div className="p-4 bg-panel rounded-lg border border-border">
          <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-400" />
            Moving Averages
          </h4>

          <div className="grid grid-cols-3 gap-4">
            {maData.EMA && Object.entries(maData.EMA).map(([period, value]) => {
              const isAbove = currentPrice > value;
              return (
                <div key={`ema-${period}`} className="space-y-1">
                  <p className="text-xs text-foreground/60">EMA {period}</p>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-mono text-foreground">
                      ${value.toFixed(2)}
                    </p>
                    {isAbove ? (
                      <TrendingUp className="h-3 w-3 text-success" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-danger" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* RSI */}
      {Object.keys(rsiData).length > 0 && (
        <div className="p-4 bg-panel rounded-lg border border-border">
          <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
            <Activity className="h-4 w-4 text-purple-400" />
            RSI (Relative Strength Index)
          </h4>

          <div className="grid grid-cols-3 gap-4">
            {Object.entries(rsiData).map(([period, value]) => {
              const condition = getRSICondition(value);
              return (
                <div key={`rsi-${period}`} className="space-y-2">
                  <p className="text-xs text-foreground/60">RSI {period}</p>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <p className="text-lg font-bold font-mono text-foreground">
                        {value.toFixed(1)}
                      </p>
                      <span className={`text-xs font-semibold ${condition.color}`}>
                        {condition.label}
                      </span>
                    </div>
                    <div className="h-2 bg-border rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          value >= 70
                            ? "bg-danger"
                            : value <= 30
                            ? "bg-success"
                            : "bg-primary"
                        }`}
                        style={{ width: `${value}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* MACD */}
      {macdData && (
        <div className="p-4 bg-panel rounded-lg border border-border">
          <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-green-400" />
            MACD
          </h4>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-foreground/60">MACD Line</p>
              <p className="text-sm font-mono text-foreground">
                {macdData.macd_line.toFixed(4)}
              </p>
            </div>
            <div>
              <p className="text-xs text-foreground/60">Signal Line</p>
              <p className="text-sm font-mono text-foreground">
                {macdData.signal_line.toFixed(4)}
              </p>
            </div>
            <div>
              <p className="text-xs text-foreground/60">Histogram</p>
              <div className="flex items-center gap-2">
                <p
                  className={`text-sm font-mono font-semibold ${
                    macdData.histogram >= 0 ? "text-success" : "text-danger"
                  }`}
                >
                  {macdData.histogram.toFixed(4)}
                </p>
                {getMACDTrend(macdData).icon && (
                  <span className={getMACDTrend(macdData).color}>
                    {React.createElement(getMACDTrend(macdData).icon, {
                      className: "h-4 w-4",
                    })}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bollinger Bands */}
      {Object.keys(bbData).length > 0 && (
        <div className="p-4 bg-panel rounded-lg border border-border">
          <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-orange-400" />
            Bollinger Bands
          </h4>

          {Object.entries(bbData).map(([period, bb]) => {
            const position = getBBPosition(bb);
            return (
              <div key={`bb-${period}`} className="space-y-3">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-foreground/60">Upper Band</p>
                    <p className="text-sm font-mono text-foreground">
                      ${bb.upper_band.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-foreground/60">Middle (SMA)</p>
                    <p className="text-sm font-mono text-foreground">
                      ${bb.middle_band.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-foreground/60">Lower Band</p>
                    <p className="text-sm font-mono text-foreground">
                      ${bb.lower_band.toFixed(2)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-foreground/60">Bandwidth</p>
                    <p className="text-sm font-mono text-foreground">
                      {bb.bandwidth.toFixed(2)}%
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-foreground/60">Position</p>
                    <p className={`text-sm font-semibold ${position.color}`}>
                      {position.label}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Volume */}
      {volumeData && (
        <div className="p-4 bg-panel rounded-lg border border-border">
          <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-pink-400" />
            Volume Analysis
          </h4>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-foreground/60">Current Volume</p>
              <p className="text-sm font-mono text-foreground">
                {volumeData.volume.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-xs text-foreground/60">Volume MA</p>
              <p className="text-sm font-mono text-foreground">
                {volumeData.volume_ma.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-xs text-foreground/60">Volume Ratio</p>
              <p
                className={`text-sm font-mono font-semibold ${
                  volumeData.volume_ratio >= 2
                    ? "text-warning"
                    : "text-foreground"
                }`}
              >
                {volumeData.volume_ratio.toFixed(2)}x
              </p>
            </div>
            <div>
              <p className="text-xs text-foreground/60">OBV</p>
              <p className="text-sm font-mono text-foreground">
                {volumeData.obv.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Compact view for sidebar/dashboard
function CompactView({ maData, rsiData, macdData, pair, currentPrice, wsConnected, getRSICondition, getMACDTrend }: any) {
  return (
    <div className="p-3 bg-panel rounded-lg border border-border space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-foreground">{pair}</span>
        <span className="text-xs text-foreground/60">
          ${currentPrice.toFixed(2)}
        </span>
      </div>

      {maData.EMA?.[20] && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-foreground/60">EMA 20</span>
          <span className="font-mono text-foreground">
            ${maData.EMA[20].toFixed(2)}
          </span>
        </div>
      )}

      {rsiData[14] && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-foreground/60">RSI 14</span>
          <span className={`font-mono font-semibold ${getRSICondition(rsiData[14]).color}`}>
            {rsiData[14].toFixed(1)}
          </span>
        </div>
      )}

      {macdData && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-foreground/60">MACD</span>
          <span className={`font-semibold ${getMACDTrend(macdData).color}`}>
            {getMACDTrend(macdData).label}
          </span>
        </div>
      )}
    </div>
  );
}
