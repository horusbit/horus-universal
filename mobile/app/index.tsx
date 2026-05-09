import { useEffect } from "react";
import { useRouter } from "expo-router";
import { View, ActivityIndicator } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

export default function Index() {
  const router = useRouter();

  useEffect(() => {
    AsyncStorage.getItem("horus_token").then(token => {
      if (token) {
        router.replace("/chat");
      } else {
        router.replace("/login");
      }
    });
  }, []);

  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#0a0a0f" }}>
      <ActivityIndicator size="large" color="#6366f1" />
    </View>
  );
}
