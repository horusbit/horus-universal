"use client";

import { createContext, useContext, useState, useCallback, useRef, ReactNode } from "react";

export type ToastType = "success" | "error" | "info" | "warning";

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

interface ToastContextValue {
  toasts: Toast[];
  showToast: (message: string, type?: ToastType, duration?: number) => void;
  dismissToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue>({
  toasts: [],
  showToast: () => {},
  dismissToast: () => {},
});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismissToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) { clearTimeout(timer); timersRef.current.delete(id); }
  }, []);

  const showToast = useCallback((message: string, type: ToastType = "info", duration = 4000) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    setToasts(prev => [...prev.slice(-4), { id, message, type, duration }]);
    const timer = setTimeout(() => dismissToast(id), duration);
    timersRef.current.set(id, timer);
  }, [dismissToast]);

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);

// ── Toast Container UI ────────────────────────────────────────────────────────

const ICONS: Record<ToastType, string> = {
  success: "✓",
  error: "✕",
  info: "ℹ",
  warning: "⚠",
};

const COLORS: Record<ToastType, string> = {
  success: "bg-green-500/10 border-green-500/30 text-green-300",
  error: "bg-red-500/10 border-red-500/30 text-red-300",
  info: "bg-indigo-500/10 border-indigo-500/30 text-indigo-300",
  warning: "bg-amber-500/10 border-amber-500/30 text-amber-300",
};

const ICON_COLORS: Record<ToastType, string> = {
  success: "text-green-400",
  error: "text-red-400",
  info: "text-indigo-400",
  warning: "text-amber-400",
};

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: string) => void }) {
  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl border shadow-2xl max-w-sm min-w-[260px] animate-in slide-in-from-right-4 fade-in duration-200 ${COLORS[toast.type]}`}
          style={{ animation: "slideIn 0.2s ease-out" }}
        >
          <span className={`text-sm font-bold mt-0.5 flex-shrink-0 ${ICON_COLORS[toast.type]}`}>
            {ICONS[toast.type]}
          </span>
          <p className="text-sm flex-1 leading-snug">{toast.message}</p>
          <button
            onClick={() => onDismiss(toast.id)}
            className="text-[#475569] hover:text-white transition-colors flex-shrink-0 ml-1"
          >
            ×
          </button>
        </div>
      ))}
      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(16px); }
          to { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}
