const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type AgentType =
  | "atlas" | "cipher" | "nova" | "lexis"
  | "oracle" | "hermes" | "echo" | "darwin" | "pixel"
  | "nexus" | "forge" | "sage" | "vector" | "chronos" | "politeia" | "educraft";

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatRequest {
  message: string;
  agent: AgentType | string;  // string also allows custom agent UUIDs
  conversation_id?: string;
  history?: ChatMessage[];
  stream?: boolean;
}

export interface ChatResponse {
  content: string;
  agent: AgentType;
  model_used: string;
  conversation_id: string;
  tokens_used?: number;
}

export interface ConversationSummary {
  id: string;
  title: string;
  message_count: number;
  last_message?: string;
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  try {
    const { supabase } = await import("./supabase");
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) {
      return { Authorization: `Bearer ${data.session.access_token}` };
    }
  } catch {}
  return {};
}

export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const authHeaders = await getAuthHeaders();
  const response = await fetch(`${API_URL}/api/v1/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders },
    body: JSON.stringify({ ...request, stream: false }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Error ${response.status}`);
  }
  return response.json();
}

export async function* streamMessage(
  request: ChatRequest,
  onChunk?: (chunk: string) => void
): AsyncGenerator<string, void, undefined> {
  const authHeaders = await getAuthHeaders();
  const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders },
    body: JSON.stringify({ ...request, stream: true }),
  });
  if (!response.ok) throw new Error(`Error ${response.status}`);

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;
        const dataStr = trimmed.slice(6).trim();
        if (!dataStr || dataStr === "[DONE]") continue;
        try {
          const data = JSON.parse(dataStr);
          if (data.type === "chunk" && data.content) {
            onChunk?.(data.content);
            yield data.content;
          } else if (data.type === "error") {
            throw new Error(data.message || "Error en streaming");
          }
        } catch (e) {
          if (e instanceof SyntaxError) continue;
          throw e;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export async function getConversations(): Promise<ConversationSummary[]> {
  try {
    const authHeaders = await getAuthHeaders();
    const r = await fetch(`${API_URL}/api/v1/conversations/`, { headers: authHeaders });
    if (!r.ok) return [];
    return r.json();
  } catch { return []; }
}

export async function getConversationMessages(id: string): Promise<ChatMessage[]> {
  try {
    const authHeaders = await getAuthHeaders();
    const r = await fetch(`${API_URL}/api/v1/conversations/${id}`, { headers: authHeaders });
    if (!r.ok) return [];
    const data = await r.json();
    return data.messages || [];
  } catch { return []; }
}

export async function setConversationTitle(id: string, title: string): Promise<void> {
  const authHeaders = await getAuthHeaders();
  await fetch(`${API_URL}/api/v1/conversations/${id}/title`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders },
    body: JSON.stringify({ title }),
  }).catch(() => {});
}

export async function deleteConversation(id: string): Promise<void> {
  const authHeaders = await getAuthHeaders();
  await fetch(`${API_URL}/api/v1/conversations/${id}`, {
    method: "DELETE",
    headers: authHeaders,
  }).catch(() => {});
}

export async function healthCheck(): Promise<boolean> {
  try {
    const r = await fetch(`${API_URL}/health`);
    return r.ok;
  } catch { return false; }
}

// ── Billing - Fase 6 ─────────────────────────────────────────────────────────

export interface UserPlan {
  plan: string;
  used: number;
  limit: number | null;
  remaining?: number;
  allowed: boolean;
}

export async function getUserPlan(): Promise<UserPlan> {
  try {
    const authHeaders = await getAuthHeaders();
    const r = await fetch(`${API_URL}/api/v1/billing/plan`, { headers: authHeaders });
    if (!r.ok) return { plan: "free", used: 0, limit: 50, allowed: true };
    return r.json();
  } catch { return { plan: "free", used: 0, limit: 50, allowed: true }; }
}

