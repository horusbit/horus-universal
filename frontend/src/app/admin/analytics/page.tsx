"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const ADMIN_EMAIL = "horuseict@gmail.com";

async function fetchAnalytics(token: string, days = 30) {
  const r = await fetch(`${API_URL}/api/v1/admin/analytics?days=${days}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error("Error cargando analytics");
  return r.json();
}

interface TimelinePoint { date: string; messages: number; active_users: number; }
interface AgentStat { agent: string; count: number; }
interface Analytics {
  period_days: number;
  timeline: TimelinePoint[];
  top_agents: AgentStat[];
  total_pro_users: number;
  new_users_period: number;
  new_conversions_period: number;
  summary: { total_messages_period: number; peak_day: string | null; avg_daily_messages: number };
}

const AGENT_ICONS: Record<string, string> = {
  atlas: "🌐", cipher: "⚡", nova: "✨", lexis: "⚖️", oracle: "🔮",
  hermes: "🌍", echo: "🎙️", darwin: "🔬", pixel: "🎨", nexus: "📡",
  forge: "📊", sage: "🎓", vector: "💼", chronos: "⏱️", politeia: "🏛️", educraft: "🏫",
};

export default function AnalyticsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<Analytics | null>(null);
  const [days, setDays] = useState(30);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!loading && (!user || (user as any).email !== ADMIN_EMAIL)) router.push("/");
  }, [user, loading, router]);

  useEffect(() => {
    if (!user) return;
    const token = (user as any).access_token;
    if (!token) return;
    setIsLoading(true);
    setError("");
    fetchAnalytics(token, days)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setIsLoading(false));
  }, [user, days]);

  if (loading || !user) return null;

  const maxMsg = data ? Math.max(...data.timeline.map(t => t.messages), 1) : 1;
  const maxUsers = data ? Math.max(...data.timeline.map(t => t.active_users), 1) : 1;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#e2e8f0] p-4 sm:p-6">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <button onClick={() => router.push("/admin")}
              className="text-xs text-[#64748b] hover:text-white mb-1 block">← Panel Admin</button>
            <h1 className="text-2xl font-bold">📊 Analytics</h1>
            <p className="text-[#64748b] text-sm">Métricas de uso · HORUS Universal</p>
          </div>
          <div className="flex gap-2">
            {[7, 14, 30, 90].map(d => (
              <button key={d} onClick={() => setDays(d)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                  ${days === d
                    ? "bg-indigo-600 border-indigo-500 text-white"
                    : "bg-[#12121a] border-[#1e1e2e] text-[#64748b] hover:text-white hover:border-indigo-500/40"
                  }`}>
                {d}d
              </button>
            ))}
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-sm">{error}</div>
        ) : data ? (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: "Mensajes", sublabel: `últimos ${days}d`, value: data.summary.total_messages_period.toLocaleString(), icon: "💬", accent: "indigo" },
                { label: "Promedio/día", sublabel: "mensajes", value: data.summary.avg_daily_messages.toString(), icon: "📈", accent: "purple" },
                { label: "Nuevos usuarios", sublabel: `últimos ${days}d`, value: data.new_users_period.toString(), icon: "👤", accent: "green" },
                { label: "Usuarios Pro", sublabel: "total acumulado", value: data.total_pro_users.toString(), icon: "⚡", accent: "amber" },
              ].map(kpi => (
                <div key={kpi.label} className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
                  <div className="text-xl mb-2">{kpi.icon}</div>
                  <div className="text-2xl font-bold">{kpi.value}</div>
                  <div className="text-xs font-medium text-[#94a3b8] mt-0.5">{kpi.label}</div>
                  <div className="text-[10px] text-[#475569]">{kpi.sublabel}</div>
                </div>
              ))}
            </div>

            {/* Messages bar chart */}
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold">Mensajes por día</h2>
                {data.summary.peak_day && (
                  <span className="text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full">
                    📍 Pico: {data.summary.peak_day}
                  </span>
                )}
              </div>
              <div className="flex items-end gap-px h-36">
                {data.timeline.map((point) => {
                  const h = Math.max(2, Math.round((point.messages / maxMsg) * 100));
                  return (
                    <div key={point.date} className="flex-1 flex flex-col items-center group relative cursor-default">
                      <div
                        className="w-full bg-indigo-600 hover:bg-indigo-400 rounded-sm transition-colors"
                        style={{ height: `${h}%` }}
                      />
                      <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover:block z-20 pointer-events-none">
                        <div className="bg-[#0d0d14] border border-[#1e1e2e] rounded-lg px-2.5 py-1.5 text-[10px] whitespace-nowrap shadow-xl">
                          <div className="font-semibold text-[#e2e8f0]">{point.date}</div>
                          <div className="text-indigo-300">💬 {point.messages} mensajes</div>
                          <div className="text-green-300">👤 {point.active_users} usuarios</div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="flex justify-between text-[10px] text-[#475569] mt-1.5">
                <span>{data.timeline[0]?.date?.slice(5)}</span>
                <span>{data.timeline[data.timeline.length - 1]?.date?.slice(5)}</span>
              </div>
            </div>

            {/* Bottom grid: Agents + Active users */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

              {/* Top agents */}
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
                <h2 className="text-sm font-semibold mb-4">🤖 Agentes más usados</h2>
                {data.top_agents.length === 0 ? (
                  <p className="text-xs text-[#475569]">Sin datos aún en este período</p>
                ) : (
                  <div className="space-y-2.5">
                    {data.top_agents.map((a) => {
                      const maxCount = data.top_agents[0]?.count || 1;
                      const pct = Math.round((a.count / maxCount) * 100);
                      return (
                        <div key={a.agent} className="flex items-center gap-2.5">
                          <span className="text-sm w-5 flex-shrink-0">{AGENT_ICONS[a.agent] || "🤖"}</span>
                          <span className="text-[11px] font-semibold w-16 text-[#94a3b8] uppercase flex-shrink-0">{a.agent}</span>
                          <div className="flex-1 h-1.5 bg-[#1e1e2e] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full transition-all"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="text-[11px] text-[#64748b] w-10 text-right flex-shrink-0">
                            {a.count.toLocaleString()}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Active users chart */}
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4">
                <h2 className="text-sm font-semibold mb-4">👤 Usuarios activos/día</h2>
                <div className="flex items-end gap-px h-28">
                  {data.timeline.map((point) => {
                    const h = Math.max(2, Math.round((point.active_users / maxUsers) * 100));
                    return (
                      <div key={point.date} className="flex-1 group relative cursor-default">
                        <div
                          className="w-full bg-green-700 hover:bg-green-500 rounded-sm transition-colors"
                          style={{ height: `${h}%` }}
                        />
                        <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 hidden group-hover:block z-20 pointer-events-none">
                          <div className="bg-[#0d0d14] border border-[#1e1e2e] rounded px-2 py-1 text-[10px] whitespace-nowrap shadow-xl">
                            {point.date}: <span className="text-green-300">{point.active_users}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between text-[10px] text-[#475569] mt-1.5">
                  <span>{data.timeline[0]?.date?.slice(5)}</span>
                  <span>{data.timeline[data.timeline.length - 1]?.date?.slice(5)}</span>
                </div>
              </div>
            </div>

            {/* Conversions */}
            {data.new_conversions_period > 0 && (
              <div className="bg-gradient-to-r from-indigo-600/10 to-purple-600/10 border border-indigo-500/20 rounded-xl p-4 flex items-center gap-4">
                <div className="text-3xl">⚡</div>
                <div>
                  <div className="text-lg font-bold text-indigo-300">{data.new_conversions_period} nuevas conversiones a Pro</div>
                  <div className="text-xs text-[#64748b]">en los últimos {days} días · {data.total_pro_users} usuarios Pro totales</div>
                </div>
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
