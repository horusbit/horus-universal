import { useState } from "react";
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ActivityIndicator, Alert,
} from "react-native";
import { useRouter } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";

const API_URL = "https://horus-backend.onrender.com";

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);

  const handleAuth = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert("Error", "Completa todos los campos");
      return;
    }
    setLoading(true);
    try {
      const endpoint = isRegister ? "/api/v1/auth/register" : "/api/v1/auth/login";
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error de autenticación");

      const token = data.access_token || data.session?.access_token;
      if (!token) throw new Error("No se recibió token");

      await AsyncStorage.setItem("horus_token", token);
      await AsyncStorage.setItem("horus_email", email.trim());
      router.replace("/chat");
    } catch (e: any) {
      Alert.alert("Error", e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View style={styles.card}>
        {/* Logo */}
        <Text style={styles.logo}>👁</Text>
        <Text style={styles.title}>HORUS Universal</Text>
        <Text style={styles.subtitle}>Tu orquestador de IA personal</Text>

        {/* Form */}
        <TextInput
          style={styles.input}
          placeholder="Correo electrónico"
          placeholderTextColor="#475569"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
        />
        <TextInput
          style={styles.input}
          placeholder="Contraseña"
          placeholderTextColor="#475569"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />

        <TouchableOpacity
          style={[styles.btn, loading && styles.btnDisabled]}
          onPress={handleAuth}
          disabled={loading}
        >
          {loading
            ? <ActivityIndicator color="#fff" />
            : <Text style={styles.btnText}>{isRegister ? "Crear cuenta" : "Iniciar sesión"}</Text>
          }
        </TouchableOpacity>

        <TouchableOpacity onPress={() => setIsRegister(r => !r)} style={styles.switchBtn}>
          <Text style={styles.switchText}>
            {isRegister ? "¿Ya tienes cuenta? Inicia sesión" : "¿No tienes cuenta? Regístrate"}
          </Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0a0a0f", justifyContent: "center", padding: 24 },
  card: { backgroundColor: "#0d0d14", borderRadius: 24, padding: 28, borderWidth: 1, borderColor: "#1e1e2e" },
  logo: { fontSize: 48, textAlign: "center", marginBottom: 8 },
  title: { fontSize: 24, fontWeight: "700", color: "#e2e8f0", textAlign: "center" },
  subtitle: { fontSize: 13, color: "#64748b", textAlign: "center", marginBottom: 28, marginTop: 4 },
  input: {
    backgroundColor: "#12121a", borderRadius: 12, padding: 14, color: "#e2e8f0",
    fontSize: 14, marginBottom: 12, borderWidth: 1, borderColor: "#1e1e2e",
  },
  btn: {
    backgroundColor: "#4f46e5", borderRadius: 12, padding: 15,
    alignItems: "center", marginTop: 4,
  },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: "#fff", fontWeight: "600", fontSize: 15 },
  switchBtn: { marginTop: 16, alignItems: "center" },
  switchText: { color: "#64748b", fontSize: 13 },
});
