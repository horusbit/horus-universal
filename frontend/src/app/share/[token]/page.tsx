"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getSharedConversation } from "@/lib/api";
import ReactMarkdown from "react-markdown";

const AGENT_META: Record<string, { icon: string; color: string; name: string }> = {
  atlas:    { icon: "🌐", color: "bg-indigo-600",  name: "ATLAS" },
  cipher:   { icon: "⚡", color: "bg-yellow-600",  name: "CIPHER" },
  nova:     { icon: "✨", color: "bg-pink-600",    name: "NOVA" },
  lexis:    { icon: "⚖️", color: "bg-blue-600",    name: "LEXIS" },
  oracle:   { icon: "🔮", color: "bg-purple-600",  name: "ORACLE" },
  hermes:   { icon: "🌍", color: "bg-green-600",   name: "HERMES" },
  echo:     { icon: "🎙️", color: "bg-orange-600", name: "ECHO" },
  darwin:   { icon: "🔬", color: "bg-teal-600",    name: "DARWIN" },
  pixel:    { icon: "🎨", color: "bg-rose-600",    name: "PIXEL" },
  nexus:    { icon: "📡", color: "bg-cyan-600",    name: "NEXUS" },
  forge:    { icon: "📊", color: "bg-emerald-600", name: "FORGE" },
  sage:     { icon: "🎓", color: "bg-sky-600",     name: "SAGE" },
  vector:   { icon: "💼", color: "bg-amber-600",   name: "VECTOR" },
  chronos:  { icon: "⏱️", color: "bg-violet-600", name: "CHRONOS" },
  politeia: { icon: "🏛️", color: "bg-slate-600",  name: "POLITEIA" },
  educraft: { icon: "🏫", color: "bg-lime-600",    name: "EDUCRAFT" },
};

interface SharedData {
  conversation_id: string;
  title: string;
  agent: string;
  messages: { role: string; content: string }[];
}

export default function SharedConversationPage() {
  const params = useParams();
  const token = params?.token as string;
  const [data, setData] = useState<SharedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!token) return;
    getSharedConversation(token).then(res => {
      if (res) setData(res);
      else setNotFound(true);
      setLoading(false);
    });
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-pulse">👁</div>
          <p className="text-[#64748b] text-sm">Cargando conversación...</p>
        </div>
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-4">
        <div className="text-center">
          <div className="text-5xl mb-4">🔍</div>
          <h1 className="text-xl font-bold text-[#e2e8f0] mb-2">Conversación no encontrada</h1>
          <p className="text-[#64748b] text-sm mb-6">El enlace puede haber expirado o ser inválido.</p>
          <a
            href="/"
            className="text-sm px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors"
          >
            Ir a HORUS Universal
          </a>
        </div>
      </div>
    );
  }

  const agentMeta = AGENT_META[data?.agent || "atlas"] || AGENT_META.atlas;
  const userMessages = data?.messages.filter(m => m.role !== "system") || [];

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#e2e8f0] overflow-y-auto">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-[#1e1e2e] bg-[#0a0a0f]/95 backdrop-blur-md">
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-indigo-600 rounded-md flex items-center justify-center text-xs">👁</div>
            <span className="font-bold text-sm">HORUS Universal</span>
            <span className="text-[#475569] text-xs hidden sm:inline">— Conversación compartida</span>
          </div>
          <a
            href="/register"
            className="text-xs px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors whitespace-nowrap"
          >
            Crear cuenta gratis
          </a>
        </div>
      </header>

      {/* Title */}
      <div className="max-w-3xl mx-auto px-4 py-6 border-b border-[#1e1e2e]">
        <div className="flex items-center gap-3 mb-2">
          <div className={`w-8 h-8 ${agentMeta.color} rounded-lg flex items-center justify-center text-sm flex-shrink-0`}>
            {agentMeta.icon}
          </div>
          <div>
            <h1 className="text-lg font-bold text-[#e2e8f0]">{data?.title || "Conversación"}</h1>
            <p className="text-xs text-[#64748b]">Agente: {agentMeta.name} · {userMessages.length} mensajes</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        {userMessages.map((msg, i) => {
          if (msg.role === "user") {
            return (
              <div key={i} className="flex justify-end">
                <div className="max-w-[80%] bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed">
                  {msg.content}
                </div>
              </div>
            );
          }

          // Clean HORUS_IMAGE blocks for display
          const cleanContent = msg.content.replace(
            /\[HORUS_IMAGE\][\s\S]*?\[\/HORUS_IMAGE\]/g,
            "_[Imagen generada por PIXEL]_"
          );

          return (
            <div key={i} className="flex gap-3">
              <div className={`w-8 h-8 ${agentMeta.color} rounded-lg flex items-center justify-center text-sm flex-shrink-0 mt-0.5`}>
                {agentMeta.icon}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-[#e2e8f0] mb-1.5">{agentMeta.name}</p>
                <div className="text-sm text-[#e2e8f0] leading-relaxed prose prose-invert prose-sm max-w-none
                  prose-code:bg-[#1e1e2e] prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-indigo-300">
                  <ReactMarkdown>{cleanContent}</ReactMarkdown>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* CTA footer */}
      <div className="max-w-3xl mx-auto px-4 py-10 text-center border-t border-[#1e1e2e] mt-6">
        <div className="text-3xl mb-3">👁</div>
        <h2 className="text-lg font-bold text-[#e2e8f0] mb-2">¿Quieres usar HORUS Universal?</h2>
        <p className="text-[#64748b] text-sm mb-4">16 agentes especializados — 50 mensajes gratis al día</p>
        <a
          href="/register"
          className="inline-block text-sm px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600
            hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl transition-all"
        >
          Crear cuenta gratis →
        </a>
      </div>
    </div>
  );
}
