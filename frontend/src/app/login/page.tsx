"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      setError(error.message);
      setLoading(false);
    } else {
      router.push("/");
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">👁</div>
          <h1 className="text-2xl font-bold text-[#e2e8f0]">HORUS Universal</h1>
          <p className="text-[#64748b] text-sm mt-1">Inicia sesión para continuar</p>
        </div>

        <form onSubmit={handleLogin} className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-8 space-y-5">
          <div>
            <label className="block text-xs text-[#64748b] mb-1.5">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              placeholder="tu@email.com"
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5
                text-[#e2e8f0] text-sm placeholder-[#374151] focus:outline-none
                focus:border-indigo-500/70 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs text-[#64748b] mb-1.5">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="w-full bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg px-4 py-2.5
                text-[#e2e8f0] text-sm placeholder-[#374151] focus:outline-none
                focus:border-indigo-500/70 transition-colors"
            />
          </div>

          {error && (
            <p className="text-red-400 text-xs bg-red-900/20 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50
              text-white text-sm font-medium rounded-lg transition-colors"
          >
            {loading ? "Entrando..." : "Iniciar sesión"}
          </button>

          <p className="text-center text-xs text-[#64748b]">
            ¿No tienes cuenta?{" "}
            <Link href="/register" className="text-indigo-400 hover:text-indigo-300 transition-colors">
              Regístrate gratis
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
