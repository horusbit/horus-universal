"use client";

import { useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { AgentType, synthesizeSpeech } from "@/lib/api";

const AGENT_META: Record<AgentType | string, { icon: string; color: string }> = {
  atlas:    { icon: "🌐", color: "bg-indigo-600" },
  cipher:   { icon: "⚡", color: "bg-yellow-600" },
  nova:     { icon: "✨", color: "bg-pink-600" },
  lexis:    { icon: "⚖️", color: "bg-blue-600" },
  oracle:   { icon: "🔮", color: "bg-purple-600" },
  hermes:   { icon: "🌍", color: "bg-green-600" },
  echo:     { icon: "🎙️", color: "bg-orange-600" },
  darwin:   { icon: "🔬", color: "bg-teal-600" },
  pixel:    { icon: "🎨", color: "bg-rose-600" },
  nexus:    { icon: "📡", color: "bg-cyan-600" },
  forge:    { icon: "📊", color: "bg-emerald-600" },
  sage:     { icon: "🎓", color: "bg-sky-600" },
  vector:   { icon: "💼", color: "bg-amber-600" },
  chronos:  { icon: "⏱️", color: "bg-violet-600" },
  politeia: { icon: "🏛️", color: "bg-slate-600" },
  educraft: { icon: "🏫", color: "bg-lime-600" },
};

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  agent?: AgentType;
  model?: string;
  isStreaming?: boolean;
  timestamp?: string;
}

