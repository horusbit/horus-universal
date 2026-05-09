"use client";

import { useState, useRef, useEffect } from "react";
import { AgentType, CustomAgent } from "@/lib/api";

interface BuiltinAgent {
  id: AgentType;
  name: string;
  icon: string;
  description: string;
}

const AGENTS: BuiltinAgent[] = [
  { id: "atlas",    name: "ATLAS",    icon: "🌐", description: "Orquestador general" },
  { id: "cipher",   name: "CIPHER",   icon: "⚡", description: "Código & Dev" },
  { id: "nova",     name: "NOVA",     icon: "✨", description: "Marketing & Copy" },
  { id: "lexis",    name: "LEXIS",    icon: "⚖️", description: "Legal & Contratos" },
  { id: "oracle",   name: "ORACLE",   icon: "🔮", description: "Estrategia & Negocios" },
  { id: "hermes",   name: "HERMES",   icon: "🌍", description: "Traducción" },
  { id: "echo",     name: "ECHO",     icon: "🎙️", description: "Voz & Podcasts" },
  { id: "darwin",   name: "DARWIN",   icon: "🔬", description: "Investigación" },
  { id: "pixel",    name: "PIXEL",    icon: "🎨", description: "Imágenes & Diseño" },
  { id: "nexus",    name: "NEXUS",    icon: "📡", description: "Redes Sociales" },
  { id: "forge",    name: "FORGE",    icon: "📊", description: "Datos & Excel" },
  { id: "sage",     name: "SAGE",     icon: "🎓", description: "Educación" },
  { id: "vector",   name: "VECTOR",   icon: "💼", description: "Ventas & CRM" },
  { id: "chronos",  name: "CHRONOS",  icon: "⏱️", description: "Productividad" },
  { id: "politeia", name: "POLITEIA", icon: "🏛️", description: "Política & Análisis" },
  { id: "educraft", name: "EDUCRAFT", icon: "🏫", description: "Cursos Online" },
];

interface AgentSelectorProps {
  selected: AgentType | string;
  onChange: (agent: AgentType | string) => void;
  customAgents?: CustomAgent[];
}

export default function AgentSelector({ selected, onChange, customAgents = [] }: AgentSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const currentBuiltin = AGENTS.find(a => a.id === selected);
  const currentCustom = customAgents.find(a => a.id === selected);
  const currentIcon = currentBuiltin?.icon ?? currentCustom?.emoji ?? "🤖";
  const currentName = currentBuiltin?.name ?? currentCustom?.name?.toUpperCase() ?? "AGENTE";
  const currentDesc = currentBuiltin?.description ?? currentCustom?.description ?? "";

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className={`
          flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium
          border transition-all duration-200
          ${open
            ? "bg-indigo-600 border-indigo-500 text-white"
            : "bg-[#12121a] border-[#1e1e2e] text-[#e2e8f0] hover:border-indigo-500/50"
          }
        `}
      >
        <span className="text-sm">{currentIcon}</span>
        <span className="font-bold">{currentName}</span>
        <span className="hidden sm:inline text-[10px] font-normal opacity-60 truncate max-w-[90px]">{currentDesc}</span>
        <span className={`text-[10px] transition-transform ml-0.5 ${open ? "rotate-180" : ""}`}>▼</span>
      </button>

      {open && (
        <div className="
          absolute top-full left-0 mt-1 z-50
          bg-[#0d0d14] border border-[#1e1e2e] rounded-xl shadow-2xl shadow-black/60
          p-3 w-[320px] sm:w-[440px]
        ">
          <p className="text-[10px] text-[#475569] font-semibold uppercase tracking-wider mb-2 px-1">
            16 Agentes disponibles
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-1">
            {AGENTS.map((agent) => (
              <button
                key={agent.id}
                onClick={() => { onChange(agent.id); setOpen(false); }}
                className={`
                  flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs
                  transition-all duration-150 text-left border
                  ${selected === agent.id
                    ? "bg-indigo-600/20 border-indigo-500/40 text-[#e2e8f0]"
                    : "border-transparent text-[#64748b] hover:bg-[#12121a] hover:text-[#e2e8f0] hover:border-[#1e1e2e]"
                  }
                `}
              >
                <span className="text-sm flex-shrink-0">{agent.icon}</span>
                <div className="min-w-0">
                  <div className="font-semibold">{agent.name}</div>
                  <div className="text-[10px] text-[#475569] truncate">{agent.description}</div>
                </div>
              </button>
            ))}
          </div>

          {customAgents.length > 0 && (
            <>
              <div className="border-t border-[#1e1e2e] my-2" />
              <p className="text-[10px] text-[#475569] font-semibold uppercase tracking-wider mb-2 px-1">Mis agentes</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1">
                {customAgents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => { onChange(agent.id); setOpen(false); }}
                    className={`
                      flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs
                      transition-all duration-150 text-left border
                      ${selected === agent.id
                        ? "bg-purple-600/20 border-purple-500/40 text-[#e2e8f0]"
                        : "border-transparent text-[#64748b] hover:bg-[#12121a] hover:text-[#e2e8f0] hover:border-[#1e1e2e]"
                      }
                    `}
                  >
                    <span className="text-sm flex-shrink-0">{agent.emoji}</span>
                    <div className="min-w-0">
                      <div className="font-semibold truncate">{agent.name.toUpperCase()}</div>
                      <div className="text-[10px] text-[#475569] truncate">{agent.description || "Personalizado"}</div>
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
