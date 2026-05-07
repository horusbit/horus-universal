"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import AgentSelector from "@/components/AgentSelector";
import MessageBubble from "@/components/MessageBubble";
import ChatInput from "@/components/ChatInput";
import Sidebar from "@/components/Sidebar";
import {
  streamMessage, AgentType, ChatMessage,
  getConversationMessages, setConversationTitle,
} from "@/lib/api";

interface Message extends ChatMessage {
  id: string;
  agent?: AgentType;
  model?: string;
  timestamp?: string;
}

const now = () => new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });

export default function HorusChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentType>("atlas");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>(uuidv4());
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarRefresh, setSidebarRefresh] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const titleSetRef = useRef(false);

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

  const handleSend = async (text: string) => {
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

    // Auto-set title con el primer mensaje
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

      // Refrescar sidebar después de cada mensaje
      setSidebarRefresh(r => r + 1);

    } catch (error) {
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: "❌ Error conectando con el servidor. Verifica que el backend esté corriendo." }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

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
          <button
            onClick={startNewChat}
            className="hidden sm:flex items-center gap-1.5 text-xs text-[#64748b] hover:text-white
              px-3 py-1.5 rounded-lg border border-[#1e1e2e] hover:border-indigo-500/50 transition-colors"
          >
            <span>✏️</span> Nuevo
          </button>
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs text-[#64748b] hidden sm:inline">Activo</span>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
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
  { agent: "cipher" as AgentType, icon: "⚡", text: "Crea una API REST con FastAPI y autenticación JWT" },
  { agent: "nova"   as AgentType, icon: "✨", text: "Escribe un post viral para LinkedIn sobre tendencias de IA" },
  { agent: "oracle" as AgentType, icon: "🔮", text: "Analiza el modelo de negocio de una SaaS B2B" },
  { agent: "darwin" as AgentType, icon: "🔬", text: "¿Cuáles son los mejores modelos de IA gratuitos en 2025?" },
  { agent: "hermes" as AgentType, icon: "🌍", text: "Traduce al inglés manteniendo tono formal y profesional" },
  { agent: "pixel"  as AgentType, icon: "🎨", text: "Crea un prompt para Midjourney de un logo futurista" },
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
          9 agentes especializados, múltiples modelos de IA, arquitectura de costo cero.
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
