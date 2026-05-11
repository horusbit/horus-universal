import {
  View, Text, FlatList, TouchableOpacity,
  StyleSheet, TextInput,
} from "react-native";
import { useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { useState } from "react";

const AGENTS = [
  { id: "atlas",    name: "ATLAS",    icon: "🔭", desc: "Asistente general inteligente", tags: ["general", "ayuda"] },
  { id: "cipher",   name: "CIPHER",   icon: "🔐", desc: "Seguridad, código y criptografía", tags: ["código", "seguridad"] },
  { id: "nova",     name: "NOVA",     icon: "✨", desc: "Creatividad, diseño e ideas", tags: ["creativo", "diseño"] },
  { id: "lexis",    name: "LEXIS",    icon: "📝", desc: "Escritura, redacción y storytelling", tags: ["escritura", "texto"] },
  { id: "oracle",   name: "ORACLE",   icon: "🔮", desc: "Análisis profundo y predicciones", tags: ["análisis", "datos"] },
  { id: "hermes",   name: "HERMES",   icon: "⚡", desc: "Velocidad, síntesis y resúmenes rápidos", tags: ["rápido", "síntesis"] },
  { id: "echo",     name: "ECHO",     icon: "🎵", desc: "Audio, podcasts y multimedia", tags: ["audio", "media"] },
  { id: "darwin",   name: "DARWIN",   icon: "🧬", desc: "Ciencia, biología y datos", tags: ["ciencia", "investigación"] },
  { id: "pixel",    name: "PIXEL",    icon: "🎨", desc: "Imágenes, gráficos y arte visual", tags: ["imágenes", "visual"] },
  { id: "nexus",    name: "NEXUS",    icon: "🕸️", desc: "Research, conexiones y web", tags: ["research", "web"] },
  { id: "forge",    name: "FORGE",    icon: "⚙️", desc: "Ingeniería, sistemas y DevOps", tags: ["ingeniería", "técnico"] },
  { id: "sage",     name: "SAGE",     icon: "📚", desc: "Conocimiento profundo y filosofía", tags: ["conocimiento", "filosofía"] },
  { id: "vector",   name: "VECTOR",   icon: "📊", desc: "Matemáticas, finanzas y estadística", tags: ["matemáticas", "finanzas"] },
  { id: "chronos",  name: "CHRONOS",  icon: "⏰", desc: "Planificación, productividad y tiempo", tags: ["planificación", "tiempo"] },
  { id: "politeia", name: "POLITEIA", icon: "⚖️", desc: "Legal, política y ética", tags: ["legal", "política"] },
  { id: "educraft", name: "EDUCRAFT", icon: "🎓", desc: "Educación, tutorías y aprendizaje", tags: ["educación", "aprendizaje"] },
];

export default function AgentsScreen() {
  const router = useRouter();
  const [search, setSearch] = useState("");

  const filtered = search.trim()
    ? AGENTS.filter(a =>
        a.name.toLowerCase().includes(search.toLowerCase()) ||
        a.desc.toLowerCase().includes(search.toLowerCase()) ||
        a.tags.some(t => t.toLowerCase().includes(search.toLowerCase()))
      )
    : AGENTS;

  const openAgent = (agentId: string) => {
    router.push({ pathname: "/chat", params: { agentId } });
  };

  const renderAgent = ({ item }: { item: typeof AGENTS[0] }) => (
    <TouchableOpacity style={styles.card} onPress={() => openAgent(item.id)} activeOpacity={0.7}>
      <View style={styles.cardIconWrap}>
        <Text style={styles.cardIcon}>{item.icon}</Text>
      </View>
      <View style={styles.cardBody}>
        <Text style={styles.cardName}>{item.name}</Text>
        <Text style={styles.cardDesc} numberOfLines={2}>{item.desc}</Text>
        <View style={styles.cardTags}>
          {item.tags.slice(0, 2).map(t => (
            <View key={t} style={styles.tag}>
              <Text style={styles.tagText}>{t}</Text>
            </View>
          ))}
        </View>
      </View>
      <Text style={styles.cardArrow}>›</Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Agentes IA</Text>
        <Text style={styles.headerCount}>{filtered.length}</Text>
      </View>

      <View style={styles.searchWrap}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          style={styles.searchInput}
          placeholder="Buscar agente..."
          placeholderTextColor="#475569"
          value={search}
          onChangeText={setSearch}
          autoCorrect={false}
        />
        {search.length > 0 && (
          <TouchableOpacity onPress={() => setSearch("")}>
            <Text style={styles.clearBtn}>✕</Text>
          </TouchableOpacity>
        )}
      </View>

      <FlatList
        data={filtered}
        keyExtractor={item => item.id}
        renderItem={renderAgent}
        contentContainerStyle={styles.list}
        ItemSeparatorComponent={() => <View style={styles.sep} />}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No se encontraron agentes</Text>
          </View>
        }
      />
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
  headerCount: {
    backgroundColor: "#1a1a2e", color: "#818cf8", fontSize: 13,
    fontWeight: "700", paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12,
  },

  searchWrap: {
    flexDirection: "row", alignItems: "center", gap: 10,
    margin: 16, backgroundColor: "#12121a", borderRadius: 14,
    paddingHorizontal: 14, borderWidth: 1, borderColor: "#1e1e2e",
  },
  searchIcon: { fontSize: 16 },
  searchInput: { flex: 1, color: "#e2e8f0", fontSize: 15, paddingVertical: 12 },
  clearBtn: { color: "#64748b", fontSize: 16, padding: 4 },

  list: { paddingBottom: 20 },
  sep: { height: 1, backgroundColor: "#12121a", marginLeft: 80 },

  card: {
    flexDirection: "row", alignItems: "center", gap: 14,
    paddingHorizontal: 16, paddingVertical: 14, backgroundColor: "#0a0a0f",
  },
  cardIconWrap: {
    width: 52, height: 52, borderRadius: 16,
    backgroundColor: "#12121a", borderWidth: 1, borderColor: "#1e1e2e",
    alignItems: "center", justifyContent: "center",
  },
  cardIcon: { fontSize: 26 },
  cardBody: { flex: 1 },
  cardName: { fontSize: 15, fontWeight: "700", color: "#e2e8f0", marginBottom: 3 },
  cardDesc: { fontSize: 13, color: "#64748b", marginBottom: 6, lineHeight: 18 },
  cardTags: { flexDirection: "row", gap: 6 },
  tag: {
    backgroundColor: "#1a1a2e", borderRadius: 8,
    paddingHorizontal: 8, paddingVertical: 3,
  },
  tagText: { fontSize: 11, color: "#6366f1", fontWeight: "600" },
  cardArrow: { fontSize: 22, color: "#334155", fontWeight: "300" },

  empty: { padding: 40, alignItems: "center" },
  emptyText: { color: "#475569", fontSize: 15 },
});
