"use client";

import { useEffect, useState, useCallback } from "react";
import { ConversationSummary, getConversations, deleteConversation, searchConversations } from "@/lib/api";

// ── localStorage helpers ──────────────────────────────────────────────────────
const LS_KEY = "horus_conversations_v2";

function loadLocalConversations(): ConversationSummary[] {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveLocalConversations(convs: ConversationSummary[]) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(convs.slice(0, 100)));
  } catch {}
}

export function saveConversationLocally(conv: {
  id: string; title: string; agent?: string; last_message?: string; message_count?: number;
}) {
  const stored = loadLocalConversations();
  const idx = stored.findIndex(c => c.id === conv.id);
  const entry: ConversationSummary = {
    id: conv.id,
    title: conv.title || "Nueva conversación",
    agent: conv.agent || "atlas",
    last_message: conv.last_message || "",
    message_count: conv.message_count || 1,
  };
  if (idx >= 0) {
    stored[idx] = { ...stored[idx], ...entry };
  } else {
    stored.unshift(entry);
  }
  saveLocalConversations(stored);
}

export function removeConversationLocally(id: string) {
  const stored = loadLocalConversations().filter(c => c.id !== id);
  saveLocalConversations(stored);
}
// ─────────────────────────────────────────────────────────────────────────────

interface SidebarProps {
  currentId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  isOpen: boolean;
  onClose: () => void;
  refreshTrigger: number;
  user?: { email?: string; id?: string } | null;
  userPlan?: { plan: string; used: number; limit: number | null } | null;
  onLogout?: () => void;
  onUpgrade?: () => void;
}

