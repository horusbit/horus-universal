"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function AuthCallback() {
  const router = useRouter();

  useEffect(() => {
    supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        router.push("/");
      } else {
        router.push("/login");
      }
    });
  }, [router]);

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
      <div className="text-center">
        <div className="text-4xl mb-4 animate-pulse">👁</div>
        <p className="text-[#64748b] text-sm">Verificando sesión...</p>
      </div>
    </div>
  );
}
