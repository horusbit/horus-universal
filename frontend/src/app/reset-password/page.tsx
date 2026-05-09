"use client";

import { useState } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabase";

export default function ResetPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/confirm`,
    });
    if (error) {
      setError(error.message);
    } else {
      setSent(true);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">👁</div>
          <h1 className="text-2xl font-bold text-[#e2e8f0]">Recuperar contraseña</h1>
          <p className="text-[#64748b] text-sm mt-1">Te enviamos un enlace a tu email</p>
        </div>

        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-8 space-y-5">
          {sent ? (
            <div className="text-center space-y-4">
              <div className="text-4xl">📧</div>
              <p className="text-[#e2e8f0] text-sm">
                Revisa tu email <strong>{email}</strong> — te enviamos un enlace para restablecer tu contraseña.
              </p>
              <p className="text-[#64748b] text-xs">Si no lo ves, revisa la carpeta de spam.</p>
              <Link href="/login" className="block text-indigo-400 hover:text-indigo-300 text-sm transition-colors">
                Volver al inicio de sesión
              </Link>
            </div>
          ) : (
            <form onSubmit={handleReset} className="space-y-4">
              <div>
                <label className="block text-xs text-[#64748b] mb-1.5">Email de tu cuenta</label>
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
                {loading ? "Enviando..." : "Enviar enlace de recuperación"}
              </button>

              <p className="text-center text-xs text-[#64748b]">
                <Link href="/login" className="text-indigo-400 hover:text-indigo-300 transition-colors">
                  ← Volver al inicio de sesión
                </Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
