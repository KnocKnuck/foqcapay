"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [apiStatus, setApiStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
      <div className="max-w-5xl w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-4">
            🤖 FOQCAPAY Trading Bot
          </h1>
          <p className="text-xl text-foreground/70">
            Multi-Agent Crypto Trading System
          </p>
        </div>

        {/* Status Card */}
        <div className="bg-panel p-8 rounded-lg border border-border">
          <h2 className="text-2xl font-semibold mb-4">System Status</h2>

          {loading ? (
            <p className="text-foreground/60">Connecting to backend...</p>
          ) : apiStatus ? (
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="font-medium">Status:</span>
                <span className="text-success">✓ {apiStatus.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Version:</span>
                <span>{apiStatus.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Mode:</span>
                <span className="uppercase font-mono bg-primary/10 px-2 py-1 rounded">
                  {apiStatus.mode}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Sprint:</span>
                <span>{apiStatus.sprint}</span>
              </div>
              <div className="mt-4 pt-4 border-t border-border">
                <p className="font-medium mb-2">Trading Pairs:</p>
                <div className="flex gap-2 flex-wrap">
                  {apiStatus.trading_pairs?.map((pair: string) => (
                    <span
                      key={pair}
                      className="bg-success/10 text-success px-3 py-1 rounded-md font-mono text-sm"
                    >
                      {pair}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-danger">
              <p>❌ Failed to connect to backend</p>
              <p className="text-sm mt-2 text-foreground/60">
                Make sure the backend is running on http://localhost:8000
              </p>
            </div>
          )}
        </div>

        {/* Quick Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-panel p-6 rounded-lg border border-border">
            <h3 className="font-semibold mb-2">📊 25 Agents</h3>
            <p className="text-sm text-foreground/70">
              Specialized agents working in parallel
            </p>
          </div>

          <div className="bg-panel p-6 rounded-lg border border-border">
            <h3 className="font-semibold mb-2">⚡ Multi-Pair</h3>
            <p className="text-sm text-foreground/70">
              BTC, ETH, LINK and more
            </p>
          </div>

          <div className="bg-panel p-6 rounded-lg border border-border">
            <h3 className="font-semibold mb-2">🛡️ Demo Mode</h3>
            <p className="text-sm text-foreground/70">
              Risk-free paper trading
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-foreground/50">
          <p>Sprint 1.2 - Infrastructure Setup</p>
          <p className="mt-1">Full dashboard coming soon! 🚀</p>
        </div>
      </div>
    </main>
  );
}
