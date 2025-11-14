/**
 * Utility functions for the frontend.
 *
 * Agent: UI Development Agent
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with proper precedence.
 *
 * Combines clsx and tailwind-merge for optimal class handling.
 *
 * @param inputs - Class values to merge
 * @returns Merged class string
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as currency (USD).
 *
 * @param value - Number to format
 * @returns Formatted currency string (e.g., "$30,125.50")
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

/**
 * Format a percentage.
 *
 * @param value - Number to format as percentage
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted percentage string (e.g., "+2.34%")
 */
export function formatPercentage(value: number, decimals: number = 2): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}%`;
}

/**
 * Normalize a trading pair for API/topic use.
 *
 * Example: "BTC/USDC" -> "btcusdc"
 *
 * @param pair - Trading pair (e.g., "BTC/USDC")
 * @returns Normalized pair string
 */
export function normalizePair(pair: string): string {
  return pair.replace("/", "").toLowerCase();
}