export default function MessageBubble({
  role, content, agent, model, isStreaming, timestamp
}: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [ttsState, setTtsState] = useState<"idle" | "loading" | "playing">("idle");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string>("");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSpeak = async () => {
    // Si está reproduciendo, parar
    if (ttsState === "playing") {
      audioRef.current?.pause();
      if (audioRef.current) audioRef.current.currentTime = 0;
      setTtsState("idle");
      return;
    }

    setTtsState("loading");

    try {
      // Limpiar texto para TTS (quitar markdown y código)
      const cleanText = content
        .replace(/```[\s\S]*?```/g, " [bloque de código] ")
        .replace(/`[^`]+`/g, "")
        .replace(/#{1,6}\s/g, "")
        .replace(/\*{1,2}([^*]+)\*{1,2}/g, "$1")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
        .trim()
        .slice(0, 1500); // máx 1500 chars para TTS

      // Revocar URL anterior si existe
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
        audioUrlRef.current = "";
      }

      const url = await synthesizeSpeech(cleanText);
      audioUrlRef.current = url;

      const audio = new Audio(url);
      audioRef.current = audio;

      audio.onended = () => setTtsState("idle");
      audio.onerror = () => setTtsState("idle");

      await audio.play();
      setTtsState("playing");

    } catch (err) {
      // Fallback: Web Speech API del navegador
      try {
        const utterance = new SpeechSynthesisUtterance(
          content.replace(/```[\s\S]*?```/g, "").slice(0, 500)
        );
        utterance.lang = "es-ES";
        utterance.onend = () => setTtsState("idle");
        utterance.onerror = () => setTtsState("idle");
        window.speechSynthesis.speak(utterance);
        setTtsState("playing");
      } catch {
        setTtsState("idle");
      }
    }
  };

  if (role === "user") {
    return (
      <div className="flex justify-end mb-4 group">
        <div className="max-w-[80%] sm:max-w-[75%]">
          <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed">
            {content}
          </div>
          <div className="flex items-center justify-end gap-2 mt-1 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
            {timestamp && <span className="text-[10px] text-[#475569]">{timestamp}</span>}
            <button
              onClick={handleCopy}
              className="text-[10px] text-[#475569] hover:text-[#94a3b8] transition-colors"
            >
              {copied ? "✓ copiado" : "copiar"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const meta = AGENT_META[agent || "atlas"] || AGENT_META.atlas;
  const agentName = agent?.toUpperCase() || "ATLAS";

  return (
    <div className="flex gap-3 mb-4 group">
      {/* Avatar */}
      <div className={`w-8 h-8 ${meta.color} rounded-lg flex items-center justify-center text-sm flex-shrink-0 mt-0.5`}>
        {meta.icon}
      </div>

      <div className="flex-1 min-w-0">
        {/* Header del agente */}
        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
          <span className="text-xs font-bold text-[#e2e8f0]">{agentName}</span>
          {model && (
            <span className="text-[10px] text-[#475569] bg-[#1e1e2e] px-1.5 py-0.5 rounded font-mono">
              {model.split("/").pop()?.replace(":free", "") || model}
            </span>
          )}
          {isStreaming && (
            <span className="flex gap-0.5">
              {[0, 1, 2].map(i => (
                <span
                  key={i}
                  className="w-1 h-1 bg-indigo-400 rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </span>
          )}
        </div>

        {/* Contenido del mensaje */}
        <div className="text-sm text-[#e2e8f0] leading-relaxed prose prose-invert prose-sm max-w-none
          prose-code:bg-[#1e1e2e] prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-indigo-300
          prose-pre:bg-transparent prose-pre:p-0">
          {content ? (
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || "");
                  return !inline && match ? (
                    <div className="relative group/code my-3 max-w-[calc(100vw-6rem)] sm:max-w-none overflow-hidden rounded-lg">
                      <div className="flex items-center justify-between bg-[#1a1a2e] px-3 py-1.5 border border-[#2e2e4e] border-b-0 rounded-t-lg">
                        <span className="text-xs text-[#64748b] font-mono">{match[1]}</span>
                        <CopyCodeButton code={String(children).replace(/\n$/, "")} />
                      </div>
                      <div className="overflow-x-auto">
                        <SyntaxHighlighter
                          style={oneDark}
                          language={match[1]}
                          PreTag="div"
                          customStyle={{
                            margin: 0,
                            borderRadius: "0 0 8px 8px",
                            border: "1px solid #2e2e4e",
                            borderTop: "none",
                            fontSize: "12px",
                          }}
                          {...props}
                        >
                          {String(children).replace(/\n$/, "")}
                        </SyntaxHighlighter>
                      </div>
                    </div>
                  ) : (
                    <code className={className} {...props}>{children}</code>
                  );
                },
              }}
            >
              {content}
            </ReactMarkdown>
          ) : isStreaming ? (
            <span className="text-[#475569] italic text-xs">Pensando...</span>
          ) : null}
        </div>

        {/* Acciones del mensaje */}
        {content && !isStreaming && (
          <div className="flex items-center gap-3 mt-2 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
            {timestamp && <span className="text-[10px] text-[#475569]">{timestamp}</span>}

            {/* Copiar */}
            <button
              onClick={handleCopy}
              className="text-[10px] text-[#475569] hover:text-[#94a3b8] transition-colors flex items-center gap-1"
            >
              {copied ? "✓ copiado" : "📋 copiar"}
            </button>

            {/* Escuchar - TTS */}
            <button
              onClick={handleSpeak}
              disabled={ttsState === "loading"}
              title={ttsState === "playing" ? "Detener" : "Escuchar respuesta"}
              className={`text-[10px] flex items-center gap-1 transition-colors
                ${ttsState === "loading" ? "text-[#475569] cursor-wait" : ""}
                ${ttsState === "playing" ? "text-indigo-400 hover:text-red-400" : "text-[#475569] hover:text-[#94a3b8]"}
              `}
            >
              {ttsState === "loading" && (
                <span className="w-2.5 h-2.5 border border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
              )}
              {ttsState === "loading" ? "cargando..." : ttsState === "playing" ? "⏹ detener" : "🔊 escuchar"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function CopyCodeButton({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        await navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="text-xs text-[#64748b] hover:text-white transition-colors"
    >
      {copied ? "✓ copiado" : "copiar"}
    </button>
  );
}
