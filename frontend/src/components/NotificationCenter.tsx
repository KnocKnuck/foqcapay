/**
 * Notification Center
 *
 * Centralized panel for viewing all notifications, alerts, and errors.
 *
 * Agent: UI Development Agent
 * Squad: UX
 * Sprint: Enhancement Phase
 *
 * Features:
 * - All notifications in one place
 * - Filter by type (signals, errors, warnings, info)
 * - Mark as read/unread
 * - Clear all or individual notifications
 * - Real-time updates via WebSocket
 * - Notification badge count
 * - Time-based grouping
 *
 * @component
 * @example
 * <NotificationCenter />
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  Bell,
  BellOff,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Zap,
  Trash2,
  Check,
  Filter,
} from "lucide-react";

interface Notification {
  id: string;
  type: "signal" | "error" | "warning" | "info" | "success";
  category: string; // 'trading', 'system', 'risk', 'api'
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  data?: any; // Additional data
}

/**
 * Notification center component.
 */
export function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filterType, setFilterType] = useState<string>("all");
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Load saved notifications from localStorage
    const saved = localStorage.getItem("notifications");
    if (saved) {
      try {
        setNotifications(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to load notifications:", e);
      }
    }

    // Connect to WebSocket for real-time notifications
    connectWebSocket();
  }, []);

  // Save notifications to localStorage
  useEffect(() => {
    localStorage.setItem("notifications", JSON.stringify(notifications));
  }, [notifications]);

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/ws/notifications-${Date.now()}`);

    ws.onopen = () => {
      setWsConnected(true);
      // Subscribe to all notification topics
      ws.send(JSON.stringify({ action: "subscribe", topic: "notifications.*" }));
      ws.send(JSON.stringify({ action: "subscribe", topic: "signals.all" }));
      ws.send(JSON.stringify({ action: "subscribe", topic: "risk.alert.*" }));
      ws.send(JSON.stringify({ action: "subscribe", topic: "error.*" }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      // Create notification from WebSocket message
      let notification: Notification | null = null;

      if (message.type?.includes("signal")) {
        notification = {
          id: `notif-${Date.now()}-${Math.random()}`,
          type: "signal",
          category: "trading",
          title: `${message.indicator} Signal`,
          message: `${message.data.signal_type} detected on ${message.data.pair}`,
          timestamp: message.data.timestamp || new Date().toISOString(),
          read: false,
          data: message.data,
        };
      } else if (message.type === "risk_alert") {
        notification = {
          id: `notif-${Date.now()}-${Math.random()}`,
          type: "warning",
          category: "risk",
          title: "Risk Alert",
          message: message.message || "Risk threshold exceeded",
          timestamp: message.timestamp || new Date().toISOString(),
          read: false,
          data: message.data,
        };
      } else if (message.type === "error") {
        notification = {
          id: `notif-${Date.now()}-${Math.random()}`,
          type: "error",
          category: message.category || "system",
          title: "Error",
          message: message.error || message.message || "An error occurred",
          timestamp: message.timestamp || new Date().toISOString(),
          read: false,
          data: message,
        };
      } else if (message.type === "trade_executed") {
        notification = {
          id: `notif-${Date.now()}-${Math.random()}`,
          type: "success",
          category: "trading",
          title: "Trade Executed",
          message: `${message.data.side.toUpperCase()} ${message.data.pair} @ $${message.data.price}`,
          timestamp: message.data.timestamp || new Date().toISOString(),
          read: false,
          data: message.data,
        };
      }

      if (notification) {
        setNotifications((prev) => [notification!, ...prev].slice(0, 500)); // Keep last 500
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      setTimeout(connectWebSocket, 3000);
    };
  };

  // Filter notifications
  const filteredNotifications = notifications.filter((notif) => {
    if (showUnreadOnly && notif.read) return false;
    if (filterType !== "all" && notif.type !== filterType) return false;
    return true;
  });

  // Mark as read
  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((notif) => (notif.id === id ? { ...notif, read: true } : notif))
    );
  };

  // Mark all as read
  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((notif) => ({ ...notif, read: true })));
  };

  // Delete notification
  const deleteNotification = (id: string) => {
    setNotifications((prev) => prev.filter((notif) => notif.id !== id));
  };

  // Clear all
  const clearAll = () => {
    if (confirm("Clear all notifications?")) {
      setNotifications([]);
    }
  };

  // Get unread count
  const unreadCount = notifications.filter((n) => !n.read).length;

  // Notification config
  const getNotificationConfig = (type: string) => {
    const configs: Record<string, { icon: any; color: string }> = {
      signal: { icon: Zap, color: "text-primary" },
      error: { icon: XCircle, color: "text-danger" },
      warning: { icon: AlertTriangle, color: "text-warning" },
      info: { icon: Info, color: "text-foreground" },
      success: { icon: CheckCircle2, color: "text-success" },
    };

    return configs[type] || { icon: Bell, color: "text-foreground" };
  };

  return (
    <div className="h-full flex flex-col bg-bg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <Bell className="h-6 w-6 text-primary" />
          <div>
            <h2 className="text-xl font-semibold text-foreground">
              Notifications
            </h2>
            <p className="text-sm text-foreground/60">
              {unreadCount > 0 ? `${unreadCount} unread` : "All caught up"}
            </p>
          </div>
        </div>

        {/* Connection Status */}
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

      {/* Actions */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-panel">
        <div className="flex items-center gap-3">
          {/* Filter by type */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-foreground/60" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-1.5 bg-bg border border-border rounded-lg text-foreground text-sm"
            >
              <option value="all">All Types</option>
              <option value="signal">Signals</option>
              <option value="error">Errors</option>
              <option value="warning">Warnings</option>
              <option value="info">Info</option>
              <option value="success">Success</option>
            </select>
          </div>

          {/* Show unread only */}
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showUnreadOnly}
              onChange={(e) => setShowUnreadOnly(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-foreground/70">Unread only</span>
          </label>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={markAllAsRead}
            className="px-3 py-1.5 text-sm text-foreground/70 hover:text-foreground transition-colors flex items-center gap-2"
            disabled={unreadCount === 0}
          >
            <Check className="h-4 w-4" />
            Mark all read
          </button>

          <button
            onClick={clearAll}
            className="px-3 py-1.5 text-sm text-danger/70 hover:text-danger transition-colors flex items-center gap-2"
            disabled={notifications.length === 0}
          >
            <Trash2 className="h-4 w-4" />
            Clear all
          </button>
        </div>
      </div>

      {/* Notification List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {filteredNotifications.length === 0 ? (
          <div className="text-center py-12">
            <BellOff className="h-12 w-12 text-foreground/30 mx-auto mb-3" />
            <p className="text-foreground/60">
              {showUnreadOnly
                ? "No unread notifications"
                : "No notifications yet"}
            </p>
          </div>
        ) : (
          filteredNotifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onMarkAsRead={markAsRead}
              onDelete={deleteNotification}
              getConfig={getNotificationConfig}
            />
          ))
        )}
      </div>
    </div>
  );
}

// Individual notification item
function NotificationItem({
  notification,
  onMarkAsRead,
  onDelete,
  getConfig,
}: {
  notification: Notification;
  onMarkAsRead: (id: string) => void;
  onDelete: (id: string) => void;
  getConfig: (type: string) => any;
}) {
  const config = getConfig(notification.type);
  const Icon = config.icon;

  // Time ago calculation
  const getTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <div
      className={`p-3 rounded-lg border transition-colors ${
        notification.read
          ? "bg-panel/50 border-border/50"
          : "bg-panel border-border"
      }`}
      onClick={() => !notification.read && onMarkAsRead(notification.id)}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <Icon className={`h-5 w-5 ${config.color} flex-shrink-0 mt-0.5`} />

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between mb-1">
            <h4 className="text-sm font-semibold text-foreground">
              {notification.title}
            </h4>
            <span className="text-xs text-foreground/60 flex-shrink-0 ml-2">
              {getTimeAgo(notification.timestamp)}
            </span>
          </div>

          <p className="text-sm text-foreground/70">{notification.message}</p>

          {/* Category badge */}
          <div className="flex items-center gap-2 mt-2">
            <span className="px-2 py-0.5 rounded text-xs bg-bg text-foreground/60">
              {notification.category}
            </span>

            {!notification.read && (
              <span className="px-2 py-0.5 rounded text-xs bg-primary/20 text-primary font-semibold">
                NEW
              </span>
            )}
          </div>
        </div>

        {/* Delete button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(notification.id);
          }}
          className="text-foreground/40 hover:text-danger transition-colors flex-shrink-0"
          aria-label="Delete"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
