import { useState, useEffect, useCallback } from "react";
import {
  View, Text, FlatList, TouchableOpacity,
  StyleSheet, ActivityIndicator, RefreshControl, Alert,
} from "react-native";
import { useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = "https://horus-backend.onrender.com";

interface Conversation {
  id: string;
  title: string;
  agent: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

const AGENT_ICONS: Record<string, string> = {
  atlas: "🔭", cipher: "🔐", nova: "✨", lexis: "📝", oracle: "🔮",
  hermes: "⚡", echo: "🎵", darwin: "🧬", pixel: "🎨", nexus: "🕸️",
  forge: "⚙️", sage: "📚", vector: "📊", chronos: "⏰", politeia: "⚖️", educraft: "🎓",
};

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return "ahora";
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d`;
  return new Date(dateStr).toLocaleDateString("es", { month: "short", day: "numeric" });
}

export default function ConversationsScreen() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchConversations = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const token = await AsyncStorage.getItem("horus_token");
      if (!token) { router.replace("/login"); return; }

      const res = await fetch(`${API_URL}/api/v1/conversations?limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) { router.replace("/login"); return; }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setConversations(Array.isArray(data) ? data : data.conversations || []);
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [router]);

  useEffect(() => { fetchConversations(); }, [fetchConversations]);

  const openConversation = (id: string) => {
    router.push({ pathname: "/chat", params: { conversationId: id } });
  };

  const deleteConversation = (id: string) => {
    Alert.alert("Eliminar conversación", "¿Eliminar esta conversación?", [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Eliminar",
        style: "destructive",
        onPress: async () => {
          try {
            const token = await AsyncStorage.getItem("horus_token");
            await fetch(`${API_URL}/api/v1/conversations/${id}`, {
              method: "DELETE",
              headers: { Authorization: `Bearer ${token}` },
            });
            setConversations(prev => prev.filter(c => c.id !== id));
          } catch {}
        },
      },
    ]);
  };

  const renderItem = ({ item }: { item: Conversation }) => {
    const icon = AGENT_ICONS[item.agent] || "🤖";
    return (
      <TouchableOpacity
        style={styles.item}
        onPress={() => openConversation(item.id)}
        onLongPress={() => deleteConversation(item.id)}
        activeOpacity={0.7}
      >
        <Text style={styles.itemIcon}>{icon}</Text>
        <View style={styles.itemBody}>
          <Text style={styles.itemTitle} numberOfLines={1}>
            {item.title || "Conversación sin título"}
          </Text>
          <View style={styles.itemMeta}>
            <Text style={styles.itemAgent}>{item.agent?.toUpperCase()}</Text>
            {item.message_count !== undefined && (
              <Text style={styles.itemCount}>· {item.message_count} msgs</Text>
            )}
          </View>
        </View>
        <Text style={styles.itemTime}>{timeAgo(item.updated_at || item.created_at)}</Text>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Conversaciones</Text>
        <TouchableOpacity onPress={() => router.push("/chat")} style={styles.newBtn}>
          <Text style={styles.newBtnText}>+ Nueva</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#6366f1" />
        </View>
      ) : conversations.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyIcon}>💬</Text>
          <Text style={styles.emptyTitle}>Sin conversaciones</Text>
          <Text style={styles.emptyHint}>Inicia tu primera conversación</Text>
          <TouchableOpacity style={styles.startBtn} onPress={() => router.push("/chat")}>
            <Text style={styles.startBtnText}>Comenzar ahora</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={conversations}
          keyExtractor={item => item.id}
          renderItem={renderItem}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => fetchConversations(true)}
              tintColor="#6366f1"
            />
          }
          contentContainerStyle={styles.list}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0a0a0f" },
  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 20, paddingVertical: 16,
    borderBottomWidth: 1, borderBottomColor: "#1e1e2e",
    backgroundColor: "#0d0d14",
  },
  headerTitle: { fontSize: 20, fontWeight: "700", color: "#e2e8f0" },
  newBtn: {
    backgroundColor: "#4f46e5", borderRadius: 20, paddingHorizontal: 16, paddingVertical: 8,
  },
  newBtnText: { color: "#fff", fontWeight: "600", fontSize: 14 },

  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 40 },
  emptyIcon: { fontSize: 56, marginBottom: 16 },
  emptyTitle: { fontSize: 18, fontWeight: "700", color: "#e2e8f0", marginBottom: 8 },
  emptyHint: { fontSize: 14, color: "#64748b", marginBottom: 24 },
  startBtn: { backgroundColor: "#4f46e5", borderRadius: 12, paddingHorizontal: 24, paddingVertical: 12 },
  startBtnText: { color: "#fff", fontWeight: "600", fontSize: 15 },

  list: { paddingVertical: 8 },
  separator: { height: 1, backgroundColor: "#12121a", marginLeft: 72 },
  item: {
    flexDirection: "row", alignItems: "center", gap: 14,
    paddingHorizontal: 20, paddingVertical: 14, backgroundColor: "#0a0a0f",
  },
  itemIcon: { fontSize: 28, width: 38, textAlign: "center" },
  itemBody: { flex: 1 },
  itemTitle: { fontSize: 15, fontWeight: "600", color: "#e2e8f0", marginBottom: 4 },
  itemMeta: { flexDirection: "row", alignItems: "center", gap: 6 },
  itemAgent: { fontSize: 11, color: "#6366f1", fontWeight: "700" },
  itemCount: { fontSize: 11, color: "#475569" },
  itemTime: { fontSize: 12, color: "#475569" },
});
