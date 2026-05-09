"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function AuthConfirmPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Supabase redirige aquí con tokens en el hash — los procesa automáticamente
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) setReady(true);
      else setError("Enlace inválido o expirado. Solicita uno nuevo.");
    });
  }, []);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Las contraseñas no coinciden.");
      return;
    }
    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres.");
      return;
    }
    setLoading(true);
    setError("");
    const { error } = await supabase.auth.updateUser({ password });
    if (error) {
      setError(error.message);
      setLoading(false);
    } else {
      router.push("/?reset=true");
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">👁</div>
          <h1 className="text-2xl font-bold text-[#e2e8f0]">Nueva contraseña</h1>
          <p className="text-[#64748b] text-sm mt-1">Elige una contraseña segura</p>
        </div>

        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-8 space-y-5">
          {!ready ? (
            <div className="text-center">
              {error ? (
                <div className="space-y-3">
                  <p className="text-red-400 text-sm">{error}</p>
                  <a href="/reset-password" className="text-indigo-400 hover:text-indigo-300 text-sm transition-colors">
                    Solicitar nuevo enlace
                  </a>
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2 text-[#64748b] text-sm">
                  <span className="w-4 h-4 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
                  Verificando enlace...
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={handleUpdate} className="space-y-4">
              <div>
                <label className="block text-xs text-[#64748b] mb-1.5">Nueva contraseña</label>
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
              <div>
                <label className="block text-xs text-[#64748b] mb-1.5">Confirmar contraseña</label>
                <input
                  type="password"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
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
                {loading ? "Actualizando..." : "Actualizar contraseña"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
