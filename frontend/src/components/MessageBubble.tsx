"use client";
import VisualMessageRenderer from "@/components/VisualMessageRenderer";

import { useState, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { AgentType, synthesizeSpeech, generateImage, shareConversation } from "@/lib/api";

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
  agent?: AgentType | string;
  model?: string;
  isStreaming?: boolean;
  timestamp?: string;
  conversationId?: string;
  isLast?: boolean;
  onRegenerate?: () => void;
}

// ── Parsear bloques [HORUS_IMAGE] ──────────────────────────────────────────────
interface TextPart  { type: "text";  content: string }
interface ImagePart { type: "image"; prompt: string; model: string; width: number; height: number }
type ContentPart = TextPart | ImagePart;

function parseContent(raw: string): ContentPart[] {
  const parts: ContentPart[] = [];
  const regex = /\[HORUS_IMAGE\]([\s\S]*?)\[\/HORUS_IMAGE\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(raw)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", content: raw.slice(lastIndex, match.index) });
    }
    const block = match[1];
    const get = (key: string, fallback: string) => {
      const m = new RegExp(`${key}:\\s*(.+)`).exec(block);
      return m ? m[1].trim() : fallback;
    };
    parts.push({
      type: "image",
      prompt: get("prompt", ""),
      model: get("model", "flux"),
      width: parseInt(get("width", "1024"), 10),
      height: parseInt(get("height", "1024"), 10),
    });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < raw.length) {
    parts.push({ type: "text", content: raw.slice(lastIndex) });
  }
  return parts;
}

