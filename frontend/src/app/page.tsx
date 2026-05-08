"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { v4 as uuidv4 } from "uuid";
import AgentSelector from "@/components/AgentSelector";
import MessageBubble from "@/components/MessageBubble";
import ChatInput from "@/components/ChatInput";
import Sidebar from "@/components/Sidebar";
import { useAuth } from "@/context/AuthContext";
import {
  streamMessage, AgentType, ChatMessage,
  getConversationMessages, setConversationTitle,
  getUserPlan, createCheckout, UserPlan,
} from "@/lib/api";

interface Message extends ChatMessage {
  id: string;
  agent?: AgentType;
  model?: string;
  timestamp?: string;
}

const now = () => new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });

export default function HorusChat() {
  const router = useRouter();
  const { user, loading: authLoading, signOut } = useAuth();

  // ── Todos los hooks ANTES de cualquier return condicional ──
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentType>("atlas");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>(uuidv4());
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarRefresh, setSidebarRefresh] = useState(0);
  const [userPlan, setUserPlan] = useState<UserPlan | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const titleSetRef = useRef(false);

  // Auth guard
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  // Wake-up ping + cargar plan del usuario
  useEffect(() => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${API_URL}/health`).catch(() => {});
    if (user) getUserPlan().then(setUserPlan);
  }, [user]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startNewChat = useCallback(() => {
    setMessages([]);
    setConversationId(uuidv4());
    setSelectedAgent("atlas");
    titleSetRef.current = false;
  }, []);

  const loadConversation = useCallback(async (id: string) => {
    setConversationId(id);
    const msgs = await getConversationMessages(id);
    const formatted: Message[] = msgs.map(m => ({
      ...m,
      id: uuidv4(),
      timestamp: now(),
    }));
    setMessages(formatted);
    titleSetRef.current = true;
  }, []);

  const autoSetTitle = useCallback(async (convId: string, firstMsg: string) => {
    if (titleSetRef.current) return;
    titleSetRef.current = true;
    const title = firstMsg.slice(0, 50) + (firstMsg.length > 50 ? "..." : "");
    await setConversationTitle(convId, title);
  }, []);

  const exportConversation = useCallback(() => {
    if (!messages.length) return;
    const lines = messages.map(m => {
      const role = m.role === "user" ? "👤 Tú" : `🤖 ${(m.agent || "ATLAS").toUpperCase()}`;
      return `## ${role}\n\n${m.content}`;
    });
    const md = `# Conversación HORUS Universal\n_Exportado: ${new Date().toLocaleString("es-ES")}_\n\n---\n\n${lines.join("\n\n---\n\n")}`;
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `horus-chat-${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }, [messages]);

  const handleSend = useCallback(async (text: string) => {
    if (isLoading) return;

    const userMsg: Message = {
      id: uuidv4(),
      role: "user",
      content: text,
      timestamp: now(),
    };

    const assistantMsgId = uuidv4();
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      agent: selectedAgent,
      timestamp: now(),
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);

    autoSetTitle(conversationId, text);

    try {
      let fullContent = "";

      for await (const chunk of streamMessage({
        message: text,
        agent: selectedAgent,
        conversation_id: conversationId,
        history: messages.slice(-10).map(({ role, content }) => ({ role, content })),
      })) {
        fullContent += chunk;
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantMsgId ? { ...m, content: fullContent } : m
          )
        );
      }

      setSidebarRefresh(r => r + 1);
      // Refrescar plan después de cada mensaje
      if (user) getUserPlan().then(setUserPlan);

    } catch (err: unknown) {
      const msg = err instanceof Error && err.message.includes("limit_reached")
        ? "⚠️ Límite diario alcanzado. [Actualiza a Pro ⚡](javascript:void(0)) para uso ilimitado."
        : "❌ Error conectando con el servidor. Verifica que el backend esté corriendo.";
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMsgId ? { ...m, content: msg } : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, selectedAgent, conversationId, messages, autoSetTitle, user]);

  // ── Returns condicionales DESPUÉS de todos los hooks ──
  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-pulse">👁</div>
          <p className="text-[#64748b] text-sm">Cargando HORUS...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex h-screen bg-[#0a0a0f] overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        currentId={conversationId}
        onSelect={loadConversation}
        onNewChat={startNewChat}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        refreshTrigger={sidebarRefresh}
      />

      {/* Main */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-[#1e1e2e] bg-[#12121a] flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-[#64748b] hover:text-white lg:hidden text-lg"
          >
            ☰
          </button>
          <button
            onClick={() => setSidebarOpen(s => !s)}
            className="hidden lg:flex text-[#64748b] hover:text-white text-sm px-2 py-1 rounded hover:bg-[#1e1e2e] transition-colors"
            title="Toggle sidebar"
          >
            ◀
          </button>
          <div className="flex-1">
            <AgentSelector selected={selectedAgent} onChange={setSelectedAgent} />
          </div>
          {/* Nuevo chat — visible en todos los tamaños */}
          <button
            onClick={startNewChat}
            className="flex items-center gap-1 text-xs text-[#64748b] hover:text-white
              p-1.5 sm:px-3 sm:py-1.5 rounded-lg border border-[#1e1e2e] hover:border-indigo-500/50 transition-colors flex-shrink-0"
            title="Nueva conversación"
          >
            <span>✏️</span>
            <span className="hidden sm:inline">Nuevo</span>
          </button>
          {/* Indicador de plan / upgrade — visible en todos los tamaños */}
          {userPlan && userPlan.plan === "free" && userPlan.limit && (
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-xs text-[#64748b] hidden sm:inline">
                {userPlan.used}/{userPlan.limit}
              </span>
              <button
                onClick={async () => {
                  const url = await createCheckout();
                  if (url) window.open(url, "_blank");
                }}
                className="text-xs px-2 py-1 sm:px-2.5 bg-gradient-to-r from-indigo-600 to-purple-600
                  hover:from-indigo-500 hover:to-purple-500 text-white rounded-lg transition-all whitespace-nowrap"
              >
                ⚡ Pro
              </button>
            </div>
          )}
          {userPlan?.plan === "pro" && (
            <span className="text-xs text-purple-400 font-medium flex-shrink-0">⚡ Pro</span>
          )}
          {/* Admin link — solo para horuseict@gmail.com */}
          {user?.email === "horuseict@gmail.com" && (
            <a
              href="/admin"
              className="text-xs text-[#64748b] hover:text-red-400 transition-colors flex-shrink-0"
              title="Panel de Admin"
            >
              🛡️
            </a>
          )}
          {/* Logout */}
          <button
            onClick={signOut}
            className="flex items-center gap-1.5 text-xs text-[#64748b] hover:text-red-400
              p-1.5 sm:px-3 sm:py-1.5 rounded-lg border border-[#1e1e2e] hover:border-red-500/50 transition-colors flex-shrink-0"
            title="Cerrar sesión"
          >
            ⏏
          </button>
          {/* Indicador online — solo desktop */}
          <div className="hidden sm:flex items-center gap-2 flex-shrink-0">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs text-[#64748b]">Activo</span>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-4">
          {messages.length === 0 ? (
            <WelcomeScreen onAgentSelect={setSelectedAgent} onSend={handleSend} />
          ) : (
            <>
              {messages.map(msg => (
                <MessageBubble
                  key={msg.id}
                  role={msg.role as "user" | "assistant"}
                  content={msg.content}
                  agent={msg.agent}
                  model={msg.model}
                  isStreaming={isLoading && msg.id === messages[messages.length - 1]?.id && msg.role === "assistant"}
                  timestamp={msg.timestamp}
                />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="px-4 pb-4 pt-2 border-t border-[#1e1e2e] bg-[#0a0a0f] flex-shrink-0">
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
            placeholder={`Mensaje para ${selectedAgent.toUpperCase()}... (Enter para enviar)`}
          />
          {messages.length > 0 && (
            <div className="flex justify-end mt-1.5">
              <button
                onClick={exportConversation}
                className="text-[10px] text-[#475569] hover:text-[#94a3b8] transition-colors flex items-center gap-1"
                title="Descargar conversación como Markdown"
              >
                ⬇ exportar chat
              </button>
            </div>
          )}
          <p className="text-center text-xs text-[#1e1e2e] mt-2 select-none">
            OpenRouter · Gemini · Llama · DeepSeek · Arquitectura costo cero
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Pantalla de bienvenida ──────────────────────────────────────────────────
const QUICK_ACTIONS = [
  { agent: "cipher"   as AgentType, icon: "⚡", text: "Crea una API REST con FastAPI y autenticación JWT" },
  { agent: "nova"     as AgentType, icon: "✨", text: "Escribe un post viral para LinkedIn sobre tendencias de IA" },
  { agent: "oracle"   as AgentType, icon: "🔮", text: "Analiza el modelo de negocio de una SaaS B2B" },
  { agent: "nexus"    as AgentType, icon: "📡", text: "Crea un calendario de contenido para Instagram y TikTok" },
  { agent: "vector"   as AgentType, icon: "💼", text: "Script de ventas para superar la objeción de precio" },
  { agent: "forge"    as AgentType, icon: "📊", text: "Analiza estos datos de ventas con Python y Pandas" },
  { agent: "chronos"  as AgentType, icon: "⏱️", text: "Diseña una rutina de productividad para emprendedores" },
  { agent: "politeia" as AgentType, icon: "🏛️", text: "Estrategia de comunicación política para campaña electoral" },
  { agent: "darwin"   as AgentType, icon: "🔬", text: "¿Cuáles son los mejores modelos de IA gratuitos en 2025?" },
];

function WelcomeScreen({
  onAgentSelect, onSend
}: {
  onAgentSelect: (a: AgentType) => void;
  onSend: (msg: string) => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-8 text-center px-4">
      <div>
        <div className="text-5xl mb-4">👁</div>
        <h2 className="text-2xl font-bold text-[#e2e8f0] mb-2">HORUS Universal</h2>
        <p className="text-[#64748b] text-sm max-w-md">
          15 agentes especializados, múltiples modelos de IA, arquitectura de costo cero.
          Selecciona un agente arriba o empieza con una acción rápida.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 w-full max-w-3xl">
        {QUICK_ACTIONS.map((action, i) => (
          <button
            key={i}
            onClick={() => { onAgentSelect(action.agent); onSend(action.text); }}
            className="text-left p-4 bg-[#12121a] border border-[#1e1e2e] rounded-xl
              hover:border-indigo-500/50 hover:bg-[#12121a]/80 transition-all group"
          >
            <div className="text-lg mb-2">{action.icon}</div>
            <p className="text-xs text-[#94a3b8] group-hover:text-[#e2e8f0] transition-colors leading-relaxed">
              {action.text}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
