"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const ADMIN_EMAIL = "horuseict@gmail.com";

async function apiFetch(path: string, token: string, options?: RequestInit) {
  const r = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options?.headers || {}),
    },
  });
  if (!r.ok) throw new Error(`Error ${r.status}`);
  return r.json();
}

interface Stats {
  total_users: number;
  plan_distribution: Record<string, number>;
  messages_today: number;
  total_conversations: number;
  total_messages_all_time: number;
  top_users_today: { user_id: string; message_count: number }[];
}

interface UserRow {
  user_id: string;
  email: string;
  plan: string;
  stripe_status: string;
  messages_today: number;
  created_at: string;
  period_end?: string;
}

interface Health {
  status: string;
  services: Record<string, string>;
  version: string;
}

const PLAN_COLORS: Record<string, string> = {
  admin: "bg-red-500/20 text-red-300 border-red-500/30",
  enterprise: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  pro: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30",
  free: "bg-slate-500/20 text-slate-300 border-slate-500/30",
};

const STATUS_COLOR: Record<string, string> = {
  ok: "text-green-400",
  configured: "text-green-400",
  "not configured": "text-yellow-400",
};

export default function AdminPanel() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [token, setToken] = useState<string>("");
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "users" | "health">("overview");
  const [planChanging, setPlanChanging] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!authLoading && (!user || user.email !== ADMIN_EMAIL)) {
      router.push("/");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (!user || user.email !== ADMIN_EMAIL) return;
    const getToken = async () => {
      const { supabase } = await import("@/lib/supabase");
      const { data } = await supabase.auth.getSession();
      const t = data.session?.access_token || "";
      setToken(t);
      return t;
    };
    getToken().then(async (t) => {
      if (!t) return;
      try {
        const [s, u, h] = await Promise.all([
          apiFetch("/admin/stats", t),
          apiFetch("/admin/users?limit=100", t),
          apiFetch("/admin/health", t),
        ]);
        setStats(s);
        setUsers(u.users || []);
        setHealth(h);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    });
  }, [user]);

  const handlePlanChange = async (userId: string, newPlan: string) => {
    if (!token) return;
    setPlanChanging(userId);
    try {
      await apiFetch(`/admin/users/${userId}/plan`, token, {
        method: "POST",
        body: JSON.stringify({ plan: newPlan }),
      });
      setUsers(prev => prev.map(u => u.user_id === userId ? { ...u, plan: newPlan } : u));
    } catch (e) {
      alert("Error cambiando plan");
    } finally {
      setPlanChanging(null);
    }
  };

  const handleResetUsage = async (userId: string) => {
    if (!token) return;
    try {
      await apiFetch(`/admin/users/${userId}/usage`, token, { method: "DELETE" });
      setUsers(prev => prev.map(u => u.user_id === userId ? { ...u, messages_today: 0 } : u));
    } catch {
      alert("Error reseteando uso");
    }
  };

  const filteredUsers = users.filter(u =>
    u.email.toLowerCase().includes(search.toLowerCase()) ||
    u.plan.includes(search.toLowerCase())
  );

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-pulse">👁</div>
          <p className="text-[#64748b] text-sm">Cargando panel de admin...</p>
        </div>
      </div>
    );
  }

  if (!user || user.email !== ADMIN_EMAIL) return null;

  return (
    <div className="h-screen overflow-y-auto bg-[#0a0a0f] text-[#e2e8f0]">
      {/* Header */}
      <header className="border-b border-[#1e1e2e] bg-[#12121a] px-4 sm:px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push("/")} className="text-[#64748b] hover:text-white text-sm">← HORUS</button>
            <span className="text-[#1e1e2e]">|</span>
            <div className="flex items-center gap-2">
              <span className="text-lg">🛡️</span>
              <h1 className="font-bold text-sm sm:text-base">Panel de Administración</h1>
          <a href="/admin/analytics"
            className="mt-1 inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-lg transition-colors">
            📊 Analytics →
          </a>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs text-[#64748b] hidden sm:inline">{health?.version || "—"}</span>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {[
              { label: "Usuarios", value: stats.total_users, icon: "👥", color: "border-indigo-500/30" },
              { label: "Pro", value: stats.plan_distribution.pro || 0, icon: "⚡", color: "border-purple-500/30" },
              { label: "Free", value: stats.plan_distribution.free || 0, icon: "🆓", color: "border-slate-500/30" },
              { label: "Msgs hoy", value: stats.messages_today, icon: "💬", color: "border-green-500/30" },
              { label: "Conversaciones", value: stats.total_conversations, icon: "📁", color: "border-teal-500/30" },
            ].map((card) => (
              <div key={card.label} className={`bg-[#12121a] border ${card.color} rounded-xl p-4`}>
                <div className="text-2xl mb-1">{card.icon}</div>
                <div className="text-xl sm:text-2xl font-bold">{card.value.toLocaleString()}</div>
                <div className="text-xs text-[#64748b] mt-0.5">{card.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 bg-[#12121a] border border-[#1e1e2e] rounded-xl p-1 w-fit">
          {(["overview", "users", "health"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-all capitalize
                ${activeTab === tab ? "bg-indigo-600 text-white" : "text-[#64748b] hover:text-white"}`}
            >
              {tab === "overview" ? "📊 Resumen" : tab === "users" ? "👥 Usuarios" : "🔧 Salud"}
            </button>
          ))}
        </div>

        {/* Tab: Overview */}
        {activeTab === "overview" && stats && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Plan distribution */}
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-4 text-[#94a3b8]">Distribución de Planes</h3>
              <div className="space-y-3">
                {Object.entries(stats.plan_distribution).map(([plan, count]) => {
                  const total = stats.total_users || 1;
                  const pct = Math.round((count / total) * 100);
                  return (
                    <div key={plan}>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="capitalize font-medium">{plan}</span>
                        <span className="text-[#64748b]">{count} usuarios ({pct}%)</span>
                      </div>
                      <div className="h-2 bg-[#1e1e2e] rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-600 rounded-full transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Top users today */}
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
              <h3 className="text-sm font-semibold mb-4 text-[#94a3b8]">Top Usuarios Hoy</h3>
              {stats.top_users_today.length === 0 ? (
                <p className="text-xs text-[#475569]">Sin actividad hoy aún.</p>
              ) : (
                <div className="space-y-2">
                  {stats.top_users_today.slice(0, 8).map((u, i) => (
                    <div key={u.user_id} className="flex items-center gap-3 text-xs">
                      <span className="text-[#475569] w-4">{i + 1}.</span>
                      <span className="font-mono text-[#64748b] truncate flex-1">
                        {u.user_id.slice(0, 16)}...
                      </span>
                      <span className="text-indigo-400 font-medium">{u.message_count} msgs</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab: Users */}
        {activeTab === "users" && (
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
            <div className="p-4 border-b border-[#1e1e2e] flex items-center gap-3">
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Buscar por email o plan..."
                className="flex-1 bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-3 py-1.5 text-xs text-[#e2e8f0]
                  placeholder:text-[#475569] outline-none focus:border-indigo-500/50"
              />
              <span className="text-xs text-[#64748b]">{filteredUsers.length} usuarios</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[#1e1e2e]">
                    {["Email", "Plan", "Msgs hoy", "Estado", "Acciones"].map(h => (
                      <th key={h} className="text-left px-4 py-3 text-[#64748b] font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((u) => (
                    <tr key={u.user_id} className="border-b border-[#1e1e2e]/50 hover:bg-[#0d0d14] transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-medium truncate max-w-[180px]">{u.email}</div>
                        <div className="text-[#475569] font-mono mt-0.5">{u.user_id.slice(0, 12)}...</div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded border text-xs font-medium capitalize ${PLAN_COLORS[u.plan] || PLAN_COLORS.free}`}>
                          {u.plan}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={u.messages_today > 40 ? "text-red-400" : "text-[#e2e8f0]"}>
                          {u.messages_today}
                        </span>
                        {u.plan === "free" && <span className="text-[#475569]">/50</span>}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs ${u.stripe_status === "active" ? "text-green-400" : "text-yellow-400"}`}>
                          {u.stripe_status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          {/* Cambiar plan */}
                          <select
                            value={u.plan}
                            disabled={planChanging === u.user_id}
                            onChange={e => handlePlanChange(u.user_id, e.target.value)}
                            className="bg-[#1e1e2e] border border-[#2e2e4e] rounded px-2 py-1 text-xs text-[#e2e8f0]
                              outline-none cursor-pointer hover:border-indigo-500/50 disabled:opacity-50"
                          >
                            <option value="free">Free</option>
                            <option value="pro">Pro</option>
                            <option value="enterprise">Enterprise</option>
                            <option value="admin">Admin</option>
                          </select>
                          {/* Reset uso */}
                          <button
                            onClick={() => handleResetUsage(u.user_id)}
                            title="Resetear uso diario"
                            className="text-[#64748b] hover:text-yellow-400 transition-colors px-1.5 py-1 rounded
                              border border-[#1e1e2e] hover:border-yellow-500/30"
                          >
                            ↺
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredUsers.length === 0 && (
                <div className="text-center text-[#475569] text-xs py-8">Sin resultados.</div>
              )}
            </div>
          </div>
        )}

        {/* Tab: Health */}
        {activeTab === "health" && health && (
          <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
            <h3 className="text-sm font-semibold mb-4 text-[#94a3b8]">Estado de Servicios</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {Object.entries(health.services).map(([service, status]) => (
                <div key={service} className="flex items-center justify-between bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-3">
                  <span className="text-xs font-medium capitalize">{service.replace(/_/g, " ")}</span>
                  <span className={`text-xs font-mono ${STATUS_COLOR[status] || "text-red-400"}`}>
                    {status === "ok" ? "✅ ok" : status === "configured" ? "✅ activo" : status === "not configured" ? "⚠️ no configurado" : `❌ ${status}`}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
