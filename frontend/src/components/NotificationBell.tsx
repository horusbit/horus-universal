"use client";

import { useState, useEffect, useRef } from "react";

export interface AppNotification {
  id: string;
  title: string;
  body: string;
  type: "info" | "success" | "warning" | "agent";
  icon?: string;
  read: boolean;
  createdAt: Date;
  action?: { label: string; href: string };
}

const STORAGE_KEY = "horus_notifications";

function loadNotifications(): AppNotification[] {
  try {
    const raw = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
    if (!raw) return [];
    return JSON.parse(raw).map((n: any) => ({ ...n, createdAt: new Date(n.createdAt) }));
  } catch { return []; }
}

function saveNotifications(notifs: AppNotification[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(notifs.slice(0, 50))); } catch {}
}

// Public API — other components can call this to push a notification
export function pushNotification(notif: Omit<AppNotification, "id" | "read" | "createdAt">) {
  const existing = loadNotifications();
  const newNotif: AppNotification = {
    ...notif,
    id: `notif-${Date.now()}`,
    read: false,
    createdAt: new Date(),
  };
  saveNotifications([newNotif, ...existing]);
  // Dispatch event so the bell updates in real-time
  window.dispatchEvent(new CustomEvent("horus:notification", { detail: newNotif }));
}

export default function NotificationBell() {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  useEffect(() => {
    setNotifications(loadNotifications());

    const handleNew = () => setNotifications(loadNotifications());
    window.addEventListener("horus:notification", handleNew);
    return () => window.removeEventListener("horus:notification", handleNew);
  }, []);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const markAllRead = () => {
    const updated = notifications.map(n => ({ ...n, read: true }));
    setNotifications(updated);
    saveNotifications(updated);
  };

  const clearAll = () => {
    setNotifications([]);
    saveNotifications([]);
  };

  const markRead = (id: string) => {
    const updated = notifications.map(n => n.id === id ? { ...n, read: true } : n);
    setNotifications(updated);
    saveNotifications(updated);
  };

  const TYPE_ICONS: Record<string, string> = {
    info: "ℹ️",
    success: "✅",
    warning: "⚠️",
    agent: "🤖",
  };

  const timeAgo = (date: Date) => {
    const s = Math.floor((Date.now() - date.getTime()) / 1000);
    if (s < 60) return "ahora";
    if (s < 3600) return `${Math.floor(s / 60)}m`;
    if (s < 86400) return `${Math.floor(s / 3600)}h`;
    return `${Math.floor(s / 86400)}d`;
  };

  return (
    <div ref={ref} className="relative flex-shrink-0">
      {/* Bell button */}
      <button
        onClick={() => { setOpen(o => !o); if (!open && unreadCount > 0) markAllRead(); }}
        className="relative w-8 h-8 flex items-center justify-center text-[#64748b] hover:text-white hover:bg-[#1e1e2e] rounded-lg transition-colors"
        title="Notificaciones"
      >
        <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-indigo-500 rounded-full text-[9px] font-bold text-white flex items-center justify-center">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-10 w-80 bg-[#0d0d14] border border-[#1e1e2e] rounded-2xl shadow-2xl z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e1e2e]">
            <span className="text-sm font-semibold">Notificaciones</span>
            <div className="flex gap-2">
              {notifications.length > 0 && (
                <>
                  <button onClick={markAllRead} className="text-[10px] text-[#64748b] hover:text-indigo-400 transition-colors">
                    Marcar todo leído
                  </button>
                  <span className="text-[#1e1e2e]">·</span>
                  <button onClick={clearAll} className="text-[10px] text-[#64748b] hover:text-red-400 transition-colors">
                    Limpiar
                  </button>
                </>
              )}
            </div>
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="py-10 text-center">
                <div className="text-3xl mb-2">🔔</div>
                <p className="text-xs text-[#475569]">Sin notificaciones aún</p>
              </div>
            ) : (
              notifications.map(notif => (
                <div
                  key={notif.id}
                  onClick={() => markRead(notif.id)}
                  className={`flex gap-3 px-4 py-3 border-b border-[#1e1e2e] last:border-0 cursor-pointer hover:bg-[#12121a] transition-colors ${!notif.read ? "bg-indigo-500/5" : ""}`}
                >
                  <span className="text-base flex-shrink-0 mt-0.5">
                    {notif.icon || TYPE_ICONS[notif.type] || "🔔"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-xs font-semibold ${!notif.read ? "text-[#e2e8f0]" : "text-[#94a3b8]"}`}>
                        {notif.title}
                      </p>
                      <span className="text-[10px] text-[#475569] flex-shrink-0">{timeAgo(notif.createdAt)}</span>
                    </div>
                    <p className="text-[11px] text-[#64748b] mt-0.5 leading-snug">{notif.body}</p>
                    {notif.action && (
                      <a
                        href={notif.action.href}
                        className="text-[11px] text-indigo-400 hover:text-indigo-300 mt-1 inline-block"
                        onClick={e => e.stopPropagation()}
                      >
                        {notif.action.label} →
                      </a>
                    )}
                  </div>
                  {!notif.read && (
                    <div className="w-2 h-2 bg-indigo-400 rounded-full flex-shrink-0 mt-1.5" />
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
