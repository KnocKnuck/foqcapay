/**
 * Price Ticker Component
 *
 * Displays live price for selected trading pair with 24h change indicator.
 * Updates in real-time (<1s latency target).
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: 1.2
 *
 * @component
 * @example
 * <PriceTicker
 *   pair="BTC/USDC"
 *   price={30125.50}
 *   change24h={2.34}
 *   volume24h={1234567.89}
 * />
 */

"use client";

import React from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { formatCurrency, formatPercentage } from "@/lib/utils";

interface PriceTickerProps {
  /** Trading pair (e.g., "BTC/USDC") */
  pair: string;

  /** Current price */
  price: number;

  /** 24-hour change percentage */
  change24h: number;

  /** 24-hour trading volume (optional) */
  volume24h?: number;

  /** Loading state (optional) */
  loading?: boolean;
}

/**
 * Real-time price ticker with 24h change indicator.
 *
 * Displays price with color-coded change (green=up, red=down)
 * and optional 24h volume.
 */
export function PriceTicker({
  pair,
  price,
  change24h,
  volume24h,
  loading = false,
}: PriceTickerProps) {
  const isPositive = change24h >= 0;

  if (loading) {
    return (
      <div className="flex items-center gap-4">
        <div className="h-8 w-32 animate-pulse bg-panel rounded" />
        <div className="h-6 w-20 animate-pulse bg-panel rounded" />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-6">
      {/* Pair Name */}
      <div className="flex flex-col">
        <span className="text-sm text-foreground/60">Pair</span>
        <span className="text-lg font-bold font-mono">{pair}</span>
      </div>

      {/* Current Price */}
      <div className="flex flex-col">
        <span className="text-sm text-foreground/60">Price</span>
        <span className="text-2xl font-bold font-mono">
          {formatCurrency(price)}
        </span>
      </div>

      {/* 24h Change */}
      <div className="flex flex-col">
        <span className="text-sm text-foreground/60">24h Change</span>
        <div
          className={`flex items-center gap-1 text-lg font-semibold ${
            isPositive ? "text-success" : "text-danger"
          }`}
        >
          {isPositive ? (
            <TrendingUp className="h-5 w-5" />
          ) : (
            <TrendingDown className="h-5 w-5" />
          )}
          <span>{formatPercentage(change24h)}</span>
        </div>
      </div>

      {/* 24h Volume (Optional) */}
      {volume24h !== undefined && (
        <div className="flex flex-col">
          <span className="text-sm text-foreground/60">24h Volume</span>
          <span className="text-lg font-mono">
            {formatCurrency(volume24h)}
          </span>
        </div>
      )}
    </div>
  );
}
