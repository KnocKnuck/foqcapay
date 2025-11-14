/**
 * Pair Selector Component
 *
 * Dropdown for selecting trading pairs (BTC/USDC, ETH/USDC, LINK/USDC, etc.)
 * Supports multi-pair trading from day one!
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: 1.2
 *
 * @component
 * @example
 * <PairSelector
 *   pairs={["BTC/USDC", "ETH/USDC", "LINK/USDC"]}
 *   selectedPair="BTC/USDC"
 *   onPairChange={(pair) => console.log("Selected:", pair)}
 * />
 */

"use client";

import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface PairSelectorProps {
  /** List of available trading pairs */
  pairs: string[];

  /** Currently selected pair */
  selectedPair?: string;

  /** Callback when user selects a different pair */
  onPairChange: (pair: string) => void;

  /** Optional CSS class name */
  className?: string;
}

/**
 * Trading pair selector dropdown.
 *
 * Displays available pairs with visual styling and allows
 * switching between them for multi-pair trading support.
 */
export function PairSelector({
  pairs,
  selectedPair,
  onPairChange,
  className = "",
}: PairSelectorProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <label className="text-sm font-medium text-foreground/70">
        Pair:
      </label>
      <Select value={selectedPair} onValueChange={onPairChange}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Select pair" />
        </SelectTrigger>
        <SelectContent>
          {pairs.map((pair) => (
            <SelectItem key={pair} value={pair}>
              <span className="font-mono font-semibold">{pair}</span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
