"use client";

import { useEffect, useState } from "react";
import { ConversationSummary, getConversations, deleteConversation } from "@/lib/api";

interface SidebarProps {
  currentId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  isOpen: boolean;
  onClose: () => void;
  refreshTrigger: number;
}

export default function Sidebar({
  currentId, onSelect, onNewChat, isOpen, onClose, refreshTrigger
}: SidebarProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getConversations().then(data => {
      if (mounted) { setConversations(data); setLoading(false); }
    });
    return () => { mounted = false; };
  }, [refreshTrigger]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteConversation(id);
    setConversations(prev => prev.filter(c => c.id !== id));
    if (currentId === id) onNewChat();
  };

  return (
    <>
      {/* Overlay móvil */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 h-full w-64 z-30 flex flex-col
        bg-[#0d0d14] border-r border-[#1e1e2e]
        transition-transform duration-300
        ${isOpen ? "translate-x-0" : "-translate-x-full"}
        lg:relative lg:translate-x-0 lg:flex
      `}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-[#1e1e2e]">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-base flex-shrink-0">
            👁
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-bold text-[#e2e8f0] truncate">HORUS Universal</h1>
            <p className="text-xs text-[#64748b]">Orquestador IA</p>
          </div>
          <button onClick={onClose} className="text-[#64748b] hover:text-white lg:hidden">✕</button>
        </div>

        {/* New Chat */}
        <div className="p-3">
          <button
            onClick={() => { onNewChat(); onClose(); }}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg
              bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium
              transition-colors"
          >
            <span className="text-base">✏️</span>
            <span>Nueva conversación</span>
          </button>
        </div>

        {/* Lista de conversaciones */}
        <div className="flex-1 overflow-y-auto px-2 pb-4">
          {loading ? (
            <div className="text-center text-[#64748b] text-xs py-8">Cargando...</div>
          ) : conversations.length === 0 ? (
            <div className="text-center text-[#64748b] text-xs py-8 px-4">
              <p className="mb-1">Sin conversaciones aún</p>
              <p>Empieza un chat ↑</p>
            </div>
          ) : (
            <div className="space-y-0.5 mt-1">
              {conversations.map((conv) => (
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
                      <p className="text-[#64748b] truncate text-xs mt-0.5">
                        {conv.last_message}
                      </p>
                    )}
                    <p className="text-[#475569] text-xs mt-0.5">
                      {conv.message_count} mensajes
                    </p>
                  </div>
                  {/* Botón eliminar */}
                  <button
                    onClick={(e) => handleDelete(e, conv.id)}
                    className="opacity-0 group-hover:opacity-100 text-[#64748b] hover:text-red-400
                      transition-opacity flex-shrink-0 text-xs"
                    title="Eliminar"
                  >
                    🗑
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-[#1e1e2e]">
          <div className="flex items-center gap-2 px-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse flex-shrink-0" />
            <span className="text-xs text-[#64748b]">9 agentes activos</span>
          </div>
        </div>
      </aside>
    </>
  );
}
