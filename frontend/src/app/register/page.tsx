"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) { setError("Las contraseñas no coinciden"); return; }
    if (password.length < 6) { setError("Mínimo 6 caracteres"); return; }
    setLoading(true);
    const { error } = await supabase.auth.signUp({ email, password });
    if (error) {
      setError(error.message);
      setLoading(false);
    } else {
      setDone(true);
    }
  };

  if (done) return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-4">
      <div className="text-center">
        <div className="text-5xl mb-4">✅</div>
        <h2 className="text-xl font-bold text-[#e2e8f0] mb-2">¡Revisa tu email!</h2>
        <p className="text-[#64748b] text-sm mb-6">Te enviamos un link de confirmación a <strong className="text-indigo-400">{email}</strong></p>
        <Link href="/login" className="text-indigo-400 hover:text-indigo-300 text-sm transition-colors">
          Volver al login →
        </Link>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">👁</div>
          <h1 className="text-2xl font-bold text-[#e2e8f0]">Crear cuenta</h1>
          <p className="text-[#64748b] text-sm mt-1">Accede a HORUS Universal gratis</p>
        </div>

        <form onSubmit={handleRegister} className="bg-[#12121a] border border-[#1e1e2e] rounded-2xl p-8 space-y-5">
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
              placeholder="Mínimo 6 caracteres"
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
              placeholder="Repite la contraseña"
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
            {loading ? "Creando cuenta..." : "Crear cuenta gratis"}
          </button>

          <p className="text-center text-xs text-[#64748b]">
            ¿Ya tienes cuenta?{" "}
            <Link href="/login" className="text-indigo-400 hover:text-indigo-300 transition-colors">
              Inicia sesión
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
