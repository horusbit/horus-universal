"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
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

interface Member {
  id: string;
  user_id: string;
  email: string;
  role: "admin" | "member" | "viewer";
  joined_at: string;
}

interface TeamDetail {
  id: string;
  name: string;
  description?: string;
  plan: string;
  my_role: string;
  owner_id: string;
  created_at: string;
  members: Member[];
}

const ROLE_LABELS: Record<string, string> = {
  admin: "👑 Admin",
  member: "Miembro",
  viewer: "Viewer",
};

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-indigo-500/10 border-indigo-500/30 text-indigo-300",
  member: "bg-green-500/10 border-green-500/30 text-green-300",
  viewer: "bg-[#1e1e2e] border-[#2d2d3e] text-[#64748b]",
};

export default function TeamDetailPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const teamId = params?.id as string;

  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"member" | "viewer">("member");
  const [inviting, setInviting] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState("");
  const [updatingRole, setUpdatingRole] = useState<string | null>(null);

  const token = (user as any)?.access_token;
  const isAdmin = team?.my_role === "admin";
  const myUserId = (user as any)?.id;

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [user, loading, router]);

  useEffect(() => {
    if (!token || !teamId) return;
    api(`/teams/${teamId}`, token)
      .then(setTeam)
      .catch(e => setError(e.message))
      .finally(() => setIsLoading(false));
  }, [token, teamId]);

  const handleInvite = async () => {
    if (!inviteEmail.trim() || !token) return;
    setInviting(true);
    setError("");
    setInviteSuccess("");
    try {
      await api(`/teams/${teamId}/invite`, token, {
        method: "POST",
        body: JSON.stringify({ email: inviteEmail.trim(), role: inviteRole }),
      });
      setInviteSuccess(`✓ Invitación enviada a ${inviteEmail.trim()}`);
      setInviteEmail("");
      // Refresh members
      const updated = await api(`/teams/${teamId}`, token);
      setTeam(updated);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setInviting(false);
    }
  };

  const handleRoleChange = async (memberId: string, newRole: string) => {
    if (!token) return;
    setUpdatingRole(memberId);
    try {
      await api(`/teams/${teamId}/members`, token, {
        method: "PATCH",
        body: JSON.stringify({ member_id: memberId, role: newRole }),
      });
      setTeam(prev => prev ? {
        ...prev,
        members: prev.members.map(m => m.id === memberId ? { ...m, role: newRole as any } : m)
      } : prev);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUpdatingRole(null);
    }
  };

  const handleRemove = async (memberId: string, memberEmail: string) => {
    if (!token || !confirm(`¿Eliminar a ${memberEmail} del equipo?`)) return;
    try {
      await api(`/teams/${teamId}/members/${memberId}`, token, { method: "DELETE" });
      setTeam(prev => prev ? {
        ...prev,
        members: prev.members.filter(m => m.id !== memberId)
      } : prev);
    } catch (e: any) {
      setError(e.message);
    }
  };

  if (loading || !user) return null;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#e2e8f0]">
      <div className="max-w-3xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <button onClick={() => router.push("/teams")} className="text-xs text-[#64748b] hover:text-white mb-1 block">
              ← Mis equipos
            </button>
            {isLoading ? (
              <div className="h-7 w-48 bg-[#1e1e2e] rounded animate-pulse mt-1" />
            ) : (
              <>
                <h1 className="text-2xl font-bold">{team?.name}</h1>
                {team?.description && (
                  <p className="text-[#64748b] text-sm mt-1">{team.description}</p>
                )}
              </>
            )}
          </div>
          {team && (
            <div className={`text-[10px] font-semibold px-2.5 py-1 rounded-full border ${ROLE_COLORS[team.my_role] || ROLE_COLORS.viewer}`}>
              {ROLE_LABELS[team.my_role] || team.my_role}
            </div>
          )}
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-3 text-sm mb-4">{error}</div>
        )}
        {inviteSuccess && (
          <div className="bg-green-500/10 border border-green-500/20 text-green-400 rounded-xl p-3 text-sm mb-4">{inviteSuccess}</div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
          </div>
        ) : team ? (
          <div className="space-y-6">

            {/* Invite section (admin only) */}
            {isAdmin && (
              <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-5">
                <h2 className="text-sm font-semibold mb-4">✉️ Invitar miembro</h2>
                <div className="flex gap-2">
                  <input
                    value={inviteEmail}
                    onChange={e => setInviteEmail(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleInvite()}
                    placeholder="correo@ejemplo.com"
                    className="flex-1 bg-[#0d0d14] border border-[#1e1e2e] rounded-xl px-3 py-2 text-sm text-[#e2e8f0] placeholder-[#475569] focus:outline-none focus:border-indigo-500/50"
                  />
                  <select
                    value={inviteRole}
                    onChange={e => setInviteRole(e.target.value as any)}
                    className="bg-[#0d0d14] border border-[#1e1e2e] rounded-xl px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-indigo-500/50"
                  >
                    <option value="member">Miembro</option>
                    <option value="viewer">Viewer</option>
                  </select>
                  <button
                    onClick={handleInvite}
                    disabled={!inviteEmail.trim() || inviting}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl disabled:opacity-50 transition-colors whitespace-nowrap"
                  >
                    {inviting ? "..." : "Invitar"}
                  </button>
                </div>
              </div>
            )}

            {/* Members list */}
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-5">
              <h2 className="text-sm font-semibold mb-4">
                👥 Miembros <span className="text-[#475569] font-normal">({team.members.length})</span>
              </h2>
              <div className="space-y-2">
                {team.members.map(member => (
                  <div
                    key={member.id}
                    className="flex items-center gap-3 py-2.5 border-b border-[#1e1e2e] last:border-0"
                  >
                    {/* Avatar */}
                    <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/20 flex items-center justify-center text-xs font-semibold text-indigo-300 flex-shrink-0">
                      {member.email[0].toUpperCase()}
                    </div>

                    {/* Email */}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-[#e2e8f0] truncate">
                        {member.email}
                        {member.user_id === myUserId && (
                          <span className="ml-1.5 text-[10px] text-[#475569]">(tú)</span>
                        )}
                      </div>
                      <div className="text-[10px] text-[#475569]">
                        Desde {new Date(member.joined_at).toLocaleDateString("es-ES")}
                      </div>
                    </div>

                    {/* Role */}
                    {isAdmin && member.user_id !== myUserId ? (
                      <select
                        value={member.role}
                        onChange={e => handleRoleChange(member.id, e.target.value)}
                        disabled={updatingRole === member.id}
                        className="bg-[#0d0d14] border border-[#1e1e2e] rounded-lg px-2 py-1 text-xs text-[#94a3b8] focus:outline-none focus:border-indigo-500/50 disabled:opacity-50"
                      >
                        <option value="admin">Admin</option>
                        <option value="member">Miembro</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    ) : (
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${ROLE_COLORS[member.role] || ROLE_COLORS.viewer}`}>
                        {ROLE_LABELS[member.role] || member.role}
                      </span>
                    )}

                    {/* Remove button (admin only, not self, not owner) */}
                    {isAdmin && member.user_id !== myUserId && member.user_id !== team.owner_id && (
                      <button
                        onClick={() => handleRemove(member.id, member.email)}
                        className="w-7 h-7 flex items-center justify-center text-[#475569] hover:text-red-400 transition-colors rounded-lg hover:bg-red-500/10 flex-shrink-0"
                        title="Eliminar miembro"
                      >
                        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Team info */}
            <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-5">
              <h2 className="text-sm font-semibold mb-3">ℹ️ Información del equipo</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-[#64748b]">Plan</span>
                  <span className="font-medium capitalize">{team.plan}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748b]">Creado</span>
                  <span>{new Date(team.created_at).toLocaleDateString("es-ES")}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748b]">ID del equipo</span>
                  <span className="text-xs text-[#475569] font-mono">{team.id.slice(0, 8)}...</span>
                </div>
              </div>
            </div>

            {/* Leave team (non-owner members) */}
            {team.my_role !== "admin" && (
              <button
                onClick={() => {
                  const me = team.members.find(m => m.user_id === myUserId);
                  if (me) handleRemove(me.id, "ti mismo");
                }}
                className="w-full py-2.5 rounded-xl border border-red-500/20 text-red-400 hover:bg-red-500/10 text-sm transition-colors"
              >
                Salir del equipo
              </button>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
