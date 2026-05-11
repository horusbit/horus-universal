import { useState, useRef, useEffect, useCallback } from "react";
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator,
  Alert, Animated, ScrollView,
} from "react-native";
import { useRouter, useLocalSearchParams } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = "https://horus-backend.onrender.com";

const AGENTS = [
  { id: "atlas",    name: "ATLAS",    icon: "🔭", desc: "Asistente general" },
  { id: "cipher",   name: "CIPHER",   icon: "🔐", desc: "Seguridad & código" },
  { id: "nova",     name: "NOVA",     icon: "✨", desc: "Creatividad & diseño" },
  { id: "lexis",    name: "LEXIS",    icon: "📝", desc: "Escritura & redacción" },
  { id: "oracle",   name: "ORACLE",   icon: "🔮", desc: "Análisis & predicción" },
  { id: "hermes",   name: "HERMES",   icon: "⚡", desc: "Velocidad & síntesis" },
  { id: "echo",     name: "ECHO",     icon: "🎵", desc: "Audio & multimedia" },
  { id: "darwin",   name: "DARWIN",   icon: "🧬", desc: "Ciencia & datos" },
  { id: "pixel",    name: "PIXEL",    icon: "🎨", desc: "Imágenes & visual" },
  { id: "nexus",    name: "NEXUS",    icon: "🕸️", desc: "Conexiones & research" },
  { id: "forge",    name: "FORGE",    icon: "⚙️", desc: "Ingeniería & sistemas" },
  { id: "sage",     name: "SAGE",     icon: "📚", desc: "Conocimiento profundo" },
  { id: "vector",   name: "VECTOR",   icon: "📊", desc: "Matemáticas & finanzas" },
  { id: "chronos",  name: "CHRONOS",  icon: "⏰", desc: "Planificación & tiempo" },
  { id: "politeia", name: "POLITEIA", icon: "⚖️", desc: "Legal & política" },
  { id: "educraft", name: "EDUCRAFT", icon: "🎓", desc: "Educación & aprendizaje" },
];

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  streaming?: boolean;
}