// ── Componente de imagen generada ─────────────────────────────────────────────
function ImageBlock({ prompt, model, width, height }: Omit<ImagePart, "type">) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [imageUrl, setImageUrl] = useState<string>("");

  const handleGenerate = useCallback(async () => {
    if (!prompt) return;
    setState("loading");
    try {
      const res = await generateImage({ prompt, model, width, height });
      setImageUrl(res.url);
      setState("done");
    } catch {
      setState("error");
    }
  }, [prompt, model, width, height]);

  if (state === "idle") {
    return (
      <div className="my-3 p-3 border border-rose-500/30 rounded-xl bg-rose-950/20">
        <p className="text-xs text-rose-300 mb-2">🎨 Imagen lista para generar</p>
        <p className="text-[11px] text-[#64748b] mb-3 line-clamp-2">{prompt}</p>
        <button
          onClick={handleGenerate}
          className="text-xs px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg transition-colors"
        >
          Generar imagen
        </button>
      </div>
    );
  }

  if (state === "loading") {
    return (
      <div className="my-3 p-4 border border-rose-500/30 rounded-xl bg-rose-950/20 flex items-center gap-3">
        <span className="w-4 h-4 border-2 border-rose-400/30 border-t-rose-400 rounded-full animate-spin flex-shrink-0" />
        <span className="text-xs text-rose-300">Generando imagen con {model}...</span>
      </div>
    );
  }

  if (state === "error") {
    return (
      <div className="my-3 p-3 border border-red-500/30 rounded-xl bg-red-950/20">
        <p className="text-xs text-red-400">⚠️ Error generando imagen.</p>
        <button onClick={handleGenerate} className="text-xs text-[#64748b] hover:text-white mt-1">
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-[#1e1e2e]">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={imageUrl}
        alt={prompt}
        className="w-full max-w-lg rounded-xl"
        loading="lazy"
      />
      <div className="flex items-center justify-between px-3 py-2 bg-[#0d0d14]">
        <span className="text-[10px] text-[#475569] truncate max-w-[200px]">{prompt}</span>
        <a
          href={imageUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[10px] text-[#64748b] hover:text-white transition-colors flex-shrink-0 ml-2"
        >
          ↗ abrir
        </a>
      </div>
    </div>
  );
}

// ── Componente principal ───────────────────────────────────────────────────────
export default function MessageBubble({
  role, content, agent, model, isStreaming, timestamp, conversationId, isLast, onRegenerate
}: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [ttsState, setTtsState] = useState<"idle" | "loading" | "playing">("idle");
  const [shareState, setShareState] = useState<"idle" | "loading" | "copied">("idle");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string>("");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = async () => {
    if (!conversationId) return;
    setShareState("loading");
    try {
      const res = await shareConversation(conversationId);
      if (res) {
        const fullUrl = `${window.location.origin}/share/${res.token}`;
        await navigator.clipboard.writeText(fullUrl);
        setShareState("copied");
        setTimeout(() => setShareState("idle"), 3000);
      } else {
        setShareState("idle");
      }
    } catch {
      setShareState("idle");
    }
  };

  const handleSpeak = async () => {
    if (ttsState === "playing") {
      audioRef.current?.pause();
      if (audioRef.current) audioRef.current.currentTime = 0;
      setTtsState("idle");
      return;
    }
    setTtsState("loading");
    try {
      const cleanText = content
        .replace(/```[\s\S]*?```/g, " [bloque de código] ")
        .replace(/`[^`]+`/g, "")
        .replace(/#{1,6}\s/g, "")
        .replace(/\*{1,2}([^*]+)\*{1,2}/g, "$1")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
        .replace(/\[HORUS_IMAGE\][\s\S]*?\[\/HORUS_IMAGE\]/g, "")
        .trim()
        .slice(0, 1500);

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
    } catch {
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
      <div className="flex justify-end mb-6 group">
        <div className="max-w-[80%] sm:max-w-[75%]">
          <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-base leading-relaxed">
            
<VisualMessageRenderer
  content={content}
  imageUrl={(message as any)?.image_url}
  visual={(message as any)?.visual}
/>

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

  const meta = AGENT_META[agent || "atlas"] || { icon: "🤖", color: "bg-purple-600" };
  const agentName = agent?.toUpperCase() || "ATLAS";
  const parts = content ? parseContent(content) : [];

  return (
    <div className="flex gap-3 mb-6 group">
      {/* Avatar */}
      <div className={`w-9 h-9 ${meta.color} rounded-xl flex items-center justify-center text-base flex-shrink-0 mt-0.5`}>
        {meta.icon}
      </div>

      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center gap-2 mb-2 flex-wrap">
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

        {/* Contenido */}
        <div className="text-base text-[#e2e8f0] leading-relaxed prose prose-invert prose-base max-w-none
          prose-p:my-2 prose-headings:mt-4 prose-headings:mb-2
          prose-code:bg-[#1e1e2e] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-indigo-300
          prose-pre:bg-transparent prose-pre:p-0">
          {parts.length > 0 ? (
            parts.map((part, i) =>
              part.type === "image" ? (
                <ImageBlock key={i} {...part} />
              ) : part.content.trim() ? (
                <ReactMarkdown
                  key={i}
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
                  {part.content}
                </ReactMarkdown>
              ) : null
            )
          ) : isStreaming ? (
            <span className="text-[#475569] italic text-xs">Pensando...</span>
          ) : null}
        </div>

        {/* Acciones */}
        {content && !isStreaming && (
          <div className="flex items-center gap-3 mt-2 flex-wrap opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
            {timestamp && <span className="text-[10px] text-[#475569]">{timestamp}</span>}

            {/* Copiar */}
            <button
              onClick={handleCopy}
              className="text-[10px] text-[#475569] hover:text-[#94a3b8] transition-colors flex items-center gap-1"
            >
              {copied ? "✓ copiado" : "📋 copiar"}
            </button>

            {/* TTS */}
            <button
              onClick={handleSpeak}
              disabled={ttsState === "loading"}
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

            {/* Compartir conversación */}
            {conversationId && (
              <button
                onClick={handleShare}
                disabled={shareState === "loading"}
                className={`text-[10px] flex items-center gap-1 transition-colors
                  ${shareState === "loading" ? "text-[#475569] cursor-wait" : ""}
                  ${shareState === "copied" ? "text-green-400" : "text-[#475569] hover:text-[#94a3b8]"}
                `}
              >
                {shareState === "loading" && (
                  <span className="w-2.5 h-2.5 border border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
                )}
                {shareState === "copied" ? "✓ link copiado" : shareState === "loading" ? "generando..." : "🔗 compartir"}
              </button>
            )}

            {/* Regenerar — solo en último mensaje */}
            {isLast && onRegenerate && (
              <button
                onClick={onRegenerate}
                className="text-[10px] text-[#475569] hover:text-indigo-400 transition-colors flex items-center gap-1"
                title="Regenerar respuesta"
              >
                🔄 regenerar
              </button>
            )}
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
