"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function api(path: string, token: string, opts?: RequestInit) {
  const r = await fetch(`${API_URL}/api/v1${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(opts?.headers || {}),
    },
  });
  if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Error ${r.status}`); }
  return r.json();
}

interface Team {
  id: string;
  name: string;
  description?: string;
  plan: string;
  my_role: string;
  created_at: string;
}

export default function TeamsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [teams, setTeams] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const token = (user as any)?.access_token;

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [user, loading, router]);

  useEffect(() => {
    if (!token) return;
    api("/teams/", token)
      .then(d => setTeams(d.teams || []))
      .catch(e => setError(e.message))
      .finally(() => setIsLoading(false));
  }, [token]);

  const handleCreate = async () => {
    if (!name.trim() || !token) return;
    setCreating(true);
    setError("");
    try {
      const team = await api("/teams/", token, {
        method: "POST",
        body: JSON.stringify({ name: name.trim(), description: description.trim() }),
      });
      router.push(`/teams/${team.id}`);
    } catch (e: any) {
      setError(e.message);
      setCreating(false);
    }
  };

  if (loading || !user) return null;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#e2e8f0]">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button onClick={() => router.push("/")} className="text-xs text-[#64748b] hover:text-white mb-1 block">
              ← Volver al chat
            </button>
            <h1 className="text-2xl font-bold">👥 Mis Equipos</h1>
            <p className="text-[#64748b] text-sm mt-1">Workspaces colaborativos de HORUS</p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl transition-colors"
          >
            <span>+</span> Crear equipo
          </button>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-3 text-sm mb-4">{error}</div>
        )}

        {/* Create modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
            <div className="bg-[#0d0d14] border border-[#1e1e2e] rounded-2xl p-6 w-full max-w-md shadow-2xl">
              <h2 className="text-lg font-bold mb-4">Crear nuevo equipo</h2>
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-[#64748b] mb-1 block">Nombre del equipo *</label>
                  <input
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="Ej: Marketing Digital, Dev Team..."
                    className="w-full bg-[#12121a] border border-[#1e1e2e] rounded-xl px-3 py-2.5 text-sm text-[#e2e8f0] placeholder-[#475569] focus:outline-none focus:border-indigo-500/50"
                  />
                </div>
                <div>
                  <label className="text-xs text-[#64748b] mb-1 block">Descripción (opcional)</label>
                  <textarea
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                    placeholder="Para qué usarán HORUS juntos..."
                    rows={3}
                    className="w-full bg-[#12121a] border border-[#1e1e2e] rounded-xl px-3 py-2.5 text-sm text-[#e2e8f0] placeholder-[#475569] focus:outline-none focus:border-indigo-500/50 resize-none"
                  />
                </div>
              </div>
              <div className="flex gap-3 mt-5">
                <button
                  onClick={() => { setShowCreate(false); setName(""); setDescription(""); }}
                  className="flex-1 py-2.5 rounded-xl border border-[#1e1e2e] text-[#64748b] hover:text-white text-sm transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!name.trim() || creating}
                  className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50 transition-colors"
                >
                  {creating ? "Creando..." : "Crear equipo"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Teams list */}
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
          </div>
        ) : teams.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">👥</div>
            <h2 className="text-lg font-semibold text-[#e2e8f0] mb-2">No tienes equipos aún</h2>
            <p className="text-[#64748b] text-sm mb-6 max-w-sm mx-auto">
              Crea un workspace de equipo para colaborar con colegas usando los 16 agentes de HORUS.
            </p>
            <button
              onClick={() => setShowCreate(true)}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl transition-colors"
            >
              Crear mi primer equipo
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {teams.map(team => (
              <div
                key={team.id}
                onClick={() => router.push(`/teams/${team.id}`)}
                className="bg-[#12121a] border border-[#1e1e2e] hover:border-indigo-500/40 rounded-2xl p-5 cursor-pointer transition-all group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 bg-indigo-600/20 border border-indigo-500/30 rounded-xl flex items-center justify-center text-lg">
                    👥
                  </div>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border
                    ${team.my_role === "admin"
                      ? "bg-indigo-500/10 border-indigo-500/30 text-indigo-300"
                      : "bg-[#1e1e2e] border-[#2d2d3e] text-[#64748b]"
                    }`}>
                    {team.my_role === "admin" ? "👑 Admin" : team.my_role === "member" ? "Miembro" : "Viewer"}
                  </span>
                </div>
                <h3 className="font-semibold text-[#e2e8f0] group-hover:text-white transition-colors mb-1">
                  {team.name}
                </h3>
                {team.description && (
                  <p className="text-xs text-[#64748b] line-clamp-2">{team.description}</p>
                )}
                <div className="flex items-center gap-2 mt-3">
                  <span className="text-[10px] text-[#475569]">
                    Creado {new Date(team.created_at).toLocaleDateString("es-ES")}
                  </span>
                  <span className="ml-auto text-[10px] text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    Ver equipo →
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
