"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  listCustomAgents, createCustomAgent, deleteCustomAgent,
  getAvailableModels, CustomAgent,
} from "@/lib/api";

const MODEL_LABELS: Record<string, string> = {
  "google/gemini-flash-1.5": "Gemini Flash 1.5",
  "google/gemini-2.0-flash-001": "Gemini 2.0 Flash",
  "meta-llama/llama-3.3-70b-instruct": "Llama 3.3 70B",
  "deepseek/deepseek-chat": "DeepSeek Chat",
  "anthropic/claude-3-haiku": "Claude 3 Haiku",
  "openai/gpt-4o-mini": "GPT-4o Mini",
};

const EMOJI_PRESETS = ["🤖", "🧠", "⚡", "🔮", "🎯", "📊", "✍️", "🔬", "💼", "🎨", "📚", "🌐", "🛡️", "🚀", "💡"];

export default function AgentsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [agents, setAgents] = useState<CustomAgent[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({
    name: "",
    emoji: "🤖",
    description: "",
    system_prompt: "",
    base_model: "google/gemini-flash-1.5",
  });

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadAgents();
      getAvailableModels().then(setModels);
    }
  }, [user]);

  const loadAgents = async () => {
    const data = await listCustomAgents();
    setAgents(data);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await createCustomAgent(form);
      setSuccess("Agente creado exitosamente.");
      setShowForm(false);
      setForm({ name: "", emoji: "🤖", description: "", system_prompt: "", base_model: "google/gemini-flash-1.5" });
      await loadAgents();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err: any) {
      setError(err?.message || "Error creando agente.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    setDeleting(id);
    await deleteCustomAgent(id);
    await loadAgents();
    setDeleting(null);
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-4xl animate-pulse">👁</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#e2e8f0]">
      {/* Header */}
      <header className="border-b border-[#1e1e2e] bg-[#12121a] px-4 py-3 flex items-center gap-4">
        <button
          onClick={() => router.push("/")}
          className="text-[#64748b] hover:text-white transition-colors text-sm"
        >
          ← Volver
        </button>
        <div className="flex-1">
          <h1 className="text-base font-bold">Mis Agentes</h1>
          <p className="text-xs text-[#64748b]">Crea agentes con personalidad y contexto propios</p>
        </div>
        <button
          onClick={() => { setShowForm(true); setError(""); }}
          disabled={agents.length >= 10}
          className="text-xs px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50
            text-white rounded-lg transition-colors"
          title={agents.length >= 10 ? "Límite de 10 agentes alcanzado" : "Crear nuevo agente"}
        >
          + Nuevo agente
        </button>
      </header>

      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Feedback */}
        {success && (
          <div className="mb-4 px-4 py-3 bg-green-900/20 border border-green-500/30 rounded-xl text-sm text-green-400">
            ✓ {success}
          </div>
        )}

        {/* Formulario de creación */}
        {showForm && (
          <div className="mb-8 bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-6">
            <h2 className="font-semibold text-sm mb-5">Nuevo agente personalizado</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              {/* Nombre + emoji */}
              <div className="flex gap-3">
                <div className="flex-shrink-0">
                  <label className="block text-xs text-[#64748b] mb-1.5">Ícono</label>
                  <div className="relative">
                    <select
                      value={form.emoji}
                      onChange={e => setForm(f => ({ ...f, emoji: e.target.value }))}
                      className="w-16 bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-2 py-2.5
                        text-center text-lg focus:outline-none focus:border-indigo-500/70 transition-colors"
                    >
                      {EMOJI_PRESETS.map(e => (
                        <option key={e} value={e}>{e}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex-1">
                  <label className="block text-xs text-[#64748b] mb-1.5">Nombre del agente</label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                    required
                    maxLength={40}
                    placeholder="ej. Mi Asistente Legal"
                    className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5
                      text-sm text-[#e2e8f0] placeholder-[#374151] focus:outline-none
                      focus:border-indigo-500/70 transition-colors"
                  />
                </div>
              </div>

              {/* Descripción */}
              <div>
                <label className="block text-xs text-[#64748b] mb-1.5">Descripción corta</label>
                <input
                  type="text"
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  maxLength={200}
                  placeholder="ej. Especialista en contratos y asesoría legal dominicana"
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5
                    text-sm text-[#e2e8f0] placeholder-[#374151] focus:outline-none
                    focus:border-indigo-500/70 transition-colors"
                />
              </div>

              {/* Modelo base */}
              <div>
                <label className="block text-xs text-[#64748b] mb-1.5">Modelo de IA</label>
                <select
                  value={form.base_model}
                  onChange={e => setForm(f => ({ ...f, base_model: e.target.value }))}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5
                    text-sm text-[#e2e8f0] focus:outline-none focus:border-indigo-500/70 transition-colors"
                >
                  {(models.length ? models : Object.keys(MODEL_LABELS)).map(m => (
                    <option key={m} value={m}>{MODEL_LABELS[m] || m}</option>
                  ))}
                </select>
              </div>

              {/* Prompt del sistema */}
              <div>
                <label className="block text-xs text-[#64748b] mb-1.5">
                  Instrucciones del sistema
                  <span className="ml-1 text-[#475569]">(define la personalidad y expertise del agente)</span>
                </label>
                <textarea
                  value={form.system_prompt}
                  onChange={e => setForm(f => ({ ...f, system_prompt: e.target.value }))}
                  required
                  minLength={10}
                  maxLength={4000}
                  rows={6}
                  placeholder={`Eres un experto en derecho dominicano con 20 años de experiencia en contratos comerciales y propiedad inmobiliaria. Respondes siempre en español con precisión legal, citando artículos del Código Civil cuando es relevante. Eres directo pero empático, y siempre aclaras que tus respuestas son orientativas y no sustituyen consulta legal formal.`}
                  className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-3
                    text-sm text-[#e2e8f0] placeholder-[#374151] focus:outline-none
                    focus:border-indigo-500/70 transition-colors resize-none"
                />
                <p className="text-xs text-[#475569] mt-1">{form.system_prompt.length}/4000 caracteres</p>
              </div>

              {error && (
                <p className="text-red-400 text-xs bg-red-900/20 border border-red-500/20 rounded-lg px-3 py-2">
                  {error}
                </p>
              )}

              <div className="flex gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => { setShowForm(false); setError(""); }}
                  className="flex-1 py-2.5 border border-[#1e1e2e] hover:border-[#2d2d4e]
                    text-[#64748b] hover:text-white text-sm rounded-lg transition-all"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50
                    text-white text-sm font-medium rounded-lg transition-all"
                >
                  {saving ? "Creando..." : "Crear agente"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Lista de agentes */}
        {agents.length === 0 && !showForm ? (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">🤖</div>
            <h3 className="text-lg font-semibold text-[#e2e8f0] mb-2">Sin agentes personalizados</h3>
            <p className="text-[#64748b] text-sm mb-6 max-w-sm mx-auto">
              Crea agentes con personalidad propia: un experto legal para tu empresa,
              un asistente de ventas de tu industria, o cualquier especialista que necesites.
            </p>
            <button
              onClick={() => setShowForm(true)}
              className="text-sm px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl transition-colors"
            >
              Crear mi primer agente
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {agents.map(agent => (
              <div
                key={agent.id}
                className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-4 flex items-start gap-4
                  hover:border-indigo-500/30 transition-colors group"
              >
                <div className="text-3xl flex-shrink-0">{agent.emoji}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-sm">{agent.name}</h3>
                    <span className="text-xs text-[#475569] bg-[#1e1e2e] px-2 py-0.5 rounded-full">
                      {MODEL_LABELS[agent.base_model] || agent.base_model}
                    </span>
                  </div>
                  {agent.description && (
                    <p className="text-xs text-[#64748b] mb-2">{agent.description}</p>
                  )}
                  <p className="text-xs text-[#475569] line-clamp-2 leading-relaxed">
                    {agent.system_prompt}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => router.push(`/?agent=${agent.id}`)}
                    className="text-xs px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/40
                      text-indigo-400 rounded-lg transition-colors"
                  >
                    Usar
                  </button>
                  <button
                    onClick={() => handleDelete(agent.id)}
                    disabled={deleting === agent.id}
                    className="text-xs px-3 py-1.5 hover:bg-red-500/20 text-[#64748b]
                      hover:text-red-400 rounded-lg transition-colors disabled:opacity-50"
                  >
                    {deleting === agent.id ? "..." : "✕"}
                  </button>
                </div>
              </div>
            ))}

            <p className="text-center text-xs text-[#475569] pt-2">
              {agents.length}/10 agentes usados
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