export default function ChatScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ conversationId?: string; agentId?: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [agent, setAgent] = useState(params.agentId || "atlas");
  const [showAgents, setShowAgents] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(params.conversationId || null);
  const flatListRef = useRef<FlatList>(null);
  const currentAgentInfo = AGENTS.find(a => a.id === agent) || AGENTS[0];

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    // Placeholder for streaming response
    const assistantMsgId = (Date.now() + 1).toString();
    setMessages(prev => [
      ...prev,
      { id: assistantMsgId, role: "assistant", content: "", agent, streaming: true },
    ]);

    try {
      const token = await AsyncStorage.getItem("horus_token");
      if (!token) {
        router.replace("/login");
        return;
      }

      // Build history from current messages
      const history = messages.map(m => ({ role: m.role, content: m.content }));

      const res = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          agent,
          conversation_id: conversationId,
          history,
          stream: true,
        }),
      });

      if (!res.ok) {
        if (res.status === 401) {
          await AsyncStorage.removeItem("horus_token");
          router.replace("/login");
          return;
        }
        throw new Error(`HTTP ${res.status}`);
      }

      // Read SSE stream
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No stream reader");

      const decoder = new TextDecoder();
      let accumulated = "";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;
          const dataStr = trimmed.slice(6).trim();
          if (!dataStr || dataStr === "[DONE]") continue;

          try {
            const data = JSON.parse(dataStr);
            if (data.conversation_id && !conversationId) {
              setConversationId(data.conversation_id);
            }
            if (data.content) {
              accumulated += data.content;
              setMessages(prev =>
                prev.map(m =>
                  m.id === assistantMsgId
                    ? { ...m, content: accumulated }
                    : m
                )
              );
            }
            if (data.done) break;
          } catch {
            // Try plain text chunk
            if (dataStr && !dataStr.startsWith("{")) {
              accumulated += dataStr;
              setMessages(prev =>
                prev.map(m =>
                  m.id === assistantMsgId
                    ? { ...m, content: accumulated }
                    : m
                )
              );
            }
          }
        }
      }

      // Mark streaming done
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMsgId ? { ...m, streaming: false } : m
        )
      );
    } catch (err: any) {
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: `Error: ${err.message}`, streaming: false }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  }, [input, loading, agent, conversationId, messages, router]);

  const handleLogout = async () => {
    Alert.alert("Cerrar sesión", "¿Estás seguro?", [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Salir",
        style: "destructive",
        onPress: async () => {
          await AsyncStorage.removeItem("horus_token");
          await AsyncStorage.removeItem("horus_email");
          router.replace("/login");
        },
      },
    ]);
  };

  const newConversation = () => {
    setMessages([]);
    setConversationId(null);
  };

  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }, [messages]);

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.role === "user";
    const agentInfo = AGENTS.find(a => a.id === item.agent);
    return (
      <View style={[styles.msgRow, isUser ? styles.msgRowUser : styles.msgRowBot]}>
        {!isUser && (
          <Text style={styles.msgAvatar}>
            {agentInfo?.icon || currentAgentInfo.icon}
          </Text>
        )}
        <View style={[styles.msgBubble, isUser ? styles.bubbleUser : styles.bubbleBot]}>
          {!isUser && (
            <Text style={styles.msgAgentName}>
              {agentInfo?.name || currentAgentInfo.name}
            </Text>
          )}
          <Text style={[styles.msgText, isUser && styles.msgTextUser]}>
            {item.content}
            {item.streaming && <Text style={styles.cursor}>▋</Text>}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={newConversation} style={styles.headerBtn}>
          <Text style={styles.headerBtnText}>✏️</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setShowAgents(!showAgents)} style={styles.agentPill}>
          <Text style={styles.agentPillIcon}>{currentAgentInfo.icon}</Text>
          <Text style={styles.agentPillName}>{currentAgentInfo.name}</Text>
          <Text style={styles.agentPillChev}>{showAgents ? "▲" : "▼"}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={handleLogout} style={styles.headerBtn}>
          <Text style={styles.headerBtnText}>⏏️</Text>
        </TouchableOpacity>
      </View>

      {/* Agent Picker Dropdown */}
      {showAgents && (
        <View style={styles.agentDropdown}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.agentScroll}>
            {AGENTS.map(a => (
              <TouchableOpacity
                key={a.id}
                style={[styles.agentChip, agent === a.id && styles.agentChipActive]}
                onPress={() => { setAgent(a.id); setShowAgents(false); }}
              >
                <Text style={styles.agentChipIcon}>{a.icon}</Text>
                <Text style={[styles.agentChipName, agent === a.id && styles.agentChipNameActive]}>
                  {a.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Messages */}
      {messages.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyIcon}>{currentAgentInfo.icon}</Text>
          <Text style={styles.emptyTitle}>{currentAgentInfo.name}</Text>
          <Text style={styles.emptyDesc}>{currentAgentInfo.desc}</Text>
          <Text style={styles.emptyHint}>Escribe un mensaje para comenzar</Text>
        </View>
      ) : (
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={item => item.id}
          renderItem={renderMessage}
          contentContainerStyle={styles.messageList}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />
      )}

      {/* Bottom Nav */}
      <View style={styles.bottomNav}>
        <TouchableOpacity style={styles.navBtn} onPress={() => router.push("/conversations")}>
          <Text style={styles.navIcon}>💬</Text>
          <Text style={styles.navLabel}>Historial</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.navBtn, styles.navBtnActive]} onPress={() => {}}>
          <Text style={styles.navIcon}>🏠</Text>
          <Text style={[styles.navLabel, styles.navLabelActive]}>Chat</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navBtn} onPress={() => router.push("/agents")}>
          <Text style={styles.navIcon}>🤖</Text>
          <Text style={styles.navLabel}>Agentes</Text>
        </TouchableOpacity>
      </View>

      {/* Input */}
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={0}
      >
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder={`Habla con ${currentAgentInfo.name}...`}
            placeholderTextColor="#475569"
            value={input}
            onChangeText={setInput}
            multiline
            maxLength={4000}
            onSubmitEditing={sendMessage}
          />
          <TouchableOpacity
            style={[styles.sendBtn, (!input.trim() || loading) && styles.sendBtnDisabled]}
            onPress={sendMessage}
            disabled={!input.trim() || loading}
          >
            {loading
              ? <ActivityIndicator color="#fff" size="small" />
              : <Text style={styles.sendIcon}>↑</Text>
            }
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0a0a0f" },

  // Header
  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 16, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: "#1e1e2e",
    backgroundColor: "#0d0d14",
  },
  headerBtn: { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  headerBtnText: { fontSize: 20 },
  agentPill: {
    flexDirection: "row", alignItems: "center", gap: 6,
    backgroundColor: "#12121a", borderRadius: 20, paddingHorizontal: 14, paddingVertical: 8,
    borderWidth: 1, borderColor: "#4f46e5",
  },
  agentPillIcon: { fontSize: 16 },
  agentPillName: { fontSize: 14, fontWeight: "700", color: "#e2e8f0", letterSpacing: 0.5 },
  agentPillChev: { fontSize: 10, color: "#64748b" },

  // Agent Dropdown
  agentDropdown: {
    backgroundColor: "#0d0d14", borderBottomWidth: 1, borderBottomColor: "#1e1e2e",
    paddingVertical: 12,
  },
  agentScroll: { paddingHorizontal: 12, gap: 8 },
  agentChip: {
    alignItems: "center", backgroundColor: "#12121a", borderRadius: 12,
    paddingHorizontal: 12, paddingVertical: 8, borderWidth: 1, borderColor: "#1e1e2e",
    minWidth: 72,
  },
  agentChipActive: { borderColor: "#4f46e5", backgroundColor: "#1a1a2e" },
  agentChipIcon: { fontSize: 20, marginBottom: 2 },
  agentChipName: { fontSize: 10, color: "#64748b", fontWeight: "600" },
  agentChipNameActive: { color: "#818cf8" },

  // Messages
  messageList: { paddingHorizontal: 16, paddingVertical: 12, gap: 12 },
  msgRow: { flexDirection: "row", alignItems: "flex-end", gap: 8 },
  msgRowUser: { justifyContent: "flex-end" },
  msgRowBot: { justifyContent: "flex-start" },
  msgAvatar: { fontSize: 24, marginBottom: 4 },
  msgBubble: {
    maxWidth: "80%", borderRadius: 16, padding: 12,
  },
  bubbleUser: { backgroundColor: "#4f46e5", borderBottomRightRadius: 4 },
  bubbleBot: { backgroundColor: "#12121a", borderWidth: 1, borderColor: "#1e1e2e", borderBottomLeftRadius: 4 },
  msgAgentName: { fontSize: 11, color: "#6366f1", fontWeight: "700", marginBottom: 4 },
  msgText: { fontSize: 15, color: "#cbd5e1", lineHeight: 22 },
  msgTextUser: { color: "#fff" },
  cursor: { color: "#818cf8", fontSize: 16 },

  // Empty state
  emptyState: { flex: 1, alignItems: "center", justifyContent: "center", padding: 40 },
  emptyIcon: { fontSize: 64, marginBottom: 16 },
  emptyTitle: { fontSize: 22, fontWeight: "700", color: "#e2e8f0", marginBottom: 8 },
  emptyDesc: { fontSize: 14, color: "#64748b", textAlign: "center", marginBottom: 24 },
  emptyHint: { fontSize: 13, color: "#334155", textAlign: "center" },

  // Input
  inputRow: {
    flexDirection: "row", alignItems: "flex-end", gap: 10,
    padding: 12, borderTopWidth: 1, borderTopColor: "#1e1e2e",
    backgroundColor: "#0d0d14",
  },
  input: {
    flex: 1, backgroundColor: "#12121a", borderRadius: 20,
    paddingHorizontal: 16, paddingVertical: 10, color: "#e2e8f0",
    fontSize: 15, maxHeight: 120, borderWidth: 1, borderColor: "#1e1e2e",
  },
  sendBtn: {
    width: 44, height: 44, borderRadius: 22, backgroundColor: "#4f46e5",
    alignItems: "center", justifyContent: "center",
  },
  sendBtnDisabled: { opacity: 0.4 },
  sendIcon: { color: "#fff", fontSize: 20, fontWeight: "700" },

  // Bottom nav
  bottomNav: {
    flexDirection: "row", justifyContent: "space-around", alignItems: "center",
    paddingVertical: 8, borderTopWidth: 1, borderTopColor: "#1e1e2e",
    backgroundColor: "#0d0d14",
  },
  navBtn: { alignItems: "center", paddingVertical: 4, paddingHorizontal: 20 },
  navBtnActive: {},
  navIcon: { fontSize: 22, marginBottom: 2 },
  navLabel: { fontSize: 11, color: "#475569" },
  navLabelActive: { color: "#818cf8" },
});