export async function createCheckout(): Promise<string | null> {
  try {
    const authHeaders = await getAuthHeaders();
    const r = await fetch(`${API_URL}/api/v1/billing/checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders },
    });
    if (!r.ok) return null;
    const data = await r.json();
    return data.checkout_url || null;
  } catch { return null; }
}

// ── Voz - Fase 2 ──────────────────────────────────────────────────────────────

export interface VoiceStatus {
  stt: { provider: string; enabled: boolean; endpoint: string };
  tts: { provider: string; voice_id: string; enabled: boolean; endpoint: string };
}

export async function getVoiceStatus(): Promise<VoiceStatus | null> {
  try {
    const r = await fetch(`${API_URL}/api/v1/voice/status`);
    if (!r.ok) return null;
    return r.json();
  } catch { return null; }
}

/**
 * Envía un blob de audio al backend y devuelve el transcript.
 * Requiere GROQ_API_KEY en el backend.
 */
export async function transcribeAudio(
  audioBlob: Blob,
  language: string = "es"
): Promise<string> {
  const formData = new FormData();
  const ext = audioBlob.type.includes("mp4") ? "mp4" : "webm";
  formData.append("audio", audioBlob, `recording.${ext}`);
  formData.append("language", language);

  const r = await fetch(`${API_URL}/api/v1/voice/transcribe`, {
    method: "POST",
    body: formData,
  });

  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || `Error ${r.status} en transcripción`);
  }

  const data = await r.json();
  return data.transcript || "";
}

/**
 * Convierte texto a audio y devuelve un URL de objeto para reproducir.
 * El backend usa ElevenLabs o Edge TTS como fallback.
 */
// ── Imágenes — PIXEL ─────────────────────────────────────────────────────────

export interface ImageGenerateRequest {
  prompt: string;
  width?: number;
  height?: number;
  model?: string;
}

export interface ImageGenerateResponse {
  url: string;
  prompt: string;
  model: string;
  width: number;
  height: number;
}

export async function generateImage(req: ImageGenerateRequest): Promise<ImageGenerateResponse> {
  const authHeaders = await getAuthHeaders();
  const r = await fetch(`${API_URL}/api/v1/images/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders },
    body: JSON.stringify({
      prompt: req.prompt,
      width: req.width ?? 1024,
      height: req.height ?? 1024,
      model: req.model ?? "flux",
      nologo: true,
      enhance: true,
    }),
  });
  if (!r.ok) throw new Error(`Image generation error ${r.status}`);
  return r.json();
}

// ── Búsqueda de conversaciones ────────────────────────────────────────────────

export async function searchConversations(q: string): Promise<ConversationSummary[]> {
  try {
    const authHeaders = await getAuthHeaders();
    const r = await fetch(`${API_URL}/api/v1/conversations/search?q=${encodeURIComponent(q)}`, {
      headers: authHeaders,
    });
    if (!r.ok) return [];
    return r.json();
  } catch { return []; }
}

// ── Compartir conversaciones ──────────────────────────────────────────────────

export interface ShareResponse {
  token: string;
  share_url: string;
}

export async function shareConversation(id: string): Promise<ShareResponse | null> {
  try {
    const authHeaders = await getAuthHeaders();
    const r = await fetch(`${API_URL}/api/v1/conversations/${id}/share`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders },
    });
    if (!r.ok) return null;
    return r.json();
  } catch { return null; }
}

export async function getSharedConversation(token: string): Promise<{
  conversation_id: string;
  title: string;
  agent: string;
  messages: { role: string; content: string }[];
} | null> {
  try {
    const r = await fetch(`${API_URL}/api/v1/share/${token}`);
    if (!r.ok) return null;
    return r.json();
  } catch { return null; }
}

// ── Agentes personalizados ────────────────────────────────────────────────────

export interface CustomAgent {
  id: string;
  name: string;
  emoji: string;
  description: string;
  system_prompt: string;
  base_model: string;
  created_at?: string;
}

export interface CustomAgentCreate {
  name: string;
  emoji: string;
  description: string;
  system_prompt: string;
  base_model: string;
}

export async function listCustomAgents(): Promise<CustomAgent[]> {
  try {
    const authHeaders = await getAuthHeaders();
    const r = await fetch(`${API_URL}/api/v1/agents/custom/`, { headers: authHeaders });
    if (!r.ok) return [];
    return r.json();
  } catch { return []; }
}

export async function createCustomAgent(data: CustomAgentCreate): Promise<CustomAgent | null> {
  try {
    const authHeaders = await getAuthHeaders();
    const r = await fetch(`${API_URL}/api/v1/agents/custom/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders },
      body: JSON.stringify(data),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || `Error ${r.status}`);
    }
    return r.json();
  } catch (e) { throw e; }
}

export async function deleteCustomAgent(id: string): Promise<void> {
  const authHeaders = await getAuthHeaders();
  await fetch(`${API_URL}/api/v1/agents/custom/${id}`, {
    method: "DELETE",
    headers: authHeaders,
  }).catch(() => {});
}

export async function getAvailableModels(): Promise<string[]> {
  try {
    const authHeaders = await getAuthHeaders();
    const r = await fetch(`${API_URL}/api/v1/agents/custom/models/available`, { headers: authHeaders });
    if (!r.ok) return [];
    const data = await r.json();
    return data.models || [];
  } catch { return []; }
}

export async function synthesizeSpeech(
  text: string,
  language: string = "es"
): Promise<string> {
  const r = await fetch(`${API_URL}/api/v1/voice/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });

  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || `Error ${r.status} en síntesis`);
  }

  const blob = await r.blob();
  return URL.createObjectURL(blob);
}
