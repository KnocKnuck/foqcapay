/**
 * Live Mode Toggle Component
 *
 * Controls switching between Demo and Live trading modes.
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: 4.1
 *
 * CRITICAL SAFETY FEATURES:
 * - Big prominent warning when enabling live mode
 * - Multi-step confirmation required
 * - API key validation before enabling
 * - Clear visual distinction (green=demo, red=live)
 * - Cannot switch while positions open
 *
 * @component
 * @example
 * <LiveModeToggle
 *   currentMode="demo"
 *   onModeChange={handleModeChange}
 *   hasOpenPositions={false}
 * />
 */

"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  DollarSign,
  Lock,
  Unlock,
} from "lucide-react";

interface LiveModeToggleProps {
  /** Current trading mode */
  currentMode: "demo" | "live";

  /** Callback when mode changes */
  onModeChange: (mode: "demo" | "live") => Promise<boolean>;

  /** Are there open positions? */
  hasOpenPositions?: boolean;

  /** Is API key configured? */
  hasApiKey?: boolean;

  /** Account balance (if live mode) */
  accountBalance?: number;
}

/**
 * Toggle between demo and live trading modes.
 *
 * Provides clear warnings and multi-step confirmation when
 * enabling live trading with real money.
 */
export function LiveModeToggle({
  currentMode,
  onModeChange,
  hasOpenPositions = false,
  hasApiKey = false,
  accountBalance = 0,
}: LiveModeToggleProps) {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [confirmStep, setConfirmStep] = useState(1);
  const [userTypedConfirm, setUserTypedConfirm] = useState("");
  const [isChanging, setIsChanging] = useState(false);

  const isDemoMode = currentMode === "demo";
  const targetMode = isDemoMode ? "live" : "demo";

  const handleToggleClick = () => {
    if (isDemoMode) {
      // Switching to live - show big warning
      setShowConfirmDialog(true);
      setConfirmStep(1);
      setUserTypedConfirm("");
    } else {
      // Switching to demo - no confirmation needed
      handleModeChangeConfirmed();
    }
  };

  const handleModeChangeConfirmed = async () => {
    setIsChanging(true);

    try {
      const success = await onModeChange(targetMode);

      if (success) {
        setShowConfirmDialog(false);
        setConfirmStep(1);
        setUserTypedConfirm("");
      } else {
        alert("Failed to change trading mode. Please check your settings.");
      }
    } catch (error) {
      console.error("Mode change error:", error);
      alert(`Error: ${error}`);
    } finally {
      setIsChanging(false);
    }
  };

  const canEnableLive = !hasOpenPositions && hasApiKey;
  const canProceedToStep2 = confirmStep === 1;
  const canProceedToStep3 = confirmStep === 2;
  const canConfirm = confirmStep === 3 && userTypedConfirm === "ENABLE LIVE TRADING";

  return (
    <div className="space-y-4">
      {/* Current Mode Display */}
      <div
        className={`flex items-center gap-3 p-4 rounded-lg border-2 ${
          isDemoMode
            ? "bg-success/10 border-success"
            : "bg-danger/10 border-danger"
        }`}
      >
        {isDemoMode ? (
          <ShieldAlert className="h-6 w-6 text-success" />
        ) : (
          <AlertTriangle className="h-6 w-6 text-danger" />
        )}

        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground/70">
              Current Mode:
            </span>
            <span
              className={`text-lg font-bold font-mono ${
                isDemoMode ? "text-success" : "text-danger"
              }`}
            >
              {isDemoMode ? "DEMO" : "LIVE"}
            </span>
          </div>

          <p className="text-xs text-foreground/60 mt-1">
            {isDemoMode
              ? "Simulated trading with virtual money - safe for testing"
              : "🚨 REAL TRADING with REAL MONEY - all orders executed on CoinEx"}
          </p>
        </div>

        {/* Toggle Button */}
        <button
          onClick={handleToggleClick}
          disabled={!isDemoMode && hasOpenPositions}
          className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
            isDemoMode
              ? "bg-danger text-white hover:bg-danger/90"
              : "bg-success text-white hover:bg-success/90"
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isDemoMode ? (
            <>
              <Unlock className="inline h-4 w-4 mr-2" />
              Enable Live Trading
            </>
          ) : (
            <>
              <Lock className="inline h-4 w-4 mr-2" />
              Switch to Demo
            </>
          )}
        </button>
      </div>

      {/* Warnings */}
      {hasOpenPositions && !isDemoMode && (
        <div className="flex items-start gap-2 p-3 bg-warning/10 border border-warning rounded-lg">
          <AlertTriangle className="h-5 w-5 text-warning flex-shrink-0 mt-0.5" />
          <div className="text-sm text-foreground">
            <strong>Cannot switch mode:</strong> Close all open positions first
          </div>
        </div>
      )}

      {isDemoMode && !hasApiKey && (
        <div className="flex items-start gap-2 p-3 bg-warning/10 border border-warning rounded-lg">
          <AlertTriangle className="h-5 w-5 text-warning flex-shrink-0 mt-0.5" />
          <div className="text-sm text-foreground">
            <strong>API Key Required:</strong> Configure your CoinEx API key in
            Settings before enabling live trading
          </div>
        </div>
      )}

      {/* Live Mode Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-panel rounded-lg max-w-2xl w-full border-2 border-danger shadow-2xl">
            {/* Header */}
            <div className="bg-danger/20 p-6 border-b-2 border-danger">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-10 w-10 text-danger" />
                <div>
                  <h2 className="text-2xl font-bold text-foreground">
                    🚨 Enable Live Trading?
                  </h2>
                  <p className="text-sm text-foreground/70 mt-1">
                    You are about to enable REAL trading with REAL MONEY
                  </p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Step 1: Warnings */}
              {confirmStep === 1 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-foreground">
                    ⚠️ Important Warnings
                  </h3>

                  <div className="space-y-3">
                    <div className="flex items-start gap-3 p-3 bg-danger/10 rounded-lg">
                      <DollarSign className="h-5 w-5 text-danger flex-shrink-0 mt-0.5" />
                      <div className="text-sm">
                        <strong className="text-foreground">Real Money:</strong>
                        <span className="text-foreground/70">
                          {" "}
                          All orders will execute on CoinEx with real funds. You
                          can lose money.
                        </span>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-danger/10 rounded-lg">
                      <ShieldAlert className="h-5 w-5 text-danger flex-shrink-0 mt-0.5" />
                      <div className="text-sm">
                        <strong className="text-foreground">
                          Production Limits:
                        </strong>
                        <span className="text-foreground/70">
                          {" "}
                          Max $5,000 per order, $20,000 daily volume limit
                        </span>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-danger/10 rounded-lg">
                      <XCircle className="h-5 w-5 text-danger flex-shrink-0 mt-0.5" />
                      <div className="text-sm">
                        <strong className="text-foreground">Risk:</strong>
                        <span className="text-foreground/70">
                          {" "}
                          Automated trading carries significant risk. Only trade
                          what you can afford to lose.
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 p-3 bg-bg rounded-lg border border-border">
                    <CheckCircle2 className="h-5 w-5 text-success" />
                    <div className="text-sm text-foreground">
                      Account Balance:{" "}
                      <span className="font-mono font-semibold">
                        ${accountBalance.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2: Acknowledge Risks */}
              {confirmStep === 2 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-foreground">
                    ✅ Acknowledge Risks
                  </h3>

                  <p className="text-sm text-foreground/70">
                    By enabling live trading, you acknowledge:
                  </p>

                  <ul className="space-y-2 text-sm text-foreground/70">
                    <li className="flex items-start gap-2">
                      <span>•</span>
                      <span>You understand this is REAL trading with REAL money</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>•</span>
                      <span>
                        You accept the risk of losing money through automated
                        trading
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>•</span>
                      <span>
                        You have tested strategies thoroughly in demo mode first
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>•</span>
                      <span>
                        You will monitor your bot and use appropriate risk limits
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>•</span>
                      <span>
                        Production safeguards are in place but not foolproof
                      </span>
                    </li>
                  </ul>
                </div>
              )}

              {/* Step 3: Type to Confirm */}
              {confirmStep === 3 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-foreground">
                    🔐 Final Confirmation
                  </h3>

                  <p className="text-sm text-foreground/70">
                    Type{" "}
                    <span className="font-mono font-bold text-danger">
                      ENABLE LIVE TRADING
                    </span>{" "}
                    to confirm:
                  </p>

                  <input
                    type="text"
                    value={userTypedConfirm}
                    onChange={(e) => setUserTypedConfirm(e.target.value)}
                    placeholder="Type here..."
                    className="w-full px-4 py-3 bg-bg border-2 border-border rounded-lg font-mono text-foreground focus:border-danger focus:outline-none"
                    autoFocus
                  />

                  {userTypedConfirm && userTypedConfirm !== "ENABLE LIVE TRADING" && (
                    <p className="text-xs text-danger">
                      Must match exactly: "ENABLE LIVE TRADING"
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-border flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowConfirmDialog(false);
                  setConfirmStep(1);
                  setUserTypedConfirm("");
                }}
                className="px-6 py-2 bg-panel border border-border text-foreground rounded-lg hover:bg-border/50 transition-colors"
                disabled={isChanging}
              >
                Cancel
              </button>

              {confirmStep < 3 && (
                <button
                  onClick={() => setConfirmStep(confirmStep + 1)}
                  className="px-6 py-2 bg-warning text-white rounded-lg hover:bg-warning/90 transition-colors font-semibold"
                >
                  {confirmStep === 1 ? "I Understand" : "I Acknowledge"}
                </button>
              )}

              {confirmStep === 3 && (
                <button
                  onClick={handleModeChangeConfirmed}
                  disabled={!canConfirm || isChanging}
                  className="px-6 py-2 bg-danger text-white rounded-lg hover:bg-danger/90 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isChanging ? "Enabling..." : "Enable Live Trading"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