export default function Sidebar({
  currentId, onSelect, onNewChat, isOpen, onClose, refreshTrigger,
  user, userPlan, onLogout, onUpgrade,
}: SidebarProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>(() => loadLocalConversations());
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<ConversationSummary[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Fetch from server, merge with localStorage
  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getConversations()
      .then(data => {
        if (!mounted) return;
        if (data && data.length > 0) {
          // Server has data — merge with local (server wins for existing IDs)
          const localOnly = loadLocalConversations().filter(
            lc => !data.find(sc => sc.id === lc.id)
          );
          const merged = [...data, ...localOnly];
          setConversations(merged);
          saveLocalConversations(merged);
        } else {
          // Server empty — use localStorage
          setConversations(loadLocalConversations());
        }
        setLoading(false);
      })
      .catch(() => {
        if (!mounted) return;
        // Network error — use localStorage
        setConversations(loadLocalConversations());
        setLoading(false);
      });
    return () => { mounted = false; };
  }, [refreshTrigger]);

  // Búsqueda con debounce
  useEffect(() => {
    if (!searchQuery.trim()) { setSearchResults(null); return; }
    const timer = setTimeout(async () => {
      setSearching(true);
      const results = await searchConversations(searchQuery.trim());
      setSearchResults(results);
      setSearching(false);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteConversation(id);
    removeConversationLocally(id);
    setConversations(prev => prev.filter(c => c.id !== id));
    if (searchResults) setSearchResults(prev => prev ? prev.filter(c => c.id !== id) : null);
    if (currentId === id) onNewChat();
  };

  const displayList = searchResults ?? conversations;
  const usedPercent = userPlan?.limit ? Math.min(100, Math.round((userPlan.used / userPlan.limit) * 100)) : 0;

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 z-20 lg:hidden" onClick={onClose} />
      )}

      <aside className={`
        fixed top-0 left-0 h-full w-64 z-30 flex flex-col
        bg-[#0d0d14] border-r border-[#1e1e2e]
        transition-transform duration-300
        ${isOpen ? "translate-x-0" : "-translate-x-full"}
        lg:relative lg:translate-x-0 lg:flex
      `}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-[#1e1e2e]">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-base flex-shrink-0">👁</div>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-bold text-[#e2e8f0] truncate">HORUS Universal</h1>
            <p className="text-xs text-[#64748b]">Orquestador IA</p>
          </div>
          <button onClick={onClose} className="text-[#64748b] hover:text-white lg:hidden">✕</button>
        </div>

        {/* New Chat */}
        <div className="p-3 pb-1">
          <button
            onClick={() => { onNewChat(); onClose(); }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg
              bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
          >
            <span className="text-base">✏️</span>
            <span>Nueva conversación</span>
          </button>
        </div>

        {/* Búsqueda */}
        <div className="px-3 pb-2">
          <div className="relative">
            <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#475569] text-xs pointer-events-none">🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Buscar conversaciones..."
              className="w-full bg-[#12121a] border border-[#1e1e2e] rounded-lg pl-7 pr-3 py-1.5
                text-xs text-[#e2e8f0] placeholder-[#475569]
                focus:outline-none focus:border-indigo-500/50 transition-colors"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-[#475569] hover:text-white text-xs">✕</button>
            )}
          </div>
        </div>

        {/* Lista de conversaciones */}
        <div className="flex-1 overflow-y-auto px-2 pb-4">
          {loading && !conversations.length ? (
            <div className="text-center text-[#64748b] text-xs py-8">Cargando...</div>
          ) : searching ? (
            <div className="text-center text-[#64748b] text-xs py-8">Buscando...</div>
          ) : displayList.length === 0 ? (
            <div className="text-center text-[#64748b] text-xs py-8 px-4">
              {searchQuery ? (
                <p>Sin resultados para &ldquo;{searchQuery}&rdquo;</p>
              ) : (
                <>
                  <p className="mb-1">Sin conversaciones aún</p>
                  <p>Empieza un chat ↑</p>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-0.5 mt-1">
              {displayList.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => { onSelect(conv.id); onClose(); }}
                  className={`
                    group relative flex items-start gap-2 px-3 py-2.5 rounded-lg cursor-pointer
                    transition-colors text-sm
                    ${currentId === conv.id
                      ? "bg-indigo-600/20 text-[#e2e8f0] border border-indigo-500/30"
                      : "text-[#94a3b8] hover:bg-[#12121a] hover:text-[#e2e8f0]"
                    }
                  `}
                >
                  <span className="text-xs mt-0.5 flex-shrink-0">💬</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate text-xs leading-relaxed">
                      {conv.title || "Nueva conversación"}
                    </p>
                    {conv.last_message && (
                      <p className="text-[#64748b] truncate text-xs mt-0.5">{conv.last_message}</p>
                    )}
                    <p className="text-[#475569] text-xs mt-0.5">{conv.message_count} mensajes</p>
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, conv.id)}
                    className="opacity-0 group-hover:opacity-100 text-[#64748b] hover:text-red-400
                      transition-opacity flex-shrink-0 text-xs"
                    title="Eliminar"
                  >🗑</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── User Profile Panel ─────────────────────────────── */}
        <div className="border-t border-[#1e1e2e]">
          {/* Usage bar (solo plan free con límite) */}
          {userPlan && userPlan.limit && (
            <div className="px-4 pt-3 pb-1">
              <div className="flex justify-between text-xs text-[#64748b] mb-1">
                <span>Uso diario</span>
                <span>{userPlan.used}/{userPlan.limit}</span>
              </div>
              <div className="h-1 bg-[#1e1e2e] rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${usedPercent > 80 ? 'bg-red-500' : 'bg-indigo-500'}`}
                  style={{ width: `${usedPercent}%` }}
                />
              </div>
            </div>
          )}

          {/* User button */}
          <div className="p-3">
            <button
              onClick={() => setShowUserMenu(m => !m)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg
                hover:bg-[#12121a] transition-colors text-left group"
            >
              <div className="w-7 h-7 bg-indigo-600/30 border border-indigo-500/40 rounded-full
                flex items-center justify-center text-xs font-bold text-indigo-300 flex-shrink-0">
                {user?.email?.[0]?.toUpperCase() || "U"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-[#e2e8f0] truncate">
                  {user?.email?.split("@")[0] || "Usuario"}
                </p>
                <p className="text-xs text-[#64748b]">
                  {userPlan?.plan === "pro" ? "⚡ Pro" : "Free"}
                </p>
              </div>
              <span className={`text-[#64748b] text-xs transition-transform ${showUserMenu ? "rotate-180" : ""}`}>▲</span>
            </button>

            {/* User dropdown menu */}
            {showUserMenu && (
              <div className="mt-1 bg-[#12121a] border border-[#1e1e2e] rounded-lg overflow-hidden">
                <div className="px-3 py-2 border-b border-[#1e1e2e]">
                  <p className="text-xs text-[#64748b] truncate">{user?.email || ""}</p>
                  <p className="text-xs font-medium text-indigo-400 mt-0.5">
                    Plan {userPlan?.plan === "pro" ? "⚡ Pro" : "Free"}
                    {userPlan?.limit && ` · ${userPlan.used}/${userPlan.limit} hoy`}
                  </p>
                </div>

                {userPlan?.plan !== "pro" && onUpgrade && (
                  <button
                    onClick={() => { onUpgrade(); setShowUserMenu(false); }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs
                      text-indigo-300 hover:bg-indigo-600/20 transition-colors"
                  >
                    ⚡ Upgrade a Pro
                  </button>
                )}

                <button
                  onClick={() => { window.location.href = "/"; setShowUserMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs
                    text-[#94a3b8] hover:bg-[#1e1e2e] transition-colors"
                >
                  🏠 Inicio
                </button>

                <button
                  onClick={() => { onLogout?.(); setShowUserMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs
                    text-red-400 hover:bg-red-500/10 transition-colors border-t border-[#1e1e2e]"
                >
                  ⏏ Cerrar sesión
                </button>
              </div>
            )}
          </div>

          {/* Agents count */}
          <div className="px-4 pb-3">
            <div className="flex items-center gap-2 px-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse flex-shrink-0" />
              <span className="text-xs text-[#64748b]">16 agentes activos</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
