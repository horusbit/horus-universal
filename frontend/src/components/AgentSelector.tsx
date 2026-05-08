"use client";

import { AgentType } from "@/lib/api";

interface Agent {
  id: AgentType;
  name: string;
  icon: string;
  description: string;
}

const AGENTS: Agent[] = [
  { id: "atlas",    name: "ATLAS",    icon: "🌐", description: "Orquestador" },
  { id: "cipher",   name: "CIPHER",   icon: "⚡", description: "Código" },
  { id: "nova",     name: "NOVA",     icon: "✨", description: "Marketing" },
  { id: "lexis",    name: "LEXIS",    icon: "⚖️", description: "Legal" },
  { id: "oracle",   name: "ORACLE",   icon: "🔮", description: "Estrategia" },
  { id: "hermes",   name: "HERMES",   icon: "🌍", description: "Traducción" },
  { id: "echo",     name: "ECHO",     icon: "🎙️", description: "Voz" },
  { id: "darwin",   name: "DARWIN",   icon: "🔬", description: "Investigación" },
  { id: "pixel",    name: "PIXEL",    icon: "🎨", description: "Imágenes" },
  { id: "nexus",    name: "NEXUS",    icon: "📡", description: "Redes Sociales" },
  { id: "forge",    name: "FORGE",    icon: "📊", description: "Datos & Excel" },
  { id: "sage",     name: "SAGE",     icon: "🎓", description: "Educación" },
  { id: "vector",   name: "VECTOR",   icon: "💼", description: "Ventas & CRM" },
  { id: "chronos",  name: "CHRONOS",  icon: "⏱️", description: "Productividad" },
  { id: "politeia", name: "POLITEIA", icon: "🏛️", description: "Política" },
  { id: "educraft", name: "EDUCRAFT", icon: "🏫", description: "Edu Online" },
];

interface AgentSelectorProps {
  selected: AgentType;
  onChange: (agent: AgentType) => void;
}

export default function AgentSelector({ selected, onChange }: AgentSelectorProps) {
  return (
    <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
      {AGENTS.map((agent) => (
        <button
          key={agent.id}
          onClick={() => onChange(agent.id)}
          title={agent.description}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
            whitespace-nowrap transition-all duration-200 border
            ${selected === agent.id
              ? "bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/20"
              : "bg-[#12121a] border-[#1e1e2e] text-[#64748b] hover:border-indigo-500/50 hover:text-[#e2e8f0]"
            }
          `}
        >
          <span>{agent.icon}</span>
          <span>{agent.name}</span>
        </button>
      ))}
    </div>
  );
}
